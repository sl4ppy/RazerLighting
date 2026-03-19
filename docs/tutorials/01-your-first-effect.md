[← Back to Tutorials](index.md) | [← Back to Documentation](../../README.md#documentation)

# Running Your First Effect

Launch Razer Lighting, pick an effect from the tray menu, and watch your keyboard come alive.

## What you'll accomplish

You will start the Razer Lighting tray app, select an effect, try the "Random" option, and learn how the tray menu works.

## Prerequisites

- Completed the [Getting Started](../getting-started.md) guide (OpenRazer installed, venv created, dependencies installed).

## Estimated time

5 minutes.

## Steps

1. Open a terminal and navigate to the project directory:

   ```bash
   cd RazerLighting
   ```

2. Start the tray application:

   ```bash
   .venv/bin/python3 razer_lighting.py
   ```

   You should see output like:

   ```
   Device: Razer Blade 14 (2021)
   Effects: Arc Sweep, Aurora Borealis, Binary Cascade, ...
   Started: Arc Sweep
   ```

   A green circle icon appears in your system tray, and the first effect (alphabetically) starts running on your keyboard.

   ![Terminal output after launching](../images/screenshots/SS-007.png)

3. Right-click the green tray icon. A menu appears listing all available effects with a radio button next to the active one.

   ![Tray menu showing effects](../images/screenshots/SS-001.png)

4. Click **Plasma** (or any effect that catches your eye). The current effect stops, and the new one starts immediately. You should see the terminal print:

   ```
   Started: Plasma
   ```

5. Click **Random** from the menu. A randomly chosen effect starts. The terminal shows which one was picked:

   ```
   Started: Metaballs (random)
   ```

6. Try a few more effects to see the variety. Each one is procedurally generated — the pattern never exactly repeats.

7. When you're done, click **Quit** from the tray menu. The keyboard LEDs turn off and the app exits.

## If something goes wrong

- **No tray icon appears:** Your desktop environment may need an extension for tray support. On GNOME with Wayland, install the AppIndicator extension. See [Troubleshooting](../troubleshooting.md#does-this-work-on-wayland).
- **Keyboard stays dark:** Check that no other RGB control app (Polychromatic, etc.) is running. Also verify keyboard brightness isn't set to zero. See [Troubleshooting](../troubleshooting.md#effect-runs-but-keyboard-stays-dark).
- **App crashes on start:** Check the terminal for error messages. The most common issue is a missing OpenRazer daemon. See [Troubleshooting](../troubleshooting.md#device-connection).

## What to try next

- Open the configuration GUI and tweak effect parameters: [Using the Config GUI](02-using-the-config-gui.md)
- Browse all 28 effects with animated previews: [Effects Guide](../../EFFECTS.md)
