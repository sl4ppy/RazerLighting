#!/usr/bin/env python3
"""Lightning Strike - random lightning bolts with restrikes and surges.

Procedurally generated bolts strike from top to bottom with branching,
restrike effects, and teal surge flickers.

Edit lightning_strike_config.py while running to tweak on the fly.
"""

import os
import random
import time

from effects.common import load_config, clear_keyboard, wait_interruptible, standalone_main

EFFECT_NAME = "Lightning Strike"
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lightning_strike_config.py")
BLACK = (0, 0, 0)


def generate_bolt(cols, rows, wander):
    """Generate a zigzag bolt path. Returns a list of column indices, one per row."""
    path = [random.randint(2, cols - 3)]
    for _ in range(1, rows):
        offset = random.choice(wander)
        path.append(max(0, min(cols - 1, path[-1] + offset)))
    return path


def generate_branches(path, cols, cfg):
    """Generate branch pixels off the main bolt. Returns list of (row, col)."""
    branches = []
    chance = cfg.get("BRANCH_CHANCE", 0.3)
    max_len = cfg.get("BRANCH_MAX_LENGTH", 3)
    for row, col in enumerate(path):
        if random.random() < chance:
            direction = random.choice([-1, 1])
            length = random.randint(1, max_len)
            for i in range(1, length + 1):
                bc = col + direction * i
                if 0 <= bc < cols:
                    branches.append((row, bc))
    return branches


def render_pixels(matrix, rows, cols, pixels):
    """Set the matrix from a dict of (row, col) -> color. Unset pixels go black."""
    for r in range(rows):
        for c in range(cols):
            matrix[r, c] = pixels.get((r, c), BLACK)


def animate_flash(matrix, device, rows, cols, path, branches, cfg, interval, stop_event):
    """Animate the 4-frame flash pattern for one bolt."""
    bolt_color = cfg.get("BOLT_COLOR", (255, 255, 255))
    glow = cfg.get("GLOW_COLOR", (10, 26, 42))
    glow_dim = cfg.get("GLOW_DIM_COLOR", (6, 14, 24))
    branch_color = cfg.get("BRANCH_COLOR", (170, 102, 221))
    branch_dim = cfg.get("BRANCH_DIM_COLOR", (204, 238, 255))

    # Frame 1: pre-flash — bolt path in dark navy
    pixels = {}
    for r, c in enumerate(path):
        pixels[(r, c)] = glow
    render_pixels(matrix, rows, cols, pixels)
    device.fx.advanced.draw()
    time.sleep(interval)
    if stop_event.is_set():
        return

    # Frame 2: full flash — white bolt, glow neighbors, branches, ambient flash
    ambient = cfg.get("AMBIENT_FLASH_COLOR", (4, 8, 20))
    pixels = {}
    # Ambient glow across entire keyboard for dramatic flash
    for r in range(rows):
        for c in range(cols):
            pixels[(r, c)] = ambient
    # Glow around bolt path (2-pixel radius)
    for r, c in enumerate(path):
        for dc in range(-2, 3):
            nc = c + dc
            if 0 <= nc < cols:
                if abs(dc) == 2:
                    pixels[(r, nc)] = tuple(max(pixels.get((r, nc), (0,0,0))[i], glow[i] // 2) for i in range(3))
                else:
                    pixels[(r, nc)] = glow
    for r, c in branches:
        pixels[(r, c)] = branch_color
    for r, c in enumerate(path):
        pixels[(r, c)] = bolt_color
    render_pixels(matrix, rows, cols, pixels)
    device.fx.advanced.draw()
    time.sleep(interval)
    if stop_event.is_set():
        return

    # Frame 3: sustain — dimmer glow, ice blue branches, white bolt remains
    pixels = {}
    for r, c in enumerate(path):
        for dc in [-1, 0, 1]:
            nc = c + dc
            if 0 <= nc < cols:
                pixels[(r, nc)] = glow_dim
    for r, c in branches:
        pixels[(r, c)] = branch_dim
    for r, c in enumerate(path):
        pixels[(r, c)] = bolt_color
    render_pixels(matrix, rows, cols, pixels)
    device.fx.advanced.draw()
    time.sleep(interval)
    if stop_event.is_set():
        return

    # Frame 4: afterglow — only bolt path in dark navy
    pixels = {}
    for r, c in enumerate(path):
        pixels[(r, c)] = glow
    render_pixels(matrix, rows, cols, pixels)
    device.fx.advanced.draw()
    time.sleep(interval)


def animate_surge(matrix, device, rows, cols, path, cfg, interval, stop_event):
    """Animate the post-restrike surge flicker."""
    surge_color = cfg.get("SURGE_COLOR", (68, 136, 170))
    branch_dim = cfg.get("BRANCH_DIM_COLOR", (204, 238, 255))
    glow = cfg.get("GLOW_COLOR", (10, 26, 42))

    # Teal surge
    pixels = {(r, c): surge_color for r, c in enumerate(path)}
    render_pixels(matrix, rows, cols, pixels)
    device.fx.advanced.draw()
    time.sleep(interval)
    if stop_event.is_set():
        return

    # Dark frame
    render_pixels(matrix, rows, cols, {})
    device.fx.advanced.draw()
    time.sleep(interval)
    if stop_event.is_set():
        return

    # Ice blue flicker
    pixels = {(r, c): branch_dim for r, c in enumerate(path)}
    render_pixels(matrix, rows, cols, pixels)
    device.fx.advanced.draw()
    time.sleep(interval)
    if stop_event.is_set():
        return

    # Final afterglow
    pixels = {(r, c): glow for r, c in enumerate(path)}
    render_pixels(matrix, rows, cols, pixels)
    device.fx.advanced.draw()
    time.sleep(interval)


def run(device, stop_event):
    """Run the lightning strike effect. Returns when stop_event is set."""
    rows = device.fx.advanced.rows
    cols = device.fx.advanced.cols
    matrix = device.fx.advanced.matrix

    while not stop_event.is_set():
        cfg = load_config(CONFIG_PATH)
        interval = 1.0 / cfg.get("FPS", 15)
        wander = cfg.get("BOLT_WANDER", [-2, -1, -1, 0, 1, 1, 2])

        # Wait before next strike
        wait = random.uniform(cfg.get("INTERVAL_MIN", 1.5), cfg.get("INTERVAL_MAX", 10.0))
        if not wait_interruptible(wait, stop_event):
            break

        # Decide how many bolts in this storm
        num_bolts = 1
        if random.random() < cfg.get("MULTI_BOLT_CHANCE", 0.35):
            num_bolts = random.randint(2, 3)

        for bolt_num in range(num_bolts):
            if stop_event.is_set():
                break

            # Gap between bolts in a multi-bolt storm
            if bolt_num > 0:
                gap = random.uniform(
                    cfg.get("MULTI_BOLT_GAP_MIN", 0.3),
                    cfg.get("MULTI_BOLT_GAP_MAX", 1.2),
                )
                if not wait_interruptible(gap, stop_event):
                    break

            path = generate_bolt(cols, rows, wander)
            branches = generate_branches(path, cols, cfg)

            # Initial flash
            animate_flash(matrix, device, rows, cols, path, branches, cfg, interval, stop_event)
            if stop_event.is_set():
                break

            # Optional restrike
            if random.random() < cfg.get("RESTRIKE_CHANCE", 0.6):
                # Dark gap before restrike
                render_pixels(matrix, rows, cols, {})
                device.fx.advanced.draw()
                dark_frames = random.randint(
                    cfg.get("RESTRIKE_GAP_MIN", 2),
                    cfg.get("RESTRIKE_GAP_MAX", 5),
                )
                if not wait_interruptible(dark_frames * interval, stop_event):
                    break

                # Restrike flash
                animate_flash(matrix, device, rows, cols, path, branches, cfg, interval, stop_event)
                if stop_event.is_set():
                    break

                # Optional surge
                if random.random() < cfg.get("SURGE_CHANCE", 0.5):
                    animate_surge(matrix, device, rows, cols, path, cfg, interval, stop_event)

        # Clear after storm
        render_pixels(matrix, rows, cols, {})
        device.fx.advanced.draw()

    # Clean up
    clear_keyboard(device)


def main():
    """Standalone entry point."""
    standalone_main(EFFECT_NAME, run)


if __name__ == "__main__":
    main()
