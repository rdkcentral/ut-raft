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
from enum import Enum

# Helper always exist in the same directory under raft and can use it for confirmation testing
dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(dir_path+"/../../../")

from framework.core.logModule import logModule
from framework.plugins.ut_raft.interactiveShell import InteractiveShell
from framework.plugins.ut_raft.configRead import ConfigRead

class MixerInputTypes(Enum):
    MIXER_INPUT_PRIMARY     = 1
    MIXER_INPUT_SECONDARY   = 2

class utPlayer():
    """
    UT Player class
    """

    def __init__(self, session:object, vendor:str, log:logModule=None):
        """
        Initializes player class.

        Args:
            session (class): The session object to communicate with the device
            vendor (str): vendor name
            log (class, optional): Parent log class. Defaults to None.
        """
        self.log = log
        if log is None:
            self.log = logModule(self.__class__.__name__)
            self.log.setLevel( self.log.INFO )

        self.session = session

        configPath = os.path.join(dir_path, "configs/utPlayerConfig.yml")
        self.playerProfile = ConfigRead(configPath, vendor)
        if self.playerProfile is None:
            self.log.fatal("Profile not found[{}]".format(configPath))

        self.player = self.playerProfile.gstreamer

        if self.player.prerequisites:
            for cmd in self.player.prerequisites:
                self.session.write(cmd)

        self.setMixerInput(MixerInputTypes.MIXER_INPUT_PRIMARY)

    def setMixerInput(self, mixer_input:MixerInputTypes):
        if mixer_input == MixerInputTypes.MIXER_INPUT_PRIMARY:
            self.mixerInputConfiguration = self.player.primary_mixer_input_config
        elif mixer_input == MixerInputTypes.MIXER_INPUT_SECONDARY:
            self.mixerInputConfiguration = self.player.secondary_mixer_input_config

        if not self.mixerInputConfiguration:
            self.mixerInputConfiguration = ""

    def play(self, streamFile:str):
        """
        Starts the playback of a stream
        Once started the stream is assumed to be blocking on the device.
        Unless an error occurs, it will remain running

        Args:
            stream (str): Stream path.
        """
        #TODO: Upgrade if required or a new function to playback from a URL
        # Example usage for gst-launch `gst-launch-1.0 filesrc location=/home/yourusername/myvideo.mp4 ! decodebin ! autovideosink`
        # Example usage for gst-play `gst-play-1.0 <file_path>`

        cmd = self.player.play_command + " " + self.mixerInputConfiguration + " " + streamFile
        self.session.write(cmd)

    def stop(self):
        """
        Stops the playback of a stream

        Args:
            None
        """
        self.session.write(self.player.stop_command)

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

