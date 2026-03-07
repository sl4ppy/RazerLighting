FPS = 20
SPEED_MIN = 0.4
SPEED_MAX = 4.0

# Pause between sweeps (seconds)
PAUSE_MIN = 0.5
PAUSE_MAX = 4.0

CENTER_COLOR = (0, 255, 0)     # #00ff00 bright green
EDGE_COLOR = (136, 0, 102)     # #880066 dark magenta

# Trailing fade behind the arc (nearest to farthest)
TRAIL = [
    (0, 100, 50),     # deep teal
    (0, 60, 40),
    (0, 30, 25),
    (0, 15, 15),
]

# Per-row column offset — row 0 leads, creating the arc/curved wavefront
ROW_OFFSETS = [0.5, 0.0, 0.0, 0.0, 0.0, 0.0]
