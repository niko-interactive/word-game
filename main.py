import pygame
import random

from constants import SCREEN_SIZE
from puzzles import PUZZLES

from alphabet import Alphabet
from phrase import Phrase
from popup import Popup
from streak import Streak
from strikes import Strikes
from topic import Topic
from shop import Shop


# Scrabble values used to weight letter rarity in difficulty calculation
SCRABBLE = {
    'A': 1, 'E': 1, 'I': 1, 'O': 1, 'U': 1,
    'N': 1, 'R': 1, 'S': 1, 'T': 1, 'L': 1, 'H': 1,
    'D': 2, 'G': 2,
    'B': 3, 'C': 3, 'M': 3, 'P': 3,
    'F': 4, 'V': 4, 'W': 4, 'Y': 4,
    'K': 5,
    'J': 8, 'X': 8,
    'Q': 10, 'Z': 10
}

# Letters that are effectively free for certain categories
FREE_LETTERS_BY_CATEGORY = {
    'What Are You Doing?': {'I', 'N', 'G'}
}


def calculate_difficulty(phrase, category):
    """
    Calculate a numeric difficulty score for a puzzle.
    Formula: (unique_letters * rarity * avg_word_length) / num_words

    For categories with known free letters (e.g. What Are You Doing? always
    ends in ING), those letters are excluded from the unique set before scoring.
    """
    unique_letters = set(phrase.replace(' ', ''))
    free = FREE_LETTERS_BY_CATEGORY.get(category, set())
    unique_letters -= free

    rarity = sum(SCRABBLE[c] for c in unique_letters)
    words = phrase.split()
    avg_word_length = sum(len(w) for w in words) / len(words)
    num_words = len(words)
    return (len(unique_letters) * rarity * avg_word_length) / num_words


def get_difficulty_range(streak_count):
    """
    Return (min_difficulty, max_difficulty) for the current streak.
    The window shifts upward as the streak grows — easy puzzles are phased
    out and harder ones phase in, so rounds escalate over time.
    """
    if streak_count >= 30:
        return 500, float('inf')
    elif streak_count >= 20:
        return 350, float('inf')
    elif streak_count >= 12:
        return 200, 700
    elif streak_count >= 8:
        return 100, 500
    elif streak_count >= 4:
        return 0, 350
    else:
        return 0, 200


def get_difficulty_tier(streak_count):
    """Return an integer tier index that increments each time the difficulty
    window changes. Used to detect when the pool needs rebuilding."""
    if streak_count >= 11:
        return 5
    elif streak_count >= 9:
        return 4
    elif streak_count >= 7:
        return 3
    elif streak_count >= 5:
        return 2
    elif streak_count >= 3:
        return 1
    else:
        return 0


def build_puzzle_pool(streak, seen):
    """
    Build and return a shuffled list of all unseen puzzles eligible at the
    current streak's difficulty range. Called at game start, after every loss,
    and whenever the difficulty tier advances mid-run.
    `seen` is a set of puzzle texts already played this run.
    """
    min_difficulty, max_difficulty = get_difficulty_range(streak.count)
    pool = [(text, topic) for text, topic in PUZZLES
            if text not in seen
            and min_difficulty <= calculate_difficulty(text, topic) <= max_difficulty]
    if not pool:
        pool = [(text, topic) for text, topic in PUZZLES if text not in seen]
    if not pool:
        pool = list(PUZZLES)
    random.shuffle(pool)
    return pool


def next_puzzle(remaining):
    """
    Pop and return the next puzzle from the remaining pool.
    The pool is already filtered to the correct difficulty range when built,
    so no re-filtering is needed here.
    Returns (text, topic) or None if the pool is exhausted.
    """
    if remaining:
        return remaining.pop()
    return None


def reset_game(font, streak, shop, remaining):
    """
    Set up a fresh round of the game using the next puzzle from `remaining`.
    Returns (phrase, alphabet, strikes, topic) or raises RuntimeError if the
    pool is empty — callers should check before calling.
    """
    text, topic_text = next_puzzle(remaining)
    phrase = Phrase(text, font, *SCREEN_SIZE)
    alphabet = Alphabet(font, *SCREEN_SIZE)

    # Max strikes depends on purchased strike upgrades
    max_strikes = shop.max_strikes()
    strikes = Strikes(font, SCREEN_SIZE[0], max_strikes)
    topic = Topic(topic_text, font, *SCREEN_SIZE)

    if phrase.letters:
        bottom = max(letter.rect.bottom for letter in phrase.letters)
        topic.update_position(bottom)

    # --- Register consumable callbacks ---
    # These allow the shop to affect the current round's phrase and alphabet
    # when a consumable is purchased mid-round

    def reveal_consonant():
        """Reveal a random hidden consonant from the phrase."""
        hidden = [
            c for c in set(phrase.word.replace(' ', ''))
            if c in {'B','C','D','F','G','H','J','K','L','M',
                     'N','P','Q','R','S','T','V','W','X','Y','Z'}
            and c not in alphabet.guessed
        ]
        if hidden:
            letter = random.choice(hidden)
            phrase.guess(letter)
            alphabet.guess(letter)

    def reveal_vowel():
        """Reveal a random hidden vowel from the phrase."""
        hidden = [
            c for c in set(phrase.word.replace(' ', ''))
            if c in {'A', 'E', 'I', 'O', 'U'}
            and c not in alphabet.guessed
        ]
        if hidden:
            letter = random.choice(hidden)
            phrase.guess(letter)
            alphabet.guess(letter)

    def eliminate_letters():
        """Mark 3 letters that are not in the phrase as guessed to remove them."""
        not_in_phrase = [
            c for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
            if c not in phrase.word and c not in alphabet.guessed
        ]
        choices = random.sample(not_in_phrase, min(3, len(not_in_phrase)))
        for c in choices:
            alphabet.guess(c)

    shop.on_reveal_consonant = reveal_consonant
    shop.on_reveal_vowel = reveal_vowel
    shop.on_eliminate_letters = eliminate_letters

    # Apply auto-guess upgrades silently at round start
    auto_guesses = shop.get_auto_guesses(phrase.word)
    for letter in auto_guesses:
        phrase.guess(letter)
        alphabet.guess(letter)

    return phrase, alphabet, strikes, topic


# --- Initialization ---
pygame.init()
screen = pygame.display.set_mode(SCREEN_SIZE)
pygame.display.set_caption('Word Game')
clock = pygame.time.Clock()
running = True

# Shared font used across all game objects
font = pygame.font.SysFont('Arial', 32)

# Streak and shop persist across rounds — only reset on loss
streak = Streak(font)
shop = Shop(font, *SCREEN_SIZE)

# Puzzle pool — shuffled list of eligible puzzles, popped one per round.
# Rebuilt from scratch after every loss, and also whenever the difficulty
# tier advances, so the pool always reflects the current window.
seen_puzzles = set()          # Texts of puzzles played this run
current_tier = get_difficulty_tier(streak.count)
remaining_puzzles = build_puzzle_pool(streak, seen_puzzles)

# Start the first round
phrase, alphabet, strikes, topic = reset_game(font, streak, shop, remaining_puzzles)
popup = None  # Active win/lose/game-complete popup, or None


def next_puzzle_available(remaining):
    """Return True if there are any puzzles left in the pool."""
    return len(remaining) > 0


def maybe_rebuild_pool():
    """
    Rebuild the puzzle pool if the difficulty tier has advanced since the
    pool was last built. Called after every win so newly-unlocked harder
    puzzles enter the pool and easy ones are phased out correctly.
    """
    global remaining_puzzles, current_tier
    new_tier = get_difficulty_tier(streak.count)
    if new_tier != current_tier:
        current_tier = new_tier
        remaining_puzzles = build_puzzle_pool(streak, seen_puzzles)


def start_next_round():
    """
    Attempt to start the next round. Returns the new game objects, or None
    if the puzzle pool is exhausted (triggering the game-complete popup).
    """
    maybe_rebuild_pool()
    if not next_puzzle_available(remaining_puzzles):
        return None
    return reset_game(font, streak, shop, remaining_puzzles)


# --- Game Loop ---
while running:
    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEBUTTONDOWN:
            if popup and popup.handle_click(event.pos):
                if popup.game_complete:
                    # Full reset — clear everything and start a new run
                    streak.lose()
                    shop.reset()
                    seen_puzzles.clear()
                    current_tier = get_difficulty_tier(streak.count)
                    remaining_puzzles = build_puzzle_pool(streak, seen_puzzles)
                    phrase, alphabet, strikes, topic = reset_game(font, streak, shop, remaining_puzzles)
                    popup = None
                else:
                    result = start_next_round()
                    if result is None:
                        popup = Popup('You Beat the Game!', font, *SCREEN_SIZE, game_complete=True)
                    else:
                        phrase, alphabet, strikes, topic = result
                        popup = None
            else:
                shop.handle_click(event.pos)

        if event.type == pygame.KEYDOWN:
            # Enter closes whichever overlay is currently open
            if event.key == pygame.K_RETURN:
                if popup:
                    if popup.game_complete:
                        streak.lose()
                        shop.reset()
                        seen_puzzles.clear()
                        current_tier = get_difficulty_tier(streak.count)
                        remaining_puzzles = build_puzzle_pool(streak, seen_puzzles)
                        phrase, alphabet, strikes, topic = reset_game(font, streak, shop, remaining_puzzles)
                        popup = None
                    else:
                        result = start_next_round()
                        if result is None:
                            popup = Popup('You Beat the Game!', font, *SCREEN_SIZE, game_complete=True, streak=streak.count)
                        else:
                            phrase, alphabet, strikes, topic = result
                            popup = None
                elif shop.visible:
                    shop.visible = False

        # Only accept letter guesses when no overlay is open
        if event.type == pygame.KEYDOWN and popup is None and not shop.visible:
            if event.unicode.isalpha():
                letter = event.unicode.upper()

                if letter not in alphabet.guessed:
                    matched = phrase.guess(letter)
                    alphabet.guess(letter)

                    if not matched:
                        # Check if a free guess consumable blocks this strike
                        if not shop.use_free_guess():
                            strikes.add_strike()

                    if phrase.is_solved():
                        seen_puzzles.add(phrase.word)
                        streak.win()
                        # Award money based on puzzle difficulty and strikes remaining
                        difficulty = calculate_difficulty(phrase.word, topic.topic)
                        strikes_left = strikes.max_strikes - strikes.count
                        shop.earn(difficulty, strikes_left, streak.count)
                        popup = Popup('You Win!', font, *SCREEN_SIZE, phrase=phrase.word)
                    elif strikes.is_game_over():
                        streak.lose()
                        shop.reset()  # Reset all upgrades and money on loss
                        # Full reset of pool and seen set after a loss
                        seen_puzzles.clear()
                        current_tier = get_difficulty_tier(streak.count)
                        remaining_puzzles = build_puzzle_pool(streak, seen_puzzles)
                        popup = Popup('You Lose!', font, *SCREEN_SIZE, phrase=phrase.word, streak=streak.previous)

    # --- Drawing ---
    screen.fill('black')
    phrase.draw(screen)
    alphabet.draw(screen)
    strikes.draw(screen)
    topic.draw(screen)
    streak.draw(screen, shop.money)
    shop.draw(screen)

    if popup:
        popup.draw(screen)

    pygame.display.update()

    # Cap at 30fps — no animation so 60fps is unnecessary
    clock.tick(30)

pygame.quit()