#!/usr/bin/env python3
"""Razer Lighting - system tray app for custom keyboard lighting effects."""

import os
import random
import signal
import subprocess
import sys
import threading

import pystray
from PIL import Image, ImageDraw

from device import get_device
from effects.common import clear_keyboard, discover_effects

APP_NAME = "Razer Lighting"
AUTOSTART_DIR = os.path.expanduser("~/.config/autostart")
AUTOSTART_FILE = os.path.join(AUTOSTART_DIR, "razer-lighting.desktop")
STATE_DIR = os.path.expanduser("~/.local/state/razer-lighting")
STATE_FILE = os.path.join(STATE_DIR, "last-effect")
RANDOM_CHOICE = "Random"


def create_icon_image():
    """Generate a simple 64x64 tray icon — green Razer-style circle."""
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([4, 4, 60, 60], fill=(0, 255, 0, 255))
    draw.ellipse([16, 16, 48, 48], fill=(0, 0, 0, 255))
    draw.ellipse([24, 24, 40, 40], fill=(0, 200, 0, 255))
    return img


def save_last_effect(name):
    """Persist the selected effect name to disk."""
    os.makedirs(STATE_DIR, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        f.write(name)


def load_last_effect():
    """Load the last selected effect name from disk."""
    try:
        with open(STATE_FILE) as f:
            return f.read().strip()
    except FileNotFoundError:
        return None


class RazerLightingApp:
    def __init__(self):
        self.device = get_device()
        self.effects = discover_effects()
        self.current_effect_name = None
        self.selected_choice = None  # tracks menu selection (effect name or RANDOM_CHOICE)
        self.effect_thread = None
        self.stop_event = threading.Event()
        self.icon = None

        print(f"Device: {self.device.name}")
        print(f"Effects: {', '.join(self.effects.keys())}")

    def start_effect(self, name, choice=None):
        """Stop any running effect and start the named one.

        choice is what the user selected (effect name or RANDOM_CHOICE).
        """
        self.stop_current()
        if name not in self.effects:
            return
        self.current_effect_name = name
        self.selected_choice = choice or name
        save_last_effect(self.selected_choice)
        self.stop_event.clear()
        module = self.effects[name]
        self.effect_thread = threading.Thread(
            target=self._run_effect_safe,
            args=(module, self.device, self.stop_event),
            daemon=True,
        )
        self.effect_thread.start()
        print(f"Started: {name}" + (" (random)" if self.selected_choice == RANDOM_CHOICE else ""))
        self._update_menu()

    def _run_effect_safe(self, module, device, stop_event):
        """Run an effect, catching crashes to avoid silent thread death."""
        try:
            module.run(device, stop_event)
        except Exception as e:
            print(f"Effect crashed: {e}", file=sys.stderr)
            try:
                clear_keyboard(device)
            except Exception:
                pass

    def stop_current(self):
        """Stop the currently running effect."""
        if self.effect_thread and self.effect_thread.is_alive():
            self.stop_event.set()
            self.effect_thread.join(timeout=3)
        self.effect_thread = None

    def open_config_window(self):
        """Open the configuration window as a separate process.

        Launched as a subprocess because the tray uses pystray (GTK on Linux)
        and the config window uses PyQt5.  GTK and Qt event loops cannot
        coexist in the same process without careful integration, so a
        separate process is the cleanest approach.
        """
        script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config_window.py")
        effect = self.current_effect_name or ""
        subprocess.Popen([sys.executable, script, effect])

    def open_about(self):
        """Open the about dialog as a separate process."""
        script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "about_window.py")
        subprocess.Popen([sys.executable, script])

    def reload_effect(self):
        """Reload the current effect module from disk and restart it."""
        if not self.current_effect_name:
            return
        name = self.current_effect_name
        choice = self.selected_choice
        # Re-discover to pick up code changes
        self.effects = discover_effects()
        self.start_effect(name, choice=choice)
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

    def _start_random(self):
        """Pick a random effect and start it."""
        if self.effects:
            name = random.choice(list(self.effects.keys()))
            self.start_effect(name, choice=RANDOM_CHOICE)

    def _build_menu(self):
        # Rescan effects directory every time the menu is built
        self.effects = discover_effects()

        effect_items = []
        for name in self.effects:
            effect_items.append(
                pystray.MenuItem(
                    name,
                    self._make_effect_action(name),
                    checked=lambda item, n=name: self.selected_choice == n,
                    radio=True,
                )
            )

        def do_random(icon, item):
            self._start_random()

        def do_reload(icon, item):
            self.reload_effect()

        def do_configure(icon, item):
            self.open_config_window()

        def do_toggle_autostart(icon, item):
            self.toggle_autostart()

        def do_about(icon, item):
            self.open_about()

        def do_quit(icon, item):
            self.quit()

        return pystray.Menu(
            *effect_items,
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                RANDOM_CHOICE,
                do_random,
                checked=lambda item: self.selected_choice == RANDOM_CHOICE,
                radio=True,
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Reload Effect", do_reload),
            pystray.MenuItem("Configure...", do_configure),
            pystray.MenuItem(
                "Start on Login",
                do_toggle_autostart,
                checked=lambda item: self.is_autostart_enabled(),
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("About...", do_about),
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
        # Restore last selection on startup
        last = load_last_effect()
        if last == RANDOM_CHOICE:
            self._start_random()
        elif last and last in self.effects:
            self.start_effect(last)
        elif self.effects:
            first = next(iter(self.effects))
            self.start_effect(first)
        self.icon.run()


def main():
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = RazerLightingApp()
    app.run()


if __name__ == "__main__":
    main()
