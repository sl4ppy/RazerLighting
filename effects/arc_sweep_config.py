FPS = 24

# Arc speed range (coordinate units per second)
SPEED_MIN = 0.134
SPEED_MAX = 4.0

# Pause between spawning arcs (seconds)
PAUSE_MIN = 0.39
PAUSE_MAX = 6.76

# Curvature: focal point distance from keyboard center
# Larger = flatter wavefronts, smaller = more curved
FOCAL_DISTANCE = 15.0

# Max simultaneous arcs (prevents pile-up with slow speeds)
MAX_ARCS = 5

# Arc thickness (Gaussian sigma — slow arcs auto-thin, fast arcs auto-widen)
ARC_WIDTH = 1.03

# Key aspect ratio (keys are ~2.5x wider than tall)
ASPECT_RATIO = 2.5

# Domain warp: organic wavefront distortion
WARP_STRENGTH = 0.5     # 0 = smooth circles, higher = more distorted
WARP_SCALE = 0.25        # noise spatial frequency

# Chromatic offset: prismatic color split at arc edges
# Blue channel leads, red trails — creates rainbow fringe
CHROMATIC_OFFSET = 0.15  # 0 = none, higher = more split

# Arc colors (one picked randomly per arc)
COLORS = [(54, 162, 79), (13, 255, 0)]

# Trail shifts toward this color as the arc passes
TRAIL_COLOR = (40, 0, 80)

# Afterglow: warmth left behind by passing arcs
AFTERGLOW_DECAY = 0.0     # per-frame (0 = instant, 1 = forever)
AFTERGLOW_DEPOSIT = 0.0     # fraction of arc brightness deposited

# Background
BG_COLOR = (2, 0, 8)
