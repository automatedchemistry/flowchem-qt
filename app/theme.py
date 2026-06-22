from PyQt5.QtCore import QSettings, Qt
from PyQt5.QtGui import QColor, QPalette
from PyQt5.QtWidgets import QApplication
from qfluentwidgets import Theme, setTheme

THEME_KEY = "theme"
LIGHT_THEME = "light"
DARK_THEME = "dark"


def load_theme(settings: QSettings) -> str:
    """Return the saved theme, falling back to light mode."""
    value = str(settings.value(THEME_KEY, LIGHT_THEME)).lower()
    return DARK_THEME if value == DARK_THEME else LIGHT_THEME


def apply_theme(app: QApplication, theme: str) -> str:
    """Apply a matching Fluent and native Qt theme."""
    theme = DARK_THEME if theme == DARK_THEME else LIGHT_THEME
    # The native Windows Vista style ignores parts of custom dark palettes,
    # leaving tab pages white while Fluent controls use white text. Fusion
    # consistently honors the application palette in both modes. Changing the
    # Qt style after widgets exist is unsafe, so only select it during startup.
    if not app.topLevelWidgets():
        app.setStyle("Fusion")
    setTheme(Theme.DARK if theme == DARK_THEME else Theme.LIGHT)
    app.setPalette(_dark_palette() if theme == DARK_THEME else _light_palette())
    return theme


def _light_palette() -> QPalette:
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor("#f3f3f3"))
    palette.setColor(QPalette.WindowText, Qt.black)
    palette.setColor(QPalette.Base, Qt.white)
    palette.setColor(QPalette.AlternateBase, QColor("#f7f7f7"))
    palette.setColor(QPalette.ToolTipBase, Qt.white)
    palette.setColor(QPalette.ToolTipText, Qt.black)
    palette.setColor(QPalette.Text, Qt.black)
    palette.setColor(QPalette.Button, QColor("#f3f3f3"))
    palette.setColor(QPalette.ButtonText, Qt.black)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor("#0065d5"))
    palette.setColor(QPalette.Highlight, QColor("#0065d5"))
    palette.setColor(QPalette.HighlightedText, Qt.white)
    palette.setColor(QPalette.PlaceholderText, QColor("#707070"))
    palette.setColor(QPalette.Disabled, QPalette.Text, QColor("#9a9a9a"))
    palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor("#9a9a9a"))
    palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor("#9a9a9a"))
    return palette


def _dark_palette() -> QPalette:
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor("#202020"))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor("#2b2b2b"))
    palette.setColor(QPalette.AlternateBase, QColor("#252525"))
    palette.setColor(QPalette.ToolTipBase, QColor("#2b2b2b"))
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor("#2b2b2b"))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, QColor("#ff6b6b"))
    palette.setColor(QPalette.Link, QColor("#69a9ff"))
    palette.setColor(QPalette.Highlight, QColor("#0065d5"))
    palette.setColor(QPalette.HighlightedText, Qt.white)
    palette.setColor(QPalette.PlaceholderText, QColor("#a0a0a0"))
    palette.setColor(QPalette.Disabled, QPalette.Text, QColor("#777777"))
    palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor("#777777"))
    palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor("#777777"))
    return palette
