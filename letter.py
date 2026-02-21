import pygame
from constants import SLOT_WIDTH, SLOT_HEIGHT


class Letter:
    def __init__(self, x, y, font):
        self.rect = pygame.Rect(x, y, SLOT_WIDTH, SLOT_HEIGHT)
        self.letter = None
        self.font = font

    def draw(self, screen):
        pygame.draw.rect(screen, 'white', self.rect, 2)
        if self.letter:
            surface = self.font.render(self.letter, True, 'white')
            letter_rect = surface.get_rect(center=self.rect.center)
            screen.blit(surface, letter_rect)
