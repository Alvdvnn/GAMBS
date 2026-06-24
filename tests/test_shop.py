from gambs import config
from gambs.save import SaveData
from gambs.shop import (
    Item,
    load_items,
    find_item,
    owned_charges,
    has_charges,
    consume_charge,
    can_afford,
    purchase,
)


def test_load_items_reads_all_catalog_items():
    items = load_items(config.ITEMS_PATH)
    ids = {it.id for it in items}
    assert ids == {"lucky_charm", "insurance_card", "vault_key", "market_intel"}
    assert all(isinstance(it, Item) for it in items)


def test_loaded_items_have_correct_types():
    items = load_items(config.ITEMS_PATH)
    for it in items:
        assert isinstance(it.name, str) and it.name
        assert isinstance(it.effect, str) and it.effect
        assert isinstance(it.charges, int) and it.charges >= 1
        assert it.price > 0


def test_find_item_returns_match_or_none():
    items = load_items(config.ITEMS_PATH)
    assert find_item(items, "vault_key").name == "Vault Key"
    assert find_item(items, "nope") is None


def test_owned_charges_zero_when_unowned():
    save = SaveData()
    assert owned_charges(save, "lucky_charm") == 0


def test_owned_charges_reads_inventory():
    save = SaveData()
    save.inventory.append({"item_id": "lucky_charm", "charges": 2})
    assert owned_charges(save, "lucky_charm") == 2


def test_can_afford_boundary_is_inclusive():
    item = Item("x", "X", "fx", 1, 400.0)
    assert can_afford(SaveData(balance=400.0), item) is True
    assert can_afford(SaveData(balance=399.99), item) is False


def test_purchase_deducts_balance_and_creates_inventory_entry():
    save = SaveData(balance=1000.0)
    item = Item("lucky_charm", "Lucky Charm", "fx", 3, 400.0)
    assert purchase(save, item) is True
    assert save.balance == 600.0
    assert owned_charges(save, "lucky_charm") == 3
    assert save.inventory == [{"item_id": "lucky_charm", "charges": 3}]


def test_purchase_tops_up_charges_additively_on_rebuy():
    save = SaveData(balance=1000.0)
    item = Item("lucky_charm", "Lucky Charm", "fx", 3, 400.0)
    purchase(save, item)
    purchase(save, item)
    assert save.balance == 200.0
    assert owned_charges(save, "lucky_charm") == 6


def test_purchase_rejects_when_insufficient_funds():
    save = SaveData(balance=100.0)
    item = Item("vault_key", "Vault Key", "fx", 1, 800.0)
    assert purchase(save, item) is False
    assert save.balance == 100.0
    assert owned_charges(save, "vault_key") == 0


def test_has_charges_reflects_inventory():
    save = SaveData()
    assert has_charges(save, "lucky_charm") is False
    save.inventory.append({"item_id": "lucky_charm", "charges": 1})
    assert has_charges(save, "lucky_charm") is True


def test_consume_charge_decrements_then_removes_entry():
    save = SaveData()
    save.inventory.append({"item_id": "lucky_charm", "charges": 2})
    assert consume_charge(save, "lucky_charm") is True
    assert owned_charges(save, "lucky_charm") == 1
    assert consume_charge(save, "lucky_charm") is True
    assert owned_charges(save, "lucky_charm") == 0
    assert save.inventory == []  # entry removed at zero


def test_consume_charge_false_when_none_held():
    save = SaveData()
    assert consume_charge(save, "lucky_charm") is False
