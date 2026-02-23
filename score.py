import pygame


class Score:
    """
    Draws the streak counter, coin balance, and star count in the top left corner.
    Reads all state directly from manager — no data needs to be passed into draw().

    Stars display shows spendable stars plus a (+n) buffer indicator when pending
    stars are waiting to be converted via prestige. The row is hidden until the
    player first earns a buffer star (reaches streak round 10).
    """

    def __init__(self, font):
        self.font = font
        self.manager = None
        # Measure the widest label once so numbers always line up in a fixed column.
        self._value_x = font.size('STREAK  ')[0] + 20

    def draw(self, screen):
        """Draw streak, money, and optionally the star row."""
        if not self.manager:
            return
        vx = self._value_x
        m  = self.manager

        screen.blit(self.font.render('STREAK', True, 'white'), (20, 20))
        screen.blit(self.font.render(str(m.streak_count), True, 'white'), (vx, 20))

        screen.blit(self.font.render('MONEY', True, 'green'), (20, 60))
        screen.blit(self.font.render(str(m.money), True, 'green'), (vx, 60))

        # Stars row appears once the first milestone is reached and never hides again.
        # Shows spendable stars and, if any are pending in the buffer, a (+n) indicator.
        if m.stars_display_unlocked:
            screen.blit(self.font.render('STARS', True, 'gold'), (20, 100))
            star_text = str(m.stars)
            if m.star_buffer > 0:
                star_text += f' (+{m.star_buffer})'
            screen.blit(self.font.render(star_text, True, 'gold'), (vx, 100))