import pygame


BTN_WIDTH  = 200
BTN_HEIGHT = 48
BTN_GAP    = 20
BTN_TOP    = 20


class MenuBar:
    """
    Owns and draws all top-center menu buttons (Shop, Prestige, etc.).
    Buttons are centered horizontally as a group regardless of how many
    are currently visible. New buttons can be added by appending to the
    _buttons list and implementing their visibility/click logic here.

    The bar reads all visibility state directly from manager via self.manager.
    shop.visible is still toggled here so the shop popup continues to work.
    """

    def __init__(self, font, screen_width, shop):
        self.font         = font
        self.small_font   = pygame.font.SysFont('Arial', 20)
        self.screen_width = screen_width
        self.shop         = shop
        self.manager      = None  # Set by main.py after GameManager is created

        # Each entry: (id, label, always_visible, gold_style)
        # Visibility for non-always buttons is checked dynamically in _visible_buttons()
        self._button_defs = [
            ('shop',     'Shop',     True,  False),
            ('prestige', 'Prestige', False, True),
            ('debug_money', 'Debug', False, False),  # Debug only — remove before release
        ]

        # Rects are rebuilt each frame in draw() and stored for hit-testing in handle_click()
        self._rects = {}

    def _visible_buttons(self):
        """Return list of (id, label, gold) for buttons that should currently be shown."""
        result = []
        for btn_id, label, always, gold in self._button_defs:
            if always:
                result.append((btn_id, label, gold))
            elif btn_id == 'prestige' and self.manager and self.manager.star_buffer > 0:
                result.append((btn_id, label, gold))
            elif btn_id == 'debug_money':
                result.append((btn_id, label, gold))  # Always visible for testing
        return result

    def _build_rects(self, visible):
        """Compute and return centred rects for the given visible button list."""
        n           = len(visible)
        total_width = n * BTN_WIDTH + (n - 1) * BTN_GAP
        start_x     = (self.screen_width - total_width) // 2
        rects = {}
        for i, (btn_id, _, _) in enumerate(visible):
            x = start_x + i * (BTN_WIDTH + BTN_GAP)
            rects[btn_id] = pygame.Rect(x, BTN_TOP, BTN_WIDTH, BTN_HEIGHT)
        return rects

    def handle_click(self, pos):
        """
        Handle a click on any menu button. Returns the id of the button clicked,
        or None if no button was hit.
        """
        for btn_id, rect in self._rects.items():
            if rect.collidepoint(pos):
                if btn_id == 'shop':
                    self.shop.visible = not self.shop.visible
                return btn_id
        return None

    def draw(self, screen):
        """Draw all visible buttons centred at the top of the screen."""
        visible = self._visible_buttons()
        self._rects = self._build_rects(visible)

        for btn_id, label, gold in visible:
            rect = self._rects[btn_id]

            if gold:
                can_prestige = self.manager and self.manager.can_prestige
                border = 'gold'    if can_prestige else '#666600'
                fill   = '#221100' if can_prestige else 'black'
                color  = 'gold'    if can_prestige else '#886600'
            else:
                border = 'white'
                fill   = 'black'
                color  = 'white'

            pygame.draw.rect(screen, fill,   rect)
            pygame.draw.rect(screen, border, rect, 2)
            surf = self.font.render(label, True, color)
            screen.blit(surf, surf.get_rect(center=rect.center))

        # Active consumable status shown below the shop button
        if self.manager and 'shop' in self._rects:
            shop_rect = self._rects['shop']
            status_y  = shop_rect.bottom + 6
            if self.manager.free_guess_active:
                fg_surf = self.small_font.render('FREE GUESS ACTIVE', True, 'green')
                screen.blit(fg_surf, fg_surf.get_rect(centerx=shop_rect.centerx, top=status_y))
                status_y += fg_surf.get_height() + 2
            if self.manager.bonus_strikes > 0:
                bs_surf = self.small_font.render(f'BONUS STRIKES: {self.manager.bonus_strikes}', True, 'green')
                screen.blit(bs_surf, bs_surf.get_rect(centerx=shop_rect.centerx, top=status_y))