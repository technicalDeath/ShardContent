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
from uo import Event  # noqa: E402

DATA = json.load(open(os.path.join(HERE, "craft_data.json"), encoding="utf-8"))

# profession -> (craft key, skill name in the skills list, tool, material, material shop wanted, station tile or None, seller)
CRAFTS = {
    16: dict(craft="Blacksmith", skill="Blacksmithy", tool="tongs", mat="iron ingot", res="IronIngot", station=(1423, 1557), shop=(1427, 1652), wanted={"ingot": 250},
             sell_to=(1418, 1550), maxcost=14),
    18: dict(craft="Tailoring", skill="Tailoring", tool="sewing kit", mat="cut cloth", res="Cloth", station=None, shop=(1467, 1688), wanted={"cut cloth": 120},
             sell_to=(1467, 1688), maxcost=20),
    17: dict(craft="Carpentry", skill="Carpentry", tool="saw", mat="board", res="Board", station=None, shop=(1427, 1652), wanted={"board": 150}, sell_to=(1430, 1599), maxcost=15),
    19: dict(craft="Tinkering", skill="Tinkering", tool="tool kit", mat="iron ingot", res="IronIngot", station=None, shop=(1427, 1652), wanted={"ingot": 150},
             sell_to=(1427, 1652), maxcost=10),
}
LEAF = re.compile(r"\((\d+) [^)]+\)\s*$")
OUTCOME = re.compile(r"You create|You failed|You fail|You make|You have worn|wore out|enough|too heavy|cannot|must|not have|put .* in|exceptional", re.I)


class CrafterBot(BotBase):
    RULES = ["r_dead", "r_flee", "r_bank", "r_retool", "r_cut", "r_sell", "r_restock", "r_craft", "r_wander"]

    # a crafter keeps tools and material, not what it makes: products go to the buyer, or into the bank when nobody buys them
    KEEP = ("book", "gold", "candle", "bag", "scroll", "potion", "recall", "scissors", "bedroll", "kindling", "bandage", "tongs", "tool", "ingot", "cloth", "leather",
            "hide", "board", "log", "saw", "hammer", "sewing", "dagger", "pickaxe", "shovel", "gears", "hinge", "springs", "kit", "ore", "feather", "shaft", "arrow")

    def __init__(self, name, profession):
        super().__init__(name, profession)
        self.cfg = CRAFTS[profession]
        self.items = DATA[self.cfg["craft"]]
        self.menu_map_path = os.path.join(self.dir, "menu_map.json")
        self.menu_map = {}
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

    # ---- the menu -------------------------------------------------------------------------------------------

    def tool(self):
        t = self.c.find(self.cfg["tool"])
        if t is None:
            self.c.open_backpack()
            t = self.c.find(self.cfg["tool"])
        return t

    def material(self):
        return self.c.find(self.cfg["mat"])

    def count(self, word):
        return sum((i.amount or 1) for i in self.c.backpack if word in i.name.lower())

    def read_menu(self, wait=2.5):
        """The open legacy menu as (local serial, server id, [(index, text)]), or None."""
        deadline = time.time() + wait
        while time.time() < deadline:
            lines = self.c.call("menus", timeout=8)
            head = next((l for l in lines if l.startswith("[MENU]")), None)
            if head:
                m = re.match(r"\[MENU\] local (0x[0-9A-Fa-f]+) server (0x[0-9A-Fa-f]+)", head)
                opts = [(int(o.group(1)), o.group(2).strip()) for l in lines for o in [re.match(r"\s*\[option (\d+)\] graphic \S+ hue \S+ (.+)", l)] if o]
                return m.group(1), m.group(2), opts
            time.sleep(0.4)
        return None

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
                menu = self.pick(menu, idx) if idx else None
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
        self.menu_map = found
        self.explored_at = (time.time(), self.skill)
        json.dump(found, open(self.menu_map_path, "w"), indent=1)
        self.log(f"learned the craft menu: {len(found)} items")
        self.note("craft", f"The {self.cfg['craft']} menu lists only what the character can make now ({len(found)} items at skill {self.skill:.0f}); it never says how hard an item is.", key="menusize")
        return found

    # ---- choosing --------------------------------------------------------------------------------------------

    def chance(self, it, skill):
        lo, hi = it["min"], it["max"]
        return 1.0 if skill >= hi else 0.0 if skill < lo else (skill - lo) / (hi - lo)

    def choose(self):
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
            key = (it["min"], -it["amount"])
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
                    return "nomenu: '" + text + "' is not offered now"
                menu = self.pick(menu, idx)
            if not menu:
                return "nomenu"
            idx = self.index_of(menu, path[-1])
            if not idx:
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
        if self.tick_no % 8 == 1:
            self.refresh_skills()
            self.skill = self.skill_values.get(self.cfg["skill"], self.skill)

    def r_flee(self):
        if self.hp_pct() >= 50 or not self.mobs(6):
            return False
        self.activity = "fleeing"
        self.c.goto(*self.facts.setdefault("home", (1470, 1620))).wait(timeout=4)
        return True

    def products(self):
        names = set(self.items)
        return [i for i in self.c.backpack if i.name.lower() in names and i.name.lower() != self.cfg["mat"]]

    def r_sell(self):
        stock = self.products()
        heavy = self.c.weight > self.c.max_weight * 0.7
        if len(stock) < 12 and not heavy and not (stock and self.count(self.cfg["mat"]) < 30 and time.time() - self.facts.get("sold_at", 0) > 300):
            return False
        if self.mobs(10) or time.time() - self.facts.get("sold_at", 0) < 150:
            return False
        self.facts["sold_at"] = time.time()
        self.activity = "selling what I made"
        gold0 = self.c.gold
        res = self.c.goto(*self.cfg["sell_to"]).wait(timeout=100)
        self.log(f"to the buyer: {res}; carrying {len(stock)} products")
        opened = False
        for v in [m for m in self.c.mobiles(within=7) if m.notoriety == "Innocent" and m.name and not m.name.startswith("Bot")]:
            self.c.events.drain()
            self.c.say(f"{v.name.split()[0]} sell")
            time.sleep(2.5)
            offers = self.cmd("selllist", timeout=10)
            if len(offers) >= 1 and any("gp" in l for l in offers):
                opened = True
                break
        if not opened:
            self.note("sell", "Saying '<vendor> sell' near the vendor opened no list of what the vendor buys; a new crafter has to discover how to sell.", key="nosell")
            return True
        cart = []
        for line in offers:
            m = re.search(r"(0x[0-9A-Fa-f]+)\s+(\d+)gp\s+x(\d+)\s+(.+)", line)
            if m and m.group(4).strip().lower() in self.items and int(m.group(2)) > 0:
                cart += [m.group(1), m.group(3)]
        if cart:
            self.cmd("sell " + " ".join(cart), timeout=10)
            time.sleep(3)
        gained = self.c.gold - gold0
        self.sold_for += max(gained, 0)
        self.log(f"sold {len(cart) // 2} kinds of product; gold {gold0} -> {self.c.gold}")
        self.note("sell", f"A {self.pname} sold {len(cart) // 2} kinds of product for {gained} gold (selllist shows each price before selling).", key="soldproducts")
        return True

    def r_retool(self):
        """The tool wore out (they do): buy another where the material is sold."""
        if self.tool() or self.mobs(10) or time.time() - self.facts.get("retool_at", 0) < 120:
            return False
        self.facts["retool_at"] = time.time()
        self.activity = "buying a new tool"
        self.note("craft", f"The {self.cfg['tool']} wore out after about {self.made + self.fails} crafts; the player has to work out where to buy a new one.", key="toolworn")
        if self.c.gold < 40 and self.facts["bank_balance"] >= 40:
            self.visit_bank("poor", withdraw=300)
        got = self.shop_at(self.cfg["shop"], {self.cfg["tool"]: 1}, budget=max(self.c.gold - 5, 0))
        self.bad_items.clear()
        self.note("shop", f"New tool bought: {got}", key="newtool")
        return True

    def r_cut(self):
        """Tailors: cloth is sold in bolts; scissors turn a bolt into cut cloth."""
        bolts = [i for i in self.c.backpack if i.name.lower() in ("bolt of cloth", "cloth")]
        if not bolts or self.cfg["craft"] != "Tailoring" or self.mobs(10):
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

    def r_restock(self):
        need = 40 if self.cfg["craft"] != "Tailoring" else 60
        if self.count(self.cfg["mat"]) >= need or self.mobs(10) or time.time() - self.facts.get("stocked_at", 0) < 200:
            return False
        self.facts["stocked_at"] = time.time()
        self.activity = "buying material"
        if self.c.gold < 60 and self.facts["bank_balance"] >= 60:
            self.visit_bank("poor", withdraw=400)
        if self.c.gold < 40:
            self.note("money", f"The {self.pname} has run out of material and money at once; there is no way to see the shortfall coming.", key="broke")
            return False
        got = self.shop_at(self.cfg["shop"], self.cfg["wanted"], budget=self.c.gold - 10)
        self.note("shop", f"Material bought for the {self.pname}: {got}", key="bought")
        return True

    def r_craft(self):
        if self.mobs(10) or self.hp_pct() < 50:
            return False
        if not self.tool():
            self.note("craft", f"The {self.pname}'s tool ({self.cfg['tool']}) is gone or worn out; no warning came before the last use.", key="notool")
            return False
        if self.count(self.cfg["mat"]) < 5:
            return False
        if self.menu_map and getattr(self, "explored_at", None) and (self.skill - self.explored_at[1] >= 4 or time.time() - self.explored_at[0] > 1500):
            self.menu_map = {}
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
        for n in range(12):
            if self.count(self.cfg["mat"]) < it["amount"]:
                break
            result = self.craft_once(name, first=(n == 0 or self.last_made != name))
            self.last_made = name
            ok = bool(re.search(r"You create|You make|put .* in|exceptional", result or "", re.I))
            self.made += ok
            self.fails += not ok
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
