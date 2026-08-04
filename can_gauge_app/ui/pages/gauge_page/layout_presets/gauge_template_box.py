from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout, 
    QFrame,
)
from PyQt5.QtGui import QPainter, QPen, QColor
from PyQt5.QtCore import Qt, pyqtSignal

class GaugeTemplateBox(QFrame):
    clicked = pyqtSignal()

    def __init__(self):
        super().__init__()

        self.setStyleSheet("""
            GaugeTemplateBox {
                border: 4px dashed #808080;
                border-radius: 16px;
                background: transparent;
            }
        """)

        self.slot = None
        self.gauge = None

        self._layout = QVBoxLayout(self)

    def paintEvent(self, event):
        super().paintEvent(event)

        if self.gauge is not None:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        pen = QPen(QColor("#808080"), 4)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)

        s = 16  # half-length of plus
        c = self.rect().center()

        painter.drawLine(c.x() - s, c.y(), c.x() + s, c.y())
        painter.drawLine(c.x(), c.y() - s, c.x(), c.y() + s)

    def mousePressEvent(self, event):
        if self.gauge is not None:
            return
        if event.button() == Qt.LeftButton:
            self.clicked.emit()

    def set_gauge(self, gauge: QWidget):
        self.gauge = gauge
        self.setStyleSheet(None)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self._layout.addWidget(gauge)
        self.update()

    def clear_gauge(self):
        """Undo set_gauge(): tear the widget back out and show the '+' placeholder again."""
        if self.gauge is None:
            return
        self._layout.removeWidget(self.gauge)
        self.setStyleSheet("""
                    GaugeTemplateBox {
                        border: 4px dashed #808080;
                        border-radius: 16px;
                        background: transparent;
                    }
                """)
        self.gauge.setParent(None)
        self.gauge.deleteLater()
        self.gauge = None
        self.update()