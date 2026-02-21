# Word Game

A Wheel of Fortune-style word guessing game built with Python and Pygame.

---

## How to Play

A secret phrase is hidden behind a row of blank letter slots. Guess letters one at a time using your keyboard to reveal the phrase. The topic category is displayed below the phrase to help you along.

- **Correct guess** — matching letters are revealed in the phrase
- **Wrong guess** — one strike is added
- **3 strikes** and you lose (more strikes can be unlocked)
- Reveal the full phrase before running out of strikes to win

---

## Upgrades

Build up your win streak to unlock passive upgrades that carry into every round:

| Streak | Upgrade |
|---|---|
| 3 | Free Consonant revealed at the start of each round |
| 5 | Free Consonant is guaranteed to be in the phrase |
| 7 | Gain a 4th strike |
| 9 | Free Vowel revealed at the start of each round |
| 11 | Free Vowel is guaranteed to be in the phrase |
| 13 | Gain a 5th strike |

Press the **Upgrades** button at the top of the screen to see your current progress.

---

## Installation

### Windows

1. Go to the [Releases](../../releases) page
2. Download `word-game-windows.exe`
3. Double click to run — no installation needed

### Mac

1. Go to the [Releases](../../releases) page
2. Download `word-game-mac.dmg`
3. Open the DMG and drag the app to your Applications folder
4. On first launch, right-click the app and choose **Open**
5. Click **Open** on the security warning — this only appears the first time

> The security warning appears because the app is not signed with an Apple Developer certificate. This is normal for independent projects.

### Linux

1. Go to the [Releases](../../releases) page
2. Download `word-game-linux.bin`
3. Open a terminal and make it executable:
```
chmod +x word-game-linux.bin
```
4. Run it:
```
./word-game-linux.bin
```

---

## Puzzle Categories

The game includes 275 puzzles across 11 categories:

- **Thing** — everyday objects
- **Proper Name** — famous people throughout history
- **Proper Place** — famous real-world landmarks and locations
- **Place** — ambiguous everyday locations
- **Phrase** — common idioms and expressions
- **Before & After** — two phrases sharing a middle word
- **Food & Drink** — dishes and drinks
- **Event** — holidays, ceremonies, and occasions
- **Around the House** — rooms, furniture, and household features
- **What Are You Doing?** — actions and activities
- **Occupation** — jobs and careers

---

## Controls

| Key | Action |
|---|---|
| A–Z | Guess a letter |
| Enter | Close popup or upgrades menu |