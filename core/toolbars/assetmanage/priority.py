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

from qgis.PyQt.QtWidgets import QMenu, QAction, QActionGroup
from qgis.PyQt.QtGui import QIcon

from ....settings import tools_qgis, tools_qt, tools_gw, dialog, tools_os, tools_log, tools_db, gw_maptool
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

        # Priority variables
        self.dlg_priority = None


    def clicked_event(self):
        self.priority()


    def priority(self):

        self.dlg_priority = PriorityUi()

        icons_folder = os.path.join(global_vars.plugin_dir, f"icons{os.sep}dialogs{os.sep}20x20")


        # Manage selection group
        # self._manage_selection()

        # Manage expression group
        self._manage_expr()

        # Manage attributes group
        self._manage_attr()

        # Manage radiobuttons
        self.dlg_priority.rb_select_all.toggled.connect(partial(self._manage_radio_buttons, 0))
        self.dlg_priority.rb_select.toggled.connect(partial(self._manage_radio_buttons, 1))
        self.dlg_priority.rb_expr.toggled.connect(partial(self._manage_radio_buttons, 2))
        self.dlg_priority.rb_attr.toggled.connect(partial(self._manage_radio_buttons, 3))
        self.dlg_priority.rb_select_all.setChecked(True)

        self._manage_radio_buttons(1, False)
        self._manage_radio_buttons(2, False)
        self._manage_radio_buttons(3, False)

        # Triggers
        self.dlg_priority.btn_load.clicked.connect(self._open_manager)
        self.dlg_priority.btn_snapping.clicked.connect(self._manage_selection)


        # Open the dialog
        tools_gw.open_dialog(self.dlg_priority, dlg_name='priority')


    def _manage_radio_buttons(self, rbtn, checked):

        if rbtn == 1:
            self.dlg_priority.grb_select.setEnabled(checked)
        elif rbtn == 2:
            self.dlg_priority.grb_expr.setEnabled(checked)
        elif rbtn == 3:
            self.dlg_priority.grb_attr.setEnabled(checked)


    def _open_manager(self):

        self.dlg_priority_manager = PriorityManagerUi()


        # Open the dialog
        tools_gw.open_dialog(self.dlg_priority_manager, dlg_name='priority')


    # region Selection

    # def _manage_selection(self):
    #     self._manage_btn_select()

    # def _manage_btn_select(self):
    #     """ Fill btn_select QMenu """
    #
    #     # Functions
    #     icons_folder = os.path.join(global_vars.plugin_dir, f"icons{os.sep}dialogs{os.sep}svg")
    #
    #     values = [
    #         [0, "Select Feature(s)", os.path.join(icons_folder, "mActionSelectRectangle.svg")],
    #         [1, "Select Features by Polygon", os.path.join(icons_folder, "mActionSelectPolygon.svg")],
    #         [2, "Select Features by Freehand", os.path.join(icons_folder, "mActionSelectRadius.svg")],
    #         [3, "Select Features by Radius", os.path.join(icons_folder, "mActionSelectRadius.svg")],
    #     ]
    #
    #     # Create and populate QMenu
    #     select_menu = QMenu()
    #     for value in values:
    #         num = value[0]
    #         label = value[1]
    #         icon = QIcon(value[2])
    #         action = select_menu.addAction(icon, f"{label}")
    #         action.triggered.connect(partial(self._trigger_action_select, num))
    #
    #     self.dlg_priority.btn_select.setMenu(select_menu)

    def _manage_selection(self):
        """ Slot function for signal 'canvas.selectionChanged' """

        maptool = gw_maptool()
        print(f"MAPTOOL -> {maptool}")


    def _trigger_action_select(self, num):

        # Set active layer
        # layer = tools_qgis.get_layer_by_tablename('v_asset_output')
        layer = tools_qgis.get_layer_by_tablename('arc_asset')
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
        rows = [[25, 'Ø25'],
                [32, 'Ø32'],
                [40, 'Ø40'],
                [50, 'Ø50']]
        tools_qt.fill_combo_values(self.dlg_priority.cmb_dnom, rows, 1, sort_by=0)

        # Combo mapzone
        rows = [['explotacion', 'Explotacion'],
                ['sector', 'Sector'],
                ['sistema', 'Sistema'],
                ['zona_operacion', 'Zona operación']]
        tools_qt.fill_combo_values(self.dlg_priority.cmb_mapzone, rows, 1)

    # endregion
