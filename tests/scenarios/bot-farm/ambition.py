"""Ambitions (R4, 2026-10-17; feature "ambitions"): every bot is a persona with a main and a secondary ambition (the watcher's A1-A8,
work/botfarm-watch/player-likeness-goals.md), knows which milestone of each it is on, and its ambitions, not a hand-made features.json cohort,
decide which of its long-term behaviours it uses:

  A1 home         save: the savings goal (goals.py) is on; milestones: 4,000 / 10,000 / 16,000 (a small house deed on this shard) banked and carried
  A2 livelihood   save; milestones: net worth rising 100 / 250 / 500 gold an hour (over the last two hours)
  A3 mastery      milestones: the working skill at 70 / 80 / 90 / 100
  A4 adventure    first trips out of the home town (never the Britain sewers: owner, 2026-10-18) (first_trip.py; its own gates still apply: a veteran, an hour played, 300 gold, the kit, the
                  trip's skill band and hit points, a safe route); milestones: another region seen / a trip completed / a dungeon seen
  A5 possessions  save (the gear goals: the next armour piece it can wear); milestones: worn armour 10 / 20 / 30
  A6 renown, A7 company: the persona carries them (talk and party read them later); no milestones yet (no fame or trade numbers exported)

Personas by profession (the watcher's mix): crafters A2+A1, fighters A4 or A5 (by name) + A6, tamers A5+A4, mages A3+A4, gatherers A2+A1; one bot
in five (by name) has company (A7) as its main ambition and its profession's main as its secondary. The persona is fixed (crc32 of the name), kept
in facts, and exported in status.json with each ambition's milestone.

Events: ev "persona" {main, second} once per brain; ev "milestone" {ambition, reached, next} when a milestone is passed.
"""
from __future__ import annotations

import time
import zlib

NAMES = {"A1": "home", "A2": "livelihood", "A3": "mastery", "A4": "adventure", "A5": "possessions", "A6": "renown", "A7": "company", "A8": "getting good"}
CRAFT = ("Blacksmith", "Carpenter", "Tailor", "Tinker")
FIGHT = ("Archer", "Bard", "Ranger", "MaceFighter", "Fencer", "Swordsman")
MAGE = ("PureMage", "Warlock", "Sorcerer")
GATHER = ("Fisherman", "Prospector")
PASSIVE = ("Meditation", "Resisting Spells", "Focus", "Hiding", "Detecting Hidden", "Anatomy", "Evaluating Intelligence", "Spirit Speak", "Healing", "Tactics")
SAVERS = ("A1", "A2", "A5")
GRANTS = ("goals", "first_trip")                 # "sewers" dropped: the owner keeps every bot out of the Britain sewers (2026-10-18; HunterBot.SEWERS_BANNED)
EVERY = 60.0
WORTH_EVERY = 600.0
WORTH_WINDOW = 2 * 3600.0
STEPS = {
    "A1": [4000, 10000, 16000],                  # a small house deed: 16,000 on this shard (housePricing, 2026-10-18)
    "A2": [100, 250, 500],
    "A3": [70, 80, 90, 100],
    "A4": ["another region", "a trip completed", "a dungeon"],
    "A5": [10, 20, 30],
}


def persona_for(name, pname):
    h = zlib.crc32((name or "").encode())
    base = (pname or "").replace(" ", "")
    if any(base.startswith(p) for p in CRAFT) or base in CRAFT:
        main, second = "A2", "A1"
    elif base in FIGHT or base.endswith(("Fighter", "Archer")):
        main, second = ("A4" if h % 2 else "A5"), "A6"
    elif base in MAGE:
        main, second = "A3", "A4"
    elif base == "AnimalTamer":
        main, second = "A5", "A4"
    elif base in GATHER:
        main, second = "A2", "A1"
    else:
        main, second = "A3", "A2"
    if (h // 7) % 5 == 0:
        main, second = "A7", main                   # the social one in five
    return {"main": main, "second": second}


class AmbitionMixin:
    def persona(self):
        p = self.facts.get("persona")
        if not p:
            p = persona_for(self.name, getattr(self, "pname", ""))
            self.facts["persona"] = p
        return p

    def ambition_on(self):
        return "ambitions" in getattr(self, "features", ())        # not self.feature(): feature() asks ambition_grants, which asks this

    def ambition_grants(self, name):
        """BotBase.feature: the long-term behaviours a persona earns, instead of a features.json cohort."""
        if name not in GRANTS or not self.ambition_on():
            return False
        if name == "goals":
            return self.wants_saving()
        return self.ambition_wants("A4") and "ambition_trips" in getattr(self, "features", ())      # first_trip, sewers: the adventurer's (staged by ambition_trips)

    def ambition_wants(self, ambition):
        """True when this bot's persona holds the ambition (main or secondary) and the feature is on."""
        if not self.ambition_on():
            return False
        p = self.persona()
        return ambition in (p["main"], p["second"])

    def wants_saving(self):
        p = self.persona() if self.ambition_on() else None
        return bool(p) and (p["main"] in SAVERS or p["second"] in SAVERS)

    # ---- where it stands -----------------------------------------------------------------------------------------------------------------------------

    def working_skill(self):
        try:
            if hasattr(self, "main_skill") and getattr(self, "skill_values", None):
                return self.skill_values.get(self.main_skill(), 0.0)
        except Exception:
            pass
        if isinstance(getattr(self, "skill", None), (int, float)):
            return float(self.skill)
        vals = [v for k, v in (getattr(self, "skill_values", None) or {}).items() if k not in PASSIVE]
        return max(vals) if vals else 0.0

    def worth_rate(self):
        """Net worth gained an hour over the last two hours (samples every 10 minutes, kept in facts)."""
        ring = self.facts.setdefault("worth_ring", [])
        if not ring:
            return 0.0
        now = time.time()
        old = [s for s in ring if now - s[0] <= WORTH_WINDOW]
        if len(old) < 2 or old[-1][0] - old[0][0] < 1800:
            return 0.0
        return (old[-1][1] - old[0][1]) / ((old[-1][0] - old[0][0]) / 3600.0)

    def ambition_value(self, a):
        if a == "A1":
            return (self.c.gold or 0) + self.facts.get("bank_balance", 0)
        if a == "A2":
            return self.worth_rate()
        if a == "A3":
            return self.working_skill()
        if a == "A4":
            seen = set(self.facts.get("regions_seen", []))
            home = (self.home() or {}).get("name") if hasattr(self, "home") else None
            trips = self.facts.get("trips_done", 0)
            n = 0
            if seen - {home, "wilds", None}:
                n = 1
            if n >= 1 and trips:
                n = 2
            if n >= 2 and self.facts.get("dungeon_seen"):
                n = 3
            return n
        if a == "A5":
            total = 0
            try:
                for layer in getattr(self, "ARMOR_BUY", {}):
                    total += self.worn_ar(layer)[0] * self.SLOT_SHARE[layer]
            except Exception:
                return 0
            return total
        return None

    def milestone(self, a):
        """(reached, next) labels for an ambition: the last milestone passed and the one it works toward."""
        steps = STEPS.get(a)
        v = self.ambition_value(a)
        if not steps or v is None:
            return None, None
        if a == "A4":
            n = int(v)
            return (steps[n - 1] if n else None), (steps[n] if n < len(steps) else None)
        done = [s for s in steps if v >= s]
        nxt = next((s for s in steps if v < s), None)
        return (done[-1] if done else None), nxt

    def ambition_status(self):
        if not self.ambition_on():
            return {}
        p = self.persona()
        out = {"persona": {"main": f"{p['main']} {NAMES[p['main']]}", "second": f"{p['second']} {NAMES[p['second']]}"}}
        prog = {}
        for a in (p["main"], p["second"]):
            reached, nxt = self.milestone(a)
            v = self.ambition_value(a)
            prog[a] = {"reached": reached, "next": nxt, "value": round(v, 1) if isinstance(v, float) else v}
        out["ambition_progress"] = prog
        return out

    def ambition_tick(self):
        if not self.ambition_on() or getattr(self.c, "ghost", False):
            return
        now = time.time()
        if now - self.__dict__.get("_amb_at", 0) < EVERY:
            return
        self.__dict__["_amb_at"] = now
        p = self.persona()
        if not self.__dict__.get("_amb_told"):
            self.__dict__["_amb_told"] = True
            self.ev("persona", main=p["main"], second=p["second"])
            self.log(f"persona: {NAMES[p['main']]} first, then {NAMES[p['second']]}")
        ring = self.facts.setdefault("worth_ring", [])
        if not ring or now - ring[-1][0] >= WORTH_EVERY:
            ring.append([round(now), (self.c.gold or 0) + self.facts.get("bank_balance", 0)])
            while ring and now - ring[0][0] > WORTH_WINDOW + WORTH_EVERY:
                ring.pop(0)
        try:
            r = self.region_name()
        except Exception:
            r = None
        if r:
            seen = self.facts.setdefault("regions_seen", [])
            if r not in seen:
                seen.append(r)
                if "dungeon" in r.lower() or r.lower() in ("despise", "covetous", "deceit", "destard", "hythloth", "shame", "wrong", "sewers", "britain sewers"):
                    self.facts["dungeon_seen"] = r
        got = self.facts.setdefault("milestones", {})
        for a in (p["main"], p["second"]):
            reached, nxt = self.milestone(a)
            if a not in got:
                got[a] = str(reached)                              # where it stood when it first looked: not an event
                continue
            if reached is not None and got[a] != str(reached):
                self.ev("milestone", ambition=f"{a} {NAMES[a]}", reached=reached, next=nxt)
                self.log(f"milestone: {NAMES[a]} {reached} (next {nxt})")
                got[a] = str(reached)
