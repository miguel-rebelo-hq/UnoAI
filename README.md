# UNO AI Game

A fully functional UNO card game implementation in Python with an interactive GUI and intelligent AI opponents.

## Overview

UnoAI is a complete implementation of the classic UNO card game featuring:

- **1 Human Player vs 3 AI Bots** - Strategic gameplay with personality-based AI decision-making
- **Official UNO Rules** - Complete rule enforcement including draw penalties, special cards, and the +4 challenge system
- **Interactive GUI** - Clean, modern tkinter interface with real-time game state visualization
- **Intelligent AI** - Adaptive AI opponents with dynamic personality profiles (Aggressive, Conservative, Monochrome, Chaotic, Finisher)
- **Match Scoring System** - Track wins across multiple rounds with a target score of 500 points
- **Full +4 Challenge Support** - Challenge illegal +4 plays with proper penalty escalation

## Features

### Game Mechanics
-  All official UNO card types (0-9, Skip, Reverse, +2, Wild, +4)
-  Proper color and value matching validation
-  Penalty card system with draw mechanics
-  Direction reversal support
-  Deck recycling when cards run out
-  Official scoring system (0-9 cards = face value, action cards = 20 points, wilds = 50 points)

### AI System
- **5 Dynamic Personas**: Each bot uses a randomized personality that influences decision-making
- **Strategic Scoring**: Cards are scored based on:
  - Impact on game (penalty cards weighted higher)
  - Opponent hand status (higher priority against players close to winning)
  - Color optimization and diversity
  - High-point card disposal
- **Legal Play Enforcement**: AI respects all game rules including +4 legality checks

### User Interface
- Hand pagination for better visibility when holding many cards
- Real-time bot status display showing card counts and UNO warnings
- Game log tracking all moves and actions
- Scoreboard for match progression
- Clear visual indicators for playable vs non-playable cards
- Turn order and direction display

## Requirements

- Python 3.8+
- tkinter (usually included with Python)

## Installation

1. **Clone the repository** or download the project files
2. **Navigate to the project directory**:
   ```bash
   cd UnoAI
   ```
3. **Install dependencies** (if needed):
   ```bash
   pip install -r requirements.txt
   ```
4. **Run the game**:
   ```bash
   python main.py
   ```

## How to Play

### Starting a Game
- Click **"New Game"** to begin a new round
- The game starts with a random player and applies the starter card effects

### Your Turn
1. **Review your hand** - Use navigation arrows if you have more than 10 cards
2. **Play a card** - Click any highlighted card to play it:
   - **Number cards**: Match by color or number
   - **Action cards**: Skip, Reverse, +2
   - **Wild cards**: Choose a color after playing
3. **Draw a card** - If you have no valid moves, click "Draw card"
4. **Pass** - After drawing, if the drawn card isn't playable, click "Pass"

### Special Situations

**+4 Card Played Against You**:
- **Accept +4**: Draw 4 cards and lose your turn
- **Challenge +4**: Risk drawing 6 cards if the play was legal, but only 4 cards if illegal

**Wild Card Color Choice**:
- Select a color button to set the active color for all players

## Project Structure

```
UnoAI/
├── main.py              # GUI implementation (tkinter)
├── uno_logic.py         # Game logic and AI system
├── requirements.txt     # Python dependencies
├── settings.json        # Game configuration
└── README.md           # This file
```

## Technical Highlights

### Core Architecture
- **Game Class**: Manages game state, turn progression, and rule enforcement
- **Card Class**: Immutable card representation with display and matching logic
- **Deck Class**: Card management with shuffle and draw operations
- **Player Class**: Player state and hand management

### AI Decision Making
The `choose_best_move()` method evaluates all legal moves using a persona-based scoring system:

```python
score = base_impact * impact_multiplier
      + color_matching_bonus
      + color_diversity_bonus
      - wild_penalty
      + high_point_discard_bonus
```

Each bot randomly selects a persona per turn, creating varied and unpredictable gameplay.

### Rule Enforcement
- Full legality checking for +4 plays
- Proper penalty card stacking prevention
- Deck recycling with discard pile management
- Turn advancement with direction support
- Win condition detection

## Game Rules Summary

- **Players**: 1 human + 3 AI bots (4 total)
- **Starting Hand**: 7 cards per player
- **Draw Penalty**: +2 and +4 cards impose mandatory draws
- **Skip/Reverse**: Skip next player or reverse turn order
- **+4 Challenge**: Target can challenge illegal +4 plays
- **Winning**: First to empty their hand wins the round
- **Scoring**: Points from all opponents' remaining cards
- **Match Goal**: First to 500 points wins the match

## Configuration

Edit `settings.json` to customize:
- Game difficulty
- Visual preferences
- AI behavior parameters
- Target score for match completion

## Future Enhancements

- [ ] Difficulty levels for AI opponents
- [ ] Two-player and 4-human-player modes
- [ ] Game statistics and win history
- [ ] Sound effects and animations
- [ ] Network multiplayer support
- [ ] UNO call/challenge mechanics

## Author

Miguel - Personal Project (2026)

## License

This project is provided as-is for educational and portfolio purposes.

---

**Enjoying the game?** Feel free to fork, modify and improve the codebase!
