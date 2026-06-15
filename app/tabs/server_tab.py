import socket
from urllib.parse import urlparse

from PyQt5.QtCore import QUrl
from PyQt5.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    CheckBox,
    ComboBox,
    HyperlinkButton,
    LineEdit,
    PrimaryPushButton,
)

_LOCAL_ONLY_INDEX = 0
_LOCAL_NETWORK_INDEX = 1
_ACCESS_OPTIONS = [
    ("This computer only", "127.0.0.1"),
    ("Local network", "0.0.0.0"),
]
_ACCESS_DESCRIPTIONS = {
    _LOCAL_ONLY_INDEX: "Recommended. FlowChem can be opened only from this computer.",
    _LOCAL_NETWORK_INDEX: (
        "Other computers on the same Wi-Fi or lab network may open FlowChem. "
        "Use this only on a network you trust."
    ),
}


class ServerTab(QWidget):
    def __init__(self, server_manager, config_tab, parent=None):
        super().__init__(parent)
        self._mgr = server_manager
        self._cfg = config_tab

        self.address_edit = LineEdit()
        self.address_edit.setText("http://localhost:8000")
        self.debug_chk = CheckBox("Debug mode")
        self.sim_chk = CheckBox("Simulation mode")
        self.access_combo = ComboBox()
        self.access_combo.addItems([label for label, _host in _ACCESS_OPTIONS])
        self.access_description = QLabel()
        self.access_description.setWordWrap(True)
        self.toggle_btn = PrimaryPushButton("Start")
        self.open_btn = HyperlinkButton(self._resolved_docs_url(), self._docs_label())

        self.address_edit.setToolTip("Base URL for the running FlowChem server.")
        self.debug_chk.setToolTip("Pass --debug to FlowChem for verbose logging.")
        self.sim_chk.setToolTip("Launch flowchem-sim instead of real device drivers.")
        self.access_combo.setToolTip("Choose who can open the running FlowChem server.")
        self.access_description.setToolTip("Explanation of the selected access option.")
        self.toggle_btn.setToolTip("Start or stop the FlowChem server.")
        self.open_btn.setToolTip("Open the server API documentation in your browser.")
        self._update_access_description()

        form = QFormLayout()
        form.addRow("Server address:", self.address_edit)
        form.addRow("", self.debug_chk)
        form.addRow("", self.sim_chk)
        form.addRow("Server access:", self.access_combo)
        form.addRow("", self.access_description)

        btn_row = QHBoxLayout()
        btn_row.addWidget(self.toggle_btn)
        btn_row.addWidget(self.open_btn)
        btn_row.addStretch()

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addLayout(btn_row)
        layout.addStretch()

        self.toggle_btn.clicked.connect(self._toggle)
        self.address_edit.textChanged.connect(self._update_open_btn)
        self.access_combo.currentIndexChanged.connect(self._on_access_changed)
        server_manager.started.connect(self._on_started)
        server_manager.stopped.connect(self._on_stopped)

    def _toggle(self):
        if self._mgr.is_running():
            self._mgr.stop()
        else:
            path = self._cfg.get_config_path()
            if not path:
                QMessageBox.warning(
                    self,
                    "No config file",
                    "Please select a config file in the Config editor tab before starting the server.",
                )
                return
            self._mgr.start(
                path,
                debug=self.debug_chk.isChecked(),
                sim=self.sim_chk.isChecked(),
                host=self._selected_host(),
            )

    def _selected_host(self) -> str:
        return _ACCESS_OPTIONS[self.access_combo.currentIndex()][1]

    def _is_local_network_access(self) -> bool:
        return self.access_combo.currentIndex() == _LOCAL_NETWORK_INDEX

    def _resolved_docs_url(self) -> str:
        base = self.address_edit.text().rstrip("/")
        try:
            parsed = urlparse(base)
            if self._is_local_network_access() and parsed.hostname in (
                "localhost",
                "127.0.0.1",
                "::1",
            ):
                ip = socket.gethostbyname(socket.gethostname())
                base = base.replace(parsed.hostname, ip, 1)
        except OSError:
            pass
        return base + "/docs"

    def _docs_label(self) -> str:
        url = self._resolved_docs_url()
        display = url.replace("http://", "").replace("https://", "")
        return f"Open API browser — {display}"

    def _update_open_btn(self):
        self.open_btn.setUrl(QUrl(self._resolved_docs_url()))
        self.open_btn.setText(self._docs_label())

    def _on_access_changed(self):
        self._update_access_description()
        self._update_open_btn()

    def _update_access_description(self):
        self.access_description.setText(
            _ACCESS_DESCRIPTIONS[self.access_combo.currentIndex()]
        )

    def _on_started(self):
        self.toggle_btn.setText("Stop")
        self.toggle_btn.setToolTip("Stop the running FlowChem server.")
        self.address_edit.setEnabled(False)
        self.debug_chk.setEnabled(False)
        self.sim_chk.setEnabled(False)
        self.access_combo.setEnabled(False)

    def _on_stopped(self, _exit_code):
        self.toggle_btn.setText("Start")
        self.toggle_btn.setToolTip("Start the FlowChem server.")
        self.address_edit.setEnabled(True)
        self.debug_chk.setEnabled(True)
        self.sim_chk.setEnabled(True)
        self.access_combo.setEnabled(True)
