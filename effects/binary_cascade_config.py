FPS = 18

# Stream spawning
STREAM_SPAWN_CHANCE = 0.15    # chance per column per frame to spawn a new stream
MAX_STREAMS = 20              # max simultaneous streams

# Stream properties
SPEED_MIN = 0.3               # cells per frame
SPEED_MAX = 1.2
TRAIL_LENGTH_MIN = 3
TRAIL_LENGTH_MAX = 8

# Colors — matrix green palette
BG_COLOR = (0, 20, 8)                # dark green background glow
HEAD_COLOR = (255, 255, 255)          # white leading character
BRIGHT_COLOR = (0, 255, 0)            # bright green body
MID_COLOR = (0, 136, 68)             # mid green
DIM_COLOR = (0, 85, 51)              # dim green trail
GLINT_COLOR = (0, 255, 204)          # cyan glint (random sparkle)
GLINT_CHANCE = 0.03                   # chance per visible cell per frame
