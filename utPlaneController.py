#!/usr/bin/env python3
#** *****************************************************************************
# *
# * If not stated otherwise in this file or this component's LICENSE file the
# * following copyright and licenses apply:
# *
# * Copyright 2025 RDK Management
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
import time
import re

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(dir_path)
sys.path.append(dir_path+"/../../../")

from framework.core.logModule import logModule
from framework.plugins.ut_raft.interactiveShell import InteractiveShell

class utPlaneController():
    """
    UT Plane Controller class for managing communication with the ut-controller.

    This class provides an interface to interact with the ut-controller running on a device.
    It facilitates sending commands and YAML configuration files to the controller via HTTP requests
    using curl commands. The controller operates over a configurable port (default: 8080) and uses
    the session object to execute commands on the target device.

    Typical usage involves:
    1. Creating an instance with an active session and optional port/log configuration
    2. Preparing YAML files with test commands or configuration
    3. Sending these files to the ut-controller using sendMessage()

    Attributes:
        session (object): Active session object for device communication
        port (int): Port number where ut-controller service is listening (default: 8080)
        log (logModule): Logger instance for recording controller activities and debugging

    Example:
        >>> controller = utPlaneController(session, port=8080)
        >>> controller.sendMessage("/path/on/dut/to/test_config.yaml")
    """

    def __init__(self, session:object, port: int = 8080, log:logModule=None):
        """
        Initializes UT Plane Controller class.

        Args:
            session (class): The session object to communicate with the device
            port (int): The port number for the controller
            log (class, optional): Parent log class. Defaults to None.
        """
        self.log = log
        if log is None:
            self.log = logModule(self.__class__.__name__)
            self.log.setLevel( self.log.INFO )

        self.session = session
        self.port = port

    def sendMessage(self, yamlString: str) -> None:
        """
        Sends a command to the ut-controller via curl.

        Args:
            yamlString (str): YAML string containing the command.

        Returns:
            None.
        """

        # Prepare the curl command
        cmd = f'curl -X POST -H "Content-Type: application/x-yaml" --data-binary "{yamlString}" "http://localhost:{self.port}/api/postKVP"'

        self.session.write(cmd)

        return None

    if __name__ == '__main__':
        """
        Example main function demonstrating usage of utPlaneController class.

        This example shows how to:
        1. Create a interactive session object for testing
        2. Initialize the utPlaneController
        3. Send a YAML configuration file to the ut-controller
        """

        shell = InteractiveShell()

        # Initialize the controller with default port 8080
        controller = utPlaneController(session=shell, port=8080)

        # Example: Send a YAML file to the ut-controller
        yaml_file_path = "/tmp/test_config.yaml"

        '''
        This is a sample YAML configuration for testing.
        HdmiCec:
            command: print
            description: Print the current HDMI CEC device map
        '''

        print(f"Sending YAML file to ut-controller: {yaml_file_path}")
        controller.sendMessage(yaml_file_path)

        print("\nExample completed successfully!")

        shell.close()