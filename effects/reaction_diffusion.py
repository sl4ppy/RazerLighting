#!/usr/bin/env python3
"""Reaction-Diffusion - Gray-Scott model on the keyboard.

Two chemicals A and B interact via the Gray-Scott equations, producing
organic, cell-like patterns that split, pulse, and reform endlessly.
Chemical B concentration is mapped to a bioluminescent teal-cyan palette.

Edit reaction_diffusion_config.py while running to tweak on the fly.
"""

import math
import os
import random
import signal
import sys
import threading
import time

EFFECT_NAME = "Reaction-Diffusion"
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reaction_diffusion_config.py")
BLACK = (0, 0, 0)


def load_config():
    cfg = {}
    try:
        with open(CONFIG_PATH) as f:
            exec(f.read(), cfg)
    except Exception as e:
        print(f"Config load error: {e}", file=sys.stderr)
    return cfg


def sample_palette(palette, t):
    """Sample a color from a palette at position t (0..1), interpolating between entries."""
    if not palette:
        return (0, 0, 0)
    t = max(0.0, min(1.0, t))
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


def seed_patches(B, rows, cols, count=None):
    """Place small random 2x2 patches of B=1.0."""
    if count is None:
        count = random.randint(3, 5)
    for _ in range(count):
        r0 = random.randint(0, rows - 1)
        c0 = random.randint(0, cols - 1)
        for dr in range(2):
            for dc in range(2):
                B[(r0 + dr) % rows][(c0 + dc) % cols] = 1.0


def laplacian(grid, r, c, rows, cols):
    """Compute Laplacian using weighted 9-point stencil with toroidal wrap."""
    center = grid[r][c]
    # Cardinal neighbors (weight 0.2 each)
    lap = 0.2 * (
        grid[(r - 1) % rows][c]
        + grid[(r + 1) % rows][c]
        + grid[r][(c - 1) % cols]
        + grid[r][(c + 1) % cols]
    )
    # Diagonal neighbors (weight 0.05 each)
    lap += 0.05 * (
        grid[(r - 1) % rows][(c - 1) % cols]
        + grid[(r - 1) % rows][(c + 1) % cols]
        + grid[(r + 1) % rows][(c - 1) % cols]
        + grid[(r + 1) % rows][(c + 1) % cols]
    )
    # Center (weight -1)
    lap += -1.0 * center
    return lap


def run(device, stop_event):
    """Run the reaction-diffusion effect."""
    rows = device.fx.advanced.rows
    cols = device.fx.advanced.cols
    matrix = device.fx.advanced.matrix

    # Initialize grids
    A = [[1.0] * cols for _ in range(rows)]
    B = [[0.0] * cols for _ in range(rows)]

    # Seed initial patches
    seed_patches(B, rows, cols)

    while not stop_event.is_set():
        cfg = load_config()
        interval = 1.0 / cfg.get("FPS", 20)
        feed = cfg.get("FEED", 0.0367)
        kill = cfg.get("KILL", 0.0649)
        d_a = cfg.get("D_A", 1.0)
        d_b = cfg.get("D_B", 0.5)
        sim_steps = cfg.get("SIM_STEPS", 8)
        palette = cfg.get("PALETTE", [(0, 0, 0), (0, 80, 80), (150, 255, 230)])
        reseed_threshold = cfg.get("RESEED_THRESHOLD", 0.5)
        dt = 1.0

        # Run simulation steps
        for _ in range(sim_steps):
            # Compute new grids
            new_A = [[0.0] * cols for _ in range(rows)]
            new_B = [[0.0] * cols for _ in range(rows)]

            for r in range(rows):
                for c in range(cols):
                    a = A[r][c]
                    b = B[r][c]
                    lap_a = laplacian(A, r, c, rows, cols)
                    lap_b = laplacian(B, r, c, rows, cols)
                    ab2 = a * b * b

                    new_A[r][c] = a + (d_a * lap_a - ab2 + feed * (1.0 - a)) * dt
                    new_B[r][c] = b + (d_b * lap_b + ab2 - (kill + feed) * b) * dt

                    # Clamp values
                    new_A[r][c] = max(0.0, min(1.0, new_A[r][c]))
                    new_B[r][c] = max(0.0, min(1.0, new_B[r][c]))

            A = new_A
            B = new_B

        # Check if B has died out
        b_sum = sum(B[r][c] for r in range(rows) for c in range(cols))
        if b_sum < reseed_threshold:
            A = [[1.0] * cols for _ in range(rows)]
            B = [[0.0] * cols for _ in range(rows)]
            seed_patches(B, rows, cols)

        # Render B concentration to colors
        for r in range(rows):
            for c in range(cols):
                color = sample_palette(palette, B[r][c])
                matrix[r, c] = color

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

    print(f"{device.name} ({device.fx.advanced.cols}x{device.fx.advanced.rows}) - reaction-diffusion")
    print("Ctrl+C to stop")

    signal.signal(signal.SIGINT, lambda *_: stop_event.set())
    signal.signal(signal.SIGTERM, lambda *_: stop_event.set())

    run(device, stop_event)


if __name__ == "__main__":
    main()
