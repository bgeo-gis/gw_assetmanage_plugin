from qgis.core import QgsTask
from qgis.PyQt.QtCore import pyqtSignal

from .task import GwTask
from ...settings import tools_db


class GwCalculatePriority(GwTask):
    report = pyqtSignal(dict)
    step = pyqtSignal(str)

    def __init__(self, description):
        super().__init__(description, QgsTask.CanCancel)

    def run(self):
        try:
            self._emit_report("Getting data from DB (1/4)...")
            self.setProgress(10)

            sql = (
                "select parameter, value::float, active "
                + "from asset.config_engine "
                + "where method = 'S-H' "
            )
            rows = tools_db.get_rows(sql)
            config_engine = {}
            for row in rows:
                parameter, value, _ = row
                config_engine[parameter] = value
            discount_rate = config_engine["drate"]
            break_growth_rate = config_engine["bratemain0"]

            sql = (
                "select dnom, cost_constr, cost_repmain, compliance "
                + "from asset.config_diameter "
            )
            rows = tools_db.get_rows(sql)
            diameters = {}
            for row in rows:
                dnom, cost_constr, cost_repmain, _ = row
                diameters[dnom] = {
                    "replacement_cost": cost_constr,
                    "repairing_cost": cost_repmain,
                }

            sql = (
                "select a.arc_id, a.matcat_id, a.dnom, "
                + "st_length(a.the_geom) length, coalesce(ai.rleak, 0) rleak "
                + "from asset.arc_asset a "
                + "left join asset.arc_input ai "
                + "on (a.arc_id = ai.arc_id and ai.result_id = 0) "
            )
            arcs = tools_db.get_rows(sql)

            if self.isCanceled():
                self._emit_report("Task canceled.")
                return False
            self._emit_report("Getting pipe data from DB (2/4)...")
            self.setProgress(25)

            return True

        except Exception as e:
            self._emit_report(f"Error: {e}")
            return False

    def _emit_report(self, *args):
        self.report.emit({"info": {"values": [{"message": arg} for arg in args]}})
