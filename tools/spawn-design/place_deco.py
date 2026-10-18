"""Picks one decoration vignette site per themed spawner (plan.py's changes with an area): the nearest tile to the
spawner's home, 7 to 20 tiles out (2 to 6 when nothing fits), clear of what is already built or decorated (builtmask.py), whose 7x7 square is all walkable (walkgrid.bin), none of it road, outside the guard
zones. Exact item tiles are laid later with the world-decorating rig; this is the design-phase site.

  python place_deco.py CENSUS.json PLAN.json OUT.json
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "world-decorating"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tests", "scenarios", "bot-farm"))
import uo_world  # noqa: E402
import builtmask  # noqa: E402
import walkroute  # noqa: E402


def main(argv):
    census = json.load(open(argv[0], encoding="utf-8"))
    plan = json.load(open(argv[1], encoding="utf-8"))
    region, built, farm, path, _ = builtmask.tiles_of(census)
    blend = set(json.load(open(os.path.join(HERE, "deco.json"), encoding="utf-8")).get("blendThemes", []))
    no_deco = {a["id"] for a in plan["areas"] if a.get("deco") is False}

    def near(x, y, tiles, r):
        return any((x + dx, y + dy) in tiles for dx in range(-r, r + 1) for dy in range(-r, r + 1))
    walk = walkroute.WalkMap()
    guarded = [r for z in census["guardZones"] for r in z["rects"]]
    by_id = {s["id"]: s for s in census["spawners"]}
    themes = {a["id"]: a["theme"] for a in plan["areas"]}

    def ok(x, y):
        for dx in range(-3, 4):
            for dy in range(-3, 4):
                px, py = x + dx, y + dy
                if not region.inside(px, py) or not walk.walkable(px, py) or uo_world.is_road(region.lid(px, py)):
                    return False
                if any(a <= px < c and b <= py < d for a, b, c, d in guarded):
                    return False
                if (px, py) in path:
                    return False
        return True

    def fits(x, y, theme, relaxed):
        """Clear of what is already built or decorated. A blending theme (farm scenery) sits beside farm buildings,
        fences and fields on purpose (its edge 3 to 11 tiles from them); every other scene keeps its edge 12 tiles clear
        (7 when relaxed). A blending theme with nothing to blend with nearby falls back to the ordinary rule."""
        if not ok(x, y):
            return False
        if theme in blend and not relaxed:
            return not near(x, y, built, 6) and near(x, y, built, 14)
        return not near(x, y, built, 10 if relaxed else 15)

    def pick(s, theme, relaxed):
        # 7 to 20 tiles out first, so a scene does not sit under its spawner's marker; nearer only when nothing fits
        for r in list(range(7, 21)) + list(range(2, 7)):
            ring = [(s["x"] + dx, s["y"] + dy) for dx in range(-r, r + 1) for dy in range(-r, r + 1) if max(abs(dx), abs(dy)) == r]
            ring.sort(key=lambda p: (math.hypot(p[0] - s["x"], p[1] - s["y"]), p))
            best = next((p for p in ring if fits(p[0], p[1], theme, relaxed)), None)
            if best:
                return best
        return None

    sites, misses = [], []
    for ch in plan["changes"]:
        if not ch.get("area") or ch["area"] in no_deco:
            continue
        s = by_id.get(ch["id"]) or {"id": ch["id"], "x": ch["x"], "y": ch["y"]}  # a new spawner the plan adds
        twin = next((v for v in sites if v["area"] == ch["area"] and math.hypot(v["x"] - s["x"], v["y"] - s["y"]) <= 16), None)
        if twin:  # stock spawners often stand in pairs on one spot: one scene serves both
            twin.setdefault("also", []).append(s["id"])
            continue
        best = None
        for relaxed in (False, True):
            best = pick(s, themes[ch["area"]], relaxed)
            if best:
                break
        if best:
            sites.append({"spawner": s["id"], "area": ch["area"], "theme": themes[ch["area"]], "x": best[0], "y": best[1], "z": region.lz(*best),
                          "blends": themes[ch["area"]] in blend and near(best[0], best[1], built, 14)})
        else:
            misses.append((s["id"], ch["area"]))
    json.dump(sites, open(argv[2], "w", encoding="utf-8"), indent=1)
    print("sites", len(sites), "no room near", misses)



if __name__ == "__main__":
    main(sys.argv[1:])
