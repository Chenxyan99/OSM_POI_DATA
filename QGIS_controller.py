from qgis.core import QgsApplication

class qgisController:
    def __init__(self):
        self.qgs = QgsApplication([], False)
        self.qgs.initQgis()

    def test(self):
        print("Hello QGIS!")

    def exit(self):
        self.qgs.exitQgis()
