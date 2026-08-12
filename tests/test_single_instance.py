import os
import subprocess
import sys
import threading
import time
import uuid

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtCore import QLockFile
from PyQt5.QtWidgets import QApplication

from app.single_instance import (
    InstanceStatus,
    SingleInstanceCoordinator,
    server_name_for_user,
)

_APP = None


def get_app():
    global _APP
    _APP = QApplication.instance() or QApplication(["test", "-platform", "offscreen"])
    _APP.setQuitOnLastWindowClosed(False)
    return _APP


def unique_server_name() -> str:
    return f"org.flowchem.gui.test.{uuid.uuid4().hex}"


def process_events_until(predicate, timeout=2.0):
    app = get_app()
    deadline = time.monotonic() + timeout
    while not predicate() and time.monotonic() < deadline:
        app.processEvents()
        time.sleep(0.01)
    return predicate()


def test_server_name_is_stable_per_user_and_distinct_between_users(tmp_path):
    app_id = "org.flowchem.gui"
    first_home = tmp_path / "first user"
    second_home = tmp_path / "second user"

    assert server_name_for_user(app_id, first_home) == server_name_for_user(
        app_id, first_home
    )
    assert server_name_for_user(app_id, first_home) != server_name_for_user(
        app_id, second_home
    )


def test_secondary_instance_notifies_primary(tmp_path):
    get_app()
    server_name = unique_server_name()
    lock_path = tmp_path / "instance.lock"
    primary = SingleInstanceCoordinator(server_name, lock_path)
    activations = []
    statuses = []
    primary.activation_requested.connect(lambda: activations.append(True))

    def notify_primary():
        secondary = SingleInstanceCoordinator(server_name, lock_path)
        statuses.append(secondary.start())
        secondary.close()

    try:
        assert primary.start() == InstanceStatus.PRIMARY
        secondary_thread = threading.Thread(target=notify_primary)
        secondary_thread.start()
        assert process_events_until(lambda: activations and statuses)
        secondary_thread.join(timeout=2)
        assert not secondary_thread.is_alive()
        assert statuses == [InstanceStatus.EXISTING_NOTIFIED]
    finally:
        primary.close()


def test_locked_but_unreachable_instance_never_becomes_primary(tmp_path):
    get_app()
    lock_path = tmp_path / "instance.lock"
    held_lock = QLockFile(str(lock_path))
    held_lock.setStaleLockTime(0)
    assert held_lock.tryLock(0)
    coordinator = SingleInstanceCoordinator(
        unique_server_name(),
        lock_path,
        connect_timeout_ms=10,
        notify_attempts=1,
    )

    try:
        assert coordinator.start() == InstanceStatus.EXISTING_UNREACHABLE
    finally:
        coordinator.close()
        held_lock.unlock()


def test_stale_lock_is_recovered_before_listening(tmp_path):
    get_app()
    lock_path = tmp_path / "instance.lock"
    script = (
        "import os, sys\n"
        "from PyQt5.QtCore import QLockFile\n"
        "lock = QLockFile(sys.argv[1])\n"
        "lock.setStaleLockTime(0)\n"
        "assert lock.tryLock(0)\n"
        "os._exit(0)\n"
    )
    subprocess.run(
        [sys.executable, "-c", script, str(lock_path)],
        check=True,
        env=os.environ.copy(),
    )
    assert lock_path.exists()
    coordinator = SingleInstanceCoordinator(unique_server_name(), lock_path)

    try:
        assert coordinator.start() == InstanceStatus.PRIMARY
    finally:
        coordinator.close()
