import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtGui import QPalette
from PyQt5.QtWidgets import QApplication
from qfluentwidgets import Theme, qconfig

from app.main_window import MainWindow
from app.theme import DARK_THEME, LIGHT_THEME, apply_theme, load_theme

_APP = None


class FakeSettings:
    def __init__(self, values=None):
        self.values = dict(values or {})

    def value(self, key, default=None):
        return self.values.get(key, default)

    def setValue(self, key, value):
        self.values[key] = value


def get_app():
    global _APP
    _APP = QApplication.instance() or QApplication(["test", "-platform", "offscreen"])
    _APP.setQuitOnLastWindowClosed(False)
    return _APP


def test_load_theme_defaults_to_light_and_rejects_unknown_values():
    assert load_theme(FakeSettings()) == LIGHT_THEME
    assert load_theme(FakeSettings({"theme": "unexpected"})) == LIGHT_THEME


def test_apply_theme_updates_fluent_and_native_qt_palettes():
    app = get_app()

    apply_theme(app, DARK_THEME)
    assert app.style().objectName().lower() == "fusion"
    assert qconfig.theme == Theme.DARK
    assert app.palette().color(QPalette.Window).name() == "#202020"
    assert app.palette().color(QPalette.Text).name() == "#ffffff"

    apply_theme(app, LIGHT_THEME)
    assert qconfig.theme == Theme.LIGHT
    assert app.palette().color(QPalette.Window).name() == "#f3f3f3"
    assert app.palette().color(QPalette.Text).name() == "#000000"


def test_theme_button_switches_label_palette_and_persists_selection():
    app = get_app()
    settings = FakeSettings()
    apply_theme(app, load_theme(settings))
    window = MainWindow(minimize_to_tray=False, settings=settings)

    assert window.theme_btn.text() == "Dark mode"
    assert window.theme_btn.isEnabled()

    window.theme_btn.click()

    assert settings.values["theme"] == DARK_THEME
    assert window.theme_btn.text() == "Light mode"
    assert qconfig.theme == Theme.DARK
    assert window.config_tab.editor.palette().color(QPalette.Text).name() == "#ffffff"
    window._on_started()
    assert window.theme_btn.isEnabled()

    window.theme_btn.click()

    assert settings.values["theme"] == LIGHT_THEME
    assert window.theme_btn.text() == "Dark mode"
    assert qconfig.theme == Theme.LIGHT


def test_main_window_uses_restored_dark_theme_for_button_label():
    app = get_app()
    settings = FakeSettings({"theme": DARK_THEME})
    apply_theme(app, load_theme(settings))

    window = MainWindow(minimize_to_tray=False, settings=settings)

    assert window.theme_btn.text() == "Light mode"
