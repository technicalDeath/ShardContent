"""A first trip out of Britain (feature "first_trip"): see work/botfarm/patches/patch_first_trip.py for the why. Mixin for HunterBot and CasterBot."""
from __future__ import annotations

import items  # noqa: E402  (the shared item table)
import basics  # noqa: E402  (shared helpers)
import json
import os
import re
import time
import zlib

from ladder import LadderMixin
from ride import RideMixin

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
# feature trip_run (owner, 2026-11-02: "Cant they run past the monsters and keep a distance from them", and "drinking any necessary potion on the run").
# A running player takes 0.2 s a tile (movement.delay.runFoot 200); the monsters on the routes out of Britain take 0.3-0.6 (npc-speeds.json: air elemental
# Fast 0.3; bone mage, gazer, reaper, corpser, ratman, orc Medium 0.45; earth elemental Slow 0.6), so a runner outpaces every one of them. The trip deaths
# of 2026-11-02 were bots that stopped: one bandaged (an 11.8 s bandage) beside a bone mage, one at 66 of 81 among spectres, wraiths and a bone mage.
TRIP_HOT = 14               # tiles: a monster's notice range here (BaseCreature.DefaultRangePerception 16 less monsterAggro.rangeReduction 2, task_core.PULL_CLEAR)
TRIP_HOT_SLICE = 2          # s of walking per tick with a monster in notice range: the danger check and the potions come round every 2 s, not every 20
TRIP_HOLD = ("r_heal", "r_cure", "r_fight", "r_avoid", "r_flee", "r_hide", "r_rest", "r_loot", "r_corpse", "r_carve")   # rules that stand still
HEAL_MISSING = 20           # a pre-AOS Heal potion restores 6-20 (HealPotion.cs MinHeal/MaxHeal): drunk on the run once 20 are missing, so none is wasted
RUN_STAM = 0.5              # a Refresh (+25% of the maximum, RefreshPotion.cs) on the run below half stamina, where Navrey's "auto" would drop to a walk
TRIP_PACK = 3               # this many dangers in notice range turn the trip back, whatever their kind
TRIP_RESUME_S = 300          # a trip saved this recently is resumed by a new brain: today's rollover gaps reached 161 s and LEAVE_GRACE runs 120 s on
DUNGEON_HUNT_S = 2400        # s a dungeon trip hunts inside (feature dungeon_hunt): two of the core's hunt budgets (task_core.HUNT_BUDGET 1200), so the hunt
                             # pays at least the walk there and back (Covetous: 8-10 min each way, 2026-11-03/04)
RETREAT_NEAR = 4             # tiles: a pack this close (detour.PACK of them) sends a dungeon hunter through the stair (r_dungeon_out)
RETREAT_REACH = 80           # tiles to the stair at most: at a run (0.2 s a tile on foot, 0.1 mounted) against a Medium chaser's 0.45 the bot gains 2.8 tiles a
                             # second, so 80 tiles is 16-8 s of running with the pack falling behind; Despise's farthest lizardman spawner is ~120 from its stair
RETREAT_SEE = 16             # tiles: a monster in war mode this near has noticed the bot (BaseCreature.DefaultRangePerception 16) and is coming; two or
                             # more that rate a lost fight send it to the stair before they arrive (r_dungeon_out), not at RETREAT_NEAR when it is boxed in
RETREAT_LINE = 2             # tiles from the straight line to a stair at which a monster stands in the way (trip_stair_near)
RETREAT_GAP = 30             # s between retreats (a pack waiting on the far side of the landing does not bounce the bot)
LEFT_INSIDE_GAP = 120        # s between tries at leaving a dungeon with no trip under way (trip_left_inside): tele_to_side tries 150 s itself
RETURN_S = 300               # s the stairs back to a dungeon's landing may take (trip_return_leg): Despise's farthest lizardman spawner is ~120 tiles from
                             # its stair (24 s at a run, Movement.cs runFoot 200 ms), so the cap leaves room for fights on the way
STAY_SAVE_S = 60             # s between the stay's saves: well inside TRIP_RESUME_S
DUNGEON_PURSE = 50          # gold a dungeon trip may carry: visit_bank puts in only what is over its reserve + 50
ESCAPE_HOLD_N = 4            # escapes within ESCAPE_HOLD_S on the way out that turn a trip back: BotArchAdvR ran 15 escape and detour legs in 2 minutes
ESCAPE_HOLD_S = 60.0         # in a camp astride the Trinsic road before it died (2026-11-04 04:06-04:08); a clean pass of a pocket takes one or two
TRIP_CASTERS = 2           # this many casters in notice range at once turn the trip back; one is run past out of its spell range (detour.py)
PASS_TILES = 40              # tiles of the route ahead (and behind) a pass past casters is costed over: twice a spell's range (casterpass.SPELL_RANGE),
                             # in and out of the reach of a caster beside the road


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


DH_CUT_S = 300                 # a dungeon hunt that ends out of the dungeon sooner than this was cut short by the bot's own walk, not a visit: the ladder
                               # counts it neither passed nor failed (BotHealAdvR, out again 3 s after entering Despise, 2026-11-05 06:03)


def _gz():
    """The gazetteer, or None where it cannot be imported (then first_trip keeps its Britain-only behaviour)."""
    try:
        import gazetteer
        return gazetteer
    except Exception:
        return None


def dense_path(wps):
    """Every tile along the waypoints (route_danger samples a path, and trip waypoints are 40 tiles apart)."""
    out = []
    for (ax, ay), (bx, by) in zip(wps, wps[1:]):
        n = max(abs(bx - ax), abs(by - ay), 1)
        out.extend((ax + (bx - ax) * i // n, ay + (by - ay) * i // n) for i in range(n))
    return out + [tuple(wps[-1])] if wps else out


# kinds that cannot walk (CantWalk = true: DeepSeaSerpent.cs, SeaSerpent.cs, Kraken.cs, Dolphin.cs; Spawns/SeaLife.json): a spawner of them off the coast
# is no danger to a walk on land, yet one at 3520,2263 refused every Magincia trip by its gate (2026-11-06 03:30). WaterElemental can walk: not here.
WATER_ONLY = ("deepseaserpent", "seaserpent", "kraken", "dolphin")
ENDS_FREE = 25          # tiles at each end of a trip's path left out of trip_threat: a destination (Britain's moongate at 1336,1997 beside Haunted Wood) is gone to anyway
AVOID_TRIES = 4          # re-plans of a trip round the cells route_danger flags before the trip is refused
AVOID_FACTOR = 50.0      # the cost a flagged cell's tiles get in that re-plan: high enough that any way round wins
RUN_EDGE = 0            # (14 from 14:48 to 15:4x while the escape was fixed; owner: survive by skill, not by avoiding) tiles past a caster lair's home range a running trip keeps clear (owner 2026-11-03, "Run past gargoyle edge"): every route from
                        # Britain to Covetous passes the gargoyles at 1906,1336 or the North-west Peaks' air elementals within their home range + 14


def straight_wps(a, b, step=40):
    """Waypoints every `step` tiles on the line from a to b (both included): the client's planner walks each leg."""
    n = max(1, -(-cheb(a[0], a[1], b[0], b[1]) // step))
    return [(round(a[0] + (b[0] - a[0]) * i / n), round(a[1] + (b[1] - a[1]) * i / n)) for i in range(n)] + [(int(b[0]), int(b[1]))]


_CIRCLES = None
_CIRCLE_PEN = None


_wr = basics.walkroute_mod                   # (basics.py: one copy, one loaded grid)


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


def seg_dist(a, b, p):
    """Chebyshev-style distance from point p to the segment a-b (tiles): how far p stands off the straight run from a to b."""
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    n = dx * dx + dy * dy
    u = 0.0 if n == 0 else max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / n))
    return max(abs(p[0] - (ax + u * dx)), abs(p[1] - (ay + u * dy)))


ROUTE_V = "fp3"                  # the route cache version: bumped when the route penalty changes (fp2, 2026-11-02: re-planned round route_danger's cells, trip_avoid)

class FirstTrip(RideMixin, LadderMixin):
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
        if t and float((getattr(self, "facts", None) or {}).get("died_at") or 0) > float(t.get("t0") or 0):
            # died since the trip began, under a brain that never closed it: BotRangerAR died at the Despise door with its trip suspended (15:15), and
            # 70 minutes later a new brain resumed its home leg at waypoint 37 from Britain's healer, back out onto the troll road (2026-11-08 16:25)
            self.trip_end("death", completed=False)
            t = self._trip["trip"]
        if t and t.get("phase") in ("out", "stay", "home"):
            age = time.time() - float(self._trip.get("saved_at") or 0)
            if age <= TRIP_RESUME_S and not getattr(self.c, "ghost", False):
                # a restart (a rollover, a safe restart) a moment ago: the character is where the last brain left it, so the trip goes on. Aborted,
                # BotFairSwordVR's trips ended at Vesper itself and by the gazer pocket (2026-11-03 15:20, 13:48), each a trip lost
                t.update(best=1e9, best_at=time.time(), fails=0, deaths0=getattr(self, "deaths", 0))
                self.log(f"first trip: resumed to {t.get('dest')} after a restart ({age:.0f} s since the last brain saved it)")
            elif t["phase"] == "home":
                t["aborted"] = "restart"                 # an old walk home is not carried on either (trip_abort leaves a home leg as it is): the bot is
                self.trip_end("restart", completed=False)   # wherever the last brain left it, and the core takes it home from there (not counted)
            else:
                self.trip_abort("restart")               # an old outing (the brain was down a while) is not carried on
        return self._trip

    def trip_save(self):
        self._trip["saved_at"] = time.time()            # (trip_load resumes an outing saved within TRIP_RESUME_S)
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
            yellow = sum((i.amount or 1) for i in self.c.backpack if items.potion_kind(i.name) == "heal")
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
        return own or ([t for t in trips if t["vetted"] and not t.get("gate")] if self.feature("first_trip") else [])      # (a gate trip only with gate_travel)

    def trip_forced(self, home):
        p = os.path.join(self.dir, "trip_now")
        if not os.path.exists(p):
            return None
        try:
            want = open(p, encoding="utf-8").read().strip().lower()
        except OSError:
            return None
        return next((t for t in self.trips_for_home(home) if t["dest"].lower() == want), None)

    def trip_busy(self):
        """Something near that stops a trip from starting: under trip_run only what can hurt it (basics.threats: an attack-on-sight kind or anything in war
        mode), as a player sets out with deer and bears about; otherwise any mobile within 10. With any mobile, 16 restarted ladder fighters started no
        trip and logged no refusal in 30 minutes (hunting, and Britain's bears in town), 2026-11-02 09:52-10:21."""
        try:
            if not self.trip_run_on():
                return bool(self.mobs(10))
            import detour
            here = (int(self.c.x), int(self.c.y))
            # its dangers (hunter.dangers: not its prey, not a passive animal), as the detours see them: threats() holds anything in war mode, and the
            # animals a ladder fighter hunts by town are in war mode with it, so a rabbit at 3, a goat at 1 and a chicken at 2 kept BotRangerBR in Britain
            # (2026-11-03 22:00-22:12)
            near = self.dangers(10) if hasattr(self, "dangers") else self.threats(10)
            for m in near:
                th = detour.Threat(int(m.x), int(m.y), bool(self.trip_caster(self.mkey(m))), getattr(m, "name", "") or "", detour.poisons(self.mkey(m)))
                if detour.clearance_at(here, [th]) < 0:
                    # inside its reach (a caster's spell range + 2, a melee monster's MELEE_CLEAR): wait. Further off, a runner sets out and runs past it
                    # (trip_detour), as a player does: 'a threat near' was the first refusal in town, 72-140 times a day for BotSwordBR, BotMaceCR,
                    # BotFencerBR and BotRangerBR, four fighters at 94-100 that never once set out (2026-11-03)
                    self.__dict__["_busy_by"] = f"{th.name} at {detour.cheb(here, (th.x, th.y))}"
                    return True
            return False
        except Exception:
            return True

    def trip_pick(self, home=None):
        """(trip, forced) for a bot that may go now, else (None, False)."""
        home = home or self.trip_home_region()
        busy = self.trip_busy()
        if not home or self.c.ghost or self.hp_pct() < 90 or busy or self.c.weight >= self.c.max_weight * 0.7:
            return self.trip_why("not in town" if not home else "a ghost" if self.c.ghost else f"hp {self.hp_pct()}% (90 needed)" if self.hp_pct() < 90
                                 else f"a threat near ({self.__dict__.get('_busy_by', '?')})" if busy else f"pack {self.c.weight}/{self.c.max_weight} (under 70% needed)"), False
        t = self.trip_forced(home)
        if t:
            return t, True
        # newbie mode (the newbie memory folder) keeps a plain first trip a veteran's, not the ladder's trips: its rungs gate on skill, health, kit and
        # gold. BotMaceCR, BotSwordBR and BotFencerBR (A4 adventurers, skill 100, 140,000+ gold banked) passed rungs 1 and 2 on 2026-11-01 and never set
        # out: 0 town trips, so never Despise (owner, 2026-11-07: "I want the bots going dungeoneering")
        if (getattr(self, "mode", "veteran") != "veteran" and not self.ladder_on()) or time.time() - self.facts.get("trip_check_at", 0) < 60:
            return None, False
        self.facts["trip_check_at"] = time.time()
        played = (getattr(self, "base", {}).get("uptime", 0) + time.time() - self.started) / 60.0
        if played < 60 or self.c.gold + self.facts.get("bank_balance", 0) < 300 or not self.trip_kit_ok():
            return self.trip_why("played under an hour" if played < 60 else "under 300 gold" if self.c.gold + self.facts.get("bank_balance", 0) < 300
                                 else "no kit (10 bandages or 2 Heal potions; 60 arrows for a bow)"), False
        power = self.trip_power()
        allowed = self.trips_allowed(home)
        ok = [t for t in allowed if power >= t["band"] and self.c.max_hp >= t["hp"] and self.trip_ok_route(home, t)]
        if not ok:
            # which check, per trip: the line alone hid it for the casters' Despise trips (2026-11-09 00:25-00:52)
            why = "; ".join(f"{t['dest']}: " + (f"skill {power:.0f} under {t['band']}" if power < t["band"] else f"hp {self.c.max_hp} under {t['hp']}"
                            if self.c.max_hp < t["hp"] else "no land route" if self.trip_routed(home, t) is None else "the route crosses a dangerous cell")
                            for t in allowed[:3]) or "none offered"
            return self.trip_why(f"no trip passes the skill, health and route checks ({why})"), False
        if self.ladder_on():
            return self.ladder_choose(ok), False
        return ok[zlib.crc32(self.name.encode()) % len(ok)], False

    # ---- the rule ---------------------------------------------------------------------------------------------------------

    TRIP_WHY_EVERY = 300       # s between "first trip: not now" lines

    def trip_why(self, why):
        """Why a ladder bot due a trip did not set out, logged and recorded (event trip_wait) at most every TRIP_WHY_EVERY s. 16 ladder fighters started
        no trip and logged nothing for an hour (2026-11-02 09:52-11:10): the gates were silent. Returns None."""
        now = time.time()
        if now - self.__dict__.get("_trip_why_at", 0) >= self.TRIP_WHY_EVERY or why != self.__dict__.get("_trip_why"):
            if now - self.__dict__.get("_trip_why_at", 0) >= 60:
                self.__dict__["_trip_why_at"], self.__dict__["_trip_why"] = now, why
                try:
                    self.log(f"first trip: not now: {why}")
                    self.ev("trip_wait", why=why)
                except Exception:
                    pass
        return None

    def trip_core_lets(self, name):
        """Under the decision core (task_core) only the reflexes run, so a ladder bot's r_trip never did (2026-11-01: three of the four ladder bots run the core).
        A ladder bot keeps r_trip, and r_fight while a trip is under way: the order a bot without the core has (the outing waits behind fights)."""
        under_way = bool(self.trip_load().get("trip"))
        if name == "r_trip":
            # a trip under way is finished whatever the features say now: BotRangerAR, walking home from Despise, lost ladder_dungeon by a features
            # change at the door camp, the core took over there with nothing open to hunt, and a troll killed it standing (2026-11-08 15:14-15:15)
            return self.ladder_on() or under_way
        if name == "r_ride":
            return self.ride_on()                                   # riding (ride.py) under the core too
        if name == "r_dungeon_out":
            return bool(self.facts.get("dungeon_hunt"))            # a dungeon hunt's way out of a pack (r_dungeon_out), ahead of r_flee
        if name == "r_loot":
            # in a dungeon the kills are r_fight's (the pack comes to the bot), and the hunt tree loots only its own target: BotHealAdvR's two Despise stays
            # made 103 kills and brought home about 63 gold, the pack at 133 stones from entry to exit (2026-11-05/06). r_loot stands aside while a hostile
            # is within 7 tiles, so it loots between fights, never instead of one
            return bool(self.facts.get("dungeon_hunt"))

        if name == "r_fight":
            return under_way
        return False

    def r_trip(self):
        st = self.trip_load()
        t = st["trip"]
        if not t and self.ladder_on() and self.trip_left_inside():
            return True
        if not t:
            if st["done"] and not os.path.exists(os.path.join(self.dir, "trip_now")) and not self.ladder_again():
                return False
            home = self.trip_home_region()
            if not home or (not self.trips_allowed(home) and not self.trip_forced(home)):
                self.trip_why("not in town" if not home else "the ladder offers no trip now")
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
            if (trip.get("kind") == "dungeon" and int(self.c.gold or 0) > DUNGEON_PURSE and hasattr(self, "visit_bank")
                    and time.time() - self.__dict__.get("_dungeon_banked_at", 0) > 600):
                # gold has no use in a dungeon and is lost with the corpse (owner, 2026-11-03: "bots going to dungeons dont need to bring gold"): bank it
                # first; the trip is picked again at the next tick. The rung's DUNGEON_WORTH counts the bank, so this never closes it.
                self.__dict__["_dungeon_banked_at"] = time.time()
                self.log(f"first trip: banking {self.c.gold} gold before {trip['dest']}")
                self.visit_bank("dungeon", reserve=0)
                return True
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

    TRIP_REST_S = 240          # as the core's walks (hunt_tree Travel, M1): at most four minutes of bandaging or waiting before walking on hurt

    def trip_rest(self, t, now):
        """True while it rests: below task_core.WALK_HP health with nothing within 10 tiles, out of a dungeon stay, it bandages (or waits) before walking
        on, at most TRIP_REST_S a hurt spell. BotHealAdvR walked home at 14 of 94 health after its resurrection and met a bear and a wolf (2026-11-05)."""
        try:
            import task_core
            low = self.hp_pct() < task_core.WALK_HP
        except Exception:
            return False
        if not low:
            t.pop("rest_since", None)
            return False
        if t.get("phase") == "stay" or self.c.ghost or self.threats(10):
            return False
        since = t.setdefault("rest_since", now)
        if now - since > self.TRIP_REST_S:
            return False
        self.activity = "first trip: resting before walking on"
        if hasattr(self, "caster_heal"):
            healed = self.caster_heal()                        # a caster heals with its spells (castfight.py); it has no bandage_self
        else:
            healed = self.bandage_self()
        if not healed:
            time.sleep(3.0)
        return True

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
        self.facts.pop("dungeon_hunt", None)                    # (a dungeon hunt ends with its trip, home, stranded or dead)
        self.trip_drop_task("surface")                           # and the core's dungeon tour with it (see the hunt's end below)
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
            if hasattr(self, "gate_trips"):
                out.extend(self.gate_trips(home, start))         # by the moongates (gate.py, feature gate_travel)
        cache[home["name"]] = out
        return out

    @staticmethod
    def trip_straight(home, dest, kind, start, end, band, hp, stay, feature):
        return {"id": f"{home['name']}-{dest}".lower().replace(" ", "-"), "feature": feature, "dest": dest, "kind": kind, "band": band, "hp": hp, "stay": stay,
                "wps": straight_wps(start, end), "home": home["name"], "vetted": False, "source": "straight"}

    # ---- walkable routes (walkroute.py): see patch_first_trip_walk.py -----------------------------------------------------------------------

    def trip_penalty(self):
        """The route cost: the far walks' own (far.py far_penalty: deaths in memory, the strong spawners, this bot's death spots, the undead box,
        spawners whose kind kills this group, teleporter tiles), so a trip and a long walk judge the ground alike. BotFenceAdvR's Skara Brae trip was
        routed past a skeletal knight's spawn that far walks go round, and it died there (2026-11-01). Without far.py: deaths and strong spawners."""
        if hasattr(self, "runner_penalty") and self.trip_run_on():
            try:
                return self.runner_penalty()                   # a running trip: the casters' home ranges only (far.runner_penalty)
            except Exception as e:
                self.log(f"first trip: runner_penalty failed ({type(e).__name__}: {e}); far_penalty")
        if hasattr(self, "far_penalty"):
            try:
                return self.far_penalty()
            except Exception as e:
                self.log(f"first trip: far_penalty failed ({type(e).__name__}: {e}); the trip's own penalty")
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
            elif trip.get("gate"):
                # two walks and the moongate between them (gate.py): to the home gate, and from the far gate into the town; jump = the home gate's index
                g = trip["gate"]
                if g.get("seed_leg"):
                    sa = wr.repair([tuple(p) for p in g["seed_leg"]], pen)       # the home's surveyed walk to its gate (gate.py)
                    a = {"waypoints": sa} if sa else None
                else:
                    a = wr.plan(wps[0], tuple(g["from"]), pen)
                b = wr.plan(tuple(g["to"]), wps[-1], pen)
                if a is None or b is None:
                    new, route = None, "gate"
                else:
                    wa = [tuple(p[:2]) for p in a["waypoints"]][:-1] + [tuple(g["from"])]
                    wb = [tuple(g["to"])] + [tuple(p[:2]) for p in b["waypoints"]][1:]
                    new, route, jump = wa + wb, "gate", len(wa) - 1
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
        if new and hasattr(self, "route_danger") and not trip.get("gate"):
            new, route = self.trip_avoid(wr, wps, trip, pen, new, route)
        out = {"wps": [list(p) for p in new] if new else [], "route": route if new else "none", "steps": steps_of(new) if new else 0,
               "secs": round(time.time() - t0, 2), "t": round(time.time())}
        if new and trip.get("gate"):
            out["jump"] = jump
            out["steps"] = steps_of(new[:jump + 1]) + steps_of(new[jump + 1:])      # the hop is no walk
        return out

    def trip_end_threat(self, end, door=False):
        """(why, x, y, radius) when the trip's end lies in the reach of a spawner this bot loses to, melee or not, else None: for a trip that ends
        out of town (a dungeon's door; trip_route_dangerous asks it for every trip but a town's). A trip stops at its end to go in, so run-past's
        "nothing catches a runner" does not hold there, and trip_threat's path check leaves the last ENDS_FREE tiles out. BotHealAdvR's first trip to
        Despise met nine at the door from the troll spawner at 1325,1071 (Outdoors, home 30), was boxed in by seven trolls and chased 60 tiles to 3
        hit points (2026-11-02 21:37-21:48). A dungeon's door (`door`) is a teleporter: a running trip steps on it without stopping and nothing follows
        it through (Teleporter.cs: no creatures), so there only a caster's reach stops it, as on the road (trip_threat); BotHealAdvR's walk in 2026-11-02 was
        before the run (trip_run), the pass costing and the pack escape of 2026-11-03/04."""
        if not end:
            return None
        run_door = door and self.trip_run_on()
        try:
            import spots
            import task_core
            for o, k in spots.deadly_spawners(self):
                if run_door and not self.trip_caster(k):
                    continue
                r = max(int(o.get("home") or 10), 1) + task_core.PULL_CLEAR
                if abs(o["x"] - end[0]) <= r and abs(o["y"] - end[1]) <= r:
                    return f"its end at {end[0]},{end[1]} is in the {k} spawner's reach at {o['x']},{o['y']}", o["x"], o["y"], r
        except Exception:
            return None
        return None

    def trip_threat(self, path):
        """(why, x, y, radius) of the first thing on the path a trip must not pass, else None: route_danger's cell (where bots died), or the reach of a
        losing spawner (spots.deadly_spawners: its home range + the creatures' notice range, task_core.PULL_CLEAR, as spots.way_clear judges a tour's way).
        route_danger knows only deaths: the Skara Brae route planned round them still passed the bone magi spawner at 1298,1962, and BotArchAdvR died
        there again (2026-11-02 03:30)."""
        import re as _re
        if path:
            (sx, sy), (ex, ey) = path[0], path[-1]
            path = [p for p in path if max(abs(p[0] - sx), abs(p[1] - sy)) > ENDS_FREE and max(abs(p[0] - ex), abs(p[1] - ey)) > ENDS_FREE]
        run = self.trip_run_on()
        try:
            try:
                bad = self.route_danger({"path": path}, passable=self.trip_cell_passable) if run else self.route_danger({"path": path})
            except TypeError:
                bad = self.route_danger({"path": path})       # a route_danger without passable (a test's stand-in): the plain rule
        except Exception:
            bad = ""
        m = _re.search(r"crosses (-?\d+),(-?\d+)", bad or "")
        if m:
            return bad, int(m.group(1)) + 20, int(m.group(2)) + 20, 40
        try:
            import spots
            import task_core
            losing = [(o["x"], o["y"], max(int(o.get("home") or 10), 1) + (RUN_EDGE if run else task_core.PULL_CLEAR), k) for o, k in spots.deadly_spawners(self)
                      if k not in WATER_ONLY]                         # a sea creature never leaves the water: no danger to a walk on land
            if run:
                # a running trip passes a melee lair (nothing there catches a runner, TRIP_HOT's note); only a caster's or breather's reach is a wall,
                # and only its home range (RUN_EDGE): the run turns back if one comes within notice range on the way (trip_run)
                losing = [o for o in losing if self.trip_caster(o[3])]
        except Exception:
            losing = []
        for x, y in path[::4]:
            for ox, oy, r, k in losing:
                if abs(ox - x) <= r and abs(oy - y) <= r:
                    return f"passes the {k} spawner at {ox},{oy}", ox, oy, r
        return None

    def trip_avoid(self, wr, wps, trip, pen, new, route):
        """Walk round what route_danger flags, as a player goes round a lair: re-plan the whole trip with the flagged cells' tiles at AVOID_FACTOR, up to
        AVOID_TRIES times. Returns (waypoints, route); the last plan when it never comes clear (trip_route_dangerous then refuses it)."""
        circles = []
        for _ in range(AVOID_TRIES):
            th = self.trip_threat(dense_path([tuple(p) for p in new]))
            if not th:
                return new, route
            _, cx, cy, rad = th
            circles.append((cx, cy, rad + 5, AVOID_FACTOR))
            try:
                p2 = wr.penalty_merge(pen, wr.penalty_circles(circles)) if pen else wr.penalty_circles(circles)
                pts = [wps[0]] + ([tuple(trip["exit"])] if trip.get("exit") else []) + [wps[-1]]
                again = []
                for a, b in zip(pts, pts[1:]):
                    r = wr.plan(a, b, p2)
                    if r is None:
                        return new, route
                    again.extend(r["waypoints"] if not again else r["waypoints"][1:])
            except Exception:
                return new, route
            new, route = again, "planned round " + ",".join(f"{c[0]},{c[1]}" for c in circles)
        return new, route

    @staticmethod
    def trip_route_key(home, trip):
        """The key a trip's planned route is kept under in trip.json (ROUTE_V: routes planned before far_penalty are not reused); a gate trip's key also
        names its first leg, so a new approach to the gate is planned afresh instead of the kept route being refused for the hour (gate.py)."""
        key = f"{ROUTE_V}|{home['name']}|{trip['dest']}|{','.join(str(v) for v in (trip.get('exit') or []))}"
        leg = (trip.get("gate") or {}).get("seed_leg")
        if leg:
            key += f"|g{zlib.crc32(json.dumps(leg).encode()) & 0xffff:04x}"
        return key

    def trip_routed(self, home, trip):
        """The trip with walkable waypoints, planned once per (home, destination, exit) and kept in trip.json; None when there is no land route."""
        if _wr() is None:
            return dict(trip, route="straight")
        st = self.trip_load()
        routes = st.setdefault("routes", {})
        key = self.trip_route_key(home, trip)
        r = routes.get(key)
        if r is None:
            r = routes[key] = self.trip_plan(trip)
            self.trip_save()
        if not r["wps"]:
            return None
        return dict(trip, wps=[tuple(p) for p in r["wps"]], route=r["route"], route_steps=r["steps"], route_secs=r.get("secs"), jump=r.get("jump"))

    def trip_ok_route(self, home, trip):
        """True when the trip has a land route and the routed waypoints pass no cell where bots die. A kept route that has turned dangerous (deaths since it
        was planned) is planned again round them, at most once an hour."""
        routed = self.trip_routed(home, trip)
        if routed is None:
            return False
        if not self.trip_route_dangerous(routed):
            return True
        st = self.trip_load()
        key = self.trip_route_key(home, trip)
        r = (st.get("routes") or {}).get(key)
        if r is not None and time.time() - float(r.get("t", 0) or 0) > 3600:
            st["routes"].pop(key, None)
            routed = self.trip_routed(home, trip)
            return routed is not None and not self.trip_route_dangerous(routed)
        return False

    def trip_route_dangerous(self, trip):
        """The routed path crosses ground the gatherers' own test refuses (route_danger on every tile: 3+ recent deaths around a cell, the danger map at
        this bot's skill, 2+ deaths of bots no stronger in 14 days), vetted seeds included: they were checked offline once, but the deaths since count.
        BotArchAdvR died on the Skara Brae seed at Haunted Wood (1236,1976) and BotWarAdvR on the Cove route in the gazer pocket (1786,1258), both first
        trips (2026-11-02 01:24 and 03:02); route_danger flags both routes (1240,1920 and 1720,1200). An unvetted route also by the waypoints, as before."""
        mem = getattr(self, "mem", None)
        if mem is None:
            return False
        wps = [tuple(int(v) for v in p[:2]) for p in trip.get("wps") or []]
        end = tuple(int(v) for v in trip["enter"][:2]) if trip.get("enter") else (wps[-1] if wps else None)
        th = self.trip_end_threat(end, door=bool(trip.get("enter"))) if trip.get("kind") != "town" else None      # a town's end is guarded ground, gone to whatever stands by its gate
        jump = trip.get("jump")
        legs = [wps[:jump + 1], wps[jump + 1:]] if jump is not None else [wps]          # a gate trip: each walk on its own, not the sea between the gates
        for leg in legs:
            th = th or (self.trip_threat(dense_path(leg)) if len(leg) >= 2 else None)
        bad = th[0] if th else ""
        if bad:
            seen = self.__dict__.setdefault("_trip_bad_logged", {})
            if time.time() - seen.get(trip.get("dest"), 0) > 1800:
                seen[trip.get("dest")] = time.time()
                self.log(f"first trip: {trip.get('dest')} refused: the route {bad}")
                self.ev("trip_skip", dest=trip.get("dest"), why=f"route {bad}")
            return True
        if trip.get("vetted", True):
            return False
        from memory import cell_of
        run = self.trip_run_on()
        # a running trip crosses a cell of deaths that shows no caster (trip_cell_passable, route_danger's own rule for a runner): the troll road to
        # Despise's door (1360,1240 and seven more) refused every caster's trip with trip_run on (2026-11-09 01:07-01:12)
        cells = [cell_of(x, y) for x, y in trip["wps"] if mem.dangerous_cell(cell_of(x, y)) and not (run and self.trip_cell_passable(cell_of(x, y)))]
        if cells:
            seen = self.__dict__.setdefault("_trip_bad_logged", {})
            if time.time() - seen.get(("cell", trip.get("dest")), 0) > 1800:
                seen[("cell", trip.get("dest"))] = time.time()
                self.log(f"first trip: {trip.get('dest')} refused: the route crosses {cells[0]}, a dangerous cell in the memory ({len(cells)} in all)")
        return bool(cells)

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

    def trip_run_on(self):
        return bool(getattr(self, "feature", None)) and self.feature("trip_run")

    def trip_walking(self):
        """A trip under way on the road (out or home), the character alive."""
        try:
            t = self.trip_load().get("trip")
        except Exception:
            return False
        return bool(t) and t.get("phase") in ("out", "home") and not self.c.ghost

    def trip_near(self):
        """The monsters that can hurt it within notice range (TRIP_HOT)."""
        try:
            near = list(self.dangers(TRIP_HOT)) if hasattr(self, "dangers") else []
        except Exception:
            near = []
        try:
            for m in self.threats(TRIP_HOT):
                if all(m.serial != o.serial for o in near):
                    near.append(m)
        except Exception:
            pass
        if near:
            self.__dict__["_trip_near_at"] = time.time()
        return near

    @staticmethod
    def trip_caster(kind):
        """A kind that hurts at range: spells or breath (creature_stats, danger.stats), what a runner cannot outpace."""
        try:
            import danger
            c = danger.stats().get(kind) or {}
            return bool(c.get("casts") or c.get("breath"))
        except Exception:
            return False

    def trip_cell_passable(self, cell):
        """A running trip crosses a cell of deaths whose sightings show no caster: the cells at 2000-2040,960-1000 hold snakes, rats, slimes and
        mongbats, and BotFairSwordNR and BotFencerBR died there stopped (a snake fight, boxed in with a broken weapon, 2026-11-02/03), not running.
        A cell no bot has looked at is not passable."""
        try:
            sights = (self.mem.state["world"]["cells"].get(cell) or {}).get("sights") or {}
        except Exception:
            return False
        return bool(sights) and not any(self.trip_caster(k) for k in sights)

    DUNGEON_HOLD = ("r_far", "r_sellmeat", "r_sell_leather", "r_stock", "r_rune_buy", "r_resupply", "r_train", "r_house", "r_bank", "r_break",
                    "r_lesson", "r_buddy", "r_party", "r_book", "r_practice", "r_scribe", "r_upgrade", "r_sell", "r_craft_sell")

    def in_dungeon_now(self):
        """Standing inside a dungeon (gazetteer.side: not the surface), alive."""
        try:
            if getattr(self.c, "ghost", False):
                return False
            import gazetteer
            return gazetteer.side(int(self.c.x), int(self.c.y)) not in (None, "surface")
        except Exception:
            return False

    def trip_skip(self, name):
        """Feature trip_run: while a trip walks, the rules that stand still wait: no fight on the road, and with a monster in notice range no bandage,
        no side-step, no flight off the route (the trip runs on, or back, with the potions drunk on the run: trip_potions). And inside a dungeon no town
        errand starts (DUNGEON_HOLD): BotWarlockAR's spellbook rule fetched gold from the bank 20 s into its Despise stay, the walk toward Britain's bank
        ran it into the dead-end west room and eight lizardmen killed it (2026-11-09 05:04-05:05); the stay's own end (kit low, its time) takes it out."""
        if name in self.DUNGEON_HOLD and self.in_dungeon_now():
            return True
        if name not in TRIP_HOLD or not self.trip_run_on() or not self.trip_walking():
            return False
        if name == "r_fight":
            return True
        if self.trip_near():
            return True
        if name == "r_heal" and time.time() - self.__dict__.get("_trip_near_at", 0) < self.trip_bandage_s():
            return True                                         # r_heal's bandage_self stands still this long, and a monster just out of range is
                                                                # back before it ends; trip_potions bandages on the run instead (bandage_start)
        return False

    def trip_bandage_s(self):
        """The seconds a self-bandage keeps the bot standing: pre-AOS 9.4 + 0.6 x (120 - Dex) / 10 (Bandage.cs, BandageContext.BeginHeal)."""
        try:
            dex = int(self.c.state.get("dex") or self.c.state.get("dexterity") or 50)
        except Exception:
            dex = 50
        return 9.4 + 0.6 * (120 - max(0, min(dex, 120))) / 10

    def trip_turn_back(self, target=None, ahead=None, behind=None):
        """Why a running trip turns back, else None: under half health with a monster near; or TRIP_CASTERS casters or breathers in notice range at
        once, or a pack (TRIP_PACK), when the detour finds no clear way on toward target (the next route point): a leg out of every threat's reach
        that still gains (trip_way_on). One caster is run past at a distance (trip_detour), as a player at full health with potions runs past it
        (owner, 2026-11-03): BotHealAdvR turned back at full health for one gargoyle at 8 tiles, then for three orcs it could have outrun."""
        near = self.trip_near()
        if near and self.hp_pct() < 50 and not self.trip_mend_left():
            return f"hurt with {near[0].name} near"            # with a heal left trip_detour runs out of reach and the potions mend on the run
        casters = [m for m in near if self.trip_caster(self.mkey(m))]
        try:
            import casterpass
            # a reaper or a corpser never moves (DisallowAllMoves): past its reach it is no member of a pack that could box the runner in
            pack = [m for m in near if not (self.mkey(m) in casterpass.IMMOBILE and (getattr(m, "distance", 9) or 9) > 2)]
        except Exception:
            pack = near
        why = None
        if len(casters) >= TRIP_CASTERS:
            why = f"casters near: {', '.join(sorted({m.name for m in casters}))[:60]}"
        elif len(pack) >= TRIP_PACK:
            why = f"pack near: {len(pack)} ({', '.join(sorted({m.name for m in pack}))[:60]})"
        if why and target is not None and self.trip_way_on(near, target):
            return None                                            # a clear leg on: run past them (trip_detour runs it)
        if why and ahead and self.trip_pass_ok(near, ahead, behind or []):
            return None                                            # the pass is affordable, or cheaper than turning back (casterpass.pass_cost)
        if why is None and ahead and casters and any((int(m.x), int(m.y)) in self.trip_fixed_spots() for m in casters):
            if not self.trip_pass_ok(near, ahead, behind or []):
                why = "caster near: passing it costs too much"     # a caster that never moves on the road, and the pass not affordable: back (trip_detour)
        return why

    def trip_fixed_spots(self):
        """{(x, y)} of the monsters in notice range that never move (casterpass.IMMOBILE: reapers, corpsers)."""
        try:
            import casterpass
            return {(int(m.x), int(m.y)) for m in self.trip_near() if getattr(m, "x", None) is not None and self.mkey(m) in casterpass.IMMOBILE}
        except Exception:
            return set()

    def trip_route_slice(self, wps, i, step, tiles=PASS_TILES):
        """The route's points from waypoint i on in the direction step, until they reach `tiles` tiles of walk (the costed pass, casterpass)."""
        out, walked, prev = [], 0, (int(self.c.x), int(self.c.y))
        while 0 <= i < len(wps) and walked < tiles:
            p = (int(wps[i][0]), int(wps[i][1]))
            walked += cheb(prev[0], prev[1], p[0], p[1])
            out.append(p)
            prev = p
            i += step
        return out

    DRIFT_WAIT_S = ESCAPE_HOLD_S   # s it waits out of notice for a pack to drift off the road: the escape window itself
    DRIFT_MARGIN = 4               # tiles past notice the pack must be before the wait starts (and the wait ends only inside notice)
    DRIFT_HOP, DRIFT_HOPS = 12, 3  # a hop away from a chasing pack: 12 tiles take a runner 2.4 s (0.2 s a tile) and a troll 5.4 (0.45)

    def trip_drift_wait(self, t, leg):
        """Once a trip, on the way out, before "the way is held" turns it back: walk the escape leg, and with nothing in notice range there, stand
        DRIFT_WAIT_S watching; nothing comes within notice and health holds: True, the run is tried again. A player waits out of sight for a camp
        to drift. The Despise door camp turned back four trips on 2026-11-08 (SwordBR 01:24, MaceAdvR 02:00, FencerBR 02:44, WarAdvR 04:03, four
        escapes round the same five trolls), each after a 40-70 minute walk, while eight trips passed it in the hour 03:12-04:12."""
        if t.get("drift_waited") or t.get("phase") != "out":
            return False
        t["drift_waited"] = True
        try:
            import detour
            notice = int(detour.NOTICE)
        except Exception:
            notice = 14
        try:
            self.c.goto(int(leg.to[0]), int(leg.to[1])).wait(timeout=20)
        except Exception:
            return False

        def near(r=notice):
            try:
                return [m for m in self.trip_near() if getattr(m, "x", None) is not None
                        and max(abs(int(m.x) - int(self.c.x)), abs(int(m.y) - int(self.c.y))) <= r]
            except Exception:
                return []

        # clear of the pack first: a hop of DRIFT_HOP tiles straight away from those within DRIFT_CLEAR, up to DRIFT_HOPS times. BotMaceCR began its wait
        # with two trolls at 13 and 14 tiles that were chasing, and the wait ended in a second (2026-11-08 04:54:33)
        for _ in range(self.DRIFT_HOPS):
            ms = near(notice + self.DRIFT_MARGIN)
            if not ms:
                break
            cx = sum(int(m.x) for m in ms) / len(ms)
            cy = sum(int(m.y) for m in ms) / len(ms)
            dx = (int(self.c.x) > cx) - (int(self.c.x) < cx)
            dy = (int(self.c.y) > cy) - (int(self.c.y) < cy)
            if not dx and not dy:
                break
            try:
                self.c.goto(int(self.c.x) + dx * self.DRIFT_HOP, int(self.c.y) + dy * self.DRIFT_HOP).wait(timeout=10)
            except Exception:
                break
            self.log(f"first trip: hop away from {len(ms)} ({', '.join(sorted({str(getattr(m, 'name', '?')) for m in ms}))}) to {self.c.x},{self.c.y}")
        if near(notice + self.DRIFT_MARGIN):
            return False
        self.log(f"first trip: the way is held: waiting {int(self.DRIFT_WAIT_S)} s out of notice at {self.c.x},{self.c.y} for the pack to drift")
        end = time.time() + self.DRIFT_WAIT_S
        while time.time() < end:
            if hasattr(self, "beat"):
                self.beat()
            time.sleep(1.0)
            if self.c.ghost or self.hp_pct() < 60 or near():
                self.ev("trip_drift_wait", ok=False, at=[int(self.c.x), int(self.c.y)])
                return False
        self.__dict__.pop("_box_held", None)
        self.ev("trip_drift_wait", ok=True, at=[int(self.c.x), int(self.c.y)])
        self.log("first trip: nothing came: trying the run again")
        return True

    def trip_held_turn(self):
        """May the way-is-held abort turn the trip back? Not when the run-past costed the way back (the route behind) at a contact with a poisoner the
        bot cannot cure (casterpass.UNCURABLE) and the way on for less, in the last few seconds: BotFairArcherVR, among two scorpions and an earth
        elemental on the Cove road, read "passing 4 monsters costs ~0 hp ... (back ~2000022): go on", and the abort the same second sent it home through
        the scorpions; dead 40 s later (2026-11-06 09:59-10:00). The escapes go on, away from them."""
        pc = self.__dict__.get("_pass_costs")
        try:
            import casterpass
            if pc and time.time() - float(pc[2]) < 5 and float(pc[1]) >= casterpass.UNCURABLE and float(pc[0]) < float(pc[1]):
                self.__dict__["_escapes_at"] = []
                if time.time() - self.__dict__.get("_held_logged", 0) > 30:
                    self.__dict__["_held_logged"] = time.time()
                    self.log(f"first trip: the way is held, but the way back passes a poisoner it cannot cure (back ~{pc[1]:.0f}, on ~{pc[0]:.0f}): going on")
                return False
        except Exception:
            pass
        return True

    def trip_pass_ok(self, monsters, ahead, behind):
        """True when running on past these casters is affordable (casterpass.affordable: the expected damage, with the Heal potions drinkable on the way,
        leaves the largest of their spells in hand) or costs no more than turning back along the route behind. A caster not in the stats table cannot
        be costed: no verdict (the old rule stands). BotFairArcherVR turned back from Skara Brae for two reapers at 9 and 12 tiles at 1035,1983 and ran
        home through the same reach (2026-11-03 20:40); reapers never move. A pack is costed the same way, every monster in view (casterpass.pass_cost: a
        melee monster that can reach the road costs a swing): BotArchAdvR turned back from Trinsic for an orc and an ettin, both slower than a runner
        (2026-11-03 21:40)."""
        try:
            import casterpass
            import danger
            table = danger.stats()
            here = (int(self.c.x), int(self.c.y))
            import detour
            cs = []
            for m in monsters:
                k = self.mkey(m)
                e = table.get(k)
                if not e or getattr(m, "x", None) is None:
                    return False
                cs.append((k, e, (int(m.x), int(m.y)), bool(self.trip_caster(k)), detour.uncurable(k)))
            st = self.c.state or {}
            stats = tuple(float(st.get(k) or 50) for k in ("str", "dex", "int"))
            rs = float(self.skill_values.get("Resisting Spells", 0.0) or 0.0) if hasattr(self, "skill_values") else 0.0
            run_s = self.run_s() if hasattr(self, "run_s") else casterpass.RUN_S         # mounted, half the time in reach (ride.py)
            on = casterpass.pass_cost(casterpass.dense([here] + list(ahead)), cs, rs, stats, run_s)
            # no route behind: the trip has only just set out, and turning back costs nothing
            back = casterpass.pass_cost(casterpass.dense([here] + list(behind)), cs, rs, stats, run_s) if behind else (0.0, 0.0, 0.0)
            pots = sum((i.amount or 1) for i in self.c.backpack if items.potion_kind(i.name) == "heal")
            ok = casterpass.affordable(self.c.hp, pots, *on) or on[0] <= back[0]
            now = time.time()
            self.__dict__["_pass_costs"] = (on[0], back[0], now)             # (trip_held_turn: the way-is-held abort reads them)
            if now - self.__dict__.get("_pass_logged", 0) > 10:
                self.__dict__["_pass_logged"] = now
                self.log(f"first trip: passing {len(cs)} {'casters' if all(c[3] for c in cs) else 'monsters'} costs ~{on[0]:.0f} hp in {on[1]:.0f} s (back ~{back[0]:.0f}), hp {self.c.hp}, "
                         f"{pots} Heal potions, largest spell {on[2]:.0f}: {'go on' if ok else 'turn back'}")
                self.ev("trip_pass", on=round(on[0], 1), back=round(back[0], 1), secs=round(on[1], 1), top=round(on[2], 1), hp=self.c.hp, pots=pots,
                        go=ok, casters=[c[0] for c in cs])
            return ok
        except Exception as e:
            self.log(f"first trip: pass cost failed ({type(e).__name__}: {e})")
            return False

    def trip_mend_left(self):
        """A heal still in the pack: a Heal potion, or a bandage (put on while running, bot_common.bandage_start)."""
        try:
            if self.potion("heal") is not None:
                return True
        except Exception:
            pass
        try:
            return hasattr(self, "bandages") and self.bandages() > 0
        except Exception:
            return False

    def trip_way_on(self, near, target):
        """True when the way on to target is clear of every threat's reach, or the detour has a leg that stays out of it and still gains."""
        try:
            import detour
            wr = _wr()
            threats = [detour.Threat(int(m.x), int(m.y), bool(self.trip_caster(self.mkey(m))), getattr(m, "name", "") or "", detour.poisons(self.mkey(m)))
                       for m in near if getattr(m, "x", None) is not None and getattr(m, "y", None) is not None]
            here, goal = (int(self.c.x), int(self.c.y)), (int(target[0]), int(target[1]))
            if not detour.needs_detour(here, goal, threats):
                return True
            leg = detour.plan_leg(here, goal, threats, wr.leg_clear, forbidden=self.trip_lair_home())
            if leg is None or leg.progress <= 0:
                return False
            if leg.clearance >= 0:
                return True
            # healthy (not yet a Heal potion's worth missing, HEAL_MISSING) with a Heal potion in the pack: run on along a leg that gains and comes
            # no closer to any threat than now, as a player at full health runs past two casters (owner, 2026-11-03). BotHealAdvR at 94/94 broke off
            # at 1929,1306 for a gargoyle at 9 and a gazer at 10: the corridor north runs along the gazer pocket, and no leg there ends 12 clear.
            healthy = (self.c.max_hp - self.c.hp) < HEAL_MISSING and self.potion("heal") is not None
            return healthy and leg.dip == 0
        except Exception:
            return False

    def trip_dash(self, t, wps):
        """True when the bot runs the route straight on past the monsters in notice range: none a caster, every one that moves slower than a runner
        (casterpass.move_s against run_s: a troll 0.45 s a tile, npc-speeds.json, the runner 0.2) and the pass affordable (trip_pass_ok). An escape out of
        a slow pack's reach gains nothing and the route leads back into it: BotHealAdvR ran four escape legs round the troll camp by Despise's door at
        93/94 hit points with the pass costed "go on", and the fourth turned the trip back ("the way is held"), 9 of its trips 2026-11-05/07 (owner,
        2026-11-07: "running past trolls should be easy as long as the bot doesn't stop")."""
        try:
            import casterpass
            import danger
            table = danger.stats()
        except Exception:
            return False
        near = [m for m in self.trip_near() if getattr(m, "x", None) is not None]
        if not near:
            return False
        held = self.__dict__.get("_box_held")
        if held:
            if time.time() < held["until"] and any(getattr(m, "serial", None) in held["serials"] for m in near):
                return False                                    # the pack judged to box it in is still in view: no second run past it (BOX_HOLD_S)
            self.__dict__.pop("_box_held", None)
        run_s = self.run_s() if hasattr(self, "run_s") else casterpass.RUN_S
        for m in near:
            k = self.mkey(m)
            e = table.get(k)
            if self.trip_caster(k) or not e:
                return False
            mv = casterpass.move_s(k, e)
            if mv is not None and mv <= run_s:
                return False                                    # it keeps up with a runner: the escapes stand
        step = 1 if t.get("phase") == "out" else -1
        ahead = self.trip_route_slice(wps, t["i"], step)
        box = self.trip_boxers(near, ahead, run_s, table, end=(wps[-1] if step == 1 and wps else None)) if self.DASH_BOX_HOLD else []
        if len(box) >= self.DASH_BOX:
            now = time.time()
            self.__dict__["_box_held"] = {"serials": {sr for _, sr in box if sr is not None}, "until": now + self.BOX_HOLD_S}
            if now - self.__dict__.get("_box_logged", 0) > 10:
                self.__dict__["_box_logged"] = now
                self.ev("trip_dash_held", boxers=len(box), kinds=sorted({k for k, _ in box}))
                self.log(f"first trip: no run past {len(box)} standing where it must stop ({', '.join(sorted({k for k, _ in box}))}) on the road or at the door: they would box the runner in")
            return False
        return self.trip_pass_ok(near, ahead, self.trip_route_slice(wps, t["i"] - step, -step))

    DASH_BOX_HOLD = False      # owner, 2026-11-08, asked "fewer deaths or more trips getting through?" at the Despise door: "Allow risky dashes". The
                               # box hold (trip_boxers, gates 113/120) is off: a slow pack on the road or at the door no longer stops the run past it. With it
                               # on there were no door deaths from 23:27 but 4 of 6 trips turned back in one hour; before it, FenceAdvR and MaceCR died boxed in
    DASH_BOX = 3               # monsters that reach the road ahead before the runner: with 4 and 5 beside it no step moved (BotMaceCR, BotFairSwordNR, BotFenceAdvR)
    BOX_HOLD_S = 60.0          # s a held dash stays held while one of that pack is in view (the trip's own "4 escapes in 60 s" window): BotArchAdvR's hold at
                               # the Trinsic road camp fired at 22:52:07, the next verdict 2 s later ran past four (a giant spider, an orc, a ratman, an ettin),
                               # and it died boxed at 22:52:23, 81 hit points to 0 (2026-11-07)
    BOX_TILES = 25             # the road ahead those are counted on
    DOOR_HELD = 4              # tiles round the trip's end (the door): the stop beside the door at Despise was 4 tiles short of it (1297,1077 for 1296,1081)

    PIN_S = 4.0                # s on one tile with two or more beside it that make a trip pinned: a run gains a tile in 0.2 s, so 20 steps without one

    def trip_pinned(self):
        """The attacker to fight when the bot has stood on one tile PIN_S seconds with two or more monsters in war mode beside it (within a tile:
        bodies block a step), else None. The position clock restarts whenever the bot moves."""
        here = (int(self.c.x), int(self.c.y))
        now = time.time()
        pos = self.__dict__.get("_pin_pos")
        if not pos or pos[0] != here:
            self.__dict__["_pin_pos"] = (here, now)
            return None
        if now - pos[1] < self.PIN_S:
            return None
        beside = [m for m in self.mobs(1) if getattr(m, "in_war_mode", False) and not getattr(m, "is_dead", False)]
        return beside[0] if len(beside) >= 2 else None

    def trip_boxers(self, near, ahead, run_s, table, end=None):
        """[(kind, serial)] of the monsters in view standing where the run would stop against them: on the next BOX_TILES of road (within a tile:
        bodies block a step), or within DOOR_HELD tiles of the trip's end (end: the door, where the run stops to step through) when that lies within
        the slice. A runner passes a slow monster beside the road at the cost of a swing (trip_pass_ok); one it must stop beside, it cannot.
        BotMaceCR ran "straight past" 3, then 5 trolls at Despise's door, "no step in any direction moved the character (4 mobiles beside it)", and
        died on the way home (2026-11-07 18:57-19:02); BotFenceAdvR died boxed at the door at 16:07, BotFairSwordNR was stranded there at 18:12."""
        import casterpass
        road = casterpass.dense([(int(self.c.x), int(self.c.y))] + list(ahead))[: self.BOX_TILES + 1]
        stop = None
        if end is not None and any(max(abs(int(end[0]) - x), abs(int(end[1]) - y)) <= 1 for x, y in road):
            stop = (int(end[0]), int(end[1]))
        out = []
        for m in near:
            mx, my = int(m.x), int(m.y)
            on_road = any(max(abs(mx - x), abs(my - y)) <= 1 for x, y in road[1:])
            at_stop = stop is not None and max(abs(mx - stop[0]), abs(my - stop[1])) <= self.DOOR_HELD
            if on_road or at_stop:
                out.append((self.mkey(m), getattr(m, "serial", None)))
        return out

    def trip_lair_home(self):
        """forbidden(point) for detour.py: inside the home range of a caster lair this bot loses to (spots.deadly_spawners), cached a minute. A
        detour bends out round a wandering caster, never into the camp it came from."""
        got = self.__dict__.get("_lair_homes")
        if got is None or time.time() - got[0] > 60:
            try:
                import spots
                homes = [(o["x"], o["y"], max(int(o.get("home") or 10), 1)) for o, k in spots.deadly_spawners(self) if self.trip_caster(k)]
            except Exception:
                homes = []
            got = self.__dict__["_lair_homes"] = (time.time(), homes)
        homes = got[1]
        return lambda p: any(abs(p[0] - x) <= r and abs(p[1] - y) <= r for x, y, r in homes)

    def trip_detour(self, t, wps, target):
        """One slice of a running trip with monsters in notice range: when the straight way to the next route point comes inside a threat's need
        (detour.py: a caster's spell range + 2, a melee monster's reach + 1), run the best short leg round them instead, out (or home) whichever
        way the trip is going, and rejoin the route at the nearest of the next few points after it. True when a detour leg took the slice."""
        try:
            import detour
            wr = _wr()
        except Exception:
            return False
        threats = [detour.Threat(int(m.x), int(m.y), bool(self.trip_caster(self.mkey(m))), getattr(m, "name", "") or "", detour.poisons(self.mkey(m)))
                   for m in self.trip_near() if getattr(m, "x", None) is not None and getattr(m, "y", None) is not None]
        if not threats:
            self.__dict__.pop("_escape", None)                  # nothing in notice range: the escape, if any, is over
            return False
        pin = self.trip_pinned()
        if pin is not None:
            # bodies on every side: no run or leg moves it, so it fights the weakest of them (basics.fight_pick) until a gap opens, as a player does.
            # BotRangerAR stood 12 s on 1362,1194 beside three trolls under a "go on" dash, 73 -> 53, and died after the trip gave up (2026-11-08 16:33)
            now = time.time()
            if now - self.__dict__.get("_pin_logged", 0) > 10:
                self.__dict__["_pin_logged"] = now
                self.log(f"first trip: pinned at {self.c.x},{self.c.y} by {len(self.mobs(1))} beside me for {self.PIN_S:.0f} s: fighting out (hp {self.c.hp})")
                self.ev("trip_pinned", at=[int(self.c.x), int(self.c.y)], hp=int(getattr(self.c, "hp", 0) or 0), n=len(self.mobs(1)))
            self.fight_back(pin)
            return True
        if hasattr(self, "note_casters"):
            self.note_casters(threats)                          # a caster seen on the road steers every bot's routes (basics.live_caster_penalty)
        here = (int(self.c.x), int(self.c.y))
        casters = [th for th in threats if th.caster]
        esc = self.__dict__.setdefault("_escape", {"on": False, "clear": 0})
        hurt = self.hp_pct() < 60
        fixed = self.trip_fixed_spots()
        movers = [th for th in casters if (th.x, th.y) not in fixed]
        dash = not casters and self.trip_dash(t, wps)
        if dash:
            # every one slower than a runner and the pass affordable: run on, never away (trip_dash); a leg round them that still gains, else the route
            esc.update(on=False, clear=0)
            self.__dict__["_escapes_at"] = []
            now = time.time()
            if now - self.__dict__.get("_dash_logged", 0) > 10:
                self.__dict__["_dash_logged"] = now
                self.log(f"first trip: running straight past {len(threats)} ({', '.join(sorted({th.name for th in threats}))[:60]}), hp {self.c.hp}")
                self.ev("trip_dash", at=list(here), hp=int(getattr(self.c, "hp", 0) or 0), phase=t.get("phase"), threats=[[th.name, th.x, th.y] for th in threats][:6])
        if not dash and not esc["on"] and not hurt and fixed:
            # a caster that never moves (a reaper, casterpass.IMMOBILE) is run past along the route, the shortest time in its range, when the pass is
            # affordable (trip_pass_ok; trip_turn_back turns back when it is not): running from it only brings the route back into its range. BotFenceAdvR
            # escaped out of a reaper's range and back in for 70 s by the Trinsic road and died, 87 -> 0 (2026-11-04 02:54:50-02:56:03)
            rest = [th for th in threats if (th.x, th.y) not in fixed]
            if not detour.needs_detour(here, (int(target[0]), int(target[1])), rest):
                step = 1 if t.get("phase") == "out" else -1
                monsters = [m for m in self.trip_near() if getattr(m, "x", None) is not None]
                if self.trip_pass_ok(monsters, self.trip_route_slice(wps, t["i"], step), self.trip_route_slice(wps, t["i"] - step, -step)):
                    return False                                # the straight way on: trip_step walks the route
        if dash:
            pass
        elif movers and detour.clearance_at(here, movers) < 0:
            esc.update(on=True, clear=0, hurt=False)            # a caster inside its reach: run from it, not along the route past it
        elif hurt and detour.clearance_at(here, threats) < 0:
            esc.update(on=True, clear=0, hurt=True)             # hurt with a monster in reach: out of every reach first, mending on the run
        elif len(threats) >= detour.PACK and detour.clearance_at(here, threats) < 0:
            esc.update(on=True, clear=0, hurt=True, pack=True)  # a pack in view and one of it in reach: out of every reach first (detour.PACK), whatever the health
        elif esc["on"] and all(detour.cheb(here, (th.x, th.y)) >= detour.NOTICE + 2 for th in (threats if esc.get("hurt") else casters)):
            esc.update(on=False, clear=0)                       # every one it ran from already past its notice range: the escape is over
        elif esc["on"] and esc.get("hurt") and not esc.get("pack") and not hurt and not casters and detour.clearance_at(here, threats) >= 0:
            esc.update(on=False, clear=0)                       # mended and out of reach: back to the route (a pack's escape runs on past its notice:
                                                                # ended at its reach, the route led back into the chasing pack, escape after escape, and
                                                                # BotArchAdvR died in a ratman and giant-spider camp by the Trinsic road, 2026-11-04 04:06-04:08)
        forbid = self.detour_forbid(here, self.trip_lair_home()) if hasattr(self, "detour_forbid") else self.trip_lair_home()
        if esc["on"]:
            leg = detour.escape_leg(here, threats, wr.leg_clear, forbidden=forbid, fixed=fixed)
            if leg is not None and t.get("phase") == "out":
                held = [x for x in self.__dict__.get("_escapes_at", []) if time.time() - x < ESCAPE_HOLD_S] + [time.time()]
                self.__dict__["_escapes_at"] = held
                if len(held) >= ESCAPE_HOLD_N and self.trip_drift_wait(t, leg):
                    self.__dict__["_escapes_at"] = []           # waited out of notice and the road cleared: the run goes on (trip_drift_wait)
                elif len(held) >= ESCAPE_HOLD_N and self.trip_held_turn():
                    # escape after escape on the way out: monsters hold the road, so the trip turns back (to be walked home round them by these legs)
                    self.__dict__["_escapes_at"] = []
                    self.trip_abort(f"run: the way is held ({len(held)} escapes in {int(ESCAPE_HOLD_S)} s)")
        else:
            leg = detour.plan_leg(here, (int(target[0]), int(target[1])), threats, wr.leg_clear, forbidden=forbid)
        if leg is None or (dash and leg.progress <= 0):
            return False                                        # (a dash: no leg that gains, the route straight on)
        if hasattr(self, "detour_note"):
            self.detour_note(here, leg)                         # how the walk goes decides whether this leg end is barred next time
        now = time.time()
        if now - self.__dict__.get("_detour_logged", 0) > 10:
            self.__dict__["_detour_logged"] = now
            near = ", ".join(f"{th.name} at {detour.cheb(here, (th.x, th.y))}" for th in threats)[:90]
            self.log(f"first trip: {leg.kind} to {leg.to[0]},{leg.to[1]} (clearance {leg.clearance}, gain {leg.progress}) round {near}")
        # every leg is recorded (the log line above only once in 10 s): BotWarAdvR's legs from an escape at 9 tiles to a scorpion at 1 went unrecorded
        self.ev("trip_detour", leg=leg.kind, at=list(here), to=list(leg.to), clearance=leg.clearance, gain=leg.progress, hp=int(getattr(self.c, "hp", 0) or 0),
                esc=bool(esc["on"]), threats=[[th.name, th.x, th.y, th.caster] for th in threats][:6])
        walk = self.goto_near(leg.to[0], leg.to[1], 1)
        self.trip_drink_on_run()                                # with the leg under way (trip_drink_on_run)
        walk.wait(timeout=TRIP_HOT_SLICE)
        if esc["on"]:
            watch = threats if esc.get("hurt") else casters
            far_off = all(detour.cheb((int(self.c.x), int(self.c.y)), (th.x, th.y)) >= detour.NOTICE + 2 for th in watch) if watch else True
            esc["clear"] = esc["clear"] + 1 if far_off else 0
            if esc["clear"] >= 2:
                esc.update(on=False, clear=0)                   # out of their notice two legs running: back to the route
        # rejoin: the nearest of the next few route points the trip is heading for
        idx = t["i"]
        step = 1 if t.get("phase") == "out" else -1
        ahead = [i for i in range(idx, idx + step * 4, step) if 0 <= i < len(wps)]
        best = min(ahead, key=lambda i: cheb(self.c.x, self.c.y, *wps[i]))
        if best != idx:
            t.update(i=best, best=1e9, best_at=time.time(), fails=0)
            self.trip_save()
        return True

    def trip_dungeon_hunt(self, t, now):
        """Feature dungeon_hunt: inside the dungeon, the stay is a hunt (owner, 2026-11-04: "have the bots actually hunt in the dungeon, not just stand there
        as a trip"). The decision core hunts that dungeon's level 1 (task_core.tiers adds the rung's tier, spots.all_spots holds the spots to that side and
        tier) for DUNGEON_HUNT_S; the trip waits (False). Returns None once the hunt is over (the time, the bot off the side, the kit or health, or the core
        on an errand: a full pack or an empty kit is sold or bought in town), and the stay then ends: the walk home crosses out through the dungeon's own
        teleporters (tele.py) to the door and goes home along the route."""
        side = t.get("dest")
        dh = self.facts.get("dungeon_hunt")
        if dh is None and t.get("dungeon_hunted"):
            # a restart resumed the stay (trip_load) but the hunt lived in the old brain's facts: the rest of it is hunted, or the stay ends now. Returning
            # "over" without ending the stay stood BotFenceAdvR at the lizardman floor "looking around Despise" from its 19:39 restart to past 20:14, and
            # BotFencerBR at the landing hall 19:04-19:12 (2026-11-07)
            until = float(t.get("stay_until") or 0)
            try:
                here = _gz().side(int(self.c.x), int(self.c.y)) if _gz() else side
            except Exception:
                here = side
            if until - now < 120 or here != side or self.c.ghost:
                t["stay_until"] = now
                return None
            dh = self.facts["dungeon_hunt"] = {"side": side, "t0": float(t.get("hunt_t0") or now), "until": until, "landing": [int(self.c.x), int(self.c.y)],
                                               "resumed": True}
            if hasattr(self, "tele_allow"):
                self.tele_allow(side, seconds=until - now + 600)
            self.__dict__.pop("_spots", None)
            self.trip_drop_task(side)
            self.log(f"first trip: the {side} hunt resumes after a restart ({(until - now) / 60:.0f} min left)")
            self.ev("dungeon_hunt_resumed", side=side, minutes_left=round((until - now) / 60, 1))
        if dh is None:
            dh = self.facts["dungeon_hunt"] = {"side": side, "t0": now, "until": now + DUNGEON_HUNT_S, "landing": [int(self.c.x), int(self.c.y)]}
            t["dungeon_hunted"] = True
            t["hunt_t0"] = now
            t["stay_until"] = dh["until"]
            if hasattr(self, "tele_allow"):
                self.tele_allow(side, seconds=DUNGEON_HUNT_S + 600)
            self.__dict__.pop("_spots", None)                   # the spot list is cached: the dungeon's spots come in at once
            self.trip_drop_task(side)
            self.trip_save()
            self.log(f"first trip: hunting {side} level 1 for {int(DUNGEON_HUNT_S // 60)} min")
            self.ev("dungeon_hunt", side=side, minutes=round(DUNGEON_HUNT_S / 60))
        why = None
        try:
            here_side = _gz().side(int(self.c.x), int(self.c.y)) if _gz() else side
        except Exception:
            here_side = side
        try:
            # the kit the road home needs (ladder_kit_strict: 15 bandages, 3 Heal potions), not the entry gate (task_core.rung_ready: 50 bandages and 90%
            # health): one bandage used, and BotHealAdvR's hunt ended "kit or health low" with 49 bandages and 10 Heal potions at 86% (2026-11-04 12:57)
            ready = (self.ladder_kit_stay() if hasattr(self, "ladder_kit_stay") else self.ladder_kit_strict() if hasattr(self, "ladder_kit_strict")
                     else True)
        except Exception:
            ready = True
        try:
            lost = hasattr(self, "weapon_now") and self.weapon_state() in ("none", "wrong")
        except Exception:
            lost = False
        task = self.facts.get("task") or {}
        if now >= float(dh.get("until", 0)):
            why = "its time"
        elif self.c.ghost:
            why = "a death"
        elif here_side != dh["side"]:
            why = "out of the dungeon"
        elif not ready:
            why = "kit low"
        elif lost:
            # its weapon broke and no spare of its skill is in the pack (ladder_geared buys one before the trip): a fighter with its fists goes home
            # to buy another, as a player would (BotMaceCR fought on in Despise with its fists after its club broke, 2026-11-08)
            why = "weapon lost"
        elif task.get("task") and task.get("task") not in ("hunt", "tour2", "wait", "rest", "camp", "loot"):
            # (camp and loot are the hunt's own: a spawner held for two respawns after a good kill, a corpse beside it; task_core keeps a dungeon hunt's
            # errands on its side. BotHealAdvR's Despise hunt ended "a camp errand" 12.6 minutes into 40, with 45 kills, 2026-11-07 11:21)
            why = f"a {task.get('task')} errand"
        elif task.get("task") == "wait":
            # nothing open to hunt in the dungeon: past the core's own wait (task_core.WAIT_S), the hunt is over and the bot goes home, not stand at the
            # landing until its time (BotHealAdvR, "no hunt area is open" from 19:40 to the hunt's end at 20:18)
            dh.setdefault("wait_since", now)
            try:
                import task_core
                wait_s = task_core.WAIT_S
            except Exception:
                wait_s = 120.0
            if now - float(dh["wait_since"]) > wait_s:
                why = "nothing open"
        elif dh.get("nothing_open_since"):
            # a caster's patrol (castdungeon.r_cdungeon) found no spot it rates: as the core's wait above
            try:
                import task_core
                wait_s = task_core.WAIT_S
            except Exception:
                wait_s = 120.0
            if now - float(dh["nothing_open_since"]) > wait_s:
                why = "nothing open"
        else:
            dh.pop("wait_since", None)
        if why:
            self.facts.pop("dungeon_hunt", None)
            self.__dict__.pop("_spots", None)
            # the core's tour of the dungeon ends with the hunt: left running, its travel walked BotHealAdvR back through the door 6 minutes after a stay
            # ended "out of the dungeon", alone, with no trip or kit check (3 kills, health 55 of 94, 2026-11-06 17:52)
            self.trip_drop_task("surface")
            t["stay_until"] = now
            if why not in ("a death", "out of the dungeon"):
                self.trip_return_plan(t, dh, now)
            if why not in ("a death", "kit low", "weapon lost") and now - float(dh.get("t0", now)) < DH_CUT_S:
                t["hunt_cut"] = True                            # not a visit: the ladder counts it neither way (ladder_trip_end)
            self.trip_save()
            mins = (now - float(dh.get("t0", now))) / 60.0
            self.log(f"first trip: the {side} hunt ends ({why}) after {mins:.0f} min")
            self.ev("dungeon_hunt_end", side=side, why=why, minutes=round(mins, 1), back_by=len((t.get("ret") or {}).get("legs") or []))
            return None
        self.activity = f"hunting {side}"
        return False

    def trip_drop_task(self, side):
        """A task the decision core holds for another side than the dungeon the trip just entered (a hunt, a wait, an errand; not a rest) ends ("switch",
        which bans nothing), so the core chooses again from the dungeon's spots. Left running, its travel walks the bot straight back out through the door."""
        task = self.facts.get("task")
        if not task or task.get("task") == "rest" or (task.get("side") or "surface") == side:
            return False                                 # an errand chosen before the trip goes too (its bank or shop is on the surface: BotHealAdvR's bank
                                                          # errand ended its Despise hunt in the second it entered, 2026-11-05 09:19); a kit the hunt needs
                                                          # ends it as "kit low" by itself
        try:
            import task_core
            task_core.end_task(self, task, "switch")
        except Exception as e:
            self.log(f"first trip: ending the core's {task.get('task')} failed ({type(e).__name__}: {e})")
            self.facts["task"] = None
        self.ev("dungeon_task_dropped", side=side, task=task.get("task"), area=task.get("area"), task_side=task.get("side") or "surface")
        return True

    def trip_left_inside(self):
        """True when it acted: a ladder bot on a rung dungeon's side with no trip under way crosses back to the surface (tele.tele_to_side), at most once a
        LEFT_INSIDE_GAP. BotHealAdvR's trip ended "stranded" on Despise's upper floor and it stood at the landing "waiting for an open hunting area" (the
        core sees only the surface's spots from there; 68 banned), 2026-11-04 12:59-13:13."""
        try:
            gz = _gz()
            side = gz.side(int(self.c.x), int(self.c.y)) if gz else "surface"
        except Exception:
            return False
        if side == "surface" or self.c.ghost or not hasattr(self, "tele_to_side"):
            return False
        try:
            import spots
            if side not in spots.RUNG_DUNGEONS:
                return False
        except Exception:
            return False
        now = time.time()
        if now - float(self.__dict__.get("_left_inside_at", 0) or 0) < LEFT_INSIDE_GAP:
            return False
        self.__dict__["_left_inside_at"] = now
        self.activity = f"leaving {side}"
        self.facts.pop("dungeon_hunt", None)
        self.trip_drop_task("surface")
        self.trip_stairs_to_exit(side)
        ok = self.tele_to_side("surface")
        self.log(f"first trip: no trip under way inside {side}: leaving for the surface ({'out' if ok else 'not out yet'})")
        self.ev("dungeon_left", side=side, ok=bool(ok))
        return True

    def retreat_pack_loses(self, near):
        """Under feature rating: the pack within RETREAT_NEAR is one the rating says not to take now (rating.rate_pack of its attack-on-sight kinds,
        at the hit points it has); without a rating, any pack (the old rule). Three or four lizardmen rate a fight for a fighter at 100 ("pack of 3
        (lizardman ...): rating 0.11"), yet each made the bots step through the landing-hall teleporter, 10-14 times an hour each at 70-87% health,
        until the hunt's walks ended "unreachable" and the stay ended in 12 minutes (2026-11-08 07:30-08:12)."""
        if not self.feature("rating"):
            return True
        try:
            import rating
            import task_core
            kinds = [self.mkey(m) for m in near if task_core.aggressive_kind(self.mkey(m)) and rating.creature(self.mkey(m))]
            if not kinds:
                return False
            r = rating.rate_pack(self, kinds)
            return r is None or not r.get("engage")
        except Exception:
            return True

    def r_dungeon_out(self):
        """During a dungeon hunt (feature dungeon_hunt), a pack closing in: run for the nearest teleporter of this level and step through it, as a player
        leaves a room by the stairs; the monsters stay behind (Teleporter.cs: no creatures), and the far side heals in peace (Despise's landing hall has
        no spawner) before the core walks back up. DETOUR_PACK monsters within RETREAT_NEAR tiles start it (detour.PACK, the trips' pack escape), or two
        beside the bot below half health. BotFairSwordVR, five lizardmen beside it on Despise's upper floor, drank 14 Heal potions in 3 minutes and its
        hunt ended "kit low" after 4 (2026-11-04 17:09-17:12); BotWarAdvR, meeting them one at a time, took 47 in 40 minutes on 4 drinks."""
        dh = self.facts.get("dungeon_hunt")
        if not dh or self.c.ghost:
            return False
        now = time.time()
        if now - float(self.__dict__.get("_retreat_at", 0) or 0) < RETREAT_GAP:
            return False
        try:
            import detour
            near = self.mobs(RETREAT_NEAR)
            close = [m for m in near if (getattr(m, "distance", 9) or 9) <= 1]
            pack = len(near) >= detour.PACK and self.retreat_pack_loses(near)
            pack = pack or (len(close) >= 2 and self.hp_pct() < 50)
            if not pack:
                # the pack that has seen it, before it arrives: BotMaceAdvR and BotArcherCR rated five to eight ettins at 13:30-13:32 and turned for the
                # stair only when boxed in, 44-85 tiles from it; 22 of 23 retreats that day failed (2026-11-08)
                seen = [m for m in self.mobs(RETREAT_SEE) if getattr(m, "in_war_mode", False) and not getattr(m, "is_dead", False)]
                if len(seen) >= 2 and self.retreat_pack_loses(seen):
                    near = seen
                    pack = True
        except Exception:
            return False
        if not pack:
            return False
        side = dh.get("side")
        tr = self.trip_stair_near(side, near)
        if tr is None:
            return False
        self.__dict__["_retreat_at"] = now
        self.activity = f"out of a pack by the stair at {tr['src'][0]},{tr['src'][1]}"
        if hasattr(self, "sprint"):
            self.sprint()
        before = (int(self.c.x), int(self.c.y))
        try:
            self.tele_allow(tr["dst_side"])
            self.tele_hop(tr)
        except Exception as e:
            self.log(f"first trip: the stair out of the pack: {type(e).__name__}: {e}")
        dst = (int(tr["dst"][0]), int(tr["dst"][1]))
        ok = cheb(self.c.x, self.c.y, dst[0], dst[1]) <= 3
        self.log(f"first trip: {len(near)} monsters within {RETREAT_NEAR} tiles at {before[0]},{before[1]} (hp {self.c.hp}): "
                 f"{'through' if ok else 'not through'} the teleporter at {tr['src'][0]},{tr['src'][1]}")
        self.ev("dungeon_retreat", side=side, n=len(near), hp=self.c.hp, at=list(before), stair=[int(tr["src"][0]), int(tr["src"][1])], ok=ok)
        self.retreat_tally(now)
        return True

    RETREATS_SPOT = 2          # retreats from one hunt's ground in a stay after which that hunt ends "danger" (the spot rests task_core.REST_S["danger"])

    def retreat_tally(self, now):
        """Counts the retreats from the running hunt's ground; at RETREATS_SPOT the hunt ends "danger", so the core picks other ground while that spot
        rests, as a player gives up a room that keeps driving him out. BotHealAdvR retreated six times from sp5490,676 in four minutes for one kill
        and its stay ended "kit low" (2026-11-08 20:22-20:27)."""
        task = self.facts.get("task") or {}
        area = task.get("area")
        if not area or task.get("task") not in ("hunt", "tour2"):
            return
        tally = self.__dict__.setdefault("_retreats", {})
        tally[area] = tally.get(area, 0) + 1
        if tally[area] >= self.RETREATS_SPOT:
            tally.pop(area, None)
            try:
                import task_core
                self.log(f"first trip: {self.RETREATS_SPOT} retreats from {area}: that ground is given up for now")
                task_core.end_task(self, task, "danger")
                self.facts["task"] = None
            except Exception as e:
                self.log(f"first trip: retreat tally: {type(e).__name__}: {e}")

    def trip_stair_near(self, side, threats=()):
        """The teleporter entry on this level (same walkable component, spots.component) within RETREAT_REACH tiles to run for: first one no monster stands
        in the way of (within RETREAT_LINE of the straight line to it), then one leading toward the way out (fewer inner stairs from its far side to an
        exit than from here, spots.inner_hops), then the nearest. The nearest alone sent BotMaceAdvR and BotArcherCR on Despise's ettin floor for the stair
        down to 5386,755, through the pack, while the stair they came by (5521,672) led back up (2026-11-08 13:31-13:40). Any dungeon: the gazetteer's
        teleporters and the walk graph, nothing of Despise."""
        try:
            import gazetteer
            import spots
            here = (int(self.c.x), int(self.c.y))
            comp = spots.component_near(here[0], here[1], side)
            trans = gazetteer.get().trans
            out_ids = {id(t) for _d, t in spots.outward_stairs(side, here, RETREAT_REACH)}
            pts = [(int(m.x), int(m.y)) for m in threats if getattr(m, "x", None) is not None]
            best = None
            for t in trans:
                if t.get("src_side") != side or t.get("dst_side") not in (side, "surface"):
                    continue                                        # never into another dungeon
                sx, sy = int(t["src"][0]), int(t["src"][1])
                d = cheb(here[0], here[1], sx, sy)
                if d > RETREAT_REACH or (comp is not None and spots.component(sx, sy, side) != comp):
                    continue
                blocked = any(seg_dist(here, (sx, sy), p) <= RETREAT_LINE and cheb(p[0], p[1], sx, sy) < d for p in pts)
                key = (blocked, id(t) not in out_ids, d)
                if best is None or key < best[0]:
                    best = (key, t)
            return best[1] if best else None
        except Exception:
            return None

    def trip_stairs_to_exit(self, side):
        """The inner stairs to the level of the exit tele_route picks (spots.inner_hops), each taken with tele_hop: tele_route knows only sides, so from
        another level it walks at an exit that no walk reaches. BotHealAdvR, on Despise's lizardman floor (component 5) with the exits in the landing
        hall (component 1, the stair at 5504,569 between), tried 5588,630-632 every two minutes for 50 minutes (2026-11-04 13:28-14:13)."""
        try:
            import spots
            route = self.tele_route((int(self.c.x), int(self.c.y)), "surface")
            if not route:
                return False
            src = (int(route[0]["src"][0]), int(route[0]["src"][1]))
            hops = spots.inner_hops(side, (int(self.c.x), int(self.c.y)), src) or []
        except Exception as e:
            self.log(f"first trip: the stairs to the way out: {type(e).__name__}: {e}")
            return False
        for h in hops:
            self.tele_allow(side)
            self.tele_hop(h)
            dst = (int(h["dst"][0]), int(h["dst"][1]))
            if cheb(self.c.x, self.c.y, dst[0], dst[1]) > max(2, cheb(h["src"][0], h["src"][1], dst[0], dst[1]) // 2):
                self.log(f"first trip: the stair at {h['src'][0]},{h['src'][1]} did not take the bot (at {self.c.x},{self.c.y})")
                return False
            self.log(f"first trip: up or down the stair at {h['src'][0]},{h['src'][1]} toward the way out of {side}")
        return True

    def trip_home_from(self, trip, wps):
        """The waypoint the walk home starts at: the last, but for a dungeon trip the one before its door. The door's surface tiles are teleporters both
        ways (Despise: 1296,1080-1082 to 5588,630-632 and back, teleporters.json), so a walk home to the door from the landing crossed out onto it and
        stepped back in, and three nopaths ended BotFairSwordVR's trip "stranded" a tile outside (2026-11-04 12:28); the goto wrappers cross out on
        their own (tele.tele_cross) toward the next waypoint."""
        last = len(wps) - 1
        return max(0, last - 1) if trip.get("enter") and last > 0 else last

    def trip_return_plan(self, t, dh, now):
        """After a dungeon hunt on another level than the landing: t["ret"], the inner teleporters (stairs) back to the landing (travel.plan_journey's
        plan_inner), walked a leg a tick before the walk home (trip_return_leg). tele.tele_route knows only the side, so from another level the walk to the
        door has no path: Despise's lizardmen are up the stair at 5573,629 from its landing (5503,570, teleporters.json)."""
        land = dh.get("landing")
        if not land:
            return
        try:
            import spots
            import travel
            hops = spots.inner_hops(dh["side"], (int(self.c.x), int(self.c.y)), tuple(land))
            j = travel.plan_journey(self, tuple(land)) if hops else None
        except Exception as e:
            self.log(f"first trip: the way back to the landing: {type(e).__name__}: {e}")
            return
        if j and j.get("legs"):
            t["ret"] = {"legs": j["legs"], "seg": 0, "wp": 0, "t0": now, "st": {}}
            self.log(f"first trip: back to the {dh['side']} landing by {len(hops)} stair{'s' if len(hops) != 1 else ''}")

    def trip_return_leg(self, t):
        """One tick of t["ret"] (trip_return_plan): True when it acted, False once it is done or dropped (the walk home then runs as before). A walk leg
        goes a waypoint at a time; a stair leg is travel's tele step. RETURN_S caps it: a stair it cannot take leaves the old walk home."""
        r = t.get("ret") or {}
        legs = r.get("legs") or []
        now = time.time()
        if r.get("seg", 0) >= len(legs) or now - float(r.get("t0", now)) > RETURN_S:
            if r.get("seg", 0) < len(legs):
                self.log(f"first trip: the way back to the {t['dest']} landing took over {RETURN_S} s: the walk home as it stands")
            t.pop("ret", None)
            self.trip_save()
            return False
        leg = legs[r["seg"]]
        self.activity = f"first trip: back to the {t['dest']} landing"
        if leg["kind"] == "walk":
            wps = leg.get("wps") or [leg["to"]]
            k = min(int(r.get("wp", 0)), len(wps) - 1)
            x, y = int(wps[k][0]), int(wps[k][1])
            if cheb(self.c.x, self.c.y, x, y) <= 2:
                if k >= len(wps) - 1:
                    r.update(seg=r["seg"] + 1, wp=0, st={})
                else:
                    r["wp"] = k + 1
                self.trip_save()
                return True
            self.goto_near(x, y, 1).wait(timeout=SLICE)
            return True
        import travel
        if leg["kind"] == "tele":
            # the stair itself: travel.tele_step refuses a hop to a dungeon side when the bot is not ready to ENTER one (task_core.rung_ready), and so
            # refused BotHealAdvR's stair back to the landing at 86% health ("not ready for the dungeon", 2026-11-04 12:58)
            try:
                self.tele_allow(leg["to_side"])
                self.tele_hop(leg["t"])
            except Exception as e:
                self.log(f"first trip: the stair back: {type(e).__name__}: {e}")
            land = tuple(leg["land"])
            res = "done" if cheb(self.c.x, self.c.y, land[0], land[1]) <= max(2, cheb(leg["t"]["src"][0], leg["t"]["src"][1], land[0], land[1]) // 2) else "did not jump"
        else:
            res = travel.STEPS[leg["kind"]](self, leg, r.setdefault("st", {}))
        if res == "done":
            r.update(seg=r["seg"] + 1, wp=0, st={})
        elif res != "running":
            self.log(f"first trip: the stair back to the {t['dest']} landing: {res}; the walk home as it stands")
            t.pop("ret", None)
        self.trip_save()
        return True

    def trip_drink_on_run(self):
        """trip_potions with the slice's walk already under way: the client walks on while the brain drinks (Navrey's goto returns at once). Drunk before the
        walk, a Cure stood the runner 1.4 s and a fighter with a shield 2-3 s more for the hand swap (basics.drink), and a cure, a heal and a bandage in one
        tick 4-5 s: a scorpion seen at 11 tiles was beside BotFairSwordVR 12 s later (2026-11-03 20:39)."""
        try:
            drunk = self.trip_potions()
        except Exception as e:
            self.log(f"first trip: drinking on the run failed ({type(e).__name__}: {e})")       # the leg runs on whatever a drink did
            return []
        if drunk:
            seen = self.poison_seen() if hasattr(self, "poison_seen") else None
            self.log(f"first trip: drank {', '.join(drunk)} on the run at {self.c.hp}/{self.c.max_hp}" + (f" (poison: {seen})" if seen else ""))
        return drunk

    def trip_potions(self):
        """On the run, as a player drinks while running: Cure when poisoned (beside an attacker too: there is no standing still to wait it out), Heal once
        HEAL_MISSING are gone (not while poisoned: refused), Refresh below RUN_STAM. Returns the potions drunk."""
        drunk = []
        now = time.time()
        if self.c.poisoned and now - self.facts.get("cured_at", 0) >= self.CURE_RECHECK and self.potion("cure") is not None:
            self.facts["cured_at"] = now
            if self.drink_cure("on the run"):
                drunk.append("cure")
        if not self.c.poisoned and self.c.max_hp - self.c.hp >= HEAL_MISSING and self.drink_heal("on the run"):
            drunk.append("heal")
        if self.c.max_hp - self.c.hp >= HEAL_MISSING and hasattr(self, "bandage_start") and self.bandage_start("on the run"):
            drunk.append("bandage")                       # put on while running (bot_common.bandage_start): the walk goes on
                                                          # (the owner, 2026-11-03: "you can bandage while moving")
        try:
            mx = int(self.c.state.get("maxStam") or 0)
        except Exception:
            mx = 0
        if mx > 0 and self.c.stamina < RUN_STAM * mx and now - self.facts.get("refresh_pot_at", 0) >= self.REFRESH_EVERY:
            pot = self.potion("refresh")
            if pot is not None:
                self.facts["refresh_pot_at"] = now
                if self.drink(pot):
                    drunk.append("refresh")
                    self.ev("consumable_used", item="red potion", stam=self.c.stamina, ok=True, why="on the run")
        return drunk

    def trip_step(self, t, trip):
        wps = trip["wps"]
        now = time.time()
        if now - t["pos_ev"] > 120:
            t["pos_ev"] = now
            self.ev("trip_pos", dest=t["dest"], phase=t["phase"], wp=t["i"], of=len(wps), left_to_dest=cheb(self.c.x, self.c.y, *wps[-1]))
        if self.trip_rest(t, now):
            return True
        if hasattr(self, "escort_hold") and self.escort_hold(t, now):
            return True                                         # an escort fell behind: wait for it (escort.py)
        escort = bool(hasattr(self, "escorting") and self.escorting(t))
        phase = t["phase"]
        if phase == "out" and t.get("in_home", True) and _gz():
            home_now = _gz().home_region(self.c.x, self.c.y, ("town",))
            if not (home_now and home_now["name"] == t["home"]):
                t["in_home"] = False
                self.trip_exit_seen(t)
        if phase in ("out", "stay") and not (phase == "stay" and self.facts.get("dungeon_hunt")):
            if self.feature("danger_model"):
                hard, soft, danger = None, None, self.trip_danger()                       # learned risk instead of the kind lists
            else:
                hard = next((self.trip_desc(m) for m in self.mobs(12) if any(k in self.trip_label(m) for k in HARD_KINDS)), None)
                soft = None if hard or self.trip_power() >= SOFT_POWER else self.trip_soft()
                danger = None
            why = ("hurt" if self.hp_pct() < 60 else f"danger: {danger}" if danger else f"hard kind: {hard}" if hard else f"soft kind: {soft}" if soft else "overweight" if self.c.weight >= self.c.max_weight * 0.9
                   else "too slow" if phase == "out" and now - t["t0"] > limit_of(trip) * 60 * (3 if escort else 1) else None)
            if self.trip_run_on() and phase == "out":
                # run past what cannot catch a runner; turn back for a caster, a pack, or half health with something near. The kind lists and the learned
                # risk were judged standing (a melee monster beside a standing bot), so on the run only "hurt", "overweight" and "too slow" stand from them
                turn = self.trip_turn_back(target=wps[min(t["i"], len(wps) - 1)], ahead=self.trip_route_slice(wps, t["i"], 1),
                                           behind=self.trip_route_slice(wps, t["i"] - 1, -1))
                why = f"run: {turn}" if turn else (why if why in ("hurt", "overweight", "too slow") else None)
            if why == "hurt" and self.trip_run_on() and self.trip_mend_left():
                # hurt with a heal left: mend on the way (bandage and potions on the run, r_heal standing when nothing is near), out of every
                # monster's reach first (trip_detour's hurt escape), as a player does; the walk home ran the same gauntlet back. BotFairSwordVR turned
                # back from Cove at 2035,845 with 5 drinks gone (18:07) and BotWarAdvR from Trinsic at 1734,2599 (17:02), both with potions left (owner,
                # 2026-11-03: "bandage, use potions, and run past ... not fall back to assuming its too dangerous")
                why = None
            if why and phase == "stay" and why != "hurt" and not why.startswith("run: "):
                # there already: a danger walking in ends the visit, not the trip (BotWarAdvR, in Minoc at 2499,658, aborted for an ogre that walked
                # up, and the town it had reached counted as a failed rung, 2026-11-03 13:18)
                self.log(f"first trip: leaving {t['dest']} early ({why})")
                t.update(phase="home", i=self.trip_home_from(trip, wps), best=1e9, best_at=now, fails=0, skips=0, left_early=why)
                self.trip_save()
                return True
            if why:
                self.trip_abort(why)
                return True
        if phase == "stay" and hasattr(self, "escort_return") and self.escort_return(t, now):
            return True                                         # a townsperson going home with it (escort.py)
        if phase == "stay":
            self.activity = f"looking around {t['dest']}"
            if t.get("entered") and (self.feature("dungeon_hunt") or self.facts.get("dungeon_hunt")) and self.trip_dungeon_hunt(t, now) is False:
                if now - float(self._trip.get("saved_at") or 0) > STAY_SAVE_S:
                    self.trip_save()
                return False                                    # the decision core hunts the dungeon's level 1 (trip_dungeon_hunt)
            if now - float(self._trip.get("saved_at") or 0) > STAY_SAVE_S:
                # the stay saves the trip again now and then, so a restart during it resumes (trip_load: TRIP_RESUME_S): saved only on arrival, BotFenceAdvR's
                # Trinsic stay was 10 min old at the 00:36 rollover and the trip was dropped (2026-11-04)
                self.trip_save()
            if now >= t["stay_until"]:
                t.update(phase="home", i=self.trip_home_from(trip, wps), best=1e9, best_at=now, fails=0, skips=0)
                self.trip_save()
            else:
                time.sleep(3)
            return True
        # a walk (out along the waypoints, home along them reversed): one slice per tick
        if phase == "home" and t.get("ret") and self.trip_return_leg(t):
            return True                                         # the stairs back to a dungeon's landing first (trip_return_plan)
        idx = t["i"]
        x, y = wps[idx]
        d = cheb(self.c.x, self.c.y, x, y)
        if d <= REACHED:
            if hasattr(self, "trip_gate_step"):
                g = self.trip_gate_step(t, trip, idx, phase)
                if g is not None:
                    return g                                    # the moongate between a gate trip's two walks (gate.py)
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
        slice_s = SLICE
        if escort and phase in ("out", "home"):
            slice_s = 3                                         # escort.ESCORT_SLICE: short legs, so the follower never drops past 16 tiles
        hot = self.trip_run_on() and self.trip_near()
        if not hot:
            self.__dict__.pop("_escape", None)                  # nothing in notice range: an escape, if any, is over (trip_detour runs only with one near)
        if hot:
            self.activity += " (running past)"
            if hasattr(self, "sprint"):
                self.sprint()                                   # run whatever the stamina (bot_common.sprint)
            slice_s = TRIP_HOT_SLICE
            if self.trip_detour(t, wps, (x, y)):
                return True                                     # a short leg round the threats this slice; the route is rejoined after it
        walk = self.goto_near(x, y, REACHED)
        if slice_s == TRIP_HOT_SLICE:
            self.trip_drink_on_run()                            # with the walk under way
        res = str(walk.wait(timeout=slice_s))
        if res.startswith("timeout") and slice_s == TRIP_HOT_SLICE:
            return True                                         # still running: the next tick checks the danger and the potions again
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
