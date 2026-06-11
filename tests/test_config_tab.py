import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtWidgets import QApplication, QFileDialog, QMessageBox

from app.tabs.config_tab import ConfigTab

_APP = None


class FakeSettings:
    def __init__(self):
        self.values = {}

    def value(self, key, default=None):
        return self.values.get(key, default)

    def setValue(self, key, value):
        self.values[key] = value


def make_tab():
    global _APP
    _APP = QApplication.instance() or QApplication(["test", "-platform", "offscreen"])
    _APP.setQuitOnLastWindowClosed(False)
    settings = FakeSettings()
    tab = ConfigTab(settings=settings)
    return tab, settings


def capture_warnings(monkeypatch):
    warnings = []

    def fake_warning(_parent, title, message):
        warnings.append((title, message))
        return QMessageBox.Ok

    monkeypatch.setattr(QMessageBox, "warning", fake_warning)
    return warnings


def test_save_without_path_opens_dialog_and_writes_toml(tmp_path, monkeypatch):
    target_without_suffix = tmp_path / "new_config"
    monkeypatch.setattr(
        QFileDialog,
        "getSaveFileName",
        lambda *_args: (str(target_without_suffix), "TOML files (*.toml)"),
    )
    warnings = capture_warnings(monkeypatch)
    tab, settings = make_tab()

    tab.editor.setPlainText("device = 'pump'")
    tab._save()

    target = target_without_suffix.with_suffix(".toml")
    assert target.read_text(encoding="utf-8") == "device = 'pump'"
    assert tab.path_edit.text() == str(target)
    assert settings.values["config_path"] == str(target)
    assert warnings == []


def test_save_dialog_cancel_returns_cleanly(tmp_path, monkeypatch):
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *_args: ("", ""))
    warnings = capture_warnings(monkeypatch)
    tab, settings = make_tab()

    tab.editor.setPlainText("device = 'pump'")
    tab._save()

    assert list(tmp_path.iterdir()) == []
    assert tab.path_edit.text() == ""
    assert "config_path" not in settings.values
    assert warnings == []


def test_save_to_folder_path_warns_without_crashing(tmp_path, monkeypatch):
    monkeypatch.setattr(
        QFileDialog,
        "getSaveFileName",
        lambda *_args: (str(tmp_path), "TOML files (*.toml)"),
    )
    warnings = capture_warnings(monkeypatch)
    tab, settings = make_tab()

    tab._save()

    assert warnings
    assert warnings[0][0] == "Invalid config file"
    assert "folder" in warnings[0][1]
    assert "config_path" not in settings.values


def test_save_permission_error_warns_without_crashing(tmp_path, monkeypatch):
    target = tmp_path / "locked.toml"
    warnings = capture_warnings(monkeypatch)
    tab, settings = make_tab()
    tab.path_edit.setText(str(target))

    def raise_permission_error(self, *_args, **_kwargs):
        raise PermissionError("permission denied")

    monkeypatch.setattr(Path, "write_text", raise_permission_error)

    tab._save()

    assert warnings
    assert warnings[0][0] == "Could not save config"
    assert "permission denied" in warnings[0][1]
    assert "config_path" not in settings.values


def test_load_without_path_opens_dialog_and_reads_toml(tmp_path, monkeypatch):
    source = tmp_path / "config.toml"
    source.write_text("device = 'pump'", encoding="utf-8")
    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileName",
        lambda *_args: (str(source), "TOML files (*.toml)"),
    )
    warnings = capture_warnings(monkeypatch)
    tab, settings = make_tab()

    tab._load()

    assert tab.editor.toPlainText() == "device = 'pump'"
    assert tab.path_edit.text() == str(source)
    assert settings.values["config_path"] == str(source)
    assert warnings == []


def test_load_missing_file_warns_without_crashing(tmp_path, monkeypatch):
    warnings = capture_warnings(monkeypatch)
    tab, settings = make_tab()
    tab.path_edit.setText(str(tmp_path / "missing.toml"))

    tab._load()

    assert warnings
    assert warnings[0][0] == "Config file not found"
    assert "config_path" not in settings.values


def test_load_folder_path_warns_without_crashing(tmp_path, monkeypatch):
    warnings = capture_warnings(monkeypatch)
    tab, settings = make_tab()
    tab.path_edit.setText(str(tmp_path))

    tab._load()

    assert warnings
    assert warnings[0][0] == "Invalid config file"
    assert "folder" in warnings[0][1]
    assert "config_path" not in settings.values
