"""
This file is part of Giswater 3
The ogram is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.
"""
# -*- coding: utf-8 -*-
from qgis.PyQt.QtWidgets import QMenu, QAction, QActionGroup, QTableView
from qgis.PyQt.QtSql import QSqlTableModel, QSqlDatabase, QSqlQueryModel

from ....settings import (
    tools_qgis,
    tools_qt,
    tools_gw,
    dialog,
    tools_os,
    tools_log,
    tools_db,
    gw_global_vars,
)
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

        # Fill results table
        self._fill_table(
            self.dlg_priority_manager,
            self.dlg_priority_manager.tbl_results,
            "asset.cat_result",
        )
        tools_gw.set_tablemodel_config(
            self.dlg_priority_manager,
            self.dlg_priority_manager.tbl_results,
            "cat_result",
            schema_name="asset",
        )

        self._set_signals()

        # Open the dialog
        tools_gw.open_dialog(self.dlg_priority_manager, dlg_name="priority_manager")

    def _fill_table(
        self,
        dialog,
        widget,
        table_name,
        hidde=False,
        set_edit_triggers=QTableView.NoEditTriggers,
        expr=None,
    ):
        """Set a model with selected filter.
        Attach that model to selected table
        @setEditStrategy:
        0: OnFieldChange
        1: OnRowChange
        2: OnManualSubmit
        """
        try:

            # Set model
            model = QSqlTableModel(db=gw_global_vars.qgis_db_credentials)
            model.setTable(table_name)
            model.setEditStrategy(QSqlTableModel.OnFieldChange)
            model.setSort(0, 0)
            model.select()

            # When change some field we need to refresh Qtableview and filter by psector_id
            # model.dataChanged.connect(partial(self._refresh_table, dialog, widget))
            widget.setEditTriggers(set_edit_triggers)

            # Check for errors
            if model.lastError().isValid():
                print(f"ERROR -> {model.lastError().text()}")

            # Attach model to table view
            if expr:
                widget.setModel(model)
                widget.model().setFilter(expr)
            else:
                widget.setModel(model)

            if hidde:
                self.refresh_table(dialog, widget)
        except Exception as e:
            print(f"EXCEPTION -> {e}")

    def _set_signals(self):
        dlg = self.dlg_priority_manager
        dlg.btn_close.clicked.connect(dlg.reject)
