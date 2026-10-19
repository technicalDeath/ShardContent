"""Tamers who play like tamers (G5 / A5; Watcher's item 2026-10-17; the Helper). Mixin for TamerBot, written into the bot-farm folder by patch_tamers.py. Behind the feature "tame_find".

The finding: four tamers made almost no attempts in 45 minutes (AR 0, BR 1, CR 1, AdvR gave up on cats "no closer than 14 tiles" / "no path"). They patrolled the town's patrol
spots, where only livestock, birds, cats, dogs and rats live. The spawner files (Spawns/*.json, make_tame_spots.py -> tame_spots.json) put every animal worth taming at a skill of 55
in the WildLife spawners (boar, horse, goat, pig, sheep, cow, cougar, panther, black / brown / grizzly bear, timber / grey wolf, great hart, eagle, bull): five of them within 300
tiles of Britain, the nearest 240 tiles west.

What a tamer does now:
 * FINDS: the spot (a spawner) whose animals are worth most at its Animal Taming, from tame_spots.json: only safe spots (nothing else there that hits for 6.5 or more), not where a
   bot died lately, not one marked empty (shared memory, 30 minutes). The value of a kind is the chance that an attempt can still teach: the server's check (AnimalTaming.cs:
   CheckTargetSkill from min - 0.1 to min + 49.9) means no chance below the animal's minimum, no gain from skill min + 49.9 on, and a success chance (skill - min + 0.1) / 50;
   the spot's value = sum of count x value of the kinds in the window, discounted by distance. It travels there (routed legs), then walks about inside the spawner's range looking
   for animals (up to 10 wander steps over one 10-minute respawn cycle), and marks the spot empty (10 min, longer when it keeps being empty) when none showed up. ev tame_spot {spot, dist, value, kinds}, tame_spot_empty {spot, wandered}.
 * CHOOSES among the animals in sight by success chance, not by hardness: a success chance near 40% (an animal at min about skill - 20); the old order took the hardest first (a
   panther at skill 55.0 is a 4% chance), and the per-attempt chance of a skill gain barely depends on the success chance (b + (1 - p) * 0.2..0.5, b = 1 - skill / 100), so the
   hard ones only cost time. A kind that would be a stronger pet than the one it has goes first when its chance is at least 15%.
 * SKIPS what it cannot reach: no gain in distance for 12 s (was 20 s / 75 s): the animal is ignored for 10 minutes for everyone.
 * KEEPS the best pet (strength = hit points x average hit; the old rule: at least 90 and 1.3x the current pet), tiers none / small / horse-class / bear-class / strong / dire-class;
   ev tame {animal, kept, strength, tier} for every tame, ev pet_tier {tier, animal, strength} when the tier rises.
 * FIGHTS with it: a hostile that is not tameable and that the pet beats easily (the monster's strength at most 0.6 of the pet's, one monster in sight, the pet near) gets "all kill";
   the tamer stays instead of walking away (r_evade). ev pet_fight {pet, target, strength, theirs}. Afterwards "all guard me" as before.
 * HEALS it with bandages where the tamer has Veterinary 20+ (BotTameAdvR): the pet below 55% health within reach, ev pet_heal {pet, hp, ok}.
Not here: stabling the pet.
"""
import json
import math
import os
import random
import re
import time

HERE = os.path.dirname(os.path.abspath(__file__))
_SPOTS = None
_CS = None
GAIN_TOP = 49.9
# The watcher, 2026-10-18: 25 spot visits ended "no worthwhile animal" against 6 tames in three hours. The spots hold 1-3 of each kind,
# the fighters hunt the same hinds and boars, and most spawners refill in 5-10 minutes; 4 looks (about 2 min) then a 30-minute block for
# every tamer kept the tamers walking between empty spots. A tamer now stays one respawn cycle and an empty spot is skipped for one cycle.
WANDER_STEPS = 10
STAY_SECS = 600
EMPTY_TTL = 600
TARGET_P = 0.4
WILD_DANGER_AVG = 14
PET_TIERS = ((0, "none"), (40, "small"), (90, "horse-class"), (240, "bear-class"), (450, "strong"), (700, "dire-class"))


def norm(t):
    return re.sub(r"[^a-z]", "", re.sub(r"^(an?|the) ", "", t.lower()))


def spots():
    global _SPOTS
    if _SPOTS is None:
        try:
            _SPOTS = json.load(open(os.path.join(HERE, "tame_spots.json"), encoding="utf-8")).get("spots", [])
        except (OSError, ValueError):
            _SPOTS = []
    return _SPOTS


def creature_stats():
    global _CS
    if _CS is None:
        try:
            _CS = json.load(open(os.path.join(HERE, "creature_stats.json"), encoding="utf-8"))
        except (OSError, ValueError):
            _CS = {}
    return _CS


def success_chance(minskill, skill):
    """AnimalTaming.cs: CheckTargetSkill(skill, creature, min - 0.1, min + 49.9): no chance below, a straight line up to 1.0 at min + 49.9."""
    return max(0.0, min(1.0, (skill - (minskill - 0.1)) / 50.0))


def gain_chance(p, skill):
    b = max(0.0, 1.0 - skill / 100.0)
    return p * (b + (1.0 - p) * 0.5) + (1.0 - p) * (b + (1.0 - p) * 0.2)


def kind_value(minskill, skill):
    """How much an attempt on this animal is worth to a tamer at this skill: nothing when it cannot be tamed yet or can no longer teach, else the chance of a gain."""
    if skill < minskill - 0.1 or skill >= minskill + GAIN_TOP:
        return 0.0
    p = success_chance(minskill, skill)
    return gain_chance(p, skill) if p >= 0.05 else 0.0


def tier(strength):
    name = PET_TIERS[0][1]
    for lo, n in PET_TIERS:
        if strength >= lo:
            name = n
    return name


class TameFindMixin:
    # ---- the spot to go to ---------------------------------------------------------------------------------------------------------------------------------

    def kind_dmg(self, key):
        import tamer
        t = tamer.TAME.get(key) or {}
        return sum(t.get("dmg") or [0, 0]) / 2.0

    def kind_strength(self, key):
        import tamer
        t = tamer.TAME.get(key) or {}
        return (t.get("hits") or 0) * sum(t.get("dmg") or [0, 0]) / 2.0

    def kind_weight(self, k, skill):
        """What an attempt on this kind is worth beyond the chance of a gain: nearer a 40% success chance is better (the harder it is, the more it wastes; the easier, the less it
        teaches a skill that is already high), a kind that makes a real pet (strength 90+) counts double, a trivial one (a cat, a rat, a bird: strength under 40) a third, and one
        bots have tried many times without a single success counts nothing."""
        p = success_chance(k["min"], skill)
        w = 0.35 + 0.65 * math.exp(-(((p - TARGET_P) / 0.3) ** 2))
        s = self.kind_strength(k["key"])
        w *= 2.0 if s >= 90 else (0.3 if s < 40 else 1.0)
        seen = self.mem.res_stats("tame", k["key"])
        if seen and seen["fail"] >= 6 and seen["ok"] == 0:
            return 0.0
        return w

    def tspot_value(self, spot, skill):
        total = 0.0
        for k in spot["kinds"]:
            if self.kind_dmg(k["key"]) > WILD_DANGER_AVG and k["min"] > skill - 8:
                continue                                          # hits too hard to try near its minimum
            total += k["n"] * kind_value(k["min"], skill) * self.kind_weight(k, skill)
        return total

    def spot_evidence(self, spot):
        """0.6 .. 1.0 by how many sightings of this spot's tameable kinds the shared memory holds within 60 tiles (bots have walked the west spawners a lot, the east ones hardly
        at all, and two of those turned out empty); full marks from 40 sightings."""
        self.mem.refresh()
        cells = self.mem.state["world"]["cells"]
        keys = {k["key"] for k in spot["kinds"]}
        seen = 0
        for cell, c in cells.items():
            cx, cy = (int(v) for v in cell.split(","))
            if abs(cx - spot["x"]) <= 60 and abs(cy - spot["y"]) <= 60:
                seen += sum(n for kind, n in c["sights"].items() if kind in keys)
        return 0.6 + 0.4 * min(1.0, seen / 40.0)

    def spot_risk(self, spot):
        """0.35 .. 1.0: down by how close the spot's range is to a dangerous spawner (tame_spots.json danger_gap: 40+ tiles clear = 1.0, overlapping by 80 = 0.5) and by the deaths bots
        had within 60 tiles (shared memory, decayed): BotTameAdvR and BotTamerAR died four times in 30 minutes at spots 30-80 tiles from an orc camp, a troll and dire-wolf spawners."""
        gap = spot.get("danger_gap", 999)
        f = 1.0 if gap >= 40 else max(0.35, 0.5 + 0.5 * (gap + 80) / 120.0)
        self.mem.refresh()
        deaths = 0.0
        for cell, c in self.mem.state["world"]["cells"].items():
            cx, cy = (int(v) for v in cell.split(","))
            if abs(cx - spot["x"]) <= 60 and abs(cy - spot["y"]) <= 60:
                deaths += c.get("deaths", 0.0)
        return f / (1.0 + deaths)

    def tspot_blocked(self, key):
        return self.facts.get("tspot_skip", {}).get(key, 0) > time.time() or not self.mem.usable("tamespot", key)

    def pick_tspot(self):
        skill = self.skill()
        here = (self.c.x, self.c.y)
        try:
            home = tuple(self.home_centre())[:2]                      # the rings: near home first (patch_tame_rings.py)
        except Exception:
            home = here
        from memory import cell_of
        best = None
        for s in spots():
            key = f"{s['x']},{s['y']}"
            if not s.get("safe") or self.tspot_blocked(key) or self.near_death_spot(s["x"], s["y"], 100):
                continue
            v = self.tspot_value(s, skill)
            if v <= 0:
                continue
            d = max(abs(s["x"] - here[0]), abs(s["y"] - here[1]))
            if d > 400:
                continue                                          # a walk of that length crosses too much to be worth it
            if self.mem.dangerous_cell(cell_of(s["x"], s["y"])):
                continue                                          # the area danger map: too strong here for this bot
            far = (d + max(abs(s["x"] - home[0]), abs(s["y"] - home[1]))) / 2.0          # from here and from home alike: a stranded tamer heads back in
            score = v * self.spot_evidence(s) * self.spot_risk(s) / (1.0 + far / 150.0)
            if best is None or score > best[0]:
                best = (score, s, d, v)
        return best

    def find_animals(self):
        """r_explore for a tamer with the feature on: go to the spawner whose animals teach most, look about, mark it empty when nothing is there. False when the data has no spot
        for this skill (the old patrol then runs)."""
        now = time.time()
        st = self.facts.get("tspot")
        if st and now - st["since"] > 1500:
            st = None                                            # a spot is worked for at most 25 minutes at a time
        if not st or self.tspot_blocked(f"{st['x']},{st['y']}"):
            best = self.pick_tspot()
            if not best:
                self.facts.pop("tspot", None)
                return False
            score, s, d, v = best
            skill = self.skill()
            st = self.facts["tspot"] = {"x": s["x"], "y": s["y"], "home": s["home"], "since": now, "wander": 0, "arrived": 0}
            self.ev("tame_spot", spot=[s["x"], s["y"]], dist=d, value=round(v, 2), kinds=[k["key"] for k in s["kinds"] if kind_value(k["min"], skill) > 0][:8])
            self.log(f"tame: going to the animals at {s['x']},{s['y']} ({d} tiles; skill {skill:.1f})")
        x, y = st["x"], st["y"]
        d = max(abs(self.c.x - x), abs(self.c.y - y))
        self.activity = f"looking for animals at {x},{y}"
        if d > max(14, st["home"] // 2):
            self.travel(x, y, near=10, tries=2, per=40)
            return True
        if not st["arrived"]:
            st["arrived"] = now
        if st["wander"] >= WANDER_STEPS or now - st["arrived"] > STAY_SECS:
            n = self.facts.setdefault("tspot_empty_n", {}).get(f"{x},{y}", 0) + 1
            self.facts["tspot_empty_n"][f"{x},{y}"] = n
            ttl = EMPTY_TTL * min(n, 4)                         # found empty again: 10, 20, 30, 40 min
            self.mem.record("blocked", kind="tamespot", key=f"{x},{y}", ttl=ttl)
            self.facts.setdefault("tspot_skip", {})[f"{x},{y}"] = now + ttl          # (the shared memory is read every 20 s: this bot must not pick the spot again meanwhile)
            self.ev("tame_spot_empty", spot=[x, y], wandered=st["wander"])
            self.log(f"tame: no worthwhile animal at {x},{y} after {st['wander']} looks: next spot")
            self.facts.pop("tspot", None)
            return True
        # walk about inside the spawner's range: a point on a ring at 40-90% of its home range, a different one each time
        r = max(6, int(st["home"] * random.uniform(0.4, 0.9)))
        ang = random.uniform(0, 2 * math.pi)
        st["wander"] += 1
        self.goto_near(x + int(r * math.cos(ang)), y + int(r * math.sin(ang)), 5).wait(timeout=25)
        return True

    # ---- choosing among the animals in sight ----------------------------------------------------------------------------------------------------------------

    def rank_candidates(self, out):
        """out: [(min, -distance, mobile, table row)]. A stronger pet than the one it has first (its chance 15%+), then the success chance nearest 40%, then the nearer."""
        skill = self.skill()
        pet = self.facts.get("pet")
        cur = pet["strength"] if pet else 0

        def key(r):
            lo, nd, m, t = r
            p = success_chance(t["min"], skill)
            strength = self.pet_strength(m.name)
            upgrade = 1 if (strength >= self.PET_MIN and strength > cur * self.PET_UPGRADE and p >= 0.15) else 0
            return (upgrade, -abs(p - TARGET_P), nd)
        return sorted(out, key=key, reverse=True)

    # ---- the pet ----------------------------------------------------------------------------------------------------------------------------------------------

    def pet_view(self):
        pet = self.facts.get("pet")
        if not pet:
            return None, None
        return pet, next((x for x in self.c.mobiles(within=18) if x.serial == pet["serial"]), None)

    def monster_strength(self, m):
        st = creature_stats().get(self.mkey(m))
        if not st:
            return None
        h, d = st.get("hits") or [0, 0], st.get("damage") or [0, 0]
        return (sum(h) / 2.0) * (sum(d) / 2.0)

    def is_monster(self, m):
        return any(w in m.name.lower() for w in self.MONSTERS) or not m.name.lower().startswith(("a ", "an "))

    def pet_handles(self, mons):
        """The pet beats this lone monster easily: its strength x 0.6 is at least the monster's, it is within 8 tiles and not hurt."""
        if len(mons) != 1 or not self.feature("tame_find"):
            return False
        pet, pm = self.pet_view()
        if not pet or pm is None or pm.distance > 8 or pm.hp_pct < 60:
            return False
        s = self.monster_strength(mons[0])
        return s is not None and s <= pet["strength"] * 0.6

    def r_pet_fight(self):
        if not self.feature("tame_find") or self.c.ghost:
            return False
        mons = [m for m in self.mobs(9) if self.is_monster(m)]
        if not self.pet_handles(mons):
            return False
        pet, mon = self.facts["pet"], mons[0]
        now = time.time()
        if now - pet.get("killed_at", 0) < 20:
            return True                                           # the order was given: the tamer stays put and lets it work
        pet["killed_at"] = now
        self.activity = f"letting the {pet['name']} fight {mon.name}"
        from uo import Event
        self.c.events.drain()
        self.c.say("all kill")
        if self.c.wait_for(Event.TARGET_REQUEST, timeout=3) is not None:
            self.c.target(mon.serial)
        self.ev("pet_fight", pet=pet["name"], target=mon.name, strength=round(pet["strength"]), theirs=round(self.monster_strength(mon) or 0))
        self.log(f"pet: {pet['name']} (strength {pet['strength']:.0f}) told to kill {mon.name}")
        return True

    def r_pet_heal(self):
        """Bandage the pet (Veterinary 20+) when it is under 55% and near."""
        if not self.feature("tame_find") or self.c.ghost or self.skill_values.get("Veterinary", 0) < 20 or self.mobs(4):
            return False
        pet, pm = self.pet_view()
        if not pet or pm is None or time.time() - pet.get("healed_at", 0) < 15:
            return False
        bandage = self.c.find("bandage")
        if not bandage:
            return False
        try:
            self.c.call(f"hp {pm.serial}", timeout=4)              # the client holds a placeholder until it has asked
        except Exception:
            pass
        cur = next((x for x in self.c.mobiles(within=18) if x.serial == pet["serial"]), pm)
        if cur.hp_pct >= 55:
            return False
        pet["healed_at"] = time.time()
        if cur.distance > 1:
            self.c.goto(cur.x, cur.y).wait(timeout=6)
        from uo import Event
        self.c.events.drain()
        self.c.use_on(bandage.serial, pet["serial"])
        ev = self.c.wait_for([Event.BANDAGE_DONE, Event.BANDAGE_FAILED], timeout=12)
        self.ev("pet_heal", pet=pet["name"], hp=round(cur.hp_pct), ok=bool(ev and ev.kind == Event.BANDAGE_DONE))
        return True

    def pet_events(self, m, strength, kept):
        """ev tame {animal, kept, strength, tier} for every tame, ev pet_tier when the kept pet's tier rises."""
        t = tier(strength)
        self.ev("tame", animal=m.name, kept=bool(kept), strength=round(strength), tier=t, m=m.name)
        if kept:
            best = self.facts.get("pet_tier_best", "none")
            names = [n for _, n in PET_TIERS]
            if names.index(t) > names.index(best):
                self.facts["pet_tier_best"] = t
                self.ev("pet_tier", tier=t, animal=m.name, strength=round(strength))
