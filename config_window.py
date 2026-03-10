#!/usr/bin/env python3
"""Razer Lighting Configuration Window — PyQt5-based effect configurator with live preview."""

import importlib.util
import os
import shutil
import sys
import tempfile
import threading
import time
from functools import partial

from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QSettings, QSize
from PyQt5.QtGui import QColor, QPainter, QPen, QBrush, QFont, QFontMetrics, QPalette
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QComboBox, QLabel, QPushButton, QSlider, QSpinBox,
    QDoubleSpinBox, QCheckBox, QScrollArea, QGroupBox, QColorDialog,
    QMessageBox, QSizePolicy, QFrame, QGridLayout, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView,
)

from config_parser import (
    parse_config, write_config, write_temp_config, get_config_path_for_effect,
    load_defaults, save_defaults, humanize_name, group_params, ConfigParam,
    _format_value,
)
from virtual_device import VirtualDevice, detect_dimensions

EFFECTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "effects")
TEMP_DIR = "/tmp/razer-lighting-preview"
SETTINGS_ORG = "RazerLighting"
SETTINGS_APP = "ConfigWindow"

# Razer Blade 14 2021 keyboard layout (from Polychromatic SVG / OpenRazer matrix)
#
# Standard key:   (label, matrix_col, width)
# Row override:   (label, matrix_col, width, matrix_row)
# Half-height:    (label, matrix_col, width, matrix_row, height, y_offset)
# No-advance:     (label, matrix_col, width, matrix_row, height, y_offset, 0)
# Spacer (gap):   (None, -1, width)   — advances x, draws nothing
#
# Column 0 is unused (legacy macro key position). Physical keys use cols 1–15.
# The spacebar has no LED on this model.
# ↑ (col 13) and ↓ (col 15) are half-height keys stacked in the same cell.
KEYBOARD_LAYOUT = [
    # Row 0: Function row (15 keys, all 1u)
    [("Esc", 1, 1.0), ("F1", 2, 1.0), ("F2", 3, 1.0), ("F3", 4, 1.0), ("F4", 5, 1.0),
     ("F5", 6, 1.0), ("F6", 7, 1.0), ("F7", 8, 1.0), ("F8", 9, 1.0), ("F9", 10, 1.0),
     ("F10", 11, 1.0), ("F11", 12, 1.0), ("F12", 13, 1.0), ("Ins", 14, 1.0),
     ("Del", 15, 1.0)],
    # Row 1: Number row (14 keys)
    [("`", 1, 1.0), ("1", 2, 1.0), ("2", 3, 1.0), ("3", 4, 1.0), ("4", 5, 1.0),
     ("5", 6, 1.0), ("6", 7, 1.0), ("7", 8, 1.0), ("8", 9, 1.0), ("9", 10, 1.0),
     ("0", 11, 1.0), ("-", 12, 1.0), ("=", 13, 1.0), ("Bksp", 15, 2.0)],
    # Row 2: QWERTY top (14 keys)
    [("Tab", 1, 1.5), ("Q", 2, 1.0), ("W", 3, 1.0), ("E", 4, 1.0), ("R", 5, 1.0),
     ("T", 6, 1.0), ("Y", 7, 1.0), ("U", 8, 1.0), ("I", 9, 1.0), ("O", 10, 1.0),
     ("P", 11, 1.0), ("[", 12, 1.0), ("]", 13, 1.0), ("\\", 15, 1.5)],
    # Row 3: Home row (13 keys)
    [("Caps", 1, 1.75), ("A", 2, 1.0), ("S", 3, 1.0), ("D", 4, 1.0), ("F", 5, 1.0),
     ("G", 6, 1.0), ("H", 7, 1.0), ("J", 8, 1.0), ("K", 9, 1.0), ("L", 10, 1.0),
     (";", 11, 1.0), ("'", 12, 1.0), ("Enter", 15, 2.25)],
    # Row 4: Shift row (12 keys — RShift extends to right edge)
    [("Shift", 1, 2.0), ("Z", 3, 1.0), ("X", 4, 1.0), ("C", 5, 1.0), ("V", 6, 1.0),
     ("B", 7, 1.0), ("N", 8, 1.0), ("M", 9, 1.0), (",", 10, 1.0), (".", 11, 1.0),
     ("/", 12, 1.0), ("Shift", 15, 3.0)],
    # Row 5: Bottom row (no spacebar LED; ↑/↓ half-height stacked)
    [("Ctrl", 1, 1.0), ("Fn", 2, 1.0), ("Super", 3, 1.0), ("Alt", 5, 1.0),
     (None, -1, 5.0),
     ("Alt", 9, 1.0), ("Fn", 10, 1.0), ("Ctrl", 11, 1.0),
     ("\u2190", 12, 1.0),
     ("\u2191", 13, 1.0, 5, 0.46, 0.0, 0.0),
     ("\u2193", 15, 1.0, 5, 0.46, 0.54),
     ("\u2192", 14, 1.0)],
]


# ─── Dark Theme ───────────────────────────────────────────────────────────────

DARK_STYLESHEET = """
QMainWindow, QWidget {
    background-color: #1a1a1a;
    color: #e0e0e0;
}
QLabel {
    color: #cccccc;
    font-size: 12px;
}
QComboBox {
    background-color: #2d2d2d;
    border: 1px solid #3d3d3d;
    border-radius: 3px;
    padding: 5px 10px;
    color: #e0e0e0;
    font-size: 13px;
    min-height: 24px;
}
QComboBox:hover { border-color: #00cc00; }
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #00cc00;
    margin-right: 8px;
}
QComboBox QAbstractItemView {
    background-color: #2d2d2d;
    color: #e0e0e0;
    selection-background-color: #004d00;
    selection-color: #00ff00;
    border: 1px solid #3d3d3d;
}
QSpinBox, QDoubleSpinBox {
    background-color: #2d2d2d;
    border: 1px solid #3d3d3d;
    border-radius: 3px;
    padding: 2px 4px;
    color: #e0e0e0;
    font-size: 12px;
}
QSpinBox:hover, QDoubleSpinBox:hover { border-color: #00cc00; }
QSpinBox::up-button, QDoubleSpinBox::up-button,
QSpinBox::down-button, QDoubleSpinBox::down-button {
    background-color: #333333;
    border: none;
    width: 16px;
}
QSlider::groove:horizontal {
    height: 6px;
    background: #2d2d2d;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #00cc00;
    width: 16px;
    margin: -5px 0;
    border-radius: 8px;
}
QSlider::sub-page:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #004d00, stop:1 #00cc00);
    border-radius: 3px;
}
QPushButton {
    background-color: #2d2d2d;
    border: 1px solid #3d3d3d;
    border-radius: 4px;
    padding: 6px 16px;
    color: #e0e0e0;
    font-size: 12px;
}
QPushButton:hover {
    border-color: #00cc00;
    background-color: #333333;
}
QPushButton:pressed { background-color: #004d00; }
QPushButton#saveButton {
    background-color: #003300;
    border-color: #00cc00;
    color: #00ff00;
    font-weight: bold;
}
QPushButton#saveButton:hover { background-color: #004d00; }
QGroupBox {
    border: 1px solid #333333;
    border-radius: 4px;
    margin-top: 8px;
    padding: 24px 8px 8px 8px;
    font-weight: bold;
    font-size: 12px;
    color: #00cc00;
}
QGroupBox::title {
    subcontrol-origin: padding;
    subcontrol-position: top left;
    left: 8px;
    top: 4px;
    padding: 0 4px;
}
QScrollArea { border: none; }
QScrollBar:vertical {
    background: #1a1a1a;
    width: 10px;
    border: none;
}
QScrollBar::handle:vertical {
    background: #3d3d3d;
    border-radius: 5px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover { background: #00cc00; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal {
    background: #1a1a1a;
    height: 10px;
    border: none;
}
QScrollBar::handle:horizontal {
    background: #3d3d3d;
    border-radius: 5px;
    min-width: 30px;
}
QScrollBar::handle:horizontal:hover { background: #00cc00; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
QCheckBox {
    spacing: 8px;
    font-size: 12px;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 3px;
    border: 1px solid #3d3d3d;
    background-color: #2d2d2d;
}
QCheckBox::indicator:checked {
    background-color: #00cc00;
    border-color: #00ff00;
}
QCheckBox::indicator:hover { border-color: #00cc00; }
QTableWidget {
    background-color: #2d2d2d;
    color: #e0e0e0;
    border: 1px solid #3d3d3d;
    gridline-color: #333333;
    font-size: 12px;
}
QTableWidget::item:selected {
    background-color: #004d00;
    color: #00ff00;
}
QHeaderView::section {
    background-color: #252525;
    color: #aaaaaa;
    border: 1px solid #333333;
    padding: 4px;
    font-size: 11px;
}
QSplitter::handle { background-color: #333333; }
QSplitter::handle:hover { background-color: #00cc00; }
"""


# ─── Effect Discovery (mirrors razer_lighting.py) ────────────────────────────

def discover_effects():
    """Find all effect modules in the effects directory."""
    effects = {}
    for filename in sorted(os.listdir(EFFECTS_DIR)):
        if filename.endswith("_config.py") or filename.startswith("__"):
            continue
        if not filename.endswith(".py"):
            continue
        path = os.path.join(EFFECTS_DIR, filename)
        try:
            spec = importlib.util.spec_from_file_location(filename[:-3], path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if hasattr(module, "run"):
                name = getattr(module, "EFFECT_NAME", filename[:-3].replace("_", " ").title())
                effects[name] = module
        except Exception as e:
            print(f"Skipping {filename}: {e}", file=sys.stderr)
    return effects


# ─── Parameter Widgets ────────────────────────────────────────────────────────

class IntParamWidget(QWidget):
    value_changed = pyqtSignal()

    def __init__(self, param):
        super().__init__()
        self.param = param
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)

        label = QLabel(humanize_name(param.name))
        label.setFixedWidth(120)
        label.setToolTip(param.tooltip)
        layout.addWidget(label)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(int(param.range_min))
        self.slider.setMaximum(int(param.range_max))
        self.slider.setSingleStep(int(param.range_step))
        self.slider.setValue(int(param.value))
        layout.addWidget(self.slider, 1)

        self.spin = QSpinBox()
        self.spin.setMinimum(int(param.range_min))
        self.spin.setMaximum(int(param.range_max))
        self.spin.setSingleStep(int(param.range_step))
        self.spin.setValue(int(param.value))
        self.spin.setFixedWidth(65)
        layout.addWidget(self.spin)

        self.slider.valueChanged.connect(self.spin.setValue)
        self.spin.valueChanged.connect(self.slider.setValue)
        self.spin.valueChanged.connect(lambda: self.value_changed.emit())

    def get_value(self):
        return self.spin.value()

    def set_value(self, val):
        self.spin.blockSignals(True)
        self.slider.blockSignals(True)
        self.spin.setValue(int(val))
        self.slider.setValue(int(val))
        self.spin.blockSignals(False)
        self.slider.blockSignals(False)


class FloatParamWidget(QWidget):
    value_changed = pyqtSignal()

    SLIDER_STEPS = 10000

    def __init__(self, param):
        super().__init__()
        self.param = param
        self._fmin = param.range_min
        self._fmax = param.range_max
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)

        label = QLabel(humanize_name(param.name))
        label.setFixedWidth(120)
        label.setToolTip(param.tooltip)
        layout.addWidget(label)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(self.SLIDER_STEPS)
        self.slider.setValue(self._to_slider(param.value))
        layout.addWidget(self.slider, 1)

        # Determine decimal places from step size
        decimals = max(1, min(6, len(str(param.range_step).rstrip('0').split('.')[-1]))) if param.range_step < 1 else 2
        self.spin = QDoubleSpinBox()
        self.spin.setDecimals(decimals)
        self.spin.setMinimum(param.range_min)
        self.spin.setMaximum(param.range_max)
        self.spin.setSingleStep(param.range_step)
        self.spin.setValue(param.value)
        self.spin.setFixedWidth(75)
        layout.addWidget(self.spin)

        self.slider.valueChanged.connect(self._slider_to_spin)
        self.spin.valueChanged.connect(self._spin_to_slider)
        self.spin.valueChanged.connect(lambda: self.value_changed.emit())

    def _to_slider(self, fval):
        if self._fmax == self._fmin:
            return 0
        t = (fval - self._fmin) / (self._fmax - self._fmin)
        return int(t * self.SLIDER_STEPS)

    def _from_slider(self, sval):
        t = sval / self.SLIDER_STEPS
        return self._fmin + t * (self._fmax - self._fmin)

    def _slider_to_spin(self, sval):
        self.spin.blockSignals(True)
        self.spin.setValue(self._from_slider(sval))
        self.spin.blockSignals(False)

    def _spin_to_slider(self, fval):
        self.slider.blockSignals(True)
        self.slider.setValue(self._to_slider(fval))
        self.slider.blockSignals(False)

    def get_value(self):
        return self.spin.value()

    def set_value(self, val):
        self.spin.blockSignals(True)
        self.slider.blockSignals(True)
        self.spin.setValue(float(val))
        self.slider.setValue(self._to_slider(float(val)))
        self.spin.blockSignals(False)
        self.slider.blockSignals(False)


class BoolParamWidget(QWidget):
    value_changed = pyqtSignal()

    def __init__(self, param):
        super().__init__()
        self.param = param
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)

        self.check = QCheckBox(humanize_name(param.name))
        self.check.setChecked(param.value)
        self.check.setToolTip(param.tooltip)
        self.check.toggled.connect(lambda: self.value_changed.emit())
        layout.addWidget(self.check)

    def get_value(self):
        return self.check.isChecked()

    def set_value(self, val):
        self.check.blockSignals(True)
        self.check.setChecked(bool(val))
        self.check.blockSignals(False)


class ColorButton(QPushButton):
    """A button that shows a color swatch and opens a color picker on click."""
    color_changed = pyqtSignal(tuple)

    def __init__(self, color=(0, 0, 0)):
        super().__init__()
        self._color = tuple(color)
        self.setFixedSize(36, 28)
        self.setCursor(Qt.PointingHandCursor)
        self._update_style()
        self.clicked.connect(self._pick_color)

    def _update_style(self):
        r, g, b = self._color
        # Use light or dark text depending on brightness
        brightness = r * 0.299 + g * 0.587 + b * 0.114
        text_color = "#000000" if brightness > 127 else "#ffffff"
        self.setStyleSheet(
            f"QPushButton {{ background-color: rgb({r},{g},{b}); "
            f"border: 1px solid #555; border-radius: 3px; color: {text_color}; "
            f"font-size: 9px; }}"
            f"QPushButton:hover {{ border-color: #00ff00; }}"
        )

    def _pick_color(self):
        r, g, b = self._color
        color = QColorDialog.getColor(QColor(r, g, b), self, "Pick Color")
        if color.isValid():
            self._color = (color.red(), color.green(), color.blue())
            self._update_style()
            self.color_changed.emit(self._color)

    def get_color(self):
        return self._color

    def set_color(self, color):
        self._color = tuple(color)
        self._update_style()


class ColorParamWidget(QWidget):
    value_changed = pyqtSignal()

    def __init__(self, param):
        super().__init__()
        self.param = param
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)

        label = QLabel(humanize_name(param.name))
        label.setFixedWidth(120)
        label.setToolTip(param.tooltip)
        layout.addWidget(label)

        self.btn = ColorButton(param.value)
        self.btn.color_changed.connect(lambda: self.value_changed.emit())
        layout.addWidget(self.btn)

        r, g, b = param.value
        self.hex_label = QLabel(f"#{r:02x}{g:02x}{b:02x}")
        self.hex_label.setStyleSheet("color: #888; font-family: monospace; font-size: 11px;")
        layout.addWidget(self.hex_label)
        layout.addStretch()

        self.btn.color_changed.connect(self._update_hex)

    def _update_hex(self, color):
        r, g, b = color
        self.hex_label.setText(f"#{r:02x}{g:02x}{b:02x}")

    def get_value(self):
        return self.btn.get_color()

    def set_value(self, val):
        self.btn.set_color(val)
        r, g, b = val
        self.hex_label.setText(f"#{r:02x}{g:02x}{b:02x}")


class PaletteWidget(QWidget):
    value_changed = pyqtSignal()

    def __init__(self, param):
        super().__init__()
        self.param = param
        self._colors = list(param.value)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 2, 0, 2)

        header = QHBoxLayout()
        label = QLabel(humanize_name(param.name))
        label.setFixedWidth(120)
        label.setToolTip(param.tooltip)
        header.addWidget(label)

        self.add_btn = QPushButton("+")
        self.add_btn.setFixedSize(28, 28)
        self.add_btn.clicked.connect(self._add_color)
        header.addWidget(self.add_btn)

        self.remove_btn = QPushButton("-")
        self.remove_btn.setFixedSize(28, 28)
        self.remove_btn.clicked.connect(self._remove_color)
        header.addWidget(self.remove_btn)
        header.addStretch()
        main_layout.addLayout(header)

        self.colors_layout = QHBoxLayout()
        self.colors_layout.setSpacing(4)
        main_layout.addLayout(self.colors_layout)

        self._rebuild_buttons()

    def _rebuild_buttons(self):
        while self.colors_layout.count():
            item = self.colors_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for i, color in enumerate(self._colors):
            btn = ColorButton(color)
            btn.color_changed.connect(partial(self._color_changed, i))
            self.colors_layout.addWidget(btn)
        self.colors_layout.addStretch()

    def _color_changed(self, index, color):
        self._colors[index] = color
        self.value_changed.emit()

    def _add_color(self):
        last = self._colors[-1] if self._colors else (128, 128, 128)
        self._colors.append(last)
        self._rebuild_buttons()
        self.value_changed.emit()

    def _remove_color(self):
        if len(self._colors) > 1:
            self._colors.pop()
            self._rebuild_buttons()
            self.value_changed.emit()

    def get_value(self):
        return list(self._colors)

    def set_value(self, val):
        self._colors = list(val)
        self._rebuild_buttons()


class FloatListWidget(QWidget):
    value_changed = pyqtSignal()

    def __init__(self, param):
        super().__init__()
        self.param = param
        self._values = list(param.value)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 2, 0, 2)

        header = QHBoxLayout()
        label = QLabel(humanize_name(param.name))
        label.setFixedWidth(120)
        label.setToolTip(param.tooltip)
        header.addWidget(label)

        add_btn = QPushButton("+")
        add_btn.setFixedSize(28, 28)
        add_btn.clicked.connect(self._add_item)
        header.addWidget(add_btn)

        remove_btn = QPushButton("-")
        remove_btn.setFixedSize(28, 28)
        remove_btn.clicked.connect(self._remove_item)
        header.addWidget(remove_btn)
        header.addStretch()
        main_layout.addLayout(header)

        self.items_layout = QHBoxLayout()
        self.items_layout.setSpacing(4)
        main_layout.addLayout(self.items_layout)

        self._rebuild_spins()

    def _rebuild_spins(self):
        while self.items_layout.count():
            item = self.items_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for i, val in enumerate(self._values):
            spin = QDoubleSpinBox()
            spin.setDecimals(3)
            spin.setMinimum(-100.0)
            spin.setMaximum(100.0)
            spin.setSingleStep(0.1)
            spin.setValue(val)
            spin.valueChanged.connect(partial(self._item_changed, i))
            self.items_layout.addWidget(spin)
        self.items_layout.addStretch()

    def _item_changed(self, index, val):
        self._values[index] = val
        self.value_changed.emit()

    def _add_item(self):
        self._values.append(0.0)
        self._rebuild_spins()
        self.value_changed.emit()

    def _remove_item(self):
        if len(self._values) > 1:
            self._values.pop()
            self._rebuild_spins()
            self.value_changed.emit()

    def get_value(self):
        return list(self._values)

    def set_value(self, val):
        self._values = list(val)
        self._rebuild_spins()


class IntListWidget(QWidget):
    value_changed = pyqtSignal()

    def __init__(self, param):
        super().__init__()
        self.param = param
        self._values = list(param.value)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 2, 0, 2)

        header = QHBoxLayout()
        label = QLabel(humanize_name(param.name))
        label.setFixedWidth(120)
        label.setToolTip(param.tooltip)
        header.addWidget(label)

        add_btn = QPushButton("+")
        add_btn.setFixedSize(28, 28)
        add_btn.clicked.connect(self._add_item)
        header.addWidget(add_btn)

        remove_btn = QPushButton("-")
        remove_btn.setFixedSize(28, 28)
        remove_btn.clicked.connect(self._remove_item)
        header.addWidget(remove_btn)
        header.addStretch()
        main_layout.addLayout(header)

        self.items_layout = QHBoxLayout()
        self.items_layout.setSpacing(4)
        main_layout.addLayout(self.items_layout)

        self._rebuild_spins()

    def _rebuild_spins(self):
        while self.items_layout.count():
            item = self.items_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for i, val in enumerate(self._values):
            spin = QSpinBox()
            spin.setMinimum(-100)
            spin.setMaximum(100)
            spin.setValue(val)
            spin.valueChanged.connect(partial(self._item_changed, i))
            self.items_layout.addWidget(spin)
        self.items_layout.addStretch()

    def _item_changed(self, index, val):
        self._values[index] = val
        self.value_changed.emit()

    def _add_item(self):
        self._values.append(0)
        self._rebuild_spins()
        self.value_changed.emit()

    def _remove_item(self):
        if len(self._values) > 1:
            self._values.pop()
            self._rebuild_spins()
            self.value_changed.emit()

    def get_value(self):
        return list(self._values)

    def set_value(self, val):
        self._values = list(val)
        self._rebuild_spins()


class TupleListWidget(QWidget):
    value_changed = pyqtSignal()

    def __init__(self, param):
        super().__init__()
        self.param = param
        self._values = [list(t) for t in param.value]
        self._tuple_len = len(param.value[0]) if param.value else 2

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 2, 0, 2)

        header = QHBoxLayout()
        label = QLabel(humanize_name(param.name))
        label.setFixedWidth(120)
        label.setToolTip(param.tooltip)
        header.addWidget(label)

        add_btn = QPushButton("+")
        add_btn.setFixedSize(28, 28)
        add_btn.clicked.connect(self._add_row)
        header.addWidget(add_btn)

        remove_btn = QPushButton("-")
        remove_btn.setFixedSize(28, 28)
        remove_btn.clicked.connect(self._remove_row)
        header.addWidget(remove_btn)
        header.addStretch()
        main_layout.addLayout(header)

        self.table = QTableWidget()
        self.table.setColumnCount(self._tuple_len)
        self.table.setMaximumHeight(150)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.cellChanged.connect(self._cell_changed)
        main_layout.addWidget(self.table)

        self._rebuild_table()

    def _rebuild_table(self):
        self.table.blockSignals(True)
        self.table.setRowCount(len(self._values))
        for i, tup in enumerate(self._values):
            for j, val in enumerate(tup):
                self.table.setItem(i, j, QTableWidgetItem(str(val)))
        self.table.blockSignals(False)

    def _cell_changed(self, row, col):
        try:
            val = int(self.table.item(row, col).text())
            self._values[row][col] = val
            self.value_changed.emit()
        except (ValueError, AttributeError):
            pass

    def _add_row(self):
        last = self._values[-1] if self._values else [0] * self._tuple_len
        self._values.append(list(last))
        self._rebuild_table()
        self.value_changed.emit()

    def _remove_row(self):
        if len(self._values) > 1:
            self._values.pop()
            self._rebuild_table()
            self.value_changed.emit()

    def get_value(self):
        return [tuple(t) for t in self._values]

    def set_value(self, val):
        self._values = [list(t) for t in val]
        self._rebuild_table()


def create_param_widget(param):
    """Factory: create the appropriate widget for a ConfigParam."""
    widgets = {
        "int": IntParamWidget,
        "float": FloatParamWidget,
        "bool": BoolParamWidget,
        "rgb": ColorParamWidget,
        "palette": PaletteWidget,
        "float_list": FloatListWidget,
        "int_list": IntListWidget,
        "tuple_list": TupleListWidget,
    }
    cls = widgets.get(param.param_type)
    if cls:
        return cls(param)
    return None


# ─── Keyboard Visualizer ─────────────────────────────────────────────────────

class KeyboardVisualizer(QWidget):
    """Renders a realistic keyboard layout with per-key colors from the effect preview."""
    frame_signal = pyqtSignal(list)

    def __init__(self, rows=6, cols=16, parent=None):
        super().__init__(parent)
        self.rows = rows
        self.cols = cols
        self._frame = [[(0, 0, 0)] * cols for _ in range(rows)]
        self._show_labels = True
        self.setMinimumSize(480, 180)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.frame_signal.connect(self._update_frame)

        # Pre-compute key rectangles (in unit space)
        self._key_rects = self._compute_layout()

    def _compute_layout(self):
        """Compute key positions as (row, col, x, y, w, h) in unit coordinates."""
        keys = []
        gap = 0.08  # gap between keys in units
        row_height = 1.0

        for row_idx, row_keys in enumerate(KEYBOARD_LAYOUT):
            x = 0.0
            for key_def in row_keys:
                label = key_def[0]
                width_u = key_def[2]
                if label is None:
                    x += width_u          # spacer — advance position only
                    continue
                n = len(key_def)
                col_idx = key_def[1]
                matrix_row = key_def[3] if n > 3 else row_idx
                h = key_def[4] if n > 4 else row_height
                y_off = key_def[5] if n > 5 else 0.0
                x_advance = key_def[6] if n > 6 else width_u
                keys.append({
                    "label": label,
                    "row": row_idx,
                    "col": col_idx,
                    "matrix_row": matrix_row,
                    "x": x,
                    "y": row_idx * (row_height + gap) + y_off,
                    "w": width_u - gap,
                    "h": h,
                })
                x += x_advance
        return keys

    def _update_frame(self, snapshot):
        self._frame = snapshot
        self.update()

    def toggle_labels(self):
        self._show_labels = not self._show_labels
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Background
        painter.fillRect(self.rect(), QColor(10, 10, 10))

        if not self._key_rects:
            return

        # Calculate total layout bounds
        max_x = max(k["x"] + k["w"] for k in self._key_rects)
        max_y = max(k["y"] + k["h"] for k in self._key_rects)

        # Scale to fit widget with padding
        pad = 8
        avail_w = self.width() - 2 * pad
        avail_h = self.height() - 2 * pad
        scale_x = avail_w / max_x if max_x > 0 else 1
        scale_y = avail_h / max_y if max_y > 0 else 1
        scale = min(scale_x, scale_y)

        # Center
        total_w = max_x * scale
        total_h = max_y * scale
        offset_x = pad + (avail_w - total_w) / 2
        offset_y = pad + (avail_h - total_h) / 2

        corner = 3 * scale / 20  # proportional corner radius
        corner = max(2, min(corner, 6))

        font = QFont("Sans", max(6, int(scale / 4.5)))
        painter.setFont(font)

        for key in self._key_rects:
            row, col = key["row"], key["col"]
            x = offset_x + key["x"] * scale
            y = offset_y + key["y"] * scale
            w = key["w"] * scale
            h = key["h"] * scale

            # Get color from frame (use matrix_row for keys like ↑ that
            # are visually in one row but mapped to a different matrix row)
            mrow = key.get("matrix_row", row)
            if mrow < len(self._frame) and col < len(self._frame[mrow]):
                r, g, b = self._frame[mrow][col]
            else:
                r, g, b = 0, 0, 0

            # Key face
            fill_color = QColor(r, g, b)
            painter.setBrush(QBrush(fill_color))

            # Subtle border - slightly darker than fill, or dim gray for dark keys
            brightness = r * 0.299 + g * 0.587 + b * 0.114
            if brightness < 20:
                border_color = QColor(35, 35, 35)
            else:
                border_color = QColor(max(0, r - 30), max(0, g - 30), max(0, b - 30))
            painter.setPen(QPen(border_color, 1))

            painter.drawRoundedRect(int(x), int(y), int(w), int(h), corner, corner)

            # Key label
            if self._show_labels and key["label"]:
                text_brightness = r * 0.299 + g * 0.587 + b * 0.114
                if text_brightness > 100:
                    painter.setPen(QPen(QColor(0, 0, 0, 100), 1))
                else:
                    painter.setPen(QPen(QColor(255, 255, 255, 60), 1))
                painter.drawText(int(x + 3), int(y + 2), int(w - 6), int(h - 4),
                                 Qt.AlignCenter, key["label"])

        painter.end()


# ─── Preview Runner ───────────────────────────────────────────────────────────

class PreviewRunner:
    """Manages running an effect on a virtual device for the visualizer."""

    def __init__(self, visualizer, rows=6, cols=16):
        self.visualizer = visualizer
        self.rows = rows
        self.cols = cols
        self.stop_event = threading.Event()
        self.thread = None
        self._temp_paths = []

    def start(self, effect_module, temp_config_path=None):
        """Start previewing an effect. Optionally override its config path."""
        self.stop()
        self.stop_event = threading.Event()

        # Load a separate copy of the effect module for preview
        src_path = effect_module.__spec__.origin
        mod_name = effect_module.__name__ + "__preview"
        spec = importlib.util.spec_from_file_location(mod_name, src_path)
        preview_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(preview_module)

        # Override CONFIG_PATH if provided
        if temp_config_path and hasattr(preview_module, "CONFIG_PATH"):
            preview_module.CONFIG_PATH = temp_config_path

        def _on_draw(snapshot):
            try:
                self.visualizer.frame_signal.emit(snapshot)
            except RuntimeError:
                pass  # Widget deleted during shutdown

        vdev = VirtualDevice(self.rows, self.cols, on_draw=_on_draw)

        self.thread = threading.Thread(
            target=preview_module.run,
            args=(vdev, self.stop_event),
            daemon=True,
        )
        self.thread.start()

    def stop(self):
        if self.thread and self.thread.is_alive():
            self.stop_event.set()
            self.thread.join(timeout=2)
        self.thread = None

    def cleanup(self):
        self.stop()
        # Clean up temp files
        if os.path.exists(TEMP_DIR):
            shutil.rmtree(TEMP_DIR, ignore_errors=True)


# ─── Main Config Window ──────────────────────────────────────────────────────

class ConfigWindow(QMainWindow):
    def __init__(self, initial_effect=None):
        super().__init__()
        self.setWindowTitle("Razer Lighting Configuration")
        self.setMinimumSize(900, 550)

        # Restore geometry
        self._settings = QSettings(SETTINGS_ORG, SETTINGS_APP)
        geo = self._settings.value("geometry")
        if geo:
            self.restoreGeometry(geo)
        else:
            self.resize(1050, 650)

        # State
        self.effects = discover_effects()
        self._params = []
        self._param_widgets = []
        self._dirty = False
        self._current_config_path = None
        self._current_effect_name = None
        self._current_module = None

        # Detect keyboard dimensions
        self._rows, self._cols = detect_dimensions()

        # Preview runner
        self.preview = PreviewRunner(None, self._rows, self._cols)

        # Debounce timer for preview updates
        self._debounce_timer = QTimer()
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.setInterval(100)  # 10 Hz max
        self._debounce_timer.timeout.connect(self._write_temp_config)

        self._build_ui()

        # Select initial effect
        if initial_effect and initial_effect in self.effects:
            idx = list(self.effects.keys()).index(initial_effect)
            self.effect_combo.setCurrentIndex(idx)
        # Explicitly trigger load (setCurrentIndex(0) won't fire signal if already at 0)
        if self.effects:
            self._on_effect_changed(self.effect_combo.currentText())

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(8)

        # ── Effect selector row ──
        selector_layout = QHBoxLayout()
        selector_layout.addWidget(QLabel("Effect:"))
        self.effect_combo = QComboBox()
        self.effect_combo.addItems(list(self.effects.keys()))
        self.effect_combo.currentTextChanged.connect(self._on_effect_changed)
        self.effect_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        selector_layout.addWidget(self.effect_combo, 1)
        main_layout.addLayout(selector_layout)

        # ── Splitter: params left, visualizer right ──
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(3)

        # Left: scrollable parameter panel
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setMinimumWidth(400)
        self.param_container = QWidget()
        self.param_layout = QVBoxLayout(self.param_container)
        self.param_layout.setContentsMargins(4, 2, 4, 4)
        self.param_layout.setSpacing(8)
        self.param_layout.addStretch()
        self.scroll.setWidget(self.param_container)
        splitter.addWidget(self.scroll)

        # Right: keyboard visualizer
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(4, 4, 4, 4)

        self.visualizer = KeyboardVisualizer(self._rows, self._cols)
        self.preview.visualizer = self.visualizer
        right_layout.addWidget(self.visualizer, 1)

        # Labels toggle
        viz_controls = QHBoxLayout()
        labels_btn = QPushButton("Toggle Key Labels")
        labels_btn.clicked.connect(self.visualizer.toggle_labels)
        viz_controls.addWidget(labels_btn)
        viz_controls.addStretch()
        right_layout.addLayout(viz_controls)

        splitter.addWidget(right_panel)
        splitter.setSizes([450, 550])
        main_layout.addWidget(splitter, 1)

        # ── Button bar ──
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        self.save_btn = QPushButton("Save")
        self.save_btn.setObjectName("saveButton")
        self.save_btn.clicked.connect(self._save)
        btn_layout.addWidget(self.save_btn)

        self.revert_btn = QPushButton("Revert to Saved")
        self.revert_btn.clicked.connect(self._revert)
        btn_layout.addWidget(self.revert_btn)

        self.defaults_btn = QPushButton("Reset to Defaults")
        self.defaults_btn.clicked.connect(self._reset_defaults)
        btn_layout.addWidget(self.defaults_btn)

        btn_layout.addStretch()
        main_layout.addLayout(btn_layout)

    def _on_effect_changed(self, effect_name):
        if not effect_name or effect_name not in self.effects:
            return

        # Check dirty state
        if self._dirty:
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                f"You have unsaved changes to {self._current_effect_name}. Discard?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
            )
            if reply == QMessageBox.No:
                # Revert combo to current
                self.effect_combo.blockSignals(True)
                idx = list(self.effects.keys()).index(self._current_effect_name)
                self.effect_combo.setCurrentIndex(idx)
                self.effect_combo.blockSignals(False)
                return

        self._current_effect_name = effect_name
        self._current_module = self.effects[effect_name]
        self._current_config_path = get_config_path_for_effect(self._current_module)

        if self._current_config_path and os.path.exists(self._current_config_path):
            self._params = parse_config(self._current_config_path)
            save_defaults(effect_name, self._params)
        else:
            self._params = []

        self._rebuild_params()
        self._set_dirty(False)
        self._start_preview()

    def _rebuild_params(self):
        """Rebuild the parameter panel with widgets for the current effect."""
        # Clear existing
        self._param_widgets = []
        while self.param_layout.count():
            item = self.param_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        if not self._params:
            self.param_layout.addWidget(QLabel("No configurable parameters."))
            self.param_layout.addStretch()
            return

        groups = group_params(self._params)
        for group_name, group_params_list in groups.items():
            group = QGroupBox(group_name)
            group_layout = QVBoxLayout(group)
            group_layout.setSpacing(4)
            group_layout.setContentsMargins(8, 8, 8, 8)

            for param in group_params_list:
                widget = create_param_widget(param)
                if widget:
                    widget.value_changed.connect(self._on_param_changed)
                    group_layout.addWidget(widget)
                    self._param_widgets.append((param, widget))

            self.param_layout.addWidget(group)

        self.param_layout.addStretch()

    def _on_param_changed(self):
        self._set_dirty(True)
        self._debounce_timer.start()

    def _set_dirty(self, dirty):
        self._dirty = dirty
        name = self._current_effect_name or "Razer Lighting"
        if dirty:
            self.setWindowTitle(f"Razer Lighting Configuration - {name} *")
        else:
            self.setWindowTitle(f"Razer Lighting Configuration - {name}")

    def _collect_values(self):
        """Read current values from all widgets into params."""
        for param, widget in self._param_widgets:
            param.value = widget.get_value()

    def _write_temp_config(self):
        """Write current param values to a temp config for the preview thread."""
        if not self._current_config_path:
            return
        self._collect_values()
        temp_path = write_temp_config(self._current_config_path, self._params)
        return temp_path

    def _start_preview(self):
        """Start or restart the preview for the current effect."""
        self.preview.stop()
        if not self._current_module or not self._current_config_path:
            return

        # Write initial temp config (copy of real config)
        temp_path = write_temp_config(self._current_config_path, self._params)

        self.preview.start(self._current_module, temp_config_path=temp_path)

    def _save(self):
        """Save current values to the real config file."""
        if not self._current_config_path:
            return
        self._collect_values()
        write_config(self._current_config_path, self._params)
        self._set_dirty(False)

    def _revert(self):
        """Revert to the saved config file values."""
        if not self._current_config_path:
            return
        self._params = parse_config(self._current_config_path)
        self._rebuild_params()
        self._set_dirty(False)
        self._start_preview()

    def _reset_defaults(self):
        """Reset to original default values."""
        if not self._current_effect_name:
            return
        defaults = load_defaults(self._current_effect_name)
        if not defaults:
            QMessageBox.information(self, "No Defaults",
                                    "No saved defaults found for this effect.")
            return

        for param, widget in self._param_widgets:
            if param.name in defaults:
                default_val = defaults[param.name]["value"]
                param.value = default_val
                widget.set_value(default_val)

        self._set_dirty(True)
        self._debounce_timer.start()

    def closeEvent(self, event):
        if self._dirty:
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "You have unsaved changes. Discard?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
            )
            if reply == QMessageBox.No:
                event.ignore()
                return

        # Save geometry
        self._settings.setValue("geometry", self.saveGeometry())

        # Stop preview
        self.preview.cleanup()
        event.accept()


def _make_app_icon():
    """Generate a simple Razer-green keyboard icon for the window/taskbar."""
    from PyQt5.QtGui import QPixmap, QIcon
    sizes = [16, 32, 48, 64, 128]
    icon = QIcon()
    for sz in sizes:
        pm = QPixmap(sz, sz)
        pm.fill(QColor(0, 0, 0, 0))
        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing)
        margin = sz * 0.08
        w, h = sz - 2 * margin, sz - 2 * margin
        # Keyboard body
        p.setBrush(QBrush(QColor(20, 20, 20)))
        p.setPen(QPen(QColor(0, 200, 0), max(1, sz / 24)))
        cr = sz * 0.12
        p.drawRoundedRect(int(margin), int(margin + h * 0.1),
                          int(w), int(h * 0.8), cr, cr)
        # Key grid (3 rows of small squares)
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(QColor(0, 180, 0)))
        key_rows, key_cols = 3, 7
        area_x = margin + w * 0.12
        area_y = margin + h * 0.22
        area_w = w * 0.76
        area_h = h * 0.56
        kw = area_w / key_cols * 0.7
        kh = area_h / key_rows * 0.65
        for r in range(key_rows):
            for c in range(key_cols):
                kx = area_x + c * (area_w / key_cols) + (area_w / key_cols - kw) / 2
                ky = area_y + r * (area_h / key_rows) + (area_h / key_rows - kh) / 2
                p.drawRoundedRect(int(kx), int(ky), int(kw), int(kh), 1, 1)
        p.end()
        icon.addPixmap(pm)
    return icon


def main():
    # Set app ID before QApplication so the desktop environment picks it up.
    # This fixes the taskbar showing "Python 3" as the window title.
    QApplication.setApplicationName("Razer Lighting")
    QApplication.setDesktopFileName("razer-lighting")

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(DARK_STYLESHEET)

    app_icon = _make_app_icon()
    app.setWindowIcon(app_icon)

    # Get initial effect from CLI args
    initial_effect = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] else None

    window = ConfigWindow(initial_effect)
    window.setWindowIcon(app_icon)
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
