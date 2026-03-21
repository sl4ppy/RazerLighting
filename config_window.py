#!/usr/bin/env python3
"""Razer Lighting Configuration Window — PyQt5-based effect configurator with live preview."""

import importlib.util
import math
import os
import shutil
import sys
import threading
import time

from PyQt5.QtCore import (
    Qt, QTimer, pyqtSignal, QSettings, QPropertyAnimation, QEasingCurve,
    QParallelAnimationGroup, QRect, QSize, pyqtProperty, QPoint,
)
from PyQt5.QtGui import (
    QColor, QPainter, QPen, QBrush, QFont, QFontDatabase, QLinearGradient,
    QRadialGradient, QPainterPath, QPixmap,
)
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QComboBox, QLabel, QPushButton, QScrollArea, QGroupBox,
    QMessageBox, QSizePolicy, QFrame, QLineEdit, QStackedWidget,
    QGridLayout, QToolButton, QStatusBar,
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


# ─── Effect metadata for gallery ─────────────────────────────────────────────

EFFECT_CATEGORIES = {
    "Organic": [
        "Fireflies", "Physarum", "Crystal Growth", "Reaction-Diffusion",
        "Boid Flock", "Heartbeat Pulse",
    ],
    "Atmospheric": [
        "Aurora Borealis", "Nebula Clouds", "Tidal Swell", "Raindrop Ripples",
        "Ember Drift", "Searchlight",
    ],
    "Mathematical": [
        "Plasma", "Lissajous", "Chladni Patterns", "Fractal Zoom",
        "Wave Interference", "Metaballs", "Heat Diffusion",
    ],
    "Glitch": [
        "Glitch", "Corrupt", "Corruption",
    ],
    "Kinetic": [
        "Arc Sweep", "Lightning Strike", "Binary Cascade",
        "Magnetic Field Lines", "Voronoi Shatter", "Cyclic Cellular Automaton",
    ],
}

EFFECT_DESCRIPTIONS = {
    "Arc Sweep": "Arcs of light sweep from random directions with trailing fade",
    "Lightning Strike": "Procedural bolts with branches, restrikes, and surges",
    "Binary Cascade": "Matrix-style falling green streams with white heads",
    "Tidal Swell": "Ocean waves with crests, foam sparkle, and depth shading",
    "Plasma": "Classic demoscene layered sine-wave plasma",
    "Searchlight": "Rotating beam on purple background, warm white glow",
    "Glitch": "Quiet baseline with violent burst corruption and scanlines",
    "Fractal Zoom": "Mandelbrot/Julia zoom with purple nebula palette",
    "Lissajous": "Dot traces Lissajous curves with fading trail",
    "Heat Diffusion": "Laplacian heat spread with hot iron palette",
    "Metaballs": "Lissajous-path blobs with molten lava palette",
    "Chladni Patterns": "Vibrating plate nodal lines with mode morphing",
    "Cyclic Cellular Automaton": "14-state Moore neighborhood with rainbow spirals",
    "Magnetic Field Lines": "Iron filings pattern with drifting poles",
    "Wave Interference": "2D wave equation with 3 moving sources",
    "Fireflies": "Kuramoto coupled oscillators with sync/chaos cycles",
    "Crystal Growth": "DLA random walkers with center seed growth",
    "Reaction-Diffusion": "Gray-Scott model with bioluminescent teal palette",
    "Physarum": "150 slime mold agents with trail sensing",
    "Raindrop Ripples": "Expanding radial rings with wave interference",
    "Ember Drift": "Rising particle embers with wind and cooling gradient",
    "Heartbeat Pulse": "Cardiac lub-dub pulses with vein network",
    "Boid Flock": "Reynolds flocking agents with luminous trails",
    "Aurora Borealis": "Multi-layer value noise curtains in green/cyan",
    "Nebula Clouds": "Dual-layer fBm noise with star birth flashes",
    "Voronoi Shatter": "Moving Voronoi seeds with neon edge glow",
    "Corrupt": "Localized corruption patches: noise, row-shifts, blocks",
    "Corruption": "Organic decay: blob infections with lifecycle phases",
}

CATEGORY_ICONS = {
    "Organic": "\u2618",      # shamrock
    "Atmospheric": "\u2601",  # cloud
    "Mathematical": "\u2206", # delta
    "Glitch": "\u26a1",       # lightning
    "Kinetic": "\u27a4",      # arrow
}

def _get_category(effect_name):
    """Return the category for an effect name."""
    for cat, names in EFFECT_CATEGORIES.items():
        if effect_name in names:
            return cat
    return "Other"


# ─── Dark Theme ───────────────────────────────────────────────────────────────

DARK_STYLESHEET = """
/* ── Base ── */
QMainWindow {
    background-color: #111113;
    color: #d8d8dd;
}
QWidget {
    background-color: transparent;
    color: #d8d8dd;
}
QMainWindow > QWidget {
    background-color: #111113;
}

/* ── Typography ── */
QLabel {
    color: #a0a0aa;
    font-size: 13px;
}
QLabel#effectTitle {
    color: #e8e8ee;
    font-size: 18px;
    font-weight: bold;
    letter-spacing: 1px;
}
QLabel#effectCategory {
    color: #44D62C;
    font-size: 12px;
    font-weight: bold;
    letter-spacing: 2px;
}
QLabel#effectDescription {
    color: #707080;
    font-size: 13px;
    font-style: italic;
}
QLabel#sectionLabel {
    color: #606068;
    font-size: 11px;
    font-weight: bold;
    letter-spacing: 3px;
}

/* ── Panels ── */
QFrame#paramPanel {
    background-color: #141416;
    border: 1px solid #1e1e22;
    border-radius: 6px;
}
QFrame#vizPanel {
    background-color: #0a0a0c;
    border: 1px solid #1a1a1e;
    border-radius: 8px;
}
QFrame#galleryPanel {
    background-color: #141416;
    border: 1px solid #1e1e22;
    border-radius: 6px;
}
QFrame#headerPanel {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #161618, stop:1 #111113);
    border-bottom: 1px solid #1e1e22;
}

/* ── Effect Gallery Cards ── */
QPushButton#effectCard {
    background-color: #18181c;
    border: 1px solid #252528;
    border-radius: 6px;
    padding: 10px 14px;
    color: #c0c0cc;
    font-size: 13px;
    text-align: left;
    min-height: 52px;
}
QPushButton#effectCard:hover {
    background-color: #1e1e24;
    border-color: #44D62C;
    color: #e8e8ee;
}
QPushButton#effectCard:checked {
    background-color: #112208;
    border-color: #44D62C;
    border-width: 2px;
    color: #66FF44;
}
QLabel#cardCategory {
    color: #44D62C;
    font-size: 10px;
    font-weight: bold;
    letter-spacing: 2px;
}
QLabel#cardDesc {
    color: #8888a0;
    font-size: 12px;
}

/* ── Search Field ── */
QLineEdit#searchField {
    background-color: #18181c;
    border: 1px solid #252528;
    border-radius: 14px;
    padding: 6px 14px 6px 32px;
    color: #c0c0cc;
    font-size: 13px;
    min-height: 22px;
}
QLineEdit#searchField:focus {
    border-color: #44D62C;
    background-color: #1a1a20;
}
QLineEdit#searchField::placeholder { color: #404048; }

/* ── Category Filter Buttons ── */
QPushButton#filterBtn {
    background-color: transparent;
    border: 1px solid #252528;
    border-radius: 12px;
    padding: 4px 8px;
    color: #606068;
    font-size: 11px;
    font-weight: bold;
    letter-spacing: 0px;
    min-height: 20px;
}
QPushButton#filterBtn:hover {
    border-color: #44D62C;
    color: #44D62C;
}
QPushButton#filterBtn:checked {
    background-color: #112208;
    border-color: #44D62C;
    color: #66FF44;
}

/* ── ComboBox (kept for fallback) ── */
QComboBox {
    background-color: #18181c;
    border: 1px solid #252528;
    border-radius: 4px;
    padding: 5px 12px;
    color: #d8d8dd;
    font-size: 12px;
    min-height: 24px;
}
QComboBox:hover { border-color: #44D62C; }
QComboBox::drop-down { border: none; width: 24px; }
QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #44D62C;
    margin-right: 8px;
}
QComboBox QAbstractItemView {
    background-color: #18181c;
    color: #d8d8dd;
    selection-background-color: #112208;
    selection-color: #66FF44;
    border: 1px solid #252528;
}

/* ── Spin Boxes ── */
QSpinBox, QDoubleSpinBox {
    background-color: #18181c;
    border: 1px solid #252528;
    border-radius: 4px;
    padding: 3px 6px;
    color: #d8d8dd;
    font-size: 13px;
    font-family: "JetBrains Mono", "Fira Code", "Source Code Pro", "Consolas", monospace;
}
QSpinBox:hover, QDoubleSpinBox:hover { border-color: #44D62C; }
QSpinBox:focus, QDoubleSpinBox:focus { border-color: #44D62C; background-color: #1a1a20; }
QSpinBox::up-button, QDoubleSpinBox::up-button,
QSpinBox::down-button, QDoubleSpinBox::down-button {
    background-color: #1e1e22;
    border: none;
    width: 18px;
}
QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {
    background-color: #252528;
}

/* ── Sliders ── */
QSlider::groove:horizontal {
    height: 8px;
    background: #1a1a1e;
    border-radius: 4px;
    border: 1px solid #252528;
}
QSlider::handle:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #55E835, stop:1 #33AA22);
    width: 18px;
    height: 18px;
    margin: -6px 0;
    border-radius: 9px;
    border: 2px solid #44D62C;
}
QSlider::handle:horizontal:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #66FF44, stop:1 #44D62C);
    border-color: #88FF55;
}
QSlider::sub-page:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #0a2200, stop:0.7 #33AA22, stop:1 #44D62C);
    border-radius: 4px;
}

/* ── Buttons ── */
QPushButton {
    background-color: #18181c;
    border: 1px solid #252528;
    border-radius: 5px;
    padding: 7px 18px;
    color: #c0c0cc;
    font-size: 13px;
    font-weight: bold;
    letter-spacing: 0.5px;
}
QPushButton:hover {
    border-color: #44D62C;
    background-color: #1e1e24;
    color: #e8e8ee;
}
QPushButton:pressed {
    background-color: #112208;
    color: #66FF44;
}
QPushButton#saveButton {
    background-color: #112208;
    border: 2px solid #44D62C;
    color: #66FF44;
    font-weight: bold;
    font-size: 14px;
    padding: 8px 24px;
}
QPushButton#saveButton:hover {
    background-color: #152a0e;
    border-color: #66FF44;
    color: #88FF55;
}

/* ── Group Boxes (collapsible sections) ── */
QGroupBox {
    border: 1px solid #1e1e22;
    border-radius: 6px;
    margin-top: 12px;
    padding: 28px 10px 10px 10px;
    font-weight: bold;
    font-size: 12px;
    color: #44D62C;
    letter-spacing: 2px;
    background-color: #141416;
}
QGroupBox::title {
    subcontrol-origin: padding;
    subcontrol-position: top left;
    left: 12px;
    top: 6px;
    padding: 0 6px;
}

/* ── Scroll Areas ── */
QScrollArea { border: none; background: transparent; }
QScrollBar:vertical {
    background: transparent;
    width: 8px;
    border: none;
    margin: 2px;
}
QScrollBar::handle:vertical {
    background: #2a2a2e;
    border-radius: 4px;
    min-height: 40px;
}
QScrollBar::handle:vertical:hover { background: #44D62C; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }
QScrollBar:horizontal {
    background: transparent;
    height: 8px;
    border: none;
    margin: 2px;
}
QScrollBar::handle:horizontal {
    background: #2a2a2e;
    border-radius: 4px;
    min-width: 40px;
}
QScrollBar::handle:horizontal:hover { background: #44D62C; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal { background: transparent; }

/* ── Checkboxes ── */
QCheckBox { spacing: 8px; font-size: 13px; }
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 2px solid #2a2a2e;
    background-color: #18181c;
}
QCheckBox::indicator:checked {
    background-color: #44D62C;
    border-color: #66FF44;
}
QCheckBox::indicator:hover { border-color: #44D62C; }

/* ── Tables ── */
QTableWidget {
    background-color: #18181c;
    color: #d8d8dd;
    border: 1px solid #252528;
    gridline-color: #1e1e22;
    font-size: 13px;
    border-radius: 4px;
}
QTableWidget::item:selected {
    background-color: #112208;
    color: #66FF44;
}
QHeaderView::section {
    background-color: #141416;
    color: #707080;
    border: 1px solid #1e1e22;
    padding: 4px;
    font-size: 12px;
    font-weight: bold;
}

/* ── Splitter ── */
QSplitter::handle {
    background-color: #1e1e22;
    width: 2px;
}
QSplitter::handle:hover { background-color: #44D62C; }

/* ── Status Bar ── */
QStatusBar {
    background-color: #0e0e10;
    color: #606070;
    font-size: 12px;
    border-top: 1px solid #1a1a1e;
    padding: 2px 8px;
    font-family: "JetBrains Mono", "Fira Code", "Source Code Pro", "Consolas", monospace;
}
QStatusBar QLabel {
    color: #606070;
    font-size: 12px;
    font-family: "JetBrains Mono", "Fira Code", "Source Code Pro", "Consolas", monospace;
}

/* ── Tooltips ── */
QToolTip {
    background-color: #1a1a1e;
    color: #c0c0cc;
    border: 1px solid #44D62C;
    border-radius: 4px;
    padding: 6px 10px;
    font-size: 13px;
}
"""


# ─── Keyboard Visualizer ─────────────────────────────────────────────────────

class KeyboardVisualizer(QWidget):
    """Renders a realistic keyboard layout with per-key RGB glow, depth, and ambient light."""
    frame_signal = pyqtSignal(list)

    def __init__(self, rows=6, cols=16, parent=None):
        super().__init__(parent)
        self.rows = rows
        self.cols = cols
        self._frame = [[(0, 0, 0)] * cols for _ in range(rows)]
        self._show_labels = True
        self.setMinimumSize(480, 200)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.frame_signal.connect(self._update_frame)

        # Pre-compute key rectangles (in unit space)
        self._key_rects = self._compute_layout()

    def _compute_layout(self):
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
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        w_full, h_full = self.width(), self.height()

        # ── Background with subtle gradient ──
        bg_grad = QLinearGradient(0, 0, 0, h_full)
        bg_grad.setColorAt(0.0, QColor(8, 8, 12))
        bg_grad.setColorAt(0.5, QColor(6, 6, 8))
        bg_grad.setColorAt(1.0, QColor(10, 10, 14))
        painter.fillRect(self.rect(), bg_grad)

        if not self._key_rects:
            painter.end()
            return

        # Calculate layout bounds
        max_x = max(k["x"] + k["w"] for k in self._key_rects)
        max_y = max(k["y"] + k["h"] for k in self._key_rects)

        # Scale to fit with generous padding for glow bleed
        pad = 24
        avail_w = w_full - 2 * pad
        avail_h = h_full - 2 * pad - 16  # extra room for desk reflection
        scale_x = avail_w / max_x if max_x > 0 else 1
        scale_y = avail_h / max_y if max_y > 0 else 1
        scale = min(scale_x, scale_y)

        total_w = max_x * scale
        total_h = max_y * scale
        offset_x = pad + (avail_w - total_w) / 2
        offset_y = pad + (avail_h - total_h) / 2

        corner = max(2, min(3 * scale / 20, 6))

        # ── Pass 1: Ambient glow beneath keys (bloom effect) ──
        for key in self._key_rects:
            row, col = key["row"], key["col"]
            mrow = key.get("matrix_row", row)
            if mrow < len(self._frame) and col < len(self._frame[mrow]):
                r, g, b = self._frame[mrow][col]
            else:
                r, g, b = 0, 0, 0

            brightness = r * 0.299 + g * 0.587 + b * 0.114
            if brightness < 15:
                continue

            x = offset_x + key["x"] * scale
            y = offset_y + key["y"] * scale
            kw = key["w"] * scale
            kh = key["h"] * scale

            # Glow radius proportional to brightness
            glow_alpha = min(60, int(brightness * 0.35))
            glow_radius = max(kw, kh) * (0.6 + brightness / 255.0 * 0.8)

            cx = x + kw / 2
            cy = y + kh / 2

            glow = QRadialGradient(cx, cy, glow_radius)
            glow.setColorAt(0.0, QColor(r, g, b, glow_alpha))
            glow.setColorAt(0.4, QColor(r, g, b, int(glow_alpha * 0.4)))
            glow.setColorAt(1.0, QColor(r, g, b, 0))

            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(glow))
            painter.drawEllipse(
                int(cx - glow_radius), int(cy - glow_radius),
                int(glow_radius * 2), int(glow_radius * 2)
            )

        # ── Pass 2: Desk surface reflection (below keyboard) ──
        desk_y = offset_y + total_h + 4
        desk_h = min(20, h_full - desk_y - 2)
        if desk_h > 4:
            for key in self._key_rects:
                row, col = key["row"], key["col"]
                mrow = key.get("matrix_row", row)
                if mrow < len(self._frame) and col < len(self._frame[mrow]):
                    r, g, b = self._frame[mrow][col]
                else:
                    continue
                brightness = r * 0.299 + g * 0.587 + b * 0.114
                if brightness < 25:
                    continue
                if key["row"] != max(k["row"] for k in self._key_rects):
                    continue  # only bottom row reflects

                x = offset_x + key["x"] * scale
                kw = key["w"] * scale
                refl_alpha = min(25, int(brightness * 0.12))
                refl = QLinearGradient(x + kw / 2, desk_y, x + kw / 2, desk_y + desk_h)
                refl.setColorAt(0.0, QColor(r, g, b, refl_alpha))
                refl.setColorAt(1.0, QColor(r, g, b, 0))
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(refl))
                painter.drawRect(int(x - 2), int(desk_y), int(kw + 4), int(desk_h))

        # ── Pass 3: Key faces with depth ──
        font_name = "JetBrains Mono"
        # Fallback font chain
        for fn in ["JetBrains Mono", "Fira Code", "Source Code Pro", "Consolas", "Monospace"]:
            if fn in QFontDatabase().families():
                font_name = fn
                break
        font = QFont(font_name, max(6, int(scale / 5)))
        painter.setFont(font)

        for key in self._key_rects:
            row, col = key["row"], key["col"]
            x = offset_x + key["x"] * scale
            y = offset_y + key["y"] * scale
            kw = key["w"] * scale
            kh = key["h"] * scale

            mrow = key.get("matrix_row", row)
            if mrow < len(self._frame) and col < len(self._frame[mrow]):
                r, g, b = self._frame[mrow][col]
            else:
                r, g, b = 0, 0, 0

            brightness = r * 0.299 + g * 0.587 + b * 0.114

            # Key body shadow (depth)
            shadow_offset = max(1, scale / 25)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor(0, 0, 0, 80)))
            painter.drawRoundedRect(
                int(x + shadow_offset), int(y + shadow_offset),
                int(kw), int(kh), corner, corner
            )

            # Key face with top-lit gradient
            face_grad = QLinearGradient(x, y, x, y + kh)
            # Brighter top edge, darker bottom for 3D feel
            r_top = min(255, int(r * 1.15 + 12))
            g_top = min(255, int(g * 1.15 + 12))
            b_top = min(255, int(b * 1.15 + 12))
            r_bot = max(0, int(r * 0.75 - 5))
            g_bot = max(0, int(g * 0.75 - 5))
            b_bot = max(0, int(b * 0.75 - 5))
            face_grad.setColorAt(0.0, QColor(r_top, g_top, b_top))
            face_grad.setColorAt(0.3, QColor(r, g, b))
            face_grad.setColorAt(1.0, QColor(r_bot, g_bot, b_bot))

            painter.setBrush(QBrush(face_grad))

            # Border: subtle highlight top, shadow bottom
            if brightness < 15:
                border_color = QColor(30, 30, 34)
            else:
                border_color = QColor(
                    max(0, int(r * 0.6)),
                    max(0, int(g * 0.6)),
                    max(0, int(b * 0.6)),
                    180
                )
            painter.setPen(QPen(border_color, 1))
            painter.drawRoundedRect(int(x), int(y), int(kw), int(kh), corner, corner)

            # Specular highlight on top edge
            if brightness > 30:
                spec_alpha = min(40, int(brightness * 0.18))
                spec = QLinearGradient(x, y, x, y + kh * 0.4)
                spec.setColorAt(0.0, QColor(255, 255, 255, spec_alpha))
                spec.setColorAt(1.0, QColor(255, 255, 255, 0))
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(spec))
                painter.drawRoundedRect(int(x + 1), int(y + 1),
                                        int(kw - 2), int(kh * 0.4), corner, corner)

            # Key label
            if self._show_labels and key["label"]:
                if brightness > 120:
                    painter.setPen(QPen(QColor(0, 0, 0, 140), 1))
                elif brightness > 50:
                    painter.setPen(QPen(QColor(0, 0, 0, 80), 1))
                else:
                    painter.setPen(QPen(QColor(255, 255, 255, 50), 1))
                painter.drawText(int(x + 3), int(y + 2), int(kw - 6), int(kh - 4),
                                 Qt.AlignCenter, key["label"])

        # ── Vignette overlay ──
        vig_grad = QRadialGradient(w_full / 2, h_full / 2, max(w_full, h_full) * 0.6)
        vig_grad.setColorAt(0.0, QColor(0, 0, 0, 0))
        vig_grad.setColorAt(0.7, QColor(0, 0, 0, 0))
        vig_grad.setColorAt(1.0, QColor(0, 0, 0, 60))
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(vig_grad))
        painter.drawRect(self.rect())

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


# ─── Effect Gallery ──────────────────────────────────────────────────────────

class EffectCard(QPushButton):
    """A clickable card representing a single effect in the gallery."""

    def __init__(self, effect_name, parent=None):
        super().__init__(parent)
        self.effect_name = effect_name
        self.setObjectName("effectCard")
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(56)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(2)

        # Category tag
        category = _get_category(effect_name)
        icon = CATEGORY_ICONS.get(category, "")
        cat_label = QLabel(f"{icon} {category.upper()}")
        cat_label.setObjectName("cardCategory")
        cat_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        layout.addWidget(cat_label)

        # Effect name
        name_label = QLabel(effect_name)
        name_label.setStyleSheet("font-size: 15px; font-weight: bold; color: #e8e8ee;")
        name_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        layout.addWidget(name_label)

        # Description
        desc = EFFECT_DESCRIPTIONS.get(effect_name, "")
        if desc:
            desc_label = QLabel(desc)
            desc_label.setObjectName("cardDesc")
            desc_label.setWordWrap(True)
            desc_label.setAttribute(Qt.WA_TransparentForMouseEvents)
            layout.addWidget(desc_label)


class EffectGallery(QWidget):
    """Scrollable gallery of effect cards with search and category filtering."""
    effect_selected = pyqtSignal(str)

    def __init__(self, effect_names, parent=None):
        super().__init__(parent)
        self._effect_names = sorted(effect_names)
        self._cards = {}
        self._active_filter = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Section label
        section = QLabel("EFFECTS")
        section.setObjectName("sectionLabel")
        layout.addWidget(section)

        # Search field
        search_row = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setObjectName("searchField")
        self.search.setPlaceholderText("Search effects...")
        self.search.textChanged.connect(self._filter_cards)
        search_row.addWidget(self.search)
        layout.addLayout(search_row)

        # Category filter buttons (two rows to avoid truncation)
        filter_grid = QGridLayout()
        filter_grid.setSpacing(4)
        self._filter_btns = {}

        all_btn = QPushButton("All")
        all_btn.setObjectName("filterBtn")
        all_btn.setCheckable(True)
        all_btn.setChecked(True)
        all_btn.clicked.connect(lambda: self._set_filter(None))
        filter_grid.addWidget(all_btn, 0, 0)
        self._filter_btns[None] = all_btn

        cats = list(EFFECT_CATEGORIES.keys())
        for i, cat in enumerate(cats):
            btn = QPushButton(cat)
            btn.setObjectName("filterBtn")
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, c=cat: self._set_filter(c))
            row = (i + 1) // 3
            col = (i + 1) % 3
            filter_grid.addWidget(btn, row, col)
            self._filter_btns[cat] = btn

        layout.addLayout(filter_grid)

        # Scrollable card list
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setFrameShape(QFrame.NoFrame)

        self.card_container = QWidget()
        self.card_layout = QVBoxLayout(self.card_container)
        self.card_layout.setContentsMargins(0, 0, 4, 0)
        self.card_layout.setSpacing(4)

        for name in self._effect_names:
            card = EffectCard(name)
            card.clicked.connect(lambda checked, n=name: self._on_card_clicked(n))
            self.card_layout.addWidget(card)
            self._cards[name] = card

        self.card_layout.addStretch()
        self.scroll.setWidget(self.card_container)
        layout.addWidget(self.scroll, 1)

    def _on_card_clicked(self, name):
        for n, card in self._cards.items():
            card.setChecked(n == name)
        self.effect_selected.emit(name)

    def select_effect(self, name):
        for n, card in self._cards.items():
            card.setChecked(n == name)

    def _set_filter(self, category):
        self._active_filter = category
        for cat, btn in self._filter_btns.items():
            btn.setChecked(cat == category)
        self._filter_cards(self.search.text())

    def _filter_cards(self, text):
        text = text.lower().strip()
        for name, card in self._cards.items():
            cat = _get_category(name)
            cat_match = self._active_filter is None or cat == self._active_filter
            text_match = not text or text in name.lower() or text in EFFECT_DESCRIPTIONS.get(name, "").lower()
            card.setVisible(cat_match and text_match)


# ─── Collapsible Group Box ───────────────────────────────────────────────────

class CollapsibleGroup(QWidget):
    """A parameter group that can be collapsed/expanded."""

    def __init__(self, title, parent=None):
        super().__init__(parent)
        self._collapsed = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header button
        self._header = QPushButton(f"\u25bc  {title}")
        self._header.setStyleSheet("""
            QPushButton {
                background-color: #141416;
                border: 1px solid #1e1e22;
                border-radius: 6px 6px 0 0;
                padding: 8px 12px;
                color: #44D62C;
                font-size: 12px;
                font-weight: bold;
                letter-spacing: 2px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #18181c;
                border-color: #44D62C;
            }
        """)
        self._header.setCursor(Qt.PointingHandCursor)
        self._header.clicked.connect(self._toggle)
        self._title = title
        layout.addWidget(self._header)

        # Content area
        self._content = QWidget()
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(10, 8, 10, 10)
        self._content_layout.setSpacing(6)
        self._content.setStyleSheet("""
            QWidget {
                background-color: #141416;
                border: 1px solid #1e1e22;
                border-top: none;
                border-radius: 0 0 6px 6px;
            }
        """)
        layout.addWidget(self._content)

    def add_widget(self, widget):
        self._content_layout.addWidget(widget)

    def _toggle(self):
        self._collapsed = not self._collapsed
        self._content.setVisible(not self._collapsed)
        arrow = "\u25b6" if self._collapsed else "\u25bc"
        self._header.setText(f"{arrow}  {self._title}")
        if self._collapsed:
            self._header.setStyleSheet(self._header.styleSheet().replace(
                "border-radius: 6px 6px 0 0", "border-radius: 6px"))
        else:
            self._header.setStyleSheet(self._header.styleSheet().replace(
                "border-radius: 6px;", "border-radius: 6px 6px 0 0;"))


# ─── Main Config Window ──────────────────────────────────────────────────────

class ConfigWindow(QMainWindow):
    def __init__(self, initial_effect=None):
        super().__init__()
        self.setWindowTitle("Razer Lighting")
        self.setMinimumSize(1000, 600)

        # Restore geometry
        self._settings = QSettings(SETTINGS_ORG, SETTINGS_APP)
        geo = self._settings.value("geometry")
        if geo:
            self.restoreGeometry(geo)
        else:
            self.resize(1200, 720)

        # State
        self.effects = discover_effects()
        self._params = []
        self._param_widgets = []
        self._dirty = False
        self._current_config_path = None
        self._current_effect_name = None
        self._current_module = None
        self._frame_count = 0
        self._fps_time = time.monotonic()

        # Detect keyboard dimensions
        self._rows, self._cols = detect_dimensions()

        # Preview runner
        self.preview = PreviewRunner(None, self._rows, self._cols)

        # Debounce timer for preview updates
        self._debounce_timer = QTimer()
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.setInterval(100)
        self._debounce_timer.timeout.connect(self._write_temp_config)

        # FPS counter timer
        self._fps_timer = QTimer()
        self._fps_timer.setInterval(1000)
        self._fps_timer.timeout.connect(self._update_fps)

        self._build_ui()
        self._fps_timer.start()

        # Select initial effect
        if initial_effect and initial_effect in self.effects:
            self.gallery.select_effect(initial_effect)
            self._on_effect_changed(initial_effect)
        elif self.effects:
            first = list(self.effects.keys())[0]
            self.gallery.select_effect(first)
            self._on_effect_changed(first)

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Left: Effect Gallery ──
        gallery_frame = QFrame()
        gallery_frame.setObjectName("galleryPanel")
        gallery_frame.setFixedWidth(280)
        gallery_layout = QVBoxLayout(gallery_frame)
        gallery_layout.setContentsMargins(0, 0, 0, 0)

        self.gallery = EffectGallery(list(self.effects.keys()))
        self.gallery.effect_selected.connect(self._on_effect_changed)
        gallery_layout.addWidget(self.gallery)

        # Hidden combo for compatibility (used by nothing now, but keeping for API)
        self.effect_combo = QComboBox()
        self.effect_combo.addItems(list(self.effects.keys()))
        self.effect_combo.setVisible(False)
        gallery_layout.addWidget(self.effect_combo)

        main_layout.addWidget(gallery_frame)

        # ── Right: Main content area ──
        right_area = QWidget()
        right_layout = QVBoxLayout(right_area)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # ── Header with effect info ──
        header_frame = QFrame()
        header_frame.setObjectName("headerPanel")
        header_frame.setFixedHeight(64)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(20, 8, 20, 8)

        header_text = QVBoxLayout()
        header_text.setSpacing(2)

        self._effect_title = QLabel("Select an effect")
        self._effect_title.setObjectName("effectTitle")
        header_text.addWidget(self._effect_title)

        info_row = QHBoxLayout()
        info_row.setSpacing(12)
        self._effect_category = QLabel("")
        self._effect_category.setObjectName("effectCategory")
        info_row.addWidget(self._effect_category)

        self._effect_desc = QLabel("")
        self._effect_desc.setObjectName("effectDescription")
        info_row.addWidget(self._effect_desc, 1)
        header_text.addLayout(info_row)

        header_layout.addLayout(header_text, 1)

        # Action buttons in header
        btn_group = QHBoxLayout()
        btn_group.setSpacing(6)

        self.save_btn = QPushButton("Save")
        self.save_btn.setObjectName("saveButton")
        self.save_btn.clicked.connect(self._save)
        btn_group.addWidget(self.save_btn)

        self.revert_btn = QPushButton("Revert")
        self.revert_btn.clicked.connect(self._revert)
        btn_group.addWidget(self.revert_btn)

        self.defaults_btn = QPushButton("Reset")
        self.defaults_btn.clicked.connect(self._reset_defaults)
        btn_group.addWidget(self.defaults_btn)

        header_layout.addLayout(btn_group)

        right_layout.addWidget(header_frame)

        # ── Splitter: visualizer top, params bottom ──
        splitter = QSplitter(Qt.Vertical)
        splitter.setHandleWidth(2)

        # Top: keyboard visualizer
        viz_frame = QFrame()
        viz_frame.setObjectName("vizPanel")
        viz_layout = QVBoxLayout(viz_frame)
        viz_layout.setContentsMargins(8, 8, 8, 4)

        self.visualizer = KeyboardVisualizer(self._rows, self._cols)
        self.preview.visualizer = self.visualizer
        viz_layout.addWidget(self.visualizer, 1)

        # Visualizer controls bar
        viz_controls = QHBoxLayout()
        viz_controls.setContentsMargins(4, 0, 4, 0)
        labels_btn = QPushButton("Labels")
        labels_btn.setFixedHeight(24)
        labels_btn.setStyleSheet("font-size: 11px; padding: 3px 12px;")
        labels_btn.clicked.connect(self.visualizer.toggle_labels)
        viz_controls.addWidget(labels_btn)
        viz_controls.addStretch()
        viz_layout.addLayout(viz_controls)

        splitter.addWidget(viz_frame)

        # Bottom: scrollable parameter panel
        param_frame = QFrame()
        param_frame.setObjectName("paramPanel")
        param_frame_layout = QVBoxLayout(param_frame)
        param_frame_layout.setContentsMargins(0, 0, 0, 0)

        # Parameters section label
        param_header = QHBoxLayout()
        param_header.setContentsMargins(14, 10, 14, 4)
        param_section = QLabel("PARAMETERS")
        param_section.setObjectName("sectionLabel")
        param_header.addWidget(param_section)
        param_header.addStretch()
        param_frame_layout.addLayout(param_header)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.param_container = QWidget()
        self.param_layout = QVBoxLayout(self.param_container)
        self.param_layout.setContentsMargins(10, 4, 10, 10)
        self.param_layout.setSpacing(6)
        self.param_layout.addStretch()
        self.scroll.setWidget(self.param_container)
        param_frame_layout.addWidget(self.scroll)

        splitter.addWidget(param_frame)
        splitter.setSizes([400, 280])

        right_layout.addWidget(splitter, 1)
        main_layout.addWidget(right_area, 1)

        # ── Status Bar ──
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self._status_effect = QLabel("")
        self._status_fps = QLabel("")
        self._status_device = QLabel(f"{self._cols}x{self._rows} matrix")
        self._status_dirty = QLabel("")

        self.status_bar.addWidget(self._status_effect)
        self.status_bar.addWidget(self._make_status_separator())
        self.status_bar.addWidget(self._status_fps)
        self.status_bar.addPermanentWidget(self._status_dirty)
        self.status_bar.addPermanentWidget(self._make_status_separator())
        self.status_bar.addPermanentWidget(self._status_device)

    def _make_status_separator(self):
        sep = QLabel("\u00b7")
        sep.setStyleSheet("color: #2a2a2e; font-size: 14px;")
        return sep

    def _update_fps(self):
        now = time.monotonic()
        elapsed = now - self._fps_time
        if elapsed > 0:
            fps = self._frame_count / elapsed
            self._status_fps.setText(f"{fps:.0f} fps")
        self._frame_count = 0
        self._fps_time = now

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
                self.gallery.select_effect(self._current_effect_name)
                return

        self._current_effect_name = effect_name
        self._current_module = self.effects[effect_name]
        self._current_config_path = get_config_path_for_effect(self._current_module)

        # Update header
        self._effect_title.setText(effect_name)
        category = _get_category(effect_name)
        icon = CATEGORY_ICONS.get(category, "")
        self._effect_category.setText(f"{icon} {category.upper()}")
        self._effect_desc.setText(EFFECT_DESCRIPTIONS.get(effect_name, ""))
        self._status_effect.setText(effect_name)

        # Sync combo (kept for compat)
        self.effect_combo.blockSignals(True)
        idx = list(self.effects.keys()).index(effect_name)
        self.effect_combo.setCurrentIndex(idx)
        self.effect_combo.blockSignals(False)

        if self._current_config_path and os.path.exists(self._current_config_path):
            self._params = parse_config(self._current_config_path)
            save_defaults(effect_name, self._params)
        else:
            self._params = []

        self._rebuild_params()
        self._set_dirty(False)
        self._start_preview()

    def _rebuild_params(self):
        """Rebuild the parameter panel with collapsible groups."""
        self._param_widgets = []
        while self.param_layout.count():
            item = self.param_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        if not self._params:
            no_params = QLabel("No configurable parameters.")
            no_params.setStyleSheet("color: #505060; font-style: italic; padding: 20px; font-size: 13px;")
            no_params.setAlignment(Qt.AlignCenter)
            self.param_layout.addWidget(no_params)
            self.param_layout.addStretch()
            return

        groups = group_params(self._params)
        for group_name, group_params_list in groups.items():
            group = CollapsibleGroup(group_name.upper())

            for param in group_params_list:
                widget = create_param_widget(param)
                if widget:
                    widget.value_changed.connect(self._on_param_changed)
                    group.add_widget(widget)
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
            self.setWindowTitle(f"Razer Lighting \u2014 {name} \u2022")
            self._status_dirty.setText("\u2022 unsaved")
            self._status_dirty.setStyleSheet(
                "color: #cc8800; font-size: 12px; font-weight: bold;"
                " font-family: 'JetBrains Mono', monospace;")
        else:
            self.setWindowTitle(f"Razer Lighting \u2014 {name}")
            self._status_dirty.setText("")

    def _collect_values(self):
        for param, widget in self._param_widgets:
            param.value = widget.get_value()

    def _write_temp_config(self):
        if not self._current_config_path:
            return
        self._collect_values()
        temp_path = write_temp_config(self._current_config_path, self._params)
        return temp_path

    def _start_preview(self):
        self.preview.stop()
        if not self._current_module or not self._current_config_path:
            return

        temp_path = write_temp_config(self._current_config_path, self._params)

        # Hook frame counter into visualizer
        orig_update = self.visualizer._update_frame
        def counting_update(snapshot):
            self._frame_count += 1
            orig_update(snapshot)
        self.visualizer._update_frame_counted = counting_update
        self.visualizer.frame_signal.disconnect()
        self.visualizer.frame_signal.connect(counting_update)

        self.preview.start(self._current_module, temp_config_path=temp_path)

    def _save(self):
        if not self._current_config_path:
            return
        self._collect_values()
        write_config(self._current_config_path, self._params)
        self._set_dirty(False)

    def _revert(self):
        if not self._current_config_path:
            return
        self._params = parse_config(self._current_config_path)
        self._rebuild_params()
        self._set_dirty(False)
        self._start_preview()

    def _reset_defaults(self):
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

        self._settings.setValue("geometry", self.saveGeometry())
        self.preview.cleanup()
        event.accept()


def _make_app_icon():
    """Generate a keyboard icon with teal-green glow for the window/taskbar."""
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

        # Glow behind keyboard
        glow = QRadialGradient(sz / 2, sz / 2, sz * 0.45)
        glow.setColorAt(0.0, QColor(68, 214, 44, 50))
        glow.setColorAt(1.0, QColor(68, 214, 44, 0))
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(glow))
        p.drawEllipse(0, 0, sz, sz)

        # Keyboard body
        p.setBrush(QBrush(QColor(17, 17, 19)))
        p.setPen(QPen(QColor(68, 214, 44), max(1, sz / 24)))
        cr = sz * 0.12
        p.drawRoundedRect(int(margin), int(margin + h * 0.1),
                          int(w), int(h * 0.8), cr, cr)
        # Key grid
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(QColor(68, 214, 44)))
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
