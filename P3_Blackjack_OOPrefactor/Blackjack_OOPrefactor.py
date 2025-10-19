#!/usr/bin/env python3
import random
from dataclasses import dataclass

RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
SUITS = ["♠", "♥", "♦", "♣"]
RANK_VALUES = {
    "A": 11,   # blackjack value (handled with ace downgrades later)
    "2": 2,  "3": 3,  "4": 4,  "5": 5,  "6": 6,
    "7": 7,  "8": 8,  "9": 9,  "10": 10, "J": 10, "Q": 10, "K": 10,
}

# For bias weighting we use "nominal" values: A=1, 2..10, J/Q/K=10
BIAS_VALUE = {
    "A": 1,
    "2": 2,  "3": 3,  "4": 4,  "5": 5,  "6": 6,
    "7": 7,  "8": 8,  "9": 9,  "10": 10, "J": 10, "Q": 10, "K": 10,
}

@dataclass(frozen=True)
class Card:
    rank: str
    suit: str
    def __str__(self) -> str:
        return f"{self.rank}{self.suit}"

class Deck:
    """
    Deck that can deal fairly or with a bias toward lower cards.
    - bias_strength in [0.0 .. 1.0]: 0 = fair, 1 = max bias to low cards.
    """
    def __init__(self, num_decks: int = 1) -> None:
        self.num_decks = num_decks
        self.cards: list[Card] = []
        self.bias_strength: float = 0.0
        self._build()

    def _build(self) -> None:
        self.cards = [Card(rank, suit)
                      for _ in range(self.num_decks)
                      for suit in SUITS
                      for rank in RANKS]
        self.shuffle()

    def shuffle(self) -> None:
        random.shuffle(self.cards)

    def set_bias(self, strength: float) -> None:
        """Set bias strength [0..1]. 0 = fair, 1 = very biased to low cards."""
        self.bias_strength = max(0.0, min(1.0, float(strength)))

    def _weights_for_bias(self) -> list[float]:
        """
        Build weights favoring low nominal values.
        Formula: w = 1 + bias * ((11 - v) / 10)
        - v in [1..10]; lower v -> larger weight.
        - If bias=0 -> all weights=1 (fair).
        """
        b = self.bias_strength
        if b <= 0.0:
            return [1.0] * len(self.cards)
        weights = []
        for c in self.cards:
            v = BIAS_VALUE[c.rank]  # 1..10
            # lowest (1) gets weight 1 + b*1, highest (10) gets weight 1 + b*0 = 1
            w = 1.0 + b * ((11 - v) / 10.0)
            weights.append(w)
        return weights

    def deal(self) -> Card:
        if not self.cards:
            self._build()
        if self.bias_strength <= 0.0 or len(self.cards) <= 1:
            # fair: pop from the end (already shuffled)
            return self.cards.pop()
        # biased: draw an index using weights, then remove that card
        weights = self._weights_for_bias()
        idx = random.choices(range(len(self.cards)), weights=weights, k=1)[0]
        return self.cards.pop(idx)

class Hand:
    def __init__(self, owner: str) -> None:
        self.owner = owner
        self.cards: list[Card] = []

    def add(self, card: Card) -> None:
        self.cards.append(card)

    def clear(self) -> None:
        self.cards.clear()

    def value(self) -> int:
        total = 0
        aces = 0
        for c in self.cards:
            total += RANK_VALUES[c.rank]
            if c.rank == "A":
                aces += 1
        while total > 21 and aces > 0:
            total -= 10
            aces -= 1
        return total

    def is_blackjack(self) -> bool:
        return len(self.cards) == 2 and self.value() == 21

    def is_bust(self) -> bool:
        return self.value() > 21

    def __str__(self) -> str:
        cards_str = " ".join(str(c) for c in self.cards)
        return f"{self.owner}: [{cards_str}] (={self.value()})"

class Game:
    def __init__(self, num_decks: int = 1) -> None:
        self.deck = Deck(num_decks=num_decks)
        self.player = Hand("Player")
        self.dealer = Hand("Dealer")
        self.round_log: list[str] = []
        self.round_no = 0  # counts completed rounds

    # ---- bias progression control ----
    def _update_bias_for_round(self) -> None:
        """
        Make round 1 fair; from round 2+, increase bias gradually.
        Tweak schedule as you like.
        """
        if self.round_no == 0:
            # next round will be #1 (first play) -> keep fair
            self.deck.set_bias(0.0)
        else:
            # after first hand, ramp up: e.g., 0.08 per round, capped at 0.99
            strength = min(0.08 * self.round_no, 0.99)
            self.deck.set_bias(strength)

    def _initial_deal(self) -> None:
        self.player.clear()
        self.dealer.clear()
        for _ in range(2):
            self.player.add(self.deck.deal())
            self.dealer.add(self.deck.deal())

    def _dealer_should_hit(self) -> bool:
        return self.dealer.value() < 17  # hit to 17

    def _result(self) -> str:
        p, d = self.player.value(), self.dealer.value()
        if self.player.is_bust():
            return "Dealer wins (player bust)."
        if self.dealer.is_bust():
            return "Player wins (dealer bust)."
        if p > d:
            return "Player wins."
        if p < d:
            return "Dealer wins."
        return "Push (tie)."

    def play_round(self) -> str:
        """Play one round; returns summary string."""
        self._update_bias_for_round()
        print(f"\n--- New Round (bias={self.deck.bias_strength:.2f}) ---")

        self._initial_deal()
        print(self.player)
        print(f"Dealer: [{self.dealer.cards[0]} ??]")

        # naturals
        if self.player.is_blackjack() or self.dealer.is_blackjack():
            print(self.dealer)
            if self.player.is_blackjack() and self.dealer.is_blackjack():
                result = "Both blackjack! Push."
            elif self.player.is_blackjack():
                result = "Blackjack! Player wins."
            else:
                result = "Dealer blackjack. Dealer wins."
            print(result)
            self._log_round(result)
            self.round_no += 1
            return result

        # player turn
        while True:
            choice = input("(H)it or (S)tand? ").strip().lower()
            if choice not in {"h", "s"}:
                print("Please enter H or S.")
                continue
            if choice == "h":
                self.player.add(self.deck.deal())
                print(self.player)
                if self.player.is_bust():
                    result = "Dealer wins (player bust)."
                    print(result)
                    self._log_round(result)
                    self.round_no += 1
                    return result
            else:
                break

        # dealer turn
        print(self.dealer)
        while self._dealer_should_hit():
            print("Dealer hits.")
            self.dealer.add(self.deck.deal())
            print(self.dealer)
            if self.dealer.is_bust():
                result = "Player wins (dealer bust)."
                print(result)
                self._log_round(result)
                self.round_no += 1
                return result
        print("Dealer stands.")

        result = self._result()
        print(result)
        self._log_round(result)
        self.round_no += 1
        return result

    def _log_round(self, result: str) -> None:
        p_cards = " ".join(str(c) for c in self.player.cards)
        d_cards = " ".join(str(c) for c in self.dealer.cards)
        summary = f"P[{p_cards}]={self.player.value()}  D[{d_cards}]={self.dealer.value()}  -> {result}"
        self.round_log.append(summary)

    def print_recent_log(self, n: int = 5) -> None:
        print("\nRecent rounds:")
        for line in self.round_log[-n:]:
            print("  " + line)

def main() -> None:
    print("Blackjack (OOP with progressive low-card bias after round 1).")
    game = Game(num_decks=1)
    while True:
        resp = input("\nPlay a round? (y/n): ").strip().lower()
        if resp in {"n", "q"}:
            break
        if resp != "y":
            continue
        game.play_round()
        game.print_recent_log(3)
    print("\nThanks for playing!")

if __name__ == "__main__":
    main()
