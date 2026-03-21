"""Shared test fixtures for Razer Lighting test suite."""

import os
import sys
import tempfile

import pytest

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(__file__))

# Force offscreen rendering for headless Qt tests
os.environ["QT_QPA_PLATFORM"] = "offscreen"


@pytest.fixture(scope="session")
def qapp():
    """Create a single QApplication for all tests that need Qt."""
    from PyQt5.QtWidgets import QApplication
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
        app.setStyle("Fusion")
        from config_window import DARK_STYLESHEET
        app.setStyleSheet(DARK_STYLESHEET)
    return app


@pytest.fixture
def virtual_device():
    """Create a VirtualDevice for testing."""
    from virtual_device import VirtualDevice
    return VirtualDevice(rows=6, cols=16)


@pytest.fixture
def tmp_config(tmp_path):
    """Create a temporary config file for testing."""
    config = tmp_path / "test_config.py"
    config.write_text(
        "FPS = 20\n"
        "SPEED = 0.5\n"
        "SCALE_X = 0.3\n"
        "ENABLED = True\n"
        'BG_COLOR = (0, 0, 0)\n'
        "PALETTE = [\n"
        "    (255, 0, 0),\n"
        "    (0, 255, 0),\n"
        "    (0, 0, 255),\n"
        "]\n"
        "WEIGHTS = [0.5, 0.3, 0.2]\n"
        "COUNTS = [1, 5, 10]\n"
        "POINTS = [(1, 2), (3, 4)]\n"
        "THRESHOLD = 0.5  # detection threshold\n"
    )
    return str(config)
