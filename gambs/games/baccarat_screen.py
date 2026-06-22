"""Interactive Baccarat screen."""

from __future__ import annotations

import random
import time

import readchar
from rich.console import Console
from rich.text import Text

from gambs import config
from gambs.games import baccarat, cards
from gambs.games.outcome import apply_net
from gambs.save import SaveData
from gambs.ui.components import balance_bar_text
from gambs.ui.prompts import bet_prompt, tutorial_gate, result_banner, pause

BACCARAT_TUTORIAL = [
    "Enter a bet amount.",
    "Bet on PLAYER, BANKER, or TIE — closest to 9 wins.",
    "Player pays 1:1, Banker 0.95:1 (5% commission), Tie 8:1.",
    "Third cards are dealt automatically by the rules.",
]

_CHOICES = {"p": baccarat.BET_PLAYER, "b": baccarat.BET_BANKER, "t": baccarat.BET_TIE}


def run_baccarat(console: Console, save: SaveData) -> None:
    tutorial_gate(console, save, "baccarat", "BACCARAT", BACCARAT_TUTORIAL)
    bet = bet_prompt(console, save)
    if bet is None:
        return
    console.print("Bet [P]layer  [B]anker  [T]ie: ", end="")
    key = readchar.readkey().lower()
    bet_type = _CHOICES.get(key)
    if bet_type is None:
        return
    console.print(Text("  dealing...", style=config.COLORS["gold"]))
    time.sleep(0.4)
    rng = random.Random()
    deck = cards.shuffle(rng)
    player, banker = baccarat.play_round(deck)
    net = baccarat.settle(bet_type, player, banker, bet)
    apply_net(save, bet, net)
    console.clear()
    console.print(
        Text(
            f"Player: {cards.hand_str(player)}  ({baccarat.hand_total(player)})",
            style=config.COLORS["gold"],
        )
    )
    console.print(
        Text(
            f"Banker: {cards.hand_str(banker)}  ({baccarat.hand_total(banker)})",
            style=config.COLORS["info"],
        )
    )
    if net > 0:
        result_banner(console, True, f"WIN +${net:,.2f}")
    elif net == 0:
        result_banner(console, False, "TIE — bet returned")
    else:
        result_banner(console, False, f"LOSE -${abs(net):,.2f}")
    console.print(balance_bar_text(save))
    pause(console)
