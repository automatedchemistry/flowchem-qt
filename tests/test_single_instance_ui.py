import builtins
import os
import sys
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon

import main as main_module
from app.main_window import MainWindow
from app.single_instance import InstanceStatus
from app.tray import TrayIcon

_APP = None


class FakeSettings:
    def value(self, _key, default=None):
        return default

    def setValue(self, _key, _value):
        pass


def get_app():
    global _APP
    _APP = QApplication.instance() or QApplication(
        ["test", "-platform", "offscreen"]
    )
    _APP.setQuitOnLastWindowClosed(False)
    return _APP


def test_show_and_activate_restores_hidden_window(monkeypatch):
    get_app()
    window = MainWindow(minimize_to_tray=False, settings=FakeSettings())
    calls = []
    monkeypatch.setattr(window, "isMinimized", lambda: False)
    monkeypatch.setattr(window, "show", lambda: calls.append("show"))
    monkeypatch.setattr(window, "showNormal", lambda: calls.append("showNormal"))
    monkeypatch.setattr(window, "raise_", lambda: calls.append("raise"))
    monkeypatch.setattr(
        window, "activateWindow", lambda: calls.append("activate")
    )

    window.show_and_activate()

    assert calls == ["show", "raise", "activate"]
    window.close()


def test_show_and_activate_restores_minimized_window(monkeypatch):
    get_app()
    window = MainWindow(minimize_to_tray=False, settings=FakeSettings())
    calls = []
    monkeypatch.setattr(window, "isMinimized", lambda: True)
    monkeypatch.setattr(window, "show", lambda: calls.append("show"))
    monkeypatch.setattr(window, "showNormal", lambda: calls.append("showNormal"))
    monkeypatch.setattr(window, "raise_", lambda: calls.append("raise"))
    monkeypatch.setattr(
        window, "activateWindow", lambda: calls.append("activate")
    )

    window.show_and_activate()

    assert calls == ["showNormal", "raise", "activate"]
    window.close()


def test_tray_actions_use_centralized_activation(monkeypatch):
    app = get_app()
    window = MainWindow(minimize_to_tray=False, settings=FakeSettings())
    activations = []
    starts = []
    monkeypatch.setattr(
        window, "show_and_activate", lambda: activations.append(True)
    )
    monkeypatch.setattr(window.server_tab, "_toggle", lambda: starts.append(True))
    tray = TrayIcon(window, window.server_manager, QIcon(), app)

    tray.contextMenu().actions()[0].trigger()
    tray._on_activated(QSystemTrayIcon.DoubleClick)
    tray._start()

    assert len(activations) == 3
    assert starts == [True]
    tray.hide()
    window.close()


def test_secondary_startup_exits_before_window_or_tray_creation(
    tmp_path, monkeypatch
):
    class FakeApp:
        pass

    class FakeCoordinator:
        def __init__(self, *_args):
            pass

        def start(self):
            return InstanceStatus.EXISTING_NOTIFIED

    primary_only_modules = {
        "qfluentwidgets",
        "app.main_window",
        "app.theme",
        "app.tray",
    }
    real_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
        if name in primary_only_modules:
            raise AssertionError(f"Primary-only module imported: {name}")
        return real_import(name, *args, **kwargs)

    fake_app = FakeApp()
    previous_stderr = sys.stderr
    monkeypatch.setattr(main_module, "_set_windows_app_id", lambda: None)
    monkeypatch.setattr(
        main_module,
        "parse_args",
        lambda argv: (SimpleNamespace(no_tray=False), argv),
    )
    monkeypatch.setattr(main_module, "QApplication", lambda _argv: fake_app)
    monkeypatch.setattr(
        main_module, "SingleInstanceCoordinator", FakeCoordinator
    )
    monkeypatch.setattr(builtins, "__import__", guarded_import)
    monkeypatch.setattr(Path, "home", classmethod(lambda _cls: tmp_path))

    try:
        assert main_module.main(["flowchem-qt"]) == 0
    finally:
        sys.stderr.close()
        sys.stderr = previous_stderr
