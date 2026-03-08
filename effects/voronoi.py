#!/usr/bin/env python3
"""Voronoi Shatter - stained-glass Voronoi cells with neon edge glow.

Moving seed points create a dynamic Voronoi diagram. Each cell is colored
by its seed's slowly rotating hue with cyberpunk-inspired saturation.
Cell edges glow with configurable neon color. Periodic shatter events
split a seed, creating dramatic fracture lines before merging back.

Edit voronoi_config.py while running to tweak on the fly.
"""

import math
import os
import random
import time

import numpy as np

from effects.common import (
    load_config, draw_frame, clear_keyboard, frame_sleep,
    make_coordinate_grids, standalone_main,
)

EFFECT_NAME = "Voronoi Shatter"
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "voronoi_config.py")


def hsv_to_rgb_array(h, s, v):
    """Vectorized HSV to RGB. h in [0,360), s,v in [0,1]. Returns (R,G,B) float arrays."""
    h = h % 360.0
    c = v * s
    hp = h / 60.0
    x = c * (1.0 - np.abs(hp % 2 - 1.0))
    m = v - c

    r = np.zeros_like(h)
    g = np.zeros_like(h)
    b = np.zeros_like(h)

    mask0 = (hp >= 0) & (hp < 1)
    mask1 = (hp >= 1) & (hp < 2)
    mask2 = (hp >= 2) & (hp < 3)
    mask3 = (hp >= 3) & (hp < 4)
    mask4 = (hp >= 4) & (hp < 5)
    mask5 = (hp >= 5) & (hp < 6)

    r[mask0] = c[mask0]; g[mask0] = x[mask0]
    r[mask1] = x[mask1]; g[mask1] = c[mask1]
    g[mask2] = c[mask2]; b[mask2] = x[mask2]
    g[mask3] = x[mask3]; b[mask3] = c[mask3]
    r[mask4] = x[mask4]; b[mask4] = c[mask4]
    r[mask5] = c[mask5]; b[mask5] = x[mask5]

    return (r + m) * 255.0, (g + m) * 255.0, (b + m) * 255.0


def run(device, stop_event):
    rows = device.fx.advanced.rows
    cols = device.fx.advanced.cols
    row_grid, col_grid = make_coordinate_grids(rows, cols)

    cfg = load_config(CONFIG_PATH)
    num_seeds = cfg.get("NUM_SEEDS", 10)

    # Initialize seeds
    sx = np.random.uniform(0, cols - 1, num_seeds).astype(np.float64)
    sy = np.random.uniform(0, rows - 1, num_seeds).astype(np.float64)
    svx = np.random.uniform(-0.03, 0.03, num_seeds)
    svy = np.random.uniform(-0.03, 0.03, num_seeds)
    shue = np.random.uniform(0, 360, num_seeds)  # per-seed hue

    # Shatter state
    shatter_countdown = random.randint(200, 400)
    shatter_active = False
    shatter_timer = 0
    extra_seed_idx = -1

    t = 0.0
    next_frame = time.monotonic()

    while not stop_event.is_set():
        cfg = load_config(CONFIG_PATH)
        interval = 1.0 / cfg.get("FPS", 20)
        seed_speed = cfg.get("SEED_SPEED", 0.02)
        seed_jitter = cfg.get("SEED_JITTER", 0.005)
        hue_speed = cfg.get("HUE_SPEED", 0.3)
        edge_width = cfg.get("EDGE_WIDTH", 1.2)
        edge_color = cfg.get("EDGE_COLOR", (0, 255, 200))
        edge_bright = cfg.get("EDGE_BRIGHTNESS", 0.9)
        cell_bright = cfg.get("CELL_BRIGHTNESS", 0.6)
        aspect = cfg.get("ASPECT_RATIO", 2.2)
        shatter_dur = cfg.get("SHATTER_DURATION", 60)
        shatter_min = cfg.get("SHATTER_INTERVAL_MIN", 200)
        shatter_max = cfg.get("SHATTER_INTERVAL_MAX", 400)

        n = len(sx)

        # Update seed positions (brownian motion + boundary bounce)
        svx += np.random.uniform(-seed_jitter, seed_jitter, n)
        svy += np.random.uniform(-seed_jitter, seed_jitter, n)
        # Dampen velocity slightly to prevent runaway
        svx *= 0.98
        svy *= 0.98
        sx += svx
        sy += svy

        # Boundary reflection
        for i in range(n):
            if sx[i] < 0:
                sx[i] = -sx[i]; svx[i] = abs(svx[i])
            if sx[i] > cols - 1:
                sx[i] = 2 * (cols - 1) - sx[i]; svx[i] = -abs(svx[i])
            if sy[i] < 0:
                sy[i] = -sy[i]; svy[i] = abs(svy[i])
            if sy[i] > rows - 1:
                sy[i] = 2 * (rows - 1) - sy[i]; svy[i] = -abs(svy[i])

        # Rotate hues
        shue = (shue + hue_speed) % 360.0

        # Shatter management
        shatter_countdown -= 1
        if shatter_countdown <= 0 and not shatter_active:
            # Split a random seed
            src = random.randint(0, min(n - 1, num_seeds - 1))
            sx = np.append(sx, sx[src] + random.uniform(-0.5, 0.5))
            sy = np.append(sy, sy[src] + random.uniform(-0.5, 0.5))
            svx = np.append(svx, -svx[src] + random.uniform(-0.05, 0.05))
            svy = np.append(svy, -svy[src] + random.uniform(-0.05, 0.05))
            shue = np.append(shue, shue[src] + 30)
            extra_seed_idx = len(sx) - 1
            shatter_active = True
            shatter_timer = shatter_dur
            n = len(sx)

        if shatter_active:
            shatter_timer -= 1
            if shatter_timer <= 0:
                # Remove extra seed
                if extra_seed_idx >= 0 and extra_seed_idx < len(sx):
                    sx = np.delete(sx, extra_seed_idx)
                    sy = np.delete(sy, extra_seed_idx)
                    svx = np.delete(svx, extra_seed_idx)
                    svy = np.delete(svy, extra_seed_idx)
                    shue = np.delete(shue, extra_seed_idx)
                    n = len(sx)
                shatter_active = False
                extra_seed_idx = -1
                shatter_countdown = random.randint(shatter_min, shatter_max)

        # Compute Voronoi: for each pixel find nearest and second nearest seed
        # distances: (n, rows, cols)
        dx = col_grid[np.newaxis, :, :] - sx[:, np.newaxis, np.newaxis]
        dy = (row_grid[np.newaxis, :, :] - sy[:, np.newaxis, np.newaxis]) * math.sqrt(aspect)
        dists = np.sqrt(dx * dx + dy * dy)  # (n, rows, cols)

        # Nearest and second nearest
        sorted_idx = np.argsort(dists, axis=0)
        nearest_idx = sorted_idx[0]  # (rows, cols) — index of nearest seed

        # Get d1, d2
        d1 = np.take_along_axis(dists, sorted_idx[0:1], axis=0)[0]
        d2 = np.take_along_axis(dists, sorted_idx[1:2], axis=0)[0]

        # Edge detection
        edge_factor = np.clip(1.0 - (d2 - d1) / edge_width, 0.0, 1.0)
        # Boost edge during shatter
        if shatter_active:
            edge_factor = np.clip(edge_factor * 1.5, 0.0, 1.0)

        # Cell colors from seed hues
        cell_hues = shue[nearest_idx]  # (rows, cols)
        # Vary saturation with distance from seed center
        max_d = np.maximum(d1.max(), 0.01)
        sat = 0.6 + 0.4 * np.clip(d1 / (max_d * 0.5), 0.0, 1.0)
        sat = np.minimum(sat, 1.0)

        cr, cg, cb = hsv_to_rgb_array(cell_hues, sat, np.full_like(sat, cell_bright))

        # Edge color overlay
        ec = np.array(edge_color, dtype=np.float64)
        edge_3d = edge_factor * edge_bright

        frame_r = cr * (1.0 - edge_3d) + ec[0] * edge_3d
        frame_g = cg * (1.0 - edge_3d) + ec[1] * edge_3d
        frame_b = cb * (1.0 - edge_3d) + ec[2] * edge_3d

        frame_rgb = np.stack([frame_r, frame_g, frame_b], axis=2)
        frame_rgb = np.clip(frame_rgb, 0, 255).astype(np.uint8)
        draw_frame(device, frame_rgb)

        t += 1.0
        next_frame = frame_sleep(next_frame, interval)

    clear_keyboard(device)


def main():
    standalone_main(EFFECT_NAME, run)


if __name__ == "__main__":
    main()
