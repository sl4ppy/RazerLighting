#!/usr/bin/env python3
"""Magnetic Field Lines - iron filings visualization of drifting magnetic poles.

Four magnetic poles (positive and negative) drift across the keyboard
on Lissajous paths. The field is visualized as iron filing patterns:
bright lines aligned with the local field direction, with red glow
near positive poles and blue glow near negative poles.

Edit magnetic_field_config.py while running to tweak on the fly.
"""

import math
import os
import random
import time

import numpy as np

from effects.common import (
    load_config, draw_frame, clear_keyboard, frame_sleep,
    make_coordinate_grids, standalone_main,
)

EFFECT_NAME = "Magnetic Field Lines"
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "magnetic_field_config.py")


def run(device, stop_event):
    """Run the magnetic field lines effect."""
    rows = device.fx.advanced.rows
    cols = device.fx.advanced.cols

    # Coordinate grids
    row_grid, col_grid = make_coordinate_grids(rows, cols)

    t = 0.0

    # Initialize poles with random Lissajous parameters
    poles = []
    for i in range(4):
        charge = 1.0 if i % 2 == 0 else -1.0
        cx = random.uniform(3.0, cols - 4.0)
        cy = random.uniform(1.0, rows - 2.0)
        ax = random.uniform(2.0, min(cx, cols - 1 - cx))
        ay = random.uniform(0.5, min(cy, rows - 1 - cy))
        fx = random.uniform(0.3, 1.2)
        fy = random.uniform(0.3, 1.2)
        px = random.uniform(0, 2 * math.pi)
        py = random.uniform(0, 2 * math.pi)
        poles.append({
            "charge": charge,
            "cx": cx, "cy": cy,
            "ax": ax, "ay": ay,
            "fx": fx, "fy": fy,
            "px": px, "py": py,
        })

    next_frame = time.monotonic()

    while not stop_event.is_set():
        cfg = load_config(CONFIG_PATH)
        interval = 1.0 / cfg.get("FPS", 20)
        num_poles = cfg.get("NUM_POLES", 4)
        pole_speed = cfg.get("POLE_SPEED", 0.006)
        pole_glow_radius = cfg.get("POLE_GLOW_RADIUS", 2.5)
        pole_glow_intensity = cfg.get("POLE_GLOW_INTENSITY", 0.6)
        num_lines = cfg.get("NUM_LINES", 6)
        field_scale = cfg.get("FIELD_SCALE", 0.3)
        line_color = cfg.get("LINE_COLOR", (0, 200, 220))
        pos_pole_color = cfg.get("POS_POLE_COLOR", (255, 40, 40))
        neg_pole_color = cfg.get("NEG_POLE_COLOR", (40, 40, 255))
        bg = cfg.get("BG_COLOR", (0, 2, 5))

        # Ensure we have enough poles
        while len(poles) < num_poles:
            charge = 1.0 if len(poles) % 2 == 0 else -1.0
            poles.append({
                "charge": charge,
                "cx": random.uniform(3.0, cols - 4.0),
                "cy": random.uniform(1.0, rows - 2.0),
                "ax": random.uniform(2.0, 5.0),
                "ay": random.uniform(0.5, 1.5),
                "fx": random.uniform(0.3, 1.2),
                "fy": random.uniform(0.3, 1.2),
                "px": random.uniform(0, 2 * math.pi),
                "py": random.uniform(0, 2 * math.pi),
            })

        epsilon = 0.1

        # Accumulate field vectors across all poles (vectorized over grid)
        field_x = np.zeros((rows, cols), dtype=np.float64)
        field_y = np.zeros((rows, cols), dtype=np.float64)

        # Compute current pole positions and accumulate field
        pole_positions = []
        for i in range(num_poles):
            p = poles[i]
            px_pos = p["cx"] + p["ax"] * math.sin(p["fx"] * t * pole_speed + p["px"])
            py_pos = p["cy"] + p["ay"] * math.sin(p["fy"] * t * pole_speed + p["py"])
            px_pos = max(0.0, min(cols - 1.0, px_pos))
            py_pos = max(0.0, min(rows - 1.0, py_pos))
            charge = p["charge"]
            pole_positions.append((px_pos, py_pos, charge))

            dx = col_grid - px_pos
            dy = row_grid - py_pos
            dist = np.sqrt(dx * dx + dy * dy) + epsilon
            strength = charge / (dist * dist)
            field_x += strength * dx / dist
            field_y += strength * dy / dist

        # Iron filings visualization (vectorized)
        field_mag = np.sqrt(field_x * field_x + field_y * field_y)
        angle = np.arctan2(field_y, field_x)
        magnitude_factor = np.minimum(1.0, field_mag * field_scale)
        brightness = np.abs(np.sin(num_lines * angle)) * magnitude_factor

        # Base color from field lines: lerp from bg to line_color by brightness
        bg_arr = np.array(bg, dtype=np.float64)
        line_arr = np.array(line_color, dtype=np.float64)
        # frame shape: (rows, cols, 3)
        frame = np.zeros((rows, cols, 3), dtype=np.float64)
        for ch in range(3):
            frame[:, :, ch] = bg_arr[ch] + brightness * (line_arr[ch] - bg_arr[ch])

        # Add pole glow (additive, vectorized per pole)
        pos_arr = np.array(pos_pole_color, dtype=np.float64)
        neg_arr = np.array(neg_pole_color, dtype=np.float64)
        for px_pos, py_pos, charge in pole_positions:
            dx = col_grid - px_pos
            dy = row_grid - py_pos
            dist = np.sqrt(dx * dx + dy * dy)
            mask = dist < pole_glow_radius
            glow = np.where(mask, (1.0 - dist / pole_glow_radius) * pole_glow_intensity, 0.0)
            glow_color = pos_arr if charge > 0 else neg_arr
            for ch in range(3):
                frame[:, :, ch] += glow * glow_color[ch]

        # Clamp to 0-255 and convert to uint8
        frame_rgb = np.clip(frame, 0, 255).astype(np.uint8)

        draw_frame(device, frame_rgb)
        t += 1.0
        next_frame = frame_sleep(next_frame, interval)

    clear_keyboard(device)


def main():
    """Standalone entry point."""
    standalone_main(EFFECT_NAME, run)


if __name__ == "__main__":
    main()
