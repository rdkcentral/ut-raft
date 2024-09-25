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

import yaml
import sys
import os
import re
import time

# Helper always exist in the same directory under raft
dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(dir_path+"/../../../")
sys.path.append(dir_path)

from framework.core.logModule import logModule
from framework.core.commandModules.consoleInterface import consoleInterface
from interactiveShell import InteractiveShell
from configRead import ConfigRead

class utCFramework:
    """This module supports the selection of C Type tests
    """

    def __init__(self, session:consoleInterface, log:logModule = None):
        """init function

        Args:
            session (consoleInterface): console interface to operate on
        """
        self.prompt=": "
        self.session = session
        self.log=log
        if log is None:
            self.log = logModule(self.__class__.__name__)
            self.log.setLevel( self.log.DEBUG )
        self.commandPrompt = r"command: "  # CUnit Prompt
        self.selectPrompt = r") : "

    def start(self, command:str ):
        """start the suite

        Args:
            command (str): start command

        Returns:
            str: prompt result
        """
        self.session.write(command)
        #result = self.session.read_all()
        result = self.session.read_until( self.commandPrompt )
        #self.log.debug("start[{}]".format(result))
        if result == "":
            self.log.error("Failed to start[{}]".format(command))
        return result

    def stop(self):
        """stops the active suite

        Returns:
            str: terminal output for debugging
        """
        # Quit from any menu we're in
        self.session.write("q")
        result = self.session.read_all()
        self.log.debug(result)
        return result

    def select(self, suite_name: str, test_name:str = None, promptWithAnswers: list = None ):
        """select a test from the suite to execute and wait for Prompt

        Args:
            suite_name (str): suite to select
            test_name (str, optional): test_name within the suite to select. Defaults to None, whole suite will be ran
            input (bool, optional): if set to true then don't wait on last prompt

        Raises:
            ValueError: Suite {suite_name} not found the suite configuration
            ValueError: Test {test_name} not found in suite

        Returns:
            str: output from the framework
        """

        # Ensure we're at the top menu
        self.session.write("x")
        self.session.write("u")
        output = self.session.read_until(self.commandPrompt)
        self.log.debug(output)
        self.session.write("s")
        output = self.session.read_until(self.selectPrompt)
        self.log.debug(output)

        # Extract test suite index from the output
        suite_index = self.find_index_in_output(output, suite_name)
        if suite_index is None:
            self.log.error(f"Suite [{suite_name}] not found in configuration.")
            return None

        self.log.info(f"Found Suite: [{suite_name}]")
        self.session.write(str(suite_index))
        output = self.session.read_until(self.commandPrompt)
        self.log.debug(output)

        if test_name is None:
            # Run the Suite of tests
            self.session.write("r")
            output = self.session.read_until(self.commandPrompt)
            self.log.debug(output)
        else:
            # Run the specific test
            self.session.write("s")
            output = self.session.read_until(self.selectPrompt)
            self.log.debug(output)

            # Extract test index from the output
            test_index = self.find_index_in_output(output, test_name)
            if test_index is None:
                self.log.error(f"Test [{test_name}] not found in suite [{suite_name}].")
                raise ValueError(f"Test [{test_name}] not found in the suite.")

            self.log.info(f"Found test: [{test_name}] @ [{test_index}]")
            # Run the specific test
            self.session.write(str(test_index))

            # If Input is present we need to then wait on them
            if promptWithAnswers is not None:
                output = self.inputPrompts( promptWithAnswers )

            # Wait for the command prompt if there's no other input required
            output += self.session.read_until(self.commandPrompt)

            self.log.debug(output)
        return output

    def inputPrompts(self, promptsWithAnswers: dict):
        """
        Sends the ecific prompts and sends corresponding input values.

        Args:
            promptsWithAnswers  A list of prompt strings to wait for.
        """

        output=""
        for prompt, input in promptsWithAnswers.items():
            output += self.session.read_until(prompt)
            self.session.write(input)
        return output

    def find_index_in_output(self, output, target_name):
        """
        Finds the index of a target name in the shell output.

        Args:
            output (str): The shell output to search in.
            target_name (str): The name of the suite or test to find.

        Returns:
            int: The index of the target_name if found, otherwise None.
        """
        lines = output.splitlines()
        for line in lines:
            if target_name in line:
                # Looking for the index e.g., "1. SuiteName"
                match = re.match(r"(\d+)\.", line.strip())
                if match:
                    return int(match.group(1))
        return None

    def collect_results(self, output):
        """
        Collects and interprets the results from the test execution output.

        Args:
            output (str): The output from the test execution.

        Returns:
            bool: True if the test passed successfully, False if the test failed, or None if the output format is unexpected.
        """

        # Pattern to detect the number of suites, tests, and asserts with their corresponding results
        # Run Summary:    Type  Total    Ran Passed Failed Inactive
        #       suites      2      0    n/a      0        0
        #        tests     16      1      1      0        0
        #      asserts      2      2      2      0      n/a
        run_summary_pattern = r"Run Summary:\s+Type\s+Total\s+Ran\s+Passed\s+Failed\s+Inactive"
        summary_match = re.search(run_summary_pattern, output)

        if summary_match:
            # Extract the relevant lines for suites, tests, and asserts
            suite_summary_line = re.search(r"suites\s+\d+\s+\d+\s+n/a\s+(\d+)\s+\d+", output)
            test_summary_line = re.search(r"tests\s+\d+\s+\d+\s+(\d+)\s+(\d+)\s+\d+", output)
            assert_summary_line = re.search(r"asserts\s+\d+\s+\d+\s+(\d+)\s+(\d+)\s+n/a", output)

            if suite_summary_line and test_summary_line and assert_summary_line:
                suites_failed = int(suite_summary_line.group(1))
                tests_failed = int(test_summary_line.group(2))
                asserts_failed = int(assert_summary_line.group(2))

                if suites_failed == 0 and tests_failed == 0 and asserts_failed == 0:
                    self.log.info("Test passed successfully.")
                    return True
                else:
                    self.log.error("Test failed.")
                    return False
            else:
                self.log.error("Unexpected output format.")
                return None
        else:
            self.log.error("Run Summary not found.")
            return None

class UTSuiteNavigatorClass:

    """
    Navigates through the UTcore menu system, trigger the execution of test cases, and collect results.
    """
    def __init__(self, config:str, startKey:str, session:consoleInterface, log:logModule=None):
        """
        Initializes the UTCoreMenuNavigator object with a menu configuration file and an optional test profile.

        Example Format:

        ```yaml
        module:  # Prefix must always exist
            description: "dsAudio Device Settings testing profile for UT"
            test:
                execute: "../bin/run.sh -p ../profiles/module_profile.yaml"
                type: UT-C # C (UT-C Cunit) / C++ (UT-G (g++ ut-core gtest backend))
                suites:
                    0:
                        name: "L1 Suite"
                    1:
                        name: "L2 Suite"
                    2:
                        name: "L3 Suite"
                        tests:
                            - "Test 1"
                            - "Test 2"
                            - "Test 3"
        ```

        Args:
            config (str): The file path to the menu configuration YAML file or a string
            startKey (str): Optional Index string into the config
            session: (consoleInterface) The console session object to communicate
            log: (logModule, optional) Log module to use
        """
        self.session = session
        self.config = ConfigRead(config, startKey)
        if log is None:
            self.log = logModule(self.__class__.__name__)
        test_type = self.config.test.type
        self.log.setLevel( self.log.INFO )
        if test_type == "UT-C" or test_type == "C":
            # Currently support the C Framework
            self.framework = utCFramework(session)
            self.log.info("C Framework Selected")
        else:
            self.log.error("Invalid Menu Type Configuration :{}".format(test_type))

    def select(self, suite_name: str, test_name:str = None, promptWithAnswers:dict = None ):
        """Select a menu from an already running system

        Args:
            suite_name (str): Suite Name
            test_id (str): Test name or None for the whole suite
            input (list optional): list of input values

        Raises:
            ValueError: not found in the menu configuration
            ValueError: not found in the suite_name
        """
        # 1. Find the suite name from the configuration
        test_section = self.config.fields.get('test')
        if not test_section:
            self.log.error("Invalid Format [test:] section not found")
            return None
        suite_list = test_section.get('suites')
        if not suite_list:
            self.log.error("Invalid Format [suites:] section not found")
            return None
        found = False
        # Just validate that the test is in the expected list
        for index in suite_list:
            suite = suite_list.get(index)
            if not suite:
                self.log.error("Invalid Format [suites.<index>]")
                return None
            testsList = suite.get("tests")
            if not testsList:
                continue
            if test_name in testsList:
                found = True
                break
        if not found:
            self.log.error("Suite:[{}] Test:[{}] Not Found".format(suite_name, test_name))
            return None

        result = self.framework.select( suite_name, test_name, promptWithAnswers )

        return result

    def start(self):
        command = self.config.test.execute
        #TODO: Handle opkg download and install in the future
        result = self.framework.start(command)
        self.log.debug( "result [{}]".format(result))

    def stop(self):
        self.framework.stop()

    def run(self, suite_name, test_name=None):
        """
        Executes the specified test by navigating to it and collecting the results.

        Args:
            suite_name (str): The name of the test suikte to navigate to.
            test_name (str): The name of the specific test case to execute.

        Returns:
            bool: The result of the test execution, True if the test passed, False otherwise.
        """
        self.framework.start()
        result = self.select( suite_name, test_name )
        results = self.framework.collect_results( result )
        return results

# Test and example usage code
if __name__ == '__main__':
    suiteConfig="""
    dsAudio:  # Prefix must always exist
        description: "dsAudio Device Settings testing profile for UT"
        test:
            execute: "cd bin;./run.sh -p ../profiles/sink/Sink_AudioSettings.yaml"
            type: UT-C # C (UT-C Cunit) / C++ (UT-G (g++ ut-core gtest backend))
            suites:
                0:
                    name: "L1 dsAudio - Sink"
                    tests:
                        - None
                1:
                    name: "L2 dsAudio - Sink"
                    tests:
                        - None
                2:
                    name: "L3 dsAudio - Sink"
                    tests:
                        - "Initialize dsAudio"
                        - "Enable Audio Port"
                        - "Disable Audio Port"
                        - "Headphone Connection"
                        - "Audio Compression"
                        - "MS12 DAP Features"
                        - "Set Stereo Mode"
                        - "Enable/Disable Stereo Auto"
                        - "Set Audio Level"
                        - "Set Audio Gain For Speaker"
                        - "Audio Mute/UnMute"
                        - "Set Audio Delay"
                        - "Get Audio Format"
                        - "Set ATMOS Output Mode"
                        - "Get ATMOS Capabilities"
                        - "Set MS12 Profiles"
                        - "Set Associate Audio Mixing"
                        - "Set Audio Mixer Levels"
                        - "Primary/Secondary Language"
                        - "Get ARC Type"
                        - "Set SAD List"
                        - "Terminate dsAudio"
    """

    # test the class
    shell = InteractiveShell()
    result = shell.open()
    print("Shell:[{}]".format(result))

    suite = "L3 dsAudio - Sink"
    # Enable to test file loading assuming that we have a Audio Settings profile for testing
    #test = UTSuiteNavigatorClass(suiteConfig, "dsAudio:", shell)
    test = UTSuiteNavigatorClass("./host/tests/class/dsAudio_test_suite.yaml", "dsAudio:", shell)
    test.start()
    test.select( suite, "test_error_validation_case" ) # error case
    result = test.select( suite, "Initialize dsAudio" ) # valid case
    result = test.select( suite, "Terminate dsAudio" ) # valid case
    promptWithAnswers = {
        "Option1": {     # Group related prompts and answers under a descriptive key
            "Select Mixer Input: ": "1",
            "Set the Volume[0 to 100]: ": "100"
        },
        "Option2": {     # Another group for clarity
            "Select Mixer Input: ": "0",
            "Set the Volume[0 to 100]: ": "50"
        }
    }
    result = test.select( suite, "Set Audio Mixer Levels", promptWithAnswers["Option1"] ) # Has non matching inputs and should error
    print(result)
    result = test.select( suite, "Set Audio Mixer Levels", promptWithAnswers["Option2"] ) # Has non matching inputs and should error
    print(result)
    test.stop()

    #test.select( "Parent", "Child" )
    #menu_config - is currently not used
    # Upgrade the help to support menu navigation input via the yaml file
    # test launch_test
    # select is working
    shell.close()
