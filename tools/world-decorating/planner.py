"""Arranges catalog furnishings in a real room: checks a layout against the server's own walkable floor, draws a plan, and writes the placement
file the test probe lays in the world.

  python planner.py LAYOUT.json            check, write the plan PNG and the client placement file, print the legend and any problems
  python planner.py LAYOUT.json --quiet    problems only

LAYOUT.json (see layouts/counselor-guild-east.json):
  {"site": "sites/counselor-guild-east.json", "name": "site4-v8", "pieces": [["Gray Brick Fireplace", "east", 1624, 1664], ...]}
Each piece is [catalog id or exact name, facing, x, y]; x, y is the piece's MIN-CORNER tile (smallest x, smallest y of its footprint).
Facings are the catalog's (south, east, north, west, none). A piece lists only the facings the art has: `facings CR-FRN-029` shows them.

SITE config (sites/*.json), all coordinates absolute map tiles:
  walkgrid      work-relative path of the server's walk grid, written by [TestOnlyWalkGrid on the probe
  interior      rectangles whose walkable cells count as the room's floor
  extraFloor    tiles that read as blocked in the walk grid but are passable (interior door tiles)
  outside       rectangles outside the walls where pieces may stand (a forecourt)
  keepClear     tiles no furniture may block (the lane inside the door, interior doorways)
  entry         the tile the connectivity check starts from (inside the door)
  rooms         {name: [x, y]} one free tile in each room: each must be reachable from the entry
  view          [x0, y0, x1, y1] the plan's window
  minReachable  smallest furniture piece (cells) that must have a free walkable neighbour (default 2; single chairs and lamps may sit in pockets)

SEMANTIC FIELDS (optional fifth element of a piece, the declared intent that the checker verifies; see the skill world-decorating):
  {"against": "N"}          the piece's back is to a wall on that side (N, S, E, W, or "N,E" for a corner): the tile beyond must not be floor
  {"serves": "<piece>"}     the piece exists for another (a chair for its table): their footprints must touch
  {"on": "<piece>"}         the piece stands on another (a table on its rug): its footprint must lie inside the other's
  {"group": "<name>"}       the piece belongs to a group (one activity or one display: a dining set, a hearth wall, a sleeping area)
  {"role": "anchor|support|accent"}   what it is to its group: the thing the group is for, what serves it, small dressing
Group checks: every group that declares roles has an anchor; the groups' bounding boxes do not overlap (a group is one unit, not a scatter that
other groups run through); pieces with no group are listed as NOTE lines (an orphan is usually a piece nobody thought about).

Rules checked (each was a real mistake while arranging the Counselor's Guild showroom):
  * every cell of every piece is on server-walkable floor (interior, extraFloor or outside) and pieces of the same kind do not overlap
  * nothing blocks keepClear tiles, so doors stay usable
  * wall hangings stand against a wall facing the right way (a "north" hanging needs a non-walkable tile to its north, a "west" one to its west)
  * every room's probe tile and every furniture piece of minReachable+ cells can be walked to from the entry
  * furniture standing on a rug is lifted to the rug's top (a rug without the Background flag, such as the Slate Dragon Rug, is height 1 and
    would otherwise draw over the furniture)
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(WORKSPACE, "ShardContent", "tools", "cosmetic-catalog"))
import uoart  # noqa: E402

DOCS = os.path.join(WORKSPACE, "ShardContent", "docs", "cosmetic-rewards")
LAYOUT_OUT = os.path.join(WORKSPACE, "work", "cosmetics", "layouts")
PLAN_OUT = os.path.join(WORKSPACE, "work", "decorating")
CATALOGS = ("cosmetic-rewards.json", "cosmetic-rewards-neutral.json")

_catalog = None


def catalog():
    """({id: reward}, {name: [rewards]}) from the era and era-neutral catalogs."""
    global _catalog
    if _catalog is None:
        by_id, by_name = {}, {}
        for n in CATALOGS:
            for r in json.load(open(os.path.join(DOCS, n), encoding="utf-8"))["rewards"]:
                by_id[r["id"]] = r
                by_name.setdefault(r["name"], []).append(r)
        _catalog = (by_id, by_name)
    return _catalog


def resolve(piece):
    by_id, by_name = catalog()
    if piece in by_id:
        return by_id[piece]
    hits = by_name.get(piece)
    if not hits:
        raise KeyError("no catalog piece called %r (use the id, e.g. CR-FRN-029)" % piece)
    if len(hits) > 1:
        raise KeyError("%r matches %s: use the id" % (piece, [h["id"] for h in hits]))
    return hits[0]


def facings(piece):
    r = resolve(piece)
    return [(r.get("facing"), r["parts"])] + [(a["facing"], a["parts"]) for a in r.get("altFacings", [])]


def parts_for(piece, facing):
    for f, p in facings(piece):
        if f == facing:
            return p
    raise KeyError("%s has no facing %r (it has %s)" % (piece, facing, [f for f, _ in facings(piece)]))


def kind_of(piece):
    p = resolve(piece)["placement"]
    return "rug" if p == "ground-cover" else "wall" if p.startswith("wall") else "furn"


class Site:
    def __init__(self, path):
        self.cfg = json.load(open(path, encoding="utf-8"))
        g = json.load(open(os.path.join(WORKSPACE, self.cfg["walkgrid"])))
        self.grid, self.gx0, self.gy0, self.gw, self.gh = g["rows"], g["x0"], g["y0"], g["w"], g["h"]
        self.interior = set()
        for (x0, y0, x1, y1) in self.cfg["interior"]:
            self.interior |= {(x, y) for x in range(x0, x1 + 1) for y in range(y0, y1 + 1) if self.walk_z(x, y) is not None}
        for c in self.cfg.get("extraFloor", []):
            self.interior.add(tuple(c))
        self.outside = [tuple(r) for r in self.cfg.get("outside", [])]
        self.keep = [tuple(c) for c in self.cfg.get("keepClear", [])]
        self.entry = tuple(self.cfg["entry"])
        self.rooms = {k: tuple(v) for k, v in self.cfg.get("rooms", {}).items()}

    def walk_z(self, x, y):
        if not (0 <= x - self.gx0 < self.gw and 0 <= y - self.gy0 < self.gh):
            return None
        return self.grid[y - self.gy0][x - self.gx0]

    def outside_ok(self, c):
        return any(r[0] <= c[0] <= r[2] and r[1] <= c[1] <= r[3] for r in self.outside)


def footprint(piece, facing):
    parts = parts_for(piece, facing)
    xs, ys = [p["dx"] for p in parts], [p["dy"] for p in parts]
    return max(xs) - min(xs) + 1, max(ys) - min(ys) + 1


def check(site, pieces):
    problems, placed = [], []
    cells = {"rug": {}, "furn": {}, "wall": {}}
    metas = []
    for entry in pieces:
        piece, facing, mx, my = entry[:4]
        metas.append(entry[4] if len(entry) > 4 else {})
        k = kind_of(piece)
        w, h = footprint(piece, facing)
        name = resolve(piece)["name"]
        for i in range(w):
            for j in range(h):
                c = (mx + i, my + j)
                if c not in site.interior and not site.outside_ok(c):
                    problems.append("%s %s: cell %s is not floor" % (name, facing, c))
                if c in cells[k]:
                    problems.append("%s overlaps %s at %s" % (name, cells[k][c], c))
                cells[k][c] = name
        placed.append((piece, name, facing, mx, my, w, h, k))
    for c in site.keep:
        if c in cells["furn"]:
            problems.append("%s blocks the clear tile %s" % (cells["furn"][c], c))
    for (piece, name, facing, mx, my, w, h, k) in placed:
        if k != "wall":
            continue
        if facing == "north":
            problems += ["%s (north) cell %s is not under a north wall" % (name, (mx + i, my)) for i in range(w) if site.walk_z(mx + i, my - 1) is not None]
        else:
            problems += ["%s (west) cell %s is not beside a west wall" % (name, (mx, my + j)) for j in range(h) if site.walk_z(mx - 1, my + j) is not None]
    free = {c for c in site.interior if c not in cells["furn"]}
    seen, stack = {site.entry}, [site.entry]
    while stack:
        x, y = stack.pop()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if n in free and n not in seen:
                seen.add(n)
                stack.append(n)
    min_cells = site.cfg.get("minReachable", 2)
    for (piece, name, facing, mx, my, w, h, k) in placed:
        if k == "furn" and w * h >= min_cells:
            body = {(mx + i, my + j) for i in range(w) for j in range(h)}
            ring = {(mx + i, my + j) for i in range(-1, w + 1) for j in range(-1, h + 1)} - body
            if not (ring & seen):
                problems.append("%s at %s cannot be reached from the entry" % (name, (mx, my)))
    for rn, rc in site.rooms.items():
        if rc not in seen:
            problems.append("room %s (probe tile %s) cannot be reached from the entry" % (rn, rc))
    semantic_checks(site, placed, metas, problems)
    return placed, cells, problems


DIRS = {"N": (0, -1), "S": (0, 1), "E": (1, 0), "W": (-1, 0)}


def cells_of(p):
    return {(p[3] + i, p[4] + j) for i in range(p[5]) for j in range(p[6])}


def semantic_checks(site, placed, metas, problems):
    """Verify the declared intent (against / serves / on / group / role): does each piece stand where its meaning says it should."""
    by_name = {p[1]: p for p in placed}

    def find(ref):
        try:
            return by_name.get(resolve(ref)["name"])
        except KeyError:
            return None

    groups = {}
    for p, m in zip(placed, metas):
        name, cs = p[1], cells_of(p)
        for d in [x.strip() for x in m.get("against", "").split(",") if x.strip()]:
            dx, dy = DIRS[d]
            for c in sorted(c for c in cs if (c[0] + dx, c[1] + dy) not in cs):
                n = (c[0] + dx, c[1] + dy)
                if n in site.interior or site.outside_ok(n):
                    problems.append("%s is meant to stand against a wall to the %s but %s beside %s is open floor" % (name, d, n, c))
        if m.get("serves"):
            t = find(m["serves"])
            if t is None:
                problems.append("%s serves %r, which is not in the layout" % (name, m["serves"]))
            elif not any((c[0] + dx, c[1] + dy) in cells_of(t) for c in cs for dx, dy in DIRS.values()):
                problems.append("%s serves %s but does not touch it" % (name, t[1]))
        if m.get("on"):
            t = find(m["on"])
            if t is None:
                problems.append("%s is meant to stand on %r, which is not in the layout" % (name, m["on"]))
            elif not cs <= cells_of(t):
                problems.append("%s is meant to stand on %s but %d of its cells are off it" % (name, t[1], len(cs - cells_of(t))))
        if m.get("group"):
            groups.setdefault(m["group"], []).append((p, m.get("role")))
        else:
            problems.append("NOTE: %s has no group" % name)
    boxes = {}
    for g, members in groups.items():
        if any(r for _, r in members) and not any(r == "anchor" for _, r in members):
            problems.append("group %r has no anchor (the thing the group is for)" % g)
        allc = set().union(*(cells_of(p) for p, _ in members))
        boxes[g] = (min(c[0] for c in allc), min(c[1] for c in allc), max(c[0] for c in allc), max(c[1] for c in allc))
    names = sorted(boxes)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            A, B = boxes[a], boxes[b]
            if not (A[2] < B[0] or B[2] < A[0] or A[3] < B[1] or B[3] < A[1]):
                problems.append("groups %r and %r overlap (%s and %s): keep each group one unit" % (a, b, A, B))


def rug_top(piece):
    t = uoart.tiles()
    return 1 + max(t[int(p["id"], 16)].height for p in resolve(piece)["parts"])


def client_layout(site, placed):
    """Absolute-coordinate placement list for the probe's [TestOnlyDecor (z from the server's walkable floor)."""
    tops = {}
    for (piece, name, facing, mx, my, w, h, k) in placed:
        if k == "rug":
            for i in range(w):
                for j in range(h):
                    tops[(mx + i, my + j)] = rug_top(piece)
    items = []
    for (piece, name, facing, mx, my, w, h, k) in placed:
        parts = parts_for(piece, facing)
        x0p, y0p = min(p["dx"] for p in parts), min(p["dy"] for p in parts)
        lift = max([tops.get((mx + i, my + j), 0) for i in range(w) for j in range(h)] + [0]) if k == "furn" else 0
        for p in parts:
            x, y = mx + p["dx"] - x0p, my + p["dy"] - y0p
            base = site.walk_z(x, y)
            z = (15 if base is None else base) + p["dz"] + (1 if k == "rug" else lift)
            items.append({"id": int(p["id"], 16), "x": x, "y": y, "z": z, "hue": p.get("hue", 0) or 0, "piece": resolve(piece)["id"]})
    return items


COL = {"rug": (120, 52, 52, 255), "furn": (200, 160, 90, 255), "wall": (90, 150, 200, 255)}


def render_plan(site, placed, out, S=34):
    x0, y0, x1, y1 = site.cfg["view"]
    w, h = (x1 - x0 + 1) * S, (y1 - y0 + 1) * S
    px = [[(30, 30, 34, 255)] * w for _ in range(h)]

    def rect(ax, ay, bx, by, col, inset=0):
        for yy in range((ay - y0) * S + inset, (by - y0 + 1) * S - inset):
            for xx in range((ax - x0) * S + inset, (bx - x0 + 1) * S - inset):
                if 0 <= yy < h and 0 <= xx < w:
                    px[yy][xx] = col

    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if site.walk_z(x, y) is not None:
                rect(x, y, x, y, (60, 78, 60, 255) if (x, y) in site.interior else (70, 70, 74, 255), 1)
    for c in site.keep:
        rect(c[0], c[1], c[0], c[1], (240, 230, 120, 255), 12)
    for n, (piece, name, facing, mx, my, w_, h_, k) in sorted(enumerate(placed, 1), key=lambda e: {"rug": 0, "furn": 1, "wall": 2}[e[1][7]]):
        if k == "wall":
            for i in range(w_ if facing == "north" else 1):
                for j in range(h_ if facing != "north" else 1):
                    rect(mx + i, my + j, mx + i, my + j, COL[k], 14)
        else:
            rect(mx, my, mx + w_ - 1, my + h_ - 1, COL[k], 2 if k == "rug" else 3)
        uoart.label(px, (mx - x0) * S + 4, (my - y0) * S + 4, str(n), (255, 255, 255, 255), 2)
    for x in range(x0, x1 + 1):
        if x % 2 == 0:
            uoart.label(px, (x - x0) * S + 2, 1, str(x)[-2:], (255, 255, 0, 255), 1)
    for y in range(y0, y1 + 1):
        if y % 2 == 0:
            uoart.label(px, 1, (y - y0) * S + 2, str(y)[-2:], (255, 255, 0, 255), 1)
    uoart.write_png(out, w, h, px)


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    if argv[1] == "sheet":        # sheet OUT.png PIECE... : every facing of each piece, numbered, rendered from the client art
        import catalog
        cells, legend = [], []
        for piece in argv[3:]:
            r = resolve(piece)
            for f, parts in facings(piece):
                e = dict(r)
                e["parts"] = parts
                e["graphics"] = [dict(p, hue=p.get("hue", 0) or 0) for p in parts]
                cells.append(e)
                xs, ys = [p["dx"] for p in parts], [p["dy"] for p in parts]
                legend.append("#%d %s / %s  %dx%d (x by y)" % (len(cells), r["name"], f, max(xs) - min(xs) + 1, max(ys) - min(ys) + 1))
        catalog.sheet_entries(argv[2], cells, cols=min(8, max(1, len(cells))), cell=150)
        print(chr(10).join(legend))
        print("wrote", argv[2])
        return 0
    if argv[1] == "facings":
        for f, parts in facings(argv[2]):
            xs, ys = [p["dx"] for p in parts], [p["dy"] for p in parts]
            print("%-6s %dx%d (x by y), %d graphics" % (f, max(xs) - min(xs) + 1, max(ys) - min(ys) + 1, len(parts)))
        return 0
    path = os.path.abspath(argv[1])
    lay = json.load(open(path, encoding="utf-8"))
    site = Site(os.path.normpath(os.path.join(os.path.dirname(path), lay["site"])))
    pieces = [tuple(p) for p in lay["pieces"]]          # [piece, facing, x, y] or [piece, facing, x, y, {semantic fields}]
    placed, cells, problems = check(site, pieces)
    name = lay["name"]
    out_dir = os.path.join(PLAN_OUT, name)
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(LAYOUT_OUT, exist_ok=True)
    items = client_layout(site, placed)
    json.dump({"absolute": True, "items": items}, open(os.path.join(LAYOUT_OUT, name + ".json"), "w"))
    render_plan(site, placed, os.path.join(out_dir, "plan.png"))
    names = [p[1] for p in placed]
    print("layout %s: %d pieces (%d distinct), %d graphics, %d furniture cells, %d rug cells" % (name, len(placed), len(set(names)), len(items), len(cells["furn"]), len(cells["rug"])))
    print("  plan:   %s" % os.path.join(out_dir, "plan.png"))
    print("  client: %s   (lay it with: lay.py %s)" % (os.path.join(LAYOUT_OUT, name + ".json"), name))
    if "--quiet" not in argv:
        for i, p in enumerate(placed, 1):
            print("   %2d  %-32s %-6s (%d,%d) %dx%d" % (i, p[1], p[2], p[3], p[4], p[5], p[6]))
    for p in problems:
        print("  %s" % (p if p.startswith("NOTE") else "PROBLEM: " + p))
    return 1 if any(not p.startswith("NOTE") for p in problems) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
