"""Places new wildlife spawners in the forests of greater Britain where no wildlife spawner is near.

  python place_wildlife.py CENSUS.json OUT.json [--gap 70] [--max 24]

A site is a walkable tile (the bot farm's walkgrid.bin, built from the client's map, statics and tiledata) with at
least MIN_TREES tree statics within 12 tiles, outside every guard zone, at least 150 tiles from the bank, and at least
--gap tiles from any other wildlife spawner (stock WildLife.json ones and sites already chosen). Densest forest first.
Each site gets a fixed, name-based GUID, so the same run gives the same ids.
"""
import json
import math
import os
import sys
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "world-decorating"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tests", "scenarios", "bot-farm"))
import uo_world  # noqa: E402
import walkroute  # noqa: E402

MIN_TREES = 25
RADIUS = 12
STEP = 8
NS = uuid.UUID("6b1d2d1e-5d3a-4f61-9a55-3c0a8f1b7e21")


def is_tree(t):
    n = t.name.lower()
    return ("tree" in n or "leaves" in n) and "xmas" not in n and "christmas" not in n and "mosaic" not in n


def main(argv):
    census = json.load(open(argv[0], encoding="utf-8"))
    out = argv[1]
    gap = int(argv[argv.index("--gap") + 1]) if "--gap" in argv else 70
    most = int(argv[argv.index("--max") + 1]) if "--max" in argv else 24
    x0, y0, x1, y1 = census["rect"]
    cx, cy = census["townCentre"]
    region = uo_world.Region(x0, y0, x1, y1)
    walk = walkroute.WalkMap()
    tiles = uo_world.tiles
    tree = set()
    for (x, y), sts in region.stat.items():
        if any(tid < len(tiles) and is_tree(tiles[tid]) for tid, _ in sts):
            tree.add((x, y))
    guarded = [r for z in census["guardZones"] for r in z["rects"]]
    taken = [(s["x"], s["y"]) for s in census["spawners"] if s["file"] == "WildLife.json"]
    cands = []
    for x in range(x0 + RADIUS, x1 - RADIUS, STEP):
        for y in range(y0 + RADIUS, y1 - RADIUS, STEP):
            if math.hypot(x - cx, y - cy) < 150 or any(a - 10 <= x < c + 10 and b - 10 <= y < d + 10 for a, b, c, d in guarded):
                continue
            p = walk.snap(x, y, 4)
            if not p:
                continue
            n = sum(1 for dx in range(-RADIUS, RADIUS + 1) for dy in range(-RADIUS, RADIUS + 1) if (p[0] + dx, p[1] + dy) in tree)
            if n >= MIN_TREES:
                cands.append((n, p))
    cands.sort(key=lambda c: (-c[0], c[1]))
    sites = []
    for n, (x, y) in cands:
        if len(sites) >= most:
            break
        if all(math.hypot(x - a, y - b) >= gap for a, b in taken):
            taken.append((x, y))
            sites.append({"x": x, "y": y, "z": region.lz(x, y), "trees": n,
                          "guid": str(uuid.uuid5(NS, "wildlife %d,%d" % (x, y))),
                          "dist": round(math.hypot(x - cx, y - cy))})
    json.dump(sites, open(out, "w", encoding="utf-8"), indent=1)
    print("trees", len(tree), "candidates", len(cands), "sites", len(sites))
    for s in sites:
        print(" ", s["x"], s["y"], s["z"], "trees", s["trees"], "d", s["dist"])


if __name__ == "__main__":
    main(sys.argv[1:])
