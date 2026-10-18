"""The death loop at a healer (feature "death_loop"; patch_death_loop.py; Operator 16:30).

BotMageAdvR died three times in two minutes at 1472-1475,1608-1612, beside Britain's healer (15:17:12, 15:18:16, 15:19:08). A troll it had meleed into town stood at its corpse ("a troll rummages through
a corpse"); each time the ghost walked to the nearest healer, accepted the offer with the troll a few tiles out of the 12-tile check, and died 10 s later with Heal failing ("More reagents are
needed"). The caster's r_dead (mage_bot) has no resurrection safety at all; BotBase.r_dead (patch_res_safe) only looks at what is in view at the moment of the offer.

A DEATH IS EVIDENCE of a hostile at that spot for 10 minutes, seen or not (own deaths: facts["death_log"], persisted; every bot's deaths: the area danger map's death list, both memory folders):
  healer(bot)      the healer a ghost walks to: the nearest of the gazetteer's healers (Places.find_places) that has no death within 15 tiles in the last 10 minutes; all of them near one: the nearest.
  decline(bot, g)  a resurrection offer made within 15 tiles of a fresh death is cancelled (the same 3-decline cap as res_safe, facts["res_declined"]); the next tick walks to another healer.
  res_flee(bot)    just resurrected (3 minutes), under 40% hit points, damage arriving in the last 6 s (deathsrc's own-damage record) and nobody to fight: walk 16 tiles away from the death spot
                   at once (at most once in 12 s) instead of standing where the unseen attacker is.
  hook(bot, event) the four moments the brains call: "died" (log the death), "resurrected" (remember when and where from), "alive" (every tick as a living bot: res_flee), "offer" (decline).
CASTER HEAL: mage_bot.Bot.can_heal() is Heal when the spell is held, mana >= 4 AND the reagents for it are in the pack (Knowledge.reagent_ok on the bag count): "More reagents are needed" three times
in a row while the troll hit is gone; without reagents r_flee falls through to a potion or the walk to town.
Nothing names a town: the healers come from the gazetteer, the evidence from the shared memory.
"""
from __future__ import annotations

import time

FEATURE = "death_loop"
NEAR = 15
WINDOW = 600.0
RES_WINDOW = 180.0
HP_LOW = 40.0
HIT_WITHIN = 6.0
FLEE_EVERY = 12.0
FLEE_DIST = 16
DECLINES = 3


def on(bot):
    try:
        return bool(bot.feature(FEATURE))
    except Exception:
        return False


def _cheb(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def note_death(bot, x, y):
    log = bot.facts.setdefault("death_log", [])
    log.append([round(time.time()), int(x), int(y)])
    del log[:-10]


def fresh_deaths(bot, window=WINDOW):
    """[(t, x, y)] of deaths in the last `window` seconds: this bot's own and everybody's (the area map reads both memory folders)."""
    now = time.time()
    out = [(t, x, y) for t, x, y in bot.facts.get("death_log", []) if now - t <= window]
    area = getattr(getattr(bot, "mem", None), "area", None)
    if area is not None:
        try:
            area.refresh()
            out += [(d["t"], d["x"], d["y"]) for d in area.deaths if now - d["t"] <= window]
        except Exception:
            pass
    return out


def near_fresh(bot, x, y, r=NEAR):
    for t, dx, dy in fresh_deaths(bot):
        if _cheb((x, y), (dx, dy)) <= r:
            return (t, dx, dy)
    return None


def healer(bot):
    """The healer a ghost walks to."""
    nearest = bot.healer_xy()
    if not on(bot):
        return nearest
    try:
        cands = [tuple(h) for h in bot.find_places(("healer",), n=4, per=2)] if hasattr(bot, "find_places") else []
    except Exception:
        cands = []
    if not cands:
        return nearest
    ok = [h for h in cands if not near_fresh(bot, h[0], h[1])]
    pick = ok[0] if ok else tuple(nearest)
    if pick != tuple(nearest) and time.time() - bot.facts.get("healer_switch_at", 0) > 60:
        bot.facts["healer_switch_at"] = time.time()
        bot.log(f"healer {tuple(nearest)} had a death within {NEAR} tiles in the last {int(WINDOW // 60)} min: going to {pick}")
        try:
            bot.ev("healer_switch", frm=list(nearest), to=list(pick))
        except Exception:
            pass
    return pick


def decline(bot, serial):
    """A resurrection offer made beside a fresh death is cancelled (3 times at most); True when it was."""
    if not on(bot) or bot.facts.get("res_declined", 0) >= DECLINES:
        return False
    d = near_fresh(bot, bot.c.x, bot.c.y)
    if not d:
        return False
    n = bot.facts["res_declined"] = bot.facts.get("res_declined", 0) + 1
    bot.c.call(f"gumpresponse 0 gump:{serial}", timeout=8)
    dist = _cheb((bot.c.x, bot.c.y), (d[1], d[2]))
    bot.log(f"resurrection offer declined ({n}/{DECLINES}): a death {dist} tiles away {int(time.time() - d[0])} s ago; another healer first")
    try:
        bot.ev("res_declined", threat="fresh death", dist=dist, n=n)
    except Exception:
        pass
    return True


def res_mark(bot):
    bot.facts["res_at"] = time.time()
    log = bot.facts.get("death_log")
    bot.facts["res_from"] = (log[-1][1], log[-1][2]) if log else (bot.c.x, bot.c.y)


def away_point(bot, spot, dist=FLEE_DIST):
    """A point `dist` tiles from the bot, away from `spot` (toward the home centre when the bot stands on it)."""
    vx, vy = bot.c.x - spot[0], bot.c.y - spot[1]
    if abs(vx) + abs(vy) < 3:
        try:
            hc = bot.home_centre()
            vx, vy = hc[0] - spot[0], hc[1] - spot[1]
        except Exception:
            pass
    if vx == 0 and vy == 0:
        vx = 1
    n = max(abs(vx), abs(vy))
    return int(bot.c.x + vx * dist / n), int(bot.c.y + vy * dist / n)


def res_flee(bot):
    """Just back from the dead, weak, hit by something nobody can see: move away from the death spot now."""
    if not on(bot):
        return False
    now = time.time()
    t = bot.facts.get("res_at")
    if not t or now - t > RES_WINDOW or bot.hp_pct() >= HP_LOW or now - bot.facts.get("res_flee_at", 0) < FLEE_EVERY:
        return False
    try:
        import deathsrc
        dm = deathsrc.state(bot)["dmg"]
    except Exception:
        return False
    if not dm or now - dm[-1][0] > HIT_WITHIN:
        return False
    bot.facts["res_flee_at"] = now
    x, y = away_point(bot, bot.facts.get("res_from") or (bot.c.x, bot.c.y))
    bot.activity = "away from where I died"
    bot.log(f"hit at {bot.hp_pct():.0f}% hit points {int(now - t)} s after the resurrection: walking away from {bot.facts.get('res_from')} to {x},{y}")
    try:
        bot.ev("res_flee", at=[x, y], hp=int(bot.hp_pct()))
    except Exception:
        pass
    bot.c.goto(x, y).wait(timeout=8)
    return True


def hook(bot, event, **kw):
    """The brains' four moments; True when the hook acted (alive, offer)."""
    if not on(bot):
        return False
    if event == "died":
        try:
            x, y = bot.death_xy() if hasattr(bot, "death_xy") else (bot.c.x, bot.c.y)
        except Exception:
            x, y = bot.c.x, bot.c.y
        note_death(bot, x, y)
        return False
    if event == "resurrected":
        res_mark(bot)
        return False
    if event == "alive":
        return res_flee(bot)
    if event == "offer":
        return decline(bot, kw["serial"])
    return False
