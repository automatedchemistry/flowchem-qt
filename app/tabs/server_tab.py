from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import CheckBox, LineEdit, PrimaryPushButton, PushButton


class ServerTab(QWidget):
    def __init__(self, server_manager, config_tab, parent=None):
        super().__init__(parent)
        self._mgr = server_manager
        self._cfg = config_tab

        self.address_edit = LineEdit()
        self.address_edit.setText("http://localhost:8000")
        self.debug_chk = CheckBox("Debug mode")
        self.sim_chk = CheckBox("Simulation mode")
        self.toggle_btn = PrimaryPushButton("Start")
        open_btn = PushButton("Open API browser")

        self.address_edit.setToolTip("Base URL for the running FlowChem server.")
        self.debug_chk.setToolTip("Pass --debug to FlowChem for verbose logging.")
        self.sim_chk.setToolTip("Launch flowchem-sim instead of real device drivers.")
        self.toggle_btn.setToolTip("Start or stop the FlowChem server.")
        open_btn.setToolTip("Open the server API documentation in your browser.")

        form = QFormLayout()
        form.addRow("Server address:", self.address_edit)
        form.addRow("", self.debug_chk)
        form.addRow("", self.sim_chk)

        btn_row = QHBoxLayout()
        btn_row.addWidget(self.toggle_btn)
        btn_row.addWidget(open_btn)
        btn_row.addStretch()

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addLayout(btn_row)
        layout.addStretch()

        self.toggle_btn.clicked.connect(self._toggle)
        open_btn.clicked.connect(self._open_browser)
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
                path, debug=self.debug_chk.isChecked(), sim=self.sim_chk.isChecked()
            )

    def _open_browser(self):
        url = self.address_edit.text().rstrip("/") + "/docs"
        QDesktopServices.openUrl(QUrl(url))

    def _on_started(self):
        self.toggle_btn.setText("Stop")
        self.toggle_btn.setToolTip("Stop the running FlowChem server.")
        self.address_edit.setEnabled(False)
        self.debug_chk.setEnabled(False)
        self.sim_chk.setEnabled(False)

    def _on_stopped(self, _exit_code):
        self.toggle_btn.setText("Start")
        self.toggle_btn.setToolTip("Start the FlowChem server.")
        self.address_edit.setEnabled(True)
        self.debug_chk.setEnabled(True)
        self.sim_chk.setEnabled(True)
