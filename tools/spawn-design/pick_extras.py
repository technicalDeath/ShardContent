"""Wandering healers and wild horses for a plan (owner, 2026-10-20): "include wandering healer spawns in each of the greater
Britain named areas, give them decent size wandering zones of like 20 tiles. But never put any closer to each other than 60
tiles", and "include wild horses in the wildlife spawns around britain so that there is at least 8 horses (one in each cardinal
direction: north, north west, north east, etc.)". The stock wildlife mix already held both; the re-themed rosters had dropped them.

Healers: one spot per area, a walkable tile (3x3 walkable, outside every guard zone, at least 8 tiles from any spawner), chosen
area by area (smallest first) as far as possible from the healers already chosen, nearest the area's middle among equals, and
only if it is at least HEALER_GAP from every other healer: an area with no such spot gets none, and the report says so.
Horses: in each of the eight directions from the centre, the wildlife spawner at the middle distance of that direction gets a
horse; a direction with no wildlife spawner gets a new wildlife site 200-350 tiles out.

  python pick_extras.py CENSUS.json PLAN.json AREAS.json        (writes "healers" and "wildHorses" into AREAS.json)
Run after plan.py without --splits, before split_sites.py.
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

HEALER_GAP = 60
HEALER_HOME = 20
DIRS = ["east", "south-east", "south", "south-west", "west", "north-west", "north", "north-east"]


def octant(x, y, cx, cy):
    return round(math.atan2(y - cy, x - cx) / (math.pi / 4)) % 8


def main(argv):
    census = json.load(open(argv[0], encoding="utf-8"))
    plan = json.load(open(argv[1], encoding="utf-8"))
    path = argv[2]
    design = json.load(open(path, encoding="utf-8"))
    x0, y0, x1, y1 = census["rect"]
    region = uo_world.Region(x0, y0, x1, y1)
    walk = walkroute.WalkMap()
    guarded = [r for z in census["guardZones"] for r in z["rects"]]
    cx, cy = census["townCentre"]
    spawners = [(s["x"], s["y"]) for s in census["spawners"]] + [(n["x"], n["y"]) for n in plan.get("added", [])] + \
               [(w["x"], w["y"]) for w in plan["wildlife"]]

    def ok(x, y):
        if not region.inside(x, y) or any(g[0] - 5 <= x < g[2] + 5 and g[1] - 5 <= y < g[3] + 5 for g in guarded):
            return False
        return all(region.inside(x + dx, y + dy) and walk.walkable(x + dx, y + dy) for dx in range(-1, 2) for dy in range(-1, 2))

    # healers
    def size(a):
        return sum((r[2] - r[0]) * (r[3] - r[1]) for r in a["rects"])

    chosen, healers, none = [], [], []
    for a in sorted(design["areas"], key=size):
        mx = sum((r[0] + r[2]) / 2 for r in a["rects"]) / len(a["rects"])
        my = sum((r[1] + r[3]) / 2 for r in a["rects"]) / len(a["rects"])
        best = None
        for r in a["rects"]:
            for x in range(r[0] + 2, r[2] - 1, 3):
                for y in range(r[1] + 2, r[3] - 1, 3):
                    gap = min((math.hypot(x - hx, y - hy) for hx, hy in chosen), default=9999)
                    if gap < HEALER_GAP or any(math.hypot(x - sx, y - sy) < 8 for sx, sy in spawners):
                        continue
                    key = (min(gap, 400), -math.hypot(x - mx, y - my))
                    if (best is None or key > best[0]) and ok(x, y):
                        best = (key, x, y)
        if best:
            _, x, y = best
            chosen.append((x, y))
            healers.append({"area": a["id"], "x": x, "y": y, "z": region.lz(x, y)})
        else:
            none.append(a["id"])
    design["healers"] = {"home": HEALER_HOME, "sites": healers}
    print("healers: %d placed, %d areas without room %s" % (len(healers), len(none), none))

    # horses
    horses = []
    for o in range(8):
        wild = sorted((math.hypot(w["x"] - cx, w["y"] - cy), w["id"]) for w in plan["wildlife"] if octant(w["x"], w["y"], cx, cy) == o)
        if wild:
            horses.append({"direction": DIRS[o], "wildlife": wild[len(wild) // 2][1]})
            continue
        site = None
        for d in range(200, 351, 6):
            for da in (0, 6, -6, 12, -12, 18, -18):
                ang = o * math.pi / 4 + math.radians(da)
                x, y = round(cx + d * math.cos(ang)), round(cy + d * math.sin(ang))
                if ok(x, y) and all(math.hypot(x - sx, y - sy) >= 20 for sx, sy in spawners + chosen):
                    site = {"direction": DIRS[o], "x": x, "y": y, "z": region.lz(x, y)}
                    break
            if site:
                break
        horses.append(site or {"direction": DIRS[o], "none": True})
    design["wildHorses"] = horses
    for h in horses:
        print("horse", h)
    json.dump(design, open(path, "w", encoding="utf-8"), indent=2)


if __name__ == "__main__":
    main(sys.argv[1:])
