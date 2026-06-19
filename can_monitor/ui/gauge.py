from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, 
    QHBoxLayout, QApplication, 
    QLineEdit
)
from PyQt5.QtCore import Qt

from .widgets.rmp_gauge import RPMGaugeWidget
from .widgets.speedometer import SpeedometerWidget

import sys

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CanGauge")
        self.showFullScreen()
        self._build_ui()
        self.polling = False

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.showNormal()
        elif event.key() == Qt.Key_F:
            self.showFullScreen()
        elif event.key() == Qt.Key_Q:
            QApplication.quit()

    def _build_ui(self):
        master = QVBoxLayout()
        text_layout = QHBoxLayout()
        gauge_layout = QHBoxLayout()
        master.addLayout(gauge_layout)
        master.addLayout(text_layout)

        # RPM Text
        # self.engine_speed_text_disp = QLineEdit("0")
        # self.engine_speed_text_disp.setReadOnly(True)
        # text_layout.addWidget(self.engine_speed_text_disp)

        # vehicle speed Text
        # self.vehicle_speed_text_disp = QLineEdit("0")
        # self.vehicle_speed_text_disp.setReadOnly(True)
        # text_layout.addWidget(self.vehicle_speed_text_disp)

        # RPM Gauge
        self.rpm_gauge = RPMGaugeWidget(min_val=0, max_val=8000, warn_val=0, danger_val=6000)
        gauge_layout.addWidget(self.rpm_gauge)

        # Speedometer
        self.speedometer = SpeedometerWidget(min_val=0, max_val=140)
        gauge_layout.addWidget(self.speedometer)

        self.setLayout(master)

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())