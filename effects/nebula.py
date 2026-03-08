#!/usr/bin/env python3
"""Nebula Clouds - deep space gas clouds with dual-layer fractal noise.

Two independent noise layers create a sense of depth: a warm nebula layer
(purple/magenta/pink) and cool accent clouds (dark blue/teal). Both drift
at different speeds and angles for parallax. Bright pixels occasionally
flash as newborn stars within the gas.

Edit nebula_config.py while running to tweak on the fly.
"""

import math
import os
import time

import numpy as np

from effects.common import (
    load_config, draw_frame, clear_keyboard, frame_sleep,
    build_palette_lut, palette_lookup, make_coordinate_grids,
    standalone_main,
)

EFFECT_NAME = "Nebula Clouds"
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "nebula_config.py")

# --- Value noise (same algorithm as aurora, different seed for variety) ---

_perm = np.arange(256, dtype=np.int32)
np.random.RandomState(137).shuffle(_perm)
_perm = np.tile(_perm, 2)


def _fade(t):
    return t * t * t * (t * (t * 6 - 15) + 10)


def noise_2d(x, y):
    xi = np.floor(x).astype(np.int32) & 255
    yi = np.floor(y).astype(np.int32) & 255
    xf = x - np.floor(x)
    yf = y - np.floor(y)
    u = _fade(xf)
    v = _fade(yf)
    aa = _perm[_perm[xi] + yi]
    ab = _perm[_perm[xi] + yi + 1]
    ba = _perm[_perm[xi + 1] + yi]
    bb = _perm[_perm[xi + 1] + yi + 1]
    x1 = aa / 255.0 + u * (ba / 255.0 - aa / 255.0)
    x2 = ab / 255.0 + u * (bb / 255.0 - ab / 255.0)
    return x1 + v * (x2 - x1)


def fbm_3oct(x, y):
    """Three-octave fractal Brownian motion."""
    return noise_2d(x, y) * 0.55 + noise_2d(x * 2, y * 2) * 0.3 + noise_2d(x * 4, y * 4) * 0.15


def fbm_2oct(x, y):
    """Two-octave fractal Brownian motion."""
    return noise_2d(x, y) * 0.65 + noise_2d(x * 2, y * 2) * 0.35


def run(device, stop_event):
    rows = device.fx.advanced.rows
    cols = device.fx.advanced.cols
    row_grid, col_grid = make_coordinate_grids(rows, cols)

    star_timer = np.zeros((rows, cols), dtype=np.int32)
    t = 0.0
    next_frame = time.monotonic()

    while not stop_event.is_set():
        cfg = load_config(CONFIG_PATH)
        interval = 1.0 / cfg.get("FPS", 18)
        scale1 = cfg.get("NOISE_SCALE_1", 0.12)
        scale2 = cfg.get("NOISE_SCALE_2", 0.18)
        drift1 = cfg.get("DRIFT_SPEED_1", 0.015)
        drift2 = cfg.get("DRIFT_SPEED_2", 0.022)
        angle1 = math.radians(cfg.get("DRIFT_ANGLE_1", 30))
        angle2 = math.radians(cfg.get("DRIFT_ANGLE_2", 150))
        accent = cfg.get("ACCENT_STRENGTH", 0.4)
        bright_mult = cfg.get("BRIGHTNESS", 1.0)
        star_chance = cfg.get("STAR_CHANCE", 0.005)
        star_thresh = cfg.get("STAR_THRESHOLD", 0.85)
        star_color = cfg.get("STAR_COLOR", (255, 255, 255))
        pal_warm = cfg.get("PALETTE_WARM", [
            (0, 0, 0), (20, 0, 40), (80, 0, 100),
            (160, 20, 140), (220, 80, 200), (255, 160, 255),
        ])
        pal_cool = cfg.get("PALETTE_COOL", [
            (0, 0, 0), (0, 10, 40), (0, 40, 100), (0, 80, 160),
        ])
        lut_warm = build_palette_lut(pal_warm)
        lut_cool = build_palette_lut(pal_cool)

        # Drift vectors
        dx1 = math.cos(angle1) * drift1 * t
        dy1 = math.sin(angle1) * drift1 * t
        dx2 = math.cos(angle2) * drift2 * t
        dy2 = math.sin(angle2) * drift2 * t

        # Layer 1: warm nebula (3 octaves)
        nx1 = col_grid * scale1 + dx1
        ny1 = row_grid * scale1 + dy1
        n1 = fbm_3oct(nx1, ny1)
        # Boost contrast
        n1 = np.clip((n1 - 0.3) * 1.8, 0.0, 1.0) * bright_mult

        # Layer 2: cool accents (2 octaves)
        nx2 = col_grid * scale2 + dx2
        ny2 = row_grid * scale2 + dy2
        n2 = fbm_2oct(nx2, ny2)
        n2 = np.clip((n2 - 0.35) * 2.0, 0.0, 1.0)

        # Map through palettes
        warm_rgb = palette_lookup(lut_warm, n1).astype(np.float64)
        cool_rgb = palette_lookup(lut_cool, n2).astype(np.float64)

        # Additive blend
        frame = warm_rgb + cool_rgb * accent

        # Star birth flashes
        star_timer = np.maximum(0, star_timer - 1)
        bright_mask = n1 > star_thresh
        new_stars = (np.random.random((rows, cols)) < star_chance) & bright_mask & (star_timer == 0)
        star_timer[new_stars] = 4
        twinkling = star_timer > 0
        if np.any(twinkling):
            flash = (star_timer.astype(np.float64) / 4.0)[:, :, np.newaxis]
            sc = np.array(star_color, dtype=np.float64)
            twinkle_mask = twinkling[:, :, np.newaxis]
            frame = np.where(twinkle_mask, frame + sc * flash, frame)

        frame_rgb = np.clip(frame, 0, 255).astype(np.uint8)
        draw_frame(device, frame_rgb)
        t += 1.0
        next_frame = frame_sleep(next_frame, interval)

    clear_keyboard(device)


def main():
    standalone_main(EFFECT_NAME, run)


if __name__ == "__main__":
    main()
