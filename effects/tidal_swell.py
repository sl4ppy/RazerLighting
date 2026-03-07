#!/usr/bin/env python3
"""Tidal Swell - ocean waves rolling across the keyboard.

Layered sine waves create a convincing ocean surface with crests,
troughs, foam sparkle, and deep water. Waves scroll right-to-left
with a slow vertical swell breathing effect.

Edit tidal_swell_config.py while running to tweak on the fly.
"""

import math
import os
import random
import signal
import sys
import threading
import time

EFFECT_NAME = "Tidal Swell"
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tidal_swell_config.py")
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
    """Linearly interpolate between two RGB colors."""
    t = max(0.0, min(1.0, t))
    return (
        int(a[0] + (b[0] - a[0]) * t),
        int(a[1] + (b[1] - a[1]) * t),
        int(a[2] + (b[2] - a[2]) * t),
    )


def sample_ocean_palette(value, cfg):
    """Map a wave height value (0=trough, 1=crest) to an ocean color."""
    deep = cfg.get("DEEP_COLOR", (0, 8, 17))
    trough = cfg.get("TROUGH_COLOR", (0, 30, 50))
    body = cfg.get("BODY_COLOR", (0, 100, 68))
    crest = cfg.get("CREST_COLOR", (0, 255, 136))
    foam = cfg.get("FOAM_COLOR", (170, 255, 204))

    if value < 0.2:
        return lerp_color(deep, trough, value / 0.2)
    elif value < 0.5:
        return lerp_color(trough, body, (value - 0.2) / 0.3)
    elif value < 0.8:
        return lerp_color(body, crest, (value - 0.5) / 0.3)
    else:
        return lerp_color(crest, foam, (value - 0.8) / 0.2)


def run(device, stop_event):
    """Run the tidal swell effect."""
    rows = device.fx.advanced.rows
    cols = device.fx.advanced.cols
    matrix = device.fx.advanced.matrix

    t = 0.0

    while not stop_event.is_set():
        cfg = load_config()
        interval = 1.0 / cfg.get("FPS", 20)
        wave_speed = cfg.get("WAVE_SPEED", 0.08)
        wave_count = cfg.get("WAVE_COUNT", 2.5)
        swell_speed = cfg.get("SWELL_SPEED", 0.02)
        foam_chance = cfg.get("FOAM_CHANCE", 0.06)
        spray_color = cfg.get("SPRAY_COLOR", (255, 255, 255))
        secondary = cfg.get("SECONDARY_WAVE", True)
        secondary_scale = cfg.get("SECONDARY_SCALE", 0.4)

        swell = math.sin(t * swell_speed) * 0.15

        for r in range(rows):
            # Depth factor: top rows are "surface", bottom rows are "deep"
            depth = 1.0 - (r / (rows - 1))  # 1.0 at top, 0.0 at bottom

            for c in range(cols):
                # Primary wave
                wave = math.sin(c * wave_count * math.pi / cols - t * wave_speed)

                # Secondary wave overlay
                if secondary:
                    wave2 = math.sin(c * wave_count * 1.7 * math.pi / cols - t * wave_speed * 0.6 + 1.3)
                    wave = wave * (1.0 - secondary_scale) + wave2 * secondary_scale

                # Add vertical swell
                wave += swell

                # Map wave to 0..1 and modulate by depth
                # Surface rows show full wave amplitude, deep rows are muted
                value = (wave + 1.0) / 2.0
                value = value * (0.3 + 0.7 * depth)

                # Row-based depth darkening
                value *= 0.4 + 0.6 * depth

                color = sample_ocean_palette(value, cfg)

                # Foam sparkle at wave crests (top rows only)
                if value > 0.75 and depth > 0.5 and random.random() < foam_chance:
                    color = spray_color

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

    print(f"{device.name} ({device.fx.advanced.cols}x{device.fx.advanced.rows}) - tidal swell")
    print("Ctrl+C to stop")

    signal.signal(signal.SIGINT, lambda *_: stop_event.set())
    signal.signal(signal.SIGTERM, lambda *_: stop_event.set())

    run(device, stop_event)


if __name__ == "__main__":
    main()
