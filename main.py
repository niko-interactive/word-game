import pygame

from constants import SCREEN_SIZE
from game_manager import GameManager, PRESTIGE_UNLOCK_STREAK
from menu_bar import MenuBar
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

shop     = Shop(font, *SCREEN_SIZE)
score    = Score(font)
menu_bar = MenuBar(font, SCREEN_SIZE[0], shop)

manager = GameManager(font, shop)
shop.manager     = manager
score.manager    = manager
menu_bar.manager = manager

popup              = None   # Active win/lose/game-complete popup
pending_lose       = False  # True when lose popup is showing but lose() hasn't fired
prestige_popup     = None   # Active prestige popup


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

            if prestige_popup:
                result = prestige_popup.handle_click(event.pos)
                if result == 'confirm':
                    manager.prestige()
                    prestige_popup = None
                elif result:  # True = close/No button
                    prestige_popup = None

            elif popup and popup.handle_click(event.pos):
                dismiss_popup()

            elif not popup:
                clicked = menu_bar.handle_click(event.pos)
                if clicked == 'debug_money':
                    manager.money += 10_000
                    manager.streak_count += 8
                elif clicked == 'prestige':
                    prestige_popup = Popup(
                        'PRESTIGE', font, *SCREEN_SIZE,
                        prestige=True,
                        star_buffer=manager.star_buffer,
                        can_prestige=manager.can_prestige,
                        streak=manager.streak_count,
                        prestige_unlock_streak=PRESTIGE_UNLOCK_STREAK,
                    )
                elif clicked is None:
                    shop.handle_click(event.pos)
                    # A consumable (reveal vowel/consonant) may have solved the puzzle
                    if manager.solved_by_consumable:
                        manager.solved_by_consumable = False
                        shop.visible = False
                        popup = Popup('You Win!', font, *SCREEN_SIZE,
                                      phrase=manager.phrase.word)

        if event.type == pygame.MOUSEWHEEL:
            shop.scroll(event.y)

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                if prestige_popup:
                    prestige_popup = None
                elif popup:
                    dismiss_popup()
                elif shop.visible:
                    shop.visible = False

        # Only accept letter guesses when no overlay is open
        if event.type == pygame.KEYDOWN and popup is None and not shop.visible and not prestige_popup:
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
                                      streak=manager.streak_count,
                                      lost_star_buffer=manager.star_buffer)

    # --- Drawing ---
    screen.fill('black')
    manager.draw(screen)
    score.draw(screen)
    menu_bar.draw(screen)
    shop.draw(screen)

    if popup:
        popup.draw(screen)

    if prestige_popup:
        prestige_popup.draw(screen)

    pygame.display.update()
    clock.tick(30)

pygame.quit()