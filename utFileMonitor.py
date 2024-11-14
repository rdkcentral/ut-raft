import sys
import os
import re
import time
import threading

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(dir_path+"/../../../")
sys.path.append(dir_path)

from framework.core.logModule import logModule
from framework.core.commandModules.consoleInterface import consoleInterface
from interactiveShell import InteractiveShell

class utFileMonitor:
    """This Class monitors the log files. If there are any new lines added to the file, then reports back
    """
    def __init__(self, session:consoleInterface, callbackFile:str, callbackFunction = None, prompt:str=":", log:logModule = None):
        """init function

        Args:
            session (consoleInterface): console interface to operate on
            callbackFile (str) : Log file to be monitored
            callbackFunction : callback function
            prompt (str): prompt to wait on
            log (logModule): log module
        """
        self.session = session
        self.log=log
        if log is None:
            self.log = logModule(self.__class__.__name__)
            self.log.setLevel( self.log.DEBUG )
        self.prompt = prompt
        self.callbackFunction = callbackFunction
        self.exitThread = False
        self.thread = threading.Thread(target=self.monitorFile, args=(callbackFile,))
    
    def monitorFile(self, filePath:str):
        """Thread function

        Args:
            filePath (str): Log file to be monitored
        """
        initial_file_size = 0
        current_file_size = 0
        self.session.write("")
        out = self.session.read_until(self.prompt)
        while self.exitThread == False:
            self.session.write(f"stat -c '%s' {filePath}")
            out = self.session.read_until(self.prompt)
            if("No such file or directory" in out):
                time.sleep(0.1)
                continue

            msg =  out.split("\r\n")
            if(len(msg) >= 2):
                msg.pop(0)
                msg.pop(len(msg) - 1)
            if(msg[0].isdigit()):
                current_file_size = int(msg[0])

            if current_file_size != initial_file_size :
                self.session.write(f"tail -c +{initial_file_size + 1} {filePath}")
                out = self.session.read_until(self.prompt)
                msg =  out.split("\r\n")
                if(len(msg) >= 2):
                    msg.pop(0)
                    msg.pop(len(msg) - 1)
                self.callbackFunction("\r\n".join(msg))
                initial_file_size = current_file_size
            time.sleep(0.1)

    def start(self):
        """
        Starts the thread.
        """
        self.thread.start()

    def join(self):
        """
        Waits for the thread to finish.
        """
        self.thread.join()

    def stop(self):
        """
        Stops the thread
        """
        self.exitThread = True

    def __del__(self):
        self.thread.join()

def testCallback(msg:str):
    print(msg)

# Test and example usage code
if __name__ == '__main__':

    # test the class
    shell = InteractiveShell()
    result = shell.open()
    print("Shell:[{}]".format(result))

    # Create file monitor object (assuming monitor file /opt/callback.txt)
    test = utFileMonitor(shell, "/opt/callback.txt", testCallback)

    # Start the monitor
    test.start()

    # Monitor for 5 sec. If there any updates to the file testCallback should print the message
    time.sleep(5)

    # Stop the monitor
    test.start()

    del test

    shell.close()