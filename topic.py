import pygame


class Topic:
    def __init__(self, topic, font, screen_width, screen_height):
        self.font = font
        self.topic = topic.upper()
        self.screen_width = screen_width
        self.screen_height = screen_height

        self.rect = pygame.Rect(20, 20, 300, 48)

    def draw(self, screen):
        pygame.draw.rect(screen, 'black', self.rect)
        surface = self.font.render(self.topic, True, 'white')
        topic_rect = surface.get_rect(midleft=(self.rect.left + 10, self.rect.centery))
        screen.blit(surface, topic_rect)
