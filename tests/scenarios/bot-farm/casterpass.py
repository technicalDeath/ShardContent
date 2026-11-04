"""What running past monster casters costs, from the engine's own numbers (UOR, pre-AOS), so a running trip goes on when the pass is affordable or
cheaper than turning back, instead of turning back at the sight of two casters (owner, 2026-11-03: "bots should be able to bandage, use potions, and
run past casters and survive most of the time").

The model, per caster in view (all from ModernUO Projects/UOContent, read 2026-11-03):
  * it casts only with the target inside the spell's TargetRange, 10 tiles in this era (ITargetingSpell.cs:8, MageAI.cs:760/777), the first cast as
    soon as it has a target (MageAI.cs:92), then every GetDelay: uniform 6 - 1.25 d .. 6 - 0.75 d s with d = 3 x Magery / 100, mean 6 - 0.03 x Magery
    (MageAI.cs:611-623);
  * a pick is a damage spell 8 of 16 times, plus the Paralyze roll at Magery 50 or less and a failed Invisibility (0.5 x Magery / 100 to succeed)
    (MageAI.cs:370-464); Poison (2 of 16) is the Cure potion's business, curses and mana drains do no damage;
  * the damage spell: Random(maxCircle x 2) over Magic Arrow 2 slots, Harm 2, Fireball 2, Lightning 2, Mind Blast 2, Energy Bolt 1, Explosion 1,
    Flamestrike the rest, maxCircle = (Magery + 20) / (100 / 7) clamped 1-8 (MageAI.cs:276-296); base damage Magic Arrow 4-7, Harm 1-15, Fireball
    10-16, Lightning 12-20, Energy Bolt 24-41, Explosion 23-44, Flamestrike 27-48 (First..Seventh/*.cs), Mind Blast (highest - lowest stat) / 2 up to 45;
    times the scalar 1 + (EvalInt - Resist) / 500 (or / 200 when Resist is higher) + (Magery - 100) / 400 (Spell.cs:279-307); a resisted spell does
    x0.75 (Flamestrike x0.6, Mind Blast x0.5) with the chance max(RS / 5, RS - ((Magery - 20) / 5 + (1 + circle) x 5)) / 2 (MagerySpell.cs:61-97);
    a cast fizzles unless (Magery - 10 x circle) / 40 succeeds (MagerySpell.cs:17, SkillCheck.cs:61-79);
  * a reaper and a corpser never move (DisallowAllMoves, Reaper.cs:53, Corpser.cs); any other caster chases at its npc-speeds.json activeMove (Medium
    0.45 s a tile, Fast 0.3) against a runner's 0.2 (movement.delay.runFoot), so after its nearest point it stays in range (10 - d) / (5 - 1/move) s more.
Line of sight is ignored (it only lowers the cost: MageAI.cs:700-713 casts nothing without it).
"""
from __future__ import annotations

import json
import math
import os
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

SPELL_RANGE = 10
RUN_S = 0.2                                  # movement.delay.runFoot: seconds a tile on foot, running
IMMOBILE = {"reaper", "corpser"}             # DisallowAllMoves (the era's monsters; Harrower and its tentacles are not in this world)
HEAL_DELAY = 10.0                            # BaseHealPotion.Delay
HEAL_MEAN = 13.0                             # a pre-AOS Heal potion restores 6-20 (HealPotion.cs MinHeal/MaxHeal)
# (name, base min, base max, 0-based circle, resisted factor) by slot of Random(maxCircle x 2)
SPELLS = [("magic arrow", 4, 7, 0, 0.75), ("magic arrow", 4, 7, 0, 0.75), ("harm", 1, 15, 1, 0.75), ("harm", 1, 15, 1, 0.75),
          ("fireball", 10, 16, 2, 0.75), ("fireball", 10, 16, 2, 0.75), ("lightning", 12, 20, 3, 0.75), ("lightning", 12, 20, 3, 0.75),
          ("mind blast", None, None, 4, 0.5), ("mind blast", None, None, 4, 0.5), ("energy bolt", 24, 41, 5, 0.75), ("explosion", 23, 44, 5, 0.75)]
FLAMESTRIKE = ("flamestrike", 27, 48, 6, 0.6)
WORKSPACE = r"C:\Users\brend\Documents\Britannia Renaissance"      # (a copy of this folder elsewhere, a gate's tree, still finds the server's data)
_SPEEDS: Optional[Dict[str, float]] = None


def _speeds() -> Dict[str, float]:
    """{class name lower: activeMove s a tile} from the server's npc-speeds.json."""
    global _SPEEDS
    if _SPEEDS is None:
        _SPEEDS = {}
        here = os.path.dirname(os.path.abspath(__file__))
        for p in (os.path.join(here, "..", "..", "..", "..", "ModernUO", "Distribution", "Data", "npc-speeds.json"),
                  os.path.join(WORKSPACE, "ModernUO", "Distribution", "Data", "npc-speeds.json")):
            try:
                for lvl in json.load(open(p, encoding="utf-8")):
                    for t in lvl.get("types") or []:
                        _SPEEDS[t.lower()] = float(lvl["activeMove"])
                break
            except (OSError, ValueError, KeyError):
                continue
    return _SPEEDS


def _mid(r, default):
    try:
        return (float(r[0]) + float(r[1])) / 2.0
    except Exception:
        return default


def max_circle(magery: float) -> int:
    return max(1, min(8, int((magery + 20) / (100 / 7))))


def scalar(evalint: float, magery: float, resist: float) -> float:
    s = 1 + (evalint - resist) / (500.0 if evalint > resist else 200.0)
    return s + (magery - 100) / 400.0


def resist_chance(rs: float, magery: float, circle: int) -> float:
    return max(0.0, min(1.0, max(rs / 5.0, rs - ((magery - 20) / 5.0 + (1 + circle) * 5)) / 2.0 / 100.0))


def success(magery: float, circle: int) -> float:
    return max(0.0, min(1.0, (magery - 10 * circle) / 40.0))


def damage_share(magery: float) -> float:
    """Share of the picks that are a damage spell (MageAI.ChooseSpell, a target neither poisoned nor paralyzed)."""
    extra = (1.0 if magery <= 50 else 0.0) + (1.0 - min(1.0, 0.5 * magery / 100.0))
    return (8.0 + extra) / 16.0


def per_cast(entry: dict, rs: float, stats: Tuple[float, float, float]) -> Tuple[float, float]:
    """(expected damage of one cast, the largest one spell can do) for a creature entry (creature_stats.json) against a target with Magic Resistance rs."""
    m = _mid(entry.get("magery"), 0.0)
    ei = _mid(entry.get("evalint"), m)
    if m <= 0:
        return 0.0, 0.0
    sc = max(0.0, scalar(ei, m, rs))
    slots = max_circle(m) * 2
    total, top = 0.0, 0.0
    for i in range(slots):
        name, lo, hi, c, rf = SPELLS[i] if i < len(SPELLS) else FLAMESTRIKE
        if lo is None:                                    # Mind Blast: half the spread of the target's stats, up to 45
            base = min(45.0, (max(stats) - min(stats)) / 2.0)
            hi_ = base
        else:
            base, hi_ = (lo + hi) / 2.0, float(hi)
        p = resist_chance(rs, m, c)
        dmg = base * sc * (1 - p + p * rf)
        total += success(m, c) * max(0.0, dmg - 0.5) / slots          # (truncated to whole points)
        top = max(top, hi_ * sc)
    return damage_share(m) * total, top


def interval(entry: dict) -> float:
    return max(0.75, 6.0 - 0.03 * _mid(entry.get("magery"), 0.0))


def move_s(kind: str, entry: dict) -> Optional[float]:
    """Seconds a tile it chases at, None for one that never moves."""
    if kind in IMMOBILE:
        return None
    return _speeds().get(str(entry.get("class") or kind).lower(), 0.45)


def dense(path: Sequence[Tuple[int, int]]) -> List[Tuple[int, int]]:
    """Every tile along the path's straight legs (the route's waypoints are tens of tiles apart)."""
    out: List[Tuple[int, int]] = []
    for a, b in zip(path, path[1:]):
        n = max(abs(b[0] - a[0]), abs(b[1] - a[1]), 1)
        for i in range(1 if out else 0, n + 1):
            out.append((round(a[0] + (b[0] - a[0]) * i / n), round(a[1] + (b[1] - a[1]) * i / n)))
    return out or list(path)


def exposure_s(tiles: Sequence[Tuple[int, int]], at: Tuple[int, int], move: Optional[float], run_s: float = RUN_S) -> float:
    """Seconds a runner on these tiles stays inside a caster's spell range: the tiles inside it, plus for a chaser the time it keeps up after the nearest.
    `run_s` the runner's seconds a tile (RUN_S on foot, ride.MOUNT_RUN_S mounted)."""
    inside = [max(abs(p[0] - at[0]), abs(p[1] - at[1])) for p in tiles]
    n = sum(1 for d in inside if d <= SPELL_RANGE)
    if not n:
        return 0.0
    secs = n * run_s
    if move is not None:
        gain = 1.0 / run_s - 1.0 / move                   # tiles a second the runner gains
        dmin = min(inside)
        secs += (SPELL_RANGE - dmin) / gain if gain > 0 else 30.0
    return secs


def pass_damage(tiles: Sequence[Tuple[int, int]], casters: Iterable[Tuple[str, dict, Tuple[int, int]]], rs: float,
                stats: Tuple[float, float, float], run_s: float = RUN_S) -> Tuple[float, float, float]:
    """(expected damage, seconds exposed in all, the largest single spell) for running these tiles past these casters (kind, entry, position)."""
    total, secs, top = 0.0, 0.0, 0.0
    for kind, entry, at in casters:
        e = exposure_s(tiles, at, move_s(kind, entry), run_s)
        if e <= 0:
            continue
        dmg, hit = per_cast(entry, rs, stats)
        total += (e / interval(entry) + 1.0) * dmg       # the first cast comes at once (MageAI.cs:92)
        secs += e
        top = max(top, hit)
    return total, secs, top


UNCURABLE = 10 ** 6                          # a contact with a monster whose poison the bot's cures cannot answer: never "affordable" (detour.POISON_CLEAR)


def melee_contact(tiles: Sequence[Tuple[int, int]], at: Tuple[int, int], move: Optional[float], run_s: float = RUN_S) -> bool:
    """True when a melee monster at `at` can stand beside some tile of the runner's path by the time the runner gets there (tile i at i x RUN_S s; the
    monster closes at 1 / move tiles a second, npc-speeds.json; one that never moves only beside the path itself)."""
    for i, p in enumerate(tiles):
        d = max(abs(p[0] - at[0]), abs(p[1] - at[1]))
        if d <= 1:
            return True
        if move is not None and d - 1 <= (i * run_s) / move:
            return True
    return False


def pass_cost(tiles: Sequence[Tuple[int, int]], monsters: Iterable[Tuple[str, dict, Tuple[int, int], bool, bool]], rs: float,
              stats: Tuple[float, float, float], run_s: float = RUN_S) -> Tuple[float, float, float]:
    """(expected damage, seconds in spell range, the largest single blow) for running these tiles past these monsters (kind, entry, position, caster,
    uncurable poison): casters as pass_damage; a melee monster that can reach the path costs one swing at its mean damage (the runner, 0.2 s a tile
    against 0.45 or 0.6, is past before a second), a contact with an uncurable poisoner UNCURABLE."""
    casters = [(k, e, at) for k, e, at, c, _p in monsters if c]
    total, secs, top = pass_damage(tiles, casters, rs, stats, run_s)
    for kind, entry, at, caster, poison in monsters:
        if caster or not melee_contact(tiles, at, move_s(kind, entry), run_s):
            continue
        lo_hi = entry.get("damage") or [0, 0]
        total += UNCURABLE if poison else _mid(lo_hi, 0.0)
        top = max(top, float(lo_hi[1]) if len(lo_hi) > 1 else 0.0)
    return total, secs, top


def affordable(hp: float, heal_potions: int, damage: float, secs: float, top: float) -> bool:
    """The pass leaves at least one of its largest spells in hand, with the Heal potions drinkable in its time (one each HEAL_DELAY)."""
    heals = min(heal_potions, int(secs // HEAL_DELAY) + 1) * HEAL_MEAN if heal_potions else 0.0
    return hp + heals - damage >= top
