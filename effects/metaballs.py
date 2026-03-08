#!/usr/bin/env python3
"""Metaballs - molten lava blobs merge and separate across the keyboard.

Several charge points (blobs) drift on Lissajous-like paths. For every
pixel the scalar field is evaluated as sum(radius^2 / dist^2) over all
blobs. The field value is then mapped through a molten-lava palette:
black edges, red glow, orange fringe, yellow-white cores where blobs
merge.

Edit metaballs_config.py while running to tweak on the fly.
"""

import math
import os
import random
import time

import numpy as np

from effects.common import (
    load_config, draw_frame, clear_keyboard, frame_sleep,
    build_palette_lut, palette_lookup, make_coordinate_grids,
    standalone_main,
)

EFFECT_NAME = "Metaballs"
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "metaballs_config.py")


def run(device, stop_event):
    """Run the metaballs effect."""
    rows = device.fx.advanced.rows
    cols = device.fx.advanced.cols

    # Coordinate grids: row_grid(rows, cols), col_grid(rows, cols)
    row_grid, col_grid = make_coordinate_grids(rows, cols)

    t = 0.0

    # Initialize blob parameters with distinct Lissajous frequencies/phases
    rng = random.Random()
    blobs = []
    for i in range(5):  # pre-allocate max; NUM_BLOBS from config selects how many to use
        blobs.append({
            "freq_x": rng.uniform(0.7, 2.5),
            "freq_y": rng.uniform(0.5, 2.0),
            "phase_x": rng.uniform(0, 2 * math.pi),
            "phase_y": rng.uniform(0, 2 * math.pi),
        })

    next_frame = time.monotonic()

    while not stop_event.is_set():
        cfg = load_config(CONFIG_PATH)
        interval = 1.0 / cfg.get("FPS", 24)
        num_blobs = cfg.get("NUM_BLOBS", 4)
        blob_radius = cfg.get("BLOB_RADIUS", 1.5)
        speed = cfg.get("SPEED", 0.015)
        aspect = cfg.get("ASPECT_RATIO", 2.2)
        threshold = cfg.get("THRESHOLD", 1.0)
        palette = cfg.get("PALETTE", [
            (0, 0, 0), (80, 0, 0), (200, 30, 0),
            (255, 100, 0), (255, 200, 50), (255, 255, 200),
        ])

        lut = build_palette_lut(palette)

        # Clamp to available blobs
        num_blobs = min(num_blobs, len(blobs))

        r_sq = blob_radius * blob_radius

        # Accumulate field across all blobs (vectorized over the grid)
        field = np.zeros((rows, cols), dtype=np.float64)
        for i in range(num_blobs):
            b = blobs[i]
            bx = (math.sin(b["freq_x"] * t + b["phase_x"]) + 1.0) / 2.0 * (cols - 1)
            by = (math.sin(b["freq_y"] * t + b["phase_y"]) + 1.0) / 2.0 * (rows - 1)
            dx = (col_grid - bx) / aspect
            dy = row_grid - by
            dist_sq = dx * dx + dy * dy
            dist_sq = np.maximum(dist_sq, 0.001)
            field += r_sq / dist_sq

        # Map field to palette: normalize then clamp
        norm = field / threshold
        palette_t = np.minimum(norm * 0.5, 1.0)
        # Where field < 0.01, force to black (palette_t = 0 maps to black anyway
        # since palette starts at black, but enforce for safety)
        palette_t = np.where(field < 0.01, 0.0, palette_t)

        frame_rgb = palette_lookup(lut, palette_t)
        draw_frame(device, frame_rgb)

        t += speed
        next_frame = frame_sleep(next_frame, interval)

    clear_keyboard(device)


def main():
    """Standalone entry point."""
    standalone_main(EFFECT_NAME, run)


if __name__ == "__main__":
    main()
