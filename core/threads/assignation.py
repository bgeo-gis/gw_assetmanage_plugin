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
            self._emit_report("Getting data from DB (1/3)...")
            self.setProgress(0)
            # TODO: Filter years
            sql = (
                "SELECT "
                + "l.id AS leak_id, "
                + "a.arc_id AS arc_id, "
                + "ST_DISTANCE(l.the_geom, a.the_geom) AS distance, "
                + f"ST_LENGTH(ST_INTERSECTION(ST_BUFFER(l.the_geom, {self.buffer}), a.the_geom)) AS length "
                + "FROM asset.leaks AS l "
                + f"JOIN asset.v_asset_arc_output AS a ON ST_DWITHIN(l.the_geom, a.the_geom, {self.buffer}) "
            )
            rows = tools_db.get_rows(sql)

            self._emit_report("Calculating leaks per km per year (2/3)...")
            self.setProgress(60)
            leaks = {}
            leaks_by_arc = {}

            for row in rows:
                leak_id, arc_id, distance, length = row

                distance_index = (self.buffer - distance) / self.buffer
                if self.method == "exponential":
                    distance_index = distance_index**2
                index = distance_index * length

                if leak_id not in leaks:
                    leaks[leak_id] = []
                leaks[leak_id].append({"arc_id": arc_id, "index": index})

            for leak_id, arcs in leaks.items():
                sum_indexes = 0
                for arc in arcs:
                    sum_indexes += arc["index"]
                for arc in arcs:
                    if sum_indexes == 0:
                        continue
                    if arc["index"] == 0:
                        continue
                    if arc["arc_id"] not in leaks_by_arc:
                        leaks_by_arc[arc["arc_id"]] = 0
                    leaks_by_arc[arc["arc_id"]] += arc["index"] / sum_indexes

            sql = "SELECT arc_id, ST_LENGTH(the_geom) FROM asset.v_asset_arc_output"
            rows = tools_db.get_rows(sql)
            rleaks = []
            for row in rows:
                arc_id, length = row
                if length and (arc_id in leaks_by_arc):
                    length = length / 1000
                    rleak = leaks_by_arc.get(arc_id, 0) / (length * self.years)
                    if rleak != 0:
                        rleaks.append([arc_id, rleak])

            self._emit_report("Saving results to DB (3/3)...")
            self.setProgress(90)
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
            self.setProgress(100)

            # TODO: Report of leaks without arcs inside buffer
            # TODO: Report of how many arcs have and don't have leaks
            # TODO: Report of max and min rleak

            self._emit_report("Task finished.")
            return True

        except Exception as e:
            self._emit_report(e)
            return False
    
    def _emit_report(self, message):
        self.report.emit({"info": {"values": [{"message": message}]}})
