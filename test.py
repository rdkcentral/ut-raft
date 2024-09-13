#!/usr/bin/env python3

import sys
from os import path

MY_PATH = path.abspath(__file__)
MY_DIR = path.dirname(MY_PATH)
sys.path.append("/home/FKC01/python_raft")


from framework.core.commandModules.sshConsole import sshConsole
from ut_core import UTCoreMenuNavigator

if __name__ == "__main__":
    CONSOLE = sshConsole("localhost", "FKC01", "", port = 22)
    CONSOLE.open()

    UT = UTCoreMenuNavigator("/home/FKC01/ut-raft/ut_menu.yml", CONSOLE)

