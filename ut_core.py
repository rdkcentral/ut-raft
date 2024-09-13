"""
Module Structure:
    - Parse the YAML configuration files to understand the structure of the menu and the available test cases.
    - Navigate through the UTcore menu system based on the parsed information.
    - Trigger the execution of a specific test case by interacting with the menu.
Key Components of the Module:
    - YAML Parsing: A method to load and parse the YAML files, extracting the necessary information to navigate the menu.
    - Menu Navigation: Methods to send appropriate commands (e.g., keystrokes) to the system to navigate through the menu.
    - Test Execution: A method to select and execute a specific test case based on the input provided.
    - Result Collection: A method to read and interpret the test results from the output.
"""
"""
## Run an individual test
ut_run.py --group "L1 tvSettings - Bank5,SetDynamicContrast_L1_positive"  -- test "test_l1_tvSettings_positive_GetDynamicContrast"
## Run a complete group
ut_run.py --group "L1 tvSettings - Bank5,SetDynamicContrast_L1_positive" # Runs the whole group
# Specify a test profile
ut_run.py --test_profile https://github.com/rdkcentral/RaftTestProfiles/blobk/main/panel/HPK_ProductATestProfile.yaml ----group "L1 tvSettings - Bank5,SetDynamicContrast_L1_positive"
"""


import yaml
import subprocess
import re

class UTCoreMenuNavigator:
    def __init__(self, menu_config_path, console, test_profile_url=None):
        self.session = console
        self.menu_config = self.load_yaml(menu_config_path)
        if test_profile_url:
            self.test_profile = self.load_yaml(test_profile_url)
        else:
            self.test_profile = None

    def load_yaml(self, path):
        # responsible for loading and parsing the YAML files
        # parsed data stored in self.menu_config and self.test_profile
        with open(path, 'r') as file:
            return yaml.safe_load(file)

    def navigate_to_test(self, group_name, test_name):
        # navigate through the UTCore menu to reach the desired test group and test case
        # simulates sending navigation commands (e.g., selecting a suite, selecting a test) using the send_command method
        # needs to be replaced with actual system interactions.
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

        # Simulate navigation commands
        self.send_command("s")  # 's' to select the suite
        self.send_command("1")
        self.send_command("s")  # 's' to select the suite
        self.send_command("1")

    def run_test(self, group_name, test_name):
        # 1st navigates to the desired test using navigate_to_test and then runs the test
        # test execution is simulated with a subprocess.run command, which captures the output of the test run
        self.navigate_to_test(group_name, test_name)

        # Command to execute the test binary (replace this with actual command execution logic)
        result = subprocess.run(['ut-raft/run.sh'], capture_output=True, text=True)
# ssh read write
        
        # Collect results
        return self.collect_results(result.stdout)

    def collect_results(self, output):
        # interpret the test output to determine whether the test passed or failed
        success_pattern = r"Total Number of Failures\s*:\s*0"
        failure_pattern = r"Total Number of Failures\s*:\s*\d+"

        if re.search(success_pattern, output):
            print("Test passed successfully.")
            return True
        elif re.search(failure_pattern, output):
            print("Test failed.")
            return False
        else:
            print("Unexpected output format.")
            return None

    def send_command(self, command):
        # placeholder for the actual system interaction logic
        # needs to send commands to the UTCore system via serial communication or another interface.
        print(f"Sending command: {command}")
        # Here you would interact with the actual system, e.g., through serial communication or similar




# UTCoreMenuNavigator class is initialised with the path to a YAML configuration file
# run_test method is used to navigate to a specific test case and run it
# results of the test execution are collected and printed
if __name__ == "__main__":
    navigator = UTCoreMenuNavigator('ut-raft/ut_menu.yml')
    test_passed = navigator.run_test('L1 plat_power', 
                                     'PLAT_INIT_L1_positive')

    if test_passed:
        print("Test executed and passed.")
    else:
        print("Test execution failed.")
