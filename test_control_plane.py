# check if control messages route to the correct submodule

import sys
from os import path
from control_plane import ControlPlane
from configRead import ConfigRead


MY_PATH = path.abspath(__file__)
MY_DIR = path.dirname(MY_PATH)
sys.path.append("/home/FKC01/ut_raft")

if __name__ == "__main__":
    try:
        # load config and initialise control plane
        config = ConfigRead('/home/FKC01/ut-raft/config.yaml')        
        control_plane = ControlPlane(config_path='/home/FKC01/ut-raft/config.yaml')

        # Example message for IR Blaster command
        message_yaml_ir = """
        irblaster:
          command: PowerOn
          target_device: TV
          code: "001"
        """
        print("Testing IR Blaster Command:")
        control_plane.process_message(message_yaml_ir)

        # Example message for HDMI command
        message_yaml_hdmi = """
        hdmicec:
          command: ImageViewOn
        """
        print("Testing HDMI Command:")
        control_plane.process_message(message_yaml_hdmi)

    except Exception as e:
        print(f"An error occurred: {e}")