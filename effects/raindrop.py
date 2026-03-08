#!/usr/bin/env python3
"""Raindrop Ripples - concentric rings expand and interfere across the keyboard.

Raindrops land at random positions, spawning radial ripple rings that expand
outward with amplitude decay. Multiple concurrent ripples create beautiful
wave interference patterns with a moonlit water surface aesthetic.

Edit raindrop_config.py while running to tweak on the fly.
"""

import math
import os
import random
import time

import numpy as np

from effects.common import (
    load_config, draw_frame, clear_keyboard, frame_sleep,
    build_palette_lut, palette_lookup, make_coordinate_grids,
    standalone_main,
)

EFFECT_NAME = "Raindrop Ripples"
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "raindrop_config.py")


def run(device, stop_event):
    rows = device.fx.advanced.rows
    cols = device.fx.advanced.cols
    row_grid, col_grid = make_coordinate_grids(rows, cols)

    ripples = []  # list of (cx, cy, birth_t, amplitude)
    t = 0.0
    next_frame = time.monotonic()

    while not stop_event.is_set():
        cfg = load_config(CONFIG_PATH)
        interval = 1.0 / cfg.get("FPS", 24)
        spawn_chance = cfg.get("SPAWN_CHANCE", 0.08)
        max_ripples = cfg.get("MAX_RIPPLES", 8)
        expand_speed = cfg.get("EXPAND_SPEED", 0.6)
        ring_freq = cfg.get("RING_FREQ", 3.0)
        ring_width = cfg.get("RING_WIDTH", 1.5)
        decay_rate = cfg.get("DECAY_RATE", 0.15)
        max_age = cfg.get("MAX_AGE", 40)
        aspect = cfg.get("ASPECT_RATIO", 2.2)
        splash_frames = cfg.get("SPLASH_FRAMES", 2)
        splash_color = cfg.get("SPLASH_COLOR", (180, 220, 255))
        palette = cfg.get("PALETTE", [
            (0, 5, 20), (0, 10, 40), (0, 15, 50),
            (20, 80, 160), (80, 180, 255), (200, 240, 255),
        ])
        lut = build_palette_lut(palette)

        # Spawn new ripple
        if random.random() < spawn_chance and len(ripples) < max_ripples:
            cx = random.uniform(0, cols - 1)
            cy = random.uniform(0, rows - 1)
            ripples.append((cx, cy, t, 1.0))

        # Compute interference field
        field = np.zeros((rows, cols), dtype=np.float64)
        splash_mask = np.zeros((rows, cols), dtype=np.float64)

        alive = []
        for cx, cy, birth_t, amplitude in ripples:
            age = t - birth_t
            if age > max_age:
                continue
            decay = amplitude / (1.0 + age * decay_rate)
            if decay < 0.03:
                continue
            alive.append((cx, cy, birth_t, amplitude))

            # Radial distance with aspect correction
            dx = (col_grid - cx) / math.sqrt(aspect)
            dy = row_grid - cy
            r = np.sqrt(dx * dx + dy * dy)

            # Ring wavefront
            wave_r = r - age * expand_speed
            ring = np.cos(wave_r * ring_freq) * np.exp(-wave_r * wave_r / (ring_width * ring_width))
            field += ring * decay

            # Splash effect at impact
            if age < splash_frames:
                splash_intensity = 1.0 - age / splash_frames
                splash_r = np.exp(-r * r * 2.0)
                splash_mask = np.maximum(splash_mask, splash_r * splash_intensity)

        ripples = alive

        # Normalize field to [0, 1] for palette mapping
        # Center around 0.4 so calm water is dark blue, crests are bright
        values = np.clip(field * 0.3 + 0.4, 0.0, 1.0)
        frame_rgb = palette_lookup(lut, values).astype(np.float64)

        # Add splash highlights
        if np.any(splash_mask > 0.01):
            sc = np.array(splash_color, dtype=np.float64)
            splash_3d = splash_mask[:, :, np.newaxis]
            frame_rgb = frame_rgb * (1.0 - splash_3d) + sc * splash_3d

        frame_rgb = np.clip(frame_rgb, 0, 255).astype(np.uint8)
        draw_frame(device, frame_rgb)
        t += 1.0
        next_frame = frame_sleep(next_frame, interval)

    clear_keyboard(device)


def main():
    standalone_main(EFFECT_NAME, run)


if __name__ == "__main__":
    main()
