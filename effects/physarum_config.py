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

# Palette — electric blue neural network
PALETTE = [
    (0, 0, 0),
    (0, 0, 40),
    (0, 40, 120),
    (0, 120, 255),
    (100, 200, 255),
    (200, 240, 255),
]
