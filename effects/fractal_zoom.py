#!/usr/bin/env python3
"""Fractal Zoom - animated Mandelbrot/Julia set zoom with color cycling.

Renders a fractal that continuously zooms in with slow rotation,
creating hypnotic patterns in a purple/magenta nebula palette.
Optional breathing pulse modulates overall brightness.

Edit fractal_zoom_config.py while running to tweak on the fly.
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

EFFECT_NAME = "Fractal Zoom"
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fractal_zoom_config.py")


def run(device, stop_event):
    """Run the fractal zoom effect."""
    rows = device.fx.advanced.rows
    cols = device.fx.advanced.cols

    # Coordinate grids for pixel mapping
    row_grid, col_grid = make_coordinate_grids(rows, cols)

    t = 0.0
    next_frame = time.monotonic()

    while not stop_event.is_set():
        cfg = load_config(CONFIG_PATH)
        interval = 1.0 / cfg.get("FPS", 15)
        zoom_speed = cfg.get("ZOOM_SPEED", 0.03)
        zoom_range = cfg.get("ZOOM_RANGE", 3.0)
        rotation_speed = cfg.get("ROTATION_SPEED", 0.01)
        max_iter = cfg.get("MAX_ITER", 20)
        center_re = cfg.get("CENTER_RE", -0.75)
        center_im = cfg.get("CENTER_IM", 0.0)
        julia_mode = cfg.get("JULIA_MODE", False)
        julia_c_re = cfg.get("JULIA_C_RE", -0.7)
        julia_c_im = cfg.get("JULIA_C_IM", 0.27015)
        palette = cfg.get("PALETTE", [(10, 0, 21), (140, 0, 200), (10, 0, 21)])
        inside_color = cfg.get("INSIDE_COLOR", (10, 0, 21))
        pulse = cfg.get("PULSE", True)
        pulse_speed = cfg.get("PULSE_SPEED", 0.05)
        pulse_amount = cfg.get("PULSE_AMOUNT", 0.25)

        lut = build_palette_lut(palette)

        # Zoom level oscillates for continuous zoom effect
        zoom_phase = (t * zoom_speed) % zoom_range
        zoom = 0.5 * math.exp(-zoom_phase)

        # Rotation
        rot = t * rotation_speed
        cos_r = math.cos(rot)
        sin_r = math.sin(rot)

        # Pulse brightness
        brightness = 1.0
        if pulse:
            brightness = 1.0 - pulse_amount * (0.5 + 0.5 * math.sin(t * pulse_speed))

        # Color cycling offset
        color_offset = t * 0.005

        # Map pixel coordinates to complex plane (vectorized)
        px = (col_grid - cols / 2.0) / cols * zoom * 4.0
        py = (row_grid - rows / 2.0) / rows * zoom * 4.0

        # Apply rotation
        rx = px * cos_r - py * sin_r
        ry = px * sin_r + py * cos_r

        # Set up z and c arrays depending on mode
        if julia_mode:
            zr = rx.copy()
            zi = ry.copy()
            cr = np.full_like(zr, julia_c_re)
            ci = np.full_like(zi, julia_c_im)
        else:
            zr = np.zeros_like(rx)
            zi = np.zeros_like(ry)
            cr = center_re + rx
            ci = center_im + ry

        # Iteration count and escape tracking
        iteration_count = np.zeros((rows, cols), dtype=np.float64)
        escaped = np.zeros((rows, cols), dtype=bool)

        # Final |z|^2 for smooth coloring
        final_mag_sq = np.zeros((rows, cols), dtype=np.float64)

        # Mandelbrot/Julia iteration (vectorized over all pixels)
        for i in range(max_iter):
            mag_sq = zr * zr + zi * zi
            # Find newly escaped pixels
            newly_escaped = (~escaped) & (mag_sq > 4.0)
            iteration_count[newly_escaped] = i
            final_mag_sq[newly_escaped] = mag_sq[newly_escaped]
            escaped |= newly_escaped

            # Continue iterating non-escaped pixels
            still_going = ~escaped
            if not np.any(still_going):
                break
            zr_new = zr * zr - zi * zi + cr
            zi_new = 2.0 * zr * zi + ci
            zr = np.where(still_going, zr_new, zr)
            zi = np.where(still_going, zi_new, zi)

        # Handle pixels that never escaped (still inside after all iterations)
        # Check final magnitudes for any remaining
        mag_sq = zr * zr + zi * zi
        last_escaped = (~escaped) & (mag_sq > 4.0)
        iteration_count[last_escaped] = max_iter
        final_mag_sq[last_escaped] = mag_sq[last_escaped]
        escaped |= last_escaped

        inside = ~escaped

        # Smooth coloring for escaped pixels
        # safe log: clamp final_mag_sq to >= 1 for log computation
        safe_mag_sq = np.maximum(final_mag_sq, 1.0)
        log_zn = np.log(safe_mag_sq) / 2.0  # log(|z|)
        smooth_val = iteration_count + 1.0 - np.log(np.maximum(log_zn, 1e-10)) / math.log(2)
        # For pixels where final_mag_sq <= 1, just use iteration count
        smooth_val = np.where(final_mag_sq > 1.0, smooth_val, iteration_count.astype(np.float64))

        t_color = np.mod(smooth_val / max_iter + color_offset, 1.0)

        # Palette lookup for escaped pixels
        frame_rgb = palette_lookup(lut, t_color)

        # Apply inside color
        if inside.any():
            frame_rgb[inside] = inside_color

        # Apply brightness
        if brightness < 1.0:
            frame_rgb = (frame_rgb.astype(np.float64) * brightness).astype(np.uint8)

        draw_frame(device, frame_rgb)
        t += 1.0
        next_frame = frame_sleep(next_frame, interval)

    clear_keyboard(device)


def main():
    """Standalone entry point."""
    standalone_main(EFFECT_NAME, run)


if __name__ == "__main__":
    main()
