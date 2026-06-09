from PyQt5.QtCore import QObject, QProcess, QTimer, pyqtSignal
from loguru import logger

_PROC_ERRORS = {
    QProcess.FailedToStart: "Failed to start — is 'flowchem' on your PATH?",
    QProcess.Crashed: "Process crashed unexpectedly",
    QProcess.Timedout: "Process timed out",
    QProcess.WriteError: "Write error communicating with process",
    QProcess.ReadError: "Read error communicating with process",
    QProcess.UnknownError: "Unknown process error",
}


class ServerManager(QObject):
    started = pyqtSignal()
    stopped = pyqtSignal(int)
    stdout_ready = pyqtSignal(str)
    stderr_ready = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._proc = QProcess(self)
        self._proc.readyReadStandardOutput.connect(self._on_stdout)
        self._proc.readyReadStandardError.connect(self._on_stderr)
        self._proc.started.connect(self.started)
        self._proc.finished.connect(self._on_finished)
        self._proc.errorOccurred.connect(self._on_error)

    def start(self, config_path: str, debug: bool = False, sim: bool = False):
        exe = "flowchem-sim" if sim else "flowchem"
        args = [config_path] + (["--debug"] if debug else [])
        logger.info(f"Starting: {exe} {' '.join(args)}")
        self._proc.start(exe, args)

    def stop(self):
        if not self.is_running():
            return
        logger.info("Stopping flowchem server")
        self._proc.terminate()
        QTimer.singleShot(3000, self._force_kill)

    def is_running(self) -> bool:
        return self._proc.state() == QProcess.Running

    def _force_kill(self):
        if self.is_running():
            logger.warning("Server did not stop gracefully — killing process")
            self._proc.kill()

    def _on_stdout(self):
        text = self._proc.readAllStandardOutput().data().decode(errors="replace")
        self.stdout_ready.emit(text)

    def _on_stderr(self):
        text = self._proc.readAllStandardError().data().decode(errors="replace")
        self.stderr_ready.emit(text)

    def _on_error(self, error):
        msg = _PROC_ERRORS.get(error, f"Process error ({error})")
        logger.error(f"FlowChem process error: {msg}")
        self.error.emit(msg)

    def _on_finished(self, exit_code, _status):
        logger.info(f"FlowChem exited with code {exit_code}")
        self.stopped.emit(exit_code)
