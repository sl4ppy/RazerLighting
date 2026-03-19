#!/usr/bin/env python3
"""Aurora Borealis - shimmering curtains of light dancing across the keyboard.

Multi-layer value noise creates flowing aurora bands with vertical curtain
displacement. Three color layers (green, cyan, magenta) drift at different
speeds with Gaussian vertical falloff, blended additively onto a dark sky.
Occasional star twinkles flash in the darker regions.

Edit aurora_config.py while running to tweak on the fly.
"""

import os
import time

import numpy as np

from effects.common import (
    load_config, draw_frame, clear_keyboard, frame_sleep,
    make_coordinate_grids, fbm, standalone_main,
)

EFFECT_NAME = "Aurora Borealis"
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "aurora_config.py")

_NOISE_SEED = 42


def run(device, stop_event):
    rows = device.fx.advanced.rows
    cols = device.fx.advanced.cols
    row_grid, col_grid = make_coordinate_grids(rows, cols)

    # Star state: tracks twinkle cooldown per pixel
    star_timer = np.zeros((rows, cols), dtype=np.int32)

    t = 0.0
    next_frame = time.monotonic()

    while not stop_event.is_set():
        cfg = load_config(CONFIG_PATH)
        fps = cfg.get("FPS", 20)
        interval = 1.0 / fps
        scroll_speed = cfg.get("SCROLL_SPEED", 0.03)
        curtain_freq = cfg.get("CURTAIN_FREQ", 0.8)
        curtain_speed = cfg.get("CURTAIN_SPEED", 0.05)
        fold_factor = cfg.get("FOLD_FACTOR", 0.4)
        noise_scale = cfg.get("NOISE_SCALE", 0.15)
        brightness = cfg.get("BRIGHTNESS", 1.0)
        bg = cfg.get("BG_COLOR", (0, 0, 8))

        bands = [
            (cfg.get("BAND_1_COLOR", (0, 220, 100)),
             cfg.get("BAND_1_ROW", 1.5),
             cfg.get("BAND_1_WIDTH", 2.0), 1.0),
            (cfg.get("BAND_2_COLOR", (0, 180, 255)),
             cfg.get("BAND_2_ROW", 2.5),
             cfg.get("BAND_2_WIDTH", 1.5), 0.7),
            (cfg.get("BAND_3_COLOR", (200, 40, 255)),
             cfg.get("BAND_3_ROW", 3.5),
             cfg.get("BAND_3_WIDTH", 1.0), 1.3),
        ]

        star_chance = cfg.get("STAR_CHANCE", 0.008)
        star_color = cfg.get("STAR_COLOR", (255, 255, 255))

        # Start with background
        frame = np.full((rows, cols, 3), bg, dtype=np.float64)

        # Curtain displacement
        curtain_offset = np.sin(
            col_grid * curtain_freq + t * curtain_speed + row_grid * fold_factor
        )

        # Render each aurora band
        for color, center_row, band_width, speed_mult in bands:
            # Sample noise at displaced coordinates
            nx = (col_grid + curtain_offset * 2.0) * noise_scale
            ny = t * scroll_speed * speed_mult + row_grid * noise_scale * 0.5
            n = fbm(nx, ny, octaves=2, weights=(0.7, 0.3), seed=_NOISE_SEED)

            # Vertical Gaussian falloff from band center
            row_dist = row_grid - center_row
            gaussian = np.exp(-row_dist * row_dist / (2.0 * band_width * band_width))

            # Combine noise with falloff
            intensity = n * gaussian * brightness

            # Additive blend
            c = np.array(color, dtype=np.float64)
            frame += intensity[:, :, np.newaxis] * c[np.newaxis, np.newaxis, :]

        # Star twinkle
        star_timer = np.maximum(0, star_timer - 1)
        dark_mask = np.sum(frame, axis=2) < 60  # dark pixels
        new_stars = (np.random.random((rows, cols)) < star_chance) & dark_mask & (star_timer == 0)
        star_timer[new_stars] = 3  # twinkle for 3 frames
        twinkling = star_timer > 0
        if np.any(twinkling):
            twinkle_brightness = star_timer.astype(np.float64) / 3.0
            sc = np.array(star_color, dtype=np.float64)
            for ch in range(3):
                frame[:, :, ch] = np.where(
                    twinkling,
                    frame[:, :, ch] + sc[ch] * twinkle_brightness,
                    frame[:, :, ch]
                )

        frame_rgb = np.clip(frame, 0, 255).astype(np.uint8)
        draw_frame(device, frame_rgb)
        next_frame, dt = frame_sleep(next_frame, interval)
        t += dt * fps

    clear_keyboard(device)


def main():
    standalone_main(EFFECT_NAME, run)


if __name__ == "__main__":
    main()
