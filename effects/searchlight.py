#!/usr/bin/env python3
"""Searchlight - a bright beam sweeps around the keyboard.

A warm white/yellow beam rotates around the keyboard like a searchlight,
illuminating keys as it passes over them against a deep purple ambient
background. The beam has soft falloff edges and subtle brightness flicker.
"""

import math
import os
import random
import time

import numpy as np

from effects.common import (
    load_config, draw_frame, clear_keyboard, frame_sleep,
    make_coordinate_grids, standalone_main,
)

EFFECT_NAME = "Searchlight"
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "searchlight_config.py")


def run(device, stop_event):
    """Run the searchlight effect."""
    rows = device.fx.advanced.rows
    cols = device.fx.advanced.cols

    row_grid, col_grid = make_coordinate_grids(rows, cols)

    angle = 0.0
    next_frame = time.monotonic()

    while not stop_event.is_set():
        cfg = load_config(CONFIG_PATH)
        fps = cfg.get("FPS", 20)
        interval = 1.0 / fps
        sweep_speed = cfg.get("SWEEP_SPEED", 0.03)
        beam_width = cfg.get("BEAM_WIDTH", 0.4)
        beam_falloff = cfg.get("BEAM_FALLOFF", 2.0)
        origin_x = cfg.get("ORIGIN_X", 0.5)
        origin_y = cfg.get("ORIGIN_Y", 0.5)

        bg = np.array(cfg.get("BG_COLOR", (17, 0, 34)), dtype=np.float64)
        core = np.array(cfg.get("BEAM_CORE_COLOR", (255, 255, 204)), dtype=np.float64)
        mid_color = np.array(cfg.get("BEAM_MID_COLOR", (200, 220, 100)), dtype=np.float64)
        edge_color = np.array(cfg.get("BEAM_EDGE_COLOR", (61, 122, 30)), dtype=np.float64)
        ambient = np.array(cfg.get("AMBIENT_COLOR", (20, 8, 32)), dtype=np.float64)

        flicker = cfg.get("FLICKER", True)
        flicker_amount = cfg.get("FLICKER_AMOUNT", 0.08)

        # Flicker modulation
        brightness = 1.0
        if flicker:
            brightness = 1.0 - random.random() * flicker_amount

        # Origin in pixel space
        ox = origin_x * (cols - 1)
        oy = origin_y * (rows - 1)

        # Deltas from origin
        dx = col_grid - ox
        dy = (row_grid - oy) * 2.0  # stretch Y since rows are taller than cols

        # Angle from origin to each pixel
        pixel_angle = np.arctan2(dy, dx)

        # Angular distance from beam center, normalized to [-pi, pi]
        diff = pixel_angle - angle
        diff = (diff + math.pi) % (2 * math.pi) - math.pi
        abs_diff = np.abs(diff)

        # Distance from origin
        dist = np.sqrt(dx * dx + dy * dy)
        max_dist = math.sqrt(cols * cols + (rows * 2) ** 2)

        # Mask: inside beam vs outside beam
        inside_beam = abs_diff < beam_width

        # --- Inside beam calculations ---
        beam_t = np.where(inside_beam, abs_diff / beam_width, 0.0)
        beam_t_curved = beam_t ** beam_falloff

        dist_factor = np.minimum(1.0, 0.5 + 0.5 * (dist / max_dist))

        # Two-segment color interpolation: core->mid for t<0.3, mid->edge for t>=0.3
        inner_seg = beam_t_curved < 0.3
        seg_t_inner = np.where(inner_seg, beam_t_curved / 0.3, 0.0)
        seg_t_outer = np.where(~inner_seg, (beam_t_curved - 0.3) / 0.7, 0.0)

        # Compute beam color per pixel
        # For inner segment: lerp(core, mid, seg_t_inner)
        beam_color_inner = (
            core[np.newaxis, np.newaxis, :]
            + (mid_color - core)[np.newaxis, np.newaxis, :] * seg_t_inner[:, :, np.newaxis]
        )
        # For outer segment: lerp(mid, edge, seg_t_outer)
        beam_color_outer = (
            mid_color[np.newaxis, np.newaxis, :]
            + (edge_color - mid_color)[np.newaxis, np.newaxis, :] * seg_t_outer[:, :, np.newaxis]
        )

        beam_color = np.where(
            inner_seg[:, :, np.newaxis],
            beam_color_inner,
            beam_color_outer,
        )

        # Blend beam color with background: lerp(bg, beam_color, (1 - beam_t_curved) * dist_factor * brightness)
        beam_blend_factor = ((1.0 - beam_t_curved) * dist_factor * brightness)[:, :, np.newaxis]
        inside_color = (
            bg[np.newaxis, np.newaxis, :]
            + (beam_color - bg[np.newaxis, np.newaxis, :]) * beam_blend_factor
        )

        # --- Outside beam calculations ---
        amb_t = (0.3 * (dist / max_dist))[:, :, np.newaxis]
        outside_color = (
            bg[np.newaxis, np.newaxis, :]
            + (ambient - bg)[np.newaxis, np.newaxis, :] * amb_t
        )

        # Combine inside and outside
        frame_float = np.where(inside_beam[:, :, np.newaxis], inside_color, outside_color)
        frame_rgb = np.clip(frame_float, 0, 255).astype(np.uint8)

        draw_frame(device, frame_rgb)
        next_frame, dt = frame_sleep(next_frame, interval)
        angle += sweep_speed * dt * fps
        if angle > math.pi:
            angle -= 2 * math.pi

    clear_keyboard(device)


def main():
    """Standalone entry point."""
    standalone_main(EFFECT_NAME, run)


if __name__ == "__main__":
    main()
