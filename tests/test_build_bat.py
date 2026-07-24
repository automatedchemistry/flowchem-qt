from pathlib import Path

import pytest

from app.windows_launcher import (
    COMMAND_EXECUTABLES,
    LAUNCHER_NAME,
    REQUIRED_EXECUTABLES,
    LauncherBuildError,
    build_launcher,
)


def create_project(project_root: Path, venv_dir: Path) -> None:
    project_root.mkdir(parents=True)
    (project_root / "main.py").write_text("# test entry point\n", encoding="utf-8")
    scripts_dir = venv_dir / "Scripts"
    scripts_dir.mkdir(parents=True)
    for executable in REQUIRED_EXECUTABLES:
        (scripts_dir / executable).write_bytes(b"")


def test_build_launcher_uses_project_relative_default_venv(tmp_path):
    project_root = tmp_path / "project with spaces"
    venv_dir = project_root / ".venv"
    create_project(project_root, venv_dir)

    launcher_path = build_launcher(project_root, Path(".venv"))

    assert launcher_path == project_root / LAUNCHER_NAME
    raw_launcher = launcher_path.read_bytes()
    launcher = raw_launcher.decode("utf-8")
    assert 'set "VENV_DIR=%~dp0.venv"' in launcher
    assert 'set "PATH=%SCRIPTS_DIR%;%PATH%"' in launcher
    assert 'cd /d "%PROJECT_DIR%"' in launcher
    assert 'set "PYTHONW=%SCRIPTS_DIR%\\pythonw.exe"' in launcher
    assert (
        'start "" "%PYTHONW%" "%PROJECT_DIR%main.py" %*'
        in launcher
    )
    assert b"\r\n" in raw_launcher
    assert b"\n" not in raw_launcher.replace(b"\r\n", b"")


def test_build_launcher_uses_relative_custom_venv_inside_project(tmp_path):
    project_root = tmp_path / "project"
    venv_dir = project_root / "environments" / "flowchem env"
    create_project(project_root, venv_dir)

    launcher_path = build_launcher(
        project_root, Path("environments") / "flowchem env"
    )

    launcher = launcher_path.read_text(encoding="utf-8")
    assert 'set "VENV_DIR=%~dp0environments\\flowchem env"' in launcher


def test_build_launcher_uses_absolute_external_venv(tmp_path):
    project_root = tmp_path / "project"
    venv_dir = tmp_path / "external venv"
    create_project(project_root, venv_dir)

    launcher_path = build_launcher(project_root, venv_dir)

    launcher = launcher_path.read_text(encoding="utf-8")
    expected_venv = str(venv_dir.resolve()).replace("/", "\\").replace("%", "%%")
    assert f'set "VENV_DIR={expected_venv}"' in launcher


def test_build_launcher_supports_base_python_layout(tmp_path):
    project_root = tmp_path / "project"
    environment_dir = tmp_path / "base python"
    create_project(project_root, environment_dir)
    (environment_dir / "Scripts" / "pythonw.exe").unlink()
    (environment_dir / "pythonw.exe").write_bytes(b"")

    launcher_path = build_launcher(project_root, environment_dir)

    launcher = launcher_path.read_text(encoding="utf-8")
    assert 'set "PYTHONW=%VENV_DIR%\\pythonw.exe"' in launcher
    assert 'start "" "%PYTHONW%" "%PROJECT_DIR%main.py" %*' in launcher


def test_build_launcher_reports_every_missing_file_without_overwriting(tmp_path):
    project_root = tmp_path / "project"
    project_root.mkdir()
    launcher_path = project_root / LAUNCHER_NAME
    launcher_path.write_text("existing launcher", encoding="utf-8")
    venv_dir = project_root / ".venv"

    with pytest.raises(LauncherBuildError) as error_info:
        build_launcher(project_root, venv_dir)

    assert error_info.value.missing_paths == [
        project_root / "main.py",
        *(venv_dir / "Scripts" / name for name in REQUIRED_EXECUTABLES),
    ]
    assert launcher_path.read_text(encoding="utf-8") == "existing launcher"


def test_generated_launcher_checks_required_files_at_runtime(tmp_path):
    project_root = tmp_path / "project"
    venv_dir = project_root / ".venv"
    create_project(project_root, venv_dir)

    launcher = build_launcher(project_root, venv_dir).read_text(encoding="utf-8")

    assert 'if not exist "%PROJECT_DIR%main.py"' in launcher
    assert 'if not exist "%PYTHONW%"' in launcher
    for executable in COMMAND_EXECUTABLES:
        assert f'if not exist "%SCRIPTS_DIR%\\{executable}"' in launcher
    assert "pause" in launcher
    assert "exit /b 1" in launcher
