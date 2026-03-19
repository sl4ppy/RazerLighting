#!/usr/bin/env python3
"""Razer Lighting Configuration Window — PyQt5-based effect configurator with live preview."""

import importlib.util
import os
import shutil
import sys
import threading
import time

from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QSettings
from PyQt5.QtGui import QColor, QPainter, QPen, QBrush, QFont
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QComboBox, QLabel, QPushButton, QScrollArea, QGroupBox,
    QMessageBox, QSizePolicy,
)

from config_parser import (
    parse_config, write_config, write_temp_config, get_config_path_for_effect,
    load_defaults, save_defaults, group_params,
)
from config_widgets import create_param_widget
from effects.common import discover_effects
from keyboard_layout import compute_key_rects
from virtual_device import VirtualDevice, detect_dimensions
TEMP_DIR = "/tmp/razer-lighting-preview"
SETTINGS_ORG = "RazerLighting"
SETTINGS_APP = "ConfigWindow"


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
        return compute_key_rects()

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
