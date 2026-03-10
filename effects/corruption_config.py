FPS = 18

# --- Baseline: breathing gradient ---
BASELINE_PALETTE = [
    (0, 8, 20),
    (0, 20, 45),
    (0, 40, 55),
    (0, 25, 35),
]
BASELINE_SPEED = 0.4

# --- Spawning ---
SPAWN_INTERVAL = 3.0              # average seconds between new sites
MAX_SITES = 4                     # max simultaneous corruption zones

# --- Site geometry ---
RADIUS_MIN = 2.0                  # minimum blob radius (cells)
RADIUS_MAX = 5.5                  # maximum blob radius (cells)

# --- Lifecycle timing (seconds) ---
INCUBATION_TIME = 0.3             # single-pixel flicker warning
SPREAD_TIME = 0.8                 # growth phase
PEAK_TIME_MIN = 0.5               # peak duration range
PEAK_TIME_MAX = 1.5
DECAY_TIME = 0.8                  # contraction / healing
SCAR_TIME = 2.0                   # residual discoloration

# --- Colors ---
CORRUPT_COLOR = (255, 0, 100)     # hot magenta-pink
SCAR_COLOR = (0, 50, 30)          # slight green tint for healed areas

# --- Behaviors ---
CASCADE_CHANCE = 0.2              # chance to spawn child sites at peak
SURGE_INTERVAL = 20.0             # seconds between power-surge flares
ROW_BLEED_CHANCE = 0.03           # chance per frame for full-width scanline
