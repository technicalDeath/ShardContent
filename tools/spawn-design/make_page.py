"""Builds the spawn-plan map page (one self-contained HTML file) from the radar image, the census and the plan.

  python make_page.py MAP.png CENSUS.json PLAN.json OUT.html [FLAVOR-SITES.json]
"""
import base64
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def main_colour(pix):
    """The piece's most telling colour for its map dot: its blooms, not its leaves. Leaf pixels (green above red and blue)
    are set aside when at least a few others remain, then the third that is most colourful or brightest is averaged (a poppy's
    red, a snowdrop's white); art with hardly any colour (bones, rocks) gets its plain average."""
    px = [p[:3] for row in pix for p in row if len(p) < 4 or p[3] > 0]
    if not px:
        return "#f4ead2"
    bloom = [c for c in px if not (c[1] > c[0] + 8 and c[1] > c[2] + 8)]
    if len(bloom) >= max(4, len(px) // 20):
        px = bloom

    def score(c):
        return (max(c) - min(c)) + sum(c) // 6

    px.sort(key=score, reverse=True)
    top = px[: max(1, len(px) // 3)]
    r, g, b = (sum(c[k] for c in top) // len(top) for k in range(3))
    return "#%02x%02x%02x" % (r, g, b)


def main(argv):
    png, census_path, plan_path, out = argv[:4]
    deco_sites = json.load(open(argv[4], encoding="utf-8")) if len(argv) > 4 else []   # place_flavor.py's sites
    deco = json.load(open(os.path.join(HERE, "deco.json"), encoding="utf-8"))["flavor"]
    sys.path.insert(0, os.path.join(HERE, "..", "cosmetic-catalog"))
    import tempfile
    import uoart
    art = {}
    tmp = os.path.join(tempfile.gettempdir(), "spawn-design-art.png")
    dot = {}
    for t in deco.values():
        for _, hexid in t["pieces"] + t.get("color", []):
            if hexid not in art:
                uoart.item_png(tmp, int(hexid, 16), scale=1, pad=2)
                art[hexid] = "data:image/png;base64," + base64.b64encode(open(tmp, "rb").read()).decode()
                dot[hexid] = main_colour(uoart.to_rgba(int(hexid, 16))[2])
    c = json.load(open(census_path, encoding="utf-8"))
    p = json.load(open(plan_path, encoding="utf-8"))
    changes = {ch["id"]: ch for ch in p["changes"]}
    kinds = {k["name"]: k for t in p["themes"].values() for k in t["kinds"]}
    kinds.update({k["name"]: k for lst in p["wildKinds"].values() for k in lst})
    in_area = {w["id"]: w["inArea"] for w in p["wildlife"]}

    def nx(entries):
        return [{"n": e["name"], "m": e["maxCount"], "t": kinds[e["name"]]["tier"], "h": kinds[e["name"]]["hits"],
                 "d": kinds[e["name"]]["dmg"], "c": kinds[e["name"]]["casts"], "p": kinds[e["name"]]["passive"]} for e in entries]
    spawners = []
    for s in c["spawners"]:
        if s["kind"] != "creature":
            continue
        ch = changes.get(s["id"])
        spawners.append({
            "id": s["id"], "file": s["file"], "label": s["label"], "x": s["x"], "y": s["y"], "count": s["count"],
            "home": s["home"], "delay": s["delay"], "tier": s["tier"], "dist": s["dist"], "guarded": s["guarded"],
            "entries": [{"n": e["name"], "m": e["max"], "t": e["tier"], "p": e["passive"], "h": e["hits"], "d": e["dmg"],
                         "c": e["casts"]} for e in s["entries"]],
            "area": ch and ch["area"], "to": ch and ch["to"],
            "next": ch and nx(ch["entries"]), "wild": s["file"] == "WildLife.json", "inArea": in_area.get(s["id"]),
        })
    cx, cy = c["townCentre"]
    for n in p.get("added", []):
        spawners.append({"id": n["id"], "file": "new", "label": "New spawner", "x": n["x"], "y": n["y"], "count": n["count"],
                         "home": n["home"], "delay": ["00:10:00", "00:20:00"], "tier": None,
                         "dist": round(((n["x"] - c["townCentre"][0]) ** 2 + (n["y"] - c["townCentre"][1]) ** 2) ** .5),
                         "guarded": False, "entries": [], "area": n["area"], "to": n["to"], "next": nx(n["entries"]),
                         "wild": False, "isNew": True, "inArea": None})
    for w in p["wildlife"]:
        if w["new"]:
            spawners.append({"id": w["id"], "file": "new", "label": "New forest wildlife", "x": w["x"], "y": w["y"], "count": w["count"],
                             "home": w["home"], "delay": ["00:05:00", "00:10:00"], "tier": None,
                             "dist": round(((w["x"] - cx) ** 2 + (w["y"] - cy) ** 2) ** .5),
                             "guarded": False, "entries": [], "area": None, "to": w["tier"], "next": nx(w["entries"]),
                             "wild": True, "isNew": True, "inArea": w["inArea"], "trees": w["trees"]})
    data = {
        "rect": c["rect"], "centre": c["townCentre"], "towns": c["towns"], "unguarded": c["unguarded"], "guardZones": c["guardZones"],
        "spawners": spawners, "deaths": c["deaths"],
        "areas": [{k: a[k] for k in ("id", "name", "theme", "rects", "tier", "spawners", "dist", "ringException", "deco", "decoNote") if k in a} for a in p["areas"]],
        "themes": {k: {"label": t["label"], "tier": t["tier"], "kinds": t["kinds"], "roster": t["roster"]} for k, t in p["themes"].items()},
        "rings": p["rings"], "wildKinds": p["wildKinds"], "deco": deco, "decoSites": deco_sites, "art": art, "dot": dot,

    }
    img = "data:image/png;base64," + base64.b64encode(open(png, "rb").read()).decode()
    # what is already built or decorated, as a see-through overlay (scenes keep clear of it)
    import builtmask
    _, built, _, _, _ = builtmask.tiles_of(c)
    x0, y0, x1, y1 = c["rect"]
    rows = [[(255, 70, 60, 150) if (x, y) in built else (0, 0, 0, 0) for x in range(x0, x1)] for y in range(y0, y1)]
    uoart.write_png(tmp, x1 - x0, y1 - y0, rows)
    data["builtImg"] = "data:image/png;base64," + base64.b64encode(open(tmp, "rb").read()).decode()
    html = open(os.path.join(HERE, "page-template.html"), encoding="utf-8").read()
    html = html.replace("__MAP__", img).replace("__DATA__", json.dumps(data, separators=(",", ":")))
    open(out, "w", encoding="utf-8").write(html)
    print("wrote", out, len(html) // 1024, "KB")


if __name__ == "__main__":
    main(sys.argv[1:])
