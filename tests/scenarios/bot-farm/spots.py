"""The per-spot ground (docs/Bot-Farm-Decision-Core-Plan-2.md, piece 1): the unit of hunting ground is the SPOT, not the area. A spot is a canonical
creature spawner on the surface within REACH of home (Britain is the hub: the owner, 2026-10-20), a canonical spawner of a rung dungeon reached from
Britain (dungeon_spots: tiers 4 to 6, offered only to a bot whose rung is open, task_core.tiers; the journey takes a gate or a teleporter as a leg), (the spawn files: its place, kinds, count, respawn delays) or a memory cell with sightings that no
spawner covers (the rule list's r_explore ground). A spot carries its kinds, its respawn clock (the shared memory's last kill at its cell, `spotkill`
events, so one bot's kill tells every bot when the respawn is due), the bots on it now (the memory's presence within the cell: crowding BY SPOT), its
tier (the Britain area it lies in, else 1) and its rate record (farm.db `task_spot`: kills a visit, keyed group|band|cell).

The hunt task is a TOUR: a cluster of spots within CLUSTER_R of a seed, ordered nearest-next, scored as expected kills a minute over the whole tour (the
walk to the seed, the legs between spots, the fights), with a Thompson draw per spot over its rate record and the prior from its contents. A crowded
spot (another bot on it) is skipped unless it holds CROWD_OK creatures or more. Banned spots (task_core: a tour that failed rests its spots) are out.
"""
from __future__ import annotations

import math
import os
import re
import time

REACH = 320                     # surface spawners this far from home. Widened step by step on the owner's word (2026-10-29, "Widen gradually"): within 400 tiles the open
                                # spawners with a paying kind release about 503 creatures an hour and the 20 bots took about 300 (roam 88%); 500 tiles hold 184 spawners
                                # (928 an hour). Britain stays the hub (the owner, 2026-10-20): the bots walk out and come back to sell. 480 was tried 18:43-19:53: four deaths in the
                                # gazer and gargoyle pocket north-east (1750-1840 x 1205-1250) and the undead box; back to 320 while the memory cells' bypass is fixed
REACH_WIDE = 375                # feature reach_wide (A/B, 2026-11-02): this far for the bots that have it. The north-east gazer and gargoyle pocket where REACH 480
                                # cost four deaths (1750-1840 x 1205-1250) begins 379 tiles from Britain's centre (y 1250 against 1629), so 375 leaves it out while
                                # taking in South Woods (5 spawners at 353-378), Far North-east Forest (2 at 370-377) and Troll Hills' far side: twenty fighters
                                # shared the spawns within 320 and roamed 36-73% of their time looking for prey (01:00-01:40)
DUNGEON_REACH = 900             # a dungeon whose surface door is this far from home, or from a public moongate (a gate leg of the journey from Britain), is a journey a player
                                # makes (Despise is 540 tiles from Britain's bank). Surface ground stays within REACH of home: Britain is the hub (the owner, 2026-10-20:
                                # "drop 'towns beyond britain' for now ... they all should be journeying to/from there")
CLUSTER_R = 90
TOUR_N = 6
CROWD_OK = 3
SURFACE_X = 5120
CELL_COVER = 20                 # a memory cell this close to a spawner spot is that spawner
SPOT_CACHE_S = 600
RANK_CAP = 3.0                  # tour_rank: a tour's estimate counts in its score up to this many times EXPECT_CAP (one wild draw does not win everything)
RANK_GOLD = 2400.0              # tour_rank, judged by gold: up to this many gold an hour. 3 x 120 tied every gold-judged tour (scores 5.75-5.98, 2026-11-05); 2,400 is
                                # the largest prior and the best fighter hour measured that day was 2,231 earned gold a bot-hour (BotFairSwordNR)
VISIT_KILLS = 2.0               # kills a visit a spot of enough creatures yields before any record (a player clears two and moves on)
DUE_SOON = 120.0                # a respawn due within this many seconds is worth the wait at the spot
# item 5 (docs/Bot-Farm-Capability-Plan-2026-10-20.md, "The world beyond Britain"): the dungeon rungs as tiers above 3. Level 1 of the seven rung dungeons is
# tier 4 (rung 1), their deeper levels tier 5 (rung 2), the Hot Zone (shard-rules.json hotZones.dungeonRegions: Hythloth) tier 6 (rung 3). A level is a
# connected component of the dungeon grid (walkroute's walkgrid-dungeons.bin): level 1 is what the entrance landing reaches on foot, or through one inner
# teleporter when the landing's component is a small antechamber (Despise lands in 18 cells behind a stair teleporter); everything beyond is deeper.
RUNG_DUNGEONS = ("Despise", "Shame", "Deceit", "Covetous", "Wrong", "Destard", "Hythloth")
TIER_RUNG1, TIER_DEEP, TIER_HOT = 4, 5, 6
ANTECHAMBER = 50                # coarse 4x4 cells: a landing component this small is an antechamber, not a level


def norm(s):
    return re.sub(r"[^a-z]", "", str(s or "").lower())


_SPAWN = {"t": None}


def spawner_spots():
    """[{id, x, y, kinds, count, mn, mx, home}] of the surface creature spawners (read once a process)."""
    if _SPAWN["t"] is not None:
        return _SPAWN["t"]
    out = []
    try:
        import danger
        import spawners as sp
        import task_core
        known = set(danger.stats().keys())
        for _f, s in sp.canonical(os.path.abspath(task_core.SPAWNS)):
            loc = s.get("location") or [0, 0, 0]
            if s.get("map") not in ("Felucca", 0) or int(loc[0]) >= SURFACE_X:
                continue
            kinds = sorted({norm(e.get("name")) for e in s.get("entries", []) if norm(e.get("name")) in known})
            if not kinds:
                continue
            mn, mx = task_core.spawn_delay_at(int(loc[0]), int(loc[1]))
            out.append({"id": f"sp{int(loc[0])},{int(loc[1])}", "x": int(loc[0]), "y": int(loc[1]), "kinds": kinds, "count": int(s.get("count", 1) or 1),
                        "mn": mn, "mx": mx, "home": int(s.get("homeRange", 10) or 10), "src": "spawner"})
    except Exception:
        out = []
    _SPAWN["t"] = out
    return out


def cell_of(x, y):
    return f"{int(x) // 40 * 40},{int(y) // 40 * 40}"


# ---- the dungeon rungs (item 5) ----------------------------------------------------------------------------------------------------------------------

_HOT = {"t": None}


def hot_zones():
    """The dungeon regions the shard runs as Hot Zones (shard-rules.json hotZones.dungeonRegions), else Hythloth."""
    if _HOT["t"] is None:
        names = []
        try:
            import json
            cfg = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "data", "configuration", "shard-rules.json")
            d = json.load(open(cfg, encoding="utf-8-sig"))
            names = [r.get("name") for r in (d.get("hotZones") or {}).get("dungeonRegions", []) if r.get("name")]
        except Exception:
            names = []
        _HOT["t"] = tuple(names) or ("Hythloth",)
    return _HOT["t"]


_LEVELS = {}
_GRAPH = {}


def _flood(grid, x, y, min_open=4):
    c0 = (int(x) // 4, int(y) // 4)
    seen, q = {c0}, [c0]
    for c in q:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                n = (c[0] + dx, c[1] + dy)
                if n not in seen and grid.open_cell(*n) >= min_open:
                    seen.add(n)
                    q.append(n)
    return seen


def dungeon_levels(dun):
    """{coarse cell: level} of a rung dungeon: level 1 is the component the entrance landings reach (an antechamber under ANTECHAMBER cells counts as the
    way in, and the inner teleporters leaving it are followed once), each inner teleporter out of a level leads to level + 1. {} without the grid."""
    if dun in _LEVELS:
        return _LEVELS[dun]
    out = {}
    try:
        import gazetteer as gz
        import walkroute
        grid = walkroute.dungeon()
        g = gz.get()
        if grid is None:
            _LEVELS[dun] = out
            return out
        inner = [t for t in g.trans if t["src_side"] == dun and t["dst_side"] == dun]
        queue = [(tuple(t["dst"][:2]), 1) for t in g.trans if t["src_side"] == "surface" and t["dst_side"] == dun]
        while queue:
            (x, y), level = queue.pop(0)
            if (x // 4, y // 4) in out:
                continue
            comp = _flood(grid, x, y)
            small = len(comp) < ANTECHAMBER
            for c in comp:
                out.setdefault(c, level)
            for t in inner:
                sx, sy = t["src"][0], t["src"][1]
                if (sx // 4, sy // 4) in comp:
                    queue.append(((t["dst"][0], t["dst"][1]), level if small else level + 1))
    except Exception:
        out = {}
    _LEVELS[dun] = out
    return out


def dungeon_graph(dun):
    """{"comp": {coarse cell: component id}, "edges": {component: [(transition, component)]}} of a rung dungeon: the walkable components of its grid (floods from
    every teleporter end inside it) and the inner teleporters joining them. A tour stays in one component; travel.inner_hops crosses between them."""
    if dun in _GRAPH:
        return _GRAPH[dun]
    out = {"comp": {}, "edges": {}}
    try:
        import gazetteer as gz
        import walkroute
        grid = walkroute.dungeon()
        g = gz.get()
        if grid is not None:
            ends = []
            for t in g.trans:
                if t["dst_side"] == dun:
                    ends.append((int(t["dst"][0]), int(t["dst"][1])))
                if t["src_side"] == dun:
                    ends.append((int(t["src"][0]), int(t["src"][1])))
            n = 0
            for x, y in ends:
                if (x // 4, y // 4) in out["comp"]:
                    continue
                n += 1
                for c in _flood(grid, x, y):
                    out["comp"].setdefault(c, n)
            for t in g.trans:
                if t["src_side"] == dun and t["dst_side"] == dun:
                    a = out["comp"].get((int(t["src"][0]) // 4, int(t["src"][1]) // 4))
                    b = out["comp"].get((int(t["dst"][0]) // 4, int(t["dst"][1]) // 4))
                    if a is not None and b is not None and a != b:
                        out["edges"].setdefault(a, []).append((t, b))
    except Exception:
        out = {"comp": {}, "edges": {}}
    _GRAPH[dun] = out
    return out


def component(x, y, side=None):
    """The walkable component id of a point in a rung dungeon (dungeon_graph), None elsewhere or off the grid."""
    try:
        import gazetteer as gz
        side = side or gz.side(int(x), int(y))
    except Exception:
        return None
    if side not in RUNG_DUNGEONS and side not in hot_zones():
        return None
    return dungeon_graph(side)["comp"].get((int(x) // 4, int(y) // 4))


def inner_hops(side, frm, to):
    """The inner teleporters to take, in order, between two points of one dungeon that no walk joins ([] when one component holds both; None when no chain does)."""
    gr = dungeon_graph(side)
    a, b = gr["comp"].get((int(frm[0]) // 4, int(frm[1]) // 4)), gr["comp"].get((int(to[0]) // 4, int(to[1]) // 4))
    if a is None or b is None:
        return None
    if a == b:
        return []
    prev, queue = {a: None}, [a]
    for cur in queue:
        for t, nxt in gr["edges"].get(cur, ()):
            if nxt not in prev:
                prev[nxt] = (cur, t)
                queue.append(nxt)
    if b not in prev:
        return None
    hops, cur = [], b
    while cur != a:
        p, t = prev[cur]
        hops.append(t)
        cur = p
    hops.reverse()
    return hops


def dungeon_tier(x, y, side=None):
    """The tier of a point on the dungeon side: TIER_HOT in a Hot Zone dungeon, TIER_RUNG1 on level 1 of a rung dungeon, TIER_DEEP deeper, None elsewhere."""
    try:
        import gazetteer as gz
        side = side or gz.side(x, y)
    except Exception:
        return None
    if side in hot_zones():
        return TIER_HOT
    if side not in RUNG_DUNGEONS:
        return None
    level = dungeon_levels(side).get((int(x) // 4, int(y) // 4))
    return TIER_RUNG1 if level == 1 else TIER_DEEP


_DUNGEON = {"t": None}


def dungeon_spots():
    """[{id, x, y, kinds, count, mn, mx, home, src: "spawner", side, tier}] the canonical creature spawners of the rung dungeons (read once a process)."""
    if _DUNGEON["t"] is not None:
        return _DUNGEON["t"]
    out = []
    try:
        import danger
        import gazetteer as gz
        import spawners as sp
        import task_core
        known = set(danger.stats().keys())
        g = gz.get()
        for _f, s in sp.canonical(os.path.abspath(task_core.SPAWNS)):
            loc = s.get("location") or [0, 0, 0]
            if s.get("map") not in ("Felucca", 0) or int(loc[0]) < SURFACE_X:
                continue
            side = g.side(int(loc[0]), int(loc[1]))
            if side not in RUNG_DUNGEONS:
                continue
            kinds = sorted({norm(e.get("name")) for e in s.get("entries", []) if norm(e.get("name")) in known})
            if not kinds:
                continue
            tier = dungeon_tier(int(loc[0]), int(loc[1]), side)
            if tier is None:
                continue
            mn, mx = task_core.spawn_delay_at(int(loc[0]), int(loc[1]))
            out.append({"id": f"sp{int(loc[0])},{int(loc[1])}", "x": int(loc[0]), "y": int(loc[1]), "kinds": kinds, "count": int(s.get("count", 1) or 1), "mn": mn, "mx": mx,
                        "home": int(s.get("homeRange", 10) or 10), "src": "spawner", "side": side, "tier": tier, "comp": component(int(loc[0]), int(loc[1]), side)})
    except Exception:
        out = []
    _DUNGEON["t"] = out
    return out


_GATES = {"t": None}


def gate_points():
    """[(x, y)] of the public moongates (the gazetteer), read once."""
    if _GATES["t"] is None:
        try:
            import gazetteer as gz
            _GATES["t"] = [(int(p["x"]), int(p["y"])) for p in gz.get().by_role.get("moongate", ()) if int(p["x"]) < SURFACE_X]
        except Exception:
            _GATES["t"] = []
    return _GATES["t"]


def entrances(dun):
    """[(x, y)] the surface entries of a dungeon's teleporters (the gazetteer's surface -> dungeon transitions)."""
    try:
        import gazetteer as gz
        return [(int(t["src"][0]), int(t["src"][1])) for t in gz.get().trans if t["src_side"] == "surface" and t["dst_side"] == dun]
    except Exception:
        return []


def door_reachable(x, y, home, reach=DUNGEON_REACH):
    """A dungeon's surface door within `reach` of home, or of a public moongate (the gate is a leg of the journey from Britain: travel.py)."""
    if max(abs(x - home[0]), abs(y - home[1])) <= reach:
        return True
    return any(max(abs(x - gx), abs(y - gy)) <= reach for gx, gy in gate_points())


def memory_spots(bot, taken):
    """Memory cells with sightings that no spawner spot covers, as spots (two creatures, five to ten minutes)."""
    out = []
    try:
        from memory import cell_center
        home = bot.home_centre()
        cells = bot.mem.hunting_cells(near=home, radius=reach_of(bot), n=20)
    except Exception:
        return out
    for score, cell in cells:
        cx, cy = cell_center(cell)
        if any(max(abs(cx - x), abs(cy - y)) <= CELL_COVER for x, y in taken):
            continue
        c = bot.mem.state["world"]["cells"].get(cell) or {}
        kinds = sorted(k for k, n in (c.get("sights") or {}).items() if n >= 1)
        if not kinds:
            continue
        out.append({"id": f"cell{cell}", "x": int(cx), "y": int(cy), "kinds": kinds, "count": 2, "mn": 300.0, "mx": 600.0, "home": 20, "src": "memory"})
    return out


def behind_box(bot, hx, hy, x, y):
    """True when the bot may not enter the undead box (task_core.box_bot: under UNDEAD_HP hit points) and the straight way from home to the spot crosses the box
    grown by the creatures' notice range (task_core.PULL_CLEAR): the ground north of it. With REACH 480, BotMaceAdvR (93 hit points) hunted north of the box and a
    spectre killed it on the way back (1439,1353, 18:53, 2026-10-29); the route penalty is soft and the flight runs toward town, through the box."""
    try:
        import task_core
        if not task_core.box_bot(bot):
            return False
        x0, y0, x1, y1 = task_core.UNDEAD_BOX
        pad = task_core.PULL_CLEAR
        n = max(1, int(max(abs(x - hx), abs(y - hy)) // 5))
        for i in range(n + 1):
            px, py = hx + (x - hx) * i / n, hy + (y - hy) * i / n
            if x0 - pad <= px <= x1 + pad and y0 - pad <= py <= y1 + pad:
                return True
        return False
    except Exception:
        return False


def way_clear(hx, hy, x, y, losing):
    """True when the straight way from home to the spot stays out of every losing spawner's reach (its home range + the creatures' notice range), the spot's
    own surroundings excepted (in_losing_range judges those). BotRangerBR walked from Britain to a wolf spawner at 1846,1160 through the gazer and gargoyle
    spawners at y 1252 and a gazer killed it at 1800,1240 (19:12, 2026-10-29): the route penalty is soft, the short way crossed."""
    n = max(1, int(max(abs(x - hx), abs(y - hy)) // 5))
    for i in range(n):                                            # the last point (the spot itself) is in_losing_range's to judge
        px, py = hx + (x - hx) * i / n, hy + (y - hy) * i / n
        for ox, oy, r in losing:
            if abs(ox - px) <= r and abs(oy - py) <= r:
                return False
    return True


def reach_of(bot):
    try:
        return REACH_WIDE if bot.feature("reach_wide") else REACH
    except Exception:
        return REACH


def all_spots(bot):
    """This bot's spots: within REACH of home, on the surface, not in a city, their tier in the bot's tiers (cached SPOT_CACHE_S)."""
    import task_core
    dh = (bot.facts or {}).get("dungeon_hunt") if hasattr(bot, "facts") else None
    if dh:
        # a dungeon trip's hunt (first_trip.trip_dungeon_hunt): that dungeon's level-1 spots only, so the core neither wanders deeper nor walks out to hunt;
        # and none holding a heavy kind (HEAVY_UNMEASURED, heavy_by_stats): Despise's "level 1" by the grid is two floors, the lizardmen (57, upstairs from
        # the landing) and the ettins and earth elementals below them (Despise.json)
        return [dict(s, cell=cell_of(s["x"], s["y"])) for s in dungeon_spots() if s["side"] == dh.get("side") and s["tier"] == TIER_RUNG1
                and not any(any(h in k for h in HEAVY_UNMEASURED) or heavy_by_stats(k) for k in s["kinds"])]
    cautious = (task_core.cautious(bot), task_core.rung_ready(bot))
    hit = bot.__dict__.get("_spots")
    if hit and time.time() - hit[0] < SPOT_CACHE_S and (len(hit) < 3 or hit[2] == cautious):         # a bot that runs out of heals (or restocks) gets its tiers again at once, not after ten minutes
        return hit[1]
    try:
        hx, hy = bot.home_centre()
    except Exception:
        hx, hy = 1470, 1620
    ts = task_core.tiers(bot)
    try:
        import places
        tier_at = places.area_tier_at
    except Exception:
        tier_at = None
    out = []
    try:
        import task_core as _tc
        losing = [(o["x"], o["y"], max(int(o.get("home") or 10), 1) + _tc.PULL_CLEAR) for o, _k in deadly_spawners(bot)]
    except Exception:
        losing = []
    reach = reach_of(bot)
    base = [s for s in spawner_spots() if max(abs(s["x"] - hx), abs(s["y"] - hy)) <= reach and not behind_box(bot, hx, hy, s["x"], s["y"])
            and way_clear(hx, hy, s["x"], s["y"], losing)]
    mem_cells = [s for s in memory_spots(bot, [(s["x"], s["y"]) for s in base])
                 if max(abs(s["x"] - hx), abs(s["y"] - hy)) <= reach and not behind_box(bot, hx, hy, s["x"], s["y"]) and way_clear(hx, hy, s["x"], s["y"], losing)]
    # the memory's hunting cells pass the same tests as the spawners: BotArcherCR toured "cell1840,1160", 539 tiles out, through the gargoyle band, and died at
    # 1834,1205 (19:52, 2026-10-29): the cells were added after the spawner filters
    for s in base + mem_cells:
        try:
            if bot.spot_in_city(s["x"], s["y"]):
                continue
        except Exception:
            pass
        tier = (tier_at(s["x"], s["y"]) if tier_at else None) or 1
        if tier not in ts:
            continue
        out.append(dict(s, tier=tier, cell=cell_of(s["x"], s["y"]), side="surface"))
    if any(t > 3 for t in ts):
        for s in dungeon_spots():
            if s["tier"] not in ts:
                continue
            doors = entrances(s["side"])
            if not doors or not any(door_reachable(dx, dy, (hx, hy)) for dx, dy in doors):
                continue
            out.append(dict(s, cell=cell_of(s["x"], s["y"])))
    bot.__dict__["_spots"] = (time.time(), out, cautious)
    return out


# ---- what a spot is worth ---------------------------------------------------------------------------------------------------------------------------

RELAX_MAX = 3                   # the fallback when no spot is open twice running (task_core.tick): 1 crowding off, 2 the area-risk veto off (deadly kinds still veto),
                                # 3 the worth floor off on the bot's lowest tier (the safest spot; the hunt tree then takes any prey the danger model accepts)


HOSTILE_R = 30                  # tiles: a spawner this near that holds an on-sight attacker a fist fighter cannot handle closes the spot to it
_HOSTILE = {}


def hostile_near(bot, s):
    """True when this spawner or another within HOSTILE_R tiles holds a kind that attacks on sight and is not something the bot's hands can kill (cached per spot and bot)."""
    import task_core
    key = (s["id"], bool(bot.facts.get("fists")))
    if key in _HOSTILE:
        return _HOSTILE[key]
    bad = False
    for o in spawner_spots() + [s]:
        if max(abs(o["x"] - s["x"]), abs(o["y"] - s["y"])) <= HOSTILE_R and any(task_core.aggressive_kind(k) and not bot.fist_prey(k) for k in o["kinds"]):
            bad = True
            break
    _HOSTILE[key] = bad
    return bad


HEAVY_UNMEASURED = ("ettin", "troll", "ogre", "gazer", "gargoyle", "shade", "wraith", "spectre", "lich", "reaper", "harpy")     # hunter.HunterBot.HEAVY_CAMP


STEP_UPS = ("orc", "ratman", "lizardman")      # hunter.HunterBot.TIER2_GROUP's beginner step-ups (the owner killed them easily with a new archer): judged by records, not by hit points


def heavy_by_stats(kind):
    """An attack-on-sight kind (creature_stats ai, not AI_Animal) at least as tough as the weakest of HEAVY_UNMEASURED: its maximum hit points at or over theirs
    (60: shade, wraith, spectre). Only asked for kinds with no fights on record: a sea spawn (water elemental 93, kraken 468) is no hunting ground for a newbie."""
    try:
        import task_core
        if not task_core.aggressive(kind) or kind in STEP_UPS:
            return False
        task_core.aggressive("cow")
        cs = task_core._CS
        floor = min(max(cs[h]["hits"]) for h in HEAVY_UNMEASURED if h in cs)
        return max((cs.get(kind) or {}).get("hits") or [0]) >= floor
    except Exception:
        return False


def deadly_spawners(bot):
    """[(spawner, kind)] of the surface spawners holding a kind whose measured death rate for this bot's group is over the cut-off (measured.deadly), cached 10 min per bot."""
    hit = bot.__dict__.get("_deadly_sp")
    if hit and time.time() - hit[0] < 600:
        return hit[1]
    import measured
    out = []
    for o in spawner_spots():
        # the spawner is a danger to this bot when its kinds, together, cost more in expected deaths than they pay (measured.net summed over its kinds with
        # data; the Watcher, 2026-10-29: one kind over a cut-off used to close every spot in its range, which closed nearly all tier-1 ground to the archers)
        nets = [(measured.net(bot, k), k) for k in o["kinds"]]
        heavy = [k for n, k in nets if n is None and (any(h in k for h in HEAVY_UNMEASURED) or heavy_by_stats(k))]
        prior_ok = getattr(bot, "prior_ok", None)
        if heavy and callable(prior_ok):
            heavy = [k for k in heavy if not prior_ok(k)]              # feature prior_worth: a heavy kind the danger prior accepts at tier 3 is not a losing spawner
        if heavy:
            out.append((o, heavy[0]))                             # an unmeasured kind of the hunter's HEAVY_CAMP list: a gazer, a gargoyle, an ettin (BotHealAdvR died to two gazers
            continue                                              # and a gargoyle 452 tiles out with REACH 480, 2026-10-29: no fights on record, so the sum below skipped them)
        nets = [(n, k) for n, k in nets if n is not None]
        if nets and sum(n for n, k in nets) < 0:
            out.append((o, min(nets)[1]))
    bot.__dict__["_deadly_sp"] = (time.time(), out)
    return out


def measured_danger_near(bot, s):
    """(kind, spawner) when a spawner whose creatures roam to this spot (the distance within that spawner's homeRange, shard spawner data) holds a kind with a measured death rate over the group's cut-off."""
    import task_core
    for o, k in deadly_spawners(bot):
        if max(abs(o["x"] - s["x"]), abs(o["y"] - s["y"])) <= max(int(o.get("home") or 10), 1) + task_core.PULL_CLEAR:    # + the creatures' perception reach (14)
            return k, o
    return None


def spot_prior(bot, s, deadly, relax=0, why=None):
    """{ek, gold, skill, die, kinds} for one visit, or None when the spot is vetoed (a deadly kind, a risky cell) or holds nothing this bot hunts. `why` (a Counter)
    gets the reason a spot is refused; `relax` (RELAX_MAX) loosens the tests in order."""
    import task_core
    if any(k in deadly for k in s["kinds"]):
        if why is not None:
            why["deadly kind"] += 1
        return None
    md = measured_danger_near(bot, s)
    if md:                                                            # a spawner whose creatures reach this spot holds a kind that kills this group (measured death_pct): the spot is off
        if why is not None:
            why["measured danger"] += 1
        key = f"{md[1]['id']}"
        logged = bot.__dict__.setdefault("_route_avoided", {})
        if time.time() - logged.get(key, 0) > 1800:
            logged[key] = time.time()
            try:
                bot.ev("route_avoided", prey=md[0], xy=[md[1]["x"], md[1]["y"]], spot=s["id"])
            except Exception:
                pass
        return None
    if task_core.avoided(bot, s["kinds"]):                            # the bot's own learned-avoid list (MaceBR's named eleven kinds and it still walked to a bone mage)
        if why is not None:
            why["learned avoid"] += 1
        return None
    try:
        if task_core.hands_only(bot) and hostile_near(bot, s):    # fists or a dagger: the cows are the earnings; a giant spider, a reaper or an ettin that attacks on sight in this spawner or within HOSTILE_R tiles is the danger (MaceBR, 14:55)
            if why is not None:
                why["on-sight attackers near"] += 1
            return None
    except Exception:
        pass
    if relax < 2:
        try:
            v, bad = bot.field_spawner([s["x"], s["y"], s["home"], s["kinds"]], deadly)
            if bad:
                if why is not None:
                    why["risky cell"] += 1
                return None
        except Exception:
            pass
    import danger
    if relax >= 3:
        kinds = [k for k in s["kinds"] if danger.acceptable(task_core.kind_risk(bot, k, s["tier"]), "prey")]
    else:
        kinds = [k for k in s["kinds"] if task_core.fightable(bot, k, deadly, s["tier"])]
    if not kinds:
        if why is not None:
            danger_ok = [k for k in s["kinds"] if danger.acceptable(task_core.kind_risk(bot, k, s["tier"]), "prey")]
            why["danger model" if not danger_ok else "worth floor"] += 1
        return None
    share = len(kinds) / max(1, len(s["kinds"]))
    ek = min(float(s["count"]) * share, VISIT_KILLS)
    gold = sum(task_core.gold_per_kill(bot, k) for k in kinds) / len(kinds)
    skill = sum(task_core.skill_per_kill(bot, k) for k in kinds) / len(kinds)
    die = sum(task_core.kind_risk(bot, k, s["tier"])["die"] for k in kinds) / len(kinds)
    ttk = sum(task_core.kill_seconds(bot, k) for k in kinds) / len(kinds)
    return {"ek": ek, "gold": gold, "skill": skill, "die": die, "kinds": kinds, "ttk": ttk}


def last_kill_at(bot, cell):
    """When something was last killed at this cell by any bot (the memory's spotkill events), else None."""
    try:
        c = bot.mem.state["world"]["cells"].get(cell)
        return float(c.get("last_kill")) if c and c.get("last_kill") else None
    except Exception:
        return None


def availability(bot, s, t=None):
    """Share of the spot's creatures expected there now: 1 with no kill known, the respawned share since the last kill otherwise."""
    t = t or time.time()
    lk = last_kill_at(bot, s["cell"])
    if lk is None:
        return 1.0
    since = t - lk
    if since >= s["mx"]:
        return 1.0
    if since < s["mn"]:
        return 0.35                                         # whatever was not killed, and the odd early respawn
    return 0.35 + 0.65 * (since - s["mn"]) / max(1.0, s["mx"] - s["mn"])


def share_load(bot, s):
    """Other bots hunting this spot's ground now or claiming it (hunter.ground_load: present in the last five minutes, or a ground claim; a started tour
    claims its spots, task_core.claim_tour). A spawner's respawn is shared among them, so a tour divides the spot's expected kills by 1 + this. Without
    it five fighters (FencerBR, MaceAdvR, FairSwordNR, MaceCR, SwordBR) toured the same two spots west of Britain at once, each expecting the whole
    respawn (18 kills a tour, 1-11 made), while the rest of the map stood empty (owner, 2026-11-07: "as soon as a player saw an area is camped/not
    enough spawns they would move on"). A dungeon hunt's spots are not shared out: one bot per stay is the ladder's rule."""
    if s.get("side", "surface") != "surface":
        return 0
    try:
        return max(0, int(bot.ground_load(s["cell"])))
    except Exception:
        return 0


def crowded(bot, s):
    try:
        return bot.ground_load(s["cell"]) >= 1 and s["count"] < CROWD_OK
    except Exception:
        return False


def rate_key(bot, cell):
    import task_core
    return f"spot|{task_core.group(bot)}|{task_core.band(bot)}|{cell}"


def tours(bot, g, rng, banned=(), relax=0):
    """[{task: hunt, area: 'tour <seed>', spots: [[x, y, ek, id], ...], tour: [ids], score, expected, walk_min, die, n, judge, minutes, budget}] best first.
    The reasons spots were refused are left in bot.__dict__["_spot_why"] (a Counter) for the no-ground report."""
    import collections
    import task_core
    try:
        bot.mem.refresh()
        deadly = bot.mem.deadly_kinds()
    except Exception:
        deadly = set()
    try:
        table = __import__("farmdb").rate_table("task_spot")
    except Exception:
        table = {}
    here = (int(bot.c.x), int(bot.c.y))
    rate = task_core.walk_rate(bot)
    now = time.time()
    vals = {}
    loads = {}
    why = collections.Counter()
    pool = all_spots(bot)
    far_seen = []
    if relax >= 3 and pool:
        low = min(s["tier"] for s in pool)
        pool = [s for s in pool if s["tier"] == low]
    for s in pool:
        if s["id"] in banned:
            why["banned"] += 1
            continue
        if task_core.death_ground(bot, s["x"], s["y"]):
            why["own deaths"] += 1
            continue
        if relax < 1 and crowded(bot, s):
            why["crowded"] += 1
            continue
        pr = spot_prior(bot, s, deadly, relax, why)
        if not pr:
            continue
        r = table.get(rate_key(bot, s["cell"]))
        n = float(r[1]) if r else 0.0
        mean = (n * float(r[0]) + task_core.PRIOR_N * pr["ek"]) / (n + task_core.PRIOR_N) if r else pr["ek"]
        ek = task_core.draw(mean, n, rng) * availability(bot, s, now)
        load = share_load(bot, s)
        ek /= 1.0 + load                                      # the respawn is shared: each creature dies once, to one of the hunters on it (share_load)
        loads[s["id"]] = load
        vals[s["id"]] = (s, pr, ek, n)
    bot.__dict__["_spot_why"] = why
    if not vals:
        return []
    budget_h = task_core.HUNT_BUDGET / 3600.0
    measure = g["measure"]
    try:
        if task_core.provisioned(bot):
            measure = "gold"                                      # the owner's experiment is cash flow: provisioned bots choose ground by gold, whatever their goal counts
    except Exception:
        pass
    ranked = sorted(vals.values(), key=lambda v: -(v[2] / (1.0 + max(abs(here[0] - v[0]["x"]), abs(here[1] - v[0]["y"])) / 150.0)))
    seeds = ranked[:14]
    # item 5: each dungeon side gets a seed too (its best spot), else the fourteen nearest always win the seat; the tour's own score then decides
    seen_far = set()
    for v in ranked[14:]:
        s = v[0]
        if s.get("side", "surface") == "surface" or s["side"] in seen_far:
            continue
        seen_far.add(s["side"])
        seeds.append(v)
    out = []
    for seed, spr, sek, sn in seeds:
        tour, at, used = [seed["id"]], (seed["x"], seed["y"]), {seed["id"]}
        legs = 0.0
        while len(tour) < TOUR_N:
            cand = [v for sid, v in vals.items() if sid not in used and v[0].get("side", "surface") == seed.get("side", "surface") and v[0].get("comp") == seed.get("comp")
                    and max(abs(v[0]["x"] - seed["x"]), abs(v[0]["y"] - seed["y"])) <= CLUSTER_R]            # one side, one walkable component (a dungeon's stairs are teleporters)
            if not cand:
                break
            nxt = min(cand, key=lambda v: max(abs(v[0]["x"] - at[0]), abs(v[0]["y"] - at[1])))
            legs += max(abs(nxt[0]["x"] - at[0]), abs(nxt[0]["y"] - at[1])) * task_core.ROUTE_FACTOR
            tour.append(nxt[0]["id"])
            used.add(nxt[0]["id"])
            at = (nxt[0]["x"], nxt[0]["y"])
        if seed.get("side", "surface") != "surface":
            lengths = [task_core.route_length(bot, d) for d in entrances(seed["side"])]
            length = min((v for v in lengths if v is not None), default=None)
            if length is not None:
                length += 60.0                                      # the dungeon walk from the landing (level 1 is close to the door)
        else:
            length = task_core.route_length(bot, (seed["x"], seed["y"]))
        if length is None:
            continue
        walk_min = length / rate
        kills = sum(vals[i][2] for i in tour)
        fights_min = sum(vals[i][2] * (vals[i][1]["ttk"] + 45.0) for i in tour) / 60.0
        minutes = walk_min + legs / rate + fights_min + 1.0 * len(tour)
        minutes = max(minutes, 8.0)
        hours = minutes / 60.0
        die = sum(vals[i][1]["die"] * vals[i][2] for i in tour) / max(kills, 1e-6)
        exp = {"kills": kills / hours, "gold": sum(vals[i][2] * vals[i][1]["gold"] for i in tour) / hours, "skill": sum(vals[i][2] * vals[i][1]["skill"] for i in tour) / hours}
        raw = {m: v * task_core.calib(bot, "hunt", m) for m, v in exp.items()}
        exp = {m: min(task_core.EXPECT_CAP.get(m, 1e9), v) for m, v in raw.items()}     # learning 1: measured against expected, per task kind, group and measure; capped
        judge = task_core.judge_measure(measure, exp)
        if judge == "kills" and measure != "kills" and bot.feature("judge_gold"):
            # feature judge_gold: a goal the hunt cannot move (a skill above 80 gains by Mastery's day, judge_measure) is hunted for gold, as a player
            # with nothing to raise in an hour hunts for money, not for the count. By kills, BotRangerAR (Archery 91) toured the chicken and rat fields
            # south-west of Britain at 40 gold an hour from its tours (2026-11-03: 3-5 kills and 0.0 skill a 12-minute tour)
            judge = "gold"
        # tour_rank: the score from the estimate before the cap (up to RANK_CAP times it). With the capped figure every tour at the cap scored
        # 18 x minutes/60 / minutes = 0.3, the ties went to the safest or nearest, and the archers and fighters circled the same few spots by town whatever
        # their records said (0.290-0.297 for every choice, 2026-11-01). The capped figure stays the monitor's expectation.
        rank = raw if bot.feature("tour_rank") else exp
        limit = RANK_GOLD if judge == "gold" else RANK_CAP * task_core.EXPECT_CAP.get(judge, 1e9)
        progress = min(rank[judge], limit) * hours
        if measure == "gold" or judge == "gold":
            progress -= die * kills * float(bot.c.gold or 0) * 0.5
        cost = minutes + die * kills * task_core.DEATH_MIN
        out.append({"task": "hunt", "area": f"tour {seed['id']}", "spots": [[vals[i][0]["x"], vals[i][0]["y"], round(vals[i][2], 2), i] for i in tour], "tour": list(tour),
                    "side": seed.get("side", "surface"), "tier": max(vals[i][0]["tier"] for i in tour),
                    "score": round(progress / max(cost, 1.0), 4), "judge": judge, "draw": round(sek, 2), "mean": round(exp[judge], 3), "expected": {k: round(v, 3) for k, v in exp.items()},
                    "rank": round(min(rank[judge], limit), 1),
                    "walk_min": round(walk_min, 1), "die": round(die, 3), "n": min(vals[i][3] for i in tour), "kinds": sorted({k for i in tour for k in vals[i][1]["kinds"]})[:8],
                    "load": max(loads.get(i, 0) for i in tour), "minutes": round(minutes, 1), "budget": float(min(task_core.HUNT_BUDGET, max(600.0, minutes * 60.0))), "relax": relax})
    if relax >= 3:
        out.sort(key=lambda c: (c["die"], -c["score"]))           # the safest first
    else:
        out.sort(key=lambda c: -c["score"])
    return out


def record_visit(bot, cell, kills):
    """A spot's rate record: kills a visit, folded at the tour's end for every spot the tour visited."""
    try:
        import farmdb
        import task_core
        farmdb.rate_update("task_spot", rate_key(bot, cell), float(kills), task_core.ALPHA)
    except Exception:
        pass
