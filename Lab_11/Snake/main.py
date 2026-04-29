'''
Snake Game — расширенная версия (Practice задание)
Добавлено поверх предыдущей версии:
  1. Еда с разными весами (разные шансы появления и очки)
  2. Еда исчезает через некоторое время (таймер)
  3. Комментарии к коду
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
MAX_SPEED       = 40   # максимальная скорость
FOOD_PER_LEVEL  = 3    # фруктов до следующего уровня

# ── Настройки типов еды ───────────────────────────────────────────────────────
#
# Каждый тип еды имеет:
#   weight      — вес (шанс появления): чем больше, тем чаще появляется
#   points      — очки за съедание (умножаются на текущий уровень)
#   lifetime    — время жизни в секундах (после — исчезает)
#   color       — цвет на поле
#   label       — подпись для отладки / HUD
#
FOOD_TYPES = {
    'common': {
        'weight':   60,
        'points':   1,
        'lifetime': 8.0,
        'color':    pygame.Color(255, 80,  80),   # красный — обычная еда
        'label':    'Common',
    },
    'rare': {
        'weight':   30,
        'points':   3,
        'lifetime': 5.0,
        'color':    pygame.Color(80,  180, 255),  # синий — редкая еда
        'label':    'Rare',
    },
    'epic': {
        'weight':   10,
        'points':   7,
        'lifetime': 3.0,
        'color':    pygame.Color(220, 80,  255),  # фиолетовый — эпическая еда
        'label':    'Epic',
    },
}

# Подготавливаем списки для random.choices (порядок фиксирован)
_FOOD_NAMES   = list(FOOD_TYPES.keys())
_FOOD_WEIGHTS = [FOOD_TYPES[n]['weight'] for n in _FOOD_NAMES]


def pick_food_type():
    """Возвращает случайный тип еды с учётом весов."""
    return random.choices(_FOOD_NAMES, weights=_FOOD_WEIGHTS, k=1)[0]


# ── Цвета ─────────────────────────────────────────────────────────────────────
BLACK      = pygame.Color(0,   0,   0)
WHITE      = pygame.Color(255, 255, 255)
GREEN      = pygame.Color(0,   200, 0)
DARK_GREEN = pygame.Color(0,   150, 0)
YELLOW     = pygame.Color(255, 220, 0)
GRAY       = pygame.Color(40,  40,  40)
WALL_COLOR = pygame.Color(80,  80,  80)

# ── Инициализация Pygame ──────────────────────────────────────────────────────
pygame.init()
pygame.display.set_caption('Змейка')
game_window = pygame.display.set_mode((WINDOW_X, WINDOW_Y))
fps_clock = pygame.time.Clock()


# ── Вспомогательные функции ───────────────────────────────────────────────────

def get_wall_cells():
    """
    Строит множество (set) координат всех граничных клеток.
    Используется для быстрой O(1) проверки столкновения со стеной.
    """
    walls = set()
    cols, rows = WINDOW_X // CELL, WINDOW_Y // CELL
    for x in range(cols):
        walls.add((x * CELL, 0))
        walls.add((x * CELL, (rows - 1) * CELL))
    for y in range(rows):
        walls.add((0, y * CELL))
        walls.add(((cols - 1) * CELL, y * CELL))
    return walls

WALL_CELLS = get_wall_cells()


def generate_food_position(snake_body):
    """
    Возвращает случайную [x, y] позицию для еды,
    которая НЕ совпадает со стеной и НЕ лежит на теле змейки.
    Возвращает None если свободных клеток нет (победа).
    """
    snake_set = set(map(tuple, snake_body))
    free = [
        [x, y]
        for x in range(CELL, WINDOW_X - CELL, CELL)
        for y in range(CELL, WINDOW_Y - CELL, CELL)
        if (x, y) not in snake_set
    ]
    return random.choice(free) if free else None


def draw_walls():
    """Рисует серые стены по периметру поля."""
    cols, rows = WINDOW_X // CELL, WINDOW_Y // CELL
    for x in range(cols):
        pygame.draw.rect(game_window, WALL_COLOR, (x * CELL, 0, CELL, CELL))
        pygame.draw.rect(game_window, WALL_COLOR, (x * CELL, (rows - 1) * CELL, CELL, CELL))
    for y in range(1, rows - 1):
        pygame.draw.rect(game_window, WALL_COLOR, (0, y * CELL, CELL, CELL))
        pygame.draw.rect(game_window, WALL_COLOR, ((cols - 1) * CELL, y * CELL, CELL, CELL))


def draw_food(food_pos, food_type, spawn_time):
    """
    Рисует еду на поле.
    По мере истечения таймера еда «мигает» — это визуальное предупреждение игроку.
    
    food_pos   — [x, y] позиция
    food_type  — строка-ключ из FOOD_TYPES
    spawn_time — time.time() момента появления еды
    """
    info     = FOOD_TYPES[food_type]
    elapsed  = time.time() - spawn_time
    lifetime = info['lifetime']
    remaining = lifetime - elapsed

    # Когда осталось меньше 2 секунд — еда мигает раз в 0.3 сек
    if remaining < 2.0:
        blink = int(elapsed / 0.3) % 2  # чередуем 0 и 1
        if blink == 1:
            return  # не рисуем в этот кадр (эффект мигания)

    color = info['color']

    # Основной квадрат еды
    pygame.draw.rect(game_window, color,
                     pygame.Rect(food_pos[0], food_pos[1], CELL, CELL))

    # Маленький белый блик в левом верхнем углу клетки (визуальный акцент)
    pygame.draw.rect(game_window, WHITE,
                     pygame.Rect(food_pos[0] + 1, food_pos[1] + 1, 3, 3))


def show_hud(score, level, snake_speed, food_type, spawn_time):
    """
    Рисует HUD в верхней части экрана:
      - слева:  Score и тип текущей еды
      - центр:  Level
      - справа: Speed и таймер до исчезновения еды
    """
    font = pygame.font.SysFont('consolas', 16)

    # Счёт
    game_window.blit(
        font.render(f'Score: {score}', True, WHITE),
        (CELL + 5, 2)
    )

    # Тип еды с цветом
    food_info  = FOOD_TYPES[food_type]
    type_surf  = font.render(f'{food_info["label"]} +{food_info["points"]}pts', True, food_info['color'])
    game_window.blit(type_surf, (CELL + 5, 18))

    # Уровень (центр)
    lvl_surf = font.render(f'Level: {level}', True, YELLOW)
    game_window.blit(lvl_surf, (WINDOW_X // 2 - 35, 2))

    # Скорость (справа)
    game_window.blit(
        font.render(f'Speed: {snake_speed}', True, WHITE),
        (WINDOW_X - 100, 2)
    )

    # Таймер до исчезновения еды
    remaining = max(0.0, food_info['lifetime'] - (time.time() - spawn_time))
    timer_color = YELLOW if remaining > 2 else pygame.Color(255, 80, 80)
    game_window.blit(
        font.render(f'Food: {remaining:.1f}s', True, timer_color),
        (WINDOW_X - 100, 18)
    )


def show_level_up(level):
    """Показывает сообщение о новом уровне с паузой 1 секунда."""
    font = pygame.font.SysFont('consolas', 40)
    text = font.render(f'LEVEL {level}!', True, YELLOW)
    game_window.blit(text, text.get_rect(center=(WINDOW_X // 2, WINDOW_Y // 2)))
    pygame.display.flip()
    time.sleep(1)


def game_over(score):
    """Экран Game Over: финальный счёт, пауза 3 сек, выход."""
    game_window.fill(BLACK)
    f_big   = pygame.font.SysFont('consolas', 48)
    f_small = pygame.font.SysFont('consolas', 24)

    game_window.blit(
        f_big.render('GAME OVER', True, pygame.Color(255, 80, 80)),
        f_big.render('GAME OVER', True, pygame.Color(255, 80, 80))
              .get_rect(center=(WINDOW_X // 2, WINDOW_Y // 2 - 50))
    )
    game_window.blit(
        f_small.render(f'Your score: {score}', True, WHITE),
        f_small.render(f'Your score: {score}', True, WHITE)
               .get_rect(center=(WINDOW_X // 2, WINDOW_Y // 2 + 10))
    )
    game_window.blit(
        f_small.render('Closing in 3 seconds...', True, GRAY),
        f_small.render('Closing in 3 seconds...', True, GRAY)
               .get_rect(center=(WINDOW_X // 2, WINDOW_Y // 2 + 50))
    )
    pygame.display.flip()
    time.sleep(3)
    pygame.quit()
    quit()


# ── Начальное состояние игры ──────────────────────────────────────────────────

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
food_eaten  = 0
snake_speed = BASE_SPEED

# Генерируем первую еду со случайным типом
current_food_type  = pick_food_type()
fruit_position     = generate_food_position(snake_body)
food_spawn_time    = time.time()   # момент появления еды (для таймера)
fruit_spawn        = True


# ── Главный игровой цикл ──────────────────────────────────────────────────────
while True:

    # Обработка событий клавиатуры
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            quit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:     change_to = 'UP'
            if event.key == pygame.K_DOWN:   change_to = 'DOWN'
            if event.key == pygame.K_LEFT:   change_to = 'LEFT'
            if event.key == pygame.K_RIGHT:  change_to = 'RIGHT'
            if event.key == pygame.K_ESCAPE:
                pygame.quit()
                quit()

    # Запрет разворота на 180°
    if change_to == 'UP'    and direction != 'DOWN':  direction = 'UP'
    if change_to == 'DOWN'  and direction != 'UP':    direction = 'DOWN'
    if change_to == 'LEFT'  and direction != 'RIGHT': direction = 'LEFT'
    if change_to == 'RIGHT' and direction != 'LEFT':  direction = 'RIGHT'

    # Движение змейки
    if direction == 'UP':    snake_position[1] -= CELL
    if direction == 'DOWN':  snake_position[1] += CELL
    if direction == 'LEFT':  snake_position[0] -= CELL
    if direction == 'RIGHT': snake_position[0] += CELL

    snake_body.insert(0, list(snake_position))

    # ── Проверяем, съела ли змейка еду ───────────────────────────────────────
    if snake_position == fruit_position:
        # Очки = базовые очки типа еды × текущий уровень
        points      = FOOD_TYPES[current_food_type]['points']
        score      += points * level
        food_eaten += 1
        fruit_spawn = False

        # Проверяем level-up
        if food_eaten >= FOOD_PER_LEVEL:
            level      += 1
            food_eaten  = 0
            snake_speed = min(MAX_SPEED, BASE_SPEED + (level - 1) * SPEED_INCREMENT)
            game_window.fill(BLACK)
            draw_walls()
            show_level_up(level)
    else:
        snake_body.pop()   # хвост убирается, если еда не съедена

    # ── Таймер: еда исчезает по истечении lifetime ────────────────────────────
    food_lifetime = FOOD_TYPES[current_food_type]['lifetime']
    food_expired  = (time.time() - food_spawn_time) >= food_lifetime

    if food_expired:
        # Еда истекла — генерируем новую с новым случайным типом
        fruit_spawn = False

    # Спавн новой еды (после съедания или истечения таймера)
    if not fruit_spawn:
        current_food_type = pick_food_type()              # новый случайный тип
        fruit_position    = generate_food_position(snake_body)
        if fruit_position is None:
            game_over(score)                              # поле заполнено — победа
        food_spawn_time = time.time()                     # сбрасываем таймер
        fruit_spawn     = True

    # ── Отрисовка кадра ──────────────────────────────────────────────────────
    game_window.fill(BLACK)
    draw_walls()

    # Змейка (голова темнее тела)
    for i, pos in enumerate(snake_body):
        color = GREEN if i > 0 else DARK_GREEN
        pygame.draw.rect(game_window, color, pygame.Rect(pos[0], pos[1], CELL, CELL))

    # Еда с эффектом мигания при истечении времени
    if fruit_position:
        draw_food(fruit_position, current_food_type, food_spawn_time)

    # ── Проверка Game Over ────────────────────────────────────────────────────

    # 1. Столкновение со стеной
    if tuple(snake_position) in WALL_CELLS:
        game_over(score)

    # 2. Выход за пределы окна (доп. защита)
    if (snake_position[0] < 0 or snake_position[0] >= WINDOW_X or
            snake_position[1] < 0 or snake_position[1] >= WINDOW_Y):
        game_over(score)

    # 3. Столкновение с телом
    for block in snake_body[1:]:
        if snake_position == block:
            game_over(score)

    # ── HUD и обновление экрана ───────────────────────────────────────────────
    show_hud(score, level, snake_speed, current_food_type, food_spawn_time)
    pygame.display.update()
    fps_clock.tick(snake_speed)