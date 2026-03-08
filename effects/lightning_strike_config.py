FPS = 15

# Seconds between lightning events (randomized)
INTERVAL_MIN = 1.5
INTERVAL_MAX = 10.0

# Multi-bolt storms: chance of 2-3 bolts firing in quick succession
MULTI_BOLT_CHANCE = 0.35
MULTI_BOLT_GAP_MIN = 0.3
MULTI_BOLT_GAP_MAX = 1.2

# Bolt shape
BOLT_WANDER = [-2, -1, -1, 0, 1, 1, 2]  # column offsets per row (weighted toward small moves)

# Branches
BRANCH_CHANCE = 0.3       # chance of branch at each row
BRANCH_MAX_LENGTH = 3     # max branch extent in columns

# Restrike and surge
RESTRIKE_CHANCE = 0.6     # chance of re-flash after initial bolt
RESTRIKE_GAP_MIN = 2      # min dark frames before restrike
RESTRIKE_GAP_MAX = 5      # max dark frames before restrike
SURGE_CHANCE = 0.5        # chance of surge flicker after restrike

# Colors — vivid electric storm
BOLT_COLOR = (255, 255, 255)         # white bolt core
GLOW_COLOR = (15, 30, 80)           # electric blue ambient glow
GLOW_DIM_COLOR = (8, 16, 50)        # darker blue (sustain frame)
BRANCH_COLOR = (160, 80, 255)       # vivid violet branch
BRANCH_DIM_COLOR = (180, 220, 255)  # pale electric blue (branch fade)
SURGE_COLOR = (80, 180, 255)        # bright cyan surge pulse
