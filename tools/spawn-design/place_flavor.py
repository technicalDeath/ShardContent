"""Scatters single flavor objects through the greater-Britain spawn areas (owner, 2026-10-18: "individual object
placement. small items like mushrooms, a nest, spilled hay, things that on their own help give flavor to the different
areas, don't require other items to be around, and not trying to compose a scene").

Each area takes the standalone pieces of its theme (deco.json "flavor" "pieces"), about one per 900 tiles of its area (6 to
40), each on its own tile, at least 14 tiles from the next; then, on new sites at least 10 tiles from every piece, as many
again from its "color" list (wildflowers, red-capped mushrooms; owner, 2026-10-18: "more color"). A tile qualifies only when it is clean open ground:
  * walkable (walkgrid.bin), not road or path, the same height as its neighbours (no slope or ledge);
  * no map static on it or within one tile, and nothing tall (a tree, its leaves, a big rock) within 3 tiles, so the piece
    is never drawn behind a trunk;
  * 6 tiles clear of anything already built or decorated (builtmask.py), outside the guard zones;
  * not on a spawner's own tile, and the area does not opt out ("deco": false, the Britain Graveyard).
Piece and order are drawn from a fixed seed per area, so the same data comes out every run.

  python place_flavor.py CENSUS.json PLAN.json OUT-SITES.json
writes OUT-SITES.json and data/map-patches/greater-britain-flavor-statics.json (map statics, not server items)
"""
import json
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "world-decorating"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tests", "scenarios", "bot-farm"))
import uo_world  # noqa: E402
import walkroute  # noqa: E402
import builtmask  # noqa: E402

PATCHES = os.path.normpath(os.path.join(HERE, "..", "..", "data", "map-patches"))
SPACING = 14
COLOR_SPACING = 10
TILES = uo_world.tiles
PER_TILES = 900


def main(argv):
    census = json.load(open(argv[0], encoding="utf-8"))
    plan = json.load(open(argv[1], encoding="utf-8"))
    flavor = json.load(open(os.path.join(HERE, "deco.json"), encoding="utf-8"))["flavor"]
    region, built, _, path, _ = builtmask.tiles_of(census)
    walk = walkroute.WalkMap()
    guarded = [r for z in census["guardZones"] for r in z["rects"]]
    homes = {(s["x"], s["y"]) for s in census["spawners"]}

    def near(x, y, tiles, r):
        return any((x + dx, y + dy) in tiles for dx in range(-r, r + 1) for dy in range(-r, r + 1))

    def clean(x, y):
        if not region.inside(x, y) or not walk.walkable(x, y) or (x, y) in homes:
            return False
        z = region.lz(x, y)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                px, py = x + dx, y + dy
                if not region.inside(px, py) or region.stat.get((px, py)) or (px, py) in path:
                    return False
                if uo_world.is_road(region.lid(px, py)) or abs(region.lz(px, py) - z) > 2 or not walk.walkable(px, py):
                    return False
        # a clear sightline: nothing tall within 3 tiles, so no tree trunk or rock is drawn in front of the piece
        for dx in range(-3, 4):
            for dy in range(-3, 4):
                for tid, _ in region.stat.get((x + dx, y + dy), []):
                    if tid < len(TILES) and (TILES[tid].height >= 8 or TILES[tid].flags & uo_world.FOLI):
                        return False
        if any(a - 2 <= x < c + 2 and b - 2 <= y < d + 2 for a, b, c, d in guarded):
            return False
        return not near(x, y, built, 6)

    sites, report = [], []

    def scatter(listkey, seed, spacing, tag):
        for a in plan["areas"]:
            if a.get("deco") is False or a["theme"] not in flavor or not flavor[a["theme"]].get(listkey):
                if listkey == "pieces":
                    report.append((a["id"], 0, "opted out" if a.get("deco") is False else "no palette"))
                continue
            pieces = flavor[a["theme"]][listkey]
            rnd = random.Random(a["id"] + seed)
            cells = [(x, y) for x1, y1, x2, y2 in a["rects"] for x in range(x1, x2, 3) for y in range(y1, y2, 3)]
            rnd.shuffle(cells)
            size = sum((x2 - x1) * (y2 - y1) for x1, y1, x2, y2 in a["rects"])
            want = max(6, min(40, round(size / PER_TILES)))
            chosen = []
            for x, y in cells:
                if len(chosen) >= want:
                    break
                if any(math.hypot(x - cx, y - cy) < spacing for cx, cy in chosen + [(s["x"], s["y"]) for s in sites]):
                    continue
                if clean(x, y):
                    chosen.append((x, y))
                    name, hexid = pieces[len(chosen) % len(pieces)] if len(chosen) <= len(pieces) else rnd.choice(pieces)
                    site = {"area": a["id"], "theme": a["theme"], "name": name, "id": hexid, "x": x, "y": y, "z": region.lz(x, y)}
                    if tag:
                        site[tag] = True
                    sites.append(site)
            report.append((a["id"], len(chosen), "%s of %d wanted" % (listkey, want)))

    # the first pass is the deployed one and comes out the same every run; the colour pass only adds new sites beside it,
    # so a world that already has the first pieces gains just the new ones from adddecorations
    scatter("pieces", "", SPACING, None)
    scatter("color", ":color", COLOR_SPACING, "color")

    # the pieces go into the map's own statics (owner, 2026-10-18: they must look and behave like the map's decoration), so the output
    # is a statics patch list, applied to the client and server map files by tools/map-patch/apply_statics_patch.py
    patch = {"about": "Greater Britain flavor objects as map statics (map 0, Felucca). Generated by tools/spawn-design/place_flavor.py; "
                      "applied to statics0.mul/staidx0.mul (and the x pair) by tools/map-patch/apply_statics_patch.py. Do not edit by hand.",
             "map": 0, "statics": [[int(s["id"], 16), s["x"], s["y"], s["z"], 0] for s in sorted(sites, key=lambda s: (s["x"], s["y"]))]}
    os.makedirs(PATCHES, exist_ok=True)
    json.dump(patch, open(os.path.join(PATCHES, "greater-britain-flavor-statics.json"), "w", encoding="utf-8", newline="\n"), separators=(",", ":"))
    json.dump(sites, open(argv[2], "w", encoding="utf-8"), indent=1)
    print("pieces", len(sites))
    for r in report:
        print("  %-18s %3d %s" % r)


if __name__ == "__main__":
    main(sys.argv[1:])
