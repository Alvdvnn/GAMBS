"""Interactive Roulette screen."""

from __future__ import annotations

import random
import time

import readchar
from rich.console import Console
from rich.text import Text

from gambs import config
from gambs.games import roulette
from gambs.games.outcome import apply_net
from gambs.save import SaveData
from gambs.ui.components import balance_bar_text
from gambs.ui.prompts import bet_prompt, tutorial_gate, result_banner, pause

ROULETTE_TUTORIAL = [
    "Enter a bet amount.",
    "Pick a bet: a single number (35:1) or red/black/odd/even/low/high (1:1).",
    "Any outside bet loses if the ball lands on 0.",
]

# key -> bet_type
_OUTSIDE = {
    "r": roulette.BET_RED,
    "b": roulette.BET_BLACK,
    "o": roulette.BET_ODD,
    "e": roulette.BET_EVEN,
    "l": roulette.BET_LOW,
    "h": roulette.BET_HIGH,
}


def run_roulette(console: Console, save: SaveData) -> None:
    tutorial_gate(console, save, "roulette", "ROULETTE", ROULETTE_TUTORIAL)
    bet = bet_prompt(console, save)
    if bet is None:
        return
    console.print("Bet [N]umber, [R]ed [B]lack [O]dd [E]ven [L]ow [H]igh: ", end="")
    key = readchar.readkey().lower()
    bet_value: int | None = None
    if key == "n":
        console.print("\nNumber 0-36: ", end="")
        raw = input().strip()
        try:
            bet_value = int(raw)
        except ValueError:
            return
        if not 0 <= bet_value <= 36:
            return
        bet_type = roulette.BET_STRAIGHT
    else:
        bet_type = _OUTSIDE.get(key)
        if bet_type is None:
            return
    rng = random.Random()
    for _ in range(16):
        n = rng.randint(0, 36)
        console.print(Text(f"  spinning... {n:>2}", style=config.COLORS["gold"]), end="\r")
        time.sleep(0.06)
    result = roulette.spin(rng)
    net = roulette.settle(bet_type, bet_value, result, bet)
    apply_net(save, bet, net)
    won = net > 0
    sign = "+" if won else "-"
    result_banner(
        console, won, f"Ball on {result} ({roulette.color(result)})  {'WIN' if won else 'LOSE'} {sign}${abs(net):,.2f}"
    )
    console.print(balance_bar_text(save))
    pause(console)
