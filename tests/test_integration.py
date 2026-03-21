"""Integration tests — end-to-end parse → widget → modify → write-back."""

import os

import pytest

from config_parser import parse_config, write_config, write_temp_config, group_params
from config_widgets import create_param_widget


class TestParseWidgetWriteRoundTrip:
    """Parse a real config, create widgets, modify values, write back, verify."""

    def test_full_roundtrip(self, qapp, tmp_config):
        # Step 1: Parse config
        params = parse_config(tmp_config)
        assert len(params) >= 8  # FPS, SPEED, SCALE_X, ENABLED, BG_COLOR, PALETTE, WEIGHTS, COUNTS, POINTS, THRESHOLD

        # Step 2: Create widgets for each param
        widgets = {}
        for p in params:
            w = create_param_widget(p)
            if w is not None:
                widgets[p.name] = (p, w)

        assert "FPS" in widgets
        assert "SPEED" in widgets
        assert "ENABLED" in widgets
        assert "BG_COLOR" in widgets
        assert "PALETTE" in widgets

        # Step 3: Verify initial values match
        assert widgets["FPS"][1].get_value() == 20
        assert abs(widgets["SPEED"][1].get_value() - 0.5) < 0.01
        assert widgets["ENABLED"][1].get_value() is True
        assert widgets["BG_COLOR"][1].get_value() == (0, 0, 0)

        # Step 4: Modify values via widgets
        widgets["FPS"][1].set_value(30)
        widgets["SPEED"][1].set_value(1.0)
        widgets["ENABLED"][1].set_value(False)
        widgets["BG_COLOR"][1].set_value((255, 128, 0))

        # Step 5: Collect values back to params
        for name, (param, widget) in widgets.items():
            param.value = widget.get_value()

        # Step 6: Write config
        write_config(tmp_config, params)

        # Step 7: Re-parse and verify
        params2 = parse_config(tmp_config)
        by_name = {p.name: p for p in params2}

        assert by_name["FPS"].value == 30
        assert abs(by_name["SPEED"].value - 1.0) < 0.01
        assert by_name["ENABLED"].value is False
        assert by_name["BG_COLOR"].value == (255, 128, 0)
        # Unchanged values preserved
        assert by_name["PALETTE"].value == [(255, 0, 0), (0, 255, 0), (0, 0, 255)]

    def test_temp_config_roundtrip(self, qapp, tmp_config, tmp_path):
        params = parse_config(tmp_config)
        by_name = {p.name: p for p in params}
        by_name["FPS"].value = 60

        temp_dir = str(tmp_path / "preview")
        temp_path = write_temp_config(tmp_config, params, temp_dir=temp_dir)

        params2 = parse_config(temp_path)
        by_name2 = {p.name: p for p in params2}
        assert by_name2["FPS"].value == 60

    def test_grouping_real_config(self, tmp_config):
        params = parse_config(tmp_config)
        groups = group_params(params)
        # FPS should be in Timing
        timing_names = {p.name for p in groups.get("Timing", [])}
        assert "FPS" in timing_names
        # BG_COLOR should be in Colors
        color_names = {p.name for p in groups.get("Colors", [])}
        assert "BG_COLOR" in color_names


class TestRealEffectConfigs:
    """Test parsing and widget creation with real effect config files."""

    @pytest.mark.parametrize("effect_name", [
        "Arc Sweep", "Plasma", "Lightning Strike", "Fireflies", "Aurora Borealis",
    ])
    def test_parse_and_create_widgets(self, qapp, effect_name):
        from effects.common import discover_effects
        from config_parser import get_config_path_for_effect

        effects = discover_effects()
        module = effects[effect_name]
        config_path = get_config_path_for_effect(module)
        assert config_path is not None

        params = parse_config(config_path)
        assert len(params) > 0

        for p in params:
            w = create_param_widget(p)
            if p.param_type != "unknown":
                assert w is not None, f"Widget creation failed for {p.name} ({p.param_type})"
                # Verify round-trip
                orig_val = w.get_value()
                w.set_value(orig_val)
                assert w.get_value() == orig_val or (
                    isinstance(orig_val, float) and abs(w.get_value() - orig_val) < 0.01
                ), f"Round-trip failed for {p.name}: {orig_val} != {w.get_value()}"
