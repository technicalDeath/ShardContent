"""The simulated shard: creatures spawn, wander, aggro by sight and fight from their stats; players walk, fight, loot, bank, shop, gather, craft, tame and cast;
the journal lines the brains parse are emitted in the farm's wording (see docs/Bot-Farm-Simulator-Evidence.md for what is modelled and what is not).

The world advances in World.step(dt) (the scheduler calls it, at most one second at a time) and answers player actions at once (World.command). Everything
is deterministic for a seed. Distances are Chebyshev (tiles), as the client reports them.
"""
from __future__ import annotations

import heapq
import json
import math
import os
import random
import re
import time

from . import world_data as wd

HERE = os.path.dirname(os.path.abspath(__file__))
CELL = 16                                       # the spatial index's cell
VIEW = 18                                       # the client's world-file range
SIGHT = 8                                       # a monster's perception (10, minus the shard's monsterAggro.rangeReduction 2)
# the watcher's eight simulator gaps (2026-10-21, "What the simulator misses"; the owner: "do all the fixes then test")
FLEE_BELOW = 0.5                                # 1. a creature that does not attack on sight runs once under this share of its hit points (AI_Animal)
FLEE_CHANCE = 0.8
FLEE_SPEED = 0.2                                # seconds a tile: a rabbit outruns a walking player and keeps pace with a running one
FLEE_LOST = 14                                  # tiles from its attacker at which a fleeing creature is gone
POISON_LESSER = (4, 16, 0.075, 3.0, 2.25, 10)   # 2. the engine's Lesser poison (PoisonKinds.cs): min, max, share of current hits, delay, interval, ticks
CAST_RANGE = 11                                 # 3. a casting creature (AI_Mage) hits from this far: the wraith that did 46 from 11 tiles
CAST_DMG = (12, 26)
CAST_EVERY = (6.0, 10.0)
RESTOCK_S = 3600.0                              # 4. a vendor's list comes back to full once an hour (BaseVendor's restock), not an item at a time
HIT_STAMINA = 3                                 # 6. a hit takes at most 3 stamina (the shard's staminaRelief); running costs none unless overloaded
STAM_REGEN_S = 3.0
TIRED_SHARE = 0.1                               # under this share of stamina a player cannot run
CHASE_LOSE = 24                                 # a monster gives up a target this far away
MONSTER_CORPSE_S = 7 * 60
PLAYER_CORPSE_S = 10 * 60
GROUND_ITEM_S = 3600
BANK_SLOTS = 125
SKILL_DELAY = 10.0                              # "You must wait a few moments to use another skill."
STAMP = "[%H:%M:%S"

SKILL_NAMES = ["Alchemy", "Anatomy", "Animal Lore", "Animal Taming", "Archery", "Arms Lore", "Begging", "Blacksmithy", "Bowcraft/Fletching", "Camping", "Carpentry",
               "Cartography", "Cooking", "Detecting Hidden", "Discordance", "Evaluating Intelligence", "Fencing", "Fishing", "Forensic Evaluation", "Healing", "Herding",
               "Hiding", "Inscription", "Item Identification", "Lockpicking", "Lumberjacking", "Mace Fighting", "Magery", "Meditation", "Mining", "Musicianship",
               "Parrying", "Peacemaking", "Poisoning", "Provocation", "Remove Trap", "Resisting Spells", "Snooping", "Spirit Speak", "Stealing", "Stealth",
               "Swordsmanship", "Tactics", "Tailoring", "Taste Identification", "Tinkering", "Tracking", "Veterinary", "Wrestling"]
WEAPON_SKILLS = {"Archery", "Fencing", "Mace Fighting", "Swordsmanship", "Wrestling"}
LAYERS = {"helm": "Helmet", "cap": "Helmet", "coif": "Helmet", "hat": "Helmet", "bandana": "Helmet", "tunic": "Torso", "chest": "Torso", "armor": "Torso", "leggings": "Pants",
          "pants": "Pants", "skirt": "Pants", "kilt": "Pants", "gloves": "Gloves", "sleeves": "Arms", "arms": "Arms", "gorget": "Neck", "boots": "Shoes", "shoes": "Shoes",
          "sandals": "Shoes", "shield": "TwoHanded", "buckler": "TwoHanded", "robe": "Robe", "cloak": "Cloak", "shirt": "Shirt", "doublet": "Shirt", "apron": "Waist", "sash": "Waist"}
ARMOR = {"leather": 2, "studded": 3, "ring": 4, "chain": 5, "plate": 6, "bone": 4, "shield": 3, "buckler": 2}
WEIGHT = [("gold coin", 0.02), ("ore", 1.0), ("ingot", 0.1), ("log", 2.0), ("board", 2.0), ("hides", 5.0), ("leather", 1.0), ("cloth", 0.1), ("fish steak", 0.1), ("fish", 1.0),
          ("raw ", 1.0), ("arrow", 0.1), ("bolt", 0.1), ("bandage", 0.1), ("potion", 1.0), ("scroll", 0.5), ("feather", 0.1), ("shaft", 0.1), ("kindling", 0.5), ("bow", 6.0),
          ("sword", 6.0), ("mace", 10.0), ("axe", 6.0), ("kryss", 2.0), ("katana", 6.0), ("club", 9.0), ("spear", 7.0), ("dagger", 1.0), ("shield", 6.0), ("tunic", 5.0),
          ("leggings", 4.0), ("gloves", 1.0), ("sleeves", 2.0), ("gorget", 1.0), ("helm", 3.0), ("coif", 1.0), ("cap", 1.0), ("pickaxe", 11.0), ("shovel", 5.0), ("hatchet", 4.0),
          ("tongs", 2.0), ("saw", 2.0), ("hammer", 8.0), ("kit", 2.0), ("tool", 1.0), ("book", 1.0), ("chair", 20.0), ("crate", 2.0), ("box", 2.0), ("table", 20.0),
          ("bench", 10.0), ("stool", 10.0), ("pole", 5.0)]
SPELL_DAMAGE = {"magic arrow": (4, 7), "harm": (1, 15), "fireball": (10, 16), "lightning": (12, 20), "mind blast": (12, 24), "energy bolt": (24, 41), "explosion": (23, 44),
                "flamestrike": (27, 48), "poison": (0, 0), "chain lightning": (23, 44), "meteor swarm": (23, 44), "earthquake": (20, 40)}
SPELL_HEAL = {"heal": (1, 10), "greater heal": (20, 40)}
REAGENT_NAMES = {"BlackPearl": "black pearl", "Bloodmoss": "blood moss", "Garlic": "garlic", "Ginseng": "ginseng", "MandrakeRoot": "mandrake root", "Nightshade": "nightshade",
                 "SpidersSilk": "spider's silk", "SulfurousAsh": "sulfurous ash"}
MEAT_NAMES = {"Ribs": "cut of raw ribs", "LambLeg": "raw leg of lamb", "Bird": "raw bird", "ChickenLeg": "raw chicken leg"}
RESOURCE_WORDS = {"IronIngot": ("iron ingot", "ingots"), "Cloth": ("cloth", "cloth"), "Board": ("board", "boards"), "Leather": ("leather", "leather"), "Log": ("log", "logs")}
DIRS = {"n": (0, -1), "s": (0, 1), "e": (1, 0), "w": (-1, 0), "ne": (1, -1), "nw": (-1, -1), "se": (1, 1), "sw": (-1, 1), "north": (0, -1), "south": (0, 1), "east": (1, 0),
        "west": (-1, 0), "northeast": (1, -1), "northwest": (-1, -1), "southeast": (1, 1), "southwest": (-1, 1)}


def cheb(ax, ay, bx, by):
    return max(abs(ax - bx), abs(ay - by))


def mid(rng, default=50.0):
    if not rng:
        return default
    try:
        return (float(rng[0]) + float(rng[1])) / 2
    except (TypeError, IndexError):
        return default


_UNIT_W = {}


def unit_weight(name):
    w = _UNIT_W.get(name)
    if w is None:
        n = (name or "").lower()
        w = _UNIT_W[name] = next((w for word, w in WEIGHT if word in n), 1.0)
    return w


def item_weight(it):
    return unit_weight(it.get("name") or "") * (it.get("amount") or 1)


class Entity:
    __slots__ = ("serial", "name", "x", "y", "z")

    def __init__(self, serial, name, x, y, z=0):
        self.serial, self.name, self.x, self.y, self.z = serial, name, x, y, z


class Creature(Entity):
    __slots__ = ("kind", "hp", "max_hp", "home", "home_range", "spawner", "target", "aggressive", "next_swing", "skill", "dmg", "armor", "species", "graphic",
                 "wander_at", "speed", "dead", "pet_of", "casts", "ai", "tamed", "karma", "last_hit_by", "fleeing", "next_cast", "passive", "hit_once")

    def __init__(self, serial, kind, data, x, y, spawner=None, home=None):
        c = data.creature(kind) or {}
        super().__init__(serial, data.display_name(kind), x, y, 0)
        self.kind = kind
        self.max_hp = max(1, int(mid(c.get("hits"), 20)))
        self.hp = self.max_hp
        self.home = home or (x, y)
        self.home_range = spawner["home"] if spawner else 10
        self.spawner = spawner
        self.target = None
        self.aggressive = data.aggressive(kind)
        self.next_swing = 0.0
        self.skill = mid(c.get("wrestling"), 30.0)
        d = c.get("damage") or [1, 2]
        self.dmg = (float(d[0]), float(d[1]))
        self.armor = float(c.get("armor") or 0)
        self.species = data.species(kind)
        self.graphic = 0
        self.wander_at = 0.0
        dex = mid(c.get("dex"), 50.0)
        self.speed = 0.2 if dex >= 75 else 0.3 if dex >= 45 else 0.4       # 6. seconds a tile in a chase, from dexterity (the creature tables carry no speed): orcs and wraiths
        self.passive = self.speed * 2                                       #    keep pace with a running player, snakes and zombies do not
        self.fleeing = None
        self.hit_once = False
        self.next_cast = 0.0
        self.dead = False
        self.pet_of = None
        self.casts = bool(c.get("casts"))
        self.ai = c.get("ai") or ""
        self.tamed = False
        self.karma = c.get("karma") or 0
        self.last_hit_by = None


class Corpse(Entity):
    __slots__ = ("items", "decay_at", "kind", "killer", "born", "carved", "owner")

    def __init__(self, serial, name, x, y, items, decay_at, kind=None, killer=None, born=0.0, owner=None):
        super().__init__(serial, name, x, y, 0)
        self.items, self.decay_at, self.kind, self.killer, self.born, self.carved, self.owner = items, decay_at, kind, killer, born, False, owner


class Vendor(Entity):
    __slots__ = ("role", "roles", "stock", "buys", "kind", "serials", "bought", "restock_at")

    def __init__(self, serial, p):
        super().__init__(serial, p["name"], p["x"], p["y"], p.get("z", 0))
        self.role, self.roles, self.kind = p["role"], p.get("roles", []), p["kind"]
        self.stock = [{"name": n, "price": pr, "qty": q, "max": q} for n, pr, q in p.get("stock", [])]
        self.buys = dict(p.get("buys", {}))
        self.serials = {}
        self.bought = {}                      # kind -> [hour, bought this hour]
        self.restock_at = None


class Player:
    """A simulated character; `state` is the dict the FakeClient serves as cuostate.json."""

    def __init__(self, world, rec, serial):
        self.gate_at = None
        self.world = world
        self.name = rec["name"]
        self.serial = serial
        self.profession = rec.get("profession")
        skills = {k: 0.0 for k in SKILL_NAMES}
        skills.update({k: float(v) for k, v in (rec.get("skills") or {}).items()})
        self.skills = skills
        pos = rec.get("pos") or list(world.data.centre)
        self.x, self.y, self.z = int(pos[0]), int(pos[1]), 0
        if not world.data.walkable(self.x, self.y):
            self.x, self.y = world.data.centre
        self.str_, self.dex, self.int_ = int(rec.get("str") or 60), int(rec.get("dex") or 50), int(rec.get("int") or 50)
        self.max_hp = int(rec.get("max_hp") or 60)
        self.hp = self.max_hp
        self.max_mana, self.max_stam = int(rec.get("max_mana") or 50), int(rec.get("max_stam") or 50)
        self.mana, self.stam = self.max_mana, self.max_stam
        self.max_weight = int(rec.get("max_weight") or 300)
        self.backpack_serial = world.new_item_serial()
        self.bank_serial = world.new_item_serial()
        self.backpack = []
        for it in rec.get("backpack") or []:
            self.add_item(dict(it, newbied=True), quiet=True)
        self.equipped = [dict(it, serial=world.new_item_serial(), newbied=True) for it in rec.get("equipped") or [] if it.get("layer") not in ("Backpack", "Bank")]
        self.bank = []
        self.ghost = False
        self.war = False
        self.between_until = 0.0                # Between Worlds (the shard's materializing flag): after a resurrection monsters cannot see the character until an action or ten minutes
        self.party = None                       # the leader's serial of the party it is in (world.parties)
        self.party_invite = None                # the serial of a player whose invitation waits
        self.target = None                      # the serial of the creature it is attacking
        self.cursor = None                      # (kind, payload) an open target cursor
        self.walk = None                        # {"tx", "ty", "near", "speed", "exact", "started"}
        self.nav = {"active": False, "status": "idle", "target": None, "reason": None}
        self.runmode = "auto"
        self.next_swing = 0.0
        self.next_skill = 0.0
        self.task = None                        # a server-side repeat: mining, chopping, fishing, bandaging, meditating, taming, cooking
        self.gumps = []                         # [(local, server, kind, lines)]
        self.menus = []                         # open legacy menus (crafting)
        self.last_shop = None                   # (vendor, "buy"|"sell", lines)
        self.bank_open = False
        self.opened = set()                     # corpses opened (serials)
        self.res_offered_at = None
        self.res_declined_near = None
        self.poisoned = False
        self.hidden = False
        self.meditating = False
        self.mastery_at = {"_start": world.now()}        # skill -> when its last Mastery allowance was paid
        self.journal = []                       # lines pending for the FakeClient's tail
        self.journal_all = 0
        self.kills = 0
        self.deaths = 0
        self.died_at = 0.0
        self.spoke = []
        self.criminal_until = 0.0
        self.pets = []
        self.mode = rec.get("mode", "veteran")
        self.walked = 0.0
        self.state = {}
        self.state_version, self.state_at = -1, -1.0
        self.cuolog = None                      # a file the journal is also written to (the client's log, for loopguard.guard_client)
        self.view_version = -1
        self.view = {"updatedAtMs": 0, "heartbeatAtMs": 0, "inGame": True, "range": VIEW, "mobiles": [], "items": [], "containers": []}
        self.refresh()

    # ---- items ----------------------------------------------------------------------------------------------------------------------------------

    def gold(self):
        return sum(i.get("amount") or 1 for i in self.backpack if (i.get("name") or "").lower() == "gold coin")

    def weight(self):
        return int(sum(item_weight(i) for i in self.backpack) + sum(item_weight(i) for i in self.equipped))

    def find(self, word, exact=False):
        w = word.lower()
        for i in self.backpack:
            n = (i.get("name") or "").lower()
            if (n == w) if exact else (w in n):
                return i
        return None

    def count(self, word):
        return sum((i.get("amount") or 1) for i in self.backpack if word in (i.get("name") or "").lower())

    def add_item(self, it, quiet=False):
        """Into the backpack, stacking by name for stackables; returns the item dict in the pack."""
        it = dict(it)
        it.setdefault("amount", 1)
        it.setdefault("graphic", 0)
        it.setdefault("hue", 0)
        name = it.get("name") or "item"
        if self.world.stackable(name):
            for i in self.backpack:
                if (i.get("name") or "") == name and i.get("hue", 0) == it.get("hue", 0):
                    i["amount"] = (i.get("amount") or 1) + (it.get("amount") or 1)
                    if not quiet:
                        self.say_line(f"[CONTAINER] +{it['amount']} 0x{it.get('graphic', 0):04X} ({i['serial']})")
                    return i
        if not it.get("serial"):
            it["serial"] = self.world.new_item_serial()
        self.backpack.append(it)
        if not quiet:
            self.say_line(f"[CONTAINER] +{it['amount']} 0x{it.get('graphic', 0):04X} ({it['serial']})")
        return it

    def take(self, name, amount):
        """Remove `amount` of a stackable by name (case-insensitive); returns what was removed."""
        left = amount
        for i in list(self.backpack):
            if (i.get("name") or "").lower() == name.lower():
                n = i.get("amount") or 1
                if n <= left:
                    self.backpack.remove(i)
                    left -= n
                else:
                    i["amount"] = n - left
                    left = 0
            if left <= 0:
                break
        return amount - left

    def add_gold(self, n):
        if n > 0:
            self.add_item({"name": "gold coin", "amount": int(n), "graphic": 0x0EED}, quiet=True)
        elif n < 0:
            self.take("gold coin", -int(n))

    def item(self, serial):
        for i in self.backpack:
            if i.get("serial") == serial:
                return i
        return None

    def worn(self, serial):
        for i in self.equipped:
            if i.get("serial") == serial:
                return i
        return None

    def weapon(self):
        for i in self.equipped:
            w = self.world.data.weapon(i.get("name", ""))
            if w and i.get("layer") in ("OneHanded", "TwoHanded"):
                return i, w
        return None, None

    def armor_rating(self):
        ar = 0
        for i in self.equipped:
            n = (i.get("name") or "").lower()
            ar += next((v for k, v in ARMOR.items() if k in n), 0)
        return ar

    def skill(self, name):
        return self.skills.get(name, 0.0)

    # ---- the journal ------------------------------------------------------------------------------------------------------------------------------

    LATENCY = 0.001                         # a reply reaches the client's log a moment after the command (1-30 ms live): a wait that drains first still sees it

    def say_line(self, text):
        self.journal.append((self.world.now() + self.LATENCY, text))
        self.journal_all += 1

    def system(self, text):
        self.say_line(f"[SYSTEM] {text}")

    def overhead(self, text):
        """The server's overhead message to the character itself: speech under its own name."""
        self.say_line(f"[SAY] {self.name}: {text}")

    # ---- state ----------------------------------------------------------------------------------------------------------------------------------

    def refresh(self):
        now_ms = int(self.world.now() * 1000)
        s = self.state
        s.update(updatedAtMs=now_ms, heartbeatAtMs=now_ms, connected=True, inGame=True, charID=self.serial, charName=self.name, charPosX=self.x, charPosY=self.y, charPosZ=self.z,
                 map=0, charGhost=self.ghost, isHidden=self.hidden, isPoisoned=self.poisoned, isParalyzed=False, isMounted=False, isHuman=True, warMode=self.war,
                 notoriety="Criminal" if self.world.now() < self.criminal_until else "Innocent", hits=self.hp, maxHits=self.max_hp, stamina=self.stam, maxStam=self.max_stam,
                 mana=self.mana, maxMana=self.max_mana, str=self.str_, dex=self.dex, int=self.int_, weight=self.weight(), maxWeight=self.max_weight, gold=self.gold(),
                 followers=len(self.pets), maxFollowers=5, backpackID=self.backpack_serial, equipped=[{"serial": self.backpack_serial, "name": "backpack", "graphic": 3701, "amount": 1, "hue": 0, "layer": "Backpack"}] + self.equipped,
                 backpackOpened=True, backpack=self.backpack, bankOpened=self.bank_open, bank=self.bank if self.bank_open else [],
                 lastCursorTarget={"kind": "none"}, lastAttack=self.world.target_record(self), nav=self.nav)


class World:
    def __init__(self, data: wd.WorldData, seed=1, now=None, walk_tps=2.6, run_tps=4.6):
        self.data = data
        self.rng = random.Random(seed)
        self._now = float(now if now is not None else time.time())
        self.walk_tps, self.run_tps = walk_tps, run_tps
        self.version = 0
        self._serial = 0x00010000
        self._iserial = 0x40000000
        self.players = {}
        self.creatures = {}
        self.corpses = {}
        self.moongates = [p for p in getattr(data, "gazetteer", {}).get("places", []) if p.get("role") == "moongate" and int(p.get("x", 99999)) < 5120]   # the public moongates (gazetteer, PublicMoongate): a gump on the gate, the response moves the bot to the chosen gate
        self.teleporters = dict(getattr(data, "transitions", {}) or {})          # (x, y) of an entry -> (x, y, src_side, dst_side): standing on it moves the bot to the exit (item 5)
        self.parties = {}                                                        # leader serial -> {"members": [serials], "loot": bool}
        self.ground = {}                          # movable items on the ground: serial -> dict with x, y
        self.vendors = {}
        self.fixtures = []
        self.cells = {}                           # (cx, cy) -> set of creature serials
        self.respawn = []                         # heap of (t, spawner index, kind)
        self.banks = {}                           # 8x8 cell -> ore / wood / fish left
        self.stats = {"kills": 0, "deaths": 0, "spawned": 0, "swings": 0, "crafts": 0, "gathers": 0, "sales": 0, "buys": 0, "casts": 0, "tames": 0}
        self.events = []                          # (t, kind, bot, detail) for the scoreboard
        self._open8 = {}                          # 8x8 cell -> walkable tiles in it (the route grid)
        self._routes = {}                         # (from cell, to cell) -> waypoints or None (no land route)
        self._stackable = {"gold coin", "iron ingot", "iron ore", "log", "board", "cut cloth", "folded cloth", "arrow", "bolt", "bandage", "feather", "shaft", "kindling", "fish",
                           "fish steak", "raw fish steak", "cut of raw ribs", "raw leg of lamb", "raw bird", "raw chicken leg", "pile of hides", "leather", "blank scroll", "nails"}
        self._place_vendors()
        self._spawn_all()
        self.kill_log = []

    # ---- time and serials --------------------------------------------------------------------------------------------------------------------------

    def now(self):
        return self._now

    def stamp(self):
        t = time.localtime(self._now)
        return time.strftime(STAMP, t) + f".{int((self._now % 1) * 1000):03d}] "

    def new_serial(self):
        self._serial += 1
        return f"0x{self._serial:08X}"

    def new_item_serial(self):
        self._iserial += 1
        return f"0x{self._iserial:08X}"

    def stackable(self, name):
        n = name.lower()
        return n in self._stackable or any(w in n for w in ("ingot", "ore", "reagent", "pearl", "moss", "garlic", "ginseng", "mandrake", "nightshade", "silk", "ash", "hides"))

    # ---- the index --------------------------------------------------------------------------------------------------------------------------------

    def _cell(self, x, y):
        return (x // CELL, y // CELL)

    def _index(self, c):
        self.cells.setdefault(self._cell(c.x, c.y), set()).add(c.serial)

    def _unindex(self, c):
        s = self.cells.get(self._cell(c.x, c.y))
        if s:
            s.discard(c.serial)

    def _move_creature(self, c, x, y):
        a, b = self._cell(c.x, c.y), self._cell(x, y)
        if a != b:
            self._unindex(c)
            c.x, c.y = x, y
            self._index(c)
        else:
            c.x, c.y = x, y
        self.version += 1

    def creatures_near(self, x, y, r):
        out = []
        cx, cy = self._cell(x, y)
        n = r // CELL + 1
        for i in range(cx - n, cx + n + 1):
            for j in range(cy - n, cy + n + 1):
                for s in self.cells.get((i, j), ()):
                    c = self.creatures.get(s)
                    if c is not None and cheb(c.x, c.y, x, y) <= r:
                        out.append(c)
        return out

    # ---- building ---------------------------------------------------------------------------------------------------------------------------------

    def _place_vendors(self):
        for p in self.data.places:
            if p["kind"] == "fixture":
                self.fixtures.append({"serial": self.new_item_serial(), "name": p["name"], "graphic": p.get("graphic", 0), "x": p["x"], "y": p["y"], "z": p.get("z", 0), "fixed": True})
            else:
                v = Vendor(self.new_serial(), p)
                self.vendors[v.serial] = v

    def _spawn_all(self):
        for i, s in enumerate(self.data.spawners):
            for _ in range(s["count"]):
                self._spawn_one(i)

    def _spawn_one(self, i):
        s = self.data.spawners[i]
        kinds = [k for k, n in s["entries"] for _ in range(n)]
        kind = self.rng.choice(kinds)
        for _ in range(12):
            x = s["x"] + self.rng.randint(-s["home"], s["home"])
            y = s["y"] + self.rng.randint(-s["home"], s["home"])
            if self.data.walkable(x, y):
                break
        else:
            x, y = s["x"], s["y"]
        c = Creature(self.new_serial(), kind, self.data, x, y, spawner=s, home=(s["x"], s["y"]))
        self.creatures[c.serial] = c
        self._index(c)
        self.stats["spawned"] += 1
        self.version += 1
        return c

    def add_player(self, rec):
        p = Player(self, rec, self.new_serial())
        self.players[p.serial] = p
        self.version += 1
        return p

    # ---- views --------------------------------------------------------------------------------------------------------------------------------------

    def target_record(self, p):
        if not p.target:
            return {"kind": "none"}
        c = self.creatures.get(p.target)
        if c is None:
            return {"kind": "mobile", "serial": p.target, "exists": False, "source": "attack"}
        return {"kind": "mobile", "serial": c.serial, "exists": cheb(c.x, c.y, p.x, p.y) <= VIEW, "name": c.name, "x": c.x, "y": c.y, "z": c.z, "hits": c.hp, "maxHits": c.max_hp,
                "graphic": c.graphic, "species": c.species, "source": "attack"}

    def build_view(self, p):
        """The world file: mobiles, movable items and containers within VIEW tiles, nearest first."""
        p.view_at = self._now
        mobs = []
        for c in self.creatures_near(p.x, p.y, VIEW):
            d = cheb(c.x, c.y, p.x, p.y)
            noto = "Innocent" if c.tamed else "Gray"
            mobs.append({"serial": c.serial, "name": c.name, "graphic": c.graphic, "species": c.species, "x": c.x, "y": c.y, "z": c.z, "distance": d, "notoriety": noto,
                         "knownMonster": c.aggressive or c.karma < 0, "hits": c.hp, "maxHits": c.max_hp, "isDead": c.dead, "isHuman": False, "inWarMode": c.target is not None,
                         "isPet": c.tamed})
        for v in self.vendors.values():
            d = cheb(v.x, v.y, p.x, p.y)
            if d <= VIEW:
                mobs.append({"serial": v.serial, "name": v.name, "graphic": 400, "species": "Human (Male)", "x": v.x, "y": v.y, "z": v.z, "distance": d, "notoriety": "Innocent",
                             "knownMonster": False, "hits": 100, "maxHits": 100, "isDead": False, "isHuman": True, "inWarMode": False, "isPet": False})
        for o in self.players.values():
            if o is p:
                continue
            d = cheb(o.x, o.y, p.x, p.y)
            if d <= VIEW and (not o.ghost or p.war or p.ghost):
                noto = "Criminal" if self.now() < o.criminal_until else "Innocent"
                mobs.append({"serial": o.serial, "name": o.name, "graphic": 402 if o.ghost else 400, "species": "Human (Male)", "x": o.x, "y": o.y, "z": o.z, "distance": d, "notoriety": noto,
                             "knownMonster": False, "hits": o.hp, "maxHits": o.max_hp, "isDead": o.ghost, "isHuman": True, "inWarMode": o.war, "isPet": False})
        mobs.sort(key=lambda m: m["distance"])
        items = []
        for it in self.ground.values():
            d = cheb(it["x"], it["y"], p.x, p.y)
            if d <= VIEW:
                items.append({"serial": it["serial"], "name": it["name"], "graphic": it.get("graphic", 0), "amount": it.get("amount", 1), "hue": 0, "x": it["x"], "y": it["y"], "z": 0, "distance": d})
        items.sort(key=lambda i: i["distance"])
        conts = []
        for c in self.corpses.values():
            d = cheb(c.x, c.y, p.x, p.y)
            if d <= VIEW:
                conts.append({"serial": c.serial, "name": c.name, "graphic": 0x2006, "x": c.x, "y": c.y, "z": 0, "distance": d, "isCorpse": True, "isContainer": True})
        conts.sort(key=lambda i: i["distance"])
        p.view.update(updatedAtMs=int(self._now * 1000), heartbeatAtMs=int(self._now * 1000), mobiles=mobs, items=items, containers=conts)
        p.view_version = self.version
        return p.view

    def mobile(self, serial):
        return self.creatures.get(serial) or self.vendors.get(serial) or self.players.get(serial)

    # ---- the clock's step ---------------------------------------------------------------------------------------------------------------------------

    STEP = 0.5                                      # the world's own tick: creatures, fights, regeneration and walks advance this often at most

    def step(self, dt):
        self._now += dt
        self._acc = getattr(self, "_acc", 0.0) + dt
        if self._acc < self.STEP:
            return
        dt, self._acc = self._acc, 0.0
        now = self._now
        for p in self.players.values():
            self._step_player(p, dt)
        self._step_creatures(dt)
        while self.respawn and self.respawn[0][0] <= now:
            _, i, _ = heapq.heappop(self.respawn)
            self._spawn_one(i)
        if int(now) % 5 == 0 and int(now) != int(now - dt):
            for s, c in list(self.corpses.items()):
                if c.decay_at <= now:
                    del self.corpses[s]
                    self.version += 1
            for s, it in list(self.ground.items()):
                if it.get("decay_at", now + 1) <= now:
                    del self.ground[s]
                    self.version += 1
            for v in self.vendors.values():
                at = getattr(v, "restock_at", None)
                if at is None:
                    v.restock_at = now + self.rng.uniform(0, RESTOCK_S)          # vendors restock on their own hour, not all at once
                elif now >= at:
                    v.restock_at = now + RESTOCK_S                              # 4. the whole list back to full once an hour
                    for st in v.stock:
                        st["qty"] = st["max"]
            for k in list(self.banks):
                if self.banks[k] < 12 and self.rng.random() < 0.08:
                    self.banks[k] += 1

    def _step_player(self, p, dt):
        now = self._now
        if p.ghost:
            self._step_walk(p, dt)
            if p.res_declined_near is not None and self._vendor_near(p, 7, role="healer") is None:
                p.res_declined_near = None             # a ghost that declined and walked off is offered again when it comes back into range (as the server does)
            return
        # regeneration: a hit point every 11 s, stamina every 7 s, mana every 7 s (three times as fast in a meditative trance)
        p.hp = min(p.max_hp, p.hp + (1 if self.rng.random() < dt / 11 else 0))
        p.stam = min(p.max_stam, p.stam + (1 if self.rng.random() < dt / STAM_REGEN_S else 0))      # 6. regenerates walking too
        rate = dt / 7 * (3 if p.meditating else 1) * (1 + p.skill("Meditation") / 100)
        p.mana = min(p.max_mana, p.mana + (1 if self.rng.random() < rate else 0))
        if p.poisoned:
            mn, mx, share, delay, every, ticks = POISON_LESSER          # 2. the engine's Lesser poison: a tick of 4 to 16 every 2.25 s, ten of them
            if not getattr(p, "poison_next", 0):
                p.poison_next, p.poison_left = now + delay, ticks
            if now >= p.poison_next:
                p.poison_next = now + every
                p.poison_left -= 1
                self.hurt(p, int(max(mn, min(mx, p.hp * share))), "poison")
                if p.poison_left <= 0:
                    p.poisoned = False
        if not p.poisoned:
            p.poison_next = 0
        self._step_walk(p, dt)
        self._step_task(p)
        if p.target and p.war:
            self._player_swing(p)

    def _step_walk(self, p, dt):
        w = p.walk
        if not w:
            return
        running = (p.runmode == "always" or p.runmode == "auto") and p.stam >= p.max_stam * TIRED_SHARE       # 6. too tired to run under a tenth of stamina
        tps = (self.run_tps if running else self.walk_tps) * (0.5 if p.weight() > p.max_weight else 1.0)
        if p.ghost:
            tps = self.run_tps
        move = tps * dt * w.get("factor", 1.0)
        while move > 0 and p.walk is w:
            lx, ly = w["path"][0]
            fx, fy = w["fx"], w["fy"]
            dist = max(abs(lx - fx), abs(ly - fy))
            last = len(w["path"]) == 1
            if move >= dist or (last and dist <= w["near"]):
                w["fx"], w["fy"] = float(lx), float(ly)
                move -= dist
                if last:
                    p.x, p.y = w["tx"], w["ty"]
                    p.walk = None
                    p.nav.update(active=False, status="arrived", reason=None)
                    self._gate_check(p)
                    p.say_line(f"[NAV] goto {w['tx']} {w['ty']} -> arrived plans=1 nodes=1 planMs=1 maxPlanMs=1")
                    self._tele_check(p)
                    break
                w["path"].pop(0)
                continue
            frac = move / dist
            w["fx"] = fx + (lx - fx) * frac
            w["fy"] = fy + (ly - fy) * frac
            p.x, p.y = int(round(w["fx"])), int(round(w["fy"]))
            move = 0
        if running and p.weight() > p.max_weight and self.rng.random() < tps * dt / 4:
            p.stam = max(0, p.stam - 1)                             # 6. running costs stamina only when overloaded
        p.walked += tps * dt
        if p.task and p.task["kind"] in ("mine", "chop", "fish", "craft_repeat"):
            p.task = None
        p.meditating = False
        self.version += 1

    def _step_task(self, p):
        t = p.task
        if not t or t["at"] > self._now:
            return
        kind = t["kind"]
        if kind == "bandage":
            who = self.players.get(p.task.get("who")) or p            # a party member bandaged (item 5's shared tour), else the bot itself
            p.task = None
            healing = p.skill("Healing")
            if who.hp >= who.max_hp:
                p.system("That being is not damaged.")
                return
            if self.rng.random() < 0.6 - healing / 150:
                who.hp = min(who.max_hp, who.hp + 1)
                p.system("You apply the bandages, but they barely help.")
            else:
                heal = int(healing / 5 + p.skill("Anatomy") / 8 + self.rng.randint(1, 6))
                who.hp = min(who.max_hp, who.hp + heal)
                p.system("You finish applying the bandages.")
            if who.poisoned and healing >= 60 and self.rng.random() < 0.5:
                who.poisoned = False
                p.system("You have been cured of all poisons.")
            self.gain(p, "Healing", 0.5)
            self.gain(p, "Anatomy", 0.3)
        elif kind == "mine":
            self._harvest(p, t, "ore")
        elif kind == "chop":
            self._harvest(p, t, "wood")
        elif kind == "fish":
            self._harvest(p, t, "fish")
        elif kind == "tame":
            p.task = None
            c = self.creatures.get(t["serial"])
            if c is None or cheb(c.x, c.y, p.x, p.y) > 3:
                p.system("You are too far away to continue taming.")
                return
            lo = t["min"]
            # AnimalTaming.cs: minSkill = MinTameSkill + 24.9, the check runs from minSkill - 25 to minSkill + 25: chance = (skill - MinTameSkill + 0.1) / 50
            chance = max(0.0, min(1.0, (p.skill("Animal Taming") - lo + 0.1) / 50))
            self.gain(p, "Animal Taming", 0.6 if 0 < chance < 1 else 0.05)
            t["tries"] = t.get("tries", 0) + 1
            if self.rng.random() >= chance and t["tries"] < 4 and self.rng.random() < 0.7:
                p.system("You seem to anger the beast!" if self.rng.random() < 0.5 else "The animal remains wild.")
                if self.rng.random() < 0.5:
                    self._creature_step_toward(c, c.x + self.rng.randint(-6, 6), c.y + self.rng.randint(-6, 6), 2.0)     # it runs; the tamer follows and tries again
                p.task = dict(t, at=self._now + 9.0)
                return
            if self.rng.random() < chance:
                c.tamed, c.target, c.aggressive = True, None, False
                c.pet_of = p.serial
                p.pets.append(c.serial)
                p.system("It seems to accept you as master.")
                self.stats["tames"] += 1
                self.events.append((self._now, "tame", p.name, c.kind))
            else:
                p.system("You fail to tame the creature.")
                if not c.tamed and self.rng.random() < 0.3 and c.karma < 0:
                    c.target = p.serial
        elif kind == "cook":
            p.task = None
            n = p.take("raw fish steak", 1)
            if n:
                if self.rng.random() < 0.3 + p.skill("Cooking") / 150:
                    p.add_item({"name": "fish steak", "amount": 1, "graphic": 0x097B})
                    p.system("You cook the food.")
                else:
                    p.system("You burn the food to a crisp! It's ruined.")
                self.gain(p, "Cooking", 0.5)

    def _harvest(self, p, t, what):
        key = f"{t['x'] // 8 * 8},{t['y'] // 8 * 8}:{what}"
        left = self.banks.setdefault(key, 12)
        if p.weight() > p.max_weight * 0.95:
            p.task = None
            p.system("You are too fatigued to move, because you are carrying too much weight!")
            return
        if left <= 0:
            p.task = None
            p.system({"ore": "There is no metal here to mine.", "wood": "There's not enough wood here to harvest.", "fish": "The fish don't seem to be biting here."}[what])
            return
        skill_name = {"ore": "Mining", "wood": "Lumberjacking", "fish": "Fishing"}[what]
        sk = p.skill(skill_name)
        if self.rng.random() < 0.45 + sk / 200:
            self.banks[key] = left - 1
            if what == "ore":
                ore = "iron ore" if sk < 65 or self.rng.random() < 0.7 else self.rng.choice(("dull copper ore", "shadow iron ore", "bronze ore"))
                p.add_item({"name": ore, "amount": 1, "graphic": 0x19B9})
                p.system(f"You dig some {ore} and put it in your backpack.")
            elif what == "wood":
                p.add_item({"name": "log", "amount": 1 + self.rng.randint(0, 4), "graphic": 0x1BDD})
                p.system("You put some logs into your backpack.")
            else:
                p.add_item({"name": "fish", "amount": 1, "graphic": 0x09CC})
                p.system("You pull out an item : fish")
            self.stats["gathers"] += 1
            self.events.append((self._now, "gather", p.name, what))
        else:
            p.system({"ore": "You loosen some rocks but fail to find any useable ore.", "wood": "You hack at the tree for a while, but fail to produce any useable wood.",
                      "fish": "You fish a while, but fail to catch anything."}[what])
        self.gain(p, skill_name, 0.5)
        t["at"] = self._now + (2.5 if what != "fish" else 8.0)

    # ---- creatures ----------------------------------------------------------------------------------------------------------------------------------

    def _step_creatures(self, dt):
        now = self._now
        active = {}
        for p in self.players.values():
            for c in self.creatures_near(p.x, p.y, 26):
                active[c.serial] = c
        for c in active.values():
            if c.fleeing is not None:
                f = self.players.get(c.fleeing)
                if f is None or f.ghost or cheb(f.x, f.y, c.x, c.y) > FLEE_LOST:
                    self._creature_gone(c)                         # it got away: out of reach and out of the fight
                    continue
                self._creature_step_away(c, f.x, f.y, dt)
                continue
            if c.tamed:
                owner = self.players.get(c.pet_of)
                if owner and cheb(c.x, c.y, owner.x, owner.y) > 3:
                    self._creature_step_toward(c, owner.x, owner.y, dt)
                continue
            tgt = self.players.get(c.target) if c.target else None
            if tgt and (tgt.ghost or cheb(tgt.x, tgt.y, c.x, c.y) > CHASE_LOSE):
                c.target, tgt = None, None
            if tgt is None and c.aggressive:
                best = None
                for p in self.players.values():
                    if p.ghost or p.hidden or now < p.between_until:
                        continue
                    d = cheb(p.x, p.y, c.x, c.y)
                    if d <= SIGHT and (best is None or d < best[0]):
                        best = (d, p)
                if best:
                    tgt = best[1]
                    c.target = tgt.serial
                    tgt.overhead(f"{c.name} is attacking you!")
            if tgt is not None:
                d = cheb(tgt.x, tgt.y, c.x, c.y)
                if c.casts and 2 <= d <= CAST_RANGE and now >= c.next_cast:
                    c.next_cast = now + self.rng.uniform(*CAST_EVERY)          # 3. a spell from range
                    dmg = self.rng.randint(*CAST_DMG)
                    tgt.say_line(f"Spell: {c.name} -> {tgt.name}")
                    self.hurt(tgt, dmg, c)
                if d > 1:
                    self._creature_step_toward(c, tgt.x, tgt.y, dt)
                elif now >= c.next_swing:
                    self._creature_swing(c, tgt)
            elif now >= c.wander_at:
                c.wander_at = now + self.rng.uniform(4, 14)
                if cheb(c.x, c.y, c.home[0], c.home[1]) > c.home_range:
                    self._creature_step_toward(c, c.home[0], c.home[1], 1.0)
                else:
                    nx, ny = c.x + self.rng.randint(-2, 2), c.y + self.rng.randint(-2, 2)
                    if self.data.walkable(nx, ny):
                        self._move_creature(c, nx, ny)

    def _creature_gone(self, c):
        self._unindex(c)
        self.creatures.pop(c.serial, None)
        if c.spawner is not None:
            i = next((k for k, s in enumerate(self.data.spawners) if s is c.spawner), None)
            if i is not None:
                heapq.heappush(self.respawn, (self._now + self.rng.uniform(c.spawner["min_delay"], c.spawner["max_delay"]), i, c.kind))
        self.version += 1

    def _creature_step_away(self, c, x, y, dt):
        steps = max(1, int(dt / FLEE_SPEED + 0.5))
        for _ in range(steps):
            dx = (c.x > x) - (c.x < x) or self.rng.choice((-1, 1))
            dy = (c.y > y) - (c.y < y) or self.rng.choice((-1, 1))
            for nx, ny in ((c.x + dx, c.y + dy), (c.x + dx, c.y), (c.x, c.y + dy)):
                if self.data.walkable(nx, ny):
                    self._move_creature(c, nx, ny)
                    break
            else:
                break

    def _creature_step_toward(self, c, x, y, dt):
        steps = max(1, int(dt / c.speed + 0.5))
        for _ in range(steps):
            dx = (x > c.x) - (x < c.x)
            dy = (y > c.y) - (y < c.y)
            if dx == 0 and dy == 0:
                break
            nx, ny = c.x + dx, c.y + dy
            if not self.data.walkable(nx, ny):
                nx, ny = (c.x + dx, c.y) if self.data.walkable(c.x + dx, c.y) else (c.x, c.y + dy)
                if not self.data.walkable(nx, ny):
                    break
            self._move_creature(c, nx, ny)

    def _creature_swing(self, c, p):
        c.next_swing = self._now + self.rng.uniform(2.0, 3.2)
        wi, w = p.weapon()
        defend = p.skill(w["skill"]) if w else p.skill("Wrestling")
        chance = max(0.02, min(0.98, (c.skill + 50) / ((defend + 50) * 2)))
        self.stats["swings"] += 1
        if self.rng.random() >= chance:
            p.say_line(f"Swing: {c.name} -> {p.name}")
            return
        dmg = self.rng.uniform(c.dmg[0], c.dmg[1]) * max(0.3, 1 - p.armor_rating() / 120)
        dmg = max(1, int(round(dmg)))
        if c.casts and self.rng.random() < 0.25:
            dmg += self.rng.randint(5, 12)
        p.say_line(f"Swing: {c.name} -> {p.name}")
        self.hurt(p, dmg, c)
        if p.task and p.task["kind"] == "bandage":
            p.system("Your fingers slip!")
            p.task["at"] += 1.5
        self.gain(p, "Parrying", 0.1)
        if c.kind in ("giantspider", "giantserpent", "snake", "scorpion") and self.rng.random() < 0.25:
            p.poisoned = True
            p.overhead("*You feel a bit nauseous*")

    def hurt(self, p, dmg, source):
        if source != "poison" and not p.ghost:
            p.stam = max(0, p.stam - min(HIT_STAMINA, int(dmg)))        # 6. a hit takes stamina, at most 3 (staminaRelief)
        if p.ghost:
            return
        p.hp -= dmg
        p.say_line(f"Damage: {p.name} takes {dmg}")
        p.meditating = False
        if p.hp <= 0:
            self._player_dies(p, source)

    def _player_dies(self, p, source):
        p.hp = 0
        p.ghost = True
        p.war = False
        p.target = None
        p.task = None
        p.walk = None
        p.nav.update(active=False, status="stopped", reason="dead")
        p.deaths += 1
        p.died_at = self._now
        p.meditating = False
        self.stats["deaths"] += 1
        items = [i for i in p.backpack if not i.get("newbied")]
        p.backpack = [i for i in p.backpack if i.get("newbied")]
        corpse = Corpse(self.new_item_serial(), f"a corpse of {p.name}", p.x, p.y, items, self._now + PLAYER_CORPSE_S, kind=None, killer=None, born=self._now, owner=p.name)
        self.corpses[corpse.serial] = corpse
        for s in p.pets:
            c = self.creatures.get(s)
            if c:
                c.tamed, c.pet_of = False, None
        p.pets = []
        p.say_line("[DEATH] You have died.")
        p.system("Your corpse will turn to bones in 7 minutes and be gone 7 minutes after that.")
        killer = source.name if isinstance(source, Creature) else str(source)
        self.events.append((self._now, "death", p.name, killer))
        self.version += 1

    # ---- the player's fight ---------------------------------------------------------------------------------------------------------------------------

    def _player_swing(self, p):
        c = self.creatures.get(p.target)
        if c is None or c.dead:
            p.target = None
            return
        wi, w = p.weapon()
        ranged = bool(w and w.get("ammo"))
        d = cheb(c.x, c.y, p.x, p.y)
        if d > (10 if ranged else 1) or self._now < p.next_swing:
            return
        if ranged:
            ammo = "bolt" if "crossbow" in (wi.get("name") or "").lower() else "arrow"
            if not p.take(ammo, 1):
                return
        skill_name = w["skill"] if w else "Wrestling"
        speed = w["speed"] if w else 50
        p.next_swing = self._now + max(1.25, 15000 / ((p.dex + 100) * speed) / 1000 * 2.5)
        skill = p.skill(skill_name)
        chance = max(0.02, min(0.98, (skill + 50) / ((c.skill + 50) * 2)))
        self.stats["swings"] += 1
        p.say_line(f"Swing: {p.name} -> {c.name}")
        self.gain(p, skill_name, 0.4)
        self.gain(p, "Tactics", 0.25)
        if self.rng.random() >= chance:
            return
        if w:
            base = self.rng.uniform(w["min"], w["max"])
        else:
            base = self.rng.uniform(1, 4)
        dmg = base * (p.skill("Tactics") + 50) / 100 * (1 + (p.str_ - 50) / 300) * max(0.3, 1 - c.armor / 150)
        dmg = max(1, int(round(dmg)))
        self.gain(p, "Anatomy", 0.2)
        if c.target is None and not c.tamed:
            c.target = p.serial
        c.last_hit_by = p.serial
        self.damage_creature(c, dmg, p)

    def damage_creature(self, c, dmg, p):
        c.hp -= dmg
        if c.hp > 0 and c.fleeing is None and not c.tamed:
            pf = self.data.flee_first_hit.get(c.kind, 0.0)
            if pf and not getattr(c, "hit_once", False) and self.rng.random() < pf:
                c.fleeing = p.serial                              # the live hour: this kind escapes that share of its fights (rabbits 86%, rats 81%)
            c.hit_once = True
        if c.hp > 0 and not c.aggressive and not c.tamed and c.fleeing is None and c.hp < c.max_hp * FLEE_BELOW and self.rng.random() < FLEE_CHANCE:
            c.fleeing = p.serial                                   # 1. it runs (the live hour: rabbits escaped 48 of 64 fights, rats 4 of 4)
        for o in self.players.values():
            if cheb(o.x, o.y, c.x, c.y) <= VIEW:
                o.say_line(f"Damage: {c.name} takes {dmg}")
        if c.hp <= 0:
            self._creature_dies(c, p)
        self.version += 1

    def _creature_dies(self, c, killer):
        c.dead = True
        self._unindex(c)
        self.creatures.pop(c.serial, None)
        if killer is not None and killer.target == c.serial:
            killer.target = None
        lv = self.data.loot.get(c.kind) or {}
        items = []
        gold = float(lv.get("gold") or 0)
        if gold > 0:
            n = int(gold * self.rng.uniform(0.15, 0.5))              # loot_value's gold is the pack's ceiling, not its mean
            if n > 0:
                items.append({"serial": self.new_item_serial(), "name": "gold coin", "amount": n, "graphic": 0x0EED})
        if "potions" in (lv.get("extras") or []) and self.rng.random() < 0.3:
            items.append({"serial": self.new_item_serial(), "name": self.rng.choice(("Yellow Potion", "Red Potion", "Orange Potion")), "amount": 1, "graphic": 0x0F0C})
        if "magic" in (lv.get("extras") or []) and self.rng.random() < 0.08:
            items.append({"serial": self.new_item_serial(), "name": self.rng.choice(("katana", "kryss", "mace", "leather tunic", "ringmail tunic", "bow")), "amount": 1, "graphic": 0x13FF})
        corpse = Corpse(self.new_item_serial(), f"{c.name} corpse", c.x, c.y, items, self._now + MONSTER_CORPSE_S, kind=c.kind, killer=killer.serial if killer else None, born=self._now)
        self.corpses[corpse.serial] = corpse
        if killer is not None:
            killer.kills += 1
            self.events.append((self._now, "kill", killer.name, c.kind))
            if c.karma < 0:
                killer.system("You have gained a little fame.")
        self.stats["kills"] += 1
        if c.spawner is not None:
            i = self.data.spawners.index(c.spawner)
            heapq.heappush(self.respawn, (self._now + self.rng.uniform(c.spawner["min_delay"], c.spawner["max_delay"]), i, c.kind))
        if c.tamed:
            o = self.players.get(c.pet_of)
            if o and c.serial in o.pets:
                o.pets.remove(c.serial)
        self.version += 1

    # ---- skills -------------------------------------------------------------------------------------------------------------------------------------

    # Mastery (docs/Mastery-Layered-Evidence.md): from 80 a guaranteed gain of 2.0 / 1.4 / 1.0 / 0.8 points a day in the bands 80-90 / 90-95 / 95-99 / 99-100, on top of a
    # chance gain at a tenth of the class rate; under 80 the shard's curve, here as a chance per use falling from about a half at 0 to a tenth at 80
    MASTERY_DAILY = ((90, 2.0), (95, 1.4), (99, 1.0), (100.1, 0.8))

    def gain(self, p, skill, weight=1.0):
        """A chance of +0.1 in a skill after using it (the gain curve under 80), and the Mastery allowance above 80."""
        v = p.skills.get(skill, 0.0)
        if v >= 100.0:
            return False
        if v < 80:
            chance = weight * (0.5 - 0.4 * v / 80)
        else:
            daily = next(d for top, d in self.MASTERY_DAILY if v < top)
            last = p.mastery_at.get(skill, p.mastery_at.get("_start", self._now))
            if self._now - last >= 86400 / (daily / 0.1):
                p.mastery_at[skill] = self._now
                chance = 1.0
            else:
                chance = weight * 0.01
        if self.rng.random() < chance:
            p.skills[skill] = round(v + 0.1, 1)
            p.system(f"Your skill in {skill} has increased by 0.1.  It is now {p.skills[skill]:.1f}.")
            self.events.append((self._now, "gain", p.name, skill))
            return True
        return False

    # ---- walking ------------------------------------------------------------------------------------------------------------------------------------

    ROUTE_CELL = 8
    ROUTE_OPEN = 10                                 # an 8x8 cell with fewer walkable tiles is not entered (water, a mountain, a block of houses)

    def _open(self, cx, cy):
        v = self._open8.get((cx, cy))
        if v is None:
            if cx < 0 or cy < 0:
                v = 0
            else:
                x0, y0 = cx * self.ROUTE_CELL, cy * self.ROUTE_CELL
                v = sum(1 for i in range(self.ROUTE_CELL) for j in range(self.ROUTE_CELL) if self.data.walkable(x0 + i, y0 + j))     # the surface grid, or the dungeon side's
            self._open8[(cx, cy)] = v
        return v

    def route(self, x0, y0, x1, y1, limit=6000):
        """Waypoints (tile coordinates, cell centres) from (x0, y0) to (x1, y1) over the 8x8 route grid, or None when no land route joins them within
        `limit` expansions (the sea, a mountain range). Cached by cell pair. A straight line is returned when the ends share a cell or sit side by side."""
        R = self.ROUTE_CELL
        a, b = (x0 // R, y0 // R), (x1 // R, y1 // R)
        if cheb(a[0], a[1], b[0], b[1]) <= 1:
            return [(x1, y1)]
        key = (a, b)
        if key in self._routes:
            r = self._routes[key]
            return None if r is None else r[:-1] + [(x1, y1)]
        start_open = self._open(*a) >= self.ROUTE_OPEN
        goal_open = self._open(*b) >= self.ROUTE_OPEN
        if not goal_open:
            self._routes[key] = None
            return None
        heap = [(cheb(a[0], a[1], b[0], b[1]), 0, a)]
        came = {a: None}
        cost = {a: 0}
        n = 0
        found = None
        while heap and n < limit:
            _, g, c = heapq.heappop(heap)
            n += 1
            if c == b:
                found = c
                break
            if cost.get(c, 1e9) < g:
                continue
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    if not dx and not dy:
                        continue
                    nb = (c[0] + dx, c[1] + dy)
                    if nb in came and cost.get(nb, 1e9) <= g + 1:
                        continue
                    if self._open(*nb) < self.ROUTE_OPEN and nb != b:
                        continue
                    ng = g + (1.4 if dx and dy else 1.0)
                    if ng < cost.get(nb, 1e9):
                        cost[nb] = ng
                        came[nb] = c
                        heapq.heappush(heap, (ng + cheb(nb[0], nb[1], b[0], b[1]), ng, nb))
        if found is None:
            self._routes[key] = None if start_open else [(x1, y1)]       # from inside a closed cell (a house, a dock) a short straight walk out is allowed
            return self._routes[key]
        path = []
        c = found
        while c is not None:
            path.append(c)
            c = came[c]
        path.reverse()
        pts = [(cx * R + R // 2, cy * R + R // 2) for cx, cy in path[1:-1]]
        pts.append((x1, y1))
        self._routes[key] = pts
        return list(pts)

    def start_walk(self, p, x, y, exact=False):
        if p.walk:
            p.say_line("Cancelled the previous walk - one at a time, newest wins")
        p.task = None if p.task and p.task["kind"] in ("mine", "chop", "fish") else p.task
        p.meditating = False
        tx, ty = int(x), int(y)
        if not self.data.walkable(tx, ty):
            snap = None
            for r in range(1, 4):
                for dx in range(-r, r + 1):
                    for dy in range(-r, r + 1):
                        if max(abs(dx), abs(dy)) == r and self.data.walkable(tx + dx, ty + dy):
                            snap = (tx + dx, ty + dy)
                            break
                    if snap:
                        break
                if snap:
                    break
            if snap is None or exact:
                self._nopath(p, tx, ty)
                return
            tx, ty = snap
        if (tx >= wd.SURFACE_X) != (p.x >= wd.SURFACE_X) or (tx >= wd.SURFACE_X and self.data.side(tx, ty) != self.data.side(p.x, p.y)):
            self._nopath(p, tx, ty)                                 # another side of the map: as the client says, no path (a teleporter joins them)
            return
        pts = self.route(p.x, p.y, tx, ty)
        if pts is None:
            self._nopath(p, tx, ty)
            return
        p.walk = {"tx": tx, "ty": ty, "fx": float(p.x), "fy": float(p.y), "near": 0 if exact else 1, "path": pts, "factor": 1 / 1.1, "started": self._now}
        p.nav.update(active=True, status="walking", target=[tx, ty], reason=None)
        p.say_line(f"Walking to ({tx}, {ty}) - not waiting; watch .nav")

    def _tele_check(self, p):
        """Standing on a teleporter's entry: the bot is moved to its exit (the shard's Teleporter item), the walk over."""
        t = self.teleporters.get((p.x, p.y))
        if not t:
            return False
        p.x, p.y = t[0], t[1]
        p.walk = None
        p.nav.update(active=False, status="arrived", reason=None)
        p.gate_at = None
        self.events.append((self._now, "tele", p.name, t[3] or ""))
        self.version += 1
        return True

    def _nopath(self, p, tx, ty):
        p.nav.update(active=False, status="nopath", target=[tx, ty], reason=f"No path from ({p.x}, {p.y}) to ({tx}, {ty})")
        p.walk = None
        p.say_line(f"[WARN ] No path from ({p.x}, {p.y}) to ({tx}, {ty})")
        p.say_line(f"[NAV] goto {tx} {ty} -> nopath (No path from ({p.x}, {p.y}) to ({tx}, {ty})) plans=1 nodes=0 planMs=1 maxPlanMs=1")

    def stop_walk(self, p):
        if p.walk:
            p.walk = None
            p.nav.update(active=False, status="stopped", reason="stopped")

    def step_dir(self, p, d):
        v = DIRS.get(d.lower())
        if not v:
            return False
        nx, ny = p.x + v[0], p.y + v[1]
        if self.data.walkable(nx, ny):
            p.x, p.y = nx, ny
            p.task = None if p.task and p.task["kind"] in ("mine", "chop", "fish") else p.task
            p.meditating = False
            self.version += 1
            self._tele_check(p)
            return True
        p.say_line(f"Walk denied (seq 1) - resync to ({p.x}, {p.y})")
        return False

    # ---- speech --------------------------------------------------------------------------------------------------------------------------------------

    def say(self, p, text):
        p.say_line(f"[SAY] {p.name}: {text}")
        for o in self.players.values():
            if o is not p and cheb(o.x, o.y, p.x, p.y) <= 12:
                o.say_line(f"[SAY] {p.name}: {text}")
        low = text.strip().lower()
        if p.ghost:
            if low not in ("", "guards"):
                p.overhead("I am dead and cannot do that.")
            return
        banker = self._vendor_near(p, 12, role="bank")
        words = set(re.findall(r"[a-z]+", low))
        if "guards" in words or "guard" in words and low != "all guard me":
            low = "guards"                                          # 7. the server's speech keywords match inside a sentence, not only alone
        elif "bank" in words and banker:
            low = "bank"
        elif "balance" in words and banker:
            low = "balance"
        elif ("buy" in words or "sell" in words) and not re.match(r"(\w+) (buy|sell|train)$", low):
            v = self._vendor_near(p, 4)
            if v is not None:
                low = f"{v.name.split()[0].lower()} {'buy' if 'buy' in words else 'sell'}"      # "vendor buy" or a sentence with "buy" near a vendor opens the nearest one's list
        if low == "bank" and banker:
            p.bank_open = True
            p.say_line(f"[CONTAINER] Opened {p.bank_serial} (gump 0x0030)")
            return
        if low == "balance" and banker:
            p.say_line(f"[SAY] {banker.name}: Thy current bank balance is {self._bank_gold(p):,} gold.")
            return
        m = re.match(r"withdraw (\d+)$", low)
        if m and banker:
            n = min(int(m.group(1)), self._bank_gold(p))
            if n > 0:
                self._bank_take_gold(p, n)
                p.add_gold(n)
                p.say_line(f"[SAY] {banker.name}: Thou hast withdrawn gold from thy account.")
            return
        if low == "guards":
            if self.data.in_town(p.x, p.y):
                for c in self.creatures_near(p.x, p.y, 10):
                    if c.aggressive and not c.tamed:
                        p.say_line(f"[SAY] a guard: Thou wilt regret thine actions, swine!")
                        self._creature_dies(c, None)
            return
        if low in ("all release", "all follow", "all guard me", "all kill", "all stay", "all come"):
            if low == "all release":
                for s in p.pets:
                    c = self.creatures.get(s)
                    if c:
                        c.tamed, c.pet_of, c.aggressive = False, None, self.data.aggressive(c.kind)
                p.pets = []
            return
        m = re.match(r"(\w+) (buy|sell|train)$", low)
        if m:
            v = self._vendor_named(p, m.group(1), 4)
            if v is None:
                return
            if m.group(2) == "train":
                p.say_line(f"[SAY] {v.name}: I can teach thee no more than thou already knowest!")
                return
            if m.group(2) == "buy":
                p.say_line(f"[CONTAINER] Opened {v.serial} (gump 0x0030)")
                p.say_line(f"[SAY] {v.name}: Greetings.  Have a look around.")
                lines = [f"[SHOP] vendor {v.serial}:"]
                for st in v.stock:
                    if st["qty"] <= 0:
                        continue
                    s = v.serials.setdefault(st["name"], self.new_item_serial())
                    lines.append(f"  {s} {st['price']:7d}gp  x{st['qty']:<4d} {st['name']}")
                p.last_shop = (v, "buy", lines)
                p.say_line(lines[0])
            else:
                lines = [f"[SHOP] sell to vendor {v.serial}:"]
                for it in p.backpack:
                    price = self._buy_price(v, it)
                    if price > 0 and not it.get("newbied"):
                        lines.append(f"  {it['serial']} {price:7d}gp  x{it.get('amount') or 1:<4d} {it['name']}")
                p.last_shop = (v, "sell", lines)
                p.say_line(lines[0])

    BUYBACK_CAP = 20                                   # a vendor buys at most this many of a kind an hour (the shard's vendors stop buying what they hold enough of)

    def _buyback_left(self, v, name):
        rec = v.bought.get(name)
        hour = int(self._now // 3600)
        if rec is None or rec[0] != hour:
            return self.BUYBACK_CAP
        return max(0, self.BUYBACK_CAP - rec[1])

    def _buy_price(self, v, it):
        n = (it.get("name") or "").lower()
        if self._buyback_left(v, n) <= 0:
            return 0
        if n in v.buys:
            return int(v.buys[n])
        for k, price in v.buys.items():
            if k in n or n in k:
                return int(price)
        for st in v.stock:
            if st["name"].lower() == n:
                return max(1, st["price"] // 2)
        return 0

    def _vendor_near(self, p, r, role=None):
        best = None
        for v in self.vendors.values():
            if role and v.role != role:
                continue
            d = cheb(v.x, v.y, p.x, p.y)
            if d <= r and (best is None or d < best[0]):
                best = (d, v)
        return best[1] if best else None

    def _vendor_named(self, p, first, r):
        for v in self.vendors.values():
            if v.name.split()[0].lower() == first and cheb(v.x, v.y, p.x, p.y) <= r:
                return v
        return None

    def _bank_gold(self, p):
        return sum(i.get("amount") or 1 for i in p.bank if (i.get("name") or "").lower() == "gold coin")

    def _bank_take_gold(self, p, n):
        left = n
        for i in list(p.bank):
            if (i.get("name") or "").lower() == "gold coin":
                a = i.get("amount") or 1
                if a <= left:
                    p.bank.remove(i)
                    left -= a
                else:
                    i["amount"] = a - left
                    left = 0
            if left <= 0:
                break

    # ---- actions ------------------------------------------------------------------------------------------------------------------------------------

    def _acted(self, p):
        if p.between_until:
            p.between_until = 0.0

    def attack(self, p, serial):
        self._acted(p)
        c = self.creatures.get(serial)
        if c is None or p.ghost:
            return
        p.target = serial
        p.war = True
        p.meditating = False
        p.say_line(f"Attacking {serial}")
        if c.tamed:
            p.criminal_until = self._now + 120
        self.version += 1

    def use(self, p, serial):
        """Double-click: an item in the pack, a worn tool, a corpse, a container, a vendor."""
        if p.ghost:
            p.overhead("I am dead and cannot do that.")
            return
        if serial == p.backpack_serial:
            return
        it = p.item(serial) or p.worn(serial)
        if it is not None:
            self._use_item(p, it)
            return
        c = self.corpses.get(serial)
        if c is not None:
            if cheb(c.x, c.y, p.x, p.y) > 2:
                p.system("You are too far away.")
                return
            if c.kind is not None and c.killer and c.killer != p.serial and self._now - c.born < 120 and not self._party(p, c.killer):
                p.system("Looting this monster corpse will be a criminal act!")
            p.opened.add(serial)
            p.say_line(f"[CONTAINER] Opened {serial} (gump 0x0009)")
            p.say_line(f"[CONTAINER] Contents: {len(c.items)} item(s)")
            return
        if serial in self.vendors:
            v = self.vendors[serial]
            p.say_line(f"[SAY] {v.name}: Greetings.  Have a look around.")

    def _party(self, p, other):
        return bool(p.party) and p.party == getattr(self.players.get(other), "party", None)

    # ---- parties (item 5: enough for two bots to share a tour) --------------------------------------------------------------------------------------------------

    def party_members(self, p):
        g = self.parties.get(p.party) if p.party else None
        return list(g["members"]) if g else []

    def party_info(self, p):
        inv = p.party_invite or 0
        if not p.party or p.party not in self.parties:
            return [f"[PARTY] not in a party leader=0x00000000 inviter={inv if isinstance(inv, str) else '0x00000000'} canloot=no members=0"]
        g = self.parties[p.party]
        names = " ".join(f"{s}:{self.players[s].name}" for s in g["members"] if s in self.players)
        return [f"[PARTY] in a party leader={p.party} inviter=0x00000000 canloot={'yes' if g['loot'] else 'no'} members={len(g['members'])} {names}"]

    def party_accept(self, p):
        inv = p.party_invite
        p.party_invite = None
        other = self.players.get(inv) if inv else None
        if other is None:
            return ["No party invitation"]
        if p.party:
            self.party_leave(p)
        leader = other.party or other.serial
        g = self.parties.setdefault(leader, {"members": [leader], "loot": False})
        other.party = leader
        if p.serial not in g["members"]:
            g["members"].append(p.serial)
        p.party = leader
        self.events.append((self._now, "party", p.name, other.name))
        for s in g["members"]:
            self.players[s].system(f"{p.name} has joined the party.")
        return ["Party invitation accepted"]

    def party_leave(self, p):
        g = self.parties.get(p.party) if p.party else None
        if g:
            g["members"] = [s for s in g["members"] if s != p.serial]
            for s in g["members"]:
                self.players[s].system(f"{p.name} has left the party.")
            if len(g["members"]) <= 1:
                for s in g["members"]:
                    self.players[s].party = None
                self.parties.pop(p.party, None)
        p.party = None
        return ["Left the party"]

    def _use_item(self, p, it):
        n = (it.get("name") or "").lower()
        if n == "bandage":
            p.cursor = ("bandage", it)
            p.say_line("[TARGET] Server wants a target (cursor 0x00000001, object) - use 'target <serial|self>'")
            p.system("Who will you use the bandages on?")
        elif n in ("pickaxe", "shovel"):
            p.cursor = ("mine", it)
            p.say_line("[TARGET] Server wants a target (cursor 0x00000002, object) - use 'target <serial|self>'")
            p.system("Where do you wish to dig?")
        elif "fishing pole" in n:
            p.cursor = ("fish", it)
            p.say_line("[TARGET] Server wants a target (cursor 0x00000003, object) - use 'target <serial|self>'")
            p.system("What water do you want to fish in?")
        elif n in ("hatchet", "axe") or "axe" in n and p.worn(it["serial"]):
            p.cursor = ("chop", it)
            p.say_line("[TARGET] Server wants a target (cursor 0x00000004, object) - use 'target <serial|self>'")
        elif "ore" in n and p.world.stackable(n):
            p.cursor = ("smelt", it)
            p.say_line("[TARGET] Server wants a target (cursor 0x00000005, object) - use 'target <serial|self>'")
            p.system("Select the forge on which to smelt the ore, or another pile of ore with which to combine it.")
        elif any(w in n for w in ("dagger", "knife", "cleaver", "sword", "kryss", "katana", "cutlass", "scimitar", "axe", "scissors")):
            p.cursor = ("blade", it)
            p.say_line("[TARGET] Server wants a target (cursor 0x00000006, object) - use 'target <serial|self>'")
            p.system("What do you want to use this item on?" if "scissors" not in n else "What should I use these scissors on?")
        elif any(w in n for w in ("tongs", "sewing kit", "saw", "tinker's tools", "tool kit", "smith's hammer", "fletching")):
            p.cursor = ("craft_tool", it)
            p.say_line("[TARGET] Server wants a target (cursor 0x00000007, object) - use 'target <serial|self>'")
            p.system("Target this tool to make last item, or any other target to begin crafting.")
        elif "yellow potion" in n or "lesser heal" in n or "heal potion" in n:
            p.take(it["name"], 1)
            p.hp = min(p.max_hp, p.hp + self.rng.randint(6, 15))
            p.system("You feel better.")
        elif "red potion" in n or "refresh" in n:
            p.take(it["name"], 1)
            p.stam = min(p.max_stam, p.stam + int(p.max_stam * 0.25))
            p.system("You feel refreshed.")
        elif "orange potion" in n or "cure" in n:
            p.take(it["name"], 1)
            if p.poisoned:
                p.poisoned = False
                p.system("You feel cured of poison.")
        elif "kindling" in n:
            p.take(it["name"], 1)
            p.system("You feel it would take a few moments to secure your camp.")
            self.gain(p, "Camping", 0.5)
        elif n in ("fish",) or n.startswith("raw ") and "fish" in n:
            pass
        elif "book" in n and "spell" in n or n == "book":
            p.say_line("[GUMP] opened local 0x00000100 server 0x00000000 SpellbookGump - use 'gumpresponse <button>'")
        else:
            p.say_line(f"Used {it['serial']}")

    def target(self, p, serial_or_self, tile=None):
        """Answer the open cursor: self, a mobile or item serial, or a tile (x, y, z)."""
        cur = p.cursor
        p.cursor = None
        if cur is None:
            p.say_line("[TARGET] nothing is asking for a target")
            return
        kind, it = cur
        if kind == "party":
            other = self.players.get(serial_or_self)
            if other is None or other is p:
                p.system("You cannot add that to your party.")
                return
            other.party_invite = p.serial
            other.system(f"{p.name} invites you to join the party.")
            return
        if kind == "bandage":
            if p.task and p.task["kind"] == "bandage":
                return
            if serial_or_self == "self" or serial_or_self == p.serial:
                if p.hp >= p.max_hp and not p.poisoned:
                    p.system("That being is not damaged.")
                    return
                p.take("bandage", 1)
                p.system("You begin applying the bandages.")
                p.task = {"kind": "bandage", "at": self._now + max(4.0, 11 - p.dex / 20)}
            else:
                other = self.players.get(serial_or_self)
                if other is not None and not other.ghost and cheb(other.x, other.y, p.x, p.y) <= 2 and other.hp < other.max_hp:
                    p.take("bandage", 1)
                    p.system("You begin applying the bandages.")
                    p.task = {"kind": "bandage", "at": self._now + max(4.0, 11 - p.dex / 20), "who": other.serial}
                else:
                    p.system("That being is not damaged.")
        elif kind in ("mine", "chop", "fish"):
            if tile is None:
                p.system("Target cannot be seen.")
                return
            x, y, z = tile
            d = cheb(x, y, p.x, p.y)
            if kind == "fish":
                if not self.data.is_water(x, y):
                    p.system("You need water to fish in!")
                    return
                if d > 4:
                    p.system("You need to be closer to the water to fish!")
                    return
            elif d > 2:
                p.system("Target cannot be seen." if d > 6 else "That is too far away.")
                return
            elif kind == "mine" and self.data.walkable(x, y) and not any(cheb(x, y, mx, my) <= 2 for mx, my, _, _ in self.data.mountains[:0]):
                if self.data.walkable(x, y) and self.data.is_water(x, y):
                    p.system("There is no metal here to mine.")
                    return
            if kind == "chop" and not any(cheb(x, y, tx, ty) <= 1 for tx, ty, _, _ in self.data.trees) and self.data.walkable(x, y):
                p.system("That is not a tree.")
                return
            if self._now < p.next_skill and kind != "chop":
                p.system("You must wait a few moments to use another skill.")
                return
            p.next_skill = self._now + SKILL_DELAY
            p.task = {"kind": kind, "x": x, "y": y, "at": self._now + 1.0}
        elif kind == "smelt":
            fx = next((f for f in self.fixtures if f["serial"] == serial_or_self), None)
            if fx is None or cheb(fx["x"], fx["y"], p.x, p.y) > 2:
                p.system("You can't reach the forge." if fx else "There is no ore in that.")
                return
            ore = p.item(it["serial"])
            if ore is None:
                return
            n = ore.get("amount") or 1
            mining = p.skill("Mining")
            colour = (ore.get("name") or "iron ore").replace(" ore", "")
            need = {"iron": 0, "dull copper": 65, "shadow iron": 70, "bronze": 80}.get(colour, 0)
            if mining < need:
                p.system("You have no idea how to smelt this strange ore!")
                return
            p.take(ore["name"], n)
            if self.rng.random() < 0.5 + mining / 200:
                p.add_item({"name": f"{colour} ingot", "amount": n, "graphic": 0x1BF2})
                p.system("You smelt the ore removing the impurities and put the metal in your backpack.")
            else:
                p.add_item({"name": f"{colour} ingot", "amount": max(1, n // 2), "graphic": 0x1BF2})
                p.system("You burn away the impurities but are left with less useable metal.")
            self.gain(p, "Mining", 0.4)
        elif kind == "blade":
            c = self.corpses.get(serial_or_self)
            if c is None:
                if "scissors" in (it.get("name") or "").lower():
                    cloth = p.item(serial_or_self)
                    if cloth and (cloth.get("name") or "").lower() == "cut cloth":
                        n = cloth.get("amount") or 1                              # the shard's Cloth.Scissor: cut cloth into bandages, one for one
                        p.take(cloth["name"], n)
                        p.add_item({"name": "bandage", "amount": n, "graphic": 0x0E21})
                        p.system("You cut the material into bandages.")
                        return
                    if cloth and "cloth" in (cloth.get("name") or "").lower() and "cut" not in cloth["name"].lower():
                        n = cloth.get("amount") or 1
                        p.take(cloth["name"], n)
                        p.add_item({"name": "cut cloth", "amount": n * (50 if "bolt" in cloth["name"].lower() else 1), "graphic": 0x1766})
                        p.system("You cut the material into pieces.")
                        return
                    hides = p.item(serial_or_self)
                    if hides and "hides" in (hides.get("name") or "").lower():
                        n = hides.get("amount") or 1                              # scissors on hides: leather, one a hide (the shard's Hides.cs)
                        p.take(hides["name"], n)
                        p.add_item({"name": "leather", "amount": n, "graphic": 0x1081})
                        p.system("You cut the hides into leather.")
                        return
                    fish = p.item(serial_or_self)
                    if fish and (fish.get("name") or "").lower() == "fish":
                        n = fish.get("amount") or 1
                        p.take("fish", n)
                        p.add_item({"name": "raw fish steak", "amount": n * 4, "graphic": 0x097A})
                        return
                p.system("You can't use a bladed item on that.")
                return
            if cheb(c.x, c.y, p.x, p.y) > 2:
                p.system("That is too far away.")
                return
            if c.kind is None:
                p.system("You can't use a bladed item on that.")
                return
            if c.carved:
                p.system("You see nothing useful to carve from the corpse.")
                return
            c.carved = True
            lv = self.data.loot.get(c.kind) or {}
            meat = int(lv.get("meat") or 0)
            hides = int(lv.get("hides") or 0)
            if meat:
                c.items.append({"serial": self.new_item_serial(), "name": MEAT_NAMES.get(lv.get("meat_type"), "cut of raw ribs"), "amount": meat, "graphic": 0x09F1})
                p.system("You carve some meat, which remains on the corpse.")
            if hides:
                c.items.append({"serial": self.new_item_serial(), "name": "pile of hides", "amount": hides, "graphic": 0x1079})
                p.system("You skin it, and the hides are now in the corpse.")
            if not meat and not hides:
                p.system("You see nothing useful to carve from the corpse.")
            if c.killer and c.killer != p.serial and self._now - c.born < 120:
                p.criminal_until = self._now + 120
                p.system("You have lost a little karma.")
        elif kind == "craft_tool":
            mat = p.item(serial_or_self)
            if mat is None:
                p.system("You cannot craft with that.")
                return
            self._open_craft_menu(p, it, mat)
        elif kind == "tame":
            c = self.creatures.get(serial_or_self)
            if c is None:
                p.system("That is not a creature you can tame.")
                return
            td = self.data.tame.get(c.kind) if hasattr(self.data, "tame") else None
            if td is None:
                p.system("That animal cannot be tamed.")
                return
            if cheb(c.x, c.y, p.x, p.y) > 3:
                p.system("You are too far away to tame that.")
                return
            if c.tamed:
                p.system("That animal looks tame already.")
                return
            if len(p.pets) >= 5:
                p.system("You have too many followers to tame that creature.")
                return
            if p.skill("Animal Taming") < td["min"] - 5:
                p.system("You have no chance of taming this creature.")
                return
            p.system("You start to tame the creature.")
            p.task = {"kind": "tame", "serial": c.serial, "min": td["min"], "at": self._now + 9.0}
        elif kind == "spell":
            self._cast_at(p, it, serial_or_self)
        elif kind == "lore":
            p.system("You cannot learn anything useful about this creature.")

    # ---- crafting ------------------------------------------------------------------------------------------------------------------------------------

    def _open_craft_menu(self, p, tool, mat):
        n = (tool.get("name") or "").lower()
        craft = "Blacksmith" if "tongs" in n or "smith" in n else "Tailoring" if "sewing" in n else "Carpentry" if "saw" in n else "Tinkering" if "tinker" in n or "tool kit" in n else None
        if craft is None or craft not in self.data.craft:
            p.system("You cannot craft with that.")
            return
        items = self.data.craft[craft]
        matn = (mat.get("name") or "").lower()
        res = {"Blacksmith": "IronIngot", "Tailoring": "Cloth", "Carpentry": "Board", "Tinkering": "IronIngot"}[craft]
        want = {"IronIngot": "ingot", "Cloth": "cloth", "Board": ("board", "log")}[res]
        if not any(w in matn for w in (want if isinstance(want, tuple) else (want,))):
            p.system("You cannot craft with that material.")
            return
        skill = p.skill({"Blacksmith": "Blacksmithy", "Tailoring": "Tailoring", "Carpentry": "Carpentry", "Tinkering": "Tinkering"}[craft])
        have = mat.get("amount") or 1
        names = sorted(k for k, v in items.items() if v.get("min", 0) <= skill and v.get("resource", res) == res)
        if not names:
            p.system("You don't have the resources required to make that item.")
            return
        groups = [names[i:i + 12] for i in range(0, len(names), 12)]
        top = [("Repair", None), ("Smelt", None)] if craft == "Blacksmith" else []
        top += [(f"Build Group {chr(65 + i)}", g) for i, g in enumerate(groups)]
        unit = RESOURCE_WORDS[res][1]
        local = 0x100 + len(p.gumps) + 1
        menu = {"local": f"0x{local:08X}", "server": "0x00000000", "title": "What would you like to make?", "options": [(i + 1, t) for i, (t, _) in enumerate(top)],
                "tree": top, "craft": craft, "mat": mat, "unit": unit, "items": items}
        p.menus = [menu]

    def menus(self, p):
        ms = getattr(p, "menus", None) or []
        if not ms:
            return ["No legacy menus open"]
        out = []
        for m in reversed(ms):
            out.append(f"[MENU] local {m['local']} server {m['server']} {m['title']}")
            for i, t in m["options"]:
                out.append(f"  [option {i}] graphic 0x0000 hue 0x0000 {t}")
        return out

    def menuresponse(self, p, local, server, index):
        ms = getattr(p, "menus", None) or []
        m = next((x for x in ms if x["local"] == local), None)
        if m is None:
            return ["No such menu"]
        ms.remove(m)
        if index == 0:
            return ["Menu closed"]
        opt = next((t for i, t in m["options"] if i == index), None)
        if opt is None:
            return ["No such option"]
        if "tree" in m:
            group = next((g for t, g in m["tree"] if t == opt), None)
            if not group:
                return [f"Menu option {index} sent; verify the resulting menu or inventory"]
            items = m["items"]
            opts = [(i + 1, f"{name} ({items[name]['amount']} {m['unit']})") for i, name in enumerate(group)]
            local2 = f"0x{int(m['local'], 16) + 1:08X}"
            p.menus.append({"local": local2, "server": "0x00000000", "title": "What would you like to make?", "options": opts, "leaf": group, "craft": m["craft"], "mat": m["mat"],
                            "items": items, "unit": m["unit"]})
            return [f"Menu option {index} sent; verify the resulting menu or inventory"]
        name = m["leaf"][index - 1]
        self._craft(p, m["craft"], name, m["items"][name], m["mat"])
        return [f"Menu option {index} sent; verify the resulting menu or inventory"]

    def _craft(self, p, craft, name, spec, mat):
        skill_name = {"Blacksmith": "Blacksmithy", "Tailoring": "Tailoring", "Carpentry": "Carpentry", "Tinkering": "Tinkering"}[craft]
        skill = p.skill(skill_name)
        need = int(spec.get("amount") or 1)
        matname = mat.get("name") or ""
        if p.count(matname.lower()) < need:
            p.system("You don't have the resources required to make that item.")
            return
        lo, hi = float(spec.get("min", 0)), float(spec.get("max", 100))
        chance = 1.0 if hi <= lo else max(0.0, min(1.0, (skill - lo) / (hi - lo)))
        self.stats["crafts"] += 1
        if self.rng.random() < chance:
            p.take(matname, need)
            exc = self.rng.random() < max(0.0, (skill - lo) / (hi - lo) - 0.5) * 0.5
            p.add_item({"name": name, "amount": 1, "graphic": 0x0F3F})
            p.system("You create an exceptional quality item." if exc else "You create the item.")
            self.events.append((self._now, "craft", p.name, name))
        else:
            p.take(matname, max(1, need // 2))
            p.system("You failed to create the item, and some of your materials are lost.")
        self.gain(p, skill_name, 0.5 if 0 < chance < 1 else 0.1)

    # ---- spells --------------------------------------------------------------------------------------------------------------------------------------

    def cast(self, p, spell):
        self._acted(p)
        info = self.data.spells.get(spell.lower())
        if info is None:
            return [f"Unknown spell '{spell}'"]
        if p.ghost:
            p.overhead("I am dead and cannot do that.")
            return ["dead"]
        p.meditating = False
        p.say_line(f"[SPELL] {p.name}: {info['mantra']}")
        if p.mana < info["mana"]:
            p.overhead("Insufficient mana for this spell.")
            return [f"Casting {info['name']} - insufficient mana"]
        for r in info.get("reagents", []):
            if p.count(REAGENT_NAMES.get(r, r.lower())) < 1:
                p.overhead("More reagents are needed for this spell.")
                return [f"Casting {info['name']} - more reagents are needed"]
        needs_target = spell.lower() not in ("reactive armor", "protection", "night sight", "magic reflection", "mind blast") or True
        p.cursor = ("spell", info)
        if spell.lower() in ("reactive armor", "protection", "night sight", "magic reflection", "agility", "strength", "cunning", "bless", "heal", "greater heal", "cure", "arch cure"):
            pass
        p.say_line(f"[TARGET] Server wants a target (cursor 0x00000965, object) - use 'target <serial|self>'")
        return [f"Casting {info['name']} (index 0, \"{info['mantra']}\", {info['mana']} mana) - a target cursor follows - answer it with `target <serial|self>`"]

    def _cast_at(self, p, info, target):
        p.mana = max(0, p.mana - info["mana"])
        for r in info.get("reagents", []):
            p.take(REAGENT_NAMES.get(r, r.lower()), 1)
        magery = p.skill("Magery")
        lo, hi = float(info.get("min_skill") or 0), float(info.get("max_skill") or 100)
        chance = max(0.0, min(1.0, (magery - lo) / max(1.0, hi - lo)))
        self.stats["casts"] += 1
        self.gain(p, "Magery", 0.5 if 0 < chance < 1 else 0.1)
        if self.rng.random() >= chance:
            p.overhead("The spell fizzles.")
            return
        name = info["name"].lower()
        if name in ("mark", "recall"):
            rune = p.item(target)
            if rune is None or "rune" not in (rune.get("name") or "").lower():
                p.system("That is not a valid rune." if name == "recall" else "That is not a rune.")
                return
            if name == "mark":
                rune["marked"] = [p.x, p.y]
                p.system("You mark the rune.")
                return
            if not rune.get("marked"):
                p.system("That rune is not yet marked.")
                return
            self.stop_walk(p)
            p.x, p.y = int(rune["marked"][0]), int(rune["marked"][1])
            self.events.append((self._now, "recall", p.name, f"{p.x},{p.y}"))
            self.version += 1
            return
        if name in SPELL_HEAL:
            tgt = p if target in ("self", p.serial) else self.players.get(target) or p
            lo_h, hi_h = SPELL_HEAL[name]
            tgt.hp = min(tgt.max_hp, tgt.hp + self.rng.randint(lo_h, hi_h) + int(magery / 10))
            return
        if name in ("cure", "arch cure"):
            p.poisoned = False
            return
        if name in SPELL_DAMAGE:
            c = self.creatures.get(target)
            if c is None:
                return
            if cheb(c.x, c.y, p.x, p.y) > 12:
                return
            lo_d, hi_d = SPELL_DAMAGE[name]
            if name == "poison":
                dmg = self.rng.randint(2, 6)
            else:
                dmg = self.rng.randint(lo_d, hi_d) * (0.8 + p.skill("Evaluating Intelligence") / 250)
            dmg = max(1, int(round(dmg * max(0.3, 1 - c.armor / 200))))
            self.gain(p, "Evaluating Intelligence", 0.3)
            if c.target is None and not c.tamed:
                c.target = p.serial
            c.last_hit_by = p.serial
            p.war = True
            self.damage_creature(c, dmg, p)

    # ---- skills by name --------------------------------------------------------------------------------------------------------------------------------

    def useskill(self, p, name):
        self._acted(p)
        n = name.lower().strip()
        if p.ghost:
            p.overhead("I am dead and cannot do that.")
            return ["dead"]
        if self._now < p.next_skill:
            p.system("You must wait a few moments to use another skill.")
            return [f"Used skill {name} - wait"]
        p.next_skill = self._now + SKILL_DELAY
        if n == "animal taming":
            p.cursor = ("tame", None)
            p.say_line("[TARGET] Server wants a target (cursor 0x00000005, object) - use 'target <serial|self>'")
            p.system("Tame which animal?")
            return ["Used skill Animal Taming (index 35) - if it needs a target, answer the cursor with `target <serial>`"]
        if n == "animal lore":
            p.cursor = ("lore", None)
            p.say_line("[TARGET] Server wants a target (cursor 0x00000006, object) - use 'target <serial|self>'")
            return ["Used skill Animal Lore (index 2) - if it needs a target, answer the cursor with `target <serial>`"]
        if n == "meditation":
            p.meditating = True
            p.system("You enter a meditative trance.")
            self.gain(p, "Meditation", 0.5)
            return ["Used skill Meditation (index 46) - if it needs a target, answer the cursor with `target <serial>`"]
        if n == "hiding":
            p.hidden = self.rng.random() < p.skill("Hiding") / 100
            p.system("You have hidden yourself well." if p.hidden else "You can't seem to hide here.")
            return ["Used skill Hiding (index 21)"]
        if n in ("peacemaking", "provocation", "discordance", "musicianship"):
            p.system("What instrument shall you play?")
            if n == "musicianship":
                self.gain(p, "Musicianship", 0.5)
                return ["Used skill Musicianship"]
            inst = next((i for i in p.backpack if any(w in (i.get("name") or "").lower() for w in ("lute", "harp", "drum", "tambourine"))), None)
            if inst is None:
                p.system("You do not have an instrument to play on!")
                return [f"Used skill {name}"]
            if n == "peacemaking":
                near = [c for c in self.creatures_near(p.x, p.y, 8) if c.target]
                if not near:
                    p.system("You play hypnotic music, but there is nothing in range for you to calm.")
                elif self.rng.random() < p.skill("Peacemaking") / 110:
                    for c in near:
                        c.target = None
                    p.system("You play your hypnotic music, stopping the battle.")
                else:
                    p.system("You attempt to calm everyone, but fail.")
                self.gain(p, "Peacemaking", 0.5)
                self.gain(p, "Musicianship", 0.3)
            else:
                p.cursor = ("bard", n)
                p.say_line("[TARGET] Server wants a target (cursor 0x00000008, object) - use 'target <serial|self>'")
            return [f"Used skill {name.title()}"]
        return [f"Used skill {name} (index 0)"]

    # ---- items in the world -----------------------------------------------------------------------------------------------------------------------------

    def get_item(self, p, serial, amount=None):
        for c in self.corpses.values():
            for it in c.items:
                if it["serial"] == serial:
                    if cheb(c.x, c.y, p.x, p.y) > 2:
                        p.system("You are too far away.")
                        return
                    if c.kind is not None and c.killer and c.killer != p.serial and self._now - c.born < 120:
                        p.criminal_until = self._now + 120
                    c.items.remove(it)
                    p.add_item(dict(it, newbied=False))
                    p.say_line(f"Grabbed {serial}")
                    self.version += 1
                    return
        it = self.ground.get(serial)
        if it is not None and cheb(it["x"], it["y"], p.x, p.y) <= 2:
            del self.ground[serial]
            p.add_item({k: v for k, v in it.items() if k not in ("x", "y", "decay_at", "fixed")})
            p.say_line(f"Grabbed {serial}")
            self.version += 1

    def drop(self, p, serial, container, amount=None):
        it = p.item(serial)
        if it is None:
            return
        n = it.get("amount") or 1
        if amount is not None:
            n = min(n, int(amount))
        if container == p.bank_serial:
            if not p.bank_open or self._vendor_near(p, 12, role="bank") is None:
                return
            if len(p.bank) >= BANK_SLOTS and not (self.stackable(it["name"]) and any((b.get("name") or "") == it["name"] for b in p.bank)):
                p.system("That container cannot hold more items.")
                return
            if n >= (it.get("amount") or 1):
                p.backpack.remove(it)
                moved = it
            else:
                it["amount"] -= n
                moved = dict(it, amount=n, serial=self.new_item_serial())
            stacked = False
            if self.stackable(moved["name"]):
                for b in p.bank:
                    if (b.get("name") or "") == moved["name"]:
                        b["amount"] = (b.get("amount") or 1) + (moved.get("amount") or 1)
                        stacked = True
                        break
            if not stacked:
                p.bank.append(moved)
            return
        if container == p.backpack_serial:
            return
        for o in self.players.values():
            if o.backpack_serial == container and cheb(o.x, o.y, p.x, p.y) <= 3:
                if n >= (it.get("amount") or 1):
                    p.backpack.remove(it)
                    o.add_item(dict(it, newbied=False))
                else:
                    it["amount"] -= n
                    o.add_item(dict(it, amount=n, serial=self.new_item_serial(), newbied=False))
                return

    def dropground(self, p, serial, amount):
        it = p.item(serial)
        if it is None:
            return [f"No such item {serial}"]
        if p.weight() > p.max_weight + 30:
            p.system("You are overloaded.")
            return ["Drop refused"]
        n = min(int(amount or 1), it.get("amount") or 1)
        if n >= (it.get("amount") or 1):
            p.backpack.remove(it)
            moved = it
        else:
            it["amount"] -= n
            moved = dict(it, amount=n, serial=self.new_item_serial())
        self.ground[moved["serial"]] = dict(moved, x=p.x, y=p.y, decay_at=self._now + GROUND_ITEM_S)
        self.version += 1
        return [f"Dropped {moved['serial']} on the ground at ({p.x}, {p.y}, 0)"]

    def equip(self, p, serial, layer=None):
        it = p.item(serial)
        if it is None:
            return [f"No such item {serial}"]
        n = (it.get("name") or "").lower()
        w = self.data.weapon(n)
        if w:
            lay = "TwoHanded" if w.get("two") else "OneHanded"
            for e in list(p.equipped):
                if e.get("layer") in ("OneHanded", "TwoHanded") and (lay == "TwoHanded" or e.get("layer") == "OneHanded" or self.data.weapon(e.get("name", ""))):
                    p.equipped.remove(e)
                    p.backpack.append(e)
        else:
            lay = layer or next((v for k, v in LAYERS.items() if k in n), None)
            if lay is None:
                return [f"Cannot equip {it['name']}"]
            for e in list(p.equipped):
                if e.get("layer") == lay:
                    p.equipped.remove(e)
                    p.backpack.append(e)
        p.backpack.remove(it)
        it["layer"] = lay
        p.equipped.append(it)
        p.say_line(f"Equipped {serial}")
        return [f"Equipped {serial}"]

    def unequip(self, p, serial):
        it = p.worn(serial)
        if it is None:
            return [f"Not worn: {serial}"]
        p.equipped.remove(it)
        it.pop("layer", None)
        p.backpack.append(it)
        p.say_line(f"Unequipped {serial}")
        return [f"Unequipped {serial}"]

    def buy(self, p, pairs):
        if not p.last_shop or p.last_shop[1] != "buy":
            return ["No shop list open"]
        v = p.last_shop[0]
        if cheb(v.x, v.y, p.x, p.y) > 6:
            return ["The vendor is too far away"]
        total, bought = 0, []
        for serial, n in pairs:
            name = next((nm for nm, s in v.serials.items() if s == serial), None)
            st = next((s for s in v.stock if s["name"] == name), None) if name else None
            if st is None:
                continue
            n = min(int(n), st["qty"])
            if n <= 0:
                continue
            total += n * st["price"]
            bought.append((st, n))
        if total > p.gold():
            p.say_line(f"[SAY] {v.name}: Begging thy pardon, but thou canst not afford that.")
            return ["Buy request sent: not enough gold"]
        p.add_gold(-total)
        for st, n in bought:
            st["qty"] -= n
            units = 50 if st["name"].lower().startswith("bolt of") and False else 1
            p.add_item({"name": st["name"].lower() if st["name"].lower() in ("bandage", "arrow", "bolt", "iron ingot", "board", "log") else st["name"], "amount": n * units, "graphic": 0x0F3F, "newbied": False})
        p.say_line(f"[SAY] {v.name}: The total of your purchase is {total} gold.  My thanks for the patronage.")
        self.stats["buys"] += 1
        self.events.append((self._now, "buy", p.name, total))
        return ["Buy request sent: " + ", ".join(f"{n} x {s}" for s, n in pairs)]

    def sell(self, p, pairs):
        if not p.last_shop or p.last_shop[1] != "sell":
            return ["No sell list open"]
        v = p.last_shop[0]
        if cheb(v.x, v.y, p.x, p.y) > 6:
            return ["The vendor is too far away"]
        total = 0
        for serial, n in pairs:
            it = p.item(serial)
            if it is None:
                continue
            price = self._buy_price(v, it)
            if price <= 0:
                continue
            n = min(int(n), it.get("amount") or 1, self._buyback_left(v, (it.get("name") or "").lower()))
            if n <= 0:
                continue
            key = (it.get("name") or "").lower()
            hour = int(self._now // 3600)
            rec = v.bought.get(key)
            v.bought[key] = [hour, (rec[1] if rec and rec[0] == hour else 0) + n]
            total += price * n
            if n >= (it.get("amount") or 1):
                p.backpack.remove(it)
            else:
                it["amount"] -= n
        if total:
            p.add_gold(total)
            self.stats["sales"] += 1
            self.events.append((self._now, "sale", p.name, total))
        return ["Sell request sent: " + ", ".join(f"{n} x {s}" for s, n in pairs)]

    # ---- gumps (the healer's offer) -------------------------------------------------------------------------------------------------------------------

    def gumps(self, p):
        if p.ghost:
            healer = self._vendor_near(p, 4, role="healer")
            far = self._vendor_near(p, 7, role="healer") is None
            if far:
                p.res_declined_near = None
            if healer and p.res_declined_near is None and not any(g[2] == "res" for g in p.gumps):
                p.gumps.append((f"0x{0x200 + len(p.gumps):08X}", self.new_item_serial(), "res", ["  Resurrection", "  [button 1] CONTINUE", "  [button 0] CANCEL"]))
        if not p.gumps:
            return ["No server gumps open"]
        out = []
        for local, server, kind, lines in p.gumps:
            out.append(f"[GUMP] local {local} server {server} {'ResurrectGump' if kind == 'res' else 'Gump'}")
            out += ["[GUMP] " + l for l in lines]
        return out

    def _gate_check(self, p):
        """Standing on a public moongate: the gate's list opens (once per standing)."""
        for i, g in enumerate(self.moongates):
            if cheb(g["x"], g["y"], p.x, p.y) <= 1 and not any(x[2] == "gate" for x in p.gumps) and p.gate_at != (g["x"], g["y"]):
                p.gate_at = (g["x"], g["y"])
                lines = ["  Pick your destination:"] + [f"  [radio {k}] {m.get('name') or 'gate'}" for k, m in enumerate(self.moongates) if k != i] + ["  [button 1] OKAY", "  [button 0] CANCEL"]
                p.gumps.append((f"0x{0x200 + len(p.gumps):08X}", self.new_item_serial(), "gate", lines))
                p.say_line("[GUMP] Moongate menu opened")
                return
        if not any(cheb(g["x"], g["y"], p.x, p.y) <= 1 for g in self.moongates):
            p.gate_at = None

    def gumpresponse(self, p, button, serial=None, switches=()):
        g = next((g for g in p.gumps if serial is None or g[1] == serial or g[0] == serial), None)
        if g is None:
            return ["No such gump"]
        p.gumps.remove(g)
        if g[2] == "gate":
            if button != 1 or not switches:
                return ["Gump closed"]
            k = int(switches[0])
            if not (0 <= k < len(self.moongates)):
                return ["No such destination"]
            m = self.moongates[k]
            self.stop_walk(p)
            p.x, p.y = int(m["x"]) + 1, int(m["y"]) + 1                 # beside the destination gate, not on it (as the shard lands you)
            p.gate_at = (int(m["x"]), int(m["y"]))
            p.say_line(f"[SYSTEM] You step through the moongate to {m.get('name')}.")
            self.events.append((self._now, "gate", p.name, m.get("name")))
            self.version += 1
            return [f"Moongate: {m.get('name')}"]
        if g[2] == "res":
            if button == 1 and p.ghost:
                p.ghost = False
                p.hp = max(10, p.max_hp // 10)
                p.war = False
                p.between_until = self._now + 600.0                      # Between Worlds: unseen by monsters until an action (attack, cast, a skill) or ten minutes
                p.system("You are between worlds: monsters cannot see you until you act.")
                p.system("You have been resurrected.")
                self.events.append((self._now, "res", p.name, ""))
            else:
                p.res_declined_near = self._now
        return [f"Gump button {button} pressed"]
