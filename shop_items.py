# ---------------------------------------------------------------------------
# Unified item schema — used by UPGRADES, CONSUMABLES, and PRESTIGE_ITEMS
# ---------------------------------------------------------------------------
#
#   id          str        Unique identifier.
#   label       str        Display name.
#   description str        Subtitle shown below the label.
#   cost        int        Cost of the first (or only) purchase.
#   cost_growth float|None  Multiplier applied per purchase: cost × growth^n.
#                          e.g. 2.0 → doubles each time, 1.5 → 50% increase.
#                          None → flat cost every time.
#   currency    str        'money' | 'stars'
#   max_owned   int|None   None → one-time purchase (disappears after buying).
#                          int  → repeatable up to this many times.
#   requires    str|None   id that must already be owned before this appears.
#
# Consumables are always currency='money', max_owned=None (unlimited, not
# tracked), cost_growth=None.  Their availability is also gated by live
# gameplay state checked separately in Shop._is_consumable_disabled().
# ---------------------------------------------------------------------------

UPGRADES = [
    {
        'id':          'free_consonant',
        'label':       'Free Consonant',
        'description': 'A random consonant is revealed each round',
        'cost':        50,
        'cost_growth': 2.0,
        'currency':    'money',
        'max_owned':   2,
        'requires':    None,
    },
    {
        'id':          'guaranteed_consonant',
        'label':       'Guaranteed Consonant',
        'description': 'Free consonant is guaranteed to be in the phrase',
        'cost':        100,
        'cost_growth': 2.0,
        'currency':    'money',
        'max_owned':   2,
        'requires':    'free_consonant',
    },
    {
        'id':          'free_vowel',
        'label':       'Free Vowel',
        'description': 'A random vowel is revealed each round',
        'cost':        100,
        'cost_growth': 2.0,
        'currency':    'money',
        'max_owned':   1,
        'requires':    None,
    },
    {
        'id':          'guaranteed_vowel',
        'label':       'Guaranteed Vowel',
        'description': 'Free vowel is guaranteed to be in the phrase',
        'cost':        200,
        'cost_growth': 2.0,
        'currency':    'money',
        'max_owned':   1,
        'requires':    'free_vowel',
    },
    {
        'id':          'extra_strike',
        'label':       'Extra Strike',
        'description': 'Gain an extra strike before losing',
        'cost':        250,
        'cost_growth': 2.0,
        'currency':    'money',
        'max_owned':   2,
        'requires':    None,
    },
]

CONSUMABLES = [
    {
        'id':          'reveal_consonant',
        'label':       'Reveal Consonant',
        'description': 'Reveals a random hidden consonant in the phrase',
        'cost':        25,
        'cost_growth': 1.2,
        'currency':    'money',
        'max_owned':   None,
        'requires':    None,
    },
    {
        'id':          'reveal_vowel',
        'label':       'Reveal Vowel',
        'description': 'Reveals a random hidden vowel in the phrase',
        'cost':        50,
        'cost_growth': 1.2,
        'currency':    'money',
        'max_owned':   None,
        'requires':    None,
    },
    {
        'id':          'eliminate_letters',
        'label':       'Eliminate 3 Letters',
        'description': 'Removes 3 wrong letters from the alphabet',
        'cost':        25,
        'cost_growth': None,
        'currency':    'money',
        'max_owned':   None,
        'requires':    None,
    },
    {
        'id':          'free_guess',
        'label':       'Free Guess',
        'description': 'Next guess costs nothing, right or wrong',
        'cost':        50,
        'cost_growth': None,
        'currency':    'money',
        'max_owned':   None,
        'requires':    None,
    },
    {
        'id':          'bonus_strike',
        'label':       'Bonus Strike',
        'description': 'Absorbs one wrong guess before a real strike',
        'cost':        75,
        'cost_growth': None,
        'currency':    'money',
        'max_owned':   None,
        'requires':    None,
    },
]

PRESTIGE_ITEMS = [
    {
        'id':          'old_man',
        'label':       'The Old Man',
        'description': 'Rescue a mysterious stranger.',
        'cost':        5,
        'cost_growth': None,
        'currency':    'stars',
        'max_owned':   None,
        'requires':    None,
    },
    {
        'id':          'topic_blue',
        'label':       'Blue',
        'description': 'Unlocks a new Blue category of puzzles.',
        'cost':        2,
        'cost_growth': None,
        'currency':    'stars',
        'max_owned':   None,
        'requires':    'old_man',
    },
    {
        'id':          'topic_green',
        'label':       'Green',
        'description': 'Unlocks a new Green category of puzzles.',
        'cost':        4,
        'cost_growth': None,
        'currency':    'stars',
        'max_owned':   None,
        'requires':    'topic_blue',
    },
    {
        'id':          'topic_yellow',
        'label':       'Yellow',
        'description': 'Unlocks a new Yellow category of puzzles.',
        'cost':        6,
        'cost_growth': None,
        'currency':    'stars',
        'max_owned':   None,
        'requires':    'topic_green',
    },
    {
        'id':          'topic_red',
        'label':       'Red',
        'description': 'Unlocks a new Red category of puzzles.',
        'cost':        8,
        'cost_growth': None,
        'currency':    'stars',
        'max_owned':   None,
        'requires':    'topic_yellow',
    },
    {
        'id':          'topic_purple',
        'label':       'Purple',
        'description': 'Unlocks a new Purple category of puzzles.',
        'cost':        10,
        'cost_growth': None,
        'currency':    'stars',
        'max_owned':   None,
        'requires':    'topic_red',
    },
    {
        'id':          'star_streak_discount',
        'label':       'Star Discount',
        'description': 'Each star is earned faster.',
        'cost':        3,
        'cost_growth': None,
        'currency':    'stars',
        'max_owned':   5,
        'requires':    None,
    },
]

# Ordered color topic ids — useful elsewhere for checking unlock state
COLOR_TOPIC_IDS = ['topic_blue', 'topic_green', 'topic_yellow', 'topic_red', 'topic_purple']