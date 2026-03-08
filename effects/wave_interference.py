#!/usr/bin/env python3
"""Wave Interference - 2D wave equation simulation on the keyboard.

Multiple point sources emit sine waves that propagate across the grid
using Verlet integration. Waves reflect, interfere constructively and
destructively, creating evolving ripple patterns. Sources drift on slow
circular/Lissajous paths for continuous variety.

Edit wave_interference_config.py while running to tweak on the fly.
"""

import math
import os
import random
import time

import numpy as np

from effects.common import (
    load_config, draw_frame, clear_keyboard, frame_sleep,
    build_palette_lut, palette_lookup, laplacian_4pt, standalone_main,
)

EFFECT_NAME = "Wave Interference"
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wave_interference_config.py")


def run(device, stop_event):
    """Run the wave interference effect."""
    rows = device.fx.advanced.rows
    cols = device.fx.advanced.cols

    # Two grids for Verlet integration: seed with low noise for instant activity
    current = np.random.uniform(-0.1, 0.1, (rows, cols))
    previous = np.random.uniform(-0.1, 0.1, (rows, cols))

    # Initialize sources with random phase offsets for their circular paths
    sources = []
    for i in range(3):
        sources.append({
            "phase_r": random.uniform(0, 2 * math.pi),
            "phase_c": random.uniform(0, 2 * math.pi),
            "freq_r": random.uniform(0.7, 1.3),
            "freq_c": random.uniform(0.7, 1.3),
        })

    t = 0.0

    next_frame = time.monotonic()

    while not stop_event.is_set():
        cfg = load_config(CONFIG_PATH)
        interval = 1.0 / cfg.get("FPS", 24)
        speed = cfg.get("SPEED", 0.6)
        damping = cfg.get("DAMPING", 0.985)
        amplitude = cfg.get("AMPLITUDE", 0.8)
        num_sources = cfg.get("NUM_SOURCES", 3)
        wave_freq = cfg.get("WAVE_FREQ", 0.8)
        source_speed = cfg.get("SOURCE_SPEED", 0.008)
        palette = cfg.get("PALETTE", [
            (0, 40, 180), (0, 15, 80), (0, 0, 0), (100, 70, 0), (220, 180, 40),
        ])

        # Build palette LUT for rendering
        lut = build_palette_lut(palette)

        # Adjust source count if config changed
        while len(sources) < num_sources:
            sources.append({
                "phase_r": random.uniform(0, 2 * math.pi),
                "phase_c": random.uniform(0, 2 * math.pi),
                "freq_r": random.uniform(0.7, 1.3),
                "freq_c": random.uniform(0.7, 1.3),
            })

        # Inject waves from moving point sources (spread over 3x3 for broad wavefronts)
        for i in range(min(num_sources, len(sources))):
            src = sources[i]
            # Sources move on Lissajous-like paths within the grid
            sr = (math.sin(t * source_speed * src["freq_r"] + src["phase_r"]) + 1.0) / 2.0 * (rows - 1)
            sc = (math.sin(t * source_speed * src["freq_c"] + src["phase_c"]) + 1.0) / 2.0 * (cols - 1)
            ri = max(0, min(rows - 1, int(round(sr))))
            ci = max(0, min(cols - 1, int(round(sc))))
            val = amplitude * math.sin(t * wave_freq + i * 2.094)
            for dr in range(-1, 2):
                for dc in range(-1, 2):
                    current[(ri + dr) % rows, (ci + dc) % cols] += val * (1.0 if dr == 0 and dc == 0 else 0.5)

        # Wave equation update with Verlet integration
        speed_sq = speed * speed
        next_grid = 2.0 * current - previous + speed_sq * laplacian_4pt(current)

        # Apply damping and shift grids
        next_grid *= damping
        previous = current
        current = next_grid

        # Render: map amplitude to diverging palette
        # Use 95th percentile instead of max to prevent source hotspots
        # from dominating the color scale
        abs_vals = np.abs(current)
        peak = max(np.percentile(abs_vals, 95) * 2.0, 0.01)
        values = np.clip((current / peak + 1.0) / 2.0, 0.0, 1.0)
        frame_rgb = palette_lookup(lut, values)
        draw_frame(device, frame_rgb)

        t += 1.0
        next_frame = frame_sleep(next_frame, interval)

    clear_keyboard(device)


def main():
    """Standalone entry point."""
    standalone_main(EFFECT_NAME, run)


if __name__ == "__main__":
    main()
