import copy

from gambs import config
from gambs.save import SaveData
from gambs.cosmetics import (
    Theme,
    load_themes,
    find_theme,
    is_owned,
    is_active,
    can_buy,
    buy,
    equip,
    apply_active_theme,
)


def test_load_themes_includes_default_and_is_free():
    themes = load_themes(config.COSMETICS_PATH)
    default = find_theme(themes, "default")
    assert default is not None
    assert default.price == 0


def test_loaded_themes_have_palette_dicts():
    themes = load_themes(config.COSMETICS_PATH)
    for t in themes:
        assert isinstance(t, Theme)
        assert isinstance(t.palette, dict)


def test_default_save_owns_and_activates_default():
    save = SaveData()
    assert is_owned(save, "default")
    assert is_active(save, "default")


def test_can_buy_requires_unowned_funds_and_vip_level():
    theme = Theme("neon", "Neon", 1500.0, 1, {})
    assert can_buy(SaveData(balance=1500.0), theme) is True
    assert can_buy(SaveData(balance=100.0), theme) is False  # too poor
    owned = SaveData(balance=5000.0)
    owned.cosmetics["owned"].append("neon")
    assert can_buy(owned, theme) is False  # already owned


def test_can_buy_blocked_below_unlock_level():
    theme = Theme("vapor", "Vapor", 2000.0, 7, {})
    poor_level = SaveData(balance=9999.0)  # level 1
    assert can_buy(poor_level, theme) is False
    high = SaveData(balance=9999.0)
    high.vip.level = 7
    assert can_buy(high, theme) is True


def test_buy_deducts_and_adds_to_owned_but_does_not_equip():
    save = SaveData(balance=2000.0)
    theme = Theme("neon", "Neon", 1500.0, 1, {})
    assert buy(save, theme) is True
    assert save.balance == 500.0
    assert is_owned(save, "neon")
    assert is_active(save, "neon") is False


def test_buy_rejected_when_cannot_afford():
    save = SaveData(balance=100.0)
    theme = Theme("neon", "Neon", 1500.0, 1, {})
    assert buy(save, theme) is False
    assert is_owned(save, "neon") is False


def test_equip_requires_ownership():
    save = SaveData()
    assert equip(save, "neon") is False
    save.cosmetics["owned"].append("neon")
    assert equip(save, "neon") is True
    assert is_active(save, "neon")


def test_apply_active_theme_overrides_palette_then_restores():
    base = copy.deepcopy(config.COLORS)
    save = SaveData()
    save.cosmetics["owned"].append("neon")
    equip(save, "neon")
    themes = [Theme("neon", "Neon", 1500.0, 1, {"gold": "#abcdef"})]
    apply_active_theme(save, themes)
    assert config.COLORS["gold"] == "#abcdef"
    # equipping default restores the base palette
    equip(save, "default")
    apply_active_theme(save, themes + [Theme("default", "Default", 0, 1, {})])
    assert config.COLORS == base
