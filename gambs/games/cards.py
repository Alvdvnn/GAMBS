"""Shared playing-card model for card games. Pure, RNG injected."""

from __future__ import annotations

import random
from dataclasses import dataclass

RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
SUITS = ["♠", "♥", "♦", "♣"]


@dataclass(frozen=True)
class Card:
    rank: str
    suit: str


def make_deck() -> list[Card]:
    """A fresh ordered 52-card deck."""
    return [Card(rank, suit) for suit in SUITS for rank in RANKS]


def shuffle(rng: random.Random) -> list[Card]:
    """Return a new shuffled 52-card deck. Draw cards with deck.pop()."""
    deck = make_deck()
    rng.shuffle(deck)
    return deck


def card_str(card: Card) -> str:
    """Compact display like 'A♠' or '10♥'."""
    return f"{card.rank}{card.suit}"


def hand_str(cards: list[Card]) -> str:
    """Space-joined cards, e.g. 'A♠ 10♥'."""
    return " ".join(card_str(card) for card in cards)
