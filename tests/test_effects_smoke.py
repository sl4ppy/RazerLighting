"""Smoke tests — run every effect on a virtual device for ~0.5s, verify no crashes."""

import threading
import time

import pytest

from effects.common import discover_effects
from virtual_device import VirtualDevice


def _run_effect_briefly(module, duration=0.5):
    """Run an effect for a short time and return (frames_drawn, error)."""
    frames = []
    error = [None]

    def on_draw(snapshot):
        frames.append(snapshot)

    dev = VirtualDevice(rows=6, cols=16, on_draw=on_draw)
    stop = threading.Event()

    def target():
        try:
            module.run(dev, stop)
        except Exception as e:
            error[0] = e

    t = threading.Thread(target=target, daemon=True)
    t.start()
    time.sleep(duration)
    stop.set()
    t.join(timeout=3)

    return len(frames), error[0], t.is_alive()


class TestAllEffectsSmoke:
    """Smoke-test each of the 28 effects."""

    @pytest.fixture(scope="class")
    def all_effects(self):
        return discover_effects()

    def test_effect_count(self, all_effects):
        assert len(all_effects) == 28

    @pytest.mark.parametrize("effect_name", sorted(discover_effects().keys()))
    def test_effect_runs(self, effect_name):
        effects = discover_effects()
        module = effects[effect_name]
        frame_count, error, hung = _run_effect_briefly(module, duration=0.5)

        assert not hung, f"{effect_name} did not stop within 3s after stop_event"
        assert error is None, f"{effect_name} raised: {error}"
        assert frame_count > 0, f"{effect_name} produced 0 frames in 0.5s"

    @pytest.mark.parametrize("effect_name", sorted(discover_effects().keys()))
    def test_effect_has_config(self, effect_name):
        """Every built-in effect should have a config file."""
        effects = discover_effects()
        module = effects[effect_name]
        assert hasattr(module, "CONFIG_PATH"), f"{effect_name} missing CONFIG_PATH"

        import os
        assert os.path.exists(module.CONFIG_PATH), \
            f"{effect_name} CONFIG_PATH doesn't exist: {module.CONFIG_PATH}"

    @pytest.mark.parametrize("effect_name", sorted(discover_effects().keys()))
    def test_effect_config_parseable(self, effect_name):
        """Every config file should parse without errors."""
        from config_parser import parse_config

        effects = discover_effects()
        module = effects[effect_name]
        if not hasattr(module, "CONFIG_PATH"):
            pytest.skip("No CONFIG_PATH")

        params = parse_config(module.CONFIG_PATH)
        assert len(params) > 0, f"{effect_name} config has no parameters"
