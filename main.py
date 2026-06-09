import argparse
import ctypes
import sys
from pathlib import Path

from qfluentwidgets import Theme, setTheme, setThemeColor
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from app.main_window import MainWindow
from app.tray import TrayIcon

_APP_ID = "org.flowchem.gui"


def _parse_args(argv: list[str]) -> tuple[argparse.Namespace, list[str]]:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--no-tray",
        action="store_true",
        help="Disable the system tray; closing the window exits the application.",
    )
    args, qt_args = parser.parse_known_args(argv[1:])
    return args, [argv[0], *qt_args]


def _set_windows_app_id():
    if sys.platform != "win32":
        return
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(_APP_ID)


def main():
    _set_windows_app_id()
    args, qt_argv = _parse_args(sys.argv)

    # pythonw suppresses the console — redirect stderr so crashes before the
    # Qt window appears are not silently swallowed.
    log_path = Path.home() / ".flowchem-qt" / "error.log"
    log_path.parent.mkdir(exist_ok=True)
    sys.stderr = open(log_path, "a", encoding="utf-8")

    app = QApplication(qt_argv)
    setTheme(Theme.AUTO)
    setThemeColor("#0065d5")
    app.setQuitOnLastWindowClosed(args.no_tray)

    icon_dir = Path(__file__).parent / "resources" / "icons"
    window_icon = QIcon(str(icon_dir / "flowchem_app_icon.ico"))
    tray_icon = QIcon(str(icon_dir / "flowchem_logo.svg"))
    app._flowchem_window_icon = window_icon
    app._flowchem_tray_icon = tray_icon
    app.setWindowIcon(window_icon)

    window = MainWindow(minimize_to_tray=not args.no_tray, window_icon=window_icon)
    if not args.no_tray:
        TrayIcon(window, window.server_manager, tray_icon, app)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
