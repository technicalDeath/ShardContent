"""What the simulated world is built from: the farm's own generated data and the shard's data files, loaded once.

    spawners        the canonical spawners of the Felucca surface within RADIUS of the centre, and those of the seven rung dungeons (item 5: Despise, Shame,
                    Deceit, Covetous, Wrong, Destard, Hythloth) on the dungeon side
    creatures       creature_stats.json (hits, damage, skills, armor, karma, ai) and fightmodes.json (who attacks on sight)
    loot            loot_value.json (gold, meat, hides per kind)
    places          the gazetteer's vendors, bankers, healers, guards and fixtures (forge, anvil, loom, oven, dummy)
    shops           work/botfarm/shops.json (the last stock list seen at each shop) and the shared memory's vendor events (names, what each buys)
    walk / water    walkgrid.bin (walkroute.py) and watergrid.bin; walkgrid-dungeons.bin for x 5120 and beyond (the dungeon side, doors open)
    transitions     the gazetteer's teleporter pairs (standing on an entry moves the bot to its exit)
    craft           craft_data.json; weapons weapon_table.json; trees trees.json; mountains mountains.json

Nothing here is live: every file is read from disk at construction. Missing optional files leave an empty table and a warning in `notes`.
"""
from __future__ import annotations

import json
import os
import re
import struct
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
BOTFARM = os.path.abspath(os.path.join(HERE, ".."))
ROOT = os.path.abspath(os.path.join(BOTFARM, "..", "..", "..", ".."))
FARM = os.path.join(ROOT, "work", "botfarm")
SPAWNS = os.path.join(ROOT, "ModernUO", "Distribution", "Data", "BritanniaRenaissance", "Alpha2b", "Spawns")
if BOTFARM not in sys.path:
    sys.path.insert(0, BOTFARM)

BRITAIN = (1470, 1620)
RADIUS = 900                                   # tiles from the centre a spawner must lie within to be simulated (the farm's bots never went further)
SURFACE_X = 5120
RUNG_DUNGEONS = ("Despise", "Shame", "Deceit", "Covetous", "Wrong", "Destard", "Hythloth")

# the fight modes that attack a player on sight (fightmodes.json, ModernUO FightMode); the rest only fight back
AGGRESSIVE_MODES = {"Closest", "Weakest", "Strongest"}
# a vendor's roles in the gazetteer (places with one of these become people a bot can talk to); fixtures become immovable ground items
VENDOR_ROLES = {"alchemist", "armorer", "baker", "banker", "bank", "bard", "beekeeper", "blacksmith", "smith", "bowyer", "butcher", "carpenter", "cobbler", "cook",
                "fisherman", "furtrader", "healer", "herbalist", "innkeeper", "jeweler", "leatherworker", "mage", "mapmaker", "miner", "provisioner", "ranger",
                "scribe", "shipwright", "tailor", "tanner", "tavernkeeper", "tinker", "veterinarian", "weaponsmith", "weaver", "animal_trainer", "architect",
                "real_estate_broker", "stablemaster", "guildmaster", "minter", "waiter", "barkeeper", "glassblower", "furnisher", "farmer", "rancher"}
FIXTURE_ROLES = {"forge": ("forge", 0x0FB1), "anvil": ("anvil", 0x0FAF), "loom": ("loom", 0x105F), "oven": ("stone oven", 0x0461), "dummy": ("training dummy", 0x1070),
                 "butte": ("archery butte", 0x100A), "ankh": ("ankh", 0x0003), "spinning_wheel": ("spinning wheel", 0x1015)}
NAMES = ["Neoma", "Jina", "Minda", "Prentice", "Aithne", "Aprille", "Elston", "Noella", "Chantal", "Caitrin", "Valentina", "Lari", "Merill", "Belora", "Lauryn",
         "Monte", "Karol", "Jumoke", "Kaatje", "Ariadne", "Tosia", "Aimee", "Yeva", "Shantha", "Hale", "Yanice", "Tyee", "Nevada", "Doris", "Finola", "Gizane",
         "Allinora", "Salimah", "Nicolette", "Greger", "Braina", "Aiko", "Delmore", "Diwarek", "Fandagh", "Ughat", "Zachariah", "Bellanca", "Caitlin", "Teodor",
         "Wenna", "Orrin", "Hesper", "Lysa", "Marek", "Ysolde", "Baldric", "Corwin", "Deryn", "Eluned", "Fenwick", "Gwenna", "Hamund", "Idony", "Joss"]

# a shop's list when shops.json has none within reach of the vendor: (item, price, quantity) by role
ROLE_STOCK = {
    "provisioner": [("Bandage", 3, 20), ("Backpack", 15, 20), ("Candle", 6, 20), ("Torch", 8, 20), ("Bread Loaf", 6, 20), ("Fishing Pole", 15, 20), ("Kindling", 2, 20)],
    "healer": [("Bandage", 3, 20), ("Yellow Potion", 15, 20), ("Red Potion", 15, 20)],          # the era shows potions by colour: Heal yellow, Refresh red, Cure orange (the brains buy them so)
    "mage": [("Black Pearl", 5, 20), ("Blood Moss", 5, 20), ("Garlic", 3, 20), ("Ginseng", 3, 20), ("Mandrake Root", 3, 20), ("Nightshade", 3, 20), ("Spider's Silk", 3, 20),
             ("Sulfurous Ash", 3, 20), ("Blank Scroll", 5, 20), ("Recall Rune", 15, 20), ("Spellbook", 18, 20)],
    "alchemist": [("Empty Bottle", 5, 20), ("Mortar And Pestle", 8, 20), ("Blood Moss", 5, 20), ("Nightshade", 3, 20), ("Mandrake Root", 3, 20), ("Garlic", 3, 20), ("Ginseng", 3, 20),
                  ("Yellow Potion", 15, 20), ("Red Potion", 15, 20), ("Orange Potion", 15, 20)],
    "tinker": [("Tongs", 7, 20), ("Sewing Kit", 3, 20), ("Pickaxe", 11, 20), ("Shovel", 12, 20), ("Tinker's Tools", 6, 20), ("Hatchet", 15, 20), ("Saw", 14, 20),
               ("Smith's Hammer", 10, 20), ("Scissors", 11, 20), ("Butcher Knife", 13, 20), ("Dagger", 20, 20), ("Lockpick", 12, 20)],
    "bowyer": [("Arrow", 2, 20), ("Bolt", 3, 20), ("Bow", 35, 20), ("Crossbow", 50, 20), ("Heavy Crossbow", 60, 20), ("Arrow Fletching", 8, 20), ("Feather", 2, 20), ("Shaft", 2, 20)],
    "smith": [("Tongs", 7, 20), ("Iron Ingot", 5, 20), ("Dagger", 20, 20), ("Mace", 38, 20), ("Katana", 50, 20), ("Kryss", 36, 20), ("Longsword", 55, 20), ("Club", 24, 20),
              ("Ringmail Tunic", 120, 20), ("Chainmail Coif", 60, 20), ("Leather Tunic", 30, 20), ("Buckler", 50, 20)],
    "weaponsmith": [("Dagger", 20, 20), ("Mace", 38, 20), ("Katana", 50, 20), ("Kryss", 36, 20), ("Longsword", 55, 20), ("Club", 24, 20), ("War Mace", 60, 20), ("Spear", 40, 20)],
    "armorer": [("Leather Tunic", 30, 20), ("Leather Leggings", 25, 20), ("Leather Gloves", 20, 20), ("Leather Gorget", 20, 20), ("Leather Cap", 15, 20), ("Leather Sleeves", 20, 20),
                ("Studded Tunic", 60, 20), ("Ringmail Tunic", 120, 20), ("Chainmail Tunic", 160, 20), ("Buckler", 50, 20), ("Wooden Shield", 40, 20)],
    "tailor": [("Scissors", 11, 20), ("Sewing Kit", 3, 20), ("Bolt Of Cloth", 100, 20), ("Folded Cloth", 3, 20), ("Cut Cloth", 2, 20), ("Dyes", 8, 20), ("Dye Tub", 8, 20)],
    "weaver": [("Bolt Of Cloth", 100, 20), ("Folded Cloth", 3, 20), ("Cut Cloth", 2, 20), ("Ball Of Yarn", 18, 20), ("Thread", 10, 20)],
    "carpenter": [("Board", 3, 20), ("Log", 2, 20), ("Saw", 14, 20), ("Hatchet", 15, 20), ("Hammer", 10, 20), ("Nails", 3, 20), ("Dovetail Saw", 12, 20)],
    "butcher": [("Butcher Knife", 13, 20), ("Cleaver", 13, 20), ("Cut Of Raw Ribs", 8, 20), ("Raw Chicken Leg", 3, 20)],
    "fisherman": [("Fishing Pole", 15, 20), ("Fish Steak", 3, 20), ("Fish", 4, 20)],
    "cook": [("Bread Loaf", 6, 20), ("Fish Steak", 3, 20), ("Cooked Bird", 7, 20), ("Rolling Pin", 2, 20), ("Flour Sifter", 2, 20)],
    "cobbler": [("Boots", 18, 20), ("Thigh Boots", 20, 20), ("Shoes", 13, 20), ("Sandals", 11, 20)],
    "tanner": [("Leather Tunic", 30, 20), ("Leather Leggings", 25, 20), ("Leather Cap", 15, 20), ("Pile Of Hides", 6, 20), ("Leather", 6, 20)],
    "scribe": [("Blank Scroll", 5, 20), ("Spellbook", 18, 20), ("Recall Scroll", 23, 20), ("Mark Scroll", 23, 20)],
    "bard": [("Lute", 132, 20), ("Lap Harp", 113, 20), ("Drum", 113, 20), ("Tambourine", 95, 20)],
    "animal_trainer": [("Pack Horse", 630, 20), ("Horse", 550, 20), ("Dog", 180, 20), ("Cat", 140, 20)],
    "ranger": [("Bow", 35, 20), ("Arrow", 2, 20), ("Fishing Pole", 15, 20)],
    "architect": [("Small Stone And Plaster House Deed", 16000, 20), ("Small Brick House Deed", 16000, 20)],
}
# what a vendor pays for things a bot carries, by role (per piece), when the shared memory has no record of it
ROLE_BUYS = {
    "butcher": {"cut of raw ribs": 8, "raw ribs": 8, "raw lamb": 4, "leg of lamb": 4, "raw bird": 4, "raw chicken": 3, "raw leg": 3, "raw fish steak": 3},
    "cook": {"fish steak": 3, "raw fish steak": 3, "cooked bird": 4},
    "fisherman": {"fish": 4, "big fish": 10, "fish steak": 3},
    "tanner": {"pile of hides": 2, "hides": 2, "leather": 3, "spined hides": 3, "leather tunic": 15, "leather leggings": 12},
    "smith": {"iron ingots": 4, "iron ingot": 4, "mace": 38, "dagger": 10, "tongs": 7, "pickaxe": 13, "smith's hammer": 10, "club": 12, "katana": 25, "kryss": 18, "longsword": 27},
    "weaponsmith": {"mace": 38, "dagger": 10, "club": 12, "katana": 25, "kryss": 18, "longsword": 27, "spear": 20, "war mace": 30, "bow": 17, "crossbow": 25},
    "armorer": {"leather tunic": 15, "leather leggings": 12, "leather gloves": 10, "leather gorget": 10, "leather cap": 7, "ringmail tunic": 60, "chainmail coif": 30, "buckler": 25,
                "wooden shield": 20, "studded tunic": 30},
    "tinker": {"tongs": 7, "pickaxe": 16, "hammer": 3, "butcher knife": 13, "lockpick": 7, "smith's hammer": 11, "sewing kit": 1, "gears": 0, "hinge": 0, "springs": 0},
    "carpenter": {"board": 2, "log": 1, "saw": 9, "chair": 33, "wooden box": 25, "wooden shield": 28, "crate": 38, "ballot box": 13, "small crate": 20, "stool": 25, "bench": 30},
    "tailor": {"cut cloth": 1, "folded cloth": 1, "bolt of cloth": 50, "skirt": 10, "cloak": 14, "robe": 16, "body sash": 4, "half apron": 6, "full apron": 10, "shirt": 10,
               "fancy shirt": 15, "long pants": 12, "short pants": 10, "tunic": 12, "doublet": 14, "cap": 7, "bandana": 5, "skullcap": 6},
    "weaver": {"cut cloth": 1, "folded cloth": 1, "bolt of cloth": 50},
    "bowyer": {"arrow": 1, "bolt": 1, "bow": 17, "crossbow": 25, "shaft": 1, "feather": 1, "arrow fletching": 4},
    "provisioner": {"bandage": 1, "fish steak": 3, "backpack": 7, "candle": 3},
    "mage": {"black pearl": 2, "blood moss": 2, "garlic": 1, "ginseng": 1, "mandrake root": 1, "nightshade": 1, "spider's silk": 1, "sulfurous ash": 1, "recall scroll": 23,
             "mark scroll": 23, "blank scroll": 2, "spellbook": 9},
    "scribe": {"recall scroll": 23, "mark scroll": 23, "blank scroll": 2, "spellbook": 9},
    "alchemist": {"empty bottle": 2, "black pearl": 2, "blood moss": 2, "garlic": 1, "ginseng": 1, "mandrake root": 1, "nightshade": 1},
    "healer": {"bandage": 1},
    "jeweler": {"ruby": 37, "sapphire": 50, "emerald": 50, "diamond": 100, "amber": 25, "citrine": 25, "tourmaline": 37, "amethyst": 50, "star sapphire": 62},
}
ARTICLE = re.compile(r"^(an?|the) ", re.I)

# a pack's worth, for the comprehensive net worth (the owner, 2026-10-21: "make the net worth calculation more comprehensive"): gold and bank PLUS what is held.
# Consumables (bandages, potions, reagents, arrows, scrolls) count at the price a shop SELLS them, since that is what replacing them costs; everything else at the
# best price a shop pays for it (ROLE_BUYS and the shared memory's buy-back records); an item no shop buys counts for nothing.
STACK_FULL, STACK_REST = 40, 0.25       # items of one kind up to STACK_FULL count in full, beyond it at a quarter
CONSUMABLES = ("bandage", "potion", "arrow", "bolt", "pearl", "moss", "garlic", "ginseng", "mandrake", "nightshade", "silk", "ash", "scroll", "kindling", "feather", "shaft")


def price_tables(vendor_buys=None):
    """({item: replacement price}, {item: best buy-back price}) over the role tables, both keyed by lower-case item name."""
    stock, buy = {}, {}
    for role, rows in ROLE_STOCK.items():
        for name, price, _q in rows:
            n = name.lower()
            stock[n] = min(stock.get(n, price), price)
    for role, d in ROLE_BUYS.items():
        for name, price in d.items():
            buy[name.lower()] = max(buy.get(name.lower(), 0), price)
    seen = {}
    for _xy, d in (vendor_buys or {}).items():                      # what shops were actually seen to pay overrides the role table (a butcher pays 4 for ribs, not 8)
        for name, price in d.items():
            n = str(name).lower()
            seen[n] = max(seen.get(n, 0), int(price))
    buy.update(seen)
    return stock, buy


def holdings_by_item(items, tables, top=6):
    """{item name: value} of the most valuable held items (holdings_value's pricing), for the metrics rows: what a bot's wealth is made of."""
    out = {}
    for it in items:
        n = (it.get("name") or "").lower()
        v = holdings_value([it], tables)
        if v:
            out[n] = out.get(n, 0) + v
    return dict(sorted(out.items(), key=lambda kv: -kv[1])[:top])


def holdings_value(items, tables):
    """The value of a list of item dicts ({"name", "amount"}) by price_tables: consumables at the replacement price, the rest at the buy-back price."""
    stock, buy = tables
    total = 0
    for it in items:
        n = (it.get("name") or "").lower()
        if n in ("gold coin", "gold"):
            continue
        amt = it.get("amount") or 1
        if any(w in n for w in CONSUMABLES):
            v = stock.get(n)
            if v is None:
                v = next((p for k, p in stock.items() if k in n or n in k), 0)
        else:
            v = buy.get(n)
            if v is None:
                v = next((p for k, p in buy.items() if k == n or (len(k) > 4 and k in n)), 0)
        amt = int(amt)
        total += int(v or 0) * (min(amt, STACK_FULL) + STACK_REST * max(0, amt - STACK_FULL))        # a shop takes about 20 of a kind an hour: a hoard is not cash
    return total


def norm(s):
    return re.sub(r"[^a-z]", "", str(s).lower())


def delay_s(text, default=300.0):
    try:
        h, m, s = (int(v) for v in str(text).split(":"))
        return h * 3600 + m * 60 + s
    except (ValueError, AttributeError):
        return default


def _load(path, default):
    try:
        return json.load(open(path, encoding="utf-8-sig"))
    except (OSError, ValueError):
        return default


class BitGrid:
    """walkgrid.bin / watergrid.bin: W x H bits, index x * H + y; x0 is the first column the file holds (5120 for walkgrid-dungeons.bin)."""

    def __init__(self, path, magic, x0=0):
        raw = open(path, "rb").read()
        assert raw[:len(magic)] == magic, f"{path}: not a {magic!r} file"
        if magic == b"WGRD1":
            self.W, self.H, n = struct.unpack_from("<HHI", raw, 5)
            self.bits = zlib.decompress(raw[13:13 + n])
        else:
            self.W, self.H = struct.unpack_from("<HH", raw, 4)
            self.bits = zlib.decompress(raw[8:])
        self.x0 = int(x0)

    def get(self, x, y):
        x -= self.x0
        if not (0 <= x < self.W and 0 <= y < self.H):
            return False
        i = x * self.H + y
        return (self.bits[i >> 3] >> (i & 7)) & 1 == 1


class WorldData:
    def __init__(self, centre=BRITAIN, radius=RADIUS, farm_dir=FARM, spawn_dir=SPAWNS, botfarm_dir=BOTFARM):
        self.notes = []
        self.centre, self.radius = centre, radius
        self.creatures = _load(os.path.join(botfarm_dir, "creature_stats.json"), {})
        self.fightmodes = _load(os.path.join(botfarm_dir, "fightmodes.json"), {})
        self.loot = _load(os.path.join(botfarm_dir, "loot_value.json"), {}).get("kinds", {})
        self.craft = _load(os.path.join(botfarm_dir, "craft_data.json"), {})
        self.weapons = _load(os.path.join(botfarm_dir, "weapon_table.json"), {}).get("weapons", {})
        self.trees = [tuple(t) for t in _load(os.path.join(botfarm_dir, "trees.json"), [])]
        self.mountains = [tuple(t[:4]) for t in _load(os.path.join(botfarm_dir, "mountains.json"), [])]
        self.gazetteer = _load(os.path.join(botfarm_dir, "gazetteer.json"), {"regions": [], "places": [], "transitions": []})
        self.spells = _load(os.path.join(botfarm_dir, "..", "new-mage-playtest", "game_data.json"), {}).get("spells", {})
        self.tame = {k: v for k, v in _load(os.path.join(botfarm_dir, "tame_data.json"), {}).items() if isinstance(v, dict) and "min" in v}
        try:
            self.walk = BitGrid(os.path.join(botfarm_dir, "walkgrid.bin"), b"WGRD1")
        except (OSError, AssertionError) as e:
            self.walk = None
            self.notes.append(f"no walk grid ({e}): every tile walkable")
        try:
            self.dwalk = BitGrid(os.path.join(botfarm_dir, "walkgrid-dungeons.bin"), b"WGRD1", x0=SURFACE_X)
        except (OSError, AssertionError) as e:
            self.dwalk = None
            self.notes.append(f"no dungeon walk grid ({e}): the dungeon side is blocked")
        try:
            self.water = BitGrid(os.path.join(botfarm_dir, "watergrid.bin"), b"WTR1")
        except (OSError, AssertionError) as e:
            self.water = None
            self.notes.append(f"no water grid ({e}): no fishing water")
        self.shops = _load(os.path.join(farm_dir, "shops.json"), {})
        self.vendor_names, self.vendor_buys, self.vendor_stock = self._memory_vendors(os.path.join(farm_dir, "memory", "world.jsonl"))
        self.flee_first_hit = {}
        try:
            self.flee_first_hit = json.load(open(os.path.join(HERE, "live_reference.json"), encoding="utf-8")).get("lost_by_kind", {})        # the live share of fights each kind escapes
        except (OSError, ValueError):
            pass
        self.regions = self.gazetteer.get("regions", [])
        self.towns = [r for r in self.regions if r.get("kind") == "town"]
        self.gates = [(int(p["x"]), int(p["y"])) for p in self.gazetteer.get("places", []) if p.get("role") == "moongate" and int(p.get("x", 99999)) < SURFACE_X]
        self.transitions = {(int(t["src"][0]), int(t["src"][1])): (int(t["dst"][0]), int(t["dst"][1]), t.get("src_side"), t.get("dst_side"))
                            for t in self.gazetteer.get("transitions", []) if t.get("src") and t.get("dst")}
        self.tele_tiles = set(self.transitions)                # a teleporter's entry is stood on whatever the grid says of the tile (a cave mouth, a stair)
        self.spawners = self._spawners(spawn_dir)
        self.places = self._places()

    def side(self, x, y):
        """The side of the map a point is on (gazetteer.side_of): "surface", a dungeon or town region's name, or a coarse cell of the dungeon side."""
        import gazetteer
        return gazetteer.side_of(self.regions, int(x), int(y))

    # ---- spawners -----------------------------------------------------------------------------------------------------------------------------------

    def _spawners(self, spawn_dir):
        import spawners as sp
        out = []
        if not os.path.isdir(spawn_dir):
            self.notes.append(f"no spawner folder {spawn_dir}: an empty world")
            return out
        cx, cy = self.centre
        for _f, s in sp.canonical(spawn_dir):
            loc = s.get("location") or [0, 0, 0]
            if s.get("map") not in ("Felucca", 0):
                continue
            if loc[0] >= SURFACE_X:
                if self.side(loc[0], loc[1]) not in RUNG_DUNGEONS:
                    continue                                       # the dungeon side: the rung dungeons only
            elif max(abs(loc[0] - cx), abs(loc[1] - cy)) > self.radius:
                continue
            entries = [(norm(e.get("name")), int(e.get("maxCount", 1) or 1)) for e in s.get("entries", []) if norm(e.get("name")) in self.creatures]
            if not entries:
                continue                                           # reagent and item spawners, or creatures the stats table does not know
            out.append({"guid": s.get("guid"), "x": loc[0], "y": loc[1], "z": loc[2] if len(loc) > 2 else 0, "count": int(s.get("count", 1) or 1),
                        "home": int(s.get("homeRange", 10) or 10), "walk": int(s.get("walkingRange", s.get("homeRange", 10)) or 10),
                        "min_delay": delay_s(s.get("minDelay"), 300), "max_delay": delay_s(s.get("maxDelay"), 600), "entries": entries})
        return out

    # ---- creatures ----------------------------------------------------------------------------------------------------------------------------------

    def creature(self, kind):
        return self.creatures.get(kind)

    def aggressive(self, kind):
        """Attacks a player on sight (FightMode Closest / Weakest / Strongest); a karma-negative monster without a recorded mode counts as aggressive."""
        fm = self.fightmodes.get(kind)
        if fm and fm.get("mode"):
            return fm["mode"] in AGGRESSIVE_MODES
        c = self.creatures.get(kind) or {}
        return (c.get("karma") or 0) < 0

    def display_name(self, kind):
        c = self.creatures.get(kind) or {}
        return c.get("name") or ("a " + kind)

    def species(self, kind):
        cls = (self.creatures.get(kind) or {}).get("class") or kind
        return re.sub(r"(?<=[a-z])(?=[A-Z])", " ", cls)

    # ---- places -------------------------------------------------------------------------------------------------------------------------------------

    def _memory_vendors(self, path):
        names, buys, stock = {}, {}, {}
        try:
            f = open(path, encoding="utf-8", errors="replace")
        except OSError:
            self.notes.append("no shared memory world.jsonl: vendors named from a list, buy-back prices by role")
            return names, buys, stock
        with f:
            for line in f:
                if '"k":"vendor"' not in line:
                    continue
                try:
                    e = json.loads(line)
                except ValueError:
                    continue
                xy = e.get("xy")
                if not xy:
                    continue
                if e.get("name"):
                    names.setdefault(xy, [])
                    if e["name"] not in names[xy]:
                        names[xy].append(e["name"])
                for item, p in (e.get("buys") or []):
                    buys.setdefault(xy, {})[str(item).lower()] = int(p)
                if e.get("stock"):
                    # every read, the largest quantity seen per item: a shop's list is what it holds when stocked, not what the last bot found (a sold-out healer's
                    # last read had no bandages, and the simulated healer lost them; 2026-10-21)
                    cur = {i: (pr, q) for i, pr, q in stock.get(xy, [])}
                    for i, pr, q in e["stock"]:
                        if str(i):
                            old_q = cur.get(str(i), (0, 0))[1]
                            cur[str(i)] = (int(pr), max(int(q), old_q))
                    stock[xy] = [(i, pr, q) for i, (pr, q) in cur.items()]
        return names, buys, stock

    def _nearest_key(self, table, x, y, reach):
        best, bd = None, reach + 1
        for k in table:
            m = re.match(r"\(?(\d+),\s*(\d+)\)?$", str(k))
            if not m:
                continue
            d = max(abs(int(m.group(1)) - x), abs(int(m.group(2)) - y))
            if d < bd:
                best, bd = k, d
        return best

    def _places(self):
        """People and fixtures from the gazetteer, within the simulated radius: [{"kind": "vendor"|"fixture"|"guard", "role", "roles", "name", "x", "y", "z", "stock", "buys"}]."""
        out = []
        cx, cy = self.centre
        name_i = 0
        for p in self.gazetteer.get("places", []):
            x, y = p.get("x"), p.get("y")
            if x is None or x >= SURFACE_X or max(abs(x - cx), abs(y - cy)) > self.radius:
                continue
            roles = set(p.get("roles", []))
            fixture = next((r for r in FIXTURE_ROLES if r in roles), None)
            if fixture:
                label, graphic = FIXTURE_ROLES[fixture]
                out.append({"kind": "fixture", "role": fixture, "roles": sorted(roles), "name": label, "graphic": graphic, "x": x, "y": y, "z": p.get("z", 0)})
                continue
            if "guard" in roles or "orderguard" in roles:
                out.append({"kind": "guard", "role": "guard", "roles": sorted(roles), "name": "a guard", "x": x, "y": y, "z": p.get("z", 0)})
                continue
            vrole = next((r for r in ("bank", "healer", "mage", "tinker", "smith", "weaponsmith", "armorer", "bowyer", "tailor", "weaver", "carpenter", "butcher", "provisioner",
                                      "alchemist", "cobbler", "tanner", "fisherman", "cook", "scribe", "bard", "animal_trainer", "ranger", "architect", "jeweler") if r in roles), None)
            if vrole is None:
                vrole = next((r for r in roles if r in VENDOR_ROLES), None)
            if vrole is None:
                continue
            n = int(p.get("n", 1) or 1)
            key = f"{x},{y}"
            known = list(self.vendor_names.get(key, []))
            for k2 in list(self.vendor_names):
                if k2 != key and max(abs(int(k2.split(",")[0]) - x), abs(int(k2.split(",")[1]) - y)) <= 3:
                    known += [nm for nm in self.vendor_names[k2] if nm not in known]
            shop_key = self._nearest_key(self.shops, x, y, 8)
            stock = []
            if shop_key:
                for l in self.shops[shop_key][1:]:
                    m = re.search(r"(\d+)gp\s+x(\d+)\s+(.+)", l)
                    if m:
                        stock.append((m.group(3).strip(), int(m.group(1)), int(m.group(2))))
            mk = self._nearest_key(self.vendor_stock, x, y, 8 if not stock else 2)       # the union only from the vendor's own record (two tiles): a neighbouring shop's items are not hers
            seen_all = list(self.vendor_stock.get(mk, [])) if mk else []
            if not stock:
                stock = seen_all
            else:
                have = {n.lower() for n, _p, _q in stock}
                stock += [r for r in seen_all if r[0].lower() not in have]            # items the live list lacked when it was read (sold out) but the shop holds when stocked
            if not stock:
                stock = list(ROLE_STOCK.get(vrole, []))
            buys = dict(ROLE_BUYS.get(vrole, {}))
            bk = self._nearest_key(self.vendor_buys, x, y, 8)
            if bk:
                buys.update(self.vendor_buys[bk])
            for i in range(n):
                name = known[i] if i < len(known) else NAMES[name_i % len(NAMES)]
                if i >= len(known):
                    name_i += 1
                out.append({"kind": "vendor", "role": vrole, "roles": sorted(roles), "name": name, "x": x + (i % 2), "y": y + (i // 2), "z": p.get("z", 0),
                            "stock": stock, "buys": buys, "type": p.get("type", "")})
        return out

    # ---- tiles --------------------------------------------------------------------------------------------------------------------------------------

    def walkable(self, x, y):
        if x < 0 or y < 0:
            return False
        if (x, y) in self.tele_tiles:
            return True
        if x >= SURFACE_X:
            return bool(self.dwalk and self.dwalk.get(x, y))
        return True if self.walk is None else self.walk.get(x, y)

    def is_water(self, x, y):
        return bool(self.water and self.water.get(x, y))

    def in_town(self, x, y):
        for r in self.towns:
            for x1, y1, x2, y2 in r.get("rects", []):
                if x1 <= x <= x2 and y1 <= y <= y2:
                    return r["name"]
        return None

    def weapon(self, item_name):
        return self.weapons.get(norm(item_name))
