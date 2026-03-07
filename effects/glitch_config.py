FPS = 15

# Idle state
IDLE_COLOR = (0, 51, 0)              # dim green idle baseline
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

# Colors
GLITCH_COLORS = [
    (0, 255, 0),              # bright green
    (204, 0, 68),             # hot pink/red
    (255, 0, 51),             # red
    (255, 255, 255),          # white
    (0, 255, 204),            # cyan
    (0, 119, 0),              # mid green
]

# Multi-burst: chance of rapid successive bursts
MULTI_BURST_CHANCE = 0.3
MULTI_BURST_GAP_MIN = 0.1
MULTI_BURST_GAP_MAX = 0.4
