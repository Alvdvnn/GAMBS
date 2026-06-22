"""Interactive Slots screen."""

from __future__ import annotations

import random
import time

from rich.console import Console
from rich.text import Text

from gambs import config
from gambs.games import slots
from gambs.games.outcome import apply_net
from gambs.save import SaveData
from gambs.ui.components import balance_bar_text
from gambs.ui.prompts import bet_prompt, tutorial_gate, result_banner, pause

SLOTS_TUTORIAL = [
    "Enter a bet amount.",
    "Three 7s pay 50x, three BARs 20x, any other triple 5x.",
    "Exactly two 7s pay 2x. Anything else loses.",
]


def run_slots(console: Console, save: SaveData) -> None:
    tutorial_gate(console, save, "slots", "SLOTS", SLOTS_TUTORIAL)
    bet = bet_prompt(console, save)
    if bet is None:
        return
    rng = random.Random()
    for _ in range(14):
        temp = rng.choices(slots.SYMBOLS, k=3)
        console.print(
            Text(f"  [ {temp[0]} | {temp[1]} | {temp[2]} ]", style=config.COLORS["gold"]),
            end="\r",
        )
        time.sleep(0.07)
    reels = slots.spin(rng)
    net = slots.settle(reels, bet)
    apply_net(save, bet, net)
    console.print(Text(f"  [ {reels[0]} | {reels[1]} | {reels[2]} ]", style=config.COLORS["gold"]))
    won = net > 0
    sign = "+" if won else "-"
    result_banner(console, won, f"{'WIN' if won else 'LOSE'} {sign}${abs(net):,.2f}")
    console.print(balance_bar_text(save))
    pause(console)
