import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtWidgets import QApplication, QFileDialog, QMessageBox

import app.main_window as main_window
from app.main_window import MainWindow
from app.windows_launcher import LauncherBuildError, SHORTCUT_NAME

_APP = None


class FakeSettings:
    def __init__(self):
        self.values = {}

    def value(self, key, default=None):
        return self.values.get(key, default)

    def setValue(self, key, value):
        self.values[key] = value


def get_app():
    global _APP
    _APP = QApplication.instance() or QApplication(["test", "-platform", "offscreen"])
    _APP.setQuitOnLastWindowClosed(False)
    return _APP


def create_window(monkeypatch, *, windows=True):
    get_app()
    monkeypatch.setattr(main_window, "IS_WINDOWS", windows)
    return MainWindow(minimize_to_tray=False, settings=FakeSettings())


def test_shortcut_button_is_beside_theme_button_on_windows(monkeypatch):
    app = get_app()
    window = create_window(monkeypatch)
    window.show()
    app.processEvents()

    assert not window.shortcut_btn.isHidden()
    assert window.shortcut_btn.parent() is window.statusBar()
    assert window.theme_btn.parent() is window.statusBar()
    assert window.shortcut_btn.geometry().right() <= window.theme_btn.geometry().left()

    window.close()


def test_shortcut_button_is_hidden_outside_windows(monkeypatch):
    window = create_window(monkeypatch, windows=False)

    assert window.shortcut_btn.isHidden()

    window.close()


def test_shortcut_dialog_cancellation_does_nothing(monkeypatch):
    window = create_window(monkeypatch)
    monkeypatch.setattr(QFileDialog, "getExistingDirectory", lambda *_args: "")

    def unexpected_build(*_args):
        raise AssertionError("BAT builder should not run after cancellation")

    monkeypatch.setattr(main_window, "build_launcher", unexpected_build)

    window.shortcut_btn.click()

    assert window.shortcut_btn.isEnabled()
    window.close()


def test_existing_shortcut_is_not_replaced_without_confirmation(tmp_path, monkeypatch):
    window = create_window(monkeypatch)
    shortcut_path = tmp_path / SHORTCUT_NAME
    shortcut_path.write_bytes(b"existing")
    monkeypatch.setattr(
        QFileDialog,
        "getExistingDirectory",
        lambda *_args: str(tmp_path),
    )
    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *_args: QMessageBox.No,
    )

    def unexpected_build(*_args):
        raise AssertionError("BAT builder should not run after overwrite rejection")

    monkeypatch.setattr(main_window, "build_launcher", unexpected_build)

    window.shortcut_btn.click()

    assert shortcut_path.read_bytes() == b"existing"
    window.close()


def test_shortcut_button_builds_with_running_environment_and_icon(
    tmp_path, monkeypatch
):
    window = create_window(monkeypatch)
    shortcut_path = tmp_path / SHORTCUT_NAME
    shortcut_path.write_bytes(b"existing")
    launcher_path = tmp_path / "flowchem-qt.bat"
    calls = {}
    messages = []

    monkeypatch.setattr(
        QFileDialog,
        "getExistingDirectory",
        lambda *_args: str(tmp_path),
    )
    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *_args: QMessageBox.Yes,
    )
    monkeypatch.setattr(
        QMessageBox,
        "information",
        lambda *_args: messages.append(_args),
    )

    def fake_build(project_root, venv_dir):
        calls["build"] = (project_root, venv_dir)
        return launcher_path

    def fake_create(shortcut, launcher, icon, *, working_directory):
        calls["shortcut"] = (
            shortcut,
            launcher,
            icon,
            working_directory,
        )
        shortcut.write_bytes(b"new shortcut")
        return shortcut

    monkeypatch.setattr(main_window, "build_launcher", fake_build)
    monkeypatch.setattr(main_window, "create_windows_shortcut", fake_create)

    window.shortcut_btn.click()

    assert calls["build"] == (main_window.PROJECT_ROOT, Path(sys.prefix))
    assert calls["shortcut"] == (
        shortcut_path,
        launcher_path,
        main_window.ICON_PATH,
        main_window.PROJECT_ROOT,
    )
    assert shortcut_path.read_bytes() == b"new shortcut"
    assert messages
    assert window.shortcut_btn.isEnabled()
    assert "Shortcut created:" in window.statusBar().currentMessage()
    window.close()


def test_shortcut_build_error_is_shown_and_button_is_reenabled(tmp_path, monkeypatch):
    window = create_window(monkeypatch)
    missing_path = tmp_path / "missing" / "flowchem.exe"
    errors = []
    monkeypatch.setattr(
        QFileDialog,
        "getExistingDirectory",
        lambda *_args: str(tmp_path),
    )

    def fake_build(*_args):
        raise LauncherBuildError([missing_path])

    monkeypatch.setattr(main_window, "build_launcher", fake_build)
    monkeypatch.setattr(
        QMessageBox,
        "critical",
        lambda *_args: errors.append(_args),
    )

    window.shortcut_btn.click()

    assert errors
    assert str(missing_path) in errors[0][-1]
    assert window.shortcut_btn.isEnabled()
    assert window.statusBar().currentMessage() == "Shortcut creation failed"
    window.close()
