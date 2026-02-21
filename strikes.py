import pygame
from constants import SLOT_WIDTH, SLOT_HEIGHT, GAP


class Strikes:
    def __init__(self, font, screen_width, max_strikes=3):
        self.font = font
        self.max_strikes = max_strikes
        self.count = 0

        total_width = max_strikes * SLOT_WIDTH + (max_strikes - 1) * GAP
        start_x = screen_width - total_width - 20
        y = 20

        self.rects = []
        for i in range(max_strikes):
            x = start_x + i * (SLOT_WIDTH + GAP)
            self.rects.append(pygame.Rect(x, y, SLOT_WIDTH, SLOT_HEIGHT))

    def add_strike(self):
        self.count += 1

    def is_game_over(self):
        return self.count >= self.max_strikes

    def draw(self, screen):
        for i, rect in enumerate(self.rects):
            color = 'red' if i < self.count else 'white'
            surface = self.font.render('X', True, color)
            x_rect = surface.get_rect(center=rect.center)
            screen.blit(surface, x_rect)
