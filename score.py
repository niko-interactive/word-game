import pygame


class Score:
    """
    Draws the streak counter, coin balance, and star count in the top left corner.
    State (streak_count, money, stars) is owned by GameManager — this class only handles display.
    Stars are a meta-currency that never resets on loss, earned at a rate of 1 per 10 rounds completed.
    The stars row is hidden until stars_display_unlocked is set in GameManager, after which it is
    always visible regardless of current star balance, losses, or spending.
    """

    def __init__(self, font):
        self.font = font
        # Measure the widest label once so numbers always line up in a fixed column.
        # 'STREAK' is the longest label — value_x is set just past it with a small gap.
        self._value_x = font.size('STREAK  ')[0] + 20

    def draw(self, screen, streak_count, money, stars, stars_display_unlocked):
        """Draw the streak counter, coin balance, and optionally the star count."""
        vx = self._value_x

        screen.blit(self.font.render('STREAK', True, 'white'), (20, 20))
        screen.blit(self.font.render(str(streak_count), True, 'white'), (vx, 20))

        screen.blit(self.font.render('MONEY', True, 'green'), (20, 60))
        screen.blit(self.font.render(str(money), True, 'green'), (vx, 60))

        # Stars row is permanently visible once unlocked — spending all stars or losing
        # does not hide it. The flag is set on first star earned and never unset.
        if stars_display_unlocked:
            screen.blit(self.font.render('STARS', True, 'gold'), (20, 100))
            screen.blit(self.font.render(str(stars), True, 'gold'), (vx, 100))