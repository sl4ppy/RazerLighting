#!/usr/bin/env python3
"""Binary Cascade - Matrix-style falling streams of light.

Streams of green light fall down columns at varying speeds with bright
white heads and fading green trails. Random cyan glints sparkle through
the streams. The effect is procedural — no two moments are alike.

Edit binary_cascade_config.py while running to tweak on the fly.
"""

import os
import random
import time

from effects.common import load_config, clear_keyboard, frame_sleep, standalone_main

EFFECT_NAME = "Binary Cascade"
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "binary_cascade_config.py")
BLACK = (0, 0, 0)


def spawn_stream(cfg, cols):
    """Create a new falling stream on a random column."""
    speed = random.uniform(cfg.get("SPEED_MIN", 0.3), cfg.get("SPEED_MAX", 1.2))
    trail_len = random.randint(cfg.get("TRAIL_LENGTH_MIN", 3), cfg.get("TRAIL_LENGTH_MAX", 8))
    return {
        "col": random.randint(0, cols - 1),
        "pos": -1.0,
        "speed": speed,
        "trail_len": trail_len,
    }


def run(device, stop_event):
    """Run the binary cascade effect."""
    rows = device.fx.advanced.rows
    cols = device.fx.advanced.cols
    matrix = device.fx.advanced.matrix

    streams = []
    next_frame = time.monotonic()

    while not stop_event.is_set():
        cfg = load_config(CONFIG_PATH)
        fps = cfg.get("FPS", 18)
        interval = 1.0 / fps
        bg = cfg.get("BG_COLOR", (0, 20, 8))
        head_color = cfg.get("HEAD_COLOR", (255, 255, 255))
        bright = cfg.get("BRIGHT_COLOR", (0, 255, 0))
        mid = cfg.get("MID_COLOR", (0, 136, 68))
        dim = cfg.get("DIM_COLOR", (0, 85, 51))
        glint_color = cfg.get("GLINT_COLOR", (0, 255, 204))
        glint_chance = cfg.get("GLINT_CHANCE", 0.03)
        max_streams = cfg.get("MAX_STREAMS", 20)
        spawn_chance = cfg.get("STREAM_SPAWN_CHANCE", 0.15)

        # Build trail gradient
        trail_colors = [bright, mid, dim]

        # Spawn new streams
        if len(streams) < max_streams:
            for c in range(cols):
                if random.random() < spawn_chance and len(streams) < max_streams:
                    streams.append(spawn_stream(cfg, cols))
                    streams[-1]["col"] = c

        # Render frame
        frame = [[bg] * cols for _ in range(rows)]

        for stream in streams:
            col = stream["col"]
            head_row = stream["pos"]
            trail_len = stream["trail_len"]

            for i in range(trail_len + 1):
                r = int(head_row) - i
                if r < 0 or r >= rows:
                    continue

                if i == 0:
                    color = head_color
                else:
                    t = i / trail_len
                    if t < 0.3:
                        # Interpolate bright -> mid
                        f = t / 0.3
                        color = (
                            int(bright[0] + (mid[0] - bright[0]) * f),
                            int(bright[1] + (mid[1] - bright[1]) * f),
                            int(bright[2] + (mid[2] - bright[2]) * f),
                        )
                    else:
                        # Interpolate mid -> dim
                        f = (t - 0.3) / 0.7
                        color = (
                            int(mid[0] + (dim[0] - mid[0]) * f),
                            int(mid[1] + (dim[1] - mid[1]) * f),
                            int(mid[2] + (dim[2] - mid[2]) * f),
                        )

                # Additive blend
                existing = frame[r][col]
                frame[r][col] = (
                    min(255, max(existing[0], color[0])),
                    min(255, max(existing[1], color[1])),
                    min(255, max(existing[2], color[2])),
                )

                # Random cyan glint
                if i > 0 and random.random() < glint_chance:
                    frame[r][col] = glint_color

        # Flush to device
        for r in range(rows):
            for c in range(cols):
                matrix[r, c] = frame[r][c]
        device.fx.advanced.draw()

        next_frame, dt = frame_sleep(next_frame, interval)

        # Advance streams
        for stream in streams:
            stream["pos"] += stream["speed"] * dt * fps

        # Remove streams that have fully exited
        streams = [s for s in streams if int(s["pos"]) - s["trail_len"] < rows]

    # Clean up
    clear_keyboard(device)


def main():
    """Standalone entry point."""
    standalone_main(EFFECT_NAME, run)


if __name__ == "__main__":
    main()
