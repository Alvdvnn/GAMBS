import io

from rich.console import Console

from gambs.earn.registry import all_earn_games, EarnEntry


def test_registry_lists_typing_heist_first():
    games = all_earn_games()
    assert isinstance(games[0], EarnEntry)
    assert games[0].id == "typing_heist"


def test_registry_entries_are_callable():
    for entry in all_earn_games():
        assert callable(entry.run)
        assert entry.label
