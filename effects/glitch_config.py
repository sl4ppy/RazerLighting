FPS = 15

# Idle state — dark teal baseline
IDLE_COLOR = (0, 25, 30)
IDLE_MIN = 1.0                        # min seconds between glitch bursts
IDLE_MAX = 6.0                        # max seconds between glitch bursts

# Glitch burst
BURST_FRAMES_MIN = 3                  # min frames per burst
BURST_FRAMES_MAX = 12                 # max frames per burst
BURST_DENSITY_MIN = 0.05              # min fraction of keys affected per frame
BURST_DENSITY_MAX = 0.6               # max fraction of keys affected per frame

# Glitch visual properties
CORRUPTION_CHANCE = 0.3               # chance of a row-shift corruption per frame
ROW_SHIFT_MAX = 4                     # max columns a row can shift during corruption
SCANLINE_CHANCE = 0.2                 # chance of a bright horizontal scanline

# Colors — cyberpunk palette
GLITCH_COLORS = [
    (255, 0, 100),             # hot magenta
    (0, 255, 220),             # electric cyan
    (255, 255, 255),           # white
    (180, 0, 255),             # neon purple
    (0, 255, 60),              # acid green
    (255, 100, 0),             # hot orange
]

# Multi-burst: chance of rapid successive bursts
MULTI_BURST_CHANCE = 0.3
MULTI_BURST_GAP_MIN = 0.1
MULTI_BURST_GAP_MAX = 0.4
