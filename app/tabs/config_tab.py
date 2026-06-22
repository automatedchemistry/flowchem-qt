from pathlib import Path

from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QMessageBox,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import LineEdit, PrimaryPushButton, PushButton
from loguru import logger

_TOML_FILTER = "TOML files (*.toml);;All files (*)"


class ConfigTab(QWidget):
    def __init__(self, parent=None, settings: QSettings | None = None):
        super().__init__(parent)
        self._settings = (
            settings if settings is not None else QSettings("flowchem", "gui")
        )

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
        if saved:
            try:
                saved_path = Path(saved)
                if saved_path.exists():
                    self.path_edit.setText(str(saved_path))
                    self._load()
            except (OSError, ValueError) as exc:
                logger.warning(f"Ignoring saved config path {saved!r}: {exc}")

    def get_config_path(self) -> str:
        return self.path_edit.text()

    def set_content(self, text: str):
        self.editor.setPlainText(text)

    def _browse(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select config file", "", _TOML_FILTER
        )
        if path:
            self.path_edit.setText(path)

    def _load(self):
        path = self._current_path()
        if path is None:
            path = self._select_load_path()
            if path is None:
                return
            self.path_edit.setText(str(path))

        try:
            if path.is_dir():
                self._warn(
                    "Invalid config file",
                    f"Selected path is a folder, not a config file:\n{path}",
                )
                return
            if not path.exists():
                self._warn("Config file not found", f"Config file not found:\n{path}")
                return
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError, ValueError) as exc:
            self._warn(
                "Could not load config",
                f"Could not load config file:\n{path}\n\n{exc}",
            )
            return

        self.editor.setPlainText(content)
        self._settings.setValue("config_path", str(path))
        logger.info(f"Loaded config: {path}")

    def _save(self):
        path = self._current_path()
        try:
            needs_dialog = path is None or path.is_dir()
        except (OSError, ValueError) as exc:
            self._warn(
                "Invalid config path",
                f"Invalid config path:\n{path}\n\n{exc}",
            )
            return

        if needs_dialog:
            path = self._select_save_path()
            if path is None:
                return

        try:
            if path.exists() and path.is_dir():
                self._warn(
                    "Invalid config file",
                    f"Selected path is a folder, not a config file:\n{path}",
                )
                return
            path.write_text(self.editor.toPlainText(), encoding="utf-8")
        except (OSError, UnicodeError, ValueError) as exc:
            self._warn(
                "Could not save config",
                f"Could not save config file:\n{path}\n\n{exc}",
            )
            return

        self.path_edit.setText(str(path))
        self._settings.setValue("config_path", str(path))
        logger.info(f"Saved config: {path}")

    def _current_path(self) -> Path | None:
        text = self.path_edit.text().strip()
        if not text:
            return None
        return Path(text)

    def _select_load_path(self) -> Path | None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Select config file", "", _TOML_FILTER
        )
        if not path:
            return None
        return Path(path)

    def _select_save_path(self) -> Path | None:
        default = self.path_edit.text().strip() or "config.toml"
        path, _ = QFileDialog.getSaveFileName(
            self, "Save config file", default, _TOML_FILTER
        )
        if not path:
            return None
        selected = Path(path)
        if selected.exists() and selected.is_dir():
            return selected
        if not selected.suffix:
            selected = selected.with_suffix(".toml")
        return selected

    def _warn(self, title: str, message: str):
        logger.warning(message.replace("\n", " "))
        QMessageBox.warning(self, title, message)
