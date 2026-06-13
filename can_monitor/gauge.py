from PyQt5.QtWidgets import (
    QWidget, QLabel,
    QPushButton, QVBoxLayout, QHBoxLayout, 
    QApplication, QLineEdit
)
from PyQt5.QtCore import QTimer

from .poll_reqs import poll_rpm, init_reqsts
from .widgets.rmp_gauge import RPMGaugeWidget

import sys

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gauge")
        # self.setFixedSize(400, 400)
        self.showMaximized()
        self._build_ui()
        self.polling = False
        # self.bus = init_reqsts()

    def _build_ui(self):
        layout = QVBoxLayout()
        
        # RPM Text
        self.value_display = QLineEdit("0")
        self.value_display.setReadOnly(True)
        layout.addWidget(self.value_display)

        # RPM Gauge
        self.rpm_gauge = RPMGaugeWidget(min_val=0, max_val=8000, unit="RPM", warn_val=0, danger_val=6000)
        layout.addWidget(self.rpm_gauge)

        # Start button
        self.start_btn = QPushButton("Start")
        self.start_btn.clicked.connect(self._poll)
        layout.addWidget(self.start_btn)
        
        self.setLayout(layout)

    def _poll(self):
        if self.polling:
            self.polling = False
            self.start_btn.setText("Start")
        else:
            self.polling = True
            self.start_btn.setText("Stop")
            self._poll_rpm()  # kick it off

    def _poll_rpm(self):
        if not self.polling:
            return  # stop the chain if polling was toggled off
        
        value = poll_rpm(self.bus)
        self.rpm_gauge.set_value(value)
        self.value_display.setText(str(value))
        QTimer.singleShot(100, self._poll_rpm)  # chain the next one


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())