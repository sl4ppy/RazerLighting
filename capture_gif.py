#!/usr/bin/env python3
"""Capture an effect as an animated GIF using the virtual device and PIL rendering."""

import ast
import importlib.util
import os
import sys
import threading
import time

from PIL import Image, ImageDraw, ImageFont

from keyboard_layout import compute_key_rects

EFFECTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "effects")
SCREENSHOTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshots")


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
        col = key["col"]
        kx = int(offset_x + key["x"] * scale)
        ky = int(offset_y + key["y"] * scale)
        kw = int(key["w"] * scale)
        kh = int(key["h"] * scale)

        mrow = key.get("matrix_row", key["row"])
        if mrow < len(frame_data) and col < len(frame_data[mrow]):
            r, g, b = frame_data[mrow][col]
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
                overrides[k] = ast.literal_eval(v)
            except (ValueError, SyntaxError):
                overrides[k] = v

    capture(effect_name, duration, overrides if overrides else None)


if __name__ == "__main__":
    main()
