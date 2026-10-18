"""The gazetteer: where things are, looked up by role and context instead of typed as coordinates (owner's direction, 2026-10-15).

Pure and importable by every brain and test: standard library only, no Navrey, no bot state. The data file gazetteer.json is generated from the
world's own data by make_gazetteer.py (regions.json, the vendor / townspeople spawner files, the decoration files and the map's statics for forges,
anvils and looms, the teleporter definitions, the Felucca public moongates, the dungeon entrances); never edit it by hand, regenerate it.

    import gazetteer as gz
    gz.home_region(x, y)                       -> the town (or dungeon) region the point is in: {"name", "kind", "centre", "rects", ...} or None
    gz.region(name)                            -> a region dict by name
    gz.nearest_town(x, y)                      -> (region, distance) of the nearest town region (0 inside one)
    gz.near("bank", x, y, n=1)                 -> the n nearest places of a role: [{"role", "type", "x", "y", "z", "region", "dist", ...}]
    gz.services(region)                        -> {role: count} of what a town has; gz.has_role(region, "healer")
    gz.in_town(x, y) / gz.town_rects(region)   -> town test and the region's rectangles [(x1, y1, x2, y2), ...]
    gz.refuges(region, n=6)                    -> [(x, y), ...] spread-out safe spots of a town: healer, centre, bank, guards, inn
    gz.transitions(x, y, radius=30)            -> teleporter pairs whose entry is near a point: [{"src": [x, y, z], "dst": [...], "kind", "dist", ...}]
    gz.route(frm, to)                          -> the teleporters to step on to get from one side of the map to the other ([] if the same side,
                                                  None if no chain of teleporters joins them); each is a transition dict, in order
    gz.side(x, y)                              -> "surface" (x < 5120) or the name of the dungeon / town region the point is in, else "interior@cell"

Roles are the canonical short names ("bank", "healer", "smith", "tailor", "carpenter", "butcher", "bowyer", "mage", "provisioner", "alchemist", ...,
"forge", "anvil", "loom", "spinning_wheel", "oven", "ankh", "dummy", "butte", "moongate", "dungeon_entrance", "guard", "guildmaster" and
"<x>_guildmaster"); a place also answers to its raw type name in lower case ("blacksmith", "banker").
Distances are straight-line tiles. Nothing here knows where the bot is; pass the position.
"""
import json
import math
import os

DEFAULT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gazetteer.json")
SURFACE_X = 5120                                       # x at or beyond this is the dungeon / T2A area of the Felucca map, not the Britannia surface


def _in_rects(rects, x, y):
    return any(r[0] <= x <= r[2] and r[1] <= y <= r[3] for r in rects)


def _rect_dist(rects, x, y):
    best = 1e9
    for x1, y1, x2, y2 in rects:
        dx = max(x1 - x, 0, x - x2)
        dy = max(y1 - y, 0, y - y2)
        best = min(best, math.hypot(dx, dy))
    return best


def _area(rects):
    return sum((r[2] - r[0] + 1) * (r[3] - r[1] + 1) for r in rects)


def side_of(regions, x, y):
    """The side of the map a point is on: "surface" (x < 5120), else the dungeon or town region it lies in, else a coarse cell. A teleporter between two
    different sides is a crossing the pathfinder cannot plan across."""
    if x < SURFACE_X:
        return "surface"
    for kind in ("dungeon", "town"):
        hits = [r for r in regions if r["kind"] == kind and _in_rects(r["rects"], x, y)]
        if hits:
            return sorted(hits, key=lambda r: (-r.get("priority", 0), _area(r["rects"])))[0]["name"]
    return f"interior@{x // 256},{y // 256}"


class Gazetteer:
    def __init__(self, data):
        self.data = data
        self.regions = data["regions"]
        self.by_name = {r["name"]: r for r in self.regions}
        self.places = data["places"]
        self.trans = data["transitions"]
        self.by_role = {}
        for p in self.places:
            for r in p["roles"]:
                self.by_role.setdefault(r, []).append(p)
        self._graph = None

    # ---- regions ------------------------------------------------------------------------------------------------------------------------------

    def region(self, name_or_region):
        if isinstance(name_or_region, dict):
            return name_or_region
        return self.by_name.get(name_or_region)

    def regions_at(self, x, y):
        return [r for r in self.regions if _in_rects(r["rects"], x, y)]

    def home_region(self, x, y, kinds=("town", "dungeon")):
        hits = [r for r in self.regions_at(x, y) if r["kind"] in kinds]
        if not hits:
            return None
        return sorted(hits, key=lambda r: (-r.get("priority", 0), _area(r["rects"])))[0]

    def towns(self):
        return [r for r in self.regions if r["kind"] == "town"]

    def nearest_town(self, x, y):
        """(region, distance in tiles to its nearest rectangle; 0 inside)."""
        best = None
        for r in self.towns():
            d = _rect_dist(r["rects"], x, y)
            if best is None or d < best[1]:
                best = (r, d)
        return best

    def in_town(self, x, y):
        return any(_in_rects(r["rects"], x, y) for r in self.towns())

    def town_rects(self, region):
        r = self.region(region)
        return [tuple(t) for t in r["rects"]] if r else []

    def side(self, x, y):
        return side_of(self.regions, x, y)

    # ---- places -------------------------------------------------------------------------------------------------------------------------------

    def near(self, role, x, y, n=1, region=None, max_dist=None, same_side=False):
        """The n nearest places of a role (a name or a tuple of names) to a point, nearest first. `region` limits to one region's places, `max_dist`
        to a radius, `same_side` to places on the point's own side of the map (inside a dungeon, only its own places)."""
        roles = (role,) if isinstance(role, str) else tuple(role)
        seen, cands = set(), []
        for rl in roles:
            for p in self.by_role.get(rl.lower(), ()):
                if id(p) not in seen:
                    seen.add(id(p))
                    cands.append(p)
        if region is not None:
            rname = region["name"] if isinstance(region, dict) else region
            cands = [p for p in cands if p.get("region") == rname]
        if same_side:
            s = self.side(x, y)
            cands = [p for p in cands if p.get("side") == s]
        out = []
        for p in cands:
            d = math.hypot(p["x"] - x, p["y"] - y)
            if max_dist is None or d <= max_dist:
                q = dict(p)
                q["dist"] = round(d, 1)
                out.append(q)
        out.sort(key=lambda q: q["dist"])
        return out[:n]

    def services(self, region):
        """{role: count} of the places in a region (canonical roles only), the roles that make a town a town for a bot."""
        r = self.region(region)
        out = {}
        if not r:
            return out
        for p in self.places:
            if p.get("region") == r["name"]:
                out[p["role"]] = out.get(p["role"], 0) + 1
        return out

    def has_role(self, region, role):
        r = self.region(region)
        return bool(r) and any(p.get("region") == r["name"] for p in self.by_role.get(role.lower(), ()))

    def refuges(self, region, n=6, min_sep=12):
        """Spread-out spots to run to in a town: its healers, centre, banks, guards and inns, nearest the centre first within each kind, no two
        closer than min_sep. Falls back to the centre (and the rectangles' middles) for a town with none of those."""
        r = self.region(region)
        if not r:
            return []
        cx, cy = r["centre"][0], r["centre"][1]
        cands = []
        for role in ("healer", "bank", "guard", "inn"):
            ps = [p for p in self.by_role.get(role, ()) if p.get("region") == r["name"]]
            ps.sort(key=lambda p: math.hypot(p["x"] - cx, p["y"] - cy))
            cands += [(p["x"], p["y"]) for p in ps]
            if role == "healer":
                cands.append((cx, cy))
        if not cands:
            cands = [(cx, cy)] + [((t[0] + t[2]) // 2, (t[1] + t[3]) // 2) for t in r["rects"]]
        out = []
        for c in cands:
            if all(math.hypot(c[0] - o[0], c[1] - o[1]) >= min_sep for o in out):
                out.append(c)
            if len(out) >= n:
                break
        return out

    # ---- teleporters ---------------------------------------------------------------------------------------------------------------------------

    def transitions(self, x, y, radius=30, kinds=None):
        out = []
        for t in self.trans:
            if kinds and t["kind"] not in kinds:
                continue
            d = math.hypot(t["src"][0] - x, t["src"][1] - y)
            if d <= radius:
                q = dict(t)
                q["dist"] = round(d, 1)
                out.append(q)
        out.sort(key=lambda q: q["dist"])
        return out

    def _side_graph(self):
        if self._graph is None:
            g = {}
            for t in self.trans:
                if t["src_side"] != t["dst_side"]:
                    g.setdefault(t["src_side"], {}).setdefault(t["dst_side"], []).append(t)
            self._graph = g
        return self._graph

    def route(self, frm, to):
        """The teleporters to step on, in order, to get from `frm` (x, y) to `to` (x, y): [] when both are on the same side of the map (the planner
        can walk it), None when no chain of teleporters joins them. At each hop the entry nearest the current position is taken."""
        a, b = self.side(frm[0], frm[1]), self.side(to[0], to[1])
        if a == b:
            return []
        g = self._side_graph()
        prev, queue = {a: None}, [a]
        for cur in queue:
            for nxt in g.get(cur, {}):
                if nxt not in prev:
                    prev[nxt] = cur
                    queue.append(nxt)
        if b not in prev:
            return None
        path, cur = [], b
        while cur != a:
            path.append(cur)
            cur = prev[cur]
        path.append(a)
        path.reverse()
        pos, hops = (frm[0], frm[1]), []
        for s1, s2 in zip(path, path[1:]):
            t = min(g[s1][s2], key=lambda t: math.hypot(t["src"][0] - pos[0], t["src"][1] - pos[1]))
            hops.append(t)
            pos = (t["dst"][0], t["dst"][1])
        return hops


_default = None


def get(path=None):
    global _default
    if path is not None:
        return Gazetteer(json.load(open(path, encoding="utf-8")))
    if _default is None:
        _default = Gazetteer(json.load(open(DEFAULT_PATH, encoding="utf-8")))
    return _default


def reload():
    global _default
    _default = None
    return get()


def home_region(x, y, kinds=("town", "dungeon")): return get().home_region(x, y, kinds)
def region(name_or_region): return get().region(name_or_region)
def regions_at(x, y): return get().regions_at(x, y)
def nearest_town(x, y): return get().nearest_town(x, y)
def towns(): return get().towns()
def in_town(x, y): return get().in_town(x, y)
def town_rects(region): return get().town_rects(region)
def side(x, y): return get().side(x, y)
def near(role, x, y, n=1, region=None, max_dist=None, same_side=False): return get().near(role, x, y, n, region, max_dist, same_side)
def services(region): return get().services(region)
def has_role(region, role): return get().has_role(region, role)
def refuges(region, n=6, min_sep=12): return get().refuges(region, n, min_sep)
def transitions(x, y, radius=30, kinds=None): return get().transitions(x, y, radius, kinds)
def route(frm, to): return get().route(frm, to)
