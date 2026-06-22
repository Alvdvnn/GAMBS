"""Interactive Video Poker screen."""

from __future__ import annotations

import random

from rich.console import Console
from rich.text import Text

from gambs import config
from gambs.games import cards, poker
from gambs.games.outcome import apply_net
from gambs.save import SaveData
from gambs.ui.components import balance_bar_text
from gambs.ui.prompts import bet_prompt, tutorial_gate, result_banner, pause

POKER_TUTORIAL = [
    "Enter a bet amount.",
    "You are dealt five cards. Choose which to keep, then redraw the rest.",
    "Type the positions to HOLD (e.g. 135) and press Enter.",
    "A pair of Jacks or better pays; a Royal Flush pays 800x.",
]

_RANK_LABELS = {
    "royal_flush": "ROYAL FLUSH",
    "straight_flush": "STRAIGHT FLUSH",
    "four_kind": "FOUR OF A KIND",
    "full_house": "FULL HOUSE",
    "flush": "FLUSH",
    "straight": "STRAIGHT",
    "three_kind": "THREE OF A KIND",
    "two_pair": "TWO PAIR",
    "jacks_or_better": "JACKS OR BETTER",
    "nothing": "NO WIN",
}


def _show_hand(console: Console, hand) -> None:
    positions = "   ".join(f"[{i + 1}]" for i in range(5))
    cards_line = "    ".join(cards.card_str(card) for card in hand)
    console.print(Text(f"  {positions}", style="dim"))
    console.print(Text(f"   {cards_line}", style=config.COLORS["gold"]))


def run_poker(console: Console, save: SaveData) -> None:
    tutorial_gate(console, save, "poker", "VIDEO POKER", POKER_TUTORIAL)
    bet = bet_prompt(console, save)
    if bet is None:
        return
    rng = random.Random()
    deck = cards.shuffle(rng)
    hand = poker.deal(deck)
    console.clear()
    _show_hand(console, hand)
    console.print("Hold which positions? (e.g. 135, blank = none): ", end="")
    raw = input().strip()
    holds = {int(ch) - 1 for ch in raw if ch in "12345"}
    hand = poker.redraw(hand, holds, deck)
    rank = poker.evaluate(hand)
    net = poker.settle(rank, bet)
    apply_net(save, bet, net)
    console.clear()
    _show_hand(console, hand)
    label = _RANK_LABELS[rank]
    if net > 0:
        result_banner(console, True, f"{label}  +${net:,.2f}")
    else:
        result_banner(console, False, f"{label}  -${abs(net):,.2f}")
    console.print(balance_bar_text(save))
    pause(console)
