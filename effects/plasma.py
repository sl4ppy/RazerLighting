#!/usr/bin/env python3
"""Plasma - classic demoscene plasma effect with layered sine waves.

Multiple sine waves at different frequencies and phases combine to
create organic, flowing color fields across the keyboard. An optional
second plasma layer adds visual complexity.
"""

import os
import time

import numpy as np

from effects.common import (
    load_config, draw_frame, clear_keyboard, frame_sleep,
    build_palette_lut, palette_lookup, make_coordinate_grids,
    standalone_main,
)

EFFECT_NAME = "Plasma"
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "plasma_config.py")


def run(device, stop_event):
    """Run the plasma effect."""
    rows = device.fx.advanced.rows
    cols = device.fx.advanced.cols

    row_grid, col_grid = make_coordinate_grids(rows, cols)

    t = 0.0
    next_frame = time.monotonic()

    while not stop_event.is_set():
        cfg = load_config(CONFIG_PATH)
        fps = cfg.get("FPS", 20)
        interval = 1.0 / fps
        scale_x = cfg.get("SCALE_X", 0.35)
        scale_y = cfg.get("SCALE_Y", 0.6)
        time_speed = cfg.get("TIME_SPEED", 0.04)
        palette = cfg.get("PALETTE", [(0, 60, 20), (0, 255, 30), (0, 60, 20)])

        overlay = cfg.get("OVERLAY", True)
        overlay_sx = cfg.get("OVERLAY_SCALE_X", 0.5)
        overlay_sy = cfg.get("OVERLAY_SCALE_Y", 0.3)
        overlay_ts = cfg.get("OVERLAY_TIME_SPEED", 0.03)
        overlay_blend = cfg.get("OVERLAY_BLEND", 0.35)

        lut = build_palette_lut(palette)

        phase = t * time_speed
        phase2 = t * overlay_ts

        # Precompute scaled coordinates
        cx = col_grid * scale_x
        ry = row_grid * scale_y

        # Classic plasma: sum of sine waves at different angles
        v1 = np.sin(cx + phase)
        v2 = np.sin(ry + phase * 1.3)
        v3 = np.sin((cx + ry) * 0.5 + phase * 0.7)
        v4 = np.sin(np.sqrt(cx ** 2 + ry ** 2) + phase * 0.9)

        value = (v1 + v2 + v3 + v4) / 4.0  # -1..1
        value = (value + 1.0) / 2.0  # 0..1

        frame_rgb = palette_lookup(lut, value)

        # Optional overlay plasma
        if overlay:
            ocx = col_grid * overlay_sx
            ory = row_grid * overlay_sy

            o1 = np.sin(ocx + phase2 * 1.1 + 2.0)
            o2 = np.sin(ory + phase2 * 0.8 + 1.0)
            o3 = np.sin((ocx - ory) * 0.6 + phase2)

            ov = (o1 + o2 + o3) / 3.0
            ov = (ov + 1.0) / 2.0

            overlay_rgb = palette_lookup(lut, ov)

            # Blend: color = color * (1 - weight) + overlay_color * weight
            frame_rgb = (
                frame_rgb.astype(np.float64) * (1.0 - overlay_blend)
                + overlay_rgb.astype(np.float64) * overlay_blend
            ).astype(np.uint8)

        draw_frame(device, frame_rgb)
        next_frame, dt = frame_sleep(next_frame, interval)
        t += dt * fps

    clear_keyboard(device)


def main():
    """Standalone entry point."""
    standalone_main(EFFECT_NAME, run)


if __name__ == "__main__":
    main()
