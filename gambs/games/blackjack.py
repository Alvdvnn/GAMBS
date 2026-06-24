"""Blackjack: pure hand math + dealer policy + settlement. RNG via deck list."""

from __future__ import annotations

from dataclasses import dataclass

from gambs.games.cards import Card

_TENS = {"10", "J", "Q", "K"}


def hand_value(cards: list[Card]) -> int:
    """Best blackjack total: aces are 11, reduced to 1 as needed to avoid bust."""
    total = 0
    aces = 0
    for card in cards:
        if card.rank == "A":
            aces += 1
            total += 11
        elif card.rank in _TENS:
            total += 10
        else:
            total += int(card.rank)
    while total > 21 and aces:
        total -= 10
        aces -= 1
    return total


def is_blackjack(cards: list[Card]) -> bool:
    """A natural: exactly two cards totalling 21."""
    return len(cards) == 2 and hand_value(cards) == 21


def _card_value(card: Card) -> int:
    """Single-card blackjack value (ace 11, tens 10)."""
    if card.rank == "A":
        return 11
    if card.rank in _TENS:
        return 10
    return int(card.rank)


def can_split(cards: list[Card]) -> bool:
    """True if the opening two cards share a value and can be split."""
    return len(cards) == 2 and _card_value(cards[0]) == _card_value(cards[1])


def dealer_upcard_is_ace(dealer: list[Card]) -> bool:
    """Whether the dealer's first (face-up) card is an Ace — insurance offer."""
    return bool(dealer) and dealer[0].rank == "A"


def insurance_result(dealer: list[Card], insurance_bet: float) -> float:
    """Settle an insurance side bet: pays 2:1 if the dealer has blackjack."""
    if is_blackjack(dealer):
        return round(insurance_bet * 2, 2)
    return round(-insurance_bet, 2)


def dealer_play(dealer: list[Card], deck: list[Card]) -> list[Card]:
    """Dealer draws (in place) until reaching 17 or more. Returns the hand."""
    while hand_value(dealer) < 17:
        dealer.append(deck.pop())
    return dealer


@dataclass
class BlackjackResult:
    outcome: str  # "blackjack" | "win" | "lose" | "push"
    net: float


def settle(
    player: list[Card], dealer: list[Card], bet: float, natural: bool = True
) -> BlackjackResult:
    """Decide a finished hand. `bet` is the effective wager (already doubled if
    the player doubled). Net follows the win-positive/loss-negative convention.

    `natural` is False for split hands, where a two-card 21 counts as an
    ordinary 21 (no 3:2 blackjack bonus).
    """
    player_bj = natural and is_blackjack(player)
    dealer_bj = is_blackjack(dealer)
    if player_bj and dealer_bj:
        return BlackjackResult("push", 0.0)
    if player_bj:
        return BlackjackResult("blackjack", round(bet * 1.5, 2))
    if dealer_bj:
        return BlackjackResult("lose", round(-bet, 2))

    pv = hand_value(player)
    dv = hand_value(dealer)
    if pv > 21:
        return BlackjackResult("lose", round(-bet, 2))
    if dv > 21 or pv > dv:
        return BlackjackResult("win", round(bet, 2))
    if pv < dv:
        return BlackjackResult("lose", round(-bet, 2))
    return BlackjackResult("push", 0.0)
