[← Back to Tutorials](index.md) | [← Back to Documentation](../../README.md#documentation)

# Autostart and Standalone Mode

Run effects automatically at login and run individual effects standalone without the tray app.

## What you'll accomplish

You will enable autostart so Razer Lighting launches at login, and learn how to run individual effects directly from the command line.

## Prerequisites

- Razer Lighting installed and working. See [Getting Started](../getting-started.md).

## Estimated time

5 minutes.

## Steps

### Part A: Autostart at login

1. Right-click the tray icon and click **Start on Login**. A checkmark appears next to the menu item.

   The app creates an XDG autostart entry at `~/.config/autostart/razer-lighting.desktop`. This tells your desktop environment to launch Razer Lighting when you log in.

2. Log out and back in (or reboot). Razer Lighting starts automatically, restoring the last selected effect.

3. To disable autostart, right-click the tray icon and click **Start on Login** again. The checkmark disappears and the autostart file is deleted.

### What the autostart entry contains

The generated `.desktop` file looks like:

```ini
[Desktop Entry]
Type=Application
Name=Razer Lighting
Exec=/path/to/RazerLighting/.venv/bin/python3 /path/to/RazerLighting/razer_lighting.py
Icon=input-keyboard
Terminal=false
X-GNOME-Autostart-enabled=true
Comment=Custom Razer keyboard lighting effects
```

It uses absolute paths to the venv's Python interpreter and the script. If you move the project directory, toggle autostart off and back on to regenerate the paths.

### Part B: Standalone effect execution

You can run any effect directly without the tray app. This is useful for:
- Testing effects during development.
- Running a single effect with minimal overhead.
- Scripting or integrating with other tools.

4. Run the Plasma effect standalone:

   ```bash
   .venv/bin/python3 effects/plasma.py
   ```

   Output:

   ```
   Razer Blade 14 (2021) (16x6) - Plasma
   Ctrl+C to stop
   ```

   The effect runs directly on your keyboard. Press Ctrl+C to stop — the keyboard clears to black.

5. Run any other effect the same way:

   ```bash
   .venv/bin/python3 effects/lightning_strike.py
   .venv/bin/python3 effects/heartbeat.py
   .venv/bin/python3 effects/boids.py
   ```

### How standalone mode works

Each effect has a `main()` function that calls `standalone_main(EFFECT_NAME, run)` from `effects/common.py`. This function:

1. Connects to OpenRazer (same as the tray app).
2. Registers Ctrl+C and SIGTERM handlers to set `stop_event`.
3. Calls your `run()` function directly.

The tray app is not involved — no tray icon, no menu, no config GUI. The effect reads its own config file directly.

### Combining standalone with config hot-reload

6. In one terminal, run an effect:

   ```bash
   .venv/bin/python3 effects/plasma.py
   ```

7. In another terminal, edit the config:

   ```bash
   nano effects/plasma_config.py
   ```

   Change `TIME_SPEED` and save. The running effect picks up the change immediately. This workflow is useful during effect development.

## If something goes wrong

- **Autostart doesn't work after reboot:** Check that your desktop environment supports XDG autostart. See [Troubleshooting](../troubleshooting.md#start-on-login-doesnt-work).
- **Standalone effect says "No Razer devices found":** The OpenRazer daemon isn't running. Start it with `systemctl --user start openrazer-daemon`.
- **Two effects running simultaneously:** If the tray app is already running an effect and you start one standalone, they'll fight over the keyboard (last draw wins each frame). Stop one before starting the other.

## What to try next

- Explore all 28 effects: [Effects Guide](../../EFFECTS.md)
- Write your own effect: [Tutorial 4](04-writing-a-custom-effect.md)
- Customize colors: [Tutorial 3](03-customizing-colors.md)
