from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QPlainTextEdit,
)
from loguru import logger


class LogsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.log_view = QPlainTextEdit(readOnly=True)

        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.log_view.clear)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(clear_btn)

        layout = QVBoxLayout(self)
        layout.addWidget(self.log_view)
        layout.addLayout(btn_row)

        logger.add(
            self._log_sink,
            level="DEBUG",
            format="{time:HH:mm:ss} | {level:<8} | {message}",
        )

    def _log_sink(self, message):
        self._append(message.strip())

    def append_process_output(self, text: str):
        self._append(text.rstrip())

    def _append(self, text: str):
        if not text:
            return
        self.log_view.appendPlainText(text)
        sb = self.log_view.verticalScrollBar()
        sb.setValue(sb.maximum())
