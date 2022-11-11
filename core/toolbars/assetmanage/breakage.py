"""
This file is part of Giswater 3
The ogram is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.
"""
# -*- coding: utf-8 -*-
from datetime import datetime
from functools import partial
from time import time
from datetime import timedelta
import psycopg2
# import arcpy
import geopandas as gpd
import os
from sqlalchemy import create_engine
# import geoalchemy2

from qgis.core import QgsApplication
from qgis.PyQt.QtCore import QTimer
from qgis.PyQt.QtWidgets import QMenu, QAction, QActionGroup, QFileDialog, QTableView, QAbstractItemView
from qgis.PyQt.QtSql import QSqlTableModel, QSqlDatabase, QSqlQueryModel

from ....settings import tools_qgis, tools_qt, tools_gw, dialog, tools_os, tools_log, tools_db, gw_global_vars
from .... import global_vars

from ...threads.assignation import GwAssignation
from ...ui.ui_manager import IncrementalUi, AssignationUi, PriorityConfigUi


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


    def _fill_action_menu(self):
        """ Fill action menu """

        # disconnect and remove previuos signals and actions
        actions = self.menu.actions()
        for action in actions:
            action.disconnect()
            self.menu.removeAction(action)
            del action
        ag = QActionGroup(self.iface.mainWindow())

        actions = ['CARGA INCREMENTAL', 'ASIGNACIÓN', 'CALCULO PRIORIDADES']
        for action in actions:
            obj_action = QAction(f"{action}", ag)
            self.menu.addAction(obj_action)
            obj_action.triggered.connect(partial(self._get_selected_action, action))

    def _get_selected_action(self, name):
        """ Gets selected action """

        if name == 'CARGA INCREMENTAL':
            self.incremental_load()
        elif name == 'ASIGNACIÓN':
            self.assignation()
        elif name == 'CALCULO PRIORIDADES':
            self.priority_config()
        else:
            msg = f"No action found"
            tools_qgis.show_warning(msg, parameter=name)


    def priority_config(self):

        self.dlg_priority_config = PriorityConfigUi()

        # Define tableviews
        self.qtbl_diameter = self.dlg_priority_config.findChild(QTableView, "tbl_diameter")
        self.qtbl_diameter.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.qtbl_material = self.dlg_priority_config.findChild(QTableView, "tbl_material")
        self.qtbl_material.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.qtbl_engine = self.dlg_priority_config.findChild(QTableView, "tbl_engine")
        self.qtbl_engine.setSelectionBehavior(QAbstractItemView.SelectRows)


        # Triggers
        self._fill_table(self.dlg_priority_config, self.qtbl_diameter, "asset.config_diameter",
                         set_edit_triggers=QTableView.DoubleClicked)
        tools_gw.set_tablemodel_config(self.dlg_priority_config, self.qtbl_diameter, "config_diameter", schema_name='asset')
        self._fill_table(self.dlg_priority_config, self.qtbl_material, "asset.config_material",
                        set_edit_triggers=QTableView.DoubleClicked)
        tools_gw.set_tablemodel_config(self.dlg_priority_config, self.qtbl_material, "config_material", schema_name='asset')
        self._fill_table(self.dlg_priority_config, self.qtbl_engine, "asset.config_engine",
                        set_edit_triggers=QTableView.DoubleClicked)
        tools_gw.set_tablemodel_config(self.dlg_priority_config, self.qtbl_engine, "config_engine", schema_name='asset')

        self.dlg_priority_config.btn_save.clicked.connect(self._execute_config)


        # Open the dialog
        tools_gw.open_dialog(self.dlg_priority_config, dlg_name='incremental')


    def incremental_load(self):

        self.dlg_incremental = IncrementalUi()

        # Disable tab log
        tools_gw.disable_tab_log(self.dlg_incremental)

        # Triggers
        self.dlg_incremental.btn_load.clicked.connect(self._upload_leaks)
        self.dlg_incremental.btn_shp_path.clicked.connect(partial(self._select_file_shp))

        # Open the dialog
        tools_gw.open_dialog(self.dlg_incremental, dlg_name='incremental')


    def assignation(self):

        self.dlg_assignation = AssignationUi()
        dlg = self.dlg_assignation

        # Disable tab log
        tools_gw.disable_tab_log(self.dlg_assignation)

        # Fill combos
        self._fill_assign_combos()

        tools_qt.double_validator(dlg.txt_buffer, min_=0, decimals=0)
        tools_qt.double_validator(dlg.txt_years, min_=0, decimals=0)

        tools_gw.disable_tab_log(dlg)
        dlg.progressBar.hide()
        
        self._assignation_user_values("load")

        self._set_assignation_signals()

        # Open the dialog
        tools_gw.open_dialog(self.dlg_assignation, dlg_name='assignation')


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

    def _execute_assignation(self):
        dlg = self.dlg_assignation

        # TODO: validate inputs

        method, _ = dlg.cmb_method.currentData()
        buffer = int(dlg.txt_buffer.text())
        years = int(dlg.txt_years.text())

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
        self.timer.timeout.connect(self._update_assignation_timer)
        self.timer.start(200)

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
        dlg.buttonBox.rejected.connect(self._cancel_assignation)

        QgsApplication.taskManager().addTask(t)

    def _update_assignation_timer(self):
        elapsed_time = time() - self.t0
        text = str(timedelta(seconds=round(elapsed_time)))
        self.dlg_assignation.lbl_timer.setText(text)

    def _cancel_assignation(self):
        self.thread.cancel()
        tools_gw.fill_tab_log (
            self.dlg_assignation,
            {"info": {"values": [{"message": "Canceling task..."}]}}, 
            reset_text=False, 
            close=False
        )

    def _assignation_ended(self):
        dlg = self.dlg_assignation
        dlg.buttonBox.rejected.disconnect()
        dlg.buttonBox.rejected.connect(dlg.reject)
        self.timer.stop()

    def _upload_leaks(self):

        # Get connection
        print(f"asdf -> {global_vars.db_credentials}")
        engine = create_engine(f"postgresql://{global_vars.db_credentials['user']}:{global_vars.db_credentials['password']}@{global_vars.db_credentials['host']}:{global_vars.db_credentials['port']}/{global_vars.db_credentials['db']}")
        print(f"ENGINE -> {engine}")
        # read in the data
        file = tools_qt.get_text(self.dlg_incremental, self.dlg_incremental.txt_shp_path)
        leaks_shp = gpd.read_file(file)
        leaks_shp.to_postgis('leaks_test', engine, index=True, index_label='Index')


    def _select_file_shp(self):
        """ Select SHP file """

        self.file_inp = tools_qt.get_text(self.dlg_incremental, self.dlg_incremental.txt_shp_path)

        # Get directory of that file
        folder_path = os.path.dirname(self.file_inp)
        if not os.path.exists(folder_path):
            folder_path = os.path.dirname(__file__)
        os.chdir(folder_path)
        message = tools_qt.tr("Select SHP file")
        self.file_inp, filter_ = QFileDialog.getOpenFileName(None, message, "", '*.shp')
        tools_qt.set_widget_text(self.dlg_incremental, self.dlg_incremental.txt_shp_path, self.file_inp)


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


        function_name = 'gw_fct_assetmanage_main'
        body = tools_gw.create_body()
        json_result = tools_gw.execute_procedure(function_name, body, rubber_band=self.rubber_band)
        print(f"json_result -> {json_result}")
