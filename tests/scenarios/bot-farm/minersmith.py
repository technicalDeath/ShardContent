"""The miner-smith (feature "miner_smith"): at the forge, after smelting, a Prospector turns its iron ingots into smithed goods at the anvil when that pays
better than selling the ingots, and sells the goods with the left-over ingots, as a UOR miner who had Blacksmithy did.

Why: a miner sells iron ingots to the Blacksmith at 4 gold (SBBlacksmith sell list, IronIngot 4). Under crafted-goods pricing a shop pays at least the
material cost x 1.25 for a smithed piece (CraftedGoodsPricing.VendorPays: ceil(5 x ingots x 1.25), IronIngot priced 5), about 6.25 gold an ingot, and a
failed craft uses up half the ingots (CraftItem.ConsumeRes, pre-UOTD: amount - amount / 2). With the success chance of the stock formula
(CraftItem.GetSuccessChance, DefBlacksmithy.GetChanceAtMin 0: (skill - min) / (max - min)) a piece pays over selling its ingots from about 47% (4.25 x chance
> 2), so at Blacksmithy 10 a buckler (-25..25, 70%) gives about 5.2 gold an ingot used against 4, and at 37 a metal shield or a bronze shield more.

Nothing is copied from the Blacksmith brain: SmithHands borrows CrafterBot's own T2A menu code (open_menu, the menu pick, explore, craft_once, chance,
craft_ev, sale_price, learn_made) and runs it on the miner, through an adapter so the menu's pick() does not hide the miner's pick() (its pickaxe).

    smith(bot)        at the forge, after the smelt and the market hold: choose by expected gold per ingot (CrafterBot.craft_ev, held ingot worth 4,
                      tool wear counted), teaching pieces first when the skill plan wants Blacksmithy and they pay at least what selling does; buy tongs from
                      the Blacksmith (SBBlacksmith 13) when there are none; craft at the station between forge and anvil (places.station_near "smith")
                      while ingots, weight (CrafterBot.CRAFT_WEIGHT) and calm last. Returns the product words to sell beside "ingot".
    after_sale(bot)   a product made this visit that the buyer's list did not show is marked refused at that shop (price 0 in the shared memory), so
                      sale_price stops offering it; only pieces made this visit count (a newbied starter dagger is never a refusal).
Events: smith_plan {item, chance, ev, per_ingot, why}, smith_done {crafts, made, failed, ingots, expected}, smith_skip {why}, smith_tool {bought}.
"""
from __future__ import annotations

import json
import os
import re
import time

import crafter as _cr
import skillplan

CrafterBot = _cr.CrafterBot
SMITH = dict(_cr.CRAFTS[16], tool_alt=("smith's hammer",))   # a copy: CRAFTS dicts are shared by every crafter. Tongs or a smith's hammer (DefBlacksmithy tools)
TOOL_PRICE = 13           # tongs at the Blacksmith (SBBlacksmith GenericBuyInfo Tongs 13; tools stay at stock price, CraftedGoodsPricing.KeptAtStock)
TOOL_USES = 50            # mean uses of a new tool: BaseTool(itemID) is RandomMinMax(25, 75)
TOOL_WEAR = TOOL_PRICE / TOOL_USES                 # gold of tool worn away by one craft (0.26)
TOOL_RESERVE = 12         # gold kept after buying tongs: one dig tool (a shovel 12 at the Tinker, SBTinker; a pickaxe 12, shard-rules shopPrices)
MIN_INGOTS = 3            # the cheapest era piece (dagger, 3 ingots, DefBlacksmithy)
RELEARN = 4.0             # skill points after which the menu is looked at again (CrafterBot.r_craft's own rule) ...
RELEARN_S = 1500          # ... or seconds, when the piece chosen is not on the learned menu (r_craft looks again after 1500 s; the menu hides what the pack's
                          # ingots do not cover, T2ACraftSystem.CanCraftItem, so a menu learned with few ingots misses the dearer pieces)
MENU_FAIL_S = 300         # s without smithing after the menu offered nothing (CrafterBot.r_craft's own pause, menu_empty_until)
MENU_FILE = "menu_map_smith.json"
META_FILE = "menu_map_smith.meta.json"
GAIN = re.compile(r"skill in .* has increased", re.I)
OK = re.compile(r"You create|You make|put .* in|exceptional", re.I)

# the era menu (T2A BlacksmithMenu.cs type lists, named as its FormatItemName names them): craft_data.json also holds the later expansions' pieces
ERA_SMITH = ("buckler", "bronze shield", "heater shield", "metal shield", "metal kite shield", "wooden kite shield",
             "broadsword", "cutlass", "dagger", "katana", "kryss", "longsword", "scimitar", "viking sword",
             "axe", "battle axe", "double axe", "executioners axe", "large battle axe", "two handed axe", "war axe",
             "bardiche", "halberd", "war fork", "short spear", "spear",
             "hammer pick", "mace", "maul", "war mace", "war hammer",
             "ringmail gloves", "ringmail legs", "ringmail arms", "ringmail chest", "chain coif", "chain legs", "chain chest",
             "bascinet", "close helm", "helmet", "norse helm", "plate helm", "plate arms", "plate gloves", "plate gorget", "plate legs", "plate chest",
             "female plate chest")


class SmithHands:
    """CrafterBot's menu code run on a miner: what the adapter does not have itself (the client, the journal, the shared memory, the log) is the bot's."""

    KEEP = CrafterBot.KEEP
    CRAFT_WEIGHT = CrafterBot.CRAFT_WEIGHT
    tool = CrafterBot.tool
    matname = CrafterBot.__dict__["matname"]
    plain = CrafterBot.__dict__["plain"]
    squash = CrafterBot.__dict__["squash"]
    material = CrafterBot.material
    count = CrafterBot.count
    open_menu = CrafterBot.open_menu
    pick = CrafterBot.pick                         # the menu answer (the miner's own pick() is its pickaxe)
    explore = CrafterBot.explore
    chance = CrafterBot.chance
    craft_ev = CrafterBot.craft_ev
    sale_price = CrafterBot.sale_price
    craft_once = CrafterBot.craft_once
    may_train = CrafterBot.may_train
    leather_on = CrafterBot.leather_on
    menu_names = CrafterBot.menu_names
    is_material = CrafterBot.is_material
    is_product = CrafterBot.is_product
    learn_made = CrafterBot.learn_made

    def __init__(self, bot):
        self.__dict__["bot"] = bot
        self.cfg = SMITH
        self.items = _cr.DATA["Blacksmith"]
        d = bot.dir
        self.menu_map_path = os.path.join(d, MENU_FILE)
        self.meta_path = os.path.join(d, META_FILE)
        self.made_names_path = os.path.join(d, "made_names_smith.json")
        self.made_as_path = os.path.join(d, "made_as_smith.json")
        self.menu_map, self.menu_map_backup = _load(self.menu_map_path, {}), {}
        self.made_names = set(_load(self.made_names_path, []))
        self.made_as = _load(self.made_as_path, {})
        meta = _load(self.meta_path, {})
        self.explored_at = (meta.get("t", 0), meta.get("skill", -100.0)) if self.menu_map else None
        self.bad_items = set()
        self.last_made = None
        self.skill = 0.0

    def __getattr__(self, name):
        return getattr(self.__dict__["bot"], name)

    # ---- the choice ----------------------------------------------------------------------------------------------------------------------------------

    def options(self, have, names=None):
        """Each piece this miner can make from `have` plain ingots: (name, item, chance, ev a craft, gold over selling a used ingot, teaches). ev is
        CrafterBot.craft_ev (sale price from the shared memory, else the shard's floor; held ingot worth HELD_VALUE 4, SBBlacksmith) less TOOL_WEAR; a
        piece every shop asked refused (craft_ev None) is out."""
        out = []
        plan_wants = skillplan.wants(self.bot, "Blacksmithy")
        held = [(i.name or "").lower() for i in self.c.backpack]
        for name in (names if names is not None else ERA_SMITH):
            it = self.items.get(name)
            if not it or it["resource"] != "IronIngot" or it["amount"] > have or name in self.bad_items:
                continue
            if any(name in h and h != name and not self.is_product(h) for h in held):
                continue                               # its name is inside a kit item's ("axe" in "pickaxe"): selling by that word would sell the kit
            ch = self.chance(it, self.skill)
            if ch <= 0:
                continue                               # the era menu does not list it (T2ACraftSystem.CanCraftItem: chance > 0)
            ev = self.craft_ev(name, it["amount"], ch)
            if ev is None:
                continue
            ev -= TOOL_WEAR
            used = it["amount"] * (ch + _cr.FAIL_LOSS * (1 - ch))      # ingots a craft uses up on average (the FAIL_LOSS of craft_ev)
            teaches = plan_wants and it["max"] > self.skill and ch >= _cr.TEACH_CHANCE
            out.append((name, it, ch, ev, ev / used, teaches))
        return out

    def choose(self, have, names=None):
        """The piece to make: one that teaches (the plan wants Blacksmithy) and pays at least what selling its ingots does, best per ingot; else the best
        paying per ingot; else, with TRAIN_RESERVE in pack and bank (CrafterBot.may_train, the crafters' own rule), a teaching piece at a loss, the least
        loss an ingot first (at the shard's floor price a piece at TEACH_CHANCE loses under a tenth of a gold an ingot; smith() stops training before the
        expected loss takes pack and bank under TRAIN_RESERVE). None: sell the ingots as they are."""
        opts = self.options(have, names)
        free = [o for o in opts if o[5] and o[3] >= 0]
        paying = [o for o in opts if o[3] > 0]
        if free:
            return max(free, key=lambda o: o[4]) + ("teaches and pays",)
        if paying:
            return max(paying, key=lambda o: o[4]) + ("pays",)
        train = [o for o in opts if o[5]]
        if train and self.may_train():
            return max(train, key=lambda o: o[4]) + ("training",)
        return None


def _load(path, default):
    try:
        return json.load(open(path, encoding="utf-8"))
    except (OSError, ValueError):
        return default


def hands(bot):
    h = bot.__dict__.get("_smith_hands")
    if h is None:
        h = bot.__dict__["_smith_hands"] = SmithHands(bot)
    h.skill = (getattr(bot, "skill_values", None) or {}).get("Blacksmithy", 0.0)
    return h


def ingots(h):
    return h.count("iron ingot")


def skip(bot, why):
    seen = bot.__dict__.setdefault("_smith_skip", {})
    if time.time() - seen.get(why[:40], 0) > 600:
        seen[why[:40]] = time.time()
        bot.log(f"miner-smith: {why}")
        bot.ev("smith_skip", why=why)
    return []


def get_tool(bot, h):
    """Tongs from the Blacksmith of this smithy when the miner has no smithing tool. False when none could be had."""
    if h.tool() is not None:
        return True
    if bot.c.gold < TOOL_PRICE + TOOL_RESERVE or time.time() < bot.facts.get("smith_tool_fail_until", 0):
        return False
    bot.activity = "buying tongs"
    got = bot.shop_at(bot.where1(("smith",), item="tongs"), {"tongs": 1}, budget=TOOL_PRICE + 2)
    bot.ev("smith_tool", bought=bool(got))
    if not got:
        bot.facts["smith_tool_fail_until"] = time.time() + 1800
        return False
    bot.c.open_backpack()
    return h.tool() is not None


def learn_menu(bot, h, want=None):
    """The era menu, learned from the client once (CrafterBot.explore) and again after RELEARN points of Blacksmithy, or after RELEARN_S when the piece
    wanted is not on it; kept in MENU_FILE with the skill it was learned at (META_FILE)."""
    if h.menu_map and h.explored_at and h.skill - h.explored_at[1] < RELEARN and (want in h.menu_map or time.time() - h.explored_at[0] < RELEARN_S):
        return True
    h.menu_map_backup = h.menu_map
    h.menu_map = {}
    bot.activity = "learning the smithing menu"
    found = h.explore()
    if found:
        json.dump({"t": round(time.time()), "skill": round(h.skill, 1)}, open(h.meta_path, "w", encoding="utf-8"))
    return bool(found)


def smith(bot):
    """At the smithy after the smelt: make what pays from the plain iron ingots. Returns the words of the pieces made this visit (to sell beside "ingot")."""
    if not bot.feature("miner_smith") or bot.threats(8) or bot.hp_pct() < 50 or time.time() < bot.facts.get("smith_menu_fail_until", 0):
        return []
    h = hands(bot)
    have = ingots(h)
    if have < MIN_INGOTS:
        return []
    first = h.choose(have)                               # from the era list: no walk, no shop and no menu for a choice that will not pay
    if first is None:
        return skip(bot, f"no piece pays over selling ingots at Blacksmithy {h.skill:.1f} ({have} ingots)")
    if first[-1] == "training" and bot.c.gold + bot.facts.get("bank_balance", 0) + first[3] < _cr.TRAIN_RESERVE:
        return skip(bot, f"training on {first[0]} would take the funds under the reserve ({_cr.TRAIN_RESERVE})")
    if bot.c.weight > bot.c.max_weight * h.CRAFT_WEIGHT:
        return skip(bot, f"too heavy to smith ({bot.c.weight}/{bot.c.max_weight})")
    if not get_tool(bot, h):
        return skip(bot, "no tongs and none bought")
    st = bot.station_near("smith")
    if st and max(abs(bot.c.x - st[0]), abs(bot.c.y - st[1])) > 2:
        bot.activity = "walking to the anvil"
        bot.c.gotoexact(*st).wait(timeout=60)
    if st and max(abs(bot.c.x - st[0]), abs(bot.c.y - st[1])) > 2:
        return skip(bot, f"could not reach the anvil at {st}")
    if not learn_menu(bot, h, first[0]):
        bot.facts["smith_menu_fail_until"] = time.time() + MENU_FAIL_S
        return skip(bot, "the smithing menu offered nothing")
    before = {i.serial for i in bot.c.backpack}
    made = failed = crafts = 0
    gold_expected = 0.0
    used0 = have
    pick = None
    learned = {}
    while True:
        bot.beat()
        have = ingots(h)
        if bot.threats(8) or bot.c.weight > bot.c.max_weight * h.CRAFT_WEIGHT or h.tool() is None:
            break
        if pick is None or have < pick[1]["amount"]:
            pick = h.choose(have, [n for n in ERA_SMITH if n in h.menu_map])
            if pick is None:
                break
            name, it, ch, ev, per, teaches, why = pick
            bot.log(f"miner-smith: making {name} ({why}): Blacksmithy {h.skill:.1f}, window {it['min']}-{it['max']}, chance {ch:.0%}, "
                    f"{ev:+.1f} gold a craft over selling the ingots ({per:+.2f} an ingot used), {have} ingots")
            bot.ev("smith_plan", item=name, chance=round(ch, 3), gain=round(ev, 2),        # not "ev": dlog's own key (TypeError, every plan, 2026-11-01)
                   per_ingot=round(per, 3), why=why, ingots=have)
            first_try = True
        name, it, ch, ev = pick[0], pick[1], pick[2], pick[3]
        if pick[-1] == "training" and bot.c.gold + bot.facts.get("bank_balance", 0) + gold_expected + ev < _cr.TRAIN_RESERVE:
            break                                   # training at a loss never takes pack and bank under the crafters' TRAIN_RESERVE
        h._need = it["amount"]
        bot.activity = f"smithing {name}"
        result = h.craft_once(name, first=first_try or h.last_made != name)
        first_try = False
        h.last_made = name
        crafts += 1
        ok = bool(OK.search(result or ""))
        made += ok
        failed += not ok
        bot.work += ok
        gold_expected += ev
        if ok and learned.get(name, 0) < 2:
            learned[name] = learned.get(name, 0) + 1
            h.learn_made(before, made=name)               # the piece's name in the pack ("chain coif" is a "chainmail coif"), as r_craft learns it
        bot.mem.record("craft", scope="prof", craft="Blacksmith", item=name, ok=ok, gain=bool(GAIN.search(result or "")),
                       exc=bool(re.search(r"exceptional", result or "", re.I)))
        if (result or "").startswith(("nomenu", "menu refused")):
            h.last_made = None
            h.bad_items.add(name)
            pick = None
            continue
        if re.search(r"not yet crafted", result or "", re.I):
            h.last_made = None                      # make-last works only after a success (CrafterBot.r_craft)
            continue
        if not ok and re.search(r"no ?mat|cannot|too heavy|not have|must|don't have the resources|silence", result or "", re.I):
            bot.log(f"miner-smith: stopped: {result}")
            if "tool" in (result or "").lower() or "silence" in (result or ""):
                h.bad_items.add(name)
            break
        if crafts >= 200:
            break                                   # (a runaway guard; a load of 25-50 ingots is 3-6 crafts)
    used = used0 - ingots(h)
    new = [i for i in bot.c.backpack if i.serial not in before and h.is_product(i.name)]
    bot.__dict__["_smith_made"] = {"serials": {i.serial for i in new}, "names": sorted({i.name.lower() for i in new})}
    if crafts:
        bot.log(f"miner-smith: {crafts} crafts, {made} made, {failed} failed, {used} ingots used, about {gold_expected:+.0f} gold over selling them")
        bot.ev("smith_done", crafts=crafts, made=made, failed=failed, ingots=used, expected=round(gold_expected, 1))
        bot.note("craft", "A miner with Blacksmithy smiths its ingots at the anvil beside the forge: a smithed piece sells for at least 1.25 x 5 gold an ingot "
                          "against the Blacksmith's 4 for the ingot itself.", key="minersmith")
    return sorted({i.name.lower() for i in new})


def after_sale(bot, xy):
    """The pieces made this visit still in the pack after the sale, of a kind the buyer's list did not show: refused at that shop (price 0)."""
    made = bot.__dict__.pop("_smith_made", None)
    if not made or not made["serials"] or xy is None:
        return []
    left = sorted({(i.name or "").lower() for i in bot.c.backpack if i.serial in made["serials"]})
    if not left:
        return []
    try:
        buys = bot.mem.state["world"]["vendors"].get(f"{xy[0]},{xy[1]}", {}).get("buys", {})
    except Exception:
        buys = {}
    refused = [n for n in left if n not in buys]
    if refused:
        bot.mem.record("vendor", xy=f"{xy[0]},{xy[1]}", name="", buys=[[n, 0] for n in refused])
        bot.log(f"miner-smith: the buyer at {xy[0]},{xy[1]} does not buy {refused}")
    return refused
