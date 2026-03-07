#!/usr/bin/env python3
"""Crystal Growth - Diffusion-Limited Aggregation on the keyboard.

A crystal seed starts at the center of the keyboard. Random walkers
drift in from the edges and stick when they touch the growing crystal,
building organic branching structures. Cells are colored by attachment
order through a blue-teal-green-amber-red palette, with a brief white
flash on each new attachment. The crystal resets when it fills more than
half the grid.

Edit crystal_growth_config.py while running to tweak on the fly.
"""

import os
import math
import random
import signal
import sys
import threading
import time

EFFECT_NAME = "Crystal Growth"
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "crystal_growth_config.py")
BLACK = (0, 0, 0)


def load_config():
    cfg = {}
    try:
        with open(CONFIG_PATH) as f:
            exec(f.read(), cfg)
    except Exception as e:
        print(f"Config load error: {e}", file=sys.stderr)
    return cfg


def spawn_walker_edge(rows, cols):
    """Spawn a walker at a random edge position."""
    edge = random.randint(0, 3)
    if edge == 0:      # top
        return [0, random.randint(0, cols - 1)]
    elif edge == 1:    # bottom
        return [rows - 1, random.randint(0, cols - 1)]
    elif edge == 2:    # left
        return [random.randint(0, rows - 1), 0]
    else:              # right
        return [random.randint(0, rows - 1), cols - 1]


def has_crystal_neighbor(r, c, crystal, rows, cols):
    """Check if (r, c) is adjacent to any crystal cell."""
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = r + dr, c + dc
        if 0 <= nr < rows and 0 <= nc < cols and crystal[nr][nc]:
            return True
    return False


def palette_color(order, total_attached, palette):
    """Map attachment order to a palette color via linear interpolation."""
    if total_attached <= 1:
        return palette[0]
    t = order / max(total_attached - 1, 1)
    t = max(0.0, min(1.0, t))
    # Scale t to palette segments
    seg = t * (len(palette) - 1)
    idx = int(seg)
    frac = seg - idx
    if idx >= len(palette) - 1:
        return palette[-1]
    c0 = palette[idx]
    c1 = palette[idx + 1]
    return (
        int(c0[0] + (c1[0] - c0[0]) * frac),
        int(c0[1] + (c1[1] - c0[1]) * frac),
        int(c0[2] + (c1[2] - c0[2]) * frac),
    )


def run(device, stop_event):
    """Run the crystal growth effect."""
    rows = device.fx.advanced.rows
    cols = device.fx.advanced.cols
    matrix = device.fx.advanced.matrix

    while not stop_event.is_set():
        # Initialize crystal state
        crystal = [[False] * cols for _ in range(rows)]
        attach_order = [[0] * cols for _ in range(rows)]
        flash_remaining = [[0] * cols for _ in range(rows)]
        total_attached = 0
        total_cells = rows * cols

        # Seed: center cell
        sr, sc = rows // 2, cols // 2
        crystal[sr][sc] = True
        attach_order[sr][sc] = 0
        flash_remaining[sr][sc] = 5
        total_attached = 1

        walkers = []

        while not stop_event.is_set():
            cfg = load_config()
            interval = 1.0 / cfg.get("FPS", 20)
            max_walkers = cfg.get("MAX_WALKERS", 80)
            steps_per_frame = cfg.get("STEPS_PER_FRAME", 30)
            fill_threshold = cfg.get("FILL_THRESHOLD", 0.55)
            flash_frames = cfg.get("FLASH_FRAMES", 5)
            palette = cfg.get("PALETTE", [
                (30, 60, 200),
                (0, 160, 160),
                (0, 180, 60),
                (200, 160, 0),
                (220, 40, 20),
            ])
            bg = cfg.get("BG_COLOR", (0, 0, 0))

            # Spawn walkers to maintain MAX_WALKERS
            while len(walkers) < max_walkers:
                walkers.append(spawn_walker_edge(rows, cols))

            # Perform random walk steps
            directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
            new_walkers = []
            for _ in range(steps_per_frame):
                still_walking = []
                for w in walkers:
                    dr, dc = random.choice(directions)
                    w[0] += dr
                    w[1] += dc

                    # Out of bounds — respawn at edge
                    if w[0] < 0 or w[0] >= rows or w[1] < 0 or w[1] >= cols:
                        w[:] = spawn_walker_edge(rows, cols)
                        still_walking.append(w)
                        continue

                    # Already on a crystal cell (shouldn't normally happen, re-spawn)
                    if crystal[w[0]][w[1]]:
                        w[:] = spawn_walker_edge(rows, cols)
                        still_walking.append(w)
                        continue

                    # Check adjacency — stick if neighbor is crystal
                    if has_crystal_neighbor(w[0], w[1], crystal, rows, cols):
                        crystal[w[0]][w[1]] = True
                        attach_order[w[0]][w[1]] = total_attached
                        flash_remaining[w[0]][w[1]] = flash_frames
                        total_attached += 1
                        # Don't add back to walkers — it stuck
                        new_walkers.append(spawn_walker_edge(rows, cols))
                    else:
                        still_walking.append(w)

                walkers = still_walking + new_walkers
                new_walkers = []

            # Check fill threshold
            if total_attached / total_cells > fill_threshold:
                # Flash the full crystal briefly, then reset
                break

            # Render frame
            for r in range(rows):
                for c in range(cols):
                    if crystal[r][c]:
                        if flash_remaining[r][c] > 0:
                            # White flash fading out
                            f = flash_remaining[r][c] / flash_frames
                            base = palette_color(attach_order[r][c], total_attached, palette)
                            color = (
                                int(base[0] + (255 - base[0]) * f),
                                int(base[1] + (255 - base[1]) * f),
                                int(base[2] + (255 - base[2]) * f),
                            )
                            flash_remaining[r][c] -= 1
                        else:
                            color = palette_color(attach_order[r][c], total_attached, palette)
                        matrix[r, c] = color
                    else:
                        matrix[r, c] = bg

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

    print(f"{device.name} ({device.fx.advanced.cols}x{device.fx.advanced.rows}) - crystal growth")
    print("Ctrl+C to stop")

    signal.signal(signal.SIGINT, lambda *_: stop_event.set())
    signal.signal(signal.SIGTERM, lambda *_: stop_event.set())

    run(device, stop_event)


if __name__ == "__main__":
    main()
