from __future__ import annotations

import hashlib
import os
from enum import Enum, auto
from pathlib import Path

from PyQt5.QtCore import QLockFile, QObject, pyqtSignal
from PyQt5.QtNetwork import QLocalServer, QLocalSocket


_ACTIVATE_MESSAGE = b"activate\n"


class InstanceStatus(Enum):
    PRIMARY = auto()
    EXISTING_NOTIFIED = auto()
    EXISTING_UNREACHABLE = auto()


class SingleInstanceError(RuntimeError):
    pass


def server_name_for_user(app_id: str, user_home: Path) -> str:
    normalized_home = str(user_home.resolve())
    if os.name == "nt":
        normalized_home = normalized_home.casefold()
    user_digest = hashlib.sha256(normalized_home.encode("utf-8")).hexdigest()[:16]
    return f"{app_id}.instance.{user_digest}"


class SingleInstanceCoordinator(QObject):
    activation_requested = pyqtSignal()

    def __init__(
        self,
        server_name: str,
        lock_path: Path,
        parent=None,
        *,
        connect_timeout_ms: int = 250,
        notify_attempts: int = 4,
    ):
        super().__init__(parent)
        self._server_name = server_name
        self._lock_path = lock_path.resolve()
        self._connect_timeout_ms = connect_timeout_ms
        self._notify_attempts = notify_attempts
        self._is_primary = False

        self._lock = QLockFile(str(self._lock_path))
        self._lock.setStaleLockTime(0)
        self._server = QLocalServer(self)
        self._server.setSocketOptions(QLocalServer.UserAccessOption)
        self._server.newConnection.connect(self._accept_connections)

    def start(self) -> InstanceStatus:
        try:
            self._lock_path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as error:
            raise SingleInstanceError(
                f"Could not create the instance-lock directory: {error}"
            ) from error

        if self._lock.tryLock(0):
            QLocalServer.removeServer(self._server_name)
            if not self._server.listen(self._server_name):
                server_error = self._server.errorString()
                self._lock.unlock()
                raise SingleInstanceError(
                    f"Could not start the local activation server: {server_error}"
                )
            self._is_primary = True
            return InstanceStatus.PRIMARY

        if self._lock.error() in (QLockFile.PermissionError, QLockFile.UnknownError):
            raise SingleInstanceError(
                f"Could not acquire the instance lock: {self._lock_path}"
            )
        if self._notify_existing_instance():
            return InstanceStatus.EXISTING_NOTIFIED
        return InstanceStatus.EXISTING_UNREACHABLE

    def close(self) -> None:
        if not self._is_primary:
            return
        self._server.close()
        QLocalServer.removeServer(self._server_name)
        self._lock.unlock()
        self._is_primary = False

    def _notify_existing_instance(self) -> bool:
        for _attempt in range(self._notify_attempts):
            socket = QLocalSocket()
            socket.connectToServer(self._server_name)
            if not socket.waitForConnected(self._connect_timeout_ms):
                socket.abort()
                continue
            accepted = socket.write(_ACTIVATE_MESSAGE)
            socket.flush()
            delivered = accepted == len(_ACTIVATE_MESSAGE) and (
                socket.bytesToWrite() == 0
                or socket.waitForBytesWritten(self._connect_timeout_ms)
            )
            socket.disconnectFromServer()
            return delivered
        return False

    def _accept_connections(self) -> None:
        while self._server.hasPendingConnections():
            socket = self._server.nextPendingConnection()
            if socket is None:
                continue
            socket.readyRead.connect(
                lambda connected_socket=socket: self._read_request(connected_socket)
            )
            socket.disconnected.connect(socket.deleteLater)
            if socket.bytesAvailable():
                self._read_request(socket)

    def _read_request(self, socket: QLocalSocket) -> None:
        message = bytes(socket.readAll())
        if _ACTIVATE_MESSAGE in message:
            self.activation_requested.emit()
        socket.disconnectFromServer()
