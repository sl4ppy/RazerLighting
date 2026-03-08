FPS = 20

# Beam sweep
SWEEP_SPEED = 0.03            # radians per frame — speed of beam rotation
BEAM_WIDTH = 0.4              # angular width of the beam (radians)
BEAM_FALLOFF = 2.0            # how sharply the beam fades at edges (higher = sharper)

# Beam origin offset (fraction of keyboard size, 0.5 = center)
ORIGIN_X = 0.5
ORIGIN_Y = 0.5

# Colors — warm spotlight on deep indigo
BG_COLOR = (5, 0, 20)                # deep indigo/black
BEAM_CORE_COLOR = (255, 240, 220)    # warm white core
BEAM_MID_COLOR = (255, 180, 60)      # golden mid-glow
BEAM_EDGE_COLOR = (180, 80, 0)       # amber edge
AMBIENT_COLOR = (10, 4, 25)          # subtle deep indigo ambient

# Flicker
FLICKER = True                        # subtle brightness variation
FLICKER_AMOUNT = 0.08                 # max brightness variation (0-1)
