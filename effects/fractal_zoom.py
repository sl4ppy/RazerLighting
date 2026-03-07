#!/usr/bin/env python3
"""Fractal Zoom - animated Mandelbrot/Julia set zoom with color cycling.

Renders a fractal that continuously zooms in with slow rotation,
creating hypnotic patterns in a purple/magenta nebula palette.
Optional breathing pulse modulates overall brightness.

Edit fractal_zoom_config.py while running to tweak on the fly.
"""

import math
import os
import signal
import sys
import threading
import time

EFFECT_NAME = "Fractal Zoom"
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fractal_zoom_config.py")
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
    """Sample a color from palette at position t (0..1)."""
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


def run(device, stop_event):
    """Run the fractal zoom effect."""
    rows = device.fx.advanced.rows
    cols = device.fx.advanced.cols
    matrix = device.fx.advanced.matrix

    t = 0.0

    while not stop_event.is_set():
        cfg = load_config()
        interval = 1.0 / cfg.get("FPS", 15)
        zoom_speed = cfg.get("ZOOM_SPEED", 0.03)
        zoom_range = cfg.get("ZOOM_RANGE", 3.0)
        rotation_speed = cfg.get("ROTATION_SPEED", 0.01)
        max_iter = cfg.get("MAX_ITER", 20)
        center_re = cfg.get("CENTER_RE", -0.75)
        center_im = cfg.get("CENTER_IM", 0.0)
        julia_mode = cfg.get("JULIA_MODE", False)
        julia_c_re = cfg.get("JULIA_C_RE", -0.7)
        julia_c_im = cfg.get("JULIA_C_IM", 0.27015)
        palette = cfg.get("PALETTE", [(10, 0, 21), (140, 0, 200), (10, 0, 21)])
        inside_color = cfg.get("INSIDE_COLOR", (10, 0, 21))
        pulse = cfg.get("PULSE", True)
        pulse_speed = cfg.get("PULSE_SPEED", 0.05)
        pulse_amount = cfg.get("PULSE_AMOUNT", 0.25)

        # Zoom level oscillates for continuous zoom effect
        zoom_phase = (t * zoom_speed) % zoom_range
        zoom = 0.5 * math.exp(-zoom_phase)  # exponential zoom in, resets

        # Rotation
        rot = t * rotation_speed
        cos_r = math.cos(rot)
        sin_r = math.sin(rot)

        # Pulse brightness
        brightness = 1.0
        if pulse:
            brightness = 1.0 - pulse_amount * (0.5 + 0.5 * math.sin(t * pulse_speed))

        # Color cycling offset
        color_offset = t * 0.005

        for r in range(rows):
            for c in range(cols):
                # Map pixel to complex plane
                px = (c - cols / 2.0) / cols * zoom * 4.0
                py = (r - rows / 2.0) / rows * zoom * 4.0

                # Apply rotation
                rx = px * cos_r - py * sin_r
                ry = px * sin_r + py * cos_r

                if julia_mode:
                    zr, zi = rx, ry
                    cr, ci = julia_c_re, julia_c_im
                else:
                    zr, zi = 0.0, 0.0
                    cr = center_re + rx
                    ci = center_im + ry

                # Iterate
                iteration = 0
                for iteration in range(max_iter):
                    if zr * zr + zi * zi > 4.0:
                        break
                    zr, zi = zr * zr - zi * zi + cr, 2.0 * zr * zi + ci
                else:
                    # Inside the set
                    color = inside_color
                    if brightness < 1.0:
                        color = (
                            int(color[0] * brightness),
                            int(color[1] * brightness),
                            int(color[2] * brightness),
                        )
                    matrix[r, c] = color
                    continue

                # Smooth coloring
                if zr * zr + zi * zi > 1.0:
                    smooth = iteration + 1 - math.log(math.log(math.sqrt(zr * zr + zi * zi))) / math.log(2)
                else:
                    smooth = float(iteration)

                t_color = (smooth / max_iter + color_offset) % 1.0
                color = sample_palette(palette, t_color)

                if brightness < 1.0:
                    color = (
                        int(color[0] * brightness),
                        int(color[1] * brightness),
                        int(color[2] * brightness),
                    )

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

    print(f"{device.name} ({device.fx.advanced.cols}x{device.fx.advanced.rows}) - fractal zoom")
    print("Ctrl+C to stop")

    signal.signal(signal.SIGINT, lambda *_: stop_event.set())
    signal.signal(signal.SIGTERM, lambda *_: stop_event.set())

    run(device, stop_event)


if __name__ == "__main__":
    main()
