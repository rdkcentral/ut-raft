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

class ConfigRead:
    """
    A class to represent configuration data loaded from a YAML file.

    This class facilitates the convenient loading and interaction with configuration data
    stored in YAML format. It allows you to access YAML values using:

    * Dot notation (e.g., `config.section.key`)
    * Indexing (e.g., `config['section']['key']`)
    * Dictionary-style access via the `self.fields` attribute (e.g., `config.fields['section']['key']`)

    This flexibility extends to nested structures within the YAML data.

    Furthermore, the `ConfigRead` class handles scenarios where YAML keys are numeric.
    It automatically prefixes such keys with an underscore '_' to ensure they're valid Python
    attribute names, enabling seamless access.

    This class empowers you to effectively integrate YAML-based configuration into your
    Python projects, simplifying the management and retrieval of settings in a structured
    and user-friendly manner.
    """

    def __init__(self, data=None, start_key=None ):
        """
        Initializes the ConfigRead object by loading data from a YAML file.

        Args:
            data (str or file-like object):
                Either a YAML string or a file-like object (e.g., opened file) containing YAML data.
            start_key (str, optional):
                If provided, processing starts from this key within the YAML data. Defaults to None (process the entire YAML).

        Returns:
            None

        Attributes:
            self.fields (dict):
                A dictionary representation of the YAML data.

        Behaviour:
            * Creates attributes on the object based on YAML keys.
            * Numeric keys in the YAML are prefixed with an underscore '_' to ensure valid attribute names.

        Example:
            YAML: `A: 0: key: value`
            Result: `self.A._0.key` will contain the value 'value'
        """
        if data is not None:
            if self.__class__.__name__ == type(data).__name__:
                # We've been passed a ConfigRead object
                self._copy_attributes(data, start_key)
                if start_key:
                    self.fields = data.fields.get(start_key)
                else:
                    self.fields = data.fields
            else:
                # Read YAML data
                yaml_data = self.__load_yaml__(data)
                activate_data = yaml_data

                if start_key:
                    start_key = start_key.rstrip(":")   # Ensure there's no : in the key
                    activate_data = yaml_data.get(start_key, {})
                    if not activate_data:
                        raise ValueError(f"start_key [{start_key}] must be present in the data")

                # Recursively set attributes
                self._set_attributes(activate_data)
                self.fields = activate_data

    def _copy_attributes(self, data, start_key):
        """
        Recursively copies attributes from another ConfigRead object.
        """
        if start_key is None:
            # Copy all attributes if no start_key is provided
            for name, value in vars(data).items():
                self._recursive_copy_attribute(name, value)
        else:
            start_key = start_key.rstrip(":")
            try:
                # Copy the attribute corresponding to the start_key
                value = getattr(data, start_key)
                for name, value in vars(value).items():
                    self._recursive_copy_attribute(name, value)
            except AttributeError:
                raise ValueError(f"start_key [{start_key}] must be a valid attribute")

    def _recursive_copy_attribute(self, name, value):
        """
        Recursively copies an attribute and its value.
        """
        if isinstance(value, ConfigRead):
            # Create a new ConfigRead object for nested attributes
            setattr(self, name, ConfigRead())
            # Recursively copy attributes from the nested object
            for nested_name, nested_value in vars(value).items():
                getattr(self, name)._recursive_copy_attribute(nested_name, nested_value)
        else:
            # Directly set the attribute value
            setattr(self, name, value)

    def __str__(self):
        # Customize this to display relevant parts of the YAML data
        return f"Configuration: {self.fields}"

    def __load_yaml__(self,input_var):
        """
        Loads YAML data from a file or a dictionary.

        Args:
            input_var (str or dict):
                * If a string and represents a valid filename, it's treated as the path to a YAML file.
                * If a string but not a valid filename, it's assumed to be a YAML string itself.
                * If a dictionary, it's assumed to be the already-loaded YAML data.

        Returns:
            dict: A dictionary containing the parsed YAML data.

        Raises:
            ValueError: If `input_var` is neither a valid file path, a YAML string, nor a dictionary.
        """
        if isinstance(input_var, str) and os.path.isfile(input_var):
            with open(input_var, 'r') as file:
                data = yaml.safe_load(file)
                if data is None:
                    self.log.error("Invalid Input File: [{}]".format(input_var))
                return data
        elif isinstance(input_var, str):
                data = yaml.safe_load(input_var)
                if data is None:
                    self.log.error("Invalid Input File: [{}]".format(input_var))
                return data
        elif isinstance(input_var, dict):
                return input_var
        raise ValueError("Input must be a valid file path or a dictionary")

    def _set_attributes(self, data):
        """
        Recursively sets object attributes from YAML data.

        This function iterates through YAML data (represented as a dictionary or list)
        and handles nested structures by recursively calling itself. It uses `setattr`
        to assign values to the object's attributes based on the YAML keys.

        Args:
            data: The YAML data to process (either a dictionary or a list).
        """
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, dict):
                    # Handle nested dictionaries
                    nested_obj = ConfigRead()
                    nested_obj._set_attributes(value)
                    if isinstance(key, int):  # Handle index in our list and prefix with _ e.g. _0.
                        key = '_'+str(key)
                    if key.isdigit():
                        key = '_'+str(key)
                    setattr(self, key, nested_obj)
                elif isinstance(value, list):
                    # Handle lists
                    if isinstance(key, int):  # Handle index in our list and prefix with _ e.g. _0.
                        key = '_'+str(key)
                    setattr(self, key, [
                        self._set_attributes(item) if isinstance(item, dict) else item
                        for item in value
                    ])
                else:
                    if isinstance(key, int):  # Handle index in our list and prefix with _ e.g. _0.
                        key = '_'+str(key)
                    # Handle simple values
                    setattr(self, key, value)
        elif isinstance(data, list):
            # Handle the case where 'data' itself is a list
            for index, value in enumerate(data):
                if isinstance(value, dict):
                    nested_obj = ConfigRead()
                    nested_obj._set_attributes(value)
                    self.append(nested_obj)  # Append nested object to the list
                else:
                    self.append(value)  # Append simple value to the list

    def append(self, value):
        """
        Appends an item to the internal list.

        This method ensures the internal list exists and appends the given
        value to it. If the list doesn't exist, it's initialized first.

        Args:
            value: The value to append to the list.
        """
        if not hasattr(self, '_data'):
            self._data = []  # Initialize the list if it doesn't exist
        self._data.append(value)

    def get(self, field_path: str = None):
        """
        Retrieves the value associated with a specified field path, 
        always returning an attribute (or the object itself).

        Args:
            field_path (str, optional): A dot-separated path to the 
                                       desired field (e.g., "section.subsection.key").

        Returns:
            The attribute (or object itself) associated with the field path.
        """
        if field_path is None:
            return self  # Return the entire object

        current_level = self
        for part in field_path.split('.'):
            try:
                # Check if the part is an integer
                if part.isdigit():
                    index = int(part)
                    current_level = current_level[index]  # Access list element by index
                else:
                    current_level = getattr(current_level, part)
            except (AttributeError, IndexError):
                return None

        return current_level

# Test and example usage code
if __name__ == '__main__':
    # Sample YAML data
    input_data = """
    config:
        database:
            host: localhost
            port: 5432
        application:
            name: MyApp
            version: 1.0
            languages:
                - Python
                - JavaScript
    """
    profile_check = """
        IAudioDecoderManager:  # Component object begins
            interfaceVersion: 1         # Integer value
            IAudioDecoder:              # Resource list
            - 0:
                supportedCodecs:        # Array of codec capabilities
                    - AAC_LC
                    - HE_AAC
                    - HE_AAC2
                    - DOLBY_AC3
                    - DOLBY_AC3_PLUS
                    - DOLBY_AC3_PLUS_JOC
                    - DOLBY_AC4
                    - X_HE_AAC
                supportsSecure: true
            - "1":                 # Resource object begins
                supportedCodecs:        # Array of codec capabilities
                    - AAC_LC
                    - HE_AAC
                    - HE_AAC2
                    - DOLBY_AC3
                    - DOLBY_AC3_PLUS
                    - DOLBY_AC3_PLUS_JOC
                    - DOLBY_AC4
                    - X_HE_AAC
                supportsSecure: true
    """

    data = ConfigRead(input_data, "config")
    # Accessing configuration using attribute style
    print(data.database.host)  # Expected: localhost
    assert data.database.host == "localhost", "Expected localhost"
    print(data.database.port)  # Expected: 5432
    assert data.database.port == 5432, "Expected 5432"
    print("Name:[{}]".format(data.application.name))  # Expected: MyApp
    assert data.application.name == "MyApp", "Expected MyApp"
    print(data.application.languages)  # Expected: ['Python', 'JavaScript']
    assert data.application.languages == ['Python', 'JavaScript'], "Expected ['Python', 'JavaScript']"
    print(data.application.languages[1])  # Expected: ['JavaScript']
    assert data.application.languages[1] == "JavaScript", "Expected JavaScript"

    data.application.name = "bob"

    application = ConfigRead( data, "application" )

    print("Name:[{}]".format(application.name))  # Expected: bob
    assert application.name == "bob", "Expected: Bob"
    print(application.languages)  # Expected: ['Python', 'JavaScript']
    assert application.languages == ['Python', 'JavaScript'], "Expected ['Python', 'JavaScript']"
    print(application.languages[1])  # Expected: ['JavaScript']
    assert application.languages[1] == "JavaScript", "Expected JavaScript"

    # index method still works if required
    #print(data.field.get(["config"]["database"]["port"]))

    database = data.database
    database.newField = "Hello"
    assert database.newField == "Hello", "Expected: Hello"

    # Accessing configuration using attribute style
    print(database.host)  # Expected: localhost
    assert database.host == "localhost", "Expected: localhost"
    print(database.port)  # Expected: 5432
    assert database.port == 5432, "Expected: 5432"

    data = ConfigRead(input_data)
    print(data.config.database.host)  # Expected: localhost
    assert data.config.database.host == "localhost", "Expected: localhost"    
    print(data.config.database.port)  # Expected: 5432
    assert data.config.database.port == 5432, "Expected: 5432"

    # Example 1: Accessing a simple value
    value = data.get("config.application.name")
    print(value)  # Output: MyApp

    # Example 2: Accessing a nested value
    value = data.get("config.application.languages.0")
    print(value)  # Output: Python
    assert value == "Python", "Expected: Python"

    # Example 3: Handling invalid field paths
    value = data.get("config.nonexistent.field")
    print(value)  # Output: None
    assert value == None, "Expected: None"

    IAudioDecoderManager = ConfigRead(profile_check, "IAudioDecoderManager")
    print( IAudioDecoderManager )   # TODO: Doesn't currently list objects, unclear if it should
    print( IAudioDecoderManager.interfaceVersion )  # Expected: 1
    assert IAudioDecoderManager.interfaceVersion == 1, "Expected: 1"

    decoders = IAudioDecoderManager._0.supportedCodecs
    checkDecoders = ['AAC_LC', 'HE_AAC', 'HE_AAC2', 'DOLBY_AC3', 'DOLBY_AC3_PLUS', 'DOLBY_AC3_PLUS_JOC', 'DOLBY_AC4', 'X_HE_AAC']
    print(decoders)
    assert decoders == checkDecoders, f"Expected: {checkDecoders}"
    print(decoders[1])
    assert decoders[1] == checkDecoders[1], f"Expected: {checkDecoders[1]}"
    print(decoders[5])
    assert decoders[5] == checkDecoders[5], f"Expected: {checkDecoders[5]}"

    decoders1 = IAudioDecoderManager._1
    print(decoders1.supportedCodecs)  # Expected: localhost
    codecs = ["AAC_LC", "HE_AAC", "HE_AAC2", "DOLBY_AC3", "DOLBY_AC3_PLUS", "DOLBY_AC3_PLUS_JOC", "DOLBY_AC4", "X_HE_AAC"]
    assert decoders1.supportedCodecs == codecs, "{}".format(codecs)
    
    print(decoders1.supportsSecure)  # Expected: True
    assert decoders1.supportsSecure == True, "Expected: True"

