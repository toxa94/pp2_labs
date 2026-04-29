import pygame
import os
import datetime
from pygame.math import Vector2

class MickeyClock:
    def __init__(self, screen):
        self.screen = screen
        self.center = (screen.get_width() // 2, screen.get_height() // 2)

        self._image_library = {}

        # Пути
        self.base_path = "C:/Users/makha/OneDrive/Desktop/PP2-Practices/Practice-09/img/"

        # Load images
        self.bg = pygame.transform.scale(
            self.get_image("mainclock.png"),
            (1200, 800)
        )

        self.left_arm = pygame.transform.scale(
            self.get_image("leftarm.png"),
            (100, 260)
        )

        self.right_arm = pygame.transform.scale(
            self.get_image("rightarm.png"),
            (120, 300)
        )

    def get_image(self, name):
        path = os.path.join(self.base_path, name)
        image = self._image_library.get(path)

        if image is None:
            image = pygame.image.load(path)
            self._image_library[path] = image

        return image

    def rotate_hand(self, image, angle, pivot):
        w, h = image.get_size()

        # под твои PNG
        offset = Vector2(0, -h // 2 + 80)

        rotated_image = pygame.transform.rotate(image, angle)
        rotated_offset = offset.rotate(-angle)

        rect = rotated_image.get_rect(center=pivot + rotated_offset)
        return rotated_image, rect

    def draw(self):
        self.screen.blit(self.bg, (0, 0))

        now = datetime.datetime.now()
        minutes = now.minute
        seconds = now.second

        # угол
        minute_angle = -(minutes * 6) - 90
        second_angle = -(seconds * 6) - 90

        pivot = Vector2(self.center)

        minute_hand, minute_rect = self.rotate_hand(
            self.right_arm,
            minute_angle,
            pivot
        )

        second_hand, second_rect = self.rotate_hand(
            self.left_arm,
            second_angle,
            pivot
        )

        self.screen.blit(minute_hand, minute_rect)
        self.screen.blit(second_hand, second_rect)