
import sys
import yaml
import re

from framework.core.logModule import logModule

class UTCoreMenuNavigator:
    """
    Navigates through the UTcore menu system, trigger the execution of test cases, and collect results.
    """

    def __init__(self, menu_config_path, console):
        """
        Initializes the UTCoreMenuNavigator object with a menu configuration file and an optional test profile.

        Args:
            menu_config_path (str): The file path to the menu configuration YAML file.
            console: The console session object to communicate with the UTcore system.
            test_profile_url (str, optional): The URL to a test profile YAML file. Defaults to None.
        """
        self.session = console
        self.menu_config = self.load_yaml(menu_config_path)
        self.shell = self.session.open_interactive_shell()
        self.log = logModule("UTCoreMenuNavigator")

    
    def find_key(self, d, target_key):
        """
        Recursively searches for a target key in a nested dictionary and returns the corresponding value.

        Args:
            d (dict): The dictionary to search in.
            target_key (str): The key to search for.

        Returns:
            The value associated with the target key if found, else None.
        """
        if target_key in d:
            return d[target_key]
        
        for key, value in d.items():
            if isinstance(value, dict):
                result = self.find_key(value, target_key)
                if result is not None:
                    return result
        return None


    def load_yaml(self, path):
        """
        Loads and parses a YAML file from the specified path.

        Args:
            path (str): The file path to the YAML file.

        Returns:
            dict: The parsed YAML content.
        """
        with open(path, 'r') as file:
            return yaml.safe_load(file)
        

    def run_commands(self, run_script_path, group_name, test_name):
        """
        Executes a sequence of commands in the session shell to run a specific test.
        After typing 's', it outputs the available groups and tests to assist with the selection.
        It then finds the corresponding indexes for the requested group and test.

        Args:
            run_script_path (str): The file path to the script that initiates the test run.
            group_name (str): The name of the test group to navigate to.
            test_name (str): The name of the specific test case to locate.

        Returns:
            None
        """
        self.session.write(run_script_path)
        
        group_output = self.session.write("s")
        
        # Extract group index from the output
        group_index = self.find_index_in_output(group_output, group_name)
        if group_index is None:
            self.log.error(f"Group '{group_name}' not found in menu configuration.")
            raise ValueError(f"Group '{group_name}' not found in the shell output.")
        
        self.log.info(f"Found group: {group_name}")
        self.session.write(str(group_index))

        
        test_output = self.session.write("s")        
        
        # Extract test index from the output
        test_index = self.find_index_in_output(test_output, test_name)
        if test_index is None:
            self.log.error(f"Test '{test_name}' not found in group '{group_name}'.")
            raise ValueError(f"Test '{test_name}' not found in the shell output.")
        
        self.log.info(f"Found test: {test_name}")
        self.session.write(str(test_index))


    def find_index_in_output(self, output, target_name):
        """
        Finds the index of a target name in the shell output.

        Args:
            output (str): The shell output to search in.
            target_name (str): The name of the group or test to find.

        Returns:
            int: The index of the target_name if found, otherwise None.
        """
        lines = output.splitlines()
        for line in lines:
            if target_name in line:
                # Looking for the index e.g., "1. GroupName"
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


    def run_test(self, run_script_path, group_name, test_name):
        """
        Executes the specified test by navigating to it and collecting the results.

        Args:
            run_script_path (str): The file path to the script that initiates the test run.
            group_name (str): The name of the test group to navigate to.
            test_name (str): The name of the specific test case to execute.

        Returns:
            bool: The result of the test execution, True if the test passed, False otherwise.
        """
        self.run_commands(run_script_path, group_name, test_name)
        full_output = self.session.read_all()

        return self.collect_results(full_output)