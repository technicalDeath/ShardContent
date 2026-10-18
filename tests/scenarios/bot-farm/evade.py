"""r_evade only for real threats (Operator's finding from the Vesper drop test; the Helper). Mixin for BotBase, written into the bot-farm folder by patch_evade.py.

The finding: r_evade fired on any grey mobile within seven tiles except a short name list: BotFisherAR in Vesper ran from crows ("A a crow came within 6 tiles", 76 evades in
25 minutes, alternating with r_fish every two seconds) and tamers evaded mongbats the same way. A gatherer stops working and walks away only for a threat now:
 * a red / enemy-coloured mobile (notoriety Murderer or Enemy);
 * anything that attacked this bot in the last two minutes (the server's "X is attacking you!" -> facts["attacked_by"]);
 * a kind that attacks on sight: the creature's FightMode in fightmodes.json (make_fightmodes.py, from the server's classes): Closest / Strongest / Weakest attack a stranger;
   Aggressor and None only fight back, Evil only attacks a negative-karma target. Kinds whose own numbers are trivial (creature_stats.json: at most 15 hit points and a hit of
   5 or less: a mongbat) are not worth leaving work for either;
 * a kind that is not in the table (a bird class gives crows and magpies random names): only one within 3 tiles that has come closer since the last look.
Each evade says why: ev "evade" {name, species, dist, why}, at most once a minute (and still the one note per kind of the old rule).
Pure classify() for the tests; EvadeMixin.evade_threats() for the rule.
"""
import json
import os
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ON_SIGHT = ("Closest", "Strongest", "Weakest")
RED = ("Murderer", "Enemy")
ATTACK_WINDOW = 120
TRIVIAL_HITS, TRIVIAL_HIT = 15, 5
_MODES = None
_STATS = None


def _load(name):
    try:
        return json.load(open(os.path.join(HERE, name), encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def modes():
    global _MODES
    if _MODES is None:
        _MODES = _load("fightmodes.json")
    return _MODES


def stats():
    global _STATS
    if _STATS is None:
        _STATS = _load("creature_stats.json")
    return _STATS


def trivial(kind):
    s = stats().get(kind)
    if not s:
        return False
    hits, dmg = s.get("hits"), s.get("damage")
    return bool(hits and dmg and hits[1] <= TRIVIAL_HITS and dmg[1] <= TRIVIAL_HIT)


def classify(kind, notoriety, dist, prev_dist, attacked, mode_table=None):
    """Why this mobile is a threat now, or None."""
    if notoriety in RED:
        return f"red ({notoriety})"
    if attacked:
        return "attacked me"
    table = modes() if mode_table is None else mode_table
    mode = (table.get(kind) or {}).get("mode")
    if mode in ON_SIGHT:
        return None if trivial(kind) else f"attacks on sight ({mode})"
    if mode is not None:
        return None
    if dist <= 3 and prev_dist is not None and dist < prev_dist:
        return "unknown kind closing in"
    return None


class EvadeMixin:
    def evade_threats(self):
        """The mobiles within 7 tiles that r_evade should walk away from, nearest first; logs what it reacts to (once a minute)."""
        now = time.time()
        seen = self.facts.setdefault("evade_seen", {})
        attacked = self.facts.get("attacked_by", {})
        out = []
        current = {}
        for m in self.mobs(7):
            kind = self.mkey(m)
            prev = seen.get(m.serial)
            prev_dist = prev[0] if prev and now - prev[1] < 15 else None
            current[m.serial] = (m.distance, now)
            why = classify(kind, m.notoriety, m.distance, prev_dist, now - attacked.get(m.name, 0) < ATTACK_WINDOW)
            if why:
                out.append((m.distance, m, kind, why))
        seen.clear()
        seen.update(current)
        out.sort(key=lambda t: t[0])
        if out and now - self.facts.get("evade_logged", 0) > 60:
            self.facts["evade_logged"] = now
            d, m, kind, why = out[0]
            self.ev("evade", name=m.name, species=kind, dist=d, why=why)           # (not kind=: ev()'s first argument is the event kind)
        return [t[1] for t in out]
