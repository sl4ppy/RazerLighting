# Screenshot & Image Briefs

Internal asset production guide for Razer Lighting documentation. This file is **not** linked from the README or any user-facing doc.

Each brief describes an image referenced in the documentation. Filenames match the paths used in Markdown image tags.

---

### SS-001
- **Filename**: `docs/images/screenshots/SS-001.png`
- **Referenced in**: `docs/getting-started.md` > Using the System Tray Menu; `docs/tutorials/01-your-first-effect.md` > Step 3
- **Subject**: The system tray right-click menu showing all available effects, Random, Reload, Configure, Start on Login, About, and Quit
- **Capture type**: UI SCREENSHOT
- **Crop tier**: PANEL CROP
- **Capture region**: The full tray dropdown menu from the green circle icon. Include the tray icon itself at the top of the capture and the complete menu down to Quit.
- **State**: App running with "Plasma" selected (radio indicator visible). At least 10 effect names visible to show the scope. "Start on Login" unchecked.
- **Annotations**:
  - CALLOUT BOX BLUE: Around the effect list section, labeled "Effects"
  - CALLOUT BOX AMBER: Around the "Configure..." menu item, labeled "Opens config GUI"
  - NUMBERED BADGE 1: Next to the radio-selected effect (Plasma)
  - NUMBERED BADGE 2: Next to "Random"
- **Alt text**: System tray right-click menu showing a list of 28 lighting effects with radio buttons, followed by Random, Reload Effect, Configure, Start on Login, About, and Quit options. Plasma is selected.

---

### SS-002
- **Filename**: `docs/images/screenshots/SS-002.png`
- **Referenced in**: `docs/getting-started.md` > Using the System Tray Menu (alternate angle)
- **Subject**: Close-up of the tray menu showing the utility options below the effect list
- **Capture type**: UI SCREENSHOT
- **Crop tier**: ELEMENT CROP
- **Capture region**: The bottom portion of the tray menu showing: separator, Reload Effect, Configure..., Start on Login (with checkmark), separator, About..., Quit
- **State**: "Start on Login" enabled (checked). An effect is running.
- **Annotations**:
  - ARROW RED: From lower-left, pointing at "Start on Login" checkmark
  - CALLOUT BOX BLUE: Around "Configure..." item, labeled "Config GUI"
- **Alt text**: Bottom portion of the tray menu showing Reload Effect, Configure with ellipsis, Start on Login with a checkmark indicating it is enabled, About, and Quit.

---

### SS-003
- **Filename**: `docs/images/screenshots/SS-003.png`
- **Referenced in**: `docs/getting-started.md` > The Configuration GUI; `docs/tutorials/02-using-the-config-gui.md` > Step 1
- **Subject**: Full configuration window (v1.1.0) showing the effect gallery sidebar, header bar, keyboard visualizer with glow effects, and collapsible parameter panel
- **Capture type**: UI SCREENSHOT
- **Crop tier**: FULL WINDOW
- **Capture region**: The entire ConfigWindow at approximately 1200×720 resolution. Dark theme with Razer green (#44D62C) accents.
- **State**: "Plasma" selected in the gallery sidebar (card highlighted). Header bar showing "Plasma" title with "MATHEMATICAL" category tag and description. Keyboard visualizer showing plasma effect with per-key glow bloom and 3D depth. Parameter panel below showing collapsible Timing group (expanded) and Colors group.
- **Annotations**:
  - NUMBERED BADGE 1: Adjacent to the effect gallery sidebar, labeled "1"
  - NUMBERED BADGE 2: Adjacent to the keyboard visualizer, labeled "2"
  - NUMBERED BADGE 3: Adjacent to the parameter panel, labeled "3"
  - CALLOUT BOX BLUE: Around the Save/Revert/Reset buttons in the header bar, labeled "Save controls"
  - CALLOUT BOX AMBER: Around the status bar at the bottom, labeled "FPS & status"
- **Alt text**: Configuration window with dark theme showing Plasma effect. Left sidebar has a searchable effect gallery with category filter buttons. Center shows a keyboard visualization with glowing orange and purple plasma colors with ambient bloom effects. Bottom panel has collapsible parameter groups with sliders for FPS and Time Speed, plus a palette editor. Header bar shows effect name, category, and action buttons. Status bar shows FPS counter and matrix dimensions.

---

### SS-007
- **Filename**: `docs/images/screenshots/SS-007.png`
- **Referenced in**: `docs/tutorials/01-your-first-effect.md` > Step 2
- **Subject**: Terminal window showing the output after launching razer_lighting.py
- **Capture type**: TERMINAL CAPTURE
- **Crop tier**: ELEMENT CROP
- **Capture region**: Terminal showing 3 lines of output: Device name, Effects list, and "Started: Arc Sweep". Include the command line above showing `.venv/bin/python3 razer_lighting.py`.
- **State**: App just launched, first effect started.
- **Annotations**:
  - ARROW GREEN: Pointing at the "Device:" line, indicating successful connection
  - HIGHLIGHT GREEN: Semi-transparent over the "Started: Arc Sweep" line
- **Alt text**: Terminal showing the command .venv/bin/python3 razer_lighting.py followed by output: Device: Razer Blade 14 (2021), a list of all available effects, and Started: Arc Sweep.

---

### SS-008
- **Filename**: `docs/images/screenshots/SS-008.png`
- **Referenced in**: `docs/tutorials/02-using-the-config-gui.md` > Step 1
- **Subject**: Tray menu with "Configure..." highlighted or being clicked
- **Capture type**: UI SCREENSHOT
- **Crop tier**: ELEMENT CROP
- **Capture region**: The middle section of the tray menu showing the separator, Reload Effect, and Configure... menu item. Configure should be visually highlighted (hover state).
- **State**: Mouse hovering over "Configure..." in the tray menu.
- **Annotations**:
  - ARROW RED: From lower-right, pointing at "Configure..." text
- **Alt text**: System tray menu with the Configure option highlighted, showing it is about to be clicked.

---

### SS-009
- **Filename**: `docs/images/screenshots/SS-009.png`
- **Referenced in**: `docs/tutorials/02-using-the-config-gui.md` > Step 3
- **Subject**: The collapsible parameter panel showing the Timing group expanded with the FPS slider being adjusted
- **Capture type**: UI SCREENSHOT
- **Crop tier**: PANEL CROP
- **Capture region**: The bottom parameter panel of the config window, showing the Timing collapsible group expanded with FPS slider and at least one other slider (Time Speed or Overlay Time Speed). The FPS slider handle should be at a non-default position (e.g., 30). The group header should show the collapse arrow.
- **State**: Plasma effect selected. FPS slider at 30, spinbox showing 30.
- **Annotations**:
  - ARROW RED: Pointing at the FPS slider handle
  - CALLOUT BOX BLUE: Around the spinbox showing "30", labeled "Exact value"
- **Alt text**: Parameter panel showing the Timing collapsible group expanded with a FPS slider set to 30 and Time Speed slider. Each slider has a label on the left and a monospace spinbox showing the exact value on the right. The group header shows a downward arrow indicating it is expanded.

---

### SS-010
- **Filename**: `docs/images/screenshots/SS-010.png`
- **Referenced in**: `docs/tutorials/02-using-the-config-gui.md` > Step 4
- **Subject**: The Colors collapsible group showing a palette editor with larger color swatches and +/- buttons
- **Capture type**: UI SCREENSHOT
- **Crop tier**: PANEL CROP
- **Capture region**: The Colors collapsible group in the parameter panel (expanded), showing the Palette parameter with its row of 48×32px color swatches (at least 5 colors from the Plasma palette), the + and − buttons, and the hex value labels in monospace.
- **State**: Plasma effect selected with its default sunset palette.
- **Annotations**:
  - NUMBERED BADGE 1: Next to a color swatch, indicating "click to change"
  - ARROW RED: Pointing at the "+" button
  - CALLOUT BOX BLUE: Around the hex label (e.g., "#ff6400"), labeled "Hex value"
- **Alt text**: Colors collapsible group showing a Palette parameter with a row of larger colored squares in orange, yellow, pink, magenta, and purple tones. Plus and minus buttons allow adding or removing colors. A monospace hex value label shows the color code.

---

### SS-011
- **Filename**: `docs/images/screenshots/SS-011.png`
- **Referenced in**: `docs/tutorials/03-customizing-colors.md` > Part A context
- **Subject**: Before/after comparison of Heat Diffusion with different palettes
- **Capture type**: ANIMATED GIF
- **Crop tier**: PANEL CROP
- **Capture region**: Two keyboard visualizer captures side by side — left showing the default hot iron palette (black→red→yellow→white), right showing a custom ocean palette (blue→cyan→white).
- **State**: Heat Diffusion effect running. Left: default config. Right: custom ocean palette.
- **Annotations**:
  - CALLOUT BOX AMBER: Below left image, labeled "Default palette"
  - CALLOUT BOX BLUE: Below right image, labeled "Custom palette"
- **Alt text**: Side-by-side comparison of the Heat Diffusion effect. Left keyboard shows the default hot iron colors with red, orange, and yellow heat spots on black. Right keyboard shows a custom ocean palette with blue and cyan heat spots on dark blue.
- **Duration / FPS**: 3 seconds, 15 fps (for each side)

---

### SS-012
- **Filename**: `docs/images/screenshots/SS-012.png`
- **Referenced in**: `docs/tutorials/04-writing-a-custom-effect.md` > Step 3
- **Subject**: Terminal showing a custom effect running standalone
- **Capture type**: TERMINAL CAPTURE
- **Crop tier**: ELEMENT CROP
- **Capture region**: Terminal showing the command `.venv/bin/python3 effects/rainbow_scroll.py` and its output: device name, dimensions, effect name, and "Ctrl+C to stop".
- **State**: Rainbow Scroll effect running standalone.
- **Annotations**:
  - HIGHLIGHT GREEN: Over the "Rainbow Scroll" text in the output
- **Alt text**: Terminal showing the command to run rainbow_scroll.py standalone, with output showing Razer Blade 14 (2021) (16x6) - Rainbow Scroll, and Ctrl+C to stop.

---

### SS-013
- **Filename**: `docs/images/screenshots/SS-013.png`
- **Referenced in**: `docs/tutorials/04-writing-a-custom-effect.md` > Understanding the code (optional reference)
- **Subject**: Diagram showing the effect lifecycle: start → loop (read config → compute colors → draw) → stop → cleanup
- **Capture type**: DIAGRAM
- **Crop tier**: FULL WINDOW
- **Capture region**: N/A — generated diagram
- **State**: N/A
- **Annotations**: None (diagram is self-annotating)
- **Alt text**: Flow diagram showing the effect lifecycle. Start leads to a loop containing three steps: read config, compute colors, draw to keyboard. The loop exits when stop event is set, leading to clear keyboard and exit.
- **Image generation prompt**: Flat design flow diagram of an effect lifecycle. Clean vector style, limited palette of dark charcoal background, Razer green (#44D62C) for flow arrows and active states, white for text. Horizontal flow from left to right. Start node (circle) → loop box containing three steps stacked vertically (Read Config → Compute Colors → Draw) with a return arrow → decision diamond (Stop Event?) → Clear Keyboard box → End node (circle). Keep minimal, no decorative elements, no rendered text inside the image that would need to be readable — use shapes and arrows only.

---

### SS-014
- **Filename**: `docs/images/screenshots/SS-014.png`
- **Referenced in**: `docs/tutorials/06-capturing-gifs.md` > Step 1
- **Subject**: Terminal showing capture_gif.py running and completing
- **Capture type**: TERMINAL CAPTURE
- **Crop tier**: ELEMENT CROP
- **Capture region**: Terminal showing the command `.venv/bin/python3 capture_gif.py plasma` and output: "Capturing plasma for 5.0s..." followed by "Saved screenshots/plasma.gif (80 frames, 50ms/frame)".
- **State**: Capture complete.
- **Annotations**:
  - HIGHLIGHT GREEN: Over the "Saved" output line
- **Alt text**: Terminal showing the capture_gif.py command capturing the plasma effect for 5 seconds, then reporting that it saved 80 frames to screenshots/plasma.gif.

---

### SS-015
- **Filename**: `docs/images/screenshots/SS-015.png`
- **Referenced in**: `docs/tutorials/07-autostart-and-standalone.md` > Part A context
- **Subject**: Tray menu showing "Start on Login" with and without a checkmark
- **Capture type**: UI SCREENSHOT
- **Crop tier**: ELEMENT CROP
- **Capture region**: The "Start on Login" menu item in the tray menu, showing the checked (enabled) state.
- **State**: Autostart enabled.
- **Annotations**:
  - ARROW RED: Pointing at the checkmark next to "Start on Login"
- **Alt text**: Tray menu item showing Start on Login with a checkmark indicating autostart is enabled.

---

### SS-016
- **Filename**: `docs/images/screenshots/SS-016.png`
- **Referenced in**: `docs/troubleshooting.md` > Device Connection context
- **Subject**: Terminal showing the "No Razer devices found" error with retry messages
- **Capture type**: TERMINAL CAPTURE
- **Crop tier**: ELEMENT CROP
- **Capture region**: Terminal showing several "No devices found, retrying in 3s..." messages followed by the final "No Razer devices found. Is openrazer-daemon running?" error.
- **State**: OpenRazer daemon not running, device not found.
- **Annotations**:
  - HIGHLIGHT RED: Over the final error message line
  - CALLOUT BOX AMBER: To the right of the retry messages, labeled "Retries 10 times"
- **Alt text**: Terminal showing repeated retry messages saying No devices found retrying in 3 seconds, followed by a final error message: No Razer devices found. Is openrazer-daemon running?
