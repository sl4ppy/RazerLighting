#!/usr/bin/env python3
"""Tidal Swell - ocean waves rolling across the keyboard.

Layered sine waves create a convincing ocean surface with crests,
troughs, foam sparkle, and deep water. Waves scroll right-to-left
with a slow vertical swell breathing effect.
"""

import math
import os
import time

import numpy as np

from effects.common import (
    load_config, draw_frame, clear_keyboard, frame_sleep,
    build_palette_lut, palette_lookup, make_coordinate_grids,
    standalone_main,
)

EFFECT_NAME = "Tidal Swell"
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tidal_swell_config.py")


def run(device, stop_event):
    """Run the tidal swell effect."""
    rows = device.fx.advanced.rows
    cols = device.fx.advanced.cols

    row_grid, col_grid = make_coordinate_grids(rows, cols)

    # Depth factor: top rows are "surface" (1.0), bottom rows are "deep" (0.0)
    depth = 1.0 - (row_grid / max(rows - 1, 1))

    t = 0.0
    next_frame = time.monotonic()

    while not stop_event.is_set():
        cfg = load_config(CONFIG_PATH)
        interval = 1.0 / cfg.get("FPS", 20)
        wave_speed = cfg.get("WAVE_SPEED", 0.08)
        wave_count = cfg.get("WAVE_COUNT", 2.5)
        swell_speed = cfg.get("SWELL_SPEED", 0.02)
        foam_chance = cfg.get("FOAM_CHANCE", 0.06)
        spray_color = cfg.get("SPRAY_COLOR", (255, 255, 255))
        secondary = cfg.get("SECONDARY_WAVE", True)
        secondary_scale = cfg.get("SECONDARY_SCALE", 0.4)

        # Build 5-stop ocean palette LUT from config colors
        # Stops at: 0.0=deep, 0.2=trough, 0.5=body, 0.8=crest, 1.0=foam
        deep = cfg.get("DEEP_COLOR", (0, 8, 17))
        trough = cfg.get("TROUGH_COLOR", (0, 30, 50))
        body = cfg.get("BODY_COLOR", (0, 100, 68))
        crest = cfg.get("CREST_COLOR", (0, 255, 136))
        foam_color = cfg.get("FOAM_COLOR", (170, 255, 204))

        # Build a 256-entry LUT matching the original non-uniform stop positions
        # Stops: 0.0->deep, 0.2->trough, 0.5->body, 0.8->crest, 1.0->foam
        lut = np.zeros((256, 3), dtype=np.uint8)
        stops = [0.0, 0.2, 0.5, 0.8, 1.0]
        colors = [np.array(deep), np.array(trough), np.array(body),
                  np.array(crest), np.array(foam_color)]
        for i in range(256):
            val = i / 255.0
            # Find which segment we're in
            for s in range(len(stops) - 1):
                if val <= stops[s + 1] or s == len(stops) - 2:
                    seg_t = (val - stops[s]) / (stops[s + 1] - stops[s])
                    seg_t = max(0.0, min(1.0, seg_t))
                    c = colors[s] + (colors[s + 1] - colors[s]) * seg_t
                    lut[i] = np.clip(c, 0, 255).astype(np.uint8)
                    break

        swell = math.sin(t * swell_speed) * 0.15

        # Primary wave
        wave = np.sin(col_grid * wave_count * math.pi / cols - t * wave_speed)

        # Secondary wave overlay
        if secondary:
            wave2 = np.sin(col_grid * wave_count * 1.7 * math.pi / cols
                           - t * wave_speed * 0.6 + 1.3)
            wave = wave * (1.0 - secondary_scale) + wave2 * secondary_scale

        # Add vertical swell
        wave = wave + swell

        # Map wave to 0..1 and modulate by depth
        value = (wave + 1.0) / 2.0
        value = value * (0.3 + 0.7 * depth)

        # Row-based depth darkening
        value = value * (0.4 + 0.6 * depth)

        # Clamp to 0..1
        value = np.clip(value, 0.0, 1.0)

        # Map through ocean palette LUT
        frame_rgb = palette_lookup(lut, value)

        # Foam sparkle at wave crests (top rows only)
        foam_mask = (value > 0.75) & (depth > 0.5) & (np.random.random((rows, cols)) < foam_chance)
        spray = np.array(spray_color, dtype=np.uint8)
        frame_rgb[foam_mask] = spray

        draw_frame(device, frame_rgb)
        t += 1.0
        next_frame = frame_sleep(next_frame, interval)

    clear_keyboard(device)


def main():
    """Standalone entry point."""
    standalone_main(EFFECT_NAME, run)


if __name__ == "__main__":
    main()
