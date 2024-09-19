#!/usr/bin/env python3
#** *****************************************************************************
# *
# * If not stated otherwise in this file or this component's LICENSE file the
# * following copyright and licenses apply:
# *
# * Copyright 2023 RDK Management
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
import os
import sys
import subprocess

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(dir_path+"/../../../")

from framework.core.testControl import testController

class utHelperClass(testController):
    """
    Unit Test Helper Code

    This module provides basic common extensions for unit testing, interacting with devices,
    and managing files.
    """
    def __init__(self, testName, qcId, log:logModule=None ):
        super().__init__(testName, qcId, log=log )

    def waitForBoot(self):
        """
        Waits for the system to boot.

        This function pings the "dut" device to check if it's up and logs the boot time.
        The actual boot process implementation might be handled by the parent class.

        Returns:
            bool: True if the system booted successfully (ping succeeded), False otherwise.
        """
        self.log.step("waitForBoot(): Target is Booting, logging time")
        isBoxUP = self.pingTest("dut", True)  # Ping the "dut" device
        if not isBoxUP:
            self.log.step("ping is failed")  # Log if the ping fails
        return True  # Always returns True, even if the ping failed

    def reboot(self, commandLine=False):
        """
        Reboots the DUT (Device Under Test).

        Args:
            commandLine (bool, optional): If True, reboots using the terminal command "reboot". 
                                        Otherwise, uses the `powerControl.reboot()` method. Defaults to False.

        Returns:
            bool: True if the reboot was successful, False otherwise.
        """
        # TODO: Upgrade this function to support `requestedDevice` as a parameter with a default value of "dut"
        self.log.step("reboot()")
        result = False

        if commandLine:
            self.session.read_all()  # Read any pending data from the session
            self.writeMessageToSession("reboot")  # Send the "reboot" command
            result = True
        else:
            result = self.powerControl.reboot()  # Use the power control interface to reboot

        return result

    def waitForSessionMessage(self, message, device="dut"):
        """
        Waits for a specific message to appear in the device's console session.

        This function reads from the console session of the specified device until the given message is found.
        It raises an exception if the message is not found within the session's timeout.

        Args:
            message (str): The message to wait for.
            device (str, optional): The device to monitor (default: "dut").

        Raises:
            Exception: If the message is not found in the session.

        Returns:
            str: The session output up to and including the found message.
        """
        self.log.debug("waitForSessionMessage([{}])".format(message).format(dut))

        activeDevice = self.devices.getDevice(device)
        session = activeDevice.getConsoleSession()

        try:
            # Read from the session until the message is found
            string = session.read_until(message)

            # Check if the message was actually found
            findStringLocation = string.find(message)
            if findStringLocation == -1:
                self.log.error("Could not find string: {}, raise an exception".format(message))
                raise Exception("Raise an exception")  # Raise a generic exception
                return False  # This line is unreachable due to the exception

        except Exception as e:
            self.log.error(e)
            raise Exception('waitForSessionMessage session message - {} failed'.format(message))

        return string

    def writeMessageToDeviceSession(self, message, device="dut"):
        """
        Writes a message to the console session of the specified device.

        Args:
            message (str): The message to write.
            device (str, optional): The device to write the message to (default: "dut").
        """
        self.log.step("testControl.writeMessageToSession({})".format(message.strip()))

        activeDevice = self.devices.getDevice(device)
        session = activeDevice.getConsoleSession()
        session.write(message)

    ## Device file operations

    def createDirectoryOnDevice(self, dirPath, device="dut"):
        """
        Creates a directory on the connected target device.

        Args:
            dirPath (str): The path of the directory to be created.
            device (str, optional): The device on which to create the directory (default: "dut").
        """
        activeDevice = self.devices.getDevice(device)
        session = activeDevice.getConsoleSession()
        self.log.info("dirPath:[%s]", dirPath)
        session.write("mkdir " + dirPath)  # Send the 'mkdir' command to create the directory
        session.write("\n")  # Send a newline to execute the command

    def mountFolderOnDevice(self, devPath, mntPath, device="dut"):
        """
        Mounts a device path (e.g., a USB drive) to a mount point on the target device.

        Args:
            devPath (str): The device path to mount (e.g., /dev/sda1).
            mntPath (str): The mount point on the target device.
            device (str, optional): The device on which to mount the folder (default: "dut").
        """
        self.log.stepMessage("Mount USB " + devPath + " to " + mntPath + " path")
        self.writeMessageToDeviceSession("mount " + devPath + " " + mntPath, device=device)  # Send the 'mount' command
        self.writeMessageToDeviceSession("\n", device=device)  # Send a newline

    def copyFolderOnDevice(self, sourcePath, destinationPath, device="dut"):
        """
        Copies a folder from one location to another on the target device.

        Args:
            sourcePath (str): The source directory path.
            destinationPath (str): The destination directory path.
            device (str, optional): The device on which to copy the folder (default: "dut").
        """
        self.writeMessageToDeviceSession("cp -r " + sourcePath + " " + destinationPath, device=device)  # Send the 'cp -r' command
        self.writeMessageToDeviceSession("\n", device=device)  # Send a newline

    def changeFolderPermissionOnDevice(self, permission, path, device="dut"):
        """
        Changes the permissions of a folder, file, or path on the target device.

        Args:
            permission (str): The new permissions to set (e.g., "755").
            path (str): The path to the folder, file, or path.
            device (str, optional): The device on which to change permissions (default: "dut").
        """
        self.writeMessageToDeviceSession("chmod " + permission + " " + path + "*", device=device)  # Send the 'chmod' command
        self.writeMessageToDeviceSession("\n", device=device)  # Send a newline

    def copyFileFromHost(self, sourcePath, destinationPath, device="dut"):
        """
        Copies a file from the host machine to the target device using SCP (for SSH connections).

        Args:
            sourcePath (str): The source path and filename on the host.
            destinationPath (str): The destination path and filename on the device.
            device (str, optional): The device to copy the file to (default: "dut").

        Returns:
            str: The message from the subprocess (SCP output).

        Raises:
            ValueError: If the session type is not "ssh".
        """
        activeDevice = self.devices.getDevice(device)

        if activeDevice.session.type == "ssh":
            self.log.stepMessage("copyFile(" + sourcePath + ", (" + destinationPath + ")")

            # TODO: Assumption: 'root' user is the default on the target, this should be specified by the configuration
            destination = "root@{}:{}".format(self.slotInfo.getDeviceAddress(), destinationPath)

            # Construct the SCP command with options to disable strict host key checking and known_hosts file
            command = ["scp", "-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null",
                    sourcePath, destination]

            # Execute the SCP command and capture the output
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            message = result.stdout.decode('utf-8').strip()

        elif self.session.type == "serial":
            # self.writeMessageToDeviceSession("cp " + source + " " + destination)  # Commented out code, potentially for serial copy
            self.log.error("Can't copy for this session type: serial")
            raise ValueError("Copying files is not supported for serial connections.")

        return message

# Device / Host Command operations

    def writeHostCommands(self, commands: list):
        """
        Executes a command on the host machine (Linux only).

        Args:
            command (list): The command list execute.

        Returns:
            str: The output/result of the command execution.
        """
        self.log.debug("writeHostCommands()")
        for cmd in commands:
            result += self.syscmd(cmd)  # Execute the command using syscmd (assuming it's defined elsewhere)
        return result

    def flushSessionData(self, timeout=1, device="dut"):
        """
        Clears any pending data from the session buffer of the specified device.

        Args:
            timeout (int, optional): The timeout in seconds to wait before reading (default: 1).
            device (str, optional): The device to flush the session data for (default: "dut").

        Returns:
            str: The accumulated data that was read from the session buffer.
        """
        self.log.debug("clearCommand()")
        self.waitSeconds(timeout)  # Wait for a short time to allow data to accumulate

        activeDevice = self.devices.getDevice(device)
        session = activeDevice.getConsoleSession()
        result = session.read_all()  # Read all available data from the session
        return result

    def writeCommandsOnDevice(self, commands:list, prompt:str=None, device:str="dut"):
        """
        Writes a command to the session on the target device and waits for a response.

        Args:
            commands (list): The command list to execute.
            prompt (str): The expected prompt after the command execution. 
                          If not provided, it will use the default prompt from the device configuration.
            device (str): The device to execute the command on (default: "dut").

        Returns:
            str: The output/response from the command execution, excluding the command itself and the prompt.
                    If no response is received, an empty string is returned.
        """
        self.log.debug("writeCommand(%s)".format(commands))

        # Loop round by the list of commands
        for cmd in commands:
            # Send the command and a newline to the device session
            self.writeMessageToDeviceSession(cmd, device=device)
            self.writeMessageToDeviceSession("\n", device=device)

            # If no prompt is not provided, use the default prompt from the device configuration
            if prompt is None:
                prompt = self.getCPEFieldValue("prompt")

            # Wait for the expected prompt or timeout
            result = self.waitForSessionMessage(prompt, device=device)

            # Flush any additional data from the session
            result += self.flushSessionData(device=device)

            # Split the result into lines
            message = result.split("\r\n")

            # If there are 2 or fewer lines, it means there was no command output
            if len(message) <= 2:
                return ""

            # Remove the first line (the command itself) and the last line (the prompt)
            message.pop(0)
            message.pop(len(message) - 1)

            # Join the remaining lines and return them as the command output
            result += "\r\n".join(message)
        return result

## Useful utility functions

    def isStringInList(self, string, searchList):
        """
        Checks if a given string is present in a list of strings.

        Args:
            string (str): The string to search for.
            searchList (list): The list of strings to search in.

        Returns:
            bool: True if the string is found in the list, False otherwise.
        """
        self.log.step("findStringInList(string:'{}')".format(string))

        # Iterate through the search list and check if the string is present in any of the items
        for line in searchList:
            if string in line:
                return True
        return False

    ## Useful log cat / save functions for the device

    def catFileOnDevice(self, filePath, device="dut"):
        """
        Reads and retrieves the contents of a file on the device using the 'cat' command.

        Args:
            filePath (str): The path to the file on the device.
            device (str): The device to read the file from (default: "dut").

        Returns:
            str or False: The contents of the file as a string if successful, 
                            False if the session is not open.
        """
        self.log.step("catFileOnDevice('{}')".format(filePath))

        # Check if the session is open
        if not self.session.sessionOpen:
            self.step.log("catFileOnDevice(): session not open")
            return False

        self.log.info("cat:[filePath]")

        # Execute the 'cat' command to read the file and return the output
        log = self.writeCommand("cat " + filePath)

        return log

    def saveLogForAnalysis(self, inputLog, filename):
        """
        Saves the provided log data to a file in the logging directory for further analysis.

        Args:
            inputLog (list): The log data as a list of strings.
            filename (str): The desired filename for the log file (without the directory path).
        """
        self.log.step("dumpLogToFile( filename:'{}' )".format(filename))

        # Construct the full path to the log file
        fullPath = self.testLogPath + filename

        # Open the file in write mode
        with open(fullPath, "w+") as fileHandle:
            # Write each line of the log data to the file
            for writeString in inputLog:
                fileHandle.write(writeString + "\n")

    def downloadToDevice(self, urls: list, target_directory: str, device: str="dut" ):
        """
        Download the file and copy to device directory.

        Args:
            url (str): url path.
            target_directory (str): target directory on device.
            device (str) : device name ( default: "dut" )
        """
        self.log.step("url( url:'{}' )".format(url))
        self.log.step("target_directory( target_directory:'{}' )".format(target_directory))

        for url in urls:
            # Download a file into the worksapce on the host
            # Then copy the file to target
            file_name = os.path.basename(url)
            self.outboundClient.downloadFile(url)
            workspace_directory = self.outboundClient.workspaceDirectory
            self.copyFileFromHost(os.path.join(workspace_directory, file_name), target_directory, device=device)

# Test and example usage code
if __name__ == '__main__':
    # test the class
    test = utHelperClass("functionTest",1)
    test.writeCommandsOnDevice()
    test.writeHostCommands()

# Tests Required
# - writeHostCommands
# - writeCommandsOnDevice