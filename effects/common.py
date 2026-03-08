"""Shared utilities for all lighting effects."""

import math
import os
import sys
import time

import numpy as np

# --- Config loading with mtime caching ---

_config_cache = {}  # path -> (mtime, config_dict)


def load_config(config_path):
    """Load config from file, using cached version if file unchanged."""
    try:
        mt = os.path.getmtime(config_path)
        cached = _config_cache.get(config_path)
        if cached and cached[0] == mt:
            return cached[1]
        cfg = {}
        with open(config_path) as f:
            exec(f.read(), cfg)
        _config_cache[config_path] = (mt, cfg)
        return cfg
    except Exception as e:
        print(f"Config load error: {e}", file=sys.stderr)
        cached = _config_cache.get(config_path)
        return cached[1] if cached else {}


# --- Palette utilities ---

def build_palette_lut(palette, size=256):
    """Build a numpy LUT from a palette list. Returns (size, 3) uint8 array."""
    if not palette:
        return np.zeros((size, 3), dtype=np.uint8)
    lut = np.zeros((size, 3), dtype=np.uint8)
    n = len(palette) - 1
    for i in range(size):
        t = i / (size - 1) if size > 1 else 0.0
        pos = t * n
        idx = min(int(pos), max(n - 1, 0))
        frac = pos - idx
        c1 = palette[idx]
        c2 = palette[min(idx + 1, n)]
        lut[i] = (
            int(c1[0] + (c2[0] - c1[0]) * frac),
            int(c1[1] + (c2[1] - c1[1]) * frac),
            int(c1[2] + (c2[2] - c1[2]) * frac),
        )
    return lut


def palette_lookup(lut, values):
    """Map a float array (0..1) to RGB using a palette LUT.

    values: numpy array of floats in [0, 1]
    Returns: array of shape (*values.shape, 3) uint8
    """
    indices = np.clip((values * 255).astype(np.int32), 0, 255)
    return lut[indices]


def sample_palette(palette, t):
    """Sample a single color from a palette at position t (0..1)."""
    if not palette:
        return (0, 0, 0)
    t = max(0.0, min(1.0, t % 1.0))
    pos = t * (len(palette) - 1)
    idx = int(pos)
    frac = pos - idx
    if idx >= len(palette) - 1:
        return palette[-1]
    c1, c2 = palette[idx], palette[idx + 1]
    return (
        int(c1[0] + (c2[0] - c1[0]) * frac),
        int(c1[1] + (c2[1] - c1[1]) * frac),
        int(c1[2] + (c2[2] - c1[2]) * frac),
    )


# --- Color helpers ---

def lerp_color(a, b, t):
    """Linearly interpolate between two RGB tuples."""
    t = max(0.0, min(1.0, t))
    return (
        int(a[0] + (b[0] - a[0]) * t),
        int(a[1] + (b[1] - a[1]) * t),
        int(a[2] + (b[2] - a[2]) * t),
    )


# --- Device helpers ---

def draw_frame(device, frame_rgb):
    """Write a numpy (rows, cols, 3) uint8 array to the device and draw."""
    matrix = device.fx.advanced.matrix
    rows, cols = frame_rgb.shape[:2]
    for r in range(rows):
        for c in range(cols):
            matrix[r, c] = (int(frame_rgb[r, c, 0]),
                            int(frame_rgb[r, c, 1]),
                            int(frame_rgb[r, c, 2]))
    device.fx.advanced.draw()


def clear_keyboard(device):
    """Set all keys to black and draw."""
    rows = device.fx.advanced.rows
    cols = device.fx.advanced.cols
    for r in range(rows):
        for c in range(cols):
            device.fx.advanced.matrix[r, c] = (0, 0, 0)
    device.fx.advanced.draw()


# --- Timing ---

def frame_sleep(next_frame_time, interval):
    """Sleep until next frame deadline. Returns the next deadline."""
    next_frame_time += interval
    now = time.monotonic()
    if next_frame_time > now:
        time.sleep(next_frame_time - now)
    else:
        # We're behind; reset to avoid spiral
        next_frame_time = now
    return next_frame_time


def wait_interruptible(seconds, stop_event):
    """Sleep for a duration, returning early if stop_event is set."""
    end = time.monotonic() + seconds
    while time.monotonic() < end and not stop_event.is_set():
        time.sleep(min(0.05, end - time.monotonic()))
    return not stop_event.is_set()


# --- Numpy grid helpers ---

def make_coordinate_grids(rows, cols):
    """Return (row_grid, col_grid) numpy arrays for vectorized per-pixel math."""
    return np.mgrid[0:rows, 0:cols].astype(np.float64)


def laplacian_4pt(grid):
    """4-neighbor Laplacian with toroidal wrapping."""
    return (
        np.roll(grid, 1, axis=0) + np.roll(grid, -1, axis=0) +
        np.roll(grid, 1, axis=1) + np.roll(grid, -1, axis=1) -
        4.0 * grid
    )


def laplacian_4pt_open(grid):
    """4-neighbor Laplacian with open (zero) boundaries."""
    padded = np.pad(grid, 1, mode='constant', constant_values=0.0)
    return (
        padded[:-2, 1:-1] + padded[2:, 1:-1] +
        padded[1:-1, :-2] + padded[1:-1, 2:] -
        4.0 * grid
    )


def laplacian_9pt(grid):
    """Weighted 9-point Laplacian with toroidal wrapping."""
    lap = 0.2 * (
        np.roll(grid, 1, axis=0) + np.roll(grid, -1, axis=0) +
        np.roll(grid, 1, axis=1) + np.roll(grid, -1, axis=1)
    )
    lap += 0.05 * (
        np.roll(np.roll(grid, 1, axis=0), 1, axis=1) +
        np.roll(np.roll(grid, 1, axis=0), -1, axis=1) +
        np.roll(np.roll(grid, -1, axis=0), 1, axis=1) +
        np.roll(np.roll(grid, -1, axis=0), -1, axis=1)
    )
    lap -= grid
    return lap


def blur_3x3(grid):
    """3x3 box blur with toroidal wrapping."""
    total = np.zeros_like(grid)
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            total += np.roll(np.roll(grid, dr, axis=0), dc, axis=1)
    return total / 9.0


# --- Standalone main helper ---

def standalone_main(effect_name, run_func):
    """Common standalone entry point for effects."""
    import signal
    import threading
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from device import get_device

    device = get_device()
    stop_event = threading.Event()

    print(f"{device.name} ({device.fx.advanced.cols}x{device.fx.advanced.rows}) - {effect_name}")
    print("Ctrl+C to stop")

    signal.signal(signal.SIGINT, lambda *_: stop_event.set())
    signal.signal(signal.SIGTERM, lambda *_: stop_event.set())

    run_func(device, stop_event)
