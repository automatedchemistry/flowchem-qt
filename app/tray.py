from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon
from loguru import logger


class TrayIcon(QSystemTrayIcon):
    def __init__(self, window, server_manager, icon: QIcon, parent=None):
        super().__init__(icon, parent)
        self._window = window
        self._mgr = server_manager

        menu = QMenu()
        menu.addAction("Show window", window.show)
        menu.addSeparator()
        self._act_start = menu.addAction("Start server", self._start)
        self._act_stop = menu.addAction("Stop server", server_manager.stop)
        menu.addSeparator()
        menu.addAction("Quit", QApplication.instance().quit)
        self.setContextMenu(menu)

        self.activated.connect(self._on_activated)
        server_manager.started.connect(self._on_started)
        server_manager.stopped.connect(self._on_stopped)
        self._on_stopped(0)

        if not QSystemTrayIcon.isSystemTrayAvailable():
            logger.warning("System tray not available on this desktop environment")
        else:
            self.show()

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._window.show()
            self._window.raise_()

    def _start(self):
        self._window.show()
        self._window.server_tab._toggle()

    def _on_started(self):
        self._act_start.setEnabled(False)
        self._act_stop.setEnabled(True)

    def _on_stopped(self, _exit_code=0):
        self._act_start.setEnabled(True)
        self._act_stop.setEnabled(False)
