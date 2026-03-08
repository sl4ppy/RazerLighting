FPS = 20

# Agent parameters
NUM_AGENTS = 120
SENSOR_ANGLE = 0.6          # radians (~34 degrees)
SENSOR_DIST = 4.0
TURN_SPEED = 0.5            # radians per step
MOVE_SPEED = 1.0

# Trail parameters
DEPOSIT_AMOUNT = 3.0
DECAY_RATE = 0.90
BUFFER_SCALE = 4
JITTER = 0.15               # random angle jitter per step (radians)

# Palette — yellow-green bioluminescent
PALETTE = [
    (0, 0, 0),
    (0, 30, 0),
    (20, 80, 0),
    (80, 180, 20),
    (180, 240, 80),
    (240, 255, 180),
]
