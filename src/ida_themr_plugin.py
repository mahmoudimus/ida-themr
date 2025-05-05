import configparser
import pathlib

import idaapi
from PyQt5 import QtCore
from PyQt5.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QHBoxLayout,
    QPushButton,
    QStyleFactory,
    QVBoxLayout,
)

PLUGIN_NAME = "QtStyleSelector"
# Configuration paths
USER_IDADIR = pathlib.Path(idaapi.get_user_idadir())
USER_CFGDIR = USER_IDADIR / "cfg"
QTAPP_STYLE_CFG = USER_CFGDIR / "qtappstyle.cfg"


def load_style():
    """Read the previously selected style and dark mode setting from the config file."""
    config = configparser.ConfigParser()
    try:
        config.read(QTAPP_STYLE_CFG)
    except Exception:
        pass

    style = config.get("default", "qt_style", fallback="Fusion")
    dark_mode = config.getboolean("default", "dark_mode", fallback=False)
    return style, dark_mode


def save_style(style: str, dark_mode: bool = False):
    """Save the chosen style and dark mode setting to the config file."""
    config = configparser.ConfigParser()
    config["default"] = {
        "qt_style": style,
        "dark_mode": str(dark_mode).lower(),
    }
    USER_CFGDIR.mkdir(parents=True, exist_ok=True)
    with open(QTAPP_STYLE_CFG, "w") as configfile:
        config.write(configfile)


def toggle_dark_theme(on: bool, property_name: str = "os-dark-theme"):
    """Toggle the OS theme for the IDA GUI.

    >>> toggle_dark_theme(True)  # force dark-theme rules on
    >>> toggle_dark_theme(False)  # back to light
    """
    app = QApplication.instance()
    # 1) flip the dynamic property on every widget
    for w in app.allWidgets():
        # if you only want to set it on widgets that actually declare it in your QSS
        # you can check w.metaObject().className() against a whitelist.
        w.setProperty(property_name, on)
        w.style().unpolish(w)
        w.style().polish(w)
        w.update()
    # 2) re-apply the stylesheet so Qt re-polishes everything
    # expanded_stylesheet = app.styleSheet()
    # print(expanded_stylesheet)
    # app.setStyleSheet("")    # clear
    # app.setStyleSheet(sheet) # re-set


class IdaThemrSettingsDialog(QDialog):
    """Dialog that lets the user pick IDA themr settings."""

    def __init__(self, parent=None):
        super(IdaThemrSettingsDialog, self).__init__(parent)
        self.setWindowTitle("Select Qt Style")

        # Layout
        layout = QVBoxLayout(self)

        # Combo box of styles
        self.combo = QComboBox(self)
        styles = QStyleFactory.keys()
        self.combo.addItems(styles)

        # Set current to saved style or default
        current = QApplication.style().objectName()
        if current in styles:
            self.combo.setCurrentText(current)
        elif "Fusion" in styles:
            self.combo.setCurrentText("Fusion")

        layout.addWidget(self.combo)

        # OK / Cancel buttons
        btn_layout = QHBoxLayout()
        ok = QPushButton("OK", self)
        cancel = QPushButton("Cancel", self)
        ok.clicked.connect(self.accept)
        cancel.clicked.connect(self.reject)
        btn_layout.addWidget(ok)
        btn_layout.addWidget(cancel)
        layout.addLayout(btn_layout)

    def selected_style(self) -> str:
        return self.combo.currentText()


class qtstyle_plugin_t(idaapi.plugin_t):
    flags = idaapi.PLUGIN_FIX
    comment = "Qt Style Selector Plugin"
    help = "Select and apply Qt style for IDA GUI"
    wanted_name = "QtStyleSelector"
    wanted_hotkey = ""

    def init(self):
        # Apply previously saved style on startup
        style, dark_mode = load_style()
        if style and style in QStyleFactory.keys():
            QApplication.setStyle(style)
            idaapi.msg(f"{PLUGIN_NAME}: Applied style: {style}")
        toggle_dark_theme(dark_mode)  # Apply dark mode setting
        QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)

        return idaapi.PLUGIN_KEEP

    def run(self, arg):
        # Show style selection dialog
        dialog = IdaThemrSettingsDialog()
        if dialog.exec_() == QDialog.Accepted:
            style = dialog.selected_style()
            QApplication.setStyle(style)
            save_style(style)

    def term(self):
        pass


def PLUGIN_ENTRY():
    return qtstyle_plugin_t()
