"""Bounty Jobs (Earn Mode): scripted branching missions loaded from JSON.

Pure engine — traversal is deterministic and the injected RNG is consulted only
at "risk" nodes. This is an *earn* game: success pays out and increments stats,
failure costs no money (only a cooldown). The screen layer drives I/O.

Node shapes (in bounty_jobs.json):
- choice node:   {"text": ..., "choices": [{"label": ..., "next": node_id}, ...]}
- risk node:     {"text": ..., "risk": {"success_chance": f, "on_success": id, "on_fail": id}}
- terminal node: {"text": ..., "terminal": {"payout": N}}  OR  {"terminal": {"fail": true}}
"""

from __future__ import annotations

import json
import random
from pathlib import Path

from gambs import config
from gambs.save import SaveData


def load_jobs(path: Path) -> dict[str, list[dict]]:
    """Load the tier -> [job, ...] map from disk."""
    return json.loads(path.read_text(encoding="utf-8"))


def tier_jobs(jobs: dict[str, list[dict]], tier: str) -> list[dict]:
    """Return the list of jobs for a tier (empty list if the tier is absent)."""
    return jobs.get(tier, [])


def start_node(job: dict) -> str:
    """The id of the job's entry node."""
    return job["start"]


def get_node(job: dict, node_id: str) -> dict:
    """Look up a node by id."""
    return job["nodes"][node_id]


def is_terminal(node: dict) -> bool:
    return "terminal" in node


def is_risk(node: dict) -> bool:
    return "risk" in node


def is_choice(node: dict) -> bool:
    return "choices" in node


def resolve_choice(job: dict, node_id: str, choice_index: int) -> str:
    """Return the next node id for a chosen option at a choice node."""
    return get_node(job, node_id)["choices"][choice_index]["next"]


def resolve_risk(node: dict, rng: random.Random) -> str:
    """Roll the risk gate; return the on_success or on_fail node id."""
    risk = node["risk"]
    if rng.random() < risk["success_chance"]:
        return risk["on_success"]
    return risk["on_fail"]


def terminal_result(node: dict) -> tuple[bool, float]:
    """Interpret a terminal node as (success, payout). Failure pays $0."""
    terminal = node["terminal"]
    if terminal.get("fail"):
        return (False, 0.0)
    return (True, float(terminal["payout"]))
