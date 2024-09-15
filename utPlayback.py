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
import sys
import subprocess

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(dir_path+"/../../../")

class utPlaybackOnDevice():
    """
    UT Player class

    """
    def __init__(self, session, playbackTool="gstreamer", prerequisites="", log=None):
        """
        Initializes player class.

        Args:
            session (class): The console session object to communicate with the device
            playbackTool (str, optional): Player tool to play the streams. Defaults to "gstreamer".
            prerequisites (str, optional): Prerequisites commands required for player. Defaults to "".
            log (class, optional): Parent log class. Defaults to None.
        """
        self.log = log
        self.playbackTool = playbackTool
        self.session = session

        if prerequisites is not None:
            for cmd in prerequisites:
                self.session.write(cmd)
    
    def utStartPlay(self, streamOnDevice):
        """
        Starts the playback.

        Args:
            streamOnDevice (str): Stream path.
        """
        if (self.playbackTool == "gstreamer"):
            cmd = "gst-play" + " " + streamOnDevice
            self.session.write(cmd)

    def utStopPlay(self):
        """
        Stops the playback.

        Args:
            None.
        """
        if (self.playbackTool == "gstreamer"):
            self.session.write("q")

    


