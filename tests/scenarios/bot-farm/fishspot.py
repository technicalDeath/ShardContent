"""Where a fisher can stand (Operator's finding from the Vesper drop test; the Helper). Pure helpers for fisher.py, written into the bot-farm folder by patch_fishspot.py.

The finding: BotFisherAR in Vesper caught nothing (69.5 nopath per bot-hour against 16 for the controls). The fisher walked to the WATER-EDGE point of a shore ("an edge tile of
deep water per 8x8 bank", shores.json / geo.py) and fished from "where the path ends"; Vesper is a canal town and most of those points lie across water or among walls:
"cannot reach the shore at (2960,673) / (2954,664) (nopath)", "the walk to 2971,687 ended at 2979,679, 8 tiles short". But fishing needs only a standing tile within the pole's
range of water (Fishing.MaxRange = 4, line of sight): so the thing to look for is a REACHABLE WALKABLE TILE with water in range, not the water's edge.

stand_for(shore, here): for the shore point S, the walkable tiles (walkroute.py's map) within STAND_RANGE of S - S is water, so each has water in range - tried nearest the bot's
path first (walkroute.plan, at most TRIES of them, spread 2+ tiles apart); the one with the shortest land route is the stand. Returns (x, y) for a reachable stand, False when the data
says no tile near S can be walked to from here (the caller blocks that shore at once instead of walking at it and getting nopath), None where there is no map data (the old walk).
nearest_water(x, y, r): the water tile nearest to a standing point within r (watergrid.bin from make_watergrid.py: the deep-water land tiles 0xA8-0xAB), with an optional filter
(a fished-out bank); instant, where the old find_water asked the client for 121 tiles.
"""
import os
import struct
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
STAND_RANGE = 3                  # a standing tile this near the shore's water tile (the pole reaches 4: a tile of margin)
CAST_RANGE = 4                   # Fishing.MaxRange
TRIES = 5
_W = None


def cheb(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


class Water:
    def __init__(self, path=None):
        raw = open(path or os.path.join(HERE, "watergrid.bin"), "rb").read()
        assert raw[:4] == b"WTR1"
        self.W, self.H = struct.unpack_from("<HH", raw, 4)
        self.bits = zlib.decompress(raw[8:])

    def is_water(self, x, y):
        if not (0 <= x < self.W and 0 <= y < self.H):
            return False
        i = x * self.H + y
        return (self.bits[i >> 3] >> (i & 7)) & 1 == 1

    def nearest(self, x, y, r, usable=None):
        for d in range(r + 1):
            ring = [(x + dx, y + dy) for dx in range(-d, d + 1) for dy in range(-d, d + 1) if max(abs(dx), abs(dy)) == d]
            ring.sort(key=lambda p: (p[0] - x) ** 2 + (p[1] - y) ** 2)
            for p in ring:
                if self.is_water(*p) and (usable is None or usable(*p)):
                    return p
        return None


def water():
    global _W
    if _W is None:
        try:
            _W = Water()
        except Exception:
            _W = False
    return _W or None


def nearest_water(x, y, r=CAST_RANGE, usable=None):
    w = water()
    return w.nearest(x, y, r, usable) if w else None


def has_stand(shore, wr_module=None):
    """Cheap pre-filter: is any tile within STAND_RANGE of the shore point walkable at all? (Most of Vesper's canal points have none.) True where there is no map data."""
    try:
        walk = (wr_module or __import__("walkroute")).get()
    except Exception:
        return True
    s = (int(shore[0]), int(shore[1]))
    return any(walk.walkable(s[0] + dx, s[1] + dy) for dx in range(-STAND_RANGE, STAND_RANGE + 1) for dy in range(-STAND_RANGE, STAND_RANGE + 1))


def stand_for(shore, here, wr_module=None):
    """(x, y) of a reachable walkable tile within STAND_RANGE of the shore point, False when none is reachable from `here`, None when there is no map data."""
    try:
        wr = wr_module or __import__("walkroute")
        walk = wr.get()
    except Exception:
        return None
    w = water()
    if w is None:
        return None
    s = (int(shore[0]), int(shore[1]))
    cands = sorted(((cheb((s[0] + dx, s[1] + dy), s), (s[0] + dx, s[1] + dy)) for dx in range(-STAND_RANGE, STAND_RANGE + 1) for dy in range(-STAND_RANGE, STAND_RANGE + 1)
                    if walk.walkable(s[0] + dx, s[1] + dy)), key=lambda t: (cheb(t[1], here), t[0]))
    picked = []
    for _, t in cands:
        if all(cheb(t, p) >= 2 for p in picked):
            picked.append(t)
        if len(picked) >= TRIES:
            break
    best = None
    for t in picked:
        r = walk.plan(here, t)
        if r is not None and cheb(r["path"][-1], t) <= 1 and (best is None or r["steps"] < best[0]):
            best = (r["steps"], t)
    return best[1] if best else False
