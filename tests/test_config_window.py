"""Tests for config_window.py — UI components, gallery, metadata, visualizer."""

import pytest

from config_window import (
    ConfigWindow, EffectCard, EffectGallery, CollapsibleGroup,
    KeyboardVisualizer, EFFECT_CATEGORIES, EFFECT_DESCRIPTIONS,
    CATEGORY_ICONS, _get_category, DARK_STYLESHEET,
)
from effects.common import discover_effects


# ── Effect Metadata Consistency ──────────────────────────────────────────────

class TestEffectMetadata:
    def test_all_effects_categorized(self):
        effects = discover_effects()
        categorized = set()
        for names in EFFECT_CATEGORIES.values():
            categorized.update(names)
        uncategorized = set(effects.keys()) - categorized
        assert uncategorized == set(), f"Uncategorized effects: {uncategorized}"

    def test_no_phantom_categories(self):
        effects = discover_effects()
        categorized = set()
        for names in EFFECT_CATEGORIES.values():
            categorized.update(names)
        phantoms = categorized - set(effects.keys())
        assert phantoms == set(), f"Effects in categories but not discovered: {phantoms}"

    def test_all_effects_have_descriptions(self):
        effects = discover_effects()
        for name in effects:
            assert name in EFFECT_DESCRIPTIONS, f"Missing description for: {name}"

    def test_no_empty_descriptions(self):
        for name, desc in EFFECT_DESCRIPTIONS.items():
            assert len(desc) > 10, f"Description too short for {name}: '{desc}'"

    def test_five_categories(self):
        assert len(EFFECT_CATEGORIES) == 5
        assert set(EFFECT_CATEGORIES.keys()) == {"Organic", "Atmospheric", "Mathematical", "Glitch", "Kinetic"}

    def test_all_categories_have_icons(self):
        for cat in EFFECT_CATEGORIES:
            assert cat in CATEGORY_ICONS, f"Missing icon for category: {cat}"

    def test_get_category(self):
        assert _get_category("Plasma") == "Mathematical"
        assert _get_category("Fireflies") == "Organic"
        assert _get_category("Glitch") == "Glitch"
        assert _get_category("Arc Sweep") == "Kinetic"
        assert _get_category("Aurora Borealis") == "Atmospheric"

    def test_get_category_unknown(self):
        assert _get_category("NonexistentEffect") == "Other"


# ── Stylesheet ───────────────────────────────────────────────────────────────

class TestStylesheet:
    def test_not_empty(self):
        assert len(DARK_STYLESHEET) > 1000

    def test_uses_razer_green(self):
        assert "#44D62C" in DARK_STYLESHEET

    def test_no_old_teal(self):
        assert "#00cc88" not in DARK_STYLESHEET
        assert "#00ffaa" not in DARK_STYLESHEET
        assert "#00cc00" not in DARK_STYLESHEET

    def test_has_key_selectors(self):
        assert "effectCard" in DARK_STYLESHEET
        assert "filterBtn" in DARK_STYLESHEET
        assert "searchField" in DARK_STYLESHEET
        assert "saveButton" in DARK_STYLESHEET
        assert "vizPanel" in DARK_STYLESHEET
        assert "paramPanel" in DARK_STYLESHEET


# ── EffectCard ───────────────────────────────────────────────────────────────

class TestEffectCard:
    def test_creation(self, qapp):
        card = EffectCard("Plasma")
        assert card.effect_name == "Plasma"
        assert card.isCheckable()

    def test_check_state(self, qapp):
        card = EffectCard("Plasma")
        card.setChecked(True)
        assert card.isChecked()
        card.setChecked(False)
        assert not card.isChecked()


# ── EffectGallery ────────────────────────────────────────────────────────────

class TestEffectGallery:
    def test_creation(self, qapp):
        effects = discover_effects()
        gallery = EffectGallery(list(effects.keys()))
        assert len(gallery._cards) == 28

    def test_select_effect(self, qapp):
        gallery = EffectGallery(["Plasma", "Glitch", "Aurora Borealis"])
        gallery.select_effect("Glitch")
        assert gallery._cards["Glitch"].isChecked()
        assert not gallery._cards["Plasma"].isChecked()

    def test_filter_by_text(self, qapp):
        gallery = EffectGallery(["Plasma", "Glitch", "Aurora Borealis"])
        gallery.show()
        gallery._filter_cards("plasma")
        assert gallery._cards["Plasma"].isVisible()
        assert not gallery._cards["Glitch"].isVisible()
        gallery.close()

    def test_filter_clear(self, qapp):
        gallery = EffectGallery(["Plasma", "Glitch"])
        gallery.show()
        gallery._filter_cards("plasma")
        gallery._filter_cards("")
        assert gallery._cards["Plasma"].isVisible()
        assert gallery._cards["Glitch"].isVisible()
        gallery.close()

    def test_category_filter(self, qapp):
        effects = discover_effects()
        gallery = EffectGallery(list(effects.keys()))
        gallery.show()
        gallery._set_filter("Glitch")
        # Only glitch effects visible
        for name, card in gallery._cards.items():
            if _get_category(name) == "Glitch":
                assert card.isVisible(), f"{name} should be visible"
            else:
                assert not card.isVisible(), f"{name} should be hidden"
        gallery.close()


# ── CollapsibleGroup ─────────────────────────────────────────────────────────

class TestCollapsibleGroup:
    def test_creation(self, qapp):
        g = CollapsibleGroup("TIMING")
        assert not g._collapsed

    def test_toggle(self, qapp):
        g = CollapsibleGroup("TIMING")
        g._toggle()
        assert g._collapsed
        g._toggle()
        assert not g._collapsed


# ── KeyboardVisualizer ───────────────────────────────────────────────────────

class TestKeyboardVisualizer:
    def test_creation(self, qapp):
        v = KeyboardVisualizer()
        assert v.rows == 6
        assert v.cols == 16
        assert v._show_labels is True

    def test_toggle_labels(self, qapp):
        v = KeyboardVisualizer()
        v.toggle_labels()
        assert v._show_labels is False
        v.toggle_labels()
        assert v._show_labels is True

    def test_update_frame(self, qapp):
        v = KeyboardVisualizer()
        frame = [[(i * 10, j * 10, 0) for j in range(16)] for i in range(6)]
        v._update_frame(frame)
        assert v._frame[0][0] == (0, 0, 0)
        assert v._frame[1][1] == (10, 10, 0)

    def test_has_key_rects(self, qapp):
        v = KeyboardVisualizer()
        assert len(v._key_rects) > 50


# ── ConfigWindow ─────────────────────────────────────────────────────────────

class TestConfigWindow:
    def test_creation(self, qapp):
        w = ConfigWindow()
        assert w._current_effect_name is not None
        assert len(w.effects) == 28
        w.preview.cleanup()

    def test_initial_state(self, qapp):
        w = ConfigWindow()
        assert w._dirty is False
        assert w._current_config_path is not None
        assert "Razer Lighting" in w.windowTitle()
        w.preview.cleanup()

    def test_has_gallery(self, qapp):
        w = ConfigWindow()
        assert hasattr(w, "gallery")
        assert len(w.gallery._cards) == 28
        w.preview.cleanup()

    def test_has_status_bar(self, qapp):
        w = ConfigWindow()
        assert w.status_bar is not None
        w.preview.cleanup()

    def test_has_visualizer(self, qapp):
        w = ConfigWindow()
        assert w.visualizer is not None
        assert isinstance(w.visualizer, KeyboardVisualizer)
        w.preview.cleanup()

    def test_effect_change(self, qapp):
        w = ConfigWindow()
        w._on_effect_changed("Plasma")
        assert w._current_effect_name == "Plasma"
        assert "Plasma" in w.windowTitle()
        w.preview.cleanup()

    def test_dirty_flag(self, qapp):
        w = ConfigWindow()
        w._set_dirty(True)
        assert w._dirty is True
        assert "\u2022" in w.windowTitle()  # bullet
        w._set_dirty(False)
        assert w._dirty is False
        w.preview.cleanup()

    def test_initial_effect_arg(self, qapp):
        w = ConfigWindow(initial_effect="Plasma")
        assert w._current_effect_name == "Plasma"
        w.preview.cleanup()
