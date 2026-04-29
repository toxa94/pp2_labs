import pygame
import sys
from player import MusicPlayer
import os

pygame.init()

WIDTH, HEIGHT = 700, 400
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Music Player")

font_big = pygame.font.SysFont(None, 40)
font_small = pygame.font.SysFont(None, 28)

playlist = [
    "music/Let it happen.wav",
    "music/NEW PERSON,SAME MISTAKES.wav"
]

player = MusicPlayer(playlist)

WHITE = (245, 245, 245)
BLACK = (30, 30, 30)
GRAY = (180, 180, 180)
GREEN = (0, 200, 0)

clock = pygame.time.Clock()

def format_time(seconds):
    seconds = int(seconds)
    minutes = seconds // 60
    seconds = seconds % 60
    return f"{minutes:02}:{seconds:02}"

def get_track_name(path):
    return os.path.basename(path)

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p:
                player.play()

            elif event.key == pygame.K_s:
                player.stop()

            elif event.key == pygame.K_n:
                player.next_track()

            elif event.key == pygame.K_b:
                player.previous_track()

            elif event.key == pygame.K_SPACE:
                player.pause_resume()

    screen.fill(WHITE)

    # 🎵 Track name
    track_name = get_track_name(player.get_current_track())
    text_track = font_big.render(track_name, True, BLACK)
    screen.blit(text_track, (50, 60))

    # 📊 Progress
    length = player.get_length()
    position = player.get_position()

    if length > 0:
        ratio = min(position / length, 1)
    else:
        ratio = 0

    bar_width = 500
    current_width = int(bar_width * ratio)

    pygame.draw.rect(screen, GRAY, (50, 150, bar_width, 10))
    pygame.draw.rect(screen, GREEN, (50, 150, current_width, 10))

    # ⏱ TIME
    time_text = font_small.render(
        f"{format_time(position)} / {format_time(length)}",
        True,
        BLACK
    )
    screen.blit(time_text, (50, 180))

    # 🟢 Status
    if player.is_paused:
        status = "Paused"
    elif player.is_playing:
        status = "Playing"
    else:
        status = "Stopped"

    text_status = font_small.render(f"Status: {status}", True, GREEN)
    screen.blit(text_status, (50, 220))

    # ⌨ Controls
    controls = [
        "P - Play",
        "S - Stop",
        "SPACE - Pause/Resume",
        "N - Next",
        "B - Back"
    ]

    for i, c in enumerate(controls):
        txt = font_small.render(c, True, BLACK)
        screen.blit(txt, (50, 260 + i * 25))

    pygame.display.flip()
    clock.tick(60)