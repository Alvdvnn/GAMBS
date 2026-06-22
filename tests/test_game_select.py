import io

from rich.console import Console

from gambs.games.registry import all_games, GameEntry
from gambs.ui.game_select import resolve_game_key, game_menu_panel


def test_registry_lists_crash_first():
    games = all_games()
    assert isinstance(games[0], GameEntry)
    assert games[0].id == "crash"


def test_registry_entries_are_callable():
    for entry in all_games():
        assert callable(entry.run)
        assert entry.label


def test_resolve_game_key_maps_digits_to_entries():
    import pytest
    if len(all_games()) < 5:
        pytest.skip("remaining games added in Tasks 3-6")
    games = all_games()
    assert resolve_game_key("1", games) is games[0]
    assert resolve_game_key("2", games) is games[1]


def test_resolve_game_key_out_of_range_is_none():
    import pytest
    if len(all_games()) < 5:
        pytest.skip("remaining games added in Tasks 3-6")
    games = all_games()
    assert resolve_game_key("0", games) is None
    assert resolve_game_key("9", games) is None
    assert resolve_game_key("x", games) is None


def test_menu_panel_lists_all_labels():
    games = all_games()
    console = Console(width=80, file=io.StringIO())
    with console.capture() as cap:
        console.print(game_menu_panel(games))
    out = cap.get()
    for entry in games:
        assert entry.label in out
