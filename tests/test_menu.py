from gambs.save import default_save
from gambs.ui.menu import resolve_route, ROUTES, menu_panel


def test_known_keys_map_to_routes():
    assert resolve_route("g") == "gamble"
    assert resolve_route("e") == "earn"
    assert resolve_route("p") == "shop"
    assert resolve_route("v") == "vip"
    assert resolve_route("s") == "stats"
    assert resolve_route("q") == "quit"


def test_route_resolution_is_case_insensitive():
    assert resolve_route("G") == "gamble"


def test_unknown_key_returns_none():
    assert resolve_route("z") is None
    assert resolve_route("") is None


def test_menu_panel_lists_all_routes():
    panel = menu_panel(default_save())
    from rich.console import Console
    console = Console(width=80)
    with console.capture() as cap:
        console.print(panel)
    out = cap.get()
    for label in ("GAMBLE", "EARN", "SHOP", "VIP", "STATS", "QUIT"):
        assert label in out
