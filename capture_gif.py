#!/usr/bin/env python3
"""Capture an effect as an animated GIF using the virtual device and PIL rendering."""

import importlib.util
import os
import sys
import threading
import time

from PIL import Image, ImageDraw, ImageFont

EFFECTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "effects")
SCREENSHOTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshots")

# Keyboard layout matching config_window.py
KEYBOARD_LAYOUT = [
    [("Esc", 0, 1.0), ("F1", 1, 1.0), ("F2", 2, 1.0), ("F3", 3, 1.0), ("F4", 4, 1.0),
     ("F5", 5, 1.0), ("F6", 6, 1.0), ("F7", 7, 1.0), ("F8", 8, 1.0), ("F9", 9, 1.0),
     ("F10", 10, 1.0), ("F11", 11, 1.0), ("F12", 12, 1.0), ("Del", 13, 1.0)],
    [("`", 0, 1.0), ("1", 1, 1.0), ("2", 2, 1.0), ("3", 3, 1.0), ("4", 4, 1.0),
     ("5", 5, 1.0), ("6", 6, 1.0), ("7", 7, 1.0), ("8", 8, 1.0), ("9", 9, 1.0),
     ("0", 10, 1.0), ("-", 11, 1.0), ("=", 12, 1.0), ("Bksp", 13, 2.0)],
    [("Tab", 0, 1.5), ("Q", 1, 1.0), ("W", 2, 1.0), ("E", 3, 1.0), ("R", 4, 1.0),
     ("T", 5, 1.0), ("Y", 6, 1.0), ("U", 7, 1.0), ("I", 8, 1.0), ("O", 9, 1.0),
     ("P", 10, 1.0), ("[", 11, 1.0), ("]", 12, 1.0), ("\\", 13, 1.5)],
    [("Caps", 0, 1.75), ("A", 1, 1.0), ("S", 2, 1.0), ("D", 3, 1.0), ("F", 4, 1.0),
     ("G", 5, 1.0), ("H", 6, 1.0), ("J", 7, 1.0), ("K", 8, 1.0), ("L", 9, 1.0),
     (";", 10, 1.0), ("'", 11, 1.0), ("Enter", 12, 2.25)],
    [("Shift", 0, 2.25), ("Z", 1, 1.0), ("X", 2, 1.0), ("C", 3, 1.0), ("V", 4, 1.0),
     ("B", 5, 1.0), ("N", 6, 1.0), ("M", 7, 1.0), (",", 8, 1.0), (".", 9, 1.0),
     ("/", 10, 1.0), ("Shift", 11, 1.75), ("\u2191", 12, 1.0)],
    [("Ctrl", 0, 1.25), ("Fn", 1, 1.0), ("Super", 2, 1.25), ("Alt", 3, 1.25),
     ("Space", 4, 6.25), ("Alt", 9, 1.0), ("Ctrl", 10, 1.0),
     ("\u2190", 11, 1.0), ("\u2193", 12, 1.0), ("\u2192", 13, 1.0)],
]

GAP = 0.08
ROW_HEIGHT = 1.0


def compute_key_rects():
    """Compute key layout as list of dicts with unit-space coordinates."""
    keys = []
    for row_idx, row_keys in enumerate(KEYBOARD_LAYOUT):
        x = 0.0
        for label, col_idx, width_u in row_keys:
            keys.append({
                "label": label,
                "row": row_idx,
                "col": col_idx,
                "x": x,
                "y": row_idx * (ROW_HEIGHT + GAP),
                "w": width_u - GAP,
                "h": ROW_HEIGHT,
            })
            x += width_u
    return keys


def render_frame(frame_data, key_rects, width=640, height=375):
    """Render a keyboard frame to a PIL Image."""
    img = Image.new("RGB", (width, height), (10, 10, 10))
    draw = ImageDraw.Draw(img)

    max_x = max(k["x"] + k["w"] for k in key_rects)
    max_y = max(k["y"] + k["h"] for k in key_rects)

    pad = 8
    avail_w = width - 2 * pad
    avail_h = height - 2 * pad
    scale_x = avail_w / max_x if max_x > 0 else 1
    scale_y = avail_h / max_y if max_y > 0 else 1
    scale = min(scale_x, scale_y)

    total_w = max_x * scale
    total_h = max_y * scale
    offset_x = pad + (avail_w - total_w) / 2
    offset_y = pad + (avail_h - total_h) / 2

    corner = max(2, min(int(3 * scale / 20), 6))

    for key in key_rects:
        row, col = key["row"], key["col"]
        kx = int(offset_x + key["x"] * scale)
        ky = int(offset_y + key["y"] * scale)
        kw = int(key["w"] * scale)
        kh = int(key["h"] * scale)

        if row < len(frame_data) and col < len(frame_data[row]):
            r, g, b = frame_data[row][col]
        else:
            r, g, b = 0, 0, 0

        draw.rounded_rectangle(
            [kx, ky, kx + kw, ky + kh],
            radius=corner,
            fill=(r, g, b),
            outline=(max(0, r - 30), max(0, g - 30), max(0, b - 30)),
        )

    return img


def load_effect(name):
    """Load an effect module by filename (without .py)."""
    path = os.path.join(EFFECTS_DIR, name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def capture(effect_name, duration=5.0, config_overrides=None):
    """Capture an effect as an animated GIF.

    config_overrides: dict of config values to override for the capture.
    """
    from virtual_device import VirtualDevice

    module = load_effect(effect_name)

    # Apply config overrides by writing a temp config
    original_config_path = getattr(module, "CONFIG_PATH", None)
    if config_overrides and original_config_path:
        import tempfile
        with open(original_config_path) as f:
            config_source = f.read()
        # Append overrides
        lines = [config_source, "\n# Capture overrides\n"]
        for k, v in config_overrides.items():
            lines.append(f"{k} = {repr(v)}\n")
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
        tmp.write("".join(lines))
        tmp.close()
        module.CONFIG_PATH = tmp.name

    frames = []
    lock = threading.Lock()
    key_rects = compute_key_rects()

    def on_draw(snapshot):
        with lock:
            frames.append(render_frame(snapshot, key_rects))

    device = VirtualDevice(6, 16, on_draw=on_draw)
    stop_event = threading.Event()

    thread = threading.Thread(target=module.run, args=(device, stop_event), daemon=True)
    thread.start()

    print(f"Capturing {effect_name} for {duration}s...")
    time.sleep(duration)
    stop_event.set()
    thread.join(timeout=3)

    # Restore original config path
    if config_overrides and original_config_path:
        os.unlink(module.CONFIG_PATH)
        module.CONFIG_PATH = original_config_path

    if not frames:
        print("No frames captured!")
        return

    # Compute frame duration from FPS
    fps = 20
    frame_ms = max(20, int(1000 / fps))

    # Limit to reasonable frame count (skip frames if too many)
    max_frames = 80
    if len(frames) > max_frames:
        step = len(frames) / max_frames
        frames = [frames[int(i * step)] for i in range(max_frames)]

    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
    out_path = os.path.join(SCREENSHOTS_DIR, f"{effect_name}.gif")

    frames[0].save(
        out_path,
        save_all=True,
        append_images=frames[1:],
        duration=frame_ms,
        loop=0,
        optimize=True,
    )
    print(f"Saved {out_path} ({len(frames)} frames, {frame_ms}ms/frame)")


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <effect_name> [duration_secs] [key=value ...]")
        print(f"Example: {sys.argv[0]} lightning_strike 8 INTERVAL_MIN=0.3 INTERVAL_MAX=1.0")
        sys.exit(1)

    effect_name = sys.argv[1]
    duration = float(sys.argv[2]) if len(sys.argv) > 2 else 5.0

    overrides = {}
    for arg in sys.argv[3:]:
        if "=" in arg:
            k, v = arg.split("=", 1)
            try:
                overrides[k] = eval(v)
            except Exception:
                overrides[k] = v

    capture(effect_name, duration, overrides if overrides else None)


if __name__ == "__main__":
    main()
