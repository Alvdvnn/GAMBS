from gambs import config
from gambs.save import SaveData
from gambs.vip import (
    activity_xp,
    add_xp,
    can_prestige,
    do_prestige,
    xp_to_next,
    privileges_for,
)


def test_activity_xp_scales_with_amount():
    assert activity_xp(100.0) == int(100.0 * config.XP_PER_DOLLAR)
    assert activity_xp(0.0) == 1  # floor of 1 XP per activity


def test_add_xp_accumulates_within_a_level():
    save = SaveData()
    add_xp(save, 100)
    assert save.vip.level == 1
    assert save.vip.xp == 100


def test_add_xp_levels_up_and_carries_remainder():
    save = SaveData()
    add_xp(save, config.VIP_XP_PER_LEVEL + 30)
    assert save.vip.level == 2
    assert save.vip.xp == 30


def test_add_xp_handles_multiple_level_ups():
    save = SaveData()
    add_xp(save, config.VIP_XP_PER_LEVEL * 3 + 10)
    assert save.vip.level == 4
    assert save.vip.xp == 10


def test_add_xp_caps_at_max_level_with_full_bar():
    save = SaveData()
    add_xp(save, config.VIP_XP_PER_LEVEL * 50)
    assert save.vip.level == config.MAX_VIP_LEVEL
    assert save.vip.xp == config.VIP_XP_PER_LEVEL  # bar pinned full at cap


def test_xp_to_next_is_remaining_to_threshold():
    save = SaveData()
    add_xp(save, 200)
    assert xp_to_next(save) == config.VIP_XP_PER_LEVEL - 200


def test_can_prestige_only_at_max_level():
    save = SaveData()
    assert can_prestige(save) is False
    save.vip.level = config.MAX_VIP_LEVEL
    assert can_prestige(save) is True


def test_do_prestige_resets_and_adds_luck_buff():
    save = SaveData()
    save.vip.level = config.MAX_VIP_LEVEL
    save.vip.xp = 123
    assert do_prestige(save) is True
    assert save.vip.level == 1
    assert save.vip.xp == 0
    assert save.vip.prestige == 1
    assert save.vip.luck_buff == config.PRESTIGE_LUCK_STEP


def test_do_prestige_rejected_below_max():
    save = SaveData()
    assert do_prestige(save) is False
    assert save.vip.prestige == 0


def test_luck_buff_is_capped():
    save = SaveData()
    for _ in range(20):
        save.vip.level = config.MAX_VIP_LEVEL
        do_prestige(save)
    assert save.vip.luck_buff == config.MAX_LUCK_BUFF


def test_privileges_for_returns_text_for_each_band():
    assert privileges_for(1)
    assert privileges_for(3)
    assert privileges_for(10)
