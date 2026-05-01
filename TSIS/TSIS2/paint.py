"""
paint.py — Extended Paint Application (TSIS 2)
=================================================
New tools (TSIS 2):  Pencil · Line · Fill · Text · Brush sizes · Save
Base tools (P10/11): Rectangle · Circle · Eraser · Color picker
                     Square · Right-triangle · Equilateral triangle · Rhombus

Controls
--------
  Tools (keyboard)
    P  → Pencil (freehand)
    L  → Straight line
    F  → Flood fill
    T  → Text
    R  → Rectangle        C  → Circle
    S  → Square           E  → Eraser
    I  → Colour picker    G  → Right triangle
    H  → Equilateral triangle
    M  → Rhombus

  Brush size
    1  → Small  (2 px)
    2  → Medium (5 px)
    3  → Large  (10 px)

  File
    Ctrl+S  → Save canvas as timestamped PNG

  Text tool
    Enter   → Commit text
    Escape  → Cancel text
"""

import pygame
import sys
import math
import datetime
import os

from tools import PencilTool, LineTool, FillTool, TextTool

# ──────────────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────────────

WINDOW_TITLE = "Paint — TSIS 2"
CANVAS_W, CANVAS_H = 1000, 680
TOOLBAR_H = 60        # top toolbar
PALETTE_H = 50        # bottom colour palette
WINDOW_W  = CANVAS_W
WINDOW_H  = CANVAS_H + TOOLBAR_H + PALETTE_H

FPS = 60

# Colour palette
PALETTE_COLORS = [
    (0,   0,   0),    (255, 255, 255), (128, 128, 128), (192, 192, 192),
    (255,   0,   0),  (128,   0,   0), (255, 128,   0), (128,  64,   0),
    (255, 255,   0),  (128, 128,   0), (  0, 255,   0), (  0, 128,   0),
    (  0, 255, 255),  (  0, 128, 128), (  0,   0, 255), (  0,   0, 128),
    (255,   0, 255),  (128,   0, 128), (255, 128, 128), (128, 255, 128),
]

# Brush sizes
BRUSH_SIZES = {1: 2, 2: 5, 3: 10}

# UI colours
UI_BG      = (40,  40,  45)
UI_BORDER  = (70,  70,  80)
UI_ACTIVE  = (80, 140, 220)
UI_TEXT    = (220, 220, 220)
CANVAS_BG  = (255, 255, 255)

# Tool names (base tools treated as dumb stubs here; logic stays from P10/P11)
ALL_TOOLS = [
    "pencil", "line", "fill", "text",
    "rect",   "circle", "eraser", "picker",
    "square", "rtriangle", "etriangle", "rhombus",
]

TOOL_LABELS = {
    "pencil":    "Pencil  [P]",
    "line":      "Line    [L]",
    "fill":      "Fill    [F]",
    "text":      "Text    [T]",
    "rect":      "Rect    [R]",
    "circle":    "Circle  [C]",
    "eraser":    "Eraser  [E]",
    "picker":    "Picker  [I]",
    "square":    "Square  [S]",
    "rtriangle": "R-Tri   [G]",
    "etriangle": "E-Tri   [H]",
    "rhombus":   "Rhombus [M]",
}

KEY_TO_TOOL = {
    pygame.K_p: "pencil",
    pygame.K_l: "line",
    pygame.K_f: "fill",
    pygame.K_t: "text",
    pygame.K_r: "rect",
    pygame.K_c: "circle",
    pygame.K_e: "eraser",
    pygame.K_i: "picker",
    pygame.K_s: "square",
    pygame.K_g: "rtriangle",
    pygame.K_h: "etriangle",
    pygame.K_m: "rhombus",
}

# ──────────────────────────────────────────────────────────────────────────────
# Base-tool shape helpers  (P10 / P11 functionality)
# ──────────────────────────────────────────────────────────────────────────────

def draw_rect(surface, color, p1, p2, size):
    x, y = min(p1[0], p2[0]), min(p1[1], p2[1])
    w, h = abs(p2[0]-p1[0]), abs(p2[1]-p1[1])
    pygame.draw.rect(surface, color, (x, y, w, h), size)

def draw_circle(surface, color, p1, p2, size):
    cx = (p1[0] + p2[0]) // 2
    cy = (p1[1] + p2[1]) // 2
    rx = abs(p2[0] - p1[0]) // 2
    ry = abs(p2[1] - p1[1]) // 2
    r  = min(rx, ry)
    if r > 0:
        pygame.draw.circle(surface, color, (cx, cy), r, size)

def draw_square(surface, color, p1, p2, size):
    side = min(abs(p2[0]-p1[0]), abs(p2[1]-p1[1]))
    x = p1[0] if p2[0] >= p1[0] else p1[0] - side
    y = p1[1] if p2[1] >= p1[1] else p1[1] - side
    pygame.draw.rect(surface, color, (x, y, side, side), size)

def draw_right_triangle(surface, color, p1, p2, size):
    pts = [p1, (p1[0], p2[1]), p2]
    pygame.draw.polygon(surface, color, pts, size)

def draw_equilateral_triangle(surface, color, p1, p2, size):
    base = abs(p2[0] - p1[0])
    h    = int(base * math.sqrt(3) / 2)
    bx   = min(p1[0], p2[0])
    by   = max(p1[1], p2[1])
    pts  = [(bx, by), (bx + base, by), (bx + base // 2, by - h)]
    pygame.draw.polygon(surface, color, pts, size)

def draw_rhombus(surface, color, p1, p2, size):
    cx = (p1[0] + p2[0]) // 2
    cy = (p1[1] + p2[1]) // 2
    pts = [
        (cx, p1[1]),
        (p2[0], cy),
        (cx, p2[1]),
        (p1[0], cy),
    ]
    pygame.draw.polygon(surface, color, pts, size)

# ──────────────────────────────────────────────────────────────────────────────
# Toolbar / UI helpers
# ──────────────────────────────────────────────────────────────────────────────

def draw_toolbar(surface, font_sm, font_xs, active_tool, brush_key, draw_color):
    """Render the top toolbar: tool name, brush size buttons, current colour."""
    bar = pygame.Rect(0, 0, WINDOW_W, TOOLBAR_H)
    pygame.draw.rect(surface, UI_BG, bar)
    pygame.draw.line(surface, UI_BORDER, (0, TOOLBAR_H-1), (WINDOW_W, TOOLBAR_H-1))

    # Active tool label
    label = font_sm.render(f"Tool: {TOOL_LABELS.get(active_tool, active_tool)}", True, UI_TEXT)
    surface.blit(label, (12, 18))

    # Brush size buttons
    for key, px in BRUSH_SIZES.items():
        bx = 340 + (key - 1) * 70
        rect = pygame.Rect(bx, 12, 60, 36)
        col  = UI_ACTIVE if key == brush_key else UI_BORDER
        pygame.draw.rect(surface, col, rect, border_radius=6)
        txt  = font_xs.render(f"[{key}] {px}px", True, UI_TEXT)
        surface.blit(txt, (bx + 5, 20))

    # Current colour swatch
    swatch = pygame.Rect(WINDOW_W - 90, 10, 40, 40)
    pygame.draw.rect(surface, draw_color, swatch)
    pygame.draw.rect(surface, UI_TEXT,   swatch, 2)
    cl = font_xs.render("Color", True, UI_TEXT)
    surface.blit(cl, (WINDOW_W - 45, 24))


def draw_palette(surface, font_xs, draw_color, toolbar_h, canvas_h):
    """Render the colour palette strip at the bottom."""
    y0 = toolbar_h + canvas_h
    pal_rect = pygame.Rect(0, y0, WINDOW_W, PALETTE_H)
    pygame.draw.rect(surface, UI_BG, pal_rect)
    pygame.draw.line(surface, UI_BORDER, (0, y0), (WINDOW_W, y0))

    swatch_size = 36
    pad = 6
    for i, col in enumerate(PALETTE_COLORS):
        rx = pad + i * (swatch_size + pad)
        ry = y0 + (PALETTE_H - swatch_size) // 2
        r  = pygame.Rect(rx, ry, swatch_size, swatch_size)
        pygame.draw.rect(surface, col, r)
        if col == draw_color:
            pygame.draw.rect(surface, (255, 255, 0), r, 3)
        else:
            pygame.draw.rect(surface, UI_BORDER, r, 1)

    # Hint text
    hint = font_xs.render("Ctrl+S = Save   |   1/2/3 = Brush size", True, UI_BORDER)
    surface.blit(hint, (WINDOW_W - hint.get_width() - 10, y0 + 16))


def point_on_canvas(pos, toolbar_h):
    """Return True if pos is within the canvas area."""
    x, y = pos
    return 0 <= x < CANVAS_W and toolbar_h <= y < TOOLBAR_H + CANVAS_H


def canvas_pos(pos, toolbar_h):
    """Translate window pos → canvas-local pos."""
    return (pos[0], pos[1] - toolbar_h)


def palette_click(pos, toolbar_h, canvas_h):
    """Return palette colour under pos, or None."""
    px, py = pos
    y0 = toolbar_h + canvas_h
    if py < y0 or py >= y0 + PALETTE_H:
        return None
    swatch_size = 36
    pad = 6
    for i, col in enumerate(PALETTE_COLORS):
        rx = pad + i * (swatch_size + pad)
        if rx <= px <= rx + swatch_size:
            return col
    return None


# ──────────────────────────────────────────────────────────────────────────────
# Save helper
# ──────────────────────────────────────────────────────────────────────────────

def save_canvas(canvas):
    """Save the canvas surface as a timestamped PNG."""
    ts       = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"canvas_{ts}.png"
    pygame.image.save(canvas, filename)
    print(f"[Saved] {filename}")
    return filename


# ──────────────────────────────────────────────────────────────────────────────
# Main application class
# ──────────────────────────────────────────────────────────────────────────────

class PaintApp:
    def __init__(self):
        pygame.init()
        pygame.key.set_repeat(0)   # no key repeat for tool keys

        self.screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
        pygame.display.set_caption(WINDOW_TITLE)
        self.clock  = pygame.time.Clock()

        # Fonts
        self.font_sm = pygame.font.SysFont("consolas,monospace", 15)
        self.font_xs = pygame.font.SysFont("consolas,monospace", 13)

        # Canvas: a persistent surface we draw onto
        self.canvas  = pygame.Surface((CANVAS_W, CANVAS_H))
        self.canvas.fill(CANVAS_BG)

        # Overlay for live previews (cleared every frame)
        self.overlay = pygame.Surface((CANVAS_W, CANVAS_H), pygame.SRCALPHA)

        # Application state
        self.active_tool = "pencil"
        self.draw_color  = (0, 0, 0)
        self.brush_key   = 1             # 1 / 2 / 3
        self.eraser_color = CANVAS_BG

        # Instantiate TSIS-2 tools
        self.pencil = PencilTool()
        self.line   = LineTool()
        self.fill   = FillTool()
        self.text   = TextTool()

        # State for base shape tools (click-drag)
        self.shape_start = None     # mouse-down position for shape tools
        self.shape_dragging = False

        # Status message (e.g. save confirmation)
        self.status_msg  = ""
        self.status_timer = 0

    # ── property shortcuts ──────────────────────────────────────────────────

    @property
    def brush_size(self):
        return BRUSH_SIZES[self.brush_key]

    # ── event dispatch ──────────────────────────────────────────────────────

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # ── Global keyboard shortcuts ──────────────────────────────────
            if event.type == pygame.KEYDOWN:
                # Ctrl+S → save
                mods = pygame.key.get_mods()
                if event.key == pygame.K_s and (mods & pygame.KMOD_CTRL):
                    fname = save_canvas(self.canvas)
                    self.status_msg   = f"Saved: {fname}"
                    self.status_timer = FPS * 3
                    continue

                # Brush size keys 1 / 2 / 3
                if event.key == pygame.K_1:
                    self.brush_key = 1; continue
                if event.key == pygame.K_2:
                    self.brush_key = 2; continue
                if event.key == pygame.K_3:
                    self.brush_key = 3; continue

                # Tool switch keys  — but NOT when text tool is typing
                if not self.text.typing:
                    if event.key in KEY_TO_TOOL:
                        new_tool = KEY_TO_TOOL[event.key]
                        # K_s mapped to "square" — only when NOT Ctrl
                        if event.key == pygame.K_s and (mods & pygame.KMOD_CTRL):
                            pass  # handled above
                        else:
                            self.active_tool = new_tool
                        continue

            # ── Translate mouse events to canvas-local coords ──────────────
            if hasattr(event, "pos"):
                raw = event.pos
                # Palette click
                pal_col = palette_click(raw, TOOLBAR_H, CANVAS_H)
                if pal_col and event.type == pygame.MOUSEBUTTONDOWN:
                    self.draw_color = pal_col
                    continue

                if not point_on_canvas(raw, TOOLBAR_H):
                    continue   # click in toolbar → ignore canvas tools

                # Translate to canvas coordinates
                cx, cy = canvas_pos(raw, TOOLBAR_H)
                # Rebuild event-like namedtuple with translated pos
                event = _retarget_event(event, (cx, cy))

            # ── Dispatch to active tool ────────────────────────────────────
            tool  = self.active_tool
            color = self.draw_color
            size  = self.brush_size

            # ── TSIS-2 tools ──
            if tool == "pencil":
                self.pencil.handle_event(event, self.canvas, color, size)

            elif tool == "line":
                self.line.handle_event(event, self.canvas, color, size)

            elif tool == "fill":
                self.fill.handle_event(event, self.canvas, color, size)

            elif tool == "text":
                self.text.handle_event(event, self.canvas, color, size)

            # ── Base tools (P10 / P11) ──
            elif tool == "eraser":
                self._eraser(event)

            elif tool == "picker":
                self._picker(event)

            elif tool in ("rect", "circle", "square", "rtriangle", "etriangle", "rhombus"):
                self._shape_tool(event, tool, color, size)

    def _eraser(self, event):
        """Simple eraser — paints white along the cursor."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._eraser_drawing = True
            self._eraser_last = event.pos
        elif event.type == pygame.MOUSEMOTION and getattr(self, "_eraser_drawing", False):
            sz = self.brush_size * 4   # eraser is bigger
            pygame.draw.line(self.canvas, CANVAS_BG, self._eraser_last, event.pos, sz)
            pygame.draw.circle(self.canvas, CANVAS_BG, event.pos, sz // 2)
            self._eraser_last = event.pos
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._eraser_drawing = False

    def _picker(self, event):
        """Pick the colour under the cursor on mouse-down."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            x, y = event.pos
            if 0 <= x < CANVAS_W and 0 <= y < CANVAS_H:
                self.draw_color = self.canvas.get_at((x, y))[:3]

    def _shape_tool(self, event, tool, color, size):
        """Shared drag-to-draw handler for all shape tools."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.shape_start    = event.pos
            self.shape_dragging = True

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.shape_dragging:
            if self.shape_start:
                self._commit_shape(tool, self.canvas, color, size,
                                   self.shape_start, event.pos)
            self.shape_start    = None
            self.shape_dragging = False

        elif event.type == pygame.MOUSEMOTION:
            pass  # preview drawn in draw()

    def _commit_shape(self, tool, surface, color, size, p1, p2):
        dispatch = {
            "rect":      draw_rect,
            "circle":    draw_circle,
            "square":    draw_square,
            "rtriangle": draw_right_triangle,
            "etriangle": draw_equilateral_triangle,
            "rhombus":   draw_rhombus,
        }
        if tool in dispatch:
            dispatch[tool](surface, color, p1, p2, size)

    # ── drawing / rendering ──────────────────────────────────────────────────

    def draw(self):
        self.screen.fill(UI_BG)

        # 1. Blit persistent canvas
        self.screen.blit(self.canvas, (0, TOOLBAR_H))

        # 2. Build overlay (preview) — cleared every frame
        self.overlay.fill((0, 0, 0, 0))

        tool  = self.active_tool
        color = self.draw_color
        size  = self.brush_size

        if tool == "line":
            self.line.draw_preview(self.overlay, color, size)
        elif tool == "text":
            self.text.draw_preview(self.overlay, color, size)
        elif tool in ("rect", "circle", "square", "rtriangle", "etriangle", "rhombus"):
            if self.shape_dragging and self.shape_start:
                mp = pygame.mouse.get_pos()
                cp = canvas_pos(mp, TOOLBAR_H)
                self._commit_shape(tool, self.overlay, color, size,
                                   self.shape_start, cp)

        self.screen.blit(self.overlay, (0, TOOLBAR_H))

        # 3. UI chrome
        draw_toolbar(self.screen, self.font_sm, self.font_xs,
                     self.active_tool, self.brush_key, self.draw_color)
        draw_palette(self.screen, self.font_xs, self.draw_color,
                     TOOLBAR_H, CANVAS_H)

        # 4. Status message
        if self.status_timer > 0:
            msg  = self.font_sm.render(self.status_msg, True, (80, 220, 120))
            self.screen.blit(msg, (550, 20))
            self.status_timer -= 1

        pygame.display.flip()

    # ── main loop ────────────────────────────────────────────────────────────

    def run(self):
        while True:
            self.handle_events()
            self.draw()
            self.clock.tick(FPS)


# ──────────────────────────────────────────────────────────────────────────────
# Utility: rebuild event with a new pos without modifying the original
# ──────────────────────────────────────────────────────────────────────────────

class _FakeEvent:
    """Lightweight event wrapper that overrides pos."""
    __slots__ = ("type", "button", "pos", "key", "text", "mod", "unicode")
    def __init__(self, src, new_pos):
        self.type    = src.type
        self.pos     = new_pos
        self.button  = getattr(src, "button",  1)
        self.key     = getattr(src, "key",     0)
        self.text    = getattr(src, "text",    "")
        self.mod     = getattr(src, "mod",     0)
        self.unicode = getattr(src, "unicode", "")

def _retarget_event(event, new_pos):
    return _FakeEvent(event, new_pos)


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = PaintApp()
    app.run()