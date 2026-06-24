"""Pure helpers for the Stats screen: derived metrics and the row model.

No I/O or rendering here — `stats_rows` returns plain (label, value) tuples
that the screen turns into a Rich table.
"""

from __future__ import annotations

from gambs import config
from gambs.save import SaveData


def net_pl(save: SaveData) -> float:
    """Net profit/loss across gamble games: gross returns minus all wagers."""
    return round(save.stats.total_won - save.stats.total_wagered, 2)


def bounty_success_rate(save: SaveData) -> float:
    """Fraction of attempted bounty jobs that were completed (0.0 if none)."""
    attempted = save.stats.bounty_jobs_attempted
    if attempted == 0:
        return 0.0
    return save.stats.bounty_jobs_completed / attempted


def format_duration(seconds: int) -> str:
    """Render a second count as a compact 'Xh YYm ZZs' / 'Ym ZZs' / 'Zs'."""
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h > 0:
        return f"{h}h {m:02d}m {s:02d}s"
    if m > 0:
        return f"{m}m {s:02d}s"
    return f"{s}s"


def stats_rows(save: SaveData, session_seconds: int) -> list[tuple[str, str]]:
    """Build the ordered (label, value) rows shown on the Stats screen."""
    st = save.stats
    best_crash = f"{st.best_crash_multiplier:.2f}x" if st.best_crash_multiplier else "—"
    rate = bounty_success_rate(save)
    return [
        ("Balance", f"${save.balance:,.2f}"),
        ("Total wagered", f"${st.total_wagered:,.2f}"),
        ("Total won", f"${st.total_won:,.2f}"),
        ("Net P/L", f"${net_pl(save):+,.2f}"),
        ("Total earned", f"${st.total_earned:,.2f}"),
        ("Games played", f"{st.games_played}"),
        ("Best Crash multiplier", best_crash),
        (
            "Bounty jobs",
            f"{st.bounty_jobs_completed}/{st.bounty_jobs_attempted} ({rate * 100:.0f}%)",
        ),
        (
            "VIP",
            f"Lv {save.vip.level} · Prestige {save.vip.prestige} · "
            f"{save.vip.xp}/{config.VIP_XP_PER_LEVEL} XP",
        ),
        ("Session", format_duration(session_seconds)),
    ]
