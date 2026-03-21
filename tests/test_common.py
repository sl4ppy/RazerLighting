"""Tests for effects/common.py — palette, grid math, noise, discovery, timing."""

import os
import time
import threading

import numpy as np
import pytest

from effects.common import (
    build_palette_lut, palette_lookup, sample_palette, lerp_color,
    draw_frame, clear_keyboard, frame_sleep, wait_interruptible,
    make_coordinate_grids, laplacian_4pt, laplacian_4pt_open,
    laplacian_9pt, blur_3x3, value_noise_2d, fbm, discover_effects,
    load_config,
)


# ── Palette Utilities ────────────────────────────────────────────────────────

class TestBuildPaletteLut:
    def test_basic_shape(self):
        pal = [(0, 0, 0), (255, 255, 255)]
        lut = build_palette_lut(pal)
        assert lut.shape == (256, 3)
        assert lut.dtype == np.uint8

    def test_endpoints(self):
        pal = [(0, 0, 0), (255, 255, 255)]
        lut = build_palette_lut(pal)
        assert tuple(lut[0]) == (0, 0, 0)
        assert tuple(lut[255]) == (255, 255, 255)

    def test_midpoint(self):
        pal = [(0, 0, 0), (255, 255, 255)]
        lut = build_palette_lut(pal)
        mid = lut[128]
        assert 120 <= mid[0] <= 135  # approx midpoint

    def test_single_color(self):
        pal = [(128, 64, 32)]
        lut = build_palette_lut(pal)
        assert tuple(lut[0]) == (128, 64, 32)
        assert tuple(lut[255]) == (128, 64, 32)

    def test_empty_palette(self):
        lut = build_palette_lut([])
        assert lut.shape == (256, 3)
        assert np.all(lut == 0)

    def test_custom_size(self):
        lut = build_palette_lut([(0, 0, 0), (255, 0, 0)], size=16)
        assert lut.shape == (16, 3)

    def test_multi_stop(self):
        pal = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
        lut = build_palette_lut(pal)
        # Start is red
        assert lut[0, 0] == 255 and lut[0, 1] == 0
        # End is blue
        assert lut[255, 2] == 255 and lut[255, 0] == 0


class TestPaletteLookup:
    def test_basic(self):
        lut = build_palette_lut([(0, 0, 0), (255, 255, 255)])
        values = np.array([0.0, 0.5, 1.0])
        result = palette_lookup(lut, values)
        assert result.shape == (3, 3)
        assert tuple(result[0]) == (0, 0, 0)
        assert tuple(result[2]) == (255, 255, 255)

    def test_2d_input(self):
        lut = build_palette_lut([(0, 0, 0), (255, 0, 0)])
        values = np.array([[0.0, 0.5], [1.0, 0.25]])
        result = palette_lookup(lut, values)
        assert result.shape == (2, 2, 3)

    def test_clamp(self):
        lut = build_palette_lut([(0, 0, 0), (255, 255, 255)])
        values = np.array([-0.5, 1.5])
        result = palette_lookup(lut, values)
        assert tuple(result[0]) == (0, 0, 0)
        assert tuple(result[1]) == (255, 255, 255)


class TestSamplePalette:
    def test_start(self):
        pal = [(255, 0, 0), (0, 0, 255)]
        assert sample_palette(pal, 0.0) == (255, 0, 0)

    def test_end(self):
        pal = [(255, 0, 0), (0, 0, 255)]
        # sample_palette uses t % 1.0, so t=1.0 wraps to 0.0 (returns first color)
        # Use t=0.999 to get the last color
        r, g, b = sample_palette(pal, 0.999)
        assert b > 250  # near-blue

    def test_mid(self):
        pal = [(0, 0, 0), (200, 200, 200)]
        r, g, b = sample_palette(pal, 0.5)
        assert 95 <= r <= 105  # should be ~100

    def test_empty(self):
        assert sample_palette([], 0.5) == (0, 0, 0)

    def test_single(self):
        assert sample_palette([(42, 42, 42)], 0.5) == (42, 42, 42)

    def test_clamp(self):
        pal = [(0, 0, 0), (255, 0, 0)]
        assert sample_palette(pal, -1.0) == (0, 0, 0)


class TestLerpColor:
    def test_start(self):
        assert lerp_color((255, 0, 0), (0, 0, 255), 0.0) == (255, 0, 0)

    def test_end(self):
        assert lerp_color((255, 0, 0), (0, 0, 255), 1.0) == (0, 0, 255)

    def test_mid(self):
        r, g, b = lerp_color((0, 0, 0), (200, 100, 50), 0.5)
        assert r == 100
        assert g == 50
        assert b == 25

    def test_clamp(self):
        assert lerp_color((0, 0, 0), (255, 255, 255), 2.0) == (255, 255, 255)
        assert lerp_color((0, 0, 0), (255, 255, 255), -1.0) == (0, 0, 0)


# ── Frame Drawing ────────────────────────────────────────────────────────────

class TestDrawFrame:
    def test_draw_frame(self, virtual_device):
        frame = np.zeros((6, 16, 3), dtype=np.uint8)
        frame[0, 0] = [255, 0, 0]
        drawn = []
        virtual_device.fx.advanced._on_draw = lambda snap: drawn.append(snap)
        draw_frame(virtual_device, frame)
        assert len(drawn) == 1
        assert drawn[0][0][0] == (255, 0, 0)

    def test_clear_keyboard(self, virtual_device):
        # Set a pixel, then clear
        virtual_device.fx.advanced.matrix[0, 0] = (255, 0, 0)
        drawn = []
        virtual_device.fx.advanced._on_draw = lambda snap: drawn.append(snap)
        clear_keyboard(virtual_device)
        assert len(drawn) == 1
        assert drawn[0][0][0] == (0, 0, 0)


# ── Timing ───────────────────────────────────────────────────────────────────

class TestTiming:
    def test_frame_sleep_returns_next_and_dt(self):
        now = time.monotonic()
        next_frame, dt = frame_sleep(now, 0.001)
        assert next_frame > now
        assert dt >= 0

    def test_wait_interruptible_returns_true(self):
        event = threading.Event()
        result = wait_interruptible(0.01, event)
        assert result is True

    def test_wait_interruptible_returns_false_on_stop(self):
        event = threading.Event()
        event.set()
        result = wait_interruptible(1.0, event)
        assert result is False


# ── Grid Math ────────────────────────────────────────────────────────────────

class TestCoordinateGrids:
    def test_shape(self):
        rows, cols = make_coordinate_grids(6, 16)
        assert rows.shape == (6, 16)
        assert cols.shape == (6, 16)

    def test_values(self):
        rows, cols = make_coordinate_grids(3, 4)
        assert rows[0, 0] == 0.0
        assert rows[2, 0] == 2.0
        assert cols[0, 0] == 0.0
        assert cols[0, 3] == 3.0


class TestLaplacian:
    def test_4pt_constant_is_zero(self):
        grid = np.ones((6, 16))
        lap = laplacian_4pt(grid)
        assert np.allclose(lap, 0)

    def test_4pt_spike(self):
        grid = np.zeros((6, 16))
        grid[3, 8] = 1.0
        lap = laplacian_4pt(grid)
        # Spike center should be negative (lower than neighbors sum)
        assert lap[3, 8] < 0

    def test_4pt_open_boundary(self):
        grid = np.ones((6, 16))
        lap = laplacian_4pt_open(grid)
        # Constant grid: interior zero, edges non-zero due to zero boundary
        assert lap[3, 8] == 0  # interior

    def test_9pt_constant_is_zero(self):
        grid = np.ones((6, 16))
        lap = laplacian_9pt(grid)
        assert np.allclose(lap, 0, atol=1e-10)


class TestBlur:
    def test_blur_preserves_constant(self):
        grid = np.ones((6, 16)) * 5.0
        blurred = blur_3x3(grid)
        assert np.allclose(blurred, 5.0)

    def test_blur_smooths_spike(self):
        grid = np.zeros((6, 16))
        grid[3, 8] = 9.0
        blurred = blur_3x3(grid)
        # Spike should spread
        assert blurred[3, 8] < 9.0
        assert blurred[3, 8] > 0
        assert blurred[2, 8] > 0  # neighbor got some


# ── Noise ────────────────────────────────────────────────────────────────────

class TestNoise:
    def test_value_noise_range(self):
        x = np.linspace(0, 10, 100)
        y = np.linspace(0, 10, 100)
        xx, yy = np.meshgrid(x, y)
        result = value_noise_2d(xx, yy)
        assert result.min() >= 0.0
        assert result.max() <= 1.0

    def test_value_noise_shape(self):
        x = np.zeros((6, 16))
        y = np.zeros((6, 16))
        result = value_noise_2d(x, y)
        assert result.shape == (6, 16)

    def test_different_seeds(self):
        x = np.linspace(0, 5, 50)
        y = np.linspace(0, 5, 50)
        xx, yy = np.meshgrid(x, y)
        r1 = value_noise_2d(xx, yy, seed=42)
        r2 = value_noise_2d(xx, yy, seed=137)
        assert not np.allclose(r1, r2)

    def test_fbm_range(self):
        x = np.linspace(0, 5, 20)
        y = np.linspace(0, 5, 20)
        xx, yy = np.meshgrid(x, y)
        result = fbm(xx, yy, octaves=3)
        assert result.min() >= 0.0
        assert result.max() <= 1.0

    def test_fbm_octaves(self):
        x = np.linspace(0, 5, 20)
        y = np.linspace(0, 5, 20)
        xx, yy = np.meshgrid(x, y)
        r1 = fbm(xx, yy, octaves=1)
        r2 = fbm(xx, yy, octaves=4)
        # Different octaves should give different results
        assert not np.allclose(r1, r2)


# ── Effect Discovery ────────────────────────────────────────────────────────

class TestDiscoverEffects:
    def test_discovers_all_28(self):
        effects = discover_effects()
        assert len(effects) == 28, f"Expected 28 effects, got {len(effects)}: {sorted(effects.keys())}"

    def test_all_have_run(self):
        effects = discover_effects()
        for name, module in effects.items():
            assert hasattr(module, "run"), f"{name} missing run()"
            assert callable(module.run), f"{name}.run is not callable"

    def test_all_have_effect_name(self):
        effects = discover_effects()
        for name, module in effects.items():
            assert hasattr(module, "EFFECT_NAME"), f"{name} missing EFFECT_NAME"

    def test_excludes_config_files(self):
        effects = discover_effects()
        for name in effects:
            assert "config" not in name.lower().replace(" ", ""), f"Config file leaked: {name}"

    def test_excludes_common(self):
        effects = discover_effects()
        assert "Common" not in effects
        assert "common" not in effects


# ── Config Loading ───────────────────────────────────────────────────────────

class TestLoadConfig:
    def test_load_basic(self, tmp_path):
        cfg = tmp_path / "cfg.py"
        cfg.write_text("FPS = 30\nSPEED = 0.5\n")
        result = load_config(str(cfg))
        assert result["FPS"] == 30
        assert result["SPEED"] == 0.5

    def test_load_caching(self, tmp_path):
        cfg = tmp_path / "cfg.py"
        cfg.write_text("X = 1\n")
        r1 = load_config(str(cfg))
        r2 = load_config(str(cfg))
        assert r1 is r2  # same cached dict

    def test_load_nonexistent_returns_empty(self):
        result = load_config("/nonexistent/path.py")
        assert result == {}
