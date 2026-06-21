from gambs.save import SaveData, default_save


def test_default_save_starts_at_1000():
    save = default_save()
    assert save.balance == 1000.0


def test_default_save_has_empty_tutorial_and_inventory():
    save = default_save()
    assert save.tutorial_seen == []
    assert save.inventory == []


def test_default_vip_is_level_1():
    save = default_save()
    assert save.vip.level == 1
    assert save.vip.xp == 0
    assert save.vip.prestige == 0


def test_default_cosmetics_has_default_active():
    save = default_save()
    assert save.cosmetics == {"owned": ["default"], "active": "default"}


def test_default_save_sets_dates():
    save = default_save()
    assert save.created_at != ""
    assert save.last_played == save.created_at


def test_savedata_is_constructable_directly():
    save = SaveData(balance=42.0)
    assert save.balance == 42.0
    assert save.stats.games_played == 0
