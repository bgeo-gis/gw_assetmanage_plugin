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

from ...ui.ui_manager import IncrementalUi, AssignationUi


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
        else:
            msg = f"No action found"
            tools_qgis.show_warning(msg, parameter=name)


    def incremental_load(self):
        print("INCREMENTAL")
        self.dlg_incremental = IncrementalUi()

        # Open the dialog
        tools_gw.open_dialog(self.dlg_incremental, dlg_name='incremental')


    def assignation(self):
        print("ASSIGNATION")
        self.dlg_assignation = AssignationUi()

        # Fill combos
        self._fill_assign_combos()

        # Open the dialog
        tools_gw.open_dialog(self.dlg_assignation, dlg_name='assignation')


    def _fill_assign_combos(self):
        # Combo method
        rows = [['buffer-50', 'buffer-50'],
                ['buffer-100', 'buffer-100'],
                ['buffer-150', 'buffer-150']]
        tools_qt.fill_combo_values(self.dlg_assignation.cmb_method, rows, 1)
