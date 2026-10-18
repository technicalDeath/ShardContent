"""The danger model (feature "danger_model"): how fights against a kind went for bots of this skill band against this pack size.
See work/botfarm/patches/patch_danger_model.py for the design. memory.py folds the fight records into state["world"]["fightb"] with fold_band(); the brains call
risk() and acceptable()."""
from __future__ import annotations

import json
import os
import time

HALF_LIFE = 6 * 3600.0
PRIOR_K = 4.0                 # a prior counts for this many fights
POOL_MIN = 10.0               # pooled fights needed before the pack ratio is trusted
KEYS = ("n", "kill", "death", "flee", "lost")
HARD = ("ettin", "ogre", "troll", "corpser", "wisp", "acidelemental", "giantserpent", "gargoyle", "orcishlord", "dragon", "drake", "wyrm", "wyvern",
        "poisonelemental", "brigand")
GROUP = ("orc", "ratman", "shade", "wraith", "spectre", "lizardman", "harpy")          # kinds that come in packs: the danger is how many
SINGLE = ("grizzlybear", "gazer")                                                     # single spawns, hard hitters
SOLO_DIE = ((30, 0.35), (50, 0.20), (70, 0.08), (1e9, 0.04))                         # a lone GROUP kind: death rate by skill band (upper edge, rate)
PETS = ("cat", "dog", "bird", "magpie", "crow", "raven", "sparrow", "pigeon", "chicken")
# livestock and small animals: the danger table's safe first prey (no deaths, 60%+ wins at 30-50); anything else unknown starts cautious
SAFE = ("cow", "bull", "sheep", "goat", "pig", "chicken", "rabbit", "hind", "hart", "deer", "rat", "dog", "cat", "bird", "frog",
        "headless", "llama", "horse", "eagle", "crane")
MODES = {"prey": (0.12, 0.60), "trip": (0.10, 0.50)}


def sband(skill):
    skill = skill or 0
    return "lt30" if skill < 30 else "30-50" if skill < 50 else "50-70" if skill < 70 else "70+"


def nband(near):
    near = near or 0
    return "0" if near <= 0 else "1" if near == 1 else "2+"


def _decay(f, now):
    dt = now - f.get("t", now)
    if dt > 0:
        k = 0.5 ** (dt / HALF_LIFE)
        for key in KEYS:
            f[key] *= k
    f["t"] = max(now, f.get("t", 0))


def fold_band(st, ev, grp):
    """One fight event into the four banded keys (st = a scope's state); events without skill or near are not banded."""
    if ev.get("skill") is None or ev.get("near") is None or ev.get("outcome") not in ("kill", "death", "flee", "lost"):
        return
    sb, nb, kind = sband(float(ev["skill"])), nband(int(ev["near"])), ev["m"]
    for key in (f"{kind}|{grp}|{sb}|{nb}", f"{kind}|{grp}|{sb}|*", f"*|{grp}|{sb}|{nb}", f"*|{grp}|{sb}|*"):
        f = st["fightb"][key]
        _decay(f, ev["t"])
        f["n"] += 1
        f[ev["outcome"]] += 1


def _counts(fb, key, now):
    f = fb.get(key)
    if not f:
        return {"n": 0.0, "kill": 0.0, "death": 0.0, "flee": 0.0}
    _decay(f, now)
    return f


# ---- the exchange estimate from the creatures' own numbers (creature_stats.json, make_creature_stats.py) ---------------------------------------------------
STATS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "creature_stats.json")
_STATS = None
EX = dict(w0=6.0, w1=0.15, swing=2.4, armk=120.0, arp=0.10, hp0=70.0, hp1=0.15, cast=1.4, breath=3.0, floor=0.01, dmax=0.95, f50=1.1, k=4.0)
POISON_X = {"Lesser": 1.2, "Regular": 1.4, "Greater": 1.7, "Deadly": 2.1, "Lethal": 2.6}
NEAR_EFF = {"0": 0, "1": 1, "2+": 2}


def stats():
    """{kind: creature entry} from creature_stats.json beside this file ({} when it is missing)."""
    global _STATS
    if _STATS is None:
        try:
            _STATS = json.load(open(STATS_PATH, encoding="utf-8"))
        except (OSError, ValueError):
            _STATS = {}
    return _STATS


def _avg(r, default):
    return (r[0] + r[1]) / 2.0 if r else default


def loss(kind, skill, near=0):
    """Fraction of the bot's hit points lost killing this kind and `near` more of it in turn, or None when the kind is not in the table."""
    c = stats().get(kind or "")
    if not c:
        return None
    skill = skill or 0
    wr = _avg(c.get("wrestling"), 30.0)
    extra = POISON_X.get(c.get("poison"), 1.3) if c.get("poison") else 1.0
    if c.get("casts"):
        extra *= EX["cast"]
    if c.get("breath"):
        extra *= EX["breath"]
    p_hit = min(1.0, max(0.02, (skill + 20) / (2.0 * (wr + 20))))
    w_eff = (EX["w0"] + EX["w1"] * skill) * (1 - c["armor"] / (c["armor"] + EX["armk"]))
    kill_s = _avg(c["hits"], 50.0) / (p_hit * w_eff / EX["swing"])
    p_c = min(1.0, max(0.02, (wr + 20) / (2.0 * (skill + 20))))
    swing_c = min(3.0, max(1.0, 3000.0 / (_avg(c.get("dex"), 60.0) + 100)))
    dps = p_c * _avg(c["damage"], 3.0) * (1 - EX["arp"]) * extra / swing_c
    turns = 1 + 1.4 * near + 0.5 * near * (near - 1)
    return dps * kill_s * turns / (EX["hp0"] + EX["hp1"] * skill)


def stats_prior(kind, skill, near=0):
    """{win, die, flee} from the exchange estimate, or None for a kind that is not in the table."""
    f = loss(kind, skill, near)
    if f is None:
        return None
    die = EX["floor"] + (EX["dmax"] - EX["floor"]) / (1.0 + (EX["f50"] / max(f, 1e-6)) ** EX["k"])
    flee = min(0.4, 0.08 + 0.3 * min(f, 1.5) / 1.5) * (1 - die)
    return {"die": die, "flee": flee, "win": max(0.0, 1.0 - die - flee)}


def prior(kind, skill, near=0):
    """{win, die, flee} before any fight record: the exchange estimate for a kind in creature_stats.json (for `near` companions), else for a bot fighting alone the species
    lists as a prior only (the cautious 15% for a kind never met)."""
    sp = stats_prior(kind, skill, near)
    if sp:
        return sp
    k = kind or ""
    if any(h in k for h in HARD):
        die, flee = 0.5, 0.3
    elif any(s in k for s in SINGLE):
        die, flee = (0.25 if (skill or 0) < 70 else 0.10), 0.2
    elif any(g in k for g in GROUP):
        die, flee = next(d for edge, d in SOLO_DIE if (skill or 0) < edge), 0.2
    elif any(p in k for p in PETS):
        die, flee = 0.0, 0.05
    else:
        if any(s in k for s in SAFE):
            die, flee = 0.02, 0.05
        else:
            return {"die": 0.15, "flee": 0.20, "win": 0.65, "unknown": True}       # never met: assume dangerous until the records say otherwise
    return {"die": die, "flee": flee, "win": max(0.0, 1.0 - die - flee)}


def prior_mem(mem, kind, skill):
    """The prior, with the kind's own fight totals (memory 'kinds', every fight of runs 1 and 2b) deciding an unknown kind: 8+ fights, won 70%+ and
    losing half the health or less on average make it 4%; otherwise it stays cautious."""
    p = prior(kind, skill, 0)
    if not p.get("unknown"):
        return p
    try:
        kd = mem.state["world"]["kinds"].get(kind)
    except Exception:
        kd = None
    if kd and kd["fights"] >= 8 and kd["kills"] / kd["fights"] >= 0.7 and kd["dmgpct"] / kd["fights"] <= 0.5:
        return {"die": 0.04, "flee": 0.10, "win": 0.86}
    return {k: v for k, v in p.items() if k != "unknown"}


def _shrink(c, p):
    """Counts c pulled toward the estimate p with PRIOR_K pseudo-fights."""
    n = c["n"]
    return {"die": (c["death"] + PRIOR_K * p["die"]) / (n + PRIOR_K), "flee": (c["flee"] + PRIOR_K * p["flee"]) / (n + PRIOR_K),
            "win": (c["kill"] + PRIOR_K * p["win"]) / (n + PRIOR_K)}


def risk(mem, kind, skill, near, grp=None):
    """{win, die, flee, n (fights in this exact band), n_kind (the kind's solo fights at this skill band), ratio (pack multiplier used), src}."""
    mem.refresh()
    fb = mem.state["world"].get("fightb") or {}
    grp, now = grp or mem.grp, time.time()
    sb, nb = sband(skill), nband(near)
    solo = _counts(fb, f"{kind}|{grp}|{sb}|0", now)
    pr = prior_mem(mem, kind, skill)
    p_solo = _shrink(solo, pr)
    if nb == "0":
        return {"win": p_solo["win"], "die": p_solo["die"], "flee": p_solo["flee"], "n": solo["n"], "n_kind": solo["n"], "ratio": 1.0,
                "src": "exact" if solo["n"] >= 5 else "prior"}
    # a pack: the kind's solo record, multiplied by how much deadlier this pack band is than fighting alone for ALL kinds at this skill band (a cautious
    # default until the pool has 10 fights in each), then pulled toward the kind's own record in this pack band
    pool_n, pool_0 = _counts(fb, f"*|{grp}|{sb}|{nb}", now), _counts(fb, f"*|{grp}|{sb}|0", now)
    ratio = 2.0 if nb == "1" else 2.5
    if pool_n["n"] >= POOL_MIN and pool_0["n"] >= POOL_MIN:
        ratio = ((pool_n["death"] + 1) / (pool_n["n"] + 4)) / ((pool_0["death"] + 1) / (pool_0["n"] + 4))
        ratio = max(1.0, min(4.0, ratio))
    ex = _counts(fb, f"{kind}|{grp}|{sb}|{nb}", now)
    adj = {"die": min(0.95, p_solo["die"] * ratio), "flee": min(0.95, p_solo["flee"] * ratio), "win": p_solo["win"] / ratio}
    if ex["n"] < 5:
        # nobody has fought this kind in this pack band yet: a clean solo record does not vouch for a pack, so the death rate is at least what the species
        # prior says for that pack (the prior solo rate times the pack multiplier in use), not the solo record that shrank it
        if kind in stats():
            floor = prior(kind, skill, NEAR_EFF[nb])                   # the exchange estimate for this pack (not the solo prior times a multiplier)
            adj["die"], adj["flee"] = max(adj["die"], floor["die"]), max(adj["flee"], floor["flee"])
        else:
            adj["die"] = max(adj["die"], pr["die"] * ratio)
    over = adj["die"] + adj["flee"] + adj["win"]
    if over > 1.0:
        adj["win"] = max(0.0, adj["win"] - (over - 1.0))
    p2 = _shrink(ex, adj)
    p2["flee"] = min(p2["flee"], max(0.0, 1.0 - p2["die"]))
    return {"win": p2["win"], "die": p2["die"], "flee": p2["flee"], "n": ex["n"], "n_kind": solo["n"], "ratio": round(ratio, 2),
            "src": "exact" if ex["n"] >= 5 else "solo x pack" if solo["n"] >= 5 else "prior"}


def acceptable(r, mode="prey"):
    die_max, bad_max = MODES[mode]
    return r["die"] <= die_max and r["die"] + r["flee"] <= bad_max
