from gambs.save import default_save
from gambs.ui.components import balance_bar_text


def test_balance_bar_shows_formatted_balance():
    save = default_save()
    save.balance = 1250.0
    text = balance_bar_text(save)
    assert "$1,250.00" in text


def test_balance_bar_shows_vip_level_and_xp():
    save = default_save()
    save.vip.level = 4
    save.vip.xp = 320
    text = balance_bar_text(save)
    assert "VIP 4" in text
    assert "320/500" in text
