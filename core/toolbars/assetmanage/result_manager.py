"""
This file is part of Giswater 3
The ogram is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.
"""
# -*- coding: utf-8 -*-
from qgis.PyQt.QtWidgets import QMenu, QAction, QActionGroup, QTableView

from ....settings import tools_qgis, tools_qt, tools_gw, dialog, tools_os, tools_log, tools_db, gw_global_vars
from .... import global_vars

from ...ui.ui_manager import PriorityUi, PriorityManagerUi


class ResultManager(dialog.GwAction):
    """ """

    def __init__(self, icon_path, action_name, text, toolbar, action_group):

        super().__init__(icon_path, action_name, text, toolbar, action_group)
        self.iface = global_vars.iface

        self.icon_path = icon_path
        self.action_name = action_name
        self.text = text
        self.toolbar = toolbar
        self.action_group = action_group


    def clicked_event(self):
        self.open_manager()


    def open_manager(self):

        self.dlg_priority_manager = PriorityManagerUi()

        # self._fill_table(self.dlg_priority_manager, self.dlg_priority_manager.tbl_selection, "asset.result_selection",
        #                  set_edit_triggers=QTableView.DoubleClicked)
        # tools_gw.set_tablemodel_config(self.dlg_priority_manager, self.dlg_priority_manager.tbl_selection,
        #                                "result_selection", schema_name='asset')

        # Open the dialog
        tools_gw.open_dialog(self.dlg_priority_manager, dlg_name='priority_manager')
