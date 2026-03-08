#!/usr/bin/env python3
"""Glitch - digital corruption bursts over a quiet baseline.

Mostly quiet dim green, periodically interrupted by violent bursts of
randomly colored pixels, row-shift corruptions, and bright scanlines.
Mimics a malfunctioning digital display with unpredictable timing.

Edit glitch_config.py while running to tweak on the fly.
"""

import os
import random
import time

from effects.common import load_config, clear_keyboard, wait_interruptible, standalone_main

EFFECT_NAME = "Glitch"
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "glitch_config.py")
BLACK = (0, 0, 0)


def render_idle(matrix, rows, cols, idle_color):
    """Render the quiet idle state."""
    for r in range(rows):
        for c in range(cols):
            matrix[r, c] = idle_color


def render_glitch_frame(matrix, rows, cols, cfg):
    """Render a single glitch burst frame."""
    idle = cfg.get("IDLE_COLOR", (0, 51, 0))
    colors = cfg.get("GLITCH_COLORS", [(0, 255, 0), (204, 0, 68), (255, 255, 255)])
    density = random.uniform(
        cfg.get("BURST_DENSITY_MIN", 0.05),
        cfg.get("BURST_DENSITY_MAX", 0.6),
    )
    corruption_chance = cfg.get("CORRUPTION_CHANCE", 0.3)
    row_shift_max = cfg.get("ROW_SHIFT_MAX", 4)
    scanline_chance = cfg.get("SCANLINE_CHANCE", 0.2)

    # Start with idle
    frame = [[idle] * cols for _ in range(rows)]

    # Row-shift corruption: shift entire rows left/right
    if random.random() < corruption_chance:
        num_rows = random.randint(1, max(1, rows // 2))
        for _ in range(num_rows):
            r = random.randint(0, rows - 1)
            shift = random.randint(-row_shift_max, row_shift_max)
            if shift == 0:
                continue
            old_row = frame[r][:]
            for c in range(cols):
                src = c - shift
                if 0 <= src < cols:
                    frame[r][c] = old_row[src]
                else:
                    frame[r][c] = random.choice(colors)

    # Scanline: one or two rows go bright
    if random.random() < scanline_chance:
        num_scanlines = random.randint(1, 2)
        for _ in range(num_scanlines):
            r = random.randint(0, rows - 1)
            scanline_color = random.choice(colors)
            # Vary intensity across the scanline
            for c in range(cols):
                intensity = random.uniform(0.5, 1.0)
                frame[r][c] = (
                    min(255, int(scanline_color[0] * intensity)),
                    min(255, int(scanline_color[1] * intensity)),
                    min(255, int(scanline_color[2] * intensity)),
                )

    # Random pixel noise
    num_pixels = int(rows * cols * density)
    for _ in range(num_pixels):
        r = random.randint(0, rows - 1)
        c = random.randint(0, cols - 1)
        color = random.choice(colors)
        # Random intensity
        intensity = random.uniform(0.3, 1.0)
        frame[r][c] = (
            min(255, int(color[0] * intensity)),
            min(255, int(color[1] * intensity)),
            min(255, int(color[2] * intensity)),
        )

    # Occasional black-out pixels for "dead pixel" feel
    for _ in range(random.randint(0, 5)):
        r = random.randint(0, rows - 1)
        c = random.randint(0, cols - 1)
        frame[r][c] = BLACK

    # Write frame
    for r in range(rows):
        for c in range(cols):
            matrix[r, c] = frame[r][c]


def run(device, stop_event):
    """Run the glitch effect."""
    rows = device.fx.advanced.rows
    cols = device.fx.advanced.cols
    matrix = device.fx.advanced.matrix

    while not stop_event.is_set():
        cfg = load_config(CONFIG_PATH)
        interval = 1.0 / cfg.get("FPS", 15)
        idle_color = cfg.get("IDLE_COLOR", (0, 51, 0))

        # Idle phase
        render_idle(matrix, rows, cols, idle_color)
        device.fx.advanced.draw()

        wait_time = random.uniform(cfg.get("IDLE_MIN", 1.0), cfg.get("IDLE_MAX", 6.0))
        if not wait_interruptible(wait_time, stop_event):
            break

        # Glitch burst
        while True:
            num_frames = random.randint(
                cfg.get("BURST_FRAMES_MIN", 3),
                cfg.get("BURST_FRAMES_MAX", 12),
            )

            for _ in range(num_frames):
                if stop_event.is_set():
                    break
                render_glitch_frame(matrix, rows, cols, cfg)
                device.fx.advanced.draw()
                time.sleep(interval)

            if stop_event.is_set():
                break

            # Multi-burst?
            if random.random() < cfg.get("MULTI_BURST_CHANCE", 0.3):
                gap = random.uniform(
                    cfg.get("MULTI_BURST_GAP_MIN", 0.1),
                    cfg.get("MULTI_BURST_GAP_MAX", 0.4),
                )
                render_idle(matrix, rows, cols, idle_color)
                device.fx.advanced.draw()
                if not wait_interruptible(gap, stop_event):
                    break
            else:
                break

        # Return to idle
        render_idle(matrix, rows, cols, idle_color)
        device.fx.advanced.draw()

    # Clean up
    clear_keyboard(device)


def main():
    """Standalone entry point."""
    standalone_main(EFFECT_NAME, run)


if __name__ == "__main__":
    main()
