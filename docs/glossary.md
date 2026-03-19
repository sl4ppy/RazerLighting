[← Back to Documentation](../README.md#documentation)

# Glossary

Terms used throughout Razer Lighting documentation, the configuration GUI, and effect config files.

---

### AST (Abstract Syntax Tree)

A structured representation of Python source code. Razer Lighting uses AST parsing to read and write config files while preserving formatting, comments, and structure. You never interact with this directly — it powers the config GUI behind the scenes.

### Config file

A Python file ending in `_config.py` that contains parameter assignments for an effect (e.g., `plasma_config.py`). These files are re-read automatically when modified, enabling hot-reload. See [User Reference > Config Files](user-reference.md#config-files).

### Device matrix

The grid of individually addressable LEDs on your keyboard, accessed through OpenRazer. On the Razer Blade 14, this is 6 rows × 16 columns. Each cell is addressed by `(row, column)` coordinates starting from `(0, 0)` at the top-left corner (Esc key area).

### Draw call

A call to `device.fx.advanced.draw()` that pushes the current color buffer to the keyboard hardware. Each draw call updates all LEDs simultaneously. Effects typically issue one draw call per frame.

### Effect

A Python module in the `effects/` directory that implements a lighting animation. Each effect has an `EFFECT_NAME` string and a `run(device, stop_event)` function. See [Creating Effects](../CREATING_EFFECTS.md).

### Effect discovery

The process by which `razer_lighting.py` scans the `effects/` directory on startup (and on each menu open) to find all valid effect modules. Files ending in `_config.py` and files starting with `__` are excluded.

### FPS (Frames Per Second)

The number of times per second an effect updates the keyboard LEDs. Most effects default to 15–30 FPS. Higher values produce smoother animation but use more CPU. Configurable per-effect via the `FPS` parameter.

### Frame

A single complete update of all keyboard LEDs. One frame = one draw call. The frame buffer is the in-memory array of RGB values that gets sent to the keyboard.

### Hot-reload

The ability to change config file values while an effect is running and see changes take effect on the next frame, without restarting anything. Powered by `load_config()` in `effects/common.py`, which checks file modification time before re-reading.

### HSV (Hue, Saturation, Value)

A color model where Hue is the color angle (0–360°), Saturation is color intensity (0–1), and Value is brightness (0–1). Some effects use HSV internally for color calculations, though the keyboard API and config files use RGB.

### Keyboard layout

The physical arrangement of keys on the keyboard, used by the configuration GUI visualizer and GIF capture tool to render a realistic preview. Defined in `keyboard_layout.py` as a list of key positions with labels, matrix column mappings, and widths.

### Laplacian

A mathematical operator that measures how much a value at a point differs from its neighbors. Used in effects like Heat Diffusion and Reaction-Diffusion to simulate how quantities spread across the grid. Available as `laplacian_4pt()`, `laplacian_9pt()`, and `laplacian_4pt_open()` in `effects/common.py`.

### LUT (Lookup Table)

A precomputed array that maps input values to output colors. `build_palette_lut()` creates a 256-entry table from a palette, allowing fast vectorized color mapping via `palette_lookup()`. See [User Reference > Shared Utilities](user-reference.md#shared-utilities-effectscommonpy).

### Matrix coordinates

The `(row, column)` address of a key in the device matrix. Row 0 is the function key row (Esc, F1–F12), row 5 is the bottom row (Ctrl, Fn, Super, Space area). Columns run left to right, typically 0–15.

### OpenRazer

An open-source Linux driver and daemon for Razer hardware. Provides a D-Bus interface and Python library for controlling device features including per-key RGB lighting. Required for Razer Lighting to communicate with your keyboard. [openrazer.github.io](https://openrazer.github.io/)

### Palette

An ordered list of RGB color tuples that defines a gradient. Effects sample along this gradient to convert scalar values (like temperature, wave amplitude, or distance) into colors. Palettes are editable in the config GUI using the palette editor widget.

### Per-key RGB

The ability to set each key's LED to an independent color, as opposed to zone-based lighting where groups of keys share a single color. Requires hardware with a "matrix" LED controller and OpenRazer's `fx.advanced` API.

### Procedural generation

Creating visual patterns algorithmically rather than from pre-recorded sequences. Every effect in Razer Lighting is procedural — it computes each frame from mathematical functions, simulations, or particle systems, so the pattern never exactly repeats.

### RGB (Red, Green, Blue)

The color model used by keyboard LEDs. Each channel ranges from 0 (off) to 255 (full brightness). Written as tuples: `(255, 0, 0)` = red, `(0, 255, 0)` = green, `(0, 0, 255)` = blue.

### Stop event

A `threading.Event` object passed to every effect's `run()` function. When the event is set (by the tray app or a Ctrl+C signal), the effect must exit its main loop and clean up. See [Creating Effects > The Effect Contract](../CREATING_EFFECTS.md#the-effect-contract).

### System tray

The notification area in your desktop panel (GNOME, KDE, etc.) where Razer Lighting displays its green circle icon. Right-clicking the icon opens the menu for selecting effects, opening the config window, and other actions.

### Toroidal wrapping

A boundary condition where the grid wraps around: the right edge connects to the left edge, and the bottom connects to the top. Used in grid simulations (Laplacian, blur) so patterns flow seamlessly across boundaries without hard edges.

### Virtual device

A software emulation of the OpenRazer device API (`virtual_device.py`) used by the configuration window for live preview. It captures each draw call and forwards the frame data to the keyboard visualizer widget.

### Venv (Virtual Environment)

A Python virtual environment created with `python3 -m venv`. Razer Lighting uses `--system-site-packages` so the venv can access the system-installed `openrazer` Python library while keeping other dependencies isolated.
