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
            self.log.error("Session type must be 'ssh' to use SCP")
            return None

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

# Test and example usage code
if __name__ == '__main__':

    shell = InteractiveShell()

    # Initialize the utBaseUtils class
    test = utBaseUtils()

    output = test.scpCopy(shell, "/path/to/source/file", "/path/on/target/device")

    print(output)

    shell.close()
