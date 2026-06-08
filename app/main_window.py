from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QLabel, QMainWindow, QMessageBox, QStatusBar, QTabWidget

from app.server_manager import ServerManager
from app.tabs.config_tab import ConfigTab
from app.tabs.discover_tab import DiscoverTab
from app.tabs.logs_tab import LogsTab
from app.tabs.server_tab import ServerTab

_ICON_PATH = Path(__file__).parent.parent / "resources" / "icons" / "flowchem_logo.svg"


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("FlowChem Manager")
        self.setWindowIcon(QIcon(str(_ICON_PATH)))
        self.resize(900, 650)

        self.server_manager = ServerManager(self)

        self.config_tab   = ConfigTab()
        self.server_tab   = ServerTab(self.server_manager, self.config_tab)
        self.discover_tab = DiscoverTab(self.config_tab)
        self.logs_tab     = LogsTab()

        tabs = QTabWidget()
        tabs.addTab(self.config_tab,   "Config editor")
        tabs.addTab(self.server_tab,   "Server")
        tabs.addTab(self.discover_tab, "Discover")
        tabs.addTab(self.logs_tab,     "Logs")
        self.setCentralWidget(tabs)

        self._status_dot = QLabel("● Server stopped")
        self._status_dot.setStyleSheet("color: red;")
        status_bar = QStatusBar()
        status_bar.addWidget(self._status_dot)
        self.setStatusBar(status_bar)

        self.server_manager.started.connect(self._on_started)
        self.server_manager.stopped.connect(self._on_stopped)
        self.server_manager.error.connect(self._on_error)
        self.server_manager.stdout_ready.connect(self.logs_tab.append_process_output)
        self.server_manager.stderr_ready.connect(self.logs_tab.append_process_output)

    def closeEvent(self, event):
        event.ignore()
        self.hide()

    def _on_started(self):
        self._status_dot.setText("● Server running")
        self._status_dot.setStyleSheet("color: green;")
        self.statusBar().showMessage("Server started", 3000)
        self.config_tab.setEnabled(False)
        self.discover_tab.setEnabled(False)

    def _on_stopped(self, exit_code):
        self._status_dot.setText("● Server stopped")
        self._status_dot.setStyleSheet("color: red;")
        msg = "Server stopped" if exit_code == 0 else f"Server stopped (exit code {exit_code})"
        self.statusBar().showMessage(msg, 5000)
        self.config_tab.setEnabled(True)
        self.discover_tab.setEnabled(True)

    def _on_error(self, msg: str):
        self.statusBar().showMessage(f"Error: {msg}", 0)  # 0 = stays until next message
        QMessageBox.critical(self, "Server error", msg)
