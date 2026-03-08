FPS = 20

# Plasma field parameters
SCALE_X = 0.8                 # horizontal frequency
SCALE_Y = 1.2                 # vertical frequency
TIME_SPEED = 0.12             # animation speed (radians per frame)

# Color palette — sunset inferno
# Smooth cycle through warm/cool complementary tones
PALETTE = [
    (200, 40, 0),             # deep ember
    (255, 100, 0),            # vivid orange
    (255, 180, 40),           # golden
    (255, 80, 120),           # coral pink
    (200, 0, 180),            # magenta
    (100, 0, 200),            # deep violet
    (40, 0, 120),             # midnight purple
    (100, 0, 200),            # deep violet
    (200, 0, 180),            # magenta
    (255, 80, 120),           # coral pink
    (255, 180, 40),           # golden
    (255, 100, 0),            # vivid orange
    (200, 40, 0),             # deep ember
]

# Overlay parameters — second plasma layer for complexity
OVERLAY = True
OVERLAY_SCALE_X = 1.1
OVERLAY_SCALE_Y = 0.7
OVERLAY_TIME_SPEED = 0.09
OVERLAY_BLEND = 0.35          # blend weight of overlay (0=none, 1=full)
