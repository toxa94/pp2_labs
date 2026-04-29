'''
Snake Game — расширенная версия
Добавлено:
  1. Проверка столкновения со стенами
  2. Генерация еды не на стене и не на змейке
  3. Уровни (каждые 3 съеденных фрукта — новый уровень)
  4. Увеличение скорости при переходе на новый уровень
  5. Счётчик очков и уровня на экране
  6. Комментарии к коду
'''

import pygame
import time
import random

# ── Настройки окна ────────────────────────────────────────────────────────────
WINDOW_X = 720
WINDOW_Y = 480
CELL = 10  # размер одной клетки в пикселях

# ── Настройки уровней и скорости ─────────────────────────────────────────────
BASE_SPEED      = 10   # начальная скорость (FPS) на уровне 1
SPEED_INCREMENT = 3    # прибавка к скорости за каждый уровень
MAX_SPEED       = 40   # максимальная скорость (чтобы игра оставалась играбельной)
FOOD_PER_LEVEL  = 3    # сколько фруктов нужно съесть для перехода на следующий уровень

# ── Цвета ─────────────────────────────────────────────────────────────────────
BLACK      = pygame.Color(0,   0,   0)
WHITE      = pygame.Color(255, 255, 255)
RED        = pygame.Color(255, 0,   0)
GREEN      = pygame.Color(0,   200, 0)
DARK_GREEN = pygame.Color(0,   150, 0)
YELLOW     = pygame.Color(255, 220, 0)
GRAY       = pygame.Color(40,  40,  40)
WALL_COLOR = pygame.Color(80,  80,  80)

# ── Инициализация Pygame ──────────────────────────────────────────────────────
pygame.init()
pygame.display.set_caption('Змейка')
game_window = pygame.display.set_mode((WINDOW_X, WINDOW_Y))
fps = pygame.time.Clock()


# ── Вспомогательные функции ───────────────────────────────────────────────────

def get_wall_cells():
    """
    Возвращает множество координат клеток, которые являются стенами.
    Стены — это граничный ряд/столбец клеток по периметру окна.
    """
    walls = set()
    cols = WINDOW_X // CELL
    rows = WINDOW_Y // CELL
    for x in range(cols):
        walls.add((x * CELL, 0))                    # верхняя стена
        walls.add((x * CELL, (rows - 1) * CELL))    # нижняя стена
    for y in range(rows):
        walls.add((0, y * CELL))                     # левая стена
        walls.add(((cols - 1) * CELL, y * CELL))    # правая стена
    return walls

WALL_CELLS = get_wall_cells()  # вычисляем один раз при запуске


def generate_food(snake_body):
    """
    Генерирует случайную позицию еды.
    Еда НЕ должна появляться:
      - на стене (граничные клетки)
      - на теле змейки
    Возвращает [x, y].
    """
    snake_set = set(map(tuple, snake_body))  # для быстрой проверки O(1)

    # Собираем все допустимые клетки (не стена, не тело змейки)
    free_cells = []
    for x in range(CELL, WINDOW_X - CELL, CELL):
        for y in range(CELL, WINDOW_Y - CELL, CELL):
            if (x, y) not in snake_set:
                free_cells.append([x, y])

    if not free_cells:
        return None  # поле полностью занято (маловероятно, но обрабатываем)

    return random.choice(free_cells)


def draw_walls():
    """Рисует стены по периметру игрового поля."""
    cols = WINDOW_X // CELL
    rows = WINDOW_Y // CELL
    for x in range(cols):
        pygame.draw.rect(game_window, WALL_COLOR, pygame.Rect(x * CELL, 0, CELL, CELL))
        pygame.draw.rect(game_window, WALL_COLOR, pygame.Rect(x * CELL, (rows - 1) * CELL, CELL, CELL))
    for y in range(1, rows - 1):
        pygame.draw.rect(game_window, WALL_COLOR, pygame.Rect(0, y * CELL, CELL, CELL))
        pygame.draw.rect(game_window, WALL_COLOR, pygame.Rect((cols - 1) * CELL, y * CELL, CELL, CELL))


def show_hud(score, level, snake_speed):
    """
    Отображает HUD: счёт, уровень и текущую скорость в верхней части экрана.
    """
    font = pygame.font.SysFont('consolas', 18)

    score_surf = font.render(f'Score: {score}', True, WHITE)
    level_surf = font.render(f'Level: {level}', True, YELLOW)
    speed_surf = font.render(f'Speed: {snake_speed}', True, WHITE)

    game_window.blit(score_surf, (CELL + 5, 2))
    game_window.blit(level_surf, (WINDOW_X // 2 - 40, 2))
    game_window.blit(speed_surf, (WINDOW_X - 110, 2))


def show_level_up(level):
    """
    Показывает сообщение о переходе на новый уровень в центре экрана.
    Делает паузу 1 секунду чтобы игрок заметил.
    """
    font = pygame.font.SysFont('consolas', 40)
    text = font.render(f'LEVEL {level}!', True, YELLOW)
    rect = text.get_rect(center=(WINDOW_X // 2, WINDOW_Y // 2))
    game_window.blit(text, rect)
    pygame.display.flip()
    time.sleep(1)


def game_over(score):
    """
    Экран завершения игры: показывает финальный счёт и выходит.
    """
    game_window.fill(BLACK)
    font_big  = pygame.font.SysFont('consolas', 48)
    font_small = pygame.font.SysFont('consolas', 24)

    over_surf  = font_big.render('GAME OVER', True, RED)
    score_surf = font_small.render(f'Your score: {score}', True, WHITE)
    quit_surf  = font_small.render('Closing in 3 seconds...', True, GRAY)

    game_window.blit(over_surf,  over_surf.get_rect(center=(WINDOW_X // 2, WINDOW_Y // 2 - 50)))
    game_window.blit(score_surf, score_surf.get_rect(center=(WINDOW_X // 2, WINDOW_Y // 2 + 10)))
    game_window.blit(quit_surf,  quit_surf.get_rect(center=(WINDOW_X // 2, WINDOW_Y // 2 + 50)))

    pygame.display.flip()
    time.sleep(3)
    pygame.quit()
    quit()


# ── Начальное состояние игры ──────────────────────────────────────────────────

# Змейка начинает в центре поля, длина 4 блока, движется вправо
snake_position = [100, 50]
snake_body = [
    [100, 50],
    [90,  50],
    [80,  50],
    [70,  50],
]

direction = 'RIGHT'
change_to = direction

score       = 0
level       = 1
food_eaten  = 0                          # счётчик еды на текущем уровне
snake_speed = BASE_SPEED                 # текущая скорость

fruit_position = generate_food(snake_body)  # первая позиция еды
fruit_spawn    = True


# ── Главный игровой цикл ──────────────────────────────────────────────────────
while True:

    # Обработка событий клавиатуры
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            quit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:    change_to = 'UP'
            if event.key == pygame.K_DOWN:  change_to = 'DOWN'
            if event.key == pygame.K_LEFT:  change_to = 'LEFT'
            if event.key == pygame.K_RIGHT: change_to = 'RIGHT'
            if event.key == pygame.K_ESCAPE:
                pygame.quit()
                quit()

    # Запрет разворота на 180° (нельзя сразу двигаться в противоположную сторону)
    if change_to == 'UP'    and direction != 'DOWN':  direction = 'UP'
    if change_to == 'DOWN'  and direction != 'UP':    direction = 'DOWN'
    if change_to == 'LEFT'  and direction != 'RIGHT': direction = 'LEFT'
    if change_to == 'RIGHT' and direction != 'LEFT':  direction = 'RIGHT'

    # Движение змейки: обновляем позицию головы
    if direction == 'UP':    snake_position[1] -= CELL
    if direction == 'DOWN':  snake_position[1] += CELL
    if direction == 'LEFT':  snake_position[0] -= CELL
    if direction == 'RIGHT': snake_position[0] += CELL

    # Добавляем новую голову в начало тела
    snake_body.insert(0, list(snake_position))

    # Проверяем, съела ли змейка фрукт
    if snake_position == fruit_position:
        score      += level * 10   # очки растут с уровнем
        food_eaten += 1
        fruit_spawn = False

        # ── Проверка условия перехода на следующий уровень ──
        if food_eaten >= FOOD_PER_LEVEL:
            level      += 1
            food_eaten  = 0

            # Увеличиваем скорость, но не выше максимума
            snake_speed = min(MAX_SPEED, BASE_SPEED + (level - 1) * SPEED_INCREMENT)

            # Рисуем экран и показываем сообщение о новом уровне
            game_window.fill(BLACK)
            draw_walls()
            show_level_up(level)

    else:
        # Фрукт не съеден — убираем хвост, длина остаётся прежней
        snake_body.pop()

    # Если фрукт был съеден — генерируем новый на допустимой позиции
    if not fruit_spawn:
        fruit_position = generate_food(snake_body)
        if fruit_position is None:
            # Поле полностью заполнено — победа (редкий случай)
            game_over(score)
        fruit_spawn = True

    # ── Отрисовка кадра ──────────────────────────────────────────────────────
    game_window.fill(BLACK)

    # Рисуем стены
    draw_walls()

    # Рисуем тело змейки (голова чуть ярче)
    for i, pos in enumerate(snake_body):
        color = GREEN if i > 0 else DARK_GREEN
        pygame.draw.rect(game_window, color, pygame.Rect(pos[0], pos[1], CELL, CELL))

    # Рисуем еду
    if fruit_position:
        pygame.draw.rect(game_window, RED,
                         pygame.Rect(fruit_position[0], fruit_position[1], CELL, CELL))

    # ── Проверка условий Game Over ────────────────────────────────────────────

    # 1. Столкновение со стеной: голова попала на граничную клетку
    if tuple(snake_position) in WALL_CELLS:
        game_over(score)

    # 2. Выход за пределы окна (дополнительная защита)
    if (snake_position[0] < 0 or snake_position[0] >= WINDOW_X or
            snake_position[1] < 0 or snake_position[1] >= WINDOW_Y):
        game_over(score)

    # 3. Столкновение с собственным телом (проверяем со второго сегмента)
    for block in snake_body[1:]:
        if snake_position == block:
            game_over(score)

    # ── HUD и обновление экрана ───────────────────────────────────────────────
    show_hud(score, level, snake_speed)
    pygame.display.update()
    fps.tick(snake_speed)