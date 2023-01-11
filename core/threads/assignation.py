import configparser
import traceback
from pathlib import Path

from qgis.core import QgsTask
from qgis.PyQt.QtCore import pyqtSignal

from .task import GwTask
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
        self.unknown_material = config.get("dialog_leaks", "unknown_material")

    def run(self):
        try:
            # sql = f"""
            #     WITH
            #         leak_dates AS (
            #             SELECT id, "date" AS date_leak
            #             FROM asset.leaks),
            #         max_date AS (
            #             SELECT max(date_leak)
            #             FROM leak_dates)
            #     SELECT id
            #     FROM leak_dates
            #     WHERE date_leak > (
            #         (SELECT * FROM max_date) - INTERVAL '{self.years} year'
            #     )::date
            #     """
            # all_leaks = {x["id"] for x in tools_db.get_rows(sql)}

            arcs = self._assign_leaks()

            if not arcs:
                return False

            if self.isCanceled():
                self._emit_report("Task canceled.")
                return False

            arcs = self._calculate_rleak(arcs)

            if self.isCanceled():
                self._emit_report("Task canceled.")
                return False

            self._emit_report("Saving results to DB (4/4)...")
            self.setProgress(75)
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

            # FIXME: Reimplement the final report
            orphan_pipes = tools_db.get_rows(
                """
                SELECT count(*) FROM asset.arc_input
                    WHERE rleak IS NULL or rleak = 0
                """
            )[0][0]

            max_rleak, min_rleak = tools_db.get_rows(
                """
                SELECT max(rleak), min(rleak) FROM asset.arc_input
                    WHERE rleak IS NOT NULL AND rleak <> 0
                """
            )[0]

            self.setProgress(100)

            # final_report = [
            #     "Task finished!",
            #     f"Leaks within the indicated period: {len(all_leaks)}.",
            #     f"Leaks without pipes intersecting its buffer: {len(orphan_leaks)}.",
            # ]

            # if by_material_diameter:
            #     final_report.append(
            #         f"Leaks assigned by material and diameter: {by_material_diameter}."
            #     )
            # if by_material:
            #     final_report.append(f"Leaks assigned by material only:  {by_material}.")
            # if by_diameter:
            #     final_report.append(f"Leaks assigned by diameter only: {by_diameter}.")
            # if any_pipe:
            #     final_report.append(f"Leaks assigned to any nearby pipes: {any_pipe}.")

            # final_report += [
            #     f"Total of pipes: {total_pipes}.",
            #     f"Pipes with zero leaks per km per year: {orphan_pipes}.",
            #     f"Max rleak: {max_rleak} leaks/km.year.",
            #     f"Min non-zero rleak: {min_rleak} leaks/km.year.",
            # ]

            # self._emit_report(*final_report)
            self._emit_report("Task finished!")
            return True

        except Exception:
            self._emit_report(traceback.format_exc())
            return False

    def _assign_leaks(self):
        max_date, min_date, interval = tools_db.get_row(
            """
            WITH leak_dates AS (
                SELECT id, "date" AS date_leak
                FROM asset.leaks)
            SELECT max(date_leak) AS max_date,
                min(date_leak) AS min_date,
                max(date_leak) - min(date_leak) AS interval
            FROM leak_dates
            """
        )
        if self.years > interval / 365:
            self._emit_report(
                "Task canceled: The number of years is greater than the interval disponible.",
                f"Oldest leak: {min_date}.",
                f"Newest leak: {max_date}.",
            )
            return False

        self._emit_report("Getting leak data from DB (1/4)...")
        self.setProgress(0)

        if self.isCanceled():
            self._emit_report("Task canceled.")
            return False

        self._emit_report("Getting pipe data from DB (2/4)...")
        self.setProgress(25)

        rows = tools_db.get_rows(
            f"""
            WITH
                leak_dates AS (
                    SELECT id, "date" AS date_leak
                    FROM asset.leaks),
                max_date AS (
                    SELECT max(date_leak)
                    FROM leak_dates)
            SELECT l.id AS leak_id,
                l.diameter AS leak_diameter,
                l.material AS leak_material,
                a.arc_id AS arc_id,
                a.dnom AS arc_diameter,
                a.matcat_id AS arc_material,
                ST_LENGTH(a.the_geom) AS arc_length,
                ST_DISTANCE(l.the_geom, a.the_geom) AS distance
            FROM asset.leaks AS l
            JOIN leak_dates AS d USING (id)
            JOIN asset.arc_asset AS a ON 
                ST_DWITHIN(l.the_geom, a.the_geom, {self.buffer})
            WHERE d.date_leak > (
                (SELECT * FROM max_date) - INTERVAL '{self.years} year')::date
            """
        )

        if self.isCanceled():
            self._emit_report("Task canceled.")
            return False

        self._emit_report("Assign leaks to pipes (3/4)...")
        self.setProgress(50)

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
            ) = row

            index = ((self.buffer - distance) / self.buffer) ** 2

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

        # by_material_diameter = 0
        # by_material = 0
        # by_diameter = 0
        # any_pipe = 0
        arcs = {}
        for leak_id, leak_arcs in leaks.items():
            same_material_exists = any([a["same_material"] for a in leak_arcs])
            same_diameter_exists = any([a["same_diameter"] for a in leak_arcs])

            if same_material_exists and same_diameter_exists:
                is_arc_valid = lambda x: x["same_material"] and x["same_diameter"]
                # by_material_diameter += 1
            elif same_material_exists:
                is_arc_valid = lambda x: x["same_material"]
                # by_material += 1
            elif same_diameter_exists:
                is_arc_valid = lambda x: x["same_diameter"]
                # by_diameter += 1
            else:
                is_arc_valid = lambda x: True
                # any_pipe += 1

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
        arc_list = sorted(arcs.values(), key=lambda a: a["length"], reverse=True)
        where_clause = self._where_clause()
        for arc in arc_list:
            if arc.get("done", False):
                continue
            if arc.get("leaks", 0) == 0:
                continue
            if arc.get("length", 0) > self.cluster_length:
                continue
            cluster = tools_db.get_rows(
                f"""
                WITH start_pipe AS (
                        SELECT arc_id, matcat_id, dnom, the_geom
                        FROM asset.arc_asset
                        WHERE arc_id = '{arc["id"]}'),
                    ordered_list AS (
                        SELECT a.arc_id, 
                            a.arc_id = s.arc_id AS start, 
                            a.matcat_id,
                            a.dnom,
                            a.the_geom <-> s.the_geom AS dist,
                            ST_LENGTH(a.the_geom) AS length
                        FROM asset.arc_asset AS a, start_pipe AS s
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

        return arcs

    def _emit_report(self, *args):
        self.report.emit({"info": {"values": [{"message": arg} for arg in args]}})

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
