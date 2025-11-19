"""
Qt Compatibility Shim for PyQt5 and PySide6

This module provides a compatibility layer between PyQt5 (Qt5) and PySide6 (Qt6),
similar to Python's 'six' module. It automatically detects and imports the
appropriate Qt binding and provides a unified API.

Inspired by Python's six module (https://github.com/benjaminp/six).

Usage:
    from qt_shim import Qt, QApplication, QWidget, QT5, QT6, QT_VERSION, QT_BINDING

    # Use Qt enums and classes normally
    widget = QWidget()
    widget.setWindowTitle("Test")

    # Check version using boolean constants (similar to six.PY2, six.PY3)
    if QT6:
        # Qt6-specific code
        pass

    # Or check version number
    if QT_VERSION == 6:
        # Qt6-specific code
        pass

    # Or check binding name
    if QT_BINDING == "PySide6":
        # PySide6-specific code
        pass
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    # Type stubs for Qt classes - these are only used for type checking
    # The actual imports happen at runtime below
    pass


# Version detection constants (similar to six.PY2, six.PY3)
# Initialize with defaults, will be reassigned based on available Qt binding
QT5: bool = False
QT6: bool = False
QT_VERSION: Literal[5, 6] = 5  # type: ignore[assignment]
QT_BINDING: Literal["PyQt5", "PySide6"] = "PyQt5"  # type: ignore[assignment]

# Try PySide6 first (IDA 9.2+, Qt6)
try:
    from PySide6.QtCore import Qt, QEvent, QTimer, QCoreApplication
    from PySide6.QtGui import (
        QCursor,
        QFont,
        QKeyEvent,
        QKeySequence,
        QPalette,
        QPixmap,
        QColor,
        QIcon,
        QTextCursor,
        QShortcut,
    )
    from PySide6.QtWidgets import (
        QApplication,
        QCheckBox,
        QComboBox,
        QDialog,
        QFileDialog,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QMainWindow,
        QMenu,
        QMessageBox,
        QPushButton,
        QSplitter,
        QStatusBar,
        QStyleFactory,
        QTabWidget,
        QTextEdit,
        QTreeWidget,
        QTreeWidgetItem,
        QVBoxLayout,
        QWidget,
        QSizePolicy,
        QHeaderView,
    )

    QT_VERSION = 6  # type: ignore[assignment]
    QT_BINDING = "PySide6"  # type: ignore[assignment]
    QT5 = False
    QT6 = True
    _QT_MODULE = "PySide6"
except ImportError:
    # Fall back to PyQt5 (IDA 9.1, Qt5)
    try:
        from PyQt5.QtCore import Qt, QEvent, QTimer, QCoreApplication
        from PyQt5.QtGui import (
            QCursor,
            QFont,
            QKeyEvent,
            QKeySequence,
            QPalette,
            QPixmap,
            QColor,
            QIcon,
            QTextCursor,
            QShortcut,
        )
        from PyQt5.QtWidgets import (
            QApplication,
            QCheckBox,
            QComboBox,
            QDialog,
            QFileDialog,
            QHBoxLayout,
            QLabel,
            QLineEdit,
            QMainWindow,
            QMenu,
            QMessageBox,
            QPushButton,
            QSplitter,
            QStatusBar,
            QStyleFactory,
            QTabWidget,
            QTextEdit,
            QTreeWidget,
            QTreeWidgetItem,
            QVBoxLayout,
            QWidget,
            QSizePolicy,
            QHeaderView,
        )

        QT_VERSION = 5  # type: ignore[assignment]
        QT_BINDING = "PyQt5"  # type: ignore[assignment]
        QT5 = True
        QT6 = False
        _QT_MODULE = "PyQt5"
    except ImportError:
        raise ImportError(
            "Neither PySide6 nor PyQt5 could be imported. "
            "Please ensure one of them is installed."
        ) from None


def _setup_compatibility() -> None:
    """
    Set up compatibility shims for API differences between PyQt5 and PySide6.

    This function handles:
    - exec_() vs exec() method naming differences
    - Keyboard modifier enum access patterns
    """
    if QT_VERSION == 6:
        # PySide6 uses exec() instead of exec_()
        # Create exec_ alias for backward compatibility
        if not hasattr(QMessageBox, "exec_"):
            QMessageBox.exec_ = QMessageBox.exec  # type: ignore[method-assign]
        if not hasattr(QMenu, "exec_"):
            QMenu.exec_ = QMenu.exec  # type: ignore[method-assign]

        # Ensure keyboard modifier shortcuts work (Qt.CTRL, Qt.ALT, etc.)
        # PySide6 may use different enum access patterns
        if not hasattr(Qt, "CTRL"):
            if hasattr(Qt, "KeyboardModifier"):
                Qt.CTRL = Qt.KeyboardModifier.ControlModifier  # type: ignore[attr-defined]
            elif hasattr(Qt, "ControlModifier"):
                Qt.CTRL = Qt.ControlModifier  # type: ignore[attr-defined]
        if not hasattr(Qt, "ALT"):
            if hasattr(Qt, "KeyboardModifier"):
                Qt.ALT = Qt.KeyboardModifier.AltModifier  # type: ignore[attr-defined]
            elif hasattr(Qt, "AltModifier"):
                Qt.ALT = Qt.AltModifier  # type: ignore[attr-defined]
        if not hasattr(Qt, "SHIFT"):
            if hasattr(Qt, "KeyboardModifier"):
                Qt.SHIFT = Qt.KeyboardModifier.ShiftModifier  # type: ignore[attr-defined]
            elif hasattr(Qt, "ShiftModifier"):
                Qt.SHIFT = Qt.ShiftModifier  # type: ignore[attr-defined]


def set_high_dpi_attributes() -> None:
    """
    Set High DPI scaling attributes appropriate for the Qt version.

    In Qt5, we need to explicitly enable High DPI scaling.
    In Qt6, High DPI scaling is enabled by default, but we can set rounding policy.

    This function should be called before creating the QApplication instance
    for best results.
    """
    if QT_VERSION == 5:
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)  # type: ignore[attr-defined]
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)  # type: ignore[attr-defined]
    elif QT_VERSION == 6:
        # Qt6: High DPI scaling is always enabled, but we can set rounding policy
        try:
            # Use QCoreApplication.setHighDpiScaleFactorRoundingPolicy() instead of setAttribute
            if hasattr(QCoreApplication, "setHighDpiScaleFactorRoundingPolicy"):
                QCoreApplication.setHighDpiScaleFactorRoundingPolicy(
                    Qt.HighDpiScaleFactorRoundingPolicy.PassThrough  # type: ignore[attr-defined]
                )
        except (AttributeError, TypeError):
            # Method or enum might not exist in all Qt6 versions
            pass


# Set up compatibility shims immediately upon import
_setup_compatibility()

# Export all Qt classes and constants for easy importing
__all__ = [
    # Version constants (similar to six.PY2, six.PY3)
    "QT5",
    "QT6",
    "QT_VERSION",
    "QT_BINDING",
    # Qt Core
    "Qt",
    "QEvent",
    "QTimer",
    # Qt Gui
    "QCursor",
    "QFont",
    "QKeyEvent",
    "QKeySequence",
    "QPalette",
    "QPixmap",
    "QColor",
    "QIcon",
    "QTextCursor",
    # Qt Widgets
    "QApplication",
    "QCheckBox",
    "QComboBox",
    "QDialog",
    "QFileDialog",
    "QHBoxLayout",
    "QLabel",
    "QLineEdit",
    "QMainWindow",
    "QMenu",
    "QMessageBox",
    "QPushButton",
    "QShortcut",
    "QSplitter",
    "QStatusBar",
    "QStyleFactory",
    "QTabWidget",
    "QTextEdit",
    "QTreeWidget",
    "QTreeWidgetItem",
    "QVBoxLayout",
    "QWidget",
    "QSizePolicy",
    "QHeaderView",
    # Utility functions
    "set_high_dpi_attributes",
]
