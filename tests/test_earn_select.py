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


from gambs.ui.earn_select import resolve_earn_key, earn_menu_panel


def test_resolve_earn_key_maps_digits_to_entries():
    games = all_earn_games()
    assert resolve_earn_key("1", games) is games[0]


def test_resolve_earn_key_out_of_range_is_none():
    games = all_earn_games()
    assert resolve_earn_key("0", games) is None
    assert resolve_earn_key("9", games) is None
    assert resolve_earn_key("x", games) is None


def test_earn_menu_panel_lists_all_labels():
    games = all_earn_games()
    console = Console(width=80, file=io.StringIO())
    with console.capture() as cap:
        console.print(earn_menu_panel(games))
    out = cap.get()
    for entry in games:
        assert entry.label in out


def test_registry_includes_trading():
    ids = [g.id for g in all_earn_games()]
    assert "trading" in ids
