#!/usr/bin/env python3
"""Arc Sweep - arcs of light sweeping across the keyboard from random directions.

Multiple arcs can be alive simultaneously, overlapping and crossing.
Edit arc_sweep_config.py while running to tweak on the fly.
"""

import math
import os
import random
import time

from effects.common import load_config, clear_keyboard, frame_sleep, standalone_main

EFFECT_NAME = "Arc Sweep"
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "arc_sweep_config.py")


def build_trail(full_trail, speed, speed_min, speed_max):
    """Scale trail length by speed -- faster = longer trail."""
    if not full_trail:
        return []
    speed_t = (speed - speed_min) / (speed_max - speed_min) if speed_max > speed_min else 1.0
    trail_len = max(1, round(len(full_trail) * speed_t))
    if trail_len >= len(full_trail):
        return list(full_trail)
    trail = []
    for i in range(trail_len):
        t = i / (trail_len - 1) * (len(full_trail) - 1) if trail_len > 1 else 0
        idx = min(int(t), len(full_trail) - 2)
        frac = t - idx
        c1, c2 = full_trail[idx], full_trail[idx + 1]
        trail.append((
            int(c1[0] + (c2[0] - c1[0]) * frac),
            int(c1[1] + (c2[1] - c1[1]) * frac),
            int(c1[2] + (c2[2] - c1[2]) * frac),
        ))
    return trail


def spawn_arc(cfg, rows, cols):
    """Create a new arc with random direction and speed."""
    speed_min = cfg.get("SPEED_MIN", 0.4)
    speed_max = cfg.get("SPEED_MAX", 4.0)
    speed = speed_min + (speed_max - speed_min) * random.random() ** 2

    angle = random.uniform(0, 360)
    angle_rad = math.radians(angle)
    nx = math.cos(angle_rad)
    ny = math.sin(angle_rad)

    trail = build_trail(cfg.get("TRAIL", []), speed, speed_min, speed_max)

    projections = [nx * c + ny * r
                   for c in (0, cols - 1)
                   for r in (0, rows - 1)]

    return {
        "nx": nx,
        "ny": ny,
        "speed": speed,
        "pos": min(projections) - 2,
        "p_max": max(projections) + 2 + len(trail),
        "trail": trail,
        "center_color": cfg.get("CENTER_COLOR", (0, 255, 0)),
        "edge_color": cfg.get("EDGE_COLOR", (136, 0, 102)),
        "row_offsets": cfg.get("ROW_OFFSETS", [0.5, 0, 0, 0, 0, 0]),
    }


def run(device, stop_event):
    """Run the arc sweep effect. Returns when stop_event is set."""
    rows = device.fx.advanced.rows
    cols = device.fx.advanced.cols
    matrix = device.fx.advanced.matrix
    BLACK = (0, 0, 0)

    arcs = []
    next_spawn = time.monotonic()

    next_frame = time.monotonic()

    while not stop_event.is_set():
        cfg = load_config(CONFIG_PATH)
        fps = cfg.get("FPS", 20)
        interval = 1.0 / fps
        now = time.monotonic()

        if now >= next_spawn:
            arcs.append(spawn_arc(cfg, rows, cols))
            pause = random.uniform(cfg.get("PAUSE_MIN", 0.5), cfg.get("PAUSE_MAX", 4.0))
            next_spawn = now + pause

        frame = [[BLACK] * cols for _ in range(rows)]

        for arc in arcs:
            nx, ny = arc["nx"], arc["ny"]
            pos = arc["pos"]
            trail = arc["trail"]
            center_color = arc["center_color"]
            edge_color = arc["edge_color"]
            offsets = arc["row_offsets"]

            for r in range(rows):
                offset = offsets[r] if r < len(offsets) else 0.0
                for c in range(cols):
                    d = round(pos - (nx * c + ny * r + offset))
                    if abs(d) == 0:
                        color = center_color
                    elif abs(d) == 1:
                        color = edge_color
                    elif d >= 2 and (d - 2) < len(trail):
                        color = trail[d - 2]
                    else:
                        continue
                    existing = frame[r][c]
                    frame[r][c] = (
                        max(existing[0], color[0]),
                        max(existing[1], color[1]),
                        max(existing[2], color[2]),
                    )

        for r in range(rows):
            for c in range(cols):
                matrix[r, c] = frame[r][c]
        device.fx.advanced.draw()

        next_frame, dt = frame_sleep(next_frame, interval)
        for arc in arcs:
            arc["pos"] += arc["speed"] * dt * fps
        arcs = [a for a in arcs if a["pos"] < a["p_max"]]

    clear_keyboard(device)


def main():
    """Standalone entry point."""
    standalone_main(EFFECT_NAME, run)


if __name__ == "__main__":
    main()
