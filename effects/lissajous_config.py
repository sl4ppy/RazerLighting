FPS = 24

# Lissajous curve parameters
FREQ_X = 3.0                  # horizontal frequency
FREQ_Y = 2.0                  # vertical frequency
PHASE_SPEED = 0.02            # phase shift speed (radians per frame) — morphs the shape
ANIM_SPEED = 0.08             # dot travel speed along the curve (radians per frame)

# Trail
TRAIL_LENGTH = 14             # number of trailing dots
TRAIL_FADE = True             # fade trail brightness

# Colors — rose gold sparkler
BG_COLOR = (5, 0, 15)                # deep midnight purple
HEAD_COLOR = (255, 220, 200)         # warm white/rose head
TRAIL_COLOR = (255, 80, 100)         # coral-pink trail
DIM_TRAIL_COLOR = (40, 5, 20)        # deep ruby faint trail

# Glow around the dot
GLOW_RADIUS = 1.8             # radius of glow around dot (in cells)
GLOW_COLOR = (255, 120, 140)  # warm pink glow

# Randomize frequencies periodically
MORPH = True
MORPH_INTERVAL = 8.0          # seconds between frequency changes
