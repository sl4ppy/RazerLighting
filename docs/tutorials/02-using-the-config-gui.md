[← Back to Tutorials](index.md) | [← Back to Documentation](../../README.md#documentation)

# Using the Config GUI

Open the configuration window, explore the parameter controls, preview changes in real time, and save your tweaks.

## What you'll accomplish

You will open the configuration GUI, adjust timing and color parameters for an effect, preview the results on the live keyboard visualizer, and save your changes.

## Prerequisites

- Razer Lighting is running (tray icon visible). See [Tutorial 1](01-your-first-effect.md).

## Estimated time

10 minutes.

## Steps

1. Right-click the tray icon and click **Configure...**.

   ![Tray menu highlighting Configure option](../images/screenshots/SS-008.png)

   The configuration window opens. It has three areas:
   - **Effect dropdown** at the top
   - **Parameter panel** on the left (scrollable)
   - **Keyboard visualizer** on the right

   ![Config window overview](../images/screenshots/SS-003.png)

2. Select **Plasma** from the effect dropdown. The parameter panel populates with controls grouped into categories (Timing, Colors, Simulation, Other), and the visualizer starts showing the Plasma effect.

3. Find the **FPS** slider in the Timing group. Drag it from 20 down to 10. Watch the visualizer — the animation slows down immediately. Drag it up to 30 — the animation becomes smoother.

   ![Adjusting the FPS slider](../images/screenshots/SS-009.png)

   > Changes you make here only affect the preview. Your actual keyboard is still running the saved config.

4. Scroll down to the **Colors** group. You should see the **Palette** parameter with a row of color swatches.

   ![Palette editor with color swatches](../images/screenshots/SS-010.png)

5. Click any color swatch in the palette. A color picker dialog opens. Choose a new color and click OK. The visualizer updates immediately with your new palette.

6. Click the **+** button next to the palette to add a new color stop. Click **-** to remove the last one. Experiment with different palette lengths and colors.

7. Hover over any parameter label to see a tooltip describing what it controls.

8. When you're happy with your changes, click **Save** in the bottom button bar. This writes your values to `effects/plasma_config.py`. The effect running on your keyboard picks up the new values on its next frame.

   > The window title shows an asterisk (`*`) when you have unsaved changes.

9. If you want to undo your changes, click **Revert to Saved** to reload the config file from disk. Or click **Reset to Defaults** to restore the values from when the GUI first opened the effect.

10. Switch to a different effect using the dropdown. If you have unsaved changes, the GUI asks whether to discard them.

## If something goes wrong

- **"No configurable parameters" message:** The selected effect doesn't have a `_config.py` file. Not all effects are guaranteed to have one, though all 28 built-in effects do.
- **Visualizer is black:** The preview may have crashed. Switch to a different effect and back to restart it.
- **Save button doesn't seem to work:** Check the terminal where you launched the tray app — if the config file has a syntax error from a previous manual edit, the effect may be using cached values.

## What to try next

- Learn about palettes and color customization in depth: [Customizing Colors](03-customizing-colors.md)
- Write your own effect with a config file: [Writing a Custom Effect](04-writing-a-custom-effect.md)
