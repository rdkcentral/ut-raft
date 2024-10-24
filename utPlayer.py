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
import time

# Helper always exist in the same directory under raft and can use it for confirmation testing
dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(dir_path+"/../../../")

from framework.core.logModule import logModule
from framework.plugins.ut_raft.interactiveShell import InteractiveShell
from framework.plugins.ut_raft.configRead import ConfigRead

class utPlayer():
    """
    UT Player class
    """
    playerConfig = os.path.join(dir_path, "uPlayerConfig.yml")

    def __init__(self, session:object, platform:str, player:str = "gstreaner", log:logModule=None):
        """
        Initializes player class.

        Args:
            session (class): The session object to communicate with the device
            platform (str): Platfrom name
            player (str, optional) : Player to use. Defaults to gstreamer
            log (class, optional): Parent log class. Defaults to None.
        """
        self.log = log
        if log is None:
            self.log = logModule(self.__class__.__name__)
            self.log.setLevel( self.log.INFO )
        self.session = session
        self.playerProfile = ConfigRead(self.playerConfig, platform)
        self.player = self.playerProfile.get(player)

        if self.player.get("prerequisites"):
            for cmd in self.player.get("prerequisites"):
                self.session.write(cmd)

    def play(self, streamFile:str, mixer_input:str = "primary"):
        """
        Starts the playback of a stream
        Once started the stream is assumed to be blocking on the device.
        Unless an error occurs, it will remain running

        Args:
            stream (str): Stream path.
            mixer_input (str, optional): Mixer input to which audio output should be connected. Defaults to "primary"
        """
        #TODO: Upgrade if required or a new function to playback from a URL
        # Example usage for gst-launch `gst-launch-1.0 filesrc location=/home/yourusername/myvideo.mp4 ! decodebin ! autovideosink`
        # Example usage for gst-play `gst-play-1.0 <file_path>`

        if mixer_input == "primary":
            cmd = self.player.get("play_command")
            if not cmd:
                self.log.error("Player command not found")
                return
            cmd += " " + streamFile
        elif mixer_input == "secondary":
            cmd = self.player.get("secondary_play_command")
            if not cmd:
                self.log.error("Secondary Player command not found")
                return
            cmd += " " + streamFile

        self.session.write(cmd)

    def stop(self):
        """
        Stops the playback of a stream

        Args:
            None
        """
        cmd = self.player.get("stop_command")
        if not cmd:
            self.log.error("Stop Player command not found")
            return

        self.session.write(cmd)

# Test and example usage code
if __name__ == '__main__':

    # utPlayerClass()
      # gStreamPlayerClass()
      # QTPlayerClass()
      # FFPMEGPlayerClass()

    # Assumes that the asset is already transfer to /tmp
    # test the class
    shell = InteractiveShell()

    test = utPlayer(shell, "element", "gstreamer")
    test.play("/tmp/audioTest.mp3")

    # Read and print the output
    output = shell.read_output()
    print(output)

    test.stop()

    # Read and print the output
    output = shell.read_output()
    print(output)

    shell.close()

