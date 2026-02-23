import pygame


class Score:
    """
    Draws the streak counter, coin balance, and star count in the top left corner.
    Reads all state directly from manager — no data needs to be passed into draw().
    """

    def __init__(self, font):
        self.font = font
        self.manager = None
        # Measure the widest label once so numbers always line up in a fixed column.
        # 'STREAK' is the longest label — value_x is set just past it with a small gap.
        self._value_x = font.size('STREAK  ')[0] + 20

    def draw(self, screen):
        """Draw the streak counter, coin balance, and optionally the star count."""
        if not self.manager:
            return
        vx = self._value_x
        m  = self.manager

        screen.blit(self.font.render('STREAK', True, 'white'), (20, 20))
        screen.blit(self.font.render(str(m.streak_count), True, 'white'), (vx, 20))

        screen.blit(self.font.render('MONEY', True, 'green'), (20, 60))
        screen.blit(self.font.render(str(m.money), True, 'green'), (vx, 60))

        # Stars row is permanently visible once unlocked — spending all stars or losing
        # does not hide it. The property derives its value from live state.
        if m.stars_display_unlocked:
            screen.blit(self.font.render('STARS', True, 'gold'), (20, 100))
            screen.blit(self.font.render(str(m.stars), True, 'gold'), (vx, 100))