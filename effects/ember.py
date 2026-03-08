#!/usr/bin/env python3
"""Ember Drift - glowing particles rise from a smoldering bed.

A particle system where hot embers spawn along the bottom edge, drifting
upward with lateral wind turbulence. Particles cool as they rise, shifting
from white-hot through orange to dark red before fading out. The bottom
rows shimmer with an ember bed glow.

Edit ember_config.py while running to tweak on the fly.
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

EFFECT_NAME = "Ember Drift"
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ember_config.py")


def run(device, stop_event):
    rows = device.fx.advanced.rows
    cols = device.fx.advanced.cols

    # Particle state arrays
    max_particles = 80
    px = np.zeros(max_particles)   # x position (col)
    py = np.zeros(max_particles)   # y position (row)
    page = np.zeros(max_particles) # current age
    pmax = np.zeros(max_particles) # max age
    pbright = np.zeros(max_particles)  # brightness multiplier
    pactive = np.zeros(max_particles, dtype=bool)

    t = 0.0
    next_frame = time.monotonic()

    while not stop_event.is_set():
        cfg = load_config(CONFIG_PATH)
        fps = cfg.get("FPS", 20)
        interval = 1.0 / fps
        num_embers = cfg.get("NUM_EMBERS", 60)
        spawn_rate = cfg.get("SPAWN_RATE", 0.4)
        rise_speed = cfg.get("RISE_SPEED", 0.12)
        rise_jitter = cfg.get("RISE_JITTER", 0.05)
        wind_strength = cfg.get("WIND_STRENGTH", 0.3)
        wind_speed = cfg.get("WIND_SPEED", 0.02)
        wind_phase = cfg.get("WIND_PHASE", 0.5)
        spark_chance = cfg.get("SPARK_CHANCE", 0.02)
        max_age = cfg.get("MAX_AGE", 50)
        bed_glow = cfg.get("BED_GLOW", 0.3)
        palette = cfg.get("PALETTE", [
            (0, 0, 0), (40, 0, 8), (120, 10, 5),
            (200, 60, 0), (255, 140, 20), (255, 220, 100), (255, 255, 220),
        ])
        lut = build_palette_lut(palette)

        active_count = int(np.sum(pactive))

        # Spawn new embers
        num_to_spawn = 0
        if spawn_rate >= 1.0:
            num_to_spawn = int(spawn_rate)
        elif random.random() < spawn_rate:
            num_to_spawn = 1

        # Occasional bright spark
        is_spark = random.random() < spark_chance

        for _ in range(num_to_spawn):
            if active_count >= num_embers:
                break
            # Find inactive slot
            inactive = np.where(~pactive)[0]
            if len(inactive) == 0:
                break
            idx = inactive[0]
            px[idx] = random.uniform(0, cols - 1)
            py[idx] = random.uniform(rows - 2.0, rows - 0.5)
            page[idx] = 0
            if is_spark:
                pmax[idx] = max_age * 0.5
                pbright[idx] = 2.0
                is_spark = False
            else:
                pmax[idx] = max_age * random.uniform(0.6, 1.0)
                pbright[idx] = random.uniform(0.6, 1.0)
            pactive[idx] = True
            active_count += 1

        # Update active particles
        active_mask = pactive
        # Rise
        py[active_mask] -= rise_speed + np.random.uniform(0, rise_jitter, np.sum(active_mask))
        # Wind
        wind = np.sin(t * wind_speed + py[active_mask] * wind_phase) * wind_strength
        wind += np.random.uniform(-0.05, 0.05, np.sum(active_mask))
        px[active_mask] += wind
        # Age
        page[active_mask] += 1
        # Kill old or off-screen
        kill = active_mask & ((py < -0.5) | (page > pmax))
        pactive[kill] = False

        # Render frame
        frame = np.zeros((rows, cols, 3), dtype=np.float64)

        # Ember bed glow on bottom two rows
        for r in range(max(0, rows - 2), rows):
            for c in range(cols):
                flicker = bed_glow * random.uniform(0.5, 1.0)
                # Map bed glow through warm part of palette
                bed_color = lut[min(255, int(flicker * 120))]
                frame[r, c] = bed_color

        # Render particles
        for i in range(max_particles):
            if not pactive[i]:
                continue
            heat = 1.0 - (page[i] / pmax[i])
            heat = max(0.0, min(1.0, heat))
            intensity = heat * pbright[i]

            # Map to pixel coordinates
            pr = int(round(py[i]))
            pc = int(round(px[i]))

            if 0 <= pr < rows and 0 <= pc < cols:
                color = lut[min(255, int(intensity * 255))]
                # Additive blending
                frame[pr, pc] = np.minimum(255, frame[pr, pc] + color * intensity)

            # Glow to adjacent pixels for larger/brighter embers
            if intensity > 0.5:
                glow = intensity * 0.3
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    gr, gc = pr + dr, pc + dc
                    if 0 <= gr < rows and 0 <= gc < cols:
                        glow_color = lut[min(255, int(glow * 255))]
                        frame[gr, gc] = np.minimum(255, frame[gr, gc] + glow_color * glow)

        frame_rgb = np.clip(frame, 0, 255).astype(np.uint8)
        draw_frame(device, frame_rgb)
        next_frame, dt = frame_sleep(next_frame, interval)
        t += dt * fps

    clear_keyboard(device)


def main():
    standalone_main(EFFECT_NAME, run)


if __name__ == "__main__":
    main()
