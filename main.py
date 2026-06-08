import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from app.main_window import MainWindow
from app.tray import TrayIcon


def main():
    # pythonw suppresses the console — redirect stderr so crashes before the
    # Qt window appears are not silently swallowed.
    log_path = Path.home() / ".flowchem-gui" / "error.log"
    log_path.parent.mkdir(exist_ok=True)
    sys.stderr = open(log_path, "a", encoding="utf-8")

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    icon_path = Path(__file__).parent / "resources" / "icons" / "flowchem_logo.svg"
    icon = QIcon(str(icon_path))
    app.setWindowIcon(icon)

    window = MainWindow()
    TrayIcon(window, window.server_manager, icon, app)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
