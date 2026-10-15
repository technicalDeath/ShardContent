"""Crafters (Blacksmith, Carpenter, Tailor, Tinker): learn the legacy craft menu once, then make the item that teaches the most, sell what piles up,
buy more material, and bank the profit.

    python crafter.py --name BotSmithA --profession 16 --for 3600

The era's craft is a target-and-menu flow: double-click the tool, target the material, answer one to three menus; "make last" is the tool targeted at
itself. craft_data.json (make_craft_data.py) holds each item's skill window and cost from the server's definitions, which is how the bot picks what to make.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from bot_common import BotBase  # noqa: E402
from hunter import HunterBot  # noqa: E402
from miner import MinerBot  # noqa: E402
from uo import Event  # noqa: E402

DATA = json.load(open(os.path.join(HERE, "craft_data.json"), encoding="utf-8"))

# profession -> (craft key, skill name in the skills list, tool, material, material shop wanted, station tile or None, seller)
CRAFTS = {
    16: dict(craft="Blacksmith", skill="Blacksmithy", tool="tongs", mat="iron ingot", res="IronIngot", station=(1423, 1557), shop=(1427, 1652), wanted={"ingot": 60},
             sell_to=(1418, 1550), maxcost=14),
    18: dict(craft="Tailoring", skill="Tailoring", tool="sewing kit", mat="cut cloth", res="Cloth", station=None, shop=(1467, 1688), wanted={"cloth": 120},
             sell_to=(1467, 1688), maxcost=20),
    # the Carpenter at 1430,1597 sells boards (3 gp) and buys the work; the Tinker the carpenters used to go to sells none
    17: dict(craft="Carpentry", skill="Carpentry", tool="saw", mat="board", mat_alt=("log",), res="Log", station=None, shop=(1430, 1599), wanted={"board": 60}, sell_to=(1430, 1599), maxcost=15),
    19: dict(craft="Tinkering", skill="Tinkering", tool="tool kit", tool_alt=("tinker's tools",), tool_buy="tinker's tools", mat="iron ingot", res="IronIngot", station=None, shop=(1427, 1652), wanted={"ingot": 50},
             sell_to=(1427, 1652), maxcost=10),
}
# where a broke crafter finds vermin for coins: the farms south-west of Britain, inside the town region (the shared memory's cows, chickens and rats)
EARN_SPOTS = [(1300, 1800), (1340, 1720), (1360, 1760)]
LEAF = re.compile(r"\((\d+) [^)]+\)\s*$")
OUTCOME = re.compile(r"You create|You failed|You fail|You make|You have worn|wore out|enough|too heavy|cannot|must|not have|put .* in|exceptional", re.I)


class CrafterBot(HunterBot):
    RULES = ["r_dead", "r_corpse", "r_gear", "r_cure", "r_flee", "r_avoid", "r_bank", "r_retool", "r_cut", "r_sell", "r_chop", "r_restock", "r_craft", "r_smelt", "r_dig", "r_earn",
             "r_wander"]
    LOOT_MATERIALS = True
    pickaxe = MinerBot.pick                               # a smith or tinker who has Mining digs its own ore when the shops are sold out (pick() answers menus)
    stand_near = MinerBot.stand_near

    # a crafter keeps tools and material, not what it makes: products go to the buyer, or into the bank when nobody buys them
    KEEP = ("book", "gold", "candle", "bag", "scroll", "potion", "recall", "scissors", "bedroll", "kindling", "bandage", "tongs", "tool", "ingot", "cloth", "leather",
            "hide", "board", "log", "hatchet", "saw", "hammer", "sewing", "dagger", "pickaxe", "shovel", "gears", "hinge", "springs", "kit", "ore", "feather", "shaft", "arrow")

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
        self.i = 0                                        # MinerBot's mountain rotation, for r_dig
        self.blocked = {}
        self.dug = 0
        self.bad_buyers_path = os.path.join(self.dir, "bad_buyers.json")
        try:
            self.facts["bad_buyers"] = json.load(open(self.bad_buyers_path, encoding="utf-8"))
        except (OSError, ValueError):
            self.facts["bad_buyers"] = {}

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

    def material(self):
        for n in (self.cfg["mat"],) + tuple(self.cfg.get("mat_alt", ())):
            m = self.c.find(n)
            if m is not None:
                return m
        return None

    def count(self, word):
        words = (word,) + tuple(self.cfg.get("mat_alt", ())) if word == self.cfg["mat"] else (word,)
        return sum((i.amount or 1) for i in self.c.backpack if any(w in i.name.lower() for w in words))

    @staticmethod
    def parse_menus(lines):
        """Every open legacy menu in a `menus` listing as [(local, server, [(index, text)])], in listing order (the newest first)."""
        menus = []
        for l in lines:
            m = re.match(r"\[MENU\] local (0x[0-9A-Fa-f]+) server (0x[0-9A-Fa-f]+)", l)
            if m:
                menus.append((m.group(1), m.group(2), []))
                continue
            o = re.match(r"\s*\[option (\d+)\] graphic \S+ hue \S+ (.+)", l)
            if o and menus:
                menus[-1][2].append((int(o.group(1)), o.group(2).strip()))
        return menus

    def read_menu(self, wait=2.5):
        """The newest open legacy menu as (local serial, server id, [(index, text)]), or None. Only that menu's own options: a listing can hold older
        menus that were never answered, and mixing their options in sent the bot down paths that do not exist (a 55 Blacksmith "learned" 0 items)."""
        deadline = time.time() + wait
        while time.time() < deadline:
            menus = self.parse_menus(self.c.call("menus", timeout=8))
            self.status_extra = {"menus": len(menus)}
            if menus:
                if len(menus) > 1:
                    self.close_menus(menus[1:])
                return menus[0]
            time.sleep(0.4)
        return None

    def close_menus(self, menus=None):
        """Answer 0 (cancel) to open menus: every menu a path abandons stays open in the client otherwise, and they pile up (134 in one Smith's client)."""
        if menus is None:
            menus = self.parse_menus(self.c.call("menus", timeout=8))
        for local, server, _ in menus:
            try:
                self.c.call(f"menuresponse {local} {server} 0", timeout=6)
            except Exception:
                pass

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

    @staticmethod
    def index_of(menu, text):
        """The option number whose text is `text` in this menu (the legacy menus are filtered by skill and material, so numbers move; words do not)."""
        for i, t in menu[2]:
            if t.strip().lower() == text.strip().lower():
                return i
        return None

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

    def choose_naive(self):
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
        for cost, name in options:
            seen = self.mem.craft_stats(self.cfg["craft"], name) or {"n": 0, "ok": 0, "gain": 0, "exc": 0}
            pick = (name, {"min": 0, "max": 100, "amount": cost, "resource": self.cfg["res"]}, (seen["ok"] + 1) / (seen["n"] + 2))
            if seen["n"] >= 6 and seen["ok"] == 0:
                continue                                  # never made one in six tries: too hard for now
            if fallback is None or cost > fallback[0]:
                fallback = (cost, *pick)
            if seen.get("exc", 0) >= 2 or (seen["n"] >= 8 and seen["gain"] == 0):
                continue                                  # comes out exceptional, or teaches nothing: too easy now
            prior = 0.3 + 0.7 * cost / top
            value = (seen["gain"] + prior) / (seen["n"] + 1) / cost ** 0.3
            if best is None or value > best[0]:
                best = (value, *pick)
        if best is None and fallback is not None:
            return (0.0, *fallback[1:])                   # everything looks too easy: the dearest piece it can still make
        return best

    def choose(self):
        if self.mode == "newbie":
            return self.choose_naive()
        have = self.count(self.cfg["mat"])
        best = None
        for name, path in self.menu_map.items():
            it = self.items.get(name)
            if not it or name in self.bad_items or it["resource"] != self.cfg["res"] or it["amount"] > have or it["amount"] > self.cfg["maxcost"]:
                continue
            ch = self.chance(it, self.skill)
            if ch >= 1.0 and it["min"] < self.skill - 30:
                continue
            if ch < 0.45 or it["max"] <= self.skill:
                continue
            seen = self.mem.craft_stats(self.cfg["craft"], name)
            if seen and seen["n"] >= 8:
                # what bots of this craft have actually got out of it: skill gains per unit of material (the formula only knows the window)
                ch = max(0.05, seen["ok"] / seen["n"])
                if ch < 0.3 and it["min"] > self.skill - 15:
                    continue
                key = (round((seen["gain"] / seen["n"]) / it["amount"], 4), it["min"])
            else:
                key = (0.15 / it["amount"] if seen is None or seen["n"] < 8 else 0, it["min"])          # untried items get a fair chance
            if best is None or key > best[0]:
                best = (key, name, it, ch)
        return best

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

    def r_flee(self):
        if self.hp_pct() >= 50 or not self.threats(6):
            return False
        self.activity = "fleeing"
        self.c.goto(*self.facts.setdefault("home", (1470, 1620))).wait(timeout=4)
        return True

    @staticmethod
    def squash(name):
        return re.sub(r"[^a-z]", "", name.lower())

    def is_product(self, name):
        n = name.lower()
        if n == self.cfg["mat"]:
            return False
        if n in self.items or n in self.made_names:
            return True
        if not hasattr(self, "_squashed"):
            self._squashed = {self.squash(i) for i in self.items}
        if self.squash(n) in self._squashed or self.squash(n) in {self.squash(m) for m in self.made_names}:
            return not any(w in n for w in self.KEEP)
        # made before the names were learned: "chair" is the tail of the menu's "wooden chair" (never a kit word: the starter bag stays)
        return not any(w in n for w in self.KEEP) and any(it.endswith(" " + n) for it in self.items)

    def products(self):
        return [i for i in self.c.backpack if self.is_product(i.name)]

    def learn_made(self, before):
        """Names of what appeared in the pack since `before` (a set of serials) that are not material, tools or kit: the crafted item's real name."""
        new = {i.name.lower() for i in self.c.backpack if i.serial not in before and i.name and not any(w in i.name.lower() for w in self.KEEP)}
        if new - self.made_names:
            self.made_names |= new
            self.log(f"learned product names: {sorted(new)}")
            json.dump(sorted(self.made_names), open(self.made_names_path, "w", encoding="utf-8"))

    def r_sell(self):
        stock = self.products()
        heavy = self.c.weight > self.c.max_weight * 0.7
        if time.time() < self.facts.get("sell_skip_until", 0) and not heavy:
            return False
        if not stock:
            return False                                 # nothing made: a trip to the buyer would sell nothing
        if len(stock) < 12 and not heavy and not (stock and self.count(self.cfg["mat"]) < 30 and time.time() - self.facts.get("sold_at", 0) > 300):
            return False
        if self.threats(10) or time.time() - self.facts.get("sold_at", 0) < 150:
            return False
        self.facts["sold_at"] = time.time()
        self.activity = "selling what I made"
        gold0 = self.c.gold
        buyer = self.cfg["sell_to"]
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
        res = self.c.goto(*buyer).wait(timeout=100)
        self.log(f"to the buyer {buyer}: {res}; carrying {len(stock)} products")
        opened = False
        offers = []
        for v in [m for m in self.c.mobiles(within=7) if m.notoriety == "Innocent" and m.name and not m.name.startswith("Bot")]:
            offers = self.vendor_list(v, "sell")
            if any("gp" in l for l in offers):
                opened = True
                break
        if not opened:
            self.note("sell", "Saying '<vendor> sell' near the vendor opened no list of what the vendor buys; a new crafter has to discover how to sell.", key="nosell")
            return True
        cart = []
        buys = {}
        for line in offers:
            m = re.search(r"(0x[0-9A-Fa-f]+)\s+(\d+)gp\s+x(\d+)\s+(.+)", line)
            if m:
                buys[m.group(4).strip().lower()] = int(m.group(2))
            if m and self.is_product(m.group(4).strip()) and int(m.group(2)) > 0:
                cart += [m.group(1), m.group(3)]
        if buys:
            self.mem.record("vendor", xy=f"{buyer[0]},{buyer[1]}", name=v.name, buys=[[k, p] for k, p in buys.items()])   # (a) the others learn what this shop buys
        if cart:
            self.cmd("sell " + " ".join(cart), timeout=10)
            time.sleep(3)
        time.sleep(2)
        gained = self.c.gold - gold0
        if gained <= 0 and buyer != self.cfg["sell_to"]:
            self.facts["bad_buyers"][f"{buyer[0]},{buyer[1]}"] = time.time() + 3600
            json.dump(self.facts["bad_buyers"], open(self.bad_buyers_path, "w", encoding="utf-8"))
        if gained <= 0:
            self.facts["sell_skip_until"] = time.time() + 900          # nobody wanted what is carried: craft, bank or hunt instead of another trip
        if cart and gained <= 0:
            self.note("sell", f"Selling {len(cart) // 2} stacks of crafted goods to {v.name} paid nothing and printed no message: the sell request was accepted silently and the items stayed in the pack.", key="silentsell")
        self.sold_for += max(gained, 0)
        self.log(f"sold {len(cart) // 2} kinds of product; gold {gold0} -> {self.c.gold}")
        self.note("sell", f"A {self.pname} sold {len(cart) // 2} kinds of product for {gained} gold (selllist shows each price before selling).", key="soldproducts")
        return True

    def r_retool(self):
        """The tool wore out (they do): buy another where the material is sold."""
        if self.tool() or self.threats(10) or time.time() - self.facts.get("retool_at", 0) < 120:
            return False
        self.facts["retool_at"] = time.time()
        self.activity = "buying a new tool"
        self.note("craft", f"The {self.cfg['tool']} wore out after about {self.made + self.fails} crafts; the player has to work out where to buy a new one.", key="toolworn")
        if self.c.gold < 40 and self.facts["bank_balance"] >= 40:
            self.visit_bank("poor", withdraw=300)
        got = self.shop_at(self.cfg["shop"], {self.cfg.get("tool_buy", self.cfg["tool"]): 1}, budget=max(self.c.gold - 5, 0))
        self.bad_items.clear()
        self.note("shop", f"New tool bought: {got}", key="newtool")
        return True

    def r_cut(self):
        """Tailors: cloth is sold in bolts; scissors turn a bolt into cut cloth."""
        # the Weaver's "Folded Cloth" is uncut cloth too: scissors make it cut cloth, as they do a bolt
        bolts = [i for i in self.c.backpack if i.name.lower() in ("bolt of cloth", "cloth", "folded cloth")]
        if not bolts or self.cfg["craft"] != "Tailoring" or self.threats(10):
            return False
        sc = self.c.find("scissors")
        if not sc:
            return False
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

    TREES = [(1431, 1631, 20, 3288), (1440, 1718, 20, 3288), (1392, 1673, 30, 3280)]
    try:
        # every choppable tree around Britain, one per harvest bank (make_trees.py reads them from the map's statics): three trees were soon chopped bare
        ALL_TREES = [tuple(t) for t in json.load(open(os.path.join(HERE, "trees.json"), encoding="utf-8"))]
    except (OSError, ValueError):
        ALL_TREES = TREES

    def near_trees(self, n=6):
        """The nearest trees within 60 tiles that no bot has found bare lately, nearest first."""
        here = (self.c.x, self.c.y)
        out = []
        for t in sorted(self.ALL_TREES, key=lambda t: max(abs(t[0] - here[0]), abs(t[1] - here[1]))):
            if max(abs(t[0] - here[0]), abs(t[1] - here[1])) > 60 or len(out) >= n:
                break
            if self.facts.get(("tree", t[0], t[1]), 0) <= time.time() and self.mem.usable("tree", f"{t[0]},{t[1]}"):
                out.append(t)
        return out

    def r_chop(self):
        """Carpenters cut their own wood when they cannot afford boards: stand by a tree, double-click the hatchet, target the tree."""
        # a fresh look at the menu needs 40 boards in the pack (r_craft), so 30-39 boards with no menu would otherwise leave the carpenter waiting
        if self.cfg["craft"] != "Carpentry" or self.count(self.cfg["mat"]) >= (30 if self.menu_map else 45) or self.threats(10) or self.hp_pct() < 50:
            return False
        if (self.c.gold >= 150 and self.facts.get("soldout_until", 0) < time.time()) or time.time() < self.facts.get("chop_fail", 0):
            return False                                  # still has money and the shop has boards: the shop goes first
        hat = self.c.find("hatchet") or next((i for i in self.c.equipped if "hatchet" in i.name.lower() or "axe" in i.name.lower()), None)
        if not hat:
            if self.c.gold >= 30:
                got = {}
                for shop in ((1481, 1584), (1418, 1550)):     # the Weaponsmith sells hatchets (the Tinker does not); the Blacksmith next
                    got = self.shop_at(shop, {"hatchet": 1}, budget=self.c.gold - 5)
                    if got:
                        break
                self.note("chop", f"The carpenter has no hatchet to cut its own wood; tried the Weaponsmith and the Blacksmith: {got}", key="hatchetbuy")
            self.facts["chop_fail"] = time.time() + 600
            return bool(self.c.gold >= 30)
        for tx, ty, tz, g in self.near_trees()[:3]:
            self.mem.record("claim", kind="tree", key=f"{tx},{ty}", ttl=300)
            self.activity = f"chopping at {tx},{ty}"
            ok = False
            self.c.goto(tx, ty).wait(timeout=60)
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1)):
                if max(abs(self.c.x - tx), abs(self.c.y - ty)) <= 2:
                    ok = True
                    break
                if str(self.c.gotoexact(tx + dx, ty + dy).wait(timeout=15)).startswith("nopath") and max(abs(self.c.x - tx), abs(self.c.y - ty)) > 6:
                    break                                  # no way into that stand of trees: the next tree, not five more tries here
            ok = ok or max(abs(self.c.x - tx), abs(self.c.y - ty)) <= 2
            if not ok:
                self.facts[("tree", tx, ty)] = time.time() + 900
                continue
            self.c.events.drain()
            self.c.use(hat.serial)
            if self.c.wait_for(Event.TARGET_REQUEST, timeout=4) is None:
                self.note("chop", "Double-clicking the hatchet raised no target cursor (an axe has to be in hand?).", key="nochopcursor")
                self.facts[("tree", tx, ty)] = time.time() + 300
                continue
            self.c.call(f"targettile {tx} {ty} {tz} {g}", timeout=8)
            end = time.time() + 45
            while time.time() < end:
                time.sleep(2.5)
                lines = self.read_journal()
                for l in lines:
                    if re.search(r"wood|log|tree|axe|lumber|chop|enough|far", l, re.I):
                        self.note("chop", f"Chopping says: {l[:100]}", key=f"chopmsg:{l[:40]}")
                if any(re.search(r"you put .* in your|logs? in your", l, re.I) for l in lines):
                    self.mem.record("res", kind="tree", key=f"{tx},{ty}", ok=True)
                if any(re.search(r"not enough wood|no wood|too far|broke", l, re.I) for l in lines):
                    self.mem.record("res", kind="tree", key=f"{tx},{ty}", ok=False, reason="no wood left or too far")
                    self.mem.record("blocked", kind="tree", key=f"{tx},{ty}", ttl=1500)
                    self.facts[("tree", tx, ty)] = time.time() + 1500
                    break
            return True
        self.facts["chop_fail"] = time.time() + 600
        return False

    def r_restock(self):
        need = 40 if self.cfg["craft"] != "Tailoring" else 60
        if self.count(self.cfg["mat"]) >= need or self.threats(10) or time.time() - self.facts.get("stocked_at", 0) < 200:
            return False
        if self.facts.get("soldout_until", 0) > time.time() and self.can_gather():
            return False                                  # the shelves were bare a few minutes ago: gather instead of walking back to look
        self.facts["stocked_at"] = time.time()
        self.activity = "buying material"
        if self.c.gold < 60 and self.facts["bank_balance"] >= 60:
            self.visit_bank("poor", withdraw=400)
        if self.c.gold < 40:
            self.note("money", f"The {self.pname} has run out of material and money at once; there is no way to see the shortfall coming.", key="broke")
            return False
        word = next(iter(self.cfg["wanted"]))
        shops = []
        for price, xy, item, qty in self.mem.vendor_selling(word):      # cheapest first, from what any bot has seen on the shelves
            xy = tuple(int(v) for v in xy.split(","))
            if price > 0 and xy not in shops:
                shops.append(xy)
        if self.cfg["shop"] not in shops:
            shops.append(self.cfg["shop"])
        got = {}
        for shop in shops[:3]:
            got = self.shop_at(shop, self.cfg["wanted"], budget=max(0, self.c.gold - 120))
            if got:
                break
            self.mem.record("vendor", xy=f"{shop[0]},{shop[1]}", name="", stock=[[word, 0, 0]])   # sold out: tell the others
        if not got:
            self.facts["soldout_until"] = time.time() + 1200
            self.note("shop", f"No shop had {word} left: the {self.pname}s and other crafters empty the shelves faster than they refill.", key=f"soldout:{word}")
        self.note("shop", f"Material bought for the {self.pname}: {got}", key="bought")
        return True

    def r_craft(self):
        if self.threats(10) or self.hp_pct() < 50:
            return False
        if not self.tool():
            self.note("craft", f"The {self.pname}'s tool ({self.cfg['tool']}) is gone or worn out; no warning came before the last use.", key="notool")
            return False
        if self.count(self.cfg["mat"]) < 5:
            return False
        if self.menu_map and getattr(self, "explored_at", None) and (self.skill - self.explored_at[1] >= 4 or time.time() - self.explored_at[0] > 1500):
            self.menu_map_backup = self.menu_map
            self.menu_map = {}
        if not self.menu_map and self.count(self.cfg["mat"]) < (40 if self.menu_map_backup else 8):
            return False                                # the menu only lists what the material in the pack allows: restock first (any amount will do for a first look)
        if not self.menu_map:
            st = self.cfg["station"]
            if st:
                self.c.gotoexact(*st).wait(timeout=100)
            self.activity = "learning the menu"
            self.explore()
            return True
        pick = self.choose()
        if not pick:
            self.note("craft", f"Nothing in the menu is both makeable and challenging at skill {self.skill:.1f}.", key=f"nochoice:{int(self.skill)}")
            time.sleep(5)
            return False
        _, name, it, ch = pick
        st = self.cfg["station"]
        if st and (abs(self.c.x - st[0]) > 2 or abs(self.c.y - st[1]) > 2):
            self.activity = "walking to the forge"
            self.c.gotoexact(*st).wait(timeout=100)
        self.activity = f"making {name}"
        self.log(f"making {name}: skill {self.skill:.1f} window {it['min']}-{it['max']} chance {ch:.0%} cost {it['amount']}")
        result = None
        before = {i.serial for i in self.c.backpack}
        for n in range(12):
            if self.count(self.cfg["mat"]) < it["amount"]:
                break
            result = self.craft_once(name, first=(n == 0 or self.last_made != name))
            self.last_made = name
            ok = bool(re.search(r"You create|You make|put .* in|exceptional", result or "", re.I))
            self.made += ok
            self.work += ok
            self.fails += not ok
            if ok and n < 3:
                self.learn_made(before)
            self.mem.record("craft", scope="prof", craft=self.cfg["craft"], item=name, ok=ok, gain=bool(re.search(r"skill in .* has increased", result or "", re.I)),
                            exc=bool(re.search(r"exceptional", result or "", re.I)))
            if re.search(r"fail", result or "", re.I):
                self.note("craft", f"A failed craft says: {result[-110:]}", key="failmsg")
            if (result or "").startswith(("nomenu", "menu refused")):
                self.last_made = None
                self.menu_map = {} if n == 0 and self.count(self.cfg["mat"]) >= it["amount"] else self.menu_map
                self.bad_items.add(name)
                break
            if re.search(r"no ?mat|cannot|too heavy|not have|must", result or "", re.I) and not ok:
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
        if self.facts.get("soldout_until", 0) < time.time() and self.c.gold >= 40:
            return False                                  # the shop may have ingots again: r_restock looks first
        if not self.pickaxe():
            if time.time() < self.facts.get("pick_fail", 0):
                return False
            self.facts["pick_fail"] = time.time() + 600
            if self.c.gold < 40 and self.facts["bank_balance"] >= 40:
                self.visit_bank("pickaxe", withdraw=100)
            got = self.shop_at((1427, 1652), {"pickaxe": 1}, budget=max(self.c.gold - 5, 0)) if self.c.gold >= 30 else {}
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
        if self.c.gold >= 60 or self.facts["bank_balance"] >= 60 or self.count(self.cfg["mat"]) >= 30:
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
        near = [s for s in EARN_SPOTS if not self.near_death_spot(*s, 40)] or [(1470, 1620)]
        x, y = near[int(time.time() // 240) % len(near)]
        self.activity = f"broke: looking for vermin toward {x},{y}"
        self.c.goto(x, y).wait(timeout=5)
        return True

    def r_wander(self):
        self.activity = "waiting"
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
