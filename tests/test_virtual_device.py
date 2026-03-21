"""Tests for virtual_device.py and keyboard_layout.py."""

import pytest

from virtual_device import VirtualDevice, VirtualMatrix, detect_dimensions
from keyboard_layout import compute_key_rects


# ── VirtualDevice ────────────────────────────────────────────────────────────

class TestVirtualMatrix:
    def test_default_black(self):
        dev = VirtualDevice()
        assert dev.fx.advanced.matrix[0, 0] == (0, 0, 0)
        assert dev.fx.advanced.matrix[5, 15] == (0, 0, 0)

    def test_set_get(self):
        dev = VirtualDevice()
        dev.fx.advanced.matrix[2, 5] = (128, 64, 32)
        assert dev.fx.advanced.matrix[2, 5] == (128, 64, 32)

    def test_out_of_bounds_safe(self):
        dev = VirtualDevice()
        # Should not crash on out-of-bounds
        dev.fx.advanced.matrix[99, 99] = (255, 0, 0)
        assert dev.fx.advanced.matrix[99, 99] == (0, 0, 0)


class TestVirtualDevice:
    def test_dimensions(self):
        dev = VirtualDevice(rows=4, cols=8)
        assert dev.fx.advanced.rows == 4
        assert dev.fx.advanced.cols == 8

    def test_default_dimensions(self):
        dev = VirtualDevice()
        assert dev.fx.advanced.rows == 6
        assert dev.fx.advanced.cols == 16

    def test_name(self):
        dev = VirtualDevice()
        assert "Virtual" in dev.name

    def test_draw_calls_callback(self):
        frames = []
        dev = VirtualDevice(on_draw=lambda snap: frames.append(snap))
        dev.fx.advanced.matrix[0, 0] = (255, 0, 0)
        dev.fx.advanced.draw()
        assert len(frames) == 1
        assert frames[0][0][0] == (255, 0, 0)

    def test_draw_snapshot_is_copy(self):
        frames = []
        dev = VirtualDevice(on_draw=lambda snap: frames.append(snap))
        dev.fx.advanced.matrix[0, 0] = (255, 0, 0)
        dev.fx.advanced.draw()
        # Modify the matrix after draw
        dev.fx.advanced.matrix[0, 0] = (0, 255, 0)
        dev.fx.advanced.draw()
        # First snapshot should still be red
        assert frames[0][0][0] == (255, 0, 0)
        assert frames[1][0][0] == (0, 255, 0)

    def test_draw_without_callback(self):
        dev = VirtualDevice()
        dev.fx.advanced.matrix[0, 0] = (255, 0, 0)
        dev.fx.advanced.draw()  # Should not crash

    def test_multiple_pixels(self):
        dev = VirtualDevice()
        dev.fx.advanced.matrix[0, 0] = (255, 0, 0)
        dev.fx.advanced.matrix[5, 15] = (0, 255, 0)
        dev.fx.advanced.matrix[3, 8] = (0, 0, 255)
        assert dev.fx.advanced.matrix[0, 0] == (255, 0, 0)
        assert dev.fx.advanced.matrix[5, 15] == (0, 255, 0)
        assert dev.fx.advanced.matrix[3, 8] == (0, 0, 255)


class TestDetectDimensions:
    def test_returns_fallback(self):
        # Without a real device, should return fallback
        rows, cols = detect_dimensions()
        assert rows == 6
        assert cols == 16


# ── Keyboard Layout ──────────────────────────────────────────────────────────

class TestKeyboardLayout:
    def test_returns_list(self):
        rects = compute_key_rects()
        assert isinstance(rects, list)
        assert len(rects) > 0

    def test_key_structure(self):
        rects = compute_key_rects()
        for key in rects:
            assert "label" in key
            assert "row" in key
            assert "col" in key
            assert "x" in key
            assert "y" in key
            assert "w" in key
            assert "h" in key

    def test_reasonable_count(self):
        rects = compute_key_rects()
        # Razer Blade 14 has ~70+ physical keys
        assert len(rects) >= 60, f"Only {len(rects)} keys found"

    def test_all_positive_dimensions(self):
        rects = compute_key_rects()
        for key in rects:
            assert key["w"] > 0, f"Key {key['label']} has zero width"
            assert key["h"] > 0, f"Key {key['label']} has zero height"

    def test_no_overlapping_keys(self):
        rects = compute_key_rects()
        # Check no two keys have identical positions
        positions = set()
        for key in rects:
            pos = (round(key["x"], 3), round(key["y"], 3))
            assert pos not in positions, f"Duplicate position {pos} for {key['label']}"
            positions.add(pos)

    def test_six_rows(self):
        rects = compute_key_rects()
        rows = set(key["row"] for key in rects)
        assert len(rows) == 6, f"Expected 6 rows, got {rows}"

    def test_column_range(self):
        rects = compute_key_rects()
        cols = set(key["col"] for key in rects)
        assert min(cols) >= 1  # col 0 is unused
        assert max(cols) <= 15

    def test_special_keys_present(self):
        rects = compute_key_rects()
        labels = {key["label"] for key in rects}
        for expected in ["Esc", "Tab", "Caps", "Shift", "Ctrl", "Enter", "Bksp"]:
            assert expected in labels, f"Missing key: {expected}"
