from qgis.core import QgsTask
from qgis.PyQt.QtCore import pyqtSignal

from .task import GwTask
from ...settings import tools_db


class GwAssignation(GwTask):
    report = pyqtSignal(dict)
    step = pyqtSignal(str)

    def __init__(
        self, description, method, buffer, years, use_material=False, use_diameter=False
    ):
        super().__init__(description, QgsTask.CanCancel)
        self.method = method
        self.buffer = buffer
        self.years = years
        self.use_material = use_material
        self.use_diameter = use_diameter

    def run(self):
        try:
            max_date, min_date, interval = tools_db.get_row(
                """
                WITH leak_dates AS (
                    SELECT id, startdate AS date_leak
                    FROM asset.leaks)
                SELECT max(date_leak) AS max_date,
                    min(date_leak) AS min_date,
                    max(date_leak) - min(date_leak) AS INTERVAL
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

            sql = f"""
                WITH
                    leak_dates AS (
                        SELECT id, startdate AS date_leak
                        FROM asset.leaks),
                    max_date AS (
                        SELECT max(date_leak)
                        FROM leak_dates)
                SELECT id
                FROM leak_dates
                WHERE date_leak > (
                    (SELECT * FROM max_date) - INTERVAL '{self.years} year'
                )::date
                """
            all_leaks = [x[0] for x in tools_db.get_rows(sql)]

            if self.isCanceled():
                self._emit_report("Task canceled.")
                return False
            self._emit_report("Getting pipe data from DB (2/4)...")
            self.setProgress(25)

            rows = tools_db.get_rows(
                f"""
                WITH
                    leak_dates AS (
                        SELECT id, startdate AS date_leak
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
                    ST_DISTANCE(l.the_geom, a.the_geom) AS distance,
                    ST_LENGTH(
                        ST_INTERSECTION(ST_BUFFER(l.the_geom, {self.buffer}), a.the_geom)
                    ) AS length
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

            self._emit_report("Calculating leaks per km per year (3/4)...")
            self.setProgress(50)
            leaks = {}
            leaks_by_arc = {}
            orphan_leaks = set()

            for row in rows:
                (
                    leak_id,
                    leak_diameter,
                    leak_material,
                    arc_id,
                    arc_diameter,
                    arc_material,
                    distance,
                    length,
                ) = row

                distance_index = (self.buffer - distance) / self.buffer
                if self.method == "exponential":
                    distance_index = distance_index**2
                index = distance_index * length

                if leak_id not in leaks:
                    leaks[leak_id] = []

                leaks[leak_id].append(
                    {
                        "arc_id": arc_id,
                        "index": index,
                        "same_diameter": (
                            # Diameters within 4mm are the same
                            leak_diameter is not None
                            and arc_diameter is not None
                            and leak_diameter - 4 <= arc_diameter <= leak_diameter + 4
                        ),
                        "same_material": (
                            # FIXME: Handle unknown materials
                            leak_material is not None
                            and leak_material == arc_material
                        ),
                    }
                )

            for leak_id in all_leaks:
                if leak_id not in leaks:
                    orphan_leaks.add(leak_id)

            by_material_diameter = 0
            by_material = 0
            by_diameter = 0
            any_pipe = 0

            for leak_id, arcs in leaks.items():
                same_material_exists = any([a["same_material"] for a in arcs])
                same_diameter_exists = any([a["same_diameter"] for a in arcs])

                if (
                    self.use_material
                    and self.use_diameter
                    and same_material_exists
                    and same_diameter_exists
                ):
                    is_arc_valid = lambda x: x["same_material"] and x["same_diameter"]
                    by_material_diameter += 1
                elif self.use_material and same_material_exists:
                    is_arc_valid = lambda x: x["same_material"]
                    by_material += 1
                elif self.use_diameter and same_diameter_exists:
                    is_arc_valid = lambda x: x["same_diameter"]
                    by_diameter += 1
                else:
                    is_arc_valid = lambda x: True
                    any_pipe += 1

                valid_arcs = list(
                    filter(
                        is_arc_valid,
                        arcs,
                    )
                )
                sum_indexes = sum([a["index"] for a in valid_arcs])
                for arc in valid_arcs:
                    if arc["arc_id"] not in leaks_by_arc:
                        leaks_by_arc[arc["arc_id"]] = 0
                    leaks_by_arc[arc["arc_id"]] += arc["index"] / sum_indexes

            if self.isCanceled():
                self._emit_report("Task canceled.")
                return False

            sql = "SELECT arc_id, ST_LENGTH(the_geom) FROM asset.arc_asset"
            rows = tools_db.get_rows(sql)
            total_pipes = len(rows)
            rleaks = []
            for row in rows:
                arc_id, length = row
                if length and (arc_id in leaks_by_arc):
                    length = length / 1000
                    rleak = leaks_by_arc.get(arc_id, 0) / (length * self.years)
                    if rleak != 0:
                        rleaks.append([arc_id, rleak])

            if self.isCanceled():
                self._emit_report("Task canceled.")
                return False

            self._emit_report("Saving results to DB (4/4)...")
            self.setProgress(75)
            sql = (
                "UPDATE asset.arc_input SET rleak = NULL; "
                + "INSERT INTO asset.arc_input (arc_id, rleak) VALUES "
            )
            for arc_id, rleak in rleaks:
                sql += f"({arc_id}, {rleak}),"
            sql = (
                sql[:-1]
                + " ON CONFLICT(arc_id) DO UPDATE SET rleak=excluded.rleak;"
            )
            tools_db.execute_sql(sql)

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

            final_report = [
                "Task finished!",
                f"Leaks within the indicated period: {len(all_leaks)}.",
                f"Leaks without pipes intersecting its buffer: {len(orphan_leaks)}.",
            ]

            if by_material_diameter:
                final_report.append(
                    f"Leaks assigned by material and diameter: {by_material_diameter}."
                )
            if by_material:
                final_report.append(f"Leaks assigned by material only:  {by_material}.")
            if by_diameter:
                final_report.append(f"Leaks assigned by diameter only: {by_diameter}.")
            if any_pipe:
                final_report.append(f"Leaks assigned to any nearby pipes: {any_pipe}.")

            final_report += [
                f"Total of pipes: {total_pipes}.",
                f"Pipes with zero leaks per km per year: {orphan_pipes}.",
                f"Max rleak: {max_rleak} leaks/km.year.",
                f"Min non-zero rleak: {min_rleak} leaks/km.year.",
            ]

            self._emit_report(*final_report)
            return True

        except Exception as e:
            self._emit_report(f"Error: {e}")
            return False

    def _emit_report(self, *args):
        self.report.emit({"info": {"values": [{"message": arg} for arg in args]}})
