from PyQt5.QtWidgets import QHBoxLayout

from cantools.database import Database

from ui.pages.gauge_page.layout_presets.gauge_layout_preset import GaugeLayoutPreset

NUM_GAUGES_PER_ROW = 3
BOX_W = 330
BOX_H = 500

class SingleRowGaugeLayout(GaugeLayoutPreset):
    name = "Single Row Layout"
    def __init__(self, can_db: Database, parent=None):
        super().__init__(can_db, parent)

        self.gauges_row = QHBoxLayout()
        self.gauges_layout.addLayout(self.gauges_row)

        for i in range(NUM_GAUGES_PER_ROW):
            self.add_gauge_template_box(layout=self.gauges_row, box_size=(BOX_W, BOX_H), slot=i)