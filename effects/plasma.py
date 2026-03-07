#!/usr/bin/env python3
"""Plasma - classic demoscene plasma effect with layered sine waves.

Multiple sine waves at different frequencies and phases combine to
create organic, flowing color fields across the keyboard. An optional
second plasma layer adds visual complexity.

Edit plasma_config.py while running to tweak on the fly.
"""

import math
import os
import signal
import sys
import threading
import time

EFFECT_NAME = "Plasma"
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "plasma_config.py")
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
    t = t % 1.0
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


def blend_colors(a, b, weight):
    """Blend color b into color a with given weight (0=all a, 1=all b)."""
    return (
        int(a[0] + (b[0] - a[0]) * weight),
        int(a[1] + (b[1] - a[1]) * weight),
        int(a[2] + (b[2] - a[2]) * weight),
    )


def run(device, stop_event):
    """Run the plasma effect."""
    rows = device.fx.advanced.rows
    cols = device.fx.advanced.cols
    matrix = device.fx.advanced.matrix

    t = 0.0

    while not stop_event.is_set():
        cfg = load_config()
        interval = 1.0 / cfg.get("FPS", 20)
        scale_x = cfg.get("SCALE_X", 0.35)
        scale_y = cfg.get("SCALE_Y", 0.6)
        time_speed = cfg.get("TIME_SPEED", 0.04)
        palette = cfg.get("PALETTE", [(0, 60, 20), (0, 255, 30), (0, 60, 20)])

        overlay = cfg.get("OVERLAY", True)
        overlay_sx = cfg.get("OVERLAY_SCALE_X", 0.5)
        overlay_sy = cfg.get("OVERLAY_SCALE_Y", 0.3)
        overlay_ts = cfg.get("OVERLAY_TIME_SPEED", 0.03)
        overlay_blend = cfg.get("OVERLAY_BLEND", 0.35)

        phase = t * time_speed
        phase2 = t * overlay_ts

        for r in range(rows):
            for c in range(cols):
                # Classic plasma: sum of sine waves at different angles
                v1 = math.sin(c * scale_x + phase)
                v2 = math.sin(r * scale_y + phase * 1.3)
                v3 = math.sin((c * scale_x + r * scale_y) * 0.5 + phase * 0.7)
                v4 = math.sin(math.sqrt((c * scale_x) ** 2 + (r * scale_y) ** 2) + phase * 0.9)

                value = (v1 + v2 + v3 + v4) / 4.0  # -1..1
                value = (value + 1.0) / 2.0  # 0..1

                color = sample_palette(palette, value)

                # Optional overlay plasma
                if overlay:
                    o1 = math.sin(c * overlay_sx + phase2 * 1.1 + 2.0)
                    o2 = math.sin(r * overlay_sy + phase2 * 0.8 + 1.0)
                    o3 = math.sin((c * overlay_sx - r * overlay_sy) * 0.6 + phase2)
                    ov = (o1 + o2 + o3) / 3.0
                    ov = (ov + 1.0) / 2.0
                    overlay_color = sample_palette(palette, ov)
                    color = blend_colors(color, overlay_color, overlay_blend)

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

    print(f"{device.name} ({device.fx.advanced.cols}x{device.fx.advanced.rows}) - plasma")
    print("Ctrl+C to stop")

    signal.signal(signal.SIGINT, lambda *_: stop_event.set())
    signal.signal(signal.SIGTERM, lambda *_: stop_event.set())

    run(device, stop_event)


if __name__ == "__main__":
    main()
