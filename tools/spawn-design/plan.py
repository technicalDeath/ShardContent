"""Applies the spawn areas (areas.json) to a census (census.py): every creature spawner inside an area takes that area's
theme, keeping its place, count, ranges and delays. Writes the plan for the map page and a draft shard spawn file whose
records reuse the stock GUIDs, so world generation replaces the stock spawners (Prepare-Alpha2bWorldData.ps1: the last
record per GUID wins) and `[Alpha2bWorldGen addspawners` swaps the stale ones in a world in use.

  python plan.py CENSUS.json WILDLIFE-SITES.json PLAN.json DRAFT-SPAWNS.json
"""
import json
import math
import os
import sys
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import census  # noqa: E402

LEAVE_ALONE = {"SeaLife.json", "TownsLife.json"}  # the sea, and the farms' cats, dogs and chickens
WILDLIFE = "WildLife.json"
NEW_NS = uuid.UUID("0f6c2a4e-8d5b-4c3e-9b1a-7e2d4f6a8c10")


def area_of(x, y, areas):
    for a in areas:
        if any(x1 <= x < x2 and y1 <= y < y2 for x1, y1, x2, y2 in a["rects"]):
            return a
    return None


def entries_for(roster, count):
    total = sum(w for _, w in roster)
    out = [[n, max(1, round(count * w / total))] for n, w in roster]
    while sum(m for _, m in out) < count:
        out[0][1] += 1
    return [{"name": n, "maxCount": m, "probability": 100} for n, m in out]


def main(argv):
    c = json.load(open(argv[0], encoding="utf-8"))
    sites = json.load(open(argv[1], encoding="utf-8"))
    argv = [argv[0]] + argv[2:]
    design = json.load(open(os.path.join(HERE, "areas.json"), encoding="utf-8"))
    stats = json.load(open(os.path.join(census.BOTS, "creature_stats.json")))
    modes = json.load(open(os.path.join(census.BOTS, "fightmodes.json")))
    themes = design["themes"]
    for key, t in themes.items():
        t["kinds"] = []
        for n, _ in t["roster"]:
            s = stats.get(n.lower())
            t["kinds"].append({"name": n, "tier": census.tier_of(n, stats, modes) if s else 0,
                               "hits": s and [int(v) for v in s["hits"]], "dmg": s and [int(v) for v in s["damage"]],
                               "casts": bool(s and s["casts"]), "passive": modes.get(n.lower(), {}).get("mode") == "Aggressor" or not s})
        t["tier"] = max(k["tier"] for k in t["kinds"])
    def kinds_of(roster):
        out = []
        for n, _ in roster:
            s = stats.get(n.lower())
            out.append({"name": n, "tier": census.tier_of(n, stats, modes) if s else 0,
                        "hits": s and [int(v) for v in s["hits"]], "dmg": s and [int(v) for v in s["damage"]],
                        "casts": bool(s and s["casts"]), "passive": modes.get(n.lower(), {}).get("mode") == "Aggressor" or not s})
        return out
    wl = design["wildlife"]
    wl_kinds = {int(t): kinds_of(r) for t, r in wl["byTier"].items()}
    tx, ty = c["townCentre"]

    def ring_tier(d):
        return 1 if d < 300 else 2 if d < 400 else 3

    def wildlife_tier(x, y):
        a = area_of(x, y, design["areas"])
        t = ring_tier(math.hypot(x - tx, y - ty))
        return min(t, themes[a["theme"]]["tier"]) if a else t, a

    wildlife = []
    changes, draft, problems = [], [], []
    for a in design["areas"]:
        a["spawners"] = []
        a["tier"] = themes[a["theme"]]["tier"]
        a.setdefault("ringException", None)
    for s in c["spawners"]:
        if s["kind"] != "creature" or s["guarded"] or s["file"] in LEAVE_ALONE:
            continue
        if s["file"] == WILDLIFE:
            t, a = wildlife_tier(s["x"], s["y"])
            new = entries_for(wl["byTier"][str(t)], s["count"])
            changes.append({"id": s["id"], "guid": s["guid"], "area": None, "wild": True, "from": s["tier"], "to": t, "changed": True, "entries": new})
            wildlife.append({"id": s["id"], "x": s["x"], "y": s["y"], "count": s["count"], "home": s["home"], "tier": t, "new": False,
                             "inArea": a and a["id"], "entries": new})
            draft.append({"$type": "Spawner", "guid": s["guid"], "name": "Wildlife (%s)" % census.TIER_NAMES[t],
                          "location": [s["x"], s["y"], s["z"]], "map": "Felucca", "count": s["count"],
                          "minDelay": s["delay"][0], "maxDelay": s["delay"][1], "team": 0,
                          "homeRange": s["home"], "walkingRange": s["walk"], "entries": new})
            continue
        a = area_of(s["x"], s["y"], design["areas"])
        if not a:
            problems.append({"id": s["id"], "x": s["x"], "y": s["y"], "why": "in no area"})
            continue
        a["spawners"].append(s["id"])
        t = themes[a["theme"]]
        new = entries_for(t["roster"], s["count"])
        same = sorted(e["name"] for e in s["entries"]) == sorted(e["name"] for e in new)
        changes.append({"id": s["id"], "guid": s["guid"], "area": a["id"], "from": s["tier"], "to": t["tier"],
                        "changed": not same, "entries": new})
        if not same:
            draft.append({"$type": "Spawner", "guid": s["guid"], "name": "%s: %s" % (a["name"], t["label"]),
                          "location": [s["x"], s["y"], s["z"]], "map": "Felucca", "count": s["count"],
                          "minDelay": s["delay"][0], "maxDelay": s["delay"][1], "team": 0,
                          "homeRange": s["home"], "walkingRange": s["walk"], "entries": new})
    # new themed spawners an area asks for (where it has none of its own)
    added = []
    nd = design.get("newSpawnerDefaults", {})
    for a in design["areas"]:
        for site in a.get("newSpawners", []):
            t = themes[a["theme"]]
            guid = str(uuid.uuid5(NEW_NS, "%s %d,%d" % (a["id"], site["x"], site["y"])))
            new = entries_for(t["roster"], nd["count"])
            a["spawners"].append(guid[:8])
            added.append({"id": guid[:8], "x": site["x"], "y": site["y"], "count": nd["count"], "home": nd["homeRange"],
                          "area": a["id"], "to": t["tier"], "entries": new})
            changes.append({"id": guid[:8], "guid": guid, "area": a["id"], "from": None, "to": t["tier"], "changed": True, "entries": new, "added": True,
                            "x": site["x"], "y": site["y"]})
            draft.append({"$type": "Spawner", "guid": guid, "name": "%s: %s" % (a["name"], t["label"]),
                          "location": [site["x"], site["y"], site["z"]], "map": "Felucca", "count": nd["count"],
                          "minDelay": nd["minDelay"], "maxDelay": nd["maxDelay"], "team": 0,
                          "homeRange": nd["homeRange"], "walkingRange": nd["walkingRange"], "entries": new})
    ns = wl["newSite"]
    for site in sites:
        t, a = wildlife_tier(site["x"], site["y"])
        new = entries_for(wl["byTier"][str(t)], ns["count"])
        wildlife.append({"id": site["guid"][:8], "x": site["x"], "y": site["y"], "count": ns["count"], "home": ns["homeRange"], "tier": t,
                         "new": True, "inArea": a and a["id"], "trees": site["trees"], "entries": new})
        draft.append({"$type": "Spawner", "guid": site["guid"], "name": "Wildlife (%s), new forest site" % census.TIER_NAMES[t],
                      "location": [site["x"], site["y"], site["z"]], "map": "Felucca", "count": ns["count"],
                      "minDelay": ns["minDelay"], "maxDelay": ns["maxDelay"], "team": 0,
                      "homeRange": ns["homeRange"], "walkingRange": ns["walkingRange"], "entries": new})
    for a in design["areas"]:
        ds = [math.hypot(s["x"] - tx, s["y"] - ty) for s in c["spawners"] + added if s["id"] in a["spawners"]]
        a["dist"] = [round(min(ds)), round(max(ds))] if ds else None
        if ds:
            ring = max((r for r in design["rings"] if min(ds) >= r["from"]), key=lambda r: r["maxTier"])
            if a["tier"] > ring["maxTier"] and not a.get("ringException"):
                problems.append({"area": a["id"], "why": "tier %d nearer than the %s ring allows" % (a["tier"], ring["name"])})
    json.dump({"rings": design["rings"], "themes": themes, "wildlife": wildlife, "wildKinds": wl_kinds, "added": added, "areas": design["areas"], "changes": changes, "problems": problems},
              open(argv[1], "w", encoding="utf-8"), indent=1)
    json.dump(draft, open(argv[2], "w", encoding="utf-8"), indent=2)
    print("wildlife", len(wildlife), "of which new", sum(w["new"] for w in wildlife), "by tier", [sum(w["tier"] == t for w in wildlife) for t in range(4)])
    print("areas", len(design["areas"]), "spawners themed", len(changes), "changed", len(draft), "problems", problems)
    for a in design["areas"]:
        print(" %-18s T%d %-20s d=%s n=%d" % (a["id"], a["tier"], a["theme"], a["dist"], len(a["spawners"])))


if __name__ == "__main__":
    main(sys.argv[1:])
