# Razer Lighting

Custom keyboard lighting effects for Razer laptops on Linux, powered by [OpenRazer](https://openrazer.github.io/). Runs as a system tray app with hot-reloadable, procedurally generated effects — no Polychromatic needed.

## Effects

| Effect | Description |
|--------|-------------|
| **Arc Sweep** | Arcs of light sweep across the keyboard from random directions with variable speed and trailing fade. Multiple arcs can overlap simultaneously. |
| **Lightning Strike** | Procedural lightning bolts strike from top to bottom with zigzag paths, purple branches, restrikes, and teal surge flickers. Mimics natural thunderstorm rhythm. |

All effects are procedurally generated — they never repeat the same pattern twice.

## Installation

### Requirements

- Linux with [OpenRazer](https://openrazer.github.io/) daemon installed
- A Razer keyboard/laptop with per-key RGB (matrix) support
- Python 3.10+

### Setup

```bash
git clone <repo-url> ~/Projects/RazerLighting
cd ~/Projects/RazerLighting
python3 -m venv --system-site-packages .venv
.venv/bin/pip install pystray
```

The `--system-site-packages` flag is required so the venv can access the system-installed `openrazer` and GTK libraries.

## Usage

### Tray App

```bash
.venv/bin/python3 razer_lighting.py
```

A system tray icon appears with a menu to:
- **Select an effect** from all discovered effects
- **Reload Effect** — re-import the current effect module from disk
- **Start on Login** — toggle XDG autostart
- **Quit** — stop the effect, clear the keyboard, and exit

### Standalone Effects

Each effect can also be run directly:

```bash
.venv/bin/python3 effects/arc_sweep.py
.venv/bin/python3 effects/lightning_strike.py
```

### Hot Reload

Each effect has a companion `_config.py` file that is re-read from disk while the effect is running. Edit the config and see changes on the next cycle — no restart needed.

## Adding New Effects

Drop a `.py` file in `effects/` with this interface:

```python
EFFECT_NAME = "My Effect"

def run(device, stop_event):
    """Main loop. Render frames until stop_event is set."""
    rows = device.fx.advanced.rows
    cols = device.fx.advanced.cols
    matrix = device.fx.advanced.matrix

    while not stop_event.is_set():
        # Set pixels: matrix[row, col] = (r, g, b)
        # Flush frame: device.fx.advanced.draw()
        # Pace: time.sleep(1.0 / fps)
        pass

    # Clean up on exit
    for r in range(rows):
        for c in range(cols):
            matrix[r, c] = (0, 0, 0)
    device.fx.advanced.draw()
```

The tray app auto-discovers new effects when you open its menu. Files ending in `_config.py` are ignored.

## Project Structure

```
├── razer_lighting.py            # System tray app
├── device.py                    # OpenRazer device connection (with retry)
├── effects/
│   ├── arc_sweep.py             # Arc Sweep effect
│   ├── arc_sweep_config.py      # Arc Sweep config (hot-reloadable)
│   ├── lightning_strike.py      # Lightning Strike effect
│   └── lightning_strike_config.py
└── .venv/                       # Python virtual environment
```

## License

MIT
