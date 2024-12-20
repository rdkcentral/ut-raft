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

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(dir_path+"/../../../../")
sys.path.append(dir_path+"/../")

from framework.core.commonRemote import commonRemoteClass
from framework.core.logModule import logModule

from configRead import ConfigRead

class remoteEventHandler:
    """
    Handles the processing and execution of remote control commands. 

    This class interacts with the `commonRemoteClass` to send key events 
    to a configured remote control device or simulate remote control actions.

    For details on the supported message format, see:
    https://github.com/rdkcentral/ut-raft/wiki/Control-Plane-Message-Format
    """
    def __init__(self, remoteInstance:commonRemoteClass, log:logModule=None):
        """
        Initializes the remote event handler.

        Args:
            remoteInstance (commonRemoteClass): An instance of the `commonRemoteClass` 
                                                for interacting with the remote control.
            log (logModule, optional): An optional logger instance. If None, a new logger 
                                        will be created. Defaults to None.
        """
        self.remoteInstance = remoteInstance
        self.log = log
        if log is None:
            self.log = logModule("remoteEventHandler")
   
    def process_message(self, inputMessage:ConfigRead):
        """
        Processes a message to extract and execute remote control commands.

        The expected message format is a list of event objects:

        ```yaml
        remote:
          - event: 
              map: "rc6"      # Optional: Remote key map to use
              key: "KEY_ENTER" # Key to be pressed
              delay: 2        # Optional: Delay in seconds (defaults to 0)
              repeat: 3       # Optional: Number of repetitions (defaults to 1)
          - event:
              # ... another event object
        ```

        Args:
            inputMessage (ConfigRead): The message data containing the remote control commands.
        """
        eventMessage = ConfigRead( inputMessage )
        events = eventMessage.get("remote")
        if events is None:
            self.log.debug("remoteEventHandler: No Action")
            return

        self.log.info("{}".format(eventMessage))

        events = eventMessage.get("remote")

        for event_obj in events.items():
            event = event_obj.get("event")
            key_map = event.get("map", None)
            key = event.get("key")
            delay = event.get("delay", 0)
            repeat = event.get("repeat", 1)

            if key_map is not None:
                self.remoteInstance.setKeyMap(key_map)

            self.remoteInstance.sendKey( key, delay, repeat )


if __name__ == "__main__":
        
    remoteMessage = {
        "remote": [
            {"event": {"key": "KEY_ENTER"}},
            {"event": {"key": "KEY_UP", "delay": 1}},
            {"event": {"key": "KEY_DOWN", "repeat": 3}}
        ]
    }
    config = {
        "remoteController": {
            "type": "None" 
        }
    }

    remoteMessage2 = """
        remote:
            map: "rc6"
            - event: 
                key: "KEY_ENTER" 
            - event:
                key: "KEY_UP"
                delay: 1
            - event:
                key: "KEY_DOWN"
                repeat: 3
    """

    log = logModule("remoteHandler")

    remoteClass = commonRemoteClass(log, config)
    handler = remoteEventHandler( remoteClass, log )

    log.info("Testing remoteCommand:") 
    handler.process_message( remoteMessage )