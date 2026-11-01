"""Spreads the monsters out (owner, 2026-10-19: "Rather than spawns with '7 max' ... have 3 spawns with 3 max and 1 with 1
max ... to give more even coverage for the spawns and make it less dangerous"; "this should only apply to step-up, dangerous
and deadly"). Every themed spawner of tier 2 or more holding more than SPLIT_MAX creatures is split into groups of at most
SPLIT_MAX (7 -> 3, 3, 1): the first group stays on the spawner's own spot, each other group gets a spot of its own nearby.
Beginner areas, wildlife and areas marked "cluster": true (the orc keep) keep their spawners whole.

A spot is a walkable tile whose 3x3 square is walkable, off roads, outside every guard zone, inside the spawner's area, no
nearer the centre than its grade allows, and at least MIN_GAP tiles from every other spawner. Each group roams half the way to
its nearest neighbour (10 to 30 tiles). Deterministic.

  python split_sites.py CENSUS.json PLAN.json AREAS.json OUT.json
Then run plan.py again with --splits OUT.json.
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

SPLIT_MAX = 3
STEP = 4          # candidate grid
MIN_GAP = 16      # never closer than this to another spawner
HOME_MIN, HOME_MAX = 10, 30


def parts_of(count):
    return [SPLIT_MAX] * (count // SPLIT_MAX) + ([count % SPLIT_MAX] if count % SPLIT_MAX else [])


def main(argv):
    census = json.load(open(argv[0], encoding="utf-8"))
    plan = json.load(open(argv[1], encoding="utf-8"))
    design = json.load(open(argv[2], encoding="utf-8"))
    out_path = argv[3]
    areas = {a["id"]: a for a in design["areas"]}
    rings = design.get("rings") or json.load(open(os.path.join(HERE, design["themesFrom"]), encoding="utf-8"))["rings"]
    cx, cy = census["townCentre"]

    def ring_allows(x, y, tier):  # the same ring rule plan.py checks: a group may not sit nearer than its grade allows
        d = math.hypot(x - cx, y - cy)
        return tier <= max((r for r in rings if d >= r["from"]), key=lambda r: r["maxTier"])["maxTier"]
    x0, y0, x1, y1 = census["rect"]
    region = uo_world.Region(x0, y0, x1, y1)
    walk = walkroute.WalkMap()
    guarded = [r for z in census["guardZones"] for r in z["rects"]]
    stock = {s["id"]: s for s in census["spawners"]}
    taken = [(s["x"], s["y"]) for s in census["spawners"]] + [(n["x"], n["y"]) for n in plan.get("added", []) if not n.get("splitFrom")]

    def ok(x, y):
        if not region.inside(x, y) or any(g[0] - 5 <= x < g[2] + 5 and g[1] - 5 <= y < g[3] + 5 for g in guarded):
            return False
        return all(region.inside(x + dx, y + dy) and walk.walkable(x + dx, y + dy) and not uo_world.is_road(region.lid(x + dx, y + dy))
                   for dx in range(-1, 2) for dy in range(-1, 2))

    # the spawners to split, by area
    jobs = {}
    for ch in plan["changes"]:
        if ch.get("wild") or not ch.get("area") or ch.get("splitFrom"):
            continue
        a = areas[ch["area"]]
        if ch["to"] < 2 or a.get("cluster"):
            continue
        if ch.get("added"):
            sx, sy = ch["x"], ch["y"]
            count = sum(e["maxCount"] for e in ch["entries"])
        else:
            s = stock[ch["id"]]
            sx, sy, count = s["x"], s["y"], s["count"]
        if len(parts_of(count)) > 1:
            jobs.setdefault(a["id"], []).append((ch, sx, sy, count))

    splits, short, spots_all = {}, [], []
    for aid, todo in jobs.items():
        a = areas[aid]
        tier = todo[0][0]["to"]
        # every spot the area could use, then farthest-point picks: each new group goes where the area is emptiest
        cands = []
        for ax0, ay0, ax1, ay1 in a["rects"]:
            for x in range(ax0 + 2, ax1 - 1, STEP):
                for y in range(ay0 + 2, ay1 - 1, STEP):
                    if (a.get("ringException") or ring_allows(x, y, tier)) and ok(x, y):
                        cands.append((x, y))
        gap = {(x, y): min(math.hypot(x - a2, y - b2) for a2, b2 in taken) for x, y in cands}
        for ch, sx, sy, count in todo:
            parts = parts_of(count)
            spots = []
            for _ in parts[1:]:
                best = max(gap, key=lambda k: (gap[k], -k[0], -k[1]), default=None)
                if best is None or gap[best] < MIN_GAP // 2:  # a cramped area (a narrow ridge) takes a closer spot rather than a bigger group
                    break
                bx, by = best
                spots.append({"x": bx, "y": by, "z": region.lz(bx, by)})
                taken.append(best)
                for k in gap:
                    gap[k] = min(gap[k], math.hypot(k[0] - bx, k[1] - by))
            groups = [{"x": sx, "y": sy, "count": parts[0]}] + [dict(p, count=c) for p, c in zip(spots, parts[1:])]
            left = sum(parts[1 + len(spots):])
            if left:  # no room: the spawner keeps the rest, and the report says so
                groups[0]["count"] += left
                short.append((ch["id"], aid, left))
            splits[ch["guid"]] = {"area": aid, "groups": groups}
            spots_all += groups
            print("%s %-24s %2d -> %s" % (ch["id"], aid, count, [g["count"] for g in groups]))
    # each group roams half way to its nearest neighbouring spawner, 10 to 30 tiles
    for sp in splits.values():
        for g in sp["groups"]:
            near = min((math.hypot(g["x"] - a2, g["y"] - b2) for a2, b2 in taken if (a2, b2) != (g["x"], g["y"])), default=60)
            g["home"] = int(max(HOME_MIN, min(HOME_MAX, near // 2)))
    json.dump(splits, open(out_path, "w", encoding="utf-8"), indent=1)
    print("%d spawners split into %d groups; %d without room for every group %s" %
          (len(splits), sum(len(v["groups"]) for v in splits.values()), len(short), short))


if __name__ == "__main__":
    main(sys.argv[1:])
