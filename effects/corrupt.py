#!/usr/bin/env python3
"""Corrupt - small corruption zones erupt across a calm keyboard.

Instead of full-keyboard glitch bursts, small rectangular patches of digital
corruption spawn at random positions and live for a few frames before dying.
Multiple patches can overlap. The rest of the keyboard stays calm with subtle
shimmer, creating a "bad memory sectors" / failing display look.

Edit corrupt_config.py while running to tweak on the fly.
"""

import os
import random
import time

from effects.common import load_config, clear_keyboard, frame_sleep, standalone_main

EFFECT_NAME = "Corrupt"
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "corrupt_config.py")
BLACK = (0, 0, 0)


def spawn_patch(rows, cols, cfg):
    """Create a new corruption patch at a random location."""
    # Random patch size
    pw_min = cfg.get("PATCH_WIDTH_MIN", 3)
    pw_max = cfg.get("PATCH_WIDTH_MAX", 7)
    ph_min = cfg.get("PATCH_HEIGHT_MIN", 2)
    ph_max = cfg.get("PATCH_HEIGHT_MAX", 4)
    w = random.randint(pw_min, min(pw_max, cols))
    h = random.randint(ph_min, min(ph_max, rows))

    # Random position (clamp to fit)
    x = random.randint(0, max(0, cols - w))
    y = random.randint(0, max(0, rows - h))

    # Lifetime in frames
    life_min = cfg.get("PATCH_LIFE_MIN", 4)
    life_max = cfg.get("PATCH_LIFE_MAX", 15)
    life = random.randint(life_min, life_max)

    return {
        "x": x, "y": y, "w": w, "h": h,
        "life": life, "age": 0,
        "style": random.choice(["noise", "noise", "shift", "scanline", "block"]),
    }


def render_patch(frame, patch, cfg):
    """Render corruption within a single patch's bounds."""
    colors = cfg.get("GLITCH_COLORS", [
        (255, 0, 100), (0, 255, 220), (255, 255, 255),
        (180, 0, 255), (0, 255, 60), (255, 100, 0),
    ])
    x, y, w, h = patch["x"], patch["y"], patch["w"], patch["h"]
    style = patch["style"]
    age_frac = patch["age"] / max(patch["life"] - 1, 1)

    # Intensity fades in then out over the patch lifetime
    if age_frac < 0.2:
        intensity_scale = age_frac / 0.2
    elif age_frac > 0.7:
        intensity_scale = (1.0 - age_frac) / 0.3
    else:
        intensity_scale = 1.0

    if style == "noise":
        # Random colored pixels within the patch
        density = random.uniform(0.3, 0.9) * intensity_scale
        for r in range(y, y + h):
            for c in range(x, x + w):
                if random.random() < density:
                    color = random.choice(colors)
                    intensity = random.uniform(0.3, 1.0) * intensity_scale
                    frame[r][c] = (
                        min(255, int(color[0] * intensity)),
                        min(255, int(color[1] * intensity)),
                        min(255, int(color[2] * intensity)),
                    )
                    # Occasional dead pixel
                    if random.random() < 0.08:
                        frame[r][c] = BLACK

    elif style == "shift":
        # Row-shift corruption within the patch
        for r in range(y, y + h):
            if random.random() < 0.6:
                shift = random.randint(-3, 3)
                if shift == 0:
                    continue
                old_row = [frame[r][c] for c in range(x, x + w)]
                for i, c in enumerate(range(x, x + w)):
                    src = i - shift
                    if 0 <= src < w:
                        frame[r][c] = old_row[src]
                    else:
                        color = random.choice(colors)
                        intensity = random.uniform(0.5, 1.0) * intensity_scale
                        frame[r][c] = (
                            min(255, int(color[0] * intensity)),
                            min(255, int(color[1] * intensity)),
                            min(255, int(color[2] * intensity)),
                        )

    elif style == "scanline":
        # Bright scanline(s) within the patch
        num_lines = random.randint(1, max(1, h // 2))
        for _ in range(num_lines):
            r = random.randint(y, y + h - 1)
            color = random.choice(colors)
            for c in range(x, x + w):
                intensity = random.uniform(0.5, 1.0) * intensity_scale
                frame[r][c] = (
                    min(255, int(color[0] * intensity)),
                    min(255, int(color[1] * intensity)),
                    min(255, int(color[2] * intensity)),
                )
        # Also scatter some noise nearby
        for r in range(y, y + h):
            for c in range(x, x + w):
                if random.random() < 0.15 * intensity_scale:
                    frame[r][c] = random.choice(colors)

    elif style == "block":
        # Solid block of a single glitch color (like a stuck memory region)
        color = random.choice(colors)
        intensity = random.uniform(0.4, 1.0) * intensity_scale
        block_color = (
            min(255, int(color[0] * intensity)),
            min(255, int(color[1] * intensity)),
            min(255, int(color[2] * intensity)),
        )
        for r in range(y, y + h):
            for c in range(x, x + w):
                # Some pixels flicker within the block
                if random.random() < 0.85:
                    frame[r][c] = block_color
                else:
                    frame[r][c] = random.choice([BLACK, random.choice(colors)])


def run(device, stop_event):
    """Run the localized glitch effect."""
    rows = device.fx.advanced.rows
    cols = device.fx.advanced.cols
    matrix = device.fx.advanced.matrix

    patches = []
    next_frame = time.monotonic()

    while not stop_event.is_set():
        cfg = load_config(CONFIG_PATH)
        fps = cfg.get("FPS", 15)
        interval = 1.0 / fps
        idle_color = cfg.get("IDLE_COLOR", (0, 25, 30))
        max_patches = cfg.get("MAX_PATCHES", 3)
        spawn_chance = cfg.get("SPAWN_CHANCE", 0.12)

        # Maybe spawn a new patch
        if len(patches) < max_patches and random.random() < spawn_chance:
            patches.append(spawn_patch(rows, cols, cfg))

        # Build frame from idle baseline with shimmer
        frame = []
        for r in range(rows):
            row = []
            for c in range(cols):
                if random.random() < 0.02:
                    f = random.uniform(0.5, 1.6)
                    row.append((
                        min(255, int(idle_color[0] * f)),
                        min(255, int(idle_color[1] * f)),
                        min(255, int(idle_color[2] * f)),
                    ))
                else:
                    row.append(idle_color)
            frame.append(row)

        # Render all active patches
        for patch in patches:
            render_patch(frame, patch, cfg)
            patch["age"] += 1

        # Remove expired patches
        patches = [p for p in patches if p["age"] < p["life"]]

        # Write frame to device
        for r in range(rows):
            for c in range(cols):
                matrix[r, c] = frame[r][c]
        device.fx.advanced.draw()

        next_frame, _dt = frame_sleep(next_frame, interval)

    clear_keyboard(device)


def main():
    """Standalone entry point."""
    standalone_main(EFFECT_NAME, run)


if __name__ == "__main__":
    main()
