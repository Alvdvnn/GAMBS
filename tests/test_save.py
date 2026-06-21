from gambs.save import SaveData, default_save, write_save, load_save, to_dict, from_dict


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


def test_to_dict_round_trips_nested_state():
    save = default_save()
    save.vip.level = 4
    save.inventory.append({"item_id": "lucky_charm", "charges": 2})
    restored = from_dict(to_dict(save))
    assert restored.vip.level == 4
    assert restored.inventory == [{"item_id": "lucky_charm", "charges": 2}]
    assert restored.cosmetics == {"owned": ["default"], "active": "default"}


def test_write_then_load_round_trip(tmp_path):
    path = tmp_path / "save.json"
    save = default_save()
    save.balance = 777.5
    save.stats.games_played = 3
    write_save(path, save)
    loaded = load_save(path)
    assert loaded.balance == 777.5
    assert loaded.stats.games_played == 3


def test_load_missing_file_returns_default(tmp_path):
    path = tmp_path / "does_not_exist.json"
    loaded = load_save(path)
    assert loaded.balance == 1000.0
    assert path.exists()  # default is persisted on first load
