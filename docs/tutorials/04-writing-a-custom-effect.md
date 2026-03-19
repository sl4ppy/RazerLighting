[← Back to Tutorials](index.md) | [← Back to Documentation](../../README.md#documentation)

# Writing a Custom Effect

Create a new procedural keyboard lighting effect from scratch, add a config file, and see it appear in the tray menu.

## What you'll accomplish

You will write a "Rainbow Scroll" effect that sweeps a rainbow gradient across the keyboard, add a hot-reloadable config file, and test it both standalone and through the tray app.

## Prerequisites

- Razer Lighting installed and working. See [Getting Started](../getting-started.md).
- Basic Python knowledge (variables, loops, functions, imports).

## Estimated time

20 minutes.

## Steps

### Step 1: Create the effect file

1. Create a new file `effects/rainbow_scroll.py`:

   ```python
   #!/usr/bin/env python3
   """Rainbow Scroll - a scrolling rainbow gradient across the keyboard."""

   import math
   import os
   import time

   from effects.common import load_config, clear_keyboard, frame_sleep, standalone_main

   EFFECT_NAME = "Rainbow Scroll"
   CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "rainbow_scroll_config.py")


   def hsv_to_rgb(h, s, v):
       """Convert HSV (0-1 range) to RGB (0-255 range)."""
       if s == 0:
           c = int(v * 255)
           return (c, c, c)
       h6 = h * 6.0
       i = int(h6)
       f = h6 - i
       p = int(v * (1 - s) * 255)
       q = int(v * (1 - s * f) * 255)
       t = int(v * (1 - s * (1 - f)) * 255)
       v = int(v * 255)
       i %= 6
       if i == 0: return (v, t, p)
       if i == 1: return (q, v, p)
       if i == 2: return (p, v, t)
       if i == 3: return (p, q, v)
       if i == 4: return (t, p, v)
       return (v, p, q)


   def run(device, stop_event):
       rows = device.fx.advanced.rows
       cols = device.fx.advanced.cols
       matrix = device.fx.advanced.matrix

       t = 0.0
       next_frame = time.monotonic()

       while not stop_event.is_set():
           cfg = load_config(CONFIG_PATH)
           fps = cfg.get("FPS", 20)
           speed = cfg.get("SPEED", 0.02)
           spread = cfg.get("SPREAD", 0.06)
           saturation = cfg.get("SATURATION", 1.0)
           brightness = cfg.get("BRIGHTNESS", 1.0)

           for r in range(rows):
               for c in range(cols):
                   hue = (c * spread + r * 0.05 + t) % 1.0
                   matrix[r, c] = hsv_to_rgb(hue, saturation, brightness)

           device.fx.advanced.draw()
           next_frame, dt = frame_sleep(next_frame, 1.0 / fps)
           t = (t + speed * dt * fps) % 1.0

       clear_keyboard(device)


   def main():
       standalone_main(EFFECT_NAME, run)


   if __name__ == "__main__":
       main()
   ```

   This file has the two required pieces:
   - `EFFECT_NAME = "Rainbow Scroll"` — the display name.
   - `run(device, stop_event)` — the main loop.

### Step 2: Create the config file

2. Create `effects/rainbow_scroll_config.py`:

   ```python
   FPS = 20
   SPEED = 0.02        # scroll speed (hue shift per frame)
   SPREAD = 0.06       # color spread across columns (higher = tighter rainbow)
   SATURATION = 1.0    # color saturation (0 = grayscale, 1 = vivid)
   BRIGHTNESS = 1.0    # LED brightness (0 = off, 1 = full)
   ```

   The config file is plain Python with simple assignments. The naming convention `<effect>_config.py` ensures it's excluded from effect discovery (the `_config.py` suffix is filtered out).

### Step 3: Test standalone

3. Run the effect directly without the tray app:

   ```bash
   .venv/bin/python3 effects/rainbow_scroll.py
   ```

   You should see:

   ```
   Razer Blade 14 (2021) (16x6) - Rainbow Scroll
   Ctrl+C to stop
   ```

   Your keyboard displays a scrolling rainbow. Press Ctrl+C to stop.

   ![Standalone effect running in terminal](../images/screenshots/SS-012.png)

### Step 4: Test hot-reload

4. While the effect is running standalone, open `effects/rainbow_scroll_config.py` in a text editor and change `SPEED` from `0.02` to `0.1`. Save the file.

   The rainbow immediately scrolls faster — no restart needed.

5. Change `SPREAD` to `0.15` — the rainbow becomes tighter with more color bands visible. Change it to `0.02` — the whole keyboard shows a gentle gradient.

6. Press Ctrl+C to stop the standalone effect.

### Step 5: Verify auto-discovery

7. If the tray app is running, right-click the tray icon. **Rainbow Scroll** should appear in the effect list. If the tray app was already running when you created the file, the effect will appear the next time you open the menu (discovery runs on every menu open).

8. Select **Rainbow Scroll** from the menu. It now runs through the tray app.

### Step 6: Test in the config GUI

9. Open **Configure...** from the tray menu. Select **Rainbow Scroll** from the dropdown. The GUI auto-detects all five parameters and generates appropriate controls:

   - **FPS** → slider (1–60)
   - **Speed** → slider (0–0.1)
   - **Spread** → slider (0–0.3)
   - **Saturation** → slider (0–1)
   - **Brightness** → slider (0–1)

   The live preview shows the effect. Drag sliders and watch the preview update in real time.

### Understanding the code

Key patterns used:

- **`load_config(CONFIG_PATH)`** reads the config file, caching by mtime. Called every frame.
- **`cfg.get("KEY", default)`** retrieves a value with a fallback. The effect works even without a config file.
- **`frame_sleep(next_frame, interval)`** provides deadline-based timing. Returns `dt` for animation speed independence.
- **`clear_keyboard(device)`** sets all keys to black on exit. Always clean up.
- **`standalone_main(EFFECT_NAME, run)`** handles device connection and signal handling for standalone execution.

## If something goes wrong

- **Effect doesn't appear in the menu:** Check the terminal for `Skipping rainbow_scroll.py: ...` error messages. Common causes: syntax error in the file, missing `run()` function, or import error.
- **Config GUI shows no parameters:** Verify the config file is named `rainbow_scroll_config.py` (matching the effect file name) and contains valid Python assignments.
- **Effect crashes:** Check the terminal for tracebacks. Common issue: forgetting to handle `stop_event` (infinite loop that never exits).

## What to try next

- Add numpy rendering for better performance: [Using the Shared Utilities](05-using-shared-utilities.md)
- Study existing effects for advanced techniques — `plasma.py` for sine-wave patterns, `heat_diffusion.py` for grid simulations, `boids.py` for particle systems
- Read the full [Creating Effects Guide](../../CREATING_EFFECTS.md) for all patterns and tips
