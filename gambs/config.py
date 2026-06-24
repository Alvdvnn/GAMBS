"""Central constants, color palette, and tunable parameters for GAMBS."""

from pathlib import Path

# --- Economy ---
STARTING_BALANCE: float = 1000.0
HOUSE_EDGE: float = 0.03

# --- VIP / prestige ---
VIP_XP_PER_LEVEL: int = 500
MAX_VIP_LEVEL: int = 10
XP_PER_DOLLAR: float = 0.1        # XP granted per $1 of wager / earnings
PRESTIGE_LUCK_STEP: float = 0.02  # luck buff gained per prestige
MAX_LUCK_BUFF: float = 0.10       # cap on stacked prestige luck buff

# --- Crash game tunables ---
CRASH_GROWTH_RATE: float = 0.15  # k in multiplier = e^(k * elapsed_seconds)
CRASH_TICK_SECONDS: float = 0.08  # animation frame interval

# --- Terminal Trading tunables ---
TRADING_STOCKS: list[str] = ["LUCK", "CHIP", "DICE", "RISK"]
TRADING_START_PRICE: float = 100.0
TRADING_MIN_PRICE: float = 1.0
TRADING_TICKS: int = 20          # player actions per session
TRADING_CAPITAL: float = 1000.0  # virtual session chips, NOT real balance

# --- Paths ---
DATA_DIR: Path = Path(__file__).resolve().parent / "data"
SAVE_PATH: Path = DATA_DIR / "save.json"

# --- Bounty Jobs tunables ---
BOUNTY_JOBS_PATH: Path = DATA_DIR / "bounty_jobs.json"
BOUNTY_COOLDOWN_SECONDS: float = 120.0

# --- Item Shop ---
ITEMS_PATH: Path = DATA_DIR / "items.json"

# --- Cosmetics ---
COSMETICS_PATH: Path = DATA_DIR / "cosmetics.json"

# --- Item effects ---
LUCKY_CHARM_BUFF: float = 0.10      # chance to rescue a loss on Coin Flip / Dice
INSURANCE_REFUND_RATE: float = 0.5  # fraction of bet refunded when Crash busts

# --- Color palette (hex, consumed by rich styles) ---
COLORS: dict[str, str] = {
    "bg": "#0a0a0f",
    "gold": "#ffd700",
    "gamble": "#ff6600",
    "earn": "#ff00ff",
    "success": "#00ff41",
    "danger": "#ff4444",
    "info": "#00ffff",
}
