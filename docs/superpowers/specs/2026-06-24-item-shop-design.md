# Item Shop — Design Spec

Date: 2026-06-24
Status: Approved

## Summary

Build the **Item Shop infrastructure**: a data-driven catalog of consumable
items, a purchase/inventory layer, and the `[P] SHOP` screen. Items become
purchasable and owned (with charges), but their gameplay **effects are inert
this iteration** — wiring each effect into its game (Coinflip/Dice, Crash,
Bounty, Trading) is a separate follow-up feature.

This spec is **consumable items only**. Cosmetics (also reachable from the
SHOP menu label) remain a separate backlog feature.

## Scope

In scope:
- `data/items.json` catalog of the 4 spec items.
- Pure shop logic: load catalog, lookup, affordability, purchase (mutates save).
- The `[P] SHOP` screen: render catalog with owned charges, buy with balance.
- Route `shop` in `main.py` to the new screen.

Out of scope (explicitly):
- Item **effects** in any game (Lucky Charm, Insurance, Vault Key, Market Intel
  do nothing yet).
- The "only one item effect active at a time" rule (no effects to gate yet).
- Cosmetics purchasing.
- Save schema changes — the existing `inventory: list[dict]` of
  `{item_id, charges}` already covers ownership.

## Catalog — `data/items.json`

A JSON array; each item: `{id, name, effect, charges, price}`. `effect` is
descriptive text shown to the player; it carries no behavior this iteration.

| id | name | effect (text) | charges | price |
|----|------|---------------|---------|-------|
| `lucky_charm` | Lucky Charm | +10% win chance on Coin Flip / Dice for next N rounds | 3 | 400 |
| `insurance_card` | Insurance Card | If Crash busts, refund 50% of bet | 1 | 600 |
| `vault_key` | Vault Key | Unlock a HIGH-tier Bounty Job, skip cooldown once | 1 | 800 |
| `market_intel` | Market Intel | Reveal next price tick trend in Terminal Trading | 2 | 500 |

`config.ITEMS_PATH = DATA_DIR / "items.json"` is added alongside the existing
data paths.

## Pure logic — `gambs/shop.py`

No I/O beyond reading the catalog file; no RNG. All mutation is confined to
`purchase`, which changes only the passed `SaveData`.

```python
@dataclass
class Item:
    id: str
    name: str
    effect: str
    charges: int
    price: float

def load_items(path) -> list[Item]: ...
def find_item(items, item_id) -> Item | None: ...
def owned_charges(save, item_id) -> int: ...        # 0 if not owned
def can_afford(save, item) -> bool: ...             # save.balance >= item.price
def purchase(save, item) -> bool: ...               # see semantics below
```

### Purchase semantics

- If `not can_afford(save, item)`: return `False`, no change.
- Otherwise: deduct `item.price` from `save.balance` (rounded to 2dp); find the
  inventory entry for `item.id` and **add** `item.charges` to it, creating the
  entry `{ "item_id": id, "charges": item.charges }` if absent. Return `True`.
- Re-buying tops up charges additively, no cap. Items stay consumable — this
  never grants a permanent buff, honoring the fairness rules.

## Screen — `gambs/ui/shop_screen.py`

Interactive/render layer (manual-smoke only).

- `shop_table(save, items) -> Table` — columns: `[n]`, Name, Effect, Price,
  Owned (charge count). Rows the player cannot afford render dimmed.
- `run_shop(console, save) -> None` — loop:
  - clear; print `balance_bar_text`; print `shop_table`; print footer
    (`[1–N] buy   [ESC] back`).
  - read a key. Digit in range → `purchase`; if it succeeds, `write_save`.
    Unaffordable / out-of-range digits are ignored (re-render). `ESC`/`q`/`Q`
    returns to the main menu.

## main.py wiring

- Import `run_shop`.
- `elif route == "shop": run_shop(console, save)`.
- Remove `"shop"` from the `_coming_soon` tuple, leaving only `("vip",)`.

## Testing

Unit tests (`tests/test_shop.py`) on the pure layer:
- `load_items` reads all 4 catalog items with correct shape and types.
- `find_item` returns the item / `None`.
- `owned_charges` is 0 when unowned, reflects inventory otherwise.
- `can_afford` boundary (exact price affordable).
- `purchase` deducts balance and creates the inventory entry on first buy.
- `purchase` tops up charges additively on re-buy.
- `purchase` rejects when funds insufficient (returns `False`, no mutation).

The screen is verified by manual smoke (render `shop_table`, run `run_shop`).

## Risks / notes

- Owning an item with charges but no effect could confuse a player. Acceptable
  for this iteration; the effects follow-up closes the gap. Effect text in the
  table sets the expectation that the item "will" help.
