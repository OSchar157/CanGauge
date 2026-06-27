import sys

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QApplication
)

from ..gauge_widgets import Gauge

from decoding.decoder import DecodedMsg


class GaugePage(QWidget):
    def __init__(self):
        super().__init__()

        master = QHBoxLayout()
        self.setLayout(master)

        self.gauges: dict[str, list[Gauge]] = {}

    def on_msg(self, msg):
        if self.gauges:
            for name, gauges in self.gauges.items():
                if name in msg.signals:
                    for gauge in gauges:
                        gauge.set_value(msg.signals[name])
                    continue
    
    def add_gauge(self, gauge_type: Gauge, name: str, args):
        new_gauge = gauge_type(**args)

        if name not in self.gauges:
            self.gauges[name] = []
        self.gauges[name].append(new_gauge)

        self.layout().addWidget(new_gauge)
        
if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = GaugePage()
    window.show()
    sys.exit(app.exec_())