import pygame

from constants import SCREEN_SIZE
from game_manager import GameManager
from popup import Popup
from shop import Shop
from score import Score


# --- Initialization ---
pygame.init()
screen = pygame.display.set_mode(SCREEN_SIZE)
pygame.display.set_caption('Word Game')
clock = pygame.time.Clock()
running = True

font = pygame.font.SysFont('Arial', 32)

# Shop and score are UI classes that persist across rounds
shop = Shop(font, *SCREEN_SIZE)
score = Score(font)

# Manager owns all run/round state — shop.manager wired so purchases can call spend()
manager = GameManager(font, shop)
shop.manager = manager

popup = None       # Active popup overlay, or None
pending_lose = False  # True when a lose popup is showing but lose() hasn't fired yet


def dismiss_popup():
    """Handle popup dismissal — win advances the round, lose resets the run."""
    global popup, pending_lose
    if pending_lose:
        pending_lose = False
        manager.lose()
        popup = None
    elif popup.game_complete:
        manager.lose()
        popup = None
    else:
        advanced = manager.win()
        if not advanced:
            popup = Popup('You Beat the Game!', font, *SCREEN_SIZE,
                          game_complete=True, streak=manager.streak_count)
        else:
            popup = None


# --- Game Loop ---
while running:
    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if popup and popup.handle_click(event.pos):
                dismiss_popup()
            elif not popup:
                shop.handle_click(event.pos, manager.purchased_upgrades)

        if event.type == pygame.MOUSEWHEEL:
            shop.scroll(event.y, manager.purchased_upgrades)

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                if popup:
                    dismiss_popup()
                elif shop.visible:
                    shop.visible = False

        # Only accept letter guesses when no overlay is open
        if event.type == pygame.KEYDOWN and popup is None and not shop.visible:
            if event.unicode.isalpha():
                letter = event.unicode.upper()

                if letter not in manager.alphabet.guessed:
                    result = manager.guess(letter)

                    if result == 'solved':
                        shop.visible = False
                        popup = Popup('You Win!', font, *SCREEN_SIZE,
                                      phrase=manager.phrase.word)

                    elif result == 'game_over':
                        pending_lose = True
                        shop.visible = False
                        popup = Popup('You Lose!', font, *SCREEN_SIZE,
                                      phrase=manager.phrase.word,
                                      streak=manager.streak_count)

    # --- Drawing ---
    screen.fill('black')
    manager.draw(screen)
    score.draw(screen, manager.streak_count, manager.money, manager.stars, manager.stars_display_unlocked)
    shop.draw(screen, manager.money, manager.purchased_upgrades)

    if popup:
        popup.draw(screen)

    pygame.display.update()
    clock.tick(30)

pygame.quit()