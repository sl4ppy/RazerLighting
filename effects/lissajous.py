#!/usr/bin/env python3
"""Lissajous - a glowing dot traces Lissajous curves across the keyboard.

A bright dot follows mathematical Lissajous curves (figure-8s and
other harmonic patterns), leaving a fading green trail. The curve
morphs over time as the phase relationship shifts, and frequencies
can periodically randomize for variety.

Edit lissajous_config.py while running to tweak on the fly.
"""

import math
import os
import random
import time

from effects.common import load_config, lerp_color, clear_keyboard, frame_sleep, standalone_main

EFFECT_NAME = "Lissajous"
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lissajous_config.py")


def run(device, stop_event):
    """Run the lissajous effect."""
    rows = device.fx.advanced.rows
    cols = device.fx.advanced.cols
    matrix = device.fx.advanced.matrix

    t = 0.0
    phase = 0.0
    freq_x = 3.0
    freq_y = 2.0
    last_morph = time.monotonic()

    # Possible freq pairs that make nice patterns
    freq_pairs = [
        (3, 2), (2, 3), (3, 4), (4, 3), (5, 4), (4, 5),
        (5, 6), (3, 5), (5, 3), (2, 5), (5, 2), (1, 2),
        (7, 4), (3, 7), (4, 7),
    ]

    next_frame = time.monotonic()

    while not stop_event.is_set():
        cfg = load_config(CONFIG_PATH)
        interval = 1.0 / cfg.get("FPS", 24)
        cfg_freq_x = cfg.get("FREQ_X", 3.0)
        cfg_freq_y = cfg.get("FREQ_Y", 2.0)
        phase_speed = cfg.get("PHASE_SPEED", 0.02)
        anim_speed = cfg.get("ANIM_SPEED", 0.08)
        trail_length = cfg.get("TRAIL_LENGTH", 12)
        trail_fade = cfg.get("TRAIL_FADE", True)
        bg = cfg.get("BG_COLOR", (0, 10, 5))
        head_color = cfg.get("HEAD_COLOR", (255, 255, 255))
        trail_color = cfg.get("TRAIL_COLOR", (0, 205, 65))
        dim_trail = cfg.get("DIM_TRAIL_COLOR", (0, 26, 13))
        glow_radius = cfg.get("GLOW_RADIUS", 1.5)
        glow_color = cfg.get("GLOW_COLOR", (0, 160, 50))
        morph = cfg.get("MORPH", True)
        morph_interval = cfg.get("MORPH_INTERVAL", 8.0)

        # Morph frequencies periodically
        if morph and time.monotonic() - last_morph > morph_interval:
            pair = random.choice(freq_pairs)
            freq_x, freq_y = float(pair[0]), float(pair[1])
            last_morph = time.monotonic()
        elif not morph:
            freq_x, freq_y = cfg_freq_x, cfg_freq_y

        # Compute trail positions
        trail_points = []
        for i in range(trail_length + 1):
            tt = t - i * anim_speed * 0.5
            x = math.sin(freq_x * tt + phase)
            y = math.sin(freq_y * tt)
            # Map from [-1,1] to pixel coordinates with margin
            px = (x + 1.0) / 2.0 * (cols - 1)
            py = (y + 1.0) / 2.0 * (rows - 1)
            trail_points.append((px, py))

        # Render frame
        frame = [[bg] * cols for _ in range(rows)]

        # Draw trail (farthest first so head overwrites)
        for i in range(len(trail_points) - 1, -1, -1):
            px, py = trail_points[i]
            fade = 1.0 - (i / max(1, len(trail_points) - 1)) if trail_fade else 1.0

            if i == 0:
                color = head_color
                radius = glow_radius
            else:
                color = lerp_color(dim_trail, trail_color, fade)
                radius = 0.5

            # Paint pixels within radius
            cr, cc = int(round(py)), int(round(px))
            r_range = max(0, int(cr - radius - 1)), min(rows, int(cr + radius + 2))
            c_range = max(0, int(cc - radius - 1)), min(cols, int(cc + radius + 2))

            for r in range(r_range[0], r_range[1]):
                for c in range(c_range[0], c_range[1]):
                    dist = math.sqrt((r - py) ** 2 + (c - px) ** 2)
                    if dist <= radius:
                        intensity = 1.0 - (dist / radius) if radius > 0 else 1.0
                        if i == 0:
                            # Head: blend from glow to head color
                            pixel_color = lerp_color(glow_color, head_color, intensity)
                        else:
                            pixel_color = (
                                int(color[0] * intensity),
                                int(color[1] * intensity),
                                int(color[2] * intensity),
                            )

                        # Max blend
                        existing = frame[r][c]
                        frame[r][c] = (
                            max(existing[0], pixel_color[0]),
                            max(existing[1], pixel_color[1]),
                            max(existing[2], pixel_color[2]),
                        )

        # Flush
        for r in range(rows):
            for c in range(cols):
                matrix[r, c] = frame[r][c]
        device.fx.advanced.draw()

        t += anim_speed
        phase += phase_speed

        next_frame = frame_sleep(next_frame, interval)

    clear_keyboard(device)


def main():
    """Standalone entry point."""
    standalone_main(EFFECT_NAME, run)


if __name__ == "__main__":
    main()
