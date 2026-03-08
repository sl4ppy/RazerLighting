#!/usr/bin/env python3
"""Heartbeat Pulse - radial cardiac rhythm waves across the keyboard.

Simulates a beating heart with lub-dub cardiac rhythm. Radial pulse rings
expand from a center point with physiologically-inspired timing. A faint
vein network pulses in the background as waves pass through. BPM slowly
oscillates for organic variation.

Edit heartbeat_config.py while running to tweak on the fly.
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

EFFECT_NAME = "Heartbeat Pulse"
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "heartbeat_config.py")


def run(device, stop_event):
    rows = device.fx.advanced.rows
    cols = device.fx.advanced.cols
    row_grid, col_grid = make_coordinate_grids(rows, cols)

    # Precompute vein network using value noise
    rng = np.random.RandomState(7)
    vein_base = np.zeros((rows, cols), dtype=np.float64)
    # Simple cellular-like vein pattern
    num_veins = 5
    vein_centers = [(rng.uniform(0, rows - 1), rng.uniform(0, cols - 1)) for _ in range(num_veins)]
    for r in range(rows):
        for c in range(cols):
            dists = sorted([math.sqrt((r - vr) ** 2 + ((c - vc) / 2.2) ** 2)
                           for vr, vc in vein_centers])
            # Veins are where two nearest seeds are equidistant (Voronoi edges)
            edge = 1.0 - min(1.0, (dists[1] - dists[0]) / 1.5)
            vein_base[r, c] = max(0.0, edge)

    # Track expanding pulse rings
    pulse_rings = []  # (birth_time_real, strength, expand_rate)

    t_real = 0.0
    t_frames = 0.0
    next_frame = time.monotonic()
    last_beat_phase = 0.0

    while not stop_event.is_set():
        cfg = load_config(CONFIG_PATH)
        fps = cfg.get("FPS", 30)
        interval = 1.0 / fps
        bpm = cfg.get("BPM", 72)
        bpm_min = cfg.get("BPM_MIN", 60)
        bpm_max = cfg.get("BPM_MAX", 90)
        bpm_cycle = cfg.get("BPM_CYCLE", 30.0)
        expand_speed = cfg.get("EXPAND_SPEED", 0.8)
        ring_width = cfg.get("RING_WIDTH", 0.5)
        lub_strength = cfg.get("LUB_STRENGTH", 1.0)
        dub_strength = cfg.get("DUB_STRENGTH", 0.7)
        center_row = cfg.get("CENTER_ROW", 2.5)
        center_col = cfg.get("CENTER_COL", 7.5)
        aspect = cfg.get("ASPECT_RATIO", 2.2)
        vein_bright = cfg.get("VEIN_BRIGHTNESS", 0.06)
        vein_pulse = cfg.get("VEIN_PULSE", 0.15)
        palette = cfg.get("PALETTE", [
            (2, 0, 4), (40, 0, 15), (120, 0, 20),
            (200, 10, 30), (255, 20, 60), (255, 80, 120),
        ])
        lut = build_palette_lut(palette)

        dt = interval
        t_real += dt

        # Oscillating BPM
        current_bpm = bpm + (bpm_max - bpm_min) * 0.5 * math.sin(t_real * 2.0 * math.pi / bpm_cycle)
        cycle_duration = 60.0 / current_bpm
        beat_phase = (t_real % cycle_duration) / cycle_duration

        # Detect phase wraps and pulse events
        # LUB at phase 0.0, DUB at phase 0.20
        if beat_phase < last_beat_phase:
            # New cycle — spawn LUB ring
            pulse_rings.append((t_real, lub_strength, expand_speed))
        if last_beat_phase < 0.20 <= beat_phase:
            # DUB
            pulse_rings.append((t_real, dub_strength, expand_speed * 0.85))
        last_beat_phase = beat_phase

        # Compute radial distance from center
        dr = row_grid - center_row
        dc = (col_grid - center_col) / math.sqrt(aspect)
        r_dist = np.sqrt(dr * dr + dc * dc)

        # Sum all active pulse rings
        pulse_field = np.zeros((rows, cols), dtype=np.float64)
        alive_rings = []
        rw_sq = ring_width * ring_width
        for birth_t, strength, exp_spd in pulse_rings:
            age = t_real - birth_t
            if age > 2.0:  # rings expire after 2 seconds
                continue
            alive_rings.append((birth_t, strength, exp_spd))
            expand_radius = age * exp_spd * 4.0
            ring_pos = r_dist - expand_radius
            # Sharp Gaussian ring with aggressive decay
            decay = math.exp(-age * 3.5)
            ring_val = np.exp(-ring_pos * ring_pos / rw_sq) * strength * decay
            pulse_field += ring_val
        pulse_rings = alive_rings

        # Ambient heartbeat glow at center (subtle throb)
        amp = 0.0
        if beat_phase < 0.10:
            amp = math.sin(beat_phase / 0.10 * math.pi) * lub_strength
        elif 0.20 <= beat_phase < 0.35:
            amp = math.sin((beat_phase - 0.20) / 0.15 * math.pi) * dub_strength

        center_glow = np.exp(-r_dist * r_dist / 4.0) * amp * 0.3
        pulse_field += center_glow

        # Vein network
        vein_field = vein_base * vein_bright
        # Veins pulse when a wave passes through
        vein_field += vein_base * pulse_field * vein_pulse

        # Combine
        total = np.clip(pulse_field + vein_field, 0.0, 1.0)

        frame_rgb = palette_lookup(lut, total)
        draw_frame(device, frame_rgb)
        t_frames += 1.0
        next_frame = frame_sleep(next_frame, interval)

    clear_keyboard(device)


def main():
    standalone_main(EFFECT_NAME, run)


if __name__ == "__main__":
    main()
