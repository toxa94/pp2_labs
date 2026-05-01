# game.py — Core gameplay logic (Snake, Food, Power-ups, Obstacles)
#
# This module intentionally does NOT handle Pygame rendering or event loops —
# that responsibility belongs to main.py.  game.py exposes a GameState class
# that encapsulates every mutable piece of game data and the rules that
# transform it each tick.

from __future__ import annotations

import random
import math
from dataclasses import dataclass, field
from typing import Optional

import pygame

from config import (
    COLS, ROWS, CELL_SIZE,
    BASE_SPEED, SPEED_PER_LEVEL, MAX_SPEED,
    FOOD_PER_LEVEL,
    BONUS_FOOD_CHANCE, BONUS_FOOD_TTL, POISON_CHANCE,
    POWERUP_SPAWN_INTERVAL, POWERUP_TTL, POWERUP_DURATION,
    OBSTACLE_PER_LEVEL,
    SNAKE_SHRINK,
)

# ── Types & helpers ────────────────────────────────────────────────────────────
Point = tuple[int, int]   # (col, row) grid coordinates

UP    = ( 0, -1)
DOWN  = ( 0,  1)
LEFT  = (-1,  0)
RIGHT = ( 1,  0)
OPPOSITE = {UP: DOWN, DOWN: UP, LEFT: RIGHT, RIGHT: LEFT}


def rand_cell(exclude: set[Point]) -> Point:
    """Return a random grid cell that is not in *exclude*."""
    while True:
        p = (random.randint(1, COLS - 2), random.randint(1, ROWS - 2))
        if p not in exclude:
            return p


# ── Food ──────────────────────────────────────────────────────────────────────

@dataclass
class Food:
    pos:      Point
    kind:     str   # "normal" | "bonus" | "poison"
    points:   int   = 10
    expire_at: Optional[int] = None   # ms timestamp; None = never

    def is_expired(self, now_ms: int) -> bool:
        return self.expire_at is not None and now_ms >= self.expire_at


# ── Power-up ──────────────────────────────────────────────────────────────────

@dataclass
class PowerUp:
    pos:       Point
    kind:      str    # "speed_boost" | "slow_motion" | "shield"
    expire_at: int    # field-presence deadline (ms)

    def is_expired(self, now_ms: int) -> bool:
        return now_ms >= self.expire_at


@dataclass
class ActiveEffect:
    kind:      str
    end_at:    int    # effect-active deadline (ms)

    def is_done(self, now_ms: int) -> bool:
        return now_ms >= self.end_at


# ── GameState ─────────────────────────────────────────────────────────────────

class GameState:
    """
    Encapsulates the mutable state of one snake-game session.

    Call  .tick(now_ms)  every game-logic frame.
    Inspect .game_over  to detect the terminal state.
    """

    def __init__(self):
        # ── Snake ──────────────────────────────────────────────────────────
        cx, cy = COLS // 2, ROWS // 2
        self.body: list[Point] = [(cx, cy), (cx - 1, cy), (cx - 2, cy)]
        self.direction:  Point = RIGHT
        self._next_dir:  Point = RIGHT

        # ── Scoring ────────────────────────────────────────────────────────
        self.score:        int  = 0
        self.level:        int  = 1
        self._food_eaten:  int  = 0   # counts toward next level

        # ── Speed (moves per second) ────────────────────────────────────────
        self._base_speed: float = BASE_SPEED
        self._move_accum: float = 0.0   # fractional-move accumulator

        # ── Obstacles ──────────────────────────────────────────────────────
        self.obstacles: set[Point] = set()

        # ── Food & power-ups ───────────────────────────────────────────────
        self.foods:    list[Food]    = []
        self.powerup:  Optional[PowerUp]   = None
        self.effects:  list[ActiveEffect]  = []
        self.shield_active: bool = False

        # Timers
        self._last_powerup_attempt: int = 0

        # ── State flags ────────────────────────────────────────────────────
        self.game_over:  bool  = False
        self.shield_flash: int = 0   # ms countdown for shield-hit visual

        # Spawn initial food
        self._spawn_food()

    # ── Public interface ───────────────────────────────────────────────────────

    def set_direction(self, new_dir: Point):
        """Queue a direction change; ignores 180° reversals."""
        if new_dir != OPPOSITE.get(self.direction):
            self._next_dir = new_dir

    def tick(self, now_ms: int, dt_s: float):
        """
        Advance game logic by *dt_s* seconds.
        *now_ms* = pygame.time.get_ticks() value.
        """
        if self.game_over:
            return

        self._expire_food(now_ms)
        self._expire_powerup(now_ms)
        self._expire_effects(now_ms)

        # Accumulate movement
        speed = self._current_speed()
        self._move_accum += speed * dt_s
        steps = int(self._move_accum)
        self._move_accum -= steps

        for _ in range(steps):
            self._step(now_ms)
            if self.game_over:
                break

        # Try spawning a power-up
        if now_ms - self._last_powerup_attempt >= POWERUP_SPAWN_INTERVAL:
            self._last_powerup_attempt = now_ms
            if self.powerup is None:
                self._spawn_powerup(now_ms)

    # ── Private: movement ──────────────────────────────────────────────────────

    def _step(self, now_ms: int):
        self.direction = self._next_dir
        head = self.body[0]
        new_head = (
            (head[0] + self.direction[0]) % COLS,
            (head[1] + self.direction[1]) % ROWS,
        )

        # Wall / border collision (cells on the outermost ring)
        if (new_head[0] == 0 or new_head[0] == COLS - 1 or
                new_head[1] == 0 or new_head[1] == ROWS - 1):
            self._handle_lethal_collision()
            return

        # Obstacle collision
        if new_head in self.obstacles:
            self._handle_lethal_collision()
            return

        # Self collision
        if new_head in self.body[:-1]:
            self._handle_lethal_collision()
            return

        # Move snake
        self.body.insert(0, new_head)
        self.body.pop()          # default: no growth

        # Check food
        for food in self.foods[:]:
            if new_head == food.pos:
                self._eat_food(food, now_ms)
                break

        # Check power-up
        if self.powerup and new_head == self.powerup.pos:
            self._collect_powerup(now_ms)

    def _handle_lethal_collision(self):
        if self.shield_active:
            self.shield_active = False
            self.shield_flash  = 400   # ms of visual feedback
            # Remove the shield effect from active list
            self.effects = [e for e in self.effects if e.kind != "shield"]
        else:
            self.game_over = True

    # ── Private: food ─────────────────────────────────────────────────────────

    def _occupied(self) -> set[Point]:
        occupied = set(self.body) | self.obstacles
        occupied |= {f.pos for f in self.foods}
        if self.powerup:
            occupied.add(self.powerup.pos)
        return occupied

    def _spawn_food(self):
        pos = rand_cell(self._occupied())
        r   = random.random()
        if r < POISON_CHANCE:
            kind, pts, ttl = "poison", 0, None
        elif r < POISON_CHANCE + BONUS_FOOD_CHANCE:
            kind, pts, ttl = "bonus", 25, pygame.time.get_ticks() + BONUS_FOOD_TTL
        else:
            kind, pts, ttl = "normal", 10, None
        self.foods.append(Food(pos=pos, kind=kind, points=pts, expire_at=ttl))

    def _expire_food(self, now_ms: int):
        removed = [f for f in self.foods if f.is_expired(now_ms)]
        self.foods = [f for f in self.foods if not f.is_expired(now_ms)]
        for _ in removed:
            self._spawn_food()   # replace expired food

    def _eat_food(self, food: Food, now_ms: int):
        self.foods.remove(food)

        if food.kind == "poison":
            # Shrink snake
            shrink = min(SNAKE_SHRINK, len(self.body) - 1)
            self.body = self.body[:-shrink] if shrink > 0 else self.body
            if len(self.body) <= 1:
                self.game_over = True
                return
        else:
            # Grow snake by 1
            self.body.append(self.body[-1])
            self.score += food.points
            self._food_eaten += 1
            if self._food_eaten >= FOOD_PER_LEVEL:
                self._level_up()

        self._spawn_food()

    # ── Private: levels ────────────────────────────────────────────────────────

    def _level_up(self):
        self._food_eaten = 0
        self.level      += 1
        self._base_speed = min(
            BASE_SPEED + (self.level - 1) * SPEED_PER_LEVEL,
            MAX_SPEED,
        )
        # Add obstacles from level 3 onward
        if self.level >= 3:
            self._spawn_obstacles()

    def _spawn_obstacles(self):
        attempts = OBSTACLE_PER_LEVEL
        for _ in range(attempts):
            exclude = self._occupied()
            # Also protect a small zone around the snake's head
            head = self.body[0]
            safe_zone = {
                (head[0] + dx, head[1] + dy)
                for dx in range(-3, 4)
                for dy in range(-3, 4)
            }
            exclude |= safe_zone
            # Avoid border cells (already lethal)
            pos = rand_cell(exclude)
            if pos[0] in (0, COLS-1) or pos[1] in (0, ROWS-1):
                continue
            self.obstacles.add(pos)

    # ── Private: power-ups ────────────────────────────────────────────────────

    def _spawn_powerup(self, now_ms: int):
        kind = random.choice(["speed_boost", "slow_motion", "shield"])
        pos  = rand_cell(self._occupied())
        self.powerup = PowerUp(pos=pos, kind=kind,
                               expire_at=now_ms + POWERUP_TTL)

    def _collect_powerup(self, now_ms: int):
        kind = self.powerup.kind
        self.powerup = None

        # Remove any conflicting active effect
        self.effects = [e for e in self.effects if e.kind != kind]

        end = now_ms + POWERUP_DURATION
        self.effects.append(ActiveEffect(kind=kind, end_at=end))

        if kind == "shield":
            self.shield_active = True

    def _expire_powerup(self, now_ms: int):
        if self.powerup and self.powerup.is_expired(now_ms):
            self.powerup = None

    def _expire_effects(self, now_ms: int):
        done = [e for e in self.effects if e.is_done(now_ms)]
        self.effects = [e for e in self.effects if not e.is_done(now_ms)]
        for e in done:
            if e.kind == "shield":
                self.shield_active = False

    # ── Private: speed ────────────────────────────────────────────────────────

    def _current_speed(self) -> float:
        speed = self._base_speed
        for e in self.effects:
            if e.kind == "speed_boost":
                speed = min(speed * 1.6, MAX_SPEED)
            elif e.kind == "slow_motion":
                speed = max(speed * 0.5, 2)
        return speed

    # ── Convenience properties ────────────────────────────────────────────────

    @property
    def head(self) -> Point:
        return self.body[0]

    def active_effect_kinds(self) -> list[str]:
        return [e.kind for e in self.effects]