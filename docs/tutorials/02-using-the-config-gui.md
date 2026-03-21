[← Back to Tutorials](index.md) | [← Back to Documentation](../../README.md#documentation)

# Using the Config GUI

Open the configuration window, explore the effect gallery, tweak parameters with live preview, and save your changes.

## What you'll accomplish

You will open the configuration GUI, browse effects in the gallery sidebar, adjust timing and color parameters, preview the results on the live keyboard visualizer, and save your changes.

## Prerequisites

- Razer Lighting is running (tray icon visible). See [Tutorial 1](01-your-first-effect.md).

## Estimated time

10 minutes.

## Steps

1. Right-click the tray icon and click **Configure...**.

   The configuration window opens. It has four main areas:
   - **Effect gallery** on the left sidebar — searchable card list of all effects with category filters
   - **Header bar** at the top — current effect name, category, description, and Save/Revert/Reset buttons
   - **Keyboard visualizer** in the center — real-time preview with glow and depth effects
   - **Parameter panel** at the bottom — collapsible groups of auto-generated controls

2. In the gallery sidebar, click the **Plasma** card. The header bar updates with "Plasma" and its description. The parameter panel populates with controls in collapsible groups (Timing, Colors, etc.), and the visualizer starts showing the Plasma effect.

   > Use the search field at the top of the gallery to find effects by name, or click the category buttons (Organic, Atmospheric, Mathematical, Glitch, Kinetic) to filter.

3. In the parameter panel, find the **Timing** group. Click its header to expand it if collapsed. Find the **FPS** slider and drag it from 20 down to 10. Watch the visualizer — the animation slows down immediately. Drag it up to 30 — the animation becomes smoother.

   > Changes you make here only affect the preview. Your actual keyboard is still running the saved config. The status bar at the bottom shows the current FPS and an "unsaved" indicator when you have pending changes.

4. Expand the **Colors** group. You should see the **Palette** parameter with a row of color swatches.

5. Click any color swatch in the palette. A color picker dialog opens. Choose a new color and click OK. The visualizer updates immediately with your new palette.

6. Click the **+** button next to the palette to add a new color stop. Click **-** to remove the last one. Experiment with different palette lengths and colors.

7. Hover over any parameter label to see a tooltip describing what it controls.

8. When you're happy with your changes, click **Save** in the header bar. This writes your values to `effects/plasma_config.py`. The effect running on your keyboard picks up the new values on its next frame.

9. If you want to undo your changes, click **Revert** to reload the config file from disk. Or click **Reset** to restore the original default values.

10. Click a different effect card in the gallery sidebar. If you have unsaved changes, the GUI asks whether to discard them.

## If something goes wrong

- **"No configurable parameters" message:** The selected effect doesn't have a `_config.py` file. Not all effects are guaranteed to have one, though all 28 built-in effects do.
- **Visualizer is black:** The preview may have crashed. Click a different effect card and then click back to restart it.
- **Save button doesn't seem to work:** Check the terminal where you launched the tray app — if the config file has a syntax error from a previous manual edit, the effect may be using cached values.

## What to try next

- Learn about palettes and color customization in depth: [Customizing Colors](03-customizing-colors.md)
- Write your own effect with a config file: [Writing a Custom Effect](04-writing-a-custom-effect.md)
