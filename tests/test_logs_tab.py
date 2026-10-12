import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from loguru import logger
from PyQt5.QtWidgets import QApplication, QFileDialog, QMessageBox

from app.tabs.logs_tab import LogsTab

_APP = None


class FakeSettings:
    def __init__(self):
        self.values = {}

    def value(self, key, default=None):
        return self.values.get(key, default)

    def setValue(self, key, value):
        self.values[key] = value


class BrokenFile:
    name = "broken.log"

    def write(self, _text):
        raise OSError("disk gone")

    def flush(self):
        pass

    def close(self):
        pass


@pytest.fixture
def make_tab():
    tabs = []

    def factory():
        global _APP
        _APP = QApplication.instance() or QApplication(
            ["test", "-platform", "offscreen"]
        )
        _APP.setQuitOnLastWindowClosed(False)
        settings = FakeSettings()
        tab = LogsTab(settings=settings)
        tabs.append(tab)
        return tab, settings

    yield factory
    for tab in tabs:
        tab.close_autosave()
        logger.remove(tab._sink_id)


def choose_file(monkeypatch, path):
    monkeypatch.setattr(
        QFileDialog,
        "getSaveFileName",
        lambda *_args: (str(path), "Log files (*.log)"),
    )


def capture_warnings(monkeypatch):
    warnings = []

    def fake_warning(_parent, title, message):
        warnings.append((title, message))
        return QMessageBox.Ok

    monkeypatch.setattr(QMessageBox, "warning", fake_warning)
    return warnings


def read_lines(path):
    return path.read_text(encoding="utf-8").splitlines()


def test_autosave_writes_existing_and_new_messages(tmp_path, monkeypatch, make_tab):
    target = tmp_path / "session.log"
    choose_file(monkeypatch, target)
    warnings = capture_warnings(monkeypatch)
    tab, settings = make_tab()
    tab.append_process_output("before autosave\n")

    tab.autosave_btn.click()
    tab.append_process_output("server line\n")
    logger.info("gui event")

    lines = read_lines(target)
    assert lines[0] == "before autosave"
    assert "Auto-saving logs to" in lines[1]
    assert lines[2] == "server line"
    assert lines[3].endswith("gui event")
    assert tab.autosave_btn.text() == "Stop auto-save"
    assert str(target) in tab.autosave_label.text()
    assert settings.values["log_dir"] == str(tmp_path)
    assert warnings == []


def test_autosave_adds_log_suffix(tmp_path, monkeypatch, make_tab):
    choose_file(monkeypatch, tmp_path / "session")
    tab, _settings = make_tab()

    tab._toggle_autosave()

    assert (tmp_path / "session.log").is_file()


def test_autosave_dialog_cancel_returns_cleanly(tmp_path, monkeypatch, make_tab):
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *_args: ("", ""))
    warnings = capture_warnings(monkeypatch)
    tab, settings = make_tab()

    tab._toggle_autosave()

    assert list(tmp_path.iterdir()) == []
    assert tab.autosave_btn.text() == "Auto-save…"
    assert "log_dir" not in settings.values
    assert warnings == []


def test_stop_autosave_stops_writing(tmp_path, monkeypatch, make_tab):
    target = tmp_path / "session.log"
    choose_file(monkeypatch, target)
    tab, _settings = make_tab()

    tab._toggle_autosave()
    tab._toggle_autosave()
    tab.append_process_output("after stop")

    content = target.read_text(encoding="utf-8")
    assert "Stopped auto-saving logs" in content
    assert "after stop" not in content
    assert tab.autosave_btn.text() == "Auto-save…"
    assert tab.autosave_label.text() == ""


def test_clear_does_not_truncate_file(tmp_path, monkeypatch, make_tab):
    target = tmp_path / "session.log"
    choose_file(monkeypatch, target)
    tab, _settings = make_tab()

    tab._toggle_autosave()
    tab.append_process_output("kept line")
    tab.log_view.clear()
    tab.append_process_output("after clear")

    lines = read_lines(target)
    assert "kept line" in lines
    assert "after clear" in lines


def test_autosave_to_folder_warns_without_crashing(tmp_path, monkeypatch, make_tab):
    choose_file(monkeypatch, tmp_path)
    warnings = capture_warnings(monkeypatch)
    tab, settings = make_tab()

    tab._toggle_autosave()

    assert warnings
    assert warnings[0][0] == "Invalid log file"
    assert "folder" in warnings[0][1]
    assert tab.autosave_btn.text() == "Auto-save…"
    assert "log_dir" not in settings.values


def test_autosave_permission_error_warns_without_crashing(
    tmp_path, monkeypatch, make_tab
):
    choose_file(monkeypatch, tmp_path / "locked.log")
    warnings = capture_warnings(monkeypatch)
    tab, settings = make_tab()

    def raise_permission_error(self, *_args, **_kwargs):
        raise PermissionError("permission denied")

    monkeypatch.setattr(Path, "open", raise_permission_error)

    tab._toggle_autosave()

    assert warnings
    assert warnings[0][0] == "Could not save logs"
    assert "permission denied" in warnings[0][1]
    assert tab.autosave_btn.text() == "Auto-save…"
    assert "log_dir" not in settings.values


def test_write_failure_stops_autosave(tmp_path, monkeypatch, make_tab):
    choose_file(monkeypatch, tmp_path / "session.log")
    warnings = capture_warnings(monkeypatch)
    tab, _settings = make_tab()

    tab._toggle_autosave()
    tab.close_autosave()
    tab._log_file = BrokenFile()
    logger.info("lost line")
    QApplication.processEvents()

    assert tab._log_file is None
    assert warnings
    assert warnings[0][0] == "Auto-save stopped"
    assert "disk gone" in warnings[0][1]
    assert tab.autosave_btn.text() == "Auto-save…"
