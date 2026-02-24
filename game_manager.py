import random

from constants import CONSONANTS, SCREEN_SIZE, VOWELS
from puzzles import PUZZLES
from phrase import Phrase
from alphabet import Alphabet
from strikes import Strikes
from topic import Topic
from shop_items import UPGRADES


# Streak round required before the player can prestige — adjust for balancing
PRESTIGE_UNLOCK_STREAK = 50

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


class GameManager:
    """
    Owns all run and round state. Responsible for the puzzle lifecycle —
    building pools, advancing rounds, tracking streaks and money, and
    exposing consumable actions to the shop.

    Other classes (Shop, Streak, etc.) call into the manager to read or
    mutate state rather than holding it themselves.
    """

    def __init__(self, font, shop):
        self.font = font
        self.shop = shop

        # Run state — persists until a loss
        self.streak_count = 0
        self.previous_streak = 0   # Streak before last loss, used in lose popup
        self.money = 0
        self.purchased_upgrades = set()    # ids of permanently owned upgrades
        self.consumable_purchases = {}     # {consumable_id: count} — resets on loss/prestige

        # Meta state — never resets on loss
        self.total_rounds_completed = 0
        self.stars = 0                       # Spendable stars, earned via prestige
        self.prestige_count = 0              # Total number of times player has prestiged; never resets
        self._stars_display_unlocked = False  # Backing field — use stars_display_unlocked property

        # Prestige purchase state — permanent, never resets on loss
        self.prestige_owned        = set()   # ids of all one_time prestige items ever purchased
        self.old_man_unlocked      = False   # True after 'old_man' prestige item is purchased
        self.unlocked_color_topics = set()   # ids of color topic prestige items purchased
        self.star_streak_discounts = 0       # Times 'star_streak_discount' has been purchased (max 5)

        # Round state — rebuilt each round
        self.phrase = None
        self.alphabet = None
        self.strikes = None
        self.topic = None
        self.free_guess_active = False  # Consumed on any guess, right or wrong
        self.bonus_strikes = 0          # Extra lives consumed only on wrong guesses

        # Pool state
        self.seen_puzzles = set()
        self.remaining_puzzles = []
        self.current_tier = self._get_difficulty_tier()

        self._build_pool()
        self._start_round()

    # --- Money ---

    def earn(self, difficulty, strikes_left):
        """Award money based on difficulty, streak, and strikes remaining."""
        amount = round(
            difficulty / 10
            * max(self.streak_count / 10, 1)
            * (1 + 0.05 * strikes_left)
        )
        self.money += amount

    def spend(self, amount):
        """Deduct money. Returns True if successful, False if insufficient funds."""
        if self.money < amount:
            return False
        self.money -= amount
        return True

    def spend_stars(self, amount):
        """Deduct stars. Returns True if successful, False if insufficient stars."""
        if self.stars < amount:
            return False
        self.stars -= amount
        return True

    def purchase_prestige_item(self, item_id):
        """
        Apply the permanent effect of a prestige item after it has been paid for.
        Called by Shop._try_purchase_prestige_item after a successful deduction.
        """
        if item_id != 'star_streak_discount':
            self.prestige_owned.add(item_id)
        if item_id == 'old_man':
            self.old_man_unlocked = True
        elif item_id.startswith('topic_'):
            self.unlocked_color_topics.add(item_id)
        elif item_id == 'star_streak_discount':
            self.star_streak_discounts = min(self.star_streak_discounts + 1, 5)

    @property
    def star_buffer(self):
        """Stars pending for this run — simply the count of milestones passed at the current streak."""
        return self._count_stars_for_streak(self.streak_count)

    @property
    def stars_display_unlocked(self):
        """True if the star display should be shown."""
        return self._stars_display_unlocked or self.stars > 0 or self.star_buffer > 0

    @stars_display_unlocked.setter
    def stars_display_unlocked(self, value):
        self._stars_display_unlocked = value

    @property
    def can_prestige(self):
        """True when the player is eligible to prestige — streak is at the unlock threshold
        and there is at least one star waiting in the buffer."""
        return self.streak_count >= PRESTIGE_UNLOCK_STREAK and self.star_buffer > 0

    def prestige(self):
        """
        Convert buffered stars to spendable stars and reset the run, preserving all
        meta state. Behaves like lose() except star_buffer is cashed out rather than wiped.
        """
        self.stars += self.star_buffer
        self._stars_display_unlocked = True  # Latch permanently — stars have been earned
        self.prestige_count += 1
        self.previous_streak = self.streak_count
        self.streak_count = 0
        self.money = 0
        self.purchased_upgrades = set()
        self.consumable_purchases = {}
        self.seen_puzzles.clear()
        self.shop.reset()
        self.current_tier = self._get_difficulty_tier()
        self._build_pool()
        self._start_round()

    # --- Streak ---

    def win(self):
        """
        Handle a round win — record the puzzle as seen, increment streak,
        award money, and advance to the next round.
        Returns True if a next round was available, False if the game is complete.
        """
        self.seen_puzzles.add(self.phrase.word)
        self.streak_count += 1
        self.total_rounds_completed += 1


        difficulty = self._calculate_difficulty(self.phrase.word, self.topic.topic)
        strikes_left = self.strikes.max_strikes - self.strikes.count  # bonus strikes excluded intentionally
        self.earn(difficulty, strikes_left)
        return self._advance_round()

    def lose(self):
        """Handle a round loss — reset all run state and start fresh. Meta state is preserved."""
        self.previous_streak = self.streak_count
        self.streak_count = 0
        self.money = 0
        self.purchased_upgrades = set()
        self.consumable_purchases = {}
        self.seen_puzzles.clear()
        self.shop.reset()
        self.current_tier = self._get_difficulty_tier()
        self._build_pool()
        self._start_round()

    def max_strikes(self):
        """Return total strikes allowed based on purchased extra_strike upgrades."""
        count = sum(1 for k in self.purchased_upgrades if k == 'extra_strike' or k.startswith('extra_strike_'))
        return 3 + count

    def get_auto_guesses(self):
        """
        Return letters to auto-reveal at round start based on purchased upgrades.
        Each free_consonant/vowel purchase adds one auto-reveal slot.
        The matching guaranteed purchase makes that slot pull only from phrase letters.
        """
        guesses        = []
        phrase_letters = set(c for c in self.phrase.word if c.isalpha())

        free_consonants = sum(1 for k in self.purchased_upgrades
                              if k == 'free_consonant' or k.startswith('free_consonant_'))
        guar_consonants = sum(1 for k in self.purchased_upgrades
                              if k == 'guaranteed_consonant' or k.startswith('guaranteed_consonant_'))
        for slot in range(free_consonants):
            guaranteed = slot < guar_consonants
            available  = phrase_letters & CONSONANTS if guaranteed else CONSONANTS
            pool       = list(available - set(guesses))
            if not pool:
                pool = list(CONSONANTS - set(guesses))
            if pool:
                guesses.append(random.choice(pool))

        free_vowels = sum(1 for k in self.purchased_upgrades
                          if k == 'free_vowel' or k.startswith('free_vowel_'))
        guar_vowels = sum(1 for k in self.purchased_upgrades
                          if k == 'guaranteed_vowel' or k.startswith('guaranteed_vowel_'))
        for slot in range(free_vowels):
            guaranteed = slot < guar_vowels
            available  = phrase_letters & VOWELS if guaranteed else VOWELS
            pool       = list(available - set(guesses))
            if not pool:
                pool = list(VOWELS - set(guesses))
            if pool:
                guesses.append(random.choice(pool))

        return guesses

    def _star_milestones(self):
        """
        Return an ordered list of streak values at which a star is awarded.

        Stars 1–5: every 10 streaks (10, 20, 30, 40, 50).
        Star 6 onward: each gap grows by (10 - star_streak_discounts), minimum 1.
          e.g. with 0 discounts: gaps are 10, 20, 30 ... → 50, 70, 100, 140 ...
          e.g. with 1 discount:  increment is 9  → 50, 68, 95 ...
          e.g. with 5 discounts: increment is 5  → 50, 65, 85 ...

        We generate enough milestones to cover any realistic run (up to 200 stars).
        """
        milestones = []
        for n in range(1, 6):          # Stars 1–5 at 10, 20, 30, 40, 50
            milestones.append(n * 10)
        increment   = 10 - self.star_streak_discounts  # base gap growth per extra star
        increment   = max(increment, 1)
        gap         = 10 + increment      # gap from 5th star to 6th: 20 normally, 19 with 1 discount, etc.
        current     = 50
        for _ in range(195):           # Stars 6–200
            current += gap
            milestones.append(current)
            gap += increment
        return milestones

    def _count_stars_for_streak(self, streak):
        """Return how many star milestones fall at or below the given streak."""
        return sum(1 for m in self._star_milestones() if m <= streak)

    # --- Round Lifecycle ---

    def _advance_round(self):
        """
        Move to the next round. Rebuilds the pool if the difficulty tier
        has advanced. Returns True if a round was started, False if exhausted.
        """
        self._maybe_rebuild_pool()
        if not self.remaining_puzzles:
            return False
        self._start_round()
        return True

    def _start_round(self):
        """Set up all round state from the next puzzle in the pool."""
        text, topic_text = self.remaining_puzzles.pop()

        self.phrase = Phrase(text, self.font, *SCREEN_SIZE)
        self.alphabet = Alphabet(self.font, *SCREEN_SIZE)
        self.strikes = Strikes(self.font, SCREEN_SIZE[0], self.max_strikes())
        self.topic = Topic(topic_text, self.font, *SCREEN_SIZE)

        if self.phrase.letters:
            bottom = max(letter.rect.bottom for letter in self.phrase.letters)
            self.topic.update_position(bottom)

        # Apply auto-guess upgrades at round start
        for letter in self.get_auto_guesses():
            self.phrase.guess(letter)
            self.alphabet.guess(letter)

        self.free_guess_active = False
        self.solved_by_consumable = False  # Set True if a consumable reveal solves the puzzle
        # bonus_strikes intentionally not reset here — carries over between rounds

        # Register consumable callbacks now that phrase and alphabet exist
        self.shop.on_reveal_consonant = self._reveal_consonant
        self.shop.on_reveal_vowel = self._reveal_vowel
        self.shop.on_eliminate_letters = self._eliminate_letters
        self.shop.on_free_guess = self._grant_free_guess
        self.shop.on_bonus_strike = self._grant_bonus_strike

    # --- Consumable Actions ---
    # Registered as callbacks on the shop so it can trigger them on purchase.

    def _reveal_consonant(self):
        """Reveal a random hidden consonant from the current phrase."""
        hidden = [
            c for c in set(self.phrase.word.replace(' ', ''))
            if c in {'B','C','D','F','G','H','J','K','L','M',
                     'N','P','Q','R','S','T','V','W','X','Y','Z'}
            and c not in self.alphabet.guessed
        ]
        if hidden:
            letter = random.choice(hidden)
            self.phrase.guess(letter)
            self.alphabet.guess(letter)
            if self.phrase.is_solved():
                self.solved_by_consumable = True

    def _reveal_vowel(self):
        """Reveal a random hidden vowel from the current phrase."""
        hidden = [
            c for c in set(self.phrase.word.replace(' ', ''))
            if c in {'A', 'E', 'I', 'O', 'U'}
            and c not in self.alphabet.guessed
        ]
        if hidden:
            letter = random.choice(hidden)
            self.phrase.guess(letter)
            self.alphabet.guess(letter)
            if self.phrase.is_solved():
                self.solved_by_consumable = True

    def _eliminate_letters(self):
        """Mark 3 letters not in the phrase as guessed to remove them from the alphabet."""
        not_in_phrase = [
            c for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
            if c not in self.phrase.word and c not in self.alphabet.guessed
        ]
        choices = random.sample(not_in_phrase, min(3, len(not_in_phrase)))
        for c in choices:
            self.alphabet.guess(c)

    def _grant_free_guess(self):
        """Grant a free guess — will be consumed on the next guess regardless of outcome."""
        self.free_guess_active = True

    def _grant_bonus_strike(self):
        """
        Grant a bonus strike. If the player has used any strikes this round,
        recover the most recent one (flip a red X back to white) rather than
        adding a green X. Only adds a true bonus strike if no used strikes exist.
        """
        if self.strikes.count > 0:
            self.strikes.count -= 1
        else:
            self.bonus_strikes += 1

    # --- Guess Handling ---

    def guess(self, letter):
        """
        Process a letter guess. Order of operations:
        1. Free guess is consumed immediately on any guess, right or wrong.
        2. If wrong: bonus strike absorbs the hit before a real strike is added.
        Returns 'solved', 'correct', 'blocked' (free guess used),
        'bonus_strike' (bonus absorbed the wrong guess), 'strike', or 'game_over'.
        """
        free_guess_used = self.free_guess_active
        self.free_guess_active = False

        matched = self.phrase.guess(letter)
        self.alphabet.guess(letter)

        if matched:
            if self.phrase.is_solved():
                return 'solved'
            return 'correct'

        if free_guess_used:
            return 'blocked'

        if self.bonus_strikes > 0:
            self.bonus_strikes -= 1
            return 'bonus_strike'

        self.strikes.add_strike()
        if self.strikes.is_game_over():
            return 'game_over'
        return 'strike'

    # --- Pool Management ---

    def _build_pool(self):
        """Build a shuffled pool of eligible unseen puzzles for the current difficulty range."""
        min_diff, max_diff = self._get_difficulty_range()
        pool = [
            (text, topic) for text, topic in PUZZLES
            if text not in self.seen_puzzles
            and min_diff <= self._calculate_difficulty(text, topic) <= max_diff
        ]
        if not pool:
            pool = [(text, topic) for text, topic in PUZZLES if text not in self.seen_puzzles]
        if not pool:
            pool = list(PUZZLES)
        random.shuffle(pool)
        self.remaining_puzzles = pool

    def _maybe_rebuild_pool(self):
        """Rebuild the pool if the difficulty tier has advanced since last build."""
        new_tier = self._get_difficulty_tier()
        if new_tier != self.current_tier:
            self.current_tier = new_tier
            self._build_pool()

    # --- Difficulty ---

    def _calculate_difficulty(self, phrase, category):
        """
        Calculate a numeric difficulty score for a puzzle.
        Formula: (unique_letters * rarity * avg_word_length) / num_words
        """
        unique_letters = set(phrase.replace(' ', ''))
        free = FREE_LETTERS_BY_CATEGORY.get(category, set())
        unique_letters -= free
        rarity = sum(SCRABBLE[c] for c in unique_letters)
        words = phrase.split()
        avg_word_length = sum(len(w) for w in words) / len(words)
        return (len(unique_letters) * rarity * avg_word_length) / len(words)

    def _get_difficulty_range(self):
        """Return (min, max) difficulty for the current streak."""
        n = self.streak_count
        if n >= 30:   return 500, float('inf')
        elif n >= 20: return 350, float('inf')
        elif n >= 12: return 200, 700
        elif n >= 8:  return 100, 500
        elif n >= 4:  return 0, 350
        else:         return 0, 200

    def _get_difficulty_tier(self):
        """Return a tier index that increments each time the difficulty window changes."""
        n = self.streak_count
        if n >= 11:   return 5
        elif n >= 9:  return 4
        elif n >= 7:  return 3
        elif n >= 5:  return 2
        elif n >= 3:  return 1
        else:         return 0

    # --- Draw ---

    def draw(self, screen):
        """Draw all round objects."""
        self.phrase.draw(screen)
        self.alphabet.draw(screen)
        self.strikes.draw(screen, self.bonus_strikes, self.free_guess_active)
        self.topic.draw(screen)