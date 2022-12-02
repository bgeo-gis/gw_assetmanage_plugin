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

from ...ui.ui_manager import ResultSelectorUi


class ResultSelector(dialog.GwAction):
    """  """

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

        self.dlg_result_selector = ResultSelectorUi()

        # Combo result_selector
        sql = "SELECT cr.result_id as id, cr.result_name as idval FROM asset.selector_result_main sm join asset.cat_result cr using (result_id);"
        rows = tools_db.get_rows(sql)
        tools_qt.fill_combo_values(self.dlg_result_selector.cmb_result_selector, rows, 1, sort_by=0)
        # Combo result_global
        sql = "SELECT cr.result_id as id, cr.result_name as idval FROM asset.selector_result_compare sc join asset.cat_result cr using (result_id);"
        rows = tools_db.get_rows(sql)
        tools_qt.fill_combo_values(self.dlg_result_selector.cmb_result_global, rows, 1, sort_by=0)

        # Open the dialog
        tools_gw.open_dialog(self.dlg_result_selector, dlg_name='result_selection')
