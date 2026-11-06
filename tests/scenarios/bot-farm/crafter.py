"""Crafters (Blacksmith, Carpenter, Tailor, Tinker): learn the legacy craft menu once, then make the item that teaches the most, sell what piles up,
buy more material, and bank the profit.

    python crafter.py --name BotSmithA --profession 16 --for 3600

The era's craft is a target-and-menu flow: double-click the tool, target the material, answer one to three menus; "make last" is the tool targeted at
itself. craft_data.json (make_craft_data.py) holds each item's skill window and cost from the server's definitions, which is how the bot picks what to make.
"""
from __future__ import annotations

import items  # noqa: E402  (the shared item table)
import argparse
import json
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from bot_common import BotBase  # noqa: E402
from wear import GATHER_ARMOR, GathererArmor  # noqa: E402  (light armour for working trades)
from hunter import HunterBot  # noqa: E402
from memory import cell_of  # noqa: E402
from miner import MinerBot  # noqa: E402
from uo import Event  # noqa: E402

DATA = json.load(open(os.path.join(HERE, "craft_data.json"), encoding="utf-8"))

# profession -> (craft key, skill name in the skills list, tool, material, material shop wanted, station tile or None, seller)
CRAFTS = {
    16: dict(craft="Blacksmith", skill="Blacksmithy", tool="tongs", mat="iron ingot", res="IronIngot", station_by="smith", shop_roles=("tinker",), wanted={"ingot": 60},
             sell_roles=("smith", "weaponsmith", "armorer"), maxcost=14),
    18: dict(craft="Tailoring", skill="Tailoring", tool="sewing kit", mat="cut cloth", res="Cloth", station_by=None, shop_roles=("tailor", "weaver"), wanted={"cut cloth": 120, "bolt of cloth": 500},
             sell_roles=("tailor", "weaver"), maxcost=20),
    # the Carpenter at 1430,1597 sells boards (3 gp) and buys the work; the Tinker the carpenters used to go to sells none
    17: dict(craft="Carpentry", skill="Carpentry", tool="saw", mat="board", mat_alt=("log",), res="Log", station_by=None, shop_roles=("carpenter",), wanted={"board": 60}, sell_roles=("carpenter",), maxcost=25),
    # 25: the dearest piece on the era menu, empty bookcase (DefCarpentry), as for the tailor; 15 left out every piece that teaches past 67 but the
    # wooden shield and ballot box (large crate 18, bench, throne and writing table 17, yew wood table 23)
    19: dict(craft="Tinkering", skill="Tinkering", tool="tool kit", tool_alt=("tinker's tools",), tool_buy="tinker's tools", mat="iron ingot", res="IronIngot", station_by=None, shop_roles=("tinker",), wanted={"ingot": 50},
             sell_roles=("tinker",), maxcost=10),
}
# where a broke crafter finds vermin for coins: the farms south-west of Britain, inside the town region (the shared memory's cows, chickens and rats)
# (the vermin ground is Places.earn_spots() now: seeds for a home that has them, else learned cells)
LEAF = re.compile(r"\((\d+) [^)]+\)\s*$")
UNIT_PRICE = {"cut cloth": 2, "cloth": 2, "iron ingot": 5, "board": 3, "log": 2, "leather": 6,    # the shard's vendor prices (CraftedGoodsPricing.MaterialPrices)
              "cut up leather": 3}       # a leather-mode tailor's leather: a hide at the Furtrader (SBFurtrader Hides 3) cuts into one (Hides.Scissor)
UNSOLD_VALID_FROM = 1793866639   # 2026-11-05 03:17: strikes from before this were names the sale did not match (a vendor's "tear kite shield" for the pack's
                                 # "kite shield", kept_word's "kit"), not refusals; before that, 2026-11-02 02:45: sales of 100+ entries the server dropped
BOLT_PRICE = 100          # a bolt of cloth at the Tailor and the Weaver (SBTailor, SBWeaver)
BOLT_WEIGHT = 5.0         # BoltOfCloth.DefaultWeight; it cuts into 50 cloth (BoltOfCloth.OnScissor)
BOLT_BATCH = 10           # bolts a trip at most: 500 cloth (CRAFTS[18] wanted "bolt of cloth" 500: at 100, two bolts a walk, 7 surcoats, 2026-11-02); a sold-out shelf doubles at the next hourly restock (GenericBuyInfo.OnRestock)
TRAIN_RESERVE = 1000      # below this (carried + banked) a crafter makes only what is expected to pay (patch_craft_profit)
TRIED = re.compile(r"You failed|You fail", re.I)   # a failed try's line (CraftItem 1044043 "You failed to create the item..."); with
                                                  # OUTCOME's create lines, the only replies that are a try
FAIL_LOSS = 0.5           # a failed craft consumes half the materials (ModernUO ConsumeType.Half)
FLOOR_MARGIN = 1.25       # a shop pays at least the materials x 1.25 for a crafted piece (CraftedGoodsPricing)
# material a craft gathers itself (carpenters chop, smiths and tinkers dig) is worth what a shop pays for it (SBInfo sell lists): the gold a craft gives up.
# Bought material (a tailor's cloth) costs what more of it costs, UNIT_PRICE. Charging chopped boards at 3 made every stool, chair and crate a loss for
# BotCarpBR (a 9-board stool sells for 23), and it stood idle (2026-10-30).
HELD_VALUE = {"board": 2, "log": 1, "iron ingot": 4}     # SBCarpenter 2/1, SBBlacksmith 4
RES_PRICE = {"Log": 2, "IronIngot": 5, "Cloth": 2, "Leather": 6}          # CraftedGoodsPricing.MaterialPrices by the craft's resource: the shard's floor
# ---- leather mode: a tailor past the cloth ladder -------------------------------------------------------------------------------------------------------
# The era's Tailoring menu (T2A TailoringMenu.cs, names as its FormatItemName gives them): targeting cloth offers ERA_CLOTH, targeting leather or hides
# offers ERA_LEATHER. In craft_data.json (DefTailoring) the cloth pieces top out at 78.9 (robe) and the leather and studded ones teach on to 119 (studded
# chest), so four tailors at 75-79 stopped gaining and made floppy hats for sale (2026-11-01). A UOR tailor there buys hides, cuts them with scissors and
# sews leather armour, which both teaches and sells (the Tanner buys it: SBTanner).
ERA_CLOTH = ("skull cap", "bandana", "floppy hat", "cap", "wide brim hat", "straw hat", "tall straw hat", "wizards hat", "bonnet", "feathered hat", "tricorne hat",
             "jester hat", "doublet", "shirt", "fancy shirt", "tunic", "surcoat", "plain dress", "short pants", "long pants", "kilt", "skirt", "cloak", "robe",
             "jester suit", "fancy dress", "body sash", "half apron", "full apron")
ERA_LEATHER = ("sandals", "shoes", "boots", "thigh boots", "leather chest", "leather gorget", "leather gloves", "leather cap", "leather arms", "leather legs",
               "studded chest", "studded gorget", "studded gloves", "studded arms", "studded legs", "female leather chest", "female studded chest",
               "leather bustier arms", "studded bustier arms", "leather shorts", "leather skirt")
# the menu's name -> the piece's name in the pack and on the Tanner's lists, where they differ (the item id's name: the Tanner's shelf at 1431,1612 in the
# shared memory, each matched to its SBTanner row by price under crafted-goods pricing, e.g. leather chest 12 leather -> 1.5 x 1.25 x 72 = 135 "leather tunic").
# "leather tunic" holds a KEEP word, so learn_made would never have learned it and the tunics would never have been carried to the Tanner.
LEATHER_PACK = {"leather chest": "leather tunic", "leather legs": "leather leggings", "leather arms": "leather sleeves", "studded chest": "studded tunic",
                "studded legs": "studded leggings", "studded arms": "studded sleeves", "female studded chest": "studded armor",
                "female leather chest": "female leather armor", "leather bustier arms": "leather bustier", "studded bustier arms": "studded bustier"}
# the leather-mode overrides, laid over a COPY of CRAFTS[18] (CRAFTS dicts are shared by every tailor and must never change). The pack calls leather
# "cut up leather" and hides "pile of hides" ("pil of hides" cut short: the farm's logs); hides are material too (CraftItem.m_TypesTable makes Hides count
# as Leather, and TailoringMenu opens the leather menu on either). Hides: Furtrader 3 gp x40 (SBFurtrader), Leatherworker 4 gp x999 (SBLeatherWorker);
# the Tanner sells leather itself, "cut leather" 6 gp x20 (SBTanner; its shelf name in the shared memory). The Tanner buys the armour (SBTanner sell list,
# raised to 1.25 x 6 gold a leather by CraftedGoodsPricing), the Cobbler the footwear (SBCobbler). The sewing kit and scissors stay the Tailor's (SBTailor).
LEATHER = dict(mat="cut up leather", mat_alt=("hide",), res="Leather", shop_roles=("furtrader", "leatherworker"), tool_roles=("tailor", "weaver"),
               wanted={"hide": 40}, sell_roles=("tanner", "cobbler"), maxcost=14)    # 14: the dearest piece on the era menu, studded chest (DefTailoring)
LEATHER_LOW = 28          # restock under two studded chests' worth (14 leather each, DefTailoring)
LEATHER_BATCH = 999       # leather and hides held after a restock at most: the shelf's ceiling. SBFurtrader starts at 40 hides, but a sold-out shelf doubles
                          # at each hourly restock up to 999 (GenericBuyInfo.OnRestock), so weight (leather_room) and gold are the real limits: at 40 a
                          # restock was 5 leather shorts, 10 s of sewing, and BotFairTailorVR bought 40, 40 and 36 hides at one shop in 7 minutes (2026-11-02)
TANNER_LEATHER = "of leather"   # the Tanner's shelf line is "Pieces Of Leather" (SBTanner Leather 6 gp): the key "cut leather" matched nothing, and with the
                                # Furtrader's hides sold out BotTailAdvR made nothing for 36 minutes beside it (2026-11-02 08:36-09:12). "of leather" is not
                                # in the pack's "cut up leather", so the pack is still not counted against the purchase
LEATHER_SHELF = 6         # the Tanner's leather, the fallback when no hides are left (SBTanner Leather 6)
TEACH_CHANCE = 0.45       # choose()'s own floor: a piece made at under 45% is not picked to train on
OUTCOME = re.compile(r"You create|You failed|You fail|You make|You have worn|wore out|enough|too heavy|cannot|must|not have|put .* in|exceptional", re.I)


from market import CrafterDemand, CrafterMarket  # noqa: E402
from colours import ColourSmith  # noqa: E402  (coloured armour for the fighters; feature colour_craft)
from earn import EarnMixin  # noqa: E402  (shared with the broke miner)


def sernum(s):
    """A serial as a number, from 0x4007... or an int; None when it is neither."""
    try:
        return int(s, 16) if isinstance(s, str) and s.lower().startswith("0x") else int(s)
    except (TypeError, ValueError):
        return None


def kept_word(n, keep):
    """A KEEP word in the name as a whole word (a plural allowed): "kit" is a tool kit or a sewing kit, never a kite shield. As a substring it kept
    BotSmithBR's 37 wooden kite shields out of every sale and the bank (185 stones; idle 72% of an hour, 2026-11-05 01:12-02:12). A module function:
    minersmith borrows is_product and learn_made onto a MinerBot, which has no kept_word method."""
    return any(re.search(r"\b" + re.escape(w) + r"(s|es)?\b", n) for w in keep)


class CrafterBot(ColourSmith, EarnMixin, CrafterDemand, CrafterMarket, HunterBot):
    TASK_CORE = False                                     # the decision core (task_core.py) is the hunter's until the crafter has its own task set
    HOME_DANGER_MOVES = True                              # a home that keeps killing it is left (patch_home_town)
    RULES = ["r_dead", "r_corpse", "r_gear", "r_cure", "r_flee", "r_hide", "r_avoid", "r_heal", "r_market", "r_bank", "r_retool", "r_upgrade", "r_cut", "r_sell", "r_chop", "r_cures", "r_restock", "r_colour", "r_craft", "r_smelt", "r_dig", "r_earn",
             "r_wander"]
    LOOT_MATERIALS = True
    LOOT_GEAR = ()                                        # a crafter hunting vermin for coins does not carry weapons home to sell
    CARVE = False
    pickaxe = MinerBot.pick                               # a smith or tinker who has Mining digs its own ore when the shops are sold out (pick() answers menus)
    stand_near = MinerBot.stand_near
    mountains = MinerBot.mountains                        # r_dig runs MinerBot.r_mine on a crafter, which asks self.mountains()
    far_spot_ok = MinerBot.far_spot_ok
    far_cands = MinerBot.far_cands
    horse_unsafe = MinerBot.horse_unsafe                  # MinerBot.r_mine asks it when a pack horse is kept (test_borrow_calls)
    FAR_PLANS, FAR_FOUND = MinerBot.FAR_PLANS, MinerBot.FAR_FOUND

    # a crafter keeps tools and material, not what it makes: products go to the buyer, or into the bank when nobody buys them
    KEEP = ("book", "gold", "candle", "bag", "scroll", "potion", "recall", "scissors", "bedroll", "kindling", "bandage", "tongs", "tool", "ingot", "cloth", "leather",
            "hide", "board", "log", "hatchet", "saw", "hammer", "sewing", "dagger", "pickaxe", "shovel", "gears", "hinge", "springs", "kit", "ore", "feather", "shaft", "arrow") + items.GOODS_WORDS          # goods a shop buys are never banked (items.py)

    def shop_xys(self):
        """The material shops by role, nearest first (the shared memory's learned shops are tried before these by r_restock)."""
        return self.find_places(self.cfg["shop_roles"], n=3, per=2) or [self.home_centre()]

    def tool_shop_xy(self):
        """Where the craft's tool is sold: the material shop, except in leather mode (the Furtrader sells hides, the sewing kit is the Tailor's)."""
        roles = self.cfg.get("tool_roles")
        found = self.find_places(roles, n=1, per=1) if roles else []
        return found[0] if found else self.shop_xys()[0]

    def buyer_xy(self):
        roles = self.cfg["sell_roles"]
        if self.leather_on() and not any(self.leather_good(i.name) for i in self.products()):
            roles = CRAFTS[18]["sell_roles"]               # only pieces from the cloth days left: they go to the Tailor, not the Tanner
        return self.where1(roles)

    def at_station(self, st):
        """An anvil and a forge each within 2 tiles (DefBlacksmithy.CheckAnvilAndForge, range 2), by the gazetteer; without it, on the station tile or
        beside it. "Within 2 of the station" (the midpoint between them) let BotSmithAR stand at 1344,1777, 3 tiles from the anvil at 1346,1774: every
        craft "nomenu", once a minute for an hour (2026-11-02)."""
        x, y = self.c.x, self.c.y
        try:
            import gazetteer as gz
            def near(kind):
                return any(max(abs(p["x"] - x), abs(p["y"] - y)) <= 2 for p in gz.near(kind, x, y, n=3, same_side=True))
            return near("anvil") and near("forge")
        except Exception:
            return abs(x - st[0]) <= 1 and abs(y - st[1]) <= 1

    def station_xy(self):
        by = self.cfg.get("station_by")
        return self.station_near(by) if by else None

    def __init__(self, name, profession):
        super().__init__(name, profession)
        self.cfg = CRAFTS[profession]
        self.items = DATA[self.cfg["craft"]]
        self.menu_map_path = os.path.join(self.dir, "menu_map.json")
        self.menu_map = {}
        self.menu_map_backup = {}
        try:
            self.menu_map = json.load(open(self.menu_map_path, encoding="utf-8"))
        except (OSError, ValueError):
            pass
        self.made = 0
        self.fails = 0
        self.sold_for = 0
        self.skill = 0.0
        self.last_made = None
        self.bad_items = set()
        # what the crafts really produce, by the name the item has in the pack: the menu's "wooden chair" is a plain "chair" once made, and a
        # Carpenter walked away from a vendor paying 38 gp a chair because the craft list had no "chair"
        self.made_names_path = os.path.join(self.dir, "made_names.json")
        try:
            self.made_names = set(json.load(open(self.made_names_path, encoding="utf-8")))
        except (OSError, ValueError):
            self.made_names = set()
        # and which menu item became which: the menu's "dart board south deed" is a plain "deed" in the pack, so a shop's refusal of "deed"
        # has to reach the menu item, or the carpenter keeps making what nobody buys
        self.made_as_path = os.path.join(self.dir, "made_as.json")
        try:
            self.made_as = json.load(open(self.made_as_path, encoding="utf-8"))
        except (OSError, ValueError):
            self.made_as = {}
        self.i = 0                                        # MinerBot's mountain rotation, for r_dig
        self.spot = None                                  # MinerBot's chosen mountain spot, for r_dig
        self.blocked = {}
        self.dug = 0
        self.bad_buyers_path = os.path.join(self.dir, "bad_buyers.json")
        try:
            self.facts["bad_buyers"] = json.load(open(self.bad_buyers_path, encoding="utf-8"))
        except (OSError, ValueError):
            self.facts["bad_buyers"] = {}
        if self.facts.get("leather_mode") and self.cfg.get("craft") == "Tailoring":
            self.enter_leather(None)                        # a restarted brain keeps sewing leather (facts leather_mode is in PERSIST)

    # ---- leather mode (a tailor past the cloth ladder) ------------------------------------------------------------------------------

    def leather_on(self):
        return (getattr(self, "cfg", None) or {}).get("res") == "Leather" and self.cfg.get("craft") == "Tailoring"

    @staticmethod
    def leather_good(name):
        """A leather or studded piece (or footwear) of the era menu, by its menu name or its name in the pack."""
        n = (name or "").strip().lower()
        return n in ERA_LEATHER or n in LEATHER_PACK.values()

    def teaches(self, names, skill):
        """The first of these menu items in choose()'s window at this skill (the chance at least TEACH_CHANCE, the skill under the item's max), else None."""
        for name in names:
            it = self.items.get(name)
            if it and it["max"] > skill and self.chance(it, skill) >= TEACH_CHANCE:
                return name
        return None

    def leather_check(self):
        """A tailor switches to leather once no cloth piece of the era menu is in its window and some leather piece is. The whole era list (ERA_CLOTH), not
        the learned menu: the menu lists only what the pack's cloth allows, so 15 cloth would hide the robe (16 cloth, teaching to 78.9) and switch early."""
        if self.cfg.get("craft") != "Tailoring" or self.leather_on() or not self.skill:
            return False
        if self.teaches(ERA_CLOTH, self.skill):
            return False
        lea = self.teaches(ERA_LEATHER, self.skill)
        if not lea:
            return False
        self.enter_leather(f"no cloth piece of the era menu teaches at {self.skill:.1f}; {lea} does")
        return True

    def enter_leather(self, why):
        """Leather mode: the material, shops and buyers of LEATHER on a copy of the cfg, the leather menu learned on its own (menu_map_leather.json: the
        cloth menu's paths start at "Build Hats", the leather menu's at "Build Leather Armor"). why None: a restart taking it over, nothing logged."""
        self.cfg = dict(self.cfg, **LEATHER)               # a copy: CRAFTS[18] is shared by every tailor and must not change
        self.menu_map_path = os.path.join(self.dir, "menu_map_leather.json")
        try:
            self.menu_map = json.load(open(self.menu_map_path, encoding="utf-8"))
        except (OSError, ValueError):
            self.menu_map = {}
        self.menu_map_backup = {}                          # the cloth menu is no fallback for leather
        self.__dict__.pop("explored_at", None)
        self.__dict__.pop("_squashed", None)
        self.bad_items.clear()
        self.last_made = None                              # "make last" would sew the last cloth piece again
        self.facts.pop("menu_empty_until", None)
        self.facts["stocked_at"] = 0
        if why is None:
            return
        self.facts.pop("soldout_until", None)              # a bare cloth shelf says nothing about hides
        self.facts["leather_mode"] = {"t": round(time.time()), "skill": round(self.skill, 1)}
        self.log(f"leather mode: {why}; buying hides and cutting them into leather from now on")
        self.ev("leather_mode", skill=round(self.skill, 1))
        self.dlog("choice", what="switch to leather", why=why)
        self.note("craft", f"A tailor at {self.skill:.0f} gains nothing more from cloth: the era menu's cloth pieces stop teaching at 78.9 and only leather and "
                           "studded armour teach on; the menu shows the leather pieces only when leather or hides are targeted.", key="leathermode")

    def leather_held(self):
        return sum((i.amount or 1) for i in self.c.backpack if self.matname("cut up leather", i.name or ""))

    def hides_held(self):
        return sum((i.amount or 1) for i in self.c.backpack if items.is_hide(i.name))

    SCISSORS_GAP = 600        # s between walks to buy scissors

    def have_scissors(self):
        """The scissors in the pack; none: the Tailor sells them (SBTailor Scissors 11), tried once in SCISSORS_GAP. None when there are still none."""
        sc = self.c.find("scissors")
        if sc is None:
            if time.time() - self.facts.get("scissors_at", 0) < self.SCISSORS_GAP or self.c.gold < 20:
                return None
            self.facts["scissors_at"] = time.time()
            self.activity = "buying scissors"
            self.shop_at(self.tool_shop_xy(), {"scissors": 1}, budget=min(30, max(0, self.c.gold - 5)))
            sc = self.c.find("scissors")
        return sc

    def cut_hides(self):
        """Scissors on every pile of hides: one leather a hide, the whole pile at once (Hides.Scissor, Item.ScissorHelper), 5 stones down to 1 (Hides.cs,
        Leathers.cs DefaultWeight). No scissors: the Tailor sells them (SBTailor Scissors 11), tried once in SCISSORS_GAP. Returns the leather made, or
        None with no scissors."""
        sc = self.have_scissors()
        if sc is None:
            return None
        before = self.leather_held()
        self.activity = "cutting hides into leather"
        for _ in range(6):
            pile = next((i for i in self.c.backpack if items.is_hide(i.name)), None)
            if pile is None:
                break
            self.c.events.drain()
            self.c.use(sc.serial)
            if self.c.wait_for(Event.TARGET_REQUEST, timeout=4) is None:
                break
            self.c.target(pile.serial)
            time.sleep(1.2)
            for l in self.read_journal():
                self.note("craft", f"Cutting hides with scissors says: {l[:100]}", key="cuthidemsg")
        made = self.leather_held() - before
        if made:
            self.log(f"cut hides into {made} leather")
            self.ev("cut_hides", leather=made)
        return made

    def leather_shops(self, word, roles):
        """Shops for hides or leather: those seen with it on the shelf, cheapest first (the shared memory), then the gazetteer's by role, nearest first."""
        shops = []
        for price, xy, item, qty in self.mem.vendor_selling(word):
            xy = tuple(int(v) for v in xy.split(","))
            if price > 0 and xy not in shops:
                shops.append(xy)
        for xy in self.find_places(roles, n=3, per=2):
            if all(max(abs(xy[0] - s[0]), abs(xy[1] - s[1])) > 2 for s in shops):
                shops.append(tuple(xy))
        return shops[:3]

    def leather_room(self, per):
        """Pieces of `per` stones that fit under CRAFT_WEIGHT (the restock_wanted rule)."""
        return max(0, int((self.c.max_weight * self.CRAFT_WEIGHT - self.c.weight - 5) // per))

    def leather_restock(self):
        """Leather mode's r_restock: hides from the Furtrader (cut at once, so the next buy fits: a hide 5 stones, its leather 1), up to LEATHER_BATCH
        leather and hides in all; when no shop has hides, the Tanner's leather. Shelves seen bare are left alone until soldout_until (20 minutes)."""
        if time.time() < self.facts.get("soldout_until", 0):
            return False
        self.mark_stocked()
        self.activity = "buying hides"
        if self.c.gold < self.purse_floor() and self.facts.get("bank_balance", 0) >= self.purse_floor():
            self.visit_bank("poor", withdraw=self.purse_fill())
        if self.c.gold < 40:
            self.note("money", f"The {self.pname} has run out of leather and money at once; there is no way to see the shortfall coming.", key="broke")
            return False
        got, opened = {}, False
        for shop in self.leather_shops("hide", self.cfg["shop_roles"]):
            for _ in range(5):                                   # buy what fits, cut it, buy again while the shelf and the purse last (5 cuts reach CRAFT_WEIGHT)
                n = min(LEATHER_BATCH - self.leather_held() - self.hides_held(), self.leather_room(items.unit_weight("hides")))
                if n <= 0:
                    break
                g = self.shop_at(shop, {"hide": self.hides_held() + n}, budget=max(0, self.c.gold - 40))    # shop_at counts the hides carried
                opened = opened or bool(self.facts.get("shop_list_opened"))
                if not g:
                    break
                for k, v in g.items():
                    got[k] = got.get(k, 0) + v
                if not self.cut_hides():
                    break                                        # no scissors: the hides are sewn as they are (CraftItem.m_TypesTable)
            if got and self.leather_held() + self.hides_held() >= self.restock_need():
                break                                            # still short: the next Furtrader, as a player whose shop ran out walks on (BotFairTailorVR
                                                                 # got the 20 hides one shelf had and stood 3 minutes on 20 leather, 2026-11-02)
        if not got:
            for shop in self.leather_shops(TANNER_LEATHER, ("tanner",)):
                n = min(LEATHER_BATCH - self.leather_held() - self.hides_held(), self.leather_room(items.unit_weight("cut up leather")),
                        max(0, self.c.gold - 40) // LEATHER_SHELF)
                if n <= 0:
                    break
                got = self.shop_at(shop, {TANNER_LEATHER: n}, budget=max(0, self.c.gold - 40))    # the pack's "cut up leather" is not counted by that key
                opened = opened or bool(self.facts.get("shop_list_opened"))
                if got:
                    break
        if not got and self.far_pending():
            return True                                  # a far walk under way, or not worth it: that is no bare shelf
        if not got:
            self.facts["soldout_until"] = time.time() + (1200 if opened else 180)
            self.note("shop", "No shop had hides or leather left for the tailor.", key="soldout:hides")
            if opened:
                # the hunter-tailor of the era (Tailoring, Swordsmanship, Tactics, Anatomy, Healing, Tracking: docs/Bot-Farm-Skill-Plans.md) kills and
                # carves its own hides while the shops restock: BotFairTailorVR wandered 16 minutes "under 5 cut up leather" (2026-11-01). r_earn hunts
                # with the hunter's rules while stall_earn_until holds, for the same 20 minutes the shelves are left alone
                self.facts["stall_earn_until"] = self.facts["soldout_until"]
                self.ev("leather_hunt", until=round(self.facts["soldout_until"]))
        else:
            self.log(f"restock: bought {got}; {self.leather_held()} leather and {self.hides_held()} hides in the pack")
            self.restock_filled()
        return True

    def restock_need(self):
        """Material under which r_restock buys more (and bank_material_out's unit)."""
        if self.leather_on():
            return LEATHER_LOW
        return 40 if self.cfg["craft"] != "Tailoring" else 60

    # ---- the menu -------------------------------------------------------------------------------------------

    def tool(self):
        names = (self.cfg["tool"],) + tuple(self.cfg.get("tool_alt", ()))
        for _ in range(2):
            for n in names:
                t = self.c.find(n)
                if t is not None:
                    return t
            self.c.open_backpack()
        return None

    @staticmethod
    def matname(w, name):
        """A material word against an item name: "=cloth" means exactly "cloth" (uncut cloth, not a bolt of cloth); any other word is a part of the name."""
        n = name.strip().lower()
        if w in ("board", "log"):
            # the whole name: "game board" and "backgammon board" are a carpenter's products, and as boards they made BotCarpAR count 50 boards it did
            # not have, so it never chopped, never bought and never crafted for an hour (2026-10-30)
            return n in (w, w + "s")
        return n == w[1:] if w.startswith("=") else w in n

    @staticmethod
    def plain(i):
        """An ingot of plain iron. The client calls every ingot "iron ingot"; a coloured one (hue 0x973 is dull copper) needs more skill, and once it
        is the selected metal the smithing menu offers only Repair and Smelt (two smiths looped on that menu for hours)."""
        return "ingot" not in i.name.lower() or not i.hue

    def material(self):
        """The stack to target: the first material name with a stack big enough for the item being made (self._need), else the largest of any name
        (the first-name rule picked 9 cut cloth over 111 uncut cloth, and every 12-cloth craft failed)."""
        need = getattr(self, "_need", None) or 1
        hue = self.__dict__.get("_colour_hue") or self.__dict__.get("_spend_hue")      # (colour_spend: the coloured metal this craft is made of)
        if hue:
            # a coloured piece (colours.r_colour): the stack of that metal, which the smithing menu then works (BlacksmithMenu: the resource targeted)
            stacks = [i for i in self.c.backpack if int(getattr(i, "hue", 0) or 0) == hue and "ingot" in (i.name or "").lower() and (i.amount or 1) >= need]
            return max(stacks, key=lambda i: i.amount or 1) if stacks else None
        biggest = None
        for n in (self.cfg["mat"],) + tuple(self.cfg.get("mat_alt", ())):
            stacks = [i for i in self.c.backpack if self.matname(n, i.name) and self.plain(i)]
            if stacks:
                top = max(stacks, key=lambda i: i.amount or 1)
                if (top.amount or 1) >= need:
                    return top
                if biggest is None or (top.amount or 1) > (biggest.amount or 1):
                    biggest = top
        return biggest

    def count(self, word):
        words = (word,) + tuple(self.cfg.get("mat_alt", ())) if word == self.cfg["mat"] else (word,)
        spend = self.__dict__.get("_spend_hue") if word == self.cfg["mat"] else None
        return sum((i.amount or 1) for i in self.c.backpack if any(self.matname(w, i.name) for w in words)
                   and (self.plain(i) or (spend and int(getattr(i, "hue", 0) or 0) == spend)))

    def spend_hue(self):
        """Feature colour_spend: the hue of the coloured ingots a smith out of iron makes its products from (the least valuable metal its Blacksmithy can work,
        the biggest stack of it), or None. With colour_craft on, COLOUR_TAKE of each metal stays for the fighters' armour."""
        if not self.feature("colour_spend") or self.cfg.get("craft") != "Blacksmith":
            return None
        keep = self.COLOUR_TAKE if self.colour_on() else 0
        best = None
        for bonus, hue, metal, stack in self.colour_metals():
            if (stack.amount or 1) - keep < 5:
                continue
            key = (bonus, -(stack.amount or 1))
            if best is None or key < best[0]:
                best = (key, hue, metal)
        return (best[1], best[2]) if best else None

    def open_menu(self):
        """Tool, then the material: the era's first menu."""
        self.c.open_backpack()
        t, mat = self.tool(), self.material()
        if not t or not mat:
            return None
        self.c.events.drain()
        self.c.use(t.serial)
        if self.c.wait_for(Event.TARGET_REQUEST, timeout=4) is None:
            return None
        self.c.target(mat.serial)
        return self.read_menu()

    def pick(self, menu, index):
        try:
            self.c.call(f"menuresponse {menu[0]} {menu[1]} {index}", timeout=8)
        except Exception as e:
            self.log(f"menu answer refused: {str(e)[-90:]}")
            return None
        return self.read_menu()

    def explore(self):
        """Walk the whole menu tree once and keep it: {item name: [option texts to press]}."""
        self.close_menus()
        found = {}
        todo = [[]]
        seen_paths = 0
        while todo and seen_paths < 60:
            path = todo.pop(0)
            seen_paths += 1
            menu = self.open_menu()
            for text in path:
                if not menu:
                    break
                idx = self.index_of(menu, text)
                if not idx:
                    self.close_menus([menu])
                    menu = None
                    break
                menu = self.pick(menu, idx)
            if not menu:
                continue
            opts = menu[2]
            if opts and all(LEAF.search(t) for _, t in opts):
                for i, t in opts:
                    found[LEAF.sub("", t).strip().lower()] = path + [t]
            else:
                for i, t in opts:
                    if not path and t.lower() in ("repair", "smelt", "repair item", "make last"):
                        continue
                    todo.append(path + [t])
            try:
                self.c.call("menuresponse %s %s 0" % (menu[0], menu[1]), timeout=8)       # close it without choosing
            except Exception:
                pass
        if not found and self.menu_map_backup:
            found = self.menu_map_backup                # an empty menu means too little material, not that nothing can be made
        self.menu_map = found
        self.explored_at = (time.time(), self.skill)
        json.dump(found, open(self.menu_map_path, "w"), indent=1)
        self.log(f"learned the craft menu: {len(found)} items")
        if found:
            self.note("craft", f"The {self.cfg['craft']} menu lists only what the character can make now ({len(found)} items at skill {self.skill:.0f}); it never says how hard an item is.", key="menusize")
        return found

    # ---- choosing --------------------------------------------------------------------------------------------

    def chance(self, it, skill):
        lo, hi = it["min"], it["max"]
        return 1.0 if skill >= hi else 0.0 if skill < lo else (skill - lo) / (hi - lo)

    def may_train(self):
        """Enough gold to spend some on skill at a loss (patch_craft_profit)."""
        return self.c.gold + self.facts.get("bank_balance", 0) >= TRAIN_RESERVE

    def craft_ev(self, name, amount, ch):
        """Expected gold per craft: chance x price - materials used (all on a success, half on a failure); None when every shop refused the piece."""
        unit = HELD_VALUE.get(self.cfg["mat"], UNIT_PRICE.get(self.cfg["mat"], 3))
        price = self.sale_price(name)
        if price == 0:
            return None
        if price is None:
            price = -(-FLOOR_MARGIN * RES_PRICE.get(self.cfg["res"], UNIT_PRICE.get(self.cfg["mat"], 3)) * amount // 1)       # no shop asked yet: the shard's floor
        return ch * price - unit * amount * (ch + FAIL_LOSS * (1 - ch))

    # armour as a working player wears it (wear.py, feature gather_armor): light leather and studded, not the fighters' metal (ore, logs and cloth are
    # carried weight); a crafter's dagger is no "weapon first" reason to go without (HunterBot.r_upgrade asks weapon_state, for this call only)
    ARMOR_BUY = GATHER_ARMOR
    SHOP_FROM = GathererArmor.SHOP_FROM
    ERRAND_PIECES = GathererArmor.ERRAND_PIECES
    armor_errand = GathererArmor.armor_errand
    in_town_now = GathererArmor.in_town_now

    def r_upgrade(self):
        if not self.feature("gather_armor"):
            return False
        self.__dict__["weapon_state"] = lambda: "ok"
        try:
            return GathererArmor.r_upgrade(self)          # in town, real threats only (wear.py)
        finally:
            self.__dict__.pop("weapon_state", None)

    OWN_ORE_MINING = 50       # Mining enough to dig and smelt iron for itself (Mining.cs: iron from 0, smelting iron needs no more)
    OWN_ORE_FOR = 900         # s the shelves are passed by once training is on its own ore

    def trains_on_own_ore(self):
        """A veteran smith or tinker that can mine and has money to train with digs its own ore instead of buying ingots, as a player with the Mining for it
        does. A piece sells for 1.25 x its material (CraftedGoodsPricing) and a failure loses half the material, so a craft from ingots bought at 5 pays
        only at 2-in-3 success or better (3.75 x chance - 2.5 gold an ingot); the pieces that teach sit nearer 50%. BotSmithAR spent 10,850 gold on ingots
        and sold for about 9,200; BotTinkAR spent 12,465 (2026-10-31), both with Mining 89-92. Money is no condition: dug ore costs nothing, and a smith
        short of gold is the one a player sends to the hills. With may_train as a condition BotSmithAR (299 gold, Mining 91) bought the few ingots it could
        afford, dug only when the shelf was bare, and smelted one ore at a time between shop walks (2026-11-01)."""
        if getattr(self, "mode", None) != "veteran" or not self.can_gather():
            return False
        # a carpenter the same with its own wood (r_chop): boards bought at 3 make pieces that sell at 1.25 x 3, a loss at the skill's edge; BotCarpAdvR,
        # Lumberjacking 100 and 54,745 gold, bought the shelf's few boards and stood idle 5 of 13 minutes waiting for more (2026-10-31)
        gather = "Mining" if self.cfg.get("res") == "IronIngot" else "Lumberjacking" if self.cfg.get("craft") == "Carpentry" else None
        if gather is None or self.skill_values.get(gather, 0) < self.OWN_ORE_MINING:
            return False
        if time.time() >= self.facts.get("soldout_until", 0):
            self.facts["soldout_until"] = time.time() + self.OWN_ORE_FOR      # r_dig's own test: no shop to look at first
            self.log(f"material: training on its own {'ore' if gather == 'Mining' else 'wood'} ({gather} {self.skill_values.get(gather, 0):.0f}); bought material loses on pieces made at the skill's edge")
            self.ev("own_ore", skill=gather, value=round(self.skill_values.get(gather, 0), 1))
        return True

    def short_of_money(self):
        return self.c.gold + self.facts.get("bank_balance", 0) < 250

    def sale_price(self, name):
        """The best price a shop has been seen to pay for this item; 0 if every shop that was offered it refused; None if no shop has been asked."""
        names = {name.lower()} | set(self.made_as.get(name, ()))      # the menu's name and the name it has in the pack
        if name.lower() in LEATHER_PACK:
            names.add(LEATHER_PACK[name.lower()])                     # known before the first one is made: "leather chest" is a "leather tunic"
        offers = [p for n in names for p, xy, item in self.mem.vendor_buying(n) if item == n]
        if not offers:
            return None
        return max(offers)

    def choose_naive(self, refused_ok=False):
        """A new crafter does not know the skill windows. It sees the menu and each item's cost, and learns from its own tries (shared among newbie
        crafters of its trade): an item that keeps coming out exceptional, or has taught nothing in eight tries, is too easy now; one never made in six
        tries is too hard. Untried items are guessed at optimistically, dearer ones more so (they are usually the harder pieces), so it climbs the menu
        the way a player does instead of working through the cheap end one item at a time (it used to rank by gain per cloth, which favoured caps)."""
        have = self.count(self.cfg["mat"])
        options = []
        for name, path in self.menu_map.items():
            m = re.search(r"\((\d+) ", path[-1])
            cost = int(m.group(1)) if m else 1
            if cost <= have and cost <= self.cfg["maxcost"] and name not in self.bad_items:
                options.append((cost, name))
        if not options:
            return None
        top = max(c for c, _ in options)
        best = fallback = None
        short = self.short_of_money()
        for cost, name in options:
            price = self.sale_price(name)
            if price == 0 and not refused_ok:
                continue                                  # every shop asked refused it: a crafter trains on what it can sell
            price = price if short else None
            # the tries at this skill (memory.CRAFT_BAND), as a player goes by what teaches now: the lifetime record counted gains from 20 points down
            try:
                seen = self.mem.craft_stats(self.cfg["craft"], name, self.skill)
            except TypeError:
                seen = self.mem.craft_stats(self.cfg["craft"], name)          # a memory without the skill bands (a test's or the simulator's)
            seen = seen or {"n": 0, "ok": 0, "gain": 0, "exc": 0}
            pick = (name, {"min": 0, "max": 100, "amount": cost, "resource": self.cfg["res"]}, (seen["ok"] + 1) / (seen["n"] + 2))
            if seen["n"] >= 6 and seen["ok"] == 0:
                continue                                  # never made one in six tries: too hard for now
            ev = self.craft_ev(name, cost, pick[2])
            if not self.may_train() and (ev is None or ev < 0):
                continue                                  # below the reserve: nothing that is expected to lose material (patch_craft_profit)
            if fallback is None or cost > fallback[0]:
                fallback = (cost, *pick)
            if seen.get("exc", 0) >= 2 or (seen["n"] >= 8 and seen["gain"] == 0):
                continue                                  # comes out exceptional, or teaches nothing: too easy now
            prior = 0.3 + 0.7 * cost / top
            value = (seen["gain"] + prior) / (seen["n"] + 1) / cost ** 0.3
            if price:
                value *= 2
            if not self.may_train():
                value = ev / cost + 0.01 * value             # below the reserve: profit per unit of material first, then what it teaches                                # broke: a piece a shop is known to buy comes first
            if best is None or value > best[0]:
                best = (value, *pick)
        if best is None and not refused_ok:
            # nothing sellable teaches now: a piece no shop buys that still teaches comes before a sellable one that cannot (BotCarpBR made wooden boxes at
            # Carpentry 70 while wooden shields taught it 12 times in 45 tries)
            again = self.choose_naive(refused_ok=True)
            if again is not None and (fallback is None or again[0] > 0):
                return again
        if best is None and fallback is not None:
            return (0.0, *fallback[1:])                   # everything looks too easy: the dearest piece it can still make
        if best is None:
            return self.choose_income_naive(have)
        return best

    def choose_income_naive(self, have):
        """A newbie with nothing to train on (or nothing it can afford to fail at): the menu piece expected to pay most per unit of material, by its own
        success record ((ok + 1) / (n + 2)), up to what the pack holds. choose() had this fallback and choose_naive had none: BotCarpBR, Carpentry 67.8 and
        55 boards, stood 98% of a run on "nothing makeable and challenging" (2026-10-30)."""
        opts = []
        for name, path in self.menu_map.items():
            m = re.search(r"\((\d+) ", path[-1])
            cost = int(m.group(1)) if m else 1
            if cost > have or name in self.bad_items or self.sale_price(name) == 0:
                continue
            seen = self.mem.craft_stats(self.cfg["craft"], name) or {"n": 0, "ok": 0}
            ch = (seen["ok"] + 1) / (seen["n"] + 2)
            ev = self.craft_ev(name, cost, ch)
            if ev is not None and ev > 0:
                opts.append((ev / cost, cost, name, ch))
        if not opts:
            return None
        score, cost, name, ch = max(opts)
        self.log(f"nothing to train on: making {name} for sale ({ch:.0%} by its record, {score:.2f} gold a unit expected)")
        return (score, name, {"min": 0, "max": 100, "amount": cost, "resource": self.cfg["res"]}, ch)

    def choose(self, refused_ok=False, relax=False):
        if not (refused_ok or relax) and self.leather_check():
            return None                                   # just switched to leather: the leather menu is learned first (r_craft, next tick)
        demand = self.demand_pick()                      # a piece a fighter wants comes first (market.py)
        if demand:
            return demand
        if self.mode == "newbie":
            return self.choose_naive()
        have = self.count(self.cfg["mat"])
        short = self.short_of_money()
        best = None
        for name, path in self.menu_map.items():
            it = self.items.get(name)
            if not it or name in self.bad_items or it["resource"] != self.cfg["res"] or it["amount"] > have or it["amount"] > self.cfg["maxcost"] * (3 if relax else 1):
                continue
            ch = self.chance(it, self.skill)
            if ch >= 1.0 and it["min"] < self.skill - 30:
                continue
            if ch < 0.45 or it["max"] <= self.skill:
                continue
            price = self.sale_price(name)
            if price == 0 and not refused_ok:
                continue                                  # every shop asked refused it (a deed): a crafter trains on what it can sell
            price = price if short else None
            seen = self.mem.craft_stats(self.cfg["craft"], name)
            if seen and seen["n"] >= 8:
                # what bots of this craft have actually got out of it: skill gains per unit of material, to rank the items. The success chance stays the
                # engine's own for this skill ((skill - min) / (max - min) over the item's window, CraftItem): the shared record mixes every skill, and its
                # 20% over 1,279 robe tries, mostly by tailors below 60, dropped the robe for BotTailAdvR at 66.8 (52%), the only cloth piece still
                # teaching there, so it sewed floppy hats and skull caps that teach nothing (2026-11-02)
                key = (round((seen["gain"] / seen["n"]) / it["amount"], 4), it["min"])
            else:
                key = (0.15 / it["amount"] if seen is None or seen["n"] < 8 else 0, it["min"])          # untried items get a fair chance
            # broke: what a shop buys comes first, the best price per unit of material; otherwise skill gain per unit of material
            key = ((1, round(price / it["amount"], 3)) if price else (0, 0)) + key
            if not self.may_train():
                ev = self.craft_ev(name, it["amount"], ch)
                if ev is None or ev < 0:
                    continue                              # below the reserve: nothing that is expected to lose material (patch_craft_profit)
                key = (1, round(ev / it["amount"], 3)) + key[2:]
            if best is None or key > best[0]:
                best = (key, name, it, ch)
        if best is None and not refused_ok:
            return self.choose(refused_ok=True, relax=relax)           # nothing sellable in the window: train on what there is
        if best is None and not relax:
            return self.choose(refused_ok=refused_ok, relax=True)     # past the cheap items: dearer ones that still teach (up to 3x the cost cap)
        if best is None and relax and refused_ok:
            return self.choose_income()                   # nothing teaches: make what sells (patch_craft_income.py)
        return best

    def choose_income(self):
        """Nothing in the menu teaches: the item that sells best per unit of material, among those a shop pays for and made at 50%+."""
        have = self.count(self.cfg["mat"])
        opts = []
        for name in self.menu_map:
            it = self.items.get(name)
            if not it or name in self.bad_items or it["resource"] != self.cfg["res"] or it["amount"] > have:
                continue
            price = self.sale_price(name)
            if price == 0:
                continue                                  # every shop asked refused it
            # (a price never asked is the shard's floor in craft_ev: each craft's shop buys that craft's goods, extraVendorBuyers; skipping the unasked left
            # BotCarpBR, Carpentry 67.8 with 55 boards and nothing in its window on the era menu, idle 98% of a run, 2026-10-30)
            ch = self.chance(it, self.skill)
            ev = self.craft_ev(name, it["amount"], ch)
            if ev is None or ev <= 0:
                continue                                  # what is expected to pay, failures counted (patch_craft_profit)
            opts.append((ev / max(1, it["amount"]), name, it, ch, price if price else f"about {-(-FLOOR_MARGIN * RES_PRICE.get(self.cfg['res'], 3) * it['amount'] // 1):.0f} (not yet offered)"))
        if not opts:
            return None
        score, name, it, ch, price = max(opts, key=lambda o: o[0])
        seen = self.__dict__.setdefault("_income_logged", {})
        if time.time() - seen.get(name, 0) > 1800:
            seen[name] = time.time()
            self.log(f"nothing teaches at skill {self.skill:.1f}: making {name} for sale ({price} gold a piece, {ch:.0%} chance)")
            self.dlog("choice", what=f"craft {name} for income", why=f"no item teaches at {self.skill:.1f}; a shop pays {price}")
        return ((2, round(score, 3)), name, it, ch)

    def craft_once(self, name, first):
        """One craft: the full menu path the first time, 'make last' (tool on itself) afterwards."""
        self.c.events.drain()
        if first:
            menu = self.open_menu()
            path = self.menu_map[name]
            for text in path[:-1]:
                if not menu:
                    return "nomenu"
                idx = self.index_of(menu, text)
                if not idx:
                    self.close_menus([menu])
                    return "nomenu: '" + text + "' is not offered now"
                menu = self.pick(menu, idx)
            if not menu:
                return "nomenu"
            idx = self.index_of(menu, path[-1])
            if not idx:
                self.close_menus([menu])
                return "nomenu: '" + path[-1] + "' is not offered now"
            try:
                self.c.call(f"menuresponse {menu[0]} {menu[1]} {idx}", timeout=8)
            except Exception as e:
                return "menu refused: " + str(e)[-80:]
        else:
            t = self.tool()
            if not t:
                return "notool"
            self.c.use(t.serial)
            if self.c.wait_for(Event.TARGET_REQUEST, timeout=4) is None:
                return "notarget"
            self.c.target(t.serial)
        deadline = time.time() + 12
        text = []
        while time.time() < deadline:
            time.sleep(0.6)
            lines = self.read_journal()
            text += lines
            if any(OUTCOME.search(l) for l in lines):
                break
        return " | ".join(text)[-160:] or "silence"

    # ---- rules ------------------------------------------------------------------------------------------------

    def observe(self):
        super().observe()
        if time.time() - self.facts.get("skills_at", 0) > 300:          # gains keep skill_values current; a full list every five minutes is plenty
            self.facts["skills_at"] = time.time()
            self.refresh_skills()
            self.skill = self.skill_values.get(self.cfg["skill"], self.skill)
            self.leather_check()                          # before r_restock buys cloth a tailor past the cloth ladder no longer needs

    def r_flee(self):
        th = self.threats(6)
        if th and self.hp_pct() < 90:
            # something it would hunt (is_prey: a giant rat, a snake) biting it from the next tile: hit back, as a player does, instead of bandaging under its
            # teeth until half health. BotTailorBR went 81 -> 40 in two minutes to a giant rat it had filed as "looks harmless" (2026-11-01 20:08-20:10)
            biter = next((m for m in th if (getattr(m, "distance", 9) or 9) <= 1 and getattr(m, "in_war_mode", False) and self.is_prey(m)), None)
            if biter is not None:
                self.activity = f"fighting back at {biter.name}"
                if self.feature("craft_guard"):
                    return self.hold_fight(biter)
                return self.fight_back(biter)
        if self.hp_pct() >= 50 or not th:
            return False
        self.activity = "fleeing"
        if self.cure_due() and self.potion("cure") is not None:
            return False                                  # r_cure first (basics.py)
        if self.drink_heal("low health"):
            return True
        if self.flee_from(th[0]) == "trapped":            # straight away, not the walk home a far crafter's client cannot plan (basics.py)
            return self.fight_back(th[0])
        return True

    HOLD_S = 45               # longest stay on one biter when no rating is known; with one, HOLD_TTK x its time to kill
    HOLD_TTK = 1.5            # real fights ran ~1.4x the rating's time to kill, the walk up included (rating_check.py, 2026-11-04)
    HOLD_MAX_S = 90           # rating.json max_ttk_s: no fight the rating would take lasts longer

    def hold_cap(self, m):
        try:
            import rating
            r = rating.rate(self, self.mkey(m))
            if r and r.get("ttk"):
                return min(self.HOLD_MAX_S, max(self.HOLD_S, self.HOLD_TTK * float(r["ttk"])))
        except Exception:
            pass
        return self.HOLD_S
    HOLD_STEP_S = 0.8

    def hold_fight(self, m):
        """Feature craft_guard: stay on a biter until it dies, leaves the next tile, or the fight stops rating as one to take from the health left. One swing
        a tick let the next rule walk away under its teeth: BotSmithAdvR fought back at a snake six times, killed nothing and died of its poison (2026-11-05
        00:49-00:52, Lesser poison, no Cure potion)."""
        self.fight_back(m)
        end = time.time() + self.hold_cap(m)
        why = "time"
        while time.time() < end:
            self.beat()
            time.sleep(self.HOLD_STEP_S)
            cur = next((x for x in self.c.mobiles(within=4) if x.serial == m.serial), None)
            if cur is None or getattr(cur, "is_dead", False):
                why = "dead"
                break
            d = getattr(cur, "distance", 9) or 9
            if d > self.HOLD_CHASE:
                why = "left"
                break
            if d > 1:
                # a step or two off: after it, as a player keeps on a snake that slid aside (BotTinkAR's "left" holds, the snake biting on, 2026-11-05)
                self.c.goto(cur.x, cur.y).wait(timeout=self.HOLD_STEP_S + 1.5)
                continue
            if not self.hold_worth(cur):
                why = "rating"
                break
            if self.hp_pct() < 35 and not self.c.poisoned:
                self.drink_heal("holding a fight")
            if not self.c.war_mode:
                self.c.war(True)
            self.c.attack(cur.serial)
        self.ev("hold_fight", at=self.mkey(m), end=why, hp=self.c.hp)
        self.log(f"held the fight with {m.name}: {why}, hp {self.c.hp}")
        return True

    HOLD_CHASE = 2             # tiles a held biter may step off and still be fought (farther, it has left: hold_fight's "left")

    def hold_worth(self, m):
        """Still a fight to take from the health left: the rating (rating.rate, current hit points) under feature rating, else is_prey."""
        if self.feature("rating"):
            r = self.rated(m)
            if r is not None:
                return bool(r["fight"])
        return bool(self.is_prey(m))

    CURE_KEEP = 2             # errands.RESTOCK's low mark for the Cure potion (learning 2: snake poison killed three of nine with none)
    CURE_BUY = 3
    CURE_PRICE = 15           # errands.PRICE["=orange potion"]
    CURE_NEAR = 60            # a seller within this many tiles: bought on a town visit, never a trip of its own
    CURE_RETRY_S = 1800       # errands.KIT_RETRY_S: shelves empty until the vendor's restock

    def cures(self):
        return sum((i.amount or 1) for i in (self.c.backpack or []) if "orange" in (i.name or "").lower() or "cure potion" in (i.name or "").lower())

    def r_cures(self):
        """Feature craft_guard: a crafter in town with fewer than CURE_KEEP Cure potions buys CURE_BUY at the nearest Alchemist or Healer. A crafter
        bitten by a snake or giant spider with none can only wait the poison out (BotSmithAdvR, 2026-11-05 00:52)."""
        if not self.feature("craft_guard") or self.cures() >= self.CURE_KEEP or self.c.ghost:
            return False
        if time.time() < float(self.facts.get("cure_try_at", 0) or 0) or (self.c.gold or 0) < self.CURE_PRICE * self.CURE_BUY or self.threats(10):
            return False
        spots = [q for q in self.find_places((("alchemist",), ("healer",)), item="=orange potion", n=3, per=1)
                 if max(abs(q[0] - self.c.x), abs(q[1] - self.c.y)) <= self.CURE_NEAR]
        if not spots:
            return False
        self.facts["cure_try_at"] = time.time() + self.CURE_RETRY_S
        self.activity = "buying Cure potions"
        got = {}
        for q in spots:
            got = self.shop_at(q, {"=orange potion": self.CURE_BUY}) or {}
            if self.cures() >= self.CURE_KEEP:
                break
        self.log(f"cure potions: {self.cures()} carried after {got}")
        self.ev("cure_stock", n=self.cures(), bought=sum(got.values()) if got else 0)
        return True

    IDLE_CLEAR = 32           # as housegoal.HOUSE_CLEAR: a creature at its home's edge sees a bot standing about (perception 16) and chases it as far again; the
                              # zombie that found BotTailorBR at 1347,1433 came from a spawner 42 tiles off (home 24)

    def monster_ground(self, x, y):
        """An attack-on-sight spawner's creatures reach (x, y): within its home range plus IDLE_CLEAR."""
        try:
            import spots as _sp
            import task_core
            return any(max(abs(o["x"] - x), abs(o["y"] - y)) <= max(int(o.get("home") or 10), 1) + self.IDLE_CLEAR
                       and any(task_core.aggressive(k) for k in o["kinds"]) for o in _sp.spawner_spots())
        except Exception:
            return False

    def idle_to_town(self):
        """Nothing to do on monster ground (an attack-on-sight spawner's home range plus IDLE_CLEAR reaches the spot): wait by the bank, where the guards
        are. Anywhere quieter it waits where it is: a carpenter by the woods chops again there when its chop rest ends (BotCarpAdvR, walked to the bank by the
        first version of this rule, found no tree there and stood 7 minutes; and inside Britain, 94 tiles from a bank, the walk ran 21 times a minute, 2026-11-01)."""
        now = time.time()
        if now < self.__dict__.get("_idle_town_at", 0):
            return False
        self.__dict__["_idle_town_at"] = now + 120
        try:
            import gazetteer as gz
            if gz.in_town(self.c.x, self.c.y):
                return False
        except Exception:
            pass
        try:
            import spots as _sp
            import task_core
            hostile = any(max(abs(o["x"] - self.c.x), abs(o["y"] - self.c.y)) <= max(int(o.get("home") or 10), 1) + self.IDLE_CLEAR
                          and any(task_core.aggressive(k) for k in o["kinds"]) for o in _sp.spawner_spots())
        except Exception:
            hostile = False
        if not hostile:
            return False
        try:
            bx, by = min(self.bank_xys(), key=lambda b: max(abs(self.c.x - b[0]), abs(self.c.y - b[1])))
        except Exception:
            return False
        self.activity = "going back to town to wait"
        self.log(f"idle at {self.c.x},{self.c.y} on monster ground, {max(abs(self.c.x - bx), abs(self.c.y - by))} tiles from the bank: waiting in town")
        self.goto_near(bx, by, 6).wait(timeout=90)
        return True

    def harmless_animal(self, m):
        n = (m.name or "").lower()
        return n.startswith(("a ", "an ")) and any(re.search(r"\b" + re.escape(w) + r"\b", n) for w in self.HARMLESS) \
            and not any(w in n for w in ("giant", "dire", "plague", "rat man", "ratman"))

    @staticmethod
    def squash(name):
        return re.sub(r"[^a-z]", "", name.lower())

    def menu_names(self):
        """The lower-case names on this crafter's own craft menu: what it makes, whatever words they share with its material (a carpenter's "game board"
        holds "board", so the KEEP word test took 40 game boards for material: never sold, never banked, BotCarpAR idle with 354/390 stones, 2026-10-30).
        In leather mode also the pieces' pack names (LEATHER_PACK): "leather tunic" holds the KEEP word "leather"."""
        names = {k.lower() for k in (getattr(self, "menu_map", None) or {})}
        if self.leather_on():
            names |= set(LEATHER_PACK.values())
        return names

    def is_material(self, n):
        mats = (self.cfg["mat"],) + tuple(self.cfg.get("mat_alt", ()))
        return n in mats or n in {m + "s" for m in mats}

    def is_product(self, name):
        n = name.lower()
        if self.is_material(n):
            return False
        if n in self.items or n in self.made_names or n in self.menu_names():
            return True
        if not hasattr(self, "_squashed"):
            self._squashed = {self.squash(i) for i in self.items}
        if self.squash(n) in self._squashed or self.squash(n) in {self.squash(m) for m in self.made_names}:
            return not kept_word(n, self.KEEP)
        # made before the names were learned: "chair" is the tail of the menu's "wooden chair" (never a kit word: the starter bag stays)
        return not kept_word(n, self.KEEP) and any(it.endswith(" " + n) for it in self.items)

    def kept_word(self, n):
        return kept_word(n, self.KEEP)

    def carried_serials(self, stock):
        """{serial number: item} of the products carried (stock, from products()), to match a sell list by serial as well as by name."""
        out = {}
        for i in stock or []:
            n = sernum(i.serial)
            if n is not None:
                out[n] = i
        return out

    def working_tools(self):
        """Serials of the tools this crafter works with, one of each, never sold as products: its craft tool, and a shovel or pickaxe when it digs its
        own ore. A tinker makes shovels and tinker's tools, so is_product called them goods: BotTinkAR bought a shovel for 55-88 gold, sold it for 9 at
        the next sale, had nothing to dig with and bought another, every 10 minutes, idle 71% of the hour (2026-11-02 07:13-08:12)."""
        cfg = getattr(self, "cfg", None) or {}
        keep, names = set(), [n for n in [cfg.get("tool")] + list(cfg.get("tool_alt", ())) if n]
        for n in names:
            it = next((i for i in self.c.backpack if (i.name or "").lower() == n.lower() or n.lower() in (i.name or "").lower()), None)
            if it is not None:
                keep.add(str(it.serial))
        try:
            digs = cfg.get("res") == "IronIngot" and self.can_gather()
        except Exception:
            digs = False
        if digs:
            it = next((i for i in self.c.backpack if re.search(r"\b(pickaxe|shovel)\b", (i.name or "").lower())), None)
            if it is not None:
                keep.add(str(it.serial))
        return keep

    def products(self):
        strikes = self.facts.setdefault("unsold", {})
        now = time.time()
        keep = self.working_tools() | self.colour_kept()             # coloured pieces on offer to the fighters (colours.py) are not NPC goods
        return [i for i in self.c.backpack if self.is_product(i.name) and str(i.serial) not in keep
                and not (strikes.get(str(i.serial), [0, 0])[0] >= 2 and now - strikes[str(i.serial)][1] < 21600 and strikes[str(i.serial)][1] >= UNSOLD_VALID_FROM)]

    def strike_unsold(self, stock):
        """A product no answered vendor listed, or that stayed in the pack after the sell (a newbied starter dagger), gets a strike; two leave it out."""
        strikes = self.facts.setdefault("unsold", {})
        held = {str(i.serial) for i in self.c.backpack}
        for it in stock:
            s = str(it.serial)
            if s in held:                                  # still carried after the trip: not sold
                n = strikes.get(s, [0, 0])[0] + 1
                strikes[s] = [n, time.time()]
                if n == 2:
                    self.log(f"{it.name} ({s}) is not sold by any vendor asked twice: no longer carried to sell")

    def learn_made(self, before, made=None):
        """Names of what appeared in the pack since `before` (a set of serials) that are not material, tools or kit: the crafted item's real name
        (and, with `made`, the menu item it came from)."""
        menu = self.menu_names()
        fresh = [i for i in self.c.backpack if i.serial not in before and i.name and not self.is_material(i.name.lower())
                 and (i.name.lower() in menu or not kept_word(i.name.lower(), self.KEEP))]
        self.__dict__.setdefault("_made_serials", set()).update(i.serial for i in fresh)       # what this bot made (r_sell: refusals count only for these)
        new = {i.name.lower() for i in fresh}
        if made and new - set(self.made_as.get(made, ())):
            self.made_as[made] = sorted(set(self.made_as.get(made, ())) | new)
            json.dump(self.made_as, open(self.made_as_path, "w", encoding="utf-8"))
        if new - self.made_names:
            self.made_names |= new
            self.log(f"learned product names: {sorted(new)}")
            json.dump(sorted(self.made_names), open(self.made_names_path, "w", encoding="utf-8"))

    def r_sell(self):
        stock = self.products()
        heavy = self.c.weight > self.c.max_weight * 0.7
        if time.time() < self.facts.get("sell_skip_until", 0):
            # (heavy or not: the last trip sold nothing, and a heavy crafter banks what nobody buys, r_bank)
            return False
        if not stock:
            return False                                 # nothing made: a trip to the buyer would sell nothing
        if len(stock) < 12 and not heavy and not (stock and self.count(self.cfg["mat"]) < 30 and time.time() - self.facts.get("sold_at", 0) > 300):
            return False
        if self.threats(10) or time.time() - self.facts.get("sold_at", 0) < 150:
            return False
        self.facts["sold_at"] = time.time()
        self.activity = "selling what I made"
        self.empty_products(stock)
        gold0 = self.c.gold
        buyer = default_buyer = self.buyer_xy()
        # the shop that pays most for what is in the pack, from what other bots saw; it must buy most of the kinds carried (one pickaxe is not a reason
        # to carry 24 tinker goods to the Miner), and a shop that bought nothing last time is skipped for half an hour
        kinds = {it.name.lower() for it in stock}
        offers_known = {}
        for xy, v in self.mem.state["world"]["vendors"].items():
            if self.facts["bad_buyers"].get(xy, 0) > time.time():
                continue
            paid = [v["buys"][k] for k in kinds if k in v["buys"] and v["buys"][k] > 0]
            # (a) it must buy most of what is carried, counted against the products, not just one kind of them
            if kinds and len(paid) >= max(1, -(-len(kinds) * 3 // 5)):
                offers_known[xy] = sum(paid)
        if offers_known:
            best_xy = max(offers_known, key=offers_known.get)
            buyer = tuple(int(v) for v in best_xy.split(","))
        res = self.far_front(buyer, "sell", 100, len(stock))
        if res:                                              # the buyer is far: a routed walk under way (r_far), or not worth it
            self.far_after(res, "sell")
            return True
        res = self.c.goto(*buyer).wait(timeout=100)
        if str(res).startswith("nopath") and not self.threats(10):
            # once more from where the walk stopped, after a step aside: BotFairTailorNR and BotTailorBR stopped 27 tiles short of the Tailor on the
            # bank street ("nopath: closest 1440,1691"), the sale was dropped and the surcoats went back to the bank, 98 of them (2026-11-02 06:43-06:51)
            self.step_out()
            res2 = self.c.goto(*buyer).wait(timeout=60)
            self.log(f"to the buyer {buyer}: {res}; tried again from {self.c.x},{self.c.y}: {res2}")
            res = res2
        self.log(f"to the buyer {buyer}: {res}; carrying {len(stock)} products")
        import talk
        if talk.on(self) and stock:
            self.chatter("sell_call", cooldown=1500, item=stock[0].name.lower() + ("" if stock[0].name.lower().endswith("s") else "s"))
        # every vendor near is asked in turn (up to three answers) until one buys some of what is carried: two vendors share most shops, and the
        # Weaver (cloth only) answering first made a tailor sell nothing and record its hats as refused at the Tailor's shop
        chosen = None
        answered = 0
        for v in sorted([m for m in self.c.mobiles(within=7) if m.notoriety == "Innocent" and m.name and not m.name.startswith("Bot")], key=lambda m: m.distance):
            lines = self.vendor_list(v, "sell")
            if not any("gp" in l for l in lines):
                continue
            answered += 1
            matched = 0
            mine = self.carried_serials(stock)
            for line in lines:
                m = re.search(r"(0x[0-9A-Fa-f]+)\s+(\d+)gp\s+x(\d+)\s+(.+)", line)
                if m and (self.is_product(m.group(4).strip()) or sernum(m.group(1)) in mine) and int(m.group(2)) > 0:
                    matched += 1
            if chosen is None or matched > chosen[2]:
                chosen = (v, lines, matched)
            if matched or answered >= 3:
                break
        opened = chosen is not None
        if opened:
            v, offers, matched = chosen
        if not opened:
            self.note("sell", "Saying '<vendor> sell' near the vendor opened no list of what the vendor buys; a new crafter has to discover how to sell.", key="nosell")
            if self.feature("broke_plan"):
                self.facts["bad_buyers"][f"{buyer[0]},{buyer[1]}"] = time.time() + 3600
                json.dump(self.facts["bad_buyers"], open(self.bad_buyers_path, "w", encoding="utf-8"))
                self.facts["sell_skip_until"] = time.time() + 900
                self.dlog("choice", what="skip the buyer", why=f"nobody at {buyer[0]},{buyer[1]} opened a sell list; not again for an hour")
            return True
        cart = []
        buys = {}
        # the pieces products() keeps back stay out of the cart too: the cart is built from the vendor's list by name, so it sold the coloured pieces on
        # offer to the fighters at the iron price (BotSmithAR's bronze plate helm, 2026-11-02 16:58) and a tinker's own shovel
        keep = {str(s_).lower() for s_ in (self.working_tools() | self.colour_kept())}
        mine = self.carried_serials(stock)
        for line in offers:
            m = re.search(r"(0x[0-9A-Fa-f]+)\s+(\d+)gp\s+x(\d+)\s+(.+)", line)
            if m:
                buys[m.group(4).strip().lower()] = int(m.group(2))
            own = mine.get(sernum(m.group(1))) if m else None
            if m and own is not None and int(m.group(2)) > 0:
                pack = (own.name or "").lower()
                buys.setdefault(pack, int(m.group(2)))             # carried under another name: bought, not refused
                vname = m.group(4).strip().lower()
                if pack and vname != pack:
                    made = next((k for k, v in self.made_as.items() if pack in v), None)
                    if made and vname not in self.made_as[made]:
                        self.made_as[made] = sorted(set(self.made_as[made]) | {vname})
                        try:
                            json.dump(self.made_as, open(self.made_as_path, "w", encoding="utf-8"))
                        except Exception:
                            pass
            if m and (self.is_product(m.group(4).strip()) or own is not None) and int(m.group(2)) > 0 and m.group(1).lower() not in keep:
                cart += [m.group(1), m.group(3)]
        # a refusal counts only for a kind this bot made and carries: a newbied starter dagger is on no vendor's list, and was recorded as "dagger: 0" at
        # all three Britain smiths, so no smith made daggers again (2026-11-01)
        made = self.__dict__.get("_made_serials") or set()
        refused = {k for k in kinds if k not in buys and any(it.serial in made for it in stock if it.name.lower() == k)}
        if refused and not (matched or answered >= 2):
            self.log(f"only {v.name} answered at {buyer} and buys none of it: no refusal recorded for the shop")
            refused = set()
        if refused:
            # carried and not on the list: this shop does not buy it (price 0), so the others stop making it for this buyer
            self.mem.record("vendor", xy=f"{buyer[0]},{buyer[1]}", name=v.name, buys=[[k, 0] for k in sorted(refused)])
        if buys:
            self.mem.record("vendor", xy=f"{buyer[0]},{buyer[1]}", name=v.name, buys=[[k, p] for k, p in buys.items()])   # (a) the others learn what this shop buys
        if cart:
            self.sell_cart(cart, v)
        time.sleep(2)
        gained = self.c.gold - gold0
        if gained <= 0 and buyer != default_buyer:
            self.facts["bad_buyers"][f"{buyer[0]},{buyer[1]}"] = time.time() + 3600
            json.dump(self.facts["bad_buyers"], open(self.bad_buyers_path, "w", encoding="utf-8"))
        if gained <= 0:
            self.facts["sell_skip_until"] = time.time() + 900          # nobody wanted what is carried: craft, bank or hunt instead of another trip
            if stock:
                self.chatter("wares", cooldown=1200, item=stock[0].name.lower() + ("" if stock[0].name.lower().endswith("s") else "s"))
        if cart and gained <= 0:
            self.note("sell", f"Selling {len(cart) // 2} stacks of crafted goods to {v.name} paid nothing and printed no message: the sell request was accepted silently and the items stayed in the pack.", key="silentsell")
        self.sold_for += max(gained, 0)
        try:
            self.strike_unsold(stock)
        except Exception:
            pass
        self.log(f"sold {len(cart) // 2} kinds of product; gold {gold0} -> {self.c.gold}")
        self.note("sell", f"A {self.pname} sold {len(cart) // 2} kinds of product for {gained} gold (selllist shows each price before selling).", key="soldproducts")
        return True

    def r_retool(self):
        """The tool wore out (they do): buy another where the material is sold."""
        if self.feature("broke_plan"):
            return self.retool_planned()
        if self.tool() or self.threats(10) or time.time() - self.facts.get("retool_at", 0) < 120:
            return False
        self.facts["retool_at"] = time.time()
        self.activity = "buying a new tool"
        self.note("craft", f"The {self.cfg['tool']} wore out after about {self.made + self.fails} crafts; the player has to work out where to buy a new one.", key="toolworn")
        if self.c.gold < 40 and self.facts["bank_balance"] >= 40:
            self.visit_bank("poor", withdraw=300)
        got = self.shop_at(self.tool_shop_xy(), {self.cfg.get("tool_buy", self.cfg["tool"]): 1}, budget=max(self.c.gold - 5, 0))
        self.bad_items.clear()
        self.note("shop", f"New tool bought: {got}", key="newtool")
        return True

    def r_cut(self):
        """Tailors: cloth is sold in bolts too; scissors turn a bolt into 50 cut cloth. Only a bolt: scissors on cut or folded cloth make bandages,
        and the craft menu takes folded cloth as it is. In leather mode, hides too: scissors make each one leather (cut_hides)."""
        if self.leather_on() and self.hides_held() and not self.threats(10):
            made = self.cut_hides()
            if made is not None:
                return True                               # cut (or a walk for scissors) took the tick; no scissors at all: the hides are sewn as they are
        bolts = [i for i in self.c.backpack if i.name.lower() in ("bolt of cloth", "bolts of cloth")]
        if not bolts or self.cfg["craft"] != "Tailoring" or self.threats(10):
            return False
        sc = self.have_scissors()
        if not sc:
            return False                                  # (have_scissors buys them: BotTailorBR lost its pair, held 36 bolts it could not cut and
                                                          # waited 42 minutes of an hour, "under 5 cut cloth", 2026-11-03)
        self.activity = "cutting cloth"
        for b in bolts:
            self.c.events.drain()
            self.c.use(sc.serial)
            if self.c.wait_for(Event.TARGET_REQUEST, timeout=4) is None:
                return False
            self.c.target(b.serial)
            time.sleep(3)
            for l in self.read_journal():
                self.note("craft", f"Cutting a bolt of cloth with scissors says: {l[:100]}", key="cutmsg")
        return True

    def r_chop(self):
        """Carpenters cut their own wood when they cannot afford boards: stand by a tree, double-click the hatchet, target the tree."""
        # a fresh look at the menu needs 40 boards in the pack (r_craft), so 30-39 boards with no menu would otherwise leave the carpenter waiting
        if self.cfg["craft"] != "Carpentry" or self.count(self.cfg["mat"]) >= (30 if self.menu_map else 45) or self.threats(10) or self.hp_pct() < 50:
            return False
        if self.c.weight > self.c.max_weight * self.CRAFT_WEIGHT:
            return False                                  # too heavy to craft: the wood could not be used (patch_craft_toss.py)
        if (self.c.gold >= 150 and self.facts.get("soldout_until", 0) < time.time() and time.time() >= self.facts.get("stall_gather_until", 0)) or time.time() < self.facts.get("chop_fail", 0):
            return False                                  # still has money and the shop has boards: the shop goes first
        hat = self.c.find("hatchet") or next((i for i in self.c.equipped if "hatchet" in i.name.lower() or "axe" in i.name.lower()), None)
        if not hat:
            if self.c.gold >= 30:
                got = {}
                for shop in self.find_places(("weaponsmith", "smith"), n=2, per=1):     # the Weaponsmith sells hatchets (the Tinker does not); the Blacksmith next
                    got = self.shop_at(shop, {"hatchet": 1}, budget=self.c.gold - 5)
                    if got:
                        break
                self.note("chop", f"The carpenter has no hatchet to cut its own wood; tried the Weaponsmith and the Blacksmith: {got}", key="hatchetbuy")
            self.facts["chop_fail"] = time.time() + 600
            return bool(self.c.gold >= 30)
        got = self.chop_trees(hat)
        if not got and got is not None and self.walk_to_wood():
            return True                                   # the trees by it are cut: on to the next wood, and chop there on the next tick
        if not got:
            self.facts["chop_fail"] = time.time() + 600
        return bool(got)

    WOOD_REACH = 300          # tiles a carpenter walks for wood when the trees within near_trees' 60 are spent

    def walk_to_wood(self):
        """The nearest tree no bot found bare lately, 60 to WOOD_REACH tiles off and off monster ground (IDLE_CLEAR): walk there, as a woodcutter goes on to the next
        stand. BotCarpAdvR, Lumberjacking 100, found no workable tree near the bank and stood 7 minutes (2026-11-01 20:29-20:36)."""
        if time.time() - self.__dict__.get("_wood_walk_at", 0) < 60:
            return False                                  # one wood walk a minute
        here = (self.c.x, self.c.y)
        try:
            import spots as _sp
            import task_core
            hostile = [o for o in _sp.spawner_spots() if any(task_core.aggressive(k) for k in o["kinds"])]
        except Exception:
            hostile = []
        for t in sorted(self.all_trees(), key=lambda t: max(abs(t[0] - here[0]), abs(t[1] - here[1]))):
            d = max(abs(t[0] - here[0]), abs(t[1] - here[1]))
            if d <= 60:
                continue
            if d > self.WOOD_REACH:
                break
            if self.facts.get(("tree", t[0], t[1]), 0) > time.time() or not self.mem.usable("tree", f"{t[0]},{t[1]}"):
                continue
            if any(max(abs(o["x"] - t[0]), abs(o["y"] - t[1])) <= max(int(o.get("home") or 10), 1) + self.IDLE_CLEAR for o in hostile):
                continue
            self.activity = f"walking to the wood at {t[0]},{t[1]}"
            self.log(f"no workable tree within 60 tiles: walking {d} tiles to the wood at {t[0]},{t[1]}")
            self.__dict__["_wood_walk_at"] = time.time()
            # beside the tree, not onto it: a tree's tile is not walkable, so a walk to the tile itself came back at once and the same tree was chosen
            # several times a second (BotCarpAdvR, 21 times in a minute, 2026-11-01 21:53)
            self.goto_near(t[0], t[1], 2).wait(timeout=90)
            if max(abs(self.c.x - t[0]), abs(self.c.y - t[1])) > 10:
                # it did not get there (the walk ended at the "closest reachable" tile: BotCarpAR stopped 53 tiles short of 1368,1548 and waited 11 minutes
                # with no boards, 2026-11-01 22:10): another wood next time
                self.facts[("tree", t[0], t[1])] = time.time() + 900
                return False
            return True
        return False

    def empty_products(self, stock):
        """Take what is inside a crafted crate, box or chest out of it (a lockable one holds its key): a vendor buys only an empty container."""
        emptied = 0
        for it in stock:
            if not any(w in it.name.lower() for w in ("crate", "box", "chest")) or it.serial in self.facts.setdefault("emptied", set()):
                continue
            self.c.use(it.serial)                     # open it once: its contents are unknown to the client until then
            time.sleep(0.8)
            try:
                inside = self.c.container(it.serial, timeout=5)
            except Exception:
                inside = []
            for k in inside:
                emptied += self.drop_to_ground(k, box=it.serial)
            self.facts["emptied"].add(it.serial)
        if emptied:
            self.log(f"took {emptied} things (keys) out of crafted containers before selling")
            self.note("sell", "A crate or box made by a crafter with some Tinkering comes out lockable with its key inside, and no vendor buys a container "
                              "that holds anything; the sell list just leaves it out, with no reason given.", key="keyinside")
        return emptied

    def offer_price(self, name):
        """Between what a shop pays the crafter and what a shop charges for it: the middle when both are known."""
        pays = [p for p, xy, item in self.mem.vendor_buying(name) if item == name and p > 0]
        asks = [p for p, xy, item, qty in self.mem.vendor_selling(name) if item == name and p > 0]
        if pays and asks:
            return max(max(pays) + 1, round((max(pays) + min(asks)) / 2))
        if asks:
            return round(min(asks) * 0.8)
        if pays:
            return round(max(pays) * 1.3)
        return None

    def r_market(self):
        """A deal booked on this crafter's offer comes first; otherwise, every ten minutes, offer what it has made at a fair price."""
        d = self.mem.deal_for(self.name)
        if d:
            return self.do_deal(d)
        if self.market_tick():                                  # wants and offers of materials (feature trade), a deal booked: its walk starts next tick
            return True
        if time.time() - self.facts.get("offered_at", 0) < 600:
            return False
        self.facts["offered_at"] = time.time()
        posted = []
        for name in sorted({i.name.lower() for i in self.products()}):
            price = self.offer_price(name)
            if price:
                self.mem.record("mkt", kind="offer", item=name, price=price)
                posted.append(f"{name} {price}")
        if posted:
            self.log(f"market: offered {posted}")
        return False

    def _assess_naive(self, m):
        """A crafter has no business 'trying' a kind nobody has fought: an unknown 'a something' is judged by danger.py's cautious prior and the records (a reaper and a giant
        spider were both 'worth a try' to a carpenter), the harmless names and livestock as before."""
        a = super()._assess_naive(m)
        if a["reason"] != "newbie: never met one, worth a try":
            return a
        import danger
        r = danger.risk(self.mem, self.mkey(m), self.skill_values.get(self.main_skill(), 0), 0)
        return {"known": False, "fight": danger.acceptable(r, "prey"), "reason": f"newbie: unknown kind, risk die {r['die']:.0%} flee {r['flee']:.0%} ({r['src']})"}

    def material_reserve(self):
        """Gold a bank visit leaves in the purse for the material this crafter is short of: a tailor sewing cloth with under 20 cut cloth keeps the price
        of the bolts it will buy (tailor_bolt's batch). The purse trip banked all but 100 just before the shop (2026-11-01, BotFairTailorNR)."""
        if self.cfg.get("craft") != "Tailoring" or self.facts.get("leather_mode") or self.count(self.cfg["mat"]) >= 20:
            return 0
        mw = getattr(self.c, "max_weight", None)
        room = max(0.0, mw * 0.7 - (getattr(self.c, "weight", 0) or 0)) if mw else BOLT_WEIGHT
        n = max(1, min(BOLT_BATCH, int(room // BOLT_WEIGHT)))
        return n * BOLT_PRICE + 10

    def tailor_bolt(self, order):
        """Feature restock_fix: no cut cloth anywhere (the craft menu takes only cut cloth) and a bolt is the one way: spend the whole purse less 5 gold on it, withdrawing from the bank when that makes up the 105."""
        if self.count(self.cfg["mat"]) >= 20 or any("bolt of cloth" in i.name.lower() for i in self.c.backpack):
            return {}
        # a batch, not one bolt: one 50-cloth bolt a trip kept four tailors walking bank-shop-bank and waiting 57-72% of an hour with thousands banked,
        # beside shelves of 7-20 bolts (2026-10-30). As many as fit under 70% of the weight limit (BOLT_WEIGHT, BoltOfCloth.cs) and the money pays for.
        bal = self.facts.get("bank_balance", 0)
        mw = getattr(self.c, "max_weight", None)
        room = max(0.0, mw * 0.7 - (getattr(self.c, "weight", 0) or 0)) if mw else BOLT_WEIGHT       # (weight unknown: one bolt, as before)
        n = max(1, min(BOLT_BATCH, int(room // BOLT_WEIGHT), (self.c.gold + bal - 40) // BOLT_PRICE))
        if self.c.gold < n * BOLT_PRICE + 5:
            if bal + self.c.gold >= BOLT_PRICE + 5 and time.time() - self.facts.get("bolt_fetch_at", 0) > 240:
                # (a gap between withdrawals for bolts, not since any bank visit: a deposit a minute earlier left BotFairTailorNR with 100 carried
                # and 13,295 banked saying "not enough gold for a bolt" 88 times an hour, 2026-11-01)
                self.facts["bolt_fetch_at"] = time.time()
                self.activity = f"fetching gold for {n} bolts of cloth"
                self.visit_bank("bolts of cloth", withdraw=min(bal, n * BOLT_PRICE + 10 - self.c.gold))
            n = min(n, (self.c.gold - 5) // BOLT_PRICE)
            if n < 1:
                self.log("restock: no cut cloth in any shop and not enough gold for a bolt (%d carried, %d banked)" % (self.c.gold, bal))
                return {}
        shops = []
        for price, xy, item, qty in self.mem.vendor_selling("bolt of cloth"):
            xy = tuple(int(v) for v in xy.split(',')) 
            if price > 0 and xy not in shops:
                shops.append(xy)
        shops += [s_ for s_ in order if tuple(s_) not in shops]
        for shop in shops[:3]:
            self.shop_walk_s = 60
            got = self.shop_at(shop, {"bolt of cloth": n}, budget=self.c.gold - 5)
            if got:
                self.log(f"restock: no cut cloth anywhere: bought {got} with the purse; r_cut makes it 50 cut cloth")
                return got
        return {}

    def own_material(self, it):
        """A stack of this craft's own material, as count() counts it (plain iron for a smith)."""
        words = (self.cfg["mat"],) + tuple(self.cfg.get("mat_alt", ()))
        return any(self.matname(w, it.name or "") for w in words) and self.plain(it)

    MAT_BANK_GAP = 300        # s between bank walks for banked material

    def bank_material_out(self, box):
        """At a bank visit, the craft's own material in the box comes out (up to three restocks' worth, within half the weight limit), before any is
        bought: BotSmithAR had 244 iron ingots banked and walked to the shops for 5 (2026-11-01). The box's count is kept (facts bank_material) for r_restock."""
        need = self.restock_need()
        try:
            stacks = [i for i in self.box_contents(box, timeout=6) if self.own_material(i)]     # with hues: coloured ingots are not plain iron (box_contents)
        except Exception:
            return 0
        banked = sum(int(i.amount or 1) for i in stacks)
        have = self.count(self.cfg["mat"])
        taken = 0
        room = self.c.max_weight * self.PRODUCTS_OUT_SHARE - self.c.weight
        for it in sorted(stacks, key=lambda i: -(i.amount or 1)):
            want = 3 * need - have - taken
            u = items.unit_weight(it.name)
            n = min(int(it.amount or 1), want, int(room // u))
            if n <= 0:
                break
            self.c.get_item(it.serial, n if (it.amount or 1) > 1 else None)
            time.sleep(1.2)
            taken += n
            room -= n * u
        self.facts["bank_material"] = banked - taken
        if taken:
            self.log(f"bank: took out {taken} {self.cfg['mat']} of {banked} banked (now {have + taken} in the pack)")
            self.ev("material_unbanked", taken=taken, banked=banked)
        colour = self.bank_colour_out(box)                   # a smith's coloured ingots for armour (colours.py, feature colour_craft)
        return 1 if taken or colour else 0

    RESTOCK_GAP = 200         # s after a restock before the next one

    def purse_floor(self):
        """Gold a restock needs carried: the 40 the shop walk keeps back, plus restock_need of material at the shop price (UNIT_PRICE, the shard's
        vendor prices): cloth 160, leather 124, ingots 240. At a flat 60 BotTailAdvR carried 63 with 13,630 banked, bought 31 cloth, made one robe and
        went back to skull caps (2026-11-02 06:24)."""
        mat = "cut up leather" if self.leather_on() else self.cfg["mat"]
        return 40 + self.restock_need() * UNIT_PRICE.get(mat, 3)

    def purse_fill(self):
        """What a bank visit for the purse takes out: five restocks' worth (at least the old 400), so the next restocks need no bank walk each."""
        return max(400, 5 * self.purse_floor())

    def too_heavy_to_restock(self):
        """The weight room under CRAFT_WEIGHT cannot bring the material up to restock_need: the shop walk would buy nothing ("owns 52 of 52": BotTailorBR
        walked to three cloth shops in two minutes, 2026-11-02 06:24-06:26). The products go to the buyer first."""
        mw = items.MAT_WEIGHT.get(self.cfg["mat"])
        if not mw or self.leather_on() or not self.products():
            return False
        room = max(0.0, (self.c.max_weight * self.CRAFT_WEIGHT - self.c.weight - 5) / mw)
        return self.count(self.cfg["mat"]) + room < self.restock_need()

    def mark_stocked(self):
        """A restock happened: RESTOCK_GAP runs from now, and the gold carried is kept (stocked_gold) for r_restock's purse test."""
        self.facts["stocked_at"] = time.time()
        self.facts["stocked_gold"] = int(self.c.gold or 0)

    def restock_gap(self):
        """True while RESTOCK_GAP holds: not after a restock the purse cut short, once the purse holds purse_floor again (BotFairTailorNR bought 1 hide on
        2 gold beside 718 on the shelf, sold for 2,714 gold 13 s later and stood out the gap, 2026-11-05 21:18)."""
        if time.time() - self.facts.get("stocked_at", 0) >= self.RESTOCK_GAP:
            return False
        floor = self.purse_floor()
        return not (int(self.facts.get("stocked_gold", 1 << 30)) < floor <= int(self.c.gold or 0))

    def restock_filled(self):
        """A restock that left restock_need or more material in the pack lifts RESTOCK_GAP, so the next one follows as soon as that is sewn or forged.
        The gap is for a restock that came back short; bare shelves have their own soldout_until. With the gap after every restock BotFairTailorVR sewed
        for 10 s and stood 3 minutes, the cloth tailors 40 s and 3 minutes: tailors 59-82% of the hour in r_wander (2026-11-02 04:40-05:40)."""
        held = self.leather_held() if self.leather_on() else self.count(self.cfg["mat"])
        if self.cfg.get("craft") == "Tailoring" and not self.leather_on():
            # bolts bought are cut by r_cut after this: 50 cloth each (BoltOfCloth.Scissor, ScissorHelper(from, new Cloth(), 50))
            held += 50 * sum((i.amount or 1) for i in self.c.backpack if (i.name or "").lower() in ("bolt of cloth", "bolts of cloth"))
        if held >= self.restock_need():
            self.facts["stocked_at"] = time.time() - self.RESTOCK_GAP
            return True
        return False

    def r_restock(self):
        try:
            hs = self.house_state() if hasattr(self, "house_state") else {}
            if hs.get("phase") == "site" and self.house_deed():
                return False                              # a deed in the pack is placed first: BotTailorBR walked 400 tiles back from its site for a sewing kit (2026-11-01 21:08)
        except Exception:
            pass
        need = self.restock_need()
        if self.count(self.cfg["mat"]) >= need or self.threats(10) or self.restock_gap():
            return False
        if self.facts.get("bank_material", 0) > 0 and time.time() - self.facts.get("mat_bank_at", 0) > self.MAT_BANK_GAP                 and self.c.weight < self.c.max_weight * self.PRODUCTS_OUT_SHARE * 0.9:     # room to carry it out, or the walk takes nothing
            self.facts["mat_bank_at"] = time.time()
            self.activity = "taking material from the bank"
            self.visit_bank("material")                      # its own banked material before a shop or the hills (bank_material_out)
            return True
        if self.too_heavy_to_restock():
            self.facts["sold_at"] = 0
            self.mark_stocked()
            self.facts["restock_heavy_at"] = time.time()   # far_worth("sell") goes whatever the item count: this restock waits on that sale
            self.skip_why("r_restock", "no room for a restock's material under the craft weight: selling what it made first")
            return False
        if self.leather_on():
            return self.leather_restock()                 # hides from the Furtrader, cut with scissors; the Tanner's leather when none are left
        if self.facts.get("soldout_until", 0) > time.time() and self.can_gather():
            return False                                  # the shelves were bare a few minutes ago: gather instead of walking back to look
        if self.trains_on_own_ore():
            return False                                  # training: on its own ore, not on bought ingots (r_dig runs)
        self.mark_stocked()
        self.activity = "buying material"
        if self.c.gold < self.purse_floor() and self.facts["bank_balance"] >= self.purse_floor():
            self.visit_bank("poor", withdraw=self.purse_fill())
        if self.c.gold < 40:
            self.note("money", f"The {self.pname} has run out of material and money at once; there is no way to see the shortfall coming.", key="broke")
            return False
        cheapest = self.cheapest_material()
        spend = max(0, self.c.gold - 40) + (self.facts.get("bank_balance", 0) or 0)
        if cheapest is not None and cheapest > spend and self.products():
            # the cheapest material any shelf has shown costs more than it can spend: what it made goes to the buyer first. BotTailorBR walked to three
            # cloth shops with 57 to spend on 100-gold bolts and 14 surcoats in the pack, again and again (2026-11-02 00:19-00:22)
            self.facts["sold_at"] = 0
            self.mark_stocked()
            self.skip_why("r_restock", f"the cheapest material is {cheapest} gold, {spend} to spend: selling what it made first")
            return False
        word = next(iter(self.cfg["wanted"]))
        shops = []
        for price, xy, item, qty in self.mem.vendor_selling(word):      # cheapest first, from what any bot has seen on the shelves
            xy = tuple(int(v) for v in xy.split(","))
            if price > 0 and xy not in shops:
                shops.append(xy)
        for xy in self.shop_xys():
            if all(max(abs(xy[0] - s[0]), abs(xy[1] - s[1])) > 2 for s in shops):
                shops.append(xy)
        got = {}
        opened = False
        fix = self.feature("restock_fix")
        order = shops[:3]
        if fix:
            bad = self.facts.get("shop_nopath", {})
            good = [s_ for s_ in order if bad.get(tuple(s_), 0) <= time.time()]
            order = good or order                              # a shop the planner could not reach is skipped for 10 minutes (all of them unreachable: try again)
        if fix and order:
            k = self.facts.get("restock_at", 0) % len(order)
            order = order[k:] + order[:k]                       # begin at the shop after the last one visited
        t_end = time.time() + 110
        for n, shop in enumerate(order):
            if fix:
                left = t_end - time.time()
                if n and left < 20:
                    self.log(f"restock: out of time after {n} shop(s); the rest next time")
                    break
                self.shop_walk_s = max(20, min(90, left))
            # a reserve of 40, not 120: tailors holding 122 gold had 2 to spend and stood idle for twenty minutes beside cloth at 3 gp
            got = self.shop_at(shop, self.restock_wanted(), budget=max(0, self.c.gold - 40))
            if got:
                break
            if fix:
                self.facts["restock_at"] = self.facts.get("restock_at", 0) + 1                      # nothing here: the next shop first next time
            if self.facts.get("shop_list_opened") and not self.facts.get("shop_had_wanted"):      # sold out only when the list lacked it
                opened = True
                self.mem.record("vendor", xy=f"{shop[0]},{shop[1]}", name="", stock=[[word, 0, 0]])   # the list opened without it: sold out, tell the others
        if not got and fix and self.cfg["craft"] == "Tailoring":
            got = self.tailor_bolt(order)
        if not got and self.far_pending():
            return True                                  # a far walk under way, or not worth it: that is no bare shelf
        if not got:
            # sold out only if a list was seen without it; no list at all is a missed vendor, worth another look soon
            self.facts["soldout_until"] = time.time() + (1200 if opened else 180)
            self.note("shop", f"No shop had {word} left: the {self.pname}s and other crafters empty the shelves faster than they refill.", key=f"soldout:{word}")
        self.note("shop", f"Material bought for the {self.pname}: {got}", key="bought")
        if got:
            self.restock_filled()
        return True

    def cheapest_material(self):
        """The lowest shelf price any bot has seen for any of the material this crafter buys (cfg wanted), or None when no shelf showed one."""
        best = None
        for word in self.cfg.get("wanted", {}):
            try:
                for price, xy, item, qty in self.mem.vendor_selling(word):
                    if price > 0 and (best is None or price < best):
                        best = price
            except Exception:
                continue
        return best

    def skip_why(self, rule, why):
        """One line per declined work rule and reason, at most every 10 minutes: an idle crafter says why."""
        seen = self.__dict__.setdefault("_skip_seen", {})
        if time.time() - seen.get((rule, why[:40]), 0) > 600:
            seen[(rule, why[:40])] = time.time()
            self.log(f"{rule}: skip - {why}")
        return False

    CRAFT_WEIGHT = 0.8                                   # no crafting above this share of the weight limit (patch_craft_weight.py)

    def restock_wanted(self):
        """The material to buy, cut to what fits under CRAFT_WEIGHT: BotCarpAdvR bought 49-51 boards to 378-384 of 390 stones, could not craft above 312,
        banked them and bought again, 360 gold in 12 minutes (2026-10-31)."""
        import items
        mw = items.MAT_WEIGHT.get(self.cfg["mat"])
        if not mw:
            return dict(self.cfg["wanted"])
        room = max(0, int((self.c.max_weight * self.CRAFT_WEIGHT - self.c.weight - 5) / mw))
        return {k: min(v, self.count(self.cfg["mat"]) + room) for k, v in self.cfg["wanted"].items()}

    def held_per_stone(self):
        """Gold a stone of this crafter's material is worth held (HELD_VALUE, the shop's buy price, over its weight): a piece a shop pays less for per stone
        is not worth carrying to that shop (toss_old_pieces)."""
        import items
        v = HELD_VALUE.get(self.cfg["mat"])
        return v / items.unit_weight(self.cfg["mat"]) if v else 0.0

    def toss_unsold(self, share=0.7):
        """Too heavy to craft and the bank box is full: drop products and spares, what no known shop buys first, to share of the limit (patch_craft_toss.py)."""
        if time.time() - self.facts.get("toss_at", 0) < 120:
            return False
        self.facts["toss_at"] = time.time()
        buys = {}
        try:
            for v in self.mem.state["world"]["vendors"].values():
                for item, price in v.get("buys", {}).items():
                    buys[item] = max(buys.get(item, 0), price)
        except Exception:
            pass
        mat = str(self.cfg.get("mat", "")).lower()
        kept, junk = set(), []
        for i in self.c.backpack:
            low = (i.name or "").lower()
            if not low or any(w in low for w in self.OVERLOAD_ESSENTIAL) or (mat and mat in low):
                continue                                        # the essentials and the craft's own material stay
            tool = next((w for w in self.OVERLOAD_TOOLS if w in low), None)
            if tool and tool not in kept:
                kept.add(tool)
                continue
            junk.append(i)
        junk.sort(key=lambda i: (buys.get((i.name or "").lower(), 0), -(i.amount or 1)))
        before, n = self.c.weight, 0
        for it in junk:
            if self.c.weight <= self.c.max_weight * share:
                break
            n += self.drop_to_ground(it)
        if n:
            self.activity = "tossing what nobody buys"
            self.log(f"bank box full and too heavy to craft: tossed {n} stacks nobody buys, weight {before} -> {self.c.weight}/{self.c.max_weight}")
            self.ev("shed", how="toss", item="products", qty=max(0, before - self.c.weight), stacks=n)
        return n > 0

    def r_craft(self):
        if time.time() < self.__dict__.get("_nomenu_until", 0):
            return False                                  # the craft menu did not open a moment ago (see craft's "nomenu")
        # a harmless animal (basics.HARMLESS: cow, sheep, warbler ...) is no reason to stop, even in war mode: it fights only what attacked it (AI_Animal,
        # FightMode.Aggressor) and a cow hits for 1-4. 40 skips in an hour named a cow, a warbler or a giant rat beside crafters (the Anomaly sweep, 2026-11-01)
        near = [m for m in self.threats_coming(10) if not self.harmless_animal(m)]
        if near:
            return self.skip_why("r_craft", f"threat near: {near[0].name}")
        if self.hp_pct() < 50:
            return False
        if time.time() < self.facts.get("menu_empty_until", 0):
            return self.skip_why("r_craft", "the craft menu was empty a few minutes ago")
        if not self.tool():
            self.note("craft", f"The {self.pname}'s tool ({self.cfg['tool']}) is gone or worn out; no warning came before the last use.", key="notool")
            return False
        self.__dict__.pop("_spend_hue", None)
        if self.count(self.cfg["mat"]) < 5:
            spend = self.spend_hue()
            if not spend:
                return self.skip_why("r_craft", f"under 5 {self.cfg['mat']}")
            self.__dict__["_spend_hue"] = spend[0]              # held until the next r_craft: count() and material() take this metal for iron
            if time.time() - self.facts.get("spend_log_at", 0) > 600:
                self.facts["spend_log_at"] = time.time()
                self.log(f"out of iron: making the products of {spend[1]} ({self.count(self.cfg['mat'])} ingots), which an NPC pays for like iron")
                self.ev("colour_spend", metal=spend[1], ingots=self.count(self.cfg["mat"]))
        if self.c.weight > self.c.max_weight * self.CRAFT_WEIGHT:
            if time.time() - self.facts.get("old_toss_at", 0) > 120:
                self.facts["old_toss_at"] = time.time()
                if self.toss_old_pieces():
                    return True                                  # pieces worth less a stone than the material go, full box or not: BotCarpAdvR carried 37
                                                                 # board games (185 stones, 37 gold) and never crafted while the box had room (2026-10-31)
            if self.bank_box_full() and self.toss_unsold():
                return True                                      # the bank is full and nobody buys it: tossed (patch_craft_toss.py)
            self.facts["craft_heavy_at"] = time.time()             # r_bank's heavy visit banks what is weighing it down (BotBase.r_bank)
            return self.skip_why("r_craft", f"the pack is too heavy ({self.c.weight}/{self.c.max_weight}): sell or bank first")     # patch_craft_weight.py
        if self.menu_map and getattr(self, "explored_at", None) and (self.skill - self.explored_at[1] >= 4 or time.time() - self.explored_at[0] > 1500):
            self.menu_map_backup = self.menu_map
            self.menu_map = {}
        if not self.menu_map and self.menu_map_backup and self.count(self.cfg["mat"]) < 40:
            self.menu_map = self.menu_map_backup                 # too little material to look again: keep crafting from the old menu
            self.explored_at = (time.time() - 1200, self.skill - 3)       # and look again in about five minutes
        if not self.menu_map and self.count(self.cfg["mat"]) < (40 if self.menu_map_backup else 8):
            return self.skip_why("r_craft", f"{self.count(self.cfg['mat'])} {self.cfg['mat']}: too little to look at the menu again")                                # the menu only lists what the material in the pack allows: restock first (any amount will do for a first look)
        if not self.menu_map:
            st = self.station_xy()
            if st:
                self.c.gotoexact(*st).wait(timeout=100)
            self.activity = "learning the menu"
            if not self.explore():
                # an empty menu: no usable material for anything (or only Repair and Smelt); let restocking, selling and earning have a turn
                self.facts["menu_empty_until"] = time.time() + 300
                self.log("the craft menu offers nothing to make: crafting paused for five minutes")
            return True
        pick = self.choose()
        if not pick:
            self.note("craft", f"Nothing in the menu is both makeable and challenging at skill {self.skill:.1f}.", key=f"nochoice:{int(self.skill)}")
            if getattr(self, "explored_at", None) is None:
                self.explored_at = (0, 0)                  # the menu was learned by an earlier brain, maybe at a lower skill: look again next tick
                self.log("the craft menu may be out of date: relearning it")
            time.sleep(5)
            return self.skip_why("r_craft", f"nothing makeable and challenging at skill {self.skill:.1f} (menu {len(self.menu_map)} items, bad {sorted(self.bad_items)[:6]})")
        _, name, it, ch = pick
        st = self.station_xy()
        if st and not self.at_station(st):
            self.activity = "walking to the forge"
            if max(abs(self.c.x - st[0]), abs(self.c.y - st[1])) > 100 and hasattr(self, "far_goto"):
                self.far_goto(st, "forge", timeout=90)    # a far smithy is a far walk (one plain walk ended short and the smith crafted where it stood)
            else:
                self.c.gotoexact(*st).wait(timeout=100)
            if not self.at_station(st):
                # not at the anvil yet: no craft here (the menu opens only beside the anvil and forge). BotSmithAdvR smelted at a far forge and tried 39 items
                # in 2.5 minutes, each "nomenu", striking every one off (2026-11-01 20:46-20:48)
                return self.skip_why("r_craft", f"not at the forge yet ({self.c.x},{self.c.y}, forge {st[0]},{st[1]})")
        self.activity = f"making {name}"
        self.log(f"making {name}: skill {self.skill:.1f} window {it['min']}-{it['max']} chance {ch:.0%} cost {it['amount']}")
        result = None
        before = {i.serial for i in self.c.backpack}
        self._need = it["amount"]                          # material() targets a stack that holds enough for this item
        for n in range(self.craft_batch(name)):
            if self.count(self.cfg["mat"]) < it["amount"]:
                break
            result = self.craft_once(name, first=(n == 0 or self.last_made != name))
            self.last_made = name
            ok = bool(re.search(r"You create|You make|put .* in|exceptional", result or "", re.I))
            tried = ok or bool(TRIED.search(result or ""))  # a real outcome: silence, notool or a refused menu was no try (BotFairTailorVR, 2026-11-05)
            self.made += ok
            self.work += ok
            self.fails += tried and not ok
            if ok and n < 3:
                self.learn_made(before, made=name)
            if tried:
                self.mem.record("craft", scope="prof", craft=self.cfg["craft"], item=name, ok=ok, gain=bool(re.search(r"skill in .* has increased", result or "", re.I)),
                                skill=round(float(self.skill or 0.0), 1),
                                exc=bool(re.search(r"exceptional", result or "", re.I)))
            if re.search(r"fail", result or "", re.I):
                self.note("craft", f"A failed craft says: {result[-110:]}", key="failmsg")
            if (result or "").startswith(("nomenu", "menu refused")):
                self.last_made = None
                if result != "nomenu":
                    self.menu_map = {} if n == 0 and self.count(self.cfg["mat"]) >= it["amount"] else self.menu_map
                    self.bad_items.add(name)              # the menu opened without this item: struck off
                else:
                    self.__dict__["_nomenu_until"] = time.time() + 60   # (a menu that did not open at all says nothing about the item: the tool, the
                break                                                  # target or the place) a minute's rest, not every item in turn
            if re.search(r"not yet crafted", result or "", re.I):
                self.last_made = None                    # make-last works only after a success: the next try goes through the menu
                continue
            if result == "notool":
                self.log("craft stopped: the tool is gone (worn out): r_retool")
                break                                     # the rest of the batch would fail too, each counted (11 failed, last "notool", BotCarpAR 2026-11-01)
            if re.search(r"no ?mat|cannot|too heavy|not have|must|don't have the resources", result or "", re.I) and not ok:
                self.log(f"craft stopped: {result}")
                if "tool" in (result or "").lower() or "silence" in result:
                    self.bad_items.add(name)
                break
            if ok:
                self.note("craft", f"A successful craft says: {result[-110:]}", key="okmsg")
        self.log(f"made {self.made} ok, {self.fails} failed; last: {result}")
        return True

    def can_gather(self):
        """Can this crafter make its own material? A carpenter chops logs; a smith or tinker with some Mining digs ore and smelts it (iron smelts from 25 Mining)."""
        if self.cfg["craft"] == "Carpentry":
            return True
        return self.cfg["res"] == "IronIngot" and self.skill_values.get("Mining", 0) >= 30
        # (not false for a pack of coloured ingots: they pile up over hours while the digging still yields plain iron. Turning gathering off for them
        # stopped all five metal crafters' digging, and the shelves' 16 ingots could not feed them: items made fell from 1,350 to 227 an hour for
        # BotTinkAR, 2026-11-02 04:07-05:12)

    def r_smelt(self):
        """Ore in the pack and the craft wants ingots: carry it to the forge and smelt it (double-click the ore, target the forge)."""
        if self.cfg["res"] != "IronIngot" or self.threats(10) or self.hp_pct() < 50:
            return False
        piles = self.ore_piles(smeltable=True)
        ore = sum((i.amount or 1) for i in piles)
        heavy = self.c.weight > self.c.max_weight * 0.7
        if not piles or (ore < 24 and not heavy and time.time() - self.facts.get("dig_started", time.time()) < 900):
            return False
        done = self.smelt()
        if done is None:
            self.facts["dig_started"] = time.time()
            return False
        self.facts.pop("dig_started", None)
        return bool(done[1] or done[2])                  # no ingots and nothing burned: let the other rules have the tick

    def r_dig(self):
        """The shops are out of ingots: a smith or tinker with Mining goes to the hills and digs (the miner's own rule), then r_smelt takes it to the forge."""
        if self.cfg["res"] != "IronIngot" or not self.can_gather() or self.count(self.cfg["mat"]) >= (20 if self.menu_map else 40) or self.threats(10) or self.hp_pct() < 50:
            return False
        if self.c.weight > self.c.max_weight * self.CRAFT_WEIGHT:
            return False                                  # too heavy to craft: the ore could not be used (patch_craft_toss.py)
        if self.facts.get("soldout_until", 0) < time.time() and self.c.gold >= 40 and time.time() >= self.facts.get("stall_gather_until", 0):
            return False                                  # the shop may have ingots again: r_restock looks first
        if not self.pickaxe():
            if time.time() < self.facts.get("pick_fail", 0):
                return False
            self.facts["pick_fail"] = time.time() + 600
            if self.c.gold < 40 and self.facts["bank_balance"] >= 40:
                self.visit_bank("pickaxe", withdraw=100)
            import miner as _miner
            got = _miner.MinerBot.buy_dig_tools(self, self.where1(("tinker",), item="shovel"), max(self.c.gold - 5, 0)) if self.c.gold >= 30 else {}
            self.note("dig", f"The {self.pname} needs a pickaxe to dig its own ore while the shops are sold out; bought: {got}", key="crafterpick")
            return bool(got)
        self.facts.setdefault("dig_started", time.time())
        self.note("dig", f"The {self.pname} goes to dig and smelt its own ore because no shop has ingots.", key="digown")
        self.pick = self.pickaxe                           # MinerBot.r_mine asks self.pick() for the pickaxe; for one call it shadows the menu pick
        try:
            return MinerBot.r_mine(self)
        finally:
            del self.pick

    def r_earn(self):
        """Broke, with nothing to make and nothing in the bank: do what a new player does and hunt vermin for coins (the hunter's own rules, limited to what is prey)."""
        if self.feature("broke_plan"):
            return self.earn_planned()
        if (self.c.gold >= 60 or self.facts["bank_balance"] >= 60 or self.count(self.cfg["mat"]) >= 30) and time.time() >= self.facts.get("stall_earn_until", 0):
            return False
        if self.products() and time.time() - self.facts.get("earn_sell_at", 0) > 600:
            self.facts["earn_sell_at"] = time.time()
            self.facts["sold_at"] = 0                     # sell what is in the pack before going out with a dagger (once in ten minutes)
            if self.r_sell():
                return True
        self.note("money", f"The {self.pname} has no money, no material and nothing in the bank, so it goes hunting for coins with a craft tool and a dagger.", key="earnhunt")
        self.activity = "broke: hunting for coins"
        for rule in ("r_loot", "r_heal", "r_fight", "r_hunt"):
            if getattr(HunterBot, rule)(self):
                return True
        # vermin near town, never the hunters' frontier: a broke tailor once walked to Britain's north-east edge for coins and met a gargoyle
        near = [s for s in self.earn_spots() if not self.near_death_spot(*s, 40)] or [self.home_centre()]
        x, y = near[int(time.time() // 240) % len(near)]
        self.activity = f"broke: looking for vermin toward {x},{y}"
        self.c.goto(x, y).wait(timeout=5)
        return True

    # ---- a broke crafter (feature "broke_plan", patch_crafter_broke.py) -----------------------------------------------------------------------------

    PERSIST = HunterBot.PERSIST + ("colour_made", "retool_block_until", "retool_soldout_until", "earn_sell_at", "scrap_try_at",
                                   "leather_mode", "scissors_at")      # a tailor past the cloth ladder stays on leather after a restart
    TOOL_PRICE_GUESS = 20                                 # a tool whose price no bot has seen on a shelf
    TOOL_RESERVE = 3                                      # gold left over after the tool
    SCRAP_PROTECT = ("gold", "book", "bandage", "potion", "recall", "rune", "bedroll", "kindling", "backpack", "bag", "candle", "scroll", "tongs", "hammer", "tool", "kit", "saw",
                     "sewing", "scissors", "pickaxe", "shovel", "hatchet", "dagger", "fishing", "mortar")
    _coin_only = False

    def tool_price(self):
        """The cheapest shelf price of this craft's tool in the shared memory, or None when no bot has seen one."""
        prices = [p for p, xy, item, qty in self.mem.vendor_selling(self.cfg.get("tool_buy", self.cfg["tool"]).lower()) if p > 0]
        return min(prices) if prices else None

    def funds(self):
        return self.c.gold + max(0, self.facts.get("bank_balance", 0))

    PACK_MAX_ITEMS = 125                                  # Container.GlobalMaxItems: a pack holding this many takes nothing more, gold from the banker included

    def retool_planned(self):
        if self.tool() or self.threats(10):
            return False
        now = time.time()
        if len(self.c.backpack) >= self.PACK_MAX_ITEMS - 2 and self.products():
            # a full pack takes no withdrawn gold: what it made goes to the buyer first. BotTinkAR, 125 items with 110 unsold products, walked 250 tiles to the
            # bank for a tool every few minutes and the banker's gold never reached it (2026-11-02 02:13-02:58)
            self.facts["sold_at"] = 0
            self.facts.pop("sell_skip_until", None)
            return False
        price = self.tool_price() or self.TOOL_PRICE_GUESS
        funds = self.funds()
        if now < self.facts.get("retool_soldout_until", 0) or now - self.facts.get("retool_at", 0) < 120 or now < self.facts.get("retool_block_until", 0):
            return False                                  # (the block holds whatever the funds: a withdrawal that failed set it, and the next try came 2 minutes later)
        if funds < price:
            if now >= self.facts.get("retool_block_until", 0):
                self.facts["retool_block_until"] = now + 900
                self.log(f"no tool and {funds} gold in all (pack {self.c.gold}, bank {self.facts.get('bank_balance', 0)}) against {price}: the shop can wait, earning first")
                self.dlog("choice", what="skip the retool", why=f"gold {self.c.gold} + bank {self.facts.get('bank_balance', 0)} under the {price} gold the {self.cfg['tool']} costs; not again for 15 min")
                self.note("money", f"The {self.pname} could not pay for a new {self.cfg['tool']} ({price} gold), so it earns first instead of walking to the shop again and again.", key="retoolwait")
            return False
        self.facts["retool_at"] = now
        self.activity = "buying a new tool"
        self.note("craft", f"The {self.cfg['tool']} wore out after about {self.made + self.fails} crafts; the player has to work out where to buy a new one.", key="toolworn")
        if self.c.gold < price + self.TOOL_RESERVE and self.facts.get("bank_balance", 0) > 0:
            self.visit_bank("tool", withdraw=min(self.facts["bank_balance"], price + self.TOOL_RESERVE - self.c.gold + 10))
        got = self.shop_at(self.tool_shop_xy(), {self.cfg.get("tool_buy", self.cfg["tool"]): 1}, budget=max(self.c.gold - 1, 0))
        self.bad_items.clear()
        self.note("shop", f"New tool bought: {got}", key="newtool")
        if not got:
            self.facts["retool_soldout_until"] = time.time() + 300 if self.c.gold >= price else 0
            if self.c.gold < price:
                self.facts["retool_block_until"] = time.time() + 900
        return True

    HIDE_MIN = 6               # hides a kill must carry to be hunted for them: the cheapest leather piece sewn past 78 (studded gorget, 6 leather)

    def hide_hunting(self):
        """Feature hide_hunt: a leather tailor that must earn hunts for hides, its material, not for coins (earn_planned)."""
        return self.feature("hide_hunt") and self.leather_on()

    def hide_kind(self, k):
        """True for a kind whose carve gives at least HIDE_MIN hides (the profit table: the engine's Hides; a hind's corpse reads "deer")."""
        try:
            import profit
            for k_ in (k,) + BotBase.CORPSE_NAMES.get(k, ()):
                e = profit.table().get(k_)
                if e and float(e.get("hides") or 0) >= self.HIDE_MIN:
                    return True
        except Exception:
            pass
        return False

    def hide_ground(self):
        """The nearest cell where some bot saw a hide-bearing animal (the shared memory's sights), safe, within EARN_REACH of home and not just found
        empty; else earn_ground."""
        try:
            home = self.home_centre()
            empty = self.facts.get("earn_empty", {})
            now = time.time()
            best = None
            for cell, c in self.mem.state["world"]["cells"].items():
                if not any(self.hide_kind(k) for k in (c.get("sights") or ())):
                    continue
                if self.mem.dangerous_cell(cell) or self.mem.camp_cell(cell):
                    continue
                cx, cy = (int(v) for v in cell.split(","))
                x, y = cx + 20, cy + 20
                if max(abs(x - home[0]), abs(y - home[1])) > self.EARN_REACH or empty.get((x, y), 0) > now:
                    continue
                d = max(abs(x - self.c.x), abs(y - self.c.y))
                if best is None or d < best[0]:
                    best = (d, (x, y))
            if best:
                return best[1]
        except Exception:
            pass
        return self.earn_ground()

    EARN_REACH = 150                                      # tiles from home a broke crafter may go for coins
    EARN_MIN_GOLD = 8                                     # looted gold (decayed) a cell must hold to be a candidate
    EARN_STAND = 120                                      # seconds on a spot without anything to fight before it is called empty
    EARN_EMPTY = 900                                      # and left alone for this long

    def earn_planned(self):
        now = time.time()
        if self.tool():
            if (self.c.gold >= 60 or self.facts["bank_balance"] >= 60 or self.count(self.cfg["mat"]) >= 30) and time.time() >= self.facts.get("stall_earn_until", 0):
                return False
        elif self.funds() >= (self.tool_price() or self.TOOL_PRICE_GUESS) + self.TOOL_RESERVE:
            return False                                  # r_retool buys it (its own rule comes first)
        stock = self.products()
        if stock and now - self.facts.get("earn_sell_at", 0) > 600:
            self.facts["earn_sell_at"] = now
            offers = [[p for p, xy, item in self.mem.vendor_buying(i.name.lower())] for i in stock]
            if any(not o or max(o) > 0 for o in offers):     # a shop pays, or none has been asked; not for what every shop has refused
                self.facts["sold_at"] = 0
                if self.r_sell():
                    return True
        scraps = self.scraps()
        if scraps and now - self.facts.get("scrap_try_at", 0) > 900:
            self.facts["scrap_try_at"] = now
            worth = sum(p * n for _, p, _, n in scraps)
            self.activity = "selling scraps"
            self.dlog("choice", what="sell scraps", why=f"{[(n, a, p) for n, p, _, a in scraps]} are bought for about {worth} gold")
            gold0 = self.c.gold
            for xy in sorted({s[2] for s in scraps}, key=lambda xy: -sum(p * n for _, p, x, n in scraps if x == xy))[:2]:
                self.sell_items(xy, [s[0] for s in scraps if s[2] == xy])
            self.log(f"sold scraps: gold {gold0} -> {self.c.gold}")
            return True
        hides = self.hide_hunting()
        if hides:
            self.note("money", "A tailor without hides hunts the animals that carry them (a cow 12, a hind or goat 8) and carves them with a dagger, as the era's hunter-tailor did.", key="hidehunt")
        else:
            self.note("money", f"The {self.pname} has no money for {'a new ' + self.cfg['tool'] if not self.tool() else 'material'} and nothing to sell, so it hunts the vermin that pay (rats), not cats and birds.", key="earnhunt")
        self.activity = "hunting for hides" if hides else "broke: hunting for coins"
        ex, ey = self.hide_ground() if hides else self.earn_ground()
        if self.monster_ground(self.c.x, self.c.y) and not self.monster_ground(ex, ey) and max(abs(self.c.x - ex), abs(self.c.y - ey)) > 6:
            # off monster ground before hunting for coins: BotTailorBR hunted giant rats beside the ratman, ogre and troll camp in the west hills after each
            # corpse run and died there five times in an hour (2026-11-01 22:16-23:02)
            self.activity = f"broke: leaving monster ground for {ex},{ey}"
            self.goto_near(ex, ey, 4).wait(timeout=90)
            return True
        self._coin_only, self._hide_only = not hides, hides
        if hides:
            self.CARVE = self.CUTS_HIDES = True              # (instance attributes) loot_corpse carves, cuts the hides on the corpse and takes the leather
        try:
            for rule in ("r_loot", "r_heal", "r_fight", "r_hunt"):
                if getattr(HunterBot, rule)(self):
                    self.facts.pop("earn_at", None)
                    return True
        finally:
            self._coin_only = self._hide_only = False
            self.__dict__.pop("CARVE", None)
            self.__dict__.pop("CUTS_HIDES", None)
        x, y = self.hide_ground() if hides else self.earn_ground()
        self.activity = f"looking for hides toward {x},{y}" if hides else f"broke: looking for vermin toward {x},{y}"
        now = time.time()
        at = self.facts.get("earn_at")
        if max(abs(self.c.x - x), abs(self.c.y - y)) <= 6:
            if not at or at[0] != (x, y):
                self.facts["earn_at"] = ((x, y), now)
            elif now - at[1] > self.EARN_STAND:
                self.facts.setdefault("earn_empty", {})[(x, y)] = now + self.EARN_EMPTY
                self.facts.pop("earn_at", None)
                self.dlog("choice", what="leave the earn spot", why=f"{int(now - at[1])} s at {x},{y} with nothing to fight; not again for {self.EARN_EMPTY // 60} min")
        else:
            self.facts.pop("earn_at", None)
        self.c.goto(x, y).wait(timeout=5)
        return True

    # the planner's activities (planner.py): crafting is the default, gathering and earning are timed windows the rules read
    CHOICES = {"craft": None, "gather": "stall_gather_until", "earn": "stall_earn_until"}
    DEFAULT_CHOICE = "craft"
    CHOICE_RULES = {"craft": ("r_craft", "r_restock", "r_sell", "r_market", "r_cut"), "gather": ("r_chop", "r_dig", "r_smelt"), "earn": ("r_earn",)}

    def plan_unpriced(self, name, buys, asks):
        """A product no shop has priced yet: the shard pays material cost plus 25% for crafted goods, so it is worth its material x 1.25 (else every
        crafting window looked like a loss until the sale, and the planner moved crafters off crafting)."""
        menu = next((m for m in self.menu_map if m == name or name in self.made_as.get(m, ()) or m.endswith(" " + name)), None)
        it = self.items.get(menu) if menu else None
        if not it:
            return 0.0
        mat = self.cfg["mat"]
        unit = buys.get(mat, 0) or 0.5 * asks.get(mat, 0) or 1.0
        return it["amount"] * unit * 1.25

    def plan_feasible(self, name):
        if name == "gather":
            return self.can_gather() and self.count(self.cfg["mat"]) < (30 if self.cfg["craft"] == "Carpentry" else 20)
        if name == "earn":
            return self.short_of_money()                  # (stall_switch: vermin for coins only when short of money)
        return True

    def stall_switch(self, n):
        """The crafter's ways out of a stall (stall.py), in turn: look at the menu again, gather its own material, hunt vermin for coins."""
        now = time.time()
        mat = self.count(self.cfg["mat"])
        ways = []
        if mat >= 40 and (getattr(self, "explored_at", None) is None or now - self.explored_at[0] > 600):
            ways.append("menu")
        if self.can_gather() and mat < (30 if self.cfg["craft"] == "Carpentry" else 20):
            ways.append("gather")
        if self.short_of_money():
            ways.append("earn")                           # vermin for coins is a broke crafter's way: BotTailAdvR, 13,877 banked, hunted rats for 25 minutes
                                                          # after a stall that was the hide shelves running dry (2026-11-02 04:19-04:45)
        if not ways:
            return f"wait for material ({mat} {self.cfg['mat']}): the shelves restock", ("r_restock",)
        if not (ways[0] == "menu" and n == 1):
            plan = self.plan_for_stall()                  # the planner's next best activity, when it knows one (planner.py)
            if plan:
                return plan
        way = ways[(n - 1) % len(ways)]
        if way == "menu":
            self.explored_at = (0, 0)
            return f"re-learn the craft menu ({mat} {self.cfg['mat']} in the pack)", ("r_craft",)
        if way == "gather":
            self.facts["stall_gather_until"] = now + 1200
            return f"gather its own material for 20 min ({mat} {self.cfg['mat']})", ("r_chop", "r_dig", "r_smelt")
        self.facts["stall_earn_until"] = now + 1200
        return "hunt vermin for coins for 20 min", ("r_earn",)

    def r_wander(self):
        self.activity = "waiting"
        if self.idle_to_town():
            return True
        if self.hide_practice():                          # idle and safe: Hiding practised (basics.py, skill plan)
            return True
        time.sleep(3)
        return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True)
    ap.add_argument("--profession", type=int, required=True)
    ap.add_argument("--for", dest="seconds", type=float, default=3600)
    a = ap.parse_args()
    bot = CrafterBot(a.name, a.profession)
    bot.refresh_skills()
    bot.skill = bot.skill_values.get(bot.cfg["skill"], 0.0)
    bot.run(a.seconds)


if __name__ == "__main__":
    sys.exit(main())
