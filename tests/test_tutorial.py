from gambs.save import default_save
from gambs.ui.tutorial import should_show_tutorial, mark_tutorial_seen, tutorial_panel


def test_unseen_game_shows_tutorial():
    save = default_save()
    assert should_show_tutorial(save, "crash") is True


def test_seen_game_does_not_show_tutorial():
    save = default_save()
    mark_tutorial_seen(save, "crash")
    assert should_show_tutorial(save, "crash") is False


def test_mark_seen_is_idempotent():
    save = default_save()
    mark_tutorial_seen(save, "crash")
    mark_tutorial_seen(save, "crash")
    assert save.tutorial_seen.count("crash") == 1


def test_tutorial_panel_includes_title_and_steps():
    panel = tutorial_panel("CRASH", ["Place a bet", "Press C to cash out"])
    from rich.console import Console
    console = Console(width=80)
    with console.capture() as cap:
        console.print(panel)
    out = cap.get()
    assert "CRASH" in out
    assert "Place a bet" in out
    assert "Press C to cash out" in out
