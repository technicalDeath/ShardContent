"""What every bot knows about items, in one place (the owner, 2026-10-30: "all bots of all brain types to have shared and standard intelligence and behavior
for basic game mechanics").

Before this, the same facts were copied into many brains and the copies drifted apart: the meat prices four times, the leather name test three times (the
casters' copy matched "cutleather" but the item is "cut up leather", so no caster ever sold leather), hide and leather weights five times, and three sets of
sale prices that disagreed. Every brain asks here now.

Sources:
- weights: the engine's DefaultWeight (Hides.cs 5.0, Leathers.cs 1.0, CookableFood.cs raw meats 1.0, Feather.cs 0.1)
- vendor prices: what a shop pays (SBButcher.cs InternalSellInfo: RawRibs 8, RawLambLeg 4, RawBird 4, RawChickenLeg 3; SBTanner.cs Leather 5;
  SBFurtrader.cs / SBLeatherWorker.cs Hides 2). Feathers have no stock buyer: 1.0 is what a feather fetched (the fighters' sale_task feathers, 2026-10-29)
- potion names: the era shows a potion by its colour ("Yellow Potion"); the simulator uses the potion's own name
"""
from __future__ import annotations

import re

# ---- potions ----------------------------------------------------------------------------------------------------------------------------------------------

POTION_NAMES = {
    "heal": ("yellow potion", "lesser heal potion", "heal potion", "greater heal potion"),
    "cure": ("orange potion", "lesser cure potion", "cure potion", "greater cure potion"),
    "refresh": ("red potion", "refresh potion", "total refresh potion"),
}


def potion_kind(name):
    """'heal', 'cure', 'refresh' or None for an item name."""
    n = (name or "").strip().lower()
    return next((k for k, names in POTION_NAMES.items() if n in names), None)


# ---- goods a shop buys ------------------------------------------------------------------------------------------------------------------------------------

GOODS_WORDS = ("leather", "hide", "raw ", "feather")          # in an item name: never banked, carried to a shop (every brain's KEEP holds these)


def is_leather(name):
    n = (name or "").strip().lower()
    return n.endswith("leather") and "armor" not in n          # "cut up leather" and "leather"; not "studded leather armor"


def is_hide(name):
    n = (name or "").strip().lower()
    return ("hide" in n) and not any(w in n for w in ("spined", "horned", "barbed"))   # the client shows "pile of hides", or "pil of hides" cut short


def is_meat(name):
    return "raw " in (name or "").lower()                       # "cut of raw ribs", "raw bird", "raw leg of lamb", "raw chicken leg"


def is_feather(name):
    return "feather" in (name or "").lower()


def is_goods(name):
    return is_leather(name) or is_hide(name) or is_meat(name) or is_feather(name)


# ---- weights (stones a piece) -----------------------------------------------------------------------------------------------------------------------------

def unit_weight(name):
    """Stones one piece weighs: hides 5, leather and raw meat 1, a feather 0.1; 1.0 for anything else (most loot)."""
    if is_hide(name):
        return 5.0
    if is_feather(name):
        return 0.1
    n = (name or "").lower()
    if n in MAT_WEIGHT:
        return MAT_WEIGHT[n]
    if n.endswith("board") and n != "board":
        return 5.0                                      # a game board, backgammon board (BaseBoard.cs DefaultWeight 5)
    return 1.0


# ---- what a shop pays (gold a piece) ----------------------------------------------------------------------------------------------------------------------

MEAT_PRICE = (("ribs", 8), ("lamb", 4), ("bird", 4), ("chicken", 3))      # SBButcher.cs: RawRibs, RawLambLeg, RawBird, RawChickenLeg
LEATHER_PRICE = 5                                                          # SBTanner.cs: Leather
HIDE_PRICE = 2                                                             # SBFurtrader.cs, SBLeatherWorker.cs: Hides
FEATHER_PRICE = 1.0                                                        # measured: no stock shop buys feathers
HIDE_CUT_VALUE = LEATHER_PRICE                                             # a hide cut with scissors is one leather (Hides.Scissor): every bot cuts before selling
# what the shops SELL crafting material for (the engine's SBInfo buy lists): the market's ceiling when no bot has seen the shelf. Without it no shop price
# for iron ingots was known, the ceiling fell back to twice the buy price (8), and smiths paid miners 6 for what the Blacksmith sells at 5 (2026-10-30)
SHOP_SELLS = {"iron ingot": 5, "board": 3, "cut cloth": 2, "bolt of cloth": 100}     # SBBlacksmith/SBTinker/SBSmithTools 5, SBCarpenter 3, SBTailor 2 and 100
MAT_WEIGHT = {"board": 1.0, "boards": 1.0, "log": 2.0, "logs": 2.0, "iron ingot": 0.1, "iron ingots": 0.1, "ingots": 0.1, "cloth": 0.1, "cut cloth": 0.1}
# Log.cs 2.0, Ingots.cs 0.1, Cloth.cs 0.1; a board has no override (tiledata): 49 bought put 54 stones on BotCarpAdvR (2026-10-31), about 1
SHELF_NAMES = {"iron ingot": ("ingots",)}      # the buy list names the stock IronIngot "Ingots" (cliloc of 0x1BF2): "iron ingot" alone found only a 7 gp "Iron Ingots" row and priced bot deals at 6


def sale_price(name):
    """Gold a shop pays for one piece of a good, else 0."""
    n = (name or "").lower()
    if is_meat(n):
        return next((p for w, p in MEAT_PRICE if w in n), 3)
    if is_leather(n):
        return LEATHER_PRICE
    if is_hide(n):
        return HIDE_PRICE
    if is_feather(n):
        return FEATHER_PRICE
    return 0


def goods_value(items):
    """Gold the goods among these items fetch at the shops."""
    return sum(float(i.amount or 1) * sale_price(i.name) for i in items)


def goods_weight(items):
    return sum(float(i.amount or 1) * unit_weight(i.name) for i in items if is_goods(i.name))


# ---- corpses ----------------------------------------------------------------------------------------------------------------------------------------------

def corpse_kind(corpse_name):
    """The kind key of a corpse ("a great hart corpse" -> "greathart"), as BotBase.mkey names the living one."""
    n = re.sub(r"^(an?|the) ", "", (corpse_name or "").lower())
    n = re.sub(r"( corpse| remains)$", "", n)
    return re.sub(r"[^a-z]", "", n)
