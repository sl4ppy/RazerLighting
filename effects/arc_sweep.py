#!/usr/bin/env python3
"""Arc Sweep — luminous curved wavefronts sweep across the keyboard.

Arcs expand from off-screen focal points, creating gently curved
shockwave-like sweeps.  Optional domain warping distorts wavefronts
organically, and chromatic edge-splitting adds prismatic fringe.

Edit arc_sweep_config.py while running to tweak on the fly.
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

EFFECT_NAME = "Arc Sweep"
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "arc_sweep_config.py")

# --- Value noise for domain warping ---

_perm = np.arange(256, dtype=np.int32)
np.random.RandomState(7).shuffle(_perm)
_perm = np.tile(_perm, 2)


def _fade(t):
    return t * t * t * (t * (t * 6 - 15) + 10)


def _noise2d(x, y):
    """Vectorized 2D value noise, returns [0, 1]."""
    xi = np.floor(x).astype(np.int32) & 255
    yi = np.floor(y).astype(np.int32) & 255
    xf = x - np.floor(x)
    yf = y - np.floor(y)
    u, v = _fade(xf), _fade(yf)
    aa = _perm[_perm[xi] + yi] / 255.0
    ab = _perm[_perm[xi] + yi + 1] / 255.0
    ba = _perm[_perm[xi + 1] + yi] / 255.0
    bb = _perm[_perm[xi + 1] + yi + 1] / 255.0
    x1 = aa + u * (ba - aa)
    x2 = ab + u * (bb - ab)
    return x1 + v * (x2 - x1)


def spawn_arc(cfg, rows, cols):
    """Create a new arc expanding from a random off-screen focal point."""
    speed_min = cfg.get("SPEED_MIN", 4.0)
    speed_max = cfg.get("SPEED_MAX", 10.0)
    speed = speed_min + (speed_max - speed_min) * random.random()

    angle = random.uniform(0, 2 * math.pi)
    focal_dist = cfg.get("FOCAL_DISTANCE", 15.0)
    aspect = cfg.get("ASPECT_RATIO", 2.5)
    cx, cy = cols / 2.0, rows * aspect / 2.0

    fx = cx - math.cos(angle) * focal_dist
    fy = cy - math.sin(angle) * focal_dist

    corners = [(0, 0), (cols - 1, 0),
               (0, (rows - 1) * aspect), (cols - 1, (rows - 1) * aspect)]
    dists = [math.hypot(x - fx, y - fy) for x, y in corners]

    colors = cfg.get("COLORS", [
        (100, 180, 255), (200, 60, 255), (255, 40, 120), (60, 255, 200),
    ])
    color = random.choice(colors) if colors else (100, 180, 255)

    # Width scales with speed: slow arcs are thin and crisp, fast ones wider
    base_width = cfg.get("ARC_WIDTH", 1.0)
    speed_t = (speed - speed_min) / (speed_max - speed_min) if speed_max > speed_min else 0.5
    width = max(base_width * (0.5 + speed_t * 0.8), 0.3)

    return {
        "fx": fx, "fy": fy,
        "speed": speed,
        "radius": min(dists) - width * 2,
        "r_max": max(dists) + width * 3,
        "width": width,
        "color": np.array(color, dtype=np.float64),
        "noise_seed": random.uniform(0, 100),
    }


def run(device, stop_event):
    rows = device.fx.advanced.rows
    cols = device.fx.advanced.cols
    row_grid, col_grid = make_coordinate_grids(rows, cols)

    afterglow = np.zeros((rows, cols, 3), dtype=np.float64)
    arcs = []
    next_spawn = time.monotonic()
    t = 0.0
    next_frame = time.monotonic()

    while not stop_event.is_set():
        cfg = load_config(CONFIG_PATH)
        fps = cfg.get("FPS", 30)
        interval = 1.0 / fps
        max_arcs = cfg.get("MAX_ARCS", 5)

        if time.monotonic() >= next_spawn and len(arcs) < max_arcs:
            arcs.append(spawn_arc(cfg, rows, cols))
            next_spawn = time.monotonic() + random.uniform(
                cfg.get("PAUSE_MIN", 0.3), cfg.get("PAUSE_MAX", 2.0))

        aspect = cfg.get("ASPECT_RATIO", 2.5)
        warp_str = cfg.get("WARP_STRENGTH", 0.5)
        warp_scl = cfg.get("WARP_SCALE", 0.25)
        chroma = cfg.get("CHROMATIC_OFFSET", 0.15)
        glow_decay = cfg.get("AFTERGLOW_DECAY", 0.88)
        glow_dep = cfg.get("AFTERGLOW_DEPOSIT", 0.25)
        trail_c = np.array(cfg.get("TRAIL_COLOR", (40, 0, 80)),
                           dtype=np.float64)
        bg = np.array(cfg.get("BG_COLOR", (2, 0, 8)), dtype=np.float64)

        row_scaled = row_grid * aspect
        afterglow *= glow_decay

        frame = np.full((rows, cols, 3), bg, dtype=np.float64)
        frame += afterglow

        # Per-channel chromatic radius offsets: blue leads, red trails
        ch_offsets = [chroma, 0.0, -chroma]

        for arc in arcs:
            dx = col_grid - arc["fx"]
            dy = row_scaled - arc["fy"]
            dist = np.sqrt(dx * dx + dy * dy)

            # Domain warp for organic wavefront distortion
            if warp_str > 0:
                warp = (_noise2d(
                    col_grid * warp_scl + arc["noise_seed"],
                    row_grid * warp_scl + t * 0.012
                ) - 0.5) * 2.0 * warp_str
                dist_w = dist + warp
            else:
                dist_w = dist

            w = arc["width"]
            for ch in range(3):
                delta = dist_w - (arc["radius"] + ch_offsets[ch])

                # Asymmetric profile: sharp leading edge, moderate trail
                sigma = np.where(delta > 0, w * 0.3, w * 0.8)
                bright = np.exp(-delta * delta / (2.0 * sigma * sigma))

                # Trail color blend (smoothstep from arc color → trail color)
                tr = np.clip(-delta / (w * 2.0), 0.0, 1.0)
                tr = tr * tr * (3 - 2 * tr)
                color_val = arc["color"][ch] * (1 - tr) + trail_c[ch] * tr

                contrib = bright * color_val
                frame[:, :, ch] += contrib
                afterglow[:, :, ch] = np.maximum(
                    afterglow[:, :, ch], contrib * glow_dep)

        draw_frame(device, np.clip(frame, 0, 255).astype(np.uint8))

        next_frame, dt = frame_sleep(next_frame, interval)
        t += dt * fps
        for arc in arcs:
            arc["radius"] += arc["speed"] * dt
        arcs = [a for a in arcs if a["radius"] < a["r_max"]]

    clear_keyboard(device)


def main():
    standalone_main(EFFECT_NAME, run)


if __name__ == "__main__":
    main()
