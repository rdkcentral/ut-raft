
#!/usr/bin/env python3
#** *****************************************************************************
# *
# * If not stated otherwise in this file or this component's LICENSE file the
# * following copyright and licenses apply:
# *
# * Copyright 2026 RDK Management
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

import re
import yaml
import os
import sys
from pathlib import Path

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(dir_path)

class IncludeRef:
    """Represents a YAML !include reference."""

    def __init__(self, filename):
        self.filename = filename


class UtYamlLoader(yaml.SafeLoader):
    """
    PyYAML loader supporting external YAML includes.

    Features:
      - include_0, include_1, etc.
      - !include tags
      - Nested includes
      - Application-relative include paths
      - Recursive dictionary merging
      - List append on duplicate nodes
      - Circular include detection
    """

    MAX_INCLUDE_DEPTH = 5

    INCLUDE_PATTERN = re.compile(r"^include(?:_\d+)?$")

    def __init__(self, stream):
        super().__init__(stream)

    # ---------------------------------------------------------
    # YAML mapping constructor
    # ---------------------------------------------------------

    def construct_mapping(self, node, deep=False):
        """
        Preserve duplicate mapping keys by merging their values.
        """

        self.flatten_mapping(node)

        result = {}

        for key_node, value_node in node.value:

            key = self.construct_object(key_node, deep=deep)

            if not isinstance(key, (str, int, float, bool, tuple)):
                raise yaml.constructor.ConstructorError(
                    "while constructing a mapping",
                    node.start_mark,
                    "unhashable key",
                    key_node.start_mark
                )

            value = self.construct_object(value_node, deep=deep)

            if key in result:
                result[key] = self._merge_values(
                    result[key], value
                )
            else:
                result[key] = value

        return result

    # ---------------------------------------------------------
    # Merge handling
    # ---------------------------------------------------------

    @staticmethod
    def _merge_values(existing, incoming):
        """
        Merge duplicate nodes.

        dict + dict  : recursive merge
        list + list  : append
        scalar       : preserve existing value
        """

        if isinstance(existing, dict) and isinstance(incoming, dict):
            return UtYamlLoader._merge_dicts(
                existing, incoming
            )

        if isinstance(existing, list) and isinstance(incoming, list):
            existing.extend(incoming)
            return existing

        return existing

    @staticmethod
    def _merge_dicts(destination, source):
        """Recursively merge two dictionaries."""

        for key, value in source.items():

            if key not in destination:
                destination[key] = value
            else:
                destination[key] = UtYamlLoader._merge_values(
                    destination[key], value
                )

        return destination

    # ---------------------------------------------------------
    # Main YAML entry point
    # ---------------------------------------------------------

    @classmethod
    def from_file(cls, filename):
        """
        Load master YAML and resolve all includes.

        Include paths are relative to the main application's
        current working directory, not the YAML file location.
        """

        path = Path(filename).resolve()

        if not path.is_file():
            raise FileNotFoundError(
                f"YAML file not found: {path}"
            )

        data = cls._parse_file(path)

        # Application working directory
        app_dir = Path.cwd().resolve()

        return cls._resolve(
            data=data,
            base_dir=app_dir,
            include_stack=(path,),
            depth=0
        )

    # ---------------------------------------------------------
    # Parse YAML file
    # ---------------------------------------------------------

    @classmethod
    def _parse_file(cls, filename):
        """Parse an individual YAML file."""

        with open(filename, "r", encoding="utf-8") as stream:

            loader = cls(stream)

            try:
                return loader.get_single_data()
            finally:
                loader.dispose()

    # ---------------------------------------------------------
    # Include file processing
    # ---------------------------------------------------------

    @classmethod
    def _load_include(
        cls,
        filename,
        base_dir,
        include_stack,
        depth
    ):
        """Load and recursively resolve an included YAML file."""

        if depth >= cls.MAX_INCLUDE_DEPTH:
            raise ValueError(
                f"Maximum include depth "
                f"({cls.MAX_INCLUDE_DEPTH}) exceeded"
            )

        # All include paths are relative to application directory
        path = (base_dir / filename).resolve()

        if path in include_stack:
            chain = " -> ".join(
                str(p) for p in include_stack + (path,)
            )

            raise ValueError(
                f"Circular YAML include detected: {chain}"
            )

        if not path.is_file():
            raise FileNotFoundError(
                f"Included YAML file not found: {path}"
            )

        data = cls._parse_file(path)

        return cls._resolve(
            data=data,

            # Keep application directory for nested includes
            base_dir=base_dir,

            include_stack=include_stack + (path,),
            depth=depth + 1
        )

    # ---------------------------------------------------------
    # Recursive include resolution
    # ---------------------------------------------------------

    @classmethod
    def _resolve(
        cls,
        data,
        base_dir,
        include_stack,
        depth
    ):

        # Handle !include tag
        if isinstance(data, IncludeRef):

            return cls._load_include(
                data.filename,
                base_dir,
                include_stack,
                depth
            )

        # Handle dictionaries
        if isinstance(data, dict):

            result = {}

            for key, value in data.items():

                # Handle include, include_0, include_1, etc.
                if (
                    isinstance(key, str)
                    and cls.INCLUDE_PATTERN.fullmatch(key)
                ):

                    include_files = (
                        value if isinstance(value, list) else [value]
                    )

                    for include_file in include_files:

                        if not isinstance(include_file, str):
                            raise TypeError(
                                f"Invalid include value: {include_file}"
                            )

                        included_data = cls._load_include(
                            include_file,
                            base_dir,
                            include_stack,
                            depth
                        )

                        if not isinstance(included_data, dict):
                            raise TypeError(
                                f"Included YAML must contain a mapping: "
                                f"{include_file}"
                            )

                        cls._merge_dicts(result, included_data)

                    continue

                # Resolve normal dictionary values
                resolved_value = cls._resolve(
                    value,
                    base_dir,
                    include_stack,
                    depth
                )

                if key in result:
                    result[key] = cls._merge_values(
                        result[key], resolved_value
                    )
                else:
                    result[key] = resolved_value

            return result

        # Handle lists/sequences
        if isinstance(data, list):

            result = []

            for item in data:

                resolved_item = cls._resolve(
                    item,
                    base_dir,
                    include_stack,
                    depth
                )

                result.append(resolved_item)

            return result

        return data


# -------------------------------------------------------------
# Register !include YAML tag
# -------------------------------------------------------------

def construct_include(loader, node):
    return IncludeRef(
        loader.construct_scalar(node)
    )


UtYamlLoader.add_constructor(
    "!include",
    construct_include
)

# Test and example usage code
if __name__ == '__main__':
    import os
    dir_path = os.path.dirname(os.path.realpath(__file__))
    config = UtYamlLoader.from_file(
        dir_path + "example.yaml"
    )
    import yaml
    print(yaml.safe_dump(config, sort_keys=False))
