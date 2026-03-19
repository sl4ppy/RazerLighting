[← Back to Documentation](../README.md#documentation)

# User Reference

Complete reference for all Razer Lighting features, configuration options, and APIs.

---

## Table of Contents

- [System Tray Application](#system-tray-application)
- [Effects](#effects)
- [Config Files](#config-files)
- [Configuration GUI](#configuration-gui)
- [Device API](#device-api)
- [Shared Utilities (effects/common.py)](#shared-utilities-effectscommonpy)
- [GIF Capture Tool](#gif-capture-tool)
- [File and Directory Reference](#file-and-directory-reference)
- [State and Data Locations](#state-and-data-locations)

---

## System Tray Application

**File:** `razer_lighting.py`

The main entry point. Runs a [system tray](glossary.md#system-tray) icon with a right-click menu for controlling effects.

### Launch

```bash
.venv/bin/python3 razer_lighting.py
```

On startup, the app:

1. Connects to the OpenRazer daemon (retries up to 10 times, 3 seconds apart).
2. Scans the `effects/` directory for valid effect modules.
3. Restores the last selected effect from `~/.local/state/razer-lighting/last-effect`.
4. Displays a green circle icon in the system tray.

### Tray Menu Items

| Item | Action |
|---|---|
| *Effect names* (radio) | Start the selected effect. A radio indicator marks the active one. |
| **Random** (radio) | Pick a random effect. Re-randomizes on each restart if "Random" was the last selection. |
| **Reload Effect** | Stop the current effect, re-import its module from disk, and restart it. Picks up code changes without restarting the app. |
| **Configure...** | Launch the configuration GUI as a separate process. |
| **Start on Login** (checkbox) | Toggle XDG autostart. Creates or removes `~/.config/autostart/razer-lighting.desktop`. |
| **About...** | Open the about dialog showing version, author, and GitHub link. |
| **Quit** | Stop the effect, clear all keyboard LEDs to black, and exit. |

### Effect Discovery

The app scans `effects/` for `.py` files that:
- Do **not** end in `_config.py`
- Do **not** start with `__`
- Have a `run()` function

The effect's display name comes from the `EFFECT_NAME` module attribute. If absent, the filename is converted from `snake_case` to `Title Case`.

Discovery runs on startup and again each time the tray menu opens, so new effects appear without restarting.

### Last-Effect Persistence

The selected effect (or "Random") is saved to `~/.local/state/razer-lighting/last-effect` as a plain text file. On next launch, the app restores this selection.

---

## Effects

28 procedural effects are included. See the [Effects Guide](../EFFECTS.md) for descriptions, animated previews, and config parameters for each one.

### Effect Contract

Every effect module must provide:

| Attribute | Type | Purpose |
|---|---|---|
| `EFFECT_NAME` | `str` | Display name shown in the tray menu |
| `run(device, stop_event)` | function | Main loop, called in a background thread |

Optional:

| Attribute | Type | Purpose |
|---|---|---|
| `CONFIG_PATH` | `str` | Absolute path to the effect's config file |

The `run()` function must:
1. Loop until `stop_event.is_set()` returns `True`.
2. Set key colors via `device.fx.advanced.matrix[row, col] = (r, g, b)`.
3. Call `device.fx.advanced.draw()` once per frame.
4. Clear the keyboard (all keys to black) before returning.

### Standalone Execution

Any effect can be run directly without the tray app:

```bash
.venv/bin/python3 effects/plasma.py
```

This connects to OpenRazer directly and runs the effect until you press Ctrl+C. Useful for testing and development.

---

## Config Files

**Location:** `effects/<effect_name>_config.py`

Config files are plain Python files containing variable assignments. They are re-read by effects on every frame using `load_config()`, which caches by file modification time.

### Supported Parameter Types

| Python value | Inferred type | GUI control |
|---|---|---|
| `42` (int) | `int` | Slider + spinbox |
| `0.5` (float) | `float` | Slider + spinbox |
| `True` / `False` | `bool` | Checkbox |
| `(255, 0, 0)` (3-int tuple, 0–255) | `rgb` | Color swatch + picker dialog |
| `[(255, 0, 0), (0, 255, 0)]` (list of RGB tuples) | `palette` | Palette editor (row of color swatches, +/- buttons) |
| `[0.1, 0.5, 0.9]` (list of floats) | `float_list` | Row of spinboxes, +/- buttons |
| `[1, 5, 10]` (list of ints) | `int_list` | Row of spinboxes, +/- buttons |
| `[(1, 2), (3, 4)]` (list of tuples) | `tuple_list` | Editable table |

### Range Inference

The config parser infers slider min/max/step from the variable name and current value:

| Name pattern | Inferred range |
|---|---|
| `FPS` | 1–60, step 1 |
| Contains `CHANCE`, `BLEND`, `AMOUNT`, `DENSITY` | 0.0–1.0 (float) or 0–100 (int) |
| Ends with `_X`, `_Y`, `_FADE` | 0.0–1.0 if current value is in that range |
| Contains `SPEED`, `RATE` | 0 to 5× current value |
| Starts with `NUM_`, `MAX_` | 1 to 5× current value (int) |
| Contains `SCALE`, `RATIO` | 0.01 to 5× current value |
| Contains `WIDTH`, `RADIUS`, `DIST` | 0 to 5× current value |

### Tooltips

Parameters have tooltips derived from three sources (checked in order):

1. **Specific tooltip registry** — hand-written descriptions in `config_parser.py:PARAM_TOOLTIPS` keyed by `(config_basename, PARAM_NAME)`.
2. **Generic name-based tooltips** — common names like `FPS`, `BG_COLOR`, `PALETTE` have default descriptions.
3. **Inline comment** — the `# comment` on the same line as the assignment.

### Parameter Grouping

The config GUI groups parameters into categories:

| Group | Matching name tokens |
|---|---|
| **Timing** | FPS, SPEED, MIN, MAX, INTERVAL, FREQ, PAUSE, GAP, FRAMES |
| **Colors** | Any parameter of type `rgb` or `palette` |
| **Simulation** | RATE, STEPS, THRESHOLD, CHANCE, DENSITY, COOLING, DAMPING, DIFFUSION, COUPLING, AMPLITUDE, DECAY, DEPOSIT, FEED, KILL |
| **Other** | Everything else |

### Example Config File

```python
FPS = 20
SPEED = 0.05
SCALE = 0.3

PALETTE = [
    (255, 0, 0),
    (255, 127, 0),
    (255, 255, 0),
    (0, 255, 0),
    (0, 0, 255),
]
```

### Editing Config Files Manually

You can edit config files in any text editor while effects are running. Changes take effect on the next frame (typically within 50ms). The config parser preserves file structure, comments, and formatting when writing back through the GUI.

Variables starting with `_` are ignored by the parser. Use this for internal constants you don't want exposed in the GUI.

---

## Configuration GUI

**File:** `config_window.py`

A PyQt5 window for visually editing effect parameters with real-time preview.

### Launch

Launched from the tray menu via **Configure...**, or directly:

```bash
.venv/bin/python3 config_window.py [effect_name]
```

The optional `effect_name` argument pre-selects an effect (e.g., `Plasma`).

### Window Layout

| Area | Description |
|---|---|
| **Effect dropdown** (top) | Select which effect to configure. Switching effects prompts to save unsaved changes. |
| **Parameter panel** (left, scrollable) | Auto-generated widgets grouped by category. |
| **Keyboard visualizer** (right) | Live effect preview on a realistic keyboard layout. |
| **Button bar** (bottom) | Save, Revert to Saved, Reset to Defaults. |

### Parameter Widgets

| Widget | Used for | Controls |
|---|---|---|
| Slider + spinbox | `int`, `float` | Drag slider or type exact value |
| Checkbox | `bool` | Toggle on/off |
| Color swatch | `rgb` | Click to open Qt color picker; shows hex value |
| Palette editor | `palette` | Row of color swatches; + adds a color, - removes the last |
| Spinbox row | `float_list`, `int_list` | Row of value spinboxes; + adds an entry, - removes the last |
| Editable table | `tuple_list` | Spreadsheet-style table of values |

### Live Preview

The visualizer runs the effect on a [virtual device](glossary.md#virtual-device) in a background thread. Parameter changes are debounced (100ms) and written to a temporary config file in `/tmp/razer-lighting-preview/`. The preview thread reads from this temp file, not the real config.

Changes in the preview do not affect the running effect on your keyboard until you click **Save**.

### Keyboard Visualizer

The visualizer renders the Razer Blade 14 keyboard layout with:
- Physically accurate key positions, sizes, and gaps
- Per-key colors from the preview effect
- Optional key labels (toggle via button below the visualizer)
- Adaptive scaling to fill the available space

### Window Settings

Window geometry (position and size) is saved between sessions via Qt's `QSettings` at `~/.config/RazerLighting/ConfigWindow.conf`.

---

## Device API

The device object passed to `run()` provides the OpenRazer matrix API:

### Properties

| Property | Type | Description |
|---|---|---|
| `device.name` | `str` | Device name (e.g., "Razer Blade 14 (2021)") |
| `device.fx.advanced.rows` | `int` | Number of matrix rows (6 on Blade 14) |
| `device.fx.advanced.cols` | `int` | Number of matrix columns (16 on Blade 14) |
| `device.fx.advanced.matrix` | matrix object | The color buffer; supports `[row, col]` indexing |

### Operations

| Operation | Syntax | Description |
|---|---|---|
| Set key color | `device.fx.advanced.matrix[r, c] = (R, G, B)` | Set a single key's color. R, G, B are 0–255. |
| Read key color | `color = device.fx.advanced.matrix[r, c]` | Returns `(R, G, B)` tuple. |
| Push frame | `device.fx.advanced.draw()` | Send the current buffer to the keyboard hardware. |

### Matrix Layout (Razer Blade 14)

```
       Col: 0    1    2    3    4    5    6    7    8    9   10   11   12   13   14   15
Row 0: [--] [Esc] [F1] [F2] [F3] [F4] [F5] [F6] [F7] [F8] [F9] [F10][F11][F12][Ins][Del]
Row 1: [--] [ ` ] [ 1] [ 2] [ 3] [ 4] [ 5] [ 6] [ 7] [ 8] [ 9] [ 0] [ -] [ =] [--] [Bk]
Row 2: [--] [Tab] [ Q] [ W] [ E] [ R] [ T] [ Y] [ U] [ I] [ O] [ P] [ [] [ ]] [--] [ \]
Row 3: [--] [Cap] [ A] [ S] [ D] [ F] [ G] [ H] [ J] [ K] [ L] [ ;] [ '] [--] [--] [Ent]
Row 4: [--] [Shf] [--] [ Z] [ X] [ C] [ V] [ B] [ N] [ M] [ ,] [ .] [ /] [--] [--] [Shf]
Row 5: [--] [Ctl] [Fn] [Sup][--] [Alt][--] [--] [--] [Alt] [Fn] [Ctl] [ ←] [ ↑] [ →] [ ↓]
```

Column 0 is unused (legacy macro column). Physical keys use columns 1–15. `[--]` indicates no LED at that position. The spacebar has no LED on the Blade 14.

---

## Shared Utilities (effects/common.py)

A library of helper functions used by effects. All are optional — import only what you need.

### Config Loading

```python
from effects.common import load_config

cfg = load_config(CONFIG_PATH)
speed = cfg.get("SPEED", 1.0)    # returns default if key missing
```

`load_config(path)` reads a Python config file via `exec()`. It caches results by file mtime — the file is only re-read when its modification time changes.

### Frame Rendering

```python
from effects.common import draw_frame, clear_keyboard

# draw_frame: write a numpy (rows, cols, 3) uint8 array to the device
draw_frame(device, frame_rgb)

# clear_keyboard: set all keys to (0, 0, 0) and draw
clear_keyboard(device)
```

### Timing

```python
from effects.common import frame_sleep, wait_interruptible

# Deadline-based frame timing (prevents drift)
next_frame, dt = frame_sleep(next_frame, 1.0 / fps)

# Interruptible sleep (returns early if stop_event is set)
still_running = wait_interruptible(seconds, stop_event)
```

`frame_sleep()` returns `(next_deadline, dt)` where `dt` is the actual elapsed time since the previous frame, capped at 3× the interval to handle system suspend/resume gracefully. Use `dt` to make animation speed independent of frame rate.

### Palette Utilities

```python
from effects.common import build_palette_lut, palette_lookup, sample_palette

palette = [(0, 0, 0), (255, 0, 0), (255, 255, 0), (255, 255, 255)]

# Vectorized: build a 256-entry LUT, then map a float array to RGB
lut = build_palette_lut(palette)
rgb_array = palette_lookup(lut, float_array)  # float_array in [0, 1]

# Single value: sample one color at position t (0–1)
r, g, b = sample_palette(palette, 0.5)
```

### Color Helpers

```python
from effects.common import lerp_color

# Linear interpolation between two RGB tuples
color = lerp_color((255, 0, 0), (0, 0, 255), 0.5)  # → (127, 0, 127)
```

### Grid Math

```python
from effects.common import (
    make_coordinate_grids,    # (row_grid, col_grid) numpy arrays
    laplacian_4pt,            # 4-neighbor Laplacian, toroidal wrapping
    laplacian_4pt_open,       # 4-neighbor Laplacian, zero boundaries
    laplacian_9pt,            # weighted 9-point Laplacian, toroidal
    blur_3x3,                 # 3x3 box blur, toroidal wrapping
)
```

| Function | Description |
|---|---|
| `make_coordinate_grids(rows, cols)` | Returns `(row_grid, col_grid)` float64 arrays for vectorized per-pixel position math. |
| `laplacian_4pt(grid)` | Sum of 4 orthogonal neighbors minus 4× center. Wraps toroidally. |
| `laplacian_4pt_open(grid)` | Same as above but with zero (open) boundaries. |
| `laplacian_9pt(grid)` | Weighted 9-point stencil (0.2 for orthogonal, 0.05 for diagonal). Wraps toroidally. |
| `blur_3x3(grid)` | Simple 3×3 box blur. Wraps toroidally. |

### Standalone Entry Point

```python
from effects.common import standalone_main

def main():
    standalone_main(EFFECT_NAME, run)

if __name__ == "__main__":
    main()
```

Handles device connection, signal handling (Ctrl+C), and the run loop.

---

## GIF Capture Tool

**File:** `capture_gif.py`

Records an effect as an animated GIF using the virtual device and PIL rendering.

### Usage

```bash
python3 capture_gif.py <effect_name> [duration_secs] [key=value ...]
```

### Parameters

| Parameter | Default | Description |
|---|---|---|
| `effect_name` | (required) | Effect module filename without `.py` (e.g., `lightning_strike`) |
| `duration_secs` | `5.0` | How long to record |
| `key=value` | (none) | Config overrides appended to the config file for this capture |

### Examples

```bash
# Capture plasma for 5 seconds with default config
python3 capture_gif.py plasma

# Capture lightning strike for 8 seconds with faster intervals
python3 capture_gif.py lightning_strike 8 INTERVAL_MIN=0.3 INTERVAL_MAX=1.0

# Capture with custom FPS
python3 capture_gif.py heat_diffusion 6 FPS=30
```

### Output

GIFs are saved to `screenshots/<effect_name>.gif`. The tool:
- Limits output to 80 frames maximum (downsamples if more are captured).
- Sets frame duration to 50ms (20 FPS playback).
- Renders the keyboard layout matching the configuration window visualizer.

---

## File and Directory Reference

| Path | Purpose |
|---|---|
| `razer_lighting.py` | System tray application entry point |
| `config_window.py` | PyQt5 configuration GUI |
| `config_parser.py` | AST-based config file parsing, type inference, and write-back |
| `virtual_device.py` | Virtual OpenRazer device for preview rendering |
| `device.py` | OpenRazer device connection with retry logic |
| `capture_gif.py` | Animated GIF capture tool |
| `about_window.py` | About dialog |
| `effects/` | Effect modules directory |
| `effects/common.py` | Shared utilities library |
| `effects/<name>.py` | Individual effect module |
| `effects/<name>_config.py` | Effect configuration (hot-reloadable) |
| `screenshots/` | Captured GIF previews |
| `assets/avatar.gif` | Avatar image for the About dialog |

---

## State and Data Locations

| Path | Purpose |
|---|---|
| `~/.local/state/razer-lighting/last-effect` | Last selected effect name (plain text) |
| `~/.local/state/razer-lighting/defaults/` | Cached default parameter values per effect (JSON) |
| `~/.config/autostart/razer-lighting.desktop` | XDG autostart entry (created by "Start on Login") |
| `~/.config/RazerLighting/ConfigWindow.conf` | Config window geometry (Qt settings) |
| `/tmp/razer-lighting-preview/` | Temporary config files used by the live preview |
