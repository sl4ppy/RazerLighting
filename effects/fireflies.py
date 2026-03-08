#!/usr/bin/env python3
"""Fireflies - coupled oscillators using the Kuramoto model.

Each key is an oscillator with its own phase and natural frequency.
Neighbors couple via the Kuramoto model, causing waves of synchronization
and chaos as the coupling strength oscillates over time. Each oscillator
"flashes" briefly once per cycle like a firefly.

Edit fireflies_config.py while running to tweak on the fly.
"""

import math
import os
import time

import numpy as np

from effects.common import (
    load_config, draw_frame, clear_keyboard, frame_sleep, standalone_main,
)

EFFECT_NAME = "Fireflies"
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fireflies_config.py")

TWO_PI = 2.0 * math.pi


def run(device, stop_event):
    """Run the fireflies effect."""
    rows = device.fx.advanced.rows
    cols = device.fx.advanced.cols

    # Initialize oscillator phases randomly across the full cycle
    phases = np.random.uniform(0.0, TWO_PI, (rows, cols))

    # Draw natural frequencies from a normal distribution
    cfg = load_config(CONFIG_PATH)
    mean_freq = cfg.get("MEAN_FREQ", 0.12)
    freq_spread = cfg.get("FREQ_SPREAD", 0.02)
    nat_freqs = np.random.normal(mean_freq, freq_spread, (rows, cols))

    t = 0.0

    next_frame = time.monotonic()

    while not stop_event.is_set():
        cfg = load_config(CONFIG_PATH)
        fps = cfg.get("FPS", 20)
        interval = 1.0 / fps
        coupling = cfg.get("COUPLING", 0.15)
        coupling_speed = cfg.get("COUPLING_SPEED", 0.003)
        sharpness = cfg.get("FLASH_SHARPNESS", 4.0)
        dim_color = cfg.get("DIM_COLOR", (0, 15, 0))
        mid_color = cfg.get("MID_COLOR", (30, 100, 0))
        bright_color = cfg.get("BRIGHT_COLOR", (150, 220, 50))
        flash_color = cfg.get("FLASH_COLOR", (255, 255, 200))

        # Oscillating coupling strength: cycles between sync and chaos
        K = coupling * (0.5 + 0.5 * math.sin(t * coupling_speed))

        # Kuramoto phase update with Moore neighborhood (8-connected)
        # Accumulate coupling sum from all 8 neighbors using np.roll
        # Use open boundaries by masking edge contributions
        coupling_sum = np.zeros((rows, cols), dtype=np.float64)
        neighbor_count = np.zeros((rows, cols), dtype=np.float64)

        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                shifted = np.roll(np.roll(phases, -dr, axis=0), -dc, axis=1)
                sin_diff = np.sin(shifted - phases)

                # Build mask for valid neighbors (open boundaries)
                mask = np.ones((rows, cols), dtype=np.bool_)
                if dr == -1:
                    mask[0, :] = False
                elif dr == 1:
                    mask[rows - 1, :] = False
                if dc == -1:
                    mask[:, 0] = False
                elif dc == 1:
                    mask[:, cols - 1] = False

                coupling_sum += sin_diff * mask
                neighbor_count += mask

        # Avoid division by zero (corners still have at least 3 neighbors)
        d_phase = nat_freqs + (K / neighbor_count) * coupling_sum
        phases = (phases + d_phase) % TWO_PI

        # Compute brightness: sin(phase) clamped to [0,1], raised to sharpness
        raw = np.sin(phases)
        brightness = np.maximum(0.0, raw) ** sharpness

        # Map brightness through 3-segment firefly color gradient using np.where
        dim = np.array(dim_color, dtype=np.float64)
        mid = np.array(mid_color, dtype=np.float64)
        bright = np.array(bright_color, dtype=np.float64)
        flash = np.array(flash_color, dtype=np.float64)

        # Segment 1: brightness < 0.3 -> dim to mid (t = brightness / 0.3)
        # Segment 2: 0.3 <= brightness < 0.7 -> mid to bright (t = (brightness - 0.3) / 0.4)
        # Segment 3: brightness >= 0.7 -> bright to flash (t = (brightness - 0.7) / 0.3)
        seg_t = np.zeros((rows, cols), dtype=np.float64)
        c1 = np.zeros((rows, cols, 3), dtype=np.float64)
        c2 = np.zeros((rows, cols, 3), dtype=np.float64)

        mask_low = brightness < 0.3
        mask_mid = (brightness >= 0.3) & (brightness < 0.7)
        mask_high = brightness >= 0.7

        seg_t[mask_low] = brightness[mask_low] / 0.3
        c1[mask_low] = dim
        c2[mask_low] = mid

        seg_t[mask_mid] = (brightness[mask_mid] - 0.3) / 0.4
        c1[mask_mid] = mid
        c2[mask_mid] = bright

        seg_t[mask_high] = (brightness[mask_high] - 0.7) / 0.3
        c1[mask_high] = bright
        c2[mask_high] = flash

        seg_t_3d = seg_t[:, :, np.newaxis]
        frame_float = c1 + (c2 - c1) * seg_t_3d
        frame_rgb = np.clip(frame_float, 0, 255).astype(np.uint8)

        draw_frame(device, frame_rgb)
        next_frame, dt = frame_sleep(next_frame, interval)
        t += dt * fps

    clear_keyboard(device)


def main():
    """Standalone entry point."""
    standalone_main(EFFECT_NAME, run)


if __name__ == "__main__":
    main()
