"""
tools.py — Drawing tool implementations for the Paint application.
Each tool is a class with handle_event() and draw() methods.
"""

import pygame
import math
from collections import deque


# ---------------------------------------------------------------------------
# Pencil (Freehand) Tool
# ---------------------------------------------------------------------------

class PencilTool:
    """Draws continuously between consecutive mouse positions while held."""

    def __init__(self):
        self.drawing = False
        self.last_pos = None

    def handle_event(self, event, canvas, color, size):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.drawing = True
            self.last_pos = event.pos
            # Draw a single dot on first click
            pygame.draw.circle(canvas, color, event.pos, size // 2)

        elif event.type == pygame.MOUSEMOTION and self.drawing:
            if self.last_pos:
                pygame.draw.line(canvas, color, self.last_pos, event.pos, size)
                # Draw circle caps so the line is smooth at curves
                pygame.draw.circle(canvas, color, event.pos, size // 2)
            self.last_pos = event.pos

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.drawing = False
            self.last_pos = None

    def draw_preview(self, surface, color, size):
        """Pencil has no separate overlay preview."""
        pass


# ---------------------------------------------------------------------------
# Straight Line Tool
# ---------------------------------------------------------------------------

class LineTool:
    """Click to set start, drag to preview, release to finalise."""

    def __init__(self):
        self.active = False
        self.start_pos = None
        self.current_pos = None

    def handle_event(self, event, canvas, color, size):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.active = True
            self.start_pos = event.pos
            self.current_pos = event.pos

        elif event.type == pygame.MOUSEMOTION and self.active:
            self.current_pos = event.pos  # live preview updated each frame

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.active:
            # Commit the line to the canvas
            if self.start_pos and self.current_pos:
                pygame.draw.line(canvas, color, self.start_pos, self.current_pos, size)
            self.active = False
            self.start_pos = None
            self.current_pos = None

    def draw_preview(self, surface, color, size):
        """Render the live rubber-band line on the overlay surface."""
        if self.active and self.start_pos and self.current_pos:
            pygame.draw.line(surface, color, self.start_pos, self.current_pos, size)


# ---------------------------------------------------------------------------
# Flood Fill Tool
# ---------------------------------------------------------------------------

class FillTool:
    """
    BFS flood fill using Surface.get_at() / set_at().
    Fills all pixels of the target color connected to the clicked pixel.
    """

    def __init__(self):
        self.active = False  # single-click tool, no drag state needed

    def handle_event(self, event, canvas, color, size):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._flood_fill(canvas, event.pos, color)

    def _flood_fill(self, surface, start, fill_color):
        """Iterative BFS flood fill — avoids Python recursion limit."""
        sw, sh = surface.get_size()
        x0, y0 = start

        # Guard: click outside canvas
        if not (0 <= x0 < sw and 0 <= y0 < sh):
            return

        target_color = surface.get_at((x0, y0))[:3]  # ignore alpha
        fill_rgb = fill_color[:3] if len(fill_color) > 3 else fill_color

        # Nothing to fill if already the same color
        if target_color == fill_rgb:
            return

        # Lock the surface once for fast pixel access
        surface.lock()
        try:
            queue = deque()
            queue.append((x0, y0))
            visited = set()
            visited.add((x0, y0))

            while queue:
                x, y = queue.popleft()
                surface.set_at((x, y), fill_color)

                for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nx, ny = x + dx, y + dy
                    if (0 <= nx < sw and 0 <= ny < sh
                            and (nx, ny) not in visited):
                        if surface.get_at((nx, ny))[:3] == target_color:
                            visited.add((nx, ny))
                            queue.append((nx, ny))
        finally:
            surface.unlock()

    def draw_preview(self, surface, color, size):
        pass  # fill is instant, no drag preview


# ---------------------------------------------------------------------------
# Text Tool
# ---------------------------------------------------------------------------

class TextTool:
    """
    Click to place cursor → type characters → Enter to commit → Escape to cancel.
    """

    def __init__(self):
        self.active = False        # whether placement mode is on
        self.typing = False        # text entry in progress
        self.position = None       # where the text will be drawn
        self.text_buffer = ""      # characters typed so far
        self.font = None           # loaded lazily

    def _get_font(self, size):
        """Return a SysFont sized proportionally to the brush size."""
        font_size = max(16, size * 3)
        return pygame.font.SysFont("consolas,monospace", font_size)

    def handle_event(self, event, canvas, color, size):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if not self.typing:
                # First click: set insertion point
                self.position = event.pos
                self.text_buffer = ""
                self.typing = True
                self.font = self._get_font(size)
                pygame.key.start_text_input()
            else:
                # Second click elsewhere: commit and move
                self._commit(canvas, color)
                self.position = event.pos
                self.text_buffer = ""
                self.font = self._get_font(size)

        elif event.type == pygame.KEYDOWN and self.typing:
            if event.key == pygame.K_RETURN:
                self._commit(canvas, color)
            elif event.key == pygame.K_ESCAPE:
                self._cancel()
            elif event.key == pygame.K_BACKSPACE:
                self.text_buffer = self.text_buffer[:-1]

        elif event.type == pygame.TEXTINPUT and self.typing:
            self.text_buffer += event.text

    def _commit(self, canvas, color):
        """Render text permanently onto the canvas."""
        if self.font and self.text_buffer and self.position:
            surf = self.font.render(self.text_buffer, True, color)
            canvas.blit(surf, self.position)
        self._cancel()

    def _cancel(self):
        self.typing = False
        self.text_buffer = ""
        self.position = None
        pygame.key.stop_text_input()

    def draw_preview(self, surface, color, size):
        """Show the in-progress text + blinking cursor on the overlay."""
        if self.typing and self.position and self.font:
            preview = self.text_buffer + "|"
            surf = self.font.render(preview, True, color)
            surface.blit(surf, self.position)