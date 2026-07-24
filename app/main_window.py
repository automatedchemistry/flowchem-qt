import sys
from pathlib import Path

from PyQt5.QtCore import QSettings, QStandardPaths
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QApplication,
    QFileDialog,
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
from app.windows_launcher import (
    ICON_PATH,
    PROJECT_ROOT,
    SHORTCUT_NAME,
    LauncherBuildError,
    ShortcutBuildError,
    build_launcher,
    create_windows_shortcut,
)


IS_WINDOWS = sys.platform == "win32"


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
        self.shortcut_btn = PushButton("Create shortcut")
        self.shortcut_btn.setToolTip("Create a Windows shortcut for FlowChem Manager.")
        self.shortcut_btn.clicked.connect(self._create_shortcut)
        status_bar.addPermanentWidget(self.shortcut_btn)
        self.shortcut_btn.setVisible(IS_WINDOWS)
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

    def _create_shortcut(self):
        desktop = QStandardPaths.writableLocation(QStandardPaths.DesktopLocation)
        if not desktop or not Path(desktop).is_dir():
            desktop = str(Path.home())
        destination = QFileDialog.getExistingDirectory(
            self,
            "Choose shortcut location",
            desktop,
            QFileDialog.ShowDirsOnly,
        )
        if not destination:
            return

        shortcut_path = Path(destination) / SHORTCUT_NAME
        if shortcut_path.exists():
            answer = QMessageBox.question(
                self,
                "Replace shortcut?",
                f"{shortcut_path.name} already exists. Replace it?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if answer != QMessageBox.Yes:
                return

        self.shortcut_btn.setEnabled(False)
        try:
            launcher_path = build_launcher(PROJECT_ROOT, Path(sys.prefix))
            create_windows_shortcut(
                shortcut_path,
                launcher_path,
                ICON_PATH,
                working_directory=PROJECT_ROOT,
            )
        except LauncherBuildError as error:
            missing = "\n".join(f"  - {path}" for path in error.missing_paths)
            self._show_shortcut_error(
                f"Could not build the launcher. Required files are missing:\n{missing}"
            )
        except (ShortcutBuildError, OSError) as error:
            self._show_shortcut_error(str(error))
        else:
            self.statusBar().showMessage(f"Shortcut created: {shortcut_path}", 5000)
            QMessageBox.information(
                self,
                "Shortcut created",
                f"Created:\n{shortcut_path}",
            )
        finally:
            self.shortcut_btn.setEnabled(True)

    def _show_shortcut_error(self, message: str):
        self.statusBar().showMessage("Shortcut creation failed", 5000)
        QMessageBox.critical(
            self,
            "Shortcut creation failed",
            message,
        )

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

    def show_and_activate(self):
        if self.isMinimized():
            self.showNormal()
        else:
            self.show()
        self.raise_()
        self.activateWindow()

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
