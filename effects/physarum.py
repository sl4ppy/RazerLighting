#!/usr/bin/env python3
"""Physarum - slime mold simulation with emergent trail networks.

Agents wander a high-res buffer, depositing onto a trail map.  They sense
the trail ahead and steer toward higher concentrations, forming organic
vein-like networks.  The trail diffuses and decays each frame, producing
a living, breathing bioluminescent pattern on the keyboard.

Edit physarum_config.py while running to tweak on the fly.
"""

import math
import os
import random
import signal
import sys
import threading
import time

EFFECT_NAME = "Physarum"
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "physarum_config.py")
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
    """Run the physarum slime mold effect."""
    rows = device.fx.advanced.rows
    cols = device.fx.advanced.cols
    matrix = device.fx.advanced.matrix

    # Load initial config to set up buffers
    cfg = load_config()
    buf_scale = cfg.get("BUFFER_SCALE", 2)
    buf_rows = buf_scale * rows
    buf_cols = buf_scale * cols
    num_agents = cfg.get("NUM_AGENTS", 150)

    # Trail map at buffer resolution
    trail = [[0.0] * buf_cols for _ in range(buf_rows)]

    # Initialize agents: each has x, y (float), angle (radians)
    agents = []
    for _ in range(num_agents):
        agents.append({
            "x": random.random() * buf_cols,
            "y": random.random() * buf_rows,
            "angle": random.random() * 2.0 * math.pi,
        })

    while not stop_event.is_set():
        cfg = load_config()
        interval = 1.0 / cfg.get("FPS", 20)
        sensor_angle = cfg.get("SENSOR_ANGLE", 0.5)
        sensor_dist = cfg.get("SENSOR_DIST", 3.0)
        turn_speed = cfg.get("TURN_SPEED", 0.4)
        move_speed = cfg.get("MOVE_SPEED", 1.0)
        deposit = cfg.get("DEPOSIT_AMOUNT", 5.0)
        decay = cfg.get("DECAY_RATE", 0.92)
        buf_scale = cfg.get("BUFFER_SCALE", 2)
        palette = cfg.get("PALETTE", [(0, 0, 0), (0, 30, 0), (20, 80, 0),
                                       (80, 180, 20), (180, 240, 80), (240, 255, 180)])

        # Recompute buffer dims (in case scale changed)
        buf_rows = buf_scale * rows
        buf_cols = buf_scale * cols

        # Resize trail map if needed
        if len(trail) != buf_rows or (trail and len(trail[0]) != buf_cols):
            trail = [[0.0] * buf_cols for _ in range(buf_rows)]

        # --- Step 1: Update agents ---
        for agent in agents:
            ax, ay, aa = agent["x"], agent["y"], agent["angle"]

            # Sample three sensors
            def sense(angle_offset):
                sx = ax + math.cos(aa + angle_offset) * sensor_dist
                sy = ay + math.sin(aa + angle_offset) * sensor_dist
                si = int(sy) % buf_rows
                sj = int(sx) % buf_cols
                return trail[si][sj]

            f_left = sense(-sensor_angle)
            f_center = sense(0.0)
            f_right = sense(sensor_angle)

            # Steer toward highest trail value
            if f_center >= f_left and f_center >= f_right:
                pass  # go straight
            elif f_left > f_right:
                aa -= turn_speed
            elif f_right > f_left:
                aa += turn_speed
            else:
                # left == right and both > center: pick randomly
                aa += turn_speed * random.choice([-1, 1])

            # Move forward
            ax += math.cos(aa) * move_speed
            ay += math.sin(aa) * move_speed

            # Wrap toroidally
            ax = ax % buf_cols
            ay = ay % buf_rows

            agent["x"] = ax
            agent["y"] = ay
            agent["angle"] = aa

            # Deposit trail
            di = int(ay) % buf_rows
            dj = int(ax) % buf_cols
            trail[di][dj] += deposit

        # --- Step 2: Diffuse and decay trail map ---
        new_trail = [[0.0] * buf_cols for _ in range(buf_rows)]
        for r in range(buf_rows):
            for c in range(buf_cols):
                total = 0.0
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        total += trail[(r + dr) % buf_rows][(c + dc) % buf_cols]
                new_trail[r][c] = (total / 9.0) * decay
        trail = new_trail

        # --- Step 3: Downsample to keyboard resolution ---
        # Find max trail value for normalization
        max_val = 0.0
        display = [[0.0] * cols for _ in range(rows)]
        for r in range(rows):
            for c in range(cols):
                total = 0.0
                for br in range(buf_scale):
                    for bc in range(buf_scale):
                        total += trail[r * buf_scale + br][c * buf_scale + bc]
                avg = total / (buf_scale * buf_scale)
                display[r][c] = avg
                if avg > max_val:
                    max_val = avg

        # --- Step 4: Map to colors and draw ---
        for r in range(rows):
            for c in range(cols):
                if max_val > 0.0:
                    t = min(1.0, display[r][c] / max_val)
                else:
                    t = 0.0
                matrix[r, c] = sample_palette(palette, t)

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

    print(f"{device.name} ({device.fx.advanced.cols}x{device.fx.advanced.rows}) - physarum")
    print("Ctrl+C to stop")

    signal.signal(signal.SIGINT, lambda *_: stop_event.set())
    signal.signal(signal.SIGTERM, lambda *_: stop_event.set())

    run(device, stop_event)


if __name__ == "__main__":
    main()
