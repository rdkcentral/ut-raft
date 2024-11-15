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

class IR:
    """
    Handles processing and executing IR (Infrared) commands.
    It simulates or interfaces with an IR blaster to send commands based on the provided parameters.
    """
    def __init__(self):
        """
        Initializes the IR handler.
        
        Attributes:
            message (dict): Stores the last processed message.
        """
        print("IR handler initialized.")
        self.message = None

    def process_command(self, message):
        """
        Processes a given message to extract and handle IR-specific commands.

        Args:
            message (dict): The message data that includes the command details.
        """
        self.message = message.get("IR")

        # Extract the relevant command information
        if self.message is not None:
            command = self.message.get('command')
            delay = self.message.get('delay', 1)
            repeat = self.message.get('repeat', 1)

            print(f"IR handling command: '{command}'")
            print(f"  Delay: {delay}")
            print(f"  Repeat: {repeat}")

            # Implement IR command logic here
            self.send_ir_signal(command, delay, repeat)
        else:
            print("No valid command found in the message.")

    def send_ir_signal(self, command, delay, repeat):
        """
        Simulates sending an IR signal with the specified parameters.

        Args:
            command (str): The command to be sent.
            delay (int): Delay between repeats in seconds.
            repeat (int): Number of times to repeat the command.
        """
        print(f"Sending IR signal '{command}' with delay {delay} seconds, repeated {repeat} times.")
        for i in range(repeat):
            print(f"Sending '{command}' (repeat {i + 1})")
            # Simulate a delay between sending commands
            import time
            time.sleep(delay)