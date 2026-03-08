FPS = 12

# Automaton rules
NUM_STATES = 8
THRESHOLD = 1
SIM_STEPS_PER_FRAME = 1

# Stagnation detection
STAGNATION_FRAMES = 60

# Jewel-tone palette — one color per state (interpolated if fewer than NUM_STATES)
# Set to empty list [] for classic HSV rainbow
PALETTE = [
    (180, 0, 255),      # amethyst
    (60, 0, 220),       # indigo
    (0, 100, 255),      # sapphire
    (0, 220, 180),      # aquamarine
    (0, 200, 60),       # emerald
    (255, 200, 0),      # topaz
    (255, 80, 0),       # fire opal
    (255, 0, 80),       # ruby
]
