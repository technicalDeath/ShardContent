"""Fast short-range routing from live conditions: the next few seconds of a walk, decided from the monsters in view (owner, 2026-11-03: "bots
definitely need the ability to do very fast short route planning based on live conditions nearby", "keep their distance as they run past",
"take a short term pathing route that leads them away from danger as fast as possible").

The long route (walkroute.plan) is decided once, from what the bots know ahead of time (lairs, deaths). It cannot see the gargoyle that wandered
out: BotHealAdvR, at full health on its way to Covetous, turned back at 1930,1267 because one came within 8 tiles of the planned line, and the
turn-back walked the same line home (2026-11-03 11:43). This module looks at the live threats, the next point of the long route and the walk
map, and picks the leg to run now:

  * no threat near the straight way on: no detour (the walk goes on as planned);
  * otherwise a STEP-tile leg in a fan round the way on, each candidate a straight walkable line (walkroute.leg_clear: microseconds a call),
    scored by its clearance from every threat (a caster wants CASTER_CLEAR, a melee monster MELEE_CLEAR) and by its progress toward the way on;
    behind is a candidate too, chosen only when every leg forward is worse;
  * escape_leg: the same fan with progress ignored: the fastest way out of reach, wherever it points.

Every number is the engine's or the walk's:
  SPELL_RANGE 10  a spell's target range in this era (ITargetingSpell.TargetRange: Core.T2A ? 10 : 12) and the range the mage AI casts from
                  (MageAI: the spell's TargetRange); gargoyles (Magery 70-85) and air elementals (60-75) are AI_Mage
  NOTICE 14       a monster notices at BaseCreature.DefaultRangePerception 16 less the shard's monsterAggro.rangeReduction 2 (first_trip.TRIP_HOT)
  STEP 10         tiles a runner covers in one 2 s slice of a running trip (first_trip.TRIP_HOT_SLICE) at movement.delay.runFoot 200 ms a tile
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, Iterable, List, Optional, Sequence, Tuple

SPELL_RANGE = 10
NOTICE = 14
CASTER_CLEAR = SPELL_RANGE + 2            # out of spell range with one step to spare
POISON_CLEAR = 9                          # a monster whose poison the shops' Lesser Cure cannot cure (pre-AOS 15% for Greater, 0 for Deadly and Lethal,
                                          # LesserCurePotion.cs _oldLevelInfo; a poisoned player cannot drink a Heal potion): two of a Medium chaser's 2 s legs
                                          # (4.4 tiles each), so a drink or a short leg still leaves one. A scorpion (Greater 80%, Deadly 20%, Scorpion.cs:57)
                                          # took BotFairSwordVR from 71 to 0 through five Cure potions (2026-11-03 20:39-20:40)
POISON_LEVELS = ("Regular", "Greater", "Deadly", "Lethal")    # kept POISON_CLEAR off: a Lesser Cure clears Regular only half the time (0.50) and each bite
                                                               # poisons again: giant spiders took BotFenceAdvR 78 -> 31 through seven cures on the Skara
                                                               # Brae road (2026-11-03 23:28-23:29)
UNCURABLE_LEVELS = ("Greater", "Deadly", "Lethal")            # a contact never affordable (casterpass.UNCURABLE): 15% and 0% with a Lesser Cure
MELEE_CLEAR = 5                           # a Medium melee monster (0.45 s a tile, npc-speeds.json: orcs, trolls, scorpions, ratmen) covers 4.4 tiles in
                                          # one 2 s leg; 2 let BotFairSwordVR run into three earth elementals and a scorpion at 1 tile (99 -> 11 hp,
                                          # 2026-11-03 18:08)
STEP = 10
PACK = 3                                  # this many in view with one already in reach: escape out of every reach, not a leg on past them (first_trip.TRIP_PACK).
                                          # BotFairArcherVR, at full health, took a 'detour ... clearance 1, gain 9' with a ratman beside it and three more in view, ran
                                          # into three giant spiders and the ratmen at 1591,2586, was boxed in and died from 92 in 24 s (2026-11-04 02:16:53-02:17:34)
ANGLES = (0, 20, -20, 40, -40, 60, -60, 90, -90, 120, -120, 150, -150, 180)
CLEAR_CAP = 8                             # clearance beyond this many tiles counts the same: past it, progress decides
SAMPLE = 2                                # tiles between the points of a leg its clearance is measured at

Point = Tuple[int, int]


@dataclass(frozen=True)
class Threat:
    x: int
    y: int
    caster: bool
    name: str = ""
    poison: bool = False                  # its poison is beyond the bot's cures (poisons())

    @property
    def need(self) -> int:
        return CASTER_CLEAR if self.caster else POISON_CLEAR if self.poison else MELEE_CLEAR


@dataclass(frozen=True)
class Leg:
    to: Point
    kind: str                             # "detour" (still gains on the way on) or "escape" (gains none)
    clearance: int                        # at the leg's end: the least (distance to a threat - what that threat needs)
    progress: int                         # tiles gained toward the way on (negative: away)
    dip: int = 0                          # how much closer than now the leg comes to a threat's need on the way (0: never closer)


def poisons(kind: str, levels=POISON_LEVELS) -> bool:
    """True for a kind whose hit poison is at one of these levels (creature_stats.json "poison", danger.stats): Regular or worse by default."""
    try:
        import danger
        return str((danger.stats().get(kind) or {}).get("poison")) in levels
    except Exception:
        return False


def uncurable(kind: str) -> bool:
    """True for a kind whose poison the shops' Lesser Cure clears a quarter of the time or never (Greater or worse)."""
    return poisons(kind, UNCURABLE_LEVELS)


def cheb(a: Point, b: Point) -> int:
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def clearance_at(p: Point, threats: Sequence[Threat]) -> int:
    return min((cheb(p, (t.x, t.y)) - t.need for t in threats), default=10 ** 6)


def leg_points(a: Point, b: Point) -> List[Point]:
    n = max(1, cheb(a, b) // SAMPLE)
    return [(round(a[0] + (b[0] - a[0]) * i / n), round(a[1] + (b[1] - a[1]) * i / n)) for i in range(1, n + 1)]


def leg_clearance(a: Point, b: Point, threats: Sequence[Threat]) -> int:
    return min(clearance_at(p, threats) for p in leg_points(a, b))


def toward(a: Point, b: Point, dist: int) -> Point:
    d = cheb(a, b)
    if d <= dist:
        return b
    return (round(a[0] + (b[0] - a[0]) * dist / d), round(a[1] + (b[1] - a[1]) * dist / d))


def fan(here: Point, heading: Tuple[float, float], dist: int = STEP, angles: Iterable[int] = ANGLES) -> List[Tuple[int, Point]]:
    """(angle, point) at dist tiles round the heading, the straight way first."""
    hx, hy = heading
    out = []
    for a in angles:
        r = math.radians(a)
        vx, vy = hx * math.cos(r) - hy * math.sin(r), hx * math.sin(r) + hy * math.cos(r)
        k = max(abs(vx), abs(vy), 1e-9)
        out.append((a, (here[0] + round(dist * vx / k), here[1] + round(dist * vy / k))))
    return out


def heading_to(a: Point, b: Point) -> Tuple[float, float]:
    dx, dy = b[0] - a[0], b[1] - a[1]
    n = math.hypot(dx, dy) or 1.0
    return dx / n, dy / n


def needs_detour(here: Point, goal: Point, threats: Sequence[Threat]) -> bool:
    """True when the straight way on (STEP tiles of it) comes inside a threat's need."""
    return bool(threats) and leg_clearance(here, toward(here, goal, STEP), threats) < 0


def judge(here: Point, p: Point, threats: Sequence[Threat]) -> Tuple[int, int]:
    """(clearance at the leg's end, dip): the dip is how far the leg comes closer than here is to a threat's need (0 when it never does). The
    start is shared by every leg, so judging a leg by its worst point would score every leg alike once a caster is already inside 12 tiles
    (BotHealAdvR, a gargoyle at 7 and a gazer at 10 at 1929,1297, 2026-11-03 13:37: no leg could ever read clear)."""
    start = clearance_at(here, threats)
    along = leg_clearance(here, p, threats)
    return clearance_at(p, threats), min(0, along - start)


def plan_leg(here: Point, goal: Point, threats: Sequence[Threat], walkable_leg: Callable[[Point, Point], bool],
             forbidden: Optional[Callable[[Point], bool]] = None) -> Optional[Leg]:
    """The leg to run now toward goal (the next point of the long route), or None when the way on is clear (no detour) or nothing walkable is
    better. A leg's score: its end clearance (capped at CLEAR_CAP) and its dip, each times 3, plus its progress."""
    if not needs_detour(here, goal, threats):
        return None
    best, best_score = None, None
    start = clearance_at(here, threats)
    for _a, p in fan(here, heading_to(here, goal)):
        if p == here or not walkable_leg(here, p) or (forbidden is not None and forbidden(p)):
            continue
        end, dip = judge(here, p, threats)
        prog = cheb(here, goal) - cheb(p, goal)
        if start < 0:
            # inside a threat's reach: getting out comes first; progress counts only for a leg that also gets further out (BotHealAdvR ran three
            # forward legs with a gazer at 1 tile and died, 2026-11-03 14:38)
            score = min(end, CLEAR_CAP) * 6 + dip * 3 + (prog if end > start else -abs(prog))
        else:
            score = min(end, CLEAR_CAP) * 3 + dip * 3 + prog
        if best_score is None or score > best_score:
            best, best_score = Leg(p, "detour" if prog > 0 else "escape", end, prog, dip), score
    return best


def escape_leg(here: Point, threats: Sequence[Threat], walkable_leg: Callable[[Point, Point], bool], prefer: Optional[Point] = None,
               forbidden: Optional[Callable[[Point], bool]] = None, fixed: Optional[set] = None) -> Optional[Leg]:
    """The fastest way out of reach: the fan round the direction away from the threats (their centre, casters counted twice), scored by clearance
    alone; prefer (a refuge, the way home) breaks ties. None when no leg is walkable."""
    if not threats:
        return None
    # the way out is away from what can follow: a monster that never moves (fixed, casterpass.IMMOBILE) steers it only while the bot is inside its
    # reach. Two reapers to the north pushed BotFairArcherVR's escapes south, leg after leg, into a giant-spider camp (2026-11-04 04:50-04:51); the
    # fixed ones still count in every leg's clearance below
    steer = [t for t in threats if not fixed or (t.x, t.y) not in fixed or clearance_at(here, [t]) < 0] or list(threats)
    w = [(t, 2 if t.caster else 1) for t in steer]
    cx = sum(t.x * k for t, k in w) / sum(k for _, k in w)
    cy = sum(t.y * k for t, k in w) / sum(k for _, k in w)
    away = heading_to((round(cx), round(cy)), here) if (round(cx), round(cy)) != here else (1.0, 0.0)
    best, best_score = None, None
    for _a, p in fan(here, away):
        if p == here or not walkable_leg(here, p) or (forbidden is not None and forbidden(p)):
            continue
        end, dip = judge(here, p, threats)
        tie = -cheb(p, prefer) / 1000.0 if prefer else 0.0
        score = min(end, CLEAR_CAP * 2) + dip + tie
        if best_score is None or score > best_score:
            best, best_score = Leg(p, "escape", end, -cheb(p, prefer) + cheb(here, prefer) if prefer else 0, dip), score
    return best
