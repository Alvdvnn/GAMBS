"""Typing Heist (Earn Mode): crack codes by typing them fast and accurately.

Pure scoring logic — RNG injected, timing passed in — so it is fully testable.
The reward formula is: base_pay (by difficulty tier) x average accuracy x speed
bonus, clamped to the session reward range. This is an *earn* game: the payout is
always positive, never a loss.
"""

from __future__ import annotations

import random
import string

PROMPTS_PER_SESSION = 5
SECONDS_PER_PROMPT = 4.0  # par time budget per code

MIN_REWARD = 50.0
MAX_REWARD = 500.0

# Base pay per difficulty tier (1 = easy/low balance, 4 = hard/high balance).
TIER_BASE_PAY = {1: 80.0, 2: 160.0, 3: 280.0, 4: 420.0}

_WORDS = {
    1: ["CASH", "GOLD", "LOCK", "SAFE", "CHIP", "COIN", "LOOT", "BANK", "KEYS", "WIRE"],
    2: ["VAULT", "BULLION", "LOOTBAG", "CIPHER", "LOCKBOX", "PAYLOAD", "DECRYPT", "OVERRIDE"],
}
_CODE_ALPHABET = string.ascii_uppercase + string.digits


def difficulty_for_balance(balance: float) -> int:
    """Map the player's balance to a difficulty tier (1-4). Richer = harder."""
    if balance < 1000:
        return 1
    if balance < 5000:
        return 2
    if balance < 20000:
        return 3
    return 4


def generate_prompt(rng: random.Random, tier: int) -> str:
    """Produce one code to type for the given tier."""
    if tier == 1:
        return rng.choice(_WORDS[1])
    if tier == 2:
        return rng.choice(_WORDS[2])
    if tier == 3:
        return f"{rng.choice(_WORDS[2])}-{rng.randint(100, 999)}"
    return "".join(rng.choice(_CODE_ALPHABET) for _ in range(10))


def generate_round(rng: random.Random, tier: int, count: int) -> list[str]:
    """Produce `count` codes for a session."""
    return [generate_prompt(rng, tier) for _ in range(count)]


def accuracy(typed: str, target: str) -> float:
    """Character-level accuracy in [0, 1]. Extra/missing characters are penalised."""
    if not target:
        return 0.0
    correct = sum(1 for a, b in zip(typed, target) if a == b)
    return correct / max(len(typed), len(target))


def speed_bonus(elapsed: float, par_time: float) -> float:
    """Multiplier in [0.5, 1.25]: beating par rewards up to 1.25x, slow down to 0.5x."""
    if elapsed <= 0:
        return 1.25
    ratio = par_time / elapsed
    return max(0.5, min(1.25, ratio))


def session_reward(tier: int, accuracies: list[float], elapsed: float) -> float:
    """Combine tier base pay, average accuracy, and speed into a clamped payout."""
    base = TIER_BASE_PAY[tier]
    avg_accuracy = sum(accuracies) / len(accuracies) if accuracies else 0.0
    par_time = len(accuracies) * SECONDS_PER_PROMPT
    raw = base * avg_accuracy * speed_bonus(elapsed, par_time)
    return round(min(MAX_REWARD, max(MIN_REWARD, raw)), 2)
