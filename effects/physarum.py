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
import time

import numpy as np

from effects.common import (
    load_config, draw_frame, clear_keyboard, frame_sleep,
    build_palette_lut, palette_lookup, blur_3x3,
    standalone_main,
)

EFFECT_NAME = "Physarum"
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "physarum_config.py")


def run(device, stop_event):
    """Run the physarum slime mold effect."""
    rows = device.fx.advanced.rows
    cols = device.fx.advanced.cols

    # Load initial config to set up buffers
    cfg = load_config(CONFIG_PATH)
    buf_scale = cfg.get("BUFFER_SCALE", 4)
    buf_rows = buf_scale * rows
    buf_cols = buf_scale * cols
    num_agents = cfg.get("NUM_AGENTS", 120)

    # Trail map at buffer resolution (numpy 2D array)
    trail = np.zeros((buf_rows, buf_cols), dtype=np.float64)

    # Initialize agents: each has x, y (float), angle (radians)
    agents = []
    for _ in range(num_agents):
        agents.append({
            "x": random.random() * buf_cols,
            "y": random.random() * buf_rows,
            "angle": random.random() * 2.0 * math.pi,
        })

    next_frame = time.monotonic()

    while not stop_event.is_set():
        cfg = load_config(CONFIG_PATH)
        fps = cfg.get("FPS", 20)
        interval = 1.0 / fps
        sensor_angle = cfg.get("SENSOR_ANGLE", 0.6)
        sensor_dist = cfg.get("SENSOR_DIST", 4.0)
        turn_speed = cfg.get("TURN_SPEED", 0.5)
        move_speed = cfg.get("MOVE_SPEED", 1.0)
        deposit = cfg.get("DEPOSIT_AMOUNT", 3.0)
        decay = cfg.get("DECAY_RATE", 0.90)
        jitter = cfg.get("JITTER", 0.15)
        new_buf_scale = cfg.get("BUFFER_SCALE", 4)
        palette = cfg.get("PALETTE", [(0, 0, 0), (0, 30, 0), (20, 80, 0),
                                       (80, 180, 20), (180, 240, 80), (240, 255, 180)])

        lut = build_palette_lut(palette)

        # Recompute buffer dims (in case scale changed)
        new_buf_rows = new_buf_scale * rows
        new_buf_cols = new_buf_scale * cols

        if new_buf_rows != buf_rows or new_buf_cols != buf_cols:
            buf_scale = new_buf_scale
            buf_rows = new_buf_rows
            buf_cols = new_buf_cols
            trail = np.zeros((buf_rows, buf_cols), dtype=np.float64)

        # --- Step 1: Update agents (scalar loop, inherently sequential) ---
        for agent in agents:
            ax, ay, aa = agent["x"], agent["y"], agent["angle"]

            # Sample three sensors
            def sense(angle_offset):
                sx = ax + math.cos(aa + angle_offset) * sensor_dist
                sy = ay + math.sin(aa + angle_offset) * sensor_dist
                si = int(sy) % buf_rows
                sj = int(sx) % buf_cols
                return trail[si, sj]

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

            # Random jitter prevents permanent convergence
            aa += (random.random() - 0.5) * 2.0 * jitter

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
            trail[di, dj] += deposit

        # --- Step 2: Diffuse and decay trail map (vectorized) ---
        trail = blur_3x3(trail) * decay

        # --- Step 3: Downsample to keyboard resolution (vectorized) ---
        # Reshape trail into (rows, buf_scale, cols, buf_scale) and average
        display = trail.reshape(rows, buf_scale, cols, buf_scale).mean(axis=(1, 3))

        # --- Step 4: Map to colors and draw (vectorized) ---
        # Use sqrt to compress dynamic range — brings out subtle trail networks
        max_val = display.max()
        if max_val > 0.0:
            normalized = np.sqrt(np.minimum(display / max_val, 1.0))
        else:
            normalized = np.zeros_like(display)

        frame_rgb = palette_lookup(lut, normalized)
        draw_frame(device, frame_rgb)

        next_frame, _dt = frame_sleep(next_frame, interval)

    clear_keyboard(device)


def main():
    """Standalone entry point."""
    standalone_main(EFFECT_NAME, run)


if __name__ == "__main__":
    main()
