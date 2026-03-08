#!/usr/bin/env python3
"""Reaction-Diffusion - Gray-Scott model on the keyboard.

Two chemicals A and B interact via the Gray-Scott equations, producing
organic, cell-like patterns that split, pulse, and reform endlessly.
Chemical B concentration is mapped to a bioluminescent teal-cyan palette.

Edit reaction_diffusion_config.py while running to tweak on the fly.
"""

import os
import random
import time

import numpy as np

from effects.common import (
    load_config, draw_frame, clear_keyboard, frame_sleep,
    build_palette_lut, palette_lookup, laplacian_9pt, standalone_main,
)

EFFECT_NAME = "Reaction-Diffusion"
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reaction_diffusion_config.py")


def seed_patches(B, rows, cols, count=None):
    """Place small random 2x2 patches of B=1.0."""
    if count is None:
        count = random.randint(3, 5)
    for _ in range(count):
        r0 = random.randint(0, rows - 1)
        c0 = random.randint(0, cols - 1)
        for dr in range(2):
            for dc in range(2):
                B[(r0 + dr) % rows, (c0 + dc) % cols] = 1.0


def run(device, stop_event):
    """Run the reaction-diffusion effect."""
    rows = device.fx.advanced.rows
    cols = device.fx.advanced.cols

    # Initialize grids
    A = np.ones((rows, cols), dtype=np.float64)
    B = np.zeros((rows, cols), dtype=np.float64)

    # Seed initial patches
    seed_patches(B, rows, cols)

    next_frame = time.monotonic()

    while not stop_event.is_set():
        cfg = load_config(CONFIG_PATH)
        interval = 1.0 / cfg.get("FPS", 20)
        feed = cfg.get("FEED", 0.0367)
        kill = cfg.get("KILL", 0.0649)
        d_a = cfg.get("D_A", 1.0)
        d_b = cfg.get("D_B", 0.5)
        sim_steps = cfg.get("SIM_STEPS", 8)
        palette = cfg.get("PALETTE", [(0, 0, 0), (0, 80, 80), (150, 255, 230)])
        reseed_threshold = cfg.get("RESEED_THRESHOLD", 0.5)
        dt = 1.0

        # Build palette LUT for rendering
        lut = build_palette_lut(palette)

        # Run simulation steps
        for _ in range(sim_steps):
            lap_a = laplacian_9pt(A)
            lap_b = laplacian_9pt(B)
            ab2 = A * B * B

            A += (d_a * lap_a - ab2 + feed * (1.0 - A)) * dt
            B += (d_b * lap_b + ab2 - (kill + feed) * B) * dt

            np.clip(A, 0.0, 1.0, out=A)
            np.clip(B, 0.0, 1.0, out=B)

        # Check if B has died out
        if B.sum() < reseed_threshold:
            A[:] = 1.0
            B[:] = 0.0
            seed_patches(B, rows, cols)

        # Render B concentration to colors
        frame_rgb = palette_lookup(lut, B)
        draw_frame(device, frame_rgb)

        next_frame = frame_sleep(next_frame, interval)

    clear_keyboard(device)


def main():
    """Standalone entry point."""
    standalone_main(EFFECT_NAME, run)


if __name__ == "__main__":
    main()
