# config.py — Global constants for the Snake Game project

# ── Window & Grid ─────────────────────────────────────────────────────────────
WINDOW_WIDTH  = 800
WINDOW_HEIGHT = 640
CELL_SIZE     = 20
COLS          = WINDOW_WIDTH  // CELL_SIZE   # 40
ROWS          = WINDOW_HEIGHT // CELL_SIZE   # 32
FPS           = 60

# ── Colors ────────────────────────────────────────────────────────────────────
BLACK        = (0,   0,   0)
WHITE        = (255, 255, 255)
DARK_BG      = (15,  17,  26)
PANEL_BG     = (22,  26,  40)
BORDER_COLOR = (40,  48,  72)

# Food colors
FOOD_COLORS = {
    "normal":  (80,  200, 120),   # green
    "bonus":   (255, 215,   0),   # gold  (high-value, disappears fast)
    "poison":  (160,  20,  20),   # dark red
}

# Power-up colors
POWERUP_COLORS = {
    "speed_boost": (255, 140,   0),  # orange
    "slow_motion": (100, 180, 255),  # sky blue
    "shield":      (180, 120, 255),  # violet
}

OBSTACLE_COLOR = (80,  90, 110)
GRID_COLOR     = (25,  30,  45)

# UI colors
ACCENT       = (80,  200, 120)
ACCENT2      = (255, 215,   0)
TEXT_MAIN    = (220, 228, 255)
TEXT_DIM     = (100, 112, 150)
BTN_NORMAL   = (35,  42,  65)
BTN_HOVER    = (50,  62,  95)
BTN_BORDER   = (60,  75, 120)

# ── Game Tuning ───────────────────────────────────────────────────────────────
BASE_SPEED          = 8          # moves per second at level 1
SPEED_PER_LEVEL     = 1          # additional moves/s per level
MAX_SPEED           = 20
FOOD_PER_LEVEL      = 5          # normal food eaten to advance a level

BONUS_FOOD_CHANCE   = 0.25       # probability a new food spawns as bonus
BONUS_FOOD_TTL      = 6_000      # ms before bonus food vanishes
POISON_CHANCE       = 0.15       # probability a new food spawns as poison

POWERUP_SPAWN_INTERVAL = 10_000  # ms between power-up spawn attempts
POWERUP_TTL            = 8_000   # ms a power-up stays on the field
POWERUP_DURATION       = 5_000   # ms effect lasts after collection

OBSTACLE_PER_LEVEL  = 4         # extra wall blocks added each level (from lvl 3)
SNAKE_SHRINK        = 2         # segments removed by poison food

# ── Screens ───────────────────────────────────────────────────────────────────
SCREEN_MENU        = "menu"
SCREEN_GAME        = "game"
SCREEN_GAMEOVER    = "gameover"
SCREEN_LEADERBOARD = "leaderboard"
SCREEN_SETTINGS    = "settings"