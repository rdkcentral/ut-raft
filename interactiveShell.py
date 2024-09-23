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
import os
import pty
import subprocess
import sys
import select
import fcntl
import time
import pexpect
import atexit
import re

#TODO: Move to raft framework, this module is ideal for local testing
#TODO: Write data to a file and have a read / write pointer, so the flushing of data is moving the read = write

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(dir_path+"/../../../")

from framework.core.commandModules.consoleInterface import consoleInterface
from framework.core.logModule import logModule

gProcess = None

def InteractiveShellCleanUp():
    if gProcess is not None:
        print("Exiting and terminating shell...")
        gProcess.terminate()
        gProcess.wait()
class InteractiveShell(consoleInterface):
    """
    Represents an interactive shell interface. 
    """
    
    def __init__(self, log:logModule=None):
        """
        Initializes an InteractiveShell by opening a pseudo-terminal.
        """
        # Open a pseudo-terminal
        if log is None:
            self.log = logModule(self.__class__.__name__)
            self.log.setLevel( logModule.INFO )
        self.prompt = r"\$ "
        self.sessionOpen = False

    def open(self):
        """
        Starts the shell process (e.g., bash) using pexpect.
        """
        self.process = pexpect.spawnu('/bin/bash -c "INTERACTIVE_SHELL=1;/bin/bash"')
        gProcess = self.process
        # Register the cleanup function to be called on exit
        atexit.register(InteractiveShellCleanUp)
        self.sessionOpen = True
        result = self.read_until( self.prompt )
        return result
    
    def write(self, command):
        """Sends a command to the shell using pexpect."""
        self.process.sendline(command)  # Use sendline to send commands and include newline
        #self.process.sendline('')   # To flush the data through
        self.log.debug(command)

    def read_until(self, message):
        """
        Reads output from the shell until a specific message is encountered using pexpect.
        """
        max_attempts=2
        output = ""
        intermediate_string = re.sub(r"\\(.)", r"\1", message)
        non_raw_message = intermediate_string.encode('utf-8').decode('unicode_escape')
        for attempt in range(max_attempts):
            try:
                found = self.process.expect(message, timeout=10)  # Wait for the specific message
                data = self.process.before  # This doesn't contain the message
                if isinstance(data, bytes):
                    output = data.decode('utf-8') + non_raw_message  # Decode if it's bytes
                else:
                    output = data + non_raw_message # No need to decode if it's already a string
                self.log.debug("[{}]".format(output))
                break;
            except pexpect.TIMEOUT:
                if attempt == max_attempts - 1:  # Last attempt
                    self.process.before=""
                    return output  # Return an empty string if the message is not found after all attempts
                else:
                    continue  # Continue to the next attempt
            except pexpect.EOF:
                self.log.error("Reached EOF - process has ended")
                self.process.before=""
                return output 

        self.process.before=""
        return output

    def read_all(self):
        """Reads all available output from the shell using pexpect."""
        output = ""
        loop = True
        while loop:
            try:
                found = self.process.expect(pexpect.TIMEOUT, timeout=1)  # Check for data without blocking
                if found == 0:
                    loop = False
            except pexpect.TIMEOUT:
                break  # No more data available
            except pexpect.EOF:
                print("Reached EOF - process has ended")
                break
            else:
                data = self.process.before
                if isinstance(data, bytes):
                    decodeData += data.decode('utf-8')  # Decode if it's bytes
                    self.log.DEBUG(decodeData)
                    output += decodeData
                else:
                    output += data  # No need to decode if it's already a string
                    self.log.debug(data)
        self.process.before=""
        return output

    def close(self):
        """Closes the shell process."""
        self.process.close()  # Use pexpect's close method
        self.sessionOpen = False

if __name__ == '__main__':
    # Create the interactive shell instance
    shell = InteractiveShell()

    # Send a command
    result = shell.open()
    print("result [{}]".format(result))
    shell.write('echo "Hello, world!"')

    # Read and print the output
    output = shell.read_all()
    print(output)

    shell.write('echo "Hello, world!"')
    result = shell.read_until( shell.prompt )
    print( result )

    # send another command and check
    shell.write('ls')
    output = shell.read_all()
    print(output)

    # When done, close the shell
    shell.close()
