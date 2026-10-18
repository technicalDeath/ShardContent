"""Lists Felucca spawners whose home square reaches into a guard zone and that spawn creatures which attack on sight.

The owner's rule (2026-10-16): monsters should not spawn inside a guard zone, and a zone is shrunk only where no vendor stands.
A guard zone is every GuardedRegion or TownRegion rectangle in Data/regions.json, minus the shard's townGuards.unguardedAreas
(shard-rules.json). "Attacks on sight" is the creature's FightMode as its constructor sets it (Closest by default, or Strongest/Weakest),
read from the UOContent source.

  python audit_guard_zones.py            spawners whose spawn LOCATION is inside a zone (they spawn monsters into town)
  python audit_guard_zones.py --reach    also spawners outside a zone whose home range reaches into one (edge spawns)
"""
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
DIST = os.path.join(WS, "ModernUO", "Distribution", "Data")
REACH = "--reach" in sys.argv

rules = json.load(open(os.path.join(WS, "ShardContent", "data", "configuration", "shard-rules.json"), encoding="utf-8"))
holes = [(r["x1"], r["y1"], r["x2"], r["y2"]) for a in rules.get("townGuards", {}).get("unguardedAreas", []) for r in a["rectangles"]]

zones = []
for r in json.load(open(os.path.join(DIST, "regions.json"), encoding="utf-8")):
    if r.get("$type") in ("GuardedRegion", "TownRegion") and r.get("Map") == "Felucca":
        name = r.get("Name") or "(part of %s)" % (r.get("Parent") or {}).get("Name")
        zones += [(name, a["x1"], a["y1"], a["x2"], a["y2"]) for a in r["Area"]]


def guarded(x, y):
    if any(a <= x < c and b <= y < d for a, b, c, d in holes):
        return None
    return next((z[0] for z in zones if z[1] <= x < z[3] and z[2] <= y < z[4]), None)


mode = {}
for path in glob.glob(os.path.join(WS, "ModernUO", "Projects", "UOContent", "Mobiles", "**", "*.cs"), recursive=True):
    text = open(path, encoding="utf-8", errors="ignore").read()
    for m in re.finditer(r"public (\w+)\(\)\s*:\s*base\(AIType\.\w+(?:,\s*FightMode\.(\w+))?", text):
        mode[m.group(1).lower()] = m.group(2) or "Closest"

skip = {"Vendors.json", "TownsPeople.json"}
found = 0
for path in sorted(glob.glob(os.path.join(DIST, "BritanniaRenaissance", "Alpha2b", "Spawns", "*.json"))):
    if os.path.basename(path) in skip:
        continue
    source = os.path.join(WS, "ShardContent", "data", "world-generation", "alpha2b", os.path.basename(path))
    path = source if os.path.exists(source) else path  # the shard's own spawn files: the source, which may be ahead of the deployed copy
    for s in json.load(open(path, encoding="utf-8")):
        if s.get("map") != "Felucca":
            continue
        x, y = s["location"][:2]
        hr = s.get("homeRange") or 0
        hostile = [e["name"] for e in s.get("entries", []) if mode.get(e["name"].lower()) in ("Closest", "Strongest", "Weakest")]
        if not hostile:
            continue
        where = guarded(x, y)
        if where is None and REACH:
            hits = {guarded(i, j) for i in range(x - hr, x + hr + 1, 2) for j in range(y - hr, y + hr + 1, 2)} - {None}
            where = ("reaches " + ", ".join(sorted(hits))) if hits else None
        if where:
            found += 1
            print(f"{os.path.basename(path)} {x},{y} range {hr} in {where}: {', '.join(hostile)}")
print(f"{found} spawner(s)")
