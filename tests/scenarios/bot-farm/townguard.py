"""Town guards (feature "town_guards"; patch_town_guards.py; Operator 16:55): in a guarded region the bots let the guards deal with monsters.

The server (ModernUO GuardedRegion): TownRegion is a GuardedRegion; saying "guards" calls guards on the guard candidates within 14 tiles of the speaker (a mobile flagged criminal and recorded by the
region as a candidate when it was aggressive, 15 s); the guards then kill it. The owner tested it: guards kill monsters in guarded areas. BotMageAdvR (15:15) attacked a troll inside Britain, was chased
to the healer and killed three times; nobody called "guards".

WHERE: the gazetteer's regions carry the engine's class name (type). A point is guarded when the highest-priority region over it is a GuardedRegion or a TownRegion (nothing underground, nothing in
the wilds). Britain's farmland and the beginner spawn belong to the Britain TownRegion.
(a) filter_prey(bot, prey): inside a guarded region a monster is NOT prey unless it is vermin (a creature of 25 hit points or fewer: rats, cats, snakes, mongbats ... the beginners' food) or it has already
    hit this bot in the last 20 s (a swing at it, "X is attacking you!", "X hits you": deathsrc's hit_by record). A bot fights back once the monster is the aggressor, never starts it. ev town_refuse {kind}
    at most once a minute per kind.
(b) tick(bot): hurt (a damage line) or hit by a named attacker in the last 6 s inside a guarded region: say "guards", at most once per 15 s, ev guard_call {kind, region}; the bot keeps defending (the
    ordinary rules) or flees (r_flee) as before.
(c) the same call when the damage has no attacker in view: it walks toward the nearer of the healer and the bank.
Nothing names a town: the regions come from the gazetteer.
"""
from __future__ import annotations

import re
import time

import gazetteer as gz

FEATURE = "town_guards"
GUARDED_TYPES = ("GuardedRegion", "TownRegion")
VERMIN_HITS = 25
HIT_RECENT = 20.0
UNDER_ATTACK = 6.0
CALL_EVERY = 15.0
REFUSE_EVERY = 60.0
_CACHE = {}


def emit(bot, name, **kw):
    """BotBase.ev(kind, **kw) already has a `kind` parameter, and these events carry a field called kind: write the same decisions line ev() writes, directly."""
    try:
        bot.dlog("ev", ev=name, cell=_cell(bot), rule=getattr(bot, "current_rule", None) or getattr(bot, "last_rule", None), **kw)
    except Exception:
        pass


def _cell(bot):
    try:
        from memory import cell_of
        return cell_of(bot.c.x, bot.c.y)
    except Exception:
        return None


def on(bot):
    try:
        return bool(bot.feature(FEATURE))
    except Exception:
        return False


_UNGUARDED = None


def unguarded_areas():
    """The shard's townGuards.unguardedAreas as (x1, y1, x2, y2) rectangles, read once from the farm host's deployed shard-rules.json, else the source file; [] when neither can be read."""
    global _UNGUARDED
    if _UNGUARDED is None:
        import json
        import os
        here = os.path.dirname(os.path.abspath(__file__))
        out = []
        for rel in (("..", "..", "..", "..", "work", "hosts", "farm", "Configuration", "shard-rules.json"), ("..", "..", "..", "data", "configuration", "shard-rules.json")):
            try:
                d = json.load(open(os.path.join(here, *rel), encoding="utf-8"))
                out = [(r["x1"], r["y1"], r["x2"], r["y2"]) for a in d.get("townGuards", {}).get("unguardedAreas", []) for r in a.get("rectangles", [])]
                break
            except (OSError, ValueError, KeyError, TypeError):
                continue
        _UNGUARDED = out
    return _UNGUARDED


def region_at(x, y):
    """The guarded region record at the point (the highest-priority region over it is a GuardedRegion or a TownRegion), else None."""
    if x >= 5120:
        return None
    if any(x1 <= x <= x2 and y1 <= y <= y2 for x1, y1, x2, y2 in unguarded_areas()):
        return None                                            # the shard took the guards away here (Britain Outskirts, Moonglow Zoo)
    key = (int(x) // 4, int(y) // 4)
    if key in _CACHE:
        return _CACHE[key]
    out = None
    try:
        rs = gz.regions_at(x, y)
    except Exception:
        rs = []
    if rs:
        top = max(r.get("priority", 0) for r in rs)
        for r in rs:
            if r.get("priority", 0) == top and r.get("type") in GUARDED_TYPES:
                out = r
                break
    if len(_CACHE) > 20000:
        _CACHE.clear()
    _CACHE[key] = out
    return out


def guarded_at(x, y):
    """The name of the guarded region at the point, else None."""
    r = region_at(x, y)
    return r["name"] if r else None


def core_rect(bot, rec):
    """The city itself: the bot's home_core when this is its home town, else the gazetteer rectangle of the region that holds its centre (the nearest one when none does)."""
    try:
        h = bot.home()
        if h and h.get("name") == rec["name"]:
            return tuple(bot.home_core())
    except Exception:
        pass
    rects = [tuple(r) for r in rec["rects"]]
    cx, cy = (rec.get("centre") or [0, 0, 0])[:2]
    inside = [r for r in rects if r[0] <= cx < r[2] and r[1] <= cy < r[3]]
    return inside[0] if inside else min(rects, key=lambda r: abs((r[0] + r[2]) / 2 - cx) + abs((r[1] + r[3]) / 2 - cy))


def in_core(bot, x, y, rec):
    r = core_rect(bot, rec)
    return r[0] <= x < r[2] and r[1] <= y < r[3]


def kind_of(m):
    return re.sub(r"[^a-z]", "", (getattr(m, "species", None) or re.sub(r"^(an?|the) ", "", m.name.lower())).lower())


def is_vermin(m):
    try:
        import danger
        c = danger.stats().get(kind_of(m))
        if c and c.get("hits"):
            return c["hits"][1] <= VERMIN_HITS
    except Exception:
        pass
    n = m.name.lower()
    return any(re.search(r"\b" + w + r"\b", n) for w in ("rat", "cat", "bird", "dog", "chicken", "sheep", "goat", "pig", "cow", "rabbit", "squirrel", "snake", "frog", "mongbat"))


def hit_me(bot, m):
    """The monster hit this bot in the last HIT_RECENT seconds (its name in deathsrc's hit_by record)."""
    try:
        import deathsrc
        t = deathsrc.state(bot).get("hit_by", {}).get(m.name.strip())
    except Exception:
        return False
    return bool(t and time.time() - t <= HIT_RECENT)


def filter_prey(bot, ps):
    """prey(): inside a guarded region only vermin and monsters that have already hit the bot remain."""
    if not ps or not on(bot):
        return ps
    rec = region_at(bot.c.x, bot.c.y)
    if not rec or not in_core(bot, bot.c.x, bot.c.y, rec):
        return ps                                             # the farms and the wilds of the region: the owner's beginner spawners; the guards are for the city
    region = rec["name"]
    out = []
    for m in ps:
        if is_vermin(m) or hit_me(bot, m):
            out.append(m)
            continue
        refused = bot.facts.setdefault("town_refused", {})
        k = kind_of(m)
        if time.time() - refused.get(k, 0) > REFUSE_EVERY:
            refused[k] = time.time()
            emit(bot, "town_refuse", kind=k)
            try:
                bot.log(f"town_guards: not starting a fight with {m.name} inside the core of {region}; the guards deal with it")
            except Exception:
                pass
    return out


RESULT_WAIT = 45.0
CALL_GAP = 5.0


def call_guards(bot, m):
    """The bot that warned about monster m (talk.warn holds the shared claim) also calls the guards, once: ev guards_called. The shard's townGuardsKillMonsters makes the call kill any attack-on-sight monster within 14 tiles of the caller."""
    if not on(bot) or getattr(bot.c, "ghost", False):
        return False
    if not region_at(bot.c.x, bot.c.y):
        return False
    now = time.time()
    if now - bot.facts.get("guard_call_at", 0) < CALL_GAP:
        return False
    bot.facts["guard_call_at"] = now
    bot.c.say("guards")
    bot.facts["guard_watch"] = {"serial": str(m.serial), "kind": kind_of(m), "t0": now}
    emit(bot, "guards_called", monster=kind_of(m), at=[int(getattr(m, "x", 0)), int(getattr(m, "y", 0))])
    return True


def watch_result(bot):
    """What came of the call: the monster dead or out of view (killed), or still there after RESULT_WAIT seconds (not)."""
    w = bot.facts.get("guard_watch")
    if not w:
        return
    now = time.time()
    m = next((o for o in bot.c.mobiles(within=24) if str(o.serial) == w["serial"]), None)
    dead = m is not None and bool(getattr(m, "is_dead", False))
    gone = m is None and now - w["t0"] >= 2.0
    if dead or gone:
        bot.facts.pop("guard_watch", None)
        emit(bot, "guards_result", monster=w["kind"], killed=True, how="dead" if dead else "gone", secs=round(now - w["t0"], 1))
    elif now - w["t0"] > RESULT_WAIT:
        bot.facts.pop("guard_watch", None)
        emit(bot, "guards_result", monster=w["kind"], killed=False, how="timeout", secs=round(now - w["t0"], 1))


def tick(bot):
    """After every tick: under attack inside a guarded region, call the guards (15 s apart); damage from nothing in view also walks toward the healer or the bank."""
    if not on(bot) or getattr(bot.c, "ghost", False):
        return
    try:
        watch_result(bot)
    except Exception:
        pass
    import deathsrc
    st = deathsrc.state(bot)
    now = time.time()
    dm = st["dmg"]
    hurt = bool(dm) and now - dm[-1][0] <= UNDER_ATTACK
    attackers = [n for n, t in st.get("hit_by", {}).items() if now - t <= UNDER_ATTACK]
    if not (hurt or attackers):
        return
    region = guarded_at(bot.c.x, bot.c.y)
    if not region or now - bot.facts.get("guard_call_at", 0) < CALL_EVERY:
        return
    bot.facts["guard_call_at"] = now
    unseen = not attackers and not bot.mobs(12)
    bot.c.say("guards")
    kind = re.sub(r"[^a-z]", "", re.sub(r"^(an?|the) ", "", attackers[0].lower())) if attackers else ("unseen" if unseen else "hostile")
    emit(bot, "guard_call", kind=kind, region=region)
    if unseen:
        try:
            spots = [tuple(bot.healer_xy())]
            if hasattr(bot, "bank_xys"):
                spots.append(tuple(bot.bank_xys()[0]))
            x, y = min(spots, key=lambda p: max(abs(p[0] - bot.c.x), abs(p[1] - bot.c.y)))
            bot.activity = "damage from nothing in view: toward the healer"
            bot.c.goto(x, y).wait(timeout=6)
        except Exception:
            pass
