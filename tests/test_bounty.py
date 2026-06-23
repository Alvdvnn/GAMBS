import random

from gambs import config
from gambs.earn.bounty import (
    load_jobs,
    tier_jobs,
    start_node,
    get_node,
    is_terminal,
    is_risk,
    is_choice,
    resolve_choice,
    resolve_risk,
    terminal_result,
)

# A small in-memory job used by traversal tests (no disk dependency).
SAMPLE_JOB = {
    "id": "test_job",
    "title": "Test Job",
    "start": "n1",
    "nodes": {
        "n1": {
            "text": "start",
            "choices": [
                {"label": "safe", "next": "win"},
                {"label": "risky", "next": "r1"},
            ],
        },
        "r1": {
            "text": "roll",
            "risk": {"success_chance": 0.5, "on_success": "win", "on_fail": "lose"},
        },
        "win": {"text": "done", "terminal": {"payout": 200}},
        "lose": {"text": "caught", "terminal": {"fail": True}},
    },
}


def test_load_jobs_reads_all_tiers():
    jobs = load_jobs(config.BOUNTY_JOBS_PATH)
    assert set(jobs) == {"LOW", "MEDIUM", "HIGH"}
    assert tier_jobs(jobs, "LOW")  # non-empty


def test_loaded_jobs_have_required_shape():
    jobs = load_jobs(config.BOUNTY_JOBS_PATH)
    for tier in ("LOW", "MEDIUM", "HIGH"):
        for job in tier_jobs(jobs, tier):
            assert job["start"] in job["nodes"]


def test_start_node_returns_start_id():
    assert start_node(SAMPLE_JOB) == "n1"


def test_node_type_predicates():
    assert is_choice(get_node(SAMPLE_JOB, "n1"))
    assert is_risk(get_node(SAMPLE_JOB, "r1"))
    assert is_terminal(get_node(SAMPLE_JOB, "win"))


def test_resolve_choice_follows_next():
    assert resolve_choice(SAMPLE_JOB, "n1", 0) == "win"
    assert resolve_choice(SAMPLE_JOB, "n1", 1) == "r1"


def test_resolve_risk_success_with_low_roll():
    # success_chance 0.5; force a roll below it
    node = get_node(SAMPLE_JOB, "r1")
    rng = random.Random()
    rng.random = lambda: 0.1  # < 0.5 -> success
    assert resolve_risk(node, rng) == "win"


def test_resolve_risk_failure_with_high_roll():
    node = get_node(SAMPLE_JOB, "r1")
    rng = random.Random()
    rng.random = lambda: 0.9  # >= 0.5 -> fail
    assert resolve_risk(node, rng) == "lose"


def test_terminal_result_success_and_failure():
    assert terminal_result(get_node(SAMPLE_JOB, "win")) == (True, 200.0)
    assert terminal_result(get_node(SAMPLE_JOB, "lose")) == (False, 0.0)


from gambs.earn.bounty import (
    is_on_cooldown,
    cooldown_remaining,
    apply_success,
    apply_failure,
)
from gambs.save import SaveData


def test_not_on_cooldown_by_default():
    save = SaveData()
    assert is_on_cooldown(save, now=1000.0) is False


def test_on_cooldown_when_now_before_until():
    save = SaveData(bounty_cooldown_until=2000.0)
    assert is_on_cooldown(save, now=1500.0) is True
    assert cooldown_remaining(save, now=1500.0) == 500.0


def test_cooldown_remaining_never_negative():
    save = SaveData(bounty_cooldown_until=1000.0)
    assert cooldown_remaining(save, now=3000.0) == 0.0


def test_apply_success_credits_and_counts():
    save = SaveData(balance=500.0)
    apply_success(save, 300.0)
    assert save.balance == 800.0
    assert save.stats.total_earned == 300.0
    assert save.stats.bounty_jobs_completed == 1
    assert save.stats.bounty_jobs_attempted == 1


def test_apply_failure_sets_cooldown_and_counts_attempt_only():
    save = SaveData(balance=500.0)
    apply_failure(save, now=1000.0)
    assert save.balance == 500.0  # no money lost
    assert save.stats.bounty_jobs_completed == 0
    assert save.stats.bounty_jobs_attempted == 1
    assert save.bounty_cooldown_until == 1000.0 + config.BOUNTY_COOLDOWN_SECONDS
