# Word Game

A Wheel of Fortune-style word guessing game built with Python and Pygame.

---

## How to Play

A secret phrase is hidden behind a row of blank letter slots. Guess letters one at a time using your keyboard. The category is shown below the phrase to help narrow it down.

- **Correct guess** — all matching letters are revealed in the phrase
- **Wrong guess** — one strike is added in the top right corner
- **3 strikes** and you lose the round
- Reveal the full phrase before running out of strikes to win

Every win extends your streak. Every loss resets everything — your streak, your money, and your upgrades — so each run starts from scratch.

---

## The Shop

Press the **Shop** button at the top of the screen at any time, even mid-round. The shop has two tabs: Upgrades and Consumables.

### Upgrades

Upgrades are permanent until you lose. They apply automatically at the start of every round. Some require an earlier upgrade to be purchased first.

| Cost | Upgrade |
|---|---|
| $50 | **Free Consonant 1** — a random consonant is revealed at the start of each round |
| $100 | **Guaranteed Consonant 1** — that consonant is guaranteed to be in the phrase |
| $100 | **Free Consonant 2** — a second consonant revealed each round |
| $200 | **Guaranteed Consonant 2** — guaranteed to be in the phrase |
| $100 | **Free Vowel 1** — a random vowel is revealed at the start of each round |
| $200 | **Guaranteed Vowel 1** — that vowel is guaranteed to be in the phrase |
| $250 | **4th Strike** — gain an extra strike before losing |
| $500 | **5th Strike** — gain yet another extra strike |

### Consumables

Consumables are single-use and take effect immediately when purchased. Some are disabled when they would have no effect or when a limit is already reached.

| Cost | Consumable |
|---|---|
| $25 | **Reveal Consonant** — reveals a random hidden consonant in the current phrase |
| $50 | **Reveal Vowel** — reveals a random hidden vowel in the current phrase |
| $25 | **Eliminate 3 Letters** — removes 3 letters not in the phrase from the alphabet |
| $50 | **Free Guess** — your next guess costs nothing, whether right or wrong |
| $75 | **Bonus Strike** — an extra life shown as a green X; absorbed on your next wrong guess. If you have used strikes, this recovers the most recent one instead. Carries over to the next round. |

### Earning Money

You earn money at the end of each won round. Harder puzzles pay more, longer streaks pay more, and leaving more strikes unused pays a bonus:

> `money earned = difficulty / 10 × max(streak / 10, 1) × (1 + 0.05 × strikes remaining)`

---

## Strikes

Strikes are shown as X marks in the top right corner.

- **White X** — a strike you haven't used yet
- **Red X** — a used strike
- **Green X** — a bonus strike from a consumable; absorbed before regular strikes

---

## Puzzle Categories

The game includes ~1,000 puzzles across 10 categories:

- **Thing** — everyday objects
- **Proper Name** — famous people throughout history
- **Proper Place** — famous real-world landmarks and locations
- **Place** — ambiguous everyday locations
- **Phrase** — common idioms and expressions
- **Food & Drink** — dishes and drinks
- **Event** — holidays, ceremonies, and occasions
- **Around the House** — rooms, furniture, and household features
- **What Are You Doing?** — actions and activities
- **Occupation** — jobs and careers

No puzzle is ever repeated within a single run. If you somehow clear every available puzzle, you'll see a special screen — but that's a very long way off.

---

## Installation

### Windows

1. Go to the [Releases](../../releases) page
2. Download `word-game-windows.exe`
3. Double-click to run — no installation needed

> A security warning may appear because the app is not signed with a certificate. This is normal for independent projects. Click **Run anyway** to proceed.

### Mac

1. Go to the [Releases](../../releases) page
2. Download `word-game-mac.dmg`
3. Open the DMG and drag the app to your Applications folder
4. On first launch, right-click the app and choose **Open**
5. Click **Open** on the security warning — this only appears the first time

> The warning appears because the app is not signed with an Apple Developer certificate. This is normal for independent projects.

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

## Controls

| Key | Action |
|---|---|
| A–Z | Guess a letter |
| Enter | Close popup