#!/usr/bin/env python3

import sys
from os import path

MY_PATH = path.abspath(__file__)
MY_DIR = path.dirname(MY_PATH)
sys.path.append("/home/FKC01/python_raft")


from framework.core.commandModules.sshConsole import sshConsole
from ut_core import UTCoreMenuNavigator

if __name__ == "__main__":
    
    try:
        CONSOLE = sshConsole("localhost", "FKC01", "", port = 22)
        CONSOLE.open()
        CONSOLE.open_interactive_shell()


        UT = UTCoreMenuNavigator("/home/FKC01/ut-raft/ut_menu.yml", CONSOLE)

        # Run a specific test
        test_passed = UT.run_test('L1 plat_power', 'PLAT_INIT_L1_positive')

        if test_passed:
            print("Test executed and passed.")
        else:
            print("Test execution failed.")
        
        # Close the SSH connection
        CONSOLE.close()
    
    except Exception as e:  
        CONSOLE.close()
        print(e)
