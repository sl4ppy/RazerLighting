FPS = 20
SPEED_MIN = 0.4
SPEED_MAX = 4.0

# Pause between sweeps (seconds)
PAUSE_MIN = 0.5
PAUSE_MAX = 4.0

CENTER_COLOR = (100, 180, 255)   # electric blue core
EDGE_COLOR = (255, 0, 120)       # hot magenta edge

# Trailing fade behind the arc (nearest to farthest)
TRAIL = [
    (120, 0, 200),     # vivid violet
    (60, 0, 140),      # deep violet
    (25, 0, 80),       # dark violet
    (8, 0, 30),        # near-black purple
]

# Per-row column offset — row 0 leads, creating the arc/curved wavefront
ROW_OFFSETS = [1.2, 0.6, 0.0, -0.3, -0.8, -1.5]
