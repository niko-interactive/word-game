# Claude of Fortune

A Wheel of Fortune-style word guessing game built with Python and Pygame.

## Gameplay

A secret phrase is displayed as a row of blank letter slots. Guess letters one at a time using your keyboard. Reveal the full phrase before running out of strikes to win!

- ✅ Correct guess — matching letters are revealed
- ❌ Wrong guess — one strike is added (3 strikes and you lose)
- The topic of the phrase is shown in the top left (e.g. *Places*, *Food & Drink*)
- The full alphabet is displayed at the bottom — guessed letters turn grey
- A popup appears when you win or lose with a **Play Again** button

## Project Structure

```
claude_of_fortune/
├── main.py          # Game loop and entry point
├── constants.py     # Screen size and shared dimensions
├── letter.py        # Individual letter slot
├── word.py          # Manages the row of letter slots for the phrase
├── alphabet.py      # Displays A-Z at the bottom of the screen
├── strikes.py       # Tracks and displays strikes in the top right
├── topic.py         # Displays the puzzle category in the top left
├── puzzles.py       # Dataset of 100 phrase and topic pairs
└── README.md
```

## Requirements

- Python 3.x
- Pygame

## Installation

1. Clone or download the repository
2. Install dependencies:
```
pip install pygame
```
3. Run the game:
```
python main.py
```

## Adding Puzzles

Puzzles are stored in `puzzles.py` as a list of tuples:

```python
("PHRASE GOES HERE", "Category")
```

Just add new entries to the `PUZZLES` list. Categories currently in use:

- Things
- Places
- People
- Phrases
- Before & After
- Food & Drink
- Events
- Around the House

## Building an Executable

To share the game with friends who don't have Python installed:

```
pip install pyinstaller
pyinstaller --onefile main.py
```

The `.exe` will be output to the `dist/` folder.