#!/usr/bin/env python3
"""Fireflies - coupled oscillators using the Kuramoto model.

Each key is an oscillator with its own phase and natural frequency.
Neighbors couple via the Kuramoto model, causing waves of synchronization
and chaos as the coupling strength oscillates over time. Each oscillator
"flashes" briefly once per cycle like a firefly.

Edit fireflies_config.py while running to tweak on the fly.
"""

import math
import os
import random
import signal
import sys
import threading
import time

EFFECT_NAME = "Fireflies"
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fireflies_config.py")
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


def run(device, stop_event):
    """Run the fireflies effect."""
    rows = device.fx.advanced.rows
    cols = device.fx.advanced.cols
    matrix = device.fx.advanced.matrix

    TWO_PI = 2.0 * math.pi

    # Initialize oscillator phases randomly across the full cycle
    phases = [[random.uniform(0.0, TWO_PI) for _ in range(cols)] for _ in range(rows)]

    # Draw natural frequencies from a normal distribution
    cfg = load_config()
    mean_freq = cfg.get("MEAN_FREQ", 0.12)
    freq_spread = cfg.get("FREQ_SPREAD", 0.02)
    nat_freqs = [
        [random.gauss(mean_freq, freq_spread) for _ in range(cols)]
        for _ in range(rows)
    ]

    t = 0.0

    while not stop_event.is_set():
        cfg = load_config()
        interval = 1.0 / cfg.get("FPS", 20)
        coupling = cfg.get("COUPLING", 0.15)
        coupling_speed = cfg.get("COUPLING_SPEED", 0.003)
        sharpness = cfg.get("FLASH_SHARPNESS", 4.0)
        dim_color = cfg.get("DIM_COLOR", (0, 15, 0))
        mid_color = cfg.get("MID_COLOR", (30, 100, 0))
        bright_color = cfg.get("BRIGHT_COLOR", (150, 220, 50))
        flash_color = cfg.get("FLASH_COLOR", (255, 255, 200))

        # Oscillating coupling strength: cycles between sync and chaos
        K = coupling * (0.5 + 0.5 * math.sin(t * coupling_speed))

        # Kuramoto phase update with Moore neighborhood (8-connected)
        new_phases = [[0.0] * cols for _ in range(rows)]
        for r in range(rows):
            for c in range(cols):
                phase_i = phases[r][c]
                coupling_sum = 0.0
                n_neighbors = 0

                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == 0 and dc == 0:
                            continue
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < rows and 0 <= nc < cols:
                            coupling_sum += math.sin(phases[nr][nc] - phase_i)
                            n_neighbors += 1

                if n_neighbors > 0:
                    d_phase = nat_freqs[r][c] + (K / n_neighbors) * coupling_sum
                else:
                    d_phase = nat_freqs[r][c]

                new_phases[r][c] = (phase_i + d_phase) % TWO_PI

        phases = new_phases

        # Render: map phase to brightness and color
        for r in range(rows):
            for c in range(cols):
                # Brightness from phase: sin(phase) clamped to [0,1], raised to sharpness
                raw = math.sin(phases[r][c])
                brightness = max(0.0, raw) ** sharpness

                # Map brightness through firefly color gradient
                if brightness < 0.3:
                    # dim to mid
                    color = lerp_color(dim_color, mid_color, brightness / 0.3)
                elif brightness < 0.7:
                    # mid to bright
                    color = lerp_color(mid_color, bright_color, (brightness - 0.3) / 0.4)
                else:
                    # bright to flash
                    color = lerp_color(bright_color, flash_color, (brightness - 0.7) / 0.3)

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

    print(f"{device.name} ({device.fx.advanced.cols}x{device.fx.advanced.rows}) - fireflies")
    print("Ctrl+C to stop")

    signal.signal(signal.SIGINT, lambda *_: stop_event.set())
    signal.signal(signal.SIGTERM, lambda *_: stop_event.set())

    run(device, stop_event)


if __name__ == "__main__":
    main()
