# Word Game

A Wheel of Fortune-style word guessing game built with Python and Pygame.

---

## How to Play

A secret phrase is hidden behind a row of blank letter slots. Guess letters one at a time using your keyboard to reveal the phrase. The category is shown below the phrase to help narrow it down.

- **Correct guess** — all matching letters are revealed in the phrase
- **Wrong guess** — one strike is added in the top right
- **3 strikes** and you lose (more can be unlocked via the shop)
- Reveal the full phrase before running out of strikes to win the round

Every win extends your streak. Every loss resets it — and resets your shop upgrades and money too, so each run starts from scratch.

---

## The Shop

Press the **Shop** button at the top of the screen at any time, even mid-round. Upgrades purchased will become in effect at the start of the next round. Consumables will be used immediately. Your money carries between rounds but resets on a loss.

### Upgrades

Upgrades are permanent until you lose and apply passively at the start of every round. Some require a cheaper upgrade to be purchased first.

| Cost | Upgrade |
|---|---|
| $50 | **Free Consonant** — a random consonant is revealed at the start of each round |
| $100 | **Guaranteed Consonant** — the free consonant is guaranteed to appear in the phrase |
| $100 | **Free Vowel** — a random vowel is revealed at the start of each round |
| $200 | **Guaranteed Vowel** — the free vowel is guaranteed to appear in the phrase |
| $250 | **4th Strike** — gain an extra strike before losing |
| $500 | **5th Strike** — gain yet another extra strike |

Guaranteed Consonant requires Free Consonant, and Guaranteed Vowel requires Free Vowel.

### Consumables

Consumables are single-use and take effect immediately when purchased.

| Cost | Consumable |
|---|---|
| $25 | **Reveal Consonant** — reveals a random hidden consonant in the current phrase |
| $50 | **Reveal Vowel** — reveals a random hidden vowel in the current phrase |
| $25 | **Eliminate 3 Letters** — removes 3 letters that are not in the phrase from the alphabet |
| $50 | **Free Guess** — your next wrong guess won't cost a strike |

### Earning Money

You earn money at the end of each won round. Harder puzzles pay more, longer streaks pay more, and leaving more strikes unused pays a small bonus:

> `difficulty / 10 × max(streak / 10, 1) × (1 + 0.05 × strikes remaining)`

---

## Difficulty

Puzzles get harder as your streak grows. Early rounds draw from a pool of easier puzzles — as your streak climbs, a minimum difficulty floor is introduced and the ceiling rises, so straightforward puzzles are phased out and tougher ones take their place.

| Streak | Difficulty Range |
|---|---|
| 0–2 | Easy only |
| 3–4 | Easy to medium |
| 5–6 | Medium to hard |
| 7–8 | Medium to hardest |
| 9–10 | Hard to hardest |
| 11+ | Hardest puzzles only |

No puzzle is ever repeated within a single run. If you somehow clear every available puzzle, you'll see a special screen — but that's a very long way off.

---

## Puzzle Categories

The game includes 1,000 puzzles across 10 categories:

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

## Controls

| Key | Action |
|---|---|
| A–Z | Guess a letter |
| Enter | Close popup or shop |