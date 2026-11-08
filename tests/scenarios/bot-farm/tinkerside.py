"""A smith's Tinkering (owner, 2026-11-07: "bots should action against their full 700 skill bank and not focus on a singular profession/skill").

The smiths' plan holds Tinkering (skillplan.TEMPLATES, "make its own tongs and hammers"), and all three stood at about 30 for a day: no brain but the
Tinker's could open the tinkering menu. A smith of the era made its own tools with tinker's tools and its own ingots. r_tinker, a few times an hour,
with ingots to spare and nothing near: one session of up to SESSION items through the era's menu (TinkeringMenu.cs: Tools, then "<name> (<n> ingots)",
the paths a Tinker bot learned, BotTinkAR menu_map.json), the item chosen by the skill's teaching range (DefTinkering.cs):
  its own tools first: tongs 35-85 (1 ingot) while it carries fewer than TONGS_KEPT, a shovel 40-90 (4 ingots) while it carries no dig tool (the
  smiths dig their own ore and bought shovels at 89 gold, BotSmithAR 18:33); else scissors 5-55 (2 ingots) below 45 and lockpicks 45-95 (1 ingot),
  which a smith never uses, so all of them go to a Tinker once SELL_AT are carried (sell_items sells by name: never the smith's own tools).
Events: tinker {item, made, ok, skill}, tinker_sold {gold}.
"""
from __future__ import annotations

import time

GAP = 900                   # s between sessions
SESSION = 5                 # items a session
INGOTS_KEPT = 15            # iron ingots left for the smithing
TONGS_KEPT = 2
SELL_AT = 10                # scissors and lockpicks carried before a sale at a Tinker
PATHS = {"scissors": ["Tools", "scissors (2 ingots)"], "tongs": ["Tools", "tongs (1 ingots)"],
         "shovel": ["Tools", "shovel (4 ingots)"], "lockpick": ["Tools", "lockpick (1 ingots)"]}
COST = {"scissors": 2, "tongs": 1, "shovel": 4, "lockpick": 1}
SELL_WORDS = ("scissors", "lockpick")


def choose(skill: float, dig_tools: int, tongs: int) -> str | None:
    """The item to make at this Tinkering (DefTinkering.cs ranges): its own tools while short, else what teaches and sells; None past 95."""
    if 35.0 <= skill < 85.0 and tongs < TONGS_KEPT:
        return "tongs"
    if 40.0 <= skill < 90.0 and dig_tools == 0:
        return "shovel"
    if 5.0 <= skill < 45.0:
        return "scissors"
    if 45.0 <= skill < 95.0:
        return "lockpick"
    return None


class TinkerSideMixin:
    def tinker_on(self):
        try:
            import skillplan
            return self.cfg.get("craft") == "Blacksmith" and skillplan.wants(self, "Tinkering")
        except Exception:
            return False

    def tinker_tools_held(self):
        return next((i for i in self.c.backpack if (i.name or "").lower() in ("tinker's tools", "tinker tools", "tool kit")), None)

    def count_named(self, word):
        return sum(1 for i in self.c.backpack if word in (i.name or "").lower())

    def r_tinker(self):
        if not self.tinker_on() or self.c.ghost or self.threats(10) or time.time() < self.facts.get("tinker_at", 0):
            return False
        sk = float(self.skill_values.get("Tinkering", 0) or 0)
        if sum(self.count_named(w) for w in SELL_WORDS) >= SELL_AT:
            return self.tinker_sell()
        item = choose(sk, self.count_named("shovel") + self.count_named("pickaxe"), self.count_named("tongs"))
        ingots = self.count("iron ingot")
        if not item or ingots < INGOTS_KEPT + COST[item]:
            return False
        self.facts["tinker_at"] = time.time() + GAP
        import crafter as _cr
        saved = self.cfg
        self.cfg = dict(_cr.CRAFTS[19])                       # the Tinker's tool, material and shop for this session (open_menu, tool, material, shop)
        made = ok = 0
        try:
            if not self.tinker_tools_held():
                xy = self.tool_shop_xy()
                if xy is None or self.c.gold < 40:
                    return False
                self.activity = "buying tinker's tools"
                got = self.shop_at(xy, {"tinker's tools": 1}, budget=40)
                self.log(f"tinker: bought tinker's tools {got}")
                return True
            self.activity = f"tinkering {item}"
            for _ in range(SESSION):
                if self.threats(10) or self.count("iron ingot") < INGOTS_KEPT + COST[item]:
                    break
                n0 = self.count_named(item.split()[0])
                self.read_journal()
                menu = self.open_menu()
                for text in PATHS[item]:
                    if not menu:
                        break
                    idx = self.index_of(menu, text)
                    if not idx:
                        self.close_menus([menu])
                        menu = None
                        break
                    menu = self.pick(menu, idx)
                if menu:
                    self.close_menus([menu])
                time.sleep(2.5)
                made += 1
                if self.count_named(item.split()[0]) > n0:
                    ok += 1
        finally:
            self.cfg = saved
        self.ev("tinker", item=item, made=made, ok=ok, skill=round(sk, 1))
        self.log(f"tinker: {ok} of {made} {item} made (Tinkering {sk:.1f})")
        return made > 0

    def tinker_sell(self):
        """The scissors and lockpicks to a Tinker (CRAFTS[19] sell_roles)."""
        import crafter as _cr
        saved = self.cfg
        self.cfg = dict(_cr.CRAFTS[19])
        try:
            xy = self.tool_shop_xy()
        finally:
            self.cfg = saved
        self.facts["tinker_at"] = time.time() + GAP
        if xy is None:
            return False
        self.activity = "selling tinkered tools"
        gold = self.sell_items(xy, list(SELL_WORDS))
        self.ev("tinker_sold", gold=int(gold or 0))
        self.log(f"tinker: sold scissors and lockpicks for {gold} gold")
        return True
