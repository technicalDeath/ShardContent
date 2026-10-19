"""Where services and fixtures are, by role (generality step 2): see work/botfarm/patches/patch_places.py. Mixin Places for the brains."""
from __future__ import annotations

import json
import math
import os
import time

try:
    import gazetteer as gz
except Exception:                      # the data missing: FALLBACK below is all there is
    gz = None

SAME = 6                               # tiles: two answers this close are one place
REFERENCE_SIDE = "surface"

# the ONE table of Britain coordinates left in the brains' service lookups: used only where the gazetteer cannot be imported
FALLBACK = {"smith": (1418, 1550), "weaponsmith": (1481, 1584), "armorer": (1481, 1584), "cobbler": (1469, 1668), "tinker": (1427, 1652), "tailor": (1467, 1688),
            "weaver": (1467, 1688), "carpenter": (1430, 1599), "butcher": (1449, 1723), "bowyer": (1470, 1579), "healer": (1472, 1613), "dummy": (1589, 1554),
            "butte": (1468, 1579), "forge": (1424, 1558), "anvil": (1423, 1556), "bank": (1425, 1690), "mage": (1485, 1553)}
FALLBACK_SPOTS = {"dummy": [(1589, 1554), (1528, 1431)], "butte": [(1468, 1579)]}
# vermin ground near home that was picked by hand (a broke tailor once walked to Britain's north-east edge for coins and met a gargoyle)
SEED_EARN = {"Britain": [(1300, 1800), (1340, 1720), (1360, 1760)]}
# Britain's patrol points (hunter.SPOTS): the spawners of its beginner and step-up hunting areas (britain_areas.json, make_britain_areas.py; the 2026-10-18
# spawn redo, patch_britain_areas.py); another home gets learned cells and a ring (Places.patrol_spots). OLD_SPOTS: the hand-picked ten of 2026-10-14,
# used only when the file is missing.
OLD_SPOTS = [(1380, 1560), (1300, 1520), (1260, 1495), (1450, 1450), (1600, 1500), (1650, 1700), (1450, 1850), (1330, 1650), (1530, 1520), (1560, 1650)]
AREA_TIERS = (1, 2)
PER_AREA = 3


def area_spots(path=None, tiers=AREA_TIERS, per_area=PER_AREA, apart=40):
    """[(x, y)] patrol points from britain_areas.json: each area's middle spawner first, then others at least `apart` tiles from those taken."""
    try:
        d = json.load(open(path or os.path.join(os.path.dirname(os.path.abspath(__file__)), "britain_areas.json"), encoding="utf-8"))
    except (OSError, ValueError):
        return []
    out = []
    for a in d.get("areas", []):
        if a.get("tier") not in tiers:
            continue
        taken = [tuple(a["spot"])]
        for sp in sorted(a.get("spawners", []), key=lambda s: (s[0], s[1])):
            if len(taken) >= per_area:
                break
            if all(max(abs(sp[0] - x), abs(sp[1] - y)) >= apart for x, y in taken):
                taken.append((sp[0], sp[1]))
        out += taken
    return out


SEED_SPOTS = {"Britain": area_spots() or OLD_SPOTS}
FALLBACK_BANKS = [(1425, 1690), (1650, 1608)]
RING_RADII = (90, 180)
VERMIN = ("cow", "chicken", "sheep", "rat", "rabbit", "hind", "pig", "goat", "bird", "giantrat", "sewerrat", "bullfrog", "snake")


def _d(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def dedupe(points, within=SAME):
    out = []
    for p in points:
        if all(_d(p, q) > within for q in out):
            out.append(p)
    return out


class Places:
    def places_ref(self, near=None):
        """Where "nearest" is measured from: `near`, else the bot's position when it stands on the surface, else the home centre."""
        if near is not None:
            return (int(near[0]), int(near[1]))
        x, y = self.c.x, self.c.y
        if gz is None or gz.side(x, y) == REFERENCE_SIDE:
            return (int(x), int(y))
        home = getattr(self, "home_centre", None)
        return home() if home else (int(x), int(y))

    def find_places(self, roles, item=None, mode="sell", near=None, n=3, per=2):
        """Standing spots for a service, best first (see patch_places.py): learned vendors for `item` first, then the gazetteer by tiers of roles."""
        ref = self.places_ref(near)
        tiers = [roles] if isinstance(roles, str) else list(roles)
        out = []
        mem = getattr(self, "mem", None)
        if item and mem is not None:
            try:
                rows = mem.vendor_selling(item) if mode == "sell" else mem.vendor_buying(item)
            except Exception:
                rows = []
            learned = []
            for r in rows:
                if r[0] > 0:
                    learned.append(tuple(int(v) for v in r[1].split(",")))
            out += sorted(dict.fromkeys(learned), key=lambda p: _d(p, ref))
        if gz is None:
            for t in tiers:
                for role in ((t,) if isinstance(t, str) else t):
                    if role in FALLBACK:
                        out.append(FALLBACK[role])
        else:
            for t in tiers:
                names = (t,) if isinstance(t, str) else tuple(t)
                found = dedupe([(p["x"], p["y"]) for p in gz.near(names, ref[0], ref[1], n=(per or n) + 6, same_side=True)])
                out += found[:per] if per else found
        return dedupe(out)[:n]

    def where1(self, roles, default=None, **kw):
        w = self.find_places(roles, n=1, **kw)
        if w:
            return w[0]
        if default is not None:
            return default
        home = getattr(self, "home_centre", None)
        return home() if home else self.places_ref()

    def spots_for(self, role, n=2, apart=12, near=None):
        """n fixtures of a role (training dummies, archery buttes), nearest first, no two closer than `apart` tiles."""
        ref = self.places_ref(near)
        if gz is None:
            return list(FALLBACK_SPOTS.get(role, []))[:n]
        out = []
        for p in gz.near(role, ref[0], ref[1], n=60, same_side=True):
            q = (p["x"], p["y"])
            if all(_d(q, o) >= apart for o in out):
                out.append(q)
            if len(out) >= n:
                break
        return out

    def station_near(self, role, near=None):
        """A tile between the forge and the anvil nearest the nearest `role` vendor (the smithy), or None when the world has no forge."""
        ref = self.places_ref(near)
        anchor = self.where1(role, near=ref, default=ref)
        if gz is None:
            return (FALLBACK["forge"][0] + FALLBACK["anvil"][0]) // 2, (FALLBACK["forge"][1] + FALLBACK["anvil"][1]) // 2
        forges = gz.near("forge", anchor[0], anchor[1], n=8, same_side=True)
        anvils = gz.near("anvil", anchor[0], anchor[1], n=12, same_side=True)
        best = None
        for f in forges:
            for a in anvils:
                gap = _d((f["x"], f["y"]), (a["x"], a["y"]))
                if gap <= 6:
                    cost = _d(anchor, (f["x"], f["y"])) + gap
                    if best is None or cost < best[0]:
                        best = (cost, f, a)
        if best:
            return (best[1]["x"] + best[2]["x"]) // 2, (best[1]["y"] + best[2]["y"]) // 2
        return (forges[0]["x"], forges[0]["y"]) if forges else None

    def earn_spots(self):
        """Vermin ground near home for a broke crafter: seeds for a home that has them, else learned cells, else the home centre."""
        home = getattr(self, "home", None)
        h = home() if home else None
        name = h["name"] if h else None
        if name in SEED_EARN:
            return list(SEED_EARN[name])
        centre = self.home_centre() if getattr(self, "home_centre", None) else self.places_ref()
        mem = getattr(self, "mem", None)
        if mem is None:
            return [centre]
        try:
            from memory import cell_center
            core = self.home_core() if getattr(self, "home_core", None) else (centre[0] - 60, centre[1] - 60, centre[0] + 60, centre[1] + 60)
            mem.refresh()
            scored = []
            for cell, c in mem.state["world"]["cells"].items():
                x, y = cell_center(cell)
                if _d((x, y), centre) > 150 or (core[0] <= x <= core[2] and core[1] <= y <= core[3]):
                    continue
                if mem.dangerous_cell(cell) or mem.camp_cell(cell):
                    continue
                vermin = sum(n for k, n in c["sights"].items() if any(v in k for v in VERMIN))
                other = sum(n for k, n in c["sights"].items() if not any(v in k for v in VERMIN))
                if vermin >= 3 and other <= vermin:
                    scored.append((vermin - _d((x, y), centre) / 20.0, (x, y)))
            scored.sort(reverse=True)
            return [p for _, p in scored[:3]] or [centre]
        except Exception:
            return [centre]

    # ---- bank, healer, meeting point, forge, mage shop, patrol spots ---------------------------------------------------------------

    def healer_xy(self):
        """The nearest healer to where the bot is (a ghost's walk); measured from home when it is underground."""
        return self.where1(("healer",))

    def bank_xys(self):
        """Banks, nearest first."""
        if gz is None:
            ref = self.places_ref()
            return sorted(FALLBACK_BANKS, key=lambda p: _d(p, ref))
        return self.find_places(("bank",), n=4, per=4) or [self.where1(("bank",))]

    def meet_spot(self):
        """Where a home's market deals are done: two tiles off the bank nearest the home centre (the same for every bot of the home)."""
        home = self.home_centre() if getattr(self, "home_centre", None) else self.places_ref()
        banks = self.find_places(("bank",), n=1, near=home)
        b = banks[0] if banks else home
        return (b[0] + 2, b[1] + 2)

    def forge_xy(self, near=None):
        """The forge nearest the nearest smith (the smithy), for smelting."""
        ref = self.places_ref(near)
        if gz is None:
            return FALLBACK["forge"]
        anchor = self.where1(("smith",), near=ref, default=ref)
        f = gz.near("forge", anchor[0], anchor[1], n=1, same_side=True)
        return (f[0]["x"], f[0]["y"]) if f else self.where1(("smith",), near=ref, default=ref)

    def mage_shop_xy(self):
        """The Mages Guild shop: reagents, and the guildmaster r_train asks (the nearest guildmaster, else the nearest mage)."""
        return self.where1(("mage_guildmaster", "mage"))

    def town_xy(self):
        """A safe standing spot in the home town: its first refuge."""
        r = self.home_refuges() if getattr(self, "home_refuges", None) else []
        return tuple(r[0]) if r else self.where1(("healer",))

    def patrol_spots(self):
        """The fixed patrol points of a home: its seeds (Britain's ten), else the memory's best hunting cells and a ring around the home centre."""
        hit = self.__dict__.get("_patrol")
        if hit and time.time() - hit[0] < 600:
            return hit[1]
        h = self.home() if getattr(self, "home", None) else None
        name = h["name"] if h else None
        if name in SEED_SPOTS or (h is None and gz is None):
            spots = list(SEED_SPOTS.get(name, SEED_SPOTS["Britain"]))
        else:
            centre = self.home_centre() if getattr(self, "home_centre", None) else self.places_ref()
            learned = []
            mem = getattr(self, "mem", None)
            if mem is not None:
                try:
                    from memory import cell_center
                    learned = [cell_center(cell) for score, cell in mem.hunting_cells(near=centre, radius=300, n=8) if score > 0.25]
                except Exception:
                    learned = []
            ring = [(int(centre[0] + r * math.cos(k * math.pi / 8)), int(centre[1] + r * math.sin(k * math.pi / 8))) for r in RING_RADII for k in range(16)]
            spots = dedupe(learned + ring, within=30)
        self._patrol = (time.time(), spots)
        return spots
