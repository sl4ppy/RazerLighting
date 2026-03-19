[← Back to Documentation](../README.md#documentation)

# Getting Started

This guide walks you through installing Razer Lighting, verifying your hardware, and running your first effect. By the end, your keyboard will be running a procedural animation.

## Prerequisites

You need three things:

1. **Linux** — Ubuntu, Fedora, Arch, or any distribution that supports OpenRazer.
2. **OpenRazer** — the open-source driver and daemon for Razer hardware.
3. **A Razer keyboard with per-key RGB** — laptops (Blade 14, Blade 15, etc.) or external keyboards with individually addressable LEDs.

### Install OpenRazer

Follow the instructions for your distribution at [openrazer.github.io/#download](https://openrazer.github.io/#download).

For Ubuntu/Debian:

```bash
sudo add-apt-repository ppa:openrazer/stable
sudo apt update
sudo apt install openrazer-meta
```

For Fedora:

```bash
sudo dnf install openrazer-meta
```

For Arch:

```bash
sudo pacman -S openrazer-daemon openrazer-driver-dkms python-openrazer
```

After installing, add your user to the `plugdev` group and reboot:

```bash
sudo gpasswd -a $USER plugdev
reboot
```

### Verify OpenRazer is running

After rebooting, confirm the daemon is active and your device is detected:

```bash
systemctl --user status openrazer-daemon
```

You should see `active (running)`. If not, start it:

```bash
systemctl --user enable --now openrazer-daemon
```

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/sl4ppy/RazerLighting.git
   cd RazerLighting
   ```

2. Create a virtual environment with system site-packages access:

   ```bash
   python3 -m venv --system-site-packages .venv
   ```

   The `--system-site-packages` flag is required so the venv can access the system-installed `openrazer` Python library and GTK bindings used by the tray icon.

3. Install Python dependencies:

   ```bash
   .venv/bin/pip install pystray Pillow PyQt5 numpy
   ```

   | Package | Purpose |
   |---|---|
   | `pystray` | System tray icon and menu |
   | `Pillow` | Tray icon image generation, GIF capture |
   | `PyQt5` | Configuration GUI window |
   | `numpy` | Fast array math for effects |

## First Run

Start the tray application:

```bash
.venv/bin/python3 razer_lighting.py
```

You should see:

```
Device: Razer Blade 14 (2021)
Effects: Arc Sweep, Aurora Borealis, Binary Cascade, ...
Started: Arc Sweep
```

A green circle icon appears in your system tray. The first effect in alphabetical order starts immediately, and your keyboard lights up.

![System tray menu showing available effects](images/screenshots/SS-001.png)

### If something goes wrong

- **"openrazer Python library not found"** — Your venv cannot access the system openrazer package. Make sure you created it with `--system-site-packages`.
- **"No Razer devices found"** — The OpenRazer daemon isn't running or hasn't detected your device. See [Troubleshooting](troubleshooting.md#no-razer-devices-found).
- **"No Razer device with per-key RGB support found"** — Your device was found but doesn't support the matrix API. Only devices with individually addressable LEDs are supported.

## Using the System Tray Menu

Right-click the green tray icon to access the menu:

![Tray menu with all options](images/screenshots/SS-002.png)

| Menu item | What it does |
|---|---|
| Effect names | Select an effect — a radio indicator shows which one is active |
| **Random** | Pick a random effect |
| **Reload Effect** | Re-import the current effect module from disk (picks up code changes) |
| **Configure...** | Open the configuration GUI (see below) |
| **Start on Login** | Toggle autostart — creates/removes an XDG autostart entry |
| **About...** | Show version and author info |
| **Quit** | Stop the current effect, turn off keyboard LEDs, and exit |

The selected effect is remembered across restarts. If you selected "Random," a new random effect is chosen each time you launch.

## The Configuration GUI

Open **Configure...** from the tray menu to launch the config window:

![Configuration window overview](images/screenshots/SS-003.png)

The window has three main areas:

1. **Effect dropdown** (top) — switch between all effects.
2. **Parameter panel** (left) — auto-generated controls for the selected effect's config file. Parameters are grouped into Timing, Colors, Simulation, and Other categories.
3. **Keyboard visualizer** (right) — a real-time preview of the effect rendered on a realistic Razer Blade keyboard layout.

Changes you make to sliders, color pickers, or checkboxes are immediately visible in the preview. They do **not** affect the real keyboard or the saved config until you click **Save**.

| Button | Action |
|---|---|
| **Save** | Write current values to the effect's `_config.py` file. The running effect picks up changes on its next frame. |
| **Revert to Saved** | Discard unsaved changes and reload from the config file on disk. |
| **Reset to Defaults** | Restore the values that were in the config when the GUI first opened it. |

## Key Concepts

### The keyboard matrix

Your keyboard's LEDs are arranged in a grid called the [matrix](glossary.md#device-matrix). On the Razer Blade 14, this grid is 6 rows by 16 columns:

- **Row 0**: Esc, F1–F12, Ins, Del (function row)
- **Row 1**: \`, 1–0, -, =, Backspace (number row)
- **Row 2**: Tab, Q–P, [, ], \\ (QWERTY top)
- **Row 3**: Caps, A–L, ;, ', Enter (home row)
- **Row 4**: Shift, Z–/, Shift (shift row)
- **Row 5**: Ctrl, Fn, Super, Alt, (space), Alt, Fn, Ctrl, arrows (bottom row)

Effects address keys by `(row, column)` — for example, `matrix[0, 1]` is the Esc key, and `matrix[3, 5]` is the F key on the home row.

### Effects and config files

Each effect is a Python file in the `effects/` directory (e.g., `plasma.py`). Most effects have a companion config file (e.g., `plasma_config.py`) that contains tunable parameters like FPS, speed, and colors.

The config file is a plain Python file with simple variable assignments:

```python
FPS = 20
SPEED = 0.05
COLOR = (255, 0, 0)
```

Effects re-read their config file every frame, so you can edit it in a text editor while the effect is running and see changes instantly. The configuration GUI provides a visual interface for the same purpose.

### How effects work

Every effect follows the same pattern:

1. Loop until told to stop.
2. Each iteration: read config, compute colors for each key, set them in the matrix, call `draw()`.
3. On exit: set all keys to black.

This is the entire API surface — there are no frameworks, event systems, or plugin registries. See [Creating Effects](../CREATING_EFFECTS.md) for the full developer guide.

## Next Steps

- Browse all 28 effects with animated previews: [Effects Guide](../EFFECTS.md)
- Learn the configuration GUI in depth: [Tutorial: Using the Config GUI](tutorials/02-using-the-config-gui.md)
- Write your own effect: [Tutorial: Writing a Custom Effect](tutorials/04-writing-a-custom-effect.md)
- Fix a problem: [Troubleshooting](troubleshooting.md)
