#!/usr/bin/env python3
"""Magnetic Field Lines - iron filings visualization of drifting magnetic poles.

Magnetic poles drift across the keyboard on Lissajous paths.  Iron filing
patterns flow along field lines with speed proportional to local field
strength.  Pole glow and polarity-tinted coloring show field structure.

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
        fps = cfg.get("FPS", 20)
        interval = 1.0 / fps
        num_poles = cfg.get("NUM_POLES", 4)
        pole_speed = cfg.get("POLE_SPEED", 0.05)
        pole_glow_radius = cfg.get("POLE_GLOW_RADIUS", 2.5)
        pole_glow_intensity = cfg.get("POLE_GLOW_INTENSITY", 0.6)
        num_lines = cfg.get("NUM_LINES", 3)
        field_scale = cfg.get("FIELD_SCALE", 0.3)
        flow_speed = cfg.get("FLOW_SPEED", 1.5)
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

        epsilon = 0.3

        # Accumulate field vectors and scalar potential
        field_x = np.zeros((rows, cols), dtype=np.float64)
        field_y = np.zeros((rows, cols), dtype=np.float64)
        potential = np.zeros((rows, cols), dtype=np.float64)

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
            potential += charge / dist

        # Field magnitude and angle
        field_mag = np.sqrt(field_x * field_x + field_y * field_y)
        angle = np.arctan2(field_y, field_x)

        # Magnitude factor with sqrt for more dynamic range
        magnitude_factor = np.sqrt(np.minimum(1.0, field_mag * field_scale))

        # Animated iron filings: phase flows along field lines
        # Use potential as spatial phase offset so flow varies with field structure
        flow_phase = t * flow_speed
        filing_pattern = np.abs(np.sin(num_lines * angle + potential * 2.0 + flow_phase))
        brightness = filing_pattern * magnitude_factor

        # Add a soft ambient field glow (visible even between filing lines)
        ambient = magnitude_factor * 0.15
        brightness = np.clip(brightness + ambient, 0.0, 1.0)

        # Polarity coloring
        polarity = np.zeros((rows, cols), dtype=np.float64)
        for px_pos, py_pos, charge in pole_positions:
            dx = col_grid - px_pos
            dy = row_grid - py_pos
            dist = np.sqrt(dx * dx + dy * dy) + epsilon
            polarity += charge / (dist + 1.0)
        pol_max = max(np.abs(polarity).max(), 0.01)
        polarity = np.clip(polarity / pol_max, -1.0, 1.0)

        bg_arr = np.array(bg, dtype=np.float64)
        line_arr = np.array(line_color, dtype=np.float64)
        pos_tint = np.array(pos_pole_color, dtype=np.float64) * 0.4 + line_arr * 0.6
        neg_tint = np.array(neg_pole_color, dtype=np.float64) * 0.4 + line_arr * 0.6

        pos_blend = np.maximum(polarity, 0.0)[:, :, np.newaxis]
        neg_blend = np.maximum(-polarity, 0.0)[:, :, np.newaxis]
        local_line = (
            line_arr[np.newaxis, np.newaxis, :] * (1.0 - pos_blend - neg_blend)
            + pos_tint[np.newaxis, np.newaxis, :] * pos_blend
            + neg_tint[np.newaxis, np.newaxis, :] * neg_blend
        )

        frame = (
            bg_arr[np.newaxis, np.newaxis, :]
            + (local_line - bg_arr[np.newaxis, np.newaxis, :]) * brightness[:, :, np.newaxis]
        )

        # Pole glow (Gaussian falloff)
        pos_arr = np.array(pos_pole_color, dtype=np.float64)
        neg_arr = np.array(neg_pole_color, dtype=np.float64)
        r_sq = pole_glow_radius * pole_glow_radius
        for px_pos, py_pos, charge in pole_positions:
            dx = col_grid - px_pos
            dy = row_grid - py_pos
            dist_sq = dx * dx + dy * dy
            glow = np.exp(-dist_sq / r_sq) * pole_glow_intensity
            glow_color = pos_arr if charge > 0 else neg_arr
            frame += glow[:, :, np.newaxis] * glow_color[np.newaxis, np.newaxis, :]

        frame_rgb = np.clip(frame, 0, 255).astype(np.uint8)

        draw_frame(device, frame_rgb)
        next_frame, dt = frame_sleep(next_frame, interval)
        t += dt * fps

    clear_keyboard(device)


def main():
    """Standalone entry point."""
    standalone_main(EFFECT_NAME, run)


if __name__ == "__main__":
    main()
