#!/usr/bin/env python3
"""Corruption - organic digital decay spreading across the keyboard.

A calm breathing gradient gets attacked by corruption that grows organically
from random seed points.  Each infection has blobby, noise-modulated edges,
gradient intensity falloff, and a multi-phase lifecycle:

  incubation (single-pixel flicker) → spread → peak → decay → scar

Sites can cascade to spawn neighbours, merge when overlapping, and trigger
full-width scanline bleeds.  A periodic power-surge flares all active zones.

Edit corruption_config.py while running to tweak on the fly.
"""

import math
import os
import random
import time

import numpy as np

from effects.common import (
    load_config, draw_frame, clear_keyboard, frame_sleep,
    build_palette_lut, palette_lookup, make_coordinate_grids,
    standalone_main,
)

EFFECT_NAME = "Corruption"
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "corruption_config.py")


# ---------------------------------------------------------------------------
# Blob-boundary noise
# ---------------------------------------------------------------------------

def _make_shape(n=8):
    """Random radial control points that give each blob a unique outline."""
    return [random.uniform(0.7, 1.3) for _ in range(n)]


def _sample_shape_vec(shape, angles):
    """Vectorised cosine-interpolated radial noise from control points."""
    n = len(shape)
    s = np.array(shape, dtype=np.float64)
    t = (angles % (2 * math.pi)) / (2 * math.pi) * n
    idx = t.astype(np.int32) % n
    frac = t - np.floor(t)
    frac = 0.5 - 0.5 * np.cos(frac * math.pi)
    nxt = (idx + 1) % n
    return s[idx] * (1.0 - frac) + s[nxt] * frac


# ---------------------------------------------------------------------------
# Infection-site helpers
# ---------------------------------------------------------------------------

def _spawn(rows, cols, cfg, parent_pos=None):
    """Create a new corruption site, optionally near *parent_pos*."""
    if parent_pos is not None:
        r = float(np.clip(parent_pos[0] + random.uniform(-4, 4), 0, rows - 1))
        c = float(np.clip(parent_pos[1] + random.uniform(-4, 4), 0, cols - 1))
    else:
        r = random.uniform(0, rows - 1)
        c = random.uniform(0, cols - 1)
    return {
        "pos": (r, c),
        "age": 0.0,
        "max_radius": random.uniform(cfg.get("RADIUS_MIN", 2.0),
                                     cfg.get("RADIUS_MAX", 5.5)),
        "shape": _make_shape(),
        "t_incubate": cfg.get("INCUBATION_TIME", 0.3),
        "t_spread":   cfg.get("SPREAD_TIME", 0.8),
        "t_peak":     random.uniform(cfg.get("PEAK_TIME_MIN", 0.5),
                                     cfg.get("PEAK_TIME_MAX", 1.5)),
        "t_decay":    cfg.get("DECAY_TIME", 0.8),
        "t_scar":     cfg.get("SCAR_TIME", 2.0),
        "cascaded":   False,
    }


_PHASES = ("t_incubate", "t_spread", "t_peak", "t_decay", "t_scar")


def _phase(site):
    """Return *(phase_key, progress_0_to_1)* for the site's current age."""
    age = site["age"]
    t = 0.0
    for name in _PHASES:
        dur = site[name]
        if age < t + dur:
            return name, (age - t) / dur if dur > 0 else 1.0
        t += dur
    return "dead", 1.0


def _severity_radius(site):
    """Current *(severity 0–1, effective_radius)* from the lifecycle phase."""
    phase, p = _phase(site)
    R = site["max_radius"]
    if phase == "t_incubate":
        return 0.15, 0.5
    if phase == "t_spread":
        return 0.15 + 0.85 * p ** 0.7, R * p
    if phase == "t_peak":
        return 1.0, R
    if phase == "t_decay":
        return 1.0 - p ** 0.5, R * (1.0 - 0.3 * p)
    if phase == "t_scar":
        return 0.0, R * (1.0 - p)
    return 0.0, 0.0


# ---------------------------------------------------------------------------
# Intensity / scar field
# ---------------------------------------------------------------------------

def _compute_fields(sites, rows, cols, rg, cg):
    """Build per-pixel *intensity* and *scar* maps from all active sites."""
    intensity = np.zeros((rows, cols), dtype=np.float64)
    scar = np.zeros((rows, cols), dtype=np.float64)

    for site in sites:
        phase, _ = _phase(site)
        if phase == "dead":
            continue

        sev, radius = _severity_radius(site)
        sr, sc = site["pos"]
        dr = rg - sr
        dc = cg - sc
        dist = np.sqrt(dr * dr + dc * dc)

        if phase == "t_incubate":
            nr = max(0, min(rows - 1, int(round(sr))))
            nc = max(0, min(cols - 1, int(round(sc))))
            if random.random() < 0.6:
                intensity[nr, nc] = max(intensity[nr, nc],
                                        random.uniform(0.2, 0.7))
            continue

        # Noise-modulated boundary
        angles = np.arctan2(dr, dc)
        mod_r = radius * _sample_shape_vec(site["shape"], angles)
        norm = np.where(mod_r > 0.01, dist / mod_r, 999.0)
        si = np.clip(1.0 - norm, 0.0, 1.0) ** 0.6 * sev

        if phase == "t_scar":
            scar = np.maximum(scar, si * 0.4)
        else:
            intensity = np.maximum(intensity, si)
            scar = np.maximum(scar, si * 0.15)

    return intensity, scar


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def _render_baseline(t, rg, cg, cfg):
    """Slowly undulating blue-teal gradient — the 'healthy signal'."""
    pal = cfg.get("BASELINE_PALETTE",
                  [(0, 8, 20), (0, 20, 45), (0, 40, 55), (0, 25, 35)])
    lut = build_palette_lut(pal)
    spd = cfg.get("BASELINE_SPEED", 0.4)
    wave = (0.5
            + 0.35 * np.sin(cg * 0.35 + t * spd)
            + 0.12 * np.sin(rg * 0.7 + t * spd * 0.6 + 1.5)
            + 0.08 * np.sin(cg * 0.7 - t * spd * 0.3 + 3.0))
    return palette_lookup(lut, np.clip(wave, 0.0, 1.0)).astype(np.float64)


def _render_corruption(baseline, intensity, scar, cfg):
    """Composite corruption artifacts onto *baseline* using the intensity map.

    Zones (by intensity):
      core  (>0.7)  – dead pixels, white flashes, colour blowout, channel swaps
      mid   (0.3–0.7) – hue shift toward corrupt colour, sparks, flicker
      fringe(<0.3)  – subtle warmth shift, rare single-frame flickers
      scar  (intensity==0, scar>0) – faint green tint fading over time
    """
    frame = baseline.copy()
    rows, cols = frame.shape[:2]
    cc = np.array(cfg.get("CORRUPT_COLOR", (255, 0, 100)), dtype=np.float64)
    sc_col = np.array(cfg.get("SCAR_COLOR", (0, 50, 30)), dtype=np.float64)

    for r in range(rows):
        for c in range(cols):
            iv = intensity[r, c]
            sv = scar[r, c]
            base = baseline[r, c]

            if iv > 0.7:
                # ---- Core ----
                roll = random.random()
                if roll < 0.12:
                    # Dead pixel
                    frame[r, c] = (0, 0, 0)
                elif roll < 0.28:
                    # White-hot flash
                    b = random.uniform(0.7, 1.0) * iv
                    frame[r, c] = (255 * b, 255 * b, 255 * b)
                elif roll < 0.55:
                    # Corrupt colour with jitter
                    b = random.uniform(0.5, 1.0) * iv
                    j = random.uniform(-30, 30)
                    frame[r, c] = (
                        np.clip((cc[0] + j) * b, 0, 255),
                        np.clip((cc[1] + j * 0.3) * b, 0, 255),
                        np.clip((cc[2] + j) * b, 0, 255),
                    )
                elif roll < 0.75:
                    # Channel swap / chromatic aberration
                    frame[r, c] = (
                        np.clip(base[2] * iv * 1.5, 0, 255),
                        np.clip(base[0] * iv * 0.5, 0, 255),
                        np.clip(base[1] * iv * 1.3, 0, 255),
                    )
                else:
                    # Overdriven baseline
                    n = random.uniform(0.3, 2.0)
                    frame[r, c] = (
                        min(255.0, base[0] * n),
                        min(255.0, base[1] * n * 0.5),
                        min(255.0, base[2] * n * 0.3),
                    )

            elif iv > 0.3:
                # ---- Mid zone ----
                blend = (iv - 0.3) / 0.4
                rnd = random.random()
                if rnd < 0.08 * blend:
                    # Bright spark
                    b = random.uniform(0.5, 1.0) * blend
                    frame[r, c] = (
                        np.clip(cc[0] * b, 0, 255),
                        np.clip(cc[1] * b, 0, 255),
                        np.clip(cc[2] * b, 0, 255),
                    )
                elif rnd < 0.11 * blend:
                    # Momentary blackout
                    frame[r, c] = (0, 0, 0)
                else:
                    # Hue-shift toward corrupt colour
                    s = blend * iv
                    frame[r, c] = (
                        np.clip(base[0] + (cc[0] - base[0]) * s * 0.4, 0, 255),
                        np.clip(base[1] * (1.0 - s * 0.3), 0, 255),
                        np.clip(base[2] * (1.0 - s * 0.5), 0, 255),
                    )
                    # Occasional brightness flicker
                    if random.random() < 0.04 * blend:
                        f = random.uniform(0.5, 1.5)
                        frame[r, c] = (
                            np.clip(frame[r, c, 0] * f, 0, 255),
                            np.clip(frame[r, c, 1] * f, 0, 255),
                            np.clip(frame[r, c, 2] * f, 0, 255),
                        )

            elif iv > 0.01:
                # ---- Fringe: subtle wrongness ----
                blend = iv / 0.3
                frame[r, c] = (
                    np.clip(base[0] + 15 * blend, 0, 255),
                    np.clip(base[1] - 5 * blend, 0, 255),
                    np.clip(base[2] - 8 * blend, 0, 255),
                )

            elif sv > 0.01:
                # ---- Scar: healing residue ----
                frame[r, c] = (
                    np.clip(base[0] + sc_col[0] * sv, 0, 255),
                    np.clip(base[1] + sc_col[1] * sv, 0, 255),
                    np.clip(base[2] + sc_col[2] * sv, 0, 255),
                )

    return frame


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def run(device, stop_event):
    """Run the Corruption effect."""
    rows = device.fx.advanced.rows
    cols = device.fx.advanced.cols
    rg, cg = make_coordinate_grids(rows, cols)

    sites = []
    t = 0.0
    surge_cd = 0.0
    next_frame = time.monotonic()

    while not stop_event.is_set():
        cfg = load_config(CONFIG_PATH)
        fps = cfg.get("FPS", 18)
        interval = 1.0 / fps

        next_frame, dt = frame_sleep(next_frame, interval)
        t += dt
        surge_cd += dt

        max_sites = cfg.get("MAX_SITES", 4)
        spawn_ivl = cfg.get("SPAWN_INTERVAL", 3.0)

        # --- Spawn ---
        if len(sites) < max_sites and random.random() < dt / spawn_ivl:
            sites.append(_spawn(rows, cols, cfg))

        # --- Age ---
        for s in sites:
            s["age"] += dt

        # --- Cascade ---
        children = []
        for s in sites:
            if not s["cascaded"]:
                ph, p = _phase(s)
                if ph == "t_peak" and 0.1 < p < 0.3:
                    s["cascaded"] = True
                    if random.random() < cfg.get("CASCADE_CHANCE", 0.2):
                        if len(sites) + len(children) < max_sites:
                            children.append(_spawn(rows, cols, cfg, s["pos"]))
                            if (random.random() < 0.3
                                    and len(sites) + len(children) < max_sites):
                                children.append(
                                    _spawn(rows, cols, cfg, s["pos"]))
        sites.extend(children)

        # --- Cull dead ---
        sites = [s for s in sites if _phase(s)[0] != "dead"]

        # --- Surge ---
        surge_ivl = cfg.get("SURGE_INTERVAL", 20.0)
        in_surge = surge_cd >= surge_ivl
        if in_surge:
            surge_cd = 0.0

        # --- Fields ---
        intensity, scar_map = _compute_fields(sites, rows, cols, rg, cg)
        if in_surge:
            intensity = np.clip(intensity * 1.8, 0.0, 1.0)

        # --- Draw ---
        baseline = _render_baseline(t, rg, cg, cfg)
        frame = _render_corruption(baseline, intensity, scar_map, cfg)

        # Row bleed: high-intensity sites can fire a full-width scanline
        bleed_chance = cfg.get("ROW_BLEED_CHANCE", 0.03)
        peak = np.max(intensity) if intensity.size else 0.0
        if peak > 0.8 and random.random() < bleed_chance:
            hr, _hc = np.unravel_index(np.argmax(intensity), intensity.shape)
            br = max(0, min(rows - 1, hr + random.randint(-1, 1)))
            bi = random.uniform(0.3, 0.7)
            cc_arr = np.array(cfg.get("CORRUPT_COLOR", (255, 0, 100)),
                              dtype=np.float64)
            frame[br, :] = cc_arr * bi

        draw_frame(device, np.clip(frame, 0, 255).astype(np.uint8))

    clear_keyboard(device)


def main():
    """Standalone entry point."""
    standalone_main(EFFECT_NAME, run)


if __name__ == "__main__":
    main()
