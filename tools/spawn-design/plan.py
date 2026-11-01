"""Applies the spawn areas (areas.json) to a census (census.py): every creature spawner inside an area takes that area's
theme, keeping its place, count, ranges and delays. Writes the plan for the map page and a draft shard spawn file whose
records reuse the stock GUIDs, so world generation replaces the stock spawners (Prepare-Alpha2bWorldData.ps1: the last
record per GUID wins) and `[Alpha2bWorldGen addspawners` swaps the stale ones in a world in use.

  python plan.py CENSUS.json WILDLIFE-SITES.json PLAN.json DRAFT-SPAWNS.json [--areas AREAS.json]
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
NEW_NS = uuid.UUID("0f6c2a4e-8d5b-4c3e-9b1a-7e2d4f6a8c10")  # area ids are unique across plans, so new GUIDs never collide


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
    areas_path = os.path.join(HERE, "areas.json")
    if "--areas" in argv:  # another plan's areas (Vesper-Minoc); it borrows the shared themes and wildlife from areas.json
        i = argv.index("--areas")
        areas_path = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
    splits = {}
    if "--splits" in argv:  # split_sites.py's groups: big step-up and harder spawners spread into groups of at most 3
        i = argv.index("--splits")
        splits = json.load(open(argv[i + 1], encoding="utf-8"))
        argv = argv[:i] + argv[i + 2:]
    design = json.load(open(areas_path, encoding="utf-8"))
    if design.get("themesFrom"):
        base = json.load(open(os.path.join(HERE, design["themesFrom"]), encoding="utf-8"))
        design["themes"] = {**base["themes"], **design.get("themes", {})}
        design.setdefault("wildlife", base["wildlife"])
        design.setdefault("newSpawnerDefaults", base.get("newSpawnerDefaults", {}))
        design.setdefault("rings", base["rings"])
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

    edges = design.get("ringEdges", [300, 400, 500])  # where the Doorstep, Near wilds and Far wilds end (circles on the page)

    def ring_tier(d):
        return 1 if d < edges[0] else 2 if d < edges[1] else 3

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
        if any(x1 <= s["x"] < x2 and y1 <= s["y"] < y2 for x1, y1, x2, y2 in design.get("britainWins", [])):
            continue  # another plan (Greater Britain) already covers it, and that plan wins
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
        sp = splits.get(s["guid"])
        count = sp["groups"][0]["count"] if sp else s["count"]
        new = entries_for(t["roster"], count)
        home = a.get("homeRange", s["home"])  # an area can keep its creatures closer (the orc fort's gate and keep)
        if sp:
            home = sp["groups"][0]["home"]
        same = sorted(e["name"] for e in s["entries"]) == sorted(e["name"] for e in new) and home == s["home"] and count == s["count"]
        changes.append({"id": s["id"], "guid": s["guid"], "area": a["id"], "from": s["tier"], "to": t["tier"],
                        "changed": not same, "entries": new, "home": home, "count": count})
        if not same:
            draft.append({"$type": "Spawner", "guid": s["guid"], "name": "%s: %s" % (a["name"], t["label"]),
                          "location": [s["x"], s["y"], s["z"]], "map": "Felucca", "count": count,
                          "minDelay": s["delay"][0], "maxDelay": s["delay"][1], "team": 0,
                          "homeRange": home, "walkingRange": home if sp else a.get("homeRange", s["walk"]), "entries": new})
    # new themed spawners an area asks for (where it has none of its own)
    added = []
    nd = design.get("newSpawnerDefaults", {})
    for a in design["areas"]:
        for site in a.get("newSpawners", []):
            t = themes[a["theme"]]
            guid = str(uuid.uuid5(NEW_NS, "%s %d,%d" % (a["id"], site["x"], site["y"])))
            count, home = site.get("count", nd["count"]), a.get("homeRange", nd["homeRange"])
            sp = splits.get(guid)
            if sp:
                count, home = sp["groups"][0]["count"], sp["groups"][0]["home"]
            new = entries_for(t["roster"], count)
            a["spawners"].append(guid[:8])
            added.append({"id": guid[:8], "x": site["x"], "y": site["y"], "count": count, "home": home,
                          "area": a["id"], "to": t["tier"], "entries": new})
            changes.append({"id": guid[:8], "guid": guid, "area": a["id"], "from": None, "to": t["tier"], "changed": True, "entries": new, "added": True,
                            "x": site["x"], "y": site["y"]})
            draft.append({"$type": "Spawner", "guid": guid, "name": "%s: %s" % (a["name"], t["label"]),
                          "location": [site["x"], site["y"], site["z"]], "map": "Felucca", "count": count,
                          "minDelay": nd["minDelay"], "maxDelay": nd["maxDelay"], "team": 0,
                          "homeRange": home, "walkingRange": a.get("homeRange", nd["walkingRange"]), "entries": new})
    # the other groups of each split spawner, on spots of their own (split_sites.py)
    by_guid = {s["guid"]: s for s in c["spawners"]}
    for a in design["areas"]:
        t = themes[a["theme"]]
        for ch in [x for x in changes if x.get("area") == a["id"] and x["guid"] in splits]:
            sp = splits[ch["guid"]]
            src = by_guid.get(ch["guid"])
            delay = src["delay"] if src else [nd["minDelay"], nd["maxDelay"]]
            for i, g in enumerate(sp["groups"][1:], 1):
                guid = str(uuid.uuid5(NEW_NS, "split %s %d" % (ch["guid"], i)))
                new = entries_for(t["roster"], g["count"])
                a["spawners"].append(guid[:8])
                added.append({"id": guid[:8], "x": g["x"], "y": g["y"], "count": g["count"], "home": g["home"],
                              "area": a["id"], "to": t["tier"], "entries": new, "splitFrom": ch["id"]})
                changes.append({"id": guid[:8], "guid": guid, "area": a["id"], "from": None, "to": t["tier"], "changed": True, "entries": new,
                                "added": True, "x": g["x"], "y": g["y"], "splitFrom": ch["id"]})
                draft.append({"$type": "Spawner", "guid": guid, "name": "%s: %s" % (a["name"], t["label"]),
                              "location": [g["x"], g["y"], g["z"]], "map": "Felucca", "count": g["count"],
                              "minDelay": delay[0], "maxDelay": delay[1], "team": 0,
                              "homeRange": g["home"], "walkingRange": g["home"], "entries": new})
    ns = wl["newSite"]
    for site in sites:
        if any(x1 <= site["x"] < x2 and y1 <= site["y"] < y2 for x1, y1, x2, y2 in design.get("britainWins", [])):
            continue  # a new forest site inside another plan (Greater Britain), which wins there
        t, a = wildlife_tier(site["x"], site["y"])
        new = entries_for(wl["byTier"][str(t)], ns["count"])
        wildlife.append({"id": site["guid"][:8], "x": site["x"], "y": site["y"], "count": ns["count"], "home": ns["homeRange"], "tier": t,
                         "new": True, "inArea": a and a["id"], "trees": site["trees"], "entries": new})
        draft.append({"$type": "Spawner", "guid": site["guid"], "name": "Wildlife (%s), new forest site" % census.TIER_NAMES[t],
                      "location": [site["x"], site["y"], site["z"]], "map": "Felucca", "count": ns["count"],
                      "minDelay": ns["minDelay"], "maxDelay": ns["maxDelay"], "team": 0,
                      "homeRange": ns["homeRange"], "walkingRange": ns["walkingRange"], "entries": new})
    # wild horses, one in each of the eight directions (pick_extras.py): a horse joins that wildlife spawner, or a new site holds one
    by_draft = {d["guid"][:8]: d for d in draft}
    for h in design.get("wildHorses", []):
        if h.get("wildlife"):
            w = next(w for w in wildlife if w["id"] == h["wildlife"])
            horse = {"name": "Horse", "maxCount": 1, "probability": 100}
            for rec in (w["entries"], by_draft[w["id"]]["entries"]):
                if not any(e["name"] == "Horse" for e in rec):
                    rec.append(dict(horse))
            w["count"] += 1
            w["horse"] = h["direction"]
            by_draft[w["id"]]["count"] = w["count"]
        elif h.get("x") is not None:
            guid = str(uuid.uuid5(NEW_NS, "wild horse %s %d,%d" % (h["direction"], h["x"], h["y"])))
            t, a = wildlife_tier(h["x"], h["y"])
            new = entries_for(wl["byTier"][str(t)], ns["count"]) + [{"name": "Horse", "maxCount": 1, "probability": 100}]
            wildlife.append({"id": guid[:8], "x": h["x"], "y": h["y"], "count": ns["count"] + 1, "home": ns["homeRange"], "tier": t,
                             "new": True, "inArea": a and a["id"], "trees": 0, "entries": new, "horse": h["direction"]})
            draft.append({"$type": "Spawner", "guid": guid, "name": "Wildlife (%s), wild horses to the %s" % (census.TIER_NAMES[t], h["direction"]),
                          "location": [h["x"], h["y"], h["z"]], "map": "Felucca", "count": ns["count"] + 1,
                          "minDelay": ns["minDelay"], "maxDelay": ns["maxDelay"], "team": 0,
                          "homeRange": ns["homeRange"], "walkingRange": ns["walkingRange"], "entries": new})
    # an area's own horses (owner, 2026-10-20: "Put a couple in the castle woods"): its first N spawners each gain one
    for a in design["areas"]:
        n = a.get("horses", 0)
        for ch in sorted((x for x in changes if x.get("area") == a["id"] and not x.get("splitFrom")), key=lambda x: x["id"])[:n]:
            rec = by_draft.get(ch["id"])
            for lst in [ch["entries"]] + ([rec["entries"]] if rec and rec["entries"] is not ch["entries"] else []):
                if not any(e["name"] == "Horse" for e in lst):
                    lst.append({"name": "Horse", "maxCount": 1, "probability": 100})
            if rec is None:  # an unchanged stock spawner becomes a changed one
                s0 = next(x for x in c["spawners"] if x["id"] == ch["id"])
                rec = {"$type": "Spawner", "guid": s0["guid"], "name": "%s: %s" % (a["name"], themes[a["theme"]]["label"]),
                       "location": [s0["x"], s0["y"], s0["z"]], "map": "Felucca", "count": s0["count"], "minDelay": s0["delay"][0],
                       "maxDelay": s0["delay"][1], "team": 0, "homeRange": s0["home"], "walkingRange": s0["walk"], "entries": ch["entries"]}
                draft.append(rec)
                by_draft[ch["id"]] = rec
            ch["changed"] = True
            rec["count"] += 1
            ch["count"] = rec["count"]
    # wandering healers, one per area where there is room, 60+ tiles apart (pick_extras.py)
    hl = design.get("healers", {})
    for site in hl.get("sites", []):
        guid = str(uuid.uuid5(NEW_NS, "healer %s %d,%d" % (site["area"], site["x"], site["y"])))
        new = [{"name": "WanderingHealer", "maxCount": 1, "probability": 100}]
        added.append({"id": guid[:8], "x": site["x"], "y": site["y"], "count": 1, "home": hl["home"], "area": site["area"], "to": 0,
                      "entries": new, "healer": True})
        changes.append({"id": guid[:8], "guid": guid, "area": None, "healer": True, "from": None, "to": 0, "changed": True, "entries": new,
                        "added": True, "x": site["x"], "y": site["y"]})
        draft.append({"$type": "Spawner", "guid": guid, "name": "Wandering healer",
                      "location": [site["x"], site["y"], site["z"]], "map": "Felucca", "count": 1,
                      "minDelay": "00:05:00", "maxDelay": "00:10:00", "team": 0,
                      "homeRange": hl["home"], "walkingRange": hl["home"], "entries": new})
    for a in design["areas"]:
        ds = [math.hypot(s["x"] - tx, s["y"] - ty) for s in c["spawners"] + added if s["id"] in a["spawners"]]
        a["dist"] = [round(min(ds)), round(max(ds))] if ds else None
        if ds:
            ring = max((r for r in design["rings"] if min(ds) >= r["from"]), key=lambda r: r["maxTier"])
            if a["tier"] > ring["maxTier"] and not a.get("ringException"):
                problems.append({"area": a["id"], "why": "tier %d nearer than the %s ring allows" % (a["tier"], ring["name"])})
    json.dump({"rings": design["rings"], "ringEdges": edges, "themes": themes, "wildlife": wildlife, "wildKinds": wl_kinds, "added": added, "areas": design["areas"], "changes": changes, "problems": problems},
              open(argv[1], "w", encoding="utf-8"), indent=1)
    json.dump(draft, open(argv[2], "w", encoding="utf-8"), indent=2)
    print("wildlife", len(wildlife), "of which new", sum(w["new"] for w in wildlife), "by tier", [sum(w["tier"] == t for w in wildlife) for t in range(4)])
    print("areas", len(design["areas"]), "spawners themed", len(changes), "changed", len(draft), "problems", problems)
    for a in design["areas"]:
        print(" %-18s T%d %-20s d=%s n=%d" % (a["id"], a["tier"], a["theme"], a["dist"], len(a["spawners"])))


if __name__ == "__main__":
    main(sys.argv[1:])
