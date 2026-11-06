"""The bard's Peacemaking in a fight (feature "bard_peace"; owner, 2026-11-05: "NEW bot capabilities"). The bards played Peacemaking only with nobody near,
to practise (hunter.r_music), and died 11 and 20 times with the skill at 97-99. The engine (Skills/Peacemaking.cs, Mobiles/BaseCreature.cs):
  - targeted Peacemaking on a creature: success by CheckTargetSkill(Peacemaking, diff - 25, diff + 25), diff its instrument difficulty less 10 (less half
    the Musicianship over 100); a calmed creature drops its combatant and war mode and stands for 100 - diff / 1.5 s, held to 10-120 (Pacify);
  - the next skill use waits 5 s after a success, 10 s after a failure (NextSkillTime, UOR);
  - damage wakes a calmed creature only with chance (HitsMax - Hits) x 0.001 a hit (BaseCreature.OnDamage), so the bard shoots it while it stands.
r_peace (a reflex, ahead of the flight): a caster in war mode within the bard's range (8 + skill / 15, BaseInstrument.GetBardRange: about 14 tiles
at 97), else a creature in war mode within FOE_R tiles, not calmed by this bard, at a chance of PEACE_MIN or more (provoke.difficulty, the creature
table's floor), the most difficult first: calmed, then the fight goes on against it; a calmed caster casts nothing (the owner's "run past casters"). Events: peace {target, chance,
ok, secs, foes}.
"""
from __future__ import annotations

import time

FOE_R = 3                  # tiles: a creature this close in war mode is in the fight
CASTER_FIRST = True        # a caster in war mode within the bard's range is calmed before it casts, ahead of what is beside the bard
PEACE_MIN = 0.6            # the chance at which a bard plays rather than shoots
MIN_SKILL = 30.0


def bard_range(skill):
    """Tiles a bard's music reaches: 8 + skill / 15 (BaseInstrument.GetBardRange)."""
    return 8 + int(float(skill or 0) // 15)


def is_caster(kind):
    """A kind that hurts at range: spells or breath (creature_stats via danger.stats, as first_trip.trip_caster)."""
    try:
        import danger
        c = danger.stats().get(kind) or {}
        return bool(c.get("casts") or c.get("breath"))
    except Exception:
        return False


def calm_seconds(diff):
    """How long a calmed creature stands: 100 - diff / 1.5, held to 10-120 (Peacemaking.cs)."""
    return max(10.0, min(120.0, 100.0 - float(diff) / 1.5))


class PeaceMixin:
    def peace_on(self):
        return self.feature("bard_peace") and float((getattr(self, "skill_values", {}) or {}).get("Peacemaking", 0)) >= MIN_SKILL

    def peace_calmed(self):
        """{serial: until} of the creatures this bard calmed, past ones dropped."""
        now = time.time()
        d = self.__dict__.setdefault("_calmed", {})
        for s in [s for s, u in d.items() if u <= now]:
            d.pop(s, None)
        return d

    def peace_pick(self):
        """(mobile, chance, diff) to calm now, or None."""
        import provoke
        sk = getattr(self, "skill_values", {}) or {}
        skill, music = float(sk.get("Peacemaking", 0) or 0), float(sk.get("Musicianship", 0) or 0)
        calmed = self.peace_calmed()
        best = None
        reach = bard_range(skill)
        for m in self.mobs(reach):
            if str(m.serial) in calmed or not getattr(m, "in_war_mode", False):
                continue
            caster = CASTER_FIRST and is_caster(provoke.kind(m.name))
            if not caster and (getattr(m, "distance", 99) or 99) > FOE_R:
                continue                                    # past FOE_R only a caster is calmed (it hurts from there)
            if (m.name or "").startswith("Bot") or getattr(m, "notoriety", "") in ("Innocent", "Ally", "Invulnerable"):
                continue
            base = provoke.difficulty(provoke.kind(m.name))
            if base is None:
                continue
            diff = base - 10.0 - (max(0.0, music - 100.0) * 0.5)
            ch = provoke.chance(skill, diff)
            if ch < PEACE_MIN:
                continue
            key = (caster, base)
            if best is None or key > best[3]:
                best = (m, ch, diff, key)
        return best[:3] if best else None

    def r_peace(self):
        """Feature bard_peace: calm the creature in the fight that is hardest and still sure enough (the module doc)."""
        if not self.peace_on() or self.c.ghost:
            return False
        now = time.time()
        if now < float(self.__dict__.get("_peace_next", 0) or 0):
            return False
        try:
            pick = self.peace_pick()
        except Exception:
            pick = None
        if pick is None:
            return False
        m, ch, diff = pick
        foes = len([x for x in self.mobs(FOE_R) if getattr(x, "in_war_mode", False)])
        self.activity = f"calming {m.name}"
        res = self.play("peacemaking", [m.serial]) or ""
        ok = "calming your target" in res.lower() or "hypnotic music" in res.lower()
        secs = calm_seconds(diff)
        self.__dict__["_peace_next"] = time.time() + (5.0 if ok else 10.0)
        if ok:
            self.peace_calmed()[str(m.serial)] = time.time() + secs
        self.ev("peace", target=self.mkey(m), chance=round(ch, 2), ok=ok, secs=round(secs) if ok else 0, foes=foes)
        self.log(f"peacemaking on {m.name} (chance {ch:.0%}): {'calmed for ' + str(round(secs)) + ' s' if ok else 'failed'}; {foes} in the fight")
        return True
