from PyQt5.QtWidgets import QHBoxLayout

from cantools.database import Database

from ui.pages.gauge_page.layout_presets.gauge_layout_preset import GaugeLayoutPreset

NUM_GAUGES_PER_ROW = 3
BOX_W = 330
BOX_H = 250

class DualRowGaugeLayout(GaugeLayoutPreset):
    name = "Daul Row Layout"
    def __init__(self, can_db: Database, parent=None):
        super().__init__(can_db, parent)

        self.top_row_gauges = QHBoxLayout()
        self.bottom_row_gauges = QHBoxLayout()

        self.gauges_layout.addLayout(self.top_row_gauges)
        self.gauges_layout.addLayout(self.bottom_row_gauges)

        for i in range(NUM_GAUGES_PER_ROW):
            self.add_gauge_template_box(layout=self.top_row_gauges, box_size=(BOX_W, BOX_H), slot=i)
            self.add_gauge_template_box(layout=self.bottom_row_gauges, box_size=(BOX_W, BOX_H), slot=i + NUM_GAUGES_PER_ROW)



