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

class utConfig(dict):

    def __init__(self, data=None, start_key=None, **kwargs):
        """
        Initialize an utConfig optionally focused at a nested dictionary key.
        
        :param data: A dict or None. If a dict is provided, it is deep-converted to utConfig.
                     If start_key is provided, initialization will begin at that sub-dictionary.
        :param start_key: Optional; a key to start at within the data dictionary.
        :param kwargs: Additional keyword arguments that are added to the instance.
        """
        super(utConfig, self).__init__()
        if data is None:
            data = {}
        else:
            if isinstance(data, utConfig):
                data = data.copy()  # Make a copy to avoid modifications to the original utConfig
            if start_key:
                data = data.get(start_key, {})
        self.update(data, **kwargs)

    def __getattr__(self, key):
        """
        Allow dictionary keys to be accessed as attributes. Missing keys raise an AttributeError.
        
        :param key: The attribute/key name to access.
        :return: The value associated with 'key'.
        :raises AttributeError: If 'key' is not in the dictionary.
        """
        try:
            value = self[key]
            if isinstance(value, dict) and not isinstance(value, utConfig):
                value = utConfig(value)
                self[key] = value
            return value
        except KeyError:
            raise AttributeError(f"'utConfig' object has no attribute '{key}'")

    def __setattr__(self, key, value):
        """
        Set the dictionary key to a given value. Ensures attribute access is synonymous with dictionary access.
        
        :param key: The attribute/key name to set.
        :param value: The value to set for the given key.
        """
        self[key] = value

    def __delattr__(self, key):
        """
        Delete a dictionary key using attribute-style access. Raises AttributeError for non-existent keys.
        
        :param key: The attribute/key name to delete.
        :raises AttributeError: If 'key' is not in the dictionary.
        """
        try:
            del self[key]
        except KeyError:
            raise AttributeError(f"'utConfig' object has no attribute '{key}'")

    def update(self, *args, **kwargs):
        """
        Update the dictionary with keys and values from another dictionary or iterable of key-value pairs.
        Nested dictionaries are converted to utConfig instances.
        
        :param args: Dictionary or iterable of key-value pairs to update the dictionary.
        :param kwargs: Keyword arguments to update the dictionary.
        """
        for key, value in dict(*args, **kwargs).items():
            if isinstance(value, dict) and not isinstance(value, utConfig):
                value = utConfig(value)
            self[key] = value

class utConfigReader:

    def __init__(self, config_data:str, start_key=None):
        """
        Initialize the ConfigReader instance with the path to a YAML configuration file
        and optionally a specific key within that file to focus on.

        :param config_data: The path to the YAML configuration file, or a dict of yaml content string
        :param child_key: Optional; the key of a subset of the configuration data to be loaded.
        """
        yaml_data = self.__load_yaml__( config_data )

        data = yaml_data
        if start_key:
            data = yaml_data.get(start_key, {})

        # Setting each key in the loaded data as an attribute of the instance
        for key, value in data.items():
            if isinstance(value, dict):
                # Convert nested dictionaries to utConfig for attribute-like access
                setattr(self, key, utConfig(value))
            else:
                setattr(self, key, value)

        self.config = utConfig( data, start_key )

    def __load_yaml__(self, input_var):
        """
        Load YAML data from a file or a dictionary.
        If input_var is a string and a valid filename, treat it as a file path.
        If input_var is a dictionary, use it directly.
        If input_var is a string and not a valid filename, treat as a yaml string
        Raises ValueError if the input is neither a file path nor a dictionary.

        :param input_var: str (file path) or dict
        :return: dict
        """
        if isinstance(input_var, str) and os.path.isfile(input_var):
            with open(input_var, 'r') as file:
                return yaml.safe_load(file)
        elif isinstance(input_var, str):
                return yaml.safe_load(input_var)
        elif isinstance(input_var, dict):
            return input_var
        else:
            raise ValueError("Input must be a valid file path or a dictionary")

# Test and example usage code
if __name__ == '__main__':
    # Sample YAML data
    yaml_data = """
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
    validation_check = """
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
            - 1:                   # Resource object begins
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

    data = utConfigReader(yaml_data, "config")
    # Accessing configuration using attribute style
    print(data.database.host)  # Expected: localhost
    print(data.database.port)  # Expected: 5432
    print(data.application.name)  # Expected: MyApp
    print(data.application.languages)  # Expected: ['Python', 'JavaScript']

    IAudioDecoderManager = utConfigReader(validation_check, "IAudioDecoderManager")
    print( IAudioDecoderManager )
    print( IAudioDecoderManager.interfaceVersion )  # Expected: localhost

    decoders = utConfig(IAudioDecoderManager.IAudioDecoder)
    print(decoders)
    #print(decoders.0.supportedCodecs)  # Expected: localhost
    #print(decoders.0.supportsSecure)  # Expected: 5432

    #print(decoders.1.supportedCodecs)  # Expected: localhost
    #print(decoders.1.supportsSecure)  # Expected: 5432

    database = utConfig(data.database)

    # Accessing configuration using attribute style
    print(database.host)  # Expected: localhost
    print(database.port)  # Expected: 5432
