from app.server_manager import ServerManager


class FakeProcess:
    def __init__(self):
        self.calls = []

    def start(self, exe, args):
        self.calls.append((exe, args))


def make_manager():
    manager = ServerManager()
    fake_proc = FakeProcess()
    manager._proc = fake_proc
    return manager, fake_proc


def test_start_defaults_to_localhost_host():
    manager, proc = make_manager()

    manager.start("config.toml")

    assert proc.calls == [("flowchem", ["config.toml", "--host", "127.0.0.1"])]


def test_start_can_expose_on_local_network():
    manager, proc = make_manager()

    manager.start("config.toml", host="0.0.0.0")

    assert proc.calls == [("flowchem", ["config.toml", "--host", "0.0.0.0"])]


def test_start_keeps_debug_and_simulation_options():
    manager, proc = make_manager()

    manager.start("config.toml", debug=True, sim=True, host="0.0.0.0")

    assert proc.calls == [
        ("flowchem-sim", ["config.toml", "--host", "0.0.0.0", "--debug"])
    ]
