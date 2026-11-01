"""Picks sites for new themed spawners in areas that have none of their own (an area's "autoNew": N), and writes them into
the area file as that area's "newSpawners". A site is a walkable tile whose 5x5 square is walkable, off roads, outside every
guard zone, at least 40 tiles from any other spawner, preferring forest (most trees within 10 tiles). Deterministic.

  python pick_sites.py CENSUS.json AREAS.json
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "world-decorating"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tests", "scenarios", "bot-farm"))
import uo_world  # noqa: E402
import walkroute  # noqa: E402
from place_wildlife import is_tree  # noqa: E402


def main(argv):
    census = json.load(open(argv[0], encoding="utf-8"))
    path = argv[1]
    design = json.load(open(path, encoding="utf-8"))
    x0, y0, x1, y1 = census["rect"]
    region = uo_world.Region(x0, y0, x1, y1)
    walk = walkroute.WalkMap()
    trees = {k for k, v in region.stat.items() if any(t < len(uo_world.tiles) and is_tree(uo_world.tiles[t]) for t, _ in v)}
    guarded = [r for z in census["guardZones"] for r in z["rects"]]
    taken = [(s["x"], s["y"]) for s in census["spawners"]]
    for a in design["areas"]:
        n = a.get("autoNew", 0)
        if not n:
            continue
        cands = []
        for ax0, ay0, ax1, ay1 in a["rects"]:
            for x in range(ax0 + 4, ax1 - 4, 4):
                for y in range(ay0 + 4, ay1 - 4, 4):
                    if not region.inside(x, y) or any(g[0] - 5 <= x < g[2] + 5 and g[1] - 5 <= y < g[3] + 5 for g in guarded):
                        continue
                    if not all(walk.walkable(x + dx, y + dy) and region.inside(x + dx, y + dy) and not uo_world.is_road(region.lid(x + dx, y + dy))
                               for dx in range(-2, 3) for dy in range(-2, 3)):
                        continue
                    score = sum((x + dx, y + dy) in trees for dx in range(-10, 11, 2) for dy in range(-10, 11, 2))
                    cands.append((-score, x, y))
        cands.sort()
        picked = []
        for _, x, y in cands:
            if len(picked) >= n:
                break
            if all(math.hypot(x - a2, y - b2) >= 40 for a2, b2 in taken + picked):
                picked.append((x, y))
        a["newSpawners"] = [{"x": x, "y": y, "z": region.lz(x, y)} for x, y in picked]
        taken += picked
        print(a["id"], a["newSpawners"])
    json.dump(design, open(path, "w", encoding="utf-8"), indent=2)


if __name__ == "__main__":
    main(sys.argv[1:])
