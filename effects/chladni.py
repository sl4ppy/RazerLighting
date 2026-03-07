#!/usr/bin/env python3
"""Chladni Patterns - vibrating plate nodal line visualization.

Simulates Chladni figures by computing the vibration amplitude across
the keyboard and highlighting nodal lines (where amplitude is near zero)
with bright azure. Mode pairs morph over time for endless variation,
and a gentle breathing pulse keeps it alive.

Edit chladni_config.py while running to tweak on the fly.
"""

import math
import os
import random
import signal
import sys
import threading
import time

EFFECT_NAME = "Chladni Patterns"
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chladni_config.py")
BLACK = (0, 0, 0)


def load_config():
    cfg = {}
    try:
        with open(CONFIG_PATH) as f:
            exec(f.read(), cfg)
    except Exception as e:
        print(f"Config load error: {e}", file=sys.stderr)
    return cfg


def chladni_value(x, y, n, m, a=1.0, b=1.0):
    """Compute Chladni plate vibration amplitude at normalized coords (x, y).

    v = a*sin(pi*n*x)*sin(pi*m*y) + b*sin(pi*m*x)*sin(pi*n*y)
    """
    return (a * math.sin(math.pi * n * x) * math.sin(math.pi * m * y)
            + b * math.sin(math.pi * m * x) * math.sin(math.pi * n * y))


def lerp_color(c1, c2, t):
    """Linearly interpolate between two RGB colors."""
    return (
        int(c1[0] + (c2[0] - c1[0]) * t),
        int(c1[1] + (c2[1] - c1[1]) * t),
        int(c1[2] + (c2[2] - c1[2]) * t),
    )


def run(device, stop_event):
    """Run the Chladni patterns effect."""
    rows = device.fx.advanced.rows
    cols = device.fx.advanced.cols
    matrix = device.fx.advanced.matrix

    t = 0.0

    while not stop_event.is_set():
        cfg = load_config()
        interval = 1.0 / cfg.get("FPS", 20)
        nodal_width = cfg.get("NODAL_WIDTH", 0.4)
        morph_speed = cfg.get("MORPH_SPEED", 0.008)
        pulse_speed = cfg.get("PULSE_SPEED", 0.06)
        mode_pairs = cfg.get("MODE_PAIRS", [(2, 3), (3, 5), (4, 3), (5, 2), (1, 4), (3, 4)])
        line_color = cfg.get("LINE_COLOR", (50, 180, 255))
        bg_color = cfg.get("BG_COLOR", (0, 5, 15))

        num_pairs = len(mode_pairs)
        if num_pairs == 0:
            time.sleep(interval)
            t += 1.0
            continue

        # Determine current and next mode pair for crossfade
        morph_phase = (t * morph_speed) % num_pairs
        pair_idx = int(morph_phase) % num_pairs
        next_idx = (pair_idx + 1) % num_pairs
        blend = morph_phase - int(morph_phase)  # 0..1 crossfade factor

        n1, m1 = mode_pairs[pair_idx]
        n2, m2 = mode_pairs[next_idx]

        # Breathing pulse
        pulse = 0.7 + 0.3 * math.sin(t * pulse_speed)

        # Precompute width squared for Gaussian
        w2 = nodal_width * nodal_width

        for r in range(rows):
            y = r / max(rows - 1, 1)
            for c in range(cols):
                x = c / max(cols - 1, 1)

                # Chladni values for current and next mode pairs
                v1 = chladni_value(x, y, n1, m1)
                v2 = chladni_value(x, y, n2, m2)

                # Crossfade between mode pairs
                v = v1 * (1.0 - blend) + v2 * blend

                # Gaussian brightness peak at nodal lines (|v| near 0)
                brightness = math.exp(-(v * v) / w2)

                # Apply breathing pulse
                brightness *= pulse

                # Clamp
                brightness = max(0.0, min(1.0, brightness))

                # Map brightness to color: bg at 0, line_color at 1
                color = lerp_color(bg_color, line_color, brightness)
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

    print(f"{device.name} ({device.fx.advanced.cols}x{device.fx.advanced.rows}) - chladni patterns")
    print("Ctrl+C to stop")

    signal.signal(signal.SIGINT, lambda *_: stop_event.set())
    signal.signal(signal.SIGTERM, lambda *_: stop_event.set())

    run(device, stop_event)


if __name__ == "__main__":
    main()
