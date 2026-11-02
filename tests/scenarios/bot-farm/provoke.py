"""Which pair a bard provokes (2026-11-01): the pair whose difficulty lets Provocation gain, from the creatures' own numbers.

Provocation.cs: diff = (GetDifficultyFor(a) + GetDifficultyFor(b)) / 2 - 5 (less (Musicianship - 100) / 2 over 100), and the check is
CheckTargetSkill(Provocation, diff - 25, diff + 25): below diff - 25 it always fails, from diff + 25 on it always succeeds, and only in between can it gain.
BaseInstrument.GetBaseDifficulty (pre-LBR): HitsMax x 0.625 + StamMax + ManaMax + SkillsTotal / 10, above 700 only 3/11 of the rest counts, +100 for a mage,
+100 for fire breath, +20 per poison level, all / 10. The bards provoked chickens (3.6) and rabbits (6.0) onto each other with Provocation 50-52, which can
never gain (the window starts at 27 for them), and gained nothing in an evening (2026-11-01 22:15-23:32). Ratmen (35), lizardmen (36) and orcs (37) are in it.
creature_stats.json holds tactics, wrestling, magery, evalint and resist; the creatures' other skills are not in it, so this is a floor."""
from __future__ import annotations

import re

import danger

POISON_LEVEL = {"Lesser": 1, "Regular": 2, "Greater": 3, "Deadly": 4, "Lethal": 5}       # GetPoisonLevel: HitPoison.Level + 1
SKILLS = ("tactics", "wrestling", "magery", "evalint", "resist")


def kind(name):
    """creature_stats key of a mobile's name (as tamer.norm): "a giant rat" -> "giantrat"."""
    return re.sub(r"[^a-z]", "", re.sub(r"^(an?|the) ", "", (name or "").lower()))


def _mid(r):
    return (r[0] + r[1]) / 2.0 if r else 0.0


def difficulty(kind):
    """GetBaseDifficulty for a creature_stats kind, or None when the kind is not in the table."""
    c = danger.stats().get(kind)
    if not c:
        return None
    v = _mid(c.get("hits")) * 0.625 + _mid(c.get("dex")) + _mid(c.get("int")) + sum(_mid(c.get(s)) for s in SKILLS if c.get(s))
    if v > 700:
        v = 700 + int((v - 700) * 3.0 / 11)
    if c.get("casts") and c.get("ai") == "AI_Mage":
        v += 100
    if c.get("breath"):
        v += 100
    v += POISON_LEVEL.get(c.get("poison") or "", 0) * 20
    return v / 10.0


def pair_diff(ka, kb, music=0.0):
    da, db = difficulty(ka), difficulty(kb)
    if da is None or db is None:
        return None
    d = (da + db) * 0.5 - 5.0
    if music > 100.0:
        d -= (music - 100.0) * 0.5
    return d


def chance(skill, d):
    """The check's success chance at this difficulty (min d - 25, max d + 25)."""
    return max(0.0, min(1.0, (skill - (d - 25.0)) / 50.0))


def can_gain(skill, d):
    return d is not None and d - 25.0 <= skill < d + 25.0


def best_pair(firsts, others, skill, music=0.0, kind_of=None):
    """(first, other, diff, gains) for the pair to provoke: one in the gain window first, the surer of those (it also has to set the fight off), else the
    hardest pair that is still sure to work. firsts: the creatures the bard wants fought (its prey); others: what they could be set on. None: no pair."""
    kind_of = kind_of or (lambda m: kind(m.name))
    best, key = None, None
    for a in firsts:
        for b in others:
            if b.serial == a.serial:
                continue
            d = pair_diff(kind_of(a), kind_of(b), music)
            if d is None:
                d = -99.0
            g = can_gain(skill, d)
            k = (1 if g else 0, chance(skill, d) if g else d)
            if key is None or k > key:
                best, key = (a, b, d, g), k
    return best
