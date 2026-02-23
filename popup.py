import pygame


class Popup:
    """
    Modal overlay shown at the end of a round.
    Displays a win or lose message, the secret phrase, and optionally
    the player's final streak if they lost. Contains a Play Again button
    to start the next round.

    game_complete=True is used for the special "You Beat the Game!" screen
    shown when the player clears every puzzle in a run. It omits the phrase
    and streak, and the Play Again button resets everything from scratch.
    """

    def __init__(self, message, font, screen_width, screen_height,
                 phrase='', streak=None, game_complete=False, lost_star_buffer=0,
                 prestige=False, star_buffer=0, can_prestige=False, prestige_unlock_streak=50):
        self.font = font
        self.small_font = pygame.font.SysFont('Arial', 22)
        self.message = message
        self.phrase = phrase
        self.streak = streak
        self.game_complete = game_complete
        self.lost_star_buffer = lost_star_buffer
        self.prestige = prestige
        self.star_buffer = star_buffer
        self.can_prestige = can_prestige
        self.prestige_unlock_streak = prestige_unlock_streak

        popup_width = 600
        padding = 40
        self.max_text_width = popup_width - padding * 2

        # Pre-wrap the phrase into lines that fit the popup width
        self.phrase_lines = self._wrap_text(phrase, self.font, self.max_text_width)

        # Calculate height dynamically based on content
        if prestige:
            # Prestige popup: title + up to 6 small lines + buttons
            line_h = pygame.font.SysFont('Arial', 22).get_height() + 6
            n_lines = 5 if can_prestige else 6
            total_height = 24 + self.font.get_height() + 16 + (n_lines * line_h) + 20 + 48 + 20
            total_height = max(300, total_height)
        else:
            phrase_height = len(self.phrase_lines) * (self.font.get_height() + 4)
            streak_height = (self.font.get_height() + 10) if streak is not None else 0
            buffer_height = (self.font.get_height() + 10) if lost_star_buffer > 0 else 0
            content_height = 30 + self.font.get_height() + 10 + phrase_height + streak_height + buffer_height + 20
            total_height = max(250, content_height + 63)  # 63 = button height + margins

        self.rect = pygame.Rect(0, 0, popup_width, total_height)
        self.rect.center = (screen_width // 2, screen_height // 2)

        self.button_rect = pygame.Rect(0, 0, 160, 48)
        self.button_rect.centerx = self.rect.centerx
        self.button_rect.bottom = self.rect.bottom - 15

        # Yes/No buttons used in prestige confirm mode — side by side
        btn_w, btn_h, btn_gap = 160, 48, 20
        self.confirm_rect = pygame.Rect(self.rect.centerx + btn_gap // 2,         self.rect.bottom - 15 - btn_h, btn_w, btn_h)
        self.cancel_rect  = pygame.Rect(self.rect.centerx - btn_gap // 2 - btn_w, self.rect.bottom - 15 - btn_h, btn_w, btn_h)

    def _wrap_text(self, text, font, max_width):
        """Split text into lines that fit within max_width pixels."""
        if not text:
            return []
        words = text.split(' ')
        lines = []
        current_line = []
        for word in words:
            test_line = ' '.join(current_line + [word])
            if font.size(test_line)[0] <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        if current_line:
            lines.append(' '.join(current_line))
        return lines

    def _draw_prestige(self, screen):
        """Draw the prestige popup — locked info or confirm screen depending on can_prestige."""
        pygame.draw.rect(screen, 'black', self.rect)
        pygame.draw.rect(screen, 'gold',  self.rect, 2)

        cx = self.rect.centerx
        y  = self.rect.top + 24

        title = self.font.render('PRESTIGE', True, 'gold')
        screen.blit(title, title.get_rect(centerx=cx, top=y))
        y += title.get_height() + 16

        if self.can_prestige:
            star_word = "star" if self.star_buffer == 1 else "stars"
            lines = [
                (f'You have {self.star_buffer} {star_word} ready to claim.', 'white'),
                ('Prestiging resets your run — streak, money,',              '#aaaaaa'),
                ('and upgrades — but you keep your stars.',                  '#aaaaaa'),
                ('',                                                          'white'),
                (f'Current streak: {self.streak}',                           'white'),
            ]
        else:
            needed = self.prestige_unlock_streak - (self.streak or 0)
            lines = [
                ('Prestige is locked.',                                        'white'),
                (f'Reach streak {self.prestige_unlock_streak} to unlock.',    '#aaaaaa'),
                (f'({needed} round{"s" if needed != 1 else ""} to go)',       '#aaaaaa'),
                ('',                                                           'white'),
                (f'Stars waiting in buffer: {self.star_buffer}',              'gold'),
                ('These will be lost if you lose first.',                      '#888888'),
            ]

        for text, color in lines:
            s = self.small_font.render(text, True, color)
            screen.blit(s, s.get_rect(centerx=cx, top=y))
            y += s.get_height() + 6

        if self.can_prestige:
            # Yes button
            pygame.draw.rect(screen, 'black', self.confirm_rect)
            pygame.draw.rect(screen, 'gold',  self.confirm_rect, 2)
            cs = self.font.render('Yes', True, 'gold')
            screen.blit(cs, cs.get_rect(center=self.confirm_rect.center))
            # No button
            pygame.draw.rect(screen, 'black',   self.cancel_rect)
            pygame.draw.rect(screen, '#666666', self.cancel_rect, 2)
            ns = self.font.render('No', True, '#aaaaaa')
            screen.blit(ns, ns.get_rect(center=self.cancel_rect.center))
        else:
            pygame.draw.rect(screen, 'black', self.button_rect)
            pygame.draw.rect(screen, 'gold',  self.button_rect, 2)
            cs = self.font.render('Close', True, 'gold')
            screen.blit(cs, cs.get_rect(center=self.button_rect.center))

    def handle_click(self, pos):
        """Return True if the Play Again/Close button was clicked, 'confirm' for prestige confirm, 'cancel' for No."""
        if self.prestige and self.can_prestige:
            if self.confirm_rect.collidepoint(pos):
                return 'confirm'
            if self.cancel_rect.collidepoint(pos):
                return 'cancel'
        return self.button_rect.collidepoint(pos)

    def draw(self, screen):
        """
        Draw the popup box, win/lose message, secret phrase, optional
        streak count, and the Play Again button.
        """
        # Background and border
        pygame.draw.rect(screen, 'black', self.rect)
        pygame.draw.rect(screen, 'white', self.rect, 2)

        # Prestige popup — entirely separate layout
        if self.prestige:
            self._draw_prestige(screen)
            return

        # Win/lose/complete message
        msg_color = 'gold' if self.game_complete else 'white' 
        msg_surface = self.font.render(self.message, True, msg_color)
        msg_rect = msg_surface.get_rect(centerx=self.rect.centerx, top=self.rect.top + 30)
        screen.blit(msg_surface, msg_rect)

        next_top = msg_rect.bottom + 10

        if self.game_complete:
            # Congratulatory subtext
            sub_surface = self.small_font.render("You've solved every puzzle. Consider going outside...", True, 'green')
            sub_rect = sub_surface.get_rect(centerx=self.rect.centerx, top=next_top)
            screen.blit(sub_surface, sub_rect)

            if self.streak is not None:
                streak_surface = self.font.render(f'Streak: {self.streak}', True, 'white')
                streak_rect = streak_surface.get_rect(centerx=self.rect.centerx,
                                                      top=next_top + 40)
                screen.blit(streak_surface, streak_rect)

        else:
            # Secret phrase shown in grey below the message, wrapped to fit
            y = next_top
            for line in self.phrase_lines:
                line_surface = self.font.render(line, True, 'grey')
                line_rect = line_surface.get_rect(centerx=self.rect.centerx, top=y)
                screen.blit(line_surface, line_rect)
                y += self.font.get_height() + 4

            # Final streak count
            if self.streak is not None:
                streak_surface = self.font.render(f'Streak: {self.streak}', True, 'white')
                streak_rect = streak_surface.get_rect(centerx=self.rect.centerx, top=y + 6)
                screen.blit(streak_surface, streak_rect)
                y = streak_rect.bottom + 6

            # Lost star buffer warning
            if self.lost_star_buffer > 0:
                star_label = f'Stars lost: {self.lost_star_buffer}'
                star_surface = self.font.render(star_label, True, 'gold')
                star_rect = star_surface.get_rect(centerx=self.rect.centerx, top=y + 6)
                screen.blit(star_surface, star_rect)

        # Play Again button
        pygame.draw.rect(screen, 'black', self.button_rect)
        pygame.draw.rect(screen, 'white', self.button_rect, 2)
        btn_label = 'New Game' if self.game_complete else 'Play Again'
        btn_surface = self.font.render(btn_label, True, 'white')
        btn_rect = btn_surface.get_rect(center=self.button_rect.center)
        screen.blit(btn_surface, btn_rect)