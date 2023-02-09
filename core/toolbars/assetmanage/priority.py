"""
This file is part of Giswater 3
The ogram is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.
"""
# -*- coding: utf-8 -*-
from datetime import date, timedelta
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
    QTableWidget,
    QTableWidgetItem,
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


class ConfigCost:
    def __init__(self, data):
        # order the dict by dnom
        self._data = {k: v for k, v in sorted(data.items(), key=lambda i: i[1]["dnom"])}

    def fill_table_widget(self, table_widget):
        # message
        headers = [
            "Arccat_id",
            "Diameter",
            "Replacement cost",
            "Repair cost",
            "Compliance",
        ]
        table_widget.setColumnCount(len(headers))
        table_widget.setHorizontalHeaderLabels(headers)
        for r, row in enumerate(self._data.values()):
            table_widget.insertRow(r)
            table_widget.setItem(r, 0, QTableWidgetItem(row["arccat_id"]))
            table_widget.setItem(r, 1, QTableWidgetItem(str(row["dnom"])))
            table_widget.setItem(r, 2, QTableWidgetItem(str(row["cost_constr"])))
            table_widget.setItem(r, 3, QTableWidgetItem(str(row["cost_repmain"])))
            table_widget.setItem(r, 4, QTableWidgetItem(str(row["compliance"])))

    def get_compliance(self, arccat_id):
        return self._data[arccat_id]["compliance"]

    def get_cost_constr(self, arccat_id):
        return self._data[arccat_id]["cost_constr"]

    def has_arccat_id(self, arccat_id):
        return arccat_id in self._data

    def max_diameter(self):
        return max(x["dnom"] for x in self._data.values())

    def save(self, result_id):
        sql = f"""
            delete from asset.config_cost where result_id = {result_id};
            insert into asset.config_cost
                (result_id, arccat_id, dnom, cost_constr, cost_repmain, compliance)
            values
        """
        for value in self._data.values():
            sql += f"""
                ({result_id},
                '{value["arccat_id"]}',
                {value["dnom"]},
                {value["cost_constr"]},
                {value["cost_repmain"]},
                {value["compliance"]}),
            """
        sql = sql.strip()[:-1]
        tools_db.execute_sql(sql)


def configcost_from_sql(sql):
    rows = tools_db.get_rows(sql)
    data = {}
    for row in rows:
        data[row["arccat_id"]] = {
            "arccat_id": row["arccat_id"],
            "dnom": row["dnom"],
            "cost_constr": row["cost_constr"],
            "cost_repmain": row["cost_repmain"],
            "compliance": row["compliance"],
        }
    return ConfigCost(data)


def configcost_from_tablewidget(table_widget):
    data = {}
    for r in range(table_widget.rowCount()):
        data[table_widget.item(r, 0).text()] = {
            "arccat_id": table_widget.item(r, 0).text(),
            "dnom": float(table_widget.item(r, 1).text()),
            "cost_constr": float(table_widget.item(r, 2).text()),
            "cost_repmain": float(table_widget.item(r, 3).text()),
            "compliance": int(table_widget.item(r, 4).text()),
        }
    return ConfigCost(data)


class ConfigMaterial:
    def __init__(self, data, unknown_material):
        # order the dict by material
        self._data = {k: data[k] for k in sorted(data.keys())}
        self._unknown_material = unknown_material

    def fill_table_widget(self, table_widget):
        # message
        headers = [
            "Material",
            "Prob. of Failure",
            "Max. Longevity",
            "Med. Longevity",
            "Min. Longevity",
            "Default Built Date",
            "Compliance",
        ]
        columns = [
            "material",
            "pleak",
            "age_max",
            "age_med",
            "age_min",
            "builtdate_vdef",
            "compliance",
        ]
        table_widget.setColumnCount(len(headers))
        table_widget.setHorizontalHeaderLabels(headers)
        for r, row in enumerate(self._data.values()):
            table_widget.insertRow(r)
            for c, column in enumerate(columns):
                table_widget.setItem(r, c, QTableWidgetItem(str(row[column])))

    def get_age(self, material, pression):
        if pression < 50:
            return self._get_attr(material, "age_max")
        elif pression < 75:
            return self._get_attr(material, "age_med")
        else:
            return self._get_attr(material, "age_min")

    def get_compliance(self, material):
        return self._get_attr(material, "compliance")

    def get_default_builtdate(self, material):
        return self._get_attr(material, "builtdate_vdef")

    def get_pleak(self, material):
        return self._get_attr(material, "pleak")

    def save(self, result_id):
        sql = f"""
            delete from asset.config_material where result_id = {result_id};
            insert into asset.config_material
                (result_id, material, pleak,
                age_max, age_med, age_min,
                builtdate_vdef, compliance)
            values
        """
        for value in self._data.values():
            sql += f"""
                ({result_id},
                '{value["material"]}',
                {value["pleak"]},
                {value["age_max"]},
                {value["age_med"]},
                {value["age_min"]},
                {value["builtdate_vdef"]},
                {value["compliance"]}),
            """
        sql = sql.strip()[:-1]
        tools_db.execute_sql(sql)

    def _get_attr(self, material, attribute):
        if material in self._data.keys():
            return self._data[material][attribute]
        return self._data[self._unknown_material][attribute]


def configmaterial_from_sql(sql, unknown_material):
    rows = tools_db.get_rows(sql)
    data = {}
    for row in rows:
        data[row["material"]] = {
            "material": row["material"],
            "pleak": row["pleak"],
            "age_max": row["age_max"],
            "age_med": row["age_med"],
            "age_min": row["age_min"],
            "builtdate_vdef": row["builtdate_vdef"],
            "compliance": row["compliance"],
        }
    return ConfigMaterial(data, unknown_material)


def configmaterial_from_tablewidget(table_widget, unknown_material):
    data = {}
    for r in range(table_widget.rowCount()):
        data[table_widget.item(r, 0).text()] = {
            "material": table_widget.item(r, 0).text(),
            "pleak": float(table_widget.item(r, 1).text()),
            "age_max": int(table_widget.item(r, 2).text()),
            "age_med": int(table_widget.item(r, 3).text()),
            "age_min": int(table_widget.item(r, 4).text()),
            "builtdate_vdef": int(table_widget.item(r, 5).text()),
            "compliance": int(table_widget.item(r, 6).text()),
        }
    return ConfigMaterial(data, unknown_material)


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


class CalculatePriorityConfig:
    def __init__(self, type):
        try:
            if type == "GLOBAL":
                dialog_type = "dialog_priority_global"
            elif type == "SELECTION":
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

            self.method = config.get("general", "engine_method")
            self.unknown_material = config.get("general", "unknown_material")
            self.show_budget = config.getboolean(dialog_type, "show_budget")
            self.show_target_year = config.getboolean(dialog_type, "show_target_year")
            self.show_selection = config.getboolean(dialog_type, "show_selection")
            self.show_maptool = config.getboolean(dialog_type, "show_maptool")
            self.show_diameter = config.getboolean(dialog_type, "show_diameter")
            self.show_material = config.getboolean(dialog_type, "show_material")
            self.show_exploitation = config.getboolean(dialog_type, "show_exploitation")
            self.show_presszone = config.getboolean(dialog_type, "show_presszone")
            self.show_ivi_button = config.getboolean(dialog_type, "show_ivi_button")
            self.show_config = config.getboolean(dialog_type, "show_config")
            self.show_config_cost = config.getboolean(dialog_type, "show_config_cost")
            self.show_config_material = config.getboolean(
                dialog_type, "show_config_material"
            )
            self.show_config_engine = config.getboolean(
                dialog_type, "show_config_engine"
            )

        except Exception as e:
            print("read_config_file error %s" % e)


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
        self.config = CalculatePriorityConfig(type)
        self.total_weight = {}

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

        # FIXME: Tables should load result config if "duplicate" or "edit"
        # TODO: Change from QTableView to QTableWidget for more flexibility
        # Define tableviews
        self.qtbl_cost = self.dlg_priority.findChild(QTableWidget, "tbl_cost")
        self.qtbl_cost.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.qtbl_cost.setSortingEnabled(True)
        configcost = configcost_from_sql("select * from asset.config_cost_def")
        configcost.fill_table_widget(self.qtbl_cost)

        self.qtbl_material = self.dlg_priority.findChild(QTableWidget, "tbl_material")
        self.qtbl_material.setSelectionBehavior(QAbstractItemView.SelectRows)
        configmaterial = configmaterial_from_sql(
            "select * from asset.config_material_def", self.config.unknown_material
        )
        configmaterial.fill_table_widget(self.qtbl_material)

        self._fill_engine_options()
        self._set_signals()

        self.dlg_priority.executing = False

        # Open the dialog
        tools_gw.open_dialog(
            self.dlg_priority,
            dlg_name="priority",
            plugin_dir=global_vars.plugin_dir,
            plugin_name=global_vars.plugin_name,
        )

    def _add_total(self, lyt):
        lbl = QLabel()
        lbl.setText(self._tr("Total"))
        value = QLabel()
        position_config = {"layoutname": lyt, "layoutorder": 100}
        tools_gw.add_widget(self.dlg_priority, position_config, lbl, value)
        setattr(self.dlg_priority, f"total_{lyt}", value)
        self._update_total_weight(lyt)

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
        dlg = self.dlg_priority

        self.config_engine_fields = []
        rows = tools_db.get_rows(
            f"""
            select parameter,
                value,
                descript,
                layoutname,
                layoutorder,
                label,
                datatype,
                widgettype
            from asset.config_engine_def
            where method = '{self.config.method}'
            """
        )

        for row in rows:
            self.config_engine_fields.append(
                {
                    "widgetname": row["parameter"],
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
            dlg, [{"fields": self.config_engine_fields}], 0, []
        )

        if self.config.method == "SH":
            dlg.grb_engine_1.setTitle(self._tr("Shamir-Howard parameters"))
            dlg.grb_engine_2.setTitle(self._tr("Weights"))
            self._add_total("lyt_engine_2")
        elif self.config.method == "WM":
            dlg.grb_engine_1.setTitle(self._tr("First iteration"))
            dlg.grb_engine_2.setTitle(self._tr("Second iteration"))
            self._add_total("lyt_engine_1")
            self._add_total("lyt_engine_2")

    def _get_weight_widgets(self, lyt):
        is_weight = lambda x: x["layoutname"] == lyt
        fields = filter(is_weight, self.config_engine_fields)
        return [tools_qt.get_widget(self.dlg_priority, x["widgetname"]) for x in fields]

    def _manage_hidden_form(self):

        if self.config.show_budget is not True and not self.result["budget"]:
            self.dlg_priority.lbl_budget.setVisible(False)
            self.dlg_priority.txt_budget.setVisible(False)
        if self.config.show_target_year is not True and not self.result["target_year"]:
            self.dlg_priority.lbl_year.setVisible(False)
            self.dlg_priority.cmb_year.setVisible(False)
        if (
            self.config.show_selection is not True
            and not self.result["features"]
            and not self.result["dnom"]
            and not self.result["material_id"]
            and not self.result["expl_id"]
            and not self.result["presszone_id"]
        ):
            self.dlg_priority.grb_selection.setVisible(False)
        else:
            if self.config.show_maptool is not True and not self.result["features"]:
                self.dlg_priority.btn_snapping.setVisible(False)
            if self.config.show_diameter is not True and not self.result["dnom"]:
                self.dlg_priority.lbl_dnom.setVisible(False)
                self.dlg_priority.cmb_dnom.setVisible(False)
            if self.config.show_material is not True and not self.result["material_id"]:
                self.dlg_priority.lbl_material.setVisible(False)
                self.dlg_priority.cmb_material.setVisible(False)
            # Hide Explotation filter if there's arcs without expl_id
            null_expl = tools_db.get_row(
                "SELECT 1 FROM asset.arc_asset WHERE expl_id IS NULL"
            )
            if not self.result["expl_id"] and (
                self.config.show_exploitation is not True or null_expl
            ):
                self.dlg_priority.lbl_expl_selection.setVisible(False)
                self.dlg_priority.cmb_expl_selection.setVisible(False)
            # Hide Presszone filter if there's arcs without presszone_id
            null_presszone = tools_db.get_row(
                "SELECT 1 FROM asset.arc_asset WHERE presszone_id IS NULL"
            )
            if not self.result["presszone_id"] and (
                self.config.show_presszone is not True or null_presszone
            ):
                self.dlg_priority.lbl_presszone.setVisible(False)
                self.dlg_priority.cmb_presszone.setVisible(False)
        if self.config.show_ivi_button is not True:
            # TODO: next approach
            pass
        if self.config.show_config is not True:
            self.dlg_priority.grb_global.setVisible(False)
        else:
            if self.config.show_config_cost is not True:
                self.dlg_priority.tab_widget.tab_diameter.setVisible(False)
            if self.config.show_config_material is not True:
                self.dlg_priority.tab_widget.tab_material.setVisible(False)
            if self.config.show_config_engine is not True:
                self.dlg_priority.tab_widget.tab_engine.setVisible(False)

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
            budget,
            target_year,
            config_cost,
            config_material,
            config_engine,
        ) = inputs

        # FIXME: Take into account the unknown material from config.config
        # FIXME: Add filters to checks
        # TODO: Check invalid arccat_ids
        # TODO: Check for invalid materials
        data_checks = tools_db.get_rows(
            f"""
            with list_null_pressures as (
                select count(*)
                from asset.arc_asset
                where press1 is null and press2 is null),
            null_pressures as (
                select 'null_pressures' as check,
                    count as qtd,
                    null as list
                from list_null_pressures)
            select * from null_pressures
            """
        )

        for row in data_checks:
            if not row["qtd"]:
                continue
            if row["check"] == "invalid_diameters":
                msg = (
                    self._tr("Pipes with invalid diameters:")
                    + f" {row['qtd']}.\n"
                    + self._tr("Invalid diameters:")
                    + f" {row['list']}.\n\n"
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
            elif row["check"] == "invalid_materials":
                message = (
                    self._tr("Pipes with invalid materials:")
                    + f" {row['qtd']}.\n"
                    + self._tr("Invalid materials:")
                    + f" {row['list']}.\n\n"
                    + self._tr(
                        "A material is considered invalid if it is not listed in the material configuration table. "
                        "As a result, the material of these pipes will be treated as:"
                    )
                    + f" {self.config.unknown_material}\n\n"
                    + self._tr("Do you want to proceed?")
                )
                if not tools_qt.show_question(message, force_action=True):
                    return
            elif row["check"] == "null_pressures":
                message = (
                    self._tr("Pipes with invalid pressures:")
                    + f" {row['qtd']}.\n"
                    + self._tr(
                        "These pipes have no pressure information for their nodes. "
                        "This will result in them receiving the maximum longevity value for their material, "
                        "which may affect the final priority value."
                    )
                    + "\n\n"
                    + self._tr("Do you want to proceed?")
                )
                if not tools_qt.show_question(message, force_action=True):
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
            budget,
            target_year,
            config_cost,
            config_material,
            config_engine,
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

        if self.config.method == "WM":
            for widget in self._get_weight_widgets("lyt_engine_1"):
                widget.textChanged.connect(
                    partial(self._update_total_weight, "lyt_engine_1")
                )

        for widget in self._get_weight_widgets("lyt_engine_2"):
            widget.textChanged.connect(
                partial(self._update_total_weight, "lyt_engine_2")
            )

    def _tr(self, msg):
        return tools_qt.tr(msg, context_name=global_vars.plugin_name)

    def _update_timer(self, widget):
        elapsed_time = time() - self.t0
        text = str(timedelta(seconds=round(elapsed_time)))
        widget.setText(text)

    def _update_total_weight(self, lyt):
        label = getattr(self.dlg_priority, f"total_{lyt}", None)
        if not label:
            return
        try:
            total = 0
            for widget in self._get_weight_widgets(lyt):
                total += float(widget.text())
            self.total_weight[lyt] = total
            label.setText(str(round(self.total_weight[lyt], 2)))
        except:
            self.total_weight[lyt] = None
            label.setText("Error")

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
        diameter = f"{diameter:g}" if diameter else None
        material = tools_qt.get_combo_value(dlg, "cmb_material") or None

        try:
            budget = float(dlg.txt_budget.text())
        except ValueError:
            if self.config.method == "SH":
                budget = None
            else:
                message = "Please enter a valid number for the budget."
                tools_qt.show_info_box(message, context_name=global_vars.plugin_name)
                return

        target_year = tools_qt.get_combo_value(dlg, "cmb_year") or None
        if self.config.method == "WM" and not target_year:
            message = "Please select a target year."
            tools_qt.show_info_box(message, context_name=global_vars.plugin_name)
            return

        try:
            config_cost = configcost_from_tablewidget(self.qtbl_cost)
        except ValueError as e:
            tools_qt.show_info_box(e)
            return

        try:
            config_material = configmaterial_from_tablewidget(
                self.qtbl_material, self.config.unknown_material
            )
        except ValueError as e:
            tools_qt.show_info_box(e)
            return

        if any(round(total, 5) != 1 for total in self.total_weight.values()):
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
            budget,
            target_year,
            config_cost,
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

        # Combo horizon year
        next_years = [
            [x + date.today().year, str(x + date.today().year)] for x in range(1, 101)
        ]
        tools_qt.fill_combo_values(
            self.dlg_priority.cmb_year, next_years, 1, add_empty=True
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
