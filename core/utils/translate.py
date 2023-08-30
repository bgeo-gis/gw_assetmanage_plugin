"""
Copyright © 2023 by BGEO. All rights reserved.
The program is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.
"""

# -*- coding: utf-8 -*-

from . import manage_translation
from ... import global_vars
from ...settings import tools_qt


def tr(msg):
    manage_translation(global_vars.plugin_name, None, plugin_dir=global_vars.plugin_dir,
                                plugin_name=global_vars.plugin_name)
    return tools_qt.tr(msg, context_name=global_vars.plugin_name)
