from qgis.core import QgsTask
from qgis.PyQt.QtCore import pyqtSignal

from .task import GwTask
from ...settings import tools_db


class GwAssignation(GwTask):
    report = pyqtSignal(dict)
    step = pyqtSignal(str)

    def __init__(self, description, method, buffer, years):
        super().__init__(description, QgsTask.CanCancel)
        self.method = method
        self.buffer = buffer
        self.years = years

    def run(self):
        try:
            sql = (
                "WITH "
                + "leak_dates AS (SELECT "
                + "id, to_date(startdate, 'DD/MM/YYYY') AS date_leak "
                + "FROM asset.leaks) "
                + "SELECT "
                + "max(date_leak) AS max_date, "
                + "min(date_leak) AS min_date, "
                + "max(date_leak) - min(date_leak) AS interval "
                + "FROM leak_dates "
            )
            rows = tools_db.get_rows(sql)
            max_date, min_date, interval = rows[0]
            if self.years > interval / 365:
                self._emit_report(
                    "Task canceled: The number of years is greater than the interval disponible.",
                    f"Oldest leak: {min_date}.",
                    f"Newest leak: {max_date}.",
                )
                return False

            self._emit_report("Getting leak data from DB (1/4)...")
            self.setProgress(0)

            sql = (
                "WITH "
                + "leak_dates AS (SELECT "
                + "id, to_date(startdate, 'DD/MM/YYYY') AS date_leak "
                + "FROM asset.leaks), "
                + "max_date AS (SELECT max(date_leak) FROM leak_dates) "
                + "SELECT id FROM leak_dates "
                + f"WHERE date_leak > ((select * from max_date) - interval '{self.years} year')::date "
            )
            all_leaks = [x[0] for x in tools_db.get_rows(sql)]

            if self.isCanceled():
                self._emit_report("Task canceled.")
                return False
            self._emit_report("Getting pipe data from DB (2/4)...")
            self.setProgress(25)

            sql = (
                "WITH "
                + "leak_dates AS (SELECT "
                + "id, to_date(startdate, 'DD/MM/YYYY') AS date_leak "
                + "FROM asset.leaks), "
                + "max_date AS (SELECT max(date_leak) FROM leak_dates) "
                + "SELECT "
                + "l.id AS leak_id, "
                + "l.diameter AS leak_diameter, "
                + "a.arc_id AS arc_id, "
                + "a.dnom AS arc_diameter, "
                + "ST_DISTANCE(l.the_geom, a.the_geom) AS distance, "
                + f"ST_LENGTH(ST_INTERSECTION(ST_BUFFER(l.the_geom, {self.buffer}), a.the_geom)) AS length "
                + "FROM asset.leaks AS l "
                + "JOIN leak_dates AS d USING (id) "
                + "JOIN asset.v_asset_arc_output AS a "
                + f"ON ST_DWITHIN(l.the_geom, a.the_geom, {self.buffer}) "
                + f"WHERE d.date_leak > ((select * from max_date) - interval '{self.years} year')::date "
            )
            rows = tools_db.get_rows(sql)

            if self.isCanceled():
                self._emit_report("Task canceled.")
                return False

            self._emit_report("Calculating leaks per km per year (3/4)...")
            self.setProgress(50)
            leaks = {}
            leaks_by_arc = {}
            orphan_leaks = set()

            for row in rows:
                leak_id, leak_diameter, arc_id, arc_diameter, distance, length = row

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
                            False
                            if not leak_diameter
                            else leak_diameter - 4 <= arc_diameter <= leak_diameter + 4
                        ),
                    }
                )

            for leak_id in all_leaks:
                if leak_id not in leaks:
                    orphan_leaks.add(leak_id)

            for leak_id, arcs in leaks.items():
                sum_indexes = 0
                sum_indexes_by_diameter = 0
                for arc in arcs:
                    sum_indexes += arc["index"]
                    if arc["same_diameter"]:
                        sum_indexes_by_diameter += arc["index"]
                for arc in arcs:
                    if sum_indexes == 0:
                        orphan_leaks.add(leak_id)
                        continue
                    if arc["index"] == 0:
                        continue
                    if sum_indexes_by_diameter and not arc["same_diameter"]:
                        continue
                    if arc["arc_id"] not in leaks_by_arc:
                        leaks_by_arc[arc["arc_id"]] = 0
                    leaks_by_arc[arc["arc_id"]] += arc["index"] / (
                        sum_indexes_by_diameter or sum_indexes
                    )

            if self.isCanceled():
                self._emit_report("Task canceled.")
                return False

            sql = "SELECT arc_id, ST_LENGTH(the_geom) FROM asset.v_asset_arc_output WHERE result_id = 0"
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
                "UPDATE asset.arc_input SET rleak = NULL WHERE result_id = 0; "
                + "INSERT INTO asset.arc_input (arc_id, result_id, rleak) VALUES "
            )
            for arc_id, rleak in rleaks:
                sql += f"({arc_id}, 0, {rleak}),"
            sql = (
                sql[:-1]
                + "ON CONFLICT(arc_id, result_id) DO UPDATE SET rleak=excluded.rleak;"
            )
            tools_db.execute_sql(sql)

            orphan_pipes = tools_db.get_rows(
                "SELECT count(1) FROM asset.v_asset_arc_output "
                + "WHERE result_id = 0 AND (rleak IS NULL or rleak = 0)"
            )[0][0]

            max_rleak, min_rleak = tools_db.get_rows(
                "SELECT max(rleak), min(rleak) FROM asset.v_asset_arc_output "
                + "WHERE result_id = 0 AND rleak IS NOT NULL AND rleak <> 0"
            )[0]

            self.setProgress(100)

            self._emit_report(
                "Task finished!",
                f"Leaks within the indicated period: {len(all_leaks)}.",
                f"Leaks without pipes intersecting its buffer: {len(orphan_leaks)}.",
                f"Total of pipes: {total_pipes}.",
                f"Pipes with zero leaks per km per year: {orphan_pipes}.",
                f"Max rleak: {max_rleak} leaks/km.year.",
                f"Min non-zero rleak: {min_rleak} leaks/km.year.",
            )
            return True

        except Exception as e:
            self._emit_report(f"Error: {e}")
            return False

    def _emit_report(self, *args):
        self.report.emit({"info": {"values": [{"message": arg} for arg in args]}})
