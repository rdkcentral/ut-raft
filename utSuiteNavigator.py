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
from utUserResponse import utUserResponse

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
        self.testUserResponse = utUserResponse()

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
        result = self.session.read_until("#")
        self.log.debug(result)
        return result

    def select(self, suite_name: str, test_name: str = None, promptWithAnswers: list = None, timeout: int = 10, is_cunit: bool = True):
        """
        Select a test from the suite to execute and wait for Prompt.

        Args:
            suite_name (str): Suite to select.
            test_name (str, optional): Test name within the suite to select. Defaults to None; whole suite will be run.
            promptWithAnswers (list, optional): List of input prompts and responses to handle during test execution.
            timeout (int): Time limit before timing out, in seconds. Defaults to 10 seconds.
            is_cunit (bool): Set to True if running CUnit tests; False for GTest. Controls initial menu navigation.

        Raises:
            ValueError: If the suite or test name is not found.

        Returns:
            str: Output from the framework.
        """

        # Ensure we're at the top menu depending on the framework
        self.session.write("x" if is_cunit else "m")
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
            # Run the suite of tests
            self.session.write("r")
            output = self.session.read_until(self.commandPrompt, timeout)
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
            self.session.write(str(test_index))

            # If input prompts are present, handle them
            if promptWithAnswers is not None:
                output = self.inputPrompts(promptWithAnswers)

            # Wait for the command prompt (final output)
            output = self.session.read_until(self.commandPrompt, timeout)
            self.log.debug(output)

        return output

    def inputPrompts(self, promptsWithAnswers: dict):
        """
        Sends the ecific prompts and sends corresponding input values.

        Args:
            promptsWithAnswers  A list of prompt strings to wait for.
        """

        output=""
        for prompt in promptsWithAnswers:
            session_output = self.session.read_until(prompt.get("query"))
            if prompt.get("query_type") == "list":
                value = self.find_index_in_output(session_output, prompt.get("input"))
                if value is None:
                    prompt = prompt.get("input")
                    self.log.error(f"Test [{prompt}] not found in suite")
                    raise ValueError(f"Test [{prompt}] not found.")
                input = str(value)
            else:
                input = prompt.get("input")

            if input == "user_prompt":
                input = self.testUserResponse.getUserYN(prompt.get("query"))
            self.session.write(input)
            output += session_output

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
        pattern = r'(\d+)\.\s*\[?' + re.escape(target_name) + r'\]?'
        match = re.search(pattern, output)
        if match:
            return int(match.group(1))
        return None


    def collect_results(self, output, gtest: bool = False):
        """
        Collects and interprets the results from the test execution output.

        Args:
            output (str): The output from the test execution.
            gtest (bool): Flag to indicate whether to parse GTest-style summary format.

        Returns:
            bool: True if the test passed successfully, False if the test failed, or None if the output format is unexpected.
        """

        if gtest:
            # GTest-style summary parsing
            run_summary_found = "Run Summary:" in output
            if not run_summary_found:
                self.log.error("Run Summary not found.")
                return None

            # Match Suites, Tests, and Asserts lines
            suite_line = re.search(r"Suites\s+\d+\s+\d+\s+n/a\s+n/a\s+(\d+)\s+n/a", output)
            test_line = re.search(r"Tests\s+\d+\s+\d+\s+(\d+)\s+(\d+)\s+\d+\s+\d+", output)
            assert_line = re.search(r"Asserts\s+\d+\s+\d+\s+(\d+)\s+(\d+)\s+\d+", output)

            if suite_line and test_line and assert_line:
                suites_inactive = int(suite_line.group(1))
                tests_passed = int(test_line.group(1))
                tests_failed = int(test_line.group(2))
                asserts_passed = int(assert_line.group(1))
                asserts_failed = int(assert_line.group(2))

                if tests_failed == 0 and asserts_failed == 0 and suites_inactive == 0:
                    self.log.info("Test passed successfully (GTest format).")
                    return True
                else:
                    self.log.error(
                        f"Test failed (GTest format). Suites inactive: {suites_inactive}, "
                        f"Tests failed: {tests_failed}, Asserts failed: {asserts_failed}"
                    )
                    return False
            else:
                self.log.error("Unexpected GTest output format.")
                return None

        else:
            # cunit parsing
            run_summary_pattern = r"Run Summary:\s+Type\s+Total\s+Ran\s+Passed\s+Failed\s+Inactive"
            summary_match = re.search(run_summary_pattern, output)

            if summary_match:
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
            targetWorkspace: "/tmp/${startKey}/" # Defined by the caller (not currently used by this module)
            test:
                execute: "../bin/run.sh -p ${targetWorkspace}/profiles/module_profile.yaml" # defined by the caller
                type: UT-C # C (c backend) / C++ (UT-G (g++ backend)
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
            config (str): The file path to the menu configuration YAML file or a decoded object
            startKey (str): Optional Index string into the config, and used in ${targetWorkspace}
            session: (consoleInterface) The console session object to communicate
            log: (logModule, optional) Log module to use
        """
        self.session = session
        self.config = ConfigRead(config, startKey)
        if log is None:
            self.log = logModule(self.__class__.__name__)
        self.log.setLevel( self.log.INFO )
        test_type = self.config.test.type
        if test_type == "UT-C" or test_type == "C":
            # Currently support the C Framework
            self.framework = utCFramework(session)
            self.log.info("C Framework Selected")
        else:
            self.log.error("Invalid Menu Type Configuration :{}".format(test_type))

    def select(self, suite_name: str, test_name: str = None, promptWithAnswers: dict = None, timeout: int = 10, is_cunit: bool = True):
        """
        Select a menu from an already running system.

        Args:
            suite_name (str): Suite Name.
            test_name (str): Test name or None for the whole suite.
            promptWithAnswers (dict, optional): Dictionary of input prompts and responses.
            timeout (int): Time limit before timing out, in seconds. Defaults to 10 seconds.
            is_cunit (bool): Set to True if running a CUnit-based test. Defaults to False.

        Raises:
            ValueError: If test or suite name is not found in the configuration.

        Returns:
            str: Output from the framework.
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
            self.log.info("Suite:[{}] Test:[{}] Not Found. Run all tests with 'r' option.".format(suite_name, test_name))

        result = self.framework.select(suite_name, test_name, promptWithAnswers, timeout, is_cunit)

        return result

    def start(self):
        command = self.config.test.execute
        result = self.framework.start(command)
        self.log.debug( "result [{}]".format(result))

    def stop(self):
        self.framework.stop()

    def collect_results(self, output, gtest: bool = False):
        results = self.framework.collect_results( output, gtest )
        return results

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

    suite = "L3 dsAudio"
    # Enable to test file loading assuming that we have a Audio Settings profile for testing
    test = UTSuiteNavigatorClass(suiteConfig, "dsAudio:", shell)

    test.start()
    test.select( suite, "test_error_validation_case" ) # error case
    result = test.select( suite, "Initialize dsAudio" ) # valid case
    result = test.select( suite, "Terminate dsAudio" ) # valid case
    promptWithAnswers = [
            {
                "query_type": "list",
                "query": "Select dsAudio Port:",
                "input": "dsAUDIOPORT_TYPE_SPEAKER"
            },
            {
                "query_type": "direct",
                "query": "Select dsAudio Port Index[0-10]:",
                "input": "0"
            }
    ]
    result = test.select( suite, "Enable Audio Port", promptWithAnswers ) # Has non matching inputs and should error
    print(result)
    promptWithAnswers = [
            {
                "query_type": "list",
                "query": "Select dsAudio Port:",
                "input": "dsAUDIOPORT_TYPE_SPEAKER"
            },
            {
                "query_type": "direct",
                "query": "Select dsAudio Port Index[0-10]:",
                "input": "0"
            },
            {
                "query_type": "direct",
                "query": "Enter Gain Level[0.0 to 100.0]:",
                "input": "20"
            }
    ]
    result = test.select( suite, "Set Audio Mixer Levels", promptWithAnswers ) # Has non matching inputs and should error
    print(result)
    test.stop()

    #test.select( "Parent", "Child" )
    #menu_config - is currently not used
    # Upgrade the help to support menu navigation input via the yaml file
    # test launch_test
    # select is working
    shell.close()
