#!/usr/bin/env python3
"""Chladni Patterns - vibrating plate nodal line visualization.

Simulates Chladni figures with flowing wave animation, gradient-based edge
glow, and chromatic displacement.  Mode pairs crossfade with smoothstep
blending while a travelling phase makes the nodal lines drift and ripple.
"""

import math
import os
import time

import numpy as np

from effects.common import (
    load_config, draw_frame, clear_keyboard, frame_sleep,
    make_coordinate_grids, build_palette_lut, palette_lookup,
    standalone_main,
)

EFFECT_NAME = "Chladni Patterns"
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chladni_config.py")

# Default palettes
_DEF_NODAL_PALETTE = [
    (0, 2, 12),
    (0, 15, 50),
    (5, 70, 130),
    (0, 180, 220),
    (100, 240, 255),
    (210, 255, 255),
    (255, 255, 255),
]
_DEF_ANTI_PALETTE = [
    (0, 0, 0),
    (40, 5, 0),
    (120, 30, 0),
    (255, 80, 10),
    (255, 160, 60),
]


def _chladni(x, y, n, m, phase):
    """Chladni field value with travelling-wave phase offsets."""
    return (np.sin(np.pi * n * x + phase * 0.7) *
            np.sin(np.pi * m * y - phase * 0.5)
            + np.sin(np.pi * m * x - phase * 0.3) *
            np.sin(np.pi * n * y + phase * 0.6))


def _gradient_mag(v, rows, cols):
    """Spatial gradient magnitude via finite differences."""
    gx = np.zeros_like(v)
    gy = np.zeros_like(v)
    if cols > 2:
        gx[:, 1:-1] = (v[:, 2:] - v[:, :-2]) * 0.5
        gx[:, 0] = v[:, 1] - v[:, 0]
        gx[:, -1] = v[:, -1] - v[:, -2]
    if rows > 2:
        gy[1:-1, :] = (v[2:, :] - v[:-2, :]) * 0.5
        gy[0, :] = v[1, :] - v[0, :]
        gy[-1, :] = v[-1, :] - v[-2, :]
    mag = np.sqrt(gx * gx + gy * gy)
    return gx, gy, mag


def run(device, stop_event):
    """Run the Chladni patterns effect."""
    rows = device.fx.advanced.rows
    cols = device.fx.advanced.cols

    row_grid, col_grid = make_coordinate_grids(rows, cols)

    x_norm = col_grid / max(cols - 1, 1)
    y_norm = row_grid / max(rows - 1, 1)

    t = 0.0
    next_frame = time.monotonic()

    while not stop_event.is_set():
        cfg = load_config(CONFIG_PATH)
        fps = cfg.get("FPS", 20)
        interval = 1.0 / fps
        nodal_width = cfg.get("NODAL_WIDTH", 0.35)
        morph_speed = cfg.get("MORPH_SPEED", 0.008)
        wave_speed = cfg.get("WAVE_SPEED", 0.4)
        pulse_speed = cfg.get("PULSE_SPEED", 0.06)
        edge_glow = cfg.get("EDGE_GLOW", 0.7)
        chromatic_spread = cfg.get("CHROMATIC_SPREAD", 0.08)
        mode_pairs = cfg.get("MODE_PAIRS", [
            (2, 3), (3, 5), (4, 3), (5, 2), (1, 4), (3, 4),
        ])
        nodal_palette = cfg.get("NODAL_PALETTE", _DEF_NODAL_PALETTE)
        anti_palette = cfg.get("ANTINODE_PALETTE", _DEF_ANTI_PALETTE)

        lut_nodal = build_palette_lut(nodal_palette)
        lut_anti = build_palette_lut(anti_palette)

        num_pairs = len(mode_pairs)
        if num_pairs == 0:
            next_frame, dt = frame_sleep(next_frame, interval)
            t += dt * fps
            continue

        # Current / next mode pair with smoothstep crossfade
        morph_phase = (t * morph_speed) % num_pairs
        pair_idx = int(morph_phase) % num_pairs
        next_idx = (pair_idx + 1) % num_pairs
        blend = morph_phase - int(morph_phase)
        blend = blend * blend * (3.0 - 2.0 * blend)  # smoothstep

        n1, m1 = mode_pairs[pair_idx]
        n2, m2 = mode_pairs[next_idx]

        phase = t * wave_speed

        v1 = _chladni(x_norm, y_norm, n1, m1, phase)
        v2 = _chladni(x_norm, y_norm, n2, m2, -phase * 0.7)
        v = v1 * (1.0 - blend) + v2 * blend

        # Nodal brightness (Gaussian peak where |v| ≈ 0)
        w2 = nodal_width * nodal_width
        nodal_b = np.exp(-(v * v) / w2)

        # Edge glow: gradient magnitude amplifies brightness at steep transitions
        gx, gy, gmag = _gradient_mag(v, rows, cols)
        gmax = gmag.max()
        if gmax > 0:
            gmag_n = gmag / gmax
        else:
            gmag_n = gmag
        edge_boost = nodal_b * gmag_n * edge_glow
        brightness = np.clip(nodal_b + edge_boost, 0.0, 1.0)

        # Dual-frequency breathing pulse
        pulse = (0.75 + 0.2 * math.sin(t * pulse_speed)
                 + 0.05 * math.sin(t * pulse_speed * 2.7))
        brightness = np.clip(brightness * pulse, 0.0, 1.0)

        # Chromatic displacement: shift R and B along gradient direction
        if chromatic_spread > 0 and gmax > 0:
            safe_mag = np.maximum(gmag, 1e-6)
            dx = gx / safe_mag
            offset_r = np.clip(brightness + chromatic_spread * dx * nodal_b, 0, 1)
            offset_b = np.clip(brightness - chromatic_spread * dx * nodal_b, 0, 1)
        else:
            offset_r = brightness
            offset_b = brightness

        # Map through palette LUTs with per-channel chromatic split
        r_ch = palette_lookup(lut_nodal, offset_r)[:, :, 0]
        g_ch = palette_lookup(lut_nodal, brightness)[:, :, 1]
        b_ch = palette_lookup(lut_nodal, offset_b)[:, :, 2]

        # Anti-node warmth (high-amplitude regions)
        anti_b = np.clip(1.0 - nodal_b, 0.0, 1.0)
        anti_b = anti_b ** 2.5 * pulse * 0.4
        anti_rgb = palette_lookup(lut_anti, anti_b)

        frame_rgb = np.stack([r_ch, g_ch, b_ch], axis=-1).astype(np.float64)
        frame_rgb += anti_rgb.astype(np.float64)
        frame_rgb = np.clip(frame_rgb, 0, 255).astype(np.uint8)

        draw_frame(device, frame_rgb)
        next_frame, dt = frame_sleep(next_frame, interval)
        t += dt * fps

    clear_keyboard(device)


def main():
    """Standalone entry point."""
    standalone_main(EFFECT_NAME, run)


if __name__ == "__main__":
    main()
