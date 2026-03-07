#!/usr/bin/env python3
"""Cyclic Cellular Automaton - self-organising rainbow spirals.

A grid of cells cycles through NUM_STATES states. Each step, a cell
advances to the next state if enough Moore-neighbourhood neighbours
already hold that next state, producing emergent rotating spirals and
travelling waves across the keyboard.

Edit cyclic_cellular_config.py while running to tweak on the fly.
"""

import math
import os
import random
import signal
import sys
import threading
import time

EFFECT_NAME = "Cyclic Cellular Automaton"
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cyclic_cellular_config.py")
BLACK = (0, 0, 0)


def load_config():
    cfg = {}
    try:
        with open(CONFIG_PATH) as f:
            exec(f.read(), cfg)
    except Exception as e:
        print(f"Config load error: {e}", file=sys.stderr)
    return cfg


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


def build_palette(num_states):
    """Generate a rainbow palette with one colour per state."""
    return [hsv_to_rgb(s / num_states * 360, 1.0, 1.0) for s in range(num_states)]


def seed_grid(rows, cols, num_states):
    """Create a randomly initialised grid."""
    return [[random.randint(0, num_states - 1) for _ in range(cols)] for _ in range(rows)]


def step_grid(grid, rows, cols, num_states, threshold):
    """Advance the automaton by one step. Returns (new_grid, changed_count)."""
    new_grid = [[0] * cols for _ in range(rows)]
    changed = 0
    for r in range(rows):
        for c in range(cols):
            current = grid[r][c]
            successor = (current + 1) % num_states
            count = 0
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    nr = (r + dr) % rows
                    nc = (c + dc) % cols
                    if grid[nr][nc] == successor:
                        count += 1
            if count >= threshold:
                new_grid[r][c] = successor
                changed += 1
            else:
                new_grid[r][c] = current
    return new_grid, changed


def run(device, stop_event):
    """Run the cyclic cellular automaton effect."""
    rows = device.fx.advanced.rows
    cols = device.fx.advanced.cols
    matrix = device.fx.advanced.matrix

    cfg = load_config()
    num_states = cfg.get("NUM_STATES", 14)
    grid = seed_grid(rows, cols, num_states)
    palette = build_palette(num_states)
    stagnant_frames = 0

    while not stop_event.is_set():
        cfg = load_config()
        interval = 1.0 / cfg.get("FPS", 12)
        num_states_cfg = cfg.get("NUM_STATES", 14)
        threshold = cfg.get("THRESHOLD", 1)
        sim_steps = cfg.get("SIM_STEPS_PER_FRAME", 1)
        stagnation_limit = cfg.get("STAGNATION_FRAMES", 60)

        # Rebuild palette / reseed if NUM_STATES changed
        if num_states_cfg != num_states:
            num_states = num_states_cfg
            palette = build_palette(num_states)
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
        for r in range(rows):
            for c in range(cols):
                matrix[r, c] = palette[grid[r][c]]

        device.fx.advanced.draw()
        time.sleep(interval)

    # Clean up
    for r in range(rows):
        for c in range(cols):
            matrix[r, c] = BLACK
    device.fx.advanced.draw()


def main():
    """Standalone entry point."""
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from device import get_device

    device = get_device()
    stop_event = threading.Event()

    print(f"{device.name} ({device.fx.advanced.cols}x{device.fx.advanced.rows}) - cyclic cellular automaton")
    print("Ctrl+C to stop")

    signal.signal(signal.SIGINT, lambda *_: stop_event.set())
    signal.signal(signal.SIGTERM, lambda *_: stop_event.set())

    run(device, stop_event)


if __name__ == "__main__":
    main()
