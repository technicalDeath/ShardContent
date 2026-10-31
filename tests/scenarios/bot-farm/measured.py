"""Measured prey numbers (work/botfarm-watch/prey_measured.json, made hourly by the Watcher's prey_measured.py from every fight record, ranged and melee apart).

Per kind and group: fights, kill_pct, ttk_p50, ttk_p90, dmg_pct_mean, dmg_pct_p90, death_pct. The brain reloads the file when it changes (checked every 30 s). Used for:
  give_up_s(bot, kind)   the kind's ttk_p90 for the bot's group: the time after which a fight that has not ended is let go
  allowed(bot, kind)     (ok, why): a kind with MIN_FIGHTS records is refused when its measured death_pct is at or over the group's limit, and for a bow user also when it is not killed
                         often enough (kill_pct under RANGED_MIN_KILL) or kills the bot at all often (death_pct at or over RANGED_PREY_DEATH). Kinds without enough fights are not judged here.
The cut-offs are parameters (PARAMS), set by the Watcher's choice and logged as the event measured_params when the file loads.

2026-10-29 (the Watcher; the owner: "no guessing ... calculations based on data and code"): the danger test is an expected value per fight, not a death-rate cut-off.
  value(k)      = kill_pct/100 x (gold + extras + CARVE_REALIZE x carve)   -- the profit table (profit.py: the engine's loot data), task_core.CARVE_REALIZE
  death_cost(k) = death_pct/100 x the mean full re-kit of the bot's group   -- work/botfarm-watch/provision.jsonl (what a death actually cost us)
  a kind is deadly for the bot when death_cost > value; a kind is allowed when it is not deadly (the kill rate already scales the value, so no separate kill cut-off).
The 3%/5% cut-offs starved the archers (prov5, 10-21/22: 2.4 kills a bot-hour, 31% waiting, 52,468 'measured danger' refusals).
"""
from __future__ import annotations

import json
import os
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PATH = os.environ.get("PREY_MEASURED") or os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", "work", "botfarm-watch", "prey_measured.json"))
PARAMS = {"min_fights": 30, "ranged_min_kill_pct": 60.0, "ranged_prey_death_pct": 2.0, "ranged_exclude_death_pct": 3.0, "melee_exclude_death_pct": 5.0}
RECHECK_S = 30.0
_state = {"mtime": None, "data": {}, "checked": 0.0, "made": None}


def _load():
    now = time.time()
    if now - _state["checked"] < RECHECK_S and _state["mtime"] is not None:
        return _state["data"]
    _state["checked"] = now
    try:
        mt = os.path.getmtime(PATH)
        if mt != _state["mtime"]:
            with open(PATH, encoding="utf-8") as f:
                d = json.load(f)
            _state.update(mtime=mt, data={"ranged": d.get("ranged") or {}, "melee": d.get("melee") or {}, "caster": d.get("caster") or {}}, made=d.get("made"))
            _state["announce"] = True
            if d.get("min_fights"):
                PARAMS["min_fights"] = int(d["min_fights"])
    except Exception:
        _state["mtime"] = _state["mtime"] or 0.0
    return _state["data"]


def group(bot):
    """"caster" for a mage (PureMage, Sorcerer, Warlock: the casters' own fight records, grp "caster"), "ranged" for a bow user with arrows in hand, else "melee"
    (a fist-mode archer fights with its hands)."""
    try:
        if getattr(bot, "pname", None) in CASTER_PROFS:
            return "caster"
        if getattr(bot, "ranged", False) and not bot.facts.get("fists"):
            return "ranged"
    except Exception:
        pass
    return "melee"


CASTER_PROFS = ("PureMage", "Sorcerer", "Warlock")
KIT_FALLBACK = {"ranged": 511.0, "melee": 306.0, "caster": 569.0}   # caster: provision.py's caster kit at the stock shop prices (reagents 398, potions 150, dagger 21), 2026-10-29   # the mean full re-kits measured from provision.jsonl on 2026-10-21 (10 ranged, 6 melee); used only when the file cannot be read
PROVISION = os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", "work", "botfarm-watch", "provision.jsonl"))
_kit = {"t": 0.0, "v": None}


def kit_cost(g):
    """The mean cost of a full re-kit for the group (ranged >= 400 gold, melee >= 250 gold in one round for one bot), from provision.jsonl, recomputed every 10 min."""
    now = time.time()
    if _kit["v"] is None or now - _kit["t"] > 600:
        _kit["t"] = now
        try:
            rounds = {}
            with open(PROVISION, encoding="utf-8") as f:
                for line in f:
                    r = json.loads(line)
                    if r.get("qty", 0) > 0:
                        key = (r["bot"], r.get("why"), round(r["t"] / 120), r["cohort"])
                        rounds[key] = rounds.get(key, 0) + r["cost"]
            v = {}
            for c, floor in (("ranged", 400), ("melee", 250), ("caster", 400)):
                full = [cost for (b, w, tt, cc), cost in rounds.items() if cc == c and cost >= floor]
                v[c] = sum(full) / len(full) if full else KIT_FALLBACK[c]
            _kit["v"] = v
        except Exception:
            _kit["v"] = dict(KIT_FALLBACK)
    return _kit["v"].get(g, KIT_FALLBACK[g])


def value(bot, kind):
    """Expected gold of one fight with this kind for the bot's group: kill_pct x (gold + extras + realise x carve) from the profit table; None without data."""
    e = entry(bot, kind)
    if e is None:
        return None
    try:
        import profit
        import task_core
        row = profit.table().get(kind) or profit.table().get(FAMILY.get(kind, "")) or {}
        loot = float(row.get("gold") or 0) + sum(profit.EXTRA_VALUE.get(x, 0) for x in row.get("extras") or ()) + float(row.get("carve") or 0) * task_core.CARVE_REALIZE
    except Exception:
        loot = 0.0
    return float(e.get("kill_pct", 0.0)) / 100.0 * loot


def death_cost(bot, kind):
    e = entry(bot, kind)
    if e is None:
        return None
    # the single-monster death rate (death_pct_solo: death_pct x the share of the group's deaths that came with at most one hostile near, prey_measured.py):
    # the bots pull one at a time (task_core.pull_crowd, the owner's 2026-10-29 rule), so pack deaths are not this fight's risk
    return float(e.get("death_pct_solo", e.get("death_pct", 0.0))) / 100.0 * kit_cost(group(bot))


def net(bot, kind):
    """Expected gold of a fight less its solo death cost and, for a bow user, the arrows a kill of this kind takes (task_core.arrow_cost: the bot's own measured
    arrows a kill at 2 gold; 2.0 for a cow, 4.2 for a hart, 5.4 for a black bear on 2026-10-29)."""
    v, c = value(bot, kind), death_cost(bot, kind)
    if v is None or c is None:
        return None
    try:
        import task_core
        arrows = task_core.arrow_cost(bot, kind) if group(bot) == "ranged" else 0.0
    except Exception:
        arrows = 0.0
    return v - c - arrows


FAMILY = {"greatermongbat": "mongbat", "spectre": "shade", "wraith": "shade"}   # Spectre.cs, Wraith.cs and Shade.cs are the same creature in the engine (AI_Mage, hits 46-60,
# damage 7-11, Magery 55-70): a spectre with no record killed BotBardAR at 1280,1400 on 2026-10-29 while the shade's record says ranged die in 70% of fights           # a kind with too few fights counts with its family (the Watcher, 2026-10-21: a greater mongbat killed BardAdvR; same family as the mongbat)


def entry(bot, kind):
    tab = _load().get(group(bot)) or {}
    for k in (kind, FAMILY.get(kind)):
        e = tab.get(k) if k else None
        if e and int(e.get("fights", 0)) >= PARAMS["min_fights"]:
            return e
    return None


def announce(bot):
    """The event measured_params once per load of the file per bot."""
    if _state.get("announce") and bot.__dict__.get("_mp_made") != _state["made"]:
        bot.__dict__["_mp_made"] = _state["made"]
        try:
            bot.ev("measured_params", made=_state["made"], kinds=len(_state["data"].get("ranged") or {}) + len(_state["data"].get("melee") or {}), rule="expected value",
                   kit_ranged=round(kit_cost("ranged")), kit_melee=round(kit_cost("melee")), min_fights=PARAMS["min_fights"])
        except Exception:
            pass


def give_up_s(bot, kind):
    """Seconds after which a fight with this kind is let go: its measured ttk_p90 for the bot's group; None without data."""
    e = entry(bot, kind)
    return float(e["ttk_p90"]) if e and e.get("ttk_p90") else None


def deadly(bot, kind):
    """True when a fight with the kind costs more in expected deaths than it pays (death_cost > value; 30+ fights of the bot's group)."""
    n = net(bot, kind)
    return n is not None and n < 0


def allowed(bot, kind):
    """(ok, why) by the measured rates of the bot's group."""
    e = entry(bot, kind)
    if e is None:
        return True, ""
    v, c = value(bot, kind), death_cost(bot, kind)
    if v is not None and c is not None and c > v:
        return False, f"{group(bot)}: expected {v:.0f} gold a fight against {c:.0f} of deaths ({e['kill_pct']:.0f}% kills, {e['death_pct']:.1f}% deaths in {e['fights']} fights)"
    return True, ""
