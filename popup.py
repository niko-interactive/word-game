import pygame


class Popup:
    def __init__(self, message, font, screen_width, screen_height):
        self.font = font
        self.message = message

        self.rect = pygame.Rect(0, 0, 400, 250)
        self.rect.center = (screen_width // 2, screen_height // 2)

        self.button_rect = pygame.Rect(0, 0, 160, 48)
        self.button_rect.centerx = self.rect.centerx
        self.button_rect.bottom = self.rect.bottom - 20

    def handle_click(self, pos):
        return self.button_rect.collidepoint(pos)

    def draw(self, screen):
        pygame.draw.rect(screen, 'black', self.rect)
        pygame.draw.rect(screen, 'white', self.rect, 2)

        msg_surface = self.font.render(self.message, True, 'white')
        msg_rect = msg_surface.get_rect(centerx=self.rect.centerx, top=self.rect.top + 40)
        screen.blit(msg_surface, msg_rect)

        pygame.draw.rect(screen, 'black', self.button_rect)
        pygame.draw.rect(screen, 'white', self.button_rect, 2)
        btn_surface = self.font.render('Play Again', True, 'white')
        btn_rect = btn_surface.get_rect(center=self.button_rect.center)
        screen.blit(btn_surface, btn_rect)
