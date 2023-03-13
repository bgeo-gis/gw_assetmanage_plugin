import configparser
import traceback
from pathlib import Path

from qgis.core import QgsTask
from qgis.PyQt.QtCore import pyqtSignal

from .task import GwTask
from ..utils import tr
from ... import global_vars
from ...settings import tools_db


class GwAssignation(GwTask):
    report = pyqtSignal(dict)
    step = pyqtSignal(str)

    def __init__(
        self,
        description,
        buffer,
        years,
        max_distance,
        cluster_length,
        filter_material=False,
        diameter_range=None,
    ):
        super().__init__(description, QgsTask.CanCancel)
        self.buffer = buffer
        self.years = years
        self.max_distance = max_distance
        self.cluster_length = cluster_length
        self.filter_material = filter_material
        self.diameter_range = diameter_range

        config_path = Path(global_vars.plugin_dir) / "config" / "config.config"
        config = configparser.ConfigParser()
        config.read(config_path)
        self.unknown_material = config.get("general", "unknown_material")

        self.msg_task_canceled = tr("Task canceled.")

    def run(self):
        try:
            self._emit_report(tr("Getting leak data from DB") + " (1/5)...")
            self.setProgress(0)

            arcs = self._assign_leaks()

            if not arcs:
                return False

            if self.isCanceled():
                self._emit_report(self.msg_task_canceled)
                return False

            arcs = self._calculate_rleak(arcs)
            if not arcs:
                return False

            if self.isCanceled():
                self._emit_report(self.msg_task_canceled)
                return False

            self._emit_report(tr("Saving results to DB") + " (5/5)...")
            self.setProgress(90)
            sql = (
                "UPDATE asset.arc_input SET rleak = NULL; "
                + "INSERT INTO asset.arc_input (arc_id, rleak) VALUES "
            )
            for arc in arcs.values():
                # Convert rleak to leaks/km.year
                rleak = arc.get("rleak", 0) * 1000 / self.years
                sql += f"('{arc['id']}', {rleak}),"
            sql = sql[:-1] + " ON CONFLICT(arc_id) DO UPDATE SET rleak=excluded.rleak;"
            tools_db.execute_sql(sql)

            self.setProgress(100)

            self._emit_report(*self._final_report())
            return True

        except Exception:
            self._emit_report(traceback.format_exc())
            return False

    def _assign_leaks(self):
        interval = tools_db.get_row("select max(date) - min(date) from asset.leaks")[0]
        if self.years:
            self.years = min(self.years, interval / 365)
        else:
            self.years = interval / 365

        if self.isCanceled():
            self._emit_report(self.msg_task_canceled)
            return False

        self._emit_report(tr("Getting pipe data from DB") + " (2/5)...")
        self.setProgress(10)

        rows = tools_db.get_rows(
            f"""
            WITH max_date AS (
                SELECT max(date)
                FROM asset.leaks)
            SELECT l.id AS leak_id,
                l.diameter AS leak_diameter,
                l.material AS leak_material,
                a.arc_id AS arc_id,
                a.dnom AS arc_diameter,
                a.matcat_id AS arc_material,
                ST_LENGTH(a.the_geom) AS arc_length,
                ST_DISTANCE(l.the_geom, a.the_geom) AS distance,
                ST_LENGTH(
                    ST_INTERSECTION(ST_BUFFER(l.the_geom, {self.buffer}), a.the_geom)
                ) AS length
            FROM asset.leaks AS l
            JOIN asset.ext_arc_asset AS a ON
                (l.date > a.builtdate OR a.builtdate IS NULL)
                AND ST_DWITHIN(l.the_geom, a.the_geom, {self.buffer})     
            WHERE l.date > (
                (SELECT * FROM max_date) - INTERVAL '{self.years} year')::date
                AND ST_LENGTH(
                    ST_INTERSECTION(ST_BUFFER(l.the_geom, {self.buffer}), a.the_geom)
                ) > 0
            """
        )

        if self.isCanceled():
            self._emit_report(self.msg_task_canceled)
            return False

        self._emit_report(tr("Assigning leaks to pipes") + " (3/5)...")
        self.setProgress(40)

        leaks = {}
        for row in rows:
            (
                leak_id,
                leak_diameter,
                leak_material,
                arc_id,
                arc_diameter,
                arc_material,
                arc_length,
                distance,
                length,
            ) = row

            index = ((self.buffer - distance) / self.buffer) ** 2 * length

            if leak_id not in leaks:
                leaks[leak_id] = []

            leaks[leak_id].append(
                {
                    "arc_id": arc_id,
                    "arc_material": arc_material,
                    "arc_diameter": arc_diameter,
                    "arc_length": arc_length,
                    "index": index,
                    "same_diameter": (
                        # Diameters within 4mm are the same
                        leak_diameter is not None
                        and arc_diameter is not None
                        and leak_diameter - 4 <= arc_diameter <= leak_diameter + 4
                    ),
                    "same_material": (
                        leak_material is not None
                        and leak_material != self.unknown_material
                        and leak_material == arc_material
                    ),
                }
            )
        self.assigned_leaks = len(leaks)
        self.by_material_diameter = 0
        self.by_material = 0
        self.by_diameter = 0
        self.any_pipe = 0
        arcs = {}
        for leak_id, leak_arcs in leaks.items():
            if any(a["same_material"] and a["same_diameter"] for a in leak_arcs):
                is_arc_valid = lambda x: x["same_material"] and x["same_diameter"]
                self.by_material_diameter += 1
            elif any(a["same_material"] for a in leak_arcs):
                is_arc_valid = lambda x: x["same_material"]
                self.by_material += 1
            elif any(a["same_diameter"] for a in leak_arcs):
                is_arc_valid = lambda x: x["same_diameter"]
                self.by_diameter += 1
            else:
                is_arc_valid = lambda x: True
                self.any_pipe += 1

            valid_arcs = list(
                filter(
                    is_arc_valid,
                    leak_arcs,
                )
            )
            sum_indexes = sum([a["index"] for a in valid_arcs])
            for arc in valid_arcs:
                arc_id = arc["arc_id"]
                if arc_id not in arcs:
                    arcs[arc_id] = {
                        "id": arc_id,
                        "material": arc["arc_material"],
                        "diameter": arc["arc_diameter"],
                        "length": arc["arc_length"],
                        "leaks": 0,
                    }
                arcs[arc_id]["leaks"] += arc["index"] / sum_indexes
        return arcs

    def _calculate_rleak(self, arcs):
        self._emit_report(tr("Calculating rleak values") + " (4/5)...")
        self.setProgress(50)

        arc_list = sorted(arcs.values(), key=lambda a: a["length"], reverse=True)
        where_clause = self._where_clause()
        for index, arc in enumerate(arc_list):
            if arc.get("done", False):
                continue
            if arc.get("leaks", 0) == 0:
                continue
            if arc.get("length", 0) > self.cluster_length:
                if "rleak" not in arc:
                    arc["rleak"] = arc["leaks"] / arc["length"]
                continue
            cluster = tools_db.get_rows(
                f"""
                WITH start_pipe AS (
                        SELECT arc_id, matcat_id, dnom, the_geom
                        FROM asset.ext_arc_asset
                        WHERE arc_id = '{arc["id"]}'),
                    ordered_list AS (
                        SELECT a.arc_id, 
                            a.arc_id = s.arc_id AS start, 
                            a.matcat_id,
                            a.dnom,
                            a.the_geom <-> s.the_geom AS dist,
                            ST_LENGTH(a.the_geom) AS length
                        FROM asset.ext_arc_asset AS a, start_pipe AS s
                        {where_clause}
                        ORDER BY start DESC, dist ASC),
                    cum_list AS (
                        SELECT arc_id, matcat_id, dnom, dist, length,
                            SUM(length) OVER (ORDER BY start DESC, dist ASC) AS cum_length
                        FROM ordered_list
                        WHERE dist < {self.max_distance})
                SELECT arc_id, length
                FROM cum_list
                WHERE cum_length <= COALESCE(
                    (SELECT MIN(cum_length) FROM cum_list WHERE cum_length > {self.cluster_length}),
                    {self.cluster_length})
                """
            )
            if not cluster:
                continue

            sum_leaks = 0
            sum_length = 0

            for row in cluster:
                id, length = row
                if id not in arcs:
                    arcs[id] = {"id": id, "length": length}
                sum_leaks += arcs[id].get("leaks", 0)
                sum_length += length

            rleak = sum_leaks / sum_length
            for row in cluster:
                id, _ = row
                arcs[id]["rleak"] = rleak
                arcs[id]["leaks"] = rleak * arcs[id]["length"]
                arcs[id]["done"] = True

            self.setProgress((90 - 50) / len(arc_list) * index + 50)

            if self.isCanceled():
                self._emit_report(self.msg_task_canceled)
                return False
        return arcs

    def _emit_report(self, *args):
        self.report.emit({"info": {"values": [{"message": arg} for arg in args]}})

    def _final_report(self):
        values = tools_db.get_row(
            f"""
            with total_leaks as (
                select count(*) as total_leaks
                from asset.leaks
                where "date" > (
                    (select max("date") from asset.leaks) - interval '{self.years} year'
                )::date),
            total_pipes as (
                select count(*) as total_pipes
                from asset.ext_arc_asset),
            orphan_pipes as (
                select count(*) as orphan_pipes
                from asset.v_asset_arc_input
                where rleak is null or rleak = 0),
            max_rleak as (
                select max(rleak) as max_rleak
                from asset.arc_input),
            min_rleak as (
                select min(rleak) as min_rleak
                from asset.arc_input
                where rleak is not null and rleak <> 0)
            select *
            from total_leaks
            cross join total_pipes
            cross join orphan_pipes
            cross join max_rleak
            cross join min_rleak
            """
        )

        final_report = [
            "Task finished!",
            f"Period of leaks: {self.years:.4g} years.",
            f"Leaks within the indicated period: {values['total_leaks']}.",
            f"Leaks without pipes intersecting its buffer: {values['total_leaks'] - self.assigned_leaks}.",
        ]

        if self.by_material_diameter:
            final_report.append(
                f"Leaks assigned by material and diameter: {self.by_material_diameter}."
            )
        if self.by_material:
            final_report.append(
                f"Leaks assigned by material only:  {self.by_material}."
            )
        if self.by_diameter:
            final_report.append(f"Leaks assigned by diameter only: {self.by_diameter}.")
        if self.any_pipe:
            final_report.append(f"Leaks assigned to any nearby pipes: {self.any_pipe}.")

        final_report += [
            f"Total of pipes: {values['total_pipes']}.",
            f"Pipes with zero leaks per km per year: {values['orphan_pipes']}.",
            f"Max rleak: {values['max_rleak']} leaks/km.year.",
            f"Min non-zero rleak: {values['min_rleak']} leaks/km.year.",
        ]

        return final_report

    def _where_clause(self):
        conditions = []
        if self.filter_material:
            conditions.append("a.matcat_id = s.matcat_id")
        if self.diameter_range:
            conditions.append(
                f"""
                a.dnom::numeric >= s.dnom::numeric * {self.diameter_range[0]}
                AND a.dnom::numeric <= s.dnom::numeric * {self.diameter_range[1]}
                """
            )
        if conditions:
            return "WHERE " + " AND ".join(conditions)
        return ""
