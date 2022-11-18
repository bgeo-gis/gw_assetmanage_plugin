"""
This file is part of Giswater 3
The ogram is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.
"""
# -*- coding: utf-8 -*-
from datetime import datetime
from functools import partial
import os

from qgis.PyQt.QtWidgets import QMenu, QAction, QActionGroup, QTableView
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtSql import QSqlTableModel

from ....settings import tools_qgis, tools_qt, tools_gw, dialog, tools_os, tools_log, tools_db, gw_global_vars
from .... import global_vars

from ...ui.ui_manager import PriorityUi, PriorityManagerUi


class AmPriority(dialog.GwAction):
    """ Button 2: Selection & priority calculation button
    Select features and calculate priorities """

    def __init__(self, icon_path, action_name, text, toolbar, action_group):

        super().__init__(icon_path, action_name, text, toolbar, action_group)
        self.iface = global_vars.iface

        self.icon_path = icon_path
        self.action_name = action_name
        self.text = text
        self.toolbar = toolbar
        self.action_group = action_group
        self.layer_to_work = 'v_asset_arc_output'
        self.layers = {}
        self.layers['arc'] = []
        self.list_ids = {}

        # Priority variables
        self.dlg_priority = None



    def clicked_event(self):
        self.priority()


    def priority(self):

        self.dlg_priority = PriorityUi()

        icons_folder = os.path.join(global_vars.plugin_dir, f"icons{os.sep}dialogs{os.sep}20x20")

        # Manage visibility for Atribute section
        # self.dlg_priority.lbl_dnom.setVisible(False)
        # self.dlg_priority.cmb_dnom.setVisible(False)
        # self.dlg_priority.lbl_material.setVisible(False)
        # self.dlg_priority.cmb_material.setVisible(False)
        # Manage visibility for Expresion section
        self.dlg_priority.rb_expr.setVisible(False)
        self.dlg_priority.grb_expr.setVisible(False)

        # Manage radiobuttons
        # self.dlg_priority.rb_select_all.toggled.connect(partial(self._manage_radio_buttons, 0))
        self.dlg_priority.rb_select.toggled.connect(partial(self._manage_radio_buttons, 1))
        self.dlg_priority.rb_expr.toggled.connect(partial(self._manage_radio_buttons, 2))
        self.dlg_priority.rb_attr.toggled.connect(partial(self._manage_radio_buttons, 3))
        # self.dlg_priority.rb_select_all.setChecked(True)

        self._manage_radio_buttons(1, False)
        self._manage_radio_buttons(2, False)
        self._manage_radio_buttons(3, False)

        # Triggers
        self.dlg_priority.btn_accept.clicked.connect(self._manage_accept)
        self.dlg_priority.btn_load.clicked.connect(self._open_manager)
        self.dlg_priority.btn_save.clicked.connect(self._manage_save)
        self.dlg_priority.cmb_mapzone.currentIndexChanged.connect(partial(self._populate_child))

        # Manage selection group
        self._manage_selection()

        # Manage expression group
        self._manage_expr()

        # Manage attributes group
        self._manage_attr()

        # Open the dialog
        tools_gw.open_dialog(self.dlg_priority, dlg_name='priority')


    def _manage_save(self):

        return

    def _manage_accept(self):
        print(f"LIST IDS -> {self.list_ids}")


    def _manage_radio_buttons(self, rbtn, checked):

        if rbtn == 1:
            self.dlg_priority.grb_select.setEnabled(checked)
        elif rbtn == 2:
            self.dlg_priority.grb_expr.setEnabled(checked)
        elif rbtn == 3:
            self.dlg_priority.grb_attr.setEnabled(checked)


    def _open_manager(self):

        self.dlg_priority_manager = PriorityManagerUi()


        self._fill_table(self.dlg_priority_manager, self.dlg_priority_manager.tbl_selection, "asset.result_selection",
                         set_edit_triggers=QTableView.DoubleClicked)
        tools_gw.set_tablemodel_config(self.dlg_priority_manager, self.dlg_priority_manager.tbl_selection, "result_selection", schema_name='asset')

        # Open the dialog
        tools_gw.open_dialog(self.dlg_priority_manager, dlg_name='priority')


    # region Selection

    def _manage_selection(self):
        """ Slot function for signal 'canvas.selectionChanged' """

        self._manage_btn_snapping()

    def _manage_btn_snapping(self):

        self.feature_type = 'arc'
        layer = tools_qgis.get_layer_by_tablename('v_asset_arc_output')
        self.layers['arc'].append(layer)

        # Remove all previous selections
        self.layers = tools_gw.remove_selection(True, layers=self.layers)


        self.dlg_priority.btn_snapping.clicked.connect(
            partial(tools_gw.selection_init, self, self.dlg_priority, self.layer_to_work))


    def old_manage_btn_snapping(self):
        """ Fill btn_snapping QMenu """

        # Functions
        icons_folder = os.path.join(global_vars.plugin_dir, f"icons{os.sep}dialogs{os.sep}svg")

        values = [
            [0, "Select Feature(s)", os.path.join(icons_folder, "mActionSelectRectangle.svg")],
            [1, "Select Features by Polygon", os.path.join(icons_folder, "mActionSelectPolygon.svg")],
            [2, "Select Features by Freehand", os.path.join(icons_folder, "mActionSelectRadius.svg")],
            [3, "Select Features by Radius", os.path.join(icons_folder, "mActionSelectRadius.svg")],
        ]

        # Create and populate QMenu
        select_menu = QMenu()
        for value in values:
            num = value[0]
            label = value[1]
            icon = QIcon(value[2])
            action = select_menu.addAction(icon, f"{label}")
            action.triggered.connect(partial(self._trigger_action_select, num))

        self.dlg_priority.btn_snapping.setMenu(select_menu)


    def _trigger_action_select(self, num):

        # Set active layer
        layer = tools_qgis.get_layer_by_tablename('v_asset_arc_output')
        self.iface.setActiveLayer(layer)

        if num == 0:
            self.iface.actionSelect().trigger()
        elif num == 1:
            self.iface.actionSelectPolygon().trigger()
        elif num == 2:
            self.iface.actionSelectFreehand().trigger()
        elif num == 3:
            self.iface.actionSelectRadius().trigger()


    def _selection_init(self):
        """ Set canvas map tool to an instance of class 'GwSelectManager' """

        # tools_gw.disconnect_signal('feature_delete')
        self.iface.actionSelect().trigger()
        # self.connect_signal_selection_changed()

    # endregion

    # region Expression

    def _manage_expr(self):
        pass

    # endregion

    # region Attribute

    def _manage_attr(self):
        # Combo dnom
        sql = "SELECT distinct(dnom) as id, dnom as idval FROM cat_arc WHERE dnom is not null;"
        rows = tools_db.get_rows(sql)
        tools_qt.fill_combo_values(self.dlg_priority.cmb_dnom, rows, 1, sort_by=0)

        # Combo material
        sql = "SELECT id, id as idval FROM cat_mat_arc;"
        rows = tools_db.get_rows(sql)
        tools_qt.fill_combo_values(self.dlg_priority.cmb_material, rows, 1)

        # Combo mapzone
        rows = [['exploitation', 'Explotacion', 'SELECT expl_id as id, name as idval FROM ws.exploitation'],
                ['sectore', 'Sector', 'SELECT sector_id as id, name as idval FROM asset.sector'],
                ['macrosector', 'Sistema', 'SELECT macrosector_id as id, name as idval FROM asset.macrosector'],
                ['presszone', 'Zona operación', 'SELECT presszone_id as id, name as idval FROM asset.presszone']]
        tools_qt.fill_combo_values(self.dlg_priority.cmb_mapzone, rows, 1)
        self._populate_child()

    def _populate_child(self):

        sql = tools_qt.get_combo_value(self.dlg_priority, 'cmb_mapzone', 2)
        if sql not in (None, ''):
            rows = tools_db.get_rows(sql)
            tools_qt.fill_combo_values(self.dlg_priority.cmb_child, rows, 1)
        else:
            self.dlg_priority.cmb_child.clear()



    # endregion

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
