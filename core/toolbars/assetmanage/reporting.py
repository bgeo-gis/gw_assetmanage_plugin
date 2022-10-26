"""
This file is part of Giswater 3
The ogram is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.
"""
# -*- coding: utf-8 -*-
from datetime import datetime
from functools import partial

from qgis.PyQt.QtWidgets import QMenu, QAction, QActionGroup

from ....settings import tools_qgis, tools_qt, tools_gw, dialog, tools_os, tools_log, tools_db
from .... import global_vars

from ...ui.ui_manager import ReportingUi


class AmReporting(dialog.GwAction):
    """ Button 3: Reporting button
    Review reports in tableview """

    def __init__(self, icon_path, action_name, text, toolbar, action_group):

        super().__init__(icon_path, action_name, text, toolbar, action_group)
        self.iface = global_vars.iface

        self.icon_path = icon_path
        self.action_name = action_name
        self.text = text
        self.toolbar = toolbar
        self.action_group = action_group

        # Reporting variables
        self.reporting_dlg = None


    def clicked_event(self):
        self.reporting()


    def reporting(self):
        print("REPORTING")
        self.reporting_dlg = ReportingUi()

        # Open the dialog
        tools_gw.open_dialog(self.reporting_dlg, dlg_name='reporting')
