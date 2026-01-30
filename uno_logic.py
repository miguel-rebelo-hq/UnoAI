from __future__ import annotations
from dataclasses import dataclass
import random
from typing import List, Optional, Tuple
import math
import copy

COLORS = ["Red", "Yellow", "Green", "Blue"]
VALUES = [str(n) for n in range(0, 10)]  # 0-9
ACTIONS = ["Skip", "Reverse", "+2"]
WILDS = ["Wild", "+4"]


@dataclass(frozen=True)
class Card:
    color: Optional[str]  # None for wilds
    value: str            # "0"-"9", "Skip", "Reverse", "+2", "Wild", "+4"

    def is_wild(self) -> bool:
        return self.value in WILDS

    def is_action(self) -> bool:
        return self.value in ACTIONS or self.is_wild()

    def display(self) -> str:
        if self.color and not self.is_wild():
            return f"{self.color} {self.value}"
        if self.is_wild():
            # Wilds display without color or with chosen color elsewhere
            return self.value
        return f"{self.value}"

    def matches(self, current_color: Optional[str], top_card: Card) -> bool:
        """Return True if this card can be played on top_card given current_color.
        current_color overrides color matching when a Wild was set.
        """
        if self.is_wild():
            return True
        # Matching by color: use current_color if set, else top_card.color
        effective_color = current_color if current_color else top_card.color
        if self.color == effective_color:
            return True
        # Matching by value/symbol
        if self.value == top_card.value:
            return True
        return False


class Deck:
    def __init__(self) -> None:
        self.cards: List[Card] = []
        self._build_deck()
        self.shuffle()

    def _build_deck(self) -> None:
        self.cards.clear()
        # Number cards
        for color in COLORS:
            # one zero
            self.cards.append(Card(color, "0"))
            # two of 1-9
            for n in range(1, 10):
                self.cards.append(Card(color, str(n)))
                self.cards.append(Card(color, str(n)))
        # Action cards (2 of each per color)
        for color in COLORS:
            for action in ACTIONS:
                self.cards.append(Card(color, action))
                self.cards.append(Card(color, action))
        # Wilds (4 of each)
        for _ in range(4):
            self.cards.append(Card(None, "Wild"))
            self.cards.append(Card(None, "+4"))

    def shuffle(self) -> None:
        random.shuffle(self.cards)

    def draw(self, n: int = 1) -> List[Card]:
        drawn: List[Card] = []
        for _ in range(n):
            if not self.cards:
                break
            drawn.append(self.cards.pop())
        return drawn

    def add_cards(self, cards: List[Card]) -> None:
        self.cards.extend(cards)
        self.shuffle()


class Player:
    def __init__(self, name: str, is_human: bool = False) -> None:
        self.name = name
        self.is_human = is_human
        self.hand: List[Card] = []

    def draw(self, deck: Deck, n: int = 1) -> List[Card]:
        cards = deck.draw(n)
        self.hand.extend(cards)
        return cards

    def remove_card(self, card: Card) -> None:
        self.hand.remove(card)


class Game:
    def __init__(self, num_players: int = 4) -> None:
        # Official request: 4 players only (1 human + 3 bots)
        assert num_players == 4, "Game must have exactly 4 players (you + 3 bots)"
        self.num_players = num_players
        self.players: List[Player] = []
        self.deck = Deck()
        self.discard_pile: List[Card] = []
        self.current_index = 0
        self.direction = 1  # 1 for clockwise, -1 for counter-clockwise
        self.current_color: Optional[str] = None  # active color after wild
        self.game_over = False
        # Turn control
        self.drew_this_turn: bool = False
        self.last_drawn_card: Optional[Card] = None
        # Penalty tracking (target index, cards drawn)
        self.last_penalty: Optional[Tuple[int, int]] = None
        # Track the winner of the round (index)
        self.winner_index: Optional[int] = None
        # Pending states
        self.pending_plus4: Optional[dict] = None  # {played_by, target, was_legal}
        self.pending_initial_wild_for: Optional[int] = None  # index who must choose starting color

    def setup(self) -> None:
        # Create players: Player 1 human, rest bots named 2..4 to match UI order
        self.players = [Player("You", is_human=True)]
        for i in range(2, self.num_players + 1):
            self.players.append(Player(f"Bot {i}"))

        # Thoroughly shuffle deck before dealing
        for _ in range(3):
            self.deck.shuffle()

        # Deal 7 cards each
        for _ in range(7):
            for p in self.players:
                p.draw(self.deck, 1)

        # Flip starter card (never +4 as first card per rules)
        first = self._draw_first_non_wild_plus4()
        self.discard_pile.append(first)

        # Randomize starting player
        self.current_index = random.randrange(len(self.players))
        # Reset per-turn flags
        self.drew_this_turn = False
        self.last_drawn_card = None
        self.last_penalty = None
        self.game_over = False
        self.winner_index = None
        self.pending_plus4 = None
        self.pending_initial_wild_for = None

        # Apply official first-card effects
        if first.value == "Wild":
            # First player chooses starting color before any play
            self.current_color = None
            self.pending_initial_wild_for = self.current_index
        elif first.value == "Reverse":
            # Reverse direction, next player (in new direction) starts
            self.direction *= -1
            self.advance_turn(1)
            # Set current color to first card's color
            self.current_color = first.color
        elif first.value == "Skip":
            # First player is skipped
            self.current_color = first.color
            self.advance_turn(1)
        elif first.value == "+2":
            # First player draws 2 and is skipped
            self.current_color = first.color
            target = self.current_index
            self.draw_cards(target, 2)
            self.last_penalty = (target, 2)
            self.advance_turn(1)
        else:
            # Number/symbol – just set color and start with current_index
            self.current_color = first.color

    def _draw_first_non_wild_plus4(self) -> Card:
        # Ensure the first card is not a +4; if empty, reshuffle from discard
        while True:
            if not self.deck.cards:
                self.deck._build_deck()
                self.deck.shuffle()
            card = self.deck.draw(1)[0]
            if card.value != "+4":
                return card
            else:
                self.deck.cards.insert(0, card)
                self.deck.shuffle()

    def top_card(self) -> Card:
        return self.discard_pile[-1]

    # --- Helpers for rule enforcement ---
    def effective_color(self) -> Optional[str]:
        return self.current_color if self.current_color else self.top_card().color

    def player_has_color(self, player_idx: int, color: Optional[str]) -> bool:
        if color is None:
            return False
        for c in self.players[player_idx].hand:
            if c.color == color:
                return True
        return False

    def can_play_plus4(self, player_idx: int) -> bool:
        # +4 legality at time of play (used for challenge resolution); not enforced upfront
        eff = self.effective_color()
        return not self.player_has_color(player_idx, eff)

    def can_play_card(self, player_idx: int, card: Card) -> Tuple[bool, Optional[str]]:
        # Block any normal action while +4 challenge or initial wild color choice is pending
        if self.pending_plus4 is not None:
            return False, "+4 is pending: accept or challenge first"
        if self.pending_initial_wild_for is not None and player_idx == self.pending_initial_wild_for:
            return False, "Choose a starting color first"
        if card not in self.players[player_idx].hand:
            return False, "Card not in hand"
        if not self.is_playable(card):
            return False, "Card not playable"
        # After drawing, only the drawn card may be played this turn
        if self.drew_this_turn and player_idx == self.current_index:
            if self.last_drawn_card is None or card is not self.last_drawn_card:
                return False, "After drawing, you may only play the drawn card"
        return True, None

    def next_player_index(self, steps: int = 1) -> int:
        return (self.current_index + steps * self.direction) % len(self.players)

    def advance_turn(self, steps: int = 1) -> None:
        self.current_index = self.next_player_index(steps)
        # Reset turn state
        self.drew_this_turn = False
        self.last_drawn_card = None

    def is_plus4_pending(self) -> bool:
        return self.pending_plus4 is not None

    def is_plus4_pending_for(self, player_idx: int) -> bool:
        return self.pending_plus4 is not None and self.pending_plus4.get("target") == player_idx

    def set_initial_wild_color(self, color: str) -> Tuple[bool, Optional[str]]:
        if self.pending_initial_wild_for is None:
            return False, None
        if color not in COLORS:
            return False, "Invalid color"
        self.current_color = color
        self.pending_initial_wild_for = None
        return True, None

    def play_card(self, player_idx: int, card: Card, chosen_color: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        if self.game_over:
            return False, "Game is over"
        if self.pending_plus4 is not None:
            return False, "+4 is pending: resolve it first"
        if self.pending_initial_wild_for is not None and player_idx == self.pending_initial_wild_for:
            return False, "Choose a starting color first"
        if player_idx != self.current_index:
            return False, "It's not your turn"
        if card not in self.players[player_idx].hand:
            return False, "Card not in hand"
        if not self.is_playable(card):
            return False, "Card not playable"

        prev_effective_color = self.effective_color()
        player = self.players[player_idx]
        player.remove_card(card)
        self.discard_pile.append(card)

        if card.is_wild():
            if chosen_color not in COLORS:
                return False, "Choose a valid color for Wild"
            self.current_color = chosen_color
        else:
            self.current_color = card.color

        self._apply_action_effect(card, prev_effective_color=prev_effective_color)

        # Win ends round immediately unless +4 resolution still pending
        if len(player.hand) == 0 and self.pending_plus4 is None:
            self.game_over = True
            self.winner_index = player_idx

        return True, None

    def is_playable(self, card: Card) -> bool:
        return card.matches(self.current_color, self.top_card())

    def get_valid_moves(self, player_idx: int) -> List[Card]:
        player = self.players[player_idx]
        return [c for c in player.hand if self.is_playable(c)]

    def get_valid_moves_enforced(self, player_idx: int) -> List[Card]:
        # +4 legality not enforced here (challenge handles it)
        return self.get_valid_moves(player_idx)

    def allowed_moves(self, player_idx: int) -> List[Card]:
        # If a +4 is pending or initial wild color is pending, no normal plays are allowed
        if self.pending_plus4 is not None:
            return []
        if self.pending_initial_wild_for is not None and player_idx == self.pending_initial_wild_for:
            return []
        if player_idx != self.current_index:
            return []
        if self.drew_this_turn:
            if self.last_drawn_card and self.is_playable(self.last_drawn_card):
                # Ensure the card is still in hand (it should be)
                if self.last_drawn_card in self.players[player_idx].hand:
                    return [self.last_drawn_card]
            return []
        return self.get_valid_moves_enforced(player_idx)

    def can_draw(self, player_idx: int) -> Tuple[bool, Optional[str]]:
        if self.game_over:
            return False, "Game is over"
        if self.pending_plus4 is not None:
            return False, "+4 is pending: accept or challenge"
        if self.pending_initial_wild_for is not None and player_idx == self.pending_initial_wild_for:
            return False, "Choose a starting color first"
        if player_idx != self.current_index:
            return False, "It's not your turn"
        if self.drew_this_turn:
            return False, "You can draw only 1 card per turn"
        return True, None

    def draw_one_action(self, player_idx: int) -> Tuple[bool, Optional[str], Optional[Card]]:
        ok, err = self.can_draw(player_idx)
        if not ok:
            return False, err, None
        if len(self.deck.cards) < 1:
            self._recycle_discard_into_deck()
        drawn = self.players[player_idx].draw(self.deck, 1)
        card = drawn[0]
        self.drew_this_turn = True
        self.last_drawn_card = card
        return True, None, card

    def can_pass(self, player_idx: int) -> Tuple[bool, Optional[str]]:
        if self.game_over:
            return False, "Game is over"
        if self.pending_plus4 is not None:
            return False, "+4 is pending: accept or challenge"
        if self.pending_initial_wild_for is not None and player_idx == self.pending_initial_wild_for:
            return False, "Choose a starting color first"
        if player_idx != self.current_index:
            return False, "It's not your turn"
        if not self.drew_this_turn:
            return False, "You need to draw before passing"
        return True, None

    def _apply_action_effect(self, card: Card, initial: bool = False, prev_effective_color: Optional[str] = None) -> None:
        """Apply effects of action cards. For +4, use prev_effective_color to evaluate legality before the wild color change."""
        prev_idx = self.current_index
        # Clear previous penalty info
        self.last_penalty = None
        # Determine targets relative to the player who played the card
        if initial:
            target_idx = self.current_index
        else:
            target_idx = self.next_player_index(1)

        if card.value == "Skip":
            self.advance_turn(2)
        elif card.value == "Reverse":
            self.direction *= -1
            self.advance_turn(1)
        elif card.value == "+2":
            self.draw_cards(target_idx, 2)
            self.last_penalty = (target_idx, 2)
            self.advance_turn(2)
        elif card.value == "Wild":
            self.advance_turn(1)
        elif card.value == "+4":
            # Use prev_effective_color to evaluate legality
            if prev_effective_color is None:
                was_legal = True
            else:
                was_legal = not self.player_has_color(prev_idx, prev_effective_color)
            self.pending_plus4 = {"played_by": prev_idx, "target": target_idx, "was_legal": was_legal}
            self.current_index = target_idx
        else:
            self.advance_turn(1)
        if self.current_index == prev_idx and card.value != "+4":
            self.advance_turn(1)

    # --- +4 Challenge resolution ---
    def accept_plus4(self, player_idx: int) -> Tuple[bool, Optional[str]]:
        if self.pending_plus4 is None or self.pending_plus4.get("target") != player_idx:
            return False, None
        played_by = self.pending_plus4["played_by"]
        self.draw_cards(player_idx, 4)
        self.last_penalty = (player_idx, 4)
        self.pending_plus4 = None
        # If +4 player had no cards (played +4 as last card), they win now
        if len(self.players[played_by].hand) == 0:
            self.game_over = True
            self.winner_index = played_by
            return True, None
        self.advance_turn(1)
        return True, None

    def challenge_plus4(self, player_idx: int) -> Tuple[bool, Optional[str], bool]:
        if self.pending_plus4 is None or self.pending_plus4.get("target") != player_idx:
            return False, None, False
        played_by = self.pending_plus4["played_by"]
        was_legal = self.pending_plus4["was_legal"]
        if was_legal:
            self.draw_cards(player_idx, 6)
            self.last_penalty = (player_idx, 6)
            self.pending_plus4 = None
            # If +4 player had no cards (played +4 as last card), they win now
            if len(self.players[played_by].hand) == 0:
                self.game_over = True
                self.winner_index = played_by
                return True, None, was_legal
            self.advance_turn(1)
        else:
            self.draw_cards(played_by, 4)
            self.last_penalty = (played_by, 4)
            self.pending_plus4 = None
            # current_index remains with challenger
        return True, None, was_legal

    # --- Scoring helpers (official UNO scoring) ---
    @staticmethod
    def card_points(card: Card) -> int:
        if card.value in [str(n) for n in range(0, 10)]:
            return int(card.value)
        if card.value in ("Skip", "Reverse", "+2"):
            return 20
        if card.value in ("Wild", "+4"):
            return 50
        return 0

    def hand_points_for_player(self, player_idx: int) -> int:
        return sum(Game.card_points(c) for c in self.players[player_idx].hand)

    def all_hands_points(self) -> List[int]:
        return [self.hand_points_for_player(i) for i in range(len(self.players))]

    def winner_points(self) -> int:
        if not self.game_over or self.winner_index is None:
            return 0
        total = 0
        for i, p in enumerate(self.players):
            if i == self.winner_index:
                continue
            total += self.hand_points_for_player(i)
        return total

    def current_player(self) -> Player:
        return self.players[self.current_index]

    # --- Bot helpers and AI ---
    def choose_color_for_bot(self, player_idx: int) -> str:
        """Pick the most frequent color in bot's hand; fallback random."""
        hand = self.players[player_idx].hand
        counts = {c: 0 for c in COLORS}
        for card in hand:
            if card.color in COLORS:
                counts[card.color] += 1
        best_color = max(counts, key=lambda c: counts[c])
        if counts[best_color] == 0:
            return random.choice(COLORS)
        return best_color

    def _color_counts(self, cards: List[Card]) -> dict:
        counts = {c: 0 for c in COLORS}
        for c in cards:
            if c.color in COLORS:
                counts[c.color] += 1
        return counts

    def _best_color_after_play(self, player_idx: int, played: Card) -> str:
        # Choose color maximizing remaining hand color count after removing played
        hand = list(self.players[player_idx].hand)
        try:
            hand.remove(played)
        except ValueError:
            pass
        counts = self._color_counts(hand)
        best = max(counts, key=lambda k: counts[k])
        return best if counts[best] > 0 else random.choice(COLORS)

    def _distinct_colors_after(self, player_idx: int, played: Card, chosen_color: Optional[str]) -> int:
        hand = list(self.players[player_idx].hand)
        try:
            hand.remove(played)
        except ValueError:
            pass
        colors = set([c.color for c in hand if c.color in COLORS])
        return len(colors)

    def _pick_persona(self) -> dict:
        personas = [
            {  # Aggressive
                "name": "Aggressive",
                "impact_mult": {"+4": 1.4, "+2": 1.3, "Skip": 1.2, "Reverse": 1.0, "_default": 1.0},
                "color_bias": 1.0,
                "diversity_bias": 1.0,
                "wild_penalty": 2.0,
                "high_points_bias": 0.05,
                "random_prob": 0.08,
                "next_uno_scale": 1.2,
            },
            {  # Conservative
                "name": "Conservative",
                "impact_mult": {"+4": 0.9, "+2": 0.95, "Skip": 1.0, "Reverse": 1.0, "_default": 1.1},
                "color_bias": 1.2,
                "diversity_bias": 1.1,
                "wild_penalty": 5.0,
                "high_points_bias": 0.02,
                "random_prob": 0.07,
                "next_uno_scale": 1.0,
            },
            {  # Monochrome (color focusing)
                "name": "Monochrome",
                "impact_mult": {"+4": 1.0, "+2": 1.0, "Skip": 1.0, "Reverse": 1.0, "_default": 1.0},
                "color_bias": 2.0,
                "diversity_bias": 1.6,
                "wild_penalty": 3.0,
                "high_points_bias": 0.03,
                "random_prob": 0.10,
                "next_uno_scale": 1.0,
            },
            {  # Chaotic
                "name": "Chaotic",
                "impact_mult": {"+4": 1.0, "+2": 1.0, "Skip": 1.0, "Reverse": 1.0, "_default": 1.0},
                "color_bias": 0.8,
                "diversity_bias": 0.8,
                "wild_penalty": 2.0,
                "high_points_bias": 0.0,
                "random_prob": 0.35,
                "next_uno_scale": 0.8,
            },
            {  # Finisher
                "name": "Finisher",
                "impact_mult": {"+4": 1.2, "+2": 1.1, "Skip": 1.1, "Reverse": 1.0, "_default": 1.0},
                "color_bias": 1.0,
                "diversity_bias": 1.2,
                "wild_penalty": 3.5,
                "high_points_bias": 0.15,
                "random_prob": 0.12,
                "next_uno_scale": 1.3,
            },
        ]
        return random.choice(personas)

    def _score_move(self, player_idx: int, card: Card, chosen_color: Optional[str], persona: Optional[dict] = None) -> float:
        # If playing this card wins immediately, prefer it
        if len(self.players[player_idx].hand) == 1:
            return math.inf
        persona = persona or {}
        impact_mult = persona.get("impact_mult", {})
        color_bias = persona.get("color_bias", 1.0)
        diversity_bias = persona.get("diversity_bias", 1.0)
        wild_penalty = persona.get("wild_penalty", 3.0)
        high_points_bias = persona.get("high_points_bias", 0.0)
        next_uno_scale = persona.get("next_uno_scale", 1.0)

        score = 0.0
        next_hand = len(self.players[self.next_player_index(1)].hand)
        base = 0.0
        if card.value == "+4":
            base = 40.0
            if next_hand == 1:
                base += 20.0 * next_uno_scale
        elif card.value == "+2":
            base = 20.0
            if next_hand == 1:
                base += 12.0 * next_uno_scale
        elif card.value == "Skip":
            base = 12.0
            if next_hand == 1:
                base += 6.0 * next_uno_scale
        elif card.value == "Reverse":
            base = 4.0
        else:
            base = 2.0
        score += base * impact_mult.get(card.value, impact_mult.get("_default", 1.0))

        # Favor setting a color we hold
        color_to_set = chosen_color if card.is_wild() else card.color
        if color_to_set in COLORS:
            counts = self._color_counts([c for c in self.players[player_idx].hand if c is not card])
            score += counts.get(color_to_set, 0) * 2.0 * color_bias

        # Prefer lower color diversity after play
        distinct = self._distinct_colors_after(player_idx, card, chosen_color)
        score += (4 - distinct) * 1.0 * diversity_bias

        # Encourage discarding high-point cards
        score += Game.card_points(card) * high_points_bias

        if card.is_wild():
            score -= wild_penalty
        return score

    def choose_best_move(self, player_idx: int) -> Tuple[str, Optional[Card], Optional[str]]:
        """Return (action, card, chosen_color). 'draw' if no allowed move. Persona randomized per turn."""
        moves = self.allowed_moves(player_idx)
        if not moves:
            return "draw", None, None
        if len(self.players[player_idx].hand) == 1:
            card = moves[0]
            color = self._best_color_after_play(player_idx, card) if card.is_wild() else None
            return "play", card, color
        persona = self._pick_persona()
        # Random human-like behavior
        if random.random() < persona.get("random_prob", 0.0):
            card = random.choice(moves)
            color = self._best_color_after_play(player_idx, card) if card.is_wild() else None
            return "play", card, color
        best_score = -math.inf
        best_move: Optional[Card] = None
        best_color: Optional[str] = None
        ordered = [c for c in moves if not c.is_wild()] + [c for c in moves if c.is_wild()]
        for card in ordered:
            color = self._best_color_after_play(player_idx, card) if card.is_wild() else None
            sc = self._score_move(player_idx, card, color, persona)
            if sc > best_score:
                best_score = sc
                best_move = card
                best_color = color
        return "play", best_move, best_color

    def _recycle_discard_into_deck(self) -> None:
        """Recycle the discard pile (except the top card) back into the deck and shuffle."""
        if len(self.discard_pile) <= 1:
            # Nothing to recycle; extremely rare, but just return
            return
        top = self.discard_pile[-1]
        rest = self.discard_pile[:-1]
        self.discard_pile = [top]
        random.shuffle(rest)
        # Put recycled cards under current deck order (or simply assign if empty)
        self.deck.cards = rest + self.deck.cards

    def draw_cards(self, player_idx: int, n: int) -> None:
        """Draw n cards for the specified player, recycling deck as needed."""
        player = self.players[player_idx]
        for _ in range(n):
            if not self.deck.cards:
                self._recycle_discard_into_deck()
            # If still empty (very rare), rebuild a fresh deck excluding current top
            if not self.deck.cards:
                # Build a fresh deck and remove the current top card if present in it
                current_top = self.top_card() if self.discard_pile else None
                self.deck._build_deck()
                # Remove one instance of current_top from deck if possible
                if current_top is not None:
                    try:
                        self.deck.cards.remove(current_top)
                    except ValueError:
                        pass
                    self.deck.shuffle()
            player.draw(self.deck, 1)
