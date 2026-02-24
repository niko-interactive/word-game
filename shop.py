import pygame

from shop_items import UPGRADES, CONSUMABLES, PRESTIGE_ITEMS


ROW_HEIGHT = 52
BTN_WIDTH  = 80
BTN_HEIGHT = 36


class Shop:
    """
    Manages the shop UI and purchase rules for upgrades, consumables, and
    prestige items.

    All three lists (UPGRADES, CONSUMABLES, PRESTIGE_ITEMS) share the same
    item schema.  Upgrades and prestige items are rendered through a single
    unified draw/click/purchase path; consumables keep a separate path because
    their availability is gated by live gameplay state rather than ownership.

    Ownership storage:
      Upgrades    → manager.purchased_upgrades  (set of id strings, resets on loss)
      Prestige    → manager.prestige_owned       (set of id strings, permanent)
      Consumables → not tracked (unlimited, applied immediately on purchase)
    """

    def __init__(self, font, screen_width, screen_height):
        self.font       = font
        self.small_font = pygame.font.SysFont('Arial', 20)
        self.screen_width  = screen_width
        self.screen_height = screen_height

        self.visible    = False
        self.active_tab = 'upgrades'

        self.scroll_offsets = {'upgrades': 0, 'consumables': 0, 'prestige': 0}

        # Consumable callbacks — set by GameManager each round
        self.on_reveal_consonant  = None
        self.on_reveal_vowel      = None
        self.on_eliminate_letters = None
        self.on_free_guess        = None
        self.on_bonus_strike      = None

        self.manager = None  # set by main.py after construction

        self.popup_rect = pygame.Rect(0, 0, 600, 480)
        self.popup_rect.center = (screen_width // 2, screen_height // 2)

        self.tab_width  = 140
        self.tab_height = 36
        self.tab_gap    = 16
        self.tab_y      = self.popup_rect.top + 55

        self.content_top    = self.popup_rect.top + 110
        self.content_bottom = self.popup_rect.bottom - 65
        self.content_height = self.content_bottom - self.content_top
        self.content_rect   = pygame.Rect(
            self.popup_rect.left + 2, self.content_top,
            self.popup_rect.width - 4, self.content_height,
        )

        self.close_rect = pygame.Rect(0, 0, 120, 40)
        self.close_rect.centerx = self.popup_rect.centerx
        self.close_rect.bottom  = self.popup_rect.bottom - 15

    # -------------------------------------------------------------------------
    # State helpers
    # -------------------------------------------------------------------------

    def reset(self):
        """Reset tab and scroll state on loss. Upgrade ownership reset by GameManager."""
        self.active_tab = 'upgrades'
        self.scroll_offsets = {k: 0 for k in self.scroll_offsets}

    def _prestige_visible(self):
        return self.manager and self.manager.prestige_count >= 1

    def _build_tab_rects(self):
        tabs = ['upgrades', 'consumables']
        if self._prestige_visible():
            tabs.append('prestige')
        n           = len(tabs)
        total_width = self.tab_width * n + self.tab_gap * (n - 1)
        start_x     = self.popup_rect.left + (self.popup_rect.width - total_width) // 2
        return {
            tab: pygame.Rect(start_x + i * (self.tab_width + self.tab_gap),
                             self.tab_y, self.tab_width, self.tab_height)
            for i, tab in enumerate(tabs)
        }

    # -------------------------------------------------------------------------
    # Ownership helpers — work for both upgrades and prestige items
    # -------------------------------------------------------------------------

    def _owned_count(self, item_id, item_list):
        """How many times this item has been purchased."""
        if not self.manager:
            return 0
        if item_list is UPGRADES:
            # purchased_upgrades stores each *purchase* as 'id_1', 'id_2', etc.
            return sum(1 for k in self.manager.purchased_upgrades
                       if k == item_id or k.startswith(item_id + '_'))
        if item_list is CONSUMABLES:
            return self.manager.consumable_purchases.get(item_id, 0)
        if item_list is PRESTIGE_ITEMS:
            if item_id == 'star_streak_discount':
                return self.manager.star_streak_discounts
            return 1 if item_id in self.manager.prestige_owned else 0
        return 0

    def _is_owned(self, item_id, item_list):
        """True if this item has been purchased at least once."""
        return self._owned_count(item_id, item_list) > 0

    def _next_cost(self, item, item_list):
        """Cost of the next purchase given how many times it's been bought."""
        count  = self._owned_count(item['id'], item_list)
        growth = item.get('cost_growth')
        if growth is not None:
            return round(item['cost'] * (growth ** count))
        return item['cost']

    def _item_requires_met(self, item, item_list):
        """True if this item's prerequisite has been purchased at least once."""
        req = item.get('requires')
        if not req:
            return True
        req_item = next((x for x in item_list if x['id'] == req), None)
        if req_item is None:
            return False
        return self._is_owned(req, item_list)

    def _item_prereq_blocked(self, item, item_list):
        """
        True when the item exists and its requires is met at the list level, but
        the *per-purchase* prereq isn't satisfied yet.

        For upgrades with cost_growth set, 'guaranteed_consonant' purchase N
        requires 'free_consonant' purchase N.  So if free_consonant is owned 1×
        and guaranteed_consonant is already owned 1×, the next guaranteed purchase
        is blocked until free_consonant reaches 2×.
        """
        req = item.get('requires')
        if not req or item.get('cost_growth') is None:
            return False
        owned_this = self._owned_count(item['id'], item_list)
        owned_req  = self._owned_count(req, item_list)
        return owned_this >= owned_req  # can't buy more of this than its prereq

    def _item_maxed(self, item, item_list):
        """True when max_owned is set and already reached."""
        max_owned = item.get('max_owned')
        if max_owned is None:
            return False
        return self._owned_count(item['id'], item_list) >= max_owned

    # -------------------------------------------------------------------------
    # Visible item lists
    # -------------------------------------------------------------------------

    def _visible_items(self, item_list):
        """
        Return items that should be displayed.
        - Always hides items whose requires isn't met.
        - Hides maxed-out prestige items (they are permanently gone once bought out).
        - Upgrades stay visible when maxed — they show as Owned and grey out.
        """
        from shop_items import PRESTIGE_ITEMS
        visible = []
        for item in item_list:
            if not self._item_requires_met(item, item_list):
                continue
            if item_list is PRESTIGE_ITEMS and self._item_maxed(item, item_list):
                continue
            visible.append(item)
        return visible

    def _item_display_label(self, item, item_list):
        """Label with (owned/max) count appended for repeatable items."""
        max_owned = item.get('max_owned')
        if max_owned is not None:
            owned = self._owned_count(item['id'], item_list)
            return f'{item["label"]} ({owned}/{max_owned})'
        return item['label']

    def _item_available(self, item, item_list):
        """True if the item can actually be purchased right now."""
        if self._item_maxed(item, item_list):
            return False
        if not self._item_requires_met(item, item_list):
            return False
        if self._item_prereq_blocked(item, item_list):
            return False
        return True

    # -------------------------------------------------------------------------
    # Consumable-specific helpers (availability gated by gameplay state)
    # -------------------------------------------------------------------------

    def _is_consumable_disabled(self, consumable_id):
        if not self.manager:
            return False
        if consumable_id == 'free_guess':
            return self.manager.free_guess_active
        if consumable_id == 'bonus_strike':
            if self.manager.strikes and self.manager.strikes.count > 0:
                return False
            return self.manager.bonus_strikes >= 3
        phrase   = self.manager.phrase
        alphabet = self.manager.alphabet
        if phrase is None or alphabet is None:
            return False
        phrase_letters = set(phrase.word.replace(' ', ''))
        if consumable_id == 'reveal_consonant':
            return not (phrase_letters & set('BCDFGHJKLMNPQRSTVWXYZ') - alphabet.guessed)
        if consumable_id == 'reveal_vowel':
            return not (phrase_letters & set('AEIOU') - alphabet.guessed)
        if consumable_id == 'eliminate_letters':
            return not [c for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
                        if c not in phrase.word and c not in alphabet.guessed]
        return False

    # -------------------------------------------------------------------------
    # Purchases
    # -------------------------------------------------------------------------

    def _try_purchase_item(self, item_id, item_list):
        """Unified purchase handler for upgrades and prestige items."""
        item = next((x for x in item_list if x['id'] == item_id), None)
        if not item or not self._item_available(item, item_list):
            return False

        cost = self._next_cost(item, item_list)

        if item['currency'] == 'stars':
            if not self.manager.spend_stars(cost):
                return False
        else:
            if not self.manager.spend(cost):
                return False

        # Record the purchase
        if item_list is UPGRADES:
            count = self._owned_count(item_id, item_list)
            key   = f'{item_id}_{count + 1}' if item.get('max_owned', 1) > 1 else item_id
            self.manager.purchased_upgrades.add(key)
        else:
            self.manager.purchase_prestige_item(item_id)

        return True

    def _try_purchase_consumable(self, consumable_id):
        consumable = next((c for c in CONSUMABLES if c['id'] == consumable_id), None)
        if not consumable or self._is_consumable_disabled(consumable_id):
            return False
        cost = self._next_cost(consumable, CONSUMABLES)
        if not self.manager.spend(cost):
            return False
        self.manager.consumable_purchases[consumable_id] =             self.manager.consumable_purchases.get(consumable_id, 0) + 1
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

    # -------------------------------------------------------------------------
    # Scroll
    # -------------------------------------------------------------------------

    def _max_scroll(self, tab):
        if tab == 'upgrades':
            count = len(self._visible_items(UPGRADES))
        elif tab == 'consumables':
            count = len(CONSUMABLES)
        else:
            count = len(self._visible_items(PRESTIGE_ITEMS))
        return max(0, count * ROW_HEIGHT - self.content_height)

    def scroll(self, dy):
        if not self.visible:
            return
        max_scroll = self._max_scroll(self.active_tab)
        current    = self.scroll_offsets[self.active_tab]
        self.scroll_offsets[self.active_tab] = max(0, min(current - dy * 20, max_scroll))

    def _switch_tab(self, tab):
        self.active_tab = tab

    # -------------------------------------------------------------------------
    # Click handling
    # -------------------------------------------------------------------------

    def handle_click(self, pos):
        if not self.visible:
            return False

        if self.close_rect.collidepoint(pos):
            self.visible = False
            return True

        for tab_id, rect in self._build_tab_rects().items():
            if rect.collidepoint(pos):
                self._switch_tab(tab_id)
                return True

        if not self.content_rect.collidepoint(pos):
            return False

        scroll    = self.scroll_offsets[self.active_tab]
        content_y = pos[1] - self.content_top + scroll

        if self.active_tab == 'consumables':
            items = CONSUMABLES
            for i, item in enumerate(items):
                btn_rect = self._btn_rect_for_row(i)
                if self._hit(btn_rect, pos, content_y):
                    self._try_purchase_consumable(item['id'])
                    return True
        else:
            item_list = UPGRADES if self.active_tab == 'upgrades' else PRESTIGE_ITEMS
            items     = self._visible_items(item_list)
            for i, item in enumerate(items):
                btn_rect = self._btn_rect_for_row(i)
                if self._hit(btn_rect, pos, content_y):
                    self._try_purchase_item(item['id'], item_list)
                    return True

        return False

    def _btn_rect_for_row(self, row_index):
        btn = pygame.Rect(0, 0, BTN_WIDTH, BTN_HEIGHT)
        btn.right   = self.popup_rect.right - 20 - self.popup_rect.left
        btn.centery = row_index * ROW_HEIGHT + ROW_HEIGHT // 2
        return btn

    def _hit(self, btn_rect, pos, content_y):
        lx = pos[0] - self.popup_rect.left
        return btn_rect.left <= lx <= btn_rect.right and btn_rect.top <= content_y <= btn_rect.bottom

    # -------------------------------------------------------------------------
    # Drawing
    # -------------------------------------------------------------------------

    def _draw_tab_content(self, screen):
        if self.active_tab == 'consumables':
            self._draw_item_rows(screen, CONSUMABLES, is_consumable=True)
        elif self.active_tab == 'upgrades':
            self._draw_item_rows(screen, self._visible_items(UPGRADES))
        else:
            self._draw_item_rows(screen, self._visible_items(PRESTIGE_ITEMS))

    def _draw_item_rows(self, screen, items, is_consumable=False):
        item_list = CONSUMABLES if is_consumable else (
            UPGRADES if self.active_tab == 'upgrades' else PRESTIGE_ITEMS
        )

        total_height    = max(len(items) * ROW_HEIGHT, self.content_height)
        surface         = pygame.Surface((self.popup_rect.width, total_height))
        surface.fill('black')

        for i, item in enumerate(items):
            y = i * ROW_HEIGHT

            # --- State ---
            if is_consumable:
                available    = not self._is_consumable_disabled(item['id'])
                cost_now     = self._next_cost(item, CONSUMABLES)
                can_afford   = self.manager.money >= cost_now
                fully_owned  = False
                blocked      = False
                display_lbl  = item['label']
                cost_prefix  = '$'
                afford_color = 'white'
                dim_color    = '#555555'
            else:
                max_owned    = item.get('max_owned')
                owned_count  = self._owned_count(item['id'], item_list)
                fully_owned  = self._item_maxed(item, item_list) or (max_owned is None and self._is_owned(item['id'], item_list))
                blocked      = self._item_prereq_blocked(item, item_list)
                available    = self._item_available(item, item_list)
                cost_now     = self._next_cost(item, item_list)
                display_lbl  = self._item_display_label(item, item_list)
                if item['currency'] == 'stars':
                    can_afford   = self.manager.stars >= cost_now
                    cost_prefix  = '*'
                    afford_color = 'gold'
                    dim_color    = '#666600'
                else:
                    can_afford   = self.manager.money >= cost_now
                    cost_prefix  = '$'
                    afford_color = 'white'
                    dim_color    = '#555555'

            # --- Label & description ---
            surface.blit(self.small_font.render(display_lbl,        True, 'white'),   (20, y + 6))
            surface.blit(self.small_font.render(item['description'], True, '#888888'), (20, y + 26))

            # --- Button ---
            btn = pygame.Rect(0, 0, BTN_WIDTH, BTN_HEIGHT)
            btn.right   = self.popup_rect.width - 20
            btn.centery = y + ROW_HEIGHT // 2

            if fully_owned:
                bg, text, border = '#333333', 'Owned', '#555555'
            elif not available or not can_afford:
                bg, text, border = '#222222', f'{cost_prefix}{cost_now}', dim_color
            else:
                bg, text, border = 'black', f'{cost_prefix}{cost_now}', afford_color

            pygame.draw.rect(surface, bg,     btn)
            pygame.draw.rect(surface, border, btn, 1)
            surface.blit(self.small_font.render(text, True, border),
                         self.small_font.render(text, True, border).get_rect(center=btn.center))

            if i < len(items) - 1:
                pygame.draw.line(surface, '#222222',
                                 (20, y + ROW_HEIGHT - 1),
                                 (self.popup_rect.width - 20, y + ROW_HEIGHT - 1), 1)

        scroll       = self.scroll_offsets[self.active_tab]
        visible_area = pygame.Rect(0, scroll, self.popup_rect.width, self.content_height)
        screen.blit(surface, (self.popup_rect.left, self.content_top), visible_area)

    def draw(self, screen):
        if not self.visible:
            return

        pygame.draw.rect(screen, 'black', self.popup_rect)
        pygame.draw.rect(screen, 'white', self.popup_rect, 2)

        title = self.font.render('SHOP', True, 'white')
        screen.blit(title, title.get_rect(centerx=self.popup_rect.centerx,
                                          top=self.popup_rect.top + 15))

        for tab_id, rect in self._build_tab_rects().items():
            is_active = self.active_tab == tab_id
            pygame.draw.rect(screen, '#222222' if is_active else 'black', rect)
            pygame.draw.rect(screen, 'white', rect, 2 if is_active else 1)
            surf = self.small_font.render(tab_id.capitalize(), True, 'white')
            screen.blit(surf, surf.get_rect(center=rect.center))

        pygame.draw.line(screen, 'grey',
                         (self.popup_rect.left + 20,  self.popup_rect.top + 100),
                         (self.popup_rect.right - 20, self.popup_rect.top + 100), 1)

        screen.set_clip(self.content_rect)
        self._draw_tab_content(screen)
        screen.set_clip(None)

        max_scroll = self._max_scroll(self.active_tab)
        if max_scroll > 0:
            scroll = self.scroll_offsets[self.active_tab]
            if self.active_tab == 'upgrades':
                count = len(self._visible_items(UPGRADES))
            elif self.active_tab == 'prestige':
                count = len(self._visible_items(PRESTIGE_ITEMS))
            else:
                count = len(CONSUMABLES)
            total_h    = count * ROW_HEIGHT
            bar_h      = max(20, int(self.content_height * (self.content_height / total_h)))
            bar_y      = self.content_top + int((scroll / max_scroll) * (self.content_height - bar_h))
            pygame.draw.rect(screen, '#555555',
                             pygame.Rect(self.popup_rect.right - 7, bar_y, 4, bar_h),
                             border_radius=2)

        pygame.draw.rect(screen, 'black', self.close_rect)
        pygame.draw.rect(screen, 'white', self.close_rect, 2)
        close_surf = self.font.render('Close', True, 'white')
        screen.blit(close_surf, close_surf.get_rect(center=self.close_rect.center))