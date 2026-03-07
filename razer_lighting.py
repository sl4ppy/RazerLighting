#!/usr/bin/env python3
"""Razer Lighting - system tray app for custom keyboard lighting effects."""

import importlib.util
import os
import signal
import sys
import threading

import pystray
from PIL import Image, ImageDraw

from device import get_device

APP_NAME = "Razer Lighting"
EFFECTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "effects")
AUTOSTART_DIR = os.path.expanduser("~/.config/autostart")
AUTOSTART_FILE = os.path.join(AUTOSTART_DIR, "razer-lighting.desktop")


def create_icon_image():
    """Generate a simple 64x64 tray icon — green Razer-style circle."""
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([4, 4, 60, 60], fill=(0, 255, 0, 255))
    draw.ellipse([16, 16, 48, 48], fill=(0, 0, 0, 255))
    draw.ellipse([24, 24, 40, 40], fill=(0, 200, 0, 255))
    return img


def discover_effects():
    """Find all effect modules in the effects directory."""
    effects = {}
    for filename in sorted(os.listdir(EFFECTS_DIR)):
        if filename.endswith("_config.py") or filename.startswith("__"):
            continue
        if not filename.endswith(".py"):
            continue
        path = os.path.join(EFFECTS_DIR, filename)
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


class RazerLightingApp:
    def __init__(self):
        self.device = get_device()
        self.effects = discover_effects()
        self.current_effect_name = None
        self.effect_thread = None
        self.stop_event = threading.Event()
        self.icon = None

        print(f"Device: {self.device.name}")
        print(f"Effects: {', '.join(self.effects.keys())}")

    def start_effect(self, name):
        """Stop any running effect and start the named one."""
        self.stop_current()
        if name not in self.effects:
            return
        self.current_effect_name = name
        self.stop_event.clear()
        module = self.effects[name]
        self.effect_thread = threading.Thread(
            target=module.run,
            args=(self.device, self.stop_event),
            daemon=True,
        )
        self.effect_thread.start()
        print(f"Started: {name}")
        self._update_menu()

    def stop_current(self):
        """Stop the currently running effect."""
        if self.effect_thread and self.effect_thread.is_alive():
            self.stop_event.set()
            self.effect_thread.join(timeout=3)
        self.effect_thread = None

    def reload_effect(self):
        """Reload the current effect module from disk and restart it."""
        if not self.current_effect_name:
            return
        name = self.current_effect_name
        # Re-discover to pick up code changes
        self.effects = discover_effects()
        self.start_effect(name)
        print(f"Reloaded: {name}")

    def is_autostart_enabled(self):
        return os.path.exists(AUTOSTART_FILE)

    def toggle_autostart(self):
        if self.is_autostart_enabled():
            os.remove(AUTOSTART_FILE)
            print("Autostart disabled")
        else:
            os.makedirs(AUTOSTART_DIR, exist_ok=True)
            script_path = os.path.abspath(__file__)
            venv_python = os.path.join(os.path.dirname(script_path), ".venv", "bin", "python3")
            python = venv_python if os.path.exists(venv_python) else sys.executable
            with open(AUTOSTART_FILE, "w") as f:
                f.write(f"""[Desktop Entry]
Type=Application
Name={APP_NAME}
Exec={python} {script_path}
Icon=input-keyboard
Terminal=false
X-GNOME-Autostart-enabled=true
Comment=Custom Razer keyboard lighting effects
""")
            print("Autostart enabled")
        self._update_menu()

    def quit(self):
        self.stop_current()
        # Clear keyboard
        try:
            rows = self.device.fx.advanced.rows
            cols = self.device.fx.advanced.cols
            for r in range(rows):
                for c in range(cols):
                    self.device.fx.advanced.matrix[r, c] = (0, 0, 0)
            self.device.fx.advanced.draw()
        except Exception:
            pass
        if self.icon:
            self.icon.stop()

    def _make_effect_action(self, name):
        def action(icon, item):
            self.start_effect(name)
        return action

    def _build_menu(self):
        # Rescan effects directory every time the menu is built
        self.effects = discover_effects()

        effect_items = []
        for name in self.effects:
            effect_items.append(
                pystray.MenuItem(
                    name,
                    self._make_effect_action(name),
                    checked=lambda item, n=name: self.current_effect_name == n,
                    radio=True,
                )
            )

        def do_reload(icon, item):
            self.reload_effect()

        def do_toggle_autostart(icon, item):
            self.toggle_autostart()

        def do_quit(icon, item):
            self.quit()

        return pystray.Menu(
            *effect_items,
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Reload Effect", do_reload),
            pystray.MenuItem(
                "Start on Login",
                do_toggle_autostart,
                checked=lambda item: self.is_autostart_enabled(),
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", do_quit),
        )

    def _update_menu(self):
        if self.icon:
            self.icon.menu = self._build_menu()
            self.icon.update_menu()

    def run(self):
        self.icon = pystray.Icon(
            "razer-lighting",
            create_icon_image(),
            APP_NAME,
            self._build_menu(),
        )
        # Auto-start the first effect
        if self.effects:
            first = next(iter(self.effects))
            self.start_effect(first)
        self.icon.run()


def main():
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = RazerLightingApp()
    app.run()


if __name__ == "__main__":
    main()
