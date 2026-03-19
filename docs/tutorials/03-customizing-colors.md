[← Back to Tutorials](index.md) | [← Back to Documentation](../../README.md#documentation)

# Customizing Colors

Change effect palettes and individual colors using both the GUI and manual config file editing.

## What you'll accomplish

You will modify an effect's color palette in the GUI, then make the same changes by editing the config file directly, and verify that hot-reload applies your changes in real time.

## Prerequisites

- Razer Lighting is running. See [Tutorial 1](01-your-first-effect.md).
- Familiarity with the config GUI. See [Tutorial 2](02-using-the-config-gui.md).

## Estimated time

10 minutes.

## Steps

### Part A: Colors in the GUI

1. Open **Configure...** from the tray menu and select the **Heat Diffusion** effect.

2. Scroll to the **Colors** group in the parameter panel. You should see:
   - **Palette** — a row of color swatches representing the hot iron gradient (black → red → orange → yellow → white).
   - **Bg Color** — the background color (likely near-black).

3. Click the first swatch in the palette (the darkest color). In the color picker, change it to a deep blue like `(0, 0, 60)`. Click OK.

   The visualizer now shows heat spots that fade into blue instead of black. This creates a "cold" base that contrasts with the hot colors.

4. Click the **+** button twice to add two new color stops at the end. Change them to bright cyan `(0, 255, 255)` and white `(255, 255, 255)`.

   Your palette now transitions: deep blue → red → orange → yellow → white → cyan → white. The hottest areas will glow cyan.

5. Click **Save** to apply to your keyboard.

### Part B: Colors in the config file

6. Open `effects/heat_diffusion_config.py` in your text editor. You should see a `PALETTE` variable with a list of RGB tuples:

   ```python
   PALETTE = [
       (0, 0, 60),
       (180, 0, 0),
       (255, 100, 0),
       (255, 220, 50),
       (255, 255, 255),
       (0, 255, 255),
       (255, 255, 255),
   ]
   ```

   These are the values you just saved from the GUI.

7. While the effect is running on your keyboard, change the palette to something completely different. For example, a cool ocean palette:

   ```python
   PALETTE = [
       (0, 0, 20),
       (0, 20, 80),
       (0, 60, 120),
       (0, 150, 200),
       (100, 220, 255),
       (200, 240, 255),
   ]
   ```

   Save the file.

8. Watch your keyboard — within one frame (1/20th of a second), the effect switches to the new palette. This is [hot-reload](../glossary.md#hot-reload) in action. No restart needed.

### Part C: Individual RGB colors

9. Some effects have individual color parameters instead of (or in addition to) palettes. Select **Lightning Strike** in the config GUI.

10. In the Colors group, find **Bolt Color**. Click the swatch and change it from white to electric blue `(100, 150, 255)`. The preview shows blue lightning bolts instead of white.

11. Change **Glow Color** to a warm amber `(40, 20, 0)` for the ambient background during strikes.

12. Click **Save** when you're satisfied.

### Understanding RGB values

Every color is specified as a tuple of three integers, each 0–255:

| Component | 0 | 128 | 255 |
|---|---|---|---|
| **Red** | No red | Half red | Full red |
| **Green** | No green | Half green | Full green |
| **Blue** | No blue | Half blue | Full blue |

Common colors:
- `(255, 0, 0)` = red
- `(0, 255, 0)` = green
- `(0, 0, 255)` = blue
- `(255, 255, 0)` = yellow
- `(0, 255, 255)` = cyan
- `(255, 0, 255)` = magenta
- `(255, 255, 255)` = white
- `(0, 0, 0)` = black (LED off)

### How palettes work

A [palette](../glossary.md#palette) is an ordered list of colors that defines a gradient. Effects map a scalar value (0.0 to 1.0) to a position along this gradient:

- `0.0` → first color
- `0.5` → middle color (interpolated)
- `1.0` → last color

Colors between stops are smoothly interpolated. More stops give you finer control over the gradient shape. The order matters — it defines the direction of the gradient.

## If something goes wrong

- **Config file edit doesn't take effect:** You may have introduced a Python syntax error (e.g., missing comma between tuples). Check the terminal for `Config load error` messages. The effect falls back to the last valid config.
- **Colors look different on screen vs. preview:** The keyboard LEDs have different color reproduction than your monitor. Bright, saturated colors tend to work best on LEDs.

## What to try next

- Write a custom effect with your own palette: [Writing a Custom Effect](04-writing-a-custom-effect.md)
- Browse all effect palettes in the [Effects Guide](../../EFFECTS.md)
