'''
Paint — расширенная версия туториала nerdparadise.com/programming/pygame/part6
Добавлено:
  1. Рисование прямоугольника (Rectangle) — drag & drop
  2. Рисование круга (Circle) — drag & drop
  3. Ластик (Eraser)
  4. Выбор цвета (Color Selection) — палитра в боковой панели
  5. Комментарии к коду
'''

import pygame
import math

pygame.init()

# ── Настройки окна ────────────────────────────────────────────────────────────
SCREEN_WIDTH  = 600   # 400 холст + 200 панель
SCREEN_HEIGHT = 600
CANVAS_W      = 400   # ширина области рисования
PANEL_X       = 400   # x-начало боковой панели

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Paint')

clock = pygame.time.Clock()
FPS   = 120

# ── Цветовая палитра ──────────────────────────────────────────────────────────
PALETTE = [
    ((255,   0,   0), 'Red'),
    ((  0,   0, 255), 'Blue'),
    ((  0, 200,   0), 'Green'),
    ((255, 165,   0), 'Orange'),
    ((255, 255,   0), 'Yellow'),
    ((128,   0, 128), 'Purple'),
    ((  0,   0,   0), 'Black'),
    ((139,  69,  19), 'Brown'),
    ((255, 192, 203), 'Pink'),
    ((  0, 255, 255), 'Cyan'),
]

# ── Доступные инструменты ─────────────────────────────────────────────────────
TOOLS = ['Pen', 'Rectangle', 'Circle', 'Eraser']


# ── Класс состояния приложения ────────────────────────────────────────────────
class AppState:
    def __init__(self):
        self.color     = (0, 0, 0)    # текущий цвет рисования
        self.tool      = 'Pen'        # текущий инструмент
        self.pen_size  = 6            # размер пера/ластика
        self.dragging  = False        # зажата ли ЛКМ
        self.start_pos = None         # точка начала drag

        # canvas — постоянная поверхность с рисунком.
        # Предпросмотр фигур рисуется поверх неё, не изменяя её до отпускания кнопки.
        self.canvas = pygame.Surface((CANVAS_W, SCREEN_HEIGHT))
        self.canvas.fill((255, 255, 255))

    def on_canvas(self, pos):
        """Проверяет, находится ли позиция внутри области холста."""
        return 0 <= pos[0] < CANVAS_W and 25 <= pos[1] < SCREEN_HEIGHT

    def handle_event(self, event):
        """Обрабатывает события мыши для рисования."""
        pos = pygame.mouse.get_pos()

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.on_canvas(pos):
                self.dragging  = True
                self.start_pos = pos

        elif event.type == pygame.MOUSEMOTION and self.dragging:
            if self.on_canvas(pos):
                # Перо и ластик рисуют непрерывно во время движения
                if self.tool == 'Pen':
                    pygame.draw.circle(self.canvas, self.color, pos, self.pen_size)
                elif self.tool == 'Eraser':
                    # Ластик закрашивает белым кружком увеличенного радиуса
                    pygame.draw.circle(self.canvas, (255, 255, 255), pos, self.pen_size * 3)

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.dragging and self.start_pos:
                end = pos
                # Фигуры фиксируются на холсте только при отпускании кнопки
                if self.tool == 'Rectangle':
                    rect = self._make_rect(self.start_pos, end)
                    pygame.draw.rect(self.canvas, self.color, rect, 2)
                elif self.tool == 'Circle':
                    cx, cy, r = self._make_circle(self.start_pos, end)
                    pygame.draw.circle(self.canvas, self.color, (cx, cy), max(1, r), 2)
            self.dragging  = False
            self.start_pos = None

    def _make_rect(self, start, end):
        """Вычисляет pygame.Rect по двум угловым точкам (порядок не важен)."""
        x = min(start[0], end[0])
        y = min(start[1], end[1])
        w = abs(end[0] - start[0])
        h = abs(end[1] - start[1])
        return pygame.Rect(x, y, w, h)

    def _make_circle(self, start, end):
        """
        Вычисляет центр и радиус круга.
        Центр — середина между start и end, радиус — половина расстояния.
        """
        cx = (start[0] + end[0]) // 2
        cy = (start[1] + end[1]) // 2
        r  = int(math.hypot(end[0] - start[0], end[1] - start[1]) / 2)
        return cx, cy, r

    def draw_preview(self, surface):
        """
        Рисует полупрозрачный предпросмотр фигуры во время drag'а.
        Перо и ластик не нуждаются в предпросмотре — они уже пишут на canvas.
        """
        if not self.dragging or self.start_pos is None:
            return
        if self.tool in ('Pen', 'Eraser'):
            return

        end     = pygame.mouse.get_pos()
        preview = pygame.Surface((CANVAS_W, SCREEN_HEIGHT), pygame.SRCALPHA)
        r, g, b = self.color

        if self.tool == 'Rectangle':
            rect = self._make_rect(self.start_pos, end)
            pygame.draw.rect(preview, (r, g, b, 150), rect, 2)

        elif self.tool == 'Circle':
            cx, cy, radius = self._make_circle(self.start_pos, end)
            if radius > 0:
                pygame.draw.circle(preview, (r, g, b, 150), (cx, cy), radius, 2)

        surface.blit(preview, (0, 0))


# ── Класс кнопки ──────────────────────────────────────────────────────────────
class Button:
    def __init__(self, x, y, w, h, color, label='', label_color=(0, 0, 0), tag=None):
        self.rect        = pygame.Rect(x, y, w, h)
        self.color       = color        # цвет фона кнопки
        self.label       = label
        self.label_color = label_color
        self.tag         = tag          # произвольное значение (имя инструмента, цвет…)
        self.active      = False        # активна ли кнопка (подсветка)

    def draw(self, surface, font):
        pygame.draw.rect(surface, self.color, self.rect)
        # Активная кнопка — белая рамка; неактивная — чёрная
        border = (255, 255, 255) if self.active else (0, 0, 0)
        pygame.draw.rect(surface, border, self.rect, 2)
        if self.label:
            text = font.render(self.label, True, self.label_color)
            surface.blit(text, text.get_rect(center=self.rect.center))

    def hit(self, pos):
        """Возвращает True если pos внутри кнопки."""
        return self.rect.collidepoint(pos)


# ── Построение кнопок панели ──────────────────────────────────────────────────
def build_buttons():
    """
    Создаёт три группы кнопок:
      color_btns — цветовая палитра (два столбца)
      tool_btns  — инструменты
      util_btns  — утилиты (Clear, размер пера +/-)
    Возвращает (color_btns, tool_btns, util_btns).
    """
    color_btns = []
    tool_btns  = []
    util_btns  = []

    # ── Палитра: сетка 2 × N ─────────────────────────────────────────────────
    btn_size = 44
    gap      = 4
    cols     = 2
    for i, (color, name) in enumerate(PALETTE):
        col = i % cols
        row = i // cols
        x   = PANEL_X + 6 + col * (btn_size + gap)
        y   = 30 + row * (btn_size + gap)
        # Белая кнопка имеет чёрную рамку чтобы её было видно
        lbl_c = (0, 0, 0) if color == (255, 255, 255) else color
        b = Button(x, y, btn_size, btn_size, color,
                   label_color=lbl_c, tag=('color', color))
        color_btns.append(b)

    # ── Инструменты ───────────────────────────────────────────────────────────
    palette_rows = math.ceil(len(PALETTE) / cols)
    tool_y_start = 30 + palette_rows * (btn_size + gap) + 10
    for i, tool_name in enumerate(TOOLS):
        y = tool_y_start + i * 38
        b = Button(PANEL_X + 6, y, 188, 34,
                   (201, 201, 201), label=tool_name, tag=('tool', tool_name))
        tool_btns.append(b)

    # Первый инструмент (Pen) активен по умолчанию
    tool_btns[0].active = True

    # ── Утилиты ───────────────────────────────────────────────────────────────
    util_y = tool_y_start + len(TOOLS) * 38 + 10
    util_btns.append(Button(PANEL_X + 6, util_y,       188, 34,
                            (201, 201, 201), label='Clear',   tag='clear'))
    util_btns.append(Button(PANEL_X + 6, util_y + 42,   90, 34,
                            (201, 201, 201), label='–  Size', tag='size_down'))
    util_btns.append(Button(PANEL_X + 104, util_y + 42, 90, 34,
                            (201, 201, 201), label='+ Size',  tag='size_up'))

    return color_btns, tool_btns, util_btns


# ── Отрисовка заголовка ───────────────────────────────────────────────────────
def draw_header(surface, state, font):
    # Серая полоска сверху
    pygame.draw.rect(surface, (175, 171, 171), (0, 0, SCREEN_WIDTH, 25))
    pygame.draw.rect(surface, (0, 0, 0), (0, 0, CANVAS_W, 25), 2)
    pygame.draw.rect(surface, (0, 0, 0), (CANVAS_W, 0, SCREEN_WIDTH - CANVAS_W, 25), 2)

    # Название холста
    t = font.render('Пэйнт', True, (0, 0, 0))
    surface.blit(t, t.get_rect(center=(CANVAS_W // 2, 13)))

    # Текущий инструмент + размер
    info = font.render(f'{state.tool}  size:{state.pen_size}', True, (0, 0, 0))
    surface.blit(info, info.get_rect(center=(PANEL_X + (SCREEN_WIDTH - PANEL_X) // 2, 13)))


# ── Главный цикл ──────────────────────────────────────────────────────────────
def main():
    state = AppState()
    font  = pygame.font.SysFont('comicsans', 18)

    color_btns, tool_btns, util_btns = build_buttons()

    run = True
    while run:
        keys = pygame.key.get_pressed()

        for event in pygame.event.get():
            if event.type == pygame.QUIT or keys[pygame.K_ESCAPE]:
                run = False

            # Передаём событие логике рисования
            state.handle_event(event)

            # Клики по кнопкам панели
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos

                # Цветовые кнопки — меняем текущий цвет
                for btn in color_btns:
                    if btn.hit(pos):
                        state.color = btn.tag[1]

                # Кнопки инструментов — меняем инструмент
                for btn in tool_btns:
                    if btn.hit(pos):
                        state.tool = btn.tag[1]
                        for b in tool_btns:
                            b.active = False
                        btn.active = True

                # Утилиты
                for btn in util_btns:
                    if btn.hit(pos):
                        if btn.tag == 'clear':
                            state.canvas.fill((255, 255, 255))
                        elif btn.tag == 'size_down' and state.pen_size > 1:
                            state.pen_size -= 1
                        elif btn.tag == 'size_up' and state.pen_size < 40:
                            state.pen_size += 1

        # ── Отрисовка кадра ──────────────────────────────────────────────────

        screen.fill((220, 220, 220))

        # 1. Постоянный холст
        screen.blit(state.canvas, (0, 0))

        # 2. Предпросмотр фигуры поверх холста (только Rectangle / Circle)
        state.draw_preview(screen)

        # 3. Курсор пера / ластика (кольцо вокруг мыши)
        mx, my = pygame.mouse.get_pos()
        if state.tool == 'Pen':
            pygame.draw.circle(screen, (150, 150, 150), (mx, my), state.pen_size, 1)
        elif state.tool == 'Eraser':
            pygame.draw.rect(screen, (150, 150, 150),
                             pygame.Rect(mx - state.pen_size * 3,
                                         my - state.pen_size * 3,
                                         state.pen_size * 6,
                                         state.pen_size * 6), 1)

        # 4. Боковая панель
        pygame.draw.rect(screen, (230, 230, 230),
                         (PANEL_X, 0, SCREEN_WIDTH - PANEL_X, SCREEN_HEIGHT))
        pygame.draw.rect(screen, (0, 0, 0),
                         (PANEL_X, 0, SCREEN_WIDTH - PANEL_X, SCREEN_HEIGHT), 2)

        # 5. Цветной индикатор выбранного цвета
        pygame.draw.rect(screen, state.color,
                         pygame.Rect(PANEL_X + 6, SCREEN_HEIGHT - 44, 188, 38))
        pygame.draw.rect(screen, (0, 0, 0),
                         pygame.Rect(PANEL_X + 6, SCREEN_HEIGHT - 44, 188, 38), 2)

        # 6. Кнопки
        for btn in color_btns:
            btn.draw(screen, font)
        for btn in tool_btns:
            btn.draw(screen, font)
        for btn in util_btns:
            btn.draw(screen, font)

        # 7. Заголовок (поверх всего)
        draw_header(screen, state, font)

        # 8. Рамка холста
        pygame.draw.rect(screen, (0, 0, 0), (0, 0, CANVAS_W, SCREEN_HEIGHT), 2)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


main()