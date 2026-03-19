"""Razer Blade 14 (2021) keyboard layout data and key-rect computation.

Used by config_window.py (live preview) and capture_gif.py (GIF rendering).

Currently hardcoded to the Razer Blade 14 (2021) layout.  Effects render
to whatever matrix size OpenRazer reports, so they work on any device —
but the visual preview and GIF capture always show this layout.  Native
support for additional device layouts is planned for the future.
"""

# Razer Blade 14 2021 keyboard layout (from Polychromatic SVG / OpenRazer matrix)
#
# Standard key:   (label, matrix_col, width)
# Row override:   (label, matrix_col, width, matrix_row)
# Half-height:    (label, matrix_col, width, matrix_row, height, y_offset)
# No-advance:     (label, matrix_col, width, matrix_row, height, y_offset, 0)
# Spacer (gap):   (None, -1, width)   — advances x, draws nothing
#
# Column 0 is unused (legacy macro key position). Physical keys use cols 1–15.
# The spacebar has no LED on this model.
# ↑ (col 13) and ↓ (col 15) are half-height keys stacked in the same cell.
KEYBOARD_LAYOUT = [
    # Row 0: Function row (15 keys, all 1u)
    [("Esc", 1, 1.0), ("F1", 2, 1.0), ("F2", 3, 1.0), ("F3", 4, 1.0), ("F4", 5, 1.0),
     ("F5", 6, 1.0), ("F6", 7, 1.0), ("F7", 8, 1.0), ("F8", 9, 1.0), ("F9", 10, 1.0),
     ("F10", 11, 1.0), ("F11", 12, 1.0), ("F12", 13, 1.0), ("Ins", 14, 1.0),
     ("Del", 15, 1.0)],
    # Row 1: Number row (14 keys)
    [("`", 1, 1.0), ("1", 2, 1.0), ("2", 3, 1.0), ("3", 4, 1.0), ("4", 5, 1.0),
     ("5", 6, 1.0), ("6", 7, 1.0), ("7", 8, 1.0), ("8", 9, 1.0), ("9", 10, 1.0),
     ("0", 11, 1.0), ("-", 12, 1.0), ("=", 13, 1.0), ("Bksp", 15, 2.0)],
    # Row 2: QWERTY top (14 keys)
    [("Tab", 1, 1.5), ("Q", 2, 1.0), ("W", 3, 1.0), ("E", 4, 1.0), ("R", 5, 1.0),
     ("T", 6, 1.0), ("Y", 7, 1.0), ("U", 8, 1.0), ("I", 9, 1.0), ("O", 10, 1.0),
     ("P", 11, 1.0), ("[", 12, 1.0), ("]", 13, 1.0), ("\\", 15, 1.5)],
    # Row 3: Home row (13 keys)
    [("Caps", 1, 1.75), ("A", 2, 1.0), ("S", 3, 1.0), ("D", 4, 1.0), ("F", 5, 1.0),
     ("G", 6, 1.0), ("H", 7, 1.0), ("J", 8, 1.0), ("K", 9, 1.0), ("L", 10, 1.0),
     (";", 11, 1.0), ("'", 12, 1.0), ("Enter", 15, 2.25)],
    # Row 4: Shift row (12 keys — RShift extends to right edge)
    [("Shift", 1, 2.0), ("Z", 3, 1.0), ("X", 4, 1.0), ("C", 5, 1.0), ("V", 6, 1.0),
     ("B", 7, 1.0), ("N", 8, 1.0), ("M", 9, 1.0), (",", 10, 1.0), (".", 11, 1.0),
     ("/", 12, 1.0), ("Shift", 15, 3.0)],
    # Row 5: Bottom row (no spacebar LED; ↑/↓ half-height stacked)
    [("Ctrl", 1, 1.0), ("Fn", 2, 1.0), ("Super", 3, 1.0), ("Alt", 5, 1.0),
     (None, -1, 5.0),
     ("Alt", 9, 1.0), ("Fn", 10, 1.0), ("Ctrl", 11, 1.0),
     ("\u2190", 12, 1.0),
     ("\u2191", 13, 1.0, 5, 0.46, 0.0, 0.0),
     ("\u2193", 15, 1.0, 5, 0.46, 0.54),
     ("\u2192", 14, 1.0)],
]

GAP = 0.08
ROW_HEIGHT = 1.0


def compute_key_rects():
    """Compute key positions as list of dicts with unit-space coordinates.

    Each dict has: label, row (visual), col (matrix column), matrix_row,
    x, y, w, h — all in unit coordinates.
    """
    keys = []
    for row_idx, row_keys in enumerate(KEYBOARD_LAYOUT):
        x = 0.0
        for key_def in row_keys:
            label = key_def[0]
            width_u = key_def[2]
            if label is None:
                x += width_u  # spacer — advance position only
                continue
            n = len(key_def)
            col_idx = key_def[1]
            matrix_row = key_def[3] if n > 3 else row_idx
            h = key_def[4] if n > 4 else ROW_HEIGHT
            y_off = key_def[5] if n > 5 else 0.0
            x_advance = key_def[6] if n > 6 else width_u
            keys.append({
                "label": label,
                "row": row_idx,
                "col": col_idx,
                "matrix_row": matrix_row,
                "x": x,
                "y": row_idx * (ROW_HEIGHT + GAP) + y_off,
                "w": width_u - GAP,
                "h": h,
            })
            x += x_advance
    return keys
