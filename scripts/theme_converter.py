import re
from collections import defaultdict

import tinycss2

_HEX_RE = re.compile(r"^#(?:[0-9a-f]{3}){1,2}$", re.I)
# captures      r  g  b  [a]
_RGBA_RE = re.compile(
    r"^rgba?\(\s*"
    r"(\d{1,3})\s*,\s*"
    r"(\d{1,3})\s*,\s*"
    r"(\d{1,3})"
    r"(?:\s*,\s*([0-9]*\.?[0-9]+))?"
    r"\s*\)$",
    re.I,
)

# --- Qt Styling Information (Comprehensive Lists for Reference) ---

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

# --- User-Defined Mappings (to be expanded based on VSCode CSS analysis) ---
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
            if angle_unit == "deg":  # Simplified angle to QSS coordinate mapping
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
        qss_coords = {"x1": 0, "y1": 0, "x2": 0, "y2": 1}

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
        if stop_parts and (
            stop_parts[0].type == "ident"
            or stop_parts[0].type == "hash"
            or (
                stop_parts[0].type == "function"
                and stop_parts[0].name in ["rgb", "rgba"]
            )
        ):
            color_val = tinycss2.serialize([stop_parts[0]]).strip()
        if len(stop_parts) > 1:
            pos_token = stop_parts[-1]
            if pos_token.type == "percentage":
                pos_val = pos_token.value / 100.0
            elif pos_token.type == "dimension" and pos_token.unit == "%":
                pos_val = pos_token.value / 100.0
        if color_val:
            if pos_val is not None:
                qss_stops.append(f"stop: {pos_val:.4f} {color_val}")
            else:
                if num_stops == 1:
                    qss_stops.extend(
                        [f"stop: 0.0 {color_val}", f"stop: 1.0 {color_val}"]
                    )
                elif num_stops > 1:
                    qss_stops.append(f"stop: {i / (num_stops - 1.0):.4f} {color_val}")
    if not qss_stops and raw_stops:
        fallback_color = tinycss2.serialize([raw_stops[0][0]]).strip()
        qss_stops.extend([f"stop: 0.0 {fallback_color}", f"stop: 1.0 {fallback_color}"])

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
                    qss_value_parts.append(
                        f"${{{tinycss2.serialize(cleaned_args).strip()}}}"
                    )
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
            # Correctly parse declarations from rule.content
            declarations = tinycss2.parse_declaration_list(
                rule.content, skip_comments=True, skip_whitespace=True
            )

            if selector_string_raw == ":root":
                for decl in declarations:
                    if decl.type == "declaration":
                        var_name = decl.name
                        var_val_qss = _serialize_component_values_to_qss_property_value(
                            decl.value, True
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
                                decl.value, True
                            )
                        )
                        ida_qss_body_styles.append(f"  {prop_name}: {prop_val_qss};")
                ida_qss_body_styles.append("}")
            else:  # General rules
                translated_qss_selectors = []
                for sel_ast in tinycss2.parse_selector_list(rule.prelude):
                    sel_str = tinycss2.serialize(sel_ast).strip().lower()
                    current_qss_sel = ""  # Placeholder for robust selector translation
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
                        continue  # Skip if no base mapping

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

    # ------------------------------------------------------------------
    #  NEW STEP – hoist identical hex literals into shared variables
    # ------------------------------------------------------------------
    duplicate_buckets = _dedupe_colors(css_variables_map)
    if duplicate_buckets:
        shared_defs, ida_qss_defs = _rewrite_defs(ida_qss_defs, duplicate_buckets)
        # put the shared @defs at the very top of the definition block
        ida_qss_defs = shared_defs + ida_qss_defs

    output = [
        "/* Generated IDA Pro QSS Theme from VSCode CSS (using tinycss2) */",
        "/* For use with IDA Pro's QSS theming engine */\n",
    ]
    if ida_qss_defs:
        output.extend(["/* Variable Definitions */"] + ida_qss_defs + ["\n"])
    if ida_qss_body_styles:
        output.extend(["/* Body Styles */"] + ida_qss_body_styles + ["\n"])
    if general_qss_rules:
        output.extend(["/* General Widget Styles */"] + general_qss_rules)

    metadata = {
        "css_variables": css_variables_map,
        "unique_colors": sorted(list(unique_colors_set)),
    }
    return "\n".join(output), metadata


def sanitize_for_var_name(text):
    text = text.lower()
    text = re.sub(r"^#", "", text)  # Remove leading #
    text = re.sub(r"[^\w-]", "_", text)  # Replace non-alphanumeric (excluding -) with _
    text = re.sub(r"_+", "_", text)  # Replace multiple underscores with single
    text = text.strip("_")
    return text


def _dedupe_colors(css_vars):
    """
    Return { '#rrggbb' : [var, var, …] } for any literal that appears ≥2×.
    Only simple hex colours are considered; gradients / rgba() are ignored.
    """
    buckets = defaultdict(list)
    for var, val in css_vars.items():
        # 1. trim ends, 2. collapse ALL whitespace so "rgba(255, 255, 0, .3)" or
        #    the multi-line variant becomes "rgba(255,255,0,.3)"
        val_clean = re.sub(r"\s+", "", val.strip().lower())

        # --- HEX ----------------------------------------------------------------
        if _HEX_RE.match(val_clean):
            buckets[val_clean].append(var)
            continue

        # --- RGB / RGBA ---------------------------------------------------------
        m = _RGBA_RE.match(val_clean)
        if m:
            r, g, b, a = m.groups()
            # clamp / canonicalise channel ranges and build minimal form
            r, g, b = [str(min(255, int(c))) for c in (r, g, b)]
            if a is None:
                canon = f"rgb({r},{g},{b})"
            else:
                # normalise alpha → strip trailing zeros, but keep one leading 0 if <1
                a_norm = str(float(a)).rstrip("0").rstrip(".")
                canon = f"rgba({r},{g},{b},{a_norm})"
            buckets[canon].append(var)
            continue

    # ignore gradients / keywords etc.
    # return buckets
    return {lit: names for lit, names in buckets.items() if len(names) > 1}


def _make_shared_name(literal, index):
    """e.g. '#75beff', 1 → 'color_01_75beff'"""
    if literal.startswith("#"):
        return f"color_{index:02d}_{literal.lstrip('#')}"
    # rgb(a) → squeeze non-digits for brevity, e.g. rgba25525525507
    squeezed = re.sub(r"[^0-9]+", "", literal)
    return f"color_{index:02d}_rgb{squeezed}"


def _rewrite_defs(original_defs, dup_map):
    """
    • Creates one shared @def per colour literal.
    • Rewrites any existing @def that carried that literal to reference it.
    Returns (shared_defs, rewritten_defs).
    """
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
            _parts = line.split(None, 2)  # "@def", var, value;
            if len(_parts) == 3:
                _, var, _ = _parts
                if var in replace_lookup:
                    rewritten.append(f"@def {var} ${{{replace_lookup[var]}}};")
                    continue
        rewritten.append(line)

    return shared_defs, rewritten


CSS_TO_PARSE = """
/*
 * These were copied from VSCode Dark High Contrast theme.
 *
 * To update these, open a webview in VSCode, open the webview developer tools and find the
 * iframe hosting the webview. The <html> element will have a style attribute that contains
 * the CSS variables. Copy these to this file.
 */
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
  --vscode-selection-background: #008000;
  --vscode-textSeparator-foreground: #000000;
  --vscode-textLink-foreground: #3794ff;
  --vscode-textLink-activeForeground: #3794ff;
  --vscode-textPreformat-foreground: #d7ba7d;
  --vscode-textBlockQuote-border: #ffffff;
  --vscode-textCodeBlock-background: #000000;
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
  --vscode-button-separator: rgba(255, 255, 255, 0.4);
  --vscode-button-border: #6fc3df;
  --vscode-button-secondaryForeground: #ffffff;
  --vscode-badge-background: #000000;
  --vscode-badge-foreground: #ffffff;
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
  --vscode-editor-selectionBackground: #ffffff;
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
  --vscode-editorInlayHint-typeForeground: #000000;
  --vscode-editorInlayHint-typeBackground: #f38518;
  --vscode-editorInlayHint-parameterForeground: #000000;
  --vscode-editorInlayHint-parameterBackground: #f38518;
  --vscode-editorLightBulb-foreground: #ffcc00;
  --vscode-editorLightBulbAutoFix-foreground: #75beff;
  --vscode-diffEditor-insertedTextBorder: #33ff2e;
  --vscode-diffEditor-removedTextBorder: #ff008f;
  --vscode-diffEditor-border: #6fc3df;
  --vscode-list-focusOutline: #f38518;
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
  --vscode-checkbox-selectBackground: #0c141f;
  --vscode-checkbox-foreground: #ffffff;
  --vscode-checkbox-border: #6fc3df;
  --vscode-checkbox-selectBorder: #0c141f;
  --vscode-menu-border: #6fc3df;
  --vscode-menu-foreground: #ffffff;
  --vscode-menu-background: #000000;
  --vscode-menu-selectionBorder: #f38518;
  --vscode-menu-separatorBackground: #6fc3df;
  --vscode-toolbar-hoverOutline: #f38518;
  --vscode-editor-snippetTabstopHighlightBackground: rgba(124, 124, 124, 0.3);
  --vscode-editor-snippetFinalTabstopHighlightBorder: #525252;
  --vscode-breadcrumb-foreground: rgba(255, 255, 255, 0.8);
  --vscode-breadcrumb-background: #000000;
  --vscode-breadcrumb-focusForeground: #ffffff;
  --vscode-breadcrumb-activeSelectionForeground: #ffffff;
  --vscode-breadcrumbPicker-background: #0c141f;
  --vscode-merge-border: #c3df6f;
  --vscode-editorOverviewRuler-currentContentForeground: #c3df6f;
  --vscode-editorOverviewRuler-incomingContentForeground: #c3df6f;
  --vscode-editorOverviewRuler-commonContentForeground: #c3df6f;
  --vscode-editorOverviewRuler-findMatchForeground: #ab5a00;
  --vscode-editorOverviewRuler-selectionHighlightForeground: rgba(
    160,
    160,
    160,
    0.8
  );
  --vscode-minimap-findMatchHighlight: #ab5a00;
  --vscode-minimap-selectionOccurrenceHighlight: #ffffff;
  --vscode-minimap-selectionHighlight: #ffffff;
  --vscode-minimap-errorHighlight: #ff3232;
  --vscode-minimap-warningHighlight: rgba(255, 204, 0, 0.8);
  --vscode-minimap-foregroundOpacity: #000000;
  --vscode-minimapSlider-background: rgba(111, 195, 223, 0.3);
  --vscode-minimapSlider-hoverBackground: rgba(111, 195, 223, 0.4);
  --vscode-minimapSlider-activeBackground: rgba(111, 195, 223, 0.5);
  --vscode-problemsErrorIcon-foreground: #f48771;
  --vscode-problemsWarningIcon-foreground: #ff0000;
  --vscode-problemsInfoIcon-foreground: #3794ff;
  --vscode-charts-foreground: #ffffff;
  --vscode-charts-lines: rgba(255, 255, 255, 0.5);
  --vscode-charts-red: #f48771;
  --vscode-charts-blue: #3794ff;
  --vscode-charts-yellow: #ff0000;
  --vscode-charts-orange: #ab5a00;
  --vscode-charts-green: #89d185;
  --vscode-charts-purple: #b180d7;
  --vscode-symbolIcon-arrayForeground: #ffffff;
  --vscode-symbolIcon-booleanForeground: #ffffff;
  --vscode-symbolIcon-classForeground: #ee9d28;
  --vscode-symbolIcon-colorForeground: #ffffff;
  --vscode-symbolIcon-constantForeground: #ffffff;
  --vscode-symbolIcon-constructorForeground: #b180d7;
  --vscode-symbolIcon-enumeratorForeground: #ee9d28;
  --vscode-symbolIcon-enumeratorMemberForeground: #75beff;
  --vscode-symbolIcon-eventForeground: #ee9d28;
  --vscode-symbolIcon-fieldForeground: #75beff;
  --vscode-symbolIcon-fileForeground: #ffffff;
  --vscode-symbolIcon-folderForeground: #ffffff;
  --vscode-symbolIcon-functionForeground: #b180d7;
  --vscode-symbolIcon-interfaceForeground: #75beff;
  --vscode-symbolIcon-keyForeground: #ffffff;
  --vscode-symbolIcon-keywordForeground: #ffffff;
  --vscode-symbolIcon-methodForeground: #b180d7;
  --vscode-symbolIcon-moduleForeground: #ffffff;
  --vscode-symbolIcon-namespaceForeground: #ffffff;
  --vscode-symbolIcon-nullForeground: #ffffff;
  --vscode-symbolIcon-numberForeground: #ffffff;
  --vscode-symbolIcon-objectForeground: #ffffff;
  --vscode-symbolIcon-operatorForeground: #ffffff;
  --vscode-symbolIcon-packageForeground: #ffffff;
  --vscode-symbolIcon-propertyForeground: #ffffff;
  --vscode-symbolIcon-referenceForeground: #ffffff;
  --vscode-symbolIcon-snippetForeground: #ffffff;
  --vscode-symbolIcon-stringForeground: #ffffff;
  --vscode-symbolIcon-structForeground: #ffffff;
  --vscode-symbolIcon-textForeground: #ffffff;
  --vscode-symbolIcon-typeParameterForeground: #ffffff;
  --vscode-symbolIcon-unitForeground: #ffffff;
  --vscode-symbolIcon-variableForeground: #75beff;
  --vscode-editor-lineHighlightBorder: #f38518;
  --vscode-editor-rangeHighlightBorder: #f38518;
  --vscode-editor-symbolHighlightBorder: #f38518;
  --vscode-editorCursor-foreground: #ffffff;
  --vscode-editorWhitespace-foreground: #7c7c7c;
  --vscode-editorIndentGuide-background: #ffffff;
  --vscode-editorIndentGuide-activeBackground: #ffffff;
  --vscode-editorLineNumber-foreground: #ffffff;
  --vscode-editorActiveLineNumber-foreground: #f38518;
  --vscode-editorLineNumber-activeForeground: #f38518;
  --vscode-editorRuler-foreground: #ffffff;
  --vscode-editorCodeLens-foreground: #999999;
  --vscode-editorBracketMatch-background: rgba(0, 100, 0, 0.1);
  --vscode-editorBracketMatch-border: #6fc3df;
  --vscode-editorOverviewRuler-border: rgba(127, 127, 127, 0.3);
  --vscode-editorGutter-background: #000000;
  --vscode-editorUnnecessaryCode-border: rgba(255, 255, 255, 0.8);
  --vscode-editorGhostText-border: rgba(255, 255, 255, 0.8);
  --vscode-editorOverviewRuler-rangeHighlightForeground: rgba(0, 122, 204, 0.6);
  --vscode-editorOverviewRuler-errorForeground: #ff3232;
  --vscode-editorOverviewRuler-warningForeground: rgba(255, 204, 0, 0.8);
  --vscode-editorOverviewRuler-infoForeground: rgba(55, 148, 255, 0.8);
  --vscode-editorBracketHighlight-foreground1: #ffd700;
  --vscode-editorBracketHighlight-foreground2: #da70d6;
  --vscode-editorBracketHighlight-foreground3: #87cefa;
  --vscode-editorBracketHighlight-foreground4: rgba(0, 0, 0, 0);
  --vscode-editorBracketHighlight-foreground5: rgba(0, 0, 0, 0);
  --vscode-editorBracketHighlight-foreground6: rgba(0, 0, 0, 0);
  --vscode-editorBracketHighlight-unexpectedBracket\.foreground: #ff3232;
  --vscode-editorBracketPairGuide-background1: rgba(0, 0, 0, 0);
  --vscode-editorBracketPairGuide-background2: rgba(0, 0, 0, 0);
  --vscode-editorBracketPairGuide-background3: rgba(0, 0, 0, 0);
  --vscode-editorBracketPairGuide-background4: rgba(0, 0, 0, 0);
  --vscode-editorBracketPairGuide-background5: rgba(0, 0, 0, 0);
  --vscode-editorBracketPairGuide-background6: rgba(0, 0, 0, 0);
  --vscode-editorBracketPairGuide-activeBackground1: rgba(0, 0, 0, 0);
  --vscode-editorBracketPairGuide-activeBackground2: rgba(0, 0, 0, 0);
  --vscode-editorBracketPairGuide-activeBackground3: rgba(0, 0, 0, 0);
  --vscode-editorBracketPairGuide-activeBackground4: rgba(0, 0, 0, 0);
  --vscode-editorBracketPairGuide-activeBackground5: rgba(0, 0, 0, 0);
  --vscode-editorBracketPairGuide-activeBackground6: rgba(0, 0, 0, 0);
  --vscode-editorUnicodeHighlight-border: #ff0000;
  --vscode-editorUnicodeHighlight-background: rgba(0, 0, 0, 0);
  --vscode-editorHoverWidget-highlightForeground: #f38518;
  --vscode-editorOverviewRuler-bracketMatchForeground: #a0a0a0;
  --vscode-editorGutter-foldingControlForeground: #ffffff;
  --vscode-editor-linkedEditingBackground: rgba(255, 0, 0, 0.3);
  --vscode-editor-wordHighlightBorder: #f38518;
  --vscode-editor-wordHighlightStrongBorder: #f38518;
  --vscode-editorOverviewRuler-wordHighlightForeground: rgba(
    160,
    160,
    160,
    0.8
  );
  --vscode-editorOverviewRuler-wordHighlightStrongForeground: rgba(
    192,
    160,
    192,
    0.8
  );
  --vscode-peekViewTitleLabel-foreground: #ffffff;
  --vscode-peekViewTitleDescription-foreground: rgba(255, 255, 255, 0.6);
  --vscode-peekView-border: #6fc3df;
  --vscode-peekViewResult-background: #000000;
  --vscode-peekViewResult-lineForeground: #ffffff;
  --vscode-peekViewResult-fileForeground: #ffffff;
  --vscode-peekViewResult-selectionForeground: #ffffff;
  --vscode-peekViewEditor-background: #000000;
  --vscode-peekViewEditorGutter-background: #000000;
  --vscode-peekViewEditor-matchHighlightBorder: #f38518;
  --vscode-editorMarkerNavigationError-background: #6fc3df;
  --vscode-editorMarkerNavigationWarning-background: #6fc3df;
  --vscode-editorMarkerNavigationWarning-headerBackground: #0c141f;
  --vscode-editorMarkerNavigationInfo-background: #6fc3df;
  --vscode-editorMarkerNavigation-background: #000000;
  --vscode-editorSuggestWidget-background: #0c141f;
  --vscode-editorSuggestWidget-border: #6fc3df;
  --vscode-editorSuggestWidget-foreground: #ffffff;
  --vscode-editorSuggestWidget-highlightForeground: #f38518;
  --vscode-editorSuggestWidget-focusHighlightForeground: #f38518;
  --vscode-editorSuggestWidgetStatus-foreground: rgba(255, 255, 255, 0.5);
  --vscode-tab-activeBackground: #000000;
  --vscode-tab-unfocusedActiveBackground: #000000;
  --vscode-tab-activeForeground: #ffffff;
  --vscode-tab-inactiveForeground: #ffffff;
  --vscode-tab-unfocusedActiveForeground: #ffffff;
  --vscode-tab-unfocusedInactiveForeground: #ffffff;
  --vscode-tab-border: #6fc3df;
  --vscode-tab-lastPinnedBorder: #6fc3df;
  --vscode-tab-inactiveModifiedBorder: #ffffff;
  --vscode-tab-unfocusedActiveModifiedBorder: #ffffff;
  --vscode-tab-unfocusedInactiveModifiedBorder: #ffffff;
  --vscode-editorPane-background: #000000;
  --vscode-editorGroup-focusedEmptyBorder: #f38518;
  --vscode-editorGroupHeader-noTabsBackground: #000000;
  --vscode-editorGroupHeader-border: #6fc3df;
  --vscode-editorGroup-border: #6fc3df;
  --vscode-editorGroup-dropIntoPromptForeground: #ffffff;
  --vscode-editorGroup-dropIntoPromptBackground: #0c141f;
  --vscode-editorGroup-dropIntoPromptBorder: #6fc3df;
  --vscode-sideBySideEditor-horizontalBorder: #6fc3df;
  --vscode-sideBySideEditor-verticalBorder: #6fc3df;
  --vscode-panel-background: #000000;
  --vscode-panel-border: #6fc3df;
  --vscode-panelTitle-activeForeground: #ffffff;
  --vscode-panelTitle-inactiveForeground: #ffffff;
  --vscode-panelTitle-activeBorder: #6fc3df;
  --vscode-panelInput-border: #6fc3df;
  --vscode-panel-dropBorder: #ffffff;
  --vscode-panelSectionHeader-border: #6fc3df;
  --vscode-panelSection-border: #6fc3df;
  --vscode-banner-iconForeground: #3794ff;
  --vscode-statusBar-foreground: #ffffff;
  --vscode-statusBar-noFolderForeground: #ffffff;
  --vscode-statusBar-border: #6fc3df;
  --vscode-statusBar-noFolderBorder: #6fc3df;
  --vscode-statusBarItem-activeBackground: rgba(255, 255, 255, 0.18);
  --vscode-statusBarItem-hoverBackground: rgba(255, 255, 255, 0.12);
  --vscode-statusBarItem-compactHoverBackground: rgba(255, 255, 255, 0.2);
  --vscode-statusBarItem-prominentForeground: #ffffff;
  --vscode-statusBarItem-prominentBackground: rgba(0, 0, 0, 0.5);
  --vscode-statusBarItem-prominentHoverBackground: rgba(0, 0, 0, 0.3);
  --vscode-statusBarItem-errorForeground: #ffffff;
  --vscode-statusBarItem-warningForeground: #ffffff;
  --vscode-activityBar-background: #000000;
  --vscode-activityBar-foreground: #ffffff;
  --vscode-activityBar-inactiveForeground: #ffffff;
  --vscode-activityBar-border: #6fc3df;
  --vscode-activityBarBadge-background: #000000;
  --vscode-activityBarBadge-foreground: #ffffff;
  --vscode-activityBarItem-profilesForeground: #ffffff;
  --vscode-activityBarItem-profilesHoverForeground: #ffffff;
  --vscode-statusBarItem-remoteBackground: rgba(0, 0, 0, 0);
  --vscode-statusBarItem-remoteForeground: #ffffff;
  --vscode-extensionBadge-remoteBackground: #000000;
  --vscode-extensionBadge-remoteForeground: #ffffff;
  --vscode-sideBar-background: #000000;
  --vscode-sideBar-border: #6fc3df;
  --vscode-sideBarTitle-foreground: #ffffff;
  --vscode-sideBarSectionHeader-border: #6fc3df;
  --vscode-titleBar-activeForeground: #ffffff;
  --vscode-titleBar-activeBackground: #000000;
  --vscode-titleBar-border: #6fc3df;
  --vscode-menubar-selectionForeground: #ffffff;
  --vscode-menubar-selectionBorder: #f38518; /* Example of a var we'd use */
  --vscode-notificationCenter-border: #6fc3df;
  --vscode-notificationToast-border: #6fc3df;
  --vscode-notifications-foreground: #ffffff;
  --vscode-notifications-background: #0c141f;
  --vscode-notificationLink-foreground: #3794ff;
  --vscode-notificationCenterHeader-background: #0c141f;
  --vscode-notifications-border: #0c141f;
  --vscode-notificationsErrorIcon-foreground: #f48771;
  --vscode-notificationsWarningIcon-foreground: #ff0000;
  --vscode-notificationsInfoIcon-foreground: #3794ff;
  --vscode-window-activeBorder: #6fc3df;
  --vscode-window-inactiveBorder: #6fc3df;
  --vscode-commandCenter-foreground: #ffffff;
  --vscode-commandCenter-activeForeground: #ffffff;
  --vscode-commandCenter-border: rgba(255, 255, 255, 0.6);
  --vscode-commandCenter-activeBorder: #ffffff;
  --vscode-editorCommentsWidget-resolvedBorder: #6fc3df;
  --vscode-editorCommentsWidget-unresolvedBorder: #6fc3df;
  --vscode-editorCommentsWidget-rangeBackground: rgba(111, 195, 223, 0.1);
  --vscode-editorCommentsWidget-rangeBorder: rgba(111, 195, 223, 0.4);
  --vscode-editorCommentsWidget-rangeActiveBackground: rgba(111, 195, 223, 0.1);
  --vscode-editorCommentsWidget-rangeActiveBorder: rgba(111, 195, 223, 0.4);
  --vscode-editorGutter-commentRangeForeground: #ffffff;
  --vscode-debugToolBar-background: #000000;
  --vscode-debugIcon-startForeground: #89d185;
  --vscode-editor-stackFrameHighlightBackground: rgba(255, 255, 0, 0.2);
  --vscode-editor-focusedStackFrameHighlightBackground: rgba(
    122,
    189,
    122,
    0.3
  );
  --vscode-mergeEditor-change\.background: rgba(155, 185, 85, 0.2);
  --vscode-mergeEditor-change\.word\.background: rgba(156, 204, 44, 0.2);
  --vscode-mergeEditor-changeBase\.background: #4b1818;
  --vscode-mergeEditor-changeBase\.word\.background: #6f1313;
  --vscode-mergeEditor-conflict\.unhandledUnfocused\.border: rgba(
    255,
    166,
    0,
    0.48
  );
  --vscode-mergeEditor-conflict\.unhandledFocused\.border: #ffa600;
  --vscode-mergeEditor-conflict\.handledUnfocused\.border: rgba(
    134,
    134,
    134,
    0.29
  );
  --vscode-mergeEditor-conflict\.handledFocused\.border: rgba(
    193,
    193,
    193,
    0.8
  );
  --vscode-mergeEditor-conflict\.handled\.minimapOverViewRuler: rgba(
    173,
    172,
    168,
    0.93
  );
  --vscode-mergeEditor-conflict\.unhandled\.minimapOverViewRuler: #fcba03;
  --vscode-mergeEditor-conflictingLines\.background: rgba(255, 234, 0, 0.28);
  --vscode-settings-headerForeground: #ffffff;
  --vscode-settings-modifiedItemIndicator: #00497a;
  --vscode-settings-headerBorder: #6fc3df;
  --vscode-settings-sashBorder: #6fc3df;
  --vscode-settings-dropdownBackground: #000000;
  --vscode-settings-dropdownForeground: #ffffff;
  --vscode-settings-dropdownBorder: #6fc3df;
  --vscode-settings-dropdownListBorder: #6fc3df;
  --vscode-settings-checkboxBackground: #000000;
  --vscode-settings-checkboxForeground: #ffffff;
  --vscode-settings-checkboxBorder: #6fc3df;
  --vscode-settings-textInputBackground: #000000;
  --vscode-settings-textInputForeground: #ffffff;
  --vscode-settings-textInputBorder: #6fc3df;
  --vscode-settings-numberInputBackground: #000000;
  --vscode-settings-numberInputForeground: #ffffff;
  --vscode-settings-numberInputBorder: #6fc3df;
  --vscode-settings-focusedRowBorder: #f38518;
  --vscode-terminal-foreground: #ffffff;
  --vscode-terminal-selectionBackground: #ffffff;
  --vscode-terminal-inactiveSelectionBackground: rgba(255, 255, 255, 0.7);
  --vscode-terminal-selectionForeground: #000000;
  --vscode-terminalCommandDecoration-defaultBackground: rgba(
    255,
    255,
    255,
    0.5
  );
  --vscode-terminalCommandDecoration-successBackground: #1b81a8;
  --vscode-terminalCommandDecoration-errorBackground: #f14c4c;
  --vscode-terminalOverviewRuler-cursorForeground: rgba(160, 160, 160, 0.8);
  --vscode-terminal-border: #6fc3df;
  --vscode-terminal-findMatchBorder: #f38518;
  --vscode-terminal-findMatchHighlightBorder: #f38518;
  --vscode-terminalOverviewRuler-findMatchForeground: #f38518;
  --vscode-testing-iconFailed: #f14c4c;
  --vscode-testing-iconErrored: #f14c4c;
  --vscode-testing-iconPassed: #73c991;
  --vscode-testing-runAction: #73c991;
  --vscode-testing-iconQueued: #cca700;
  --vscode-testing-iconUnset: #848484;
  --vscode-testing-iconSkipped: #848484;
  --vscode-testing-peekBorder: #6fc3df;
  --vscode-testing-message\.error\.decorationForeground: #ffffff;
  --vscode-testing-message\.info\.decorationForeground: rgba(
    255,
    255,
    255,
    0.5
  );
  --vscode-welcomePage-tileBackground: #000000;
  --vscode-welcomePage-tileBorder: #6fc3df;
  --vscode-welcomePage-progress\.background: #000000;
  --vscode-welcomePage-progress\.foreground: #3794ff;
  --vscode-debugExceptionWidget-border: #a31515;
  --vscode-debugExceptionWidget-background: #420b0d;
  --vscode-ports-iconRunningProcessForeground: #ffffff;
  --vscode-statusBar-debuggingBackground: #ba592c;
  --vscode-statusBar-debuggingForeground: #ffffff;
  --vscode-statusBar-debuggingBorder: #6fc3df;
  --vscode-editor-inlineValuesForeground: rgba(255, 255, 255, 0.5);
  --vscode-editor-inlineValuesBackground: rgba(255, 200, 0, 0.2);
  --vscode-editorGutter-modifiedBackground: #1b81a8;
  --vscode-editorGutter-addedBackground: #487e02;
  --vscode-editorGutter-deletedBackground: #f48771;
  --vscode-minimapGutter-modifiedBackground: #1b81a8;
  --vscode-minimapGutter-addedBackground: #487e02;
  --vscode-minimapGutter-deletedBackground: #f48771;
  --vscode-editorOverviewRuler-modifiedForeground: rgba(27, 129, 168, 0.6);
  --vscode-editorOverviewRuler-addedForeground: rgba(72, 126, 2, 0.6);
  --vscode-editorOverviewRuler-deletedForeground: rgba(244, 135, 113, 0.6);
  --vscode-debugIcon-breakpointForeground: #e51400;
  --vscode-debugIcon-breakpointDisabledForeground: #848484;
  --vscode-debugIcon-breakpointUnverifiedForeground: #848484;
  --vscode-debugIcon-breakpointCurrentStackframeForeground: #ffcc00;
  --vscode-debugIcon-breakpointStackframeForeground: #89d185;
  --vscode-notebook-cellBorderColor: #6fc3df;
  --vscode-notebook-focusedEditorBorder: #f38518;
  --vscode-notebookStatusSuccessIcon-foreground: #89d185;
  --vscode-notebookStatusErrorIcon-foreground: #f48771;
  --vscode-notebookStatusRunningIcon-foreground: #ffffff;
  --vscode-notebook-cellToolbarSeparator: #6fc3df;
  --vscode-notebook-selectedCellBorder: #6fc3df;
  --vscode-notebook-inactiveSelectedCellBorder: #f38518;
  --vscode-notebook-focusedCellBorder: #f38518;
  --vscode-notebook-inactiveFocusedCellBorder: #6fc3df;
  --vscode-notebook-cellStatusBarItemHoverBackground: rgba(255, 255, 255, 0.15);
  --vscode-notebook-cellInsertionIndicator: #f38518;
  --vscode-notebookScrollbarSlider-background: rgba(111, 195, 223, 0.6);
  --vscode-notebookScrollbarSlider-hoverBackground: rgba(111, 195, 223, 0.8);
  --vscode-notebookScrollbarSlider-activeBackground: #6fc3df;
  --vscode-scm-providerBorder: #6fc3df;
  --vscode-searchEditor-textInputBorder: #6fc3df;
  --vscode-debugTokenExpression-name: #ffffff;
  --vscode-debugTokenExpression-value: #ffffff;
  --vscode-debugTokenExpression-string: #f48771;
  --vscode-debugTokenExpression-boolean: #75bdfe;
  --vscode-debugTokenExpression-number: #89d185;
  --vscode-debugTokenExpression-error: #f48771;
  --vscode-debugView-exceptionLabelForeground: #ffffff;
  --vscode-debugView-exceptionLabelBackground: #6c2022;
  --vscode-debugView-stateLabelForeground: #ffffff;
  --vscode-debugView-stateLabelBackground: rgba(136, 136, 136, 0.27);
  --vscode-debugView-valueChangedHighlight: #569cd6;
  --vscode-debugConsole-infoForeground: #ffffff;
  --vscode-debugConsole-warningForeground: #008000;
  --vscode-debugConsole-errorForeground: #f48771;
  --vscode-debugConsole-sourceForeground: #ffffff;
  --vscode-debugConsoleInputIcon-foreground: #ffffff;
  --vscode-debugIcon-pauseForeground: #75beff;
  --vscode-debugIcon-stopForeground: #f48771;
  --vscode-debugIcon-disconnectForeground: #f48771;
  --vscode-debugIcon-restartForeground: #89d185;
  --vscode-debugIcon-stepOverForeground: #75beff;
  --vscode-debugIcon-stepIntoForeground: #75beff;
  --vscode-debugIcon-stepOutForeground: #75beff;
  --vscode-debugIcon-continueForeground: #75beff;
  --vscode-debugIcon-stepBackForeground: #75beff;
  --vscode-extensionButton-separator: rgba(255, 255, 255, 0.4);
  --vscode-extensionIcon-starForeground: #ff8e00;
  --vscode-extensionIcon-verifiedForeground: #3794ff;
  --vscode-extensionIcon-preReleaseForeground: #1d9271;
  --vscode-terminal-ansiBlack: #000000;
  --vscode-terminal-ansiRed: #cd0000;
  --vscode-terminal-ansiGreen: #00cd00;
  --vscode-terminal-ansiYellow: #cdcd00;
  --vscode-terminal-ansiBlue: #0000ee;
  --vscode-terminal-ansiMagenta: #cd00cd;
  --vscode-terminal-ansiCyan: #00cdcd;
  --vscode-terminal-ansiWhite: #e5e5e5;
  --vscode-terminal-ansiBrightBlack: #7f7f7f;
  --vscode-terminal-ansiBrightRed: #ff0000;
  --vscode-terminal-ansiBrightGreen: #00ff00;
  --vscode-terminal-ansiBrightYellow: #ffff00;
  --vscode-terminal-ansiBrightBlue: #5c5cff;
  --vscode-terminal-ansiBrightMagenta: #ff00ff;
  --vscode-terminal-ansiBrightCyan: #00ffff;
  --vscode-terminal-ansiBrightWhite: #ffffff;
  --vscode-interactive-activeCodeBorder: #6fc3df;
  --vscode-interactive-inactiveCodeBorder: #6fc3df;
  --vscode-gitDecoration-addedResourceForeground: #a1e3ad;
  --vscode-gitDecoration-modifiedResourceForeground: #e2c08d;
  --vscode-gitDecoration-deletedResourceForeground: #c74e39;
  --vscode-gitDecoration-renamedResourceForeground: #73c991;
  --vscode-gitDecoration-untrackedResourceForeground: #73c991;
  --vscode-gitDecoration-ignoredResourceForeground: #a7a8a9;
  --vscode-gitDecoration-stageModifiedResourceForeground: #e2c08d;
  --vscode-gitDecoration-stageDeletedResourceForeground: #c74e39;
  --vscode-gitDecoration-conflictingResourceForeground: #c74e39;
  --vscode-gitDecoration-submoduleResourceForeground: #8db9e2;
  --vscode-testExplorer-errorDecorationBackground: #000000;
}

/**
 * This is copied in the same way, but from the <body> element
 */
body {
  background-color: transparent;
  color: var(--vscode-editor-foreground);
  font-family: var(--vscode-font-family);
  font-weight: var(--vscode-font-weight);
  font-size: var(--vscode-font-size);
  margin: 0;
  padding: 0 20px;
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
    #     if "gradient" in var_value: # Print examples of gradients if any
    #         print(f"{var_name}: {var_value}")

    print(
        f"\n--- Extracted Unique Colors (Total: {len(extracted_metadata['unique_colors'])}) ---"
    )
    # for color in extracted_metadata["unique_colors"]:
    #     print(color)

    # Example test for gradient conversion
    # print("\n--- Gradient Conversion Test ---")
    # test_gradients = [
    #     "linear-gradient(to top right, #ff0000 0%, blue 100%)",
    #     "linear-gradient(90deg, red, yellow 50%, #0000ff)",
    #     "linear-gradient(red, blue)",
    #     "linear-gradient(45deg, #f00, #00f)",
    #     "linear-gradient(to bottom, red 20%, yellow 50%, green 80%)",
    #     "linear-gradient(rgba(255,0,0,0.5), transparent)",
    #     "linear-gradient(red)"
    # ]
    # for css_grad_str in test_gradients:
    #     args_str = css_grad_str.split("(",1)[1].rsplit(")",1)[0]
    #     parsed_grad_args = tinycss2.parse_component_value_list(args_str)
    #     qss_grad = _parse_css_linear_gradient_to_qss(parsed_grad_args)
    #     print(f"CSS: {css_grad_str} -> QSS: {qss_grad}")
