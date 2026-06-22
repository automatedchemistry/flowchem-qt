from PyQt5.QtCore import QSettings
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QMessageBox,
    QStatusBar,
    QTabWidget,
)
from qfluentwidgets import PushButton

from app.server_manager import ServerManager
from app.tabs.config_tab import ConfigTab
from app.tabs.discover_tab import DiscoverTab
from app.tabs.logs_tab import LogsTab
from app.tabs.server_tab import ServerTab
from app.theme import DARK_THEME, LIGHT_THEME, THEME_KEY, apply_theme, load_theme


class MainWindow(QMainWindow):
    def __init__(
        self,
        parent=None,
        minimize_to_tray: bool = True,
        window_icon: QIcon | None = None,
        settings: QSettings | None = None,
    ):
        super().__init__(parent)
        self._minimize_to_tray = minimize_to_tray
        self._settings = (
            settings if settings is not None else QSettings("flowchem", "gui")
        )
        self._theme = load_theme(self._settings)
        self.setWindowTitle("FlowChem Manager")
        if window_icon is not None:
            self.setWindowIcon(window_icon)
        self.resize(900, 650)

        self.server_manager = ServerManager(self)

        self.config_tab = ConfigTab(settings=self._settings)
        self.server_tab = ServerTab(self.server_manager, self.config_tab)
        self.discover_tab = DiscoverTab(self.config_tab)
        self.logs_tab = LogsTab()

        tabs = QTabWidget()
        tabs.addTab(self.config_tab, "Config editor")
        tabs.addTab(self.server_tab, "Server")
        tabs.addTab(self.discover_tab, "Discover")
        tabs.addTab(self.logs_tab, "Logs")
        tabs.setTabToolTip(0, "Edit and save the FlowChem TOML configuration.")
        tabs.setTabToolTip(1, "Start, stop, and open the FlowChem server API.")
        tabs.setTabToolTip(2, "Detect connected devices and copy the generated config.")
        tabs.setTabToolTip(3, "View FlowChem server output and GUI events.")
        self.setCentralWidget(tabs)

        self._status_dot = QLabel("● Server stopped")
        self._status_dot.setToolTip("Current FlowChem server status.")
        self._status_dot.setStyleSheet("color: red;")
        status_bar = QStatusBar()
        status_bar.setToolTip("Shows the latest FlowChem Manager status message.")
        status_bar.addWidget(self._status_dot)
        self.theme_btn = PushButton()
        self.theme_btn.clicked.connect(self._toggle_theme)
        self._update_theme_button()
        status_bar.addPermanentWidget(self.theme_btn)
        self.setStatusBar(status_bar)

        self.server_manager.started.connect(self._on_started)
        self.server_manager.stopped.connect(self._on_stopped)
        self.server_manager.error.connect(self._on_error)
        self.server_manager.stdout_ready.connect(self.logs_tab.append_process_output)
        self.server_manager.stderr_ready.connect(self.logs_tab.append_process_output)

    def _toggle_theme(self):
        next_theme = LIGHT_THEME if self._theme == DARK_THEME else DARK_THEME
        qt_app = QApplication.instance()
        if qt_app is None:
            return
        self._theme = apply_theme(qt_app, next_theme)
        self._settings.setValue(THEME_KEY, self._theme)
        self._update_theme_button()

    def _update_theme_button(self):
        target = "Light" if self._theme == DARK_THEME else "Dark"
        self.theme_btn.setText(f"{target} mode")
        self.theme_btn.setToolTip(f"Switch to {target.lower()} mode.")

    def closeEvent(self, event):
        if self._minimize_to_tray:
            event.ignore()
            self.hide()
            return
        super().closeEvent(event)

    def _on_started(self):
        self._status_dot.setText("● Server running")
        self._status_dot.setToolTip("FlowChem server is running.")
        self._status_dot.setStyleSheet("color: green;")
        self.statusBar().showMessage("Server started", 3000)
        self.config_tab.setEnabled(False)
        self.discover_tab.setEnabled(False)

    def _on_stopped(self, exit_code):
        self._status_dot.setText("● Server stopped")
        self._status_dot.setToolTip("FlowChem server is stopped.")
        self._status_dot.setStyleSheet("color: red;")
        msg = (
            "Server stopped"
            if exit_code == 0
            else f"Server stopped (exit code {exit_code})"
        )
        self.statusBar().showMessage(msg, 5000)
        self.config_tab.setEnabled(True)
        self.discover_tab.setEnabled(True)

    def _on_error(self, msg: str):
        self.statusBar().showMessage(f"Error: {msg}", 0)  # 0 = stays until next message
        QMessageBox.critical(self, "Server error", msg)
