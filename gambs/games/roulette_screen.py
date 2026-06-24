"""Interactive Roulette screen."""

from __future__ import annotations

import random
import time

import readchar
from rich.console import Console
from rich.text import Text

from gambs import config
from gambs.difficulty import min_bet_for
from gambs.games import roulette
from gambs.games.outcome import apply_net
from gambs.save import SaveData
from gambs.ui.components import balance_bar_text
from gambs.ui.prompts import tutorial_gate, result_banner, pause

ROULETTE_TUTORIAL = [
    "Place one or more bets, then spin once to settle them all.",
    "Each bet is a single number (35:1) or red/black/odd/even/low/high (1:1).",
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


def _bet_label(bet_type: str, bet_value: int | None) -> str:
    if bet_type == roulette.BET_STRAIGHT:
        return f"#{bet_value}"
    return bet_type


def _add_bet(console: Console, save: SaveData, remaining: float, min_bet: float):
    """Prompt for one bet. Returns (bet_type, bet_value, amount) or None."""
    console.print(
        "  Bet [N]umber, [R]ed [B]lack [O]dd [E]ven [L]ow [H]igh: ", end=""
    )
    key = readchar.readkey().lower()
    bet_value: int | None = None
    if key == "n":
        raw = input("\n  Number 0-36: ").strip()
        try:
            bet_value = int(raw)
        except ValueError:
            return None
        if not 0 <= bet_value <= 36:
            return None
        bet_type = roulette.BET_STRAIGHT
    else:
        bet_type = _OUTSIDE.get(key)
        if bet_type is None:
            return None
    raw = input(f"  Amount (min ${min_bet:,.0f}, free ${remaining:,.2f}): ").strip()
    try:
        amount = round(float(raw), 2)
    except ValueError:
        return None
    if amount < min_bet or amount > remaining:
        console.print(Text("  Invalid amount.", style=config.COLORS["danger"]))
        pause(console)
        return None
    return bet_type, bet_value, amount


def run_roulette(console: Console, save: SaveData) -> None:
    tutorial_gate(console, save, "roulette", "ROULETTE", ROULETTE_TUTORIAL)
    min_bet = min_bet_for(save.vip.level)
    bets: list[tuple[str, int | None, float]] = []

    while True:
        console.clear()
        console.print(balance_bar_text(save))
        staked = sum(amount for _, _, amount in bets)
        for bet_type, bet_value, amount in bets:
            console.print(
                Text(f"  • {_bet_label(bet_type, bet_value)}  ${amount:,.2f}", style=config.COLORS["gold"])
            )
        remaining = round(save.balance - staked, 2)
        console.print(
            Text(
                f"[A]dd bet   [Enter] spin   [ESC] cancel   "
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
            new = _add_bet(console, save, remaining, min_bet)
            if new is not None:
                bets.append(new)

    rng = random.Random()
    for _ in range(16):
        n = rng.randint(0, 36)
        console.print(Text(f"  spinning... {n:>2}", style=config.COLORS["gold"]), end="\r")
        time.sleep(0.06)
    result = roulette.spin(rng)
    nets = roulette.settle_all(bets, result)
    for (bet_type, bet_value, amount), net in zip(bets, nets):
        apply_net(save, amount, net)

    console.clear()
    console.print(
        Text(f"Ball on {result} ({roulette.color(result)})", style=config.COLORS["info"])
    )
    for (bet_type, bet_value, _), net in zip(bets, nets):
        console.print(
            Text(f"  {_bet_label(bet_type, bet_value)}: {net:+,.2f}", style=config.COLORS["gold"])
        )
    total = sum(nets)
    sign = f"+${total:,.2f}" if total >= 0 else f"-${abs(total):,.2f}"
    result_banner(console, total > 0, f"Net {sign}")
    console.print(balance_bar_text(save))
    pause(console)
