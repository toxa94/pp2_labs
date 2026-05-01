# main.py — Pygame application: screens, rendering, input, settings I/O
#
# Screens:   MENU → GAME → GAMEOVER → MENU
#                 ↘ LEADERBOARD ↗
#                 ↘ SETTINGS   ↗

from __future__ import annotations

import json
import math
import os
import sys
import time
from pathlib import Path
from typing import Optional

import pygame

from config import *
from db    import Database
from game  import GameState, UP, DOWN, LEFT, RIGHT


# ── Settings helpers ──────────────────────────────────────────────────────────
SETTINGS_PATH = Path(__file__).parent / "settings.json"
DEFAULT_SETTINGS = {
    "snake_color": [80, 200, 120],
    "grid":        True,
    "sound":       False,
}


def load_settings() -> dict:
    try:
        with open(SETTINGS_PATH) as f:
            data = json.load(f)
        # Fill missing keys with defaults
        for k, v in DEFAULT_SETTINGS.items():
            data.setdefault(k, v)
        return data
    except Exception:
        return dict(DEFAULT_SETTINGS)


def save_settings(settings: dict):
    with open(SETTINGS_PATH, "w") as f:
        json.dump(settings, f, indent=2)


# ── Font helpers ──────────────────────────────────────────────────────────────

def _font(size: int, bold: bool = False) -> pygame.font.Font:
    return pygame.font.SysFont("Segoe UI Symbol", size, bold=bold)


# ── Button widget ─────────────────────────────────────────────────────────────

class Button:
    def __init__(self, rect: pygame.Rect, label: str, font: pygame.font.Font):
        self.rect   = rect
        self.label  = label
        self.font   = font
        self.hovered = False

    def draw(self, surf: pygame.Surface):
        color  = BTN_HOVER   if self.hovered else BTN_NORMAL
        border = ACCENT      if self.hovered else BTN_BORDER
        pygame.draw.rect(surf, color,  self.rect, border_radius=8)
        pygame.draw.rect(surf, border, self.rect, 2, border_radius=8)
        text = self.font.render(self.label, True,
                                WHITE if self.hovered else TEXT_MAIN)
        surf.blit(text, text.get_rect(center=self.rect.center))

    def update(self, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)

    def clicked(self, event) -> bool:
        return (event.type == pygame.MOUSEBUTTONDOWN and
                event.button == 1 and
                self.rect.collidepoint(event.pos))


# ── Main application ──────────────────────────────────────────────────────────

class App:

    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        pygame.display.set_caption("Snake — TSIS 4")

        self.screen  = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock   = pygame.time.Clock()

        # Sounds
        self.sound_food = pygame.mixer.Sound("TSIS/TSIS4/assets/food.mp3")
        self.sound_game_over = pygame.mixer.Sound("TSIS/TSIS4/assets/game_over.mp3")

        pygame.mixer.music.load("TSIS/TSIS4/assets/background.mp3")
        pygame.mixer.music.play(-1)

        # Fonts
        self.font_xl  = _font(64, bold=True)
        self.font_lg  = _font(36, bold=True)
        self.font_md  = _font(24)
        self.font_sm  = _font(18)
        self.font_xs  = _font(14)

        # Settings
        self.settings = load_settings()

        # Database
        self.db = Database()
        self.db_ok = self.db.connect()
        if self.db_ok:
            self.db.init_schema()

        # State
        self.screen_name: str       = SCREEN_MENU
        self.username:    str       = ""
        self.player_id:   Optional[int] = None
        self.personal_best: int     = 0
        self.game_state:  Optional[GameState] = None
        self._input_active: bool    = True   # for username input
        self._leaderboard_cache: list = []

        # Color picker state (settings screen)
        self._color_r = self.settings["snake_color"][0]
        self._color_g = self.settings["snake_color"][1]
        self._color_b = self.settings["snake_color"][2]

    # ── Main loop ─────────────────────────────────────────────────────────────

    def run(self):
        while True:
            dt = self.clock.tick(FPS) / 1000.0
            now = pygame.time.get_ticks()

            events = pygame.event.get()
            for e in events:
                if e.type == pygame.QUIT:
                    self._quit()

            mouse = pygame.mouse.get_pos()

            if self.screen_name == SCREEN_MENU:
                self._menu_frame(events, mouse)
            elif self.screen_name == SCREEN_GAME:
                self._game_frame(events, mouse, dt, now)
            elif self.screen_name == SCREEN_GAMEOVER:
                self._gameover_frame(events, mouse)
            elif self.screen_name == SCREEN_LEADERBOARD:
                self._leaderboard_frame(events, mouse)
            elif self.screen_name == SCREEN_SETTINGS:
                self._settings_frame(events, mouse)

            pygame.display.flip()

    def _quit(self):
        self.db.close()
        pygame.quit()
        sys.exit()

    # ═══════════════════════════════════════════════════════════════════════════
    # MENU SCREEN
    # ═══════════════════════════════════════════════════════════════════════════

    def _menu_frame(self, events, mouse):
        surf = self.screen
        surf.fill(DARK_BG)
        self._draw_grid_bg()

        # Title
        title = self.font_xl.render("SNAKE", True, ACCENT)
        surf.blit(title, title.get_rect(centerx=WINDOW_WIDTH // 2, y=60))
        sub = self.font_sm.render("TSIS 4 — Database Edition", True, TEXT_DIM)
        surf.blit(sub, sub.get_rect(centerx=WINDOW_WIDTH // 2, y=130))

        cx = WINDOW_WIDTH // 2
        bw, bh = 260, 48
        buttons = [
            Button(pygame.Rect(cx - bw//2, 200, bw, bh), "▶  PLAY",        self.font_md),
            Button(pygame.Rect(cx - bw//2, 260, bw, bh), "🏆  LEADERBOARD", self.font_md),
            Button(pygame.Rect(cx - bw//2, 320, bw, bh), "⚙  SETTINGS",    self.font_md),
            Button(pygame.Rect(cx - bw//2, 380, bw, bh), "✕  QUIT",         self.font_md),
        ]
        for b in buttons:
            b.update(mouse)
            b.draw(surf)

        # Username input box
        self._draw_username_box(surf, events)

        # DB status
        db_label = "● DB connected" if self.db_ok else "○ DB offline (scores won't save)"
        db_color  = ACCENT if self.db_ok else (200, 80, 80)
        db_surf   = self.font_xs.render(db_label, True, db_color)
        surf.blit(db_surf, (16, WINDOW_HEIGHT - 28))

        for e in events:
            if buttons[0].clicked(e):
                if self.username.strip():
                    self._start_game()
                # else flash prompt (username required)
            elif buttons[1].clicked(e):
                self._leaderboard_cache = self.db.get_leaderboard()
                self.screen_name = SCREEN_LEADERBOARD
            elif buttons[2].clicked(e):
                self.screen_name = SCREEN_SETTINGS
            elif buttons[3].clicked(e):
                self._quit()

    def _draw_username_box(self, surf, events):
        label = self.font_sm.render("Username:", True, TEXT_DIM)
        surf.blit(label, (WINDOW_WIDTH // 2 - 160, 456))

        box_rect = pygame.Rect(WINDOW_WIDTH // 2 - 160, 480, 320, 42)
        pygame.draw.rect(surf, PANEL_BG, box_rect, border_radius=6)
        pygame.draw.rect(surf, ACCENT if self._input_active else BTN_BORDER,
                         box_rect, 2, border_radius=6)

        display = self.username + ("|" if int(time.time() * 2) % 2 == 0 else " ")
        text_s  = self.font_md.render(display, True, WHITE)
        surf.blit(text_s, (box_rect.x + 10, box_rect.y + 8))

        if not self.username.strip():
            hint = self.font_xs.render("Enter username to play", True, (200, 80, 80))
            surf.blit(hint, hint.get_rect(centerx=WINDOW_WIDTH // 2, y=528))

        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN:
                self._input_active = box_rect.collidepoint(e.pos)
            if e.type == pygame.KEYDOWN and self._input_active:
                if e.key == pygame.K_BACKSPACE:
                    self.username = self.username[:-1]
                elif e.key in (pygame.K_RETURN, pygame.K_TAB):
                    self._input_active = False
                elif len(self.username) < 20 and e.unicode.isprintable():
                    self.username += e.unicode

    # ═══════════════════════════════════════════════════════════════════════════
    # GAME SCREEN
    # ═══════════════════════════════════════════════════════════════════════════

    def _start_game(self):
        # Resolve player in DB
        if self.db_ok:
            self.player_id    = self.db.get_or_create_player(self.username)
            self.personal_best = self.db.get_personal_best(self.player_id)
        else:
            self.player_id    = None
            self.personal_best = 0

        self.game_state  = GameState()
        self.screen_name = SCREEN_GAME

    def _game_frame(self, events, mouse, dt, now):
        gs = self.game_state

        # Input
        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_UP,    pygame.K_w): gs.set_direction(UP)
                if e.key in (pygame.K_DOWN,  pygame.K_s): gs.set_direction(DOWN)
                if e.key in (pygame.K_LEFT,  pygame.K_a): gs.set_direction(LEFT)
                if e.key in (pygame.K_RIGHT, pygame.K_d): gs.set_direction(RIGHT)
                if e.key == pygame.K_ESCAPE:
                    self.screen_name = SCREEN_MENU
                    return

        prev_score = gs.score
        prev_game_over = gs.game_over

        gs.tick(now, dt)

        # звук еды (если счет увеличился)
        if gs.score > prev_score:
            self.sound_food.play()

        # звук проигрыша
        if gs.game_over and not prev_game_over:
            self.sound_game_over.play()

        if gs.game_over:
            # Save to DB
            if self.db_ok and self.player_id is not None:
                self.db.save_session(self.player_id, gs.score, gs.level)
                self.personal_best = self.db.get_personal_best(self.player_id)
            self.screen_name = SCREEN_GAMEOVER
            return

        self._render_game(gs, now)

    def _render_game(self, gs: GameState, now: int):
        surf = self.screen
        surf.fill(DARK_BG)

        # Grid overlay
        if self.settings.get("grid"):
            self._draw_grid()

        # Obstacles
        for ob in gs.obstacles:
            self._draw_cell(surf, ob, OBSTACLE_COLOR)

        # Foods
        for food in gs.foods:
            color = FOOD_COLORS.get(food.kind, FOOD_COLORS["normal"])
            # Blink bonus food near expiry
            if food.expire_at:
                remaining = food.expire_at - now
                if remaining < 2000 and (remaining // 200) % 2 == 0:
                    color = TEXT_DIM
            self._draw_cell(surf, food.pos, color, radius_factor=0.45)

        # Power-up
        if gs.powerup:
            pu_color = POWERUP_COLORS.get(gs.powerup.kind, WHITE)
            # Pulse animation
            pulse = 0.35 + 0.15 * math.sin(now / 200)
            self._draw_cell(surf, gs.powerup.pos, pu_color, radius_factor=pulse)
            # Ring
            px = gs.powerup.pos[0] * CELL_SIZE + CELL_SIZE // 2
            py = gs.powerup.pos[1] * CELL_SIZE + CELL_SIZE // 2
            pygame.draw.circle(surf, pu_color, (px, py),
                               int(CELL_SIZE * 0.5), 2)

        # Snake body
        snake_color = tuple(self.settings["snake_color"])
        shield_active = gs.shield_active
        for i, seg in enumerate(gs.body):
            if i == 0:   # head — brighter
                c = tuple(min(255, int(v * 1.4)) for v in snake_color)
            else:
                fade = max(0.45, 1.0 - i * 0.015)
                c    = tuple(int(v * fade) for v in snake_color)

            if shield_active:
                # Violet tint while shielded
                c = (int(c[0] * 0.6 + 130),
                     int(c[1] * 0.6 + 60),
                     min(255, int(c[2] * 0.6 + 200)))

            self._draw_cell(surf, seg, c, radius_factor=0.42)

        # Shield-hit flash overlay
        if gs.shield_flash > 0:
            gs.shield_flash -= 16
            alpha = min(180, gs.shield_flash)
            flash = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            flash.fill((130, 80, 255, alpha))
            surf.blit(flash, (0, 0))

        # Border walls (visual)
        pygame.draw.rect(surf, BORDER_COLOR,
                         (0, 0, WINDOW_WIDTH, WINDOW_HEIGHT), CELL_SIZE)

        # HUD
        self._draw_hud(surf, gs, now)

    def _draw_hud(self, surf, gs: GameState, now: int):
        padding = 8
        # Score
        score_s = self.font_md.render(f"Score  {gs.score}", True, ACCENT)
        surf.blit(score_s, (CELL_SIZE + padding, CELL_SIZE + padding))

        # Level
        lvl_s = self.font_md.render(f"Lvl  {gs.level}", True, ACCENT2)
        surf.blit(lvl_s, (WINDOW_WIDTH // 2 - lvl_s.get_width() // 2,
                          CELL_SIZE + padding))

        # Personal best
        pb_s = self.font_sm.render(f"Best  {self.personal_best}", True, TEXT_DIM)
        surf.blit(pb_s, (WINDOW_WIDTH - pb_s.get_width() - CELL_SIZE - padding,
                         CELL_SIZE + padding))

        # Active effects
        effect_x = CELL_SIZE + padding
        effect_y  = WINDOW_HEIGHT - CELL_SIZE - 30
        for eff in gs.effects:
            remaining = max(0, eff.end_at - now)
            secs      = remaining / 1000
            label = {
                "speed_boost": f"⚡ FAST {secs:.1f}s",
                "slow_motion": f"🐢 SLOW {secs:.1f}s",
                "shield":      f"🛡 SHIELD {secs:.1f}s",
            }.get(eff.kind, eff.kind)
            eff_s = self.font_sm.render(label, True,
                                        POWERUP_COLORS.get(eff.kind, WHITE))
            surf.blit(eff_s, (effect_x, effect_y))
            effect_x += eff_s.get_width() + 20

    # ═══════════════════════════════════════════════════════════════════════════
    # GAME OVER SCREEN
    # ═══════════════════════════════════════════════════════════════════════════

    def _gameover_frame(self, events, mouse):
        surf = self.screen
        surf.fill(DARK_BG)
        self._draw_grid_bg()

        gs = self.game_state

        cx = WINDOW_WIDTH // 2

        # Title
        go_s = self.font_xl.render("GAME OVER", True, (220, 60, 60))
        surf.blit(go_s, go_s.get_rect(centerx=cx, y=80))

        # Stats panel
        panel = pygame.Rect(cx - 200, 170, 400, 160)
        pygame.draw.rect(surf, PANEL_BG, panel, border_radius=10)
        pygame.draw.rect(surf, BORDER_COLOR, panel, 2, border_radius=10)

        rows = [
            (f"Score",         str(gs.score),        ACCENT),
            (f"Level Reached", str(gs.level),         ACCENT2),
            (f"Personal Best", str(self.personal_best), TEXT_DIM),
        ]
        for i, (lbl, val, col) in enumerate(rows):
            y = 188 + i * 44
            lbl_s = self.font_md.render(lbl + ":", True, TEXT_DIM)
            val_s = self.font_md.render(val,       True, col)
            surf.blit(lbl_s, (panel.x + 20, y))
            surf.blit(val_s, (panel.right - val_s.get_width() - 20, y))

        bw, bh = 200, 48
        btn_retry = Button(pygame.Rect(cx - bw - 12, 360, bw, bh), "↺  RETRY",     self.font_md)
        btn_menu  = Button(pygame.Rect(cx + 12,       360, bw, bh), "⌂  MAIN MENU", self.font_md)

        for b in (btn_retry, btn_menu):
            b.update(mouse)
            b.draw(surf)

        for e in events:
            if btn_retry.clicked(e):
                self._start_game()
            elif btn_menu.clicked(e):
                self.screen_name = SCREEN_MENU

    # ═══════════════════════════════════════════════════════════════════════════
    # LEADERBOARD SCREEN
    # ═══════════════════════════════════════════════════════════════════════════

    def _leaderboard_frame(self, events, mouse):
        surf = self.screen
        surf.fill(DARK_BG)
        self._draw_grid_bg()

        cx = WINDOW_WIDTH // 2

        title = self.font_lg.render("🏆  TOP 10 LEADERBOARD", True, ACCENT2)
        surf.blit(title, title.get_rect(centerx=cx, y=30))

        # Table header
        headers = ["#", "Username", "Score", "Level", "Date"]
        col_x   = [60, 120, 380, 480, 560]
        header_y = 95
        for h, x in zip(headers, col_x):
            hs = self.font_sm.render(h, True, TEXT_DIM)
            surf.blit(hs, (x, header_y))
        pygame.draw.line(surf, BORDER_COLOR, (40, 118), (WINDOW_WIDTH - 40, 118), 1)

        # Table rows
        entries = self._leaderboard_cache
        if not entries and not self.db_ok:
            no_db = self.font_md.render("Database not connected.", True, (200, 80, 80))
            surf.blit(no_db, no_db.get_rect(centerx=cx, y=200))
        elif not entries:
            empty = self.font_md.render("No records yet.", True, TEXT_DIM)
            surf.blit(empty, empty.get_rect(centerx=cx, y=200))

        for i, row in enumerate(entries):
            y    = 130 + i * 42
            rank = i + 1
            bg   = PANEL_BG if i % 2 == 0 else (18, 22, 35)
            pygame.draw.rect(surf, bg, pygame.Rect(40, y - 4, WINDOW_WIDTH - 80, 38))

            rank_color = (ACCENT2 if rank == 1 else
                          (180, 180, 180) if rank == 2 else
                          (180, 120, 60) if rank == 3 else TEXT_MAIN)

            played_at = row["played_at"]
            date_str  = played_at.strftime("%m/%d %H:%M") if played_at else "—"

            cells = [str(rank), row["username"][:16],
                     str(row["score"]), str(row["level_reached"]), date_str]
            for cell, x in zip(cells, col_x):
                color = rank_color if cells.index(cell) == 0 else TEXT_MAIN
                cs = self.font_sm.render(cell, True, color)
                surf.blit(cs, (x, y + 4))

        # Back button
        bw, bh = 180, 44
        btn_back = Button(pygame.Rect(cx - bw//2, WINDOW_HEIGHT - 70, bw, bh),
                          "← BACK", self.font_md)
        btn_back.update(mouse)
        btn_back.draw(surf)

        for e in events:
            if btn_back.clicked(e):
                self.screen_name = SCREEN_MENU

    # ═══════════════════════════════════════════════════════════════════════════
    # SETTINGS SCREEN
    # ═══════════════════════════════════════════════════════════════════════════

    def _settings_frame(self, events, mouse):
        surf = self.screen
        surf.fill(DARK_BG)
        self._draw_grid_bg()

        cx = WINDOW_WIDTH // 2
        title = self.font_lg.render("⚙  SETTINGS", True, TEXT_MAIN)
        surf.blit(title, title.get_rect(centerx=cx, y=40))

        panel = pygame.Rect(cx - 250, 110, 500, 360)
        pygame.draw.rect(surf, PANEL_BG, panel, border_radius=12)
        pygame.draw.rect(surf, BORDER_COLOR, panel, 2, border_radius=12)

        # Grid toggle
        grid_btn = self._toggle_button(
            surf, mouse, pygame.Rect(cx - 200, 140, 180, 42),
            "Grid: ON" if self.settings["grid"] else "Grid: OFF",
            self.settings["grid"],
        )

        # Sound toggle
        snd_btn = self._toggle_button(
            surf, mouse, pygame.Rect(cx + 20, 140, 180, 42),
            "Sound: ON" if self.settings["sound"] else "Sound: OFF",
            self.settings["sound"],
        )

        # Snake color sliders
        lbl = self.font_sm.render("Snake Color (R / G / B):", True, TEXT_DIM)
        surf.blit(lbl, (cx - 200, 210))

        self._color_r = self._slider(surf, events, mouse, cx - 200, 240, self._color_r, (200, 60, 60))
        self._color_g = self._slider(surf, events, mouse, cx - 200, 280, self._color_g, (60, 200, 60))
        self._color_b = self._slider(surf, events, mouse, cx - 200, 320, self._color_b, (60, 120, 220))

        # Color preview
        preview_rect = pygame.Rect(cx + 100, 240, 90, 90)
        pygame.draw.rect(surf, (self._color_r, self._color_g, self._color_b),
                         preview_rect, border_radius=8)
        pygame.draw.rect(surf, BORDER_COLOR, preview_rect, 2, border_radius=8)

        # Save & Back button
        bw, bh = 220, 46
        btn_save = Button(pygame.Rect(cx - bw//2, 490, bw, bh), "💾  SAVE & BACK", self.font_md)
        btn_save.update(mouse)
        btn_save.draw(surf)

        for e in events:
            if grid_btn.clicked(e):
                self.settings["grid"] = not self.settings["grid"]
            if snd_btn.clicked(e):
                self.settings["sound"] = not self.settings["sound"]
            if btn_save.clicked(e):
                self.settings["snake_color"] = [self._color_r, self._color_g, self._color_b]
                save_settings(self.settings)
                self.screen_name = SCREEN_MENU

    def _toggle_button(self, surf, mouse, rect, label, active) -> Button:
        b = Button(rect, label, self.font_sm)
        b.hovered = rect.collidepoint(mouse)
        # Override color for active state
        color  = (30, 90, 50) if active else BTN_NORMAL
        border = ACCENT       if active else BTN_BORDER
        pygame.draw.rect(surf, color,  rect, border_radius=8)
        pygame.draw.rect(surf, border, rect, 2, border_radius=8)
        t = self.font_sm.render(label, True, ACCENT if active else TEXT_MAIN)
        surf.blit(t, t.get_rect(center=rect.center))
        return b

    def _slider(self, surf, events, mouse, x, y, value: int, color) -> int:
        """Simple RGB component slider; returns updated value."""
        BAR_W = 240
        bar_rect   = pygame.Rect(x, y + 10, BAR_W, 10)
        thumb_x    = x + int(value / 255 * BAR_W)
        thumb_rect = pygame.Rect(thumb_x - 7, y + 3, 14, 24)

        pygame.draw.rect(surf, PANEL_BG, bar_rect, border_radius=5)
        # Filled portion
        fill = pygame.Rect(x, y + 10, thumb_x - x, 10)
        pygame.draw.rect(surf, color, fill, border_radius=5)
        pygame.draw.rect(surf, BORDER_COLOR, bar_rect, 1, border_radius=5)
        pygame.draw.rect(surf, WHITE, thumb_rect, border_radius=4)

        # Drag
        if pygame.mouse.get_pressed()[0] and thumb_rect.inflate(20, 20).collidepoint(mouse):
            value = max(0, min(255, int((mouse[0] - x) / BAR_W * 255)))

        val_s = self.font_xs.render(str(value), True, TEXT_DIM)
        surf.blit(val_s, (x + BAR_W + 10, y + 6))

        return value

    # ── Rendering helpers ──────────────────────────────────────────────────────

    def _draw_cell(self, surf, pos, color, radius_factor=0.42):
        px = pos[0] * CELL_SIZE
        py = pos[1] * CELL_SIZE
        r  = int(CELL_SIZE * radius_factor)
        cx = px + CELL_SIZE // 2
        cy = py + CELL_SIZE // 2
        pygame.draw.circle(surf, color, (cx, cy), r)

    def _draw_grid(self):
        surf = self.screen
        for col in range(COLS):
            x = col * CELL_SIZE
            pygame.draw.line(surf, GRID_COLOR, (x, 0), (x, WINDOW_HEIGHT))
        for row in range(ROWS):
            y = row * CELL_SIZE
            pygame.draw.line(surf, GRID_COLOR, (0, y), (WINDOW_WIDTH, y))

    def _draw_grid_bg(self):
        """Draw a faint background grid (used on menu / overlay screens)."""
        for col in range(COLS):
            for row in range(ROWS):
                if (col + row) % 2 == 0:
                    r = pygame.Rect(col * CELL_SIZE, row * CELL_SIZE,
                                    CELL_SIZE, CELL_SIZE)
                    pygame.draw.rect(self.screen, (18, 21, 32), r)


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    App().run()