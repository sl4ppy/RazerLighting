FPS = 24

# Lissajous curve parameters
FREQ_X = 3.0                  # horizontal frequency
FREQ_Y = 2.0                  # vertical frequency
PHASE_SPEED = 0.02            # phase shift speed (radians per frame) — morphs the shape
ANIM_SPEED = 0.08             # dot travel speed along the curve (radians per frame)

# Trail
TRAIL_LENGTH = 12             # number of trailing dots
TRAIL_FADE = True             # fade trail brightness

# Colors
BG_COLOR = (0, 10, 5)                # dark background
HEAD_COLOR = (255, 255, 255)          # bright white dot head
TRAIL_COLOR = (0, 205, 65)           # green trail
DIM_TRAIL_COLOR = (0, 26, 13)        # faintest trail

# Glow around the dot
GLOW_RADIUS = 1.5             # radius of glow around dot (in cells)
GLOW_COLOR = (0, 160, 50)    # glow color

# Randomize frequencies periodically
MORPH = True
MORPH_INTERVAL = 8.0          # seconds between frequency changes
