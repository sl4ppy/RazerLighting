#!/usr/bin/env python3
"""Heat Diffusion - thermal simulation with hot iron palette.

Random hot spots ignite across the keyboard and heat spreads via
discrete Laplacian diffusion. Global cooling gradually pulls cells
back toward zero. The result is mapped to a hot iron palette that
transitions from black through red, orange, and yellow to white.

Edit heat_diffusion_config.py while running to tweak on the fly.
"""

import math
import os
import random
import signal
import sys
import threading
import time

EFFECT_NAME = "Heat Diffusion"
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "heat_diffusion_config.py")
BLACK = (0, 0, 0)


def load_config():
    cfg = {}
    try:
        with open(CONFIG_PATH) as f:
            exec(f.read(), cfg)
    except Exception as e:
        print(f"Config load error: {e}", file=sys.stderr)
    return cfg


def heat_to_color(palette, heat):
    """Map a heat value (0.0+) to a color by interpolating through the palette."""
    if not palette:
        return (0, 0, 0)
    # Clamp heat to [0, 1] for palette lookup
    t = max(0.0, min(1.0, heat))
    pos = t * (len(palette) - 1)
    idx = int(pos)
    frac = pos - idx
    if idx >= len(palette) - 1:
        return palette[-1]
    c1, c2 = palette[idx], palette[idx + 1]
    return (
        int(c1[0] + (c2[0] - c1[0]) * frac),
        int(c1[1] + (c2[1] - c1[1]) * frac),
        int(c1[2] + (c2[2] - c1[2]) * frac),
    )


def run(device, stop_event):
    """Run the heat diffusion effect."""
    rows = device.fx.advanced.rows
    cols = device.fx.advanced.cols
    matrix = device.fx.advanced.matrix

    # Initialize heat grid
    heat = [[0.0] * cols for _ in range(rows)]

    while not stop_event.is_set():
        cfg = load_config()
        interval = 1.0 / cfg.get("FPS", 20)
        diffusion_rate = cfg.get("DIFFUSION_RATE", 0.25)
        cooling = cfg.get("COOLING", 0.008)
        ignition_chance = cfg.get("IGNITION_CHANCE", 0.08)
        ignition_heat = cfg.get("IGNITION_HEAT", 1.0)
        palette = cfg.get("PALETTE", [(0, 0, 0), (180, 0, 0), (255, 100, 0), (255, 220, 50), (255, 255, 255)])

        # Random ignition
        for r in range(rows):
            for c in range(cols):
                if random.random() < ignition_chance:
                    heat[r][c] = ignition_heat

        # Diffusion via discrete Laplacian
        new_heat = [[0.0] * cols for _ in range(rows)]
        for r in range(rows):
            for c in range(cols):
                # Sum of 4 neighbors (open boundary: out-of-bounds treated as 0)
                neighbors = 0.0
                if r > 0:
                    neighbors += heat[r - 1][c]
                if r < rows - 1:
                    neighbors += heat[r + 1][c]
                if c > 0:
                    neighbors += heat[r][c - 1]
                if c < cols - 1:
                    neighbors += heat[r][c + 1]

                new_heat[r][c] = heat[r][c] + diffusion_rate * (neighbors - 4.0 * heat[r][c])

        # Global cooling and clamping
        for r in range(rows):
            for c in range(cols):
                new_heat[r][c] = max(0.0, new_heat[r][c] - cooling)

        heat = new_heat

        # Render
        for r in range(rows):
            for c in range(cols):
                matrix[r, c] = heat_to_color(palette, heat[r][c])

        device.fx.advanced.draw()
        time.sleep(interval)

    # Clean up
    for r in range(rows):
        for c in range(cols):
            matrix[r, c] = BLACK
    device.fx.advanced.draw()


def main():
    """Standalone entry point."""
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from device import get_device

    device = get_device()
    stop_event = threading.Event()

    print(f"{device.name} ({device.fx.advanced.cols}x{device.fx.advanced.rows}) - heat diffusion")
    print("Ctrl+C to stop")

    signal.signal(signal.SIGINT, lambda *_: stop_event.set())
    signal.signal(signal.SIGTERM, lambda *_: stop_event.set())

    run(device, stop_event)


if __name__ == "__main__":
    main()
