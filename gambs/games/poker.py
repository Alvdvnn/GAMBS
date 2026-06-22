"""Video Poker (Jacks or Better): hand evaluation, draw, paytable, settlement."""

from __future__ import annotations

from collections import Counter

from gambs.games.cards import Card

# Net-profit multipliers per unit bet. "nothing" loses the bet.
PAYTABLE = {
    "royal_flush": 800,
    "straight_flush": 50,
    "four_kind": 25,
    "full_house": 9,
    "flush": 6,
    "straight": 4,
    "three_kind": 3,
    "two_pair": 2,
    "jacks_or_better": 1,
    "nothing": 0,
}

_ORDER = {
    "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9,
    "10": 10, "J": 11, "Q": 12, "K": 13, "A": 14,
}


def _is_straight(values: list[int]) -> bool:
    """True if five distinct ranks form a run (ace high or the A-2-3-4-5 wheel)."""
    unique = sorted(set(values))
    if len(unique) != 5:
        return False
    if unique[-1] - unique[0] == 4:
        return True
    return unique == [2, 3, 4, 5, 14]


def evaluate(cards: list[Card]) -> str:
    """Return the paytable category for a 5-card hand."""
    counts = Counter(card.rank for card in cards)
    count_pattern = sorted(counts.values(), reverse=True)
    values = sorted(_ORDER[card.rank] for card in cards)
    is_flush = len({card.suit for card in cards}) == 1
    is_straight = _is_straight(values)

    if is_straight and is_flush:
        if set(values) == {10, 11, 12, 13, 14}:
            return "royal_flush"
        return "straight_flush"
    if count_pattern == [4, 1]:
        return "four_kind"
    if count_pattern == [3, 2]:
        return "full_house"
    if is_flush:
        return "flush"
    if is_straight:
        return "straight"
    if count_pattern == [3, 1, 1]:
        return "three_kind"
    if count_pattern == [2, 2, 1]:
        return "two_pair"
    if count_pattern[0] == 2:
        pair_rank = next(rank for rank, ct in counts.items() if ct == 2)
        if _ORDER[pair_rank] >= 11:  # J, Q, K, A
            return "jacks_or_better"
    return "nothing"


def deal(deck: list[Card]) -> list[Card]:
    """Draw the opening five cards from the deck."""
    return [deck.pop() for _ in range(5)]


def redraw(hand: list[Card], holds: set[int], deck: list[Card]) -> list[Card]:
    """Return a new hand keeping held indices, replacing the rest from the deck."""
    return [card if i in holds else deck.pop() for i, card in enumerate(hand)]


def settle(rank: str, bet: float) -> float:
    """Net profit for a final hand: bet * paytable multiplier, or -bet if it pays 0."""
    mult = PAYTABLE[rank]
    if mult == 0:
        return round(-bet, 2)
    return round(bet * mult, 2)
