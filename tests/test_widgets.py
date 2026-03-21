"""Tests for config_widgets.py — widget factory, value round-trips, all types."""

import pytest

from config_parser import ConfigParam
from config_widgets import (
    create_param_widget, IntParamWidget, FloatParamWidget,
    BoolParamWidget, ColorParamWidget, PaletteWidget,
    FloatListWidget, IntListWidget, TupleListWidget, ColorButton,
    LABEL_WIDTH,
)


def _make_param(name, value, ptype, rmin=0, rmax=100, rstep=1):
    return ConfigParam(
        name=name, value=value, param_type=ptype, line_number=1,
        range_min=rmin, range_max=rmax, range_step=rstep, tooltip="test",
    )


# ── Factory ──────────────────────────────────────────────────────────────────

class TestFactory:
    def test_int(self, qapp):
        w = create_param_widget(_make_param("FPS", 20, "int", 1, 60, 1))
        assert isinstance(w, IntParamWidget)

    def test_float(self, qapp):
        w = create_param_widget(_make_param("SPEED", 0.5, "float", 0, 1, 0.01))
        assert isinstance(w, FloatParamWidget)

    def test_bool(self, qapp):
        w = create_param_widget(_make_param("ENABLED", True, "bool"))
        assert isinstance(w, BoolParamWidget)

    def test_rgb(self, qapp):
        w = create_param_widget(_make_param("COLOR", (255, 0, 0), "rgb"))
        assert isinstance(w, ColorParamWidget)

    def test_palette(self, qapp):
        w = create_param_widget(_make_param("PAL", [(255, 0, 0), (0, 255, 0)], "palette"))
        assert isinstance(w, PaletteWidget)

    def test_float_list(self, qapp):
        w = create_param_widget(_make_param("W", [0.5, 0.3], "float_list"))
        assert isinstance(w, FloatListWidget)

    def test_int_list(self, qapp):
        w = create_param_widget(_make_param("C", [1, 2], "int_list"))
        assert isinstance(w, IntListWidget)

    def test_tuple_list(self, qapp):
        w = create_param_widget(_make_param("P", [(1, 2), (3, 4)], "tuple_list"))
        assert isinstance(w, TupleListWidget)

    def test_unknown_returns_none(self, qapp):
        w = create_param_widget(_make_param("X", "hello", "unknown"))
        assert w is None


# ── Value Round-Trips ────────────────────────────────────────────────────────

class TestIntWidget:
    def test_get_initial(self, qapp):
        w = IntParamWidget(_make_param("FPS", 20, "int", 1, 60, 1))
        assert w.get_value() == 20

    def test_set_get(self, qapp):
        w = IntParamWidget(_make_param("FPS", 20, "int", 1, 60, 1))
        w.set_value(42)
        assert w.get_value() == 42

    def test_slider_sync(self, qapp):
        w = IntParamWidget(_make_param("FPS", 20, "int", 1, 60, 1))
        w.set_value(30)
        assert w.slider.value() == 30
        assert w.spin.value() == 30


class TestFloatWidget:
    def test_get_initial(self, qapp):
        w = FloatParamWidget(_make_param("SPEED", 0.5, "float", 0.0, 1.0, 0.01))
        assert abs(w.get_value() - 0.5) < 0.01

    def test_set_get(self, qapp):
        w = FloatParamWidget(_make_param("SPEED", 0.5, "float", 0.0, 1.0, 0.01))
        w.set_value(0.75)
        assert abs(w.get_value() - 0.75) < 0.01

    def test_boundary_values(self, qapp):
        w = FloatParamWidget(_make_param("X", 0.0, "float", 0.0, 1.0, 0.01))
        w.set_value(0.0)
        assert w.get_value() == 0.0
        w.set_value(1.0)
        assert w.get_value() == 1.0


class TestBoolWidget:
    def test_get_true(self, qapp):
        w = BoolParamWidget(_make_param("E", True, "bool"))
        assert w.get_value() is True

    def test_get_false(self, qapp):
        w = BoolParamWidget(_make_param("E", False, "bool"))
        assert w.get_value() is False

    def test_set_toggle(self, qapp):
        w = BoolParamWidget(_make_param("E", True, "bool"))
        w.set_value(False)
        assert w.get_value() is False
        w.set_value(True)
        assert w.get_value() is True


class TestColorWidget:
    def test_get_initial(self, qapp):
        w = ColorParamWidget(_make_param("C", (255, 128, 0), "rgb"))
        assert w.get_value() == (255, 128, 0)

    def test_set_get(self, qapp):
        w = ColorParamWidget(_make_param("C", (0, 0, 0), "rgb"))
        w.set_value((100, 200, 50))
        assert w.get_value() == (100, 200, 50)


class TestPaletteWidget:
    def test_get_initial(self, qapp):
        pal = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
        w = PaletteWidget(_make_param("P", pal, "palette"))
        assert w.get_value() == pal

    def test_set_get(self, qapp):
        w = PaletteWidget(_make_param("P", [(0, 0, 0)], "palette"))
        new_pal = [(255, 255, 255), (128, 128, 128)]
        w.set_value(new_pal)
        assert w.get_value() == new_pal


class TestFloatListWidget:
    def test_get_initial(self, qapp):
        w = FloatListWidget(_make_param("W", [0.5, 0.3, 0.2], "float_list"))
        vals = w.get_value()
        assert len(vals) == 3
        assert abs(vals[0] - 0.5) < 0.01

    def test_set_get(self, qapp):
        w = FloatListWidget(_make_param("W", [1.0], "float_list"))
        w.set_value([0.1, 0.9])
        vals = w.get_value()
        assert len(vals) == 2


class TestIntListWidget:
    def test_get_initial(self, qapp):
        w = IntListWidget(_make_param("C", [1, 5, 10], "int_list"))
        assert w.get_value() == [1, 5, 10]

    def test_set_get(self, qapp):
        w = IntListWidget(_make_param("C", [1], "int_list"))
        w.set_value([10, 20])
        assert w.get_value() == [10, 20]


class TestTupleListWidget:
    def test_get_initial(self, qapp):
        w = TupleListWidget(_make_param("P", [(1, 2), (3, 4)], "tuple_list"))
        assert w.get_value() == [(1, 2), (3, 4)]


# ── ColorButton ──────────────────────────────────────────────────────────────

class TestColorButton:
    def test_initial_color(self, qapp):
        btn = ColorButton((128, 64, 32))
        assert btn.get_color() == (128, 64, 32)

    def test_set_color(self, qapp):
        btn = ColorButton((0, 0, 0))
        btn.set_color((255, 128, 0))
        assert btn.get_color() == (255, 128, 0)


# ── Label Width ──────────────────────────────────────────────────────────────

class TestConstants:
    def test_label_width(self):
        assert LABEL_WIDTH == 130
