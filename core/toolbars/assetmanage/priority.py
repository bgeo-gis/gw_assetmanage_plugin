"""
This file is part of Giswater 3
The ogram is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.
"""
# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from functools import partial
from time import time
import configparser
import os
import json

from qgis.core import QgsApplication
from qgis.PyQt.QtCore import QTimer
from qgis.PyQt.QtWidgets import (
    QLabel,
    QMenu,
    QAbstractItemView,
    QAction,
    QActionGroup,
    QTableView,
)
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtSql import QSqlTableModel

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

from ...threads.calculatepriority import GwCalculatePriority
from ...ui.ui_manager import PriorityUi, PriorityManagerUi


def table2data(table_view):
    model = table_view.model()
    data = []
    for row in range(model.rowCount()):
        record = model.record(row)
        data.append(
            {
                record.fieldName(i): record.value(i)
                for i in range(len(record))
                if not table_view.isColumnHidden(i)
            }
        )
    return data


class AmPriority(dialog.GwAction):
    """Button 2: Selection & priority calculation button
    Select features and calculate priorities"""

    def __init__(self, icon_path, action_name, text, toolbar, action_group):

        super().__init__(icon_path, action_name, text, toolbar, action_group)
        self.iface = global_vars.iface

        self.icon_path = icon_path
        self.action_name = action_name
        self.text = text
        self.toolbar = toolbar
        self.action_group = action_group

    def clicked_event(self):
        calculate_priority = CalculatePriority(type="SELECTION")
        calculate_priority.clicked_event()


class CalculatePriority:
    def __init__(self, type="GLOBAL", mode="new", result_id=None):
        if mode != "new":
            if not result_id:
                raise ValueError(f"For mode '{mode}', an result_id must be informed.")
            self.result = tools_db.get_row(
                f"""
                SELECT result_id AS id,
                    result_name AS name,
                    result_type AS type,
                    descript,
                    expl_id,
                    budget,
                    target_year,
                    status,
                    presszone_id,
                    material_id,
                    features,
                    dnom
                FROM asset.cat_result
                WHERE result_id = {result_id}
                """
            )
        else:
            self.result = {
                "id": None,
                "name": None,
                "type": None,
                "descript": None,
                "expl_id": None,
                "budget": None,
                "target_year": None,
                "status": None,
                "presszone_id": None,
                "material_id": None,
                "features": None,
                "dnom": None,
            }
        self.type = type if mode == "new" else self.result["type"]
        self.mode = mode
        self.layer_to_work = "v_asset_arc_input"
        self.layers = {}
        self.layers["arc"] = []
        self.list_ids = {}

        # Priority variables
        self.dlg_priority = None

    def clicked_event(self):
        self.dlg_priority = PriorityUi()
        dlg = self.dlg_priority
        dlg.setWindowTitle(dlg.windowTitle() + f" ({self._tr(self.type)})")

        tools_gw.disable_tab_log(self.dlg_priority)

        icons_folder = os.path.join(
            global_vars.plugin_dir, f"icons{os.sep}dialogs{os.sep}20x20"
        )
        icon_path = os.path.join(icons_folder, str(137) + ".png")
        if os.path.exists(icon_path):
            self.dlg_priority.btn_snapping.setIcon(QIcon(icon_path))

        # Manage form

        # Hidden widgets
        self._manage_hidden_form()

        # Manage selection group
        self._manage_selection()

        # Manage attributes group
        self._manage_attr()

        # Define tableviews
        self.qtbl_diameter = self.dlg_priority.findChild(QTableView, "tbl_diameter")
        self.qtbl_diameter.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.qtbl_material = self.dlg_priority.findChild(QTableView, "tbl_material")
        self.qtbl_material.setSelectionBehavior(QAbstractItemView.SelectRows)

        # Triggers
        self._fill_table(
            self.dlg_priority,
            self.qtbl_diameter,
            "asset.config_diameter_def",
            set_edit_triggers=QTableView.DoubleClicked,
        )
        tools_gw.set_tablemodel_config(
            self.dlg_priority,
            self.qtbl_diameter,
            "config_diameter_def",
            schema_name="asset",
        )
        self._fill_table(
            self.dlg_priority,
            self.qtbl_material,
            "asset.config_material_def",
            set_edit_triggers=QTableView.DoubleClicked,
        )
        tools_gw.set_tablemodel_config(
            self.dlg_priority,
            self.qtbl_material,
            "config_material_def",
            schema_name="asset",
        )

        self._fill_engine_options()
        self._set_signals()

        self.dlg_priority.executing = False

        # Open the dialog
        tools_gw.open_dialog(self.dlg_priority, dlg_name="priority")

    def _calculate_ended(self):
        dlg = self.dlg_priority
        dlg.btn_cancel.clicked.disconnect()
        dlg.btn_cancel.clicked.connect(dlg.reject)
        dlg.executing = False
        self.timer.stop()

    def _cancel_thread(self, dlg):
        self.thread.cancel()
        tools_gw.fill_tab_log(
            dlg,
            {"info": {"values": [{"message": self._tr("Canceling task...")}]}},
            reset_text=False,
            close=False,
        )

    def _fill_engine_options(self):
        self.config_engine_fields = []
        rows = tools_db.get_rows(
            """
            select parameter,
                value,
                descript,
                layoutname,
                layoutorder,
                label,
                datatype,
                widgettype
            from asset.config_engine_def
            """
        )

        for row in rows:
            self.config_engine_fields.append(
                {
                    "widgetname": row[0],
                    "value": row[1],
                    "tooltip": row[2],
                    "layoutname": row[3],
                    "layoutorder": row[4],
                    "label": row[5],
                    "datatype": row[6],
                    "widgettype": row[7],
                    "isMandatory": True,
                }
            )
        tools_gw.build_dialog_options(
            self.dlg_priority, [{"fields": self.config_engine_fields}], 0, []
        )

        lbl = QLabel()
        lbl.setText(self._tr("Total"))
        lbl_total_weight = QLabel()
        self.dlg_priority.lbl_total_weight = lbl_total_weight
        position_config = {"layoutname": "lyt_weights", "layoutorder": 100}
        tools_gw.add_widget(self.dlg_priority, position_config, lbl, lbl_total_weight)
        self._update_total_weight()

    def _get_weight_widgets(self):
        is_weight = lambda x: x["layoutname"] == "lyt_weights"
        fields = filter(is_weight, self.config_engine_fields)
        return [tools_qt.get_widget(self.dlg_priority, x["widgetname"]) for x in fields]

    def _manage_hidden_form(self):
        status = True
        try:
            if self.type == "GLOBAL":
                dialog_type = "dialog_priority_global"
            elif self.type == "SELECTION":
                dialog_type = "dialog_priority_selection"
            else:
                raise ValueError(
                    self._tr(
                        "Invalid value for type of priority dialog. "
                        "Please pass either 'GLOBAL' or 'SELECTION'. "
                        "Value passed:"
                    )
                    + f" '{self.type}'."
                )

            # Read the config file
            config = configparser.ConfigParser()
            config_path = os.path.join(
                global_vars.plugin_dir, f"config{os.sep}config.config"
            )
            if not os.path.exists(config_path):
                print(f"Config file not found: {config_path}")
                return

            config.read(config_path)

            # Get configuration parameters
            if (
                config.getboolean(dialog_type, "show_budget") is not True
                and not self.result["budget"]
            ):
                self.dlg_priority.lbl_budget.setVisible(False)
                self.dlg_priority.txt_budget.setVisible(False)
            if (
                config.getboolean(dialog_type, "show_target_year") is not True
                and not self.result["target_year"]
            ):
                self.dlg_priority.lbl_year.setVisible(False)
                self.dlg_priority.cmb_year.setVisible(False)
            if (
                config.getboolean(dialog_type, "show_selection") is not True
                and not self.result["features"]
                and not self.result["dnom"]
                and not self.result["material_id"]
                and not self.result["expl_id"]
                and not self.result["presszone_id"]
            ):
                self.dlg_priority.grb_selection.setVisible(False)
            else:
                if (
                    config.getboolean(dialog_type, "show_maptool") is not True
                    and not self.result["features"]
                ):
                    self.dlg_priority.btn_snapping.setVisible(False)
                if (
                    config.getboolean(dialog_type, "show_diameter") is not True
                    and not self.result["dnom"]
                ):
                    self.dlg_priority.lbl_dnom.setVisible(False)
                    self.dlg_priority.cmb_dnom.setVisible(False)
                if (
                    config.getboolean(dialog_type, "show_material") is not True
                    and not self.result["material_id"]
                ):
                    self.dlg_priority.lbl_material.setVisible(False)
                    self.dlg_priority.cmb_material.setVisible(False)
                # Hide Explotation filter if there's arcs without expl_id
                null_expl = tools_db.get_row(
                    "SELECT 1 FROM asset.arc_asset WHERE expl_id IS NULL"
                )
                if not self.result["expl_id"] and (
                    config.getboolean(dialog_type, "show_exploitation") is not True
                    or null_expl
                ):
                    self.dlg_priority.lbl_expl_selection.setVisible(False)
                    self.dlg_priority.cmb_expl_selection.setVisible(False)
                # Hide Presszone filter if there's arcs without presszone_id
                null_presszone = tools_db.get_row(
                    "SELECT 1 FROM asset.arc_asset WHERE presszone_id IS NULL"
                )
                if not self.result["presszone_id"] and (
                    config.getboolean(dialog_type, "show_presszone") is not True
                    or null_presszone
                ):
                    self.dlg_priority.lbl_presszone.setVisible(False)
                    self.dlg_priority.cmb_presszone.setVisible(False)
            if config.getboolean(dialog_type, "show_ivi_button") is not True:
                # TODO: next approach
                pass
            if config.getboolean(dialog_type, "show_config") is not True:
                self.dlg_priority.grb_global.setVisible(False)
            else:
                if config.getboolean(dialog_type, "show_config_diameter") is not True:
                    self.dlg_priority.tab_widget.tab_diameter.setVisible(False)
                if config.getboolean(dialog_type, "show_config_arc") is not True:
                    self.dlg_priority.tab_widget.tab_diameter.setVisible(False)
                if config.getboolean(dialog_type, "show_config_material") is not True:
                    self.dlg_priority.tab_widget.tab_material.setVisible(False)
                if config.getboolean(dialog_type, "show_config_engine") is not True:
                    self.dlg_priority.tab_widget.tab_engine.setVisible(False)

        except Exception as e:
            print("read_config_file error %s" % e)
            status = False

        return status

    def _manage_calculate(self):
        dlg = self.dlg_priority

        inputs = self._validate_inputs()
        if not inputs:
            return

        (
            result_name,
            result_description,
            status,
            features,
            exploitation,
            presszone,
            diameter,
            material,
            config_diameter,
            config_material,
            config_engine,
        ) = inputs

        invalid_diameters_count = tools_db.get_row(
            f"""
            select count(*)
            from asset.arc_asset
            where dnom is null 
                or dnom::numeric <= 0
                or dnom::numeric > ({max(config_diameter.keys())})
            """
        )[0]
        if invalid_diameters_count:
            invalid_diameters = [
                x[0]
                for x in tools_db.get_rows(
                    f"""
                    select distinct dnom
                    from asset.arc_asset
                    where dnom is null 
                        or dnom::numeric <= 0
                        or dnom::numeric > ({max(config_diameter.keys())})
                    """
                )
            ]
            msg = (
                self._tr("Pipes with invalid diameters:")
                + f" {invalid_diameters_count}.\n"
                + self._tr("Invalid diameters:")
                + f" {', '.join(map(lambda x: 'NULL' if x is None else str(x), invalid_diameters))}.\n\n"
                + self._tr(
                    "A diameter value is considered invalid if it is zero, negative, "
                    "NULL or greater than the maximum diameter in the configuration table. "
                    "As a result, these pipes will NOT be assigned a priority value."
                )
                + "\n\n"
                + self._tr("Do you want to proceed?")
            )
            if not tools_qt.show_question(msg, force_action=True):
                return

        # FIXME: Take into account the unknown material from config.config
        invalid_materials_count = tools_db.get_row(
            f"""
            select count(*)
            from asset.arc_asset a
            where matcat_id not in ('{"','".join(config_material.keys())}')
            """
        )[0]
        if invalid_materials_count:
            invalid_materials = [
                x[0]
                for x in tools_db.get_rows(
                    f"""
                    select distinct matcat_id
                    from asset.arc_asset a
                    where matcat_id not in ('{"','".join(config_material.keys())}')
                    """
                )
            ]
            msg = (
                self._tr("Pipes with invalid materials:")
                + f" {invalid_materials_count}.\n"
                + self._tr("Invalid materials:")
                + f" {', '.join(map(lambda x: 'NULL' if x is None else str(x), invalid_materials))}.\n\n"
                + self._tr(
                    "A material is considered invalid if it is not listed in the material configuration table. "
                    "As a result, these pipes will be set as compliant by default, which may affect the priority value."
                )
                + "\n\n"
                + self._tr("Do you want to proceed?")
            )
            if not tools_qt.show_question(msg, force_action=True):
                return

        self.thread = GwCalculatePriority(
            self._tr("Calculate Priority"),
            self.type,
            result_name,
            result_description,
            status,
            features,
            exploitation,
            presszone,
            diameter,
            material,
            budget=None,
            target_year=None,
            config_diameter=config_diameter,
            config_material=config_material,
            config_engine=config_engine,
        )
        t = self.thread
        t.taskCompleted.connect(self._calculate_ended)
        t.taskTerminated.connect(self._calculate_ended)

        # Set timer
        self.t0 = time()
        self.timer = QTimer()
        self.timer.timeout.connect(partial(self._update_timer, dlg.lbl_timer))
        self.timer.start(250)

        # Log behavior
        t.report.connect(
            partial(tools_gw.fill_tab_log, dlg, reset_text=False, close=False)
        )

        # Progress bar behavior
        t.progressChanged.connect(dlg.progressBar.setValue)

        # Button OK behavior
        dlg.btn_calc.setEnabled(False)

        # Button Cancel behavior
        dlg.btn_cancel.clicked.disconnect()
        dlg.btn_cancel.clicked.connect(partial(self._cancel_thread, dlg))

        dlg.executing = True
        QgsApplication.taskManager().addTask(t)

    # region Selection

    def _manage_selection(self):
        """Slot function for signal 'canvas.selectionChanged'"""

        self._manage_btn_snapping()

    def _manage_btn_snapping(self):

        # FIXME: In case of "duplicate" or "edit", load result selection

        self.feature_type = "arc"
        layer = tools_qgis.get_layer_by_tablename(self.layer_to_work)
        self.layers["arc"].append(layer)

        # Remove all previous selections
        self.layers = tools_gw.remove_selection(True, layers=self.layers)

        self.dlg_priority.btn_snapping.clicked.connect(
            partial(
                tools_gw.selection_init, self, self.dlg_priority, self.layer_to_work
            )
        )

    def old_manage_btn_snapping(self):
        """Fill btn_snapping QMenu"""

        # Functions
        icons_folder = os.path.join(
            global_vars.plugin_dir, f"icons{os.sep}dialogs{os.sep}svg"
        )

        values = [
            [
                0,
                "Select Feature(s)",
                os.path.join(icons_folder, "mActionSelectRectangle.svg"),
            ],
            [
                1,
                "Select Features by Polygon",
                os.path.join(icons_folder, "mActionSelectPolygon.svg"),
            ],
            [
                2,
                "Select Features by Freehand",
                os.path.join(icons_folder, "mActionSelectRadius.svg"),
            ],
            [
                3,
                "Select Features by Radius",
                os.path.join(icons_folder, "mActionSelectRadius.svg"),
            ],
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
        layer = tools_qgis.get_layer_by_tablename(self.layer_to_work)
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
        """Set canvas map tool to an instance of class 'GwSelectManager'"""

        # tools_gw.disconnect_signal('feature_delete')
        self.iface.actionSelect().trigger()
        # self.connect_signal_selection_changed()

    # endregion

    def _set_signals(self):
        dlg = self.dlg_priority
        dlg.btn_calc.clicked.connect(self._manage_calculate)
        dlg.btn_cancel.clicked.connect(partial(tools_gw.close_dialog, dlg))
        dlg.rejected.connect(partial(tools_gw.close_dialog, dlg))

        for widget in self._get_weight_widgets():
            widget.textChanged.connect(self._update_total_weight)

    def _tr(self, msg):
        return tools_qt.tr(msg, context_name=global_vars.plugin_name)

    def _update_timer(self, widget):
        elapsed_time = time() - self.t0
        text = str(timedelta(seconds=round(elapsed_time)))
        widget.setText(text)

    def _update_total_weight(self):
        try:
            total = 0
            for widget in self._get_weight_widgets():
                total += float(widget.text())
            self.total_weight = total
            self.dlg_priority.lbl_total_weight.setText(str(round(self.total_weight, 2)))
        except:
            self.total_weight = None
            self.dlg_priority.lbl_total_weight.setText("Error")

    def _validate_inputs(self):
        dlg = self.dlg_priority

        result_name = dlg.txt_result_id.text()
        if not result_name:
            msg = "Please provide a result name."
            tools_qt.show_info_box(msg, context_name=global_vars.plugin_name)
            return
        if tools_db.get_row(
            f"""
            select * from asset.cat_result
            where result_name = '{result_name}'
            """
        ):
            msg = "This result name already exists"
            info = "Please choose a different name."
            tools_qt.show_info_box(
                msg,
                inf_text=info,
                context_name=global_vars.plugin_name,
                parameter=result_name,
            )
            return

        result_description = self.dlg_priority.txt_descript.text()
        status = tools_qt.get_combo_value(dlg, dlg.cmb_status)

        features = None
        if "arc" in self.list_ids:
            features = self.list_ids["arc"] or None

        exploitation = tools_qt.get_combo_value(dlg, "cmb_expl_selection") or None
        presszone = tools_qt.get_combo_value(dlg, "cmb_presszone") or None
        diameter = tools_qt.get_combo_value(dlg, "cmb_dnom") or None
        material = tools_qt.get_combo_value(dlg, "cmb_material") or None

        config_diameter = {}
        for row in table2data(self.qtbl_diameter):
            if not row["dnom"]:
                msg = "Empty value detected in 'Diameter' tab. Please enter a value for diameter."
                tools_qt.show_info_box(msg, context_name=global_vars.plugin_name)
                return
            if not row["cost_constr"]:
                msg = "Please provide the replacing cost for diameter"
                tools_qt.show_info_box(
                    msg, context_name=global_vars.plugin_name, parameter=row["dnom"]
                )
                return
            if not row["cost_repmain"]:
                msg = "Please provide the repairing cost for diameter"
                tools_qt.show_info_box(
                    msg, context_name=global_vars.plugin_name, parameter=row["dnom"]
                )
                return
            if not (0 <= row["compliance"] <= 10):
                msg = "Invalid compliance value for diameter"
                info = "Compliance value must be between 0 and 10 inclusive."
                tools_qt.show_info_box(
                    msg,
                    inf_text=info,
                    context_name=global_vars.plugin_name,
                    parameter=row["dnom"],
                )
            config_diameter[int(row["dnom"])] = {
                k: v for k, v in row.items() if k != "dnom"
            }

        config_material = {}
        for row in table2data(self.qtbl_material):
            if not (0 <= row["compliance"] <= 10):
                msg = "Invalid compliance value for material"
                info = "Compliance value must be between 0 and 10 inclusive."
                tools_qt.show_info_box(
                    msg,
                    inf_text=info,
                    context_name=global_vars.plugin_name,
                    parameter=row["material"],
                )
                return
            config_material[row["material"]] = {
                k: v for k, v in row.items() if k != "material"
            }

        if round(self.total_weight, 5) != 1:
            msg = (
                "The sum of weights must equal 1. Please adjust the values accordingly."
            )
            tools_qt.show_info_box(msg, context_name=global_vars.plugin_name)
            return
        config_engine = {}
        for field in self.config_engine_fields:
            widget_name = field["widgetname"]
            try:
                config_engine[widget_name] = float(
                    tools_qt.get_widget(dlg, widget_name).text()
                )
            except:
                msg = "Invalid value for field"
                info = "Please enter a valid number."
                tools_qt.show_info_box(
                    msg,
                    inf_text=info,
                    context_name=global_vars.plugin_name,
                    parameter=field["label"],
                )
                return

        return (
            result_name,
            result_description,
            status,
            features,
            exploitation,
            presszone,
            diameter,
            material,
            config_diameter,
            config_material,
            config_engine,
        )

    # region Attribute

    def _manage_attr(self):
        # Combo status
        rows = tools_db.get_rows("SELECT id, idval FROM asset.value_status")
        tools_qt.fill_combo_values(self.dlg_priority.cmb_status, rows, 1)
        tools_qt.set_combo_value(
            self.dlg_priority.cmb_status, "ON PLANNING", 0, add_new=False
        )
        tools_qt.set_combo_item_select_unselectable(
            self.dlg_priority.cmb_status, list_id=["FINISHED"]
        )

        # Combo dnom
        sql = "SELECT distinct(dnom::float) as id, dnom as idval FROM cat_arc WHERE dnom is not null ORDER BY id;"
        rows = tools_db.get_rows(sql)
        tools_qt.fill_combo_values(
            self.dlg_priority.cmb_dnom, rows, 1, sort_by=0, add_empty=True
        )
        tools_qt.set_combo_value(
            self.dlg_priority.cmb_dnom, self.result["dnom"], 0, add_new=False
        )

        # Combo material
        sql = "SELECT id, id as idval FROM cat_mat_arc ORDER BY id;"
        rows = tools_db.get_rows(sql)
        tools_qt.fill_combo_values(
            self.dlg_priority.cmb_material, rows, 1, add_empty=True
        )
        tools_qt.set_combo_value(
            self.dlg_priority.cmb_material, self.result["material_id"], 0, add_new=False
        )

        # Combo exploitation
        sql = "SELECT expl_id as id, name as idval FROM asset.exploitation;"
        rows = tools_db.get_rows(sql)
        tools_qt.fill_combo_values(
            self.dlg_priority.cmb_expl_selection, rows, 1, add_empty=True
        )
        tools_qt.set_combo_value(
            self.dlg_priority.cmb_expl_selection,
            self.result["expl_id"],
            0,
            add_new=False,
        )

        # Combo presszone
        sql = "SELECT presszone_id as id, name as idval FROM asset.presszone"
        rows = tools_db.get_rows(sql)
        tools_qt.fill_combo_values(
            self.dlg_priority.cmb_presszone, rows, 1, add_empty=True
        )
        tools_qt.set_combo_value(
            self.dlg_priority.cmb_presszone,
            self.result["presszone_id"],
            0,
            add_new=False,
        )

    # endregion

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
            model.setEditStrategy(QSqlTableModel.OnManualSubmit)
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
