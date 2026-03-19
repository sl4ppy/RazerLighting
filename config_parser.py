"""Parse, infer metadata, and write back effect config files."""

import ast
import json
import os
import re
import tempfile
from dataclasses import dataclass, field
from typing import Any

STATE_DIR = os.path.expanduser("~/.local/state/razer-lighting")
DEFAULTS_DIR = os.path.join(STATE_DIR, "defaults")


@dataclass
class ConfigParam:
    name: str
    value: Any
    param_type: str  # 'int', 'float', 'bool', 'rgb', 'palette', 'float_list', 'int_list', 'tuple_list'
    line_number: int  # 1-based
    comment: str = ""
    range_min: float = 0.0
    range_max: float = 1.0
    range_step: float = 0.01
    tooltip: str = ""


# ─── Per-parameter tooltip descriptions ───────────────────────────────────────
# Keys: (config_basename_without_ext, PARAM_NAME) → description
# Falls back to generic name-based tooltips if not found here.

PARAM_TOOLTIPS = {
    # ── Arc Sweep ──
    ("arc_sweep_config", "FPS"): "Animation frame rate. Higher values give smoother motion but use more CPU.",
    ("arc_sweep_config", "SPEED_MIN"): "Minimum arc travel speed. Slower arcs create a more gentle sweep.",
    ("arc_sweep_config", "SPEED_MAX"): "Maximum arc travel speed. Faster arcs create a more energetic sweep.",
    ("arc_sweep_config", "PAUSE_MIN"): "Minimum pause between spawning new arcs (seconds).",
    ("arc_sweep_config", "PAUSE_MAX"): "Maximum pause between spawning new arcs (seconds).",
    ("arc_sweep_config", "CENTER_COLOR"): "Color of the bright leading edge of the arc.",
    ("arc_sweep_config", "EDGE_COLOR"): "Color of the arc edges, flanking the center line.",
    ("arc_sweep_config", "TRAIL"): "Gradient colors trailing behind the arc, from nearest to farthest.",
    ("arc_sweep_config", "ROW_OFFSETS"): "Per-row column offset. Creates the curved wavefront shape. Row 0 leads.",

    # ── Binary Cascade ──
    ("binary_cascade_config", "FPS"): "Animation frame rate. Higher values give smoother falling streams.",
    ("binary_cascade_config", "STREAM_SPAWN_CHANCE"): "Probability per column per frame to spawn a new falling stream.",
    ("binary_cascade_config", "MAX_STREAMS"): "Maximum number of simultaneous falling streams on screen.",
    ("binary_cascade_config", "SPEED_MIN"): "Minimum stream fall speed (cells per frame).",
    ("binary_cascade_config", "SPEED_MAX"): "Maximum stream fall speed (cells per frame).",
    ("binary_cascade_config", "TRAIL_LENGTH_MIN"): "Minimum length of the fading trail behind each stream head.",
    ("binary_cascade_config", "TRAIL_LENGTH_MAX"): "Maximum length of the fading trail behind each stream head.",
    ("binary_cascade_config", "BG_COLOR"): "Dark background color. A subtle glow behind the falling streams.",
    ("binary_cascade_config", "HEAD_COLOR"): "Color of the leading character at the head of each stream.",
    ("binary_cascade_config", "BRIGHT_COLOR"): "Brightest body color of the stream, just behind the head.",
    ("binary_cascade_config", "MID_COLOR"): "Mid-brightness body color in the stream trail.",
    ("binary_cascade_config", "DIM_COLOR"): "Dimmest body color at the tail end of the stream.",
    ("binary_cascade_config", "GLINT_COLOR"): "Color of random sparkle glints on visible stream cells.",
    ("binary_cascade_config", "GLINT_CHANCE"): "Probability of a cyan sparkle glint per visible cell per frame.",

    # ── Chladni Patterns ──
    ("chladni_config", "FPS"): "Animation frame rate for the vibrating plate simulation.",
    ("chladni_config", "NODAL_WIDTH"): "Width of the nodal lines (Gaussian spread). Larger values make thicker lines.",
    ("chladni_config", "MORPH_SPEED"): "Speed of transition between Chladni mode pairs. Controls how fast patterns change.",
    ("chladni_config", "PULSE_SPEED"): "Speed of the breathing brightness pulse overlay.",
    ("chladni_config", "MODE_PAIRS"): "List of (n, m) Chladni mode pairs to cycle through. Each creates a unique nodal pattern.",
    ("chladni_config", "LINE_COLOR"): "Color of the bright nodal lines on the vibrating plate.",
    ("chladni_config", "BG_COLOR"): "Dark background color between the nodal lines.",

    # ── Crystal Growth ──
    ("crystal_growth_config", "FPS"): "Animation frame rate for the crystal growth simulation.",
    ("crystal_growth_config", "MAX_WALKERS"): "Maximum number of DLA random walkers moving simultaneously.",
    ("crystal_growth_config", "WALK_STEPS"): "Number of random walk steps per walker per animation cycle.",
    ("crystal_growth_config", "MAX_ATTACH_PER_FRAME"): "Cap on new crystal cells per frame. Limits growth speed for visible buildup.",
    ("crystal_growth_config", "FILL_THRESHOLD"): "Fraction of grid filled before the crystal resets and regrows (0-1).",
    ("crystal_growth_config", "FLASH_FRAMES"): "Duration of the white flash when a new cell attaches to the crystal.",
    ("crystal_growth_config", "PALETTE"): "Colors applied to crystal cells by attachment order (early → late growth).",
    ("crystal_growth_config", "BG_COLOR"): "Background color for empty cells.",

    # ── Cyclic Cellular Automaton ──
    ("cyclic_cellular_config", "FPS"): "Animation frame rate for the cellular automaton.",
    ("cyclic_cellular_config", "NUM_STATES"): "Number of states in the cycle. More states create a wider rainbow palette.",
    ("cyclic_cellular_config", "THRESHOLD"): "Number of next-state neighbors needed to advance. Higher values slow propagation.",
    ("cyclic_cellular_config", "SIM_STEPS_PER_FRAME"): "Simulation iterations per rendered frame. Higher values speed up evolution.",
    ("cyclic_cellular_config", "STAGNATION_FRAMES"): "Frames with no state changes before the grid reseeds with fresh random data.",

    # ── Fireflies ──
    ("fireflies_config", "FPS"): "Animation frame rate for the firefly simulation.",
    ("fireflies_config", "MEAN_FREQ"): "Average oscillation frequency of the firefly blinking cycle.",
    ("fireflies_config", "FREQ_SPREAD"): "Spread (std deviation) of individual firefly frequencies around the mean.",
    ("fireflies_config", "COUPLING"): "Kuramoto coupling strength. Higher values make fireflies synchronize faster.",
    ("fireflies_config", "COUPLING_SPEED"): "Speed of coupling oscillation between sync and chaos phases.",
    ("fireflies_config", "FLASH_SHARPNESS"): "Exponent for phase-to-brightness mapping. Higher values make sharper, briefer flashes.",
    ("fireflies_config", "DIM_COLOR"): "Color when a firefly is at its dimmest (between flashes).",
    ("fireflies_config", "MID_COLOR"): "Color at mid-brightness during the flash cycle.",
    ("fireflies_config", "BRIGHT_COLOR"): "Color at high brightness, just before peak flash.",
    ("fireflies_config", "FLASH_COLOR"): "Peak flash color — the brightest moment of the blink.",

    # ── Fractal Zoom ──
    ("fractal_zoom_config", "FPS"): "Animation frame rate for the fractal zoom.",
    ("fractal_zoom_config", "ZOOM_SPEED"): "How fast the zoom progresses per frame. Higher values zoom faster.",
    ("fractal_zoom_config", "ZOOM_RANGE"): "Total zoom depth before the view resets and starts over.",
    ("fractal_zoom_config", "ROTATION_SPEED"): "Slow rotation per frame (radians). Adds a spiral effect to the zoom.",
    ("fractal_zoom_config", "MAX_ITER"): "Mandelbrot iteration depth. Higher values reveal more fractal detail but render slower.",
    ("fractal_zoom_config", "CENTER_RE"): "Real-axis center of the fractal view. Changes which area of the set you zoom into.",
    ("fractal_zoom_config", "CENTER_IM"): "Imaginary-axis center of the fractal view.",
    ("fractal_zoom_config", "JULIA_MODE"): "When enabled, renders a Julia set instead of the Mandelbrot set.",
    ("fractal_zoom_config", "JULIA_C_RE"): "Real part of the Julia constant. Different values create dramatically different patterns.",
    ("fractal_zoom_config", "JULIA_C_IM"): "Imaginary part of the Julia constant.",
    ("fractal_zoom_config", "PALETTE"): "Color gradient sampled by iteration count. Defines the fractal's visual character.",
    ("fractal_zoom_config", "INSIDE_COLOR"): "Color for points inside the Mandelbrot/Julia set (infinite iterations).",
    ("fractal_zoom_config", "PULSE"): "Enable a slow breathing brightness pulse overlaid on the fractal.",
    ("fractal_zoom_config", "PULSE_SPEED"): "Speed of the breathing brightness pulse.",
    ("fractal_zoom_config", "PULSE_AMOUNT"): "Depth of brightness modulation from the pulse (0 = none, 1 = full).",

    # ── Glitch ──
    ("glitch_config", "FPS"): "Animation frame rate for the glitch effect.",
    ("glitch_config", "IDLE_COLOR"): "Dim baseline color shown during quiet periods between glitch bursts.",
    ("glitch_config", "IDLE_MIN"): "Minimum seconds of quiet between glitch bursts.",
    ("glitch_config", "IDLE_MAX"): "Maximum seconds of quiet between glitch bursts.",
    ("glitch_config", "BURST_FRAMES_MIN"): "Minimum duration of a glitch burst (in frames).",
    ("glitch_config", "BURST_FRAMES_MAX"): "Maximum duration of a glitch burst (in frames).",
    ("glitch_config", "BURST_DENSITY_MIN"): "Minimum fraction of keys affected per frame during a burst.",
    ("glitch_config", "BURST_DENSITY_MAX"): "Maximum fraction of keys affected per frame during a burst.",
    ("glitch_config", "CORRUPTION_CHANCE"): "Probability of a row-shift corruption per frame during a burst.",
    ("glitch_config", "ROW_SHIFT_MAX"): "Maximum columns a row can shift horizontally during corruption.",
    ("glitch_config", "SCANLINE_CHANCE"): "Probability of a bright horizontal scanline flashing across a row.",
    ("glitch_config", "GLITCH_COLORS"): "Palette of colors used for corrupted pixels during glitch bursts.",
    ("glitch_config", "MULTI_BURST_CHANCE"): "Chance of rapid successive bursts firing back-to-back.",
    ("glitch_config", "MULTI_BURST_GAP_MIN"): "Minimum gap between rapid successive bursts (seconds).",
    ("glitch_config", "MULTI_BURST_GAP_MAX"): "Maximum gap between rapid successive bursts (seconds).",

    # ── Heat Diffusion ──
    ("heat_diffusion_config", "FPS"): "Animation frame rate for the heat simulation.",
    ("heat_diffusion_config", "DIFFUSION_RATE"): "How fast heat spreads to neighboring cells. Higher values create faster diffusion.",
    ("heat_diffusion_config", "COOLING"): "Heat decay per frame. Higher values make hot spots cool down faster.",
    ("heat_diffusion_config", "IGNITION_CHANCE"): "Probability of a new random heat source appearing each frame.",
    ("heat_diffusion_config", "IGNITION_HEAT"): "Temperature value of new heat sources (1.0 = maximum heat).",
    ("heat_diffusion_config", "PALETTE"): "Hot iron color gradient: black → red → orange → yellow → white.",

    # ── Lightning Strike ──
    ("lightning_strike_config", "FPS"): "Animation frame rate for lightning rendering.",
    ("lightning_strike_config", "INTERVAL_MIN"): "Minimum seconds between lightning bolt events.",
    ("lightning_strike_config", "INTERVAL_MAX"): "Maximum seconds between lightning bolt events.",
    ("lightning_strike_config", "MULTI_BOLT_CHANCE"): "Probability of a multi-bolt storm (2-3 bolts in quick succession).",
    ("lightning_strike_config", "MULTI_BOLT_GAP_MIN"): "Minimum gap between bolts in a multi-bolt storm (seconds).",
    ("lightning_strike_config", "MULTI_BOLT_GAP_MAX"): "Maximum gap between bolts in a multi-bolt storm (seconds).",
    ("lightning_strike_config", "BOLT_WANDER"): "Column offset weights per row. Controls how much the bolt zigzags horizontally.",
    ("lightning_strike_config", "BRANCH_CHANCE"): "Probability of a branch splitting off the main bolt at each row.",
    ("lightning_strike_config", "BRANCH_MAX_LENGTH"): "Maximum horizontal extent of a branch (in columns).",
    ("lightning_strike_config", "RESTRIKE_CHANCE"): "Probability of a re-flash along the same bolt path after the initial strike.",
    ("lightning_strike_config", "RESTRIKE_GAP_MIN"): "Minimum dark frames before a restrike flash.",
    ("lightning_strike_config", "RESTRIKE_GAP_MAX"): "Maximum dark frames before a restrike flash.",
    ("lightning_strike_config", "SURGE_CHANCE"): "Probability of a surge flicker after a restrike — a lingering electric glow.",
    ("lightning_strike_config", "BOLT_COLOR"): "Color of the main bolt core — typically bright white.",
    ("lightning_strike_config", "GLOW_COLOR"): "Ambient background glow color during a bolt strike.",
    ("lightning_strike_config", "GLOW_DIM_COLOR"): "Darker ambient glow during sustain frames after the initial flash.",
    ("lightning_strike_config", "BRANCH_COLOR"): "Color of branch forks splitting off the main bolt.",
    ("lightning_strike_config", "BRANCH_DIM_COLOR"): "Faded color of branches as they dissipate.",
    ("lightning_strike_config", "SURGE_COLOR"): "Color of the lingering surge pulse after a restrike.",

    # ── Lissajous ──
    ("lissajous_config", "FPS"): "Animation frame rate for the Lissajous curve tracer.",
    ("lissajous_config", "FREQ_X"): "Horizontal oscillation frequency. Changing this alters the curve shape.",
    ("lissajous_config", "FREQ_Y"): "Vertical oscillation frequency. The ratio of X:Y determines the pattern.",
    ("lissajous_config", "PHASE_SPEED"): "Speed of phase shift (radians/frame). Morphs the curve shape over time.",
    ("lissajous_config", "ANIM_SPEED"): "Speed of the dot traveling along the curve (radians/frame).",
    ("lissajous_config", "TRAIL_LENGTH"): "Number of trailing dots behind the moving head.",
    ("lissajous_config", "TRAIL_FADE"): "Enable fading brightness along the trail from head to tail.",
    ("lissajous_config", "BG_COLOR"): "Dark background color behind the curve.",
    ("lissajous_config", "HEAD_COLOR"): "Color of the leading dot at the head of the curve.",
    ("lissajous_config", "TRAIL_COLOR"): "Brightest trail color, just behind the head.",
    ("lissajous_config", "DIM_TRAIL_COLOR"): "Faintest trail color at the tail end.",
    ("lissajous_config", "GLOW_RADIUS"): "Radius of the soft glow around the moving dot (in key units).",
    ("lissajous_config", "GLOW_COLOR"): "Color of the glow halo around the dot.",
    ("lissajous_config", "MORPH"): "Enable periodic random changes to the frequency ratio, creating new patterns.",
    ("lissajous_config", "MORPH_INTERVAL"): "Seconds between random frequency changes when morphing is enabled.",

    # ── Magnetic Field ──
    ("magnetic_field_config", "FPS"): "Animation frame rate for the magnetic field visualization.",
    ("magnetic_field_config", "NUM_POLES"): "Number of magnetic poles drifting across the keyboard.",
    ("magnetic_field_config", "POLE_SPEED"): "Speed at which poles drift around the keyboard.",
    ("magnetic_field_config", "POLE_GLOW_RADIUS"): "Radius of the bright glow around each pole (in key units).",
    ("magnetic_field_config", "POLE_GLOW_INTENSITY"): "Brightness multiplier for the pole glow effect.",
    ("magnetic_field_config", "NUM_LINES"): "Number of field lines rendered between poles.",
    ("magnetic_field_config", "FIELD_SCALE"): "Scaling factor for field line step size. Affects line density.",
    ("magnetic_field_config", "LINE_COLOR"): "Color of the iron-filing field lines.",
    ("magnetic_field_config", "POS_POLE_COLOR"): "Glow color for positive magnetic poles.",
    ("magnetic_field_config", "NEG_POLE_COLOR"): "Glow color for negative magnetic poles.",
    ("magnetic_field_config", "BG_COLOR"): "Dark background color.",

    # ── Metaballs ──
    ("metaballs_config", "FPS"): "Animation frame rate for the metaball simulation.",
    ("metaballs_config", "NUM_BLOBS"): "Number of metaball blobs floating around the keyboard.",
    ("metaballs_config", "BLOB_RADIUS"): "Influence radius of each blob. Larger values create bigger blobs.",
    ("metaballs_config", "SPEED"): "Movement speed of the blobs along their Lissajous paths.",
    ("metaballs_config", "ASPECT_RATIO"): "Aspect ratio correction for the keyboard shape (width/height).",
    ("metaballs_config", "THRESHOLD"): "Field strength threshold for blob surface rendering. Lower values make blobs larger.",
    ("metaballs_config", "PALETTE"): "Molten lava color gradient sampled by field strength.",

    # ── Physarum ──
    ("physarum_config", "FPS"): "Animation frame rate for the slime mold simulation.",
    ("physarum_config", "NUM_AGENTS"): "Number of slime mold agents depositing trails on the surface.",
    ("physarum_config", "SENSOR_ANGLE"): "Angle between each agent's left and right sensors (radians). Affects trail pattern width.",
    ("physarum_config", "SENSOR_DIST"): "Distance ahead that agents sense pheromone trails. Longer distances create wider patterns.",
    ("physarum_config", "TURN_SPEED"): "How sharply agents turn toward detected pheromone (radians/step).",
    ("physarum_config", "MOVE_SPEED"): "Agent movement speed per frame.",
    ("physarum_config", "DEPOSIT_AMOUNT"): "Amount of pheromone each agent deposits per step. Higher values create brighter trails.",
    ("physarum_config", "DECAY_RATE"): "Pheromone decay multiplier per frame (0-1). Lower values make trails fade faster.",
    ("physarum_config", "BUFFER_SCALE"): "Internal buffer resolution multiplier. Higher values give finer detail.",
    ("physarum_config", "PALETTE"): "Bioluminescent color gradient from dark to bright (sampled by trail intensity).",

    # ── Plasma ──
    ("plasma_config", "FPS"): "Animation frame rate for the plasma effect.",
    ("plasma_config", "SCALE_X"): "Horizontal spatial frequency of the plasma waves. Higher values create tighter patterns.",
    ("plasma_config", "SCALE_Y"): "Vertical spatial frequency of the plasma waves.",
    ("plasma_config", "TIME_SPEED"): "Animation speed (radians/frame). How fast the plasma swirls.",
    ("plasma_config", "PALETTE"): "Color palette sampled along the plasma gradient. Defines the visual character.",
    ("plasma_config", "OVERLAY"): "Enable a second plasma layer blended on top for added complexity.",
    ("plasma_config", "OVERLAY_SCALE_X"): "Horizontal frequency of the overlay plasma layer.",
    ("plasma_config", "OVERLAY_SCALE_Y"): "Vertical frequency of the overlay plasma layer.",
    ("plasma_config", "OVERLAY_TIME_SPEED"): "Animation speed of the overlay layer.",
    ("plasma_config", "OVERLAY_BLEND"): "Blend weight of the overlay layer (0 = hidden, 1 = fully visible).",

    # ── Reaction-Diffusion ──
    ("reaction_diffusion_config", "FPS"): "Animation frame rate for the reaction-diffusion simulation.",
    ("reaction_diffusion_config", "FEED"): "Gray-Scott feed rate. Controls how fast chemical A is replenished. Tiny changes have big effects.",
    ("reaction_diffusion_config", "KILL"): "Gray-Scott kill rate. Controls how fast chemical B decays. Tiny changes have big effects.",
    ("reaction_diffusion_config", "D_A"): "Diffusion coefficient for chemical A. How fast A spreads spatially.",
    ("reaction_diffusion_config", "D_B"): "Diffusion coefficient for chemical B. How fast B spreads (usually slower than A).",
    ("reaction_diffusion_config", "SIM_STEPS"): "Simulation iterations per rendered frame. More steps speed up pattern evolution.",
    ("reaction_diffusion_config", "PALETTE"): "Bioluminescent color gradient sampled by chemical B concentration.",
    ("reaction_diffusion_config", "RESEED_THRESHOLD"): "When total B drops below this, the simulation reseeds with fresh spots.",

    # ── Searchlight ──
    ("searchlight_config", "FPS"): "Animation frame rate for the searchlight beam.",
    ("searchlight_config", "SWEEP_SPEED"): "Beam rotation speed (radians/frame). How fast the searchlight sweeps.",
    ("searchlight_config", "BEAM_WIDTH"): "Angular width of the light beam (radians). Wider beams illuminate more keys.",
    ("searchlight_config", "BEAM_FALLOFF"): "Edge sharpness of the beam. Higher values create a harder, more defined edge.",
    ("searchlight_config", "ORIGIN_X"): "Horizontal origin of the beam (0 = left edge, 0.5 = center, 1 = right edge).",
    ("searchlight_config", "ORIGIN_Y"): "Vertical origin of the beam (0 = top, 0.5 = center, 1 = bottom).",
    ("searchlight_config", "BG_COLOR"): "Ambient background color when the beam is pointing away.",
    ("searchlight_config", "BEAM_CORE_COLOR"): "Brightest color at the center of the beam.",
    ("searchlight_config", "BEAM_MID_COLOR"): "Mid-brightness color between beam center and edge.",
    ("searchlight_config", "BEAM_EDGE_COLOR"): "Color at the fading edge of the beam.",
    ("searchlight_config", "AMBIENT_COLOR"): "Subtle ambient color that tints the background.",
    ("searchlight_config", "FLICKER"): "Enable subtle random brightness variation to simulate a real light source.",
    ("searchlight_config", "FLICKER_AMOUNT"): "Maximum brightness variation from flicker (0 = steady, 1 = extreme).",

    # ── Tidal Swell ──
    ("tidal_swell_config", "FPS"): "Animation frame rate for the ocean wave simulation.",
    ("tidal_swell_config", "WAVE_SPEED"): "How fast waves scroll across the keyboard (radians/frame).",
    ("tidal_swell_config", "WAVE_COUNT"): "Number of wave crests visible across the keyboard at once.",
    ("tidal_swell_config", "SWELL_SPEED"): "Speed of the slow vertical breathing/swell motion.",
    ("tidal_swell_config", "DEEP_COLOR"): "Color of the deep ocean floor between waves.",
    ("tidal_swell_config", "TROUGH_COLOR"): "Color of the wave trough (lowest point between crests).",
    ("tidal_swell_config", "BODY_COLOR"): "Color of the main wave body.",
    ("tidal_swell_config", "CREST_COLOR"): "Bright color at the top of each wave crest.",
    ("tidal_swell_config", "FOAM_COLOR"): "Color of foam/spray near the wave crest.",
    ("tidal_swell_config", "SPRAY_COLOR"): "Brightest white spray highlight at the very top of breaking waves.",
    ("tidal_swell_config", "FOAM_CHANCE"): "Probability of a foam sparkle appearing at each wave crest per frame.",
    ("tidal_swell_config", "SECONDARY_WAVE"): "Enable a second wave at a different frequency for added complexity.",
    ("tidal_swell_config", "SECONDARY_SCALE"): "Amplitude scale of the secondary wave (0 = none, 1 = same as primary).",

    # ── Wave Interference ──
    ("wave_interference_config", "FPS"): "Animation frame rate for the wave simulation.",
    ("wave_interference_config", "SPEED"): "Wave equation propagation speed. How fast ripples travel outward.",
    ("wave_interference_config", "DAMPING"): "Energy damping per frame (0-1). Values near 1 sustain waves longer.",
    ("wave_interference_config", "AMPLITUDE"): "Wave source amplitude. Higher values create stronger, brighter waves.",
    ("wave_interference_config", "NUM_SOURCES"): "Number of wave source points moving around the keyboard.",
    ("wave_interference_config", "WAVE_FREQ"): "Oscillation frequency of wave sources. Higher values create tighter ripple rings.",
    ("wave_interference_config", "SOURCE_SPEED"): "Movement speed of the wave source points.",
    ("wave_interference_config", "PALETTE"): "Diverging color gradient: blue (negative) → black (zero) → gold (positive).",
}

# Generic tooltips based on parameter name patterns
_GENERIC_TOOLTIPS = {
    "FPS": "Animation frame rate. Higher values are smoother but use more CPU.",
    "BG_COLOR": "Background color for unlit or inactive areas.",
    "PALETTE": "Color gradient used to colorize the effect output.",
}


def _get_tooltip(config_basename, param_name, comment):
    """Get the best available tooltip for a parameter."""
    # 1. Check specific tooltip registry
    key = (config_basename, param_name)
    if key in PARAM_TOOLTIPS:
        return PARAM_TOOLTIPS[key]
    # 2. Check generic name-based tooltips
    if param_name in _GENERIC_TOOLTIPS:
        return _GENERIC_TOOLTIPS[param_name]
    # 3. Use inline comment from config file (strip leading #)
    if comment:
        tip = comment.lstrip("# ").strip()
        if tip:
            return tip[0].upper() + tip[1:] if tip else ""
    # 4. Humanize the variable name as last resort
    return humanize_name(param_name)



def _is_rgb(val):
    """Check if value is an (R, G, B) tuple with ints 0-255."""
    return (isinstance(val, tuple) and len(val) == 3
            and all(isinstance(v, int) and 0 <= v <= 255 for v in val))


def _infer_type(name, value):
    """Infer parameter type from its Python value."""
    if isinstance(value, bool):
        return "bool"
    if _is_rgb(value):
        return "rgb"
    if isinstance(value, list) and len(value) > 0:
        if all(_is_rgb(v) for v in value):
            return "palette"
        if all(isinstance(v, tuple) for v in value):
            return "tuple_list"
        if all(isinstance(v, float) for v in value):
            return "float_list"
        if all(isinstance(v, int) for v in value):
            return "int_list"
        # Mixed int/float list — treat as float
        if all(isinstance(v, (int, float)) for v in value):
            return "float_list"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    return "unknown"


def _infer_range(name, value, param_type):
    """Infer slider min/max/step from variable name and current value.

    Uses a priority cascade of name-pattern matching on the UPPER_CASE
    variable name.  Earlier matches take priority:

      1. Exact:   FPS → 1..60
      2. Probability keywords (CHANCE, BLEND, AMOUNT, DENSITY, DAMPING)
                  → 0..1 for float, 0..100 for int
      3. Position suffixes (_X, _Y, _FADE) → 0..1 if current value is in range
      4. THRESHOLD → 0..value*3 (float) or 0..value*5 (int)
      5. Count prefixes (NUM_, MAX_) → 1..value*5 (int only)
      6. SPEED / RATE → scaled from current value
      7. SCALE / RATIO → 0.01..value*5
      8. WIDTH / RADIUS / DIST → 0..value*5
      9. SHARPNESS / INTENSITY / FALLOFF → 0..value*3
     10. Fallback: derive range from current value magnitude

    When adding a new effect, parameters with non-standard names will hit
    the fallback (rule 10).  Add a specific rule above if the fallback
    produces a poor range for a common naming pattern.
    """
    if param_type not in ("int", "float"):
        return 0.0, 1.0, 0.01

    uname = name.upper()

    if uname == "FPS":
        return 1, 60, 1

    # Probability/ratio params (0-1 range)
    if any(s in uname for s in ("CHANCE", "BLEND", "AMOUNT", "DENSITY", "DAMPING")):
        if param_type == "float":
            return 0.0, 1.0, 0.01
        return 0, 100, 1

    # Fractional position params (0-1 range)
    if any(uname.endswith(s) for s in ("_X", "_Y", "_FADE")):
        if param_type == "float" and 0.0 <= value <= 1.0:
            return 0.0, 1.0, 0.01

    # Threshold params
    if "THRESHOLD" in uname:
        if param_type == "float":
            return 0.0, max(value * 3, 2.0), 0.01
        return 0, max(int(value * 5), 20), 1

    # Count params
    if any(uname.startswith(s) for s in ("NUM_", "MAX_")):
        if param_type == "int":
            return 1, max(int(value * 5), 20), 1

    # Speed/rate params
    if any(s in uname for s in ("SPEED", "RATE")):
        if param_type == "float":
            if value > 0 and value < 0.1:
                return 0.0, max(value * 20, 0.5), 0.001
            return 0.0, max(value * 5, 2.0), 0.001 if value < 1 else 0.01

    # Scale/ratio
    if any(s in uname for s in ("SCALE", "RATIO")):
        if param_type == "float":
            return 0.01, max(value * 5, 10.0), 0.01

    # Width/radius
    if any(s in uname for s in ("WIDTH", "RADIUS", "DIST")):
        if param_type == "float":
            return 0.0, max(value * 5, 10.0), 0.01

    # Sharpness/intensity/exponent
    if any(s in uname for s in ("SHARPNESS", "INTENSITY", "FALLOFF")):
        if param_type == "float":
            return 0.0, max(value * 3, 10.0), 0.1

    # General numeric
    if param_type == "int":
        if value < 0:
            return min(int(value * 3), -20), max(int(abs(value) * 3), 20), 1
        if value < 10:
            return 0, max(int(value * 5), 20), 1
        return 1, int(value * 5), 1

    if param_type == "float":
        if value < 0:
            return min(value * 3, -5.0), max(abs(value) * 3, 5.0), 0.01
        return 0.0, max(value * 5, 10.0), 0.01


def _extract_comment(line_text, value_repr):
    """Extract inline comment from a config line."""
    # Find the comment after the value
    # Simple approach: find # that's not inside a string
    idx = line_text.find("#")
    while idx >= 0:
        # Check if # is inside a string by counting quotes before it
        before = line_text[:idx]
        if before.count("'") % 2 == 0 and before.count('"') % 2 == 0:
            return line_text[idx:].rstrip()
        idx = line_text.find("#", idx + 1)
    return ""


def parse_config(config_path):
    """Parse a config file and return list of ConfigParam."""
    with open(config_path) as f:
        source = f.read()
        lines = source.splitlines()

    tree = ast.parse(source, filename=config_path)
    params = []

    # Derive config basename for tooltip lookup (e.g., "arc_sweep_config")
    config_basename = os.path.splitext(os.path.basename(config_path))[0]

    for node in ast.iter_child_nodes(tree):
        if not isinstance(node, ast.Assign):
            continue
        if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            continue

        name = node.targets[0].id
        # Skip dunder names
        if name.startswith("_"):
            continue

        try:
            value = ast.literal_eval(node.value)
        except (ValueError, TypeError):
            continue

        param_type = _infer_type(name, value)
        if param_type == "unknown":
            continue

        line_num = node.lineno  # 1-based
        line_text = lines[line_num - 1] if line_num <= len(lines) else ""

        # For multi-line values (lists), get the end line
        end_line = getattr(node, "end_lineno", line_num)

        comment = _extract_comment(line_text, "")
        range_min, range_max, range_step = _infer_range(name, value, param_type)
        tooltip = _get_tooltip(config_basename, name, comment)

        params.append(ConfigParam(
            name=name,
            value=value,
            param_type=param_type,
            line_number=line_num,
            comment=comment,
            range_min=range_min,
            range_max=range_max,
            range_step=range_step,
            tooltip=tooltip,
        ))

    return params


def _format_value(value, param_type):
    """Format a value for writing back to a config file."""
    if param_type == "bool":
        return repr(value)
    if param_type == "rgb":
        return f"({value[0]}, {value[1]}, {value[2]})"
    if param_type == "palette":
        if len(value) <= 3:
            inner = ", ".join(f"({r}, {g}, {b})" for r, g, b in value)
            return f"[{inner}]"
        lines = []
        lines.append("[")
        for i, (r, g, b) in enumerate(value):
            comma = "," if i < len(value) - 1 else ","
            lines.append(f"    ({r}, {g}, {b}){comma}")
        lines.append("]")
        return "\n".join(lines)
    if param_type == "float_list":
        return repr(value)
    if param_type == "int_list":
        return repr(value)
    if param_type == "tuple_list":
        inner = ", ".join(repr(t) for t in value)
        return f"[{inner}]"
    if param_type == "float":
        # Preserve reasonable precision
        if abs(value) < 0.001 and value != 0:
            return f"{value}"
        formatted = f"{value:.6f}".rstrip("0").rstrip(".")
        # Ensure at least one decimal for floats
        if "." not in formatted:
            formatted += ".0"
        return formatted
    return repr(value)


def write_config(config_path, params):
    """Write modified params back to a config file, preserving structure."""
    with open(config_path) as f:
        source = f.read()

    tree = ast.parse(source, filename=config_path)
    lines = source.splitlines(keepends=True)

    # Build a map of variable name -> (start_line, end_line) from AST
    assignments = {}
    for node in ast.iter_child_nodes(tree):
        if not isinstance(node, ast.Assign):
            continue
        if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            continue
        name = node.targets[0].id
        start = node.lineno  # 1-based
        end = getattr(node, "end_lineno", start)
        assignments[name] = (start, end)

    # Parse original values for comparison
    orig_values = {}
    for node in ast.iter_child_nodes(tree):
        if not isinstance(node, ast.Assign):
            continue
        if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            continue
        try:
            orig_values[node.targets[0].id] = ast.literal_eval(node.value)
        except (ValueError, TypeError):
            pass

    # Build param lookup
    param_map = {p.name: p for p in params}

    # Process replacements in reverse order to preserve line numbers
    replacements = []
    for name, (start, end) in sorted(assignments.items(), key=lambda x: x[1][0], reverse=True):
        if name not in param_map:
            continue
        param = param_map[name]
        # Skip unchanged values to preserve original formatting and comments
        if name in orig_values and orig_values[name] == param.value:
            continue
        formatted = _format_value(param.value, param.param_type)

        # Get the original line to preserve inline comment
        orig_line = lines[start - 1] if start <= len(lines) else ""
        comment = _extract_comment(orig_line, "")

        if "\n" in formatted:
            # Multi-line value (palette)
            new_content = f"{name} = {formatted}"
            if comment:
                new_content = f"{name} = {formatted}  {comment}"
            new_content += "\n"
        else:
            if comment:
                new_content = f"{name} = {formatted}     {comment}\n"
            else:
                new_content = f"{name} = {formatted}\n"

        replacements.append((start - 1, end, new_content))

    # Apply replacements
    for start_idx, end_line, new_content in replacements:
        lines[start_idx:end_line] = [new_content]

    # Write atomically
    dir_name = os.path.dirname(config_path)
    fd, tmp_path = tempfile.mkstemp(dir=dir_name, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            f.writelines(lines)
        os.replace(tmp_path, config_path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def write_temp_config(config_path, params, temp_dir="/tmp/razer-lighting-preview"):
    """Write params to a temp config file for preview. Returns temp path."""
    os.makedirs(temp_dir, exist_ok=True)
    basename = os.path.basename(config_path)
    temp_path = os.path.join(temp_dir, basename)

    # Start from the real config file content to preserve structure
    if os.path.exists(config_path):
        with open(config_path) as f:
            content = f.read()
        # Write base content first
        with open(temp_path, "w") as f:
            f.write(content)
        # Then apply param modifications
        write_config(temp_path, params)
    else:
        # Generate from scratch
        with open(temp_path, "w") as f:
            for p in params:
                formatted = _format_value(p.value, p.param_type)
                f.write(f"{p.name} = {formatted}\n")

    return temp_path


def get_config_path_for_effect(effect_module):
    """Get the config file path for an effect module."""
    return getattr(effect_module, "CONFIG_PATH", None)


def load_defaults(effect_name):
    """Load cached default values for an effect."""
    path = os.path.join(DEFAULTS_DIR, f"{effect_name}.json")
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def save_defaults(effect_name, params):
    """Cache default values for an effect (only if not already cached)."""
    os.makedirs(DEFAULTS_DIR, exist_ok=True)
    path = os.path.join(DEFAULTS_DIR, f"{effect_name}.json")
    if os.path.exists(path):
        return  # Never overwrite defaults
    data = {}
    for p in params:
        data[p.name] = {"value": p.value, "param_type": p.param_type}
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def humanize_name(name):
    """Convert UPPER_SNAKE_CASE to Title Case for display."""
    return name.replace("_", " ").title()


def group_params(params):
    """Group parameters into categories for display."""
    groups = {
        "Timing": [],
        "Colors": [],
        "Simulation": [],
        "Other": [],
    }

    timing_patterns = {"FPS", "SPEED", "MIN", "MAX", "INTERVAL", "FREQ", "PAUSE", "GAP", "FRAMES"}
    sim_patterns = {"RATE", "STEPS", "THRESHOLD", "CHANCE", "DENSITY", "COOLING", "DAMPING",
                    "DIFFUSION", "COUPLING", "AMPLITUDE", "DECAY", "DEPOSIT", "FEED", "KILL"}

    for p in params:
        uname = p.name.upper()
        tokens = set(uname.split("_"))

        if p.param_type in ("rgb", "palette"):
            groups["Colors"].append(p)
        elif tokens & timing_patterns:
            groups["Timing"].append(p)
        elif tokens & sim_patterns:
            groups["Simulation"].append(p)
        else:
            groups["Other"].append(p)

    # Remove empty groups
    return {k: v for k, v in groups.items() if v}
