"""
This file is part of Giswater 3
The ogram is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.
"""
# -*- coding: utf-8 -*-
from functools import partial
from qgis.PyQt.QtWidgets import (
    QAbstractItemView,
    QMenu,
    QAction,
    QActionGroup,
    QTableView,
)
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

from ...ui.ui_manager import PriorityUi, PriorityManagerUi, StatusSelectorUi


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
        # TODO: use a join to translate type and status of a result
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

    def _delete_result(self):
        table = self.dlg_priority_manager.tbl_results
        selected = [x.data() for x in table.selectedIndexes() if x.column() == 0]
        for result_id in selected:
            row = tools_db.get_row(
                f"""
                SELECT result_name, status 
                FROM asset.cat_result 
                WHERE result_id = {result_id}
                """
            )
            if not row:
                continue
            result_name, status = row
            if status == "CANCELED":
                msg = "You are about to delete the result"
                info = "This action cannot be undone. Do you want to proceed?"
                if tools_qt.show_question(
                    msg,
                    inf_text=info,
                    context_name=global_vars.plugin_name,
                    parameter=f"{result_id}-{result_name}",
                ):
                    tools_db.execute_sql(
                        f"""
                        DELETE FROM asset.cat_result
                        WHERE result_id = {result_id}
                        """
                    )
            else:
                msg = "The result cannot be deleted"
                info = "You can only delete results with the status 'CANCELED'."
                tools_qt.show_info_box(
                    msg,
                    inf_text=info,
                    context_name=global_vars.plugin_name,
                    parameter=f"{result_id}-{result_name}",
                )
        table.model().select()

    def _dlg_status_accept(self, result_id):
        new_status = tools_qt.get_combo_value(self.dlg_status, "cmb_status")
        tools_db.execute_sql(
            f"""
            UPDATE asset.cat_result
            SET status = '{new_status}'
            WHERE result_id = {result_id}
            """
        )
        self.dlg_status.close()
        self.dlg_priority_manager.tbl_results.model().select()

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
            widget.setSelectionBehavior(QAbstractItemView.SelectRows)

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

    def _open_status_selector(self):
        table = self.dlg_priority_manager.tbl_results
        selected = [x.data() for x in table.selectedIndexes() if x.column() == 0]

        if len(selected) != 1:
            msg = "Please select only one result before changing its status."
            tools_qt.show_info_box(msg, context_name=global_vars.plugin_name)
            return

        row = tools_db.get_row(
            f"""
            SELECT result_id, result_name, status
            FROM asset.cat_result
            WHERE result_id = {selected[0]}
            """
        )
        if not row:
            return

        result_id, result_name, status = row
        if status == "FINISHED":
            msg = "You cannot change the status of a result with status 'FINISHED'."
            tools_qt.show_info_box(msg, context_name=global_vars.plugin_name)
            return

        self.dlg_status = StatusSelectorUi()
        self.dlg_status.lbl_result.setText(f"{result_id}: {result_name}")
        rows = tools_db.get_rows("SELECT id, idval FROM asset.value_status")
        tools_qt.fill_combo_values(self.dlg_status.cmb_status, rows, 1)
        tools_qt.set_combo_value(self.dlg_status.cmb_status, status, 0, add_new=False)
        self.dlg_status.btn_accept.clicked.connect(
            partial(self._dlg_status_accept, result_id)
        )
        self.dlg_status.btn_cancel.clicked.connect(self.dlg_status.reject)

        tools_gw.open_dialog(self.dlg_status, dlg_name="status_selector")

    def _set_signals(self):
        dlg = self.dlg_priority_manager
        dlg.btn_status.clicked.connect(self._open_status_selector)
        dlg.btn_delete.clicked.connect(self._delete_result)
        dlg.btn_close.clicked.connect(dlg.reject)
