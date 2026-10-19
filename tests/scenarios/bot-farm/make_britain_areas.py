"""Generate britain_areas.json: the themed hunting areas around Britain (the Spawn Designer's 2026-10-18 redo), what lives in each and how dangerous it is,
for the bots' patrol seeds (places.SEED_SPOTS["Britain"]). Read-only on inputs; deterministic. What a new player in Britain hears in town: deer in the
castle woods, wolves in the north fields, ratmen in the west foothills, and that danger rises the further out you go.

    python make_britain_areas.py            # writes britain_areas.json next to this file
    python make_britain_areas.py --check    # exit 1 if it differs from what the inputs produce

Inputs: ShardContent/tools/spawn-design/areas.json (area rectangles and themes), the canonical spawners of the Alpha2b Spawns folder (spawners.py: what the
server spawns; Felucca surface), creature_stats.json and fightmodes.json, and the tier rule of tools/spawn-design/census.py (0 harmless .. 4 deadly).
One entry per area: id, name, theme, tier (its worst creature), ring distance from the bank (1470,1620), its spawners [x, y, reach, [kinds]] and a
spot: the spawner nearest the middle of the area (spawners stand on walkable ground, so a bot can walk to it).
"""
import argparse
import json
import math
import os
import re
import sys

import spawners

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
DESIGN = os.path.join(ROOT, "ShardContent", "tools", "spawn-design")
SPAWNS = os.path.join(ROOT, "ModernUO", "Distribution", "Data", "BritanniaRenaissance", "Alpha2b", "Spawns")
OUT = os.path.join(HERE, "britain_areas.json")
BANK = (1470, 1620)

sys.path.insert(0, DESIGN)
from census import tier_of  # noqa: E402


def build():
    stats = json.load(open(os.path.join(HERE, "creature_stats.json"), encoding="utf-8"))
    modes = json.load(open(os.path.join(HERE, "fightmodes.json"), encoding="utf-8"))
    design = json.load(open(os.path.join(DESIGN, "areas.json"), encoding="utf-8"))
    areas = []
    for a in design["areas"]:
        areas.append({"id": a["id"], "name": a["name"], "theme": a["theme"], "label": design["themes"].get(a["theme"], {}).get("label", a["theme"]),
                      "rects": a["rects"], "tier": 0, "spawners": {}})

    def area_at(x, y):
        for a in areas:
            if any(x0 <= x <= x1 and y0 <= y <= y1 for x0, y0, x1, y1 in a["rects"]):
                return a
        return None

    for _f, s in spawners.canonical(SPAWNS):            # each spawner once, as the server makes it (a re-themed one by its last definition)
        loc = s.get("location")
        if not loc or s.get("map") != "Felucca" or loc[0] >= 5120:
            continue
        a = area_at(loc[0], loc[1])
        if a is None:
            continue
        kinds = sorted({re.sub(r"[^a-z]", "", str(e.get("name", "")).lower()) for e in s.get("entries", [])} & set(stats))
        if not kinds:
            continue                                      # a vendor, a camp, a crop
        sp = a["spawners"].setdefault((loc[0], loc[1]), [loc[0], loc[1], 0, set()])
        sp[2] = max(sp[2], int(s.get("homeRange") or 0), int(s.get("walkingRange") or 0))
        sp[3] |= set(kinds)
    out = []
    for a in areas:
        sps = [[x, y, r, sorted(k)] for (x, y), (_, _, r, k) in sorted(a["spawners"].items())]
        if not sps:
            continue
        tiers = [tier_of(k, stats, modes) for sp in sps for k in sp[3]]
        mx = (sum((r[0] + r[2]) / 2 * (r[2] - r[0]) * (r[3] - r[1]) for r in a["rects"]) / sum((r[2] - r[0]) * (r[3] - r[1]) for r in a["rects"]))
        my = (sum((r[1] + r[3]) / 2 * (r[2] - r[0]) * (r[3] - r[1]) for r in a["rects"]) / sum((r[2] - r[0]) * (r[3] - r[1]) for r in a["rects"]))
        spot = min(sps, key=lambda sp: (max(abs(sp[0] - mx), abs(sp[1] - my)), sp[0], sp[1]))
        out.append({"id": a["id"], "name": a["name"], "theme": a["theme"], "label": a["label"], "tier": max([t for t in tiers if t is not None] or [0]),
                    "ring": round(math.dist((spot[0], spot[1]), BANK)), "spot": spot[:2], "rects": a["rects"], "spawners": sps})
    out.sort(key=lambda a: (a["tier"], a["ring"], a["id"]))
    return {"schema": 1, "bank": list(BANK), "areas": out}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    text = json.dumps(build(), indent=1, sort_keys=True) + "\n"
    if a.check:
        cur = open(OUT, encoding="utf-8").read() if os.path.exists(OUT) else ""
        if cur != text:
            print("britain_areas.json differs from the inputs")
            sys.exit(1)
        print("britain_areas.json is current")
        return
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    d = json.loads(text)
    for ar in d["areas"]:
        print(f"  tier {ar['tier']}  {ar['ring']:4} tiles  {ar['name']:24} spot {ar['spot']}  {len(ar['spawners'])} spawners  {ar['label']}")


if __name__ == "__main__":
    main()
