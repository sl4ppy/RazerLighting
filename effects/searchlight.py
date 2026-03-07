#!/usr/bin/env python3
"""Searchlight - a bright beam sweeps around the keyboard.

A warm white/yellow beam rotates around the keyboard like a searchlight,
illuminating keys as it passes over them against a deep purple ambient
background. The beam has soft falloff edges and subtle brightness flicker.

Edit searchlight_config.py while running to tweak on the fly.
"""

import math
import os
import random
import signal
import sys
import threading
import time

EFFECT_NAME = "Searchlight"
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "searchlight_config.py")
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


def scale_color(c, s):
    return (
        min(255, int(c[0] * s)),
        min(255, int(c[1] * s)),
        min(255, int(c[2] * s)),
    )


def run(device, stop_event):
    """Run the searchlight effect."""
    rows = device.fx.advanced.rows
    cols = device.fx.advanced.cols
    matrix = device.fx.advanced.matrix

    angle = 0.0

    while not stop_event.is_set():
        cfg = load_config()
        interval = 1.0 / cfg.get("FPS", 20)
        sweep_speed = cfg.get("SWEEP_SPEED", 0.03)
        beam_width = cfg.get("BEAM_WIDTH", 0.4)
        beam_falloff = cfg.get("BEAM_FALLOFF", 2.0)
        origin_x = cfg.get("ORIGIN_X", 0.5)
        origin_y = cfg.get("ORIGIN_Y", 0.5)

        bg = cfg.get("BG_COLOR", (17, 0, 34))
        core = cfg.get("BEAM_CORE_COLOR", (255, 255, 204))
        mid_color = cfg.get("BEAM_MID_COLOR", (200, 220, 100))
        edge_color = cfg.get("BEAM_EDGE_COLOR", (61, 122, 30))
        ambient = cfg.get("AMBIENT_COLOR", (20, 8, 32))

        flicker = cfg.get("FLICKER", True)
        flicker_amount = cfg.get("FLICKER_AMOUNT", 0.08)

        # Flicker modulation
        brightness = 1.0
        if flicker:
            brightness = 1.0 - random.random() * flicker_amount

        # Origin in pixel space
        ox = origin_x * (cols - 1)
        oy = origin_y * (rows - 1)

        for r in range(rows):
            for c in range(cols):
                # Angle from origin to this pixel
                dx = c - ox
                dy = (r - oy) * 2.0  # stretch Y since rows are taller than cols
                pixel_angle = math.atan2(dy, dx)

                # Angular distance from beam center
                diff = pixel_angle - angle
                # Normalize to [-pi, pi]
                diff = (diff + math.pi) % (2 * math.pi) - math.pi
                abs_diff = abs(diff)

                if abs_diff < beam_width:
                    # Inside beam — interpolate core -> edge
                    beam_t = abs_diff / beam_width
                    beam_t = beam_t ** beam_falloff  # apply falloff curve

                    # Distance from origin affects intensity too
                    dist = math.sqrt(dx * dx + dy * dy)
                    max_dist = math.sqrt(cols * cols + (rows * 2) ** 2)
                    dist_factor = min(1.0, 0.5 + 0.5 * (dist / max_dist))

                    if beam_t < 0.3:
                        color = lerp_color(core, mid_color, beam_t / 0.3)
                    else:
                        color = lerp_color(mid_color, edge_color, (beam_t - 0.3) / 0.7)

                    color = lerp_color(bg, color, (1.0 - beam_t) * dist_factor * brightness)
                else:
                    # Outside beam — ambient with subtle distance-based variation
                    dist = math.sqrt(dx * dx + dy * dy)
                    max_dist = math.sqrt(cols * cols + (rows * 2) ** 2)
                    amb_t = 0.3 * (dist / max_dist)
                    color = lerp_color(bg, ambient, amb_t)

                matrix[r, c] = color

        device.fx.advanced.draw()
        angle += sweep_speed
        if angle > math.pi:
            angle -= 2 * math.pi
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

    print(f"{device.name} ({device.fx.advanced.cols}x{device.fx.advanced.rows}) - searchlight")
    print("Ctrl+C to stop")

    signal.signal(signal.SIGINT, lambda *_: stop_event.set())
    signal.signal(signal.SIGTERM, lambda *_: stop_event.set())

    run(device, stop_event)


if __name__ == "__main__":
    main()
