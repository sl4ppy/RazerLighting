#!/usr/bin/env python3
"""Magnetic Field Lines - iron filings visualization of drifting magnetic poles.

Four magnetic poles (positive and negative) drift across the keyboard
on Lissajous paths. The field is visualized as iron filing patterns:
bright lines aligned with the local field direction, with red glow
near positive poles and blue glow near negative poles.

Edit magnetic_field_config.py while running to tweak on the fly.
"""

import math
import os
import random
import signal
import sys
import threading
import time

EFFECT_NAME = "Magnetic Field Lines"
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "magnetic_field_config.py")
BLACK = (0, 0, 0)


def load_config():
    cfg = {}
    try:
        with open(CONFIG_PATH) as f:
            exec(f.read(), cfg)
    except Exception as e:
        print(f"Config load error: {e}", file=sys.stderr)
    return cfg


def clamp(v, lo=0, hi=255):
    return max(lo, min(hi, int(v)))


def run(device, stop_event):
    """Run the magnetic field lines effect."""
    rows = device.fx.advanced.rows
    cols = device.fx.advanced.cols
    matrix = device.fx.advanced.matrix

    t = 0.0

    # Initialize poles with random Lissajous parameters
    # Each pole: charge, cx, cy, ax, ay, fx, fy, px, py
    poles = []
    for i in range(4):
        charge = 1.0 if i % 2 == 0 else -1.0
        cx = random.uniform(3.0, cols - 4.0)
        cy = random.uniform(1.0, rows - 2.0)
        ax = random.uniform(2.0, min(cx, cols - 1 - cx))
        ay = random.uniform(0.5, min(cy, rows - 1 - cy))
        fx = random.uniform(0.3, 1.2)
        fy = random.uniform(0.3, 1.2)
        px = random.uniform(0, 2 * math.pi)
        py = random.uniform(0, 2 * math.pi)
        poles.append({
            "charge": charge,
            "cx": cx, "cy": cy,
            "ax": ax, "ay": ay,
            "fx": fx, "fy": fy,
            "px": px, "py": py,
        })

    while not stop_event.is_set():
        cfg = load_config()
        interval = 1.0 / cfg.get("FPS", 20)
        num_poles = cfg.get("NUM_POLES", 4)
        pole_speed = cfg.get("POLE_SPEED", 0.006)
        pole_glow_radius = cfg.get("POLE_GLOW_RADIUS", 2.5)
        pole_glow_intensity = cfg.get("POLE_GLOW_INTENSITY", 0.6)
        num_lines = cfg.get("NUM_LINES", 6)
        field_scale = cfg.get("FIELD_SCALE", 0.3)
        line_color = cfg.get("LINE_COLOR", (0, 200, 220))
        pos_pole_color = cfg.get("POS_POLE_COLOR", (255, 40, 40))
        neg_pole_color = cfg.get("NEG_POLE_COLOR", (40, 40, 255))
        bg = cfg.get("BG_COLOR", (0, 2, 5))

        # Ensure we have enough poles
        while len(poles) < num_poles:
            charge = 1.0 if len(poles) % 2 == 0 else -1.0
            poles.append({
                "charge": charge,
                "cx": random.uniform(3.0, cols - 4.0),
                "cy": random.uniform(1.0, rows - 2.0),
                "ax": random.uniform(2.0, 5.0),
                "ay": random.uniform(0.5, 1.5),
                "fx": random.uniform(0.3, 1.2),
                "fy": random.uniform(0.3, 1.2),
                "px": random.uniform(0, 2 * math.pi),
                "py": random.uniform(0, 2 * math.pi),
            })

        # Compute current pole positions
        pole_positions = []
        for i in range(num_poles):
            p = poles[i]
            px = p["cx"] + p["ax"] * math.sin(p["fx"] * t * pole_speed + p["px"])
            py = p["cy"] + p["ay"] * math.sin(p["fy"] * t * pole_speed + p["py"])
            # Clamp to keyboard bounds
            px = max(0.0, min(cols - 1.0, px))
            py = max(0.0, min(rows - 1.0, py))
            pole_positions.append((px, py, p["charge"]))

        # Render frame
        epsilon = 0.1

        for r in range(rows):
            for c in range(cols):
                # Compute total field vector at this pixel
                field_x = 0.0
                field_y = 0.0

                for pole_x, pole_y, charge in pole_positions:
                    dx = c - pole_x
                    dy = r - pole_y
                    dist = math.sqrt(dx * dx + dy * dy) + epsilon
                    strength = charge / (dist * dist)
                    field_x += strength * dx / dist
                    field_y += strength * dy / dist

                # Iron filings visualization
                field_mag = math.sqrt(field_x * field_x + field_y * field_y)
                angle = math.atan2(field_y, field_x)
                magnitude_factor = min(1.0, field_mag * field_scale)
                brightness = abs(math.sin(num_lines * angle)) * magnitude_factor

                # Base color from field lines
                cr_out = bg[0] + brightness * (line_color[0] - bg[0])
                cg_out = bg[1] + brightness * (line_color[1] - bg[1])
                cb_out = bg[2] + brightness * (line_color[2] - bg[2])

                # Add pole glow (additive)
                for pole_x, pole_y, charge in pole_positions:
                    dx = c - pole_x
                    dy = r - pole_y
                    dist = math.sqrt(dx * dx + dy * dy)
                    if dist < pole_glow_radius:
                        glow = (1.0 - dist / pole_glow_radius) * pole_glow_intensity
                        if charge > 0:
                            cr_out += pos_pole_color[0] * glow
                            cg_out += pos_pole_color[1] * glow
                            cb_out += pos_pole_color[2] * glow
                        else:
                            cr_out += neg_pole_color[0] * glow
                            cg_out += neg_pole_color[1] * glow
                            cb_out += neg_pole_color[2] * glow

                matrix[r, c] = (clamp(cr_out), clamp(cg_out), clamp(cb_out))

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

    print(f"{device.name} ({device.fx.advanced.cols}x{device.fx.advanced.rows}) - magnetic field")
    print("Ctrl+C to stop")

    signal.signal(signal.SIGINT, lambda *_: stop_event.set())
    signal.signal(signal.SIGTERM, lambda *_: stop_event.set())

    run(device, stop_event)


if __name__ == "__main__":
    main()
