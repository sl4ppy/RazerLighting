FPS = 20

# Beam sweep
SWEEP_SPEED = 0.03            # radians per frame — speed of beam rotation
BEAM_WIDTH = 0.4              # angular width of the beam (radians)
BEAM_FALLOFF = 2.0            # how sharply the beam fades at edges (higher = sharper)

# Beam origin offset (fraction of keyboard size, 0.5 = center)
ORIGIN_X = 0.5
ORIGIN_Y = 0.5

# Colors
BG_COLOR = (17, 0, 34)               # deep purple/black ambient
BEAM_CORE_COLOR = (255, 255, 204)     # warm white/yellow core
BEAM_MID_COLOR = (200, 220, 100)      # warm glow
BEAM_EDGE_COLOR = (61, 122, 30)       # green tint at beam edge
AMBIENT_COLOR = (20, 8, 32)           # subtle purple ambient

# Flicker
FLICKER = True                         # subtle brightness variation
FLICKER_AMOUNT = 0.08                  # max brightness variation (0-1)
