import sys

from PyQt5.QtCore import QEvent, Qt
from PyQt5.QtGui import (
    QColor,
    QCursor,
    QFont,
    QIcon,
    QKeyEvent,
    QKeySequence,
    QPalette,
    QPixmap,
)
from PyQt5.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QShortcut,
    QSizePolicy,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class ObjectInspector(QWidget):
    """
    Rudimentary Qt object inspector.
    Automatically inspects widgets on hover without stealing focus.
    Presents inspection data in a two-column table with copy capability.
    Includes deep metadata: style engine, cursor, autofill, focus, dynamic properties, palette, actions.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # Always on top as a tool window, but does not grab focus
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

        # Flag to track if updates are suspended
        self.updates_suspended = False

        # Install event filter for hover events
        app = QApplication.instance()
        app.installEventFilter(self)

        # Shortcut F7 to select parent
        sch = QShortcut(QKeySequence(Qt.Key_F7), self)
        sch.setContext(Qt.ApplicationShortcut)
        sch.activated.connect(self.select_parent)

        self.selected_widget = None

        self._create_ui()
        self._set_table_style()

        # Enable key tracking
        self.setFocusPolicy(Qt.StrongFocus)

    def _create_ui(self):
        self.setWindowTitle("Object Inspector")

        # Buttons
        self.btn_select_parent = QPushButton("Select parent", self)
        self.btn_select_parent.released.connect(self.select_parent)

        self.btn_copy = QPushButton("Copy", self)
        self.btn_copy.released.connect(self.copy_to_clipboard)

        # Help label
        self.lbl_help = QLabel(
            "Hover over any widget to inspect it; press F7 to select its parent.",
            self,
        )

        spacer = QWidget(self)
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        # Top controls layout
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(2, 2, 2, 2)
        top_layout.setSpacing(4)
        top_layout.addWidget(self.btn_select_parent)
        top_layout.addWidget(self.btn_copy)
        top_layout.addWidget(self.lbl_help)
        top_layout.addWidget(spacer)

        # Inspection table
        self.tbl_inspection = QTableWidget(self)
        self.tbl_inspection.setColumnCount(2)
        self.tbl_inspection.setHorizontalHeaderLabels(["Property", "Value"])
        self.tbl_inspection.horizontalHeader().setStretchLastSection(True)
        self.tbl_inspection.verticalHeader().setVisible(False)
        self.tbl_inspection.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tbl_inspection.setSelectionMode(QTableWidget.NoSelection)
        self.tbl_inspection.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Status bar
        self.status_bar = QStatusBar(self)
        self.status_bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.status_bar.showMessage("Hold Ctrl OR Shift to suspend updates")

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(6)
        main_layout.addLayout(top_layout)
        main_layout.addWidget(self.tbl_inspection)
        main_layout.addWidget(self.status_bar)
        self.setLayout(main_layout)

    def _set_table_style(self):
        font = QFont("Monospace")
        font.setStyleHint(QFont.TypeWriter)
        self.tbl_inspection.setFont(font)

    def _update_suspended_state(self):
        """Check and update the suspended state based on modifier keys."""
        modifiers = QApplication.keyboardModifiers()
        was_suspended = self.updates_suspended
        self.updates_suspended = bool(
            modifiers & Qt.ControlModifier or modifiers & Qt.ShiftModifier
        )

        if self.updates_suspended != was_suspended:
            if self.updates_suspended:
                self.status_bar.showMessage("Updates suspended")
            else:
                self.status_bar.showMessage("Hold Ctrl OR Shift to suspend updates")

        return self.updates_suspended

    def eventFilter(self, obj, event):
        # Check if modifiers changed on any event
        if event.type() in (QEvent.KeyPress, QEvent.KeyRelease):
            self._update_suspended_state()

        # Handle Enter events for widget inspection
        elif event.type() == QEvent.Enter and isinstance(obj, QWidget):
            if obj is self or self.isAncestorOf(obj):
                return super().eventFilter(obj, event)

            # Check keyboard modifiers
            if not self._update_suspended_state() and obj is not self:
                self._inspect_widget(obj)

        return super().eventFilter(obj, event)

    def select_parent(self):
        if not self.selected_widget:
            return
        parent = self.selected_widget.parent()
        if parent and parent.inherits("QWidget"):
            self._inspect_widget(parent)

    def _get_specific_css_selector(self, widget):
        """Generate the most specific CSS selector for a widget."""
        widget_type = widget.metaObject().className()
        object_name = widget.objectName()

        if object_name:
            return f'{widget_type}[objectName="{object_name}"]'
        else:
            return widget_type

    def _get_css_selector_with_parent(self, widget):
        """Generate a CSS selector that includes the immediate parent."""
        if not widget.parent():
            return self._get_specific_css_selector(widget)

        parent_selector = self._get_specific_css_selector(widget.parent())
        widget_selector = self._get_specific_css_selector(widget)
        return f"{parent_selector} > {widget_selector}"

    def _get_full_hierarchy_css_selector(self, widget):
        """Generate a CSS selector with the full widget hierarchy from root to widget."""
        selectors = []
        current = widget

        while current:
            selectors.insert(0, self._get_specific_css_selector(current))
            current = current.parent()

        return " > ".join(selectors)

    def _add_css_selector_hierarchy(self, widget, properties):
        """Add CSS selectors for the widget and all its parents to the properties."""
        # Add the most specific selector for this widget
        properties.append(
            ("CSS Selector (Specific)", self._get_specific_css_selector(widget))
        )

        # Build a list of all ancestors
        ancestors = []
        current = widget
        while current.parent():
            ancestors.insert(0, current.parent())
            current = current.parent()

        # Add a selector for each level of the hierarchy
        if ancestors:
            # First, add the immediate parent relationship
            properties.append(
                (
                    "CSS Selector (With Parent)",
                    self._get_css_selector_with_parent(widget),
                )
            )

            # Then add the full hierarchy selector
            properties.append(
                (
                    "CSS Selector (Full Hierarchy)",
                    self._get_full_hierarchy_css_selector(widget),
                )
            )

            # Add intermediate levels if there are more than one parent
            if len(ancestors) > 1:
                # Start building from the root
                path_selectors = []
                for i, ancestor in enumerate(ancestors):
                    path_selectors.append(self._get_specific_css_selector(ancestor))
                    # Skip the immediate parent (already covered) and full hierarchy (already covered)
                    if 0 < i < len(ancestors) - 1:
                        path_selectors_copy = path_selectors.copy()
                        path_selectors_copy.append(
                            self._get_specific_css_selector(widget)
                        )
                        properties.append(
                            (
                                f"CSS Selector (With {i+1} Parents)",
                                " > ".join(path_selectors_copy),
                            )
                        )

    def _inspect_widget(self, widget):
        # Disconnect previous destroyed signal
        if self.selected_widget is not None:
            try:
                self.selected_widget.destroyed.disconnect(self.on_widget_destroyed)
            except TypeError:
                pass

        self.selected_widget = widget
        properties = []

        # Screen info
        screen = QApplication.primaryScreen()
        res = screen.size()
        phy = screen.physicalSize()
        dpi = screen.logicalDotsPerInch()
        properties += [
            ("Screen Resolution", f"{res.width()}×{res.height()} px"),
            ("Physical Size", f"{phy.width()}×{phy.height()} mm"),
            ("DPI", f"{dpi:.1f}"),
        ]

        if widget:
            # Basic info
            properties += [
                ("Type", widget.metaObject().className()),
                ("Name", widget.objectName() or "<none>"),
                ("Children Count", str(len(widget.children()))),
            ]

            # Add CSS selectors
            self._add_css_selector_hierarchy(widget, properties)

            # Parent info
            parent = widget.parent()
            properties += [
                (
                    "Parent Type",
                    parent.metaObject().className() if parent else "<none>",
                ),
                (
                    "Parent Name",
                    parent.objectName() if parent and parent.objectName() else "<none>",
                ),
            ]
            # Pseudo states
            properties += [
                ("Enabled", str(widget.isEnabled())),
                ("Visible", str(widget.isVisible())),
                ("Under Mouse", str(widget.underMouse())),
                ("Has Focus", str(widget.hasFocus())),
            ]
            # Style engine
            properties.append(("Style Engine", widget.style().metaObject().className()))
            # Cursor
            properties.append(("Cursor Shape", str(widget.cursor().shape())))
            # Auto fill background
            properties.append(("AutoFillBackground", str(widget.autoFillBackground())))
            # Focus policy
            properties.append(("Focus Policy", str(widget.focusPolicy())))
            # Font
            font = widget.font()
            properties.append(
                (
                    "Font",
                    f"family={font.family()}, size={font.pointSize()}, "
                    f"weight={font.weight()}, italic={font.italic()}",
                )
            )
            # Geometry
            geom = widget.geometry()
            properties.append(
                (
                    "Geometry",
                    f"x={geom.x()}, y={geom.y()}, width={geom.width()}, height={geom.height()}",
                )
            )
            # Layout margins
            layout = widget.layout()
            if layout:
                m = layout.contentsMargins()
                properties.append(
                    (
                        "Layout Margins",
                        f"left={m.left()}, top={m.top()}, right={m.right()}, bottom={m.bottom()}",
                    )
                )
            else:
                properties.append(("Layout Margins", "<no layout>"))
            # Style sheet
            properties.append(("StyleSheet", widget.styleSheet() or "<none>"))
            # Dynamic properties
            dp = [name.data().decode() for name in widget.dynamicPropertyNames()]
            properties.append(("Dynamic Properties", ", ".join(dp) or "<none>"))
            # Palette colors
            pal = widget.palette()
            roles = {
                "Window": QPalette.Window,
                "WindowText": QPalette.WindowText,
                "Base": QPalette.Base,
                "Text": QPalette.Text,
                "Button": QPalette.Button,
                "ButtonText": QPalette.ButtonText,
                "Highlight": QPalette.Highlight,
                "HighlightedText": QPalette.HighlightedText,
            }
            for name, role in roles.items():
                color = pal.color(role).name()
                properties.append((f"Palette.{name}", color))
            # Shortcuts
            shortcuts = widget.findChildren(QShortcut)
            sc_list = [sc.key().toString() for sc in shortcuts]
            properties.append(("Shortcuts", ", ".join(sc_list) or "<none>"))
            # Actions
            actions = widget.actions()
            act_list = [
                f"{act.text()} ({act.shortcut().toString()})" for act in actions
            ]
            properties.append(("Actions", "; ".join(act_list) or "<none>"))
            # Paint engine
            engine = widget.paintEngine()
            properties.append(
                ("Paint Engine", engine.__class__.__name__ if engine else "<none>")
            )
        else:
            properties.append(("<no widget>", ""))

        # Populate table with icons for palette colors
        self.tbl_inspection.setRowCount(len(properties))
        for row, (prop, val) in enumerate(properties):
            key_item = QTableWidgetItem(prop)
            val_item = QTableWidgetItem(val)
            if prop.startswith("Palette."):
                pix = QPixmap(16, 16)
                pix.fill(QColor(val))
                val_item.setIcon(QIcon(pix))
            self.tbl_inspection.setItem(row, 0, key_item)
            self.tbl_inspection.setItem(row, 1, val_item)

        widget.destroyed.connect(self.on_widget_destroyed)

    def copy_to_clipboard(self):
        if not self.selected_widget:
            return
        rows = self.tbl_inspection.rowCount()
        lines = []
        for row in range(rows):
            prop = self.tbl_inspection.item(row, 0).text()
            val = self.tbl_inspection.item(row, 1).text()
            lines.append(f"{prop}: {val}")
        QApplication.clipboard().setText("\n".join(lines))

    def on_widget_destroyed(self, _):
        self.selected_widget = None


# In IDA, QApplication is already running
if __name__ == "__main__":
    inspector = ObjectInspector()
    inspector.show()
