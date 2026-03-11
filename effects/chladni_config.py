FPS = 20

# Chladni parameters
NODAL_WIDTH = 0.35
MORPH_SPEED = 0.008
WAVE_SPEED = 0.4
PULSE_SPEED = 0.06

# Edge glow intensity (0 = off, 1 = strong)
EDGE_GLOW = 0.7

# Chromatic displacement along gradient (0 = off)
CHROMATIC_SPREAD = 0.08

# Mode pairs to cycle through (n, m)
MODE_PAIRS = [
    (2, 3), (3, 5), (4, 3), (5, 2), (1, 4), (3, 4),
]

# Nodal line palette (dark → bright along nodal lines)
NODAL_PALETTE = [
    (0, 2, 12),
    (0, 15, 50),
    (5, 70, 130),
    (0, 180, 220),
    (100, 240, 255),
    (210, 255, 255),
    (255, 255, 255),
]

# Anti-node palette (warm glow in high-amplitude regions)
ANTINODE_PALETTE = [
    (0, 0, 0),
    (40, 5, 0),
    (120, 30, 0),
    (255, 80, 10),
    (255, 160, 60),
]
