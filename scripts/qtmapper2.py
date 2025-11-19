import re
from collections import defaultdict

import tinycss2

# --- Existing Regexes and Qt Info (from user) ---
_HEX_RE = re.compile(r"^#(?:[0-9a-f]{3}){1,2}$", re.I)
_RGBA_RE = re.compile(
    r"^rgba?\(\s*"
    r"(\d{1,3})\s*,\s*"
    r"(\d{1,3})\s*,\s*"
    r"(\d{1,3})"
    r"(?:\s*,\s*([0-9]*\.?[0-9]+))?"
    r"\s*\)$",
    re.I,
)

QT_STYLEABLE_WIDGETS = [
    "QAbstractScrollArea",
    "QCheckBox",
    "QColumnView",
    "QComboBox",
    "QDateEdit",
    "QDateTimeEdit",
    "QDialog",
    "QDialogButtonBox",
    "QDockWidget",
    "QDoubleSpinBox",
    "QFrame",
    "QGroupBox",
    "QHeaderView",
    "QLabel",
    "QLineEdit",
    "QListView",
    "QListWidget",
    "QMainWindow",
    "QMenu",
    "QMenuBar",
    "QMessageBox",
    "QProgressBar",
    "QPushButton",
    "QRadioButton",
    "QScrollBar",
    "QSizeGrip",
    "QSlider",
    "QSpinBox",
    "QSplitter",
    "QStatusBar",
    "QTabBar",
    "QTabWidget",
    "QTableView",
    "QTableWidget",
    "QTextEdit",
    "QTimeEdit",
    "QToolBar",
    "QToolButton",
    "QToolBox",
    "QToolTip",
    "QTreeView",
    "QTreeWidget",
    "QWidget",
]

QT_STYLE_PROPERTIES = {
    "Background Properties": [
        "alternate-background-color",
        "background",
        "background-color",
        "background-image",
        "background-repeat",
        "background-position",
        "background-attachment",
        "background-clip",
        "background-origin",
    ],
    "Border Properties": [
        "border",
        "border-top",
        "border-right",
        "border-bottom",
        "border-left",
        "border-color",
        "border-top-color",
        "border-right-color",
        "border-bottom-color",
        "border-left-color",
        "border-image",
        "border-radius",
        "border-top-left-radius",
        "border-top-right-radius",
        "border-bottom-right-radius",
        "border-bottom-left-radius",
        "border-style",
        "border-top-style",
        "border-right-style",
        "border-bottom-style",
        "border-left-style",
        "border-width",
        "border-top-width",
        "border-right-width",
        "border-bottom-width",
        "border-left-width",
    ],
    "Text & Color Properties": [
        "color",
        "font",
        "font-family",
        "font-size",
        "font-style",
        "font-weight",
        "text-align",
        "text-decoration",
        "selection-color",
        "selection-background-color",
    ],
    "Size Properties": [
        "width",
        "height",
        "min-width",
        "min-height",
        "max-width",
        "max-height",
    ],
    "Layout & Spacing Properties": [
        "margin",
        "margin-top",
        "margin-right",
        "margin-bottom",
        "margin-left",
        "padding",
        "padding-top",
        "padding-right",
        "padding-bottom",
        "padding-left",
        "spacing",
    ],
    "Positioning Properties": [
        "position",
        "top",
        "right",
        "bottom",
        "left",
        "subcontrol-origin",
        "subcontrol-position",
    ],
    "Outline Properties": [
        "outline",
        "outline-color",
        "outline-offset",
        "outline-style",
        "outline-radius",
        "outline-bottom-left-radius",
        "outline-bottom-right-radius",
        "outline-top-left-radius",
        "outline-top-right-radius",
    ],
    "Widget-Specific Properties": [
        "button-layout",
        "dialogbuttonbox-buttons-have-icons",
        "gridline-color",
        "icon",
        "icon-size",
        "image",
        "image-position",
        "lineedit-password-character",
        "lineedit-password-mask-delay",
        "messagebox-text-interaction-flags",
        "opacity",
        "paint-alternating-row-colors-for-empty-area",
        "show-decoration-selected",
        "titlebar-show-tooltips-on-buttons",
        "widget-animation-duration",
    ],
    "Qt-Specific Properties": ["-qt-background-role", "-qt-style-features"],
}

QT_PSEUDO_STATES = {
    "State-Related": [
        ":active",
        ":disabled",
        ":enabled",
        ":focus",
        ":hover",
        ":pressed",
        ":checked",
        ":unchecked",
        ":indeterminate",
        ":open",
        ":closed",
        ":on",
        ":off",
        ":selected",
        ":edit-focus",
        ":read-only",
    ],
    "Position-Related": [
        ":horizontal",
        ":vertical",
        ":left",
        ":right",
        ":top",
        ":bottom",
        ":first",
        ":last",
        ":middle",
        ":only-one",
        ":next-selected",
        ":previous-selected",
    ],
    "Widget-Specific": [
        ":adjoins-item",
        ":alternate",
        ":closable",
        ":default",
        ":editable",
        ":exclusive",
        ":flat",
        ":floatable",
        ":has-children",
        ":has-siblings",
        ":maximized",
        ":minimized",
        ":movable",
        ":no-frame",
        ":non-exclusive",
        ":window",
    ],
}

QT_SUB_CONTROLS = {
    "Navigation Controls": [
        "::add-line",
        "::add-page",
        "::sub-line",
        "::sub-page",
        "::up-arrow",
        "::down-arrow",
        "::left-arrow",
        "::right-arrow",
        "::up-button",
        "::down-button",
    ],
    "Widget Components": [
        "::handle",
        "::groove",
        "::indicator",
        "::chunk",
        "::menu-arrow",
        "::menu-button",
        "::menu-indicator",
        "::drop-down",
    ],
    "Container Elements": [
        "::branch",
        "::item",
        "::tab",
        "::tab-bar",
        "::pane",
        "::section",
        "::separator",
        "::scroller",
    ],
    "Special Elements": [
        "::close-button",
        "::float-button",
        "::tear",
        "::tearoff",
        "::text",
        "::title",
        "::corner",
        "::left-corner",
        "::right-corner",
        "::icon",
    ],
}

CSS_CLASS_TO_QT_MAPPING = {
    "open": {"qt_pseudo_state": ":open"},
    "active": {"qt_pseudo_state": ":active"},
    "selected": {"qt_pseudo_state": ":selected"},
    "disabled": {"qt_pseudo_state": ":disabled"},
    "checked": {"qt_pseudo_state": ":checked"},
    "horizontal": {"qt_pseudo_state": ":horizontal"},
    "vertical": {"qt_pseudo_state": ":vertical"},
    "menubar-menu-button": {"qt_widget": "QMenuBar"},
    "menubar-menu-title": {
        "qt_sub_control": "::item",
        "context_parent_class": "menubar-menu-button",
    },
    "menu-item": {"qt_widget": "QMenu", "qt_sub_control": "::item"},
    "slider-thumb": {"qt_widget": "QSlider", "qt_sub_control": "::handle"},
    "scrollbar-button-up": {"qt_widget": "QScrollBar", "qt_sub_control": "::up-arrow"},
    "tab-label": {"qt_widget": "QTabBar", "qt_sub_control": "::tab"},
    "groupbox-title-text": {"qt_widget": "QGroupBox", "qt_sub_control": "::title"},
    "input-field": {"qt_widget": "QLineEdit"},
    "button": {"qt_widget": "QPushButton"},
    "checkbox-indicator": {"qt_widget": "QCheckBox", "qt_sub_control": "::indicator"},
    "progressbar-chunk": {"qt_widget": "QProgressBar", "qt_sub_control": "::chunk"},
}

CSS_PSEUDO_CLASS_TO_QT_PSEUDO_STATE = {
    "hover": ":hover",
    "focus": ":focus",
    "active": ":pressed",
    "disabled": ":disabled",
    "enabled": ":enabled",
    "checked": ":checked",
    "indeterminate": ":indeterminate",
    "open": ":open",
    "first-child": ":first",
    "last-child": ":last",
}

CSS_PROPERTY_TO_QSS_PROPERTY = {
    "alternate-background-color": "alternate-background-color",
    "background": "background",
    "background-color": "background-color",
    "background-image": "background-image",
    "background-repeat": "background-repeat",
    "background-position": "background-position",
    "border": "border",
    "border-top": "border-top",
    "border-right": "border-right",
    "border-bottom": "border-bottom",
    "border-left": "border-left",
    "border-color": "border-color",
    "border-top-color": "border-top-color",
    "border-right-color": "border-right-color",
    "border-bottom-color": "border-bottom-color",
    "border-left-color": "border-left-color",
    "border-radius": "border-radius",
    "border-top-left-radius": "border-top-left-radius",
    "border-top-right-radius": "border-top-right-radius",
    "border-bottom-left-radius": "border-bottom-left-radius",
    "border-bottom-right-radius": "border-bottom-right-radius",
    "border-style": "border-style",
    "border-top-style": "border-top-style",
    "border-right-style": "border-right-style",
    "border-bottom-style": "border-bottom-style",
    "border-left-style": "border-left-style",
    "border-width": "border-width",
    "border-top-width": "border-top-width",
    "border-right-width": "border-right-width",
    "border-bottom-width": "border-bottom-width",
    "border-left-width": "border-left-width",
    "color": "color",
    "font": "font",
    "font-family": "font-family",
    "font-size": "font-size",
    "font-style": "font-style",
    "font-weight": "font-weight",
    "text-align": "text-align",
    "text-decoration": "text-decoration",
    "selection-color": "selection-color",
    "selection-background-color": "selection-background-color",
    "width": "width",
    "height": "height",
    "min-width": "min-width",
    "min-height": "min-height",
    "max-width": "max-width",
    "max-height": "max-height",
    "margin": "margin",
    "margin-top": "margin-top",
    "margin-right": "margin-right",
    "margin-bottom": "margin-bottom",
    "margin-left": "margin-left",
    "padding": "padding",
    "padding-top": "padding-top",
    "padding-right": "padding-right",
    "padding-bottom": "padding-bottom",
    "padding-left": "padding-left",
    "outline": "outline",
    "outline-color": "outline-color",
    "outline-offset": "outline-offset",
    "outline-style": "outline-style",
    "outline-radius": "outline-radius",
    "outline-top-left-radius": "outline-top-left-radius",
    "outline-top-right-radius": "outline-top-right-radius",
    "outline-bottom-left-radius": "outline-bottom-left-radius",
    "outline-bottom-right-radius": "outline-bottom-right-radius",
    "opacity": "opacity",
    "position": None,
    "top": None,
    "right": None,
    "bottom": None,
    "left": None,
    "box-shadow": None,
    "text-shadow": None,
    "display": None,
    "float": None,
    "clear": None,
    "z-index": None,
    "cursor": None,
    "list-style": None,
    "list-style-type": None,
    "list-style-image": None,
    "list-style-position": None,
    "visibility": None,
    "overflow": None,
    "clip": None,
    "content": None,
    "quotes": None,
    "counter-reset": None,
    "counter-increment": None,
    "table-layout": None,
    "caption-side": None,
    "empty-cells": None,
    "page-break-after": None,
    "page-break-before": None,
    "page-break-inside": None,
    "orphans": None,
    "widows": None,
    "transform": None,
    "transform-origin": None,
    "transform-style": None,
    "perspective": None,
    "perspective-origin": None,
    "backface-visibility": None,
    "transition": None,
    "transition-property": None,
    "transition-duration": None,
    "transition-timing-function": None,
    "transition-delay": None,
    "animation": None,
    "animation-name": None,
    "animation-duration": None,
    "animation-timing-function": None,
    "animation-delay": None,
    "animation-iteration-count": None,
    "animation-direction": None,
    "animation-fill-mode": None,
    "animation-play-state": None,
    "flex": None,
    "flex-basis": None,
    "flex-direction": None,
    "flex-flow": None,
    "flex-grow": None,
    "flex-shrink": None,
    "flex-wrap": None,
    "align-content": None,
    "align-items": None,
    "align-self": None,
    "justify-content": None,
    "order": None,
    "grid": None,
    "grid-area": None,
    "grid-auto-columns": None,
    "grid-auto-flow": None,
    "grid-auto-rows": None,
    "grid-column": None,
    "grid-column-end": None,
    "grid-column-gap": None,
    "grid-column-start": None,
    "grid-gap": None,
    "grid-row": None,
    "grid-row-end": None,
    "grid-row-gap": None,
    "grid-row-start": None,
    "grid-template": None,
    "grid-template-areas": None,
    "grid-template-columns": None,
    "grid-template-rows": None,
}

# --- VSCode Variable to Qt Style Mapping ---
VSCODE_VAR_TO_QT_STYLE_MAP = [
    # General Foreground/Background/Borders
    {
        "vscode_var_pattern": r"--vscode-foreground$",
        "styles": [
            {"qt_target": "QWidget", "qss_property": "color"},
            {"qt_target": "QLabel", "qss_property": "color"},
            {"qt_target": "QToolTip", "qss_property": "color"},
            {"qt_target": "QGroupBox", "qss_property": "color"},
            {"qt_target": "QRadioButton", "qss_property": "color"},
            {"qt_target": "QCheckBox", "qss_property": "color"},
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-disabledForeground$",
        "styles": [
            {"qt_target": "QWidget", "states": [":disabled"], "qss_property": "color"},
            {"qt_target": "QLabel", "states": [":disabled"], "qss_property": "color"},
            {
                "qt_target": "QPushButton",
                "states": [":disabled"],
                "qss_property": "color",
            },
            {
                "qt_target": "QLineEdit",
                "states": [":disabled"],
                "qss_property": "color",
            },
            {
                "qt_target": "QCheckBox",
                "states": [":disabled"],
                "qss_property": "color",
            },
            {
                "qt_target": "QRadioButton",
                "states": [":disabled"],
                "qss_property": "color",
            },
            {
                "qt_target": "QComboBox",
                "states": [":disabled"],
                "qss_property": "color",
            },
            {"qt_target": "QSpinBox", "states": [":disabled"], "qss_property": "color"},
            {
                "qt_target": "QDoubleSpinBox",
                "states": [":disabled"],
                "qss_property": "color",
            },
            {
                "qt_target": "QTextEdit",
                "states": [":disabled", ":read-only"],
                "qss_property": "color",
            },
            {
                "qt_target": "QPlainTextEdit",
                "states": [":disabled", ":read-only"],
                "qss_property": "color",
            },
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-errorForeground$",
        "styles": [
            {"qt_target": 'QLabel[errorState="true"]', "qss_property": "color"},
            {"qt_target": 'QLineEdit[errorState="true"]', "qss_property": "color"},
        ],
        "note": "Error foreground is context-dependent. Applied to specific widgets with assumed 'errorState' property.",
    },
    {
        "vscode_var_pattern": r"--vscode-focusBorder$",
        "styles": [
            {
                "qt_target": "QPushButton",
                "states": [":focus"],
                "qss_property": "border",
                "value_prefix": "1px solid ",
            },
            {
                "qt_target": "QLineEdit",
                "states": [":focus"],
                "qss_property": "border",
                "value_prefix": "1px solid ",
            },
            {
                "qt_target": "QComboBox",
                "states": [":focus"],
                "qss_property": "border",
                "value_prefix": "1px solid ",
            },
            {
                "qt_target": "QSpinBox",
                "states": [":focus"],
                "qss_property": "border",
                "value_prefix": "1px solid ",
            },
            {
                "qt_target": "QDoubleSpinBox",
                "states": [":focus"],
                "qss_property": "border",
                "value_prefix": "1px solid ",
            },
            {
                "qt_target": "QDateEdit",
                "states": [":focus"],
                "qss_property": "border",
                "value_prefix": "1px solid ",
            },
            {
                "qt_target": "QTimeEdit",
                "states": [":focus"],
                "qss_property": "border",
                "value_prefix": "1px solid ",
            },
            {
                "qt_target": "QDateTimeEdit",
                "states": [":focus"],
                "qss_property": "border",
                "value_prefix": "1px solid ",
            },
            {
                "qt_target": "QSlider",
                "states": [":focus"],
                "qss_property": "border",
                "value_prefix": "1px solid ",
            },
            {
                "qt_target": "QTextEdit",
                "states": [":focus"],
                "qss_property": "border",
                "value_prefix": "1px solid ",
            },
            {
                "qt_target": "QPlainTextEdit",
                "states": [":focus"],
                "qss_property": "border",
                "value_prefix": "1px solid ",
            },
            {
                "qt_target": "QListView",
                "states": [":focus"],
                "qss_property": "outline",
                "value_prefix": "1px solid ",
            },
            {
                "qt_target": "QTreeView",
                "states": [":focus"],
                "qss_property": "outline",
                "value_prefix": "1px solid ",
            },
            {
                "qt_target": "QTableView",
                "states": [":focus"],
                "qss_property": "outline",
                "value_prefix": "1px solid ",
            },
            {
                "qt_target": "QTabBar::tab",
                "states": [":focus"],
                "qss_property": "outline",
                "value_prefix": "1px solid ",
            },
        ],
        "note": "Focus border applied as 1px solid border or outline. Adjust thickness/style as needed.",
    },
    {
        "vscode_var_pattern": r"--vscode-contrastBorder$",
        "styles": [
            {
                "qt_target": 'QFrame[frameShape="HLine"]',
                "qss_property": "border",
                "value_prefix": "1px solid ",
            },
            {
                "qt_target": 'QFrame[frameShape="VLine"]',
                "qss_property": "border",
                "value_prefix": "1px solid ",
            },
            {"qt_target": "QSplitter::handle", "qss_property": "background-color"},
        ],
        "note": "Contrast border applied to QFrame lines and QSplitter handles.",
    },
    {
        "vscode_var_pattern": r"--vscode-contrastActiveBorder$",
        "styles": [
            {
                "qt_target": "QPushButton",
                "states": [":focus", ":pressed"],
                "qss_property": "border",
                "value_prefix": "1px solid ",
            },
            {
                "qt_target": "QSplitter::handle",
                "states": [":hover", ":pressed"],
                "qss_property": "background-color",
            },
        ],
    },
    # Text / Editor related
    {
        "vscode_var_pattern": r"--vscode-editor-background$",
        "styles": [
            {"qt_target": "QTextEdit", "qss_property": "background-color"},
            {"qt_target": "QPlainTextEdit", "qss_property": "background-color"},
            {
                "qt_target": "QListView",
                "qss_property": "background-color",
                "skip_if_default_value": True,
            },
            {
                "qt_target": "QTreeView",
                "qss_property": "background-color",
                "skip_if_default_value": True,
            },
            {
                "qt_target": "QTableView",
                "qss_property": "background-color",
                "skip_if_default_value": True,
            },
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-editor-foreground$",
        "styles": [
            {"qt_target": "QTextEdit", "qss_property": "color"},
            {"qt_target": "QPlainTextEdit", "qss_property": "color"},
            {"qt_target": "QListView", "qss_property": "color"},
            {"qt_target": "QTreeView", "qss_property": "color"},
            {"qt_target": "QTableView", "qss_property": "color"},
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-editor-selectionBackground$",
        "styles": [
            {"qt_target": "QTextEdit", "qss_property": "selection-background-color"},
            {
                "qt_target": "QPlainTextEdit",
                "qss_property": "selection-background-color",
            },
            {"qt_target": "QLineEdit", "qss_property": "selection-background-color"},
            {
                "qt_target": "QListView::item",
                "states": [":selected"],
                "qss_property": "background-color",
            },
            {
                "qt_target": "QTreeView::item",
                "states": [":selected"],
                "qss_property": "background-color",
            },
            {
                "qt_target": "QTableView::item",
                "states": [":selected"],
                "qss_property": "background-color",
            },
            {
                "qt_target": "QComboBox QAbstractItemView::item",
                "states": [":selected"],
                "qss_property": "background-color",
            },
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-editor-selectionForeground$",
        "styles": [
            {"qt_target": "QTextEdit", "qss_property": "selection-color"},
            {"qt_target": "QPlainTextEdit", "qss_property": "selection-color"},
            {"qt_target": "QLineEdit", "qss_property": "selection-color"},
            {
                "qt_target": "QListView::item",
                "states": [":selected"],
                "qss_property": "color",
            },
            {
                "qt_target": "QTreeView::item",
                "states": [":selected"],
                "qss_property": "color",
            },
            {
                "qt_target": "QTableView::item",
                "states": [":selected"],
                "qss_property": "color",
            },
            {
                "qt_target": "QComboBox QAbstractItemView::item",
                "states": [":selected"],
                "qss_property": "color",
            },
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-editorWidget-background$",
        "styles": [
            {
                "qt_target": 'QDialog[isEditorWidget="true"]',
                "qss_property": "background-color",
                "skip_if_default_value": True,
            },
            {
                "qt_target": "QMenu",
                "qss_property": "background-color",
                "skip_if_default_value": True,
            },
            {
                "qt_target": "QToolTip",
                "qss_property": "background-color",
                "skip_if_default_value": True,
            },
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-editorWidget-foreground$",
        "styles": [
            {"qt_target": 'QDialog[isEditorWidget="true"]', "qss_property": "color"},
            {"qt_target": "QMenu", "qss_property": "color"},
            {"qt_target": "QToolTip", "qss_property": "color"},
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-editorWidget-border$",
        "styles": [
            {
                "qt_target": 'QDialog[isEditorWidget="true"]',
                "qss_property": "border",
                "value_prefix": "1px solid ",
            },
            {
                "qt_target": "QMenu",
                "qss_property": "border",
                "value_prefix": "1px solid ",
            },
            {
                "qt_target": "QToolTip",
                "qss_property": "border",
                "value_prefix": "1px solid ",
            },
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-editorLineNumber-foreground$",
        "styles": [],
        "note": "Styling QPlainTextEdit line numbers is complex, often not via QSS alone.",
    },
    {
        "vscode_var_pattern": r"--vscode-editorLineNumber-activeForeground$",
        "styles": [],
        "note": "Styling QPlainTextEdit active line number is complex.",
    },
    {
        "vscode_var_pattern": r"--vscode-editorGutter-background$",
        "styles": [],
        "note": "Editor gutter background is part of the editor widget, often not separately styleable via simple QSS for QPlainTextEdit.",
    },
    {
        "vscode_var_pattern": r"--vscode-editor-lineHighlightBorder$",
        "styles": [],
        "note": "Current line highlight in QPlainTextEdit is usually background, border is complex.",
    },
    {
        "vscode_var_pattern": r"--vscode-editorWhitespace-foreground$",
        "styles": [],
        "note": "Whitespace character styling is usually an editor feature, not direct QSS.",
    },
    {
        "vscode_var_pattern": r"--vscode-editorIndentGuide-background$",
        "styles": [],
        "note": "Indent guide styling in text editors is an editor feature, not simple QSS.",
    },
    # Inputs (QLineEdit, QSpinBox, etc.)
    {
        "vscode_var_pattern": r"--vscode-input-background$",
        "styles": [
            {
                "qt_target": "QLineEdit",
                "qss_property": "background-color",
                "skip_if_default_value": True,
            },
            {
                "qt_target": "QSpinBox",
                "qss_property": "background-color",
                "skip_if_default_value": True,
            },
            {
                "qt_target": "QDoubleSpinBox",
                "qss_property": "background-color",
                "skip_if_default_value": True,
            },
            {
                "qt_target": "QComboBox",
                "qss_property": "background-color",
                "skip_if_default_value": True,
            },
            {
                "qt_target": "QDateEdit",
                "qss_property": "background-color",
                "skip_if_default_value": True,
            },
            {
                "qt_target": "QTimeEdit",
                "qss_property": "background-color",
                "skip_if_default_value": True,
            },
            {
                "qt_target": "QDateTimeEdit",
                "qss_property": "background-color",
                "skip_if_default_value": True,
            },
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-input-foreground$",
        "styles": [
            {"qt_target": "QLineEdit", "qss_property": "color"},
            {"qt_target": "QSpinBox", "qss_property": "color"},
            {"qt_target": "QDoubleSpinBox", "qss_property": "color"},
            {"qt_target": "QComboBox", "qss_property": "color"},
            {"qt_target": "QDateEdit", "qss_property": "color"},
            {"qt_target": "QTimeEdit", "qss_property": "color"},
            {"qt_target": "QDateTimeEdit", "qss_property": "color"},
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-input-border$",
        "styles": [
            {
                "qt_target": "QLineEdit",
                "qss_property": "border",
                "value_prefix": "1px solid ",
            },
            {
                "qt_target": "QSpinBox",
                "qss_property": "border",
                "value_prefix": "1px solid ",
            },
            {
                "qt_target": "QDoubleSpinBox",
                "qss_property": "border",
                "value_prefix": "1px solid ",
            },
            {
                "qt_target": "QComboBox",
                "qss_property": "border",
                "value_prefix": "1px solid ",
            },
            {
                "qt_target": "QDateEdit",
                "qss_property": "border",
                "value_prefix": "1px solid ",
            },
            {
                "qt_target": "QTimeEdit",
                "qss_property": "border",
                "value_prefix": "1px solid ",
            },
            {
                "qt_target": "QDateTimeEdit",
                "qss_property": "border",
                "value_prefix": "1px solid ",
            },
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-input-placeholderForeground$",
        "styles": [
            {
                "qt_target": "QLineEdit",
                "qss_property": "placeholder-text-color",
                "value_format_is_direct": True,
            },
        ],
        "note": "QLineEdit placeholder uses 'placeholder-text-color'.",
    },
    {
        "vscode_var_pattern": r"--vscode-inputOption-activeBorder$",
        "styles": [
            {
                "qt_target": "QComboBox QAbstractItemView::item",
                "states": [":selected", ":active"],
                "qss_property": "border",
                "value_prefix": "1px solid ",
            },
            {
                "qt_target": "QMenu::item",
                "states": [":selected"],
                "qss_property": "border",
                "value_prefix": "1px solid ",
            },
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-inputOption-activeBackground$",
        "styles": [
            {
                "qt_target": "QComboBox QAbstractItemView::item",
                "states": [":selected", ":active"],
                "qss_property": "background-color",
                "skip_if_default_value": True,
            },
            {
                "qt_target": "QMenu::item",
                "states": [":selected"],
                "qss_property": "background-color",
                "skip_if_default_value": True,
            },
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-inputOption-activeForeground$",
        "styles": [
            {
                "qt_target": "QComboBox QAbstractItemView::item",
                "states": [":selected", ":active"],
                "qss_property": "color",
            },
            {
                "qt_target": "QMenu::item",
                "states": [":selected"],
                "qss_property": "color",
            },
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-inputValidation-(info|warning|error)Border$",
        "styles": [
            {
                "qt_target": 'QLineEdit[validationState="info"]',
                "qss_property": "border-color",
                "dynamic_var_part_idx": 0,
                "condition_value": "info",
            },
            {
                "qt_target": 'QLineEdit[validationState="warning"]',
                "qss_property": "border-color",
                "dynamic_var_part_idx": 0,
                "condition_value": "warning",
            },
            {
                "qt_target": 'QLineEdit[validationState="error"]',
                "qss_property": "border-color",
                "dynamic_var_part_idx": 0,
                "condition_value": "error",
            },
        ],
        "note": "Input validation styles are highly dependent on custom widget states/properties.",
    },
    {
        "vscode_var_pattern": r"--vscode-inputValidation-(info|warning|error)Background$",
        "styles": [
            {
                "qt_target": 'QLineEdit[validationState="info"]',
                "qss_property": "background-color",
                "dynamic_var_part_idx": 0,
                "condition_value": "info",
                "skip_if_default_value": True,
            },
            {
                "qt_target": 'QLineEdit[validationState="warning"]',
                "qss_property": "background-color",
                "dynamic_var_part_idx": 0,
                "condition_value": "warning",
                "skip_if_default_value": True,
            },
            {
                "qt_target": 'QLineEdit[validationState="error"]',
                "qss_property": "background-color",
                "dynamic_var_part_idx": 0,
                "condition_value": "error",
                "skip_if_default_value": True,
            },
        ],
    },
    # Buttons
    {
        "vscode_var_pattern": r"--vscode-button-background$",
        "styles": [
            {
                "qt_target": "QPushButton",
                "qss_property": "background-color",
                "skip_if_default_value": True,
            }
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-button-foreground$",
        "styles": [{"qt_target": "QPushButton", "qss_property": "color"}],
    },
    {
        "vscode_var_pattern": r"--vscode-button-hoverBackground$",
        "styles": [
            {
                "qt_target": "QPushButton",
                "states": [":hover"],
                "qss_property": "background-color",
                "skip_if_default_value": True,
            }
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-button-border$",
        "styles": [
            {
                "qt_target": "QPushButton",
                "qss_property": "border",
                "value_prefix": "1px solid ",
            }
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-button-secondaryBackground$",
        "styles": [
            {
                "qt_target": 'QPushButton[buttonRole="secondary"]',
                "qss_property": "background-color",
                "skip_if_default_value": True,
            }
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-button-secondaryForeground$",
        "styles": [
            {
                "qt_target": 'QPushButton[buttonRole="secondary"]',
                "qss_property": "color",
            }
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-button-secondaryHoverBackground$",
        "styles": [
            {
                "qt_target": 'QPushButton[buttonRole="secondary"]',
                "states": [":hover"],
                "qss_property": "background-color",
                "skip_if_default_value": True,
            }
        ],
    },
    # Dropdowns / ComboBox
    {
        "vscode_var_pattern": r"--vscode-dropdown-background$",
        "styles": [
            {
                "qt_target": "QComboBox",
                "qss_property": "background-color",
                "skip_if_default_value": True,
            },
            {
                "qt_target": "QComboBox QAbstractItemView",
                "qss_property": "background-color",
                "skip_if_default_value": True,
            },
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-dropdown-listBackground$",
        "styles": [
            {
                "qt_target": "QComboBox QAbstractItemView",
                "qss_property": "background-color",
                "skip_if_default_value": True,
            },
            {
                "qt_target": "QMenu",
                "qss_property": "background-color",
                "skip_if_default_value": True,
            },
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-dropdown-foreground$",
        "styles": [
            {"qt_target": "QComboBox", "qss_property": "color"},
            {"qt_target": "QComboBox QAbstractItemView", "qss_property": "color"},
            {"qt_target": "QMenu", "qss_property": "color"},
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-dropdown-border$",
        "styles": [
            {
                "qt_target": "QComboBox",
                "qss_property": "border",
                "value_prefix": "1px solid ",
            },
            {
                "qt_target": "QComboBox QAbstractItemView",
                "qss_property": "border",
                "value_prefix": "1px solid ",
            },
            {
                "qt_target": "QMenu",
                "qss_property": "border",
                "value_prefix": "1px solid ",
            },
        ],
    },
    # Scrollbars
    {
        "vscode_var_pattern": r"--vscode-scrollbarSlider-background$",
        "styles": [
            {
                "qt_target": "QScrollBar::handle:horizontal",
                "qss_property": "background-color",
                "skip_if_default_value": True,
            },
            {
                "qt_target": "QScrollBar::handle:vertical",
                "qss_property": "background-color",
                "skip_if_default_value": True,
            },
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-scrollbarSlider-hoverBackground$",
        "styles": [
            {
                "qt_target": "QScrollBar::handle:horizontal",
                "states": [":hover"],
                "qss_property": "background-color",
                "skip_if_default_value": True,
            },
            {
                "qt_target": "QScrollBar::handle:vertical",
                "states": [":hover"],
                "qss_property": "background-color",
                "skip_if_default_value": True,
            },
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-scrollbarSlider-activeBackground$",
        "styles": [
            {
                "qt_target": "QScrollBar::handle:horizontal",
                "states": [":pressed"],
                "qss_property": "background-color",
                "skip_if_default_value": True,
            },
            {
                "qt_target": "QScrollBar::handle:vertical",
                "states": [":pressed"],
                "qss_property": "background-color",
                "skip_if_default_value": True,
            },
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-scrollbar-shadow$",
        "styles": [
            {
                "qt_target": "QScrollBar::groove:horizontal",
                "qss_property": "background-color",
                "skip_if_default_value": True,
            },
            {
                "qt_target": "QScrollBar::groove:vertical",
                "qss_property": "background-color",
                "skip_if_default_value": True,
            },
        ],
        "note": "Scrollbar shadow mapped to groove background. QSS has no direct box-shadow.",
    },
    # Menus (QMenu, QMenuBar)
    {
        "vscode_var_pattern": r"--vscode-menu-background$",
        "styles": [
            {
                "qt_target": "QMenu",
                "qss_property": "background-color",
                "skip_if_default_value": True,
            }
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-menu-foreground$",
        "styles": [
            {"qt_target": "QMenu", "qss_property": "color"},
            {"qt_target": "QMenuBar", "qss_property": "color"},
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-menu-selectionBackground$",
        "styles": [
            {
                "qt_target": "QMenu::item",
                "states": [":selected"],
                "qss_property": "background-color",
                "skip_if_default_value": True,
            },
            {
                "qt_target": "QMenuBar::item",
                "states": [":selected", ":pressed"],
                "qss_property": "background-color",
                "skip_if_default_value": True,
            },
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-menu-selectionForeground$",
        "styles": [
            {
                "qt_target": "QMenu::item",
                "states": [":selected"],
                "qss_property": "color",
            },
            {
                "qt_target": "QMenuBar::item",
                "states": [":selected", ":pressed"],
                "qss_property": "color",
            },
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-menu-border$",
        "styles": [
            {
                "qt_target": "QMenu",
                "qss_property": "border",
                "value_prefix": "1px solid ",
            }
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-menu-separatorBackground$",
        "styles": [
            {"qt_target": "QMenu::separator", "qss_property": "background-color"}
        ],
        "note": "Menu separator might need height/margin in QSS for visibility (e.g. height: 1px; margin-left: 5px; margin-right: 5px;).",
    },
    {
        "vscode_var_pattern": r"--vscode-menubar-selectionBorder$",
        "styles": [
            {
                "qt_target": "QMenuBar::item",
                "states": [":selected"],
                "qss_property": "border",
                "value_prefix": "1px solid ",
            },
            {
                "qt_target": "QMenuBar::item",
                "states": [":pressed"],
                "qss_property": "border",
                "value_prefix": "1px solid ",
            },
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-menubar-selectionForeground$",
        "styles": [
            {
                "qt_target": "QMenuBar::item",
                "states": [":selected"],
                "qss_property": "color",
            },
            {
                "qt_target": "QMenuBar::item",
                "states": [":pressed"],
                "qss_property": "color",
            },
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-titleBar-activeBackground$",
        "styles": [
            {
                "qt_target": "QMenuBar",
                "qss_property": "background-color",
                "skip_if_default_value": True,
            }
        ],
    },
    # Lists & Trees (QListView, QTreeView, QTableView)
    {
        "vscode_var_pattern": r"--vscode-list-hoverBackground$",
        "styles": [
            {
                "qt_target": "QListView::item",
                "states": [":hover"],
                "qss_property": "background-color",
                "skip_if_default_value": True,
            },
            {
                "qt_target": "QTreeView::item",
                "states": [":hover"],
                "qss_property": "background-color",
                "skip_if_default_value": True,
            },
            {
                "qt_target": "QTableView::item",
                "states": [":hover"],
                "qss_property": "background-color",
                "skip_if_default_value": True,
            },
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-list-hoverForeground$",
        "styles": [
            {
                "qt_target": "QListView::item",
                "states": [":hover"],
                "qss_property": "color",
            },
            {
                "qt_target": "QTreeView::item",
                "states": [":hover"],
                "qss_property": "color",
            },
            {
                "qt_target": "QTableView::item",
                "states": [":hover"],
                "qss_property": "color",
            },
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-list-activeSelectionBackground$",
        "styles": [
            {
                "qt_target": "QListView::item",
                "states": [":selected", ":active"],
                "qss_property": "background-color",
                "skip_if_default_value": True,
            },
            {
                "qt_target": "QTreeView::item",
                "states": [":selected", ":active"],
                "qss_property": "background-color",
                "skip_if_default_value": True,
            },
            {
                "qt_target": "QTableView::item",
                "states": [":selected", ":active"],
                "qss_property": "background-color",
                "skip_if_default_value": True,
            },
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-list-activeSelectionForeground$",
        "styles": [
            {
                "qt_target": "QListView::item",
                "states": [":selected", ":active"],
                "qss_property": "color",
            },
            {
                "qt_target": "QTreeView::item",
                "states": [":selected", ":active"],
                "qss_property": "color",
            },
            {
                "qt_target": "QTableView::item",
                "states": [":selected", ":active"],
                "qss_property": "color",
            },
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-list-inactiveSelectionBackground$",
        "styles": [
            {
                "qt_target": "QListView::item",
                "states": [":selected", ":!active"],
                "qss_property": "background-color",
                "skip_if_default_value": True,
            },
            {
                "qt_target": "QTreeView::item",
                "states": [":selected", ":!active"],
                "qss_property": "background-color",
                "skip_if_default_value": True,
            },
            {
                "qt_target": "QTableView::item",
                "states": [":selected", ":!active"],
                "qss_property": "background-color",
                "skip_if_default_value": True,
            },
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-list-inactiveSelectionForeground$",
        "styles": [
            {
                "qt_target": "QListView::item",
                "states": [":selected", ":!active"],
                "qss_property": "color",
            },
            {
                "qt_target": "QTreeView::item",
                "states": [":selected", ":!active"],
                "qss_property": "color",
            },
            {
                "qt_target": "QTableView::item",
                "states": [":selected", ":!active"],
                "qss_property": "color",
            },
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-list-focusOutline$",
        "styles": [
            {
                "qt_target": "QListView",
                "states": [":focus"],
                "qss_property": "outline",
                "value_prefix": "1px solid ",
            },
            {
                "qt_target": "QTreeView",
                "states": [":focus"],
                "qss_property": "outline",
                "value_prefix": "1px solid ",
            },
            {
                "qt_target": "QTableView",
                "states": [":focus"],
                "qss_property": "outline",
                "value_prefix": "1px solid ",
            },
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-list-focusAndSelectionOutline$",
        "styles": [
            {
                "qt_target": "QListView::item",
                "states": [":selected", ":focus"],
                "qss_property": "border",
                "value_prefix": "1px solid ",
            },
            {
                "qt_target": "QTreeView::item",
                "states": [":selected", ":focus"],
                "qss_property": "border",
                "value_prefix": "1px solid ",
            },
            {
                "qt_target": "QTableView::item",
                "states": [":selected", ":focus"],
                "qss_property": "border",
                "value_prefix": "1px solid ",
            },
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-tree-indentGuidesStroke$",
        "styles": [{"qt_target": "QTreeView::branch", "qss_property": "border-color"}],
        "note": "Tree indent guides are complex in QSS. This is a simplified mapping. Often uses border-image.",
    },
    {
        "vscode_var_pattern": r"--vscode-editorGroupHeader-tabsBackground$",
        "styles": [
            {
                "qt_target": "QHeaderView::section",
                "qss_property": "background-color",
                "skip_if_default_value": True,
            }
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-editorGroupHeader-tabsBorder$",
        "styles": [
            {
                "qt_target": "QHeaderView::section",
                "qss_property": "border",
                "value_prefix": "1px solid ",
            }
        ],
    },
    # Tabs (QTabBar, QTabWidget)
    {
        "vscode_var_pattern": r"--vscode-tab-activeBackground$",
        "styles": [
            {
                "qt_target": "QTabBar::tab",
                "states": [":selected"],
                "qss_property": "background-color",
                "skip_if_default_value": True,
            }
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-tab-activeForeground$",
        "styles": [
            {
                "qt_target": "QTabBar::tab",
                "states": [":selected"],
                "qss_property": "color",
            }
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-tab-inactiveBackground$",
        "styles": [
            {
                "qt_target": "QTabBar::tab",
                "states": [":!selected"],
                "qss_property": "background-color",
                "skip_if_default_value": True,
            }
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-tab-inactiveForeground$",
        "styles": [
            {
                "qt_target": "QTabBar::tab",
                "states": [":!selected"],
                "qss_property": "color",
            }
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-tab-border$",
        "styles": [
            {
                "qt_target": "QTabWidget::pane",
                "qss_property": "border",
                "value_prefix": "1px solid ",
            },
            {
                "qt_target": "QTabBar",
                "qss_property": "border-bottom",
                "value_prefix": "1px solid ",
            },
        ],
        "note": "Tab borders applied to pane and tab bar bottom. Individual tab borders can be complex.",
    },
    {
        "vscode_var_pattern": r"--vscode-tab-hoverBackground$",
        "styles": [
            {
                "qt_target": "QTabBar::tab",
                "states": [":hover", ":!selected"],
                "qss_property": "background-color",
                "skip_if_default_value": True,
            }
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-tab-hoverForeground$",
        "styles": [
            {
                "qt_target": "QTabBar::tab",
                "states": [":hover", ":!selected"],
                "qss_property": "color",
            }
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-editorGroupHeader-tabsBackground$",
        "styles": [
            {
                "qt_target": "QTabBar",
                "qss_property": "background-color",
                "skip_if_default_value": True,
            }
        ],
    },
    # Status Bar (QStatusBar)
    {
        "vscode_var_pattern": r"--vscode-statusBar-background$",
        "styles": [
            {
                "qt_target": "QStatusBar",
                "qss_property": "background-color",
                "skip_if_default_value": True,
            }
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-statusBar-foreground$",
        "styles": [{"qt_target": "QStatusBar", "qss_property": "color"}],
    },
    {
        "vscode_var_pattern": r"--vscode-statusBar-border$",
        "styles": [
            {
                "qt_target": "QStatusBar",
                "qss_property": "border-top",
                "value_prefix": "1px solid ",
            }
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-statusBarItem-hoverBackground$",
        "styles": [
            {
                "qt_target": "QStatusBar::item",
                "states": [":hover"],
                "qss_property": "background-color",
                "skip_if_default_value": True,
            }
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-statusBarItem-activeBackground$",
        "styles": [
            {
                "qt_target": "QStatusBar::item",
                "states": [":pressed"],
                "qss_property": "background-color",
                "skip_if_default_value": True,
            }
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-statusBarItem-prominentBackground$",
        "styles": [
            {
                "qt_target": 'QStatusBar QLabel[isProminent="true"]',
                "qss_property": "background-color",
                "skip_if_default_value": True,
            }
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-statusBarItem-prominentForeground$",
        "styles": [
            {
                "qt_target": 'QStatusBar QLabel[isProminent="true"]',
                "qss_property": "color",
            }
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-statusBarItem-prominentHoverBackground$",
        "styles": [
            {
                "qt_target": 'QStatusBar QLabel[isProminent="true"]:hover',
                "qss_property": "background-color",
                "skip_if_default_value": True,
            }
        ],
    },
    # Tooltip (QToolTip)
    {
        "vscode_var_pattern": r"--vscode-editorHoverWidget-background$",
        "styles": [
            {
                "qt_target": "QToolTip",
                "qss_property": "background-color",
                "skip_if_default_value": True,
            }
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-editorHoverWidget-foreground$",
        "styles": [{"qt_target": "QToolTip", "qss_property": "color"}],
    },
    {
        "vscode_var_pattern": r"--vscode-editorHoverWidget-border$",
        "styles": [
            {
                "qt_target": "QToolTip",
                "qss_property": "border",
                "value_prefix": "1px solid ",
            }
        ],
    },
    # Checkbox (QCheckBox) & RadioButton (QRadioButton)
    {
        "vscode_var_pattern": r"--vscode-checkbox-background$",
        "styles": [
            {
                "qt_target": "QCheckBox::indicator",
                "qss_property": "background-color",
                "skip_if_default_value": True,
            },
            {
                "qt_target": "QRadioButton::indicator",
                "qss_property": "background-color",
                "skip_if_default_value": True,
            },
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-checkbox-foreground$",
        "styles": [
            {"qt_target": "QCheckBox", "qss_property": "color"},
            {"qt_target": "QRadioButton", "qss_property": "color"},
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-checkbox-border$",
        "styles": [
            {
                "qt_target": "QCheckBox::indicator",
                "qss_property": "border",
                "value_prefix": "1px solid ",
            },
            {
                "qt_target": "QRadioButton::indicator",
                "qss_property": "border",
                "value_prefix": "1px solid ",
            },
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-checkbox-selectBackground$",
        "styles": [
            {
                "qt_target": "QCheckBox::indicator:checked",
                "qss_property": "background-color",
                "skip_if_default_value": True,
            },
            {
                "qt_target": "QRadioButton::indicator:checked",
                "qss_property": "background-color",
                "skip_if_default_value": True,
            },
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-checkbox-selectBorder$",
        "styles": [
            {
                "qt_target": "QCheckBox::indicator:checked",
                "qss_property": "border-color",
            },
            {
                "qt_target": "QRadioButton::indicator:checked",
                "qss_property": "border-color",
            },
        ],
    },
    # Progress Bar (QProgressBar)
    {
        "vscode_var_pattern": r"--vscode-progressBar-background$",
        "styles": [
            {"qt_target": "QProgressBar::chunk", "qss_property": "background-color"},
            {
                "qt_target": "QProgressBar",
                "qss_property": "border",
                "value_prefix": "1px solid ",
            },
        ],
    },
    # Panel, SideBar, TitleBar, ActivityBar (QMainWindow, QDockWidget, QToolBar etc. - approximate)
    {
        "vscode_var_pattern": r"--vscode-sideBar-background$",
        "styles": [
            {
                "qt_target": "QDockWidget",
                "qss_property": "background-color",
                "skip_if_default_value": True,
            },
            {
                "qt_target": "QToolBox::tab",
                "qss_property": "background-color",
                "skip_if_default_value": True,
            },
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-sideBar-foreground$",
        "styles": [
            {"qt_target": "QDockWidget", "qss_property": "color"},
            {"qt_target": "QToolBox::tab", "qss_property": "color"},
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-sideBar-border$",
        "styles": [
            {
                "qt_target": "QDockWidget",
                "qss_property": "border",
                "value_prefix": "1px solid ",
            },
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-sideBarTitle-foreground$",
        "styles": [{"qt_target": "QDockWidget::title", "qss_property": "color"}],
    },
    {
        "vscode_var_pattern": r"--vscode-sideBarSectionHeader-background$",
        "styles": [
            {
                "qt_target": "QDockWidget::title",
                "qss_property": "background-color",
                "skip_if_default_value": True,
            }
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-sideBarSectionHeader-border$",
        "styles": [
            {
                "qt_target": "QDockWidget::title",
                "qss_property": "border",
                "value_prefix": "1px solid ",
            }
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-panel-background$",
        "styles": [
            {
                "qt_target": 'QFrame[frameShape="StyledPanel"]',
                "qss_property": "background-color",
                "skip_if_default_value": True,
            },
            {
                "qt_target": "QTabWidget::pane",
                "qss_property": "background-color",
                "skip_if_default_value": True,
            },
            {
                "qt_target": "QGroupBox",
                "qss_property": "background-color",
                "skip_if_default_value": True,
            },
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-panel-border$",
        "styles": [
            {
                "qt_target": 'QFrame[frameShape="StyledPanel"]',
                "qss_property": "border",
                "value_prefix": "1px solid ",
            },
            {
                "qt_target": "QGroupBox",
                "qss_property": "border",
                "value_prefix": "1px solid ",
            },
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-panelTitle-activeForeground$",
        "styles": [
            {"qt_target": "QGroupBox::title", "qss_property": "color"},
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-panelTitle-activeBorder$",
        "styles": [
            {
                "qt_target": "QGroupBox",
                "qss_property": "border-top",
                "value_prefix": "1px solid ",
            },
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-titleBar-activeBackground$",
        "styles": [
            {
                "qt_target": "QMainWindow",
                "qss_property": "background-color",
                "skip_if_default_value": True,
            }
        ],
        "note": "QMainWindow title bar is largely OS controlled. This sets background for the QMainWindow itself.",
    },
    {
        "vscode_var_pattern": r"--vscode-titleBar-activeForeground$",
        "styles": [],
        "note": "QMainWindow title bar text color is OS controlled.",
    },
    {
        "vscode_var_pattern": r"--vscode-titleBar-border$",
        "styles": [
            {
                "qt_target": "QMainWindow",
                "qss_property": "border-bottom",
                "value_prefix": "1px solid ",
            }
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-activityBar-background$",
        "styles": [
            {
                "qt_target": "QToolBar",
                "qss_property": "background-color",
                "skip_if_default_value": True,
            }
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-activityBar-foreground$",
        "styles": [
            {"qt_target": "QToolBar", "qss_property": "color"},
            {"qt_target": "QToolButton", "qss_property": "color"},
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-activityBar-border$",
        "styles": [
            {
                "qt_target": "QToolBar",
                "qss_property": "border",
                "value_prefix": "1px solid ",
            }
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-activityBar-activeBorder$",
        "styles": [
            {
                "qt_target": "QToolButton",
                "states": [":checked", ":hover"],
                "qss_property": "border",
                "value_prefix": "1px solid ",
            }
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-activityBar-activeBackground$",
        "styles": [
            {
                "qt_target": "QToolButton",
                "states": [":checked"],
                "qss_property": "background-color",
                "skip_if_default_value": True,
            }
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-activityBarBadge-background$",
        "styles": [
            {
                "qt_target": 'QLabel[isBadge="true"]',
                "qss_property": "background-color",
                "skip_if_default_value": True,
            }
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-activityBarBadge-foreground$",
        "styles": [{"qt_target": 'QLabel[isBadge="true"]', "qss_property": "color"}],
    },
    # Notifications (QMessageBox, or custom notification widgets)
    {
        "vscode_var_pattern": r"--vscode-notifications-background$",
        "styles": [
            {
                "qt_target": "QMessageBox",
                "qss_property": "background-color",
                "skip_if_default_value": True,
            }
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-notifications-foreground$",
        "styles": [{"qt_target": "QMessageBox", "qss_property": "color"}],
    },
    {
        "vscode_var_pattern": r"--vscode-notifications-border$",
        "styles": [
            {
                "qt_target": "QMessageBox",
                "qss_property": "border",
                "value_prefix": "1px solid ",
            }
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-notificationsErrorIcon-foreground$",
        "styles": [
            {"qt_target": 'QMessageBox QLabel[isIcon="error"]', "qss_property": "color"}
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-notificationsWarningIcon-foreground$",
        "styles": [
            {
                "qt_target": 'QMessageBox QLabel[isIcon="warning"]',
                "qss_property": "color",
            }
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-notificationsInfoIcon-foreground$",
        "styles": [
            {"qt_target": 'QMessageBox QLabel[isIcon="info"]', "qss_property": "color"}
        ],
    },
    # Keybinding Label (QLabel or custom)
    {
        "vscode_var_pattern": r"--vscode-keybindingLabel-background$",
        "styles": [
            {
                "qt_target": 'QLabel[objectName="keybindingLabel"]',
                "qss_property": "background-color",
                "skip_if_default_value": True,
            }
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-keybindingLabel-foreground$",
        "styles": [
            {
                "qt_target": 'QLabel[objectName="keybindingLabel"]',
                "qss_property": "color",
            }
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-keybindingLabel-border$",
        "styles": [
            {
                "qt_target": 'QLabel[objectName="keybindingLabel"]',
                "qss_property": "border",
                "value_prefix": "1px solid ",
            }
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-widget-shadow$",
        "styles": [
            {
                "qt_target": "QMenu",
                "qss_property": "border",
                "value_prefix": "1px solid ",
            },
            {
                "qt_target": "QToolTip",
                "qss_property": "border",
                "value_prefix": "1px solid ",
            },
            {
                "qt_target": "QComboBox QAbstractItemView",
                "qss_property": "border",
                "value_prefix": "1px solid ",
            },
        ],
        "note": "Widget shadow mapped to border. True shadow effects are complex in QSS.",
    },
    {
        "vscode_var_pattern": r"--vscode-textLink-foreground$",
        "styles": [
            {"qt_target": 'QLabel[htmlLink="true"]', "qss_property": "color"},
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-textLink-activeForeground$",
        "styles": [
            {"qt_target": 'QLabel[htmlLink="true"]:hover', "qss_property": "color"},
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-pickerGroup-border$",
        "styles": [
            {
                "qt_target": 'QFrame[isPickerGroup="true"]',
                "qss_property": "border",
                "value_prefix": "1px solid ",
            },
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-pickerGroup-foreground$",
        "styles": [
            {"qt_target": "QGroupBox::title", "qss_property": "color"},
            {"qt_target": 'QLabel[isPickerGroupLabel="true"]', "qss_property": "color"},
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-terminal-foreground$",
        "styles": [
            {"qt_target": 'QPlainTextEdit[isTerminal="true"]', "qss_property": "color"}
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-terminal-background$",
        "styles": [
            {
                "qt_target": 'QPlainTextEdit[isTerminal="true"]',
                "qss_property": "background-color",
                "skip_if_default_value": True,
            }
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-terminal-selectionBackground$",
        "styles": [
            {
                "qt_target": 'QPlainTextEdit[isTerminal="true"]',
                "qss_property": "selection-background-color",
            }
        ],
    },
    {
        "vscode_var_pattern": r"--vscode-terminalCursor-foreground$",
        "styles": [
            {
                "qt_target": 'QPlainTextEdit[isTerminal="true"]',
                "qss_property": "cursor-color",
            }
        ],
        "note": "cursor-color is not standard QSS, text cursor color is usually via palette.",
    },
]


def _extract_colors_from_component_values(component_values, unique_colors_set):
    for cv in component_values:
        if cv.type == "hash" and not cv.is_identifier:
            unique_colors_set.add(f"#{cv.value}")
        elif cv.type == "function" and cv.name in ("rgb", "rgba"):
            unique_colors_set.add(tinycss2.serialize([cv]))


def _parse_css_linear_gradient_to_qss(css_gradient_args):
    qss_coords = {}
    qss_stops = []
    direction_processed = False
    arg_idx = 0

    while (
        arg_idx < len(css_gradient_args)
        and css_gradient_args[arg_idx].type == "whitespace"
    ):
        arg_idx += 1

    if arg_idx < len(css_gradient_args):
        first_token = css_gradient_args[arg_idx]
        if first_token.type == "ident" and first_token.value.lower() == "to":
            arg_idx += 1
            while (
                arg_idx < len(css_gradient_args)
                and css_gradient_args[arg_idx].type == "whitespace"
            ):
                arg_idx += 1
            direction_parts = []
            while (
                arg_idx < len(css_gradient_args)
                and css_gradient_args[arg_idx].type == "ident"
            ):
                direction_parts.append(css_gradient_args[arg_idx].value.lower())
                arg_idx += 1
                if (
                    arg_idx < len(css_gradient_args)
                    and css_gradient_args[arg_idx].type == "whitespace"
                ):
                    arg_idx += 1
                else:
                    break
            direction = "_".join(sorted(direction_parts))
            coords_map = {
                "bottom": (0, 0, 0, 1),
                "top": (0, 1, 0, 0),
                "left": (1, 0, 0, 0),
                "right": (0, 0, 1, 0),
                "bottom_left": (1, 0, 0, 1),
                "bottom_right": (0, 0, 1, 1),
                "left_top": (1, 1, 0, 0),
                "right_top": (0, 1, 1, 0),
            }
            c = coords_map.get(direction, (0, 0, 0, 1))  # Default to bottom
            qss_coords = {"x1": c[0], "y1": c[1], "x2": c[2], "y2": c[3]}
            direction_processed = True
        elif first_token.type == "dimension" and first_token.unit.lower() in [
            "deg",
            "rad",
            "grad",
            "turn",
        ]:
            angle_val, angle_unit = first_token.value, first_token.unit.lower()
            if angle_unit == "deg":
                angle_val %= 360
                if angle_val == 0:
                    c = (0, 1, 0, 0)  # to top
                elif angle_val == 90:
                    c = (0, 0, 1, 0)  # to right
                elif angle_val == 180:
                    c = (0, 0, 0, 1)  # to bottom
                elif angle_val == 270:
                    c = (1, 0, 0, 0)  # to left
                else:
                    c = (0, 0, 0, 1)  # Default for other angles
                qss_coords = {"x1": c[0], "y1": c[1], "x2": c[2], "y2": c[3]}
            else:
                qss_coords = {"x1": 0, "y1": 0, "x2": 0, "y2": 1}  # Default for non-deg
            arg_idx += 1
            direction_processed = True

    if not direction_processed:
        qss_coords = {"x1": 0, "y1": 0, "x2": 0, "y2": 1}  # Default: top to bottom

    if (
        arg_idx < len(css_gradient_args)
        and css_gradient_args[arg_idx].type == "literal"
        and css_gradient_args[arg_idx].value == ","
    ):
        arg_idx += 1

    raw_stops = []
    current_stop_parts = []
    while arg_idx < len(css_gradient_args):
        token = css_gradient_args[arg_idx]
        arg_idx += 1
        if token.type == "whitespace":
            continue
        if token.type == "literal" and token.value == ",":
            if current_stop_parts:
                raw_stops.append(current_stop_parts)
            current_stop_parts = []
            continue
        current_stop_parts.append(token)
    if current_stop_parts:
        raw_stops.append(current_stop_parts)

    num_stops = len(raw_stops)
    for i, stop_parts in enumerate(raw_stops):
        color_val, pos_val = None, None

        processed_color_part = False
        for part_idx, part_token in enumerate(stop_parts):
            if not processed_color_part and (
                part_token.type == "ident"
                or part_token.type == "hash"
                or (
                    part_token.type == "function" and part_token.name in ["rgb", "rgba"]
                )
            ):
                color_val = tinycss2.serialize([part_token]).strip()
                processed_color_part = True
                continue

            if processed_color_part and part_token.type != "whitespace":
                if part_token.type == "percentage":
                    pos_val = part_token.value / 100.0
                    break
                elif part_token.type == "dimension" and part_token.unit == "%":
                    pos_val = part_token.value / 100.0
                    break
                break

        if color_val:
            if pos_val is not None:
                qss_stops.append(f"stop: {pos_val:.4f} {color_val}")
            else:
                if num_stops == 0:
                    continue
                if num_stops == 1:
                    qss_stops.extend(
                        [f"stop: 0.0000 {color_val}", f"stop: 1.0000 {color_val}"]
                    )
                elif num_stops > 1:
                    qss_stops.append(f"stop: {i / (num_stops - 1.0):.4f} {color_val}")

    if not qss_stops and raw_stops:
        first_color_candidate = None
        for part in raw_stops[0]:
            if (
                part.type == "ident"
                or part.type == "hash"
                or (part.type == "function" and part.name in ["rgb", "rgba"])
            ):
                first_color_candidate = tinycss2.serialize([part]).strip()
                break
        if first_color_candidate:
            qss_stops.extend(
                [
                    f"stop: 0.0000 {first_color_candidate}",
                    f"stop: 1.0000 {first_color_candidate}",
                ]
            )

    if not qss_coords or not qss_stops:
        return None
    return f"qlineargradient({', '.join(f'{k}: {v}' for k, v in qss_coords.items())}, {', '.join(qss_stops)})"


def _serialize_component_values_to_qss_property_value(
    component_values, attempt_gradient_conversion=False
):
    qss_value_parts = []
    for cv in component_values:
        if cv.type == "function":
            func_name = cv.name.lower()
            if func_name == "var":
                cleaned_args = [scv for scv in cv.arguments if scv.type != "whitespace"]
                if cleaned_args:
                    var_ref_name = tinycss2.serialize(cleaned_args).strip()
                    qss_value_parts.append(f"${{{var_ref_name}}}")
                else:
                    qss_value_parts.append(tinycss2.serialize([cv]))
            elif attempt_gradient_conversion and func_name == "linear-gradient":
                qss_gradient = _parse_css_linear_gradient_to_qss(cv.arguments)
                qss_value_parts.append(
                    qss_gradient if qss_gradient else tinycss2.serialize([cv])
                )
            else:
                qss_value_parts.append(tinycss2.serialize([cv]))
        else:
            qss_value_parts.append(tinycss2.serialize([cv]))
    return "".join(qss_value_parts)


def sanitize_for_var_name(text):
    text = text.lower()
    text = re.sub(r"^#", "", text)
    text = re.sub(r"[^\w-]", "_", text)
    text = re.sub(r"_+", "_", text)
    text = text.strip("_")
    return text


def _dedupe_colors(css_vars):
    buckets = defaultdict(list)
    for var, val in css_vars.items():
        val_clean = re.sub(r"\s+", "", val.strip().lower())
        if _HEX_RE.match(val_clean):
            buckets[val_clean].append(var)
            continue
        m = _RGBA_RE.match(val_clean)
        if m:
            r, g, b, a = m.groups()
            r, g, b = [str(min(255, int(c))) for c in (r, g, b)]
            if a is None:
                canon = f"rgb({r},{g},{b})"
            else:
                a_norm = str(float(a)).rstrip("0").rstrip(".")
                if a_norm == "0":
                    a_norm = "0"
                elif a_norm == "1":
                    a_norm = "1"
                canon = f"rgba({r},{g},{b},{a_norm})"
            buckets[canon].append(var)
    return {lit: names for lit, names in buckets.items() if len(names) > 1}


def _make_shared_name(literal, index):
    if literal.startswith("#"):
        return f"color_{index:02d}_{literal.lstrip('#')}"
    squeezed = re.sub(r"[^0-9]+", "", literal)
    return f"color_{index:02d}_rgb{squeezed}"


def _rewrite_defs(original_defs, dup_map):
    shared_defs = []
    replace_lookup = {}
    for idx, (literal, vars_using) in enumerate(sorted(dup_map.items()), start=1):
        shared_name = _make_shared_name(literal, idx)
        shared_defs.append(f"@def {shared_name} {literal};")
        for v in vars_using:
            replace_lookup[v] = shared_name

    rewritten = []
    for line in original_defs:
        if line.startswith("@def "):
            _parts = line.split(None, 2)
            if len(_parts) == 3:
                _, var, val_part = _parts
                if var in replace_lookup:
                    rewritten.append(f"@def {var} ${{{replace_lookup[var]}}};")
                    continue
        rewritten.append(line)
    return shared_defs, rewritten


def parse_vscode_css_to_ida_qss_tinycss2(css_content):
    ida_qss_defs, ida_qss_body_styles, css_variables_map, general_qss_rules = (
        [],
        [],
        {},
        [],
    )
    unique_colors_set = set()
    rules = tinycss2.parse_stylesheet(
        css_content, skip_comments=True, skip_whitespace=True
    )

    for rule in rules:
        if rule.type == "error":
            continue
        if rule.type == "qualified-rule":
            selector_string_raw = tinycss2.serialize(rule.prelude).strip()
            declarations = tinycss2.parse_declaration_list(
                rule.content, skip_comments=True, skip_whitespace=True
            )

            if selector_string_raw == ":root":
                for decl in declarations:
                    if decl.type == "declaration":
                        var_name = decl.name
                        var_val_qss = _serialize_component_values_to_qss_property_value(
                            decl.value, attempt_gradient_conversion=True
                        )
                        css_variables_map[var_name] = var_val_qss
                        ida_qss_defs.append(f"@def {var_name} {var_val_qss};")
                        _extract_colors_from_component_values(
                            decl.value, unique_colors_set
                        )
            elif selector_string_raw == "body":
                ida_qss_body_styles.append("body {")
                for decl in declarations:
                    if decl.type == "declaration":
                        prop_name = decl.name
                        prop_val_qss = (
                            _serialize_component_values_to_qss_property_value(
                                decl.value, attempt_gradient_conversion=True
                            )
                        )
                        if prop_val_qss.startswith("var("):
                            var_ref = prop_val_qss[4:-1]
                            prop_val_qss = f"${{{var_ref}}}"
                        ida_qss_body_styles.append(f"  {prop_name}: {prop_val_qss};")
                ida_qss_body_styles.append("}")
            else:
                translated_qss_selectors = []
                for sel_ast in tinycss2.parse_selector_list(rule.prelude):
                    sel_str = tinycss2.serialize(sel_ast).strip().lower()
                    current_qss_sel = ""
                    if "menubar-menu-title" in sel_str:
                        base = CSS_CLASS_TO_QT_MAPPING.get(
                            "menubar-menu-button", {}
                        ).get("qt_widget", "QMenuBar")
                        sub = CSS_CLASS_TO_QT_MAPPING.get("menubar-menu-title", {}).get(
                            "qt_sub_control", "::item"
                        )
                        current_qss_sel = base + sub
                    elif "menubar-menu-button" in sel_str:
                        current_qss_sel = CSS_CLASS_TO_QT_MAPPING.get(
                            "menubar-menu-button", {}
                        ).get("qt_widget", "QMenuBar")

                    if not current_qss_sel:
                        continue

                    states = []
                    if ".open" in sel_str:
                        s = CSS_CLASS_TO_QT_MAPPING.get("open", {}).get(
                            "qt_pseudo_state"
                        )
                        _ = s and states.append(s)
                    if ":focus" in sel_str:
                        s = CSS_PSEUDO_CLASS_TO_QT_PSEUDO_STATE.get("focus")
                        _ = s and states.append(s)
                    if ":hover" in sel_str:
                        s = CSS_PSEUDO_CLASS_TO_QT_PSEUDO_STATE.get("hover")
                        _ = s and states.append(s)
                    if states:
                        current_qss_sel += "".join(sorted(list(set(states))))

                    if current_qss_sel:
                        translated_qss_selectors.append(current_qss_sel)

                if not translated_qss_selectors:
                    continue
                final_qss_selector = ", ".join(
                    sorted(list(set(translated_qss_selectors)))
                )
                qss_decls = []
                for decl in declarations:
                    if decl.type == "declaration":
                        (
                            css_prop,
                            qss_prop,
                        ) = decl.name.lower(), CSS_PROPERTY_TO_QSS_PROPERTY.get(
                            decl.name.lower()
                        )
                        if (
                            qss_prop is None
                            and css_prop in CSS_PROPERTY_TO_QSS_PROPERTY
                        ):
                            continue
                        if not qss_prop:
                            continue
                        qss_val = _serialize_component_values_to_qss_property_value(
                            decl.value, True
                        )
                        qss_decls.append(f"  {qss_prop}: {qss_val};")
                if qss_decls:
                    general_qss_rules.extend(
                        [f"{final_qss_selector} {{"] + qss_decls + ["}", ""]
                    )

    duplicate_buckets = _dedupe_colors(css_variables_map)
    if duplicate_buckets:
        shared_defs, ida_qss_defs = _rewrite_defs(ida_qss_defs, duplicate_buckets)
        ida_qss_defs = shared_defs + ida_qss_defs

    # MODIFIED: Use defaultdict(dict) to store property-value pairs for each selector
    generated_widget_rules = defaultdict(dict)
    for var_name_orig, resolved_var_value in css_variables_map.items():
        qss_value_ref = f"${{{var_name_orig}}}"

        for mapping_entry in VSCODE_VAR_TO_QT_STYLE_MAP:
            pattern = mapping_entry["vscode_var_pattern"]
            match = re.fullmatch(pattern, var_name_orig)

            if match:
                for style_rule in mapping_entry["styles"]:
                    if (
                        "dynamic_var_part_idx" in style_rule
                        and "condition_value" in style_rule
                    ):
                        # Ensure match.groups() is not empty and index is valid
                        if not match.groups() or style_rule[
                            "dynamic_var_part_idx"
                        ] >= len(match.groups()):
                            continue  # Cannot evaluate condition
                        captured_group = match.groups()[
                            style_rule["dynamic_var_part_idx"]
                        ]
                        if (
                            captured_group.lower()
                            != style_rule["condition_value"].lower()
                        ):
                            continue

                    if style_rule.get("skip_if_default_value", False):
                        normalized_resolved_value = resolved_var_value.lower().replace(
                            " ", ""
                        )
                        if (
                            normalized_resolved_value == "rgba(0,0,0,0)"
                            or normalized_resolved_value == "transparent"
                            or (
                                style_rule.get("qss_property") == "background-color"
                                and normalized_resolved_value == "rgba(0,0,0,0.0)"
                            )
                        ):
                            continue

                    qt_target = style_rule["qt_target"]
                    qss_prop = style_rule["qss_property"]
                    sub_control = style_rule.get("sub_control", "")
                    states_list = style_rule.get("states", [])
                    states = "".join(sorted(list(set(states_list))))

                    selector = f"{qt_target}{states}{sub_control}"

                    value_prefix = style_rule.get("value_prefix", "")
                    value_suffix = style_rule.get("value_suffix", "")

                    final_value_part = ""
                    if style_rule.get("value_format_is_direct"):
                        final_value_part = qss_value_ref
                    else:
                        final_value_part = (
                            f"{value_prefix}{qss_value_ref}{value_suffix}"
                        )

                    # MODIFIED: Store as property: full_declaration_string pair
                    # This ensures "last write wins" for the same property on the same selector
                    generated_widget_rules[selector][
                        qss_prop
                    ] = f"  {qss_prop}: {final_value_part};"

    # MODIFIED: Iterate through the dictionary of properties for each selector
    for selector, properties_dict in sorted(generated_widget_rules.items()):
        if properties_dict:  # if there are any properties for this selector
            general_qss_rules.append(f"{selector} {{")
            # Sort by property name (key of properties_dict) for consistent output of declarations
            for qss_prop_key in sorted(properties_dict.keys()):
                general_qss_rules.append(properties_dict[qss_prop_key])
            general_qss_rules.append("}")
            general_qss_rules.append("")

    output = [
        "/* Generated IDA Pro QSS Theme from VSCode CSS (using tinycss2) */",
        "/* For use with IDA Pro's QSS theming engine */\n",
    ]
    if ida_qss_defs:
        output.extend(
            ["/* Variable Definitions */"] + sorted(list(set(ida_qss_defs))) + ["\n"]
        )
    if ida_qss_body_styles:
        output.extend(["/* Body Styles */"] + ida_qss_body_styles + ["\n"])
    if general_qss_rules:
        output.extend(["/* General Widget Styles */"] + general_qss_rules)

    final_css_variables_map_for_metadata = {}
    for def_line in ida_qss_defs:
        parts = def_line.replace("@def ", "").replace(";", "").split(None, 1)
        if len(parts) == 2:
            final_css_variables_map_for_metadata[parts[0]] = parts[1]

    metadata = {
        "css_variables": final_css_variables_map_for_metadata,
        "unique_colors": sorted(list(unique_colors_set)),
    }
    return "\n".join(output), metadata


CSS_TO_PARSE = r"""
:root {
  --vscode-font-family: -apple-system, BlinkMacSystemFont, sans-serif;
  --vscode-font-weight: normal;
  --vscode-font-size: 13px;
  --vscode-editor-font-family: Menlo, Monaco, "Courier New", monospace;
  --vscode-editor-font-weight: normal;
  --vscode-editor-font-size: 12px;
  --vscode-foreground: #ffffff;
  --vscode-disabledForeground: #a5a5a5;
  --vscode-errorForeground: #f48771;
  --vscode-descriptionForeground: rgba(255, 255, 255, 0.7);
  --vscode-icon-foreground: #ffffff;
  --vscode-focusBorder: #f38518;
  --vscode-contrastBorder: #6fc3df;
  --vscode-contrastActiveBorder: #f38518;
  --vscode-selection-background: #008000; /* This is --vscode-editor-selectionBackground in newer themes */
  --vscode-textSeparator-foreground: #000000;
  --vscode-textLink-foreground: #3794ff;
  --vscode-textLink-activeForeground: #3794ff;
  --vscode-textPreformat-foreground: #d7ba7d;
  --vscode-textBlockQuote-border: #ffffff;
  --vscode-textCodeBlock-background: #000000;
  --vscode-widget-shadow: rgba(0, 0, 0, 0.36); /* Added for testing */
  --vscode-input-background: #000000;
  --vscode-input-foreground: #ffffff;
  --vscode-input-border: #6fc3df;
  --vscode-inputOption-activeBorder: #6fc3df;
  --vscode-inputOption-activeBackground: rgba(0, 0, 0, 0);
  --vscode-inputOption-activeForeground: #ffffff;
  --vscode-input-placeholderForeground: rgba(255, 255, 255, 0.7);
  --vscode-inputValidation-infoBackground: #000000;
  --vscode-inputValidation-infoBorder: #6fc3df;
  --vscode-inputValidation-warningBackground: #000000;
  --vscode-inputValidation-warningBorder: #6fc3df;
  --vscode-inputValidation-errorBackground: #000000;
  --vscode-inputValidation-errorBorder: #6fc3df;
  --vscode-dropdown-background: #000000;
  --vscode-dropdown-listBackground: #000000;
  --vscode-dropdown-foreground: #ffffff;
  --vscode-dropdown-border: #6fc3df;
  --vscode-button-foreground: #ffffff;
  --vscode-button-background: #0e639c; /* Added a default button bg for testing */
  --vscode-button-hoverBackground: #1177bb; /* Added for testing */
  --vscode-button-separator: rgba(255, 255, 255, 0.4);
  --vscode-button-border: #6fc3df;
  --vscode-button-secondaryForeground: #ffffff;
  --vscode-button-secondaryBackground: #3a3d41; /* Added for testing */
  --vscode-button-secondaryHoverBackground: #4c5055; /* Added for testing */
  --vscode-badge-background: #000000;
  --vscode-badge-foreground: #ffffff;
  --vscode-scrollbar-shadow: rgba(0, 0, 0, 0.2); /* Added for testing */
  --vscode-scrollbarSlider-background: rgba(111, 195, 223, 0.6);
  --vscode-scrollbarSlider-hoverBackground: rgba(111, 195, 223, 0.8);
  --vscode-scrollbarSlider-activeBackground: #6fc3df;
  --vscode-progressBar-background: #6fc3df;
  --vscode-editorError-foreground: #f48771;
  --vscode-editorError-border: rgba(228, 119, 119, 0.8);
  --vscode-editorWarning-foreground: #ff0000;
  --vscode-editorWarning-border: rgba(255, 204, 0, 0.8);
  --vscode-editorInfo-foreground: #3794ff;
  --vscode-editorInfo-border: rgba(55, 148, 255, 0.8);
  --vscode-editorHint-border: rgba(238, 238, 238, 0.8);
  --vscode-sash-hoverBorder: #f38518;
  --vscode-editor-background: #000000;
  --vscode-editor-foreground: #ffffff;
  --vscode-editorStickyScroll-background: #000000;
  --vscode-editorWidget-background: #0c141f;
  --vscode-editorWidget-foreground: #ffffff;
  --vscode-editorWidget-border: #6fc3df;
  --vscode-quickInput-background: #0c141f;
  --vscode-quickInput-foreground: #ffffff;
  --vscode-quickInputTitle-background: #000000;
  --vscode-pickerGroup-foreground: #ffffff;
  --vscode-pickerGroup-border: #ffffff;
  --vscode-keybindingLabel-background: rgba(0, 0, 0, 0);
  --vscode-keybindingLabel-foreground: #ffffff;
  --vscode-keybindingLabel-border: #6fc3df;
  --vscode-keybindingLabel-bottomBorder: #6fc3df;
  --vscode-editor-selectionBackground: #ffffff; /* Note: VSCode often uses more specific like editor.selectionBackground */
  --vscode-editor-selectionForeground: #000000;
  --vscode-editor-inactiveSelectionBackground: rgba(255, 255, 255, 0.7);
  --vscode-editor-selectionHighlightBorder: #f38518;
  --vscode-editor-findMatchBorder: #f38518;
  --vscode-editor-findMatchHighlightBorder: #f38518;
  --vscode-editor-findRangeHighlightBorder: rgba(243, 133, 24, 0.4);
  --vscode-searchEditor-findMatchBorder: #f38518;
  --vscode-editor-hoverHighlightBackground: rgba(173, 214, 255, 0.15);
  --vscode-editorHoverWidget-background: #0c141f;
  --vscode-editorHoverWidget-foreground: #ffffff;
  --vscode-editorHoverWidget-border: #6fc3df;
  --vscode-editorHoverWidget-statusBarBackground: #0c141f;
  --vscode-editorLink-activeForeground: #00ffff;
  --vscode-editorInlayHint-foreground: #000000;
  --vscode-editorInlayHint-background: #f38518;
  --vscode-editorLightBulb-foreground: #ffcc00;
  --vscode-editorLightBulbAutoFix-foreground: #75beff;
  --vscode-diffEditor-insertedTextBorder: #33ff2e;
  --vscode-diffEditor-removedTextBorder: #ff008f;
  --vscode-diffEditor-border: #6fc3df;
  --vscode-list-focusOutline: #f38518;
  --vscode-list-activeSelectionBackground: #094771; /* Added for testing */
  --vscode-list-activeSelectionForeground: #ffffff; /* Added for testing */
  --vscode-list-inactiveSelectionBackground: #37373d; /* Added for testing */
  --vscode-list-inactiveSelectionForeground: #cccccc; /* Added for testing */
  --vscode-list-hoverBackground: rgba(255, 255, 255, 0.1); /* Added for testing */
  --vscode-list-hoverForeground: #ffffff; /* Added for testing */
  --vscode-list-highlightForeground: #f38518;
  --vscode-list-focusHighlightForeground: #f38518;
  --vscode-list-invalidItemForeground: #b89500;
  --vscode-listFilterWidget-background: #0c141f;
  --vscode-listFilterWidget-outline: #f38518;
  --vscode-listFilterWidget-noMatchesOutline: #6fc3df;
  --vscode-list-filterMatchBorder: #6fc3df;
  --vscode-tree-indentGuidesStroke: #a9a9a9;
  --vscode-list-deemphasizedForeground: #a7a8a9;
  --vscode-checkbox-background: #000000;
  --vscode-checkbox-selectBackground: #0c141f; /* For checked state */
  --vscode-checkbox-foreground: #ffffff;
  --vscode-checkbox-border: #6fc3df;
  --vscode-checkbox-selectBorder: #0c141f; /* Border for checked state */
  --vscode-menu-border: #6fc3df;
  --vscode-menu-foreground: #ffffff;
  --vscode-menu-background: #000000;
  --vscode-menu-selectionBorder: #f38518;
  --vscode-menu-selectionBackground: #094771; /* Added for testing */
  --vscode-menu-selectionForeground: #ffffff; /* Added for testing */
  --vscode-menu-separatorBackground: #6fc3df;
  --vscode-toolbar-hoverOutline: #f38518;
  --vscode-editor-snippetTabstopHighlightBackground: rgba(124, 124, 124, 0.3);
  --vscode-editor-snippetFinalTabstopHighlightBorder: #525252;
  --vscode-breadcrumb-foreground: rgba(255, 255, 255, 0.8);
  --vscode-breadcrumb-background: #000000;
  --vscode-breadcrumb-focusForeground: #ffffff;
  --vscode-breadcrumb-activeSelectionForeground: #ffffff;
  --vscode-breadcrumbPicker-background: #0c141f;
  --vscode-settings-headerForeground: #ffffff;
  --vscode-settings-modifiedItemIndicator: #00497a;
  --vscode-settings-dropdownBackground: #000000;
  --vscode-settings-dropdownForeground: #ffffff;
  --vscode-settings-dropdownBorder: #6fc3df;
  --vscode-settings-textInputBackground: #000000;
  --vscode-settings-textInputForeground: #ffffff;
  --vscode-settings-textInputBorder: #6fc3df;
  --vscode-settings-numberInputBackground: #000000;
  --vscode-settings-numberInputForeground: #ffffff;
  --vscode-settings-numberInputBorder: #6fc3df;
  --vscode-settings-focusedRowBorder: #f38518; /* For settings UI */
  --vscode-terminal-foreground: #cccccc; /* Example */
  --vscode-terminal-background: #1e1e1e; /* Example */
  --vscode-terminal-selectionBackground: #ffffff;
  --vscode-terminal-inactiveSelectionBackground: rgba(255, 255, 255, 0.7);
  --vscode-terminal-selectionForeground: #000000;
  --vscode-terminalCursor-foreground: #ffffff; /* Example */
  --vscode-terminal-border: #6fc3df;
  --vscode-terminal-findMatchBorder: #f38518;
  --vscode-terminal-findMatchHighlightBorder: #f38518;
  --vscode-testing-iconFailed: #f14c4c;
  --vscode-testing-iconErrored: #f14c4c;
  --vscode-testing-iconPassed: #73c991;
  --vscode-testing-runAction: #73c991;
  --vscode-testing-iconQueued: #cca700;
  --vscode-testing-iconUnset: #848484;
  --vscode-testing-iconSkipped: #848484;
  --vscode-testing-peekBorder: #6fc3df;
  --vscode-welcomePage-tileBackground: #000000;
  --vscode-welcomePage-tileBorder: #6fc3df;
  --vscode-welcomePage-progress\.background: #000000;
  --vscode-welcomePage-progress\.foreground: #3794ff;
  --vscode-editor-lineHighlightBorder: #f38518;
  --vscode-editorCursor-foreground: #ffffff;
  --vscode-editorWhitespace-foreground: #7c7c7c;
  --vscode-editorIndentGuide-background: #ffffff;
  --vscode-editorIndentGuide-activeBackground: #ffffff;
  --vscode-editorLineNumber-foreground: #ffffff;
  --vscode-editorActiveLineNumber-foreground: #f38518;
  --vscode-editorLineNumber-activeForeground: #f38518;
  --vscode-editorRuler-foreground: #ffffff;
  --vscode-editorBracketMatch-background: rgba(0, 100, 0, 0.1);
  --vscode-editorBracketMatch-border: #6fc3df;
  --vscode-editorGutter-background: #000000;
  --vscode-tab-activeBackground: #000000;
  --vscode-tab-unfocusedActiveBackground: #000000;
  --vscode-tab-activeForeground: #ffffff;
  --vscode-tab-inactiveBackground: #2d2d2d; /* Added for testing */
  --vscode-tab-inactiveForeground: #ffffff;
  --vscode-tab-unfocusedActiveForeground: #ffffff;
  --vscode-tab-unfocusedInactiveForeground: #ffffff;
  --vscode-tab-border: #6fc3df;
  --vscode-tab-hoverBackground: rgba(255,255,255,0.1); /* Added for testing */
  --vscode-tab-hoverForeground: #ffffff; /* Added for testing */
  --vscode-editorGroupHeader-tabsBackground: #1e1e1e; /* Background for tab bar area */
  --vscode-editorGroupHeader-tabsBorder: #333333; /* Border below tab bar */
  --vscode-editorPane-background: #000000;
  --vscode-panel-background: #000000;
  --vscode-panel-border: #6fc3df;
  --vscode-panelTitle-activeForeground: #ffffff;
  --vscode-panelTitle-inactiveForeground: #ffffff;
  --vscode-panelTitle-activeBorder: #6fc3df;
  --vscode-panelInput-border: #6fc3df;
  --vscode-statusBar-background: #000000;
  --vscode-statusBar-foreground: #ffffff;
  --vscode-statusBar-border: #6fc3df;
  --vscode-statusBarItem-activeBackground: rgba(255, 255, 255, 0.18);
  --vscode-statusBarItem-hoverBackground: rgba(255, 255, 255, 0.12);
  --vscode-statusBarItem-prominentBackground: rgba(0, 0, 0, 0.5);
  --vscode-statusBarItem-prominentForeground: #ffffff;
  --vscode-statusBarItem-prominentHoverBackground: rgba(0, 0, 0, 0.3);
  --vscode-activityBar-background: #000000;
  --vscode-activityBar-foreground: #ffffff;
  --vscode-activityBar-inactiveForeground: #ffffff;
  --vscode-activityBar-border: #6fc3df;
  --vscode-activityBar-activeBorder: #ffffff; /* For active/focused toolbar button */
  --vscode-activityBar-activeBackground: #ffffff33; /* For active/focused toolbar button */
  --vscode-activityBarBadge-background: #000000;
  --vscode-activityBarBadge-foreground: #ffffff;
  --vscode-sideBar-background: #000000;
  --vscode-sideBar-border: #6fc3df;
  --vscode-sideBarTitle-foreground: #ffffff;
  --vscode-sideBarSectionHeader-background: #00000033; /* Background for section headers in sidebar */
  --vscode-sideBarSectionHeader-border: #6fc3df88;
  --vscode-titleBar-activeBackground: #000000;
  --vscode-titleBar-activeForeground: #ffffff;
  --vscode-titleBar-border: #6fc3df;
  --vscode-menubar-selectionForeground: #ffffff;
  --vscode-menubar-selectionBackground: #ffffff33; /* Background for selected menubar item */
  --vscode-menubar-selectionBorder: #f38518;
  --vscode-notifications-foreground: #ffffff;
  --vscode-notifications-background: #0c141f;
  --vscode-notifications-border: #0c141f;
  --vscode-notificationsErrorIcon-foreground: #f48771;
  --vscode-notificationsWarningIcon-foreground: #ff0000;
  --vscode-notificationsInfoIcon-foreground: #3794ff;
}

body {
  background-color: var(--vscode-editor-background); /* Use a variable */
  color: var(--vscode-editor-foreground);
  font-family: var(--vscode-font-family);
  font-weight: var(--vscode-font-weight);
  font-size: var(--vscode-font-size);
  margin: 0;
  padding: 0 20px; /* This might not be desired for QSS */
}

/* Example of a rule that would need mapping, if it existed in the input */
/*
.monaco-workbench .menubar > .menubar-menu-button.open .menubar-menu-title,
.monaco-workbench .menubar > .menubar-menu-button:focus .menubar-menu-title,
.monaco-workbench .menubar > .menubar-menu-button:hover .menubar-menu-title {
  outline-color: var(--vscode-menubar-selectionBorder);
  outline-offset: -1px;
}
*/
"""

if __name__ == "__main__":
    qss_output, extracted_metadata = parse_vscode_css_to_ida_qss_tinycss2(CSS_TO_PARSE)

    print("--- Generated IDA Pro QSS (using tinycss2) ---")
    print(qss_output)

    print(
        f"\n--- Extracted CSS Variables (Total: {len(extracted_metadata['css_variables'])}) ---"
    )
    # for var_name, var_value in extracted_metadata["css_variables"].items():
    #     print(f"{var_name}: {var_value}")

    print(
        f"\n--- Extracted Unique Colors (Total: {len(extracted_metadata['unique_colors'])}) ---"
    )
    # for color in extracted_metadata["unique_colors"]:
    #     print(color)
    pass
