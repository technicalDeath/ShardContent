"""A ranger's companion (2026-11-01; feature "ranger_pet"). Mixin for HunterBot: only a Ranger with the feature uses it.

A UOR ranger (Archery + Animal Taming) kept one animal that followed it and went for what it shot. The farm's two rangers (Taming 42-43, Animal Lore 0)
had none. What a ranger with the feature does now:

 * KEEPS one companion (facts["pet"], the tamer's record shape, so tamefind.pet_view and pethunt.kind_power work on it; in PERSIST). A pet of its own in
   view with no record (a restarted brain) is adopted.
 * CHOOSES the kind by the engine's numbers, not by hardness alone. A kind qualifies when
     - the ranger may try it at all: Animal Taming >= MinTameSkill (AnimalTaming.cs, "You have no chance");
     - a try succeeds often enough: tamefind.success_chance >= MIN_TAME_P (0.15, tamefind's own floor for a pet worth going for);
     - it will obey: BaseCreature.GetControlChance (pre-ML: (Taming x 4 + Lore) / 5 against MinTameSkill, x6 above and x14 below, 700 + bonus clamped to
       220..990, 1.0 at MinTameSkill 29.1 or less) >= CONTROL_MIN. Each order is a roll: obeyed +1 loyalty, refused -3 (CheckControlChance), and
       LoyaltyTimer takes MaxLoyalty / 10 = 10 an hour; with an order every REORDER_S (120 s, tamer.r_pet's "every couple of minutes", 30 an hour) loyalty
       holds when 30 x (4p - 3) >= 10, p >= 0.833. Below that the pet drifts to 0 and goes wild (LoyaltyTimer releases it);
     - it is worth keeping: strength (pethunt.kind_power: hit points x average damage, creature_stats.json) >= PET_MIN (pethunt.PET_HUNT_MIN, 90).
   The strongest qualifying kind wins. At Taming 43.3 / Lore 0 that is the timber wolf (287; MinTameSkill 23.1: control 1.0, success 0.41); a black bear
   (371) obeys at 0.63 and qualifies from Taming 46.8; brown bear and cougar (MinTameSkill 41.1) obey at 0.22 until Taming 52.5.
 * TAMES at a calm moment (no target, no fight, no threat within 9 tiles (r_fight's prey radius), health >= REST_BELOW, no pressing errand, not mid-errand):
   an animal in view that qualifies and is within PET_UPGRADE (1.3, tamer.PET_UPGRADE) of the best kind it could walk to is tamed where it stands;
   otherwise, past the cooldown, it walks to the tame spot (tamefind.spots(), tame_spots.json) with the strongest qualifying kind, discounted by distance
   as tamefind.pick_tspot (/ (1 + far / 150), 400 tiles at most from here and from home), times tamefind.spot_risk, never near a death (100 tiles, as
   tamefind), never a cell the area danger map refuses, never a walk route_danger refuses (tamefind.tspot_route_ok). There it looks about as
   tamefind.find_animals does (WANDER_STEPS looks within the spawner's range, STAY_SECS at most, both tamefind's). A hunt task of the decision core is
   ended "switch" (no ban: task_core.REST_S has no "switch") when the walk starts, so its monitor does not judge the trip as hunting.
   A try is the tamer's: up to the animal (two tiles, TamerBot.TAME_RANGE), useskill animal taming through basics.cursor_after, the journal read for the
   engine's lines. An animal is tried until a success was 95% likely at its chance (ceil(log 0.05 / log(1 - p)), at most MAX_TRIES), then left 10 minutes.
 * NEVER BLOCKS hunting for long: a trip lasts the route's walk (task_core.route_length / walk_rate) plus STAY_SECS; a trip that ends without a pet sets the
   next one TIME_SHARE_WAIT x its length away (9: at most a tenth of the time goes to taming trips) and the spot is skipped tamefind.EMPTY_TTL x
   (1, 2, 3, 4) as tamefind.find_animals does.
 * FIGHTS beside it: the ranger's target (self.target: r_fight and the hunt tree's Pick both set it) gets "all kill" + the target once per target while the
   pet is within ORDER_REACH (14: BaseAI.IsValidTarget, from.InRange(Mobile, 14)) and not hurt (60%: tamefind.pet_handles); the pet is called back
   ("all follow me") when the target is gone, when the ranger is fleeing (hp under flee_below()), or when the pet is hurt. Between fights "all follow me"
   every REORDER_S. The rule speaks and returns False: it never takes a tick from the fight.
 * HEALS it with a bandage when the pet is under 55% (tamefind.r_pet_heal), adjacent (Bandage.Range 1 before AOS) or a step away, nothing hostile within 4
   and no fight on. Bandaging an animal uses Veterinary and Animal Lore (BandageContext.GetPrimarySkill): at Veterinary 12 a bandage lands 22% of the time
   ((12 + 10) / 100) for 5-16 points, so it is done only when hurt (the ranger's skill plan has no Veterinary).
 * LOSES it: not seen for LOST_S (600 s, tamer.r_pet) or a corpse of its kind where it was last seen within 8 tiles of the ranger. Out of view but seen in
   the last LOST_S, within FETCH_REACH (far.FAR, a near walk) of where it was, the ranger walks back once and calls it (a following pet stands still past
   16 tiles, BaseAI.FollowTarget; it hears orders within RangePerception 16).
Events: ranger_pet_adopted, ranger_pet_trip {spot, kind, strength, dist, budget_min}, ranger_pet_try {m, chance, control, n}, ranger_pet_tamed {m, strength,
control, tries}, ranger_pet_trip_end {why, mins, next_min}, ranger_pet_kill {pet, target}, ranger_pet_recall {why}, ranger_pet_heal {hp, ok}, ranger_pet_lost
{why}, ranger_pet_fetch {walk}.
"""
from __future__ import annotations

import math
import random
import re
import time

import pethunt
import tamefind
from bot_common import BotBase

FEATURE = "ranger_pet"
RULES = ("r_ranger_pet", "r_ranger_pet_heal", "r_ranger_tame")
MIN_TAME_P = 0.15                 # tamefind.rank_candidates / spot_upgrade: a stronger pet is worth going for from a 15% chance
PET_MIN = pethunt.PET_HUNT_MIN    # 90: a pet strong enough to hunt with (a horse, 128, and up)
PET_UPGRADE = 1.3                 # tamer.TamerBot.PET_UPGRADE: an animal in view this close to the best one about is as good as the walk
MAX_LOYALTY = 100                 # BaseCreature.MaxLoyalty
LOYALTY_DROP_H = MAX_LOYALTY / 10      # LoyaltyTimer, every hour
REORDER_S = 120                   # tamer.r_pet: "all guard me" every couple of minutes; here "all follow me"
CONTROL_MIN = (LOYALTY_DROP_H / (3600.0 / REORDER_S) + 3.0) / 4.0     # 0.833: obeyed +1, refused -3 (CheckControlChance), 30 orders an hour
ORDER_REACH = 14                  # BaseAI.IsValidTarget: the master within 14 tiles of the pet, or the order is ignored
PET_HURT = 60                     # tamefind.pet_handles: a pet under 60% is not sent
HEAL_BELOW = 55                   # tamefind.r_pet_heal
HEAL_GAP = 15                     # tamefind.r_pet_heal: one bandage try per 15 s at most
CALM_R = 9                        # HunterBot.r_fight: prey(9), what it would engage
TAME_RANGE = 2                    # TamerBot.TAME_RANGE: AnimalTaming's target range before AOS
CHASE_STALL = 12                  # TamerBot.r_tame with tame_find: no nearer for 12 s ...
CHASE_MAX = 45                    # ... or 45 s on one animal: left for IGNORE_S
IGNORE_S = 600                    # TamerBot.r_tame with tame_find
SEEN_R = 12                       # an animal this near is tamed where it stands (tamer.candidates: reachable() reads line of sight within 12)
MAX_TRIES = 10                    # tries on one animal at a 15% chance (the floor): 1 - 0.85^10 = 80%; each try is 9-12 s (AnimalTaming InternalTimer, 3-4 ticks of 3 s)
TRY_S = 12.0
TIME_SHARE_WAIT = 9               # a failed trip of T minutes: the next one in 9 T (taming trips at most a tenth of the time)
LOST_S = 600                      # tamer.r_pet: not seen for ten minutes, it is gone
FETCH_AFTER = 20                  # s out of view before the ranger goes back for it (a following pet steps at run pace on the farm, petsKeepUp)
FETCH_REACH = 120                 # far.FAR: a near walk
DEATH_NEAR = 100                  # tamefind.pick_tspot: near_death_spot(x, y, 100)
SPOT_MAX = 400                    # tamefind.pick_tspot: from here and from home
RESULT_RE = r"accept you|even challenging|fail|cannot|already|too far|no chance|stops|too many followers|angry"


def control_chance(min_skill, taming, lore, loyalty=MAX_LOYALTY):
    """BaseCreature.GetControlChance before ML, in the engine's fixed point (tenths, integer division)."""
    if min_skill <= 29.1:
        return 1.0
    difficulty = int(min_skill * 10)
    weighted = (int(round(taming * 10)) * 4 + int(round(lore * 10))) // 5
    bonus = weighted - difficulty
    bonus = bonus * 14 if bonus <= 0 else bonus * 6
    chance = min(990, max(220, 700 + bonus)) - (MAX_LOYALTY - loyalty) * 10
    return chance / 1000.0


def tries_for(p):
    """Tries on one animal: until a success was 95% likely at chance p, at most MAX_TRIES."""
    if p >= 0.95:
        return 1
    if p <= 0:
        return 0
    return max(1, min(MAX_TRIES, int(math.ceil(math.log(0.05) / math.log(1.0 - p)))))


_KIND_MIN = None


def kind_min():
    """{kind: MinTameSkill} of every kind the tame spots hold (tame_spots.json, from the spawners and the creature classes)."""
    global _KIND_MIN
    if _KIND_MIN is None:
        _KIND_MIN = {}
        for s in tamefind.spots():
            for k in s.get("kinds") or ():
                _KIND_MIN[k["key"]] = float(k["min"])
    return _KIND_MIN


class RangerPetMixin:
    PERSIST = BotBase.PERSIST + ("pet", "rpet")

    # ---- gates ----------------------------------------------------------------------------------------------------------------------------------------

    def rp_on(self):
        return getattr(self, "pname", "") == "Ranger" and self.feature(FEATURE)

    def core_lets(self, name):
        """The decision core passes the ranger's pet rules (each has its own limits: the orders only speak, the heal waits 15 s, taming waits for calm and a cooldown)."""
        if name in RULES:
            return self.rp_on()
        return super().core_lets(name)

    def rp_state(self):
        return self.facts.setdefault("rpet", {})

    def rp_skills(self):
        sv = self.skill_values
        return sv.get("Animal Taming", 0.0), sv.get("Animal Lore", 0.0)

    # ---- which kinds ----------------------------------------------------------------------------------------------------------------------------------

    def rp_kind(self, key, owned=False):
        """(strength, success, control) when this kind qualifies as the ranger's companion now, else None. owned: an animal this character owned
        before is tamed with no skill check (AnimalTaming.cs alreadyOwned, "That wasn't even challenging"), so only obedience and strength count."""
        mn = kind_min().get(key)
        if mn is None:
            return None
        taming, lore = self.rp_skills()
        p = 1.0 if owned else tamefind.success_chance(mn, taming)
        if not owned and taming < mn:
            return None                                       # "You have no chance of taming this creature."
        ctl = control_chance(mn, taming, lore)
        strength = pethunt.kind_power(key) or 0.0
        if p < MIN_TAME_P or ctl < CONTROL_MIN or strength < PET_MIN:
            return None
        return strength, p, ctl

    def rp_calm(self):
        if self.c.ghost or self.hp_pct() < getattr(self, "REST_BELOW", 65):
            return False
        if getattr(self, "target", None) or getattr(self, "fight", None):
            return False
        if self.threats(CALM_R):
            return False
        return True

    def rp_errand(self):
        """A task of the decision core that is not a hunt (a sale, the bank, supplies) or a pressing errand: no taming walk now. The pressing-need
        reading (task_core.pressing_need, every errand's candidates) is kept for the core's own MONITOR_S."""
        task = self.facts.get("task")
        if task and task.get("task") not in ("hunt", "tour2"):
            return True
        try:
            import task_core
        except Exception:
            return False
        c = self.__dict__.get("_rp_press")
        if c and time.time() - c[0] < task_core.MONITOR_S:
            return c[1]
        try:
            v = task_core.pressing_need(self) is not None
        except Exception:
            v = False
        self.__dict__["_rp_press"] = (time.time(), v)
        return v

    def rp_slot_free(self):
        try:
            f = int(self.c.state.get("followers") or 0)
            mx = int(self.c.state.get("maxFollowers") or 5)          # Mobile.FollowersMax 5; every candidate kind takes ControlSlots 1
        except Exception:
            return True
        return mx <= 0 or f + 1 <= mx

    # ---- the companion ------------------------------------------------------------------------------------------------------------------------------

    def rp_pet(self):
        """(record, mobile in view or None)."""
        return tamefind.TameFindMixin.pet_view(self)

    @staticmethod
    def rp_hp(m):
        """The pet's health in percent, None while the client has no real figure (it holds a placeholder until asked)."""
        mx = getattr(m, "max_hits", 0) or 0
        return None if mx <= 1 else 100.0 * (getattr(m, "hits", 0) or 0) / mx

    def rp_say(self, text, why=None):
        pet = self.facts.get("pet")
        try:
            self.c.say(text)
        except Exception:
            return
        if pet is not None:
            pet["ordered"] = time.time()
        if why:
            self.ev("ranger_pet_recall", why=why)

    def rp_adopt(self):
        """No record, but a pet of this character in view (the world file's isPet): it is the companion (a restarted brain, an old tame)."""
        pets = [m for m in self.c.mobiles(within=14) if (getattr(m, "_d", None) or {}).get("isPet")]
        if not pets:
            return False
        m = max(pets, key=lambda x: (pethunt.kind_power(tamefind.norm(x.name)) or 0, -x.distance))
        self.rp_keep(m, adopted=True)
        self.ev("ranger_pet_adopted", m=m.name, pets=len(pets))
        self.log(f"ranger pet: {m.name} ({m.distance} tiles) is already this ranger's: adopted")
        return True

    def rp_keep(self, m, adopted=False):
        now = time.time()
        key = tamefind.norm(m.name)
        self.facts["pet"] = {"serial": m.serial, "name": m.name, "kind": key, "strength": pethunt.kind_power(key) or 0.0, "since": now, "seen": now,
                             "xy": [m.x, m.y], "kill": None, "ordered": 0}
        owned = [s for s in (self.facts.get("owned_serials") or []) if s != m.serial] + [m.serial]
        self.facts["owned_serials"] = owned[-300:]
        self.rp_say("all follow me")

    # ---- step 2: the orders in a fight (before r_flee; speech only, never a turn) ------------------------------------------------------------------------

    def r_ranger_pet(self):
        if not self.rp_on() or self.c.ghost:
            return False
        pet, pm = self.rp_pet()
        if not pet:
            return False
        now = time.time()
        if pm is None:
            self.rp_missing(pet, now)
            return False
        pet["seen"], pet["xy"] = now, [pm.x, pm.y]
        pet["near"] = pm.distance
        pet.pop("fetched", None)                                 # in view again: a later loss may be walked back for once more
        hp = self.rp_hp(pm)
        if hp is not None:
            pet["hp"] = round(hp)
        hurt = hp is not None and hp < PET_HURT
        tgt = getattr(self, "target", None)
        fleeing = self.hp_pct() < self.flee_below()
        sent = pet.get("kill")
        if sent and (fleeing or tgt != sent or hurt):
            pet["kill"] = None
            self.rp_say("all follow me", why="fleeing" if fleeing else "pet hurt" if hurt else "target done")
            sent = None
        if tgt and not sent and not fleeing and not hurt and tgt != pet.get("last_kill") and pm.distance <= ORDER_REACH:
            m = next((x for x in self.c.mobiles(within=18) if x.serial == tgt), None)
            if m is not None and m.notoriety != "Innocent" and not getattr(m, "is_dead", False):
                pet["kill"] = pet["last_kill"] = tgt               # once per target, whether or not the pet obeys (CheckControlChance is silent)
                self.rp_order_kill(m)
                self.ev("ranger_pet_kill", pet=pet["name"], target=m.name)
                self.activity = f"sending the {pet['name']} at {m.name}"
            return False
        if not sent and not tgt and now - pet.get("ordered", 0) > REORDER_S:
            self.rp_say("all follow me")                         # at heel, and +1 loyalty when obeyed
        return False

    def rp_order_kill(self, m):
        """'all kill' and the target (pethunt.pet_order's speech, through basics.cursor_after so a cursor that lands before the wait is not missed)."""
        if self.cursor_after(lambda: self.c.say("all kill"), timeout=3.0):
            self.c.target(m.serial)
            return True
        try:
            self.c.call("canceltarget", timeout=4)
        except Exception:
            pass
        return False

    def rp_missing(self, pet, now):
        """Out of view: dead (a corpse of its kind where it was, last seen near), lost (LOST_S), or to be fetched (r_ranger_tame)."""
        seen = pet.get("seen", pet.get("since", now))
        xy = pet.get("xy")
        if xy and (pet.get("near") or 99) <= 8 and now - seen < 30:
            kind = pet.get("kind") or tamefind.norm(pet["name"])
            for c in self.c.containers(within=16):
                n = (c.name or "").lower()
                if "corpse" in n and kind in re.sub(r"[^a-z]", "", n) and max(abs(c.x - xy[0]), abs(c.y - xy[1])) <= 3:
                    self.rp_lost(pet, "dead")
                    return
        if now - seen > LOST_S:
            self.rp_lost(pet, "not seen")

    def rp_lost(self, pet, why):
        self.facts.pop("pet", None)
        if why != "dead":
            lost = [p for p in (self.facts.get("lost_pets") or []) if time.time() - p["t"] < 11 * 3600]
            lost.append({"name": pet["name"], "serial": pet["serial"], "xy": pet.get("xy") or [self.c.x, self.c.y], "t": pet.get("seen", time.time())})
            self.facts["lost_pets"] = lost[-5:]                  # it holds its follower slot until it goes wild (tamer.FERAL_AFTER)
        self.ev("ranger_pet_lost", m=pet["name"], why=why)
        self.log(f"ranger pet: {pet['name']} {'died' if why == 'dead' else 'lost (not seen for ten minutes)'}")

    # ---- step 3: the bandage (after r_heal) -------------------------------------------------------------------------------------------------------

    def r_ranger_pet_heal(self):
        if not self.rp_on() or self.c.ghost or getattr(self, "target", None) or self.mobs(4):
            return False
        pet, pm = self.rp_pet()
        if not pet or pm is None or time.time() - pet.get("healed_at", 0) < HEAL_GAP:
            return False
        bandage = self.c.find("bandage")
        if not bandage:
            return False
        try:
            self.c.call(f"hp {pm.serial}", timeout=4)              # the client holds a placeholder until it has asked (tamefind.r_pet_heal)
        except Exception:
            pass
        cur = next((x for x in self.c.mobiles(within=18) if x.serial == pet["serial"]), pm)
        hp = self.rp_hp(cur)
        if hp is None or hp >= HEAL_BELOW:
            return False
        pet["healed_at"] = time.time()
        if cur.distance > 1:
            if cur.distance > 3:
                return False                                      # it comes to heel on "all follow me"; no walk after it
            self.c.goto(cur.x, cur.y).wait(timeout=6)
        from uo import Event
        self.c.events.drain()
        self.activity = f"bandaging the {pet['name']}"
        self.c.use_on(bandage.serial, pet["serial"])
        ev = self.c.wait_for([Event.BANDAGE_DONE, Event.BANDAGE_FAILED], timeout=12)
        self.ev("ranger_pet_heal", pet=pet["name"], hp=round(hp), ok=bool(ev and ev.kind == Event.BANDAGE_DONE))
        return True

    # ---- step 1: getting one (before r_fight; only when calm) --------------------------------------------------------------------------------------

    def r_ranger_tame(self):
        if not self.rp_on() or self.c.ghost:
            return False
        st = self.rp_state()
        now = time.time()
        pet = self.facts.get("pet")
        if pet:
            if st.get("trip"):
                self.rp_trip_end("tamed")
            return self.rp_fetch(pet, now)
        if self.rp_adopt():
            if st.get("trip"):
                self.rp_trip_end("adopted")
            return False
        trip = st.get("trip")
        if trip and now > trip["until"]:
            self.rp_trip_end("budget")
            trip = None
        if not self.rp_calm():
            return False                                          # a trip waits behind the fight (its budget runs on)
        if not self.rp_slot_free():
            if trip:
                self.rp_trip_end("no follower slot")
            st["next_at"] = max(st.get("next_at", 0), now + LOST_S)
            return False
        m = self.rp_candidate()
        if m is not None:
            if not trip:
                if self.rp_errand():
                    return False
                trip = self.rp_trip_start(None, m)
            return self.rp_tame(m, trip)
        if trip and trip.get("spot") is None:
            self.rp_trip_end("none left")                       # the animal in view was tamed by another, left, or tried out
            return False
        if not trip:
            if now < st.get("next_at", 0) or self.rp_errand():
                return False
            best = self.rp_pick_spot()
            if not best:
                st["next_at"] = now + LOST_S                      # nothing qualifies within reach: look again in ten minutes
                return False
            trip = self.rp_trip_start(best, None)
        return self.rp_trip_walk(trip)

    # ---- candidates in view ---------------------------------------------------------------------------------------------------------------------------

    def rp_ignored(self):
        return self.__dict__.setdefault("_rp_ignored", {})

    def rp_candidate(self):
        """The strongest qualifying wild animal within SEEN_R that this ranger can reach, when it is within PET_UPGRADE of the best kind about."""
        now = time.time()
        ign = self.rp_ignored()
        owned = set(self.facts.get("owned_serials") or [])
        best_about = self.rp_best_strength()
        out = []
        for m in self.c.mobiles(within=SEEN_R):
            if m.notoriety == "Innocent" or (getattr(m, "_d", None) or {}).get("isPet") or ign.get(m.serial, 0) > now:
                continue
            key = tamefind.norm(m.name)
            q = self.rp_kind(key, owned=m.serial in owned)
            if q is None:
                continue
            if abs((m.pos[2] or 0) - (self.c.z or 0)) > 14 or not (m.distance > 12 or self.los(m.serial)):
                continue                                          # tamer.reachable
            try:
                if not self.mem.usable("tamemob", m.serial):
                    continue                                      # a tamer has claimed it, or it was found unreachable
            except Exception:
                pass
            strength = q[0]
            if best_about and strength * PET_UPGRADE < best_about:
                continue                                          # the walk to the spot gives a clearly better one
            out.append((m.serial in owned, strength, -m.distance, m))
        if not out:
            return None
        return max(out, key=lambda r: r[:3])[3]                  # an animal it owned before first: a sure tame ("That wasn't even challenging")

    def rp_best_strength(self):
        """The strength of the best spot's kind (cached 10 minutes), 0 when none qualifies within reach."""
        c = self.__dict__.get("_rp_best")
        if c and time.time() - c[0] < LOST_S:
            return c[1]
        best = self.rp_pick_spot()
        v = best[1] if best else 0.0
        self.__dict__["_rp_best"] = (time.time(), v)
        return v

    # ---- the spot ---------------------------------------------------------------------------------------------------------------------------------

    def rp_pick_spot(self):
        """(spot, strength, kind, dist) of the best tame spot, else None."""
        from memory import cell_of
        here = (self.c.x, self.c.y)
        try:
            home = tuple(self.home_centre())[:2]
        except Exception:
            home = here
        skip = self.rp_state().get("skip", {})
        now = time.time()
        best = None
        for s in tamefind.spots():
            key = f"{s['x']},{s['y']}"
            if not s.get("safe") or skip.get(key, 0) > now:
                continue
            kinds = [(self.rp_kind(k["key"]), k["key"]) for k in s.get("kinds") or ()]
            kinds = [(q[0], k) for q, k in kinds if q]
            if not kinds:
                continue
            d = max(abs(s["x"] - here[0]), abs(s["y"] - here[1]))
            dh = max(abs(s["x"] - home[0]), abs(s["y"] - home[1]))
            if d > SPOT_MAX or dh > SPOT_MAX:
                continue
            if self.near_death_spot(s["x"], s["y"], DEATH_NEAR):
                continue
            try:
                if self.mem.dangerous_cell(cell_of(s["x"], s["y"])):
                    continue
            except Exception:
                pass
            strength, kind = max(kinds)
            try:
                risk = tamefind.TameFindMixin.spot_risk(self, s)
            except Exception:
                risk = 1.0
            score = strength * risk / (1.0 + (d + dh) / 2.0 / 150.0)
            if best is None or score > best[0]:
                best = (score, s, strength, kind, d)
        if best is None:
            return None
        s = best[1]
        try:
            if not tamefind.TameFindMixin.tspot_route_ok(self, s, here):
                self.rp_state().setdefault("skip", {})[f"{s['x']},{s['y']}"] = now + tamefind.EMPTY_TTL
                return None                                      # the walk crosses ground this bot may not use: that spot is out, the next pick looks further
        except Exception:
            pass
        return s, best[2], best[3], best[4]

    def rp_trip_start(self, best, m):
        """A trip: to a spot (best) or here, for an animal in view (m). Its budget is the walk and one stay. A walk to a spot ends the core's hunt task
        ("switch"); a tame where it stands (a minute or two) leaves the task running."""
        now = time.time()
        task = self.facts.get("task")
        if best is not None and task and task.get("task") in ("hunt", "tour2"):
            try:
                import task_core
                task_core.end_task(self, task, "switch")          # the hunt ends cleanly; the core chooses again after the trip ("switch" bans nothing)
            except Exception:
                pass
        if best is None:
            p = self.rp_kind(tamefind.norm(m.name))
            n = tries_for(p[1]) if p else 1
            trip = {"x": m.x, "y": m.y, "home": 6, "kind": tamefind.norm(m.name), "since": now, "arrived": now, "wander": 0, "spot": None,
                    "until": now + CHASE_MAX + n * TRY_S}
            self.log(f"ranger pet: taming {m.name} here ({m.distance} tiles)")
        else:
            s, strength, kind, d = best
            try:
                import task_core
                tiles = task_core.route_length(self, (s["x"], s["y"])) or d
                walk_s = 60.0 * tiles / task_core.walk_rate(self)
            except Exception:
                walk_s = 60.0 * d / 55.0                           # task_core.WALK_RATE, the farm's median
            trip = {"x": s["x"], "y": s["y"], "home": s.get("home", 10), "kind": kind, "since": now, "arrived": 0, "wander": 0, "spot": f"{s['x']},{s['y']}",
                    "until": now + walk_s + tamefind.STAY_SECS}
            self.ev("ranger_pet_trip", spot=[s["x"], s["y"]], species=kind, strength=round(strength), dist=d, budget_min=round((trip["until"] - now) / 60, 1))
            self.log(f"ranger pet: going for a {kind} (strength {strength:.0f}) at {s['x']},{s['y']} ({d} tiles)")
            self.dlog("choice", what=f"tame a companion {kind}", why=f"strength {strength:.0f}, {d} tiles")
        self.rp_state()["trip"] = trip
        return trip

    def rp_trip_end(self, why):
        st = self.rp_state()
        trip = st.pop("trip", None)
        if not trip:
            return
        now = time.time()
        dur = now - trip["since"]
        nxt = 0.0
        if why not in ("tamed", "adopted"):
            nxt = TIME_SHARE_WAIT * dur
            st["next_at"] = max(st.get("next_at", 0), now + nxt)
            if trip.get("spot"):
                n = st.setdefault("skip_n", {}).get(trip["spot"], 0) + 1
                st["skip_n"][trip["spot"]] = n
                st.setdefault("skip", {})[trip["spot"]] = now + tamefind.EMPTY_TTL * min(n, 4)
        far = self.facts.get("far")
        if far and trip.get("spot") and list(far.get("dest") or []) == [trip["x"], trip["y"]]:
            self.facts.pop("far", None)                           # the routed walk to the spot (travel/far_goto): r_far must not resume it
        self.__dict__.pop("_rp_best", None)
        self.ev("ranger_pet_trip_end", why=why, mins=round(dur / 60, 1), next_min=round(nxt / 60, 1), spot=trip.get("spot"), species=trip.get("kind"))
        self.log(f"ranger pet: trip for a {trip.get('kind')} ended ({why}) after {dur / 60:.1f} min" + (f"; next in {nxt / 60:.0f} min" if nxt else ""))

    def rp_trip_walk(self, trip):
        """To the spot, then look about inside the spawner's range (tamefind.find_animals)."""
        now = time.time()
        x, y = trip["x"], trip["y"]
        d = max(abs(self.c.x - x), abs(self.c.y - y))
        self.activity = f"looking for a {trip['kind']} to tame at {x},{y}"
        if d > max(14, trip["home"] // 2):
            self.travel(x, y, near=10, tries=2, per=40)
            return True
        if not trip["arrived"]:
            trip["arrived"] = now
        if trip["wander"] >= tamefind.WANDER_STEPS or now - trip["arrived"] > tamefind.STAY_SECS:
            self.rp_trip_end("none found")
            return True
        r = max(6, int(trip["home"] * random.uniform(0.4, 0.9)))
        ang = random.uniform(0, 2 * math.pi)
        trip["wander"] += 1
        self.goto_near(x + int(r * math.cos(ang)), y + int(r * math.sin(ang)), 5).wait(timeout=25)
        return True

    # ---- a try -----------------------------------------------------------------------------------------------------------------------------------

    def rp_tame(self, m, trip):
        now = time.time()
        ign = self.rp_ignored()
        chases = self.__dict__.setdefault("_rp_chase", {})
        ch = chases.setdefault(m.serial, {"since": now, "best": m.distance, "best_at": now})
        if m.distance < ch["best"]:
            ch["best"], ch["best_at"] = m.distance, now
        self.activity = f"taming {m.name}"
        if m.distance > TAME_RANGE:
            res = str(self.c.goto(m.x, m.y).wait(timeout=5))
            if res.startswith(("nopath", "failed")) or now - ch["best_at"] > CHASE_STALL or now - ch["since"] > CHASE_MAX:
                ign[m.serial] = now + IGNORE_S
                chases.pop(m.serial, None)
                self.log(f"ranger pet: gave up walking to {m.name} ({res[:30]}; no closer than {ch['best']} tiles)")
            return True
        chases.pop(m.serial, None)
        tries = self.__dict__.setdefault("_rp_tries", {})
        key = tamefind.norm(m.name)
        owned = m.serial in set(self.facts.get("owned_serials") or [])
        q = self.rp_kind(key, owned=owned)
        cap = tries_for(q[1]) if q else 0
        if tries.get(m.serial, 0) >= cap:
            ign[m.serial] = now + IGNORE_S
            return True
        if not self.cursor_after(lambda: self.c.call("useskill animal taming", timeout=6)):
            time.sleep(2)
            return True
        cur = next((x for x in self.c.mobiles(within=8) if x.serial == m.serial), None)
        if cur is None or max(abs(cur.x - self.c.x), abs(cur.y - self.c.y)) > TAME_RANGE:
            try:
                self.c.call("canceltarget", timeout=4)
            except Exception:
                pass
            return True
        tries[m.serial] = tries.get(m.serial, 0) + 1
        self.c.target(m.serial)
        taming, lore = self.rp_skills()
        mn = kind_min().get(key, 0.0)
        self.ev("ranger_pet_try", m=m.name, chance=round(tamefind.success_chance(mn, taming), 2), control=round(control_chance(mn, taming, lore), 2), n=tries[m.serial])
        result = ""
        deadline = time.time() + 30
        while time.time() < deadline:
            time.sleep(1.5)
            for l in self.read_journal():
                if re.search(RESULT_RE + r"|master|tame|follower|control", l, re.I):
                    result = l
            if re.search(RESULT_RE, result, re.I):
                break
        self.log(f"ranger pet: tame {m.name} (min {mn}, skill {taming:.1f}, try {tries[m.serial]}): {result[:100]}")
        self.refresh_skills()
        if re.search(r"accept you|even challenging", result, re.I):
            self.rp_keep(cur)
            strength = self.facts["pet"]["strength"]
            self.ev("ranger_pet_tamed", m=m.name, strength=round(strength), control=round(control_chance(mn, taming, lore), 2), tries=tries.pop(m.serial, 1))
            self.dlog("choice", what=f"keep companion {key}", why=f"strength {strength:.0f}")
            self.log(f"ranger pet: keeping {m.name} (strength {strength:.0f}) as a companion")
            self.rp_trip_end("tamed")
            return True
        if re.search(r"too many followers", result, re.I):
            self.rp_trip_end("no follower slot")
            self.rp_state()["next_at"] = time.time() + LOST_S
        elif re.search(r"no chance|cannot|too far|angry", result, re.I):
            ign[m.serial] = time.time() + IGNORE_S
        return True

    # ---- fetching it back -------------------------------------------------------------------------------------------------------------------------

    def rp_fetch(self, pet, now):
        """Out of view for FETCH_AFTER s, not yet LOST_S, within FETCH_REACH of where it was: walk back once, calm only, and call it."""
        if pet.get("fetched") or not pet.get("xy") or not self.rp_calm():
            return False
        unseen = now - pet.get("seen", now)
        if unseen < FETCH_AFTER or unseen > LOST_S:
            return False
        if any(m.serial == pet["serial"] for m in self.c.mobiles(within=18)):
            return False
        x, y = pet["xy"]
        if max(abs(self.c.x - x), abs(self.c.y - y)) > FETCH_REACH:
            return False
        pet["fetched"] = now
        self.activity = f"going back for the {pet['name']}"
        res = self.travel(x, y, near=6, tries=2, per=40)
        self.c.say("all come")
        time.sleep(1.0)
        self.rp_say("all follow me")
        self.ev("ranger_pet_fetch", m=pet["name"], walk=str(res)[:40])
        return True
