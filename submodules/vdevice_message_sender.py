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
import websocket

class VDeviceMessageSender:
    """
    VDeviceMessageSender class handles sending commands to a virtual device using WebSocket communication.
    """
    def __init__(self, config):
        """
        Initializes the VDeviceMessageSender instance.
        
        Args:
            config (dict): Configuration dictionary containing the command port and supported commands.
        
        Attributes:
            ws_port (int): The WebSocket port for sending commands.
            supported_commands (list): A list of supported commands that can be sent.
        """
        self.ws_port = config['command_port']
        self.supported_commands = config['supported_commands']
        
    def send_command(self, command_data):
        """
        Sends a command to the virtual device via WebSocket.

        Args:
            command_data (dict): Dictionary containing the command details to be sent.

        Raises:
            ValueError: If the command in `command_data` is not in the list of supported commands.
        """
        command = command_data.get('command')
        
        if command not in self.supported_commands:
            raise ValueError(f"Unsupported command: {command}")

        # Connect to the WebSocket and send the command
        # TODO: Upgrade this to extract the data target information from the config passed.
        # The config will specify the IP destination and port to which the device is connected for sending messages.
        ws_url = f"ws://localhost:{self.ws_port}"
        ws = websocket.create_connection(ws_url)
        print(f"Sending vDevice command '{command}' to WebSocket at {ws_url}")
        ws.send(command)
        ws.close()