from PySide6.QtCore import QProcess
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMessageBox,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import PrimaryPushButton, PushButton
from loguru import logger

_WARNING = (
    "Autodiscover communicates over serial ports.\n"
    "Unsupported devices could be placed in an unsafe state.\n\n"
    "Continue?"
)


class DiscoverTab(QWidget):
    def __init__(self, config_tab, parent=None):
        super().__init__(parent)
        self._cfg = config_tab
        self._proc = QProcess(self)

        self.output = QPlainTextEdit(readOnly=True)
        run_btn = PrimaryPushButton("Run autodiscover")
        self.copy_btn = PushButton("Copy to editor")
        self.copy_btn.setEnabled(False)

        self.output.setToolTip("Autodiscover output from stdout and stderr.")
        run_btn.setToolTip("Run flowchem-autodiscover after confirming the warning.")
        self.copy_btn.setToolTip("Copy autodiscover output into the Config editor.")

        btn_row = QHBoxLayout()
        btn_row.addWidget(run_btn)
        btn_row.addWidget(self.copy_btn)
        btn_row.addStretch()

        layout = QVBoxLayout(self)
        layout.addLayout(btn_row)
        layout.addWidget(self.output)

        run_btn.clicked.connect(self._run)
        self.copy_btn.clicked.connect(self._copy_to_editor)
        self._proc.readyReadStandardOutput.connect(
            lambda: self._append(self._proc.readAllStandardOutput().data())
        )
        self._proc.readyReadStandardError.connect(
            lambda: self._append(self._proc.readAllStandardError().data())
        )
        self._proc.finished.connect(self._on_finished)

    def _run(self):
        reply = QMessageBox.warning(
            self,
            "Warning",
            _WARNING,
            QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
        )
        if reply != QMessageBox.StandardButton.Ok:
            return
        self.output.clear()
        self.copy_btn.setEnabled(False)
        logger.info("Running flowchem-autodiscover")
        self._proc.start("flowchem-autodiscover", [])

    def _append(self, data: bytes):
        text = data.decode(errors="replace").rstrip()
        if text:
            self.output.appendPlainText(text)

    def _on_finished(self, exit_code, _status):
        logger.info(f"Autodiscover finished (exit code {exit_code})")
        self.copy_btn.setEnabled(bool(self.output.toPlainText()))

    def _copy_to_editor(self):
        self._cfg.set_content(self.output.toPlainText())
        logger.info("Autodiscover output copied to config editor")
