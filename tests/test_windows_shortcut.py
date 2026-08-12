from pathlib import Path
from subprocess import CompletedProcess

import pytest

import app.windows_launcher as windows_launcher
from app.windows_launcher import ShortcutBuildError, create_windows_shortcut


def create_shortcut_inputs(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    destination = tmp_path / "shortcut destination & spaces"
    destination.mkdir()
    working_directory = tmp_path / "project with spaces"
    working_directory.mkdir()
    launcher_path = working_directory / "flowchem-qt.bat"
    launcher_path.write_bytes(b"@echo off\r\n")
    icon_path = working_directory / "flowchem icon.ico"
    icon_path.write_bytes(b"icon")
    shortcut_path = destination / "FlowChem Qt.lnk"
    return shortcut_path, launcher_path, icon_path, working_directory


def test_create_windows_shortcut_passes_fields_safely_via_environment(
    tmp_path, monkeypatch
):
    shortcut_path, launcher_path, icon_path, working_directory = create_shortcut_inputs(
        tmp_path
    )
    captured = {}

    def fake_run(command, **kwargs):
        captured["command"] = command
        captured["kwargs"] = kwargs
        Path(kwargs["env"]["FLOWCHEM_QT_SHORTCUT_PATH"]).write_bytes(b"shortcut")
        return CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(windows_launcher.subprocess, "run", fake_run)

    result = create_windows_shortcut(
        shortcut_path,
        launcher_path,
        icon_path,
        working_directory,
    )

    assert result == shortcut_path.resolve()
    command = captured["command"]
    kwargs = captured["kwargs"]
    assert command[:5] == [
        "powershell.exe",
        "-NoLogo",
        "-NoProfile",
        "-NonInteractive",
        "-Command",
    ]
    assert str(shortcut_path.resolve()) not in command[-1]
    assert kwargs["env"]["FLOWCHEM_QT_SHORTCUT_PATH"] == str(shortcut_path.resolve())
    assert kwargs["env"]["FLOWCHEM_QT_LAUNCHER_PATH"] == str(launcher_path.resolve())
    assert kwargs["env"]["FLOWCHEM_QT_WORKING_DIRECTORY"] == str(
        working_directory.resolve()
    )
    assert kwargs["env"]["FLOWCHEM_QT_ICON_PATH"] == str(icon_path.resolve())
    assert kwargs["creationflags"] == getattr(
        windows_launcher.subprocess, "CREATE_NO_WINDOW", 0
    )


def test_create_windows_shortcut_reports_powershell_failure(tmp_path, monkeypatch):
    shortcut_path, launcher_path, icon_path, working_directory = create_shortcut_inputs(
        tmp_path
    )

    def fake_run(command, **_kwargs):
        return CompletedProcess(
            command,
            1,
            stdout="",
            stderr="WScript.Shell failed",
        )

    monkeypatch.setattr(windows_launcher.subprocess, "run", fake_run)

    with pytest.raises(ShortcutBuildError, match="WScript.Shell failed"):
        create_windows_shortcut(
            shortcut_path,
            launcher_path,
            icon_path,
            working_directory,
        )


def test_create_windows_shortcut_requires_created_output(tmp_path, monkeypatch):
    shortcut_path, launcher_path, icon_path, working_directory = create_shortcut_inputs(
        tmp_path
    )

    def fake_run(command, **_kwargs):
        return CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(windows_launcher.subprocess, "run", fake_run)

    with pytest.raises(ShortcutBuildError, match="completed without creating"):
        create_windows_shortcut(
            shortcut_path,
            launcher_path,
            icon_path,
            working_directory,
        )


def test_create_windows_shortcut_validates_required_paths(tmp_path):
    destination = tmp_path / "destination"
    destination.mkdir()

    with pytest.raises(ShortcutBuildError) as error_info:
        create_windows_shortcut(
            destination / "FlowChem Qt.lnk",
            tmp_path / "missing.bat",
            tmp_path / "missing.ico",
            tmp_path / "missing project",
        )

    message = str(error_info.value)
    assert "missing.bat" in message
    assert "missing.ico" in message
    assert "missing project" in message
