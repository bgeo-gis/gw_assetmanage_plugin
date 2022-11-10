from qgis.core import QgsTask
from qgis.PyQt.QtCore import pyqtSignal

from .task import GwTask


class GwAssignation(GwTask):
    report = pyqtSignal(dict)

    def __init__(self, description, method, buffer, years):
        super().__init__(description, QgsTask.CanCancel)
        self.method = method
        self.buffer = buffer
        self.years = years

    def run(self):
        try:
            self.report.emit({"info": {"values": [{"message": "finished"}]}})
            return True

        except Exception as e:
            self.report.emit({"info": {"values": [{"message": e}]}})
            return False
