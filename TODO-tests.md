# Test Suite Plan

Priority order for adding tests. No tests currently exist.

## 1. config_parser.py (highest priority)
- `_infer_type()`: all 8 type categories (int, float, bool, rgb, palette, float_list, int_list, tuple_list), edge cases (empty lists, mixed int/float lists, tuples that aren't RGB)
- `_infer_range()`: all 10 priority rules (FPS, probability keywords, position suffixes, threshold, count, speed/rate, scale/ratio, width/radius, sharpness/intensity, fallback), edge cases (zero values, negative values, very small floats)
- `parse_config()`: round-trip parsing of all parameter types, inline comment extraction, multi-line value handling, skipping of dunder/private names
- `write_config()`: round-trip preservation (parse → modify → write → parse gives expected values), comment preservation, atomic write behavior, multi-line palette formatting
- `write_temp_config()`: temp file creation, content matches expectations
- `group_params()`: correct categorization into Timing/Colors/Simulation/Other
- `humanize_name()`: UPPER_SNAKE_CASE → Title Case

## 2. effects/common.py
- `build_palette_lut()`: single-color palette, two-color gradient, multi-stop, empty palette
- `palette_lookup()`: boundary values (0.0, 1.0), array shapes
- `sample_palette()`: interpolation accuracy, wrapping behavior
- `lerp_color()`: t=0, t=1, t=0.5, clamping
- `frame_sleep()`: returns correct next deadline, handles behind-schedule case
- `laplacian_4pt()` / `laplacian_9pt()` / `laplacian_4pt_open()`: known inputs → expected outputs, boundary wrapping
- `blur_3x3()`: uniform input stays uniform, wrapping behavior
- `discover_effects()`: finds .py files, excludes _config.py and common.py, requires run() attribute

## 3. config_widgets.py
- Widget factory `create_param_widget()`: returns correct widget type for each param_type, returns None for unknown
- Value round-trip: `set_value()` → `get_value()` for each widget type

## 4. virtual_device.py
- `VirtualDevice`: matrix read/write, bounds checking, draw callback fires with correct snapshot
- `detect_dimensions()`: fallback when no device available

## 5. keyboard_layout.py
- `compute_key_rects()`: all keys present, no overlaps, correct matrix_row mappings for arrow keys

## Framework
- pytest (add to requirements.txt as dev dependency)
- No hardware needed: virtual_device.py covers device mocking
- No GUI needed for parser/common tests; widget tests need QApplication fixture
