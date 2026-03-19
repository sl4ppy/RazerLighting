[← Back to Documentation](../README.md#documentation)

# Troubleshooting & FAQ

Solutions to common problems with Razer Lighting. If your issue isn't covered here, open an issue on [GitHub](https://github.com/sl4ppy/RazerLighting/issues).

---

## Installation Problems

### "openrazer Python library not found"

**Cause:** The Python virtual environment cannot access the system-installed `openrazer` package.

**Fix:** Recreate the venv with the `--system-site-packages` flag:

```bash
rm -rf .venv
python3 -m venv --system-site-packages .venv
.venv/bin/pip install pystray Pillow PyQt5 numpy
```

If you already have a venv without system packages, you cannot retroactively enable it — you must recreate it.

### "No module named 'pystray'" (or Pillow, PyQt5, numpy)

**Cause:** Dependencies weren't installed into the venv.

**Fix:**

```bash
.venv/bin/pip install pystray Pillow PyQt5 numpy
```

Make sure you use `.venv/bin/pip`, not the system `pip`.

### PyQt5 fails to install via pip

**Cause:** On some Linux distributions, PyQt5 wheels are not available or require system libraries.

**Fix:** Install PyQt5 from your distribution's package manager instead:

```bash
# Ubuntu/Debian
sudo apt install python3-pyqt5

# Fedora
sudo dnf install python3-qt5

# Arch
sudo pacman -S python-pyqt5
```

Then recreate the venv with `--system-site-packages` so it can access the system-installed PyQt5.

---

## Device Connection

### "No Razer devices found. Is openrazer-daemon running?"

**Cause:** The OpenRazer daemon isn't running or hasn't started yet.

**Fix:**

1. Check the daemon status:

   ```bash
   systemctl --user status openrazer-daemon
   ```

2. If it's not running, start and enable it:

   ```bash
   systemctl --user enable --now openrazer-daemon
   ```

3. If it fails to start, check that you're in the `plugdev` group:

   ```bash
   groups
   ```

   If `plugdev` is missing:

   ```bash
   sudo gpasswd -a $USER plugdev
   ```

   Then log out and back in (or reboot).

### "No Razer device with per-key RGB support found"

**Cause:** Your Razer device was detected but doesn't support the matrix API (individually addressable LEDs). Zone-based lighting devices are not supported.

**Check:** The error message lists your detected devices and whether they have matrix support. If your device shows `matrix: no`, it uses zone-based lighting and cannot be controlled per-key.

### Device not detected after boot / sleep

**Cause:** The OpenRazer daemon sometimes loses connection to the device after a suspend/resume cycle, or the USB bus re-enumerates.

**Fix:** Restart the daemon:

```bash
systemctl --user restart openrazer-daemon
```

Then restart Razer Lighting. The application retries device connection up to 10 times with 3-second intervals on startup, so a brief delay after resume is usually handled automatically.

### Connection works but Razer Lighting exits immediately

**Cause:** The daemon is running but the device hasn't been registered yet. This can happen if Razer Lighting starts before the daemon finishes initializing (e.g., at login).

**Fix:** The app retries 10 times with 3-second delays by default. If your system is particularly slow to initialize, try starting the app manually after login, or increase the retry count in `device.py`.

---

## Effects

### Effect runs but keyboard stays dark

**Possible causes:**

1. **Brightness is set to zero** in Razer's own configuration. Check:

   ```bash
   # If you have polychromatic or razer-cli installed:
   razer-cli -l
   ```

   Set brightness to 100% using your Razer's built-in Fn+brightness keys.

2. **Another application is controlling the keyboard.** Close Polychromatic, Razer Synapse (if running under Wine), or any other RGB control software.

3. **The effect crashed silently.** Check the terminal where you launched `razer_lighting.py` for error output.

### Effect is choppy or laggy

**Cause:** CPU load is too high, or the FPS is set too high for the effect's computational complexity.

**Fix:**

1. Lower the FPS in the effect's config file or config GUI. Most effects run well at 15–24 FPS.
2. Close other CPU-intensive applications.
3. Check if numpy is installed — effects without numpy fall back to pure Python loops, which are much slower:

   ```bash
   .venv/bin/python3 -c "import numpy; print(numpy.__version__)"
   ```

### Effect doesn't appear in the tray menu

**Possible causes:**

1. **Missing `run()` function.** Every effect must have a `run(device, stop_event)` function.
2. **Import error.** The effect file has a syntax error or imports a module that isn't available. Check the terminal — skipped effects print a warning:

   ```
   Skipping my_effect.py: ModuleNotFoundError: No module named 'foo'
   ```

3. **File ends in `_config.py`.** Config files are excluded from discovery.
4. **File starts with `__`.** Files starting with double underscores are excluded.

### Config changes don't take effect

**Possible causes:**

1. **The config file has a syntax error.** The effect falls back to cached values when `load_config()` fails. Check the terminal for `Config load error` messages.
2. **You edited the wrong file.** Make sure you're editing the file in the `effects/` directory, not a copy elsewhere.
3. **The config GUI hasn't saved yet.** Changes in the GUI only affect the preview until you click **Save**.

---

## Configuration GUI

### Config window shows "No configurable parameters"

**Cause:** The selected effect doesn't have a config file, or the config file contains no parseable assignments.

**Check:** Look for a `<effect_name>_config.py` file in the `effects/` directory. The config parser only recognizes simple top-level assignments with literal values (`int`, `float`, `bool`, `tuple`, `list`).

### Color picker doesn't open / crashes

**Cause:** Missing Qt5 platform plugin or display server issue.

**Fix:** Make sure you have the Qt5 platform plugins installed:

```bash
# Ubuntu/Debian
sudo apt install qt5-gtk-platformtheme

# Fedora
sudo dnf install qt5-qtbase-gui
```

### Keyboard visualizer shows wrong layout

**Cause:** The visualizer is hardcoded to the Razer Blade 14 (2021) keyboard layout. If you have a different Razer keyboard, keys may not align perfectly with the visual layout.

**Note:** The matrix coordinates and colors are still correct — only the visual representation of key shapes and positions may differ. Effects render correctly regardless of the visualizer layout.

---

## Autostart

### "Start on Login" doesn't work

**Possible causes:**

1. **Your desktop environment doesn't support XDG autostart.** The toggle creates a `.desktop` file in `~/.config/autostart/`. This works on GNOME, KDE, XFCE, and most other desktop environments.

2. **The venv path changed.** The autostart entry uses an absolute path to the venv's Python interpreter. If you move the project directory, toggle autostart off and back on to regenerate the path.

3. **OpenRazer daemon isn't ready at login time.** The app retries device connection 10 times (30 seconds total). If your system takes longer than that, the app gives up. You can increase the retry parameters in `device.py:get_device()`.

### How do I remove autostart manually?

Delete the autostart file:

```bash
rm ~/.config/autostart/razer-lighting.desktop
```

---

## General

### LEDs stay on after quitting

**Cause:** The app clears the keyboard on a normal quit, but if it crashes or is killed with `kill -9`, the last frame stays on the keyboard.

**Fix:** Restart and quit the app normally, or restart the OpenRazer daemon:

```bash
systemctl --user restart openrazer-daemon
```

### Can I run multiple effects simultaneously?

No. The app runs one effect at a time. Selecting a new effect stops the previous one. The keyboard hardware has a single RGB buffer — there's no built-in layer blending.

### Does this work on Wayland?

Yes, but system tray support varies by compositor. GNOME on Wayland requires the [AppIndicator extension](https://extensions.gnome.org/extension/615/appindicator-support/) for tray icons. KDE Plasma supports tray icons natively on Wayland.

The configuration GUI (PyQt5) works on both X11 and Wayland.

### Can I use this alongside Polychromatic?

Not simultaneously. Both applications write to the same device matrix. Run one at a time. If Polychromatic has set a static color and you start Razer Lighting, the effect will immediately overwrite it.

### How do I uninstall?

1. Toggle off "Start on Login" from the tray menu (or manually `rm ~/.config/autostart/razer-lighting.desktop`).
2. Delete the project directory.
3. Optionally remove saved state: `rm -rf ~/.local/state/razer-lighting`.
