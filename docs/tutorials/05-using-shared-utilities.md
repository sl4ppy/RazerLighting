[← Back to Tutorials](index.md) | [← Back to Documentation](../../README.md#documentation)

# Using the Shared Utilities

Use the `effects/common.py` library for palette rendering, numpy-accelerated frame output, and grid math.

## What you'll accomplish

You will refactor the Rainbow Scroll effect from [Tutorial 4](04-writing-a-custom-effect.md) to use numpy arrays, palette LUTs, and coordinate grids — making it faster, shorter, and easier to extend.

## Prerequisites

- Completed [Tutorial 4](04-writing-a-custom-effect.md) (Rainbow Scroll effect exists).
- Basic familiarity with numpy arrays.

## Estimated time

15 minutes.

## Steps

### Step 1: Understand the performance problem

The Rainbow Scroll effect from Tutorial 4 uses a Python `for` loop over every key:

```python
for r in range(rows):
    for c in range(cols):
        hue = (c * spread + r * 0.05 + t) % 1.0
        matrix[r, c] = hsv_to_rgb(hue, saturation, brightness)
```

For 96 keys (6 × 16), this is fast enough. But more complex effects — especially those with per-pixel math like noise functions or physics simulations — need vectorized numpy operations to maintain smooth frame rates.

### Step 2: Add palette-based rendering

1. Update `effects/rainbow_scroll_config.py` to include a palette:

   ```python
   FPS = 20
   SPEED = 0.02
   SPREAD = 0.06

   PALETTE = [
       (255, 0, 0),       # red
       (255, 127, 0),     # orange
       (255, 255, 0),     # yellow
       (0, 255, 0),       # green
       (0, 0, 255),       # blue
       (127, 0, 255),     # violet
       (255, 0, 0),       # red (wrap-around for smooth looping)
   ]
   ```

2. Rewrite `effects/rainbow_scroll.py` using palette utilities:

   ```python
   #!/usr/bin/env python3
   """Rainbow Scroll - scrolling rainbow gradient using palette LUT."""

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
           speed = cfg.get("SPEED", 0.02)
           spread = cfg.get("SPREAD", 0.06)
           palette = cfg.get("PALETTE", [
               (255, 0, 0), (255, 255, 0), (0, 255, 0),
               (0, 0, 255), (255, 0, 255), (255, 0, 0),
           ])

           lut = build_palette_lut(palette)

           # Compute scrolling gradient: all keys at once
           values = (col_grid * spread + row_grid * 0.03 + t) % 1.0
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

### Step 3: Understand each utility

**`make_coordinate_grids(rows, cols)`** — returns two numpy arrays of shape `(rows, cols)`:
- `row_grid[r, c] = r` (0.0 to 5.0)
- `col_grid[r, c] = c` (0.0 to 15.0)

Use these for vectorized per-pixel position math instead of for-loops.

**`build_palette_lut(palette)`** — takes a list of RGB tuples and returns a `(256, 3)` uint8 array. Each entry is the interpolated color at that position along the gradient. Build this once per frame (it's fast).

**`palette_lookup(lut, values)`** — maps a float array (values in 0.0–1.0) to RGB using the LUT. Returns a `(rows, cols, 3)` uint8 array. The entire keyboard is colored in one vectorized operation.

**`draw_frame(device, frame_rgb)`** — writes a `(rows, cols, 3)` uint8 numpy array to the device matrix and calls `draw()`. Replaces the manual per-key loop.

### Step 4: Test the result

3. Run the effect:

   ```bash
   .venv/bin/python3 effects/rainbow_scroll.py
   ```

   The visual result is the same, but the rendering is now vectorized. The benefit grows with effect complexity.

4. Open the config GUI — the **Palette** parameter now appears as a palette editor with color swatches, +/- buttons, and color pickers. Users can visually redesign your effect's color scheme.

### Step 5: Add more interesting math

5. Try replacing the simple linear gradient with something more complex. Edit the `values` computation in the run loop:

   ```python
   # Sinusoidal plasma-style gradient
   v1 = np.sin(col_grid * spread + t * 3)
   v2 = np.sin(row_grid * 0.5 + t * 2)
   v3 = np.sin((col_grid + row_grid) * 0.3 + t)
   values = ((v1 + v2 + v3) / 3.0 + 1.0) / 2.0  # normalize to 0-1
   ```

   This creates a plasma-like pattern using only the coordinate grids and numpy sine functions.

### Available grid math utilities

For physics simulations and cellular automata, `effects/common.py` provides:

| Function | What it does |
|---|---|
| `laplacian_4pt(grid)` | Measures how each cell differs from its 4 neighbors. Used for heat diffusion, wave equations. Wraps toroidally. |
| `laplacian_9pt(grid)` | Weighted 9-point version — smoother results for reaction-diffusion. |
| `blur_3x3(grid)` | Smooths a grid using a 3×3 box average. Used by physarum for trail diffusion. |
| `value_noise_2d(x, y, seed)` | Vectorized 2D value noise returning values in [0, 1]. Different seeds give different patterns. |
| `fbm(x, y, octaves, weights, seed)` | Fractal Brownian motion — layered noise for organic textures. Used by aurora, arc sweep, and nebula. |

See the [User Reference > Shared Utilities](../user-reference.md#shared-utilities-effectscommonpy) for full details.

## If something goes wrong

- **"No module named 'numpy'":** Install numpy: `.venv/bin/pip install numpy`
- **Colors look wrong:** Make sure `values` is in the 0.0–1.0 range. Values outside this range are clipped by `palette_lookup()`.
- **`draw_frame` is slow:** This function iterates over all keys in Python. For the 96-key matrix, this is fast enough. The numpy benefit comes from the math *before* the draw call.

## What to try next

- Capture a GIF of your effect: [Capturing GIF Previews](06-capturing-gifs.md)
- Study existing effects that use these utilities: `plasma.py` (palette + sine waves), `heat_diffusion.py` (Laplacian), `physarum.py` (blur + agents)
