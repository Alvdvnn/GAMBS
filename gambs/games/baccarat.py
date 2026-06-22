"""Baccarat (punto banco): card values, third-card rules, settlement."""

from __future__ import annotations

from gambs.games.cards import Card

BET_PLAYER = "player"
BET_BANKER = "banker"
BET_TIE = "tie"

_ZERO = {"10", "J", "Q", "K"}


def card_value(card: Card) -> int:
    """A=1, 2-9 face value, 10/J/Q/K=0."""
    if card.rank in _ZERO:
        return 0
    if card.rank == "A":
        return 1
    return int(card.rank)


def hand_total(cards: list[Card]) -> int:
    """Baccarat hand total: sum of card values mod 10."""
    return sum(card_value(c) for c in cards) % 10


def play_round(deck: list[Card]) -> tuple[list[Card], list[Card]]:
    """Deal a round per punto banco rules; draw cards with deck.pop().

    Returns (player_cards, banker_cards).
    """
    player = [deck.pop(), deck.pop()]
    banker = [deck.pop(), deck.pop()]
    pt = hand_total(player)
    bt = hand_total(banker)

    # Natural: either side showing 8 or 9 ends the round immediately.
    if pt >= 8 or bt >= 8:
        return player, banker

    player_third: int | None = None
    if pt <= 5:
        third = deck.pop()
        player.append(third)
        player_third = card_value(third)

    if player_third is None:
        # Player stood (6 or 7): banker draws on 0-5, stands on 6-7.
        if bt <= 5:
            banker.append(deck.pop())
    else:
        if bt <= 2:
            banker.append(deck.pop())
        elif bt == 3 and player_third != 8:
            banker.append(deck.pop())
        elif bt == 4 and player_third in (2, 3, 4, 5, 6, 7):
            banker.append(deck.pop())
        elif bt == 5 and player_third in (4, 5, 6, 7):
            banker.append(deck.pop())
        elif bt == 6 and player_third in (6, 7):
            banker.append(deck.pop())
        # bt == 7: banker stands.

    return player, banker


def settle(bet_type: str, player: list[Card], banker: list[Card], bet: float) -> float:
    """Net result. PLAYER 1:1, BANKER 0.95:1 (commission), TIE 8:1.

    Player/Banker bets push on a tie; a Tie bet loses when it is not a tie.
    """
    pt = hand_total(player)
    bt = hand_total(banker)
    if pt == bt:
        if bet_type == BET_TIE:
            return round(bet * 8, 2)
        return 0.0
    if bet_type == BET_TIE:
        return round(-bet, 2)
    winner = BET_PLAYER if pt > bt else BET_BANKER
    if bet_type != winner:
        return round(-bet, 2)
    if winner == BET_BANKER:
        return round(bet * 0.95, 2)
    return round(bet, 2)
