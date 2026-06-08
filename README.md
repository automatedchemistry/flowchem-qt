# FlowChem GUI

A simple desktop application to manage the [FlowChem](https://github.com/automatedchemistry/flowchem) server.

## Requirements

- Python ≥ 3.11
- FlowChem installed and available on `PATH` (activate your FlowChem virtualenv before launching)

## Installation

```bash
pip install -e .
```

## Usage

```bash
flowchem-gui          # launches silently (no console window on Windows)
python main.py        # development / debug
```

## Window Overview

The main window has four tabs and a persistent status bar at the bottom.

### Status bar

Always visible. Shows a coloured dot indicating the current server state:
- **Red dot** — server is stopped
- **Green dot** — server is running

### Tab 1 — Config editor

Manages the FlowChem configuration file (`config.toml`).

| Element | Description |
|---|---|
| Path field | Full path to the config file. Remembered between sessions. |
| Browse | Opens a file dialog to pick a `.toml` file. |
| Load | Reads the selected file into the editor. |
| Save | Writes the editor content back to disk. |
| Editor area | Plain-text editor for the raw TOML content. No validation — the FlowChem server validates on startup. |

> This tab is disabled while the server is running.

### Tab 2 — Server

Controls the FlowChem server process.

| Element | Description |
|---|---|
| Server address | Base URL of the running server (default `http://localhost:8000`). Used by the API browser link. |
| Debug mode | When checked, passes `--debug` to FlowChem for verbose (DEBUG-level) log output. |
| Simulation mode | When checked, launches `flowchem-sim` instead of `flowchem`. All real device drivers are replaced with simulated counterparts — no physical hardware required. The same `config.toml` is used unchanged. |
| Start / Stop button | Single toggle button. Green when stopped, red when running. |
| Open API browser | Opens `<server address>/docs` in the system browser. |

> The address field, debug checkbox, and simulation mode checkbox are disabled while the server is running.

### Tab 3 — Discover

Runs the `flowchem-autodiscover` tool to detect connected devices.

| Element | Description |
|---|---|
| Run autodiscover | Shows a safety warning, then runs `flowchem-autodiscover`. Output streams in real time. |
| Output area | Read-only display of the autodiscover stdout and stderr. |
| Copy to editor | Copies the autodiscover output into the Config editor (Tab 1) for review and saving. |

> A warning dialog is shown before running because autodiscovery communicates over serial ports and could place unsupported devices in an unsafe state.
>
> This tab is disabled while the server is running.

### Tab 4 — Logs

Live log viewer. Always accessible, even while the server is running.

| Element | Description |
|---|---|
| Log area | Streams output from two sources: the FlowChem server process (stderr) and internal GUI events. Auto-scrolls to the latest entry. |
| Clear | Clears the log area. |

### System tray

Closing the main window minimises it to the system tray — the application keeps running in the background. Right-click the tray icon to access the menu:

| Menu item | Description |
|---|---|
| Show window | Brings the main window back to the foreground. |
| Start server | Starts the FlowChem server (uses the config path currently set in Tab 1). |
| Stop server | Stops the running server. |
| Quit | Fully exits the application.
