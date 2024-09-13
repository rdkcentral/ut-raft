
import socket
import time
import yaml
import re

class UTCoreMenuNavigator:
    """
    Navigates through the UTcore menu system, trigger the execution of test cases, and collect results.
    """

    def __init__(self, menu_config_path, console, test_profile_url=None):
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

        if test_profile_url:
            self.test_profile = self.load_yaml(test_profile_url)
        else:
            self.test_profile = None

    
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

    
    def navigate_to_test(self, group_name, test_name):
        """
        Navigates the menu system to locate the specified test case.

        Args:
            group_name (str): The name of the test group to navigate to.
            test_name (str): The name of the specific test case to locate.

        Returns:
            str: The full output from the system after navigation and test execution.

        Raises:
            ValueError: If the specified group or test is not found in the menu configuration.
        """
        group_found = False
        test_found = False

        # Navigate to the correct group
        for group in self.menu_config['tvsettings']['control']['menu']['groups']:
            if group['name'] == group_name:
                group_found = True
                print(f"Found group: {group_name}")
                break

        if not group_found:
            raise ValueError(f"Group '{group_name}' not found in menu configuration.")

        # Navigate to the correct test
        for test in group['tests']:
            if test == test_name:
                test_found = True
                print(f"Found test: {test_name}")
                break

        if not test_found:
            raise ValueError(f"Test '{test_name}' not found in group '{group_name}'.")

        self.session.write_to_shell("/home/FKC01/rdk-halif-power_manager/ut/bin/run.sh")
        self.session.write_to_shell("s",3)
        self.session.write_to_shell("1", 3)
        self.session.write_to_shell("s", 3)
        self.session.write_to_shell("1", 3)

        full_output = self.session.get_full_output()

        return full_output


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
                    print("Test passed successfully.")
                    return True
                else:
                    print("Test failed.")
                    return False
            else:
                print("Unexpected output format.")
                return None
        else:
            print("Run Summary not found.")
            return None


    def run_test(self, group_name, test_name):
        """
        Executes the specified test by navigating to it and collecting the results.

        Args:
            group_name (str): The name of the test group to navigate to.
            test_name (str): The name of the specific test case to execute.

        Returns:
            bool: The result of the test execution, True if the test passed, False otherwise.
        """
        output = self.navigate_to_test(group_name, test_name)
        return self.collect_results(output)