import ctypes
import sys
from pathlib import Path

from PyQt5.QtWidgets import QApplication, QMessageBox

from app.cli import parse_args
from app.single_instance import (
    InstanceStatus,
    SingleInstanceCoordinator,
    SingleInstanceError,
    server_name_for_user,
)

_APP_ID = "org.flowchem.gui"


def _set_windows_app_id():
    if sys.platform != "win32":
        return
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(_APP_ID)


def main(argv: list[str] | None = None) -> int:
    _set_windows_app_id()
    argv = sys.argv if argv is None else argv
    args, qt_argv = parse_args(argv)

    # pythonw suppresses the console — redirect stderr so crashes before the
    # Qt window appears are not silently swallowed.
    app_dir = Path.home() / ".flowchem-qt"
    log_path = app_dir / "error.log"
    app_dir.mkdir(exist_ok=True)
    sys.stderr = open(log_path, "a", encoding="utf-8")

    app = QApplication(qt_argv)
    coordinator = SingleInstanceCoordinator(
        server_name_for_user(_APP_ID, Path.home()),
        app_dir / "instance.lock",
        app,
    )
    try:
        instance_status = coordinator.start()
    except SingleInstanceError as error:
        QMessageBox.critical(
            None,
            "FlowChem Manager startup failed",
            str(error),
        )
        return 1

    if instance_status == InstanceStatus.EXISTING_NOTIFIED:
        return 0
    if instance_status == InstanceStatus.EXISTING_UNREACHABLE:
        QMessageBox.warning(
            None,
            "FlowChem Manager is already running",
            "The existing FlowChem Manager instance could not be activated.",
        )
        return 1

    app._flowchem_single_instance = coordinator
    app.aboutToQuit.connect(coordinator.close)

    from qfluentwidgets import setThemeColor
    from PyQt5.QtCore import QSettings
    from PyQt5.QtGui import QIcon

    from app.main_window import MainWindow
    from app.theme import apply_theme, load_theme
    from app.tray import TrayIcon

    settings = QSettings("flowchem", "gui")
    apply_theme(app, load_theme(settings))
    setThemeColor("#0065d5")
    app.setQuitOnLastWindowClosed(args.no_tray)

    icon_dir = Path(__file__).parent / "resources" / "icons"
    window_icon = QIcon(str(icon_dir / "flowchem_app_icon.ico"))
    tray_icon = QIcon(str(icon_dir / "flowchem_logo.svg"))
    app._flowchem_window_icon = window_icon
    app._flowchem_tray_icon = tray_icon
    app.setWindowIcon(window_icon)

    window = MainWindow(
        minimize_to_tray=not args.no_tray,
        window_icon=window_icon,
        settings=settings,
    )
    coordinator.activation_requested.connect(window.show_and_activate)
    if not args.no_tray:
        TrayIcon(window, window.server_manager, tray_icon, app)
    window.show()
    return app.exec_()


if __name__ == "__main__":
    raise SystemExit(main())
