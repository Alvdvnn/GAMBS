from gambs.save import SaveData
from gambs.ui.stats import (
    net_pl,
    bounty_success_rate,
    format_duration,
    stats_rows,
)


def test_net_pl_is_won_minus_wagered():
    save = SaveData()
    save.stats.total_wagered = 300.0
    save.stats.total_won = 450.0
    assert net_pl(save) == 150.0


def test_net_pl_is_negative_when_wagered_exceeds_won():
    save = SaveData()
    save.stats.total_wagered = 500.0
    save.stats.total_won = 120.0
    assert net_pl(save) == -380.0


def test_bounty_success_rate_zero_when_no_attempts():
    save = SaveData()
    assert bounty_success_rate(save) == 0.0


def test_bounty_success_rate_is_completed_over_attempted():
    save = SaveData()
    save.stats.bounty_jobs_attempted = 4
    save.stats.bounty_jobs_completed = 1
    assert bounty_success_rate(save) == 0.25


def test_format_duration_seconds_only():
    assert format_duration(42) == "42s"


def test_format_duration_minutes_and_seconds():
    assert format_duration(125) == "2m 05s"


def test_format_duration_hours_minutes_seconds():
    assert format_duration(3723) == "1h 02m 03s"


def test_stats_rows_returns_label_value_pairs():
    save = SaveData()
    rows = stats_rows(save, session_seconds=0)
    assert all(isinstance(r, tuple) and len(r) == 2 for r in rows)
    labels = [label for label, _ in rows]
    assert "Balance" in labels
    assert "Net P/L" in labels
    assert "Session" in labels


def test_stats_rows_reflects_save_values():
    save = SaveData(balance=2500.0)
    save.stats.games_played = 7
    rows = dict(stats_rows(save, session_seconds=65))
    assert "2,500.00" in rows["Balance"]
    assert rows["Games played"] == "7"
    assert rows["Session"] == "1m 05s"
