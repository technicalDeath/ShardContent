"""Savings goals (feature "goals"; patch_goals.py; the watcher's A1 home / A2 income / A3 purpose): a bot holds ONE goal that fits its persona and state, saves for it, buys it when the
fund covers it, and does not spend on idle things meanwhile.

THE GOAL (facts["goal"], persisted with facts["goals_done"] and facts["inc_log"]):
  {id, kind, name, cost, set_at, eta_h, progress_at, meta}. Providers return candidates {id, kind, name, cost, value} for a bot:
    gear    (HunterBot: ARMOR_BUY, worn_ar)  every armour piece the bot is strong enough to wear that beats what it wears, priced from the shelves the memory has seen; value = the armour gained x the slot's
            share of the body. Done when the layer holds that piece or better.
    spells  (casters with the spellbook feature: book_wants)  the missing scrolls the book wants (circles 1-3 a Mage shop sells), priced from the shelves (else the spellbook's guess); one goal,
            "complete the book". Done when book_wants() is empty after the book was read.
    house   (every bot, only when nothing else is left)  a small house deed, 16,000 gold on this shard. It only accumulates: no placement, no purchase. goal_done fires once when the fund covers it.
  Not (yet) a goal: a tamer's pet (tamers tame, they do not buy one), crafters' stock (their tools and material are the business and are bought by their own rules). They fall to the house fund.
THE PICK: the bot's income per hour is what it earned (sale, loot and trade gold events, after_tick) over the last two hours, never under INCOME_FLOOR. A candidate is reachable when
(cost - have) / income <= REACH_H (3 hours). The reachable one with the highest value wins (cheaper on a tie); with none reachable the nearest by eta; the house fund last.
"have" = bank + purse. A goal is re-picked when it is done or no longer a candidate (the piece was bought elsewhere), or when its eta passes 6 hours while another candidate is within 3.
EVENTS (ev): goal_set {goal, cost, eta_h}, goal_progress {goal, have, cost} every 15 minutes, goal_done {goal, minutes}.
SPENDING RULES while a goal is active (the hooks in patch_goals.py):
  * the purse stays small: visit_bank keeps at most PURSE (100) gold instead of its reserve (up to 200) and r_bank banks sooner (a purse over 160, or 300 away from town, instead of 250/400), so
    the fund sits in the bank, out of reach of a death (a corpse run lost 650 gold) and of idle buying;
  * r_upgrade buys only the goal's piece (and only when gold + bank cover its price with a 100 gold reserve for potions); r_resupply's optional potions (heal, refresh) wait while the fund
    would drop under the goal; bandages and ammunition are business and never wait;
  * r_book funds the next scroll from the bank (the goal's purchase) instead of skipping it for a thin purse.
Nothing here names a town: prices come from the shared memory (vendor_selling), the pieces from the bot's own tables.
"""
from __future__ import annotations

import time

HOUSE_COST = 16000                       # the shard's small house price (owner, 2026-10-18: housePricing.smallHouses; stock 43,800)
REACH_H = 3.0
RERUN_H = 6.0
INCOME_FLOOR = 120.0                     # gold an hour assumed for a bot with no earnings record yet
INCOME_WINDOW = 2 * 3600.0
LOG_KEEP = 3 * 3600.0
PROGRESS_EVERY = 900.0
TICK_EVERY = 60.0
PURSE = 100                              # gold a bot with a goal keeps on it when it banks
PURSE_CORE, PURSE_AWAY = 160, 300        # the thresholds at which it walks to the bank to bank (instead of 250 / 400)
UPGRADE_KEEP = 100                       # kept for potions when the goal's piece is bought
INCOME_KINDS = ("sale", "loot", "trade")


def on(bot):
    try:
        return bool(bot.feature("goals"))
    except Exception:
        return False


# ---- income ------------------------------------------------------------------------------------------------------------------------------------

def income(bot, kind, delta):
    """after_tick: gold earned by a sale, a loot or a trade counts toward the income rate."""
    if kind in INCOME_KINDS and delta > 0 and on(bot):
        log = bot.facts.setdefault("inc_log", [])
        log.append([round(time.time()), int(delta)])
        cut = time.time() - LOG_KEEP
        while log and log[0][0] < cut:
            log.pop(0)


def income_h(bot):
    now = time.time()
    log = [e for e in bot.facts.get("inc_log", []) if now - e[0] <= INCOME_WINDOW]
    if not log:
        return INCOME_FLOOR
    span = max(0.5 * 3600.0, now - log[0][0])            # at least half an hour: one big sale is not a rate
    return max(INCOME_FLOOR, sum(e[1] for e in log) / (span / 3600.0))


def have(bot):
    return max(0, bot.facts.get("bank_balance", 0)) + bot.c.gold


# ---- the candidates ----------------------------------------------------------------------------------------------------------------------------

def gear_options(bot):
    """[(score, layer, name, price, xy, cur, ar)] of every wearable piece that beats what is worn and whose price the memory knows (HunterBot.next_upgrade without the money test)."""
    if not (hasattr(bot, "ARMOR_BUY") and hasattr(bot, "worn_ar")):
        return []
    out = []
    try:
        strength = int(bot.c.state.get("str") or 0)
    except Exception:
        strength = 0
    for layer, options in bot.ARMOR_BUY.items():
        cur, _ = bot.worn_ar(layer)
        for name, ar, need, dex in options:
            if ar <= cur or need > strength or (getattr(bot, "ranged", False) and dex < -2):
                continue
            offers = [o for o in bot.mem.vendor_selling(name) if o[2] == name]
            if not offers:
                continue
            price, xy = offers[0][0], tuple(int(v) for v in offers[0][1].split(","))
            out.append(((ar - cur) * bot.SLOT_SHARE[layer] / max(price, 1), layer, name, price, xy, cur, ar))
    return out


def gear_candidates(bot):
    return [{"id": f"gear:{name}", "kind": "gear", "name": f"{name} for the {layer.lower()}", "cost": price, "value": (ar - cur) * bot.SLOT_SHARE[layer],
             "meta": {"item": name, "layer": layer, "ar": ar}} for _, layer, name, price, xy, cur, ar in gear_options(bot)]


def spell_candidates(bot):
    if not (hasattr(bot, "book_wants") and hasattr(bot, "book_state")):
        return []
    try:
        if not bot.feature("spellbook") or bot.book_state().get("have") is None:
            return []
        wants = bot.book_wants()
    except Exception:
        return []
    if not wants:
        return []
    cost = 0
    for n in wants:
        prices = [p for p, xy, item, qty in bot.mem.vendor_selling(f"{n} scroll") if p > 0]
        cost += min(prices) if prices else bot.book_price_guess(n)
    return [{"id": "spells:book", "kind": "spells", "name": f"complete the spellbook ({', '.join(wants[:4])}{'...' if len(wants) > 4 else ''})", "cost": cost, "value": 1.0 + 0.1 * len(wants),
             "meta": {"wants": list(wants)}}]


def house_candidates(bot):
    return [{"id": "house:fund", "kind": "house", "name": "house fund (a small house deed)", "cost": HOUSE_COST, "value": 0.05, "meta": {}}]


PROVIDERS = (gear_candidates, spell_candidates)


def candidates(bot):
    out = []
    for p in PROVIDERS:
        try:
            out += p(bot)
        except Exception:
            continue
    return out or house_candidates(bot)


# ---- the pick, the progress, the end -----------------------------------------------------------------------------------------------------------

def eta_h(bot, cost):
    return max(0.0, cost - have(bot)) / income_h(bot)


def pick(bot, cands):
    reach = [c for c in cands if c["kind"] != "house" and eta_h(bot, c["cost"]) <= REACH_H]
    if reach:
        return max(reach, key=lambda c: (c["value"], -c["cost"]))
    rest = [c for c in cands if c["kind"] != "house"]
    if rest:
        return min(rest, key=lambda c: (eta_h(bot, c["cost"]), -c["value"]))
    return cands[0]


def set_goal(bot, c):
    e = eta_h(bot, c["cost"])
    now = time.time()
    bot.facts["goal"] = {"id": c["id"], "kind": c["kind"], "name": c["name"], "cost": c["cost"], "set_at": now, "eta_h": round(e, 1), "progress_at": now, "meta": c.get("meta", {})}
    bot.ev("goal_set", goal=c["name"], cost=c["cost"], eta_h=round(e, 1))
    bot.log(f"goal: {c['name']}, {c['cost']} gold, eta {e:.1f} h at {income_h(bot):.0f} gold an hour")


def done(bot, g, why=""):
    bot.ev("goal_done", goal=g["name"], minutes=int((time.time() - g["set_at"]) / 60))
    bot.log(f"goal done: {g['name']} ({why})")
    bot.facts.setdefault("goals_done", []).append(g["id"])
    bot.facts.pop("goal", None)


def is_done(bot, g, cands):
    kind = g["kind"]
    if kind == "gear":
        layer, ar = g["meta"].get("layer"), g["meta"].get("ar", 0)
        try:
            return bot.worn_ar(layer)[0] >= ar
        except Exception:
            return False
    if kind == "spells":
        return not any(c["kind"] == "spells" for c in cands) and bot.book_state().get("have") is not None
    if kind == "house":
        return have(bot) >= g["cost"] and not g["meta"].get("fund_done")
    return False


def tick(bot):
    """Once a minute: keep the goal (set, progress, done, re-pick)."""
    if not on(bot) or getattr(bot.c, "ghost", False):
        return
    now = time.time()
    if now - bot.__dict__.get("_goal_at", 0) < TICK_EVERY:
        return
    bot._goal_at = now
    g = bot.facts.get("goal")
    cands = candidates(bot)
    if g:
        if g["kind"] == "house":
            if is_done(bot, g, cands):
                g["meta"]["fund_done"] = True
                bot.ev("goal_done", goal=g["name"], minutes=int((now - g["set_at"]) / 60))
                bot.log(f"goal done: {g['name']} (the fund covers {g['cost']})")
            if any(c["kind"] != "house" for c in cands):
                bot.facts.pop("goal", None)                    # something to buy again: the house waits
                g = None
        else:
            cur = next((c for c in cands if c["id"] == g["id"]), None)
            if is_done(bot, g, cands):
                done(bot, g, "bought")
                g = None
            elif cur is None:
                bot.facts.pop("goal", None)                    # no longer a candidate (the piece went on elsewhere, the shop forgot it)
                bot.log(f"goal dropped: {g['name']} is no longer on offer")
                g = None
            else:
                g["cost"] = cur["cost"]
                if eta_h(bot, g["cost"]) > RERUN_H:
                    better = [c for c in cands if c["id"] != g["id"] and c["kind"] != "house" and eta_h(bot, c["cost"]) <= REACH_H]
                    if better:
                        bot.facts.pop("goal", None)
                        g = None
    if not g:
        c = pick(bot, cands)
        set_goal(bot, c)
        return
    if now - g.get("progress_at", 0) >= PROGRESS_EVERY:
        g["progress_at"] = now
        bot.ev("goal_progress", goal=g["name"], have=have(bot), cost=g["cost"])


# ---- what the goal changes in spending ---------------------------------------------------------------------------------------------------------

def active(bot):
    """The goal when this bot has one it is saving for (the house fund counts: it only accumulates)."""
    return bot.facts.get("goal") if on(bot) else None


def reserve(bot, reserve, why=""):
    """visit_bank: the gold the purse keeps when banking: at most PURSE while saving (a withdrawing trip, reserve 0, is left alone)."""
    if active(bot) and reserve > PURSE:
        return PURSE
    return reserve


def purse_limit(bot, default):
    """r_bank: the purse size that sends the bot to the bank."""
    if not active(bot):
        return default
    return min(default, PURSE_CORE if default <= 300 else PURSE_AWAY)


def idle_ok(bot, cost):
    """True when buying something that is not the goal still leaves the fund able to cover the goal (or there is no goal)."""
    g = active(bot)
    if not g:
        return True
    return have(bot) - cost >= g["cost"]


def upgrade_choice(bot, money):
    """r_upgrade: with a gear goal only its piece may be bought (when gold + bank cover its price and the 100 gold kept for potions); other goals leave the old choice alone."""
    g = active(bot)
    if not g or g["kind"] != "gear":
        return bot.next_upgrade(money)
    item = g["meta"].get("item")
    for opt in gear_options(bot):
        if opt[2] == item and opt[3] + UPGRADE_KEEP <= have(bot):
            return opt
    return None


def fund(bot, need):
    """r_book: the purse must hold `need` gold for the next scroll. With a spells goal and the gold in the bank, fetch it. True when the purse holds it."""
    if bot.c.gold >= need:
        return True
    g = active(bot)
    if not g or g["kind"] != "spells" or bot.facts.get("bank_balance", 0) < need - bot.c.gold:
        return False
    bot.visit_bank("goal", withdraw=need - bot.c.gold + 30, reserve=0)
    return bot.c.gold >= need
