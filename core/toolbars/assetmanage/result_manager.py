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
    QCompleter,
)
from qgis.PyQt.QtCore import QStringListModel
from qgis.PyQt.QtSql import QSqlTableModel, QSqlDatabase, QSqlQueryModel

from .priority import CalculatePriority
from ...ui.ui_manager import PriorityUi, PriorityManagerUi, StatusSelectorUi
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
from .priority import CalculatePriority


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

        # Fill filters
        rows = tools_db.get_rows("SELECT id, idval FROM asset.value_result_type")
        tools_qt.fill_combo_values(
            self.dlg_priority_manager.cmb_type, rows, 1, add_empty=True
        )

        rows = tools_db.get_rows("SELECT expl_id, name FROM asset.exploitation")
        tools_qt.fill_combo_values(
            self.dlg_priority_manager.cmb_expl, rows, 1, add_empty=True
        )

        rows = tools_db.get_rows("SELECT id, idval FROM asset.value_status")
        tools_qt.fill_combo_values(
            self.dlg_priority_manager.cmb_status, rows, 1, add_empty=True
        )

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
        tools_gw.open_dialog(
            self.dlg_priority_manager,
            dlg_name="priority_manager",
            plugin_dir=global_vars.plugin_dir,
            plugin_name=global_vars.plugin_name,
        )

    def _manage_txt_report(self):

        dlg = self.dlg_priority_manager

        selected_list = dlg.tbl_results.selectionModel().selectedRows()

        if len(selected_list) == 0 or len(selected_list) > 1:
            dlg.txt_info.setText("")
            return

        row = selected_list[0].row()
        report = dlg.tbl_results.model().record(row).value("report")

        dlg.txt_info.setText(report)

    def _manage_btn_action(self):

        dlg = self.dlg_priority_manager

        selected_list = dlg.tbl_results.selectionModel().selectedRows()

        if len(selected_list) == 0 or len(selected_list) > 1:
            dlg.btn_delete.setEnabled(False)
            dlg.btn_status.setEnabled(False)
            dlg.btn_duplicate.setEnabled(False)
            dlg.btn_open.setEnabled(False)
            return

        row = selected_list[0].row()
        status = dlg.tbl_results.model().record(row).value("status")

        if status == "FINISHED":
            dlg.btn_open.setEnabled(False)
            dlg.btn_duplicate.setEnabled(True)
            dlg.btn_status.setEnabled(False)
            dlg.btn_delete.setEnabled(False)
        elif status == "ON PLANNING":
            dlg.btn_open.setEnabled(True)
            dlg.btn_duplicate.setEnabled(True)
            dlg.btn_status.setEnabled(True)
            dlg.btn_delete.setEnabled(False)
        else:
            dlg.btn_open.setEnabled(False)
            dlg.btn_duplicate.setEnabled(False)
            dlg.btn_status.setEnabled(True)
            dlg.btn_delete.setEnabled(True)

    def _filter_table(self):

        dlg = self.dlg_priority_manager

        tbl_result = dlg.tbl_results

        expr = ""
        id_ = tools_qt.get_text(dlg, dlg.txt_filter, False, False)
        result_type = tools_qt.get_combo_value(dlg, dlg.cmb_type, 0)
        expl_id = tools_qt.get_combo_value(dlg, dlg.cmb_expl, 0)
        status = tools_qt.get_combo_value(dlg, dlg.cmb_status, 0)

        expr += f" result_name ILIKE '%{id_}%'"
        expr += f" AND (result_type ILIKE '%{result_type}%')"
        if expl_id:
            expr += f" AND (expl_id = {expl_id})"
        expr += f" AND (status::text ILIKE '%{status}%')"

        # Refresh model with selected filter
        tbl_result.model().setFilter(expr)
        tbl_result.model().select()

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

    def _open_result(self):

        # Get parameters

        dlg = self.dlg_priority_manager
        selected_list = dlg.tbl_results.selectionModel().selectedRows()
        row = selected_list[0].row()
        result_id = dlg.tbl_results.model().record(row).value("result_id")
        result_type = dlg.tbl_results.model().record(row).value("result_type")

        calculate_priority = CalculatePriority(
            type=result_type, mode="edit", result_id=result_id
        )
        calculate_priority.clicked_event()

    def _duplicate_result(self):

        dlg = self.dlg_priority_manager
        selected_list = dlg.tbl_results.selectionModel().selectedRows()
        row = selected_list[0].row()
        result_id = dlg.tbl_results.model().record(row).value("result_id")
        result_type = dlg.tbl_results.model().record(row).value("result_type")

        calculate_priority = CalculatePriority(
            type=result_type, mode="duplicate", result_id=result_id
        )
        calculate_priority.clicked_event()

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

        tools_gw.open_dialog(
            self.dlg_status,
            dlg_name="status_selector",
            plugin_dir=global_vars.plugin_dir,
            plugin_name=global_vars.plugin_name,
        )

    def _set_signals(self):
        dlg = self.dlg_priority_manager
        dlg.btn_open.clicked.connect(self._open_result)
        dlg.btn_duplicate.clicked.connect(self._duplicate_result)
        dlg.btn_status.clicked.connect(self._open_status_selector)
        dlg.btn_delete.clicked.connect(self._delete_result)
        dlg.btn_close.clicked.connect(dlg.reject)

        dlg.txt_filter.textChanged.connect(partial(self._filter_table))
        dlg.cmb_type.currentIndexChanged.connect(partial(self._filter_table))
        dlg.cmb_expl.currentIndexChanged.connect(partial(self._filter_table))
        dlg.cmb_status.currentIndexChanged.connect(partial(self._filter_table))

        selection_model = dlg.tbl_results.selectionModel()
        selection_model.selectionChanged.connect(partial(self._manage_btn_action))
        selection_model.selectionChanged.connect(partial(self._manage_txt_report))
