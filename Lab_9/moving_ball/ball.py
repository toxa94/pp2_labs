import pygame

class Ball:
    def __init__(self, x, y, radius, step, screen_width, screen_height):
        self.x = x
        self.y = y
        self.radius = radius
        self.step = step
        self.screen_width = screen_width
        self.screen_height = screen_height

    def move(self, key):
        if key == pygame.K_LEFT:
            if self.x - self.step - self.radius >= 0:
                self.x -= self.step

        elif key == pygame.K_RIGHT:
            if self.x + self.step + self.radius <= self.screen_width:
                self.x += self.step

        elif key == pygame.K_UP:
            if self.y - self.step - self.radius >= 0:
                self.y -= self.step

        elif key == pygame.K_DOWN:
            if self.y + self.step + self.radius <= self.screen_height:
                self.y += self.step

    def draw(self, screen):
        pygame.draw.circle(screen, (255, 0, 0), (self.x, self.y), self.radius)