import sys

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QApplication
)

from ..widgets.rmp_gauge import RPMGaugeWidget
from ..widgets.speedometer import SpeedometerWidget

from decoding.decoder import DecodedMsg


class GaugePage(QWidget):
    def __init__(self):
        super().__init__()

        master = QHBoxLayout()
        self.setLayout(master)

        # # RPM Gauge
        # self.rpm_gauge = RPMGaugeWidget(min_val=0, max_val=8000, warn_val=0, danger_val=6000)
        # master.addWidget(self.rpm_gauge)

        #  # Speedometer
        # self.speedometer = SpeedometerWidget(min_val=0, max_val=140)
        # master.addWidget(self.speedometer)

        self.gauges: dict = {}

    def on_msg(self, msg):
        if self.gauges:
            for gauge_id, gauge in self.gauges.items():
                if gauge_id in msg.signals:
                    gauge.set_value(msg.signals[gauge_id])
                    continue
    
    # def on_msg(self, msg: DecodedMsg):
    #     if 'Engine_RPM' in msg.signals:
    #         self.rpm_gauge.set_value(msg.signals['Engine_RPM'])
    #     elif all(k in msg.signals for k in ('FL', 'FR', 'RL', 'RR')):
    #         speed = sum(msg.signals[k] for k in ('FL', 'FR', 'RL', 'RR')) / 4
    #         self.speedometer.set_value(speed)

    def add_gauge(self, args):
        new_gauge = RPMGaugeWidget(int(args["min_val"]), int(args["max_val"]), int(args["warn_val"]), int(args["danger_val"]))
        self.gauges[args["name"]] = new_gauge
        self.layout().addWidget(new_gauge)
        
if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = GaugePage()
    window.show()
    sys.exit(app.exec_())