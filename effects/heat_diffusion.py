#!/usr/bin/env python3
"""Heat Diffusion - thermal simulation with hot iron palette.

Rare ignition events spawn glowing embers that inject heat over several
frames.  Heat spreads via discrete Laplacian diffusion while global
cooling pulls cells back toward zero, creating organic pools that bloom
outward and fade through a hot iron palette (black → red → orange →
yellow → white).

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

_DEF_PALETTE = [
    (0, 0, 20),
    (0, 0, 60),
    (120, 0, 0),
    (220, 40, 0),
    (255, 140, 20),
    (255, 240, 100),
    (255, 255, 255),
]


def run(device, stop_event):
    """Run the heat diffusion effect."""
    rows = device.fx.advanced.rows
    cols = device.fx.advanced.cols

    heat = np.zeros((rows, cols), dtype=np.float64)
    # Active embers: list of [row, col, frames_remaining, intensity]
    embers = []

    next_frame = time.monotonic()

    while not stop_event.is_set():
        cfg = load_config(CONFIG_PATH)
        fps = cfg.get("FPS", 20)
        interval = 1.0 / fps
        diffusion_rate = cfg.get("DIFFUSION_RATE", 0.25)
        sim_steps = cfg.get("SIM_STEPS", 3)
        cooling = cfg.get("COOLING", 0.01)
        ignitions_per_sec = cfg.get("IGNITIONS_PER_SEC", 4.0)
        ember_duration = cfg.get("EMBER_DURATION", 12)
        ignition_heat = cfg.get("IGNITION_HEAT", 1.2)
        palette = cfg.get("PALETTE", _DEF_PALETTE)

        lut = build_palette_lut(palette)

        # Spawn new embers (Poisson-distributed)
        expected = ignitions_per_sec / fps
        num_new = np.random.poisson(expected)
        for _ in range(num_new):
            r = np.random.randint(0, rows)
            c = np.random.randint(0, cols)
            embers.append([r, c, ember_duration, ignition_heat])

        # Embers inject heat and tick down
        alive = []
        for em in embers:
            r, c, remaining, intensity = em
            # Inject heat, decaying over ember lifetime
            heat[r, c] = min(heat[r, c] + intensity * (remaining / ember_duration), 1.5)
            remaining -= 1
            if remaining > 0:
                alive.append([r, c, remaining, intensity])
        embers = alive

        # Multiple diffusion substeps for smooth spreading
        for _ in range(sim_steps):
            heat += diffusion_rate * laplacian_4pt_open(heat)

        # Global cooling and clamping
        heat -= cooling
        np.clip(heat, 0.0, None, out=heat)

        # Render
        values = np.clip(heat, 0.0, 1.0)
        frame_rgb = palette_lookup(lut, values)
        draw_frame(device, frame_rgb)

        next_frame, _dt = frame_sleep(next_frame, interval)

    clear_keyboard(device)


def main():
    """Standalone entry point."""
    standalone_main(EFFECT_NAME, run)


if __name__ == "__main__":
    main()
