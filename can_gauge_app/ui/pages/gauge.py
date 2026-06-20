import sys

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QApplication
)

from ..widgets.rmp_gauge import RPMGaugeWidget
from ..widgets.speedometer import SpeedometerWidget


class GaugePage(QWidget):
    def __init__(self):
        super().__init__()

        master = QHBoxLayout()
        self.setLayout(master)

        # RPM Gauge
        self.rpm_gauge = RPMGaugeWidget(min_val=0, max_val=8000, warn_val=0, danger_val=6000)
        master.addWidget(self.rpm_gauge)

         # Speedometer
        self.speedometer = SpeedometerWidget(min_val=0, max_val=140)
        master.addWidget(self.speedometer)
        

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = GaugePage()
    window.show()
    sys.exit(app.exec_())