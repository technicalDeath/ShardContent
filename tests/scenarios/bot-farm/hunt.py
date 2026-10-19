"""Casters' hunting ground from the spawner files, behind the feature "caster_hunt" (the Helper; Operator item 2026-10-17).

The finding: casters spent 60-95% of their time in r_explore and 1% fighting; what they looked at was cats (242 assess lines in a night), rats and dogs, because the ground choice
(caster_ground) only knows cells where something was SEEN, and critters are no prey from skill 35. hunt_spots.json (make_hunt_spots.py) lists what each spawner near Britain
spawns. HuntMixin.hunt_spot() scores every spot with the same numbers as Knowledge.assess for THIS caster (its Magery, hit points, mana): a kind it kills in a few casts
without taking more than 60% of its health is worth (count x 1..2, more the more casts it takes up: they train Magery), a kind it cannot fight costs 1.5 per spawn. Spots with a
kind in the memory's deadly list, a recent death within 50 tiles or another bot already there are skipped. Meditation between pulls is mage_bot.r_rest (it already runs).
Event: hunt_spot {spot, score, fightable, avoid, from_britain}.
"""
import json
import os
import random
import time

HERE = os.path.dirname(os.path.abspath(__file__))


PETS = {"cat", "dog", "bird", "chicken", "cow", "sheep", "pig", "goat", "rabbit", "hind", "greathart", "eagle", "bull", "snake", "rat"}


class _Fake:
    def __init__(self, name):
        self.name = name
        self.species = None


def load_spots():
    try:
        return json.load(open(os.path.join(HERE, "hunt_spots.json"), encoding="utf-8"))["spots"]
    except (OSError, ValueError, KeyError):
        return []


_GOLD = None


def kind_gold(cls):
    """Estimated gold a kill of cls carries: kinds with negative karma have loot, about 10 + fame / 20, at most 60; animals none (patch_caster_budget.py)."""
    global _GOLD
    if _GOLD is None:
        try:
            _GOLD = json.load(open(os.path.join(HERE, "creature_stats.json"), encoding="utf-8"))
        except (OSError, ValueError):
            _GOLD = {}
    c = _GOLD.get(str(cls).lower()) or {}
    karma, fame = c.get("karma") or 0, c.get("fame") or 0
    if isinstance(karma, list):
        karma = sum(karma) / len(karma) if karma else 0
    if isinstance(fame, list):
        fame = sum(fame) / len(fame) if fame else 0
    return 0.0 if karma >= 0 else min(60.0, 10.0 + fame / 20.0)


class HuntMixin:
    def hunt_gold_value(self, kind):
        """What a fightable kind's gold adds to a spawner's worth: 1.0 per 40 gold for a poor caster (gold + bank < 300), else 0.25 per 40."""
        poor = (getattr(self.c, "gold", 0) or 0) + ((getattr(self, "facts", None) or {}).get("bank_balance", 0) or 0) < 300
        return kind_gold(kind["cls"]) / 40.0 * (1.0 if poor else 0.25)

    HUNT_SPOTS = None
    HUNT_RANGE = 260                                     # spawner grounds are chosen up to this far (Chebyshev) from Britain

    def hunt_leash(self):
        return self.HUNT_RANGE + 15 if self.feature("caster_hunt") else self.CASTER_LEASH

    def hunt_kind_value(self, kind):
        """(value per spawned creature, cost per spawned creature) for this caster against kind."""
        m = self.k.monsters.get(kind["cls"])
        if not m or kind["cls"] in PETS:
            return 0.0, 0.0                              # town animals and farm stock are no prey
        if kind["cls"] in {d.replace(" ", "") for d in self.mem.deadly_kinds()}:
            return 0.0, 1.5
        name = m.get("name") or kind["cls"]
        hp = max(self.c.max_hp, 1)
        mana = max(int(self.c.state.get("maxMana") or 0), int(self.c.mana or 0), 50)       # a full pool: a caster at 43 now has more when rested
        regs = {r: 99 for r in ("SulfurousAsh", "SpidersSilk", "Nightshade", "MandrakeRoot", "Ginseng", "Garlic", "Bloodmoss", "BlackPearl")}
        a = self.k.assess(_Fake(name), hp, mana, getattr(self, "skill", 0.0), regs)
        if not a.get("known") or not a.get("fight"):
            return 0.0, 1.5
        casts = a.get("casts") or 1
        frac = (a.get("expected_damage") or 0) / hp
        if casts < 2:
            return 0.5, 0.0                              # dies at once: every cast still trains, but there is little to cast at
        if frac > 0.25:
            return 0.0, 0.5                              # a hard fight, and these come in packs
        return (1.0 + min(1.0, casts / 8.0)) * (1.0 - frac), 0.0

    def hunt_spot(self):
        """[score, x, y, spot] for the best spawner for this caster, or None."""
        if HuntMixin.HUNT_SPOTS is None:
            HuntMixin.HUNT_SPOTS = load_spots()
        recent = self.facts.get("spots_reached", [])[-2:]
        deaths = self.facts.get("death_spots", [])
        vals = []
        why = {"range": 0, "no_value": 0, "recent": 0, "overlap_threat": 0, "hard_kind": 0, "crowded": 0}
        for sp in HuntMixin.HUNT_SPOTS:
            x, y = sp["x"], sp["y"]
            if self.britain_dist(x, y) > self.HUNT_RANGE:
                why["range"] += 1
                continue
            val = cost = 0.0
            good = []
            for k in sp["kinds"]:
                v, c = self.hunt_kind_value(k)
                if v:
                    v += self.hunt_gold_value(k)                    # loot pays for the reagents (patch_caster_budget.py)
                val += v * k["n"]
                cost += c * k["n"]
                if v:
                    good.append(k["cls"])
            vals.append((sp, val, cost, good))
        threats = [(sp["x"], sp["y"], sp["home"]) for sp, val, cost, good in vals if cost >= 5.0 and cost > val]
        scored = []
        for sp, val, cost, good in vals:
            x, y = sp["x"], sp["y"]
            if any(abs(x - rx) < 20 and abs(y - ry) < 20 for rx, ry in recent) or any(abs(x - dx) < 50 and abs(y - dy) < 50 for dx, dy in deaths):
                why["recent"] += 1
                continue
            if val < 2.5 or cost > 0:
                why["no_value" if val < 2.5 else "hard_kind"] += 1
                continue                                  # any kind it cannot beat (a shade, a wraith, a spectre) rules the whole spawner out
            gap = min([max(abs(x - tx), abs(y - ty)) - th - sp["home"] for tx, ty, th in threats if (tx, ty) != (x, y)] or [999])
            if gap < 0:
                why["overlap_threat"] += 1
                continue                                  # its animals roam into a pack of something it cannot fight
            cell = f"{x // 40 * 40},{y // 40 * 40}"
            if self.caster_load(cell) >= 2:
                why["crowded"] += 1
                continue
            score = val - cost - self.britain_dist(x, y) / 100.0 - max(0.0, 40 - gap) / 20.0 - max(abs(x - self.c.x), abs(y - self.c.y)) / 150.0
            if self.feature("hunt_rates"):
                score += self.gr_bonus(cell)
            scored.append((score, x, y, sp, good))
        self.hunt_why = ",".join(f"{k}={v}" for k, v in why.items() if v) or "no spots"
        if not scored:
            return None
        top = max(s[0] for s in scored)
        pick = random.choice([s for s in scored if s[0] >= top - 0.25 * abs(top)])
        return pick
