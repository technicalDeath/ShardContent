"""The decision core's errand tasks, phase 2 (docs/Bot-Farm-Decision-Core-Plan.md, the task table): sell, resupply, bank, rest, train, upgrade, camp and loot
as short behaviour trees with the hunt tree's shape (hunt_tree.py): a non-blocking travel to the place, then one act that reuses the rule list's own code
(r_sellgear / r_sellmeat / r_sellloot, r_resupply, visit_bank, bandage_self, the training dummy, r_upgrade, the hunt cycle bound to one spawner, the loot
step) standing where that code's own walk is a step or two. The NEEDS decide when an errand beats hunting (task_core.candidates): a need is a
(task, urgency, destination, budget) the bot's state raises; urgency 1.0 is "as good as the best hunt", 2.0 twice as pressing. A done errand is
judged by its act (the need met: event task_end why "done" or "unmet"); an unmet errand rests that task UNMET_REST.

    sell      loot to sell: 3+ gear pieces, 6+ meat, gems, or heavy with any of it; urgency 1.2, 1.8 when over 70% weight
    resupply  bandages under 8 (urgency 2.0; 3.0 at none), an archer's ammunition under 25 (2.0; 3.0 at none), potions wanted with gold to spare (0.8)
    bank      gold over the purse limit (goals.purse_limit): 1.0 at the limit, up to 2.0 at twice it; overloaded with leftovers: 2.0
    rest      health under REST_AT with no hostile about, or out of breath: 1.5 (no walk; bandages, then standing)
    train     the main weapon skill under TRAIN_CAP (the dummy teaches that far): 0.9
    upgrade   the goal's gear piece affordable (goals.upgrade_choice / next_upgrade): 1.6 (it ends the goal)
    camp      a fresh kill of a worthwhile kind (facts["anchor"], the rule list's camp) with no hunt task running: the hunt tree bound to that spawner for two respawns; 0.9
    loot      a corpse of ours pending with no hunt task: 1.5 (short)
"""
from __future__ import annotations

import time
import items  # noqa: E402  (the shared item table)

import py_trees
from py_trees.common import Status

import hunt_tree
from hunt_tree import Ctx, Step, cheb

UNMET_REST = 1800.0
NOBUY_S = 1800.0
# what a fighter keeps in its pack, and how many (the owner, 2026-10-20: "make sure resupply adds ALL items a bot could use not just bandages"): bandages, the three
# potions the era shows by colour (Heal yellow, Refresh red, Cure orange; the rung's price of entry is 3 Heal and 2 Refresh), and an archer's ammunition (the old
# rule's own Bowyer trip). Each item is wanted below its LOW mark and bought up to its FULL mark; the shops are tried in order until each is met.
RESTOCK = (("=orange potion", 2, 3, ("alchemist", "healer")), ("bandage", 20, 30, ("healer",)), ("=yellow potion", 3, 5, ("healer", "alchemist")),
           ("=red potion", 2, 3, ("healer", "alchemist")))        # the Cure potion first (learning 2: snake poison killed three of the nine, none had a cure);
                                                                    # bandages to 40, not 60: twenty bots asking for 60 emptied Britain's one healer in a minute (2026-10-20 21:00)
CLOTH_BANDAGES = True           # the healer out of bandages: folded cloth from a tailor, cut with scissors into cut cloth, and cut again into bandages, one for one (Cloth.cs)
CLOTH_PRICE = 2                 # cut cloth and cloth at the Britain tailors (2 gold, 20 in stock: Chantal at 1467,1686)
CLOTH_MAX = 50                  # at most this many cloth bought for bandages in one visit (the dungeon trip wants 50 bandages)
POTION_NAMES = {"=yellow potion": ("yellow potion",), "=red potion": ("red potion",), "=orange potion": ("orange potion",)}
WITHDRAW = 300                  # carried gold under the cost of what is wanted with money in the bank: this much is taken out first
PRICE = {"bandage": 3, "=yellow potion": 15, "=red potion": 15, "=orange potion": 15}


ALCHEMIST_TRIES = 3


def alchemists(b):
    """The alchemists the gazetteer knows, nearest first, within FAR_SHOP of the bot."""
    try:
        import gazetteer as gz
        pts = [(int(p["x"]), int(p["y"])) for p in gz.get().by_role.get("alchemist", ())]
    except Exception:
        return []
    here = (int(b.c.x), int(b.c.y))
    return sorted((p for p in pts if max(abs(p[0] - here[0]), abs(p[1] - here[1])) <= FAR_SHOP), key=lambda p: max(abs(p[0] - here[0]), abs(p[1] - here[1])))


FAR_SHOP = 250


def weapon_shops(b):
    """Standing spots of Britain's weapon sellers (the gazetteer's smith, weaponsmith, bowyer), and the spots that did not sell a weapon lately."""
    try:
        shops = [tuple(p) for p in b.find_places(("smith", "weaponsmith", "bowyer"), n=8, per=8)]
    except Exception:
        shops = []
    bad = {tuple(int(v) for v in k.split(",")) for k, until in (b.facts.get("arm_bad_shop") or {}).items() if until > time.time()}
    return shops, bad


AMMO_SHOPS = (("bowyer",), ("provisioner",))   # a Provisioner sells arrows and bolts too (SBProvisioner: Arrow 2 gold, Bolt 5, 20 a restock)
FLETCH_MATS = 50                               # shafts and feathers a fletcher buys when the arrows are sold out (about 250 gold at 3 + 2)
SOLD_OUT_S = 3600                              # a shelf that is sold out comes back at the vendor's next restock (BaseVendor.RestockDelay 1 h), doubled (GenericBuyInfo.OnRestock)


def ammo_shop(b):
    """The Bowyer's standing spot, else a Provisioner's, skipping a shop sold out lately or that failed twice in a row (ammo_bad_shop)."""
    bad = {tuple(int(v) for v in k.split(",")) for k, until in (b.facts.get("ammo_bad_shop") or {}).items() if until > time.time()}
    try:
        # the exact ammunition name ("=arrow"): "arrow" matched every mage's shop by its Magic Arrow scroll, and BotRangerBR walked to four of them in turn, each
        # marked empty only after the walk (2026-11-01 20:38-21:09)
        for p in b.find_places(AMMO_SHOPS, n=8, item=ammo_item(b)):
            if tuple(p) not in bad and not any(max(abs(p[0] - q[0]), abs(p[1] - q[1])) <= 6 for q in bad):
                return tuple(p)
    except Exception:
        pass
    fs = tuple(b.FLETCH_SHOP)
    if any(max(abs(fs[0] - q[0]), abs(fs[1] - q[1])) <= 6 for q in bad):
        return None                                   # every ammunition shop known was found empty within the hour (SOLD_OUT_S)
    return b.FLETCH_SHOP


def ammo_item(b):
    """The Bowyer's ammunition for the weapon in hand or the pack: bolts for a crossbow, arrows otherwise."""
    try:
        bow = b.the_bow()
        if bow is not None and "crossbow" in (bow.name or "").lower():
            return "=bolt"
    except Exception:
        pass
    return "=arrow"


def carried(bot, item):
    """How many of a restock item the pack holds."""
    names = POTION_NAMES.get(item)
    try:
        if names:
            return sum((i.amount or 1) for i in bot.c.backpack if (i.name or "").lower() in names)
        return int(bot.bandages())
    except Exception:
        return 0


def trip_stock_wanted(bot):
    """The restock aims at the dungeon trip's kit (task_core.KIT: 10 Heal, 15 Cure, 50 bandages) for a bot that could use it: weapon skill at the kit's mark, a rung open or the
    tiers below paid, and money for the whole kit with 250 over. Otherwise the ordinary marks."""
    try:
        import task_core
        if not bot.feature("ladder"):
            return False
        if time.time() < float(bot.facts.get("kit_short_until", 0) or 0):
            return False                                  # the shelves could not fill the kit: after their restock (KIT_RETRY_S)                                  # only a bot that goes down (feature ladder) buys the dungeon kit: all twenty core fighters did, and Britain's
                                                          # shelves (10-15 Heal and Cure a vendor an hour; two Cure sellers seen) were bare for the four that go (2026-11-01)
        if float(bot.skill_values.get(bot.main_skill(), 0) or 0) < task_core.KIT["skill"]:
            return False
        paid = sum(float((bot.facts.get("rung_kills") or {}).get(str(t), 0) or 0) for t in (2, 3))
        if task_core.rung(bot) < 1 and paid < task_core.RUNG_PAY:
            return False
        money = (bot.c.gold or 0) + (bot.facts.get("bank_balance", 0) or 0)
        cost = task_core.KIT["heal"] * PRICE["=yellow potion"] + task_core.KIT["cure"] * PRICE["=orange potion"] + task_core.KIT["bandages"] * PRICE["bandage"]
        return money >= cost + 250
    except Exception:
        return False


def marks(bot):
    """((item, low, full, roles), ...): the restock's marks, raised to the dungeon trip's kit when trip_stock_wanted."""
    if not trip_stock_wanted(bot):
        return RESTOCK
    import task_core
    k = task_core.KIT
    return (("=orange potion", k["cure"], k["cure"], ("alchemist", "healer")), ("bandage", k["bandages"], k["bandages"], ("healer",)),
            ("=yellow potion", k["heal"], k["heal"], ("healer", "alchemist")), ("=red potion", k["refresh"], k["refresh"] + 1, ("healer", "alchemist")))


def restock_wants(bot):
    """{item: amount to buy} of everything below its LOW mark, up to FULL."""
    out = {}
    for item, low, full, _roles in marks(bot):
        n = carried(bot, item)
        if n < low:
            out[item] = full - n
    return out

ERRAND_NEAR = 3
KIT_RETRY_S = 3600              # BaseVendor.RestockDelay: a vendor restocks an hour after its last restock, when next opened
REST_AT = 50                    # the rest errand below this health (the hunt tree rests itself between 50 and 65 with nothing about)
REST_TO = 75
TRAIN_CAP = 30.0
AMMO_MONEY_STEP = 20             # an ammunition errand that came back unmet runs again once gold plus bank has changed by this much (the Watcher, 2026-10-21)
ARM_URGENCY = 2.5               # a fighter that cannot fight (no weapon of its skill, or a worn one) is pressing: it interrupts a hunt
FIST_BUY = 100                  # gold at which a broke archer (fists, no arrows) goes to the Bowyer: it buys ~50 arrows and takes the bow back (hunter.fists_check at REARM)
PROVISIONED_SKIPS = ("resupply", "ammo", "arm", "upgrade", "rune_buy")          # (fletch stays: it works on what the pack holds, no purchase)      # feature "provisioned" (the owner, 2026-10-21): staff gives the kit, the bot hunts with it
GATHER_FUNDS = 100              # a bot with fewer gold than this (carried and banked), and no way to hunt for coin, chops logs and sells them (the Watcher, 2026-10-21)
GATHER_LOGS = 30                # logs wanted before the walk to the Carpenter
GATHER_REST = 900.0             # a gather errand that found no tree or no buyer rests this long
BUDGET = {"gather": 900.0, "ammo": 240.0, "arm": 300.0, "fletch": 240.0, "sell": 300.0, "resupply": 360.0, "bank": 120.0, "rest": 300.0, "train": 600.0, "upgrade": 180.0, "loot": 120.0, "rune_buy": 180.0}
ERRANDS = ("gather", "ammo", "arm", "fletch", "sell", "resupply", "bank", "rest", "train", "upgrade", "camp", "loot", "rune_buy")


# ---- the needs ------------------------------------------------------------------------------------------------------------------------------------

def _loot_to_sell(bot):
    gear = len(bot.gear_loot()) if hasattr(bot, "gear_loot") else 0
    meat = sum((i.amount or 1) for i in bot.c.backpack if "raw " in (i.name or "").lower())          # "cut of raw ribs" too (BardBR carried 50 of them, 8 gold each at the Butcher, and 12 gold)
    gems = sum(1 for i in bot.c.backpack if any(w in (i.name or "").lower() for w in ("amethyst", "star sapphire", "ruby", "sapphire", "emerald", "diamond", "amber", "citrine", "tourmaline")))
    return gear, meat, gems


CLOTHES_PRICE = {"robe": 40, "cloak": 35, "boots": 75, "hat": 30, "sash": 10}      # what the shared vendor lists show the shops pay (2026-10-21)


def is_death_robe(i):
    """The robe a resurrection gives (hue 2301, newbied): never sold, never counted."""
    try:
        return int(getattr(i, "hue", 0) or 0) == 2301 or bool(getattr(i, "newbied", False))
    except Exception:
        return False


def _robes(bot):
    """Clothes loose in the pack that a Tailor buys (robe 40, cloak 35, thigh boots 75, hat 30, sash 10: monsters drop them; MaceBR carried 30 robes and had 9 gold). Worn ones are not in the pack.
    Off (the Watcher, 2026-10-29): 0 of 48 robe sales went through in two hours ("You have nothing I would be interested in": the loose clothes are the newbied
    starters, which no vendor takes), each a walk of one to two minutes; a monster's robe fetches 9 at the stock Tailor (SBTailor), not 40."""
    return 0
    return sum((i.amount or 1) for i in bot.c.backpack if any(w in (i.name or "").lower() for w in CLOTHES_PRICE) and not is_death_robe(i))


def _clothes_value(bot):
    return sum((i.amount or 1) * next((p for w, p in CLOTHES_PRICE.items() if w in (i.name or "").lower()), 0) for i in bot.c.backpack if not is_death_robe(i))


def drop_death_robes(bot):
    """Death robes in the pack (the engine gives one per resurrection; newbied, no shop takes them) are dropped on the ground; event death_robe_dropped. Returns how many."""
    n = 0
    for i in list(bot.c.backpack):
        if (i.name or "").lower() in ("robe", "death robe") and is_death_robe(i):
            try:
                if bot.drop_to_ground(i):
                    n += int(i.amount or 1)
            except Exception:
                break
    if n:
        bot.ev("death_robe_dropped", n=n)
    return n


REAGENT_WORDS = ("black pearl", "blood moss", "garlic", "ginseng", "mandrake", "nightshade", "sulfurous ash", "spider's silk", "empty bottle")
SELL_VALUE = 300                # held loot worth this much at the known prices raises the sell errand. Derived (the Watcher, 2026-10-29): a trip costs T = 4.5 min (295 min over 65
                                # sells, 13:31-16:00) of hunting worth r = 6 gold a minute (+360 a bot-hour net), and carried loot is lost at p = 0.0037 deaths a minute (provisioned bots
                                # skip the corpse run); trip cost plus expected loss per gold is least at V = r * sqrt(2T / p) = 6 * sqrt(2 * 4.5 / 0.0037) ~ 300. It was 150, and the
                                # item counts below (6 meat ~ 47 gold, 25 feathers ~ 25, one gem) raised a 4.5-minute trip for less than it cost


def _reagents(bot):
    """Reagents loose in the pack of a bot that does not cast (a mage keeps them): the Mage or Alchemist buys them (about 3 gold each)."""
    try:
        if float(bot.skill_values.get("Magery", 0) or 0) >= 30 or float(bot.skill_values.get("Alchemy", 0) or 0) >= 30 or float(bot.skill_values.get("Inscription", 0) or 0) >= 30:
            return 0
    except Exception:
        pass
    return sum((i.amount or 1) for i in bot.c.backpack if any(w in (i.name or "").lower() for w in REAGENT_WORDS))


SELL_R, SELL_P, SELL_T_MIN = 6.0, 0.0037, 4.5   # gold a hunting minute, deaths a minute, the measured mean trip (minutes): SELL_VALUE's sources (2026-10-29)


def sell_value(bot):
    """SELL_VALUE for this bot where it stands: V = r * sqrt(2T / p) with T its round trip home (straight tiles x 2 / task_core.walk_rate), never under the
    measured mean trip; a bot hunting 480 tiles out carries more before it walks back (the owner's widening, 2026-10-29)."""
    try:
        import math
        import task_core
        hx, hy = bot.home_centre()
        tiles = max(abs(int(bot.c.x) - hx), abs(int(bot.c.y) - hy))
        trip = max(SELL_T_MIN, 2.0 * tiles / task_core.walk_rate(bot))
        return SELL_R * math.sqrt(2.0 * trip / SELL_P)
    except Exception:
        return SELL_VALUE


def held_value(bot):
    """Gold the sellable loot in the pack would fetch: the goods at the shops' prices (items.py: meat by its cut, leather 5, a hide cut into leather 5, a feather
    1.0; until 2026-10-30 a guessed feather 1.5, meat 7, hide 3, leather 4), reagent 3, gem 40, gear 15, robes 9."""
    gear, meat, gems = _loot_to_sell(bot)
    hides, leather, feathers = _carved(bot)
    goods = sum(float(i.amount or 1) * items.sale_price(i.name) for i in bot.c.backpack if items.is_meat(i.name) or items.is_leather(i.name) or items.is_feather(i.name))
    return goods + hides * items.HIDE_CUT_VALUE + _reagents(bot) * 3 + gems * 40 + gear * 15 + _clothes_value(bot)


def _carved(bot):
    """(hides, leather, feathers) in the pack: a low-skill hunter's income (hides cut into leather at the Tanner, feathers at the Bowyer)."""
    hides = sum((i.amount or 1) for i in bot.c.backpack if items.is_hide(i.name))
    leather = sum((i.amount or 1) for i in bot.c.backpack if items.is_leather(i.name))
    feathers = sum((i.amount or 1) for i in bot.c.backpack if items.is_feather(i.name))
    return hides, leather, feathers


def cut_hides(b, st):
    """Scissors on every pile of hides (bought at the Tailor when none is carried): leather. Returns the leather made."""
    scissors = next((i for i in b.c.backpack if "scissors" in (i.name or "").lower()), None)
    if scissors is None:
        if b.c.gold < 20 or st.get("scissors_tried"):
            return 0
        st["scissors_tried"] = True
        try:
            b.shop_at(b.where1(("tailor", "weaver")), {"scissors": 1}, budget=30)
        except Exception:
            pass
        scissors = next((i for i in b.c.backpack if "scissors" in (i.name or "").lower()), None)
        if scissors is None:
            return 0
    before = _carved(b)[1]
    for _ in range(12):
        pile = next((i for i in b.c.backpack if "hide" in (i.name or "").lower()), None)
        if pile is None:
            break
        b.c.events.drain()
        b.c.use(scissors.serial)
        try:
            from uo import Event
            if b.c.wait_for(Event.TARGET_REQUEST, timeout=4) is None:
                break
        except Exception:
            pass
        b.c.target(pile.serial)
        time.sleep(1.2)
        b.read_journal()
    made = _carved(b)[1] - before
    if made:
        b.ev("cut_hides", leather=made)
    return made


def cloth_shops(b):
    """Standing spots of shops that sell cut cloth or cloth, nearest first: the shared memory's vendor records (what was seen on their lists), else the gazetteer's tailors and weavers."""
    out = []
    try:
        for word in ("cut cloth", "cloth"):
            for _price, xy, item, _qty in b.mem.vendor_selling(word):
                if "bolt" in item or "folded" in item and word == "cloth":
                    continue
                pt = tuple(int(v) for v in xy.split(","))
                if pt not in out:
                    out.append(pt)
    except Exception:
        pass
    here = (int(b.c.x), int(b.c.y))
    out.sort(key=lambda p: max(abs(p[0] - here[0]), abs(p[1] - here[1])))
    try:
        for pt in b.find_places(("tailor", "weaver"), n=3, per=1):
            if pt not in out:
                out.append(pt)
    except Exception:
        pass
    return out[:2]


def cloth_bandages(b, st, need):
    """Bandages made the way a player makes them when the healer has none (the Watcher, 2026-10-21: the healer showed none at 39 reads, the provisioners sell none): cut cloth
    (2 gold) or cloth from a tailor, scissors bought there or at a tinker when none is carried, cut with the scissors (cut cloth into bandages, cloth into cut cloth first).
    At most 40 bought, within budget. Returns the bandages made."""
    need = min(int(need), CLOTH_MAX)
    if need <= 0 or (b.c.gold or 0) < CLOTH_PRICE * 5:
        return 0
    before = int(b.bandages())
    shops = cloth_shops(b)
    if not shops:
        b.log("errand resupply: no tailor known to buy cloth from")
        return 0
    budget_for = lambda n: min((b.c.gold or 0) * 3 // 4, n * CLOTH_PRICE + 10)
    for shop in shops:
        b.beat()
        if not any("scissors" in (i.name or "").lower() for i in b.c.backpack):
            for where in (shop, b.where1(("tinker",))):
                try:
                    b.shop_at(where, {"scissors": 1}, budget=30)
                except Exception:
                    pass
                if any("scissors" in (i.name or "").lower() for i in b.c.backpack):
                    break
        if not any("scissors" in (i.name or "").lower() for i in b.c.backpack):
            continue
        try:
            owned = sum((i.amount or 1) for i in b.c.backpack if (i.name or "").lower() in ("cut cloth", "cloth"))
            if owned < need:
                b.shop_at(shop, {"=cut cloth": need - owned}, budget=budget_for(need - owned))
            owned = sum((i.amount or 1) for i in b.c.backpack if (i.name or "").lower() in ("cut cloth", "cloth"))
            if owned < need:
                b.shop_at(shop, {"=cloth": need - owned}, budget=budget_for(need - owned))
        except Exception as e:
            b.log(f"errand resupply: cloth: {type(e).__name__}: {e}")
        if any((i.name or "").lower() in ("cut cloth", "cloth") for i in b.c.backpack):
            break
    scissors = next((i for i in b.c.backpack if "scissors" in (i.name or "").lower()), None)
    if scissors is None:
        b.log("errand resupply: no scissors to be had for the cloth")
        return 0
    for word in ("cloth", "cut cloth"):                         # cloth first (into cut cloth), then cut cloth (into bandages)
        for _ in range(8):
            pile = next((i for i in b.c.backpack if (i.name or "").lower() == word), None)
            if pile is None:
                break
            name0, n0 = pile.name, pile.amount
            b.c.events.drain()
            b.c.use(scissors.serial)
            try:
                from uo import Event
                if b.c.wait_for(Event.TARGET_REQUEST, timeout=4) is None:
                    break
            except Exception:
                pass
            b.c.target(pile.serial)
            time.sleep(1.2)
            b.read_journal()
            b.beat()
            again = next((i for i in b.c.backpack if i.serial == pile.serial), None)
            if again is not None and again.name == name0 and again.amount == n0:
                break                                               # the scissors did nothing to it
    made = int(b.bandages()) - before
    if made > 0:
        b.ev("cloth_bandages", made=made)
        b.log(f"errand resupply: cut {made} bandages from cloth")
    return made


def needs(bot, hunting=False):
    """[(task, urgency, dest (x, y) or None, budget_s, detail)] this bot's state raises now; hunting=True while a hunt task runs (camp and loot are then the hunt's)."""
    out = []
    now = time.time()
    f = bot.facts
    try:
        heavy = bot.c.weight > bot.c.max_weight * 0.7
    except Exception:
        heavy = False
    wstate = "ok"
    try:
        wstate = bot.weapon_state()
    except Exception:
        pass
    if wstate in ("none", "wrong", "worn") and now - f.get("arm_task_at", 0) > 300:
        try:
            shops, bad = weapon_shops(bot)
            best = bot.next_weapon((bot.c.gold or 0) + (f.get("bank_balance", 0) or 0), replace=(wstate == "worn"), shops=shops, avoid=bad)
        except Exception:
            best = None
        if best:
            out.append(("arm", ARM_URGENCY, best[3], BUDGET["arm"], f"{best[4]} for {best[2]} gold ({wstate})"))
    try:                                                           # the broke bot's livelihood: logs from the nearest trees to the Carpenter (1 gold a log, 2 a board)
        funds = (bot.c.gold or 0) + (f.get("bank_balance", 0) or 0)
        hands = bool(f.get("fists")) or wstate in ("none", "wrong") or (bot.bow_kind() and bot.ammo() == 0)
        loot_left = _loot_to_sell(bot)[1] >= 6 or _robes(bot) >= 3 or _loot_to_sell(bot)[0] >= 3
        if funds < GATHER_FUNDS and hands and not loot_left and now - f.get("gather_task_at", 0) > GATHER_REST and bot.hp_pct() >= 70:
            has_hat = any("hatchet" in (i.name or "").lower() for i in list(bot.c.backpack) + list(bot.c.equipped))
            if (has_hat or (bot.c.gold or 0) >= 16) and bot.near_trees(1):
                out.append(("gather", 1.1, bot.where1(("carpenter",)), BUDGET["gather"], f"{funds} gold, {'hatchet' if has_hat else 'no hatchet'}, hands only"))
    except Exception:
        pass
    gear, meat, gems = _loot_to_sell(bot)
    hides, leather, feathers = _carved(bot)
    robes = _robes(bot)
    nobuy = {k: t for k, t in (f.get("sell_nobuy") or {}).items() if now - t < NOBUY_S}        # a category no shop in reach took: not raised again for NOBUY_S
    if nobuy:
        gear = 0 if "gear" in nobuy else gear
        meat = 0 if "meat" in nobuy else meat
        gems = 0 if "gems" in nobuy else gems
        hides = 0 if "leather" in nobuy else hides
        leather = 0 if "leather" in nobuy else leather
        feathers = 0 if "feathers" in nobuy else feathers
        robes = 0 if "robes" in nobuy else robes
    reagents = _reagents(bot)
    if nobuy and "reagents" in nobuy:
        reagents = 0
    value = held_value(bot)
    if nobuy:
        value = 0 if len(nobuy) >= 3 else value                  # most categories refused lately: the value alone does not raise it
    if (value >= sell_value(bot) or (heavy and value >= 20) or (heavy and (gear or meat or hides or leather))) and now - f.get("sold_task_at", 0) > 300:
        dest = None
        try:
            if gear:
                dest = bot.GEAR_SHOPS[0] if bot.GEAR_SHOPS else None
            elif meat:
                dest = bot.BUTCHER
            elif robes:
                dest = bot.where1(("tailor", "weaver"))
            elif reagents and not (hides or leather or feathers):
                dest = bot.where1(("mage", "alchemist"))
            elif feathers and not (hides or leather):
                dest = bot.where1(("bowyer",))
            else:
                dest = bot.where1(("jeweler", "jeweller", "gem"))
        except Exception:
            dest = None
        out.append(("sell", 1.8 if heavy else 1.2, dest, BUDGET["sell"], f"{gear} gear, {meat} meat, {gems} gems, {hides} hides, {leather} leather, {feathers} feathers, {robes} robes"))
    try:
        bandages = bot.bandages()
    except Exception:
        bandages = 99
    archer = False
    try:
        archer = bool(bot.bow_kind())
    except Exception:
        pass
    ranged = (getattr(bot, "ranged", False) and not f.get("fists")) or archer          # an archer in fist mode needs arrows too: it buys them as soon as it has FIST_BUY gold (fix C)
    try:
        ammo = bot.ammo() if ranged else 99
    except Exception:
        ammo = 99
    can_make = 0
    try:
        can_make = bot.can_make_arrows()
    except Exception:
        pass
    low_ammo = ranged and ammo < 25 and can_make < 25
    wants = restock_wants(bot)
    money = (bot.c.gold or 0) + (f.get("bank_balance", 0) or 0)
    if f.get("fists") and low_ammo and money < FIST_BUY:
        low_ammo = False                                          # not enough yet: a broke archer earns first (livestock, the fletcher's tools), it does not walk to a shop it cannot pay
    if low_ammo and money >= 24:                                  # ammunition is its own errand: an unmet bandage or potion run must not stop it (ArcherCR and BardAdvR sat out 15 minutes with money and no arrows)
        try:
            dest_a = ammo_shop(bot)
        except Exception:
            dest_a = None
        if dest_a is not None or ammo == 0:
            # every shop found empty within the hour and arrows still carried: it hunts with them until a shelf restocks. BotBardBR broke off four tours in
            # 25 minutes for Bowyers that had none (15, 13, 13 and 10 arrows, 28,205 gold banked; 2026-11-01 19:39-19:54)
            out.append(("ammo", 3.0 if ammo == 0 else 2.0, dest_a or tuple(bot.FLETCH_SHOP), BUDGET["ammo"], f"{ammo} arrows, {money} gold with the bank"))
    if (bandages < 8 or wants) and money >= 40 and now - f.get("shop_at", 0) > 300:
        urg = 3.0 if bandages == 0 else 2.0 if bandages < 8 else 0.8
        try:
            dest = bot.where1(("healer",))
        except Exception:
            dest = None
        out.append(("resupply", urg, dest, BUDGET["resupply"], f"bandages {bandages}, ammo {ammo}, wants {', '.join(f'{k.strip(chr(61))} {v}' for k, v in wants.items()) or 'none'}"))
    try:                                                           # fix C: arrows from what the pack holds (feathers, wood or shafts, the fletcher's tools): an archer with no arrows makes some
        if archer and ammo < 120 and bot.skill_values.get("Bowcraft/Fletching", 0) >= 25 and now - f.get("fletch_task_at", 0) > 600:
            names = [(i.name or "").lower() for i in list(bot.c.backpack) + list(bot.c.equipped)]
            feathers = sum((i.amount or 1) for i in bot.c.backpack if (i.name or "").lower() in ("feather", "feathers"))
            wood = sum((i.amount or 1) for i in bot.c.backpack if (i.name or "").lower() in ("shaft", "shafts", "board", "boards", "log", "logs"))
            has_hat = any("hatchet" in n for n in names)
            # feathers become arrows (the owner, 2026-10-21): with ammunition low, or with a pile of feathers (10+) to use; no wood but a hatchet and 25 feathers: it chops first
            if "arrow fletching" in names and ammo_item(bot) == "=arrow" and ((ammo < 10 and feathers >= 3) or feathers >= 10) and (wood >= 1 or (has_hat and feathers >= 25)):
                out.append(("fletch", 1.6, None, BUDGET["fletch"], f"{feathers} feathers, {wood} wood or shafts, {ammo} arrows"))
    except Exception:
        pass
    try:
        import goals
        limit = goals.purse_limit(bot, 250)
    except Exception:
        limit = 250
    gold = bot.c.gold or 0
    overloaded = f.get("bank_heavy") and bot.c.weight > bot.c.max_weight * 0.9
    if (gold > limit or overloaded) and now - f.get("banked_at", 0) > 600 and now - f.get("bank_fail", 0) > 180:
        try:
            dest = bot.bank_xys()[0]
        except Exception:
            dest = None
        out.append(("bank", 2.0 if overloaded else min(2.0, 1.0 + (gold - limit) / max(limit, 1)), dest, BUDGET["bank"], f"gold {gold}, limit {limit}"))
    try:
        tired = bot.tired()
    except Exception:
        tired = False
    try:
        import task_core
        bare = task_core.hurt_bare(bot)
    except Exception:
        bare = False
    if bare:
        try:
            dest = bot.home_refuges()[0]
        except Exception:
            dest = None
        out.append(("rest", 2.5, dest, BUDGET["rest"], f"hp {bot.hp_pct():.0f}% and nothing to heal with: home"))      # learning 3: pressing, even in a hunt
    elif (bot.hp_pct() < REST_AT or tired) and not bot.threats(10) and not hunting:
        out.append(("rest", 1.5, None, BUDGET["rest"], f"hp {bot.hp_pct():.0f}%" + (", tired" if tired else "")))
    try:
        skill = float(bot.skill_values.get(bot.main_skill(), 0) or 0)
    except Exception:
        skill = 99.0
    if skill < TRAIN_CAP and now - f.get("train_task_at", 0) > 1800:
        try:
            spots = bot.spots_for("butte" if ranged else "dummy", n=1)
        except Exception:
            spots = []
        if spots:
            out.append(("train", 0.9, spots[0], BUDGET["train"], f"{bot.main_skill()} {skill:.0f}"))
    if now - f.get("upgrade_at", 0) > 600 and bot.hp_pct() >= 70 and not (archer and ammo < 50) and wstate == "ok":          # fix D: ammunition first, then armour; and a working weapon before either
        try:
            import goals
            money = gold + (f.get("bank_balance", 0) or 0) - getattr(bot, "UPGRADE_RESERVE", 250)
            best = goals.upgrade_choice(bot, money) if goals.active(bot) else bot.next_upgrade(money)
        except Exception:
            best = None
        skip = f.get("upgrade_skip") or {}
        if best and now < skip.get(best[2], 0):
            best = None                                              # M3: an upgrade that came back unmet twice rests 30 minutes
        if best:
            out.append(("upgrade", 1.6, tuple(best[4]), BUDGET["upgrade"], f"{best[2]} for {best[3]}"))
    try:
        import runes as runes_mod
        if (bot.rune_on() and bot.rune_able() and not bot.rune_blanks() and bot.rune_count() < runes_mod.RUNES_WANT
                and bot.c.gold >= runes_mod.BUY_FLOOR + runes_mod.BUY_N * runes_mod.PRICE_GUESS and now - f.get("rune_buy_at", 0) > runes_mod.BUY_EVERY):
            out.append(("rune_buy", 1.1, bot.mage_shop_xy(), 180.0, f"{bot.rune_count()} runes, {bot.c.gold} gold"))
    except Exception:
        pass
    if not hunting:
        a = f.get("anchor")
        if a and now - a.get("last", 0) < 360:
            try:
                import task_core
                mn, mx = task_core.spawn_delay_at(a["x"], a["y"])
            except Exception:
                mn, mx = 300.0, 600.0
            out.append(("camp", 0.9, (a["x"], a["y"]), 2 * mx, f"{a.get('kills', 0)} kills at {a['x']},{a['y']}"))
        pend = (f.get("task") or {}).get("state", {}).get("corpses") if f.get("task") else None
        if pend:
            out.append(("loot", 1.5, None, BUDGET["loot"], f"{len(pend)} corpses"))
    try:
        if bot.feature("provisioned"):                                # a provisioned bot is stocked by staff: it never raises a supply errand (sell, bank, gather and the rest stay: they are income)
            out = [n for n in out if n[0] not in PROVISIONED_SKIPS]
    except Exception:
        pass
    out.sort(key=lambda n: -n[1])
    return out


# ---- the trees -------------------------------------------------------------------------------------------------------------------------------------

class ErrandTravel(hunt_tree.Travel):
    """The hunt tree's travel to one spot, arrived within ERRAND_NEAR tiles (no fights on the road for an errand with a pressing need; the reflexes still run)."""

    def update(self):
        c, task = self.ctx, self.ctx.task
        spots = task.get("spots") or []
        if not spots:
            task["arrived"] = task.get("arrived") or time.time()
            return Status.SUCCESS
        if not task.get("arrived") and cheb(c.here(), (spots[0][0], spots[0][1])) <= ERRAND_NEAR:
            task["arrived"] = time.time()
            self.ctx.bot.ev("task_arrived", task=task["task"], area=task["area"], mins=round((time.time() - task["t0"]) / 60, 1))
        if task.get("arrived"):
            return Status.SUCCESS
        task["_no_road"] = True
        task["near"] = ERRAND_NEAR                                # arrived means at the counter, not within the hunt's 15 tiles
        return super().update()

    def road_fight(self):
        return None


class Act(Step):
    """One errand's act, where the rule list's own code does the work (its walk is a step or two from here). SUCCESS when the need is met, FAILURE "unmet"."""

    def update(self):
        c, b, st, task = self.ctx, self.ctx.bot, self.ctx.st, self.ctx.task
        kind = task["task"]
        c.step = kind
        b.activity = f"errand: {kind}"
        try:
            ok = getattr(self, "do_" + kind)(b, st, task)
        except Exception as e:
            b.log(f"errand {kind}: {type(e).__name__}: {e}")
            ok = False
        if ok is None:
            return Status.RUNNING
        return Status.SUCCESS if ok else c.fail(kind, "unmet")

    def do_sell(self, b, st, task):
        """Sell by category at a buyer the memory knows, then the role's shop (a second shop when the first takes nothing); gear no shop takes is dropped."""
        gold0 = b.c.gold
        gems = ("amethyst", "star sapphire", "ruby", "sapphire", "emerald", "diamond", "amber", "citrine", "tourmaline")
        groups = []
        try:
            gear = sorted({(i.name or "").lower() for i in b.gear_loot()})
        except Exception:
            gear = []
        if gear:
            groups.append(("gear", gear, ("smith", "weaponsmith", "armorer", "cobbler")))
        if any("raw " in (i.name or "").lower() for i in b.c.backpack):
            groups.append(("meat", ["raw "], ("butcher",)))
        if _robes(b) >= 1:
            drop_death_robes(b)
            groups.append(("robes", list(CLOTHES_PRICE), ("tailor", "weaver", "cobbler")))
        if _reagents(b) >= 1:
            groups.append(("reagents", list(REAGENT_WORDS), ("mage", "alchemist")))
        if any(any(w in (i.name or "").lower() for w in gems) for i in b.c.backpack):
            groups.append(("gems", list(gems), ("jeweler", "jeweller", "gem")))
        if _carved(b)[0]:
            cut_hides(b, st)                                      # hides into leather first (owner, 2026-10-20: leather at 5 a piece)
        if _carved(b)[1]:
            groups.append(("leather", ["leather"], ("tanner", "tailor", "weaver")))
        if _carved(b)[2]:
            groups.append(("feathers", ["feather"], ("bowyer", "fletcher", "tanner")))
        sold = 0
        for label, words, roles in groups:
            shops = []
            for w in words:
                try:
                    for pr, xy, item in b.mem.vendor_buying(w):
                        pt = tuple(int(v) for v in xy.split(","))
                        if pr > 0 and pt not in shops:
                            shops.append(pt)
                except Exception:
                    pass
            try:
                if label != "robes":                                  # clothes only where a vendor's recorded list names them with a price (Jumoke's list holds no robe)
                    shops += [xy for xy in b.find_places(roles, n=2, per=1) if xy not in shops]
            except Exception:
                pass
            n_items = sum((i.amount or 1) for i in b.c.backpack if any(w in (i.name or "").lower() for w in words))
            # where this bot has sold this category first, and a shop that took nothing lately left out (the Watcher, 2026-10-29: BotFencerBR carried 1,000 gold
            # of leather, meat and feathers to the Tailor's door at 1388,1588, the best-priced record, never got in, and never reached the Butcher or the Tanner)
            good = (b.facts.get("shop_sold") or {}).get(label) or {}
            bad = (b.facts.get("shop_fail") or {}).get(label) or {}
            now_ = time.time()
            shops = [xy for xy in shops if now_ - float(bad.get(f"{xy[0]},{xy[1]}", 0)) > NOBUY_S]
            shops.sort(key=lambda xy: -int(good.get(f"{xy[0]},{xy[1]}", 0)))
            for xy in shops[:2]:
                try:
                    earned = b.sell_items(xy, words)
                except Exception as e:
                    b.log(f"errand sell: {label} at {xy}: {type(e).__name__}: {e}")
                    earned = 0
                key = f"{xy[0]},{xy[1]}"
                if earned and earned > 0:
                    sold += earned
                    b.ev("sale_task", what=label, gold=earned, shop=list(xy), items=n_items)
                    rec = b.facts.setdefault("shop_sold", {}).setdefault(label, {})
                    rec[key] = int(rec.get(key, 0)) + 1
                    break
                b.facts.setdefault("shop_fail", {}).setdefault(label, {})[key] = time.time()
            else:
                b.facts.setdefault("sell_nobuy", {})[label] = time.time()       # no shop took this category: the need is not raised for it again for NOBUY_S
                b.log(f"errand sell: no shop took the {label} (tried {len(shops[:2])}): not again for {int(NOBUY_S / 60)} min")
            if label == "gear":
                try:
                    left = b.gear_loot()
                    for it in left:
                        b.drop_to_ground(it)
                        b.facts.get("gear_looted", set()).discard(it.serial)
                    if left:
                        b.log(f"errand sell: dropped {len(left)} pieces no shop took")
                except Exception:
                    pass
        b.facts["sold_task_at"] = time.time()
        return sold > 0 or b.c.gold > gold0

    def do_resupply(self, b, st, task):
        """The restock, step by step, each shop once (the Watcher, 2026-10-21: BotMaceBR visited the healer three times and the alchemist twice and was killed for writing no
        status before it reached the tailor): money first (the bank, enough for the potions, the bandages and the cloth route), the Bowyer for an archer's arrows, the healer
        (bandages, Heal, Refresh), the alchemist (Cure, and whatever is still short), then the tailor's cloth for bandages when the healer had too few. A heartbeat is written
        between steps. Done only when the pack holds more than before."""
        b.facts["shop_at"] = 0                                   # the rule's own five-minute gap: this task is the decision
        def stock():
            try:
                ammo = b.ammo() if getattr(b, "ranged", False) else 0
            except Exception:
                ammo = 0
            return sum(carried(b, item) for item, *_ in RESTOCK) + ammo
        visited = st.setdefault("visited", [])
        def visit(xy, wanted, share=0.75):
            xy = tuple(int(v) for v in xy)
            if not wanted or xy in visited or (b.c.gold or 0) < 10:
                return
            visited.append(xy)
            b.beat()
            try:
                b.shop_at(xy, wanted, budget=max(10, int((b.c.gold or 0) * share)))
            except Exception as e:
                b.log(f"errand resupply: shop {xy}: {type(e).__name__}: {e}")
            b.beat()
        before = stock()
        wants = restock_wants(b)
        ranged = getattr(b, "ranged", False)
        try:
            ranged = ranged or bool(b.bow_kind())
        except Exception:
            pass
        try:
            low_ammo = ranged and b.ammo() < 25
        except Exception:
            low_ammo = False
        cost = sum(PRICE.get(k, 10) * v for k, v in wants.items()) + (CLOTH_MAX * CLOTH_PRICE + 15 if int(b.bandages()) < 20 else 0) + (150 if low_ammo else 0)
        cost = max(cost, 0)
        bank = int(b.facts.get("bank_balance", 0) or 0)
        if (b.c.gold or 0) < cost and bank > 0 and not st.get("withdrew"):
            st["withdrew"] = True                                 # money first, enough for everything this errand may buy (BotMaceBR banked 151 and shopped with 0)
            try:
                b.visit_bank("restock", withdraw=min(bank, max(WITHDRAW, cost - int(b.c.gold or 0) + 50)), reserve=0)
            except Exception as e:
                b.log(f"errand resupply: the withdrawal: {type(e).__name__}: {e}")
            b.beat()
        healer = {item: full - carried(b, item) for item, low, full, roles in marks(b) if "healer" in roles and item != "=orange potion" and carried(b, item) < low}
        if healer:
            visit(b.where1(("healer",)), healer, share=0.7)        # one visit: bandages, Heal, Refresh
        rest = {item: full - carried(b, item) for item, low, full, roles in marks(b) if carried(b, item) < low and "alchemist" in roles}
        if rest:
            visit(b.where1(("alchemist",)), rest)                  # one visit: Cure, and whatever the healer did not have
        # sold out: the next alchemists, nearest first, as a player walks on to the next shop (Britain has four; the nearest two were bare)
        for xy in alchemists(b)[:ALCHEMIST_TRIES]:
            rest = {item: full - carried(b, item) for item, low, full, roles in marks(b) if carried(b, item) < low and "alchemist" in roles}
            if not rest:
                break
            visit(xy, rest)
        bmark = next((m for m in marks(b) if m[0] == "bandage"), ("bandage", 20, 30, ()))
        short = bmark[2] - int(b.bandages())
        if CLOTH_BANDAGES and int(b.bandages()) < bmark[1] and not st.get("cloth_tried"):          # the healer could not fill the need: the tailor
            st["cloth_tried"] = True
            try:
                cloth_bandages(b, st, short)
            except Exception as e:
                b.log(f"errand resupply: cloth bandages: {type(e).__name__}: {e}")
            b.beat()
        after = stock()
        left = restock_wants(b)
        if after <= before:
            b.log(f"errand resupply: nothing bought (bandages {b.bandages()}, gold {b.c.gold}, bank {b.facts.get('bank_balance', 0)}): unmet")
        elif left:
            b.log(f"errand resupply: still short of {', '.join(k.strip('=') for k in left)}")
        if left and trip_stock_wanted(b):
            # the dungeon kit cannot be filled now (Britain's four Cure shelves held 10 each when every core fighter began to want 15): the kit waits for the
            # shelves to restock (BaseVendor.RestockDelay, one hour) and the bot hunts on its ordinary marks meanwhile, as a player does. BotArchAdvR,
            # BotFairArcherNR and BotRangerAR looped sell, bank and resupply instead of hunting (2026-11-01 19:44-19:53)
            b.facts["kit_short_until"] = time.time() + KIT_RETRY_S
            b.log(f"errand resupply: the dungeon kit is short ({', '.join(k.strip('=') for k in left)}): hunting on the ordinary marks for {KIT_RETRY_S // 60} min")
        b.facts["restock_failed_at"] = 0 if after > before else time.time()
        return after > before

    def do_gather(self, b, st, task):
        """Logs for coin: a hatchet (bought at the Carpenter for about 15 gold when none is carried), chop at the nearest trees until GATHER_LOGS logs, sell them at the Carpenter,
        the bow back in hand. RUNNING between chops; done when something sold, unmet when no tree could be worked or nobody paid."""
        b.facts["gather_task_at"] = time.time()
        pack = lambda: list(b.c.backpack) + list(b.c.equipped)
        hat = next((i for i in pack() if "hatchet" in (i.name or "").lower()), None)
        if hat is None:
            b.shop_at(b.where1(("carpenter",)), {"=hatchet": 1}, budget=min(int(b.c.gold or 0), 30))
            b.beat()
            hat = next((i for i in pack() if "hatchet" in (i.name or "").lower()), None)
            if hat is None:
                b.facts["errand_reason"] = "no hatchet could be bought"
                return False
        logs = lambda: sum((i.amount or 1) for i in b.c.backpack if (i.name or "").lower() in ("log", "logs", "board", "boards"))
        if st.get("phase") != "sell":
            if logs() < GATHER_LOGS and st.get("n", 0) < 8:
                st["n"] = st.get("n", 0) + 1
                before = logs()
                bow = next((i for i in b.c.equipped if i.layer in ("OneHanded", "TwoHanded")), None)
                got = b.chop_trees(hat)
                if bow is not None and bow.serial != hat.serial:
                    try:
                        b.wield(bow)
                    except Exception:
                        pass
                b.ev("gather_chop", logs=logs() - before, worked=got, n=st["n"])
                b.beat()
                if got is False and logs() == 0:
                    b.facts["errand_reason"] = "no tree near could be worked"
                    return False
                return None
            st["phase"] = "sell"
        if logs() <= 0:
            b.facts["errand_reason"] = "no logs after chopping"
            return False
        n = logs()
        earned = b.sell_items(tuple(b.where1(("carpenter",))), ["log", "board"])
        b.ev("gather_sold", logs=n, gold=int(earned or 0))
        try:
            b.fists_check()
        except Exception:
            pass
        if not earned:
            b.facts["errand_reason"] = "the Carpenter paid nothing"
        return bool(earned)

    def do_ammo(self, b, st, task):
        """Arrows (bolts for a crossbow) at the Bowyer: the bank first when the purse is short, then the shop, then the bow back in hand (fists_check at REARM arrows). Done when
        the pack holds more ammunition than before; unmet otherwise, and then it runs again once gold plus bank has changed by AMMO_MONEY_STEP."""
        before = b.ammo()
        money = (b.c.gold or 0) + (b.facts.get("bank_balance", 0) or 0)
        b.facts["ammo_unmet_money"] = money
        if (b.c.gold or 0) < 100 and (b.facts.get("bank_balance", 0) or 0) > 0:
            b.visit_bank("ammunition", withdraw=min(int(b.facts.get("bank_balance", 0) or 0), 300 if b.fletcher() else 150), reserve=0)   # a fletcher may buy materials instead (FLETCH_MATS)
            b.beat()
        gold = int(b.c.gold or 0)
        if gold < 4:
            b.facts["errand_reason"] = "no gold after the bank"
            return False
        shop = ammo_shop(b) or tuple(b.FLETCH_SHOP)      # out of arrows altogether: the Bowyer anyway (a shelf may have restocked)
        try:
            b.shop_at(shop, {ammo_item(b): 150}, budget=max(4, int(gold * 0.85)))
        except Exception as e:
            b.log(f"errand ammo: {type(e).__name__}: {e}")
            b.facts["errand_reason"] = f"shop error {type(e).__name__}"
        b.beat()
        try:
            b.fists_check()
        except Exception:
            pass
        ok = b.ammo() > before
        if ok:
            b.facts.pop("ammo_unmet_money", None)
        else:
            b.facts["errand_reason"] = f"shop gave nothing: list opened {b.facts.get('shop_list_opened')}, had wanted {b.facts.get('shop_had_wanted')}, gold {b.c.gold}"
            if b.facts.get("shop_list_opened") and not b.facts.get("shop_had_wanted"):
                # the list opened without arrows on it: sold out until the vendor restocks. A player walks on to the next shop that sells them, not back here in
                # four minutes (BotFairArcherVR asked the one Bowyer five times in 40 minutes, then hunted with none and died, 2026-11-01)
                b.facts.setdefault("ammo_bad_shop", {})[f"{shop[0]},{shop[1]}"] = time.time() + SOLD_OUT_S
                if b.fletcher():
                    # no arrows on the shelf, but shafts and feathers are (SBRangedWeapon: Shaft 3, Feather 2): a fletcher buys the makings at the same counter
                    # and makes its own (hunter.r_fletch). 8 of 10 ammo errands bought nothing in 19:33-20:03 (2026-11-01) with every Britain Bowyer out of arrows
                    made0 = b.can_make_arrows()
                    try:
                        b.shop_at(shop, {"=shaft": FLETCH_MATS, "=feather": FLETCH_MATS}, budget=max(4, int((b.c.gold or 0) * 0.85)))
                    except Exception as e:
                        b.log(f"errand ammo: the makings: {type(e).__name__}: {e}")
                    if b.can_make_arrows() > made0:
                        b.facts["fletch_wait"] = 0
                        b.log(f"errand ammo: no arrows on the shelf: bought the makings of {b.can_make_arrows()} (shafts and feathers) to fletch")
                        b.ev("ammo_makings", can_make=b.can_make_arrows(), arrows=b.ammo())
                        b.facts.pop("ammo_unmet_money", None)
                        return True
            b.ev("ammo_unmet", step="shop", list_opened=b.facts.get("shop_list_opened"), had_wanted=b.facts.get("shop_had_wanted"), shop=list(shop), gold=int(b.c.gold or 0),
                 bank=int(b.facts.get("bank_balance", 0) or 0), arrows=b.ammo())
            b.log(f"errand ammo: nothing bought (arrows {b.ammo()}, gold {b.c.gold}, bank {b.facts.get('bank_balance', 0)})")
        return ok

    def do_arm(self, b, st, task):
        """A fighter that cannot fight buys a weapon of its skill (the weapon batch, 2026-10-21): the best the shop lists in memory sell within its money (replace: any weapon of the
        worn one's class), the bank first, then the shop, then wield it (weaponup.arms_wield, which also marks the old one so r_gear does not put it back). Done when it is wielded."""
        b.facts["arm_task_at"] = time.time()
        state = b.weapon_state()
        money = (b.c.gold or 0) + (b.facts.get("bank_balance", 0) or 0)
        shops, bad = weapon_shops(b)
        best = b.next_weapon(money, replace=(state == "worn"), shops=shops, avoid=bad)
        if not best and shops and not st.get("lists_read"):
            st["lists_read"] = True                                   # nothing on record for its skill: read the nearest weapon shops' lists itself (the rule list's r_window, which the core bypasses)
            here = (int(b.c.x), int(b.c.y))
            for shop in sorted([s_ for s_ in shops if tuple(s_) not in bad], key=lambda s_: max(abs(s_[0] - here[0]), abs(s_[1] - here[1])))[:2]:
                try:
                    b.beat()
                    b.shop_at(tuple(shop), {"=nothing": 1}, budget=1)   # opens the list and records it; buys nothing
                except Exception as e_:
                    b.log(f"errand arm: reading the list at {tuple(shop)}: {type(e_).__name__}: {e_}")
            best = b.next_weapon(money, replace=(state == "worn"), shops=shops, avoid=bad)
        if not best:
            b.log(f"errand arm: no weapon of its skill on offer at {len(shops)} weapon shops within {money} gold ({state}; shops that did not sell: {sorted(bad)})")
            return False
        _, e, price, xy, name, cur = best
        b.log(f"errand arm: wants a {name} for {price} gold at {tuple(xy)} ({state}); gold {b.c.gold}, bank {b.facts.get('bank_balance', 0)}; weapon shops {shops[:4]}")
        b.beat()
        if (b.c.gold or 0) < price + 10 and (b.facts.get("bank_balance", 0) or 0) > 0:
            b.visit_bank("weapon", withdraw=min(int(b.facts.get("bank_balance", 0) or 0), price + 60), reserve=0)
            b.beat()
        if (b.c.gold or 0) < price:
            return False
        got = b.shop_at(xy, {"=" + name: 1}, budget=price + 5)
        b.beat()
        if not got:
            seen = []
            try:
                for k, v in b.mem.state["world"]["vendors"].items():
                    pt = tuple(int(c) for c in k.split(","))
                    if max(abs(pt[0] - xy[0]), abs(pt[1] - xy[1])) <= 12:
                        seen.append((k, sorted(v["stock"])[:8]))
            except Exception:
                pass
            b.facts.setdefault("arm_bad_shop", {})[f"{xy[0]},{xy[1]}"] = time.time() + 1800        # another shop next time
            b.ev("weapon_fail", item=name, why="the shop did not sell it", shop=list(xy), gold=int(b.c.gold or 0), lists=str(seen)[:200])
            b.log(f"errand arm: the shop at {tuple(xy)} did not sell a {name} (gold {b.c.gold}); lists on record there: {seen[:3]}")
            return False
        return bool(b.arms_wield(name, price, "shop", (cur["value"] if cur else 0.0), e["value"]))

    def do_fletch(self, b, st, task):
        """Arrows from what the pack holds (fix C, the Watcher 2026-10-21): the hunter's own r_fletch (wood into shafts, shafts and feathers into arrows, one stack a call, the
        fletcher's tool bought if it is missing) forced on for a bot in fist mode; the bow back in hand at REARM arrows (fists_check). Done when nothing more can be made."""
        b.facts["fletch_task_at"] = time.time()
        b.facts["fletch_force"] = True
        try:
            if not st.get("chopped") and not b.fletch_stock()[1] and not b.fletch_stock()[3]:
                st["chopped"] = True
                b.facts["wood_wait"] = 0
                b.r_wood()                                           # no wood or shafts: the hatchet fells a tree first
                b.beat()
            if time.time() < b.facts.get("fletch_wait", 0):
                time.sleep(2.0)
                return None if st.get("n", 0) < 20 else True       # the tool's short wait between stacks
            st["n"] = st.get("n", 0) + 1
            b.beat()
            acted = bool(b.r_fletch())
            try:
                b.fists_check()
            except Exception:
                pass
            if acted:
                return None
            return True if b.ammo() > 0 or st.get("n", 0) > 1 else False
        finally:
            b.facts.pop("fletch_force", None)

    def do_bank(self, b, st, task):
        b.facts["banked_at"] = 0
        try:
            return bool(b.r_bank()) or bool(b.visit_bank("task", reserve=100))
        except Exception as e:
            b.log(f"errand bank: {type(e).__name__}: {e}")
            return False

    def do_rest(self, b, st, task):
        if b.threats(10):
            return True                                           # something came: the rest is over, the reflexes and the next choice take it
        if b.hp_pct() >= (95 if "nothing to heal with" in str(task.get("area") or "") or "nothing to heal" in str(task.get("detail") or "") else REST_TO) and not b.tired():
            return True
        if b.tired() and time.time() - b.facts.get("refreshed_at", 0) > 60:
            red = b.potion("refresh")
            if red:
                b.facts["refreshed_at"] = time.time()
                b.drink(red)
                b.ev("consumable_used", item="red potion", hp=b.hp_pct())
        if not b.bandage_self():
            time.sleep(3.0)
        return None                                               # still resting (the budget ends it)

    def do_train(self, b, st, task):
        b.facts["train_task_at"] = time.time()
        word = "butte" if getattr(b, "ranged", False) else "dummy"
        try:
            items = [it for it in b.ground_items(8) if word in it.name.lower()]
        except Exception:
            items = []
        if not items:
            return False
        n = st.get("trained", 0)
        if n >= 20:
            return True
        b.c.use(items[0].serial)
        st["trained"] = n + 1
        time.sleep(4.0)
        return None

    def do_upgrade(self, b, st, task):
        b.facts["upgrade_at"] = 0
        want = None
        try:
            import goals
            money = (b.c.gold or 0) + (b.facts.get("bank_balance", 0) or 0) - getattr(b, "UPGRADE_RESERVE", 250)
            want = goals.upgrade_choice(b, money) if goals.active(b) else b.next_upgrade(money)
        except Exception:
            want = None
        if want:
            b.log(f"errand upgrade: wants a {want[2]} for {want[3]} gold at {tuple(want[4])} (armour {want[5]} -> {want[6]}); gold {b.c.gold}, bank {b.facts.get('bank_balance', 0)}")
        ok = False
        try:
            ok = bool(b.r_upgrade())
        except Exception as e:
            b.log(f"errand upgrade: {type(e).__name__}: {e}")
        if not ok:
            why = []                                                  # the reasons r_upgrade says no without buying, in its own order
            try:
                if b.mobs(10):
                    why.append("hostiles near")
                if b.hp_pct() < 70:
                    why.append(f"health {b.hp_pct():.0f}% under 70")
                if b.bow_kind() and b.ammo() < 50:
                    why.append(f"{b.ammo()} arrows under 50")
                if b.weapon_state() in ("none", "wrong", "worn"):
                    why.append(f"weapon {b.weapon_state()}")
            except Exception:
                pass
            b.ev("upgrade_unmet", item=(want[2] if want else None), price=(want[3] if want else None), shop=(list(want[4]) if want else None), why=", ".join(why) or "the shop did not sell it or the purse was short")
            if want:
                n = b.facts.setdefault("upgrade_unmets", {})
                n[want[2]] = n.get(want[2], 0) + 1
                if n[want[2]] >= 2:
                    b.facts.setdefault("upgrade_skip", {})[want[2]] = time.time() + 1800
                    n[want[2]] = 0
                    b.log(f"errand upgrade: the {want[2]} came back unmet twice: not for 30 minutes")
        return ok

    def do_rune_buy(self, b, st, task):
        b.facts["rune_buy_at"] = 0
        try:
            return bool(b.r_rune_buy())
        except Exception as e:
            b.log(f"errand rune_buy: {type(e).__name__}: {e}")
            return False

    def do_loot(self, b, st, task):
        loot = hunt_tree.Loot("loot", self.ctx)
        s = loot.update()
        return None if s == Status.RUNNING else True


def build(ctx):
    kind = ctx.task["task"]
    if kind == "camp":
        tree = hunt_tree.build(ctx)                              # the hunt tree bound to the one spawner (the task's spots)
        return tree
    steps = py_trees.composites.Sequence("steps", memory=True, children=[ErrandTravel("travel", ctx), Act("act", ctx)])
    return py_trees.composites.Sequence(kind, memory=False, children=[hunt_tree.Guard("guard", ctx), steps])


def tick(bot, task):
    """One tick of an errand. Returns (step, why): why "" while it runs, "done" when the act met the need, "unmet" when it could not, or the travel's failure."""
    entry = bot.__dict__.get("_core_tree")
    if entry is None or entry[0].task is not task:
        ctx = Ctx(bot, task)
        entry = bot.__dict__["_core_tree"] = (ctx, build(ctx))
    ctx, root = entry
    ctx.why = ""
    root.tick_once()
    if root.status == Status.SUCCESS:
        return ctx.step, "done"
    if root.status == Status.FAILURE and ctx.why:
        return ctx.step, ctx.why
    return ctx.step, ""
