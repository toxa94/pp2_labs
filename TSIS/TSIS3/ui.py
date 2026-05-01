"""
ui.py
All Pygame screen classes:
  - MainMenu
  - SettingsScreen
  - LeaderboardScreen
  - GameOverScreen
  - UsernameEntry
Each screen has handle_event(event) → action_str and draw(surface).

FIX: Removed emoji from SysFont buttons — emoji glyphs are not reliably
supported by Arial/system fonts on all platforms and render as empty boxes.
All button labels now use plain ASCII.
"""

import pygame
import math
from racer import SCREEN_W, SCREEN_H

# ─── Palette ───────────────────────────────────────────────────────────────────
C_BG        = (10, 12, 28)
C_ROAD      = (40, 44, 60)
C_ACCENT    = (0, 210, 255)
C_GOLD      = (255, 210, 0)
C_WHITE     = (240, 240, 255)
C_GRAY      = (120, 130, 155)
C_RED       = (240, 60, 60)
C_GREEN     = (60, 220, 100)
C_PANEL     = (18, 22, 45)
C_PANEL2    = (24, 30, 58)

# ─── Fonts (lazy initialised) ─────────────────────────────────────────────────
_fonts: dict = {}

def _font(size: int, bold: bool = False) -> pygame.font.Font:
    key = (size, bold)
    if key not in _fonts:
        _fonts[key] = pygame.font.SysFont("Arial", size, bold=bold)
    return _fonts[key]


# ─── Reusable Button ──────────────────────────────────────────────────────────

class Button:
    def __init__(self, rect: pygame.Rect, text: str,
                 color=C_ACCENT, text_color=C_BG, font_size: int = 22):
        self.rect       = rect
        self.text       = text
        self.color      = color
        self.text_color = text_color
        self.font_size  = font_size
        self._hover     = False
        self._pulse     = 0.0

    def update(self, dt: float) -> None:
        mx, my = pygame.mouse.get_pos()
        self._hover = self.rect.collidepoint(mx, my)
        self._pulse = (self._pulse + dt * 4) % (math.pi * 2)

    def is_clicked(self, event: pygame.event.Event) -> bool:
        return (event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1
                and self.rect.collidepoint(event.pos))

    def draw(self, surface: pygame.Surface) -> None:
        scale  = 1.04 if self._hover else 1.0
        glow   = int(10 + 8 * math.sin(self._pulse)) if self._hover else 0
        col    = tuple(min(255, c + glow) for c in self.color)

        w = int(self.rect.width * scale)
        h = int(self.rect.height * scale)
        x = self.rect.centerx - w // 2
        y = self.rect.centery - h // 2
        r = pygame.Rect(x, y, w, h)

        pygame.draw.rect(surface, col, r, border_radius=10)
        if self._hover:
            pygame.draw.rect(surface, C_WHITE, r, 2, border_radius=10)

        f   = _font(self.font_size, bold=True)
        lbl = f.render(self.text, True, self.text_color)
        surface.blit(lbl, (r.centerx - lbl.get_width() // 2,
                           r.centery - lbl.get_height() // 2))


# ─── Stars background helper ──────────────────────────────────────────────────

def _draw_stars(surface: pygame.Surface, t: float) -> None:
    """Animate a simple starfield."""
    for i in range(40):
        x = (i * 73 + int(t * 5 * (i % 3 + 1))) % SCREEN_W
        y = (i * 47 + int(t * 10)) % SCREEN_H
        r = 1 + (i % 3)
        alpha = int(100 + 80 * math.sin(t * 2 + i))
        s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (200, 220, 255, alpha), (r, r), r)
        surface.blit(s, (x, y))


# ─── Main Menu ────────────────────────────────────────────────────────────────

class MainMenu:
    def __init__(self):
        bw, bh = 220, 48
        cx = SCREEN_W // 2 - bw // 2
        self.buttons = {
            "play":        Button(pygame.Rect(cx, 270, bw, bh), "> PLAY",          C_ACCENT),
            "leaderboard": Button(pygame.Rect(cx, 334, bw, bh), "LEADERBOARD",     C_GOLD,  C_BG),
            "settings":    Button(pygame.Rect(cx, 398, bw, bh), "SETTINGS",        C_PANEL2, C_WHITE),
            "quit":        Button(pygame.Rect(cx, 462, bw, bh), "QUIT",            C_RED,   C_WHITE),
        }
        self._t = 0.0

    def handle_event(self, event: pygame.event.Event) -> str | None:
        for name, btn in self.buttons.items():
            if btn.is_clicked(event):
                return name
        return None

    def update(self, dt: float) -> None:
        self._t += dt
        for btn in self.buttons.values():
            btn.update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(C_BG)
        _draw_stars(surface, self._t)

        # Animated road stripe at bottom
        road = pygame.Surface((SCREEN_W, 120), pygame.SRCALPHA)
        road.fill((30, 34, 50, 200))
        surface.blit(road, (0, SCREEN_H - 120))

        # Title with pulsing glow
        title_f = _font(52, bold=True)
        title   = title_f.render("RACER", True, C_ACCENT)
        glow_a  = int(60 + 40 * math.sin(self._t * 2))
        glow    = pygame.Surface(title.get_size(), pygame.SRCALPHA)
        glow.fill((0, 210, 255, glow_a))
        ty = 134 + int(math.sin(self._t) * 4)
        surface.blit(glow,  (SCREEN_W // 2 - title.get_width() // 2 + 4, ty + 4))
        surface.blit(title, (SCREEN_W // 2 - title.get_width() // 2, ty))

        sub = _font(16).render("Advanced Driving Edition", True, C_GRAY)
        surface.blit(sub, (SCREEN_W // 2 - sub.get_width() // 2, 198))

        for btn in self.buttons.values():
            btn.draw(surface)

        ver = _font(12).render("v3.0  |  Arrow keys / A-D to drive", True, C_GRAY)
        surface.blit(ver, (SCREEN_W // 2 - ver.get_width() // 2, SCREEN_H - 22))


# ─── Username Entry ───────────────────────────────────────────────────────────

class UsernameEntry:
    MAX_LEN = 16

    def __init__(self):
        bw, bh = 200, 46
        cx     = SCREEN_W // 2 - bw // 2
        self.start_btn   = Button(pygame.Rect(cx, 370, bw, bh), "START RACE", C_GREEN)
        self.back_btn    = Button(pygame.Rect(cx, 430, bw, bh), "<< BACK",    C_GRAY, C_WHITE)
        self.text        = ""
        self._cursor_t   = 0.0
        self._t          = 0.0
        self._input_rect = pygame.Rect(SCREEN_W // 2 - 140, 290, 280, 50)

    def handle_event(self, event: pygame.event.Event) -> tuple[str, str] | None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_RETURN:
                if self.text.strip():
                    return ("start", self.text.strip())
            elif len(self.text) < self.MAX_LEN and event.unicode.isprintable():
                self.text += event.unicode
        if self.start_btn.is_clicked(event) and self.text.strip():
            return ("start", self.text.strip())
        if self.back_btn.is_clicked(event):
            return ("back", "")
        return None

    def update(self, dt: float) -> None:
        self._t        += dt
        self._cursor_t += dt
        self.start_btn.update(dt)
        self.back_btn.update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(C_BG)
        _draw_stars(surface, self._t)

        title = _font(36, bold=True).render("ENTER YOUR NAME", True, C_ACCENT)
        surface.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 180))

        sub = _font(15).render("Your name will appear on the leaderboard", True, C_GRAY)
        surface.blit(sub, (SCREEN_W // 2 - sub.get_width() // 2, 230))

        pygame.draw.rect(surface, C_PANEL2, self._input_rect, border_radius=8)
        pygame.draw.rect(surface, C_ACCENT,  self._input_rect, 2, border_radius=8)

        cursor  = "|" if int(self._cursor_t * 2) % 2 == 0 else " "
        display = self.text + cursor
        inp_lbl = _font(24, bold=True).render(display, True, C_WHITE)
        surface.blit(inp_lbl, (self._input_rect.x + 12,
                                self._input_rect.centery - inp_lbl.get_height() // 2))

        self.start_btn.draw(surface)
        self.back_btn.draw(surface)


# ─── Settings Screen ──────────────────────────────────────────────────────────

class SettingsScreen:
    CAR_COLORS = ["blue", "red", "green", "yellow"]
    CAR_COLOR_DISPLAY = {
        "blue":   (0, 150, 255),
        "red":    (230, 50, 50),
        "green":  (50, 210, 80),
        "yellow": (240, 220, 0),
    }
    DIFFICULTIES = ["easy", "normal", "hard"]

    def __init__(self, settings: dict):
        self.settings = dict(settings)
        self._t       = 0.0

        bw, bh = 200, 44
        cx     = SCREEN_W // 2 - bw // 2

        self.sound_btn = Button(pygame.Rect(cx, 210, bw, bh), self._sound_label(), C_ACCENT)
        self.diff_btn  = Button(pygame.Rect(cx, 310, bw, bh), self._diff_label(),  C_GOLD, C_BG)
        self.color_btn = Button(pygame.Rect(cx, 410, bw, bh), self._color_label(), C_PANEL2, C_WHITE)
        self.save_btn  = Button(pygame.Rect(cx, 500, bw, bh), "SAVE",              C_GREEN)
        self.back_btn  = Button(pygame.Rect(cx, 558, bw, bh), "<< BACK",           C_GRAY, C_WHITE)

    def _sound_label(self) -> str:
        return "Sound: ON" if self.settings["sound"] else "Sound: OFF"

    def _diff_label(self) -> str:
        return f"Difficulty: {self.settings['difficulty'].upper()}"

    def _color_label(self) -> str:
        return f"Car Color: {self.settings['car_color'].capitalize()}"

    def handle_event(self, event: pygame.event.Event) -> str | None:
        if self.sound_btn.is_clicked(event):
            self.settings["sound"] = not self.settings["sound"]
            self.sound_btn.text    = self._sound_label()
        elif self.diff_btn.is_clicked(event):
            i = self.DIFFICULTIES.index(self.settings["difficulty"])
            self.settings["difficulty"] = self.DIFFICULTIES[(i + 1) % len(self.DIFFICULTIES)]
            self.diff_btn.text = self._diff_label()
        elif self.color_btn.is_clicked(event):
            i = self.CAR_COLORS.index(self.settings["car_color"])
            self.settings["car_color"] = self.CAR_COLORS[(i + 1) % len(self.CAR_COLORS)]
            self.color_btn.text  = self._color_label()
            self.color_btn.color = self.CAR_COLOR_DISPLAY[self.settings["car_color"]]
        elif self.save_btn.is_clicked(event):
            return "save"
        elif self.back_btn.is_clicked(event):
            return "back"
        return None

    def update(self, dt: float) -> None:
        self._t += dt
        for btn in [self.sound_btn, self.diff_btn, self.color_btn, self.save_btn, self.back_btn]:
            btn.update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(C_BG)
        _draw_stars(surface, self._t)

        title = _font(36, bold=True).render("SETTINGS", True, C_ACCENT)
        surface.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 120))

        labels = [
            (170, "Sound"),
            (270, "Difficulty"),
            (370, "Car Color"),
        ]
        for y, txt in labels:
            lbl = _font(14).render(txt.upper(), True, C_GRAY)
            surface.blit(lbl, (SCREEN_W // 2 - lbl.get_width() // 2, y))

        swatch_col = self.CAR_COLOR_DISPLAY.get(self.settings["car_color"], C_WHITE)
        pygame.draw.circle(surface, swatch_col, (SCREEN_W // 2 + 130, 432), 14)
        pygame.draw.circle(surface, C_WHITE,    (SCREEN_W // 2 + 130, 432), 14, 2)

        self.sound_btn.draw(surface)
        self.diff_btn.draw(surface)
        self.color_btn.draw(surface)
        self.save_btn.draw(surface)
        self.back_btn.draw(surface)


# ─── Leaderboard Screen ───────────────────────────────────────────────────────

class LeaderboardScreen:
    def __init__(self, entries: list):
        self.entries  = entries
        bw, bh        = 180, 44
        self.back_btn = Button(
            pygame.Rect(SCREEN_W // 2 - bw // 2, SCREEN_H - 74, bw, bh),
            "<< BACK", C_GRAY, C_WHITE
        )
        self._t = 0.0

    def handle_event(self, event: pygame.event.Event) -> str | None:
        if self.back_btn.is_clicked(event):
            return "back"
        return None

    def update(self, dt: float) -> None:
        self._t += dt
        self.back_btn.update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(C_BG)
        _draw_stars(surface, self._t)

        title = _font(34, bold=True).render("LEADERBOARD", True, C_GOLD)
        surface.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 34))

        hx   = [32, 60, 180, 310, 400]
        hdrs = ["#", "NAME", "SCORE", "DIST", "COINS"]
        for x, h in zip(hx, hdrs):
            lbl = _font(13, bold=True).render(h, True, C_ACCENT)
            surface.blit(lbl, (x, 92))

        pygame.draw.line(surface, C_ACCENT, (30, 110), (SCREEN_W - 30, 110), 1)

        row_colors = [C_GOLD, (200, 200, 200), (180, 120, 60)]

        for rank, entry in enumerate(self.entries, 1):
            y = 118 + (rank - 1) * 44

            row_bg = pygame.Surface((SCREEN_W - 30, 38), pygame.SRCALPHA)
            row_bg.fill((255, 255, 255, 8) if rank % 2 == 0 else (0, 0, 0, 0))
            surface.blit(row_bg, (15, y - 2))

            col = row_colors[rank - 1] if rank <= 3 else C_WHITE

            vals = [
                str(rank),
                entry.get("username", "?")[:12],
                str(entry.get("score", 0)),
                f"{entry.get('distance', 0)}m",
                str(entry.get("coins", 0)),
            ]
            for x, v in zip(hx, vals):
                lbl = _font(15, bold=(rank <= 3)).render(v, True, col)
                surface.blit(lbl, (x, y + 6))

        if not self.entries:
            empty = _font(18).render("No scores yet -- go race!", True, C_GRAY)
            surface.blit(empty, (SCREEN_W // 2 - empty.get_width() // 2, 250))

        self.back_btn.draw(surface)


# ─── Game Over Screen ─────────────────────────────────────────────────────────

class GameOverScreen:
    def __init__(self, score: int, distance: int, coins: int):
        self.score    = score
        self.distance = distance
        self.coins    = coins
        bw, bh        = 200, 48
        cx            = SCREEN_W // 2 - bw // 2
        self.retry_btn = Button(pygame.Rect(cx, 430, bw, bh), "RETRY",      C_GREEN)
        self.menu_btn  = Button(pygame.Rect(cx, 492, bw, bh), "MAIN MENU",  C_ACCENT)
        self._t        = 0.0

    def handle_event(self, event: pygame.event.Event) -> str | None:
        if self.retry_btn.is_clicked(event):
            return "retry"
        if self.menu_btn.is_clicked(event):
            return "menu"
        return None

    def update(self, dt: float) -> None:
        self._t += dt
        self.retry_btn.update(dt)
        self.menu_btn.update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(C_BG)
        _draw_stars(surface, self._t)

        crash_f = _font(62, bold=True)
        crash   = crash_f.render("CRASH!", True, C_RED)
        shake   = int(math.sin(self._t * 18) * (3 if self._t < 1 else 0))
        surface.blit(crash, (SCREEN_W // 2 - crash.get_width() // 2 + shake, 130))

        sub = _font(18).render("Your run has ended", True, C_GRAY)
        surface.blit(sub, (SCREEN_W // 2 - sub.get_width() // 2, 208))

        panel = pygame.Surface((300, 140), pygame.SRCALPHA)
        panel.fill((20, 24, 50, 200))
        px = SCREEN_W // 2 - 150
        surface.blit(panel, (px, 245))
        pygame.draw.rect(surface, C_ACCENT, pygame.Rect(px, 245, 300, 140), 1, border_radius=6)

        stats = [
            ("Score",    str(self.score),    C_GOLD),
            ("Distance", f"{self.distance}m", C_ACCENT),
            ("Coins",    str(self.coins),     C_GREEN),
        ]
        for i, (label, val, col) in enumerate(stats):
            y = 262 + i * 38
            lbl     = _font(15).render(label, True, C_GRAY)
            val_lbl = _font(22, bold=True).render(val, True, col)
            surface.blit(lbl,     (px + 20, y))
            surface.blit(val_lbl, (px + 300 - val_lbl.get_width() - 20, y))

        self.retry_btn.draw(surface)
        self.menu_btn.draw(surface)