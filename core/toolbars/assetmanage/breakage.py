"""
This file is part of Giswater 3
The ogram is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.
"""
# -*- coding: utf-8 -*-
import configparser
import os

from functools import partial
from time import time
from datetime import timedelta

from qgis.core import QgsApplication
from qgis.PyQt.QtCore import QTimer, QPoint
from qgis.PyQt.QtWidgets import QMenu, QAction, QActionGroup, QFileDialog, QTableView, QAbstractItemView
from qgis.PyQt.QtSql import QSqlTableModel, QSqlDatabase, QSqlQueryModel

from ....settings import tools_qgis, tools_qt, tools_gw, dialog, tools_os, tools_log, tools_db, gw_global_vars
from .... import global_vars

from ...threads.assignation import GwAssignation
from ...threads.calculatepriority import GwCalculatePriority
from ...ui.ui_manager import AssignationUi, PriorityUi


class AmBreakage(dialog.GwAction):
    """ Button 1: Breakage button
    Dropdown with two options: 'Incremental load' and 'Assigning' """

    def __init__(self, icon_path, action_name, text, toolbar, action_group):

        super().__init__(icon_path, action_name, text, toolbar, action_group)
        self.iface = global_vars.iface

        self.icon_path = icon_path
        self.action_name = action_name
        self.text = text
        self.toolbar = toolbar
        self.action_group = action_group

        # Create a menu and add all the actions
        self.menu = QMenu()
        self.menu.setObjectName("AM_breakage_tools")
        self._fill_action_menu()

        if toolbar is not None:
            self.action.setMenu(self.menu)
            toolbar.addAction(self.action)

        # Incremental variables
        self.dlg_incremental = None

        # Assignation variables
        self.dlg_assignation = None

    def clicked_event(self):
        button = self.action.associatedWidgets()[1]
        menu_point = button.mapToGlobal(QPoint(0,button.height()))
        self.menu.exec(menu_point)


    def _fill_action_menu(self):
        """ Fill action menu """

        # disconnect and remove previuos signals and actions
        actions = self.menu.actions()
        for action in actions:
            action.disconnect()
            self.menu.removeAction(action)
            del action
        ag = QActionGroup(self.iface.mainWindow())

        actions = ['ASIGNACIÓN ROTURAS', 'CÁLCULO PRIORIDADES']
        for action in actions:
            obj_action = QAction(f"{action}", ag)
            self.menu.addAction(obj_action)
            obj_action.triggered.connect(partial(self._get_selected_action, action))

    def _get_selected_action(self, name):
        """ Gets selected action """

        if name == 'ASIGNACIÓN ROTURAS':
            self.assignation()
        elif name == 'CÁLCULO PRIORIDADES':
            self.priority_config()
        else:
            msg = f"No action found"
            tools_qgis.show_warning(msg, parameter=name)


    def priority_config(self):

        self.dlg_priority_global = PriorityUi()

        tools_gw.disable_tab_log(self.dlg_priority_global)


        # Manage form

        # Hidden widgets
        self._manage_hidden_form_global()

        # Define tableviews
        self.qtbl_diameter = self.dlg_priority_global.findChild(QTableView, "tbl_diameter")
        self.qtbl_diameter.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.qtbl_material = self.dlg_priority_global.findChild(QTableView, "tbl_material")
        self.qtbl_material.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.qtbl_engine = self.dlg_priority_global.findChild(QTableView, "tbl_engine")
        self.qtbl_engine.setSelectionBehavior(QAbstractItemView.SelectRows)


        # Triggers
        self._fill_table(self.dlg_priority_global, self.qtbl_diameter, "asset.config_diameter",
                         set_edit_triggers=QTableView.DoubleClicked)
        tools_gw.set_tablemodel_config(self.dlg_priority_global, self.qtbl_diameter, "config_diameter", schema_name='asset')
        self._fill_table(self.dlg_priority_global, self.qtbl_material, "asset.config_material",
                        set_edit_triggers=QTableView.DoubleClicked)
        tools_gw.set_tablemodel_config(self.dlg_priority_global, self.qtbl_material, "config_material", schema_name='asset')
        self._fill_table(self.dlg_priority_global, self.qtbl_engine, "asset.config_engine",
                        set_edit_triggers=QTableView.DoubleClicked)
        tools_gw.set_tablemodel_config(self.dlg_priority_global, self.qtbl_engine, "config_engine", schema_name='asset')

        self.dlg_priority_global.btn_calc.clicked.connect(self._execute_config)
        self.dlg_priority_global.btn_cancel.clicked.connect(partial(tools_gw.close_dialog, self.dlg_priority_global))


        # Open the dialog
        tools_gw.open_dialog(self.dlg_priority_global, dlg_name='incremental')


    def assignation(self):

        self.dlg_assignation = AssignationUi()
        dlg = self.dlg_assignation
        tools_gw.load_settings(dlg)


        # Manage form

        # Hidden widgets
        self._manage_hidden_form_leaks()

        # Fill combos
        self._fill_assign_combos()

        tools_qt.double_validator(dlg.txt_buffer, min_=0, decimals=0)
        tools_qt.double_validator(dlg.txt_years, min_=0, decimals=0)

        # Disable tab log
        tools_gw.disable_tab_log(dlg)
        dlg.progressBar.hide()

        self._assignation_user_values("load")

        self._set_assignation_signals()

        # Open the dialog
        tools_gw.open_dialog(self.dlg_assignation, dlg_name='assignation')


    def _manage_hidden_form_leaks(self):

        status = True
        try:

            # Read the config file
            config = configparser.ConfigParser()
            config_path = os.path.join(global_vars.plugin_dir, f"config{os.sep}config.config")
            if not os.path.exists(config_path):
                print(f"Config file not found: {config_path}")
                return

            config.read(config_path)

            # Get configuration parameters
            if tools_os.set_boolean(config.get("dialog_leaks", "show_check_material")) is not True:
                self.dlg_assignation.lbl_material.setVisible(False)
                self.dlg_assignation.chk_material.setVisible(False)
            if tools_os.set_boolean(config.get("dialog_leaks", "show_check_diameter")) is not True:
                self.dlg_assignation.lbl_diameter.setVisible(False)
                self.dlg_assignation.chk_diameter.setVisible(False)


        except Exception as e:
            print('read_config_file error %s' % e)
            status = False

        return status


    def _fill_assign_combos(self):
        # Combo method
        rows = [['linear', 'lineal'],
                ['exponential', 'exponencial']]
        tools_qt.fill_combo_values(self.dlg_assignation.cmb_method, rows, 1)

    def _assignation_user_values(self, action):
        widgets = [
            "cmb_method",
            "txt_buffer",
            "txt_years",
        ]
        for widget in widgets:
            if action == "load":
                value = tools_gw.get_config_parser(
                    "assignation",
                    widget,
                    "user",
                    "session",
                    plugin=global_vars.user_folder_name,
                )
                tools_qt.set_widget_text(self.dlg_assignation, widget, value)
            elif action == "save":
                value = tools_qt.get_text(self.dlg_assignation, widget, False, False)
                value = value.replace("%", "%%")
                tools_gw.set_config_parser(
                    "assignation",
                    widget,
                    value,
                    plugin=global_vars.user_folder_name,
                )

    def _set_assignation_signals(self):
        dlg = self.dlg_assignation

        dlg.buttonBox.accepted.disconnect()
        dlg.buttonBox.accepted.connect(self._execute_assignation)
        dlg.rejected.connect(partial(self._assignation_user_values, "save"))
        dlg.rejected.connect(partial(tools_gw.close_dialog, dlg))

    def _execute_assignation(self):
        dlg = self.dlg_assignation

        inputs = self._validate_assignation_input()
        if not inputs:
            return
        method, _ = dlg.cmb_method.currentData()
        buffer, years = inputs

        self.thread = GwAssignation(
            "Leak Assignation",
            method,
            buffer,
            years,
        )
        t = self.thread
        t.taskCompleted.connect(self._assignation_ended)
        t.taskTerminated.connect(self._assignation_ended)

        # Set timer
        self.t0 = time()
        self.timer = QTimer()
        self.timer.timeout.connect(partial(self._update_timer, dlg.lbl_timer))
        self.timer.start(250)

        # Log behavior
        t.report.connect(partial(tools_gw.fill_tab_log, dlg, reset_text=False, close=False))

        # Progress bar behavior
        dlg.progressBar.show()
        t.progressChanged.connect(dlg.progressBar.setValue)

        # Button OK behavior
        ok = dlg.buttonBox.StandardButton.Ok
        dlg.buttonBox.button(ok).setEnabled(False)

        # Button Cancel behavior
        dlg.buttonBox.rejected.disconnect()
        dlg.buttonBox.rejected.connect(partial(self._cancel_thread, dlg))

        QgsApplication.taskManager().addTask(t)

    def _validate_assignation_input(self):
        dlg = self.dlg_assignation

        try:
            buffer = int(dlg.txt_buffer.text())
        except ValueError:
            tools_qt.show_info_box("The buffer should be a valid integer number!")
            return

        try:
            years = int(dlg.txt_years.text())
        except ValueError:
            tools_qt.show_info_box("The number of years should be a valid integer number!")
            return

        return buffer, years

    def _update_timer(self, widget):
        elapsed_time = time() - self.t0
        text = str(timedelta(seconds=round(elapsed_time)))
        widget.setText(text)

    def _cancel_thread(self, dlg):
        self.thread.cancel()
        tools_gw.fill_tab_log (
            dlg,
            {"info": {"values": [{"message": "Canceling task..."}]}}, 
            reset_text=False, 
            close=False
        )

    def _assignation_ended(self):
        dlg = self.dlg_assignation
        dlg.buttonBox.rejected.disconnect()
        dlg.buttonBox.rejected.connect(dlg.reject)
        self.timer.stop()


    def _fill_table(self, dialog, widget, table_name, hidde=False, set_edit_triggers=QTableView.NoEditTriggers, expr=None):
        """ Set a model with selected filter.
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


    def _execute_config(self):
        dlg = self.dlg_priority_global

        inputs = self._validate_config_input()
        if not inputs:
            return
        result_name, result_description = inputs

        invalid_diameters_count = tools_db.get_rows("""
            select count(*)
            from asset.arc_asset
            where dnom is null 
                or dnom <= 0
                or dnom > (select max(dnom) from asset.config_diameter)
        """)[0][0]
        if invalid_diameters_count:
            invalid_diameters = [
                x[0]
                for x in tools_db.get_rows(
                    """
                    select distinct dnom
                    from asset.arc_asset
                    where dnom is null 
                        or dnom <= 0
                        or dnom > (select max(dnom) from asset.config_diameter)
                    """
                )
            ]
            text = (
                f"Pipes with invalid diameters: {invalid_diameters_count}.\n"
                f"Invalid diameters: {', '.join(map(lambda x: 'NULL' if x is None else str(x), invalid_diameters))}.\n\n"
                "A diameter value is invalid if it is zero, negative, NULL, "
                "or is greater than the maximum diameter in the configuration table. "
                "These pipes WILL NOT be assigned a priority value.\n\n"
                "Do you want to proceed?"
            )
            if not tools_qt.show_question(text, force_action=True):
                return

        invalid_materials_count = tools_db.get_rows("""
            select count(*)
            from asset.arc_asset a
            where not exists (
                select 1
                from asset.config_material
                where material = a.matcat_id
            )
        """)[0][0]
        if invalid_materials_count:
            invalid_materials = [
                x[0]
                for x in tools_db.get_rows(
                    """
                    select distinct matcat_id
                    from asset.arc_asset a
                    where not exists (
                        select 1
                        from asset.config_material
                        where material = a.matcat_id
                    )
                    """
                )
            ]
            text = (
                f"Pipes with invalid material: {invalid_materials_count}.\n"
                f"Invalid materials: {', '.join(map(lambda x: 'NULL' if x is None else str(x), invalid_materials))}.\n\n"
                "A material value is invalid if "
                "it is not in the material configuration table. "
                "These pipes will be assigned as compliant by default, "
                "which may result in a lower priority value.\n\n"
                "Do you want to proceed?"
            )
            if not tools_qt.show_question(text, force_action=True):
                return

        self.thread = GwCalculatePriority(
            "Priority Calculation",
            result_name,
            result_description,
        )
        t = self.thread
        t.taskCompleted.connect(self._config_ended)
        t.taskTerminated.connect(self._config_ended)

        # Set timer
        self.t0 = time()
        self.timer = QTimer()
        self.timer.timeout.connect(partial(self._update_timer, dlg.lbl_timer))
        self.timer.start(250)

        # Log behavior
        t.report.connect(partial(tools_gw.fill_tab_log, dlg, reset_text=False, close=False))

        # Progress bar behavior
        t.progressChanged.connect(dlg.progressBar.setValue)

        # Button OK behavior
        dlg.btn_calc.setEnabled(False)

        # Button Cancel behavior
        dlg.btn_cancel.clicked.disconnect()
        dlg.btn_cancel.clicked.connect(partial(self._cancel_thread, dlg))

        QgsApplication.taskManager().addTask(t)

    def _validate_config_input(self):
        dlg = self.dlg_priority_global

        result_name = dlg.txt_result_id.text()
        if not len(result_name):
            tools_qt.show_info_box("You must enter an identifier for the result!")
            return

        # TODO: verify if result_name already exists

        description = dlg.txt_descript.text()
        if not len(description):
            tools_qt.show_info_box("You must enter a description for the result!")
            return

        return result_name, description

    def _config_ended(self):
        dlg = self.dlg_priority_global
        dlg.btn_cancel.clicked.disconnect()
        dlg.btn_cancel.clicked.connect(dlg.reject)
        self.timer.stop()


    def _manage_hidden_form_global(self):

        status = True
        try:

            # Read the config file
            config = configparser.ConfigParser()
            config_path = os.path.join(global_vars.plugin_dir, f"config{os.sep}config.config")
            if not os.path.exists(config_path):
                print(f"Config file not found: {config_path}")
                return

            config.read(config_path)

            # Get configuration parameters
            if tools_os.set_boolean(config.get("dialog_priority_global", "show_selection")) is not True:
                print(F"AAA")
                self.dlg_priority_global.grb_selection.setVisible(False)
            else:
                print(F"BBB")
                if tools_os.set_boolean(config.get("dialog_priority_global", "show_maptool")) is not True:
                    self.dlg_priority_global.btn_snapping.setVisible(False)
                if tools_os.set_boolean(config.get("dialog_priority_global", "show_diameter")) is not True:
                    self.dlg_priority_global.lbl_dnom.setVisible(False)
                    self.dlg_priority_global.cmb_dnom.setVisible(False)
                if tools_os.set_boolean(config.get("dialog_priority_global", "show_material")) is not True:
                    self.dlg_priority_global.lbl_material.setVisible(False)
                    self.dlg_priority_global.cmb_material.setVisible(False)
                if tools_os.set_boolean(config.get("dialog_priority_global", "show_exploitation")) is not True:
                    self.dlg_priority_global.lbl_expl.setVisible(False)
                    self.dlg_priority_global.cmb_expl.setVisible(False)
                if tools_os.set_boolean(config.get("dialog_priority_global", "show_presszone")) is not True:
                    pass
            if tools_os.set_boolean(config.get("dialog_priority_global", "show_ivi_button")) is not True:
                pass
            if tools_os.set_boolean(config.get("dialog_priority_global", "show_config")) is not True:
                self.dlg_priority_global.grb_global.setVisible(False)
            else:
                if tools_os.set_boolean(config.get("dialog_priority_global", "show_config_diameter")) is not True:
                    self.dlg_priority_global.tab_widget.tab_diameter.setVisible(False)
                if tools_os.set_boolean(config.get("dialog_priority_global", "show_config_arc")) is not True:
                    self.dlg_priority_global.tab_widget.tab_diameter.setVisible(False)
                if tools_os.set_boolean(config.get("dialog_priority_global", "show_config_material")) is not True:
                    self.dlg_priority_global.tab_widget.tab_material.setVisible(False)
                if tools_os.set_boolean(config.get("dialog_priority_global", "show_config_engine")) is not True:
                    self.dlg_priority_global.tab_widget.tab_engine.setVisible(False)

        except Exception as e:
            print('read_config_file error %s' % e)
            status = False

        return status