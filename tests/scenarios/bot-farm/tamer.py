"""Animal Tamer: looks for animals the server's taming table says it can tame, walks up to the one that teaches the most, tames it, uses Animal Lore on it
and lets it go to make room for the next. The pet-handling messages it meets (followers, control, release) go to the notes.

    python tamer.py --name BotTamerA --profession 20 --for 3600
"""
from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
import time

from bot_common import BotBase
from hunter import SPOTS, HunterBot
from memory import cell_of, choose_spot
from uo import Event
from tamefind import TAME_RES, TameFindMixin
from fields import FieldsMixin
from pethunt import PetHuntMixin                         # the pet kills, the tamer loots (feature pet_hunt)
from tamerarms import TamerArmsMixin                     # the tamer shoots beside its pet (feature tamer_weapon)

HERE = os.path.dirname(os.path.abspath(__file__))
TAME = json.load(open(os.path.join(HERE, "tame_data.json"), encoding="utf-8"))
WILD_DANGER = 14      # average damage per hit at which a tame attempt is not worth the bandage bill for a 77 hit point character
RELEASE_GAP = 120     # full follower slots are freed at most this often (patch_tamer_followers)
GIVE_UP = 3600        # a release that freed nothing (the pets are out of earshot): not again for this long (patch_step3_fixes)
OWNED_MAX = 300       # serials of animals this tamer has owned, kept to never tame them again (AnimalTaming.cs: an animal whose Owners list holds the tamer
                      # is tamed with no skill check, "That wasn't even challenging": no Taming or Lore gain, and a follower slot taken all the same)
FLIERS = ("eagle", "bird", "hawk", "raven", "crow", "harpy")      # not taken back as a pet: they keep ahead of a walking tamer
LOST_REACH = 200      # a lost pet last seen within this many tiles is walked back to and released, when the slots are full
FERAL_AFTER = 11 * 3600   # an unfed pet loses MaxLoyalty / 10 an hour (BaseCreature.LoyaltyTimer) and goes free at 0: its slot is back within about 11 h


def norm(t):
    return re.sub(r"[^a-z]", "", re.sub(r"^(an?|the) ", "", t.lower()))


from stock import TamerStock  # noqa: E402
from wear import GathererArmor  # noqa: E402  (leather and studded armour, feature gather_armor)
class TamerBot(TamerArmsMixin, PetHuntMixin, FieldsMixin, TamerStock, TameFindMixin, GathererArmor, BotBase):
    RULES = ["r_dead", "r_corpse", "r_gear", "r_cure", "r_flee", "r_loot", "r_pet_hunt", "r_pet_fight", "r_evade", "r_heal", "r_pet_heal", "r_pet", "r_stock", "r_tamer_arms", "r_upgrade", "r_tame", "r_sellgoods", "r_bank", "r_explore"]

    # feature tamer_carve (2026-11-02): the tamer carves what its pet kills and sells it, as a tamer of the era lived on hides and meat. The pet hunt valued
    # an animal by its coins alone (pethunt.kind_loot): a great hart (carve 123), a grizzly (96), a hind (80), bears (68) and cougars (58) were worth 0, the
    # animal fields all "worth 0", and the bear was sent at rats and slimes the fighters had cleared: 1-2 kills an hour. The loot code skipped every carve
    # ("not_carvable": a TamerBot had no CARVE) though it carries a dagger and a skinning knife. The carving parts are the fighters' own (HunterBot).
    CUTS_HIDES = True          # hides cut on the corpse (5 stones each, the leather 1): uncut, the tamer dropped 46 piles of hides in half an hour (03:00-03:25)
    CARVE_KINDS = HunterBot.CARVE_KINDS
    BLADES = HunterBot.BLADES
    carving_blade = HunterBot.carving_blade

    @property
    def CARVE(self):
        return self.feature("tamer_carve")

    def r_sellgoods(self):
        """Carved goods (meat, hides cut into leather, feathers) to the shops that buy them, with the fighters' sell errand (errands.Act.do_sell): when the
        trip pays or the pack is heavy (basics.sell_due), or twenty minutes after the last sale."""
        if not self.CARVE:
            return False
        import errands
        import items
        if not any(items.is_goods(i.name) for i in self.c.backpack) or self.threats(10) or time.time() - self.facts.get("goods_sold_at", 0) < 300:
            return False
        if not (self.sell_due() or self.sale_due("goods_sold_at")):
            return False
        self.facts["goods_sold_at"] = time.time()
        self.activity = "selling carved goods"
        gold0 = self.c.gold
        errands.Act.do_sell(None, self, {}, {"task": "sell"})
        self.log(f"sold carved goods: gold {gold0} -> {self.c.gold}")
        return True
    PET_MIN = 90               # a horse (98) and up: around Britain the bears and wolves are rare and go to the fighters first
    PET_UPGRADE = 1.3          # trade up only for a clearly stronger animal
    PERSIST = BotBase.PERSIST + ("pet", "lost_pets", "owned_serials", "goods_sold_at")      # a restart keeps the pet: the pets follow on, the record did not (2026-10-30)
    PERSIST_CAPS = {"owned_serials": OWNED_MAX}           # saved lists keep their newest 20: the 300 owned animals came back as 20 at each restart, and the
                                                          # tamer re-tamed its old animals ("wasn't even challenging") 19-24 times a half-hour (2026-11-01)
    # its own r_evade: wild animals are what a tamer walks up to, monsters are what it walks away from
    MONSTERS = ("orc", "troll", "skeleton", "zombie", "shade", "wraith", "spectre", "lizardman", "ettin", "ogre", "harpy", "ratman", "gazer",
                "daemon", "lich", "gargoyle", "headless", "slime", "mongbat", "corpser", "reaper", "brigand")

    def __init__(self, name, profession):
        super().__init__(name, profession)
        self.spots = list(self.patrol_spots())
        random.Random(name).shuffle(self.spots)
        self.tamed = 0
        self.failed = 0
        self.ignored = {}
        self.chases = {}                  # serial -> {"since", "best", "best_at"}: how the walk up to each animal is going

    def skill(self):
        return self.skill_values.get("Animal Taming", 50.0)

    EVADE_SKIP = 600          # s a tame spot is left after a monster was walked away from there

    def r_evade(self):
        """A monster within seven tiles (a troll, a lizardman, the undead, or a creature with a personal name, which are orcs, lizardmen and
        ratmen): walk away from it toward town before it arrives. BotTameAdvR died twice in its first ten minutes standing beside them, since
        nothing but r_flee at 40% health moved a tamer. Animals are left alone: they are what a tamer walks up to."""
        if self.c.ghost:
            return False
        near = [m for m in self.mobs(7) if any(w in m.name.lower() for w in self.MONSTERS) or not m.name.lower().startswith(("a ", "an "))]
        if not near or self.pet_handles(near):
            return False                                  # (a monster the pet beats easily is the pet's: r_pet_fight)
        m = near[0]
        self.activity = f"walking away from {m.name}"
        self.note("danger", f"A {m.name} came within {m.distance} tiles of a tamer looking for animals; a tamer has no weapon skill and can only walk "
                            "away and come back later.", key=f"evade:{self.mkey(m)}")
        self.cur_spot = None                          # and look for animals somewhere else
        st = self.facts.pop("tspot", None)
        if st:
            # the tame spot it was working (tamefind.find_animals) is left for EVADE_SKIP: kept, the next tick walked back to it past the same monster. BotTamerAR
            # went evade, explore, evade, explore four times past a lizardman and died at 7 hit points (2026-10-31; 18 such runs in its log)
            self.facts.setdefault("tspot_skip", {})[f"{st['x']},{st['y']}"] = time.time() + self.EVADE_SKIP
            self.ev("tame_spot_evaded", spot=[st["x"], st["y"]], m=self.mkey(m))
        self.sprint()
        self.c.goto(*self.flee_point(m)).wait(timeout=8)
        return True

    def reachable(self, m):
        return abs((m.pos[2] or 0) - (self.c.z or 0)) <= 14 and (m.distance > 12 or self.los(m.serial))

    def candidates_naive(self):
        """A new tamer does not know how hard each animal is: it tries what looks like an animal and learns from "You have no chance" and from failures."""
        out = []
        for m in self.c.mobiles(within=16):
            n = m.name.lower()
            if m.notoriety == "Innocent" or self.ignored.get(m.serial, 0) > time.time() or not n.startswith(("a ", "an ")) or not self.mem.usable("tamemob", m.serial):
                continue
            if any(w in n for w in ("orc", "troll", "skeleton", "zombie", "shade", "wraith", "spectre", "lizardman", "ettin", "ogre", "harpy", "ratman", "gazer", "daemon", "lich")):
                continue
            if not self.reachable(m):
                continue
            seen = self.mem.res_stats(TAME_RES, norm(m.name))
            if seen and seen["fail"] >= 4 and seen["ok"] == 0:
                continue
            taught = self.mem.res_stats("tamegain", norm(m.name))
            if taught and taught["fail"] >= 3 and taught["ok"] == 0:
                continue                      # tamed (or tried) three times without a single gain: too easy to teach anything now
            score = ((seen["ok"] if seen else 0) + 1) / ((seen["ok"] + seen["fail"] if seen else 0) + 2)
            out.append((score, -m.distance, m, {"min": 0}))
        out.sort(key=lambda r: (r[0], r[1]), reverse=True)
        return out

    def candidates(self):
        if self.mode == "newbie":
            return self.candidates_naive()
        out = []
        sk = self.skill()
        owned = set(self.facts.get("owned_serials") or [])
        why = self.__dict__.setdefault("_cand_why", {})       # what each animal in view was turned down for, read out when a spot ends empty (tamefind)
        for m in self.c.mobiles(within=16):
            t = TAME.get(norm(m.name))
            if not t:
                continue                      # not an animal that can be tamed
            retake = m.serial == self.__dict__.get("_retake")          # a pet taken back on purpose (retake_pet)
            if m.notoriety == "Innocent" or (m.serial in owned and not retake) or self.ignored.get(m.serial, 0) > time.time() or not self.mem.usable("tamemob", m.serial):
                why[norm(m.name) + (": owned" if m.serial in owned else ": ignored/blocked")] = why.get(norm(m.name) + (": owned" if m.serial in owned else ": ignored/blocked"), 0) + 1
                continue                      # (an animal it owned once teaches nothing and takes a slot: OWNED_MAX)
            if retake:
                out.append((t["min"], -m.distance, m, t))
                continue
            kept = self.facts.get("pet")
            if kept and m.serial != kept.get("serial") and norm(m.name) == norm(kept.get("name") or ""):
                why[norm(m.name) + ": same name as the pet"] = why.get(norm(m.name) + ": same name as the pet", 0) + 1
                continue                      # speech names pets by their name: a second brown bear tamed beside the kept one is let go with "release"
                                              # for both (after_tame), and the pet goes with it: BotTamerAR lost its brown bear (strength 414) so at
                                              # 22:37 and hunted nothing for an hour (2026-11-01)
            if t["min"] > sk + 1 or t["min"] < sk - 46:
                why[norm(m.name) + ": skill window"] = why.get(norm(m.name) + ": skill window", 0) + 1
                continue                      # unreachable, or so easy that taming it cannot teach anything
            if not self.reachable(m):
                why[norm(m.name) + ": unreachable"] = why.get(norm(m.name) + ": unreachable", 0) + 1
                continue
            seen = self.mem.res_stats(TAME_RES, norm(m.name))
            if seen and seen["fail"] >= 6 and seen["ok"] == 0:
                why[norm(m.name) + ": never tamed by bots"] = why.get(norm(m.name) + ": never tamed by bots", 0) + 1
                continue                      # bots have tried this kind many times and never tamed one: not worth the time
            dmg = (t.get("dmg") or [0, 0])
            if sum(dmg) / 2 > WILD_DANGER and t["min"] > sk - 8:
                why[norm(m.name) + ": too strong"] = why.get(norm(m.name) + ": too strong", 0) + 1
                continue
            out.append((t["min"], -m.distance, m, t))
        if self.feature("tame_find"):
            return self.rank_candidates(out)                  # the success chance nearest 40%, a stronger pet first
        out.sort(key=lambda r: (r[0], r[1]), reverse=True)
        return out

    def r_heal(self):
        if self.hp_pct() >= 65 or self.mobs(3) or not self.c.find("bandage"):
            return False
        return self.bandage_self()

    def tame_rolled(self, result, t):
        """True when the engine rolled this tame: accepted, "You fail to tame the creature." or "too angry" (AnimalTaming.cs), at a skill at or above the
        kind's MinTameSkill (below it the engine refuses before any roll, line 206). Only these go to the shared TAME_RES verdict: six great hart
        tries at 58.1-58.5 (min 59.1), all with no answer read, barred the kind as "never tamed by bots" from BotTamerAR at 79.5, where the engine
        gives it (79.5 - 59.1 + 0.1) / 50 = 41% and gains to 109 (2026-11-02)."""
        if not re.search(r"accept you|fail to tame|too angry", result or "", re.I):
            return False
        try:
            return self.skill() >= float((t or {}).get("min", 0) or 0)
        except Exception:
            return False

    def r_tame(self):
        if self.hp_pct() < 55 or self.hunt_due():
            return False                                  # (taming waits while the pet hunts: pethunt.py)
        if self.release_spares():
            return True
        cands = self.candidates()
        if not cands and self.retake_pet():
            cands = self.candidates()
        if not cands:
            return self.clear_owned()
        lo, _, m, t = cands[0]
        freed = self.free_slots_for(m)
        if freed:
            return freed is True                          # freed: a turn spent; "full" (pets out of reach): the other rules run (patch_step3_fixes)
        self.activity = f"taming {m.name} (needs {lo})"
        now = time.time()
        self.chases = {s: c for s, c in self.chases.items() if now - c["since"] < 600}
        ch = self.chases.setdefault(m.serial, {"since": now, "best": m.distance, "best_at": now})
        if m.distance < ch["best"]:
            ch["best"], ch["best_at"] = m.distance, now
        if m.distance > 2:
            # Taming reaches two tiles. An animal in a pen or one that keeps wandering off can be chased forever: give up when the walk stops gaining.
            res = str(self.c.goto(m.x, m.y).wait(timeout=5))
            find = self.feature("tame_find")
            stalled = now - ch["best_at"] > (12 if find else 20) or now - ch["since"] > (45 if find else 75)
            if res.startswith(("nopath", "failed")) or stalled:
                why = "no path to it" if res.startswith(("nopath", "failed")) else f"no closer than {ch['best']} tiles in {now - ch['since']:.0f} s"
                self.ignored[m.serial] = now + (600 if find else 300)
                self.mem.record("blocked", kind="tamemob", key=m.serial, ttl=600)
                self.mem.record("res", kind="tamereach", key=norm(m.name), ok=False, reason=why)
                self.log(f"gave up walking to {m.name} at {m.x},{m.y}: {why}")
                self.note("tame", f"A tamer could not get within two tiles of {m.name} ({why}); penned or wandering animals look tameable but nothing says they cannot be reached.",
                          key=f"tameunreachable:{norm(m.name)}")
                self.chases.pop(m.serial, None)
                return True
            self.mem.record("claim", kind="tamemob", key=m.serial, ttl=60)
            return True
        self.chases.pop(m.serial, None)
        if not self.tame_in_range(m):
            return True                                       # it walked off while we stood: close in again next tick
        if not self.cursor_after(lambda: self.c.call("useskill animal taming", timeout=6)):      # (basics.cursor_after: the cursor lands before wait_for listens)
            self.note("tame", "Using Animal Taming raised no target cursor.", key="notamecursor")
            time.sleep(2)
            return True
        if not self.tame_in_range(m):
            try:
                self.c.call("canceltarget", timeout=4)       # the cursor is open: do not spend it on "too far away"
            except Exception:
                pass
            return True
        self.c.target(m.serial)
        deadline = time.time() + 30
        result = ""
        while time.time() < deadline:
            time.sleep(1.5)
            lines = self.read_journal()
            for l in lines:
                if re.search(r"accept you as|even challenging|master|tame|fail|too far|cannot|must wait|already|stable|follower|control", l, re.I):
                    # "That wasn't even challenging." (AnimalTaming.cs, alreadyOwned) has none of the other words: unread, the owned animal took a slot and
                    # was never let go (BotTamerAR at 5 of 5 all night, 2026-11-01)
                    result = l
            if re.search(r"accept you|even challenging|fail|cannot|already|too far|no chance|stops", result, re.I):
                break
        self.log(f"tame {m.name} (min {lo}, skill {self.skill():.1f}): {result[:100]}")
        if self.__dict__.get("_retake") == m.serial:
            self.__dict__.pop("_retake", None)            # one try: left set, the mark let the owned animal past candidates() at every tick, and each
                                                          # re-tame with no slot to spare was let go again (a grey wolf four times in a minute, 24 an
                                                          # half-hour, 2026-11-01)
        if re.search(r"accept you|even challenging", result, re.I):
            owned = [s for s in (self.facts.get("owned_serials") or []) if s != m.serial] + [m.serial]
            self.facts["owned_serials"] = owned[-OWNED_MAX:]
        if re.search(r"even challenging", result, re.I):
            # an animal it owned before: a follower again, with no gain; kept or let go at once, or its slot is lost (5 of 5 full for a day, 2026-10-29/30)
            self.ev("tame_owned_again", m=m.name)
            self.after_tame(m)
            return True
        gained = any(re.search(r"skill in animal taming has increased", l, re.I) for l in list(self.journal)[-12:])
        if self.tame_rolled(result, t):
            self.mem.record("res", kind="tamegain", key=norm(m.name), ok=gained)      # a refused try teaches nothing and says nothing of the kind
            self.mem.record("res", kind=TAME_RES, key=norm(m.name), ok=bool(re.search(r"accept you", result, re.I)), reason=result[:60])
        if re.search(r"accept you", result, re.I):
            self.work += 1
            self.tamed += 1
            if not self.feature("tame_find"):
                self.ev("tame", m=m.name)
            self.note("tame", f"A successful tame says: {result[:100]}", key="tamemsg")
            self.after_tame(m)
        else:
            self.failed += 1
            if re.search(r"too many followers", result, re.I):
                self.facts["slots_full"] = True           # freed at the next tick (patch_tamer_followers)
            unseen = re.search(r"cannot be seen|too far", result, re.I)
            self.ignored[m.serial] = time.time() + (300 if unseen else 60)
            self.note("tame", f"A failed or refused tame says: {result[:100] or 'nothing'}", key=f"tamefail:{result[:30]}")
        self.refresh_skills()
        return True

    def retake_pet(self):
        """No pet, nothing to tame, and an animal it owned before in view that is strong enough to keep: take it back. An owned animal is tamed with no
        skill check (AnimalTaming.cs alreadyOwned, "That wasn't even challenging"), so it is a sure pet; the pet then clears the other released ones
        (clear_owned) and hunts (pethunt). BotTamerAR had no pet and only its own released animals around it for an hour (2026-10-30)."""
        if not self.feature("pet_hunt") or self.facts.get("pet") or not hasattr(self, "pet_view"):
            return False
        if not self.slot_to_spare():
            return False                                  # a pet taken back would fill the last slot, and taming needs one
        if self.adopt_pet():
            return False                                  # a pet of its own was following all along: clear_owned can use it now
        now = time.time()
        if now - self.__dict__.get("_retake_at", 0) < 30:
            return False                                  # once in 30 s: an eagle that out-flew the walk was picked, refused (ignored) and picked again
                                                          # dozens of times a second (5,060 rabbit looks in two minutes, 2026-10-30)
        self.__dict__["_retake_at"] = now
        owned = set(self.facts.get("owned_serials") or [])
        mine = [m for m in self.c.mobiles(within=10) if m.serial in owned and self.pet_strength(m.name) >= self.PET_MIN and self.ignored.get(m.serial, 0) <= now
                and not any(w in m.name.lower() for w in FLIERS)       # an eagle out-flew the walk to it and was never reached (run 3, 2026-10-30)
                and self.mem.usable("tamemob", m.serial) and self.reachable(m)]       # the candidate scan's own filters: run 4 picked a cougar the shared memory
                                                                                    # had blocked, so candidates() dropped it and nothing was tamed
        if not mine:
            return False
        m = max(mine, key=lambda x: (self.pet_strength(x.name), -x.distance))
        self.__dict__["_retake"] = m.serial
        self.log(f"tame: no pet, and {m.name} (strength {self.pet_strength(m.name):.0f}), released earlier, is here: taking it back as the pet")
        self.ev("retake_pet", m=m.name)
        return True

    SPARE_REACH = 12           # pets hear orders within their perception range (BaseCreature.HandlesOnSpeech, RangePerception 16 for animals)

    def release_spares(self):
        """Every follower slot is taken and pets of this tamer other than the kept one stand within earshot: "all release" (confirmed), then the
        strongest is taken back, a sure tame (AnimalTaming.cs alreadyOwned). free_slots_for only runs for a candidate, and with only owned animals about
        there was none: BotTamerAR held 5 of 5 slots for hours, "no taming for 209 min", with two spare black bears at 2-4 tiles (2026-10-30)."""
        try:
            f = int(self.c.state.get("followers") or 0)
            mx = int(self.c.state.get("maxFollowers") or 5)
        except Exception:
            return False
        if mx <= 0 or f < mx:
            return False
        now = time.time()
        if now - self.__dict__.get("_spares_at", 0) < 60:
            return False
        pets = [m for m in self.c.mobiles(within=self.SPARE_REACH) if (getattr(m, "_d", None) or {}).get("isPet")]
        keep = (self.facts.get("pet") or {}).get("serial")
        if not [m for m in pets if m.serial != keep]:
            return False
        self.__dict__["_spares_at"] = now
        self.activity = "releasing spare pets"
        self.log(f"tame: {f} of {mx} follower slots taken, {len(pets)} of its pets in earshot: releasing them all, then taking the strongest back")
        self.release("all", count=len(pets))
        time.sleep(1.5)
        try:
            after = int(self.c.state.get("followers") or 0)
        except Exception:
            after = f
        best = max(pets, key=lambda x: (self.pet_strength(x.name), -x.distance))
        owned = [s_ for s_ in (self.facts.get("owned_serials") or []) if s_ not in {m.serial for m in pets}] + [m.serial for m in pets]
        self.facts["owned_serials"] = owned[-OWNED_MAX:]          # released, they are its own animals: no skill check, cleared by the pet later
        self.facts.pop("pet", None)
        self.facts.pop("release_gave_up_until", None)
        if after + 1 >= mx:
            # taking one back would fill the slots again: the freed slot is for taming. With four slots held by pets out of earshot, BotTamerAR freed
            # one, took a boar back and was full again, a dozen times in eight minutes, each "tame" of its own boar teaching nothing (2026-10-31)
            self.log(f"tame: followers {f} -> {after}; no pet taken back: the free slot is for taming")
            self.ev("release_spares", pets=len(pets), before=f, after=after, keep=None)
            return True
        self.__dict__["_retake"] = best.serial
        self.log(f"tame: followers {f} -> {after}; taking {best.name} back as the pet")
        self.ev("release_spares", pets=len(pets), before=f, after=after, keep=best.name)
        return True

    def adopt_pet(self):
        """No pet on record, but the client shows pets of this character in view (the world file's isPet): adopt the strongest. The pet record did not
        survive a brain restart while the pets did: BotTamerAR walked with two black bears at 2-3 tiles (5 of 5 follower slots), tried to "take back" one of
        them twice, and had no pet to clear or hunt with (2026-10-30)."""
        pets = [m for m in self.c.mobiles(within=14) if (getattr(m, "_d", None) or {}).get("isPet")]
        if not pets:
            return False
        m = max(pets, key=lambda x: (self.pet_strength(x.name), -x.distance))
        now = time.time()
        self.facts["pet"] = {"serial": m.serial, "name": m.name, "strength": self.pet_strength(m.name), "since": now, "seen": now}
        owned = [s_ for s_ in (self.facts.get("owned_serials") or []) if s_ != m.serial] + [m.serial]
        self.facts["owned_serials"] = owned[-OWNED_MAX:]
        self.log(f"tame: {m.name} ({m.distance} tiles) is already this tamer's pet: adopted ({len(pets)} pets in view)")
        self.ev("pet_adopted", m=m.name, pets=len(pets))
        self.c.say("all guard me")
        return True

    def clear_owned(self):
        """Nothing to tame in view, but animals this tamer owned before are: they teach nothing (AnimalTaming.cs alreadyOwned) and no spawner replaces
        them while they live, as taming unlinked them (BaseSpawner.UnlinkOnTaming). The pet kills one; r_loot carves and loots it. At five spots in 20
        minutes the animals in view were its own released boars, hinds, cougars and wolves (2026-10-30). True when the pet was sent."""
        if not self.feature("pet_hunt") or not hasattr(self, "pet_view"):
            return False
        pet, pm = self.pet_view()
        if pm is None:
            return False
        now = time.time()
        if now - self.__dict__.get("_clear_at", 0) < 30:
            return False
        owned = set(self.facts.get("owned_serials") or [])
        mine = [m for m in self.c.mobiles(within=10) if m.serial in owned and m.serial != pet.get("serial") and self.pet_beats([self.mkey(m)])
                and self.ignored.get(m.serial, 0) <= now]
        if not mine:
            return False
        m = min(mine, key=lambda x: x.distance)
        self.__dict__["_clear_at"] = now
        self.ignored[m.serial] = now + 120                   # one order a target; the pet finishes it while the tamer looks on
        self.pet_order(m)
        self.activity = f"letting the {pet['name']} clear {m.name}, an animal it owned"
        self.log(f"tame: sent {pet['name']} at {m.name} ({m.distance} tiles), released earlier: it teaches nothing and keeps the spawn from refilling")
        self.ev("clear_owned", pet=pet["name"], target=m.name)
        return True

    def free_slots_for(self, m):
        """No follower slot for this animal (the client's follower count, or the server said so): release them all. True when it did (patch_tamer_followers)."""
        try:
            f = int(self.c.state.get("followers") or 0)
            mx = int(self.c.state.get("maxFollowers") or 5)
        except Exception:
            f, mx = 0, 5
        need = int((TAME.get(norm(m.name)) or {}).get("slots") or 1)
        full = self.facts.pop("slots_full", False) or (mx > 0 and f + need > mx)
        if full and time.time() < self.facts.get("release_gave_up_until", 0):
            return "full"                                 # the pets are out of earshot: no tame until slots come back (patch_step3_fixes)
        if not full or time.time() - self.facts.get("released_at", 0) < RELEASE_GAP:
            return False
        self.facts["released_at"] = time.time()
        why = f"{f} of {mx} follower slots in use, {need} needed for {m.name}"
        pet = self.facts.get("pet")
        self.log(f"tame: {why}: releasing them all" + (f" but {pet['name']}, the kept pet" if pet else ""))
        self.release("all", count=max(1, f), keep=(pet or {}).get("name"))
        time.sleep(1.5)
        try:
            after = int(self.c.state.get("followers") or 0)
        except Exception:
            after = f
        if f and after >= f and self.fetch_lost_pet():
            return True                                   # walked back to where a lost pet was last seen and released there
        if f and after >= f:
            lost = [p for p in (self.facts.get("lost_pets") or []) if time.time() - p["t"] < FERAL_AFTER]
            wait = GIVE_UP if not lost else max(GIVE_UP, min(p["t"] for p in lost) + FERAL_AFTER - time.time())
            self.facts["release_gave_up_until"] = time.time() + wait
            self.log(f"tame: the release freed nothing ({after} of {mx} still): the pets are out of earshot; no taming for {wait // 60:.0f} min")
            self.ev("pets_out_of_reach", n=after)
        self.ev("pets_released", n=f, why=why)
        self.dlog("choice", what="release all pets", why=why)
        return True

    def fetch_lost_pet(self):
        """The slots are full and "all release" reached nobody: walk to where the newest lost pet was last seen (within LOST_REACH, on ground this bot
        may use) and release all there, as a player goes back for a pet left behind. Each lost pet is gone back for once. True when it walked."""
        now = time.time()
        lost = [p for p in (self.facts.get("lost_pets") or []) if now - p["t"] < FERAL_AFTER and not p.get("fetched")]
        near = [p for p in lost if max(abs(p["xy"][0] - self.c.x), abs(p["xy"][1] - self.c.y)) <= LOST_REACH and not self.gather_danger(cell_of(*p["xy"]))]
        if not near:
            return False
        p = max(near, key=lambda p: p["t"])
        p["fetched"] = now
        self.activity = f"going back for {p['name']} at {p['xy'][0]},{p['xy'][1]}"
        res = self.travel(p["xy"][0], p["xy"][1], near=6)
        before = int(self.c.state.get("followers") or 0)
        self.release("all", count=max(1, before))
        time.sleep(1.5)
        after = int(self.c.state.get("followers") or 0)
        self.log(f"tame: went back for {p['name']} at {p['xy'][0]},{p['xy'][1]} ({res}): followers {before} -> {after}")
        self.ev("lost_pet_fetched", m=p["name"], walk=str(res)[:40], before=before, after=after)
        return True

    TAME_RANGE = 2                                            # AnimalTaming's target range before AOS

    def tame_in_range(self, m):
        """The animal's position now (the world file), within taming range of this character; False when it moved away or left view."""
        cur = next((x for x in self.c.mobiles(within=8) if x.serial == m.serial), None)
        if cur is None:
            return False
        return max(abs(cur.x - self.c.x), abs(cur.y - self.c.y)) <= self.TAME_RANGE

    def lost_pets_hold_slots(self):
        """Pets left out of earshot hold follower slots until they go feral (FERAL_AFTER). Then the last slot is better spent on a pet that hunts than on
        training tames let go at once: with four slots held so, BotTamerAR let every new pet go as "a training tame" and killed nothing for an hour (2026-11-01)."""
        now = time.time()
        return any(now - p.get("t", 0) < FERAL_AFTER for p in (self.facts.get("lost_pets") or [])) or now < self.facts.get("release_gave_up_until", 0)

    def slot_to_spare(self, counted=False):
        """True when a pet can be kept and a slot still stays free for taming. counted: the animal just tamed is in the count already."""
        try:
            f = int(self.c.state.get("followers") or 0)
            mx = int(self.c.state.get("maxFollowers") or 5)
        except Exception:
            return True
        return mx <= 0 or f + (0 if counted else 1) < mx

    def follower_count(self):
        try:
            return int(self.c.state.get("followers"))
        except Exception:
            return None

    @staticmethod
    def pet_strength(name):
        t = TAME.get(norm(name)) or {}
        dmg = t.get("dmg") or [0, 0]
        return (t.get("hits") or 0) * (dmg[0] + dmg[1]) / 2.0

    CONFIRM_WAIT = 5.0         # s to wait for the release confirm windows

    def release(self, name, count=1, keep=None):
        """Release a pet by speech, "<name> release". The server answers with a window asking to confirm (ConfirmReleaseGump): Okay is button 2.
        There is no "all release": release (keyword 0x16D) is only heard named (BaseAI/OnSpeech.cs, WasNamed: the speech starts with the pet's
        name), so "all" names each of this tamer's pets in earshot. The window is a Singleton (ConfirmReleaseGump.Singleton): a second pet's window
        closes the first, so five pets named at once let one go (BotTamerAR: "followers 5 -> 4" a dozen times, the other four kept, 2026-11-01).
        A player answers one window and then names the next pet: one pet a turn, as many turns as pets."""
        self.c.events.drain()
        if name == "all":
            turns = [m.name for m in self.c.mobiles(within=self.SPARE_REACH) if (getattr(m, "_d", None) or {}).get("isPet") and m.name
                     and not (keep and m.name.lower() == keep.lower())]              # keep: the kept pet's name, not named (free_slots_for)
            turns = sorted(turns)[:max(count, len(turns))]
        else:
            turns = [name] * max(1, count)
        wins = 0
        for n_ in turns:
            wins += self._release_one(n_)
        self.__dict__["_release_windows"] = wins

    def _release_one(self, name):
        """Name one pet for release and answer its window (waited for up to CONFIRM_WAIT); 1 when a window was answered. Two pets of one name both
        answer, and the Singleton window leaves the last: one of them goes, the next turn takes the other."""
        self.c.say(f"{name} release")
        end = time.time() + self.CONFIRM_WAIT
        serials = []
        while True:
            time.sleep(0.5)
            serials, cur = [], None
            try:
                for line in self.c.call("gumps", timeout=6):
                    mg = re.search(r"\[GUMP\] local 0x[0-9A-Fa-f]+ server (0x[0-9A-Fa-f]+)", line)
                    if mg:
                        cur = mg.group(1)
                    elif cur and "release" in line.lower() and cur not in serials:
                        serials.append(cur)
            except Exception:
                pass
            if serials or time.time() >= end:
                break
        for g in serials[-1:]:
            try:
                self.c.call(f"gumpresponse 2 gump:{g}", timeout=5)
            except Exception:
                pass
            time.sleep(0.8)
        self.note("pet", "Releasing a pet by speech opens a window asking to confirm; the pet is released only when Okay is pressed.", key="releaseconfirm")
        return 1 if serials else 0

    def r_pet(self):
        """Keep the kept pet close: every couple of minutes, if it is in sight, "all guard me"; if it has not been seen for ten minutes (it died,
        or wandered off after its master died), it is gone."""
        pet = self.facts.get("pet")
        if not pet or self.c.ghost:
            return False
        now = time.time()
        it = next((m for m in self.c.mobiles(within=18) if m.serial == pet["serial"]), None)
        seen = it is not None
        if seen:
            pet["seen"], pet["xy"] = now, [it.x, it.y]
        elif now - pet.get("seen", pet["since"]) > 600:
            self.facts.pop("pet")
            # alive somewhere it still holds its follower slot until it goes feral (FERAL_AFTER): where it was last seen is kept, to go back and release it
            lost = [p for p in (self.facts.get("lost_pets") or []) if now - p["t"] < FERAL_AFTER]
            lost.append({"name": pet["name"], "serial": pet["serial"], "xy": pet.get("xy") or [self.c.x, self.c.y], "t": pet.get("seen", now)})
            self.facts["lost_pets"] = lost[-5:]
            self.log(f"lost the pet {pet['name']} (not seen for ten minutes)")
            self.note("pet", f"A tamer lost its pet {pet['name']}: not seen for ten minutes (killed, or left behind).", key="petlost")
            return False
        if seen and now - pet.get("ordered", 0) > 120:
            pet["ordered"] = now
            self.c.say("all guard me")
            return False                                  # one line of speech, not a turn
        return False

    def after_tame(self, m):
        """Animal Lore on the new pet; keep it if it is the best fighter tamed yet, else let it go so the next animal can be tamed."""
        if self.cursor_after(lambda: self.c.call("useskill animal lore", timeout=6)):
            self.c.target(m.serial)
            time.sleep(3)
            for l in self.read_journal()[-4:]:
                self.note("tame", f"Animal Lore on a pet answers: {l[:100]}", key="loremsg")
            self.c.call("gumps", timeout=6)
        pet = self.facts.get("pet")
        strength = self.pet_strength(m.name)
        keep = strength >= self.PET_MIN and (pet is None or strength > pet["strength"] * self.PET_UPGRADE)
        if keep and pet is None and not self.slot_to_spare(counted=True) and not self.lost_pets_hold_slots():
            keep = False                                  # a first pet kept in the last slot leaves none to tame with: it goes, as a training tame
        if keep:
            if pet and pet["name"].lower() != m.name.lower():
                self.release(pet["name"])                    # the old pet, by its name; the new one has another
            self.facts["pet"] = {"serial": m.serial, "name": m.name, "strength": strength, "since": time.time(), "seen": time.time()}
            self.c.say("all guard me")
            if self.feature("tame_find"):
                self.pet_events(m, strength, True)
            self.dlog("choice", what=f"keep pet {norm(m.name)}", why=f"strength {strength:.0f}" + (f", over {pet['name']} ({pet['strength']:.0f})" if pet else ""))
            self.log(f"keeping {m.name} as a pet (strength {strength:.0f})")
            self.note("pet", f"A tamer kept a {m.name} as its pet and told it 'all guard me'.", key=f"keep:{norm(m.name)}")
            return
        if self.feature("tame_find"):
            self.pet_events(m, strength, False)
        before = self.follower_count()
        if pet and pet["name"].lower() == m.name.lower():
            # same name as the kept pet: speech cannot tell them apart, so the pet is let go with it and the next good tame is kept instead
            self.release("all", count=2)
            self.facts.pop("pet", None)
        else:
            self.release(m.name)
            time.sleep(1.0)
            after = self.follower_count()
            if before is not None and after is not None and after >= before:
                # not let go: once more, then the record (the slot stays taken until it goes feral, FERAL_AFTER)
                wins = self.__dict__.get("_release_windows", 0)
                self.release(m.name)
                time.sleep(1.0)
                again = self.follower_count()
                self.log(f"tame: {m.name} was not let go ({wins} confirm windows; followers {before} -> {after}); again: {again}")
                self.ev("release_unconfirmed", m=m.name, windows=wins, before=before, after=after, again=again)
        for l in self.read_journal():
            self.note("tame", f"Releasing a pet answers: {l[:100]}", key="releasemsg")

    def r_explore(self):
        if self.field_explore():
            return True                                   # the pet's hunt: a tier-1 area with monsters it beats (pethunt.py)
        if self.feature("tame_find") and self.find_animals():            # the spawner whose animals teach most (tame_spots.json), not the town's patrol spots
            return True
        if getattr(self, "cur_spot", None) is None or time.time() - self.facts.get("spot_since", 0) > self.explore_limit():
            recent = self.facts.setdefault("spots_reached", [])
            crowded = self.facts.get("crowded", {})
            self.cur_spot = choose_spot(self.mem, self.spots, lambda x, y: self.near_death_spot(x, y, 60) or crowded.get(cell_of(x, y), 0) > time.time(),
                                        here=(self.c.x, self.c.y), recent=recent[-4:],
                                        on_fallback=lambda spot, why: self.ev("spot_fallback", spot=list(spot), why=why))
            self.facts["spot_since"] = time.time()
        x, y = self.cur_spot
        self.activity = f"looking for animals toward {x},{y}"
        res = self.goto_near(x, y, 6).wait(timeout=6)
        if abs(self.c.x - x) < 6 and abs(self.c.y - y) < 6 or str(res).startswith(("nopath", "blocked")):
            self.facts.setdefault("spots_reached", []).append((x, y))
            self.cur_spot = None
        return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True)
    ap.add_argument("--profession", type=int, default=20)
    ap.add_argument("--for", dest="seconds", type=float, default=3600)
    a = ap.parse_args()
    bot = TamerBot(a.name, a.profession)
    bot.refresh_skills()
    bot.run(a.seconds)


if __name__ == "__main__":
    sys.exit(main())
