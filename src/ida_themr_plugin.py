import os
import pathlib

import ida_kernwin
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
    """Read the previously selected style from the config file."""
    try:
        return QTAPP_STYLE_CFG.read_text().strip()
    except Exception:
        return None


def save_style(style: str):
    """Save the chosen style to the config file."""
    USER_CFGDIR.mkdir(parents=True, exist_ok=True)
    QTAPP_STYLE_CFG.write_text(style)


class QtStyleDialog(QDialog):
    """Dialog that lets the user pick a Qt style from a dropdown."""

    def __init__(self, parent=None):
        super(QtStyleDialog, self).__init__(parent)
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
        style = load_style()
        if style and style in QStyleFactory.keys():
            QApplication.setStyle(style)
            idaapi.msg(f"{PLUGIN_NAME}: Applied style: {style}")
        QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)

        return idaapi.PLUGIN_KEEP

    def run(self, arg):
        # Show style selection dialog
        dialog = QtStyleDialog()
        if dialog.exec_() == QDialog.Accepted:
            style = dialog.selected_style()
            QApplication.setStyle(style)
            save_style(style)

    def term(self):
        pass


def PLUGIN_ENTRY():
    return qtstyle_plugin_t()
