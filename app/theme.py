from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QAbstractScrollArea, QApplication
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
    # Qt 6 does not re-inherit the changed application palette on widgets that
    # own a cached palette, such as QPlainTextEdit/QTextEdit (QAbstractScrollArea).
    # Force those already-created widgets to adopt the new palette on each toggle.
    for widget in app.allWidgets():
        if isinstance(widget, QAbstractScrollArea):
            widget.setPalette(app.palette())
    return theme


def _light_palette() -> QPalette:
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#f3f3f3"))
    palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.black)
    palette.setColor(QPalette.ColorRole.Base, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#f7f7f7"))
    palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.black)
    palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.black)
    palette.setColor(QPalette.ColorRole.Button, QColor("#f3f3f3"))
    palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.black)
    palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
    palette.setColor(QPalette.ColorRole.Link, QColor("#0065d5"))
    palette.setColor(QPalette.ColorRole.Highlight, QColor("#0065d5"))
    palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor("#707070"))
    palette.setColor(
        QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor("#9a9a9a")
    )
    palette.setColor(
        QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor("#9a9a9a")
    )
    palette.setColor(
        QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor("#9a9a9a")
    )
    return palette


def _dark_palette() -> QPalette:
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#202020"))
    palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Base, QColor("#2b2b2b"))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#252525"))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#2b2b2b"))
    palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Button, QColor("#2b2b2b"))
    palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.BrightText, QColor("#ff6b6b"))
    palette.setColor(QPalette.ColorRole.Link, QColor("#69a9ff"))
    palette.setColor(QPalette.ColorRole.Highlight, QColor("#0065d5"))
    palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor("#a0a0a0"))
    palette.setColor(
        QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor("#777777")
    )
    palette.setColor(
        QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor("#777777")
    )
    palette.setColor(
        QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor("#777777")
    )
    return palette
