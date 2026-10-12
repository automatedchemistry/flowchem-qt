from contextlib import suppress
from datetime import datetime
from pathlib import Path
from typing import TextIO

from PyQt5.QtCore import QSettings, QStandardPaths, QTimer
from PyQt5.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import PushButton
from loguru import logger

_LOG_FILTER = "Log files (*.log);;Text files (*.txt);;All files (*)"


class LogsTab(QWidget):
    def __init__(self, parent=None, settings: QSettings | None = None):
        super().__init__(parent)
        self._settings = (
            settings if settings is not None else QSettings("flowchem", "gui")
        )
        self._log_file: TextIO | None = None
        self.log_view = QPlainTextEdit(readOnly=True)

        self.autosave_label = QLabel()
        self.autosave_btn = PushButton()
        clear_btn = PushButton("Clear")
        self.log_view.setToolTip("Live FlowChem process output and GUI log events.")
        self.autosave_label.setToolTip("File receiving the log output.")
        clear_btn.setToolTip(
            "Clear the displayed log output. The auto-save file is not affected."
        )
        self.autosave_btn.clicked.connect(self._toggle_autosave)
        clear_btn.clicked.connect(self.log_view.clear)
        self._update_autosave_ui(None)

        btn_row = QHBoxLayout()
        btn_row.addWidget(self.autosave_label)
        btn_row.addStretch()
        btn_row.addWidget(self.autosave_btn)
        btn_row.addWidget(clear_btn)

        layout = QVBoxLayout(self)
        layout.addWidget(self.log_view)
        layout.addLayout(btn_row)

        self._sink_id = logger.add(
            self._log_sink,
            level="DEBUG",
            format="{time:HH:mm:ss} | {level:<8} | {message}",
        )

    def _log_sink(self, message):
        self._append(message.strip())

    def append_process_output(self, text: str):
        self._append(text.rstrip())

    def close_autosave(self):
        self._close_log_file()

    def _append(self, text: str):
        if not text:
            return
        self.log_view.appendPlainText(text)
        sb = self.log_view.verticalScrollBar()
        sb.setValue(sb.maximum())
        if self._log_file is not None:
            self._write_to_file(self._log_file, text)

    def _write_to_file(self, log_file: TextIO, text: str):
        try:
            log_file.write(text + "\n")
            log_file.flush()
        except (OSError, ValueError) as exc:
            message = f"Could not write to log file:\n{log_file.name}\n\n{exc}"
            self._close_log_file()
            # This can run inside the loguru sink, where logging again is not
            # allowed — report the failure from the event loop instead.
            QTimer.singleShot(0, lambda: self._on_autosave_failed(message))

    def _on_autosave_failed(self, message: str):
        self._update_autosave_ui(None)
        self._warn("Auto-save stopped", message)

    def _toggle_autosave(self):
        if self._log_file is not None:
            self._stop_autosave()
        else:
            self._start_autosave()

    def _start_autosave(self):
        path = self._select_autosave_path()
        if path is None:
            return

        try:
            if path.is_dir():
                self._warn(
                    "Invalid log file",
                    f"Selected path is a folder, not a log file:\n{path}",
                )
                return
            self._log_file = path.open("w", encoding="utf-8")
            existing = self.log_view.toPlainText()
            if existing:
                self._log_file.write(existing + "\n")
                self._log_file.flush()
        except (OSError, ValueError) as exc:
            self._close_log_file()
            self._warn(
                "Could not save logs",
                f"Could not write log file:\n{path}\n\n{exc}",
            )
            return

        self._settings.setValue("log_dir", str(path.parent))
        self._update_autosave_ui(path)
        logger.info(f"Auto-saving logs to {path}")

    def _stop_autosave(self):
        logger.info("Stopped auto-saving logs")
        self._close_log_file()
        self._update_autosave_ui(None)

    def _close_log_file(self):
        log_file, self._log_file = self._log_file, None
        if log_file is None:
            return
        with suppress(OSError, ValueError):
            log_file.close()

    def _select_autosave_path(self) -> Path | None:
        folder = (
            self._settings.value("log_dir", "")
            or QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation)
            or str(Path.home())
        )
        default = Path(folder) / f"flowchem_{datetime.now():%Y%m%d_%H%M%S}.log"
        path, _ = QFileDialog.getSaveFileName(
            self, "Auto-save logs to", str(default), _LOG_FILTER
        )
        if not path:
            return None
        selected = Path(path)
        if selected.exists() and selected.is_dir():
            return selected
        if not selected.suffix:
            selected = selected.with_suffix(".log")
        return selected

    def _update_autosave_ui(self, path: Path | None):
        if path is None:
            self.autosave_btn.setText("Auto-save…")
            self.autosave_btn.setToolTip(
                "Choose a file and keep saving all log output to it."
            )
            self.autosave_label.setText("")
        else:
            self.autosave_btn.setText("Stop auto-save")
            self.autosave_btn.setToolTip("Stop saving log output to the file.")
            self.autosave_label.setText(f"Saving to: {path}")

    def _warn(self, title: str, message: str):
        logger.warning(message.replace("\n", " "))
        QMessageBox.warning(self, title, message)
