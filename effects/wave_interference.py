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
import signal
import sys
import threading
import time

EFFECT_NAME = "Wave Interference"
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wave_interference_config.py")
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


def run(device, stop_event):
    """Run the wave interference effect."""
    rows = device.fx.advanced.rows
    cols = device.fx.advanced.cols
    matrix = device.fx.advanced.matrix

    # Two grids for Verlet integration: current and previous
    current = [[0.0] * cols for _ in range(rows)]
    previous = [[0.0] * cols for _ in range(rows)]

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

    while not stop_event.is_set():
        cfg = load_config()
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

        # Adjust source count if config changed
        while len(sources) < num_sources:
            sources.append({
                "phase_r": random.uniform(0, 2 * math.pi),
                "phase_c": random.uniform(0, 2 * math.pi),
                "freq_r": random.uniform(0.7, 1.3),
                "freq_c": random.uniform(0.7, 1.3),
            })

        # Inject waves from moving point sources
        for i in range(min(num_sources, len(sources))):
            src = sources[i]
            # Sources move on Lissajous-like paths within the grid
            sr = (math.sin(t * source_speed * src["freq_r"] + src["phase_r"]) + 1.0) / 2.0 * (rows - 1)
            sc = (math.sin(t * source_speed * src["freq_c"] + src["phase_c"]) + 1.0) / 2.0 * (cols - 1)
            ri, ci = int(round(sr)), int(round(sc))
            ri = max(0, min(rows - 1, ri))
            ci = max(0, min(cols - 1, ci))
            current[ri][ci] += amplitude * math.sin(t * wave_freq + i * 2.094)

        # Wave equation update with Verlet integration
        speed_sq = speed * speed
        next_grid = [[0.0] * cols for _ in range(rows)]

        for r in range(rows):
            for c in range(cols):
                # Laplacian with open boundaries (edge cells use 0 for out-of-bounds)
                center = current[r][c]
                up = current[r - 1][c] if r > 0 else 0.0
                down = current[r + 1][c] if r < rows - 1 else 0.0
                left = current[r][c - 1] if c > 0 else 0.0
                right = current[r][c + 1] if c < cols - 1 else 0.0
                laplacian = up + down + left + right - 4.0 * center

                next_val = 2.0 * center - previous[r][c] + speed_sq * laplacian
                next_grid[r][c] = next_val

        # Apply damping and shift grids
        for r in range(rows):
            for c in range(cols):
                next_grid[r][c] *= damping

        previous = current
        current = next_grid

        # Render: map amplitude to diverging palette
        for r in range(rows):
            for c in range(cols):
                # Map wave amplitude to 0..1 range (amplitude centered at 0)
                value = (current[r][c] + 1.0) / 2.0
                value = max(0.0, min(1.0, value))
                color = sample_palette(palette, value)
                matrix[r, c] = color

        device.fx.advanced.draw()
        t += 1.0
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

    print(f"{device.name} ({device.fx.advanced.cols}x{device.fx.advanced.rows}) - wave interference")
    print("Ctrl+C to stop")

    signal.signal(signal.SIGINT, lambda *_: stop_event.set())
    signal.signal(signal.SIGTERM, lambda *_: stop_event.set())

    run(device, stop_event)


if __name__ == "__main__":
    main()
