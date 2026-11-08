"""Tinkering for every bot whose plan holds it (owner, 2026-11-07: "bots should action against their full 700 skill bank and not focus on a singular
profession/skill"; "Get all the bots onto the same tech").

The smiths' and the prospectors' plans hold Tinkering (skillplan.TEMPLATES: "make its own tongs and hammers", "Tinkering for its own shovels"), and
all six stood at about 30 for a day: no brain but the Tinker's could open the tinkering menu. One engine serves them all: TinkerHands runs CrafterBot's
own T2A menu code (open_menu, the menu pick, tool, material, count, the shop lookups) with the Tinker's craft (crafter.CRAFTS[19]) on any bot, as
minersmith.SmithHands runs the smithing menu on a miner. session(bot), a few times an hour, with ingots to spare and nothing near: up to SESSION items
through the era's menu (TinkeringMenu.cs: Tools, then "<name> (<n> ingots)", the paths a Tinker bot learned, BotTinkAR menu_map.json), the item chosen
by the skill's teaching range (DefTinkering.cs):
  its own tools once they succeed half the time: tongs 35-85 (1 ingot) from 60 while it carries fewer than TONGS_KEPT, a shovel 40-90 (4 ingots)
  from 65 while it carries no dig tool (the smiths and miners dig their own ore and bought shovels at 89 gold, BotSmithAR 18:33); else scissors 5-55
  (2 ingots) below 50 and lockpicks 45-95 (1 ingot), which neither uses, so all of them go to a Tinker once SELL_AT are carried (sell_items sells by
  name: never its own tools).
Callers: CrafterBot.r_tinker (TinkerSideMixin; a smith, between crafts) and MinerBot.r_sell (miner_tinker; at the forge after the smelt, before the
ingots are sold). Events: tinker {item, made, ok, skill}, tinker_sold {gold}.
"""
from __future__ import annotations

import time

GAP = 900                   # s between sessions
SESSION = 5                 # items a session
INGOTS_KEPT = 15            # iron ingots left for the smithing (a miner's are its sale: it keeps none back, MINER_KEPT)
MINER_KEPT = 0
TONGS_KEPT = 2
SELL_AT = 10                # scissors and lockpicks carried before a sale at a Tinker
PATHS = {"scissors": ["Tools", "scissors (2 ingots)"], "tongs": ["Tools", "tongs (1 ingots)"],
         "shovel": ["Tools", "shovel (4 ingots)"], "lockpick": ["Tools", "lockpick (1 ingots)"]}
COST = {"scissors": 2, "tongs": 1, "shovel": 4, "lockpick": 1}
SELL_WORDS = ("scissors", "lockpick")
TOOL_NAMES = ("tinker's tools", "tinker tools", "tool kit")


def choose(skill: float, dig_tools: int, tongs: int) -> str | None:
    """The item to make at this Tinkering (DefTinkering.cs ranges; the success chance is (skill - min) / (max - min), CraftItem): its own tools once
    they succeed half the time (tongs 35-85 from 60, a shovel 40-90 from 65), else what teaches and sells: scissors (5-55) below 50, lockpicks
    (45-95) to 95. At Tinkering 37.8 BotSmithBR failed 5 tongs of 5, about 6% each (2026-11-07 19:06)."""
    if 60.0 <= skill < 85.0 and tongs < TONGS_KEPT:
        return "tongs"
    if 65.0 <= skill < 90.0 and dig_tools == 0:
        return "shovel"
    if 5.0 <= skill < 50.0:
        return "scissors"
    if 50.0 <= skill < 95.0:
        return "lockpick"
    return None


def _crafter():
    import crafter as _cr                          # (at call time: crafter imports miner, which calls into this module)
    return _cr


class TinkerHands:
    """CrafterBot's menu code run with the Tinker's craft on any bot: what the adapter does not have itself (the client, the journal, the shared
    memory, the log, the shops) is the bot's. The bot's own cfg (a smith's, or none for a miner) is never touched."""

    def __init__(self, bot):
        cr = _crafter()
        self.__dict__["bot"] = bot
        self.__dict__["cfg"] = dict(cr.CRAFTS[19])
        for name in ("tool", "material", "count", "open_menu", "pick", "tool_shop_xy", "shop_xys"):
            self.__dict__[name] = getattr(cr.CrafterBot, name).__get__(self)
        for name in ("matname", "plain", "squash"):
            self.__dict__[name] = cr.CrafterBot.__dict__[name].__get__(self)

    def __getattr__(self, name):
        return getattr(self.__dict__["bot"], name)


def hands(bot):
    h = bot.__dict__.get("_tinker_hands")
    if h is None:
        h = bot.__dict__["_tinker_hands"] = TinkerHands(bot)
    return h


def wants(bot):
    try:
        import skillplan
        return bool(skillplan.wants(bot, "Tinkering"))
    except Exception:
        return False


def count_named(bot, word):
    return sum(1 for i in bot.c.backpack if word in (i.name or "").lower())


def session(bot, kept=INGOTS_KEPT):
    """One tinkering session (the module doc), or the sale at a Tinker; True when it acted. kept: iron ingots it leaves for its own work."""
    if not wants(bot) or bot.c.ghost or bot.threats(10) or time.time() < bot.facts.get("tinker_at", 0):
        return False
    h = hands(bot)
    sk = float((getattr(bot, "skill_values", None) or {}).get("Tinkering", 0) or 0)
    if sum(count_named(bot, w) for w in SELL_WORDS) >= SELL_AT and time.time() >= float(bot.facts.get("tinker_sell_fail_until", 0) or 0):
        return sell(bot)
    item = choose(sk, count_named(bot, "shovel") + count_named(bot, "pickaxe"), count_named(bot, "tongs"))
    if not item or h.count("iron ingot") < kept + COST[item]:
        return False
    bot.facts["tinker_at"] = time.time() + GAP
    if not any((i.name or "").lower() in TOOL_NAMES for i in bot.c.backpack):
        xy = h.tool_shop_xy()
        if xy is None or bot.c.gold < 40:
            return False
        bot.activity = "buying tinker's tools"
        got = bot.shop_at(xy, {"tinker's tools": 1}, budget=40)
        bot.log(f"tinker: bought tinker's tools {got}")
        return True
    bot.activity = f"tinkering {item}"
    h.__dict__["_need"] = COST[item]                          # material(): a stack that covers the item, not whatever the bot's own craft needs
    made = ok = 0
    for _ in range(SESSION):
        if bot.threats(10) or h.count("iron ingot") < kept + COST[item]:
            break
        n0 = count_named(bot, item.split()[0])
        bot.read_journal()
        menu = h.open_menu()
        for text in PATHS[item]:
            if not menu:
                break
            idx = bot.index_of(menu, text)
            if not idx:
                bot.close_menus([menu])
                menu = None
                break
            menu = h.pick(menu, idx)
        if menu:
            bot.close_menus([menu])
        time.sleep(2.5)
        made += 1
        if count_named(bot, item.split()[0]) > n0:
            ok += 1
    bot.ev("tinker", item=item, made=made, ok=ok, skill=round(sk, 1))
    bot.log(f"tinker: {ok} of {made} {item} made (Tinkering {sk:.1f})")
    return made > 0


def sell(bot):
    """The scissors and lockpicks to a Tinker (CRAFTS[19] shop roles)."""
    bot.facts["tinker_at"] = time.time() + GAP
    xy = hands(bot).tool_shop_xy()
    if xy is None:
        return False
    bot.activity = "selling tinkered tools"
    gold = bot.sell_items(xy, list(SELL_WORDS))
    if not gold:
        # the Tinker not reached, or nothing bought: tinkering goes on and the sale waits an hour. BotSmithBR sold for 0 three times in 32 minutes
        # (07:41-08:13) and each time the session was the sale, so it made nothing
        bot.facts["tinker_sell_fail_until"] = time.time() + 3600
    bot.ev("tinker_sold", gold=int(gold or 0))
    bot.log(f"tinker: sold scissors and lockpicks for {gold} gold")
    return True


def miner_tinker(bot):
    """At the forge after the smelt (MinerBot.r_sell), before the ingots go to the Blacksmith: a session on the fresh ingots."""
    try:
        return session(bot, kept=MINER_KEPT)
    except Exception as e:
        bot.log(f"tinker: {type(e).__name__}: {e}")
        return False


class TinkerSideMixin:
    def r_tinker(self):
        """A smith's session between crafts (the module doc)."""
        if self.cfg.get("craft") != "Blacksmith":
            return False
        return session(self, kept=INGOTS_KEPT)
