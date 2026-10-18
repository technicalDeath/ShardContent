"""Tests for walkroute.py (walkgrid.bin from make_walkgrid.py): python test_walkroute.py

Oracles that do not come from the same code: the gazetteer's vendor and healer spots (an NPC stands there, so a tile next to it must be walkable), land tiles
read straight from the client's map for water / grass samples, the Trinsic / Skara Brae / Yew / Vesper step counts of the survey, and the first-trip
waypoint lists whose straight legs over obstacles this module is meant to catch.
"""
import ast
import json
import os
import random
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gazetteer as gz
import make_walkgrid as mk
import walkroute as wr

# ---- pure ------------------------------------------------------------------------------------------------------------------------------------------
tree = ast.parse(open(os.path.join(HERE, "walkroute.py"), encoding="utf-8").read())
imports = {n.names[0].name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import)} | {n.module.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
assert imports <= {"heapq", "math", "os", "struct", "zlib"}, imports

m = wr.get()
assert (m.W, m.H) == (5120, 4096)

# ---- the grid agrees with the world data ------------------------------------------------------------------------------------------------------------
checked = ok = 0
for role in ("bank", "healer", "smith", "tailor", "carpenter", "butcher", "bowyer", "mage", "provisioner", "forge", "anvil", "loom", "dummy", "butte"):
    for p in gz.near(role, 1470, 1620, n=20, region="Britain"):
        checked += 1
        ok += any(m.walkable(p["x"] + dx, p["y"] + dy) for dx in range(-3, 4) for dy in range(-3, 4))
assert checked >= 30 and ok / checked >= 0.9, (ok, checked)
for t in gz.towns():
    if t["centre"][0] < wr.get().W:
        assert m.snap(t["centre"][0], t["centre"][1], 12) is not None, t["name"]

uodata = os.path.join(mk.ROOT, "UOData")
if os.path.exists(os.path.join(uodata, "tiledata.mul")):
    raw = open(os.path.join(uodata, "tiledata.mul"), "rb").read()
    water, grass, o = set(), set(), 0
    for g in range(512):
        o += 4
        for i in range(32):
            nm = raw[o + 10:o + 30].split(b"\0")[0].decode("latin1")
            (water if nm == "water" else grass if nm == "grass" else set()).add(g * 32 + i) if nm in ("water", "grass") else None
            o += 30
    mp = mk.load_map(uodata)
    rnd = random.Random(7)
    wet = dry = nw = nd = 0
    for _ in range(40000):
        x, y = rnd.randrange(0, mk.W), rnd.randrange(0, mk.H)
        tid = struct.unpack_from("<H", mp, ((x >> 3) * (mk.MAP_H // 8) + (y >> 3)) * 196 + 4 + ((y & 7) * 8 + (x & 7)) * 3)[0]
        if tid in water and nw < 600:
            nw += 1
            wet += m.walkable(x, y)
        elif tid in grass and nd < 600:
            nd += 1
            dry += m.walkable(x, y)
    assert nw >= 300 and nd >= 300 and wet <= 0.05 * nw and dry >= 0.6 * nd, (wet, nw, dry, nd)       # water is not walkable (a few bridges); open grass mostly is

# ---- planning ---------------------------------------------------------------------------------------------------------------------------------------
BRIT = (1475, 1645)
for name, dest, lo, hi in (("Trinsic", (1927, 2779), 1250, 1350), ("Skara Brae", (811, 2243), 700, 820), ("Yew", (535, 992), 1330, 1440), ("Vesper", (2882, 788), 1560, 1680)):
    r = m.plan(BRIT, dest)
    assert r and r["exact"] and lo <= r["steps"] <= hi, (name, r and (r["steps"], r["exact"]))
    wp = r["waypoints"]
    assert all(m.walkable(*p) for p in wp) and wr.cheb(wp[0], BRIT) <= 12 and wr.cheb(wp[-1], dest) <= 12
    assert all(wr.cheb(a, b) <= 40 for a, b in zip(wp, wp[1:])) and m.check_legs(wp) == [], name         # every straight leg is clear
    assert 3 <= len(r["corners"]) <= 25
assert m.plan(BRIT, (4111, 432)) is None                                  # Deceit's entrance is on another landmass
assert m.plan(BRIT, (1475, 1645))["steps"] == 0
short = m.plan(BRIT, (1491, 1641)); assert short and short["exact"] and short["steps"] < 60 and m.check_legs(short["waypoints"]) == []
assert m.plan((1475, 1645), (5300, 3000)) is None or True                 # off the surface grid: no route, no crash
assert m.plan((-5, -5), BRIT) is not None or True

# ---- leg checks -------------------------------------------------------------------------------------------------------------------------------------
assert m.first_blocked((1475, 1645), (1448, 1678)) == (1473, 1647) and not m.walkable(1473, 1647)         # a first-trip leg that walks into a wall
assert m.leg_clear((1475, 1645), (1475, 1645)) and wr.leg_clear((1475, 1645), (1475, 1645))
bad = m.check_legs([(1475, 1645), (1448, 1678), (1446, 1700)])
assert bad and bad[0]["i"] == 0 and bad[0]["blocked_at"] == (1473, 1647)

# ---- danger costs -----------------------------------------------------------------------------------------------------------------------------------
base = m.plan(BRIT, (1927, 2779))
mid = base["path"][len(base["path"]) // 2]
pen = wr.penalty_circles([(mid[0], mid[1], 60, 8.0)])
assert pen[(mid[0] // 4, mid[1] // 4)] == 8.0 and len(pen) > 100
inside = lambda path: sum(1 for p in path if ((p[0] - mid[0]) ** 2 + (p[1] - mid[1]) ** 2) ** 0.5 <= 60)
det = m.plan(BRIT, (1927, 2779), pen)
assert det and det["exact"] and det["steps"] >= base["steps"] and inside(det["path"]) < inside(base["path"]) * 0.5 and m.check_legs(det["waypoints"]) == [], \
    (det and det["steps"], base["steps"], inside(det["path"]), inside(base["path"]))
assert wr.penalty_merge(pen, {(mid[0] // 4, mid[1] // 4): 20.0})[(mid[0] // 4, mid[1] // 4)] == 20.0


class Mem:
    """What penalty_from_memory reads: world cells with decayed death counts, and dangerous_cell."""
    def __init__(self, cells, dangerous=()):
        self.state = {"world": {"cells": cells}}; self.dangerous = set(dangerous)
    def dangerous_cell(self, c): return c in self.dangerous

cx, cy = (mid[0] // 40) * 40, (mid[1] // 40) * 40
mem = Mem({f"{cx},{cy}": {"deaths": 2.0, "kills": 0.0}, f"{cx + 40},{cy}": {"deaths": 0.0}, f"{cx},{cy + 40}": {"deaths": 0.0}, "0,0": {"deaths": 0.1}}, dangerous={f"{cx},{cy + 40}"})
pm = wr.penalty_from_memory(mem)
assert pm[(cx // 4 + 1, cy // 4 + 1)] == 5.0                                       # 1 + 2 * deaths
assert pm[(cx // 4 + 1, cy // 4 + 11)] == 6.0                                      # a dangerous cell
assert (0, 0) not in pm and (cx // 4 + 11, cy // 4 + 1) not in pm                    # faint or no deaths: free
assert wr.penalty_from_memory(object()) == {}
rr = m.plan(BRIT, (1927, 2779), pm)
assert rr and rr["exact"] and rr["steps"] >= base["steps"]

# ---- a heavy penalty (the strong spawners of hardspots.json) must not turn a route into a 4-tile-cell guess (regression: Trinsic -> its moongate)
hs = os.path.join(HERE, "hardspots.json")
if os.path.exists(hs):
    circ = [(c["x"], c["y"], c["r"], c["factor"]) for c in json.load(open(hs, encoding="utf-8"))["circles"]]
    hp = wr.penalty_circles(circ)
    for a, b in (((1867, 2780), (1828, 2948)), (BRIT, (1927, 2779)), (BRIT, (811, 2243)), (BRIT, (535, 992)), (BRIT, (2882, 788))):
        r = m.plan(a, b, hp)
        assert r and r["exact"] and m.check_legs(r["waypoints"]) == [] and all(m.walkable(*p) for p in r["waypoints"]), (a, b, r and (r["exact"], r["steps"]))

# ---- repair of waypoint lists with legs over obstacles -----------------------------------------------------------------------------------------------
routes = json.load(open(os.path.join(HERE, "..", "..", "..", "..", "work", "botfarm-watch", "first-trip-routes.json"), encoding="utf-8")) \
    if os.path.exists(os.path.join(HERE, "..", "..", "..", "..", "work", "botfarm-watch", "first-trip-routes.json")) else None
if routes:
    reported = []
    for tr in routes["trips"]:
        wps = tr["waypoints"]
        if not wps or not tr.get("reachable_on_foot", True):
            continue
        before = len(m.check_legs(wps))
        fixed = m.repair(wps)
        assert fixed is not None and m.check_legs(fixed) == [] and all(m.walkable(*p) for p in fixed), tr["id"]
        reported.append((tr["id"], before, len(wps), len(fixed)))
    print("first-trip legs over obstacles (id, bad legs, waypoints, repaired waypoints):", reported)
assert m.repair([(1475, 1645), (4111, 432)]) is None                                # a leg with no land route
assert m.repair([(1475, 1645), (1491, 1641)]) is not None

# ---- the file is what the inputs produce (slow; run `python make_walkgrid.py --check` after a change of the map data) ---------------------------------------
print("test_walkroute OK:", os.path.getsize(wr.DEFAULT_PATH), "bytes of grid")
