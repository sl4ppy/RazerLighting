# Razer Lighting

Custom keyboard lighting effects for Razer laptops on Linux, powered by [OpenRazer](https://openrazer.github.io/). A system tray app with **27 procedural effects** that never repeat — no Polychromatic needed.

![Plasma effect](screenshots/plasma.gif)

<p align="center">
  <img src="screenshots/metaballs.gif" width="49%" />
  <img src="screenshots/arc_sweep.gif" width="49%" />
</p>

> Every effect is procedurally generated and runs indefinitely. See all 27 with animated previews in the **[Effects Guide](EFFECTS.md)**.

## Features

- **27 procedural effects** — from physics simulations to demoscene classics, each infinitely unique
- **Plain Python scripts** — every effect is a simple `.py` file; easy to read, modify, and create your own
- **Live configuration GUI** — tune every parameter with sliders, color pickers, and a real-time keyboard preview
- **Hot-reloadable configs** — edit `_config.py` files while effects run; changes apply instantly
- **System tray integration** — select effects, randomize, toggle autostart, all from the tray icon
- **Auto-discovery** — drop a new `.py` file in `effects/` and it appears in the menu automatically
- **Write your own** — see the **[Creating Effects Guide](CREATING_EFFECTS.md)** to build custom effects

## Getting Started

### Requirements

- Linux with [OpenRazer](https://openrazer.github.io/) daemon installed
- Razer keyboard or laptop with per-key RGB (matrix) support
- Python 3.10+

### Install & Run

```bash
git clone https://github.com/sl4ppy/RazerLighting.git
cd RazerLighting
python3 -m venv --system-site-packages .venv
.venv/bin/pip install pystray Pillow
.venv/bin/python3 razer_lighting.py
```

The `--system-site-packages` flag is required for access to the system-installed `openrazer` and GTK libraries.

## Configuration

Open **Configure...** from the tray menu to launch the configuration window:

![Configuration window](screenshots/wave_interference.gif)

- **Effect selector** — switch between all 27 effects from the dropdown
- **Auto-generated controls** — sliders, spinboxes, color pickers, palette editors, and checkboxes inferred from each effect's config
- **Live keyboard preview** — realistic Razer Blade layout renders the effect in real time as you tweak
- **Tooltips** — hover over any parameter for a description of what it does
- **Save / Revert / Defaults** — changes only affect the preview until you Save

Effects can also be run standalone: `.venv/bin/python3 effects/arc_sweep.py`

## Adding Effects

Every effect is a plain Python script — no framework, no boilerplate. Drop a `.py` file in `effects/` with an `EFFECT_NAME` string and a `run(device, stop_event)` function, and it appears in the tray menu automatically.

```python
EFFECT_NAME = "My Effect"

def run(device, stop_event):
    while not stop_event.is_set():
        # Set colors and draw
        device.fx.advanced.matrix[0, 0] = (255, 0, 0)
        device.fx.advanced.draw()
```

See the **[Creating Effects Guide](CREATING_EFFECTS.md)** for a complete walkthrough with examples, shared utilities, config files, and tips.

## Project Structure

```
razer_lighting.py            System tray app
config_window.py             PyQt5 configuration GUI with live preview
config_parser.py             AST-based config file parsing & writing
virtual_device.py            Virtual device for preview rendering
device.py                    OpenRazer device connection with retry
effects/
  ├── arc_sweep.py           Effect module (27 total)
  ├── arc_sweep_config.py    Hot-reloadable config
  └── ...
```

## Support

<a href="https://www.buymeacoffee.com/chrisvd"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" height="40" /></a>

## License

MIT
