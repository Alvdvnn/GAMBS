"""Interactive Baccarat screen."""

from __future__ import annotations

import random
import time

import readchar
from rich.console import Console
from rich.text import Text

from gambs import config
from gambs.difficulty import min_bet_for
from gambs.games import baccarat, cards
from gambs.games.outcome import apply_net
from gambs.save import SaveData
from gambs.ui.components import balance_bar_text
from gambs.ui.prompts import tutorial_gate, result_banner, pause

BACCARAT_TUTORIAL = [
    "Place one or more bets, then deal once to settle them all.",
    "Bet on PLAYER, BANKER, or TIE — closest to 9 wins.",
    "Player pays 1:1, Banker 0.95:1 (5% commission), Tie 8:1.",
    "Third cards are dealt automatically by the rules.",
]

_CHOICES = {"p": baccarat.BET_PLAYER, "b": baccarat.BET_BANKER, "t": baccarat.BET_TIE}


def _add_bet(console: Console, remaining: float, min_bet: float):
    """Prompt for one bet. Returns (bet_type, amount) or None."""
    console.print("  Bet [P]layer  [B]anker  [T]ie: ", end="")
    bet_type = _CHOICES.get(readchar.readkey().lower())
    if bet_type is None:
        return None
    raw = input(f"\n  Amount (min ${min_bet:,.0f}, free ${remaining:,.2f}): ").strip()
    try:
        amount = round(float(raw), 2)
    except ValueError:
        return None
    if amount < min_bet or amount > remaining:
        console.print(Text("  Invalid amount.", style=config.COLORS["danger"]))
        pause(console)
        return None
    return bet_type, amount


def run_baccarat(console: Console, save: SaveData) -> None:
    tutorial_gate(console, save, "baccarat", "BACCARAT", BACCARAT_TUTORIAL)
    min_bet = min_bet_for(save.vip.level)
    bets: list[tuple[str, float]] = []

    while True:
        console.clear()
        console.print(balance_bar_text(save))
        staked = sum(amount for _, amount in bets)
        for bet_type, amount in bets:
            console.print(Text(f"  • {bet_type}  ${amount:,.2f}", style=config.COLORS["gold"]))
        remaining = round(save.balance - staked, 2)
        console.print(
            Text(
                f"[A]dd bet   [Enter] deal   [ESC] cancel   "
                f"(staked ${staked:,.2f}, free ${remaining:,.2f})",
                style="dim",
            )
        )
        key = readchar.readkey()
        if key in ("\x1b", "q", "Q"):
            return
        if key in ("\r", "\n"):
            if bets:
                break
            continue
        if key in ("a", "A") and remaining >= min_bet:
            new = _add_bet(console, remaining, min_bet)
            if new is not None:
                bets.append(new)

    console.print(Text("  dealing...", style=config.COLORS["gold"]))
    time.sleep(0.4)
    rng = random.Random()
    deck = cards.shuffle(rng)
    player, banker = baccarat.play_round(deck)
    nets = baccarat.settle_all(bets, player, banker)
    for (bet_type, amount), net in zip(bets, nets):
        apply_net(save, amount, net)

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
    for (bet_type, _), net in zip(bets, nets):
        console.print(Text(f"  {bet_type}: {net:+,.2f}", style=config.COLORS["gold"]))
    total = sum(nets)
    sign = f"+${total:,.2f}" if total >= 0 else f"-${abs(total):,.2f}"
    result_banner(console, total > 0, f"Net {sign}")
    console.print(balance_bar_text(save))
    pause(console)
