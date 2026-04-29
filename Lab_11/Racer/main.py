# Racer — расширенная версия
# Добавлено:
#   1. Монеты с разными весами (gold/silver/bronze) — разные шансы появления и очки
#   2. Увеличение скорости врага при накоплении N монет
#   3. Комментарии к коду

import pygame
import random
import time
from itertools import chain

pygame.init()

# ── Цвета ─────────────────────────────────────────────────────────────────────
black = pygame.Color((0, 0, 0))
white = pygame.Color((255, 255, 255))
red   = pygame.Color((255, 0, 0))
blue  = pygame.Color((0, 0, 255))
green = pygame.Color((0, 255, 0))

# ── Игровые переменные ────────────────────────────────────────────────────────
screen_width  = 400
screen_height = 600
speed         = 5    # начальная скорость врага (глобальная, меняется при level-up)

# Очки и монеты
score      = 0   # счёт за объезд врагов
coin_score = 0   # общее кол-во очков от монет

# Порог монет для увеличения скорости врага
COINS_PER_SPEEDUP = 5    # каждые 5 монет (по весу) — враг ускоряется
SPEED_INCREMENT   = 1    # на сколько единиц растёт скорость
MAX_SPEED         = 15   # максимальная скорость врага

# ── Шрифты ───────────────────────────────────────────────────────────────────
font       = pygame.font.SysFont("Verdana", 60)
font_small = pygame.font.SysFont("Verdana", 18)
game_over_text = font.render("Game Over", True, black)

# ── Фон ──────────────────────────────────────────────────────────────────────
background = pygame.image.load("C:/Users/makha/OneDrive/Desktop/PP2-Practices/Practice-10/Racer/img/AnimatedStreet.png")

# ── Экран ────────────────────────────────────────────────────────────────────
screen = pygame.display.set_mode((screen_width, screen_height))
screen.fill(white)
pygame.display.set_caption("Racer")
clock = pygame.time.Clock()
loop  = True


# ── Классы ───────────────────────────────────────────────────────────────────

class Enemy(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.image.load("C:/Users/makha/OneDrive/Desktop/PP2-Practices/Practice-10/Racer/img/Enemy.png")
        self.rect  = self.image.get_rect()
        self.rect.center = (random.randint(40, screen_width - 40), -20)

    def move(self):
        """Двигает врага вниз. Когда выезжает за экран — перемещает наверх и даёт очко."""
        global score
        self.rect.move_ip(0, speed)
        if self.rect.top > screen_height:
            score += 1
            self.rect.top = 0
            self.rect.center = (random.randint(40, screen_width - 40), -20)


class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.image.load("C:/Users/makha/OneDrive/Desktop/PP2-Practices/Practice-10/Racer/img/Player.png")
        self.rect  = self.image.get_rect()
        self.rect.center = (160, 520)

    def move(self):
        """Двигает игрока влево/вправо по нажатию стрелок."""
        pressed = pygame.key.get_pressed()
        if self.rect.left > 0 and pressed[pygame.K_LEFT]:
            self.rect.move_ip(-5, 0)
        if self.rect.right < screen_width and pressed[pygame.K_RIGHT]:
            self.rect.move_ip(5, 0)


# ── Монеты с весами ───────────────────────────────────────────────────────────
#
# У каждой монеты есть «тип» с разными характеристиками:
#   weight  — относительный шанс появления (используется в random.choices)
#   value   — сколько очков даёт монета при подборе
#   color   — цвет прямоугольника-заглушки (если нет отдельных изображений)
#
# Чем больше weight — тем чаще появляется монета.
# Bronze появляется чаще всего, gold — крайне редко.

COIN_TYPES = {
    'bronze': {'weight': 60, 'value': 1,  'color': pygame.Color(180, 100, 40)},
    'silver': {'weight': 30, 'value': 3,  'color': pygame.Color(180, 180, 180)},
    'gold':   {'weight': 10, 'value': 5,  'color': pygame.Color(255, 200, 0)},
}

# Списки для random.choices (порядок должен совпадать)
_coin_names   = list(COIN_TYPES.keys())
_coin_weights = [COIN_TYPES[n]['weight'] for n in _coin_names]


def pick_coin_type():
    """Возвращает название типа монеты с учётом весов."""
    return random.choices(_coin_names, weights=_coin_weights, k=1)[0]


def safe_x_range(enemy_rect):
    """
    Возвращает список допустимых X-координат для монеты,
    исключая зону перекрытия с врагом (чтобы они не спавнились друг на друге).
    """
    ex = enemy_rect.center[0]
    left_range  = range(22, max(22, ex - 24 - 22))
    right_range = range(min(ex + 24 + 22, screen_width - 22), screen_width - 22)
    full = list(chain(left_range, right_range))
    # Если диапазон пустой (враг у края) — берём противоположную сторону
    return full if full else list(range(22, screen_width - 22))


class Coin(pygame.sprite.Sprite):
    def __init__(self, enemy):
        super().__init__()
        # Выбираем тип монеты случайно с учётом весов
        self.coin_type = pick_coin_type()
        self.value     = COIN_TYPES[self.coin_type]['value']
        color          = COIN_TYPES[self.coin_type]['color']

        # Пробуем загрузить отдельное изображение для типа монеты.
        # Если файла нет — рисуем цветной квадрат-заглушку.
        try:
            self.image = pygame.image.load(f"img/coin_{self.coin_type}.png").convert_alpha()
        except FileNotFoundError:
            try:
                self.image = pygame.image.load("img/coin.png").convert_alpha()
                # Тонируем изображение в цвет типа монеты
                tint = pygame.Surface(self.image.get_size(), pygame.SRCALPHA)
                tint.fill((*color[:3], 120))
                self.image.blit(tint, (0, 0))
            except FileNotFoundError:
                # Совсем нет изображений — рисуем круг нужного цвета
                self.image = pygame.Surface((20, 20), pygame.SRCALPHA)
                pygame.draw.circle(self.image, color, (10, 10), 10)

        self.rect = self.image.get_rect()
        self.rect.center = (random.choice(safe_x_range(enemy.rect)), 0)

    def move(self, enemy):
        """Двигает монету вниз. При выходе за экран — респавнит наверху."""
        self.rect.move_ip(0, speed)
        if self.rect.top > screen_height:
            self.coin_type = pick_coin_type()          # новый тип при каждом респавне
            self.value     = COIN_TYPES[self.coin_type]['value']
            self.rect.center = (random.choice(safe_x_range(enemy.rect)), 0)


# ── Создание спрайтов ─────────────────────────────────────────────────────────
P1   = Player()
E1   = Enemy()
coin = Coin(E1)

enemies     = pygame.sprite.Group()
enemies.add(E1)

coins_group = pygame.sprite.Group()
coins_group.add(coin)

car_sprites = pygame.sprite.Group()
car_sprites.add(P1, E1)

all_sprites = pygame.sprite.Group()
all_sprites.add(P1, E1, coin)

# Порог следующего ускорения (растёт на COINS_PER_SPEEDUP после каждого спидапа)
next_speedup_threshold = COINS_PER_SPEEDUP


# ── Главный игровой цикл ──────────────────────────────────────────────────────
while loop:

    # Обработка событий
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            loop = False

    # Рисуем фон
    screen.blit(background, (0, 0))

    # ── HUD: счёт и монеты ────────────────────────────────────────────────────
    scores_surf      = font_small.render(f"Score: {score}", True, black)
    coin_surf        = font_small.render(f"Coins: {coin_score}", True, black)
    speed_surf       = font_small.render(f"Speed: {speed}", True, black)

    screen.blit(scores_surf, (10, 10))
    screen.blit(coin_surf,   (screen_width - 120, 10))  # правый верхний угол
    screen.blit(speed_surf,  (10, 30))

    # Подсказка о следующем ускорении
    next_surf = font_small.render(
        f"Next boost: {next_speedup_threshold - coin_score} coins", True, blue)
    screen.blit(next_surf, (10, 50))

    # ── Движение и отрисовка спрайтов ────────────────────────────────────────
    for entity in car_sprites:
        screen.blit(entity.image, entity.rect)
        entity.move()

    # Двигаем и рисуем монету
    screen.blit(coin.image, coin.rect)
    coin.move(E1)

    # ── Проверка столкновения с врагом → Game Over ────────────────────────────
    if pygame.sprite.spritecollideany(P1, enemies):
        try:
            pygame.mixer.Sound("C:/Users/makha/OneDrive/Desktop/PP2-Practices/Practice-10/Racer/sound/crash.wav").play()
        except Exception:
            pass
        time.sleep(1)

        screen.fill(red)
        screen.blit(game_over_text, (30, 200))

        # Итоговые очки на экране game over
        final = font_small.render(
            f"Score: {score}   Coins: {coin_score}", True, black)
        screen.blit(final, (60, 300))
        pygame.display.update()

        for entity in all_sprites:
            entity.kill()
        time.sleep(2)
        pygame.quit()
        break

    # ── Подбор монеты ─────────────────────────────────────────────────────────
    hit_coins = pygame.sprite.spritecollide(P1, coins_group, dokill=True)
    if hit_coins:
        for hit in hit_coins:
            # Добавляем очки согласно весу (ценности) монеты
            coin_score += hit.value

        try:
            pygame.mixer.Sound("C:/Users/makha/OneDrive/Desktop/PP2-Practices/Practice-10/Racer/sound/getcoin.mp3").play()
        except Exception:
            pass

        # Создаём новую монету взамен подобранной
        coin = Coin(E1)
        coins_group.add(coin)
        all_sprites.add(coin)

        # ── Проверка: нужно ли ускорить врага? ──────────────────────────────
        # Скорость растёт каждый раз, когда coin_score достигает порога
        if coin_score >= next_speedup_threshold and speed < MAX_SPEED:
            speed += SPEED_INCREMENT
            next_speedup_threshold += COINS_PER_SPEEDUP  # двигаем следующий порог

            # Кратко показываем сообщение об ускорении
            boost_surf = font_small.render("SPEED UP!", True, red)
            screen.blit(boost_surf, (screen_width // 2 - 50, screen_height // 2))
            pygame.display.flip()
            time.sleep(0.5)

    # Обновляем экран
    try:
        pygame.display.flip()
    except Exception:
        print("Game Over!")
        loop = False

    clock.tick(60)