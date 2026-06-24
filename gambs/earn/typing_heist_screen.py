"""Interactive Typing Heist screen."""

from __future__ import annotations

import random
import time

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from gambs import config
from gambs.earn import typing_heist
from gambs.save import SaveData
from gambs.ui.components import balance_bar_text
from gambs.ui.prompts import tutorial_gate, result_banner, pause
from gambs.vip import activity_xp, add_xp

TYPING_HEIST_TUTORIAL = [
    "Codes flash on screen — type each one and press Enter.",
    "Reward = base pay x typing accuracy x speed bonus.",
    "Richer crews crack harder codes for bigger payouts.",
    "This is an EARN job: you always walk away with cash, win or lose.",
]


def run_typing_heist(console: Console, save: SaveData) -> None:
    tutorial_gate(console, save, "typing_heist", "TYPING HEIST", TYPING_HEIST_TUTORIAL)
    tier = typing_heist.difficulty_for_balance(save.balance)
    rng = random.Random()
    prompts = typing_heist.generate_round(
        rng, tier, typing_heist.PROMPTS_PER_SESSION
    )

    console.clear()
    console.print(
        Panel(
            Text(
                f"Crack {len(prompts)} codes. Type each exactly, then Enter. "
                f"Tier {tier} job.",
                style=config.COLORS["earn"],
            ),
            title="⌨  TYPING HEIST",
            title_align="left",
            style=config.COLORS["earn"],
        )
    )

    accuracies: list[float] = []
    start = time.time()
    for index, target in enumerate(prompts, start=1):
        console.print(
            Text(f"  [{index}/{len(prompts)}]  ", style="dim")
            + Text(target, style=f"bold {config.COLORS['gold']}")
        )
        typed = input("  > ").strip().upper()
        accuracies.append(typing_heist.accuracy(typed, target))
    elapsed = time.time() - start

    reward = typing_heist.session_reward(tier, accuracies, elapsed)
    save.balance = round(save.balance + reward, 2)
    save.stats.total_earned = round(save.stats.total_earned + reward, 2)
    if reward > 0:
        add_xp(save, activity_xp(reward))

    avg = sum(accuracies) / len(accuracies) if accuracies else 0.0
    console.print(
        Text(
            f"  Accuracy {avg * 100:.0f}%  ·  Time {elapsed:.1f}s",
            style=config.COLORS["info"],
        )
    )
    result_banner(console, True, f"HEIST PAYOUT  +${reward:,.2f}")
    console.print(balance_bar_text(save))
    pause(console)
