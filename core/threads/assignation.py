from qgis.core import QgsTask
from qgis.PyQt.QtCore import pyqtSignal

from .task import GwTask
from ...settings import tools_db


class GwAssignation(GwTask):
    report = pyqtSignal(dict)

    def __init__(self, description, method, buffer, years):
        super().__init__(description, QgsTask.CanCancel)
        self.method = method
        self.buffer = buffer
        self.years = years

    def run(self):
        try:
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

            self.report.emit({"info": {"values": [{"message": len(rleaks)}]}})
            return True

        except Exception as e:
            self.report.emit({"info": {"values": [{"message": e}]}})
            return False
