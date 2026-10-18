"""A first trip out of Britain (feature "first_trip"): see work/botfarm/patches/patch_first_trip.py for the why. Mixin for HunterBot and CasterBot."""
from __future__ import annotations

import json
import os
import re
import time
import zlib

from ladder import LadderMixin

BRITAIN_CENTER = (1475, 1645)
HARD_KINDS = ("ettin", "ogre", "troll", "corpser", "wisp", "acid elemental", "giant serpent", "gargoyle", "orcish lord", "dragon", "drake", "wyrm",
              "wyvern", "poison elemental", "brigand", "orc lord")

# work/botfarm-watch/first-trip-routes.json (the Helper's survey), the SAFER routes, waypoints at most 40 tiles apart, every one walkable; band = main
# fighting skill, hp = max hit points the survey asks for, stay = minutes at the destination. The way out is allowed steps // 25 minutes (at least 12).
TRIPS = [
    {"id": "britain-gate-walk", "home": "Britain", "vetted": True, "source": "seed", "feature": "first_trip_gate", "dest": "Britain Moongate", "kind": "gate", "band": 0, "hp": 40, "stay": 5,
     "wps": [(1475, 1645), (1448, 1678), (1422, 1715), (1386, 1754), (1375, 1784), (1363, 1824), (1351, 1864), (1347, 1904), (1343, 1944),
             (1343, 1984), (1336, 1997)]},
    {"id": "skara-brae", "home": "Britain", "vetted": True, "source": "seed", "feature": "first_trip_skara", "dest": "Skara Brae", "kind": "town", "band": 50, "hp": 60, "stay": 10,
     "wps": [(1475, 1645), (1446, 1678), (1417, 1715), (1386, 1744), (1360, 1784), (1331, 1824), (1303, 1863), (1269, 1903), (1241, 1943),
             (1219, 1983), (1201, 2023), (1185, 2063), (1163, 2102), (1123, 2132), (1083, 2138), (1043, 2152), (1003, 2156), (963, 2156),
             (923, 2172), (883, 2192), (843, 2219), (811, 2243)]},
    {"id": "trinsic", "home": "Britain", "vetted": True, "source": "seed", "feature": "first_trip_trinsic", "dest": "Trinsic", "kind": "town", "band": 50, "hp": 70, "stay": 15,
     "wps": [(1475, 1645), (1448, 1678), (1422, 1715), (1386, 1754), (1375, 1784), (1374, 1824), (1373, 1864), (1363, 1904), (1355, 1944),
             (1361, 1984), (1395, 2024), (1419, 2064), (1437, 2104), (1465, 2144), (1495, 2162), (1535, 2147), (1575, 2177), (1615, 2207),
             (1655, 2230), (1695, 2264), (1735, 2290), (1769, 2321), (1784, 2359), (1799, 2399), (1804, 2439), (1804, 2479), (1778, 2519),
             (1755, 2559), (1735, 2599), (1759, 2639), (1786, 2679), (1790, 2719), (1790, 2759), (1821, 2770), (1861, 2777), (1901, 2777),
             (1927, 2779)]},
]
GATE = (1397, 1744)         # the SW gate of Britain: every outing leaves by it
# kinds the farm's own fights say beat 30-70 fighters (work/botfarm-watch/creature-danger.md): a bot under SOFT_POWER turns round for them too
SOFT_KINDS = re.compile(r"\b(orcs?|orcish|ratmen|ratman|shades?|lizardmen|lizardman|harpy|harpies|grizzly bears?|gazers?)\b", re.I)
SOFT_POWER = 70
CASTER_EXTRA = 5            # a caster needs this much more skill than a fighter for the same trip
SLICE = 20                  # seconds of walking per tick
REACHED = 8                 # tiles from a waypoint that count as reaching it


def cheb(ax, ay, bx, by):
    return max(abs(ax - bx), abs(ay - by))


def with_gate(wps):
    """The waypoints with the SW gate inserted where it adds the least walking."""
    best = min(range(1, len(wps)), key=lambda i: cheb(*wps[i - 1], *GATE) + cheb(*GATE, *wps[i]) - cheb(*wps[i - 1], *wps[i]))
    return wps[:best] + [GATE] + wps[best:]


for _t in TRIPS:
    _t["wps"] = with_gate(_t["wps"])


def limit_of(trip):
    return max(12, steps_of(trip["wps"]) // 25)


def steps_of(wps):
    return sum(cheb(*wps[i], *wps[i + 1]) for i in range(len(wps) - 1))


def _gz():
    """The gazetteer, or None where it cannot be imported (then first_trip keeps its Britain-only behaviour)."""
    try:
        import gazetteer
        return gazetteer
    except Exception:
        return None


def straight_wps(a, b, step=40):
    """Waypoints every `step` tiles on the line from a to b (both included): the client's planner walks each leg."""
    n = max(1, -(-cheb(a[0], a[1], b[0], b[1]) // step))
    return [(round(a[0] + (b[0] - a[0]) * i / n), round(a[1] + (b[1] - a[1]) * i / n)) for i in range(n)] + [(int(b[0]), int(b[1]))]


_WR = None
_CIRCLES = None
_CIRCLE_PEN = None


def _wr():
    """walkroute, or None where it or its grid cannot be loaded (then trips keep their waypoints)."""
    global _WR
    if _WR is None:
        try:
            import walkroute
            walkroute.get()
            _WR = walkroute
        except Exception:
            _WR = False
    return _WR or None


def _circle_penalty(wr):
    """The penalty of the strong spawners (hardspots.json: x, y, radius, factor), built once per process."""
    global _CIRCLES, _CIRCLE_PEN
    if _CIRCLE_PEN is None:
        try:
            d = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "hardspots.json"), encoding="utf-8"))
            _CIRCLES = [(c["x"], c["y"], c["r"], c["factor"]) for c in d["circles"]]
        except (OSError, ValueError, KeyError):
            _CIRCLES = []
        _CIRCLE_PEN = wr.penalty_circles(_CIRCLES)
    return _CIRCLE_PEN


class FirstTrip(LadderMixin):
    # ---- state: work/botfarm/<bot>/trip.json ------------------------------------------------------------------------------

    def trip_path(self):
        return os.path.join(self.dir, "trip.json")

    def trip_load(self):
        if getattr(self, "_trip", None) is not None:
            return self._trip
        self._trip = {"done": False, "trip": None}
        try:
            self._trip.update(json.load(open(self.trip_path(), encoding="utf-8")))
        except (OSError, ValueError):
            pass
        t = self._trip["trip"]
        if t and not t.get("def"):                         # a trip.json from before the gazetteer: the seed with that destination, else dropped
            seed = next((x for x in TRIPS if x["dest"] == t.get("dest")), None)
            if seed:
                t["def"], t["home"] = dict(seed, vetted=True, source="seed"), "Britain"
            else:
                t = self._trip["trip"] = None
        if t and t.get("phase") in ("out", "stay"):
            self.trip_abort("restart")                   # a new brain does not carry on an outing it did not start
        return self._trip

    def trip_save(self):
        try:
            with open(self.trip_path() + ".tmp", "w", encoding="utf-8") as f:
                json.dump(self._trip, f)
            os.replace(self.trip_path() + ".tmp", self.trip_path())
        except (OSError, TypeError, ValueError):
            pass

    # ---- who goes where ---------------------------------------------------------------------------------------------------

    def trip_power(self):
        if hasattr(self, "main_skill"):
            return self.skill_values.get(self.main_skill(), 0)
        return getattr(self, "skill", 0) - CASTER_EXTRA          # a caster's Magery, held to a stricter band

    def trip_kit_ok(self):
        if hasattr(self, "bandages"):
            yellow = sum((i.amount or 1) for i in self.c.backpack if i.name == "Yellow Potion")
            if self.bandages() < 10 and yellow < 2:
                return False
            return not (getattr(self, "ranged", False) and self.ammo() < 60)
        try:
            return bool(self.can_cast())
        except Exception:
            return False

    def trips_allowed(self, home=None):
        """The trips this bot may take from its home: those it has a per-trip feature for (first_trip_gate | _skara | _trinsic | _explore), else the VETTED
        ones with the plain first_trip feature, else none. The per-trip features stage a rollout (gate walk first) from features.json."""
        home = home or self.trip_home_region()
        if not home:
            return []
        if self.ladder_on():
            return self.ladder_trips(home)                           # the exploration ladder's rungs (ladder.py)
        trips = self.trips_for_home(home)
        own = [t for t in trips if self.feature(t["feature"])]
        return own or ([t for t in trips if t["vetted"]] if self.feature("first_trip") else [])

    def trip_forced(self, home):
        p = os.path.join(self.dir, "trip_now")
        if not os.path.exists(p):
            return None
        try:
            want = open(p, encoding="utf-8").read().strip().lower()
        except OSError:
            return None
        return next((t for t in self.trips_for_home(home) if t["dest"].lower() == want), None)

    def trip_pick(self, home=None):
        """(trip, forced) for a bot that may go now, else (None, False)."""
        home = home or self.trip_home_region()
        if not home or self.c.ghost or self.hp_pct() < 90 or self.mobs(10) or self.c.weight >= self.c.max_weight * 0.7:
            return None, False
        t = self.trip_forced(home)
        if t:
            return t, True
        if getattr(self, "mode", "veteran") != "veteran" or time.time() - self.facts.get("trip_check_at", 0) < 60:
            return None, False
        self.facts["trip_check_at"] = time.time()
        played = (getattr(self, "base", {}).get("uptime", 0) + time.time() - self.started) / 60.0
        if played < 60 or self.c.gold + self.facts.get("bank_balance", 0) < 300 or not self.trip_kit_ok():
            return None, False
        power = self.trip_power()
        ok = [t for t in self.trips_allowed(home) if power >= t["band"] and self.c.max_hp >= t["hp"] and self.trip_ok_route(home, t)]
        if not ok:
            return None, False
        if self.ladder_on():
            return self.ladder_choose(ok), False
        return ok[zlib.crc32(self.name.encode()) % len(ok)], False

    # ---- the rule ---------------------------------------------------------------------------------------------------------

    def r_trip(self):
        st = self.trip_load()
        t = st["trip"]
        if not t:
            if st["done"] and not os.path.exists(os.path.join(self.dir, "trip_now")) and not self.ladder_again():
                return False
            home = self.trip_home_region()
            if not home or not self.trips_allowed(home):
                return False
            trip, forced = self.trip_pick(home)
            if not trip:
                return False
            trip = self.trip_with_exit(home, trip)
            routed = self.trip_routed(home, trip)                    # walkable waypoints, planned once (walkroute)
            if routed is None:
                self.ev("trip_skip", dest=trip["dest"], why="no land route")
                try:
                    os.remove(os.path.join(self.dir, "trip_now"))
                except OSError:
                    pass
                return False
            trip = routed
            try:
                os.remove(os.path.join(self.dir, "trip_now"))
            except OSError:
                pass
            st["trip"] = t = {"dest": trip["dest"], "def": trip, "home": home["name"], "in_home": True, "phase": "out", "i": 0, "t0": time.time(), "deaths0": self.deaths, "fails": 0, "skips": 0,
                              "best": 1e9, "best_at": time.time(), "pos_ev": 0, "stay_until": 0, "t_arrive": 0, "forced": forced}
            self.ev("trip_start", dest=trip["dest"], trip_kind=trip["kind"], home=home["name"], source=trip.get("source", "seed"), vetted=trip.get("vetted", True), route=trip.get("route", "straight"), route_steps=trip.get("route_steps"), route_secs=trip.get("route_secs"),
                    steps=steps_of(trip["wps"]), power=round(self.trip_power(), 1),
                    played_min=int((getattr(self, "base", {}).get("uptime", 0) + time.time() - self.started) / 60), forced=forced)
            self.log(f"first trip: {trip['dest']} ({steps_of(trip['wps'])} steps)")
            self.trip_save()
        if self.deaths > t["deaths0"]:
            self.trip_end("death", completed=False)
            return False
        return self.trip_step(t, self.trip_def(t))

    def trip_abort(self, why):
        """Turn the outing into the walk home (a hard kind near, hurt, too slow...); the walk home itself gives up in trip_step."""
        t = self._trip["trip"]
        if not t or t["phase"] == "home":
            return
        trip = self.trip_def(t)
        self.ev("trip_abort", why=why, at=[self.c.x, self.c.y], dest=t["dest"], phase=t["phase"])
        self.trip_exit_failed(t, why)
        self.log(f"first trip to {t['dest']} aborted ({why}) at {self.c.x},{self.c.y}: walking home")
        t.update(phase="home", i=max(0, min(t["i"] - 1, len(trip["wps"]) - 1)), aborted=why, best=1e9, best_at=time.time(), fails=0, skips=0)   # back from the waypoint behind
        self.trip_save()

    def trip_end(self, how, completed):
        t = self._trip["trip"]
        if how == "death":
            self.ev("trip_abort", why="death", at=[self.c.x, self.c.y], dest=t["dest"], phase=t["phase"])
        elif how == "stranded":
            self.ev("trip_abort", why="stranded", at=[self.c.x, self.c.y], dest=t["dest"], phase=t["phase"])
        else:
            if completed and not t.get("aborted"):
                self.facts["trips_done"] = self.facts.get("trips_done", 0) + 1      # ambition A4 (ambition.py)
            self.ev("trip_home", dest=t["dest"], minutes=round((time.time() - t["t0"]) / 60, 1), hp=self.c.hp,
                    outcome="completed" if completed and not t.get("aborted") else "aborted")
        try:
            self.ladder_trip_end(t, how, completed)
        except Exception as e:
            self.log(f"ladder: {type(e).__name__}: {e}")
        self._trip = {"done": True, "trip": None}
        self.trip_save()

    @staticmethod
    def trip_label(m):
        """Name and body species of a mobile, lower case: a personally named orc (\"Dilug\") is still an Orc, a wraith is a Shade."""
        return f"{m.name} {getattr(m, 'species', None) or ''}".lower()

    @staticmethod
    def trip_desc(m):
        sp = getattr(m, "species", None)
        return f"{m.name} ({sp})" if sp and sp.lower() not in m.name.lower() else m.name

    def trip_soft(self):
        """The group kinds near: under 50 the first one turns the bot round, from 50 a pack of two or more (the owner: the danger is how many)."""
        near = [m for m in self.mobs(12) if SOFT_KINDS.search(self.trip_label(m))]
        if not near or (self.trip_power() >= 50 and len(near) < 2):
            return None
        return self.trip_desc(near[0]) + (f" and {len(near) - 1} more" if len(near) > 1 else "")

    # ---- home, trips and exits from the gazetteer -------------------------------------------------------------------------

    def trip_home_region(self):
        """The town region the bot stands in, or None. Without the gazetteer: Britain when in_britain()."""
        gz = _gz()
        if gz:
            return gz.home_region(self.c.x, self.c.y, ("town",))
        return {"name": "Britain", "centre": [BRITAIN_CENTER[0], BRITAIN_CENTER[1], 0], "rects": []} if self.in_britain() else None

    def trip_def(self, t):
        return t["def"]

    def trips_for_home(self, home):
        """The trips a bot at this home may take (see patch_first_trip_gaz.py): vetted seeds, a gate trip, and town trips."""
        cache = self.__dict__.setdefault("_trip_cache", {})
        if home["name"] in cache:
            return cache[home["name"]]
        out = [dict(t) for t in TRIPS if t.get("home", "Britain") == home["name"]]
        gz = _gz()
        if gz:
            refuges = gz.refuges(home, n=1)
            start = tuple(refuges[0]) if refuges else (home["centre"][0], home["centre"][1])
            side = gz.side(*start)
            if not any(t["kind"] == "gate" for t in out):
                gates = [p for p in gz.near("moongate", start[0], start[1], n=6, same_side=True) if not gz.in_town(p["x"], p["y"])]
                if gates:
                    out.append(self.trip_straight(home, f"{home['name']} Moongate", "gate", start, (gates[0]["x"], gates[0]["y"]), 0, 40, 5, "first_trip_gate"))
            have = {t["dest"] for t in out}
            towns = sorted((r for r in gz.towns() if r["name"] != home["name"] and r["name"] not in have),
                           key=lambda r: cheb(start[0], start[1], r["centre"][0], r["centre"][1]))
            for r in towns:
                end = (r["centre"][0], r["centre"][1])
                if cheb(start[0], start[1], *end) <= 1600 and gz.side(*end) == side:
                    out.append(self.trip_straight(home, r["name"], "town", start, end, 70, 90, 10, "first_trip_explore"))
        cache[home["name"]] = out
        return out

    @staticmethod
    def trip_straight(home, dest, kind, start, end, band, hp, stay, feature):
        return {"id": f"{home['name']}-{dest}".lower().replace(" ", "-"), "feature": feature, "dest": dest, "kind": kind, "band": band, "hp": hp, "stay": stay,
                "wps": straight_wps(start, end), "home": home["name"], "vetted": False, "source": "straight"}

    # ---- walkable routes (walkroute.py): see patch_first_trip_walk.py -----------------------------------------------------------------------

    def trip_penalty(self):
        """The route cost: cells where bots died (shared memory) merged with the strong spawners' circles; the memory part is rebuilt every 10 minutes."""
        wr = _wr()
        got = getattr(self, "_trip_pen", None)
        if got is None or time.time() - got[0] > 600:
            mem = getattr(self, "mem", None)
            try:
                mine = wr.penalty_from_memory(mem) if mem is not None else {}
            except Exception:
                mine = {}
            got = self._trip_pen = (time.time(), wr.penalty_merge(mine, _circle_penalty(wr)))
        return got[1]

    def trip_plan(self, trip):
        """{"wps", "route", "steps"} for a trip: seeds repaired, straight trips planned; wps empty when there is no land route; the trip's own waypoints
        (route "straight") when planning is not possible."""
        wr = _wr()
        wps = [tuple(p) for p in trip["wps"]]
        t0 = time.time()
        try:
            pen = self.trip_penalty()
            if trip.get("source") == "seed":
                new, route = wr.repair(wps, pen), "seed+repair"
            else:
                pts = [wps[0]] + ([tuple(trip["exit"])] if trip.get("exit") else []) + [wps[-1]]
                new, route = [], "planned"
                for a, b in zip(pts, pts[1:]):
                    r = wr.plan(a, b, pen)
                    if r is None:
                        new = None
                        break
                    new.extend(r["waypoints"] if not new else r["waypoints"][1:])          # the first waypoint is the start snapped onto walkable ground
        except Exception as e:
            self.log(f"first trip: planning {trip['dest']} failed ({type(e).__name__}: {e}); keeping its waypoints")
            return {"wps": [list(p) for p in wps], "route": "straight", "steps": steps_of(wps)}
        return {"wps": [list(p) for p in new] if new else [], "route": route if new else "none", "steps": steps_of(new) if new else 0,
                "secs": round(time.time() - t0, 2)}

    def trip_routed(self, home, trip):
        """The trip with walkable waypoints, planned once per (home, destination, exit) and kept in trip.json; None when there is no land route."""
        if _wr() is None:
            return dict(trip, route="straight")
        st = self.trip_load()
        routes = st.setdefault("routes", {})
        key = f"{home['name']}|{trip['dest']}|{','.join(str(v) for v in (trip.get('exit') or []))}"
        r = routes.get(key)
        if r is None:
            r = routes[key] = self.trip_plan(trip)
            self.trip_save()
        if not r["wps"]:
            return None
        return dict(trip, wps=[tuple(p) for p in r["wps"]], route=r["route"], route_steps=r["steps"], route_secs=r.get("secs"))

    def trip_ok_route(self, home, trip):
        """True when the trip has a land route and the routed waypoints pass no cell where bots die."""
        routed = self.trip_routed(home, trip)
        return routed is not None and not self.trip_route_dangerous(routed)

    def trip_route_dangerous(self, trip):
        """An unvetted (straight-line) route that passes a cell where bots have died more than they killed is not taken; vetted seeds were checked offline."""
        mem = getattr(self, "mem", None)
        if mem is None or trip.get("vetted", True):
            return False
        from memory import cell_of
        return any(mem.dangerous_cell(cell_of(x, y)) for x, y in trip["wps"])

    def trip_with_exit(self, home, trip):
        """A straight-line trip with the best learned exit of this home inserted where it costs least; seeds (their gate is in their data) unchanged."""
        if trip.get("source") != "straight" or getattr(self, "mem", None) is None:
            return trip
        from memory import cell_of
        wps = trip["wps"]
        best = None
        for key, r in (self.mem.state["world"]["res"].get("trip_exit") or {}).items():
            h, xy = key.split("|", 1)
            if h != home["name"] or r["fail"] > r["ok"]:
                continue
            x, y = (int(v) for v in xy.split(","))
            if self.mem.dangerous_cell(cell_of(x, y)):
                continue
            i = min(range(1, len(wps)), key=lambda i: cheb(*wps[i - 1], x, y) + cheb(x, y, *wps[i]) - cheb(*wps[i - 1], *wps[i]))
            cost = cheb(*wps[i - 1], x, y) + cheb(x, y, *wps[i]) - cheb(*wps[i - 1], *wps[i]) + 150 * r["fail"] - 20 * min(r["ok"], 5)
            if best is None or cost < best[0]:
                best = (cost, i, (x, y))
        if not best:
            return trip
        return dict(trip, wps=wps[:best[1]] + [best[2]] + wps[best[1]:], exit=list(best[2]))

    def trip_exit_seen(self, t):
        """The bot has just left its home region on a trip: remember where."""
        key = f"{t['home']}|{self.c.x // 8 * 8},{self.c.y // 8 * 8}"
        t["exit_key"] = key
        if getattr(self, "mem", None) is not None:
            self.mem.record("res", kind="trip_exit", key=key, ok=True)
        self.ev("trip_exit", home=t["home"], at=[self.c.x, self.c.y])

    def trip_exit_failed(self, t, why):
        key = t.get("exit_key")
        if key and t["phase"] == "out" and why != "restart":
            x, y = (int(v) for v in key.split("|", 1)[1].split(","))
            if cheb(self.c.x, self.c.y, x, y) <= 80 and getattr(self, "mem", None) is not None:
                self.mem.record("res", kind="trip_exit", key=key, ok=False, reason=str(why)[:60])

    def trip_look(self):
        """The ground items around, for the arrival event: range 8, then 12; errors logged, raw `items` lines kept when nothing parses."""
        out = {"items": [], "raw": [], "err": None, "range": 0}
        for rng in (8, 12):
            out["range"] = rng
            try:
                if hasattr(self, "ground_items"):
                    out["items"] = [i.name for i in self.ground_items(rng)]
                if not out["items"]:
                    out["raw"] = [str(l).strip()[:100] for l in self.c.call(f"items {rng}", timeout=8)][:6]
            except Exception as e:
                out["err"] = f"{type(e).__name__}: {e}"[:120]
                self.log(f"first trip: the item look (items {rng}) failed: {out['err']}")
            if out["items"]:
                break
        return out

    def trip_danger(self):
        """Feature danger_model: the first hostile within 12 tiles whose learned risk (danger.py: its kind, this skill band, the pack around it) is not
        acceptable for a trip, described; else None."""
        import re as _re
        import danger
        mobs = sorted(self.mobs(12), key=lambda m: m.distance)
        skill = self.trip_power()
        for m in mobs:
            kind = _re.sub(r"[^a-z]", "", (getattr(m, "species", None) or _re.sub(r"^(an?|the) ", "", m.name.lower())).lower())
            near = sum(1 for o in mobs if o is not m and max(abs(o.x - m.x), abs(o.y - m.y)) <= 10)
            r = danger.risk(self.mem, kind, skill, near)
            if not danger.acceptable(r, "trip"):
                return f"{self.trip_desc(m)} (die {r['die']:.0%}, flee {r['flee']:.0%}, n {r['n']:.0f}, pack {near})"
        return None

    def trip_step(self, t, trip):
        wps = trip["wps"]
        now = time.time()
        if now - t["pos_ev"] > 120:
            t["pos_ev"] = now
            self.ev("trip_pos", dest=t["dest"], phase=t["phase"], wp=t["i"], of=len(wps), left_to_dest=cheb(self.c.x, self.c.y, *wps[-1]))
        phase = t["phase"]
        if phase == "out" and t.get("in_home", True) and _gz():
            home_now = _gz().home_region(self.c.x, self.c.y, ("town",))
            if not (home_now and home_now["name"] == t["home"]):
                t["in_home"] = False
                self.trip_exit_seen(t)
        if phase in ("out", "stay"):
            if self.feature("danger_model"):
                hard, soft, danger = None, None, self.trip_danger()                       # learned risk instead of the kind lists
            else:
                hard = next((self.trip_desc(m) for m in self.mobs(12) if any(k in self.trip_label(m) for k in HARD_KINDS)), None)
                soft = None if hard or self.trip_power() >= SOFT_POWER else self.trip_soft()
                danger = None
            why = ("hurt" if self.hp_pct() < 60 else f"danger: {danger}" if danger else f"hard kind: {hard}" if hard else f"soft kind: {soft}" if soft else "overweight" if self.c.weight >= self.c.max_weight * 0.9
                   else "too slow" if phase == "out" and now - t["t0"] > limit_of(trip) * 60 else None)
            if why:
                self.trip_abort(why)
                return True
        if phase == "stay":
            self.activity = f"looking around {t['dest']}"
            if now >= t["stay_until"]:
                t.update(phase="home", i=len(wps) - 1, best=1e9, best_at=now, fails=0, skips=0)
                self.trip_save()
            else:
                time.sleep(3)
            return True
        # a walk (out along the waypoints, home along them reversed): one slice per tick
        idx = t["i"]
        x, y = wps[idx]
        d = cheb(self.c.x, self.c.y, x, y)
        if d <= REACHED:
            if phase == "out":
                if idx >= len(wps) - 1:
                    others = [m for m in self.c.mobiles(within=20) if m.notoriety == "Innocent" and m.name and not m.name.startswith("Bot")]
                    look = self.trip_look()
                    items = look["items"]
                    self.ev("trip_arrive", dest=t["dest"], minutes=round((now - t["t0"]) / 60, 1), innocents=len(others),
                            humans=sorted({m.name for m in others if getattr(m, "is_human", False)})[:8],
                            gate_seen=any("gate" in n.lower() for n in items), items=sorted(set(items))[:12],
                            items_raw=look["raw"], look_err=look["err"], look_range=look["range"])
                    self.log(f"first trip: arrived at {t['dest']}; {len(others)} innocents in view")
                    try:
                        self.ladder_arrive(t, trip)                    # a dungeon trip steps through the door (ladder.py)
                    except Exception as e:
                        self.log(f"ladder: {type(e).__name__}: {e}")
                    t.update(phase="stay", stay_until=now + (0 if t.get("enter_failed") else trip["stay"] * 60), t_arrive=now)
                    self.trip_save()
                    return True
                t.update(i=idx + 1, best=1e9, best_at=now, fails=0)
            else:
                if idx <= 0:
                    self.trip_end("home", completed=True)
                    return True
                t.update(i=idx - 1, best=1e9, best_at=now, fails=0)
            self.trip_save()
            return True
        if d < t["best"] - 5:
            t["best"], t["best_at"] = d, now
        elif now - t["best_at"] > 300:
            if phase == "home":
                self.trip_end("stranded", completed=False)               # no way home along the route: the normal rules take over
                return False
            self.trip_abort("no progress")
            return True
        self.activity = f"first trip: {'to' if phase == 'out' else 'home from'} {t['dest']}"
        res = str(self.goto_near(x, y, REACHED).wait(timeout=SLICE))
        if res.startswith(("nopath", "blocked")):
            t["fails"] += 1
            if t["fails"] >= 3:
                t["skips"] += 1
                if t["skips"] > 1:
                    if phase == "home":
                        self.trip_end("stranded", completed=False)
                        return False
                    self.trip_abort("nopath")
                    return True
                t.update(i=idx + (1 if phase == "out" else -1), best=1e9, best_at=now, fails=0)       # one waypoint may be skipped
                t["i"] = max(0, min(t["i"], len(wps) - 1))
        return True
