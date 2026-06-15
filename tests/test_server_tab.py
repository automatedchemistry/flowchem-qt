import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QApplication

from app.tabs.server_tab import ServerTab

_APP = None


class FakeConfigTab:
    def __init__(self, path="config.toml"):
        self.path = path

    def get_config_path(self):
        return self.path


class FakeServerManager(QObject):
    started = pyqtSignal()
    stopped = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.running = False
        self.start_calls = []
        self.stop_calls = 0

    def is_running(self):
        return self.running

    def start(self, config_path, debug=False, sim=False, host="127.0.0.1"):
        self.start_calls.append(
            {
                "config_path": config_path,
                "debug": debug,
                "sim": sim,
                "host": host,
            }
        )

    def stop(self):
        self.stop_calls += 1


def make_tab():
    global _APP
    _APP = QApplication.instance() or QApplication(["test", "-platform", "offscreen"])
    _APP.setQuitOnLastWindowClosed(False)
    manager = FakeServerManager()
    tab = ServerTab(manager, FakeConfigTab())
    return tab, manager


def test_server_access_defaults_to_local_only():
    tab, _manager = make_tab()

    assert tab.access_combo.currentText() == "This computer only"
    assert tab._selected_host() == "127.0.0.1"
    assert "Recommended" in tab.access_description.text()
    assert tab._resolved_docs_url() == "http://localhost:8000/docs"


def test_server_access_local_network_updates_description_and_docs_url(monkeypatch):
    tab, _manager = make_tab()
    monkeypatch.setattr("app.tabs.server_tab.socket.gethostname", lambda: "lab-pc")
    monkeypatch.setattr(
        "app.tabs.server_tab.socket.gethostbyname", lambda _host: "192.168.1.20"
    )

    tab.access_combo.setCurrentIndex(1)

    assert tab._selected_host() == "0.0.0.0"
    assert "Other computers" in tab.access_description.text()
    assert tab._resolved_docs_url() == "http://192.168.1.20:8000/docs"


def test_start_passes_selected_access_host():
    tab, manager = make_tab()
    tab.access_combo.setCurrentIndex(1)
    tab.debug_chk.setChecked(True)
    tab.sim_chk.setChecked(True)

    tab._toggle()

    assert manager.start_calls == [
        {
            "config_path": "config.toml",
            "debug": True,
            "sim": True,
            "host": "0.0.0.0",
        }
    ]


def test_access_selector_is_disabled_while_running():
    tab, _manager = make_tab()

    tab._on_started()

    assert not tab.access_combo.isEnabled()

    tab._on_stopped(0)

    assert tab.access_combo.isEnabled()
