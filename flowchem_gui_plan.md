# FlowChem GUI — Planning Document

A simple Qt desktop application to manage the [FlowChem](https://github.com/automatedchemistry/flowchem) server.

---

## Coding Philosophy

- **Concise and pythonic** — prefer idiomatic Python; avoid boilerplate and verbosity.
- **No gold-plating** — implement only what is specified here; do not add features speculatively.
- **No comments that restate the code** — only add a comment when the *why* is non-obvious.
- **Flat over nested** — prefer simple, readable logic over deep class hierarchies.

---

## Goals

Keep the application simple and focused. The FlowChem server handles all device communication and validation — the GUI only needs to:

1. Load, edit, and save the configuration file (`config.toml`)
2. Launch and stop the FlowChem server
3. Run device autodiscovery and show the results
4. View the server process log in real time
5. Open the FlowChem API browser in the system browser

---

## Recommended Stack

| Concern | Choice | Notes |
|---|---|---|
| GUI framework | `PySide6` | LGPL license, no GPL concerns |
| Logging | `loguru` | Same library FlowChem uses; custom sink forwards GUI logs to the Logs tab |
| Process management | `QProcess` | Integrates with Qt event loop, no extra threads needed |
| System tray | `QSystemTrayIcon` | Built into Qt, no extra dependency |
| TOML reading | `tomllib` | Standard library (Python ≥ 3.11) |
| TOML writing | `tomli-w` | Lightweight, pip install |
| Open URL | `QDesktopServices` | Opens API browser in system browser |
| Settings persistence | `QSettings` | Saves last-used config path between sessions |
| Headless launch | `pythonw` (Windows) / `nohup` or `.desktop` (Linux) | |

---

## Window Layout

The application has a single main window with **4 tabs** and a **persistent status bar**.

```
┌─────────────────────────────────────────────┐
│  FlowChem Manager                    ● ○ ✕  │
├──────────────┬──────────┬────────────┬──────┤
│ Config editor│  Server  │  Discover  │ Logs │
├─────────────────────────────────────────────┤
│                                             │
│             (tab content)                   │
│                                             │
├─────────────────────────────────────────────┤
│ ● Server stopped          Tray: active      │
└─────────────────────────────────────────────┘
```

The status dot in the status bar shows:
- 🔴 Red — server stopped
- 🟢 Green — server running

---

## Tab 1 — Config Editor

**Purpose:** Load, edit, and save the FlowChem `config.toml` file.

**Widgets:**
- Path field (`QLineEdit`) + **Browse** button → file dialog to pick the `.toml` file
- Plain text editor (`QPlainTextEdit`) — displays the raw TOML content
- **Load** button — reads the file into the editor
- **Save** button — writes the editor content back to the file

**Notes:**
- The last-used config path is saved via `QSettings` and restored on next launch. If the saved path still exists, the file is loaded automatically on startup.
- No TOML validation in the GUI. The FlowChem server handles validation on startup.
- Optional later: add basic TOML syntax highlighting via `QSyntaxHighlighter`.

```python
self.path_edit = QLineEdit()
self.browse_btn = QPushButton("Browse")
self.editor = QPlainTextEdit()
self.load_btn = QPushButton("Load")
self.save_btn = QPushButton("Save")
```

---

## Tab 2 — Server

**Purpose:** Start and stop the FlowChem server process.

**Widgets:**
- Server address field (default: `http://localhost:8000`) — editable
- **Debug mode** checkbox — when checked, passes `--debug` to `flowchem` for DEBUG-level log output (default: unchecked, INFO level)
- **Start / Stop** single toggle button — same button, changes label and style based on server state:
  - Stopped → green background, label **"Start"**
  - Running → red background, label **"Stop"**
- **Open API browser** link — opens `http://localhost:8000/docs` in the system browser

**Behaviour:**
- Clicking while stopped → launches `flowchem <config_path>` (+ `--debug` if checked) via `QProcess`. The `flowchem` executable is expected to be on `PATH`.
- Clicking while running → calls `process.terminate()` (then `kill()` after a short timeout if needed)
- The status bar dot and button state track `ServerManager.started` / `ServerManager.stopped` signals

---

## UI Locking While Server is Running

While the FlowChem server is running, the UI is partially locked — the user can only stop the server and view logs.

| Element | Running | Stopped |
|---|---|---|
| Tab 1 — Config | Disabled | Enabled |
| Tab 2 — Toggle button | Enabled (shows "Stop") | Enabled (shows "Start") |
| Tab 2 — Address field + Debug checkbox | Disabled | Enabled |
| Tab 3 — Discover | Disabled | Enabled |
| Tab 4 — Logs | Always enabled | Always enabled |
| Tray → Start | Disabled | Enabled |
| Tray → Stop | Enabled | Disabled |

`MainWindow` listens to `ServerManager.started` / `ServerManager.stopped` and calls `setEnabled()` on the affected widgets.

---

## Tab 3 — Discover

**Purpose:** Run `flowchem-autodiscover` and show the results.

**Widgets:**
- **Run autodiscover** button
- Output text area (`QPlainTextEdit`, read-only) — streams stdout and stderr from the autodiscover process
- **Copy to editor** button — pastes the discovered config text into Tab 1's editor

> ⚠️ **Important:** Show this warning before running autodiscover:
> *"Autodiscover communicates over serial ports. Unsupported devices could be placed in an unsafe state. Continue?"*
> (This warning comes from the FlowChem documentation.)

---

## Tab 4 — Logs

**Purpose:** Show all log output in one place — both the running FlowChem server process and the GUI app's own internal messages.

**Two log sources:**

1. **FlowChem server logs** — streamed from `QProcess` stderr. FlowChem uses [loguru](https://github.com/Delgan/loguru) and by default writes INFO-level logs to stderr. Passing `--debug` when starting the process switches it to DEBUG level (more verbose).

2. **GUI internal logs** — the app itself logs events (e.g., "config file saved", "server started", errors). These are also sent to loguru inside the GUI with a custom sink that forwards them to the log view widget.

**Widgets:**
- Log view (`QPlainTextEdit`, read-only) — auto-scrolls to the bottom
- **Clear** button

**Loguru sink for internal GUI logs:**
```python
from loguru import logger

def _log_sink(message):
    self.log_view.appendPlainText(message.strip())
    self.log_view.verticalScrollBar().setValue(
        self.log_view.verticalScrollBar().maximum()
    )

logger.add(_log_sink, level="DEBUG", format="{time:HH:mm:ss} | {level} | {message}")
```

**FlowChem process log streaming (via QProcess):**
```python
def on_stderr(self):
    text = self.process.readAllStandardError().data().decode()
    self.log_view.appendPlainText(text.strip())
    self.log_view.verticalScrollBar().setValue(
        self.log_view.verticalScrollBar().maximum()
    )
```

> FlowChem writes logs to stderr (not stdout) by default. The `--debug` flag enables DEBUG-level output. Both are captured by `QProcess`.

---

## Process Management

Use `QProcess` to manage the FlowChem server subprocess. It integrates directly into Qt's event loop — no extra threads needed.

```python
self.process = QProcess()
self.process.readyReadStandardOutput.connect(self.on_stdout)
self.process.readyReadStandardError.connect(self.on_stderr)
self.process.finished.connect(self.on_finished)

def start_server(self):
    config_path = self.path_edit.text()
    self.process.start("flowchem", [config_path])

def stop_server(self):
    self.process.terminate()

def on_finished(self, exit_code, exit_status):
    self.update_status(running=False)
```

---

## System Tray Icon

Use `QSystemTrayIcon` (built into PySide6 / PyQt6). No extra dependency like `pystray` needed.

**Icon:** Use the FlowChem logo SVG (`resources/icons/flowchem_logo.svg`, copied from `flowchem/docs/_static/`). Qt can load SVGs directly via `QIcon` — no conversion needed (requires `QtSvg`, included in PySide6).

```python
icon = QIcon("resources/icons/flowchem_logo.svg")
tray.setIcon(icon)
app.setWindowIcon(icon)
```

> The logo is a wide wordmark (≈ 2:1 aspect ratio). In the tray slot it will be letterboxed into a square — this is acceptable. If a square crop is later preferred, extract just the symbol portion of the SVG.

**Close behaviour:** Clicking the main window's X button **minimizes to tray** (the app keeps running). The user must choose **Quit** from the tray menu to fully exit. This requires:
- `app.setQuitOnLastWindowClosed(False)` in `main.py`
- Overriding `closeEvent` in `MainWindow` to call `event.ignore()` + `self.hide()`

**Tray menu items:**
- Show window
- Start server
- Stop server
- Quit

### Linux compatibility

`QSystemTrayIcon` works on Linux, but with platform differences:

| Desktop | Status |
|---|---|
| KDE Plasma | ✅ Works natively |
| XFCE, LXQt, MATE | ✅ Works natively |
| GNOME (Ubuntu default) | ⚠️ Requires the **AppIndicator** GNOME Shell extension |

**Recommended approach:** Detect tray availability with `QSystemTrayIcon.isSystemTrayAvailable()` and show a fallback message if the tray is not supported, rather than crashing.

```python
if not QSystemTrayIcon.isSystemTrayAvailable():
    print("System tray not available on this desktop environment.")
```

---

## Project Structure

```
flowchem-gui/
├── main.py                  # Entry point — QApplication, tray icon, main window
├── app/
│   ├── main_window.py       # QMainWindow with QTabWidget
│   ├── tabs/
│   │   ├── config_tab.py    # Tab 1 — TOML file editor
│   │   ├── server_tab.py    # Tab 2 — Start/stop + API link
│   │   ├── discover_tab.py  # Tab 3 — Autodiscover runner
│   │   └── logs_tab.py      # Tab 4 — Live log viewer
│   ├── server_manager.py    # QProcess wrapper for flowchem subprocess
│   └── tray.py              # QSystemTrayIcon setup and menu
├── resources/
│   └── icons/
│       └── flowchem_logo.svg   # copied from flowchem/docs/_static/
├── pyproject.toml
└── README.md
```

---

## CLI Entry Point

The app is installed and launched via a `flowchem-gui` command. Using `[project.gui-scripts]` in `pyproject.toml` makes the launcher use `pythonw.exe` on Windows — no console window appears.

```toml
# pyproject.toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.backends.legacy:build"

[project]
name = "flowchem-gui"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "PySide6>=6.5",
    "tomli-w>=1.0",
    "loguru>=0.7",
]

[project.gui-scripts]
flowchem-gui = "main:main"
```

`main.py` must expose a `main()` function as the entry point:

```python
def main():
    # Redirect stderr to a log file early, because pythonw suppresses
    # the console — any crash before the Qt window appears would be silent.
    log_path = Path.home() / ".flowchem-gui" / "error.log"
    log_path.parent.mkdir(exist_ok=True)
    sys.stderr = open(log_path, "a")

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    window = MainWindow()
    tray = TrayIcon(window)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
```

**Installation:**
```
pip install -e .        # editable install from source
flowchem-gui            # launches silently, no console window
```

> On Linux/macOS `[project.gui-scripts]` behaves identically to `[project.scripts]` — both generate a plain shell script. The silent-launch distinction is Windows-only.

---

## Dependencies

```
# pyproject.toml replaces requirements.txt — see CLI Entry Point section above
PySide6>=6.5
tomli-w>=1.0
```

> `tomllib` is part of the Python standard library since Python 3.11.

---

## README.md

The README should cover:
1. **What it is** — one sentence description
2. **Requirements** — Python ≥ 3.11, FlowChem installed and on PATH
3. **Installation** — `pip install -e .`
4. **Usage** — `flowchem-gui` (or `python main.py` for development)
5. **Features** — brief bullet list matching the Goals section

---

## Out of Scope

The following are intentionally excluded to keep the application simple:

- TOML schema validation — handled by the FlowChem server on startup
- Device status polling / live metrics — handled by the FlowChem REST API
- Multiple config profiles
- Embedded REST API client

These can be added in a later version once the core application is stable.
