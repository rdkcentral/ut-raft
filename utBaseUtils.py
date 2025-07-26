#!/usr/bin/env python3
#** *****************************************************************************
# *
# * If not stated otherwise in this file or this component's LICENSE file the
# * following copyright and licenses apply:
# *
# * Copyright 2024 RDK Management
# *
# * Licensed under the Apache License, Version 2.0 (the "License");
# * you may not use this file except in compliance with the License.
# * You may obtain a copy of the License at
# *
# *
# http://www.apache.org/licenses/LICENSE-2.0
# *
# * Unless required by applicable law or agreed to in writing, software
# * distributed under the License is distributed on an "AS IS" BASIS,
# * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# * See the License for the specific language governing permissions and
# * limitations under the License.
# *
#* ******************************************************************************

import sys
import os
import subprocess
import time

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(dir_path+"/../../../")
sys.path.append(dir_path)

from framework.core.logModule import logModule
from framework.plugins.ut_raft.interactiveShell import InteractiveShell

class utBaseUtils():
    """
    UT Base utility class providing reusable functionalities
    """
    def __init__(self, log:logModule=None):
        """
        Initializes player class.

        Args:
            log (class, optional): Parent log class. Defaults to None.
        """
        self.log = log
        if log is None:
            self.log = logModule(self.__class__.__name__)
            self.log.setLevel( self.log.INFO )

    def sftpCopy(self, session, sourcePath, destinationPath):
        """
        Copies a file from the host machine to the target device using SFTP (via Paramiko).

        Args:
            session (session class): The active SSH session object containing the connection details.
            sourcePath (str): The full path of the file on the host machine.
            destinationPath (str): The target directory on the device.

        Returns:
            str: A message indicating the result of the file transfer.

        Raises:
            FileNotFoundError: If the source file does not exist.
            Exception: If all retries of the file transfer fail.
        """
        # Ensure the session type is SSH
        if session.type != "ssh":
            self.log.fatal("Session type must be 'ssh'")

        try:
            # Open the SSH session if it's not already open
            if not session.is_open:
                session.open()

            # Create the destination directory on the remote device
            session.write(f"mkdir -p {destinationPath}")

            # Short delay to ensure mkdir completes before file transfer
            time.sleep(0.5)

            # Normalize destination path to end with a slash
            if not destinationPath.endswith('/'):
                destinationPath += '/'

            # Ensure the source file exists on the host before attempting to transfer
            if not os.path.isfile(sourcePath):
                raise FileNotFoundError(f"Source file not found: {sourcePath}")

            # Extract the filename and create the full remote file path
            filename = os.path.basename(sourcePath)
            remote_path = destinationPath + filename

            # Get the existing Paramiko SSH client and open SFTP session
            ssh_client = session.console
            sftp = ssh_client.open_sftp()

            # Attempt to upload the file with retries
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    sftp.put(sourcePath, remote_path)
                    break  # Success, exit retry loop
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e  # Final failure, re-raise the exception
                    time.sleep(1)  # Wait and retry

            # Close the SFTP session
            sftp.close()

            return f"SFTP: Copied {sourcePath} to {remote_path}"

        except Exception as e:
            # Return error message in case of failure
            return f"SFTP copy failed: {e}"

    def scpCopy(self, session, sourcePath, destinationPath):
        """
        Copies a file from the host machine to the target device using SCP (for SSH connections).

        Args:
            session (session class): The active session object that contains SSH connection details.
            sourcePath (str): The full path of the file on the host machine.
            destinationPath (str): The target path on the device where the file will be copied.

        Returns:
            str: The message from the subprocess (SCP output).
        """
        if session.type != "ssh":
            self.log.fatal("Session type must be 'ssh'")

        # make sure that the folder is created on the device
        session.write(f"mkdir -p {destinationPath}")

        username = session.username
        destination = "{}@{}:{}".format(username, session.address, destinationPath)

        port = session.port
        # Construct the SCP command with options to disable strict host key checking and known_hosts file
        command = [
            "scp",
            "-P", str(port),
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null",
            "-o", "HostKeyAlgorithms=ssh-rsa,rsa-sha2-512,rsa-sha2-256,ssh-ed25519",
            sourcePath, destination
        ]

        # Execute the SCP command and capture the output
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        message = result.stdout.decode('utf-8').strip()

        return message

    def rsync(self, session, sourcePath, destinationPath):
        """
        Synchronizes files from a local source to a remote destination using rsync over SSH.

        Args:
            session (session class): The active session object that contains SSH connection details.
            sourcePath (str): The full path of the file on the host machine.
            destinationPath (str): The target path on the device where the file will be copied.

        Returns:
            str: The message from the subprocess.
        """
        if session.type != "ssh":
            self.log.fatal("Session type must be 'ssh'")

        session.write("rsync")
        result = session.read_until("rsync")
        message = ""
        if "command not found" in result:
            self.log.error("Target doesn't support rsync, using scp copy to copy the folder")
            for files in os.listdir(sourcePath):
                message += self.scpCopy(session, os.path.join(sourcePath, files), destinationPath)
        else:
            username = session.username
            destination = "{}@{}:{}".format(username, session.address, destinationPath)

            port = session.port
            ssh_options = f"ssh -p {port} -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o HostKeyAlgorithms=ssh-rsa,rsa-sha2-512,rsa-sha2-256,ssh-ed25519"
            # Construct the SCP command with options to disable strict host key checking and known_hosts file
            command = [
                "rsync",
                "-av",
                "-e",
                ssh_options,
                sourcePath, destination
            ]

            # Execute the SCP command and capture the output
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            message = result.stdout.decode('utf-8').strip()

        return message

    def untar(self, session, tar_gz_path, extract_path):
        """
        Untar a .tar.gz file on the remote device via the SSH session.

        Args:
            session (session class): The active SSH session object.
            tar_gz_path (str): Full path of the .tar.gz file on the remote device.
            extract_path (str): Directory on the remote device to extract the files.

        Returns:
            bool: True if successful, False otherwise.
        """

        if session.type != "ssh":
            self.log.fatal("Session type must be 'ssh'")
            return False

        # If tar_gz_path is a list of strings
        if isinstance(tar_gz_path, list):
            tar_gz_path = os.path.normpath(os.path.join(*tar_gz_path))

        # Now safe to use basename
        tar_file_name = os.path.basename(tar_gz_path)

        # You can optionally change directory before untarring
        # e.g., cd to extract_path and untar from there if needed:
        # cmd_untar = f"cd {extract_path} && tar -xzf {tar_gz_path}"
        # But generally, -C {extract_path} is enough.

        # Untar command on the remote device (using full path of tar file)
        cmd_untar = f"tar -xzf {tar_file_name} -C {extract_path}"
        session.write(cmd_untar)

        # Wait for command to complete (adapt prompt accordingly)
        output = session.read_until(session.prompt, timeout=5)
        self.log.info(output)
        # Simple error check
        if "tar:" in output.lower() or "error" in output.lower():
            self.log.error(f"Failed to untar on remote: {output}")
            return False
        else:
            self.log.info(f"Successfully untarred {tar_file_name} on remote to {extract_path}")
            return True

    def change_directory(self, session, directory_path):
        """
        Changes the working directory on the remote device via SSH and verifies the change.

        Args:
            session (session class): The active SSH session object.
            directory_path (str): The path of the directory to change to on the remote device.

        Returns:
            bool: True if successfully changed, False otherwise.
        """
        if session.type != "ssh":
            self.log.fatal("Session type must be 'ssh'")
            return False

        # Combine cd and pwd to verify
        cd_cmd = f"cd {directory_path} && pwd"
        session.write(cd_cmd)
        self.log.info(f"Changing directory on remote to: {directory_path}")

        # Read output to verify current directory
        output = session.read(timeout=5)

        if directory_path.rstrip("/") in output:
            self.log.info(f"Successfully changed to directory: {directory_path}")
            return True
        else:
            self.log.error(f"Failed to change directory. Output:\n{output}")
            return False


# Test and example usage code
if __name__ == '__main__':

    shell = InteractiveShell()

    # Initialize the utBaseUtils class
    test = utBaseUtils()

    # Assuming file.dat is available in current directory
    output = test.scpCopy(shell, "./file.dat", "/tmp")

    print(output)

    # Assuming bin folder is available in current directory
    output = test.rsync(shell, "./bin/", "/tmp")

    print(output)

    shell.close()
