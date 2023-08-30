"""
Copyright © 2023 by BGEO. All rights reserved.
The program is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.
"""

# -*- coding: utf-8 -*-
import os

from qgis.PyQt.QtCore import Qt

from ... import global_vars
from ...settings import tools_db, tools_gw, tools_log, tools_qgis, tools_qt


def manage_translation(*args, **kwargs):
    if _use_polyfill():
        _manage_translation_polyfill(*args, **kwargs)
    else:
        tools_qt.manage_translation(*args, **kwargs)


def open_dialog(*args, **kwargs):
    if _use_polyfill():
        _open_dialog_polyfill(*args, **kwargs)
    else:
        tools_gw.open_dialog(*args, **kwargs)


def _manage_translation_polyfill(
    context_name, dialog=None, log_info=False, plugin_dir=None, plugin_name=None
):
    """Manage locale and corresponding 'i18n' file"""

    # Get locale of QGIS application
    locale = tools_qgis.get_locale()

    if plugin_dir is None:
        plugin_dir = global_vars.plugin_dir
    if plugin_name is None:
        plugin_name = global_vars.plugin_name

    locale_path = os.path.join(plugin_dir, "i18n", f"{plugin_name}_{locale}.qm")
    if not os.path.exists(locale_path):
        if log_info:
            tools_log.log_info("Locale not found", parameter=locale_path)
        locale_path = os.path.join(
            global_vars.plugin_dir, "i18n", f"{global_vars.plugin_name}_en_US.qm"
        )
        # If English locale file not found, exit function
        # It means that probably that form has not been translated yet
        if not os.path.exists(locale_path):
            if log_info:
                tools_log.log_info("Locale not found", parameter=locale_path)
            return

    # Add translation file
    tools_qt._add_translator(locale_path)

    # If dialog is set, then translate form
    if dialog:
        tools_qt._translate_form(dialog, context_name)


def _open_dialog_polyfill(
    dlg,
    dlg_name=None,
    stay_on_top=True,
    title=None,
    hide_config_widgets=False,
    plugin_dir=global_vars.plugin_dir,
    plugin_name=global_vars.plugin_name,
):
    """Open dialog"""

    # Check database connection before opening dialog
    if (
        dlg_name != "admin_credentials" and dlg_name != "admin_ui"
    ) and not tools_db.check_db_connection():
        return

    # Manage translate
    if dlg_name:
        _manage_translation_polyfill(
            dlg_name, dlg, plugin_dir=plugin_dir, plugin_name=plugin_name
        )

    # Set window title
    if title is not None:
        dlg.setWindowTitle(title)

    # Manage stay on top, maximize/minimize button and information button
    flags = Qt.WindowCloseButtonHint | Qt.WindowMinMaxButtonsHint

    if stay_on_top:
        flags |= Qt.WindowStaysOnTopHint

    dlg.setWindowFlags(flags)

    dlg.open()


def _use_polyfill():
    """Return True if version equals or minor than 3.5.031"""
    gw_version_str = tools_qgis.get_plugin_version()[0]
    if not gw_version_str:
        return True

    gw_version = [int(x) for x in gw_version_str.split(".")]

    if gw_version[0] > 3:
        return False
    if gw_version[0] == 3 and gw_version[1] > 5:
        return False
    if gw_version[0] == 3 and gw_version[1] == 5 and gw_version[2] > 31:
        return False

    return True
