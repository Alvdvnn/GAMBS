import io

from rich.console import Console

from gambs.save import default_save
from gambs.ui.prompts import bet_prompt


def _console():
    return Console(file=io.StringIO())


def test_bet_prompt_accepts_valid(monkeypatch):
    save = default_save()
    monkeypatch.setattr("builtins.input", lambda: "100")
    assert bet_prompt(_console(), save) == 100.0


def test_bet_prompt_blank_cancels(monkeypatch):
    save = default_save()
    monkeypatch.setattr("builtins.input", lambda: "   ")
    assert bet_prompt(_console(), save) is None


def test_bet_prompt_rejects_over_balance(monkeypatch):
    save = default_save()
    save.balance = 50.0
    monkeypatch.setattr("builtins.input", lambda: "100")
    assert bet_prompt(_console(), save) is None


def test_bet_prompt_rejects_nonpositive(monkeypatch):
    save = default_save()
    monkeypatch.setattr("builtins.input", lambda: "0")
    assert bet_prompt(_console(), save) is None


def test_bet_prompt_rejects_garbage(monkeypatch):
    save = default_save()
    monkeypatch.setattr("builtins.input", lambda: "abc")
    assert bet_prompt(_console(), save) is None


def test_bet_prompt_rejects_below_vip_min_bet(monkeypatch):
    save = default_save()
    save.balance = 5000.0
    save.vip.level = 5  # min bet $25
    monkeypatch.setattr("builtins.input", lambda: "10")
    assert bet_prompt(_console(), save) is None


def test_bet_prompt_accepts_at_vip_min_bet(monkeypatch):
    save = default_save()
    save.balance = 5000.0
    save.vip.level = 5
    monkeypatch.setattr("builtins.input", lambda: "25")
    assert bet_prompt(_console(), save) == 25.0
