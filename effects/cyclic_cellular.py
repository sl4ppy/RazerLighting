#!/usr/bin/env python3
"""Cyclic Cellular Automaton - self-organising rainbow spirals.

A grid of cells cycles through NUM_STATES states. Each step, a cell
advances to the next state if enough Moore-neighbourhood neighbours
already hold that next state, producing emergent rotating spirals and
travelling waves across the keyboard.

Edit cyclic_cellular_config.py while running to tweak on the fly.
"""

import os
import time

import numpy as np

from effects.common import load_config, draw_frame, clear_keyboard, frame_sleep, standalone_main

EFFECT_NAME = "Cyclic Cellular Automaton"
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cyclic_cellular_config.py")


def hsv_to_rgb(h, s, v):
    """Convert HSV (h in 0..360, s and v in 0..1) to an (R, G, B) tuple."""
    h = h % 360
    c = v * s
    x = c * (1 - abs((h / 60) % 2 - 1))
    m = v - c
    if h < 60:
        r, g, b = c, x, 0
    elif h < 120:
        r, g, b = x, c, 0
    elif h < 180:
        r, g, b = 0, c, x
    elif h < 240:
        r, g, b = 0, x, c
    elif h < 300:
        r, g, b = x, 0, c
    else:
        r, g, b = c, 0, x
    return (int((r + m) * 255), int((g + m) * 255), int((b + m) * 255))


def interpolate_palette(base_colors, num_states):
    """Interpolate a base palette to produce exactly num_states colors."""
    if len(base_colors) == 0:
        return [(0, 0, 0)] * num_states
    if len(base_colors) == 1:
        return [base_colors[0]] * num_states
    result = []
    n = len(base_colors) - 1
    for s in range(num_states):
        t = s / max(num_states - 1, 1) * n
        idx = min(int(t), n - 1)
        frac = t - idx
        c1, c2 = base_colors[idx], base_colors[min(idx + 1, n)]
        result.append((
            int(c1[0] + (c2[0] - c1[0]) * frac),
            int(c1[1] + (c2[1] - c1[1]) * frac),
            int(c1[2] + (c2[2] - c1[2]) * frac),
        ))
    return result


def build_palette(num_states, custom_palette=None):
    """Generate a palette with one colour per state.

    If custom_palette is provided and non-empty, interpolate it to num_states.
    Otherwise fall back to HSV rainbow.
    """
    if custom_palette:
        return interpolate_palette(custom_palette, num_states)
    return [hsv_to_rgb(s / num_states * 360, 1.0, 1.0) for s in range(num_states)]


def seed_grid(rows, cols, num_states):
    """Create a randomly initialised grid."""
    return np.random.randint(0, num_states, (rows, cols))


def step_grid(grid, rows, cols, num_states, threshold):
    """Advance the automaton by one step. Returns (new_grid, changed_count)."""
    successor = (grid + 1) % num_states
    count = np.zeros_like(grid)
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            neighbor = np.roll(np.roll(grid, -dr, axis=0), -dc, axis=1)
            count += (neighbor == successor).astype(int)
    advance = count >= threshold
    new_grid = np.where(advance, successor, grid)
    changed = int(np.sum(advance))
    return new_grid, changed


def run(device, stop_event):
    """Run the cyclic cellular automaton effect."""
    rows = device.fx.advanced.rows
    cols = device.fx.advanced.cols

    cfg = load_config(CONFIG_PATH)
    num_states = cfg.get("NUM_STATES", 14)
    custom_palette = cfg.get("PALETTE", [])
    grid = seed_grid(rows, cols, num_states)
    palette = build_palette(num_states, custom_palette)
    palette_array = np.array(palette, dtype=np.uint8)
    stagnant_frames = 0

    next_frame = time.monotonic()

    while not stop_event.is_set():
        cfg = load_config(CONFIG_PATH)
        fps = cfg.get("FPS", 12)
        interval = 1.0 / fps
        num_states_cfg = cfg.get("NUM_STATES", 14)
        threshold = cfg.get("THRESHOLD", 1)
        sim_steps = cfg.get("SIM_STEPS_PER_FRAME", 1)
        stagnation_limit = cfg.get("STAGNATION_FRAMES", 60)

        new_custom_palette = cfg.get("PALETTE", [])
        # Rebuild palette / reseed if NUM_STATES or palette changed
        if num_states_cfg != num_states or new_custom_palette != custom_palette:
            num_states = num_states_cfg
            custom_palette = new_custom_palette
            palette = build_palette(num_states, custom_palette)
            palette_array = np.array(palette, dtype=np.uint8)
            grid = seed_grid(rows, cols, num_states)
            stagnant_frames = 0

        # Simulation steps
        total_changed = 0
        for _ in range(sim_steps):
            grid, changed = step_grid(grid, rows, cols, num_states, threshold)
            total_changed += changed

        # Stagnation detection
        if total_changed == 0:
            stagnant_frames += 1
        else:
            stagnant_frames = 0

        if stagnant_frames >= stagnation_limit:
            grid = seed_grid(rows, cols, num_states)
            stagnant_frames = 0

        # Render
        frame_rgb = palette_array[grid]
        draw_frame(device, frame_rgb)

        next_frame, _dt = frame_sleep(next_frame, interval)

    clear_keyboard(device)


def main():
    """Standalone entry point."""
    standalone_main(EFFECT_NAME, run)


if __name__ == "__main__":
    main()
