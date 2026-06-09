from pathlib import Path

from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import LineEdit, PrimaryPushButton, PushButton
from loguru import logger


class ConfigTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._settings = QSettings("flowchem", "gui")

        self.path_edit = LineEdit()
        self.path_edit.setPlaceholderText("Path to config.toml")
        browse_btn = PushButton("Browse")
        load_btn = PushButton("Load")
        self.save_btn = PrimaryPushButton("Save")
        self.editor = QPlainTextEdit()

        self.path_edit.setToolTip("Path to the FlowChem TOML configuration file.")
        browse_btn.setToolTip("Select a FlowChem TOML configuration file.")
        load_btn.setToolTip("Load the selected TOML file into the editor.")
        self.save_btn.setToolTip("Save the editor contents to the selected TOML file.")
        self.editor.setToolTip("Edit the raw FlowChem TOML configuration.")

        path_row = QHBoxLayout()
        path_row.addWidget(self.path_edit)
        path_row.addWidget(browse_btn)
        path_row.addWidget(load_btn)
        path_row.addWidget(self.save_btn)

        layout = QVBoxLayout(self)
        layout.addLayout(path_row)
        layout.addWidget(self.editor)

        browse_btn.clicked.connect(self._browse)
        load_btn.clicked.connect(self._load)
        self.save_btn.clicked.connect(self._save)

        saved = self._settings.value("config_path", "")
        if saved and Path(saved).exists():
            self.path_edit.setText(saved)
            self._load()

    def get_config_path(self) -> str:
        return self.path_edit.text()

    def set_content(self, text: str):
        self.editor.setPlainText(text)

    def _browse(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select config file", "", "TOML files (*.toml)"
        )
        if path:
            self.path_edit.setText(path)

    def _load(self):
        path = Path(self.path_edit.text())
        if not path.exists():
            logger.warning(f"Config file not found: {path}")
            return
        self.editor.setPlainText(path.read_text(encoding="utf-8"))
        self._settings.setValue("config_path", str(path))
        logger.info(f"Loaded config: {path}")

    def _save(self):
        path = Path(self.path_edit.text())
        path.write_text(self.editor.toPlainText(), encoding="utf-8")
        self._settings.setValue("config_path", str(path))
        logger.info(f"Saved config: {path}")
