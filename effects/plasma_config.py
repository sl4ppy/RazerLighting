FPS = 20

# Plasma field parameters
SCALE_X = 0.8                 # horizontal frequency
SCALE_Y = 1.2                 # vertical frequency
TIME_SPEED = 0.12             # animation speed (radians per frame)

# Color palette — emerald plasma
# Colors are sampled along a gradient based on plasma value [0..1]
PALETTE = [
    (200, 60, 0),             # deep orange
    (255, 100, 0),            # vivid orange
    (255, 140, 40),           # bright orange
    (200, 80, 255),           # vivid lavender
    (160, 40, 220),           # bright purple
    (100, 0, 160),            # purple
    (40, 0, 60),              # deep purple
    (100, 0, 160),            # purple
    (160, 40, 220),           # bright purple
    (200, 80, 255),           # vivid lavender
    (255, 140, 40),           # bright orange
    (255, 100, 0),            # vivid orange
    (200, 60, 0),             # deep orange
]

# Overlay parameters — second plasma layer for complexity
OVERLAY = True
OVERLAY_SCALE_X = 1.1
OVERLAY_SCALE_Y = 0.7
OVERLAY_TIME_SPEED = 0.09
OVERLAY_BLEND = 0.35          # blend weight of overlay (0=none, 1=full)
