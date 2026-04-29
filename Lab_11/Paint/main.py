'''
Paint — расширенная версия (Practice задание)
Добавлено поверх оригинала:
  1. Рисование квадрата (Square)
  2. Рисование прямоугольного треугольника (Right Triangle)
  3. Рисование равностороннего треугольника (Equilateral Triangle)
  4. Рисование ромба (Rhombus)
  5. Комментарии к коду

Управление фигурами:
  - Выбери инструмент кнопкой в панели Tools
  - Зажми ЛКМ на холсте → тяни → отпусти → фигура нарисована
  - Инструмент "Pen" — оригинальный режим рисования от руки
'''

import pygame
import math

pygame.init()

FPS = 120
FramePerSec = pygame.time.Clock()

# ── Размер окна ───────────────────────────────────────────────────────────────
WIN_X = 600       # увеличили по ширине: 400 холст + 200 панель
WIN_Y = 600

CANVAS_W = 400    # ширина области рисования
PANEL_X  = 400    # x-начало боковой панели

win = pygame.display.set_mode((WIN_X, WIN_Y))
pygame.display.set_caption('Paint')

# ── Доступные инструменты ─────────────────────────────────────────────────────
# Каждый инструмент имеет:
#   key    — внутреннее название
#   label  — текст на кнопке
TOOLS = [
    {'key': 'pen',      'label': 'Pen'},
    {'key': 'square',   'label': 'Square'},
    {'key': 'rtri',     'label': 'R.Tri'},    # прямоугольный треугольник
    {'key': 'etri',     'label': 'E.Tri'},    # равносторонний треугольник
    {'key': 'rhombus',  'label': 'Rhombus'},
    {'key': 'eraser',   'label': 'Eraser'},
]

# ── Цветовая палитра ──────────────────────────────────────────────────────────
PALETTE = [
    (0,   0,   0),      # чёрный
    (255, 0,   0),      # красный
    (0,   0,   255),    # синий
    (0,   200, 0),      # зелёный
    (255, 192, 0),      # оранжевый
    (255, 255, 0),      # жёлтый
    (112, 48,  160),    # фиолетовый
    (255, 255, 255),    # белый (ластик-цвет)
]


# ── Класс состояния рисовалки ─────────────────────────────────────────────────
class DrawingState:
    def __init__(self):
        self.color      = (0, 0, 0)    # текущий цвет
        self.tool       = 'pen'        # текущий инструмент
        self.pen_size   = 6            # радиус пера / ластика
        self.dragging   = False        # зажата ли ЛКМ
        self.start_pos  = None         # точка начала drag'а

        # Отдельная поверхность-буфер: на ней живёт «постоянный» рисунок.
        # Поверх неё мы рисуем предпросмотр текущей фигуры во время drag'а.
        self.canvas = pygame.Surface((CANVAS_W, WIN_Y))
        self.canvas.fill((255, 255, 255))

    # ── Вспомогательные геометрические функции ────────────────────────────────

    def _square_points(self, x0, y0, x1, y1):
        """
        Возвращает pygame.Rect для квадрата.
        Сторона квадрата = min(|dx|, |dy|), направление сохраняется.
        """
        dx = x1 - x0
        dy = y1 - y0
        side = min(abs(dx), abs(dy))
        # Сохраняем знак (направление от стартовой точки)
        sx = side if dx >= 0 else -side
        sy = side if dy >= 0 else -side
        return pygame.Rect(min(x0, x0 + sx), min(y0, y0 + sy), side, side)

    def _right_triangle_points(self, x0, y0, x1, y1):
        """
        Прямоугольный треугольник с прямым углом в точке (x0, y1).
        Вершины: (x0,y0) — верхний угол, (x1,y1) — правый, (x0,y1) — прямой угол.
        """
        return [(x0, y0), (x1, y1), (x0, y1)]

    def _equilateral_triangle_points(self, x0, y0, x1, y1):
        """
        Равносторонний треугольник.
        Основание = отрезок (x0,y1)–(x1,y1), вершина — над центром основания.
        Высота равностороннего треугольника = сторона * sqrt(3)/2.
        """
        cx    = (x0 + x1) / 2            # центр основания по X
        base  = abs(x1 - x0)
        h     = base * math.sqrt(3) / 2  # высота
        # Вершина поднимается вверх от нижней стороны
        top_y = y1 - h if y0 <= y1 else y1 + h
        return [(x0, y1), (x1, y1), (cx, top_y)]

    def _rhombus_points(self, x0, y0, x1, y1):
        """
        Ромб (diamond): вписан в ограничивающий прямоугольник (x0,y0)–(x1,y1).
        4 вершины — средины сторон прямоугольника.
        """
        cx = (x0 + x1) / 2
        cy = (y0 + y1) / 2
        return [(cx, y0), (x1, cy), (cx, y1), (x0, cy)]

    # ── Отрисовка одной фигуры на произвольную поверхность ───────────────────

    def draw_shape(self, surface, tool, color, size, start, end):
        """
        Рисует выбранный инструмент (tool) на surface.
        start, end — пиксельные координаты начала и конца drag'а.
        """
        x0, y0 = start
        x1, y1 = end

        if tool == 'pen':
            pygame.draw.circle(surface, color, end, size)

        elif tool == 'eraser':
            # Ластик рисует белым кружком большего размера
            pygame.draw.circle(surface, (255, 255, 255), end, size * 2)

        elif tool == 'square':
            rect = self._square_points(x0, y0, x1, y1)
            pygame.draw.rect(surface, color, rect, 2)

        elif tool == 'rtri':
            pts = self._right_triangle_points(x0, y0, x1, y1)
            pygame.draw.polygon(surface, color, pts, 2)

        elif tool == 'etri':
            pts = self._equilateral_triangle_points(x0, y0, x1, y1)
            pygame.draw.polygon(surface, color, pts, 2)

        elif tool == 'rhombus':
            pts = self._rhombus_points(x0, y0, x1, y1)
            pygame.draw.polygon(surface, color, pts, 2)

    # ── Обработка мыши ────────────────────────────────────────────────────────

    def handle_mouse(self, event):
        """
        Обрабатывает события мыши: нажатие, движение, отпускание.
        Рисование происходит только внутри области холста (x < CANVAS_W).
        """
        pos = pygame.mouse.get_pos()
        on_canvas = pos[0] < CANVAS_W and pos[1] > 25  # 25 — высота заголовка

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if on_canvas:
                self.dragging  = True
                self.start_pos = pos

        elif event.type == pygame.MOUSEMOTION and self.dragging:
            if on_canvas:
                # Перо и ластик работают непрерывно во время движения
                if self.tool in ('pen', 'eraser'):
                    self.draw_shape(self.canvas, self.tool,
                                    self.color, self.pen_size,
                                    self.start_pos, pos)

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.dragging and self.start_pos:
                end = pos
                # Фигуры фиксируются на постоянном холсте при отпускании кнопки
                if self.tool not in ('pen', 'eraser'):
                    self.draw_shape(self.canvas, self.tool,
                                    self.color, self.pen_size,
                                    self.start_pos, end)
            self.dragging  = False
            self.start_pos = None


# ── Класс кнопки панели ───────────────────────────────────────────────────────
class Button:
    def __init__(self, x, y, w, h, bg, label='', label_color=(0, 0, 0),
                 action=None, outline=0):
        self.rect        = pygame.Rect(x, y, w, h)
        self.bg          = bg          # цвет фона кнопки
        self.label       = label
        self.label_color = label_color
        self.action      = action      # произвольный объект (строка, число, цвет)
        self.outline     = outline
        self.active      = False       # подсветка активной кнопки

    def draw(self, surface, font):
        # Подсвечиваем активную кнопку белой рамкой
        border_color = (255, 255, 255) if self.active else (0, 0, 0)
        pygame.draw.rect(surface, self.bg, self.rect)
        pygame.draw.rect(surface, border_color, self.rect, 2)

        if self.label:
            text = font.render(self.label, True, self.label_color)
            tr   = text.get_rect(center=self.rect.center)
            surface.blit(text, tr)

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)


# ── Построение панели инструментов ────────────────────────────────────────────

def build_panel():
    """
    Создаёт и возвращает списки кнопок:
      color_buttons — цветовая палитра
      tool_buttons  — инструменты (pen, square, …)
      util_buttons  — утилиты (clear, size +/-)
    """
    font_small = pygame.font.SysFont('comicsans', 18)
    color_buttons = []
    tool_buttons  = []
    util_buttons  = []

    # Цвета: сетка 2×N начиная с y=30
    cols = 2
    btn_size = 44
    gap = 4
    for i, color in enumerate(PALETTE):
        col = i % cols
        row = i // cols
        x = PANEL_X + 6 + col * (btn_size + gap)
        y = 30 + row * (btn_size + gap)
        outline = 1 if color == (255, 255, 255) else 0
        lbl_color = (0, 0, 0) if color == (255, 255, 255) else color
        b = Button(x, y, btn_size, btn_size, color, outline=outline,
                   label_color=lbl_color, action=('color', color))
        color_buttons.append(b)

    # Инструменты: столбик под палитрой
    tool_y_start = 30 + (len(PALETTE) // cols) * (btn_size + gap) + 10
    for i, tool in enumerate(TOOLS):
        y = tool_y_start + i * 38
        b = Button(PANEL_X + 6, y, 188, 34,
                   (201, 201, 201), label=tool['label'],
                   action=('tool', tool['key']))
        tool_buttons.append(b)

    # Утилиты: Clear, –, +
    util_y = tool_y_start + len(TOOLS) * 38 + 10
    util_buttons.append(
        Button(PANEL_X + 6, util_y, 188, 34, (201, 201, 201),
               label='Clear', action='clear'))
    util_buttons.append(
        Button(PANEL_X + 6, util_y + 42, 88, 34, (201, 201, 201),
               label='-', action='size_down'))
    util_buttons.append(
        Button(PANEL_X + 106, util_y + 42, 88, 34, (201, 201, 201),
               label='+', action='size_up'))

    return color_buttons, tool_buttons, util_buttons


# ── Отрисовка заголовка ───────────────────────────────────────────────────────
def draw_header(surface, ds, font):
    pygame.draw.rect(surface, (175, 171, 171), (0, 0, WIN_X, 25))
    pygame.draw.rect(surface, (0, 0, 0), (0, 0, CANVAS_W, 25), 2)
    pygame.draw.rect(surface, (0, 0, 0), (CANVAS_W, 0, WIN_X - CANVAS_W, 25), 2)

    t1 = font.render('Пэйнт', True, (0, 0, 0))
    surface.blit(t1, t1.get_rect(center=(CANVAS_W // 2, 13)))

    t2 = font.render(f'Tools  size:{ds.pen_size}', True, (0, 0, 0))
    surface.blit(t2, t2.get_rect(center=(PANEL_X + (WIN_X - PANEL_X) // 2, 13)))


# ── Предпросмотр фигуры во время drag'а ──────────────────────────────────────
def draw_preview(surface, ds):
    """
    Пока пользователь держит кнопку мыши и тянет — показывает
    контур будущей фигуры поверх холста (не записывая в canvas).
    Для пера/ластика предпросмотр не нужен.
    """
    if not ds.dragging or ds.start_pos is None:
        return
    if ds.tool in ('pen', 'eraser'):
        return

    end = pygame.mouse.get_pos()
    # Временная поверхность для предпросмотра с прозрачностью
    preview = pygame.Surface((CANVAS_W, WIN_Y), pygame.SRCALPHA)
    # Рисуем контур полупрозрачным цветом
    r, g, b = ds.color
    ds.draw_shape(preview, ds.tool, (r, g, b, 160), ds.pen_size,
                  ds.start_pos, end)
    surface.blit(preview, (0, 0))


# ── Главный цикл ─────────────────────────────────────────────────────────────
def main():
    ds = DrawingState()
    font      = pygame.font.SysFont('comicsans', 22)
    font_small = pygame.font.SysFont('comicsans', 17)

    color_buttons, tool_buttons, util_buttons = build_panel()

    # Помечаем первый инструмент (pen) как активный
    tool_buttons[0].active = True

    run = True
    while run:
        keys = pygame.key.get_pressed()

        for event in pygame.event.get():
            if event.type == pygame.QUIT or keys[pygame.K_ESCAPE]:
                run = False

            # Обработка движения и кликов мыши
            ds.handle_mouse(event)

            # Клики по кнопкам панели (только MOUSEBUTTONDOWN)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos

                # Цветовые кнопки
                for btn in color_buttons:
                    if btn.is_clicked(pos):
                        ds.color = btn.action[1]

                # Кнопки инструментов
                for btn in tool_buttons:
                    if btn.is_clicked(pos):
                        ds.tool = btn.action[1]
                        # Сбрасываем подсветку и ставим на выбранную
                        for b in tool_buttons:
                            b.active = False
                        btn.active = True

                # Утилиты
                for btn in util_buttons:
                    if btn.is_clicked(pos):
                        if btn.action == 'clear':
                            ds.canvas.fill((255, 255, 255))
                        elif btn.action == 'size_down' and ds.pen_size > 2:
                            ds.pen_size -= 1
                        elif btn.action == 'size_up' and ds.pen_size < 30:
                            ds.pen_size += 1

        # ── Отрисовка кадра ──────────────────────────────────────────────────
        win.fill((240, 240, 240))

        # Холст (постоянный рисунок)
        win.blit(ds.canvas, (0, 0))

        # Предпросмотр текущей фигуры поверх холста
        draw_preview(win, ds)

        # Курсор пера / ластика
        if ds.tool in ('pen', 'eraser'):
            mx, my = pygame.mouse.get_pos()
            r = ds.pen_size * (2 if ds.tool == 'eraser' else 1)
            pygame.draw.circle(win, (180, 180, 180), (mx, my), r, 1)

        # Боковая панель (фон)
        pygame.draw.rect(win, (230, 230, 230), (PANEL_X, 0, WIN_X - PANEL_X, WIN_Y))
        pygame.draw.rect(win, (0, 0, 0), (PANEL_X, 0, WIN_X - PANEL_X, WIN_Y), 2)

        # Кнопки
        for btn in color_buttons:
            btn.draw(win, font_small)
        for btn in tool_buttons:
            btn.draw(win, font_small)
        for btn in util_buttons:
            btn.draw(win, font_small)

        # Заголовок (поверх всего)
        draw_header(win, ds, font_small)

        # Граница холста
        pygame.draw.rect(win, (0, 0, 0), (0, 0, CANVAS_W, WIN_Y), 2)

        pygame.display.update()
        FramePerSec.tick(FPS)

    pygame.quit()


main()