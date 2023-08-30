"""
Copyright © 2023 by BGEO. All rights reserved.
The program is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.
"""

import os.path
from ... import global_vars


def parse_variable(file_name:str, var_name: str, default_value=None):
    """
    Searches for a config variable named var_name and returns the value it holds.

    :param var_name: The config variable name to find in file init.config.
    :param default_value: Returns this value if no config variable name was found.
    :return: The found config variable's value. If no config variable was found, returns default_value.
    """

    file_path = os.path.join(global_vars.plugin_dir, f"config{os.sep}{file_name}")
    config_file = open(file_path, mode="r")

    while True:
        config_line = config_file.readline()

        # If config line starts with a # character, ignore the entire line and continue checking.
        if config_line.startswith("#"):
            continue

        # If config line starts with the desired variable name, return the value it holds.
        if config_line.startswith(var_name):
            config_line = config_line.split(":")[1]
            config_line = config_line.strip()
            return config_line

        # If the file has been entirely read and no matching config variable name was found,
        # display a warning and return the default value, if specified.
        if not config_line:
            print(f"Could not find a configuration variable with name «{var_name}». Using default value.")
            return default_value

    config_file.close()