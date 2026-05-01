"""
racer.py
Core game objects and logic:
  - Player car
  - Enemy / traffic cars
  - Coins (weighted values from Practice 11)
  - Lane hazards: oil spills, slow zones, speed bumps
  - Power-ups: Nitro, Shield, Repair
  - Moving barriers (dynamic road events)
  - Difficulty scaling
"""

import pygame
import random
import math

# ─── Constants ─────────────────────────────────────────────────────────────────

SCREEN_W = 480
SCREEN_H = 700
FPS = 60

# Road / lane geometry
ROAD_LEFT   = 60
ROAD_RIGHT  = 420
LANE_COUNT  = 3
LANE_WIDTH  = (ROAD_RIGHT - ROAD_LEFT) // LANE_COUNT
LANE_CENTERS = [ROAD_LEFT + LANE_WIDTH * i + LANE_WIDTH // 2 for i in range(LANE_COUNT)]

# Sprite dimensions — original image sizes (no scaling = no quality loss)
PLAYER_W, PLAYER_H = 44, 96
ENEMY_W,  ENEMY_H  = 48, 93
COIN_W,   COIN_H   = 44, 44
POWERUP_W, POWERUP_H = 36, 36

# Colors (fallback when images unavailable)
COLOR_PLAYER  = (0, 150, 255)
COLOR_ENEMY   = (220, 50, 50)
COLOR_COIN    = (255, 215, 0)
COLOR_OIL     = (30, 30, 60)
COLOR_BUMP    = (180, 80, 0)
COLOR_BARRIER = (255, 100, 0)
COLOR_NITRO   = (0, 220, 255)
COLOR_SHIELD  = (100, 100, 255)
COLOR_REPAIR  = (0, 200, 80)
COLOR_SLOWZONE = (200, 200, 0, 120)

# Difficulty tables  {name: (base_enemy_speed, spawn_interval_ms, obstacle_freq)}
DIFFICULTY = {
    "easy":   {"base_speed": 4, "enemy_interval": 2200, "hazard_prob": 0.003},
    "normal": {"base_speed": 5, "enemy_interval": 1600, "hazard_prob": 0.005},
    "hard":   {"base_speed": 7, "enemy_interval": 1100, "hazard_prob": 0.008},
}

# Coin weights (value → relative probability)
COIN_WEIGHTS = {1: 60, 3: 30, 5: 10}

# Power-up types
POWERUP_TYPES = ["nitro", "shield", "repair"]

# How long power-up items stay on road before disappearing (ms)
POWERUP_LIFESPAN = 7000


# ─── Helpers ───────────────────────────────────────────────────────────────────

def random_lane() -> int:
    return random.randint(0, LANE_COUNT - 1)


def lane_x(lane: int) -> int:
    return LANE_CENTERS[lane]


def weighted_coin_value() -> int:
    pool = []
    for val, weight in COIN_WEIGHTS.items():
        pool.extend([val] * weight)
    return random.choice(pool)


def load_image(path: str, size: tuple) -> pygame.Surface:
    """Load image at original size — no scaling, no quality loss."""
    try:
        raw = pygame.image.load(path).convert_alpha()
        raw.set_colorkey((255, 255, 255), pygame.RLEACCEL)
        return raw
    except Exception as e:
        print(f"[load_image] Failed to load {path}: {e}")
        surf = pygame.Surface(size, pygame.SRCALPHA)
        surf.fill((200, 200, 200, 180))
        return surf


# ─── Asset cache ───────────────────────────────────────────────────────────────

_assets: dict = {}

def init_assets(car_color: str = "blue") -> None:
    """Load all game sprites into the _assets dict."""
    global _assets
    color_tint_map = {
        "blue":   None,
        "red":    (255, 60, 60),
        "green":  (60, 220, 80),
        "yellow": (255, 230, 0),
    }

    player_img = load_image("assets/Player.png", (PLAYER_W, PLAYER_H))

    tint = color_tint_map.get(car_color)
    if tint:
        tinted = player_img.copy()
        tint_surf = pygame.Surface(tinted.get_size(), pygame.SRCALPHA)
        tint_surf.fill((*tint, 120))
        tinted.blit(tint_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        player_img = tinted

    _assets["player"]  = player_img
    _assets["enemy"]   = load_image("assets/Enemy.png",  (ENEMY_W,  ENEMY_H))
    _assets["coin"]    = load_image("assets/coin.png",   (COIN_W,   COIN_H))


# ─── Player ────────────────────────────────────────────────────────────────────

class Player:
    """Lane-based player car."""

    def __init__(self):
        self.lane = 1
        self.x = float(lane_x(self.lane))
        self.y = float(SCREEN_H - 140)
        self.width  = PLAYER_W
        self.height = PLAYER_H
        self.speed  = 5.0

        # Power-up state
        self.shield_active  = False
        self.nitro_active   = False
        self.nitro_timer    = 0.0
        self.nitro_boost    = 3.0

        # Slow effect (oil spill)
        self.slow_active    = False
        self.slow_timer     = 0.0
        self.slow_factor    = 0.5

        # Invincibility frames after a hit (ms)
        self.inv_timer      = 0

        # Lane transition animation
        self._target_x      = float(lane_x(self.lane))
        self.moving         = False

    # ── Input ──────────────────────────────────────────────────────────────────

    def move_left(self):
        if self.lane > 0 and not self.moving:
            self.lane -= 1
            self._target_x = float(lane_x(self.lane))
            self.moving = True

    def move_right(self):
        if self.lane < LANE_COUNT - 1 and not self.moving:
            self.lane += 1
            self._target_x = float(lane_x(self.lane))
            self.moving = True

    # ── Update ─────────────────────────────────────────────────────────────────

    def update(self, dt: float) -> None:
        # Smooth lane transition
        diff = self._target_x - self.x
        if abs(diff) > 2:
            self.x += diff * min(1.0, 12 * dt)
        else:
            self.x = self._target_x
            self.moving = False

        # Nitro countdown
        if self.nitro_active:
            self.nitro_timer -= dt
            if self.nitro_timer <= 0:
                self.nitro_active = False

        # Slow countdown
        if self.slow_active:
            self.slow_timer -= dt
            if self.slow_timer <= 0:
                self.slow_active = False

        # Invincibility countdown
        if self.inv_timer > 0:
            self.inv_timer -= dt * 1000

    def effective_speed(self) -> float:
        spd = self.speed
        if self.nitro_active:
            spd += self.nitro_boost
        if self.slow_active:
            spd *= self.slow_factor
        return spd

    # ── Collision rect ─────────────────────────────────────────────────────────

    def rect(self) -> pygame.Rect:
        return pygame.Rect(
            int(self.x) - self.width  // 2,
            int(self.y) - self.height // 2,
            self.width, self.height
        )

    # ── Power-up application ───────────────────────────────────────────────────

    def apply_nitro(self):
        self.nitro_active = True
        self.nitro_timer  = random.uniform(3, 5)

    def apply_shield(self):
        self.shield_active = True

    def apply_slow(self, duration: float = 2.5):
        self.slow_active = True
        self.slow_timer  = duration

    def consume_shield(self) -> bool:
        """Use shield if active; return True if shield blocked the hit."""
        if self.shield_active:
            self.shield_active = False
            self.inv_timer = 1500
            return True
        return False

    # ── Draw ───────────────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface) -> None:
        img = _assets.get("player")
        r = self.rect()

        # Flicker when invincible
        if self.inv_timer > 0 and (pygame.time.get_ticks() // 100) % 2 == 0:
            return

        if img:
            surface.blit(img, r)
        else:
            pygame.draw.rect(surface, COLOR_PLAYER, r, border_radius=6)

        # Shield aura
        if self.shield_active:
            aura = pygame.Surface((r.width + 16, r.height + 16), pygame.SRCALPHA)
            pygame.draw.ellipse(aura, (100, 100, 255, 80), aura.get_rect())
            surface.blit(aura, (r.x - 8, r.y - 8))

        # Nitro flame
        if self.nitro_active:
            for i in range(3):
                fx = r.centerx + random.randint(-10, 10)
                fy = r.bottom + random.randint(4, 18)
                pygame.draw.circle(surface, (0, 200, 255), (fx, fy), random.randint(4, 8))

            glow = pygame.Surface((r.width + 20, r.height + 20), pygame.SRCALPHA)
            pygame.draw.rect(glow, (0, 200, 255, 60), glow.get_rect(), border_radius=12)
            surface.blit(glow, (r.x - 10, r.y - 10))


# ─── Enemy / Traffic Car ───────────────────────────────────────────────────────

class EnemyCar:
    def __init__(self, lane: int, y: float, speed: float):
        self.lane   = lane
        self.x      = float(lane_x(lane))
        self.y      = y
        self.speed  = speed          # own downward speed (pixels per second)
        self.width  = ENEMY_W
        self.height = ENEMY_H

    def update(self, dt: float, scroll_speed: float) -> None:
        # Enemy moves with the road scroll + its own relative speed.
        # scroll_speed is in pixels/frame; self.speed is pixels/second.
        self.y += scroll_speed + self.speed * dt

    def rect(self) -> pygame.Rect:
        return pygame.Rect(
            int(self.x) - self.width  // 2,
            int(self.y) - self.height // 2,
            self.width, self.height
        )

    def is_off_screen(self) -> bool:
        return self.y > SCREEN_H + self.height

    def draw(self, surface: pygame.Surface) -> None:
        img = _assets.get("enemy")
        r = self.rect()
        if img:
            surface.blit(img, r)
        else:
            pygame.draw.rect(surface, COLOR_ENEMY, r, border_radius=6)


# ─── Coin ──────────────────────────────────────────────────────────────────────

class Coin:
    def __init__(self, lane: int, y: float):
        self.lane  = lane
        self.x     = float(lane_x(lane))
        self.y     = y
        self.value = weighted_coin_value()
        self.width  = COIN_W
        self.height = COIN_H
        self._t = random.uniform(0, math.pi * 2)

    def update(self, scroll_speed: float, dt: float) -> None:
        self.y  += scroll_speed
        self._t += dt * 4

    def rect(self) -> pygame.Rect:
        bob = int(math.sin(self._t) * 3)
        return pygame.Rect(
            int(self.x) - self.width  // 2,
            int(self.y) - self.height // 2 + bob,
            self.width, self.height
        )

    def is_off_screen(self) -> bool:
        return self.y > SCREEN_H + self.height

    def draw(self, surface: pygame.Surface) -> None:
        img = _assets.get("coin")
        r = self.rect()
        if img:
            angle = (self._t * 60) % 360
            x_scale = abs(math.cos(math.radians(angle)))
            spin_w  = max(4, int(self.width * x_scale))
            scaled  = pygame.transform.smoothscale(img, (spin_w, self.height))
            surface.blit(scaled, (r.centerx - spin_w // 2, r.top))
        else:
            pygame.draw.circle(surface, COLOR_COIN, r.center, self.width // 2)
        if self.value > 1:
            font = pygame.font.SysFont("Arial", 11, bold=True)
            lbl = font.render(f"+{self.value}", True, (80, 40, 0))
            surface.blit(lbl, (r.right + 2, r.top))


# ─── Hazards ───────────────────────────────────────────────────────────────────

class OilSpill:
    """Slows the player on contact."""
    def __init__(self, lane: int, y: float):
        self.lane = lane
        self.x    = float(lane_x(lane))
        self.y    = y
        self.w    = LANE_WIDTH - 10
        self.h    = 40

    def update(self, scroll_speed: float) -> None:
        self.y += scroll_speed

    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x) - self.w // 2, int(self.y) - self.h // 2, self.w, self.h)

    def is_off_screen(self) -> bool:
        return self.y > SCREEN_H + self.h

    def draw(self, surface: pygame.Surface) -> None:
        r = self.rect()
        oil = pygame.Surface((r.width, r.height), pygame.SRCALPHA)
        oil.fill((20, 20, 50, 180))
        pygame.draw.ellipse(oil, (100, 0, 180, 120), oil.get_rect(), 4)
        surface.blit(oil, r)
        font = pygame.font.SysFont("Arial", 12, bold=True)
        lbl = font.render("OIL", True, (180, 100, 255))
        surface.blit(lbl, (r.centerx - lbl.get_width() // 2, r.centery - lbl.get_height() // 2))


class SpeedBump:
    """Briefly slows the player."""
    def __init__(self, y: float):
        self.y  = y
        self.w  = ROAD_RIGHT - ROAD_LEFT
        self.h  = 18
        self.x  = ROAD_LEFT

    def update(self, scroll_speed: float) -> None:
        self.y += scroll_speed

    def rect(self) -> pygame.Rect:
        return pygame.Rect(self.x, int(self.y) - self.h // 2, self.w, self.h)

    def is_off_screen(self) -> bool:
        return self.y > SCREEN_H + self.h

    def draw(self, surface: pygame.Surface) -> None:
        r = self.rect()
        pygame.draw.rect(surface, (160, 90, 10), r, border_radius=4)
        stripe_w = 20
        for sx in range(r.left, r.right, stripe_w * 2):
            pygame.draw.rect(surface, (255, 200, 0),
                             pygame.Rect(sx, r.top, stripe_w, r.height), border_radius=2)


class Pothole:
    """Instant game-over hazard."""
    def __init__(self, lane: int, y: float):
        self.lane = lane
        self.x    = float(lane_x(lane))
        self.y    = y
        self.r    = 22

    def update(self, scroll_speed: float) -> None:
        self.y += scroll_speed

    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x) - self.r, int(self.y) - self.r, self.r * 2, self.r * 2)

    def is_off_screen(self) -> bool:
        return self.y > SCREEN_H + self.r * 2

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.circle(surface, (30, 20, 10), (int(self.x), int(self.y)), self.r)
        pygame.draw.circle(surface, (60, 40, 20), (int(self.x), int(self.y)), self.r, 3)
        font = pygame.font.SysFont("Arial", 14, bold=True)
        lbl = font.render("!", True, (255, 220, 0))
        surface.blit(lbl, (int(self.x) - lbl.get_width() // 2, int(self.y) - lbl.get_height() // 2))


class MovingBarrier:
    """Dynamic barrier that slides back and forth."""
    def __init__(self, y: float):
        self.y    = y
        self.x    = float(ROAD_LEFT)
        self.w    = LANE_WIDTH - 8
        self.h    = 22
        self.dir  = 1
        self.hspeed = 90

    def update(self, scroll_speed: float, dt: float) -> None:
        self.y += scroll_speed
        self.x += self.dir * self.hspeed * dt
        if self.x + self.w >= ROAD_RIGHT:
            self.x  = ROAD_RIGHT - self.w
            self.dir = -1
        if self.x <= ROAD_LEFT:
            self.x  = ROAD_LEFT
            self.dir = 1

    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y) - self.h // 2, self.w, self.h)

    def is_off_screen(self) -> bool:
        return self.y > SCREEN_H + self.h

    def draw(self, surface: pygame.Surface) -> None:
        r = self.rect()
        pygame.draw.rect(surface, (220, 80, 0), r, border_radius=5)
        for i in range(0, r.width, 16):
            pygame.draw.rect(surface, (255, 255, 255),
                             pygame.Rect(r.left + i, r.top, 8, r.height))
        bar = pygame.Surface((r.width, r.height), pygame.SRCALPHA)
        bar.fill((220, 80, 0, 160))
        surface.blit(bar, r)


class NitroStrip:
    """Collectible road strip that grants Nitro."""
    def __init__(self, lane: int, y: float):
        self.lane = lane
        self.x    = float(lane_x(lane))
        self.y    = y
        self.w    = LANE_WIDTH - 12
        self.h    = 30

    def update(self, scroll_speed: float) -> None:
        self.y += scroll_speed

    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x) - self.w // 2, int(self.y) - self.h // 2, self.w, self.h)

    def is_off_screen(self) -> bool:
        return self.y > SCREEN_H + self.h

    def draw(self, surface: pygame.Surface) -> None:
        r = self.rect()
        surf = pygame.Surface((r.width, r.height), pygame.SRCALPHA)
        surf.fill((0, 220, 255, 160))
        surface.blit(surf, r)
        font = pygame.font.SysFont("Arial", 13, bold=True)
        lbl = font.render("NITRO", True, (0, 80, 160))
        surface.blit(lbl, (r.centerx - lbl.get_width() // 2, r.centery - lbl.get_height() // 2))


# ─── Power-Up Item ─────────────────────────────────────────────────────────────

class PowerUpItem:
    COLORS = {
        "nitro":  (0, 220, 255),
        "shield": (100, 120, 255),
        "repair": (0, 200, 80),
    }
    LABELS = {
        "nitro":  "N",
        "shield": "S",
        "repair": "R",
    }

    def __init__(self, kind: str, lane: int, y: float):
        self.kind     = kind
        self.lane     = lane
        self.x        = float(lane_x(lane))
        self.y        = y
        self.w        = POWERUP_W
        self.h        = POWERUP_H
        self.born_ms  = pygame.time.get_ticks()
        self._pulse   = 0.0

    def update(self, scroll_speed: float, dt: float) -> None:
        self.y     += scroll_speed
        self._pulse += dt * 5

    def is_expired(self) -> bool:
        return pygame.time.get_ticks() - self.born_ms > POWERUP_LIFESPAN

    def is_off_screen(self) -> bool:
        return self.y > SCREEN_H + self.h

    def rect(self) -> pygame.Rect:
        return pygame.Rect(
            int(self.x) - self.w // 2,
            int(self.y) - self.h // 2,
            self.w, self.h
        )

    def draw(self, surface: pygame.Surface) -> None:
        r    = self.rect()
        col  = self.COLORS[self.kind]
        alpha = int(160 + 80 * math.sin(self._pulse))

        glow = pygame.Surface((self.w + 12, self.h + 12), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*col, alpha // 2),
                           (glow.get_width() // 2, glow.get_height() // 2),
                           self.w // 2 + 6)
        surface.blit(glow, (r.x - 6, r.y - 6))

        pygame.draw.circle(surface, col, r.center, self.w // 2)
        pygame.draw.circle(surface, (255, 255, 255), r.center, self.w // 2, 2)

        font = pygame.font.SysFont("Arial", 18, bold=True)
        lbl  = font.render(self.LABELS[self.kind], True, (255, 255, 255))
        surface.blit(lbl, (r.centerx - lbl.get_width() // 2,
                            r.centery - lbl.get_height() // 2))

        elapsed = (pygame.time.get_ticks() - self.born_ms) / POWERUP_LIFESPAN
        bar_w = int(self.w * (1 - elapsed))
        if bar_w > 0:
            pygame.draw.rect(surface, col,
                             pygame.Rect(r.left, r.bottom + 2, bar_w, 3))


# ─── Road Scroller ─────────────────────────────────────────────────────────────

class RoadScroller:
    """
    Tiles the AnimatedStreet background texture vertically.
    Uses two copies to ensure seamless looping with no visible seam.
    """
    def __init__(self):
        self.bg = None
        self.bg_h = SCREEN_H
        try:
            raw = pygame.image.load("assets/AnimatedStreet.png").convert()
            # Scale to exact screen width; keep aspect ratio for height
            img_w, img_h = raw.get_size()
            scaled_h = int(img_h * SCREEN_W / img_w)
            # Ensure at least SCREEN_H tall so tiling covers the screen
            scaled_h = max(scaled_h, SCREEN_H)
            self.bg   = pygame.transform.scale(raw, (SCREEN_W, scaled_h))
            self.bg_h = scaled_h
        except Exception:
            pass
        self.offset = 0.0

    def update(self, speed: float) -> None:
        self.offset = (self.offset + speed) % self.bg_h

    def draw(self, surface: pygame.Surface) -> None:
        if self.bg:
            # Draw two tiles so there's always full coverage
            y1 = int(self.offset)
            y2 = y1 - self.bg_h
            surface.blit(self.bg, (0, y2))
            surface.blit(self.bg, (0, y1))
        else:
            # Fallback: plain grey road with dashed lane lines
            surface.fill((90, 90, 90))
            for lx in LANE_CENTERS[:-1]:
                for dy in range(0, SCREEN_H, 40):
                    pygame.draw.rect(surface, (220, 220, 100),
                                     pygame.Rect(lx - 2, dy, 4, 22))


# ─── GameSession ───────────────────────────────────────────────────────────────

class GameSession:
    """
    Manages all runtime state for one playthrough.
    """

    def __init__(self, settings: dict, sound_manager):
        diff_name = settings.get("difficulty", "normal")
        diff      = DIFFICULTY.get(diff_name, DIFFICULTY["normal"])

        init_assets(settings.get("car_color", "blue"))

        self.road       = RoadScroller()
        self.player     = Player()
        self.player.speed = diff["base_speed"]

        self.enemies:      list[EnemyCar]      = []
        self.coins:        list[Coin]          = []
        self.powerups:     list[PowerUpItem]   = []
        self.oils:         list[OilSpill]      = []
        self.bumps:        list[SpeedBump]     = []
        self.potholes:     list[Pothole]       = []
        self.barriers:     list[MovingBarrier] = []
        self.nitro_strips: list[NitroStrip]    = []

        self.coin_count  = 0
        self.score       = 0
        self.distance    = 0.0

        self._enemy_timer    = 0.0
        self._coin_timer     = 0.0
        self._hazard_timer   = 0.0
        self._powerup_timer  = 0.0
        self._diff_timer     = 0.0

        self._base_speed     = diff["base_speed"]
        self._enemy_interval = diff["enemy_interval"] / 1000
        self._hazard_prob    = diff["hazard_prob"]
        self._diff_name      = diff_name

        self.active_powerup: tuple | None = None

        self.sound     = sound_manager
        self.game_over = False

    # ── Input ──────────────────────────────────────────────────────────────────

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_LEFT, pygame.K_a):
                self.player.move_left()
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self.player.move_right()

    # ── Update ─────────────────────────────────────────────────────────────────

    def update(self, dt: float) -> None:
        if self.game_over:
            return

        spd = self.player.effective_speed()

        self.road.update(spd)
        self.distance += spd

        self.player.update(dt)

        # Difficulty scaling every 30 seconds
        self._diff_timer += dt
        if self._diff_timer >= 30:
            self._diff_timer = 0
            self.player.speed = min(self.player.speed + 0.5, 14)
            self._enemy_interval = max(self._enemy_interval - 0.1, 0.5)

        # Spawn enemies
        self._enemy_timer += dt
        if self._enemy_timer >= self._enemy_interval:
            self._enemy_timer = 0
            self._spawn_enemy(spd)

        # Spawn coins
        self._coin_timer += dt
        if self._coin_timer >= 1.2:
            self._coin_timer = 0
            lane = random_lane()
            self.coins.append(Coin(lane, -COIN_H))

        # Spawn hazards
        self._hazard_timer += dt
        if self._hazard_timer >= 1.5:
            self._hazard_timer = 0
            self._maybe_spawn_hazard()

        # Spawn power-ups
        self._powerup_timer += dt
        if self._powerup_timer >= 8.0:
            self._powerup_timer = 0
            kind = random.choice(POWERUP_TYPES)
            lane = random_lane()
            self.powerups.append(PowerUpItem(kind, lane, -POWERUP_H))

        # Update all objects — pass scroll speed to enemies
        for e in self.enemies:
            e.update(dt, spd)
        for c in self.coins:
            c.update(spd, dt)
        for p in self.powerups:
            p.update(spd, dt)
        for o in self.oils:
            o.update(spd)
        for b in self.bumps:
            b.update(spd)
        for ph in self.potholes:
            ph.update(spd)
        for bar in self.barriers:
            bar.update(spd, dt)
        for ns in self.nitro_strips:
            ns.update(spd)

        if self.active_powerup:
            kind, remaining = self.active_powerup
            remaining -= dt
            if remaining <= 0:
                self.active_powerup = None
            else:
                self.active_powerup = (kind, remaining)

        self._check_collisions()
        self._cleanup()

        self.score = self.coin_count * 10 + int(self.distance // 50)

    def _spawn_enemy(self, player_speed: float) -> None:
        lane = random_lane()
        if lane == self.player.lane:
            lane = (lane + 1) % LANE_COUNT
        # speed in pixels/second — enemy moves ~60–180 px/s relative to scroll
        speed = (self._base_speed * 0.6 + random.uniform(0.5, 1.5)) * 60
        self.enemies.append(EnemyCar(lane, -ENEMY_H, speed))

    def _maybe_spawn_hazard(self) -> None:
        """
        FIX: Replaced broken overlapping probability thresholds with a
        clean weighted random choice so each hazard type spawns at a
        predictable, balanced rate.

        Base spawn chance per check: hazard_prob (e.g. 0.005 for normal).
        If the roll passes, pick one hazard type from a weighted table.
        """
        if random.random() > self._hazard_prob * 30:
            return  # no hazard this tick

        # Weights: higher = more common
        hazard_choices = ["oil", "bump", "pothole", "barrier", "nitro_strip"]
        hazard_weights = [35,    25,     20,         10,        10]

        choice = random.choices(hazard_choices, weights=hazard_weights, k=1)[0]

        if choice == "oil":
            self.oils.append(OilSpill(random_lane(), -50))
        elif choice == "bump":
            self.bumps.append(SpeedBump(-20))
        elif choice == "pothole":
            self.potholes.append(Pothole(random_lane(), -50))
        elif choice == "barrier":
            self.barriers.append(MovingBarrier(-30))
        elif choice == "nitro_strip":
            self.nitro_strips.append(NitroStrip(random_lane(), -40))

    def _check_collisions(self) -> None:
        pr = self.player.rect()

        for e in self.enemies[:]:
            if pr.colliderect(e.rect()):
                if self.player.inv_timer > 0:
                    continue
                if self.player.consume_shield():
                    self.enemies.remove(e)
                    self.sound.play("crash")
                else:
                    self.game_over = True
                    self.sound.play("crash")
                    return

        for c in self.coins[:]:
            if pr.colliderect(c.rect()):
                self.coin_count += c.value
                self.coins.remove(c)
                self.sound.play("coin")

        for p in self.powerups[:]:
            if pr.colliderect(p.rect()):
                self._apply_powerup(p.kind)
                self.powerups.remove(p)

        for o in self.oils[:]:
            if pr.colliderect(o.rect()):
                self.player.apply_slow(2.5)

        for b in self.bumps[:]:
            if pr.colliderect(b.rect()):
                self.player.apply_slow(1.0)

        for ph in self.potholes[:]:
            if pr.colliderect(ph.rect()):
                if self.player.inv_timer > 0:
                    continue
                if self.player.consume_shield():
                    self.potholes.remove(ph)
                    self.sound.play("crash")
                else:
                    self.game_over = True
                    self.sound.play("crash")
                    return

        for bar in self.barriers[:]:
            if pr.colliderect(bar.rect()):
                if self.player.inv_timer > 0:
                    continue
                if self.player.consume_shield():
                    self.barriers.remove(bar)
                    self.sound.play("crash")
                else:
                    self.game_over = True
                    self.sound.play("crash")
                    return

        for ns in self.nitro_strips[:]:
            if pr.colliderect(ns.rect()):
                self.player.apply_nitro()
                self.active_powerup = ("nitro", self.player.nitro_timer)
                self.nitro_strips.remove(ns)

    def _apply_powerup(self, kind: str) -> None:
        if kind == "nitro":
            self.player.apply_nitro()
            self.active_powerup = ("nitro", self.player.nitro_timer)
        elif kind == "shield":
            self.player.apply_shield()
            self.active_powerup = ("shield", 999)
        elif kind == "repair":
            self.player.inv_timer = 2000
            if self.potholes:
                self.potholes.pop()
            elif self.barriers:
                self.barriers.pop()
            elif self.oils:
                self.oils.pop()
            self.active_powerup = ("repair", 0.5)

    def _cleanup(self) -> None:
        self.enemies      = [e  for e  in self.enemies      if not e.is_off_screen()]
        self.coins        = [c  for c  in self.coins        if not c.is_off_screen()]
        self.powerups     = [p  for p  in self.powerups     if not p.is_expired() and not p.is_off_screen()]
        self.oils         = [o  for o  in self.oils         if not o.is_off_screen()]
        self.bumps        = [b  for b  in self.bumps        if not b.is_off_screen()]
        self.potholes     = [ph for ph in self.potholes     if not ph.is_off_screen()]
        self.barriers     = [br for br in self.barriers     if not br.is_off_screen()]
        self.nitro_strips = [ns for ns in self.nitro_strips if not ns.is_off_screen()]

    # ── Draw ───────────────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface) -> None:
        self.road.draw(surface)

        for ns in self.nitro_strips:
            ns.draw(surface)
        for b in self.bumps:
            b.draw(surface)
        for o in self.oils:
            o.draw(surface)
        for bar in self.barriers:
            bar.draw(surface)
        for ph in self.potholes:
            ph.draw(surface)
        for c in self.coins:
            c.draw(surface)
        for p in self.powerups:
            p.draw(surface)
        for e in self.enemies:
            e.draw(surface)

        self.player.draw(surface)
        self._draw_hud(surface)

    def _draw_hud(self, surface: pygame.Surface) -> None:
        font_sm = pygame.font.SysFont("Arial", 16, bold=True)
        font_md = pygame.font.SysFont("Arial", 20, bold=True)

        hud = pygame.Surface((SCREEN_W, 52), pygame.SRCALPHA)
        hud.fill((0, 0, 0, 140))
        surface.blit(hud, (0, 0))

        score_lbl = font_md.render(f"Score: {self.score}", True, (255, 230, 0))
        surface.blit(score_lbl, (8, 4))

        coin_lbl = font_sm.render(f"Coins: {self.coin_count}", True, (200, 255, 100))
        surface.blit(coin_lbl, (8, 28))

        dist_m = int(self.distance // 10)
        dist_lbl = font_sm.render(f"Dist: {dist_m}m", True, (180, 220, 255))
        surface.blit(dist_lbl, (SCREEN_W // 2 - dist_lbl.get_width() // 2, 28))

        spd_lbl = font_sm.render(f"Speed: {self.player.effective_speed():.1f}", True, (200, 200, 200))
        surface.blit(spd_lbl, (SCREEN_W - spd_lbl.get_width() - 8, 28))

        if self.active_powerup:
            kind, remaining = self.active_powerup
            pu_colors = {"nitro": (0, 220, 255), "shield": (100, 120, 255), "repair": (0, 200, 80)}
            col = pu_colors.get(kind, (255, 255, 255))
            if kind == "shield":
                txt = f"[{kind.upper()}] ACTIVE"
            elif kind == "repair":
                txt = f"[{kind.upper()}] APPLIED"
            else:
                txt = f"[{kind.upper()}] {remaining:.1f}s"
            pu_lbl = font_sm.render(txt, True, col)
            surface.blit(pu_lbl, (SCREEN_W - pu_lbl.get_width() - 8, 6))

        if self.player.shield_active:
            shield_lbl = font_sm.render("** SHIELD **", True, (100, 120, 255))
            surface.blit(shield_lbl, (SCREEN_W // 2 - shield_lbl.get_width() // 2, 6))