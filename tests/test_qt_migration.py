import tomllib
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

_RUNTIME_SOURCE_PATHS = [
    PROJECT_ROOT / "main.py",
    PROJECT_ROOT / "scripts" / "generate_icon.py",
    *sorted((PROJECT_ROOT / "app").rglob("*.py")),
]


def test_runtime_sources_do_not_import_pyqt_bindings():
    forbidden = ["PyQt5", "PyQt6", "pyqtSignal"]

    offenders = [
        f"{path.relative_to(PROJECT_ROOT)}: {token}"
        for path in _RUNTIME_SOURCE_PATHS
        for token in forbidden
        if token in path.read_text(encoding="utf-8")
    ]

    assert offenders == []


def test_runtime_sources_use_qt6_scoped_enums():
    # PySide6 (Qt 6) requires scoped enums. These bare (PyQt5-style) member
    # accesses, plus the unscoped QMessageBox constants, would break at runtime.
    forbidden_members = [
        "QProcess.FailedToStart",
        "QProcess.Crashed",
        "QProcess.Timedout",
        "QProcess.WriteError",
        "QProcess.ReadError",
        "QProcess.UnknownError",
        "QProcess.Running",
        "QLocalServer.UserAccessOption",
        "QLockFile.PermissionError",
        "QLockFile.UnknownError",
        "QSystemTrayIcon.DoubleClick",
        "QFileDialog.ShowDirsOnly",
        "QImage.Format_ARGB32_Premultiplied",
        "QPainter.Antialiasing",
        "QPainter.SmoothPixmapTransform",
        "QIODevice.WriteOnly",
    ]

    offenders = [
        f"{path.relative_to(PROJECT_ROOT)}: {member}"
        for path in _RUNTIME_SOURCE_PATHS
        for member in forbidden_members
        if member in path.read_text(encoding="utf-8")
    ]

    assert offenders == []


def test_pyproject_uses_pyside6_dependencies():
    data = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    dependencies = data["project"]["dependencies"]

    assert any(dependency.startswith("PySide6") for dependency in dependencies)
    assert any(
        dependency.startswith("PySide6-Fluent-Widgets") for dependency in dependencies
    )
    assert not any(
        dependency.startswith(("PyQt5", "PyQt6")) for dependency in dependencies
    )
    assert not any(
        "PyQt" in dependency and "Fluent" in dependency for dependency in dependencies
    )
