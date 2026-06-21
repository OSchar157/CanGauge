from PyQt5 import QtWidgets, QtCore

class LogViewer(QtWidgets.QPlainTextEdit):
    def __init__(self):
        super().__init__()
        self.setReadOnly(True)
        self.setMaximumBlockCount(1000)  # Prevents infinite memory growth
        self.buffer = []

        # Batch update UI every 20ms
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.flush_logs)
        self.timer.start(80)

    @QtCore.pyqtSlot(str)
    def append_log_safe(self, msg):
        """Worker calls this via signal. Thread-safe."""
        self.buffer.append(msg)

    def flush_logs(self):
        """Flushes buffered logs to UI in one single operation."""
        if self.buffer:
            self.appendPlainText("\n".join(self.buffer))
            self.buffer.clear()
