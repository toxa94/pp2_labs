import pygame
import sys

# Initialize pygame
pygame.init()

# Screen settings
WIDTH, HEIGHT = 600, 400
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Moving Ball Game")

# Colors
WHITE = (255, 255, 255)
RED = (255, 0, 0)

# Ball settings
radius = 25
x, y = WIDTH // 2, HEIGHT // 2
step = 20

clock = pygame.time.Clock()

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.KEYDOWN:
            # Move with boundaries check
            if event.key == pygame.K_LEFT:
                if x - step - radius >= 0:
                    x -= step
            if event.key == pygame.K_RIGHT:
                if x + step + radius <= WIDTH:
                    x += step
            if event.key == pygame.K_UP:
                if y - step - radius >= 0:
                    y -= step
            if event.key == pygame.K_DOWN:
                if y + step + radius <= HEIGHT:
                    y += step

    # Draw
    screen.fill(WHITE)
    pygame.draw.circle(screen, RED, (x, y), radius)

    pygame.display.flip()
    clock.tick(60)