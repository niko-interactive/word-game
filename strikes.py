import pygame
from constants import LETTER_SLOT_WIDTH, LETTER_SLOT_HEIGHT, GAP


class Strikes:
    """
    Tracks and displays the player's strikes for the current round.
    Shows a row of X marks in the top right corner (red = used, white = remaining).
    Bonus strikes visually heal red X's back to white. Any overflow beyond all
    used strikes is shown as a '+N bonus' counter below the row.
    Max strikes can increase via upgrades.
    """

    def __init__(self, font, screen_width, max_strikes=3):
        self.font       = font
        self.small_font = pygame.font.SysFont("Arial", 20)
        self.screen_width = screen_width
        self.max_strikes = max_strikes
        self.count = 0

    def _build_slots(self, num_slots):
        """Build a list of rects for num_slots X marks, flush to the top right."""
        total_width = num_slots * LETTER_SLOT_WIDTH + (num_slots - 1) * GAP
        start_x = self.screen_width - total_width - 20
        y = 20
        return [
            pygame.Rect(start_x + i * (LETTER_SLOT_WIDTH + GAP), y, LETTER_SLOT_WIDTH, LETTER_SLOT_HEIGHT)
            for i in range(num_slots)
        ]

    def add_strike(self):
        """Add one strike after a wrong guess."""
        self.count += 1

    def is_game_over(self):
        """Return True if the player has used all their strikes."""
        return self.count >= self.max_strikes

    def draw(self, screen, bonus_strikes=0, free_guess_active=False):
        """
        Draw the strike row flush to the top-right, then status text below it.

        Bonus strikes first heal used (red) slots visually, turning them white.
        Any bonus strikes left over after all used slots are healed are shown as
        a '+N bonus' counter below the row, right-aligned to match.
        Free guess indicator also sits below the row if active.
        """
        slots = self._build_slots(self.max_strikes)

        # How many used strikes are visually healed by bonus strikes
        healed = min(bonus_strikes, self.count)

        for i, rect in enumerate(slots):
            used = i < self.count
            is_healed = used and i >= (self.count - healed)
            if is_healed:
                color = 'white'
            elif used:
                color = 'red'
            else:
                color = 'white'
            surface = self.font.render('X', True, color)
            screen.blit(surface, surface.get_rect(center=rect.center))

        # Text indicators below the strike row, right-aligned

        small_font = self.small_font
        right_x    = slots[-1].right
        text_y     = slots[-1].bottom + 6

        overflow = bonus_strikes - healed
        if overflow > 0:
            surf = small_font.render(f'+{overflow} BONUS STRIKE', True, 'green')
            screen.blit(surf, surf.get_rect(right=right_x, top=text_y))
            text_y += surf.get_height() + 2

        if free_guess_active:
            surf = small_font.render('FREE GUESS', True, 'green')
            screen.blit(surf, surf.get_rect(right=right_x, top=text_y))