import pygame

from shop_items import UPGRADES, CONSUMABLES
from secret_shop_items import SECRET_ITEMS


ROW_HEIGHT = 52
BTN_WIDTH = 80
BTN_HEIGHT = 36

SECRET_UNLOCK_COST = 5  # Stars required to unlock the secret tab


class Shop:
    """
    Manages the shop UI and purchase rules for upgrades, consumables, and secret items.
    Upgrades are permanent until the player loses.
    Consumables are purchased and used immediately.
    Secret items cost stars (*) and are permanently unlocked across losses.

    The secret tab is invisible until the player has at least 1 star, then visible
    but locked. Clicking it while locked spends 5 stars to unlock it permanently.
    Once unlocked, it behaves like a normal tab.

    Money and purchased_upgrades are owned by GameManager. The shop reads
    them via manager references and never tracks them itself. Consumable
    effects are registered as callbacks by GameManager each round.

    The content area of each tab scrolls independently. Adding a new tab
    means adding a key to self.scroll_offsets and a branch in the draw/click
    methods — the scroll infrastructure handles the rest automatically.
    """

    def __init__(self, font, screen_width, screen_height):
        self.font = font
        self.small_font = pygame.font.SysFont('Arial', 20)
        self.screen_width = screen_width
        self.screen_height = screen_height

        self.free_guess_active = False   # kept temporarily for draw indicator — read from manager instead
        self.visible = False
        self.active_tab = 'upgrades'     # 'upgrades', 'consumables', or 'secret'

        # Per-tab scroll offsets in pixels — add a key here when adding a new tab
        self.scroll_offsets = {
            'upgrades':    0,
            'consumables': 0,
            'secret':      0,
        }

        # Set by GameManager each round — called when a consumable is purchased
        self.on_reveal_consonant = None
        self.on_reveal_vowel     = None
        self.on_eliminate_letters = None
        self.on_free_guess       = None
        self.on_bonus_strike     = None

        # Set by main.py after GameManager is created
        self.manager = None

        # Shop button centered at the top of the screen
        self.button_rect = pygame.Rect(0, 0, 160, 48)
        self.button_rect.centerx = screen_width // 2
        self.button_rect.top = 20

        # Popup centered on screen
        self.popup_rect = pygame.Rect(0, 0, 600, 480)
        self.popup_rect.center = (screen_width // 2, screen_height // 2)

        # Tab dimensions — rects are computed dynamically in _build_tab_rects()
        # so that the visible tabs stay centred whether the secret tab is shown or not.
        self.tab_width  = 140
        self.tab_height = 36
        self.tab_gap    = 16
        self.tab_y      = self.popup_rect.top + 55

        # Scrollable content area — sits below the tab row, above the close button.
        # Inset by 2px on each side to stay inside the popup border.
        self.content_top    = self.popup_rect.top + 110
        self.content_bottom = self.popup_rect.bottom - 65  # leaves room for close button
        self.content_height = self.content_bottom - self.content_top
        self.content_rect   = pygame.Rect(
            self.popup_rect.left + 2,
            self.content_top,
            self.popup_rect.width - 4,
            self.content_height,
        )

        # Close button centered at the bottom of the popup
        self.close_rect = pygame.Rect(0, 0, 120, 40)
        self.close_rect.centerx = self.popup_rect.centerx
        self.close_rect.bottom  = self.popup_rect.bottom - 15

    # --- State ---

    def reset(self):
        """Reset consumable state on a loss. Upgrades and round state reset by GameManager."""
        pass

    def _secret_visible(self):
        """
        Secret tab appears once the player has at least 1 star, and stays visible
        permanently after that — including after unlocking (which spends stars to 0)
        and after losing runs. Tied to stars_display_unlocked so it never disappears.
        """
        return self.manager and (
            self.manager.secret_shop_unlocked
            or self.manager.stars_display_unlocked
        )

    def _secret_unlocked(self):
        """Secret tab is unlocked (enterable) once the player has spent 5 stars on it."""
        return self.manager and self.manager.secret_shop_unlocked


    def _build_tab_rects(self):
        """
        Build and return tab rects centred in the popup for however many tabs are
        currently visible. Always includes upgrades and consumables. Adds secret
        only when _secret_visible() is True, keeping visible tabs centred whether
        or not the secret tab has appeared yet.
        """
        visible_tabs = ["upgrades", "consumables"]
        if self._secret_visible():
            visible_tabs.append("secret")
        n = len(visible_tabs)
        total_width = self.tab_width * n + self.tab_gap * (n - 1)
        start_x = self.popup_rect.left + (self.popup_rect.width - total_width) // 2
        return {
            tab_id: pygame.Rect(
                start_x + i * (self.tab_width + self.tab_gap),
                self.tab_y,
                self.tab_width,
                self.tab_height,
            )
            for i, tab_id in enumerate(visible_tabs)
        }

    def _visible_upgrades(self, purchased_upgrades):
        """Return upgrades that should be visible — prereq must be purchased first."""
        return [u for u in UPGRADES
                if u['requires'] is None or u['requires'] in purchased_upgrades]

    def is_upgrade_available(self, upgrade, purchased_upgrades):
        """Return True if the upgrade can be purchased — not already owned and prereq met."""
        if upgrade['id'] in purchased_upgrades:
            return False
        if upgrade['requires'] and upgrade['requires'] not in purchased_upgrades:
            return False
        return True

    def _is_consumable_disabled(self, consumable_id):
        """
        Return True if a consumable should be blocked from purchase.
        Checks both hard rules (caps, active state) and whether the effect
        would actually do anything given the current phrase/alphabet state.
        """
        if not self.manager:
            return False

        if consumable_id == 'free_guess':
            return self.manager.free_guess_active

        if consumable_id == 'bonus_strike':
            # Can always recover a used strike; cap only applies to true bonus strikes
            if self.manager.strikes and self.manager.strikes.count > 0:
                return False
            return self.manager.bonus_strikes >= 3

        # For the remaining consumables, check if there's anything left to act on
        phrase   = self.manager.phrase
        alphabet = self.manager.alphabet
        if phrase is None or alphabet is None:
            return False

        phrase_letters = set(phrase.word.replace(' ', ''))

        if consumable_id == 'reveal_consonant':
            hidden_consonants = phrase_letters & {'B','C','D','F','G','H','J','K','L','M',
                                                  'N','P','Q','R','S','T','V','W','X','Y','Z'} \
                                - alphabet.guessed
            return len(hidden_consonants) == 0

        if consumable_id == 'reveal_vowel':
            hidden_vowels = phrase_letters & {'A','E','I','O','U'} - alphabet.guessed
            return len(hidden_vowels) == 0

        if consumable_id == 'eliminate_letters':
            wrong_letters = [c for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
                             if c not in phrase.word and c not in alphabet.guessed]
            return len(wrong_letters) == 0

        return False

    # --- Purchases ---

    def _try_purchase_upgrade(self, upgrade_id):
        """Attempt to purchase an upgrade. Returns True if successful."""
        purchased = self.manager.purchased_upgrades
        upgrade = next((u for u in UPGRADES if u['id'] == upgrade_id), None)
        if not upgrade or not self.is_upgrade_available(upgrade, purchased):
            return False
        if not self.manager.spend(upgrade['cost']):
            return False
        purchased.add(upgrade_id)
        return True

    def _try_purchase_consumable(self, consumable_id):
        """Attempt to purchase and immediately apply a consumable."""
        consumable = next((c for c in CONSUMABLES if c['id'] == consumable_id), None)
        if not consumable:
            return False
        if self._is_consumable_disabled(consumable_id):
            return False
        if not self.manager.spend(consumable['cost']):
            return False

        callbacks = {
            'reveal_consonant':  self.on_reveal_consonant,
            'reveal_vowel':      self.on_reveal_vowel,
            'eliminate_letters': self.on_eliminate_letters,
            'free_guess':        self.on_free_guess,
            'bonus_strike':      self.on_bonus_strike,
        }
        cb = callbacks.get(consumable_id)
        if cb:
            cb()

        return True

    def _try_unlock_secret(self):
        """Spend 5 stars to permanently unlock the secret tab. Returns True if successful."""
        if not self.manager:
            return False
        if self.manager.secret_shop_unlocked:
            return False
        if not self.manager.spend_stars(SECRET_UNLOCK_COST):
            return False
        self.manager.secret_shop_unlocked = True
        self.active_tab = 'secret'  # Switch into the tab immediately on unlock
        return True

    def _try_purchase_secret_item(self, item_id):
        """Attempt to purchase a secret item, spending stars or money as appropriate."""
        item = next((i for i in SECRET_ITEMS if i['id'] == item_id), None)
        if not item:
            return False
        if item['currency'] == 'stars':
            if not self.manager.spend_stars(item['cost']):
                return False
        else:
            if not self.manager.spend(item['cost']):
                return False
        # Placeholder: no effect yet. Future items wire callbacks here.
        return True

    # --- Scroll ---

    def _max_scroll(self, tab, purchased_upgrades):
        """Return the maximum scroll offset for a tab based on its total content height."""
        if tab == 'upgrades':
            count = len(self._visible_upgrades(purchased_upgrades))
        elif tab == 'consumables':
            count = len(CONSUMABLES)
        else:
            count = len(SECRET_ITEMS) if self._secret_unlocked() else 0
        total_content_height = count * ROW_HEIGHT
        return max(0, total_content_height - self.content_height)

    def scroll(self, dy, purchased_upgrades):
        """
        Scroll the active tab by dy pixels (negative = scroll down, positive = scroll up).
        Clamps to valid range so content never scrolls past its bounds.
        """
        if not self.visible:
            return
        max_scroll = self._max_scroll(self.active_tab, purchased_upgrades)
        current = self.scroll_offsets[self.active_tab]
        self.scroll_offsets[self.active_tab] = max(0, min(current - dy * 20, max_scroll))

    def _switch_tab(self, tab):
        """Switch to a tab. Scroll offset for each tab is preserved independently."""
        self.active_tab = tab

    # --- Click Handling ---

    def handle_click(self, pos, purchased_upgrades):
        """Handle all clicks for the shop button, tabs, buy buttons, and close."""
        if self.button_rect.collidepoint(pos):
            self.visible = not self.visible
            return True

        if not self.visible:
            return False

        if self.close_rect.collidepoint(pos):
            self.visible = False
            return True

        for tab_id, rect in self._build_tab_rects().items():
            if not rect.collidepoint(pos):
                continue
            # Clicking the secret tab while locked attempts to unlock it
            if tab_id == 'secret' and not self._secret_unlocked():
                self._try_unlock_secret()
                return True
            self._switch_tab(tab_id)
            return True

        # Only register clicks inside the scrollable content area
        if not self.content_rect.collidepoint(pos):
            return False

        scroll    = self.scroll_offsets[self.active_tab]
        content_y = pos[1] - self.content_top + scroll

        if self.active_tab == 'upgrades':
            visible = self._visible_upgrades(purchased_upgrades)
            for i, upgrade in enumerate(visible):
                row_y    = i * ROW_HEIGHT
                btn_rect = pygame.Rect(0, 0, BTN_WIDTH, BTN_HEIGHT)
                btn_rect.right   = self.popup_rect.right - 20 - self.popup_rect.left
                btn_rect.centery = row_y + ROW_HEIGHT // 2
                if btn_rect.left <= pos[0] - self.popup_rect.left <= btn_rect.right:
                    if btn_rect.top <= content_y <= btn_rect.bottom:
                        self._try_purchase_upgrade(upgrade['id'])
                        return True

        elif self.active_tab == 'consumables':
            for i, consumable in enumerate(CONSUMABLES):
                row_y    = i * ROW_HEIGHT
                btn_rect = pygame.Rect(0, 0, BTN_WIDTH, BTN_HEIGHT)
                btn_rect.right   = self.popup_rect.right - 20 - self.popup_rect.left
                btn_rect.centery = row_y + ROW_HEIGHT // 2
                if btn_rect.left <= pos[0] - self.popup_rect.left <= btn_rect.right:
                    if btn_rect.top <= content_y <= btn_rect.bottom:
                        self._try_purchase_consumable(consumable['id'])
                        return True

        elif self.active_tab == 'secret' and self._secret_unlocked():
            for i, item in enumerate(SECRET_ITEMS):
                row_y    = i * ROW_HEIGHT
                btn_rect = pygame.Rect(0, 0, BTN_WIDTH, BTN_HEIGHT)
                btn_rect.right   = self.popup_rect.right - 20 - self.popup_rect.left
                btn_rect.centery = row_y + ROW_HEIGHT // 2
                if btn_rect.left <= pos[0] - self.popup_rect.left <= btn_rect.right:
                    if btn_rect.top <= content_y <= btn_rect.bottom:
                        self._try_purchase_secret_item(item['id'])
                        return True

        return False

    # --- Drawing ---

    def _draw_tab_content(self, screen, money, purchased_upgrades):
        """
        Draw the scrollable content for the active tab.
        Renders all rows onto an offscreen surface, then blits a clipped
        window of it onto the popup at the correct scroll position.

        The secret tab has two states:
          - Locked: shows a single centred unlock prompt instead of items.
          - Unlocked: renders SECRET_ITEMS rows with star-cost buttons.
        """
        if self.active_tab == 'secret':
            self._draw_secret_content(screen)
            return

        if self.active_tab == 'upgrades':
            items = self._visible_upgrades(purchased_upgrades)
        else:
            items = CONSUMABLES

        total_height    = max(len(items) * ROW_HEIGHT, self.content_height)
        content_surface = pygame.Surface((self.popup_rect.width, total_height))
        content_surface.fill('black')

        for i, item in enumerate(items):
            y          = i * ROW_HEIGHT
            is_upgrade = self.active_tab == 'upgrades'

            owned     = is_upgrade and item['id'] in purchased_upgrades
            disabled  = not is_upgrade and self._is_consumable_disabled(item['id'])
            can_afford = money >= item['cost']

            # Labels always white, descriptions always grey regardless of state
            label_surf = self.small_font.render(item['label'],       True, 'white')
            desc_surf  = self.small_font.render(item['description'], True, '#888888')
            content_surface.blit(label_surf, (20, y + 6))
            content_surface.blit(desc_surf,  (20, y + 26))

            btn_rect         = pygame.Rect(0, 0, BTN_WIDTH, BTN_HEIGHT)
            btn_rect.right   = self.popup_rect.width - 20
            btn_rect.centery = y + ROW_HEIGHT // 2

            if owned:
                btn_color, btn_text, text_color, border_color = '#333333', 'Owned',          '#555555', '#555555'
            elif disabled or not can_afford:
                btn_color, btn_text, text_color, border_color = '#222222', f'${item["cost"]}', '#555555', '#555555'
            else:
                btn_color, btn_text, text_color, border_color = 'black',   f'${item["cost"]}', 'white',   'white'

            pygame.draw.rect(content_surface, btn_color,    btn_rect)
            pygame.draw.rect(content_surface, border_color, btn_rect, 1)
            btn_surf = self.small_font.render(btn_text, True, text_color)
            content_surface.blit(btn_surf, btn_surf.get_rect(center=btn_rect.center))

            if i < len(items) - 1:
                pygame.draw.line(content_surface, '#222222',
                                 (20, y + ROW_HEIGHT - 1),
                                 (self.popup_rect.width - 20, y + ROW_HEIGHT - 1), 1)

        scroll       = self.scroll_offsets[self.active_tab]
        visible_area = pygame.Rect(0, scroll, self.popup_rect.width, self.content_height)
        screen.blit(content_surface, (self.popup_rect.left, self.content_top), visible_area)

    def _draw_secret_content(self, screen):
        """
        Draw the secret tab content area.
        Locked: centred prompt showing the star cost to unlock.
        Unlocked: scrollable item rows with star-cost buttons (gold).
        """
        stars = self.manager.stars if self.manager else 0

        if not self._secret_unlocked():
            # Locked state — show unlock prompt centred in the content area
            cx = self.popup_rect.centerx
            cy = self.content_top + self.content_height // 2 - 20

            can_afford   = stars >= SECRET_UNLOCK_COST
            prompt_color = 'white' if can_afford else '#555555'
            cost_color   = 'gold'  if can_afford else '#666600'

            prompt = self.small_font.render('Unlock the Secret Shop for', True, prompt_color)
            cost   = self.font.render(f'*{SECRET_UNLOCK_COST}', True, cost_color)
            note   = self.small_font.render(f'You have *{stars}', True, '#888888')

            screen.blit(prompt, prompt.get_rect(centerx=cx, bottom=cy))
            screen.blit(cost,   cost.get_rect(centerx=cx, top=cy))
            screen.blit(note,   note.get_rect(centerx=cx, top=cy + cost.get_height() + 6))
            return

        # Unlocked — draw item rows
        total_height    = max(len(SECRET_ITEMS) * ROW_HEIGHT, self.content_height)
        content_surface = pygame.Surface((self.popup_rect.width, total_height))
        content_surface.fill('black')

        for i, item in enumerate(SECRET_ITEMS):
            y = i * ROW_HEIGHT

            if item['currency'] == 'stars':
                can_afford = stars >= item['cost']
                cost_label = f'*{item["cost"]}'
                afford_color  = 'gold'
                disable_color = '#666600'
            else:
                can_afford = self.manager and self.manager.money >= item['cost']
                cost_label = f'${item["cost"]}'
                afford_color  = 'white'
                disable_color = '#555555'

            label_surf = self.small_font.render(item['label'],       True, 'white')
            desc_surf  = self.small_font.render(item['description'], True, '#888888')
            content_surface.blit(label_surf, (20, y + 6))
            content_surface.blit(desc_surf,  (20, y + 26))

            btn_rect         = pygame.Rect(0, 0, BTN_WIDTH, BTN_HEIGHT)
            btn_rect.right   = self.popup_rect.width - 20
            btn_rect.centery = y + ROW_HEIGHT // 2

            if can_afford:
                btn_color, text_color, border_color = 'black',    afford_color,  afford_color
            else:
                btn_color, text_color, border_color = '#222222',  disable_color, disable_color

            pygame.draw.rect(content_surface, btn_color,    btn_rect)
            pygame.draw.rect(content_surface, border_color, btn_rect, 1)
            btn_surf = self.small_font.render(cost_label, True, text_color)
            content_surface.blit(btn_surf, btn_surf.get_rect(center=btn_rect.center))

            if i < len(SECRET_ITEMS) - 1:
                pygame.draw.line(content_surface, '#222222',
                                 (20, y + ROW_HEIGHT - 1),
                                 (self.popup_rect.width - 20, y + ROW_HEIGHT - 1), 1)

        scroll       = self.scroll_offsets['secret']
        visible_area = pygame.Rect(0, scroll, self.popup_rect.width, self.content_height)
        screen.blit(content_surface, (self.popup_rect.left, self.content_top), visible_area)

    def draw(self, screen, money, purchased_upgrades):
        """Draw the shop button, active consumable status, and popup if visible."""
        pygame.draw.rect(screen, 'black', self.button_rect)
        pygame.draw.rect(screen, 'white', self.button_rect, 2)
        btn_surface = self.font.render('Shop', True, 'white')
        screen.blit(btn_surface, btn_surface.get_rect(center=self.button_rect.center))

        # Active consumable status shown below the shop button on the main screen
        if self.manager:
            status_y = self.button_rect.bottom + 6
            if self.manager.free_guess_active:
                fg_surf = self.small_font.render('FREE GUESS ACTIVE', True, 'green')
                screen.blit(fg_surf, fg_surf.get_rect(centerx=self.button_rect.centerx, top=status_y))
                status_y += fg_surf.get_height() + 2
            if self.manager.bonus_strikes > 0:
                bs_surf = self.small_font.render(f'BONUS STRIKES: {self.manager.bonus_strikes}', True, 'green')
                screen.blit(bs_surf, bs_surf.get_rect(centerx=self.button_rect.centerx, top=status_y))

        if not self.visible:
            return

        # Popup background and border
        pygame.draw.rect(screen, 'black', self.popup_rect)
        pygame.draw.rect(screen, 'white', self.popup_rect, 2)

        # Title
        title = self.font.render('SHOP', True, 'white')
        screen.blit(title, title.get_rect(centerx=self.popup_rect.centerx, top=self.popup_rect.top + 15))

        for tab_id, rect in self._build_tab_rects().items():

            is_active = self.active_tab == tab_id
            is_locked = tab_id == 'secret' and not self._secret_unlocked()

            # Locked secret tab styling — brightens to full gold when player can afford unlock
            can_afford_unlock = is_locked and self.manager and self.manager.stars >= SECRET_UNLOCK_COST
            if is_locked:
                border_color = 'gold'    if can_afford_unlock else '#666600'
                fill_color   = '#221100' if (can_afford_unlock and is_active) else ('#111100' if is_active else 'black')
            else:
                border_color = 'white'
                fill_color   = '#222222' if is_active else 'black'

            pygame.draw.rect(screen, fill_color,    rect)
            pygame.draw.rect(screen, border_color,  rect, 2 if is_active else 1)

            if is_locked:
                label      = '! Secret !' if can_afford_unlock else '? Secret ?'
                text_color = 'gold'        if can_afford_unlock else '#888800'
            else:
                label      = tab_id.capitalize()
                text_color = 'white'
            tab_surf = self.small_font.render(label, True, text_color)
            screen.blit(tab_surf, tab_surf.get_rect(center=rect.center))

        # Divider below tabs
        pygame.draw.line(screen, 'grey',
                         (self.popup_rect.left + 20,  self.popup_rect.top + 100),
                         (self.popup_rect.right - 20, self.popup_rect.top + 100), 1)

        # Scrollable content — clipped so rows can't bleed outside the popup
        screen.set_clip(self.content_rect)
        self._draw_tab_content(screen, money, purchased_upgrades)
        screen.set_clip(None)

        # Scroll indicator — only relevant for tabs with scrollable content
        max_scroll = self._max_scroll(self.active_tab, purchased_upgrades)
        if max_scroll > 0:
            scroll = self.scroll_offsets[self.active_tab]
            if self.active_tab == 'upgrades':
                item_count = len(self._visible_upgrades(purchased_upgrades))
            elif self.active_tab == 'secret':
                item_count = len(SECRET_ITEMS)
            else:
                item_count = len(CONSUMABLES)
            total_height = item_count * ROW_HEIGHT
            bar_height   = max(20, int(self.content_height * (self.content_height / total_height)))
            bar_y        = self.content_top + int((scroll / max_scroll) * (self.content_height - bar_height))
            bar_rect     = pygame.Rect(self.popup_rect.right - 7, bar_y, 4, bar_height)
            pygame.draw.rect(screen, '#555555', bar_rect, border_radius=2)

        # Close button — drawn after set_clip(None) so it's never clipped
        pygame.draw.rect(screen, 'black', self.close_rect)
        pygame.draw.rect(screen, 'white', self.close_rect, 2)
        close_surf = self.font.render('Close', True, 'white')
        screen.blit(close_surf, close_surf.get_rect(center=self.close_rect.center))