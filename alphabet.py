import pygame
from constants import SLOT_WIDTH, SLOT_HEIGHT, GAP


class Alphabet:
    def __init__(self, font, screen_width, screen_height):
        self.font = font
        self.guessed = set()

        total_width = 26 * SLOT_WIDTH + 25 * GAP
        start_x = (screen_width - total_width) // 2
        y = screen_height - SLOT_HEIGHT - 20

        self.slots = {}
        for i, char in enumerate('ABCDEFGHIJKLMNOPQRSTUVWXYZ'):
            x = start_x + i * (SLOT_WIDTH + GAP)
            self.slots[char] = pygame.Rect(x, y, SLOT_WIDTH, SLOT_HEIGHT)

    def guess(self, letter):
        self.guessed.add(letter.upper())

    def draw(self, screen):
        for char, rect in self.slots.items():
            if char in self.guessed:
                surface = self.font.render(char, True, 'grey')
            else:
                surface = self.font.render(char, True, 'white')
            letter_rect = surface.get_rect(center=rect.center)
            screen.blit(surface, letter_rect)
