"""Shared utilities for all lighting effects."""

import importlib.util
import math
import os
import sys
import time

import numpy as np

# --- Config loading with mtime caching ---

_config_cache = {}  # path -> (mtime, config_dict)


def load_config(config_path):
    """Load config from file, using cached version if file unchanged.

    Uses exec() rather than importlib so config files are simple namespace
    dicts without module registration side effects.  Config files are local
    user-owned files, not external input — the exec() is intentional.
    """
    try:
        mt = os.path.getmtime(config_path)
        cached = _config_cache.get(config_path)
        if cached and cached[0] == mt:
            return cached[1]
        cfg = {}
        with open(config_path) as f:
            exec(f.read(), cfg)  # noqa: S102 — intentional; see docstring
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
    """Sleep until next frame deadline. Returns (next_deadline, dt).

    dt is the actual elapsed time since the previous deadline, capped at
    3× interval to avoid huge jumps after a system suspend/resume.
    """
    prev = next_frame_time
    next_frame_time += interval
    now = time.monotonic()
    if next_frame_time > now:
        time.sleep(next_frame_time - now)
    else:
        # We're behind; reset to avoid spiral
        next_frame_time = now
    dt = min(next_frame_time - prev, interval * 3)
    return next_frame_time, dt


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


# --- Value noise ---

def _make_perm(seed):
    """Build a 512-entry permutation table from a seed."""
    perm = np.arange(256, dtype=np.int32)
    np.random.RandomState(seed).shuffle(perm)
    return np.tile(perm, 2)


# Pre-built tables for each effect that uses noise (avoids rebuilding per frame)
_perm_tables = {}


def _get_perm(seed):
    if seed not in _perm_tables:
        _perm_tables[seed] = _make_perm(seed)
    return _perm_tables[seed]


def _fade(t):
    return t * t * t * (t * (t * 6 - 15) + 10)


def value_noise_2d(x, y, seed=42):
    """Vectorized 2D value noise. Returns values in [0, 1].

    x, y: numpy arrays of the same shape (sampling coordinates).
    seed: integer seed for the permutation table (different seeds give
          different patterns).
    """
    perm = _get_perm(seed)
    xi = np.floor(x).astype(np.int32) & 255
    yi = np.floor(y).astype(np.int32) & 255
    xf = x - np.floor(x)
    yf = y - np.floor(y)
    u = _fade(xf)
    v = _fade(yf)
    aa = perm[perm[xi] + yi] / 255.0
    ab = perm[perm[xi] + yi + 1] / 255.0
    ba = perm[perm[xi + 1] + yi] / 255.0
    bb = perm[perm[xi + 1] + yi + 1] / 255.0
    x1 = aa + u * (ba - aa)
    x2 = ab + u * (bb - ab)
    return x1 + v * (x2 - x1)


def fbm(x, y, octaves=2, weights=None, seed=42):
    """Fractal Brownian motion built on value_noise_2d.

    octaves: number of noise layers (default 2).
    weights: per-octave amplitude weights.  If None, uses standard
             halving (0.7, 0.3 for 2 octaves; 0.55, 0.3, 0.15 for 3).
    seed: permutation table seed.
    """
    if weights is None:
        if octaves == 2:
            weights = (0.7, 0.3)
        elif octaves == 3:
            weights = (0.55, 0.3, 0.15)
        else:
            # Geometric falloff
            raw = [0.5 ** i for i in range(octaves)]
            total = sum(raw)
            weights = [w / total for w in raw]
    result = np.zeros_like(x, dtype=np.float64)
    freq = 1.0
    for w in weights:
        result += value_noise_2d(x * freq, y * freq, seed=seed) * w
        freq *= 2.0
    return result


# --- Effect discovery ---

EFFECTS_DIR = os.path.dirname(os.path.abspath(__file__))


def discover_effects(effects_dir=None):
    """Find all effect modules in the effects directory."""
    if effects_dir is None:
        effects_dir = EFFECTS_DIR
    effects = {}
    for filename in sorted(os.listdir(effects_dir)):
        if filename.endswith("_config.py") or filename.startswith("__"):
            continue
        if not filename.endswith(".py"):
            continue
        if filename == "common.py":
            continue
        path = os.path.join(effects_dir, filename)
        try:
            spec = importlib.util.spec_from_file_location(filename[:-3], path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if hasattr(module, "run"):
                name = getattr(module, "EFFECT_NAME", filename[:-3].replace("_", " ").title())
                effects[name] = module
        except Exception as e:
            print(f"Skipping {filename}: {e}", file=sys.stderr)
    return effects


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
