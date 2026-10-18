"""Resource lists per region (shores, mountains, trees) for the brains: see work/botfarm/patches/patch_geo.py.

    python geo.py --towns [--kinds shores mountains trees] [--radius 300]      make the files for every surface town
    python geo.py --region Trinsic
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
GEO_DIR = os.path.join(ROOT, "work", "botfarm", "geo")
BRITAIN_CENTRE = (1470, 1620)            # the centre the Britain files were made around, and the old reach tests measured from
BRITAIN_LIKE = 150                       # a home this close to it keeps the Britain lists
MAP_W, MAP_H = 7168, 4096
KINDS = ("shores", "mountains", "trees")


def cheb(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def home_centre(home):
    return (int(home["centre"][0]), int(home["centre"][1]))


def is_britain(home):
    """No home known, or a home within BRITAIN_LIKE tiles of Britain's old centre: the Britain lists apply."""
    return home is None or cheb(home_centre(home), BRITAIN_CENTRE) <= BRITAIN_LIKE or cheb(home_centre(home), (1495, 1629)) <= BRITAIN_LIKE


def centre_of(home):
    """The centre a brain measures its work radius from: Britain's old centre for a Britain-like home, else the home's centre."""
    return BRITAIN_CENTRE if is_britain(home) else home_centre(home)


def slug(name):
    return "".join(ch if ch.isalnum() else "-" for ch in name.lower()).strip("-")


def path(kind, name):
    return os.path.join(GEO_DIR, f"{kind}-{slug(name)}.json")


def build(kind, centre, radius=300):
    """The resource list in the box around centre, nearest the centre first (made from the map files; needs UOData)."""
    box = (max(0, centre[0] - radius), max(0, centre[1] - radius), min(MAP_W - 1, centre[0] + radius), min(MAP_H - 1, centre[1] + radius))
    if kind == "shores":
        import make_shores
        return make_shores.build(*box, centre=centre)
    if kind == "mountains":
        import make_mountains
        return make_mountains.build(*box, centre=centre)
    if kind == "trees":
        import make_trees
        return sorted(make_trees.build(*box), key=lambda t: cheb(t, centre))
    raise ValueError(kind)


def get(kind, home, radius=300, make=True):
    """The home's own list (a list of lists), read from its file, made on demand; [] when it cannot be made."""
    p = path(kind, home["name"])
    try:
        return json.load(open(p, encoding="utf-8"))
    except (OSError, ValueError):
        pass
    if not make:
        return []
    try:
        out = build(kind, home_centre(home), radius)
        os.makedirs(GEO_DIR, exist_ok=True)
        tmp = p + f".{os.getpid()}.tmp"
        json.dump(out, open(tmp, "w", encoding="utf-8"))
        os.replace(tmp, p)
        return out
    except Exception as e:
        print(f"geo: could not make the {kind} list for {home['name']}: {type(e).__name__}: {e}", file=sys.stderr)
        return []


def regional(kind, home, britain_list, radius=300):
    """The list a bot at `home` should use: the Britain list unchanged for a Britain-like home, else the home's own nearest-first list within `radius`."""
    if is_britain(home):
        return britain_list
    c = home_centre(home)
    rows = [tuple(t) for t in get(kind, home, radius) if cheb(t, c) <= radius]
    return sorted(rows, key=lambda t: cheb(t, c))


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--towns", action="store_true")
    ap.add_argument("--region")
    ap.add_argument("--kinds", nargs="+", default=list(KINDS))
    ap.add_argument("--radius", type=int, default=300)
    a = ap.parse_args()
    import gazetteer as gz
    homes = [r for r in gz.towns() if r["centre"][0] < gz.SURFACE_X]
    if a.region:
        homes = [r for r in homes if r["name"].lower() == a.region.lower()]
    elif not a.towns:
        ap.error("--towns or --region NAME")
    for r in homes:
        for kind in a.kinds:
            out = get(kind, r, a.radius)
            print(f"{r['name']:18} {kind:9} {len(out):5} -> {path(kind, r['name'])}")


if __name__ == "__main__":
    sys.exit(main())
