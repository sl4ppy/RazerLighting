# Creating Effects

This guide covers everything you need to write your own keyboard lighting effect. Effects are plain Python scripts — no framework to learn, no special tooling required.

## Minimal Example

Create `effects/my_effect.py`:

```python
import time

EFFECT_NAME = "My Effect"

def run(device, stop_event):
    rows = device.fx.advanced.rows   # 6 on Razer Blade 14
    cols = device.fx.advanced.cols   # 16
    matrix = device.fx.advanced.matrix

    t = 0
    while not stop_event.is_set():
        for r in range(rows):
            for c in range(cols):
                red = int((1 + __import__('math').sin(t + c * 0.5)) * 127)
                matrix[r, c] = (red, 0, 255 - red)
        device.fx.advanced.draw()
        t += 0.1
        time.sleep(1.0 / 20)

    # Clear keyboard on exit
    for r in range(rows):
        for c in range(cols):
            matrix[r, c] = (0, 0, 0)
    device.fx.advanced.draw()
```

That's it. Save the file, and it appears in the system tray menu.

## The Effect Contract

Your effect file needs exactly two things:

1. **`EFFECT_NAME`** — a string displayed in the tray menu
2. **`run(device, stop_event)`** — called in a background thread when the effect starts

The `run` function must:
- Loop until `stop_event.is_set()` returns `True`
- Set pixel colors via `device.fx.advanced.matrix[row, col] = (r, g, b)`
- Call `device.fx.advanced.draw()` to push each frame
- Clean up (set all keys to black) before returning

## Device API

```python
rows = device.fx.advanced.rows      # number of key rows (6)
cols = device.fx.advanced.cols      # number of key columns (16)
matrix = device.fx.advanced.matrix  # the pixel buffer

matrix[row, col] = (r, g, b)       # set a key color (0-255 each)
device.fx.advanced.draw()           # push the frame to the keyboard
```

The grid is 6 rows x 16 columns. Row 0 is the top (Esc/F-keys), row 5 is the bottom (Ctrl/Space).

## Shared Utilities

The `effects/common.py` module provides helpers that eliminate boilerplate and improve performance. All are optional — use what you need.

### Frame rendering

```python
from effects.common import draw_frame, clear_keyboard

# draw_frame takes a numpy array of shape (rows, cols, 3) uint8
import numpy as np
frame = np.zeros((rows, cols, 3), dtype=np.uint8)
frame[:, :, 0] = 255  # all red
draw_frame(device, frame)

# clear_keyboard sets all keys to black
clear_keyboard(device)
```

### Timing

```python
from effects.common import frame_sleep

next_frame = time.monotonic()
while not stop_event.is_set():
    # ... render frame ...
    next_frame, dt = frame_sleep(next_frame, 1.0 / 20)  # 20 FPS
```

`frame_sleep` uses deadline-based timing instead of `time.sleep(interval)`, preventing frame drift. It returns `(next_deadline, dt)` where `dt` is the actual elapsed time since the previous frame. Use `dt` to make animation speed independent of frame rate:

```python
fps = cfg.get("FPS", 20)
interval = 1.0 / fps
# ...
next_frame, dt = frame_sleep(next_frame, interval)
t += dt * fps  # advances by 1.0 at target FPS, more when behind
```

This ensures effects run at the same visual speed regardless of whether `draw()` is fast or slow (e.g. after a reboot or driver change).

### Palette colors

```python
from effects.common import build_palette_lut, palette_lookup, sample_palette

palette = [(0, 0, 0), (255, 0, 0), (255, 255, 0), (255, 255, 255)]

# For numpy arrays (fast, vectorized):
lut = build_palette_lut(palette)           # 256-entry lookup table
values = np.random.rand(rows, cols)        # float array in [0, 1]
frame_rgb = palette_lookup(lut, values)    # (rows, cols, 3) uint8

# For single values:
r, g, b = sample_palette(palette, 0.5)    # returns (255, 128, 0)
```

### Grid math

```python
from effects.common import (
    make_coordinate_grids,   # (row_grid, col_grid) for vectorized per-pixel math
    laplacian_4pt,           # 4-neighbor Laplacian, toroidal wrapping
    laplacian_4pt_open,      # 4-neighbor Laplacian, zero boundaries
    laplacian_9pt,           # weighted 9-point Laplacian, toroidal
    blur_3x3,               # 3x3 box blur, toroidal wrapping
)
```

### Config loading

```python
from effects.common import load_config

cfg = load_config(CONFIG_PATH)
speed = cfg.get("SPEED", 1.0)  # second arg is the default
```

`load_config` caches by file mtime — it only re-reads when the file actually changes.

### Standalone entry point

```python
from effects.common import standalone_main

def main():
    standalone_main(EFFECT_NAME, run)

if __name__ == "__main__":
    main()
```

This lets you run your effect directly with `python3 effects/my_effect.py` for testing.

## Hot-Reloadable Config

To make your effect configurable at runtime, create a companion config file. If your effect is `my_effect.py`, create `my_effect_config.py`:

```python
FPS = 20
SPEED = 1.0
COLOR = (255, 0, 0)
```

Then load it each frame in your effect:

```python
import os
from effects.common import load_config

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "my_effect_config.py")

def run(device, stop_event):
    while not stop_event.is_set():
        cfg = load_config(CONFIG_PATH)
        fps = cfg.get("FPS", 20)
        speed = cfg.get("SPEED", 1.0)
        color = cfg.get("COLOR", (255, 0, 0))
        # ... use these values ...
```

Edit the config file while the effect is running and changes apply on the next frame. The config GUI also auto-detects your parameters and generates sliders, color pickers, and other controls for them.

### Config parameter types

The config GUI infers control types from your default values:

| Python type | GUI control |
|---|---|
| `int` or `float` | Slider / spinbox |
| `bool` | Checkbox |
| `(r, g, b)` tuple | Color picker |
| List of `(r, g, b)` | Palette editor |

## Complete Example

Here's a full effect with config, numpy rendering, and all the recommended patterns:

**`effects/rainbow_scroll.py`:**

```python
#!/usr/bin/env python3
"""Rainbow Scroll - a scrolling rainbow gradient across the keyboard."""

import math
import os
import time

import numpy as np

from effects.common import (
    load_config, draw_frame, clear_keyboard, frame_sleep,
    build_palette_lut, palette_lookup, make_coordinate_grids,
    standalone_main,
)

EFFECT_NAME = "Rainbow Scroll"
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "rainbow_scroll_config.py")


def run(device, stop_event):
    rows = device.fx.advanced.rows
    cols = device.fx.advanced.cols
    row_grid, col_grid = make_coordinate_grids(rows, cols)

    t = 0.0
    next_frame = time.monotonic()

    while not stop_event.is_set():
        cfg = load_config(CONFIG_PATH)
        fps = cfg.get("FPS", 20)
        speed = cfg.get("SPEED", 0.05)
        scale = cfg.get("SCALE", 0.3)
        palette = cfg.get("PALETTE", [
            (255, 0, 0), (255, 127, 0), (255, 255, 0),
            (0, 255, 0), (0, 0, 255), (127, 0, 255), (255, 0, 0),
        ])

        lut = build_palette_lut(palette)

        # Compute a scrolling gradient using column position + time
        values = (col_grid * scale + row_grid * 0.1 + t) % 1.0
        frame_rgb = palette_lookup(lut, values)
        draw_frame(device, frame_rgb)

        next_frame, dt = frame_sleep(next_frame, 1.0 / fps)
        t = (t + speed * dt * fps) % 1.0

    clear_keyboard(device)


def main():
    standalone_main(EFFECT_NAME, run)


if __name__ == "__main__":
    main()
```

**`effects/rainbow_scroll_config.py`:**

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
    (127, 0, 255),
    (255, 0, 0),
]
```

## Capturing GIFs

You can capture a preview GIF of your effect for documentation:

```bash
python3 capture_gif.py my_effect 8         # 8-second capture
python3 capture_gif.py my_effect 5 FPS=30  # with config overrides
```

GIFs are saved to `screenshots/`.

## Tips

- **Start simple.** Get pixels on screen first, then add complexity.
- **Use numpy** for anything that touches every pixel. A Python loop over 96 keys is fine; nested math per pixel is not.
- **Always provide defaults** with `cfg.get("KEY", default)` so the effect works even without a config file.
- **Name your config file** `<effect_name>_config.py` — files ending in `_config.py` are excluded from effect discovery.
- **Test standalone** with `python3 effects/my_effect.py` before running through the tray app.
- Look at existing effects for inspiration — `plasma.py` is a clean sine-wave example, `heat_diffusion.py` shows grid simulation, `lightning_strike.py` demonstrates event-driven timing.
