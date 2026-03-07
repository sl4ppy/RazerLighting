#!/usr/bin/env python3
"""Lightning Strike - random lightning bolts with restrikes and surges.

Procedurally generated bolts strike from top to bottom with branching,
restrike effects, and teal surge flickers.

Edit lightning_strike_config.py while running to tweak on the fly.
"""

import os
import random
import signal
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

EFFECT_NAME = "Lightning Strike"
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lightning_strike_config.py")
BLACK = (0, 0, 0)


def load_config():
    cfg = {}
    try:
        with open(CONFIG_PATH) as f:
            exec(f.read(), cfg)
    except Exception as e:
        print(f"Config load error: {e}", file=sys.stderr)
    return cfg


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


def draw_frame(matrix, rows, cols, pixels):
    """Set the matrix from a dict of (row, col) -> color. Unset pixels go black."""
    for r in range(rows):
        for c in range(cols):
            matrix[r, c] = pixels.get((r, c), BLACK)


def wait_interruptible(seconds, stop_event):
    """Sleep for a duration, returning early if stop_event is set."""
    end = time.monotonic() + seconds
    while time.monotonic() < end and not stop_event.is_set():
        time.sleep(min(0.05, end - time.monotonic()))
    return not stop_event.is_set()


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
    draw_frame(matrix, rows, cols, pixels)
    device.fx.advanced.draw()
    time.sleep(interval)
    if stop_event.is_set():
        return

    # Frame 2: full flash — white bolt, navy glow neighbors, purple branches
    pixels = {}
    for r, c in enumerate(path):
        for dc in [-1, 0, 1]:
            nc = c + dc
            if 0 <= nc < cols:
                pixels[(r, nc)] = glow
        for r, c in branches:
            pixels[(r, c)] = branch_color
    for r, c in enumerate(path):
        pixels[(r, c)] = bolt_color
    draw_frame(matrix, rows, cols, pixels)
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
    draw_frame(matrix, rows, cols, pixels)
    device.fx.advanced.draw()
    time.sleep(interval)
    if stop_event.is_set():
        return

    # Frame 4: afterglow — only bolt path in dark navy
    pixels = {}
    for r, c in enumerate(path):
        pixels[(r, c)] = glow
    draw_frame(matrix, rows, cols, pixels)
    device.fx.advanced.draw()
    time.sleep(interval)


def animate_surge(matrix, device, rows, cols, path, cfg, interval, stop_event):
    """Animate the post-restrike surge flicker."""
    surge_color = cfg.get("SURGE_COLOR", (68, 136, 170))
    branch_dim = cfg.get("BRANCH_DIM_COLOR", (204, 238, 255))
    glow = cfg.get("GLOW_COLOR", (10, 26, 42))

    # Teal surge
    pixels = {(r, c): surge_color for r, c in enumerate(path)}
    draw_frame(matrix, rows, cols, pixels)
    device.fx.advanced.draw()
    time.sleep(interval)
    if stop_event.is_set():
        return

    # Dark frame
    draw_frame(matrix, rows, cols, {})
    device.fx.advanced.draw()
    time.sleep(interval)
    if stop_event.is_set():
        return

    # Ice blue flicker
    pixels = {(r, c): branch_dim for r, c in enumerate(path)}
    draw_frame(matrix, rows, cols, pixels)
    device.fx.advanced.draw()
    time.sleep(interval)
    if stop_event.is_set():
        return

    # Final afterglow
    pixels = {(r, c): glow for r, c in enumerate(path)}
    draw_frame(matrix, rows, cols, pixels)
    device.fx.advanced.draw()
    time.sleep(interval)


def run(device, stop_event):
    """Run the lightning strike effect. Returns when stop_event is set."""
    rows = device.fx.advanced.rows
    cols = device.fx.advanced.cols
    matrix = device.fx.advanced.matrix

    while not stop_event.is_set():
        cfg = load_config()
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
                draw_frame(matrix, rows, cols, {})
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
        draw_frame(matrix, rows, cols, {})
        device.fx.advanced.draw()

    # Clean up
    draw_frame(matrix, rows, cols, {})
    device.fx.advanced.draw()


def main():
    """Standalone entry point."""
    from device import get_device

    device = get_device()
    stop_event = threading.Event()

    print(f"{device.name} ({device.fx.advanced.cols}x{device.fx.advanced.rows}) - lightning strike")
    print("Ctrl+C to stop")

    signal.signal(signal.SIGINT, lambda *_: stop_event.set())
    signal.signal(signal.SIGTERM, lambda *_: stop_event.set())

    run(device, stop_event)


if __name__ == "__main__":
    main()
