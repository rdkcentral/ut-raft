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

#TODO: Move to raft framework, this module is ideal for local testing

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(dir_path+"/../../../")

from framework.core.commandModules.consoleInterface import consoleInterface

class InteractiveShell(consoleInterface):
    """
    Represents an interactive shell interface. 
    """
    
    def __init__(self):
        """
        Initializes an InteractiveShell by opening a pseudo-terminal.
        """
        # Open a pseudo-terminal
        self.master, self.slave = pty.openpty()
        self.open()

    def open(self):
        """
        Starts the shell process (e.g., bash).
        """
        # Start the shell process (bash)
        self.process = subprocess.Popen(
            ["/bin/bash"],
            stdin=self.slave,
            stdout=self.slave,
            stderr=self.slave,
            text=True
        )
    
    def write(self, command):
        """Sends a command to the shell."""
        os.write(self.master, (command + "\n").encode())

    def read_all(self):
        """Reads all available output from the shell."""
        return self.read_output()

    def read_until(self):
        """
        Reads output from the shell until a specific condition is met. 
        (Implementation not provided in this snippet)
        """
        return self.read_output()

    def read_output(self):
        """Reads the output from the shell."""
        output = os.read(self.master, 1024).decode()
        return output

    def close(self):
        """Closes the shell process."""
        self.process.terminate()
        self.process.wait()

# Create the interactive shell instance
shell = InteractiveShell()

# Send a command
shell.open()
shell.write('echo "Hello, world!"')

# Read and print the output
output = shell.read_output()
print(output)

# send another command and check
shell.write('ls')
output = shell.read_output()
print(output)

# When done, close the shell
shell.close()
