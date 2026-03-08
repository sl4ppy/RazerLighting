#!/usr/bin/env python3
"""Heat Diffusion - thermal simulation with hot iron palette.

Random hot spots ignite across the keyboard and heat spreads via
discrete Laplacian diffusion. Global cooling gradually pulls cells
back toward zero. The result is mapped to a hot iron palette that
transitions from black through red, orange, and yellow to white.

Edit heat_diffusion_config.py while running to tweak on the fly.
"""

import os
import time

import numpy as np

from effects.common import (
    load_config, draw_frame, clear_keyboard, frame_sleep,
    build_palette_lut, palette_lookup, laplacian_4pt_open, standalone_main,
)

EFFECT_NAME = "Heat Diffusion"
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "heat_diffusion_config.py")


def run(device, stop_event):
    """Run the heat diffusion effect."""
    rows = device.fx.advanced.rows
    cols = device.fx.advanced.cols

    # Initialize heat grid
    heat = np.zeros((rows, cols), dtype=np.float64)

    next_frame = time.monotonic()

    while not stop_event.is_set():
        cfg = load_config(CONFIG_PATH)
        interval = 1.0 / cfg.get("FPS", 20)
        diffusion_rate = cfg.get("DIFFUSION_RATE", 0.25)
        cooling = cfg.get("COOLING", 0.008)
        ignition_chance = cfg.get("IGNITION_CHANCE", 0.08)
        ignition_heat = cfg.get("IGNITION_HEAT", 1.0)
        palette = cfg.get("PALETTE", [(0, 0, 0), (180, 0, 0), (255, 100, 0), (255, 220, 50), (255, 255, 255)])

        # Build palette LUT for rendering
        lut = build_palette_lut(palette)

        # Random ignition
        ignite_mask = np.random.random((rows, cols)) < ignition_chance
        heat[ignite_mask] = ignition_heat

        # Diffusion via discrete Laplacian (open boundaries)
        heat += diffusion_rate * laplacian_4pt_open(heat)

        # Global cooling and clamping
        heat -= cooling
        np.clip(heat, 0.0, None, out=heat)

        # Render
        values = np.clip(heat, 0.0, 1.0)
        frame_rgb = palette_lookup(lut, values)
        draw_frame(device, frame_rgb)

        next_frame = frame_sleep(next_frame, interval)

    clear_keyboard(device)


def main():
    """Standalone entry point."""
    standalone_main(EFFECT_NAME, run)


if __name__ == "__main__":
    main()
