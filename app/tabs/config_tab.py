from pathlib import Path

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from loguru import logger


class ConfigTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._settings = QSettings("flowchem", "gui")

        self.path_edit = QLineEdit(placeholderText="Path to config.toml")
        browse_btn = QPushButton("Browse")
        load_btn = QPushButton("Load")
        self.save_btn = QPushButton("Save")
        self.editor = QPlainTextEdit()

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
