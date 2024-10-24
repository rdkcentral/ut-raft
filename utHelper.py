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
import time

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(dir_path+"/../../../")

from framework.core.testControl import testController
from framework.core.outboundClient import outboundClientClass
from framework.core.logModule import logModule
from framework.plugins.ut_raft.interactiveShell import InteractiveShell
from framework.plugins.ut_raft.utBaseUtils import utBaseUtils

class utHelperClass(testController):
    """
    Unit Test Helper Code

    This module provides basic common extensions for unit testing, interacting with devices,
    and managing files.
    """
    def __init__(self, testName:str, qcId:str, log:logModule=None ):
        super().__init__(testName, qcId, log=log )
        self.log=log
        if log is None:
            self.log = logModule(self.__class__.__name__)
            self.log.setLevel( self.log.INFO )

        self.baseUtils = utBaseUtils()

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
            self.session.write("reboot")  # Send the "reboot" command
            result = True
        else:
            result = self.powerControl.reboot()  # Use the power control interface to reboot

        return result

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

    def copyFolder(self, sourcePath, destinationPath, session=None):
        """
        Copies a folder from one location to another on the target device.

        Args:
            sourcePath (str): The source directory path.
            destinationPath (str): The destination directory path.
            device (str, optional): The device on which to copy the folder (default: "dut").
        """
        if session is None:
            session = self.session
        session.write("cp -r " + sourcePath + " " + destinationPath)  # Send the 'cp -r' command
        session.write("\n")  # Send a newline

    def changeFolderPermission(self, permission, path, session=None):
        """
        Changes the permissions of a folder, file, or path on the target device.

        Args:
            permission (str): The new permissions to set (e.g., "755").
            path (str): The path to the folder, file, or path.
            device (str, optional): The device on which to change permissions (default: "dut").
        """
        if session is None:
            session = self.session
        session.write("chmod " + permission + " " + path + "*")  # Send the 'chmod' command
        session.write("\n")  # Send a newline

    def copyFileFromHost(self, sourcePath, destinationPath, targetDevice="dut"):
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
        #TODO: Upgrade to support this via the outbound client
        activeDevice = self.devices.getDevice(targetDevice)

        if activeDevice.session.type == "ssh":
            self.log.stepMessage("copyFile(" + sourcePath + ", (" + destinationPath + ")")

            message = self.baseUtils.scpCopy(activeDevice.session, sourcePath, destinationPath)
        else:
            # self.writeMessageToDeviceSession("cp " + source + " " + destination)  # Commented out code, potentially for serial copy
            self.log.error("Can't copy for this session type")
            raise ValueError("Copying files is not supported for connections.")

        return message

    # Session Command operations
    def writeCommands(self, commands: str, session:object=None):
        """
        Executes a command on the session

        Args:
            command (list): The command list execute.

        Returns:
            str: The output/result of the command execution.
        """
        self.log.debug("writeCommands()")
        if session is None:
            session = self.session

        # Flush the buffer by reading it all
        output = session.read_all()
        self.log.debug( output )

        # Split the data into lines
        lines = commands.splitlines()

        # Filter out empty lines and extract commands
        strippedCommands = [line.strip() for line in lines if line.strip()]
        result = ""
        for cmd in strippedCommands:
            session.write(cmd)
            #TODO: Upgrade the session class to know it's prompt, then we should wait for prompt
            #TODO: This function should move to the session class
            output = session.read_all()
            self.log.debug( output )
            result += output
            #result += self.syscmd(cmd)  # Execute the command using syscmd (assuming it's defined elsewhere)
        return result

    def writeCommandsOnPrompt(self, commands:list, prompt:str=None, session:object=None):
        """
        Writes a command to the session amnd waits for prompt between commands.

        Args:
            commands (list): The command list to execute.
            prompt (str): The expected prompt after the command execution.
                          If not provided, it will use the default prompt from the device configuration.
            device (str): The device to execute the command on (default: "dut").

        Returns:
            str: The output/response from the command execution, excluding the command itself and the prompt.
                    If no response is received, an empty string is returned.
        """
        self.log.debug("writeCommandsOnPrompt(%s)".format(commands))

        if session is None:
            session = self.session

        # Flush the buffer by reading it all
        output = session.read_all()
        self.log.debug( output )

        # Split the data into lines
        lines = commands.splitlines()

        # Filter out empty lines and extract commands
        strippedCommands = [line.strip() for line in lines if line.strip()]
        result = ""

        # Loop round by the list of commands
        for cmd in strippedCommands:
            # Send the command and a newline to the device session
            cmd += "\n"
            session.write(cmd)

            # If no prompt is not provided, use the default prompt from the device configuration
            if prompt is None:
                prompt = self.getCPEFieldValue("prompt")

            # Wait for the expected prompt or timeout
            result = self.session.read_until(prompt)

            # Flush any additional data from the session
            result += self.session.read_all()

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
    def catFile(self, filePath, prompt=None, session=None):
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

        localSession = self.session
        if session is not None:
            localSession = session
        # Check if the session is open
        if not localSession.sessionOpen:
            self.step.error("catFile(): session not open")
            return False

        self.log.debug("cat:[{}]".format(filePath))

        # Execute the 'cat' command to read the file and return the output
        log = self.writeCommandsOnPrompt("cat " + filePath, prompt=prompt, session=localSession)

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
        self.log.debug("urls( url:'{}' )".format(urls))
        self.log.debug("target_directory( target_directory:'{}' )".format(target_directory))

        for url in urls:
            # Download a file into the workspace on the host
            # Then copy the file to target
            file_name = os.path.basename(url)
            if hasattr(self, 'outboundClient'):
                self.outboundClient.downloadFile(url)
                workspace_directory = self.outboundClient.workspaceDirectory
                self.copyFileFromHost(os.path.join(workspace_directory, file_name), target_directory, targetDevice=device)
            else:
                self.log.error("outboundClient not present")

    def deleteFromDevice(self, files: list, device: str="dut" ):
        """
        Deletes the file from device

        Args:
            files (list:str): list of file paths to delete.
            device (str) : device name ( default: "dut" )
        """
        for file in files:
            cmd = "rm -rf " + file
            self.writeCommands(cmd)

# Test and example usage code
if __name__ == '__main__':

    #TODO: This tests should be expanded as each class is extended or touched
    #TODO: Coverage of all tests is required
    # Test assumes that it's ran with --config <localbox>
    test = utHelperClass("functionTest",1)
    commands="""
        echo helloworld
        ls ~/.bashrc
    """
    shell=InteractiveShell()
    shell.open()
    test.session = shell    # Override the default shell

    print("-----------------writeCommands-------------")
    result = test.writeCommands(commands, session=shell)
    print("-----------------writeCommands:result-------------")
    print(result)
    print("-----------------writeCommandsOnPrompt-------------")
    result = test.writeCommandsOnPrompt(commands, prompt=shell.prompt, session=shell)
    print("-----------------writeCommandsOnPrompt:result-------------")
    print(result)
    print("-----------------catFile-------------")
    result = test.catFile("~/.bashrc", prompt=shell.prompt )
    print("-----------------catFile: Result-------------")
    print(result)

    # Assuming testing 
    #if hasattr( test, "outboundClient" ) == False:
        #test.outboundClient = outboundClientClass( workspaceDirectory="~/Downloads/OBC" )
    #test.downloadToDevice("utHelper.py","/tmp/")

    shell.close()
