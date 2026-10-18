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
from memory import cell_of  # noqa: E402
from miner import MinerBot  # noqa: E402
from uo import Event  # noqa: E402

DATA = json.load(open(os.path.join(HERE, "craft_data.json"), encoding="utf-8"))

# profession -> (craft key, skill name in the skills list, tool, material, material shop wanted, station tile or None, seller)
CRAFTS = {
    16: dict(craft="Blacksmith", skill="Blacksmithy", tool="tongs", mat="iron ingot", res="IronIngot", station_by="smith", shop_roles=("tinker",), wanted={"ingot": 60},
             sell_roles=("smith", "weaponsmith", "armorer"), maxcost=14),
    18: dict(craft="Tailoring", skill="Tailoring", tool="sewing kit", mat="cut cloth", res="Cloth", station_by=None, shop_roles=("tailor", "weaver"), wanted={"cut cloth": 120, "bolt of cloth": 100},
             sell_roles=("tailor", "weaver"), maxcost=20),
    # the Carpenter at 1430,1597 sells boards (3 gp) and buys the work; the Tinker the carpenters used to go to sells none
    17: dict(craft="Carpentry", skill="Carpentry", tool="saw", mat="board", mat_alt=("log",), res="Log", station_by=None, shop_roles=("carpenter",), wanted={"board": 60}, sell_roles=("carpenter",), maxcost=15),
    19: dict(craft="Tinkering", skill="Tinkering", tool="tool kit", tool_alt=("tinker's tools",), tool_buy="tinker's tools", mat="iron ingot", res="IronIngot", station_by=None, shop_roles=("tinker",), wanted={"ingot": 50},
             sell_roles=("tinker",), maxcost=10),
}
# where a broke crafter finds vermin for coins: the farms south-west of Britain, inside the town region (the shared memory's cows, chickens and rats)
# (the vermin ground is Places.earn_spots() now: seeds for a home that has them, else learned cells)
LEAF = re.compile(r"\((\d+) [^)]+\)\s*$")
OUTCOME = re.compile(r"You create|You failed|You fail|You make|You have worn|wore out|enough|too heavy|cannot|must|not have|put .* in|exceptional", re.I)


from market import CrafterDemand, CrafterMarket  # noqa: E402


class CrafterBot(CrafterDemand, CrafterMarket, HunterBot):
    RULES = ["r_dead", "r_corpse", "r_gear", "r_cure", "r_flee", "r_avoid", "r_market", "r_bank", "r_retool", "r_cut", "r_sell", "r_chop", "r_restock", "r_craft", "r_smelt", "r_dig", "r_earn",
             "r_wander"]
    LOOT_MATERIALS = True
    LOOT_GEAR = ()                                        # a crafter hunting vermin for coins does not carry weapons home to sell
    CARVE = False
    pickaxe = MinerBot.pick                               # a smith or tinker who has Mining digs its own ore when the shops are sold out (pick() answers menus)
    stand_near = MinerBot.stand_near
    mountains = MinerBot.mountains                        # r_dig runs MinerBot.r_mine on a crafter, which asks self.mountains()

    # a crafter keeps tools and material, not what it makes: products go to the buyer, or into the bank when nobody buys them
    KEEP = ("book", "gold", "candle", "bag", "scroll", "potion", "recall", "scissors", "bedroll", "kindling", "bandage", "tongs", "tool", "ingot", "cloth", "leather",
            "hide", "board", "log", "hatchet", "saw", "hammer", "sewing", "dagger", "pickaxe", "shovel", "gears", "hinge", "springs", "kit", "ore", "feather", "shaft", "arrow")

    def shop_xys(self):
        """The material shops by role, nearest first (the shared memory's learned shops are tried before these by r_restock)."""
        return self.find_places(self.cfg["shop_roles"], n=3, per=2) or [self.home_centre()]

    def buyer_xy(self):
        return self.where1(self.cfg["sell_roles"])

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
        return sum((i.amount or 1) for i in self.c.backpack if any(self.matname(w, i.name) for w in words) and self.plain(i))

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

    def short_of_money(self):
        return self.c.gold + self.facts.get("bank_balance", 0) < 250

    def sale_price(self, name):
        """The best price a shop has been seen to pay for this item; 0 if every shop that was offered it refused; None if no shop has been asked."""
        names = {name.lower()} | set(self.made_as.get(name, ()))      # the menu's name and the name it has in the pack
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
            if price:
                value *= 2                                # broke: a piece a shop is known to buy comes first
            if best is None or value > best[0]:
                best = (value, *pick)
        if best is None and fallback is not None:
            return (0.0, *fallback[1:])                   # everything looks too easy: the dearest piece it can still make
        if best is None and not refused_ok:
            return self.choose_naive(refused_ok=True)     # nothing sellable can be made now: train on what there is
        return best

    def choose(self, refused_ok=False, relax=False):
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
                # what bots of this craft have actually got out of it: skill gains per unit of material (the formula only knows the window)
                ch = max(0.05, seen["ok"] / seen["n"])
                if ch < 0.3 and it["min"] > self.skill - 15:
                    continue
                key = (round((seen["gain"] / seen["n"]) / it["amount"], 4), it["min"])
            else:
                key = (0.15 / it["amount"] if seen is None or seen["n"] < 8 else 0, it["min"])          # untried items get a fair chance
            # broke: what a shop buys comes first, the best price per unit of material; otherwise skill gain per unit of material
            key = ((1, round(price / it["amount"], 3)) if price else (0, 0)) + key
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
            if not price:
                continue
            ch = self.chance(it, self.skill)
            if ch < 0.5:
                continue
            opts.append((price * ch / max(1, it["amount"]), name, it, ch, price))
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

    def r_flee(self):
        if self.hp_pct() >= 50 or not self.threats(6):
            return False
        self.activity = "fleeing"
        self.sprint()
        self.c.goto(*self.facts.setdefault("home", self.home_centre())).wait(timeout=4)
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
        strikes = self.facts.setdefault("unsold", {})
        now = time.time()
        return [i for i in self.c.backpack if self.is_product(i.name) and not (strikes.get(str(i.serial), [0, 0])[0] >= 2 and now - strikes[str(i.serial)][1] < 21600)]

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
        new = {i.name.lower() for i in self.c.backpack if i.serial not in before and i.name and not any(w in i.name.lower() for w in self.KEEP)}
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
        buyer = self.buyer_xy()
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
            for line in lines:
                m = re.search(r"(0x[0-9A-Fa-f]+)\s+(\d+)gp\s+x(\d+)\s+(.+)", line)
                if m and self.is_product(m.group(4).strip()) and int(m.group(2)) > 0:
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
        for line in offers:
            m = re.search(r"(0x[0-9A-Fa-f]+)\s+(\d+)gp\s+x(\d+)\s+(.+)", line)
            if m:
                buys[m.group(4).strip().lower()] = int(m.group(2))
            if m and self.is_product(m.group(4).strip()) and int(m.group(2)) > 0:
                cart += [m.group(1), m.group(3)]
        refused = {k for k in kinds if k not in buys}
        if refused and not (matched or answered >= 2):
            self.log(f"only {v.name} answered at {buyer} and buys none of it: no refusal recorded for the shop")
            refused = set()
        if refused:
            # carried and not on the list: this shop does not buy it (price 0), so the others stop making it for this buyer
            self.mem.record("vendor", xy=f"{buyer[0]},{buyer[1]}", name=v.name, buys=[[k, 0] for k in sorted(refused)])
        if buys:
            self.mem.record("vendor", xy=f"{buyer[0]},{buyer[1]}", name=v.name, buys=[[k, p] for k, p in buys.items()])   # (a) the others learn what this shop buys
        if cart:
            self.cmd("sell " + " ".join(cart), timeout=10)
            time.sleep(3)
        time.sleep(2)
        gained = self.c.gold - gold0
        if gained <= 0 and buyer != self.buyer_xy():
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
        got = self.shop_at(self.shop_xys()[0], {self.cfg.get("tool_buy", self.cfg["tool"]): 1}, budget=max(self.c.gold - 5, 0))
        self.bad_items.clear()
        self.note("shop", f"New tool bought: {got}", key="newtool")
        return True

    def r_cut(self):
        """Tailors: cloth is sold in bolts too; scissors turn a bolt into 50 cut cloth. Only a bolt: scissors on cut or folded cloth make bandages,
        and the craft menu takes folded cloth as it is."""
        bolts = [i for i in self.c.backpack if i.name.lower() in ("bolt of cloth", "bolts of cloth")]
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

    def r_chop(self):
        """Carpenters cut their own wood when they cannot afford boards: stand by a tree, double-click the hatchet, target the tree."""
        # a fresh look at the menu needs 40 boards in the pack (r_craft), so 30-39 boards with no menu would otherwise leave the carpenter waiting
        if self.cfg["craft"] != "Carpentry" or self.count(self.cfg["mat"]) >= (30 if self.menu_map else 45) or self.threats(10) or self.hp_pct() < 50:
            return False
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
        if not got:
            self.facts["chop_fail"] = time.time() + 600
        return bool(got)

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
                self.c.call(f"dropground {k.serial} {k.amount or 1}", timeout=8)
                time.sleep(0.6)
                emptied += 1
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

    def tailor_bolt(self, order):
        """Feature restock_fix: no cut cloth anywhere (the craft menu takes only cut cloth) and a bolt is the one way: spend the whole purse less 5 gold on it, withdrawing from the bank when that makes up the 105."""
        if self.count(self.cfg["mat"]) >= 20 or any("bolt of cloth" in i.name.lower() for i in self.c.backpack):
            return {}
        if self.c.gold < 105:
            bal = self.facts.get("bank_balance", 0)
            if bal + self.c.gold >= 105 and time.time() - self.facts.get("banked_at", 0) > 240:
                self.activity = "fetching gold for a bolt of cloth"
                self.visit_bank("a bolt of cloth", withdraw=min(bal, 150))
            if self.c.gold < 105:
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
            got = self.shop_at(shop, {"bolt of cloth": 1}, budget=self.c.gold - 5)
            if got:
                self.log(f"restock: no cut cloth anywhere: bought {got} with the purse; r_cut makes it 50 cut cloth")
                return got
        return {}

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
            got = self.shop_at(shop, self.cfg["wanted"], budget=max(0, self.c.gold - 40))
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
        return True

    def skip_why(self, rule, why):
        """One line per declined work rule and reason, at most every 10 minutes: an idle crafter says why."""
        seen = self.__dict__.setdefault("_skip_seen", {})
        if time.time() - seen.get((rule, why[:40]), 0) > 600:
            seen[(rule, why[:40])] = time.time()
            self.log(f"{rule}: skip - {why}")
        return False

    def r_craft(self):
        if self.threats(10):
            return self.skip_why("r_craft", f"threat near: {self.threats(10)[0].name}")
        if self.hp_pct() < 50:
            return False
        if time.time() < self.facts.get("menu_empty_until", 0):
            return self.skip_why("r_craft", "the craft menu was empty a few minutes ago")
        if not self.tool():
            self.note("craft", f"The {self.pname}'s tool ({self.cfg['tool']}) is gone or worn out; no warning came before the last use.", key="notool")
            return False
        if self.count(self.cfg["mat"]) < 5:
            return self.skip_why("r_craft", f"under 5 {self.cfg['mat']}")
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
        if st and (abs(self.c.x - st[0]) > 2 or abs(self.c.y - st[1]) > 2):
            self.activity = "walking to the forge"
            self.c.gotoexact(*st).wait(timeout=100)
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
            self.made += ok
            self.work += ok
            self.fails += not ok
            if ok and n < 3:
                self.learn_made(before, made=name)
            self.mem.record("craft", scope="prof", craft=self.cfg["craft"], item=name, ok=ok, gain=bool(re.search(r"skill in .* has increased", result or "", re.I)),
                            exc=bool(re.search(r"exceptional", result or "", re.I)))
            if re.search(r"fail", result or "", re.I):
                self.note("craft", f"A failed craft says: {result[-110:]}", key="failmsg")
            if (result or "").startswith(("nomenu", "menu refused")):
                self.last_made = None
                self.menu_map = {} if n == 0 and self.count(self.cfg["mat"]) >= it["amount"] else self.menu_map
                self.bad_items.add(name)
                break
            if re.search(r"not yet crafted", result or "", re.I):
                self.last_made = None                    # make-last works only after a success: the next try goes through the menu
                continue
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
        if self.facts.get("soldout_until", 0) < time.time() and self.c.gold >= 40 and time.time() >= self.facts.get("stall_gather_until", 0):
            return False                                  # the shop may have ingots again: r_restock looks first
        if not self.pickaxe():
            if time.time() < self.facts.get("pick_fail", 0):
                return False
            self.facts["pick_fail"] = time.time() + 600
            if self.c.gold < 40 and self.facts["bank_balance"] >= 40:
                self.visit_bank("pickaxe", withdraw=100)
            got = self.shop_at(self.where1(("tinker",), item="pickaxe"), {"pickaxe": 1}, budget=max(self.c.gold - 5, 0)) if self.c.gold >= 30 else {}
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

    PERSIST = HunterBot.PERSIST + ("retool_block_until", "retool_soldout_until", "earn_sell_at", "scrap_try_at")
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

    def retool_planned(self):
        if self.tool() or self.threats(10):
            return False
        now = time.time()
        price = self.tool_price() or self.TOOL_PRICE_GUESS
        funds = self.funds()
        if now < self.facts.get("retool_soldout_until", 0) or now - self.facts.get("retool_at", 0) < 120:
            return False
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
        got = self.shop_at(self.shop_xys()[0], {self.cfg.get("tool_buy", self.cfg["tool"]): 1}, budget=max(self.c.gold - 1, 0))
        self.bad_items.clear()
        self.note("shop", f"New tool bought: {got}", key="newtool")
        if not got:
            self.facts["retool_soldout_until"] = time.time() + 300 if self.c.gold >= price else 0
            if self.c.gold < price:
                self.facts["retool_block_until"] = time.time() + 900
        return True

    def coin_value(self, kind):
        """Gold a kill of this kind pays, from every bot's loot (kloot) over the fights seen: a number, 0.0 for a kind fought 6+ times that never paid, None when not measured."""
        w = self.mem.state["world"]
        kl = w["kloot"]
        fights = sum(g["n"] for g in w["fights"].get(kind, {}).values()) if kind in w["fights"] else 0
        hit = kl.get(kind) or kl.get(kind + "s")
        if hit and hit["n"] >= 2:
            return hit["gold"] / max(fights, hit["n"])
        if any(k != kind and (k.startswith(kind) or kind.startswith(k)) for k in kl):
            return None                                   # the loot record may sit under a nearby spelling ("ratmans" for "ratman"): not a known zero
        return 0.0 if fights >= 6 and not hit else None

    def prey(self, within=9):
        ps = super().prey(within)
        if not self._coin_only:
            return ps
        keep = []
        for m in ps:
            v = self.coin_value(self.mkey(m))
            if m.distance <= 1 or v is None or v >= 1.0:
                keep.append(m)
            else:
                skipped = self.facts.setdefault("coin_skipped", set())
                if self.mkey(m) not in skipped:
                    skipped.add(self.mkey(m))
                    self.dlog("choice", what=f"skip {self.mkey(m)} for coins", why=f"{v:.1f} gold a kill in the shared memory")
        return keep

    def scraps(self):
        """[(name, price, xy, amount)] of pack items some known shop buys at a price: nothing the craft or the trip needs; its material only when the tool is gone and the funds are short."""
        out = []
        toolless = not self.tool()
        for it in self.c.backpack:
            low = it.name.lower()
            is_mat = low == self.cfg["mat"] or low in self.cfg.get("mat_alt", ())
            if any(w in low for w in self.SCRAP_PROTECT) or (is_mat and not (toolless and self.funds() < (self.tool_price() or self.TOOL_PRICE_GUESS))):
                continue
            offers = [(p, xy) for p, xy, item in self.mem.vendor_buying(low) if p > 0 and item in (low, low + "s")]
            if offers:
                p, xy = offers[0]
                out.append((low, p, tuple(int(v) for v in xy.split(",")), it.amount or 1))
        return out

    EARN_REACH = 150                                      # tiles from home a broke crafter may go for coins
    EARN_MIN_GOLD = 8                                     # looted gold (decayed) a cell must hold to be a candidate
    EARN_STAND = 120                                      # seconds on a spot without anything to fight before it is called empty
    EARN_EMPTY = 900                                      # and left alone for this long

    def earn_candidates(self):
        """[(x, y, score)]: the earn spots and the cells within EARN_REACH of home that have paid, minus the empty ones; score = looted gold less 1 per 30 tiles from the bot."""
        home = self.home_centre()
        core = self.home_core() if getattr(self, "home_core", None) else (home[0] - 60, home[1] - 60, home[0] + 60, home[1] + 60)
        cells = self.mem.state["world"]["cells"]
        cand = {}
        for x, y in self.earn_spots():
            cand[(x, y)] = cells[cell_of(x, y)]["gold"] if cell_of(x, y) in cells else 0.0
        for cell, c in cells.items():
            if c["gold"] < self.EARN_MIN_GOLD:
                continue
            cx, cy = (int(v) for v in cell.split(","))
            x, y = cx + 20, cy + 20
            if max(abs(x - home[0]), abs(y - home[1])) > self.EARN_REACH or (core[0] <= x <= core[2] and core[1] <= y <= core[3]):
                continue
            if self.mem.dangerous_cell(cell) or self.mem.camp_cell(cell):
                continue
            cand[(x, y)] = max(cand.get((x, y), 0.0), c["gold"])
        empty = self.facts.get("earn_empty", {})
        now = time.time()
        out = []
        for (x, y), g in cand.items():
            if self.near_death_spot(x, y, 40) or empty.get((x, y), 0) > now:
                continue
            out.append((x, y, g - max(abs(x - self.c.x), abs(y - self.c.y)) / 30.0))
        return out

    def earn_ground(self):
        """The best candidate by looted gold less distance; the old rotation through the spots when none has paid or all are empty."""
        cand = self.earn_candidates()
        if not cand:
            self.facts.pop("earn_empty", None)                # everything was empty: start over
            spots = [s for s in self.earn_spots() if not self.near_death_spot(*s, 40) and not self.mem.dangerous_cell(cell_of(*s))] or [self.home_centre()]
            return spots[int(time.time() // 240) % len(spots)]
        best = max(cand, key=lambda c: c[2])
        if best[2] > 0:
            return best[0], best[1]
        pool = sorted(cand, key=lambda c: (c[0], c[1]))
        return pool[int(time.time() // 240) % len(pool)][:2]

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
        self.note("money", f"The {self.pname} has no money for {'a new ' + self.cfg['tool'] if not self.tool() else 'material'} and nothing to sell, so it hunts the vermin that pay (rats), not cats and birds.", key="earnhunt")
        self.activity = "broke: hunting for coins"
        self._coin_only = True
        try:
            for rule in ("r_loot", "r_heal", "r_fight", "r_hunt"):
                if getattr(HunterBot, rule)(self):
                    self.facts.pop("earn_at", None)
                    return True
        finally:
            self._coin_only = False
        x, y = self.earn_ground()
        self.activity = f"broke: looking for vermin toward {x},{y}"
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
        ways.append("earn")
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
