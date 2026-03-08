#!/usr/bin/env python3
"""Boid Flock - Reynolds flocking simulation with luminous trails.

Autonomous boid agents follow classic flocking rules (separation, alignment,
cohesion) creating emergent swarm behavior. Each boid deposits a glowing
trail that fades over time. Periodic startle events scatter the flock,
which then gracefully re-forms.

Edit boids_config.py while running to tweak on the fly.
"""

import math
import os
import random
import time

import numpy as np

from effects.common import (
    load_config, draw_frame, clear_keyboard, frame_sleep,
    build_palette_lut, palette_lookup, standalone_main,
)

EFFECT_NAME = "Boid Flock"
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "boids_config.py")


def run(device, stop_event):
    rows = device.fx.advanced.rows
    cols = device.fx.advanced.cols

    cfg = load_config(CONFIG_PATH)
    num_boids = cfg.get("NUM_BOIDS", 18)

    # Initialize boids with random positions and velocities
    bx = np.random.uniform(1, cols - 2, num_boids)
    by = np.random.uniform(1, rows - 2, num_boids)
    bvx = np.random.uniform(-0.3, 0.3, num_boids)
    bvy = np.random.uniform(-0.3, 0.3, num_boids)

    # Trail buffer
    trail = np.zeros((rows, cols), dtype=np.float64)

    t = 0.0
    next_startle = random.randint(300, 500)
    next_frame = time.monotonic()

    while not stop_event.is_set():
        cfg = load_config(CONFIG_PATH)
        fps = cfg.get("FPS", 20)
        interval = 1.0 / fps
        visual_range = cfg.get("VISUAL_RANGE", 4.0)
        sep_dist = cfg.get("SEPARATION_DIST", 1.5)
        w_sep = cfg.get("W_SEPARATION", 0.08)
        w_ali = cfg.get("W_ALIGNMENT", 0.04)
        w_coh = cfg.get("W_COHESION", 0.03)
        w_wall = cfg.get("W_WALL", 0.15)
        margin = cfg.get("MARGIN", 1.5)
        min_speed = cfg.get("MIN_SPEED", 0.1)
        max_speed = cfg.get("MAX_SPEED", 0.5)
        trail_deposit = cfg.get("TRAIL_DEPOSIT", 0.8)
        trail_decay = cfg.get("TRAIL_DECAY", 0.85)
        aspect = cfg.get("ASPECT_RATIO", 2.2)
        startle_min = cfg.get("STARTLE_INTERVAL_MIN", 300)
        startle_max = cfg.get("STARTLE_INTERVAL_MAX", 500)
        startle_impulse = cfg.get("STARTLE_IMPULSE", 0.8)
        palette = cfg.get("PALETTE", [
            (0, 0, 8), (0, 20, 40), (0, 60, 80),
            (20, 120, 140), (80, 200, 180), (200, 255, 120), (255, 220, 60),
        ])
        lut = build_palette_lut(palette)

        n = len(bx)

        # Adjust boid count if config changed
        new_num = cfg.get("NUM_BOIDS", 18)
        if new_num > n:
            bx = np.append(bx, np.random.uniform(1, cols - 2, new_num - n))
            by = np.append(by, np.random.uniform(1, rows - 2, new_num - n))
            bvx = np.append(bvx, np.random.uniform(-0.2, 0.2, new_num - n))
            bvy = np.append(bvy, np.random.uniform(-0.2, 0.2, new_num - n))
        elif new_num < n:
            bx = bx[:new_num]
            by = by[:new_num]
            bvx = bvx[:new_num]
            bvy = bvy[:new_num]
        n = len(bx)

        # Startle check
        if t >= next_startle:
            angles = np.random.uniform(0, 2 * math.pi, n)
            bvx += np.cos(angles) * startle_impulse
            bvy += np.sin(angles) * startle_impulse
            next_startle = t + random.randint(startle_min, startle_max)

        # Flocking forces (brute force N^2)
        fx = np.zeros(n)
        fy = np.zeros(n)

        for i in range(n):
            sep_x, sep_y = 0.0, 0.0
            ali_x, ali_y = 0.0, 0.0
            coh_x, coh_y = 0.0, 0.0
            neighbors = 0
            sep_count = 0

            for j in range(n):
                if i == j:
                    continue
                dx = bx[j] - bx[i]
                dy = (by[j] - by[i]) * math.sqrt(aspect)
                dist = math.sqrt(dx * dx + dy * dy)

                if dist < visual_range:
                    neighbors += 1
                    ali_x += bvx[j]
                    ali_y += bvy[j]
                    coh_x += bx[j]
                    coh_y += by[j]

                    if dist < sep_dist and dist > 0.01:
                        sep_x -= (bx[j] - bx[i]) / dist
                        sep_y -= (by[j] - by[i]) / dist
                        sep_count += 1

            if neighbors > 0:
                # Alignment: steer toward average velocity
                ali_x = ali_x / neighbors - bvx[i]
                ali_y = ali_y / neighbors - bvy[i]
                # Cohesion: steer toward center of mass
                coh_x = coh_x / neighbors - bx[i]
                coh_y = coh_y / neighbors - by[i]

                fx[i] += sep_x * w_sep + ali_x * w_ali + coh_x * w_coh
                fy[i] += sep_y * w_sep + ali_y * w_ali + coh_y * w_coh

            # Wall avoidance
            if bx[i] < margin:
                fx[i] += w_wall * (margin - bx[i])
            if bx[i] > cols - 1 - margin:
                fx[i] -= w_wall * (bx[i] - (cols - 1 - margin))
            if by[i] < margin:
                fy[i] += w_wall * (margin - by[i])
            if by[i] > rows - 1 - margin:
                fy[i] -= w_wall * (by[i] - (rows - 1 - margin))

        # Update velocities
        bvx += fx
        bvy += fy

        # Clamp speed
        speeds = np.sqrt(bvx * bvx + bvy * bvy)
        for i in range(n):
            if speeds[i] > max_speed:
                bvx[i] = bvx[i] / speeds[i] * max_speed
                bvy[i] = bvy[i] / speeds[i] * max_speed
            elif speeds[i] < min_speed and speeds[i] > 0.001:
                bvx[i] = bvx[i] / speeds[i] * min_speed
                bvy[i] = bvy[i] / speeds[i] * min_speed

        # Update positions
        bx += bvx
        by += bvy

        # Soft boundary clamp
        bx = np.clip(bx, 0, cols - 1)
        by = np.clip(by, 0, rows - 1)

        # Decay trail
        trail *= trail_decay

        # Deposit trail at boid positions
        for i in range(n):
            ri = int(round(by[i]))
            ci = int(round(bx[i]))
            if 0 <= ri < rows and 0 <= ci < cols:
                trail[ri, ci] = min(1.0, trail[ri, ci] + trail_deposit)
                # Subtle glow to neighbors
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = ri + dr, ci + dc
                    if 0 <= nr < rows and 0 <= nc < cols:
                        trail[nr, nc] = min(1.0, trail[nr, nc] + trail_deposit * 0.25)

        # Render
        values = np.clip(trail, 0.0, 1.0)
        frame_rgb = palette_lookup(lut, values)
        draw_frame(device, frame_rgb)

        next_frame, dt = frame_sleep(next_frame, interval)
        t += dt * fps

    clear_keyboard(device)


def main():
    standalone_main(EFFECT_NAME, run)


if __name__ == "__main__":
    main()
