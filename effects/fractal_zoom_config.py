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

# Color palette — purple/magenta nebula
PALETTE = [
    (10, 0, 21),              # near-black purple
    (37, 0, 66),              # deep purple
    (75, 0, 120),             # purple
    (140, 0, 200),            # bright purple
    (180, 50, 255),           # vivid magenta
    (140, 0, 200),            # bright purple (mirror)
    (75, 0, 120),             # purple
    (37, 0, 66),              # deep purple
]
INSIDE_COLOR = (10, 0, 21)    # color for points inside the set

# Pulse breathing overlay
PULSE = True
PULSE_SPEED = 0.05            # breathing speed
PULSE_AMOUNT = 0.25           # brightness modulation depth
