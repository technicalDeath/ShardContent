"""Tamers hunt with their pets (watcher, 2026-10-19; feature "pet_hunt"; the owner's "Yes, pets hunt", after "today tamers earn nothing").

The finding (2026-10-19, 15.4 bot-hours each): the four tamers spent 66-99% of their time in r_tame and earned nothing. BotTamerAR kept a brown bear (strength
414), BotTameAdvR a timber wolf (238); BotTameAdvR's pet fought 28 times (r_pet_fight), but a TamerBot had no r_loot, so the kills were left where they lay. A tamer
in the era lived on its pet: the pet kills, the tamer loots. The pet's damage counts for its master (Mobile.RegisterDamage: GetDamageMaster), so the
master has the looting rights.

What a tamer with the feature does:
 * HUNTS for part of each hour, once it has a pet of strength PET_HUNT_MIN or more, seen in the last SEEN s: HUNT_MINS minutes an hour, BROKE_MINS while its
   carried and banked gold is under BROKE. The hour's phase comes from the bot's name, so the four tamers do not all hunt at once and a restart keeps it.
   Taming waits (r_tame yields) during the hunt; outside it everything is as before.
 * WORKS a tier-1 hunting area (fields.py, the fighters' areas): a kind is worth its loot (the engine's loot table: gold plus extras) when the pet beats it
   easily (its strength at most RATIO of the pet's, as r_pet_fight) and it pays at least LOW; a kind that killed tamers puts the area out.
 * SENDS the pet: the nearest such monster within REACH ("all kill", then the target); the tamer walks to within FOLLOW tiles of it and no closer. A group the
   pet beats together (strengths summed) is not walked away from (r_evade). When the target vanishes and its corpse is there it is a kill (kills, last_kill_at,
   ev pet_kill) and "all guard me" again; a fight over GIVE_UP s is dropped.
 * LOOTS the corpse (BotBase.r_loot: gold, reagents, gems; never another's kill) and sells gems (r_sellloot, feature livelihood).
Events: pet_hunt_start / pet_hunt_end {pet, worth, mins}, pet_hunt_target {pet, target, theirs, strength}, pet_kill {pet, target, secs}, pet_hunt_gave_up.
"""
from __future__ import annotations

import re
import time
import zlib

HUNT_MINS = 20
BROKE_MINS = 40
BROKE = 1000
CYCLE = 3600
PET_HUNT_MIN = 90
RATIO = 0.6
LOW = 10.0
SEEN = 120
REACH = 14
FOLLOW = 5
GIVE_UP = 60
REORDER = 20


def kind_power(k):
    import tamefind
    st = tamefind.creature_stats().get(k)
    if not st:
        return None
    h, d = st.get("hits") or [0, 0], st.get("damage") or [0, 0]
    return (sum(h) / 2.0) * (sum(d) / 2.0)


def kind_loot(k):
    try:
        import profit
        e = profit.table().get(k)
    except Exception:
        return 0.0
    if not e:
        return 0.0
    return float(e.get("gold") or 0) + sum(profit.EXTRA_VALUE.get(x, 0) for x in e.get("extras") or ())


class PetHuntMixin:
    # ---- when ---------------------------------------------------------------------------------------------------------------------------------------------

    def hunt_pet(self):
        """The kept pet when it can hunt: strong enough and seen lately (the sighting is refreshed here: r_pet, which also does it, waits behind a hunt)."""
        pet = self.facts.get("pet")
        if not pet or pet.get("strength", 0) < PET_HUNT_MIN:
            return None
        try:
            _, pm = self.pet_view()
        except Exception:
            pm = None
        if pm is not None:
            pet["seen"] = time.time()
        if time.time() - pet.get("seen", pet.get("since", 0)) > SEEN:
            return None
        return pet

    def hunt_worth(self):
        return int(self.c.gold or 0) + int(self.facts.get("bank_balance") or 0)

    def hunt_due(self):
        if not self.feature("pet_hunt") or self.c.ghost:
            return False
        pet = self.hunt_pet()
        mins = BROKE_MINS if self.hunt_worth() < BROKE else HUNT_MINS
        phase = (time.time() + zlib.crc32(str(getattr(self, "name", "")).encode())) % CYCLE
        due = bool(pet) and phase < mins * 60
        if due != bool(self.facts.get("hunting")):
            self.facts["hunting"] = due
            name = pet["name"] if pet else (self.facts.get("pet") or {}).get("name")
            self.ev("pet_hunt_start" if due else "pet_hunt_end", pet=name, worth=self.hunt_worth(), mins=mins)
            self.log(f"pet hunt: {'starting' if due else 'ending'} ({name}; {self.hunt_worth()} gold carried and banked; {mins} min an hour)")
            if not due:
                self.facts["field"] = None
                self.facts.pop("pet_target", None)
                if pet:
                    self.c.say("all guard me")
        return due

    # ---- what the pet beats -------------------------------------------------------------------------------------------------------------------------------

    def pet_beats(self, kinds):
        pet = self.facts.get("pet")
        if not pet or not kinds:
            return False
        total = 0.0
        for k in kinds:
            s = kind_power(k)
            if s is None:
                return False
            total += s
        return total <= pet.get("strength", 0) * RATIO

    def pet_handles(self, mons):
        """With the feature, a group the pet beats together (strengths summed) is the pet's too, not only a lone monster."""
        if self.feature("pet_hunt") and len(mons) > 1:
            try:
                pet, pm = self.pet_view()
            except Exception:
                return False
            if not pet or pm is None or pm.distance > 8 or pm.hp_pct < 60:
                return False
            return self.pet_beats([self.mkey(m) for m in mons])
        import tamefind
        return tamefind.TameFindMixin.pet_handles(self, mons)

    # ---- the hunting area (FieldsMixin hooks) -------------------------------------------------------------------------------------------------------------

    def fields_on(self):
        return self.hunt_due()

    def field_tiers(self):
        # tier 2 too (orcs, ratmen, lizardmen: about 60 gold a kill, the engine's loot tables) once the pet is strong enough: field_spawner below vetoes
        # any area holding an aggressive kind the pet does not beat. On tier 1 alone a brown bear found rats and mongbats (13 gold) and the tamer
        # stayed at about 200 gold, too poor for armour (owner, 2026-11-01: "bottamerar has no armor")
        return (1, 2)

    def field_spawner(self, sp, deadly):
        import fields
        v, bad = fields.FieldsMixin.field_spawner(self, sp, deadly)
        if bad:
            return v, bad
        import task_core
        for k in sp[3]:
            if task_core.aggressive(k) and not self.pet_beats([k]):
                return 0.0, True                          # it would go for the tamer, and the pet cannot stop it
        return v, bad

    def worth_kind(self, k, deadly):
        if k in deadly or not self.pet_beats([k]):
            return 0.0
        v = kind_loot(k)
        return v if v >= LOW else 0.0

    def ground_load(self, cell):
        import hunter
        return hunter.HunterBot.ground_load(self, cell)

    def prey(self, within=9):
        """Monsters in sight the pet beats easily that drop LOW gold or more, not already fought by another bot."""
        others = [m for m in self.c.mobiles(within=within + 4) if m.name.startswith("Bot")]
        out = []
        for m in self.mobs(within):
            k = self.mkey(m)
            if not self.pet_beats([k]) or kind_loot(k) < LOW:
                continue
            if any(max(abs(o.x - m.x), abs(o.y - m.y)) <= 3 for o in others):
                continue                                  # another bot's fight: its kill and its loot
            out.append(m)
        return out

    # ---- the rules ----------------------------------------------------------------------------------------------------------------------------------------

    def r_loot(self):
        if not self.feature("pet_hunt"):
            return False
        from bot_common import BotBase
        return BotBase.r_loot(self)

    def r_pet_hunt(self):
        if not self.hunt_due() or self.hp_pct() < 55:
            return False
        pet, pm = self.pet_view()
        if pm is None:
            return False
        now = time.time()
        h = self.facts.get("pet_target")
        if h:
            cur = next((m for m in self.c.mobiles(within=18) if m.serial == h["serial"]), None)
            if cur is None:
                self.facts.pop("pet_target", None)
                corpse = next((i for i in self.c.containers(within=16) if "corpse" in i.name.lower() and h["kind"] in re.sub(r"[^a-z]", "", i.name.lower())), None)
                if corpse is None:
                    return False                          # it walked out of sight
                self.kills += 1
                self.note_kill_at(corpse.x, corpse.y, h["kind"])
                self.ev("pet_kill", pet=pet["name"], target=h["name"], secs=round(now - h["t"]))
                self.log(f"pet hunt: {pet['name']} killed {h['name']} in {now - h['t']:.0f} s")
                self.c.say("all guard me")
                if max(abs(self.c.x - corpse.x), abs(self.c.y - corpse.y)) > 6:
                    self.c.goto(corpse.x, corpse.y).wait(timeout=6)          # r_loot takes it from within 8
                return True
            if now - h["t"] > GIVE_UP:
                self.facts.pop("pet_target", None)
                self.ignored[cur.serial] = now + 300
                self.ev("pet_hunt_gave_up", pet=pet["name"], target=cur.name, secs=round(now - h["t"]))
                self.c.say("all guard me")
                return False
            self.activity = f"letting the {pet['name']} kill {cur.name}"
            if now - h.get("ordered", 0) > REORDER:
                self.pet_order(cur)
                h["ordered"] = now
            if cur.distance > FOLLOW:
                self.c.goto(cur.x, cur.y).wait(timeout=3)
            else:
                time.sleep(1.0)
            return True
        prey = [m for m in self.prey(REACH) if self.ignored.get(m.serial, 0) <= now]
        if not prey:
            return False
        m = min(prey, key=lambda x: x.distance)
        self.facts["pet_target"] = {"serial": m.serial, "name": m.name, "kind": self.mkey(m), "t": now, "ordered": now}
        self.pet_order(m)
        self.activity = f"sending the {pet['name']} at {m.name}"
        self.ev("pet_hunt_target", pet=pet["name"], target=m.name, theirs=round(kind_power(self.mkey(m)) or 0), strength=round(pet["strength"]))
        self.log(f"pet hunt: {pet['name']} (strength {pet['strength']:.0f}) sent at {m.name} {m.distance} tiles away")
        if m.distance > FOLLOW:
            self.c.goto(m.x, m.y).wait(timeout=3)
        return True

    def pet_order(self, m):
        from uo import Event
        self.c.events.drain()
        self.c.say("all kill")
        if self.c.wait_for(Event.TARGET_REQUEST, timeout=3) is not None:
            self.c.target(m.serial)
