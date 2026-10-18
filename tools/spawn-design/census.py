"""Spawn census of a rectangle of Felucca: every generated spawner in it, each creature's danger tier, the guard zones,
and where the bot farm's bots died and what they fought. Writes one JSON file for the spawn map page.

  python census.py X0 Y0 X1 Y1 OUT.json

Inputs: the deployed generated spawn data (ModernUO/Distribution/Data/BritanniaRenaissance/Alpha2b/Spawns), the
bot farm's creature stats and fight modes (tests/scenarios/bot-farm), regions.json and shard-rules.json (guard zones),
and the bot farm's shared-memory logs under work/ (fight and death records, 40x40 cells).

Danger tiers (for a new character: about 75 hit points, weapon skill 30-50):
  0 harmless  - passive (fights only when attacked) and weak, or does no damage
  1 beginner  - at most about 60 hit points and 10 a hit, no spells or poison above Lesser
  2 step-up   - about 60-75 hit points, or poison, or a passive animal that hits hard; bots at 30-70 skill lose about a quarter of these fights
  3 dangerous - 75-130 hit points, or casts spells
  4 deadly    - over 130 hit points or 15+ a hit
"""
import collections
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SC = os.path.normpath(os.path.join(HERE, "..", ".."))
WS = os.path.normpath(os.path.join(SC, ".."))
SPAWNS = os.path.join(WS, "ModernUO", "Distribution", "Data", "BritanniaRenaissance", "Alpha2b", "Spawns")
BOTS = os.path.join(SC, "tests", "scenarios", "bot-farm")
TOWN_CENTRE = (1470, 1620)

# Hand rulings where the formula and the farm's fights disagree (creature-danger.md, 2026-10-15).
TIER_OVERRIDE = {
    "orc": 2, "ratman": 2, "lizardman": 2, "harpy": 2, "greatermongbat": 2,
    "mongbat": 1, "skeleton": 1, "giantspider": 2, "brownbear": 2, "bull": 2,
    "grizzlybear": 3, "wisp": 4,
    # Hit hard but slow, rooted or rare in the farm's fights: dangerous, not deadly.
    "ettin": 3, "corpser": 3, "reaper": 3, "direwolf": 3,
    # The weak undead casters (46-60 hit points, a few points a hit) fight like orcs and ratmen, not like trolls: the farm's
    # shades won 28% and killed bots in 23% of 80 fights (orc 20% / 28%, ratman 22% / 26%). Step-up, not dangerous.
    "shade": 2, "spectre": 2, "wraith": 2, "bonemagi": 2, "skeletalmage": 2,
    # Armoured skeletons hit like an ettin with a troll's hit points: dangerous, not deadly.
    "boneknight": 3, "skeletalknight": 3,
}
TIER_NAMES = ["harmless", "beginner", "step-up", "dangerous", "deadly"]


def tier_of(name, stats, modes):
    k = name.lower()
    c = stats.get(k)
    if not c:
        return None  # not a creature (vendor, reagent, crop, camp)
    if k in TIER_OVERRIDE:
        return TIER_OVERRIDE[k]
    hits = sum(c["hits"]) / 2
    dmax = c["damage"][1]
    passive = modes.get(k, {}).get("mode") == "Aggressor"
    if hits > 130 or dmax >= 15:
        return 4
    if c["casts"] or hits > 75:
        return 3
    if hits > 60 or c["poison"] not in (None, "Lesser") or dmax > 10:
        return 2
    if passive and (hits <= 20 or dmax <= 2):
        return 0
    return 1


def guard_zones(rect):
    regions = json.load(open(os.path.join(WS, "ModernUO", "Distribution", "Data", "regions.json"), encoding="utf-8-sig"))
    rules = json.load(open(os.path.join(SC, "data", "configuration", "shard-rules.json"), encoding="utf-8-sig"))
    towns, other = [], []
    for r in regions:
        if r.get("Map") != "Felucca":
            continue
        areas = [[a["x1"], a["y1"], a["x2"], a["y2"]] for a in r.get("Area", [])
                 if a["x2"] > rect[0] and a["x1"] < rect[2] and a["y2"] > rect[1] and a["y1"] < rect[3]]
        if not areas:
            continue
        entry = {"name": r.get("Name"), "type": r["$type"], "rects": areas,
                 "child": bool(r.get("Parent")), "disabled": bool(r.get("GuardsDisabled"))}
        (towns if r["$type"] in ("TownRegion", "GuardedRegion") else other).append(entry)
    unguarded = [{"name": u["name"], "rects": [[q["x1"], q["y1"], q["x2"], q["y2"]] for q in u["rectangles"]]}
                 for u in rules.get("townGuards", {}).get("unguardedAreas", []) if u.get("map") == "Felucca"]
    return towns, other, unguarded


def subtract(rects, holes):
    """Rectangles [x1, y1, x2, y2) minus holes, as non-overlapping rectangles."""
    out = list(rects)
    for hx1, hy1, hx2, hy2 in holes:
        nxt = []
        for x1, y1, x2, y2 in out:
            if hx1 >= x2 or hx2 <= x1 or hy1 >= y2 or hy2 <= y1:
                nxt.append([x1, y1, x2, y2])
                continue
            if y1 < hy1: nxt.append([x1, y1, x2, hy1])
            if hy2 < y2: nxt.append([x1, hy2, x2, y2])
            my1, my2 = max(y1, hy1), min(y2, hy2)
            if x1 < hx1: nxt.append([x1, my1, hx1, my2])
            if hx2 < x2: nxt.append([hx2, my1, x2, my2])
        out = nxt
    return out


def outline(rects):
    """Boundary segments of a union of non-overlapping rectangles: edges shared by two rectangles cancel."""
    xs = sorted({v for r in rects for v in (r[0], r[2])})
    ys = sorted({v for r in rects for v in (r[1], r[3])})
    count = collections.Counter()
    for x1, y1, x2, y2 in rects:
        cut_x = [x for x in xs if x1 <= x <= x2]
        cut_y = [y for y in ys if y1 <= y <= y2]
        for a, b in zip(cut_x, cut_x[1:]):
            count[(a, y1, b, y1)] += 1
            count[(a, y2, b, y2)] += 1
        for a, b in zip(cut_y, cut_y[1:]):
            count[(x1, a, x1, b)] += 1
            count[(x2, a, x2, b)] += 1
    return [list(s) for s, n in count.items() if n == 1]


def guarded_zones(towns, unguarded):
    """Where the guards answer: top-level town and guarded regions (their child regions lie inside them) minus the
    shard's unguarded areas, which sit at priority 51 above the towns' 50 (TownGuardsService.UnguardedPriority)."""
    holes = [r for u in unguarded for r in u["rects"]]
    zones = []
    for t in towns:
        if t["name"] and not t.get("child") and not t.get("disabled"):
            rects = subtract(t["rects"], holes)
            if rects:
                zones.append({"name": t["name"], "rects": rects, "outline": outline(rects)})
    return zones


def in_rects(x, y, rects):
    return any(a <= x < c and b <= y < d for a, b, c, d in rects)


def bot_records(rect):
    deaths = collections.defaultdict(lambda: {"n": 0, "killers": collections.Counter()})
    fights = collections.defaultdict(lambda: {"n": 0, "deaths": 0, "kinds": collections.Counter()})
    files = sorted(set(glob.glob(os.path.join(WS, "work", "botfarm*", "memory*", "world.jsonl"))))
    files = [f for f in files if "false-start" not in f]
    for f in files:
        for line in open(f, encoding="utf-8", errors="replace"):
            if '"k":"death"' not in line and '"k":"fight"' not in line:
                continue
            try:
                r = json.loads(line)
            except ValueError:
                continue
            try:
                cx, cy = (int(v) for v in r.get("cell", "").split(","))
            except ValueError:
                continue
            if not (rect[0] - 40 < cx < rect[2] and rect[1] - 40 < cy < rect[3]):
                continue
            if r["k"] == "death":
                d = deaths[(cx, cy)]
                d["n"] += 1
                for k in r.get("killers") or []:
                    d["killers"][k if isinstance(k, str) else k.get("m", "?")] += 1
            else:
                g = fights[(cx, cy)]
                g["n"] += 1
                g["kinds"][r.get("m", "?")] += 1
                if r.get("outcome") == "death":
                    g["deaths"] += 1
    return ([{"x": x, "y": y, "n": v["n"], "killers": dict(v["killers"].most_common(4))} for (x, y), v in deaths.items()],
            [{"x": x, "y": y, "n": v["n"], "deaths": v["deaths"], "kinds": dict(v["kinds"].most_common(5))} for (x, y), v in fights.items()],
            [os.path.relpath(f, WS) for f in files])


def main(argv):
    rect = [int(v) for v in argv[:4]]
    out = argv[4]
    stats = json.load(open(os.path.join(BOTS, "creature_stats.json")))
    modes = json.load(open(os.path.join(BOTS, "fightmodes.json")))
    towns, other, unguarded = guard_zones(rect)
    zones = guarded_zones(towns, unguarded)
    guarded_rects = [r for z in zones for r in z["rects"]]
    manifest = json.load(open(os.path.join(SC, "data", "world-generation", "alpha2b", "world-generation.json"), encoding="utf-8-sig"))
    records = []
    for name in manifest["spawnerFiles"] + manifest["customSpawnerFiles"]:
        f = os.path.join(SPAWNS, name)
        if os.path.exists(f):
            records += [(f, r) for r in json.load(open(f, encoding="utf-8-sig"))]
    # The world-generation rule (Prepare-Alpha2bWorldData.ps1): walking back from the last record, a record is canonical
    # when its location and its guid are both new, so a shard file overrides a stock spawner by reusing its guid.
    seen_loc, seen_guid, canonical = set(), set(), []
    for f, r in reversed(records):
        key = (r["$type"], r.get("map"), *r["location"])
        if key not in seen_loc and r["guid"].lower() not in seen_guid:
            canonical.append((f, r))
        seen_loc.add(key)
        seen_guid.add(r["guid"].lower())
    canonical.reverse()
    spawners = []
    for f, s in canonical:
        if True:
            if s.get("map") != "Felucca":
                continue
            x, y, z = s["location"]
            if not (rect[0] <= x < rect[2] and rect[1] <= y < rect[3]):
                continue
            entries = []
            for e in s["entries"]:
                t = tier_of(e["name"], stats, modes)
                c = stats.get(e["name"].lower())
                entries.append({
                    "name": e["name"], "max": e["maxCount"], "tier": t,
                    "passive": modes.get(e["name"].lower(), {}).get("mode") == "Aggressor",
                    "hits": c and [int(v) for v in c["hits"]], "dmg": c and [int(v) for v in c["damage"]],
                    "casts": bool(c and c["casts"]), "poison": c and c["poison"],
                })
            creature = [e for e in entries if e["tier"] is not None]
            if not creature:
                kind = "vendor" if os.path.basename(f) in ("Vendors.json", "TownsPeople.json", "britain-vendor-overrides.json") else "resource"
                if any(e["name"].lower().endswith("camp") for e in entries):
                    kind = "camp"
            else:
                kind = "creature"
            guarded = in_rects(x, y, guarded_rects)
            spawners.append({
                "id": s["guid"][:8], "guid": s["guid"], "file": os.path.basename(f), "label": s.get("name"),
                "x": x, "y": y, "z": z, "count": s.get("count"), "home": s.get("homeRange", 0), "walk": s.get("walkingRange", 0),
                "delay": [s.get("minDelay"), s.get("maxDelay")], "region": s.get("region"), "kind": kind,
                # Graded by its most dangerous creature, passive or not (owner, 2026-10-18).
                "tier": max((e["tier"] for e in creature), default=None),
                "guarded": guarded,
                "dist": round(((x - TOWN_CENTRE[0]) ** 2 + (y - TOWN_CENTRE[1]) ** 2) ** 0.5),
                "entries": entries,
            })
    deaths, fights, files = bot_records(rect)
    json.dump({
        "rect": rect, "townCentre": TOWN_CENTRE, "tierNames": TIER_NAMES,
        "towns": towns, "otherRegions": other, "unguarded": unguarded, "guardZones": zones,
        "spawners": spawners, "deaths": deaths, "fights": fights, "botFiles": files,
    }, open(out, "w", encoding="utf-8"), indent=1)
    print("wrote", out, len(spawners), "spawners,", sum(d["n"] for d in deaths), "deaths in", len(deaths), "cells")


if __name__ == "__main__":
    main(sys.argv[1:])
