#!/usr/bin/env python3
"""Chladni Patterns - vibrating plate nodal line visualization.

Simulates Chladni figures by computing the vibration amplitude across
the keyboard and highlighting nodal lines (where amplitude is near zero)
with bright azure. Mode pairs morph over time for endless variation,
and a gentle breathing pulse keeps it alive.
"""

import math
import os
import time

import numpy as np

from effects.common import (
    load_config, draw_frame, clear_keyboard, frame_sleep,
    make_coordinate_grids, standalone_main,
)

EFFECT_NAME = "Chladni Patterns"
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chladni_config.py")


def run(device, stop_event):
    """Run the Chladni patterns effect."""
    rows = device.fx.advanced.rows
    cols = device.fx.advanced.cols

    row_grid, col_grid = make_coordinate_grids(rows, cols)

    # Normalized coordinates (0..1)
    x_norm = col_grid / max(cols - 1, 1)
    y_norm = row_grid / max(rows - 1, 1)

    t = 0.0
    next_frame = time.monotonic()

    while not stop_event.is_set():
        cfg = load_config(CONFIG_PATH)
        fps = cfg.get("FPS", 20)
        interval = 1.0 / fps
        nodal_width = cfg.get("NODAL_WIDTH", 0.4)
        morph_speed = cfg.get("MORPH_SPEED", 0.008)
        pulse_speed = cfg.get("PULSE_SPEED", 0.06)
        mode_pairs = cfg.get("MODE_PAIRS", [(2, 3), (3, 5), (4, 3), (5, 2), (1, 4), (3, 4)])
        line_color = cfg.get("LINE_COLOR", (0, 200, 255))
        antinode_color = cfg.get("ANTINODE_COLOR", (255, 100, 0))
        bg_color = cfg.get("BG_COLOR", (0, 2, 8))

        num_pairs = len(mode_pairs)
        if num_pairs == 0:
            next_frame, dt = frame_sleep(next_frame, interval)
            t += dt * fps
            continue

        # Determine current and next mode pair for crossfade
        morph_phase = (t * morph_speed) % num_pairs
        pair_idx = int(morph_phase) % num_pairs
        next_idx = (pair_idx + 1) % num_pairs
        blend = morph_phase - int(morph_phase)  # 0..1 crossfade factor

        n1, m1 = mode_pairs[pair_idx]
        n2, m2 = mode_pairs[next_idx]

        # Chladni values for current mode pair:
        # v = a*sin(pi*n*x)*sin(pi*m*y) + b*sin(pi*m*x)*sin(pi*n*y)
        v1 = (np.sin(np.pi * n1 * x_norm) * np.sin(np.pi * m1 * y_norm)
              + np.sin(np.pi * m1 * x_norm) * np.sin(np.pi * n1 * y_norm))

        # Chladni values for next mode pair
        v2 = (np.sin(np.pi * n2 * x_norm) * np.sin(np.pi * m2 * y_norm)
              + np.sin(np.pi * m2 * x_norm) * np.sin(np.pi * n2 * y_norm))

        # Crossfade between mode pairs
        v = v1 * (1.0 - blend) + v2 * blend

        # Gaussian brightness peak at nodal lines (|v| near 0)
        w2 = nodal_width * nodal_width
        brightness = np.exp(-(v * v) / w2)

        # Breathing pulse
        pulse = 0.7 + 0.3 * math.sin(t * pulse_speed)
        brightness = brightness * pulse

        # Clamp
        brightness = np.clip(brightness, 0.0, 1.0)

        # Dual-tone coloring: nodal lines (|v| near 0) get line_color,
        # anti-nodes (|v| large) get antinode_color, bg in between
        bg_arr = np.array(bg_color, dtype=np.float64)
        line_arr = np.array(line_color, dtype=np.float64)
        anti_arr = np.array(antinode_color, dtype=np.float64)

        # Anti-node brightness: peaks where |v| is large (inverse of nodal)
        anti_brightness = np.clip(1.0 - brightness, 0.0, 1.0)
        # Sharpen the anti-node glow to only show in high-amplitude regions
        anti_brightness = anti_brightness ** 2.5 * pulse * 0.5

        frame_rgb = (
            bg_arr[np.newaxis, np.newaxis, :]
            + (line_arr - bg_arr)[np.newaxis, np.newaxis, :] * brightness[:, :, np.newaxis]
            + (anti_arr - bg_arr)[np.newaxis, np.newaxis, :] * anti_brightness[:, :, np.newaxis]
        )
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
