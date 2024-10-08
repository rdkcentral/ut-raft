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

from framework.core.logModule import logModule

class utUserResponse():
    """Reads the user response
    """
    
    def __init__(self, log:logModule=None):
        """
        Initializes a configuration reader instance based on the parameters.

        Args:
            device (str)
            log (class, optional): Parent log class. Defaults to None.
        """
        self.log = log
        if log is None:
            self.log = logModule(self.__class__.__name__)
            self.log.setLevel( self.log.INFO )

    def getUserYN(self, query="Please Enter Y or N :"):
        """
        Reads Y/N user response to the query.

        Args:
            query (str, optional): Query to the user. Defaults to ""

        Returns:
            bool: returns the response
        """

        if self.log is not None:
            self.log.debug(query)
        response = input(query)

        if response == 'y' or response == 'Y' :
            return True
        else :
            return False

# Test and example usage code
if __name__ == '__main__':
    # Test the module
    prompt = utUserResponse()
    result = prompt.getUserYN()
    print( "result:[{}]".format(result))

    result = prompt.getUserYN("Please Enter Stuff: ")
    print( "result:[{}]".format(result))

