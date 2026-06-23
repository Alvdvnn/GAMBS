"""Interactive Bounty Jobs screen.

Shows a tiered job board, runs the chosen job through the pure engine in
gambs/earn/bounty.py, and applies the reward or cooldown. RNG is real here; the
engine stays pure.
"""

from __future__ import annotations

import random
import time

import readchar
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from gambs import config
from gambs.earn import bounty
from gambs.save import SaveData
from gambs.ui.components import balance_bar_text
from gambs.ui.prompts import tutorial_gate, result_banner, pause

BOUNTY_TUTORIAL = [
    "Pick a job from the board — LOW, MEDIUM, or HIGH tier.",
    "Each job is a chain of decisions; some choices roll the dice.",
    "Succeed and you bank the payout. Fail and you wait out a short cooldown.",
    "This is an EARN job: failing never costs you money, only time.",
]

_TIERS = ["LOW", "MEDIUM", "HIGH"]


def _board_panel(jobs: dict, save: SaveData, now: float) -> Panel:
    body = Text()
    for i, tier in enumerate(_TIERS, start=1):
        entries = bounty.tier_jobs(jobs, tier)
        title = entries[0]["title"] if entries else "(none)"
        body.append(f" [{i}] ", style=f"bold {config.COLORS['gold']}")
        body.append(f"{tier:<7} — {title}\n", style=f"bold {config.COLORS['earn']}")
    if bounty.is_on_cooldown(save, now):
        body.append(
            f"\n On cooldown: {bounty.cooldown_remaining(save, now):.0f}s left",
            style=config.COLORS["danger"],
        )
    body.append("\n [ESC] Back", style="dim")
    return Panel(
        body, title="🎯  BOUNTY BOARD", title_align="left", style=config.COLORS["earn"]
    )


def _play_job(console: Console, job: dict, rng: random.Random) -> tuple[bool, float]:
    """Walk the job to a terminal node. Returns (success, payout)."""
    node_id = bounty.start_node(job)
    while True:
        node = bounty.get_node(job, node_id)
        console.print(Text(f"\n  {node['text']}", style=config.COLORS["info"]))

        if bounty.is_terminal(node):
            return bounty.terminal_result(node)

        if bounty.is_risk(node):
            console.print(Text("  ...rolling the dice...", style="dim"))
            time.sleep(0.6)
            node_id = bounty.resolve_risk(node, rng)
            continue

        # choice node
        choices = node["choices"]
        for idx, choice in enumerate(choices, start=1):
            console.print(
                Text(f"   [{idx}] ", style=f"bold {config.COLORS['gold']}")
                + Text(choice["label"], style=config.COLORS["earn"])
            )
        console.print("  Choose: ", end="")
        key = readchar.readkey()
        if key.isdigit() and 1 <= int(key) <= len(choices):
            node_id = bounty.resolve_choice(job, node_id, int(key) - 1)


def run_bounty(console: Console, save: SaveData) -> None:
    tutorial_gate(console, save, "bounty", "BOUNTY JOBS", BOUNTY_TUTORIAL)
    jobs = bounty.load_jobs(config.BOUNTY_JOBS_PATH)

    while True:
        now = time.time()
        console.clear()
        console.print(balance_bar_text(save))
        console.print(_board_panel(jobs, save, now))
        console.print("Pick a tier: ", end="")
        key = readchar.readkey()
        if key in ("\x1b", "q", "Q"):
            return
        if not (key.isdigit() and 1 <= int(key) <= len(_TIERS)):
            continue

        if bounty.is_on_cooldown(save, now):
            console.print(
                Text(
                    f"  Still on cooldown ({bounty.cooldown_remaining(save, now):.0f}s).",
                    style=config.COLORS["danger"],
                )
            )
            pause(console)
            continue

        tier = _TIERS[int(key) - 1]
        entries = bounty.tier_jobs(jobs, tier)
        if not entries:
            continue
        job = random.choice(entries)
        rng = random.Random()

        success, payout = _play_job(console, job, rng)
        if success:
            bounty.apply_success(save, payout)
            result_banner(console, True, f"JOB COMPLETE  +${payout:,.2f}")
        else:
            bounty.apply_failure(save, time.time())
            result_banner(console, False, "JOB FAILED — cooldown started")

        console.print(balance_bar_text(save))
        pause(console)
