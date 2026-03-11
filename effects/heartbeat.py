#!/usr/bin/env python3
"""Heartbeat Pulse - radial cardiac rhythm waves across the keyboard.

Simulates a beating heart with lub-dub cardiac rhythm.  The S1 (lub) fires
a broad, soft pressure wave; the S2 (dub) follows ~0.3 s later with a
tighter, sharper ring.  A systole flush warms the whole keyboard during
contraction, veins fill sequentially as the wavefront passes through,
and BPM drifts for organic variation.

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

_DEF_PALETTE = [
    (2, 0, 6),
    (15, 0, 10),
    (50, 0, 18),
    (120, 5, 25),
    (200, 15, 40),
    (255, 40, 70),
    (255, 90, 120),
    (255, 170, 180),
]


def run(device, stop_event):
    rows = device.fx.advanced.rows
    cols = device.fx.advanced.cols
    row_grid, col_grid = make_coordinate_grids(rows, cols)

    # Precompute vein network (Voronoi edge pattern)
    rng = np.random.RandomState(7)
    vein_base = np.zeros((rows, cols), dtype=np.float64)
    num_veins = 5
    vein_centers = [(rng.uniform(0, rows - 1), rng.uniform(0, cols - 1))
                    for _ in range(num_veins)]
    for r in range(rows):
        for c in range(cols):
            dists = sorted([math.sqrt((r - vr) ** 2 + ((c - vc) / 2.2) ** 2)
                           for vr, vc in vein_centers])
            edge = 1.0 - min(1.0, (dists[1] - dists[0]) / 1.5)
            vein_base[r, c] = max(0.0, edge)

    # Pulse rings: (birth_time, strength, expand_speed, half_width, decay_rate)
    pulse_rings = []

    t_real = 0.0
    next_frame = time.monotonic()
    # Phase accumulator: advances by dt/cycle_duration each frame.
    # Avoids the broken t_real%cycle_duration approach which drifts
    # when cycle_duration changes with oscillating BPM.
    beat_phase = 0.0
    dub_pending = False
    dt = 0.0

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
        dub_phase = cfg.get("DUB_PHASE", 0.36)
        center_row = cfg.get("CENTER_ROW", 2.5)
        center_col = cfg.get("CENTER_COL", 7.5)
        aspect = cfg.get("ASPECT_RATIO", 2.2)
        vein_bright = cfg.get("VEIN_BRIGHTNESS", 0.06)
        vein_pulse = cfg.get("VEIN_PULSE", 0.15)
        systole_flush = cfg.get("SYSTOLE_FLUSH", 0.08)
        palette = cfg.get("PALETTE", _DEF_PALETTE)
        lut = build_palette_lut(palette)

        t_real += dt

        # Oscillating BPM
        current_bpm = bpm + (bpm_max - bpm_min) * 0.5 * math.sin(
            t_real * 2.0 * math.pi / bpm_cycle)
        cycle_duration = 60.0 / current_bpm

        # Advance phase accumulator
        old_phase = beat_phase
        beat_phase += dt / cycle_duration

        # LUB: fires when phase crosses an integer (new cycle)
        if math.floor(beat_phase) > math.floor(old_phase):
            pulse_rings.append((
                t_real, lub_strength, expand_speed,
                ring_width * 1.1, 4.5,
            ))
            dub_pending = True

        # DUB: fires once per cycle when fractional phase reaches dub_phase
        frac = beat_phase % 1.0
        if dub_pending and frac >= dub_phase:
            pulse_rings.append((
                t_real, dub_strength, expand_speed * 0.7,
                ring_width * 0.6, 6.0,
            ))
            dub_pending = False

        # Keep accumulator from growing huge
        if beat_phase > 1000.0:
            beat_phase -= 1000.0

        # Radial distance from center (aspect-corrected)
        dr = row_grid - center_row
        dc = (col_grid - center_col) / math.sqrt(aspect)
        r_dist = np.sqrt(dr * dr + dc * dc)

        # Sum all active pulse rings
        pulse_field = np.zeros((rows, cols), dtype=np.float64)
        alive_rings = []
        for birth_t, strength, exp_spd, hw, decay_r in pulse_rings:
            age = t_real - birth_t
            if age > 2.0:
                continue
            alive_rings.append((birth_t, strength, exp_spd, hw, decay_r))
            expand_radius = age * exp_spd * 4.0
            ring_pos = r_dist - expand_radius
            hw_sq = hw * hw
            decay = math.exp(-age * decay_r)
            ring_val = np.exp(-ring_pos * ring_pos / hw_sq) * strength * decay
            pulse_field += ring_val
        pulse_rings = alive_rings

        # Center throb synced to cardiac phases
        amp = 0.0
        if frac < 0.10:
            amp = math.sin(frac / 0.10 * math.pi) * lub_strength
        elif dub_phase <= frac < dub_phase + 0.10:
            t_in = (frac - dub_phase) / 0.10
            amp = math.sin(t_in * math.pi) * dub_strength
        center_glow = np.exp(-r_dist * r_dist / 3.5) * amp * 0.35
        pulse_field += center_glow

        # Systole flush: whole-keyboard warm tint during contraction
        flush = 0.0
        if frac < 0.15:
            flush = math.sin(frac / 0.15 * math.pi) * systole_flush
        elif dub_phase <= frac < dub_phase + 0.12:
            t_in = (frac - dub_phase) / 0.12
            flush = math.sin(t_in * math.pi) * systole_flush * 0.6
        pulse_field += flush

        # Vein network: veins brighten as wavefront passes
        vein_field = vein_base * vein_bright
        vein_field += vein_base * pulse_field * vein_pulse

        total = np.clip(pulse_field + vein_field, 0.0, 1.0)

        frame_rgb = palette_lookup(lut, total)
        draw_frame(device, frame_rgb)
        next_frame, dt = frame_sleep(next_frame, interval)

    clear_keyboard(device)


def main():
    standalone_main(EFFECT_NAME, run)


if __name__ == "__main__":
    main()
