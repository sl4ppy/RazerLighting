[← Back to Tutorials](index.md) | [← Back to Documentation](../../README.md#documentation)

# Capturing GIF Previews

Record any effect as an animated GIF for documentation, sharing, or README files.

## What you'll accomplish

You will use the `capture_gif.py` tool to record an effect as an animated GIF, apply config overrides for the capture, and view the result.

## Prerequisites

- Razer Lighting installed with dependencies (Pillow is required for GIF rendering).
- No hardware required — the capture tool uses the virtual device.

## Estimated time

5 minutes.

## Steps

1. Capture the Plasma effect with default settings (5-second recording):

   ```bash
   .venv/bin/python3 capture_gif.py plasma
   ```

   Output:

   ```
   Capturing plasma for 5.0s...
   Saved screenshots/plasma.gif (80 frames, 50ms/frame)
   ```

   ![Terminal showing capture_gif output](../images/screenshots/SS-014.png)

2. Open `screenshots/plasma.gif` in an image viewer or browser to see the result.

3. Capture with a longer duration and config overrides:

   ```bash
   .venv/bin/python3 capture_gif.py lightning_strike 8 INTERVAL_MIN=0.3 INTERVAL_MAX=1.0
   ```

   This records Lightning Strike for 8 seconds with faster bolt intervals than the default config.

4. Capture your own custom effect (if you created one in [Tutorial 4](04-writing-a-custom-effect.md)):

   ```bash
   .venv/bin/python3 capture_gif.py rainbow_scroll 5
   ```

### How the capture tool works

- It loads the effect module and runs it against a [virtual device](../glossary.md#virtual-device) — no physical keyboard needed.
- Each draw call renders a PIL image of the keyboard layout (640 × 375 pixels).
- After the capture duration, frames are saved as an animated GIF.
- If more than 80 frames are captured, the tool evenly downsamples to 80 frames.
- Config overrides are appended to the effect's config file temporarily.

### Command reference

```
python3 capture_gif.py <effect_name> [duration] [KEY=VALUE ...]
```

| Argument | Default | Description |
|---|---|---|
| `effect_name` | (required) | Module filename without `.py` (e.g., `plasma`, `heat_diffusion`) |
| `duration` | `5.0` | Capture duration in seconds |
| `KEY=VALUE` | — | Config parameter overrides (e.g., `FPS=30`, `SPEED=0.1`) |

## If something goes wrong

- **"No frames captured!":** The effect may have crashed during capture. Run it standalone first to check for errors: `.venv/bin/python3 effects/<name>.py`
- **GIF is too large:** Reduce the duration or increase FPS (fewer unique frames). The tool caps at 80 frames.
- **Colors look different from the keyboard:** GIF uses a 256-color palette per frame, which can slightly alter colors compared to the 24-bit keyboard LEDs.

## What to try next

- Set up effects to run at login: [Autostart and Standalone Mode](07-autostart-and-standalone.md)
- Share your GIF in a pull request or the project README
