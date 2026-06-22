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
