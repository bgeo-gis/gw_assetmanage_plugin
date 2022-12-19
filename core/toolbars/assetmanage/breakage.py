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

from .priority import CalculatePriority
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

        actions = ['ASIGNACIÓN ROTURAS', 'CÁLCULO PRIORIDADES (GLOBAL)']
        for action in actions:
            obj_action = QAction(f"{action}", ag)
            self.menu.addAction(obj_action)
            obj_action.triggered.connect(partial(self._get_selected_action, action))

    def _get_selected_action(self, name):
        """ Gets selected action """

        if name == 'ASIGNACIÓN ROTURAS':
            self.assignation()
        elif name == 'CÁLCULO PRIORIDADES (GLOBAL)':
            self.priority_config()
        else:
            msg = f"No action found"
            tools_qgis.show_warning(msg, parameter=name)


    def priority_config(self):
        calculate_priority = CalculatePriority(type="GLOBAL")
        calculate_priority.clicked_event()

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
                self.dlg_assignation.chk_material.setChecked(False)
                self.dlg_assignation.chk_material.setVisible(False)
            if tools_os.set_boolean(config.get("dialog_leaks", "show_check_diameter")) is not True:
                self.dlg_assignation.lbl_diameter.setVisible(False)
                self.dlg_assignation.chk_diameter.setChecked(False)
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
                if not self.dlg_assignation.txt_buffer.text():
                    self.dlg_assignation.txt_buffer.setText('500')
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
        use_diameter = dlg.chk_diameter.isChecked()
        use_material = dlg.chk_material.isChecked()
        method, _ = dlg.cmb_method.currentData()
        buffer, years = inputs

        if not tools_qt.show_question(
            "This task may take a while to complete. Do you want to continue?"
        ):
            return

        self.thread = GwAssignation(
            "Leak Assignation",
            method,
            buffer,
            years,
            use_material,
            use_diameter,
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

        if buffer > 1000:
            tools_qt.show_info_box("The buffer must be an integer less than 1000!")
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
