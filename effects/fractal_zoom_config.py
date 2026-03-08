FPS = 15

# Zoom parameters
ZOOM_SPEED = 0.03             # how fast the zoom progresses per frame
ZOOM_RANGE = 3.0              # total zoom range before reset
ROTATION_SPEED = 0.01         # slow rotation per frame (radians)

# Mandelbrot/Julia parameters
MAX_ITER = 20                 # iteration depth (higher = more detail, slower)
CENTER_RE = -0.75             # real center of view
CENTER_IM = 0.0               # imaginary center of view
JULIA_MODE = False            # True = Julia set, False = Mandelbrot
JULIA_C_RE = -0.7             # Julia constant (real)
JULIA_C_IM = 0.27015          # Julia constant (imaginary)

# Color palette — cosmic nebula (blue/magenta/gold)
PALETTE = [
    (2, 0, 10),               # void black
    (0, 20, 80),              # deep blue
    (80, 0, 160),             # royal purple
    (255, 0, 120),            # hot pink
    (255, 200, 50),           # gold highlight
    (255, 0, 120),            # hot pink (mirror)
    (80, 0, 160),             # royal purple
    (0, 20, 80),              # deep blue
]
INSIDE_COLOR = (2, 0, 10)     # color for points inside the set

# Pulse breathing overlay
PULSE = True
PULSE_SPEED = 0.05            # breathing speed
PULSE_AMOUNT = 0.25           # brightness modulation depth
