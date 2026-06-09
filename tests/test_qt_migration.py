from pathlib import Path
import tomllib


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_runtime_sources_do_not_import_pyside6():
    source_paths = [
        PROJECT_ROOT / "main.py",
        PROJECT_ROOT / "scripts" / "generate_icon.py",
        *sorted((PROJECT_ROOT / "app").rglob("*.py")),
    ]

    offenders = [
        str(path.relative_to(PROJECT_ROOT))
        for path in source_paths
        if "PySide6" in path.read_text(encoding="utf-8")
    ]

    assert offenders == []


def test_runtime_sources_do_not_use_qt6_scoped_enums():
    source_paths = [
        PROJECT_ROOT / "main.py",
        PROJECT_ROOT / "scripts" / "generate_icon.py",
        *sorted((PROJECT_ROOT / "app").rglob("*.py")),
    ]
    qt6_only_patterns = [
        "ActivationReason.",
        "Format.",
        "OpenModeFlag.",
        "ProcessError.",
        "ProcessState.",
        "StandardButton.",
    ]

    offenders = [
        f"{path.relative_to(PROJECT_ROOT)}: {pattern}"
        for path in source_paths
        for pattern in qt6_only_patterns
        if pattern in path.read_text(encoding="utf-8")
    ]

    assert offenders == []


def test_pyproject_uses_pyqt5_dependencies():
    data = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    dependencies = data["project"]["dependencies"]

    assert "PyQt5>=5.15.11" in dependencies
    assert "PyQt-Fluent-Widgets>=1.11.2" in dependencies
    assert not any(dependency.startswith("PySide6") for dependency in dependencies)
    assert not any(dependency.startswith("PyQt6") for dependency in dependencies)
