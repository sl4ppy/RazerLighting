"""Exhaustive tests for config_parser.py — type inference, range inference, parse/write, grouping."""

import os
import tempfile

import pytest

from config_parser import (
    ConfigParam, parse_config, write_config, write_temp_config,
    humanize_name, group_params, _infer_type, _infer_range, _is_rgb,
    _extract_comment,
)


# ── humanize_name ────────────────────────────────────────────────────────────

class TestHumanizeName:
    def test_simple(self):
        assert humanize_name("FPS") == "Fps"

    def test_multi_word(self):
        assert humanize_name("SPEED_MAX") == "Speed Max"

    def test_three_words(self):
        assert humanize_name("BG_COLOR_R") == "Bg Color R"

    def test_single_char(self):
        assert humanize_name("X") == "X"

    def test_already_title(self):
        assert humanize_name("Speed") == "Speed"


# ── _is_rgb ──────────────────────────────────────────────────────────────────

class TestIsRgb:
    def test_valid_rgb(self):
        assert _is_rgb((255, 0, 0))
        assert _is_rgb((0, 0, 0))
        assert _is_rgb((255, 255, 255))
        assert _is_rgb((128, 64, 32))

    def test_boundary(self):
        assert _is_rgb((0, 0, 0))
        assert _is_rgb((255, 255, 255))

    def test_out_of_range(self):
        assert not _is_rgb((256, 0, 0))
        assert not _is_rgb((-1, 0, 0))
        assert not _is_rgb((0, 0, 300))

    def test_wrong_length(self):
        assert not _is_rgb((255, 0))
        assert not _is_rgb((255, 0, 0, 255))

    def test_wrong_types(self):
        assert not _is_rgb((1.0, 0.0, 0.0))
        assert not _is_rgb("red")
        assert not _is_rgb([255, 0, 0])

    def test_not_tuple(self):
        assert not _is_rgb(None)
        assert not _is_rgb(42)


# ── _infer_type ──────────────────────────────────────────────────────────────

class TestInferType:
    def test_bool(self):
        assert _infer_type("ENABLED", True) == "bool"
        assert _infer_type("ENABLED", False) == "bool"

    def test_bool_before_int(self):
        # bool is subclass of int, must check first
        assert _infer_type("FLAG", True) == "bool"

    def test_int(self):
        assert _infer_type("FPS", 20) == "int"
        assert _infer_type("COUNT", 0) == "int"
        assert _infer_type("NEG", -5) == "int"

    def test_float(self):
        assert _infer_type("SPEED", 0.5) == "float"
        assert _infer_type("RATE", 0.0) == "float"

    def test_rgb(self):
        assert _infer_type("BG_COLOR", (255, 0, 0)) == "rgb"
        assert _infer_type("COLOR", (0, 0, 0)) == "rgb"

    def test_palette(self):
        assert _infer_type("PALETTE", [(255, 0, 0), (0, 255, 0)]) == "palette"

    def test_float_list(self):
        assert _infer_type("WEIGHTS", [0.5, 0.3, 0.2]) == "float_list"

    def test_int_list(self):
        assert _infer_type("COUNTS", [1, 5, 10]) == "int_list"

    def test_tuple_list(self):
        assert _infer_type("POINTS", [(1, 2), (3, 4)]) == "tuple_list"

    def test_mixed_numeric_list(self):
        assert _infer_type("MIXED", [1, 0.5, 2]) == "float_list"

    def test_empty_list(self):
        # Empty list can't be inferred
        assert _infer_type("EMPTY", []) == "unknown"

    def test_string_unknown(self):
        assert _infer_type("NAME", "hello") == "unknown"

    def test_none_unknown(self):
        assert _infer_type("NONE", None) == "unknown"

    def test_single_element_palette(self):
        assert _infer_type("PAL", [(128, 128, 128)]) == "palette"


# ── _infer_range ─────────────────────────────────────────────────────────────

class TestInferRange:
    def test_non_numeric_returns_default(self):
        assert _infer_range("X", True, "bool") == (0.0, 1.0, 0.01)
        assert _infer_range("X", [], "palette") == (0.0, 1.0, 0.01)

    def test_fps(self):
        rmin, rmax, step = _infer_range("FPS", 20, "int")
        assert rmin == 1
        assert rmax == 60
        assert step == 1

    def test_chance_float(self):
        rmin, rmax, step = _infer_range("SPAWN_CHANCE", 0.3, "float")
        assert rmin == 0.0
        assert rmax == 1.0

    def test_chance_int(self):
        rmin, rmax, step = _infer_range("DENSITY", 50, "int")
        assert rmin == 0
        assert rmax == 100

    def test_blend(self):
        rmin, rmax, step = _infer_range("COLOR_BLEND", 0.5, "float")
        assert rmax == 1.0

    def test_position_suffix_x(self):
        rmin, rmax, step = _infer_range("CENTER_X", 0.5, "float")
        assert rmin == 0.0
        assert rmax == 1.0

    def test_position_suffix_y(self):
        rmin, rmax, step = _infer_range("CENTER_Y", 0.3, "float")
        assert rmin == 0.0
        assert rmax == 1.0

    def test_position_suffix_fade(self):
        rmin, rmax, step = _infer_range("EDGE_FADE", 0.8, "float")
        assert rmin == 0.0
        assert rmax == 1.0

    def test_position_suffix_out_of_range(self):
        # Value > 1.0, should NOT match position suffix
        rmin, rmax, step = _infer_range("CENTER_X", 5.0, "float")
        assert rmax != 1.0  # falls through to another rule

    def test_threshold_float(self):
        rmin, rmax, step = _infer_range("THRESHOLD", 0.5, "float")
        assert rmin == 0.0
        assert rmax >= 1.5  # value * 3

    def test_threshold_int(self):
        rmin, rmax, step = _infer_range("THRESHOLD", 10, "int")
        assert rmin == 0
        assert rmax >= 50  # value * 5

    def test_num_prefix(self):
        rmin, rmax, step = _infer_range("NUM_PARTICLES", 100, "int")
        assert rmin == 1
        assert rmax >= 500

    def test_max_prefix(self):
        rmin, rmax, step = _infer_range("MAX_STREAMS", 10, "int")
        assert rmin == 1
        assert rmax >= 50

    def test_speed_float_small(self):
        rmin, rmax, step = _infer_range("SPEED", 0.05, "float")
        assert rmin == 0.0
        assert step == 0.001

    def test_speed_float_large(self):
        rmin, rmax, step = _infer_range("SPEED_MAX", 5.0, "float")
        assert rmin == 0.0
        assert rmax >= 25.0

    def test_scale_float(self):
        rmin, rmax, step = _infer_range("SCALE", 2.0, "float")
        assert rmin == 0.01
        assert rmax >= 10.0

    def test_width_float(self):
        rmin, rmax, step = _infer_range("BEAM_WIDTH", 3.0, "float")
        assert rmin == 0.0
        assert rmax >= 15.0

    def test_sharpness_float(self):
        rmin, rmax, step = _infer_range("SHARPNESS", 2.0, "float")
        assert rmin == 0.0
        assert rmax >= 6.0

    def test_fallback_int_small(self):
        rmin, rmax, step = _infer_range("FOO", 5, "int")
        assert rmin == 0
        assert rmax >= 20

    def test_fallback_int_large(self):
        rmin, rmax, step = _infer_range("FOO", 100, "int")
        assert rmin == 1
        assert rmax == 500

    def test_fallback_int_negative(self):
        rmin, rmax, step = _infer_range("OFFSET", -10, "int")
        assert rmin < 0
        assert rmax > 0

    def test_fallback_float(self):
        rmin, rmax, step = _infer_range("PARAM", 2.0, "float")
        assert rmin == 0.0
        assert rmax >= 10.0

    def test_fallback_float_negative(self):
        rmin, rmax, step = _infer_range("OFFSET", -2.0, "float")
        assert rmin < 0
        assert rmax > 0


# ── parse_config + write_config round-trip ───────────────────────────────────

class TestParseConfig:
    def test_parse_basic(self, tmp_config):
        params = parse_config(tmp_config)
        assert len(params) > 0
        names = [p.name for p in params]
        assert "FPS" in names
        assert "SPEED" in names
        assert "ENABLED" in names
        assert "BG_COLOR" in names
        assert "PALETTE" in names

    def test_types_inferred(self, tmp_config):
        params = parse_config(tmp_config)
        by_name = {p.name: p for p in params}
        assert by_name["FPS"].param_type == "int"
        assert by_name["SPEED"].param_type == "float"
        assert by_name["ENABLED"].param_type == "bool"
        assert by_name["BG_COLOR"].param_type == "rgb"
        assert by_name["PALETTE"].param_type == "palette"
        assert by_name["WEIGHTS"].param_type == "float_list"
        assert by_name["COUNTS"].param_type == "int_list"
        assert by_name["POINTS"].param_type == "tuple_list"

    def test_values_correct(self, tmp_config):
        params = parse_config(tmp_config)
        by_name = {p.name: p for p in params}
        assert by_name["FPS"].value == 20
        assert by_name["SPEED"].value == 0.5
        assert by_name["ENABLED"].value is True
        assert by_name["BG_COLOR"].value == (0, 0, 0)
        assert by_name["PALETTE"].value == [(255, 0, 0), (0, 255, 0), (0, 0, 255)]

    def test_inline_comment_extracted(self, tmp_config):
        params = parse_config(tmp_config)
        by_name = {p.name: p for p in params}
        assert "threshold" in by_name["THRESHOLD"].comment.lower() or "threshold" in by_name["THRESHOLD"].tooltip.lower()

    def test_write_roundtrip(self, tmp_config):
        params = parse_config(tmp_config)
        by_name = {p.name: p for p in params}

        # Modify a value
        by_name["FPS"].value = 30
        by_name["SPEED"].value = 1.5

        write_config(tmp_config, params)

        # Re-parse and verify
        params2 = parse_config(tmp_config)
        by_name2 = {p.name: p for p in params2}
        assert by_name2["FPS"].value == 30
        assert by_name2["SPEED"].value == 1.5
        # Unchanged values preserved
        assert by_name2["ENABLED"].value is True
        assert by_name2["BG_COLOR"].value == (0, 0, 0)

    def test_write_temp_config(self, tmp_config, tmp_path):
        params = parse_config(tmp_config)
        temp_dir = str(tmp_path / "preview")
        temp_path = write_temp_config(tmp_config, params, temp_dir=temp_dir)
        assert os.path.exists(temp_path)
        # Re-parse temp file
        params2 = parse_config(temp_path)
        assert len(params2) == len(params)

    def test_empty_file(self, tmp_path):
        empty = tmp_path / "empty.py"
        empty.write_text("")
        params = parse_config(str(empty))
        assert params == []

    def test_nonexistent_file(self, tmp_path):
        params = parse_config(str(tmp_path / "nonexistent.py"))
        assert params == []

    def test_underscore_vars_excluded(self, tmp_path):
        cfg = tmp_path / "cfg.py"
        cfg.write_text("_INTERNAL = 42\nFPS = 20\n")
        params = parse_config(str(cfg))
        names = [p.name for p in params]
        assert "_INTERNAL" not in names
        assert "FPS" in names


# ── _extract_comment ─────────────────────────────────────────────────────────

class TestExtractComment:
    def test_simple_comment(self):
        result = _extract_comment("FPS = 20  # frames per second", "20")
        assert "frames per second" in result

    def test_no_comment(self):
        result = _extract_comment("FPS = 20", "20")
        assert result == ""

    def test_hash_in_string(self):
        result = _extract_comment("NAME = '#ff0000'  # hex color", "'#ff0000'")
        assert "hex color" in result


# ── group_params ─────────────────────────────────────────────────────────────

class TestGroupParams:
    def _make_param(self, name, ptype="int"):
        return ConfigParam(name=name, value=0, param_type=ptype, line_number=1)

    def test_timing_group(self):
        params = [self._make_param("FPS"), self._make_param("SPEED_MAX")]
        groups = group_params(params)
        assert "Timing" in groups
        assert len(groups["Timing"]) == 2

    def test_colors_group(self):
        params = [self._make_param("BG_COLOR", "rgb"), self._make_param("PALETTE", "palette")]
        groups = group_params(params)
        assert "Colors" in groups
        assert len(groups["Colors"]) == 2

    def test_simulation_group(self):
        params = [self._make_param("DECAY_RATE"), self._make_param("DENSITY")]
        groups = group_params(params)
        assert "Simulation" in groups

    def test_other_group(self):
        params = [self._make_param("FOO_BAR")]
        groups = group_params(params)
        assert "Other" in groups

    def test_empty_groups_removed(self):
        params = [self._make_param("FPS")]
        groups = group_params(params)
        assert "Colors" not in groups
        assert "Simulation" not in groups

    def test_empty_input(self):
        groups = group_params([])
        assert groups == {}
