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
import signal
import sys
import threading
import time

EFFECT_NAME = "Metaballs"
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "metaballs_config.py")
BLACK = (0, 0, 0)


def load_config():
    cfg = {}
    try:
        with open(CONFIG_PATH) as f:
            exec(f.read(), cfg)
    except Exception as e:
        print(f"Config load error: {e}", file=sys.stderr)
    return cfg


def lerp_color(a, b, t):
    t = max(0.0, min(1.0, t))
    return (
        int(a[0] + (b[0] - a[0]) * t),
        int(a[1] + (b[1] - a[1]) * t),
        int(a[2] + (b[2] - a[2]) * t),
    )


def sample_palette(palette, t):
    """Sample a color from the palette at position t (0.0 to 1.0)."""
    if not palette:
        return BLACK
    t = max(0.0, min(1.0, t))
    n = len(palette) - 1
    idx = t * n
    lo = int(idx)
    hi = min(lo + 1, n)
    frac = idx - lo
    return lerp_color(palette[lo], palette[hi], frac)


def run(device, stop_event):
    """Run the metaballs effect."""
    rows = device.fx.advanced.rows
    cols = device.fx.advanced.cols
    matrix = device.fx.advanced.matrix

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

    while not stop_event.is_set():
        cfg = load_config()
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

        # Clamp to available blobs
        num_blobs = min(num_blobs, len(blobs))

        # Compute blob positions via Lissajous paths
        blob_positions = []
        for i in range(num_blobs):
            b = blobs[i]
            bx = (math.sin(b["freq_x"] * t + b["phase_x"]) + 1.0) / 2.0 * (cols - 1)
            by = (math.sin(b["freq_y"] * t + b["phase_y"]) + 1.0) / 2.0 * (rows - 1)
            blob_positions.append((bx, by))

        r_sq = blob_radius * blob_radius

        # Render frame
        for r in range(rows):
            for c in range(cols):
                field = 0.0
                for bx, by in blob_positions:
                    dx = (c - bx) / aspect
                    dy = r - by
                    dist_sq = dx * dx + dy * dy
                    if dist_sq < 0.001:
                        dist_sq = 0.001
                    field += r_sq / dist_sq

                # Map field to palette
                if field < 0.01:
                    color = BLACK
                else:
                    # Normalize: field/threshold gives 1.0 at the surface
                    # Map so that threshold maps to ~0.5 in palette, above goes brighter
                    norm = field / threshold
                    # Clamp palette lookup
                    palette_t = min(1.0, norm * 0.5)
                    color = sample_palette(palette, palette_t)

                matrix[r, c] = color

        device.fx.advanced.draw()

        t += speed
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

    print(f"{device.name} ({device.fx.advanced.cols}x{device.fx.advanced.rows}) - metaballs")
    print("Ctrl+C to stop")

    signal.signal(signal.SIGINT, lambda *_: stop_event.set())
    signal.signal(signal.SIGTERM, lambda *_: stop_event.set())

    run(device, stop_event)


if __name__ == "__main__":
    main()
