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
from hunter import SPOTS
from memory import cell_of, choose_spot
from uo import Event
from tamefind import TameFindMixin

HERE = os.path.dirname(os.path.abspath(__file__))
TAME = json.load(open(os.path.join(HERE, "tame_data.json"), encoding="utf-8"))
WILD_DANGER = 14      # average damage per hit at which a tame attempt is not worth the bandage bill for a 77 hit point character


def norm(t):
    return re.sub(r"[^a-z]", "", re.sub(r"^(an?|the) ", "", t.lower()))


from stock import TamerStock  # noqa: E402
class TamerBot(TamerStock, TameFindMixin, BotBase):
    RULES = ["r_dead", "r_corpse", "r_gear", "r_cure", "r_flee", "r_pet_fight", "r_evade", "r_heal", "r_pet_heal", "r_pet", "r_stock", "r_tame", "r_bank", "r_explore"]
    PET_MIN = 90               # a horse (98) and up: around Britain the bears and wolves are rare and go to the fighters first
    PET_UPGRADE = 1.3          # trade up only for a clearly stronger animal
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
            seen = self.mem.res_stats("tame", norm(m.name))
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
        for m in self.c.mobiles(within=16):
            if m.notoriety == "Innocent" or self.ignored.get(m.serial, 0) > time.time() or not self.mem.usable("tamemob", m.serial):
                continue
            t = TAME.get(norm(m.name))
            if not t or t["min"] > sk + 1 or t["min"] < sk - 46:
                continue                      # unreachable, or so easy that taming it cannot teach anything
            if not self.reachable(m):
                continue
            seen = self.mem.res_stats("tame", norm(m.name))
            if seen and seen["fail"] >= 6 and seen["ok"] == 0:
                continue                      # bots have tried this kind many times and never tamed one: not worth the time
            dmg = (t.get("dmg") or [0, 0])
            if sum(dmg) / 2 > WILD_DANGER and t["min"] > sk - 8:
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

    def r_tame(self):
        if self.hp_pct() < 55:
            return False
        cands = self.candidates()
        if not cands:
            return False
        lo, _, m, t = cands[0]
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
        self.c.events.drain()
        self.c.call("useskill animal taming", timeout=6)
        if self.c.wait_for(Event.TARGET_REQUEST, timeout=4) is None:
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
                if re.search(r"accept you as|master|tame|fail|too far|cannot|must wait|already|stable|follower|control", l, re.I):
                    result = l
            if re.search(r"accept you|fail|cannot|already|too far|no chance|stops", result, re.I):
                break
        self.log(f"tame {m.name} (min {lo}, skill {self.skill():.1f}): {result[:100]}")
        gained = any(re.search(r"skill in animal taming has increased", l, re.I) for l in list(self.journal)[-12:])
        self.mem.record("res", kind="tamegain", key=norm(m.name), ok=gained)
        self.mem.record("res", kind="tame", key=norm(m.name), ok=bool(re.search(r"accept you", result, re.I)), reason=result[:60])
        if re.search(r"accept you", result, re.I):
            self.work += 1
            self.tamed += 1
            if not self.feature("tame_find"):
                self.ev("tame", m=m.name)
            self.note("tame", f"A successful tame says: {result[:100]}", key="tamemsg")
            self.after_tame(m)
        else:
            self.failed += 1
            unseen = re.search(r"cannot be seen|too far", result, re.I)
            self.ignored[m.serial] = time.time() + (300 if unseen else 60)
            self.note("tame", f"A failed or refused tame says: {result[:100] or 'nothing'}", key=f"tamefail:{result[:30]}")
        self.refresh_skills()
        return True

    TAME_RANGE = 2                                            # AnimalTaming's target range before AOS

    def tame_in_range(self, m):
        """The animal's position now (the world file), within taming range of this character; False when it moved away or left view."""
        cur = next((x for x in self.c.mobiles(within=8) if x.serial == m.serial), None)
        if cur is None:
            return False
        return max(abs(cur.x - self.c.x), abs(cur.y - self.c.y)) <= self.TAME_RANGE

    @staticmethod
    def pet_strength(name):
        t = TAME.get(norm(name)) or {}
        dmg = t.get("dmg") or [0, 0]
        return (t.get("hits") or 0) * (dmg[0] + dmg[1]) / 2.0

    def release(self, name, count=1):
        """Release a pet by speech ("<name> release", or "all release"). The server answers with a window asking to confirm
        (ConfirmReleaseGump): Okay is button 2. Unanswered, nothing is released, which is what every "all release" did until now."""
        self.c.events.drain()
        self.c.say(f"{name} release")
        time.sleep(1.5)
        # one confirm window per pet named; answer each by its serial (with several windows open, gumpresponse will not guess)
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
        for g in serials[:max(count, 1) + 2]:
            try:
                self.c.call(f"gumpresponse 2 gump:{g}", timeout=5)
            except Exception:
                pass
            time.sleep(0.8)
        self.note("pet", "Releasing a pet by speech opens a window asking to confirm; the pet is released only when Okay is pressed.", key="releaseconfirm")

    def r_pet(self):
        """Keep the kept pet close: every couple of minutes, if it is in sight, "all guard me"; if it has not been seen for ten minutes (it died,
        or wandered off after its master died), it is gone."""
        pet = self.facts.get("pet")
        if not pet or self.c.ghost:
            return False
        now = time.time()
        seen = any(m.serial == pet["serial"] for m in self.c.mobiles(within=18))
        if seen:
            pet["seen"] = now
        elif now - pet.get("seen", pet["since"]) > 600:
            self.facts.pop("pet")
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
        self.c.events.drain()
        self.c.call("useskill animal lore", timeout=6)
        if self.c.wait_for(Event.TARGET_REQUEST, timeout=4) is not None:
            self.c.target(m.serial)
            time.sleep(3)
            for l in self.read_journal()[-4:]:
                self.note("tame", f"Animal Lore on a pet answers: {l[:100]}", key="loremsg")
            self.c.call("gumps", timeout=6)
        pet = self.facts.get("pet")
        strength = self.pet_strength(m.name)
        keep = strength >= self.PET_MIN and (pet is None or strength > pet["strength"] * self.PET_UPGRADE)
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
        if pet and pet["name"].lower() == m.name.lower():
            # same name as the kept pet: speech cannot tell them apart, so the pet is let go with it and the next good tame is kept instead
            self.release("all", count=2)
            self.facts.pop("pet", None)
        else:
            self.release(m.name)
        for l in self.read_journal():
            self.note("tame", f"Releasing a pet answers: {l[:100]}", key="releasemsg")

    def r_explore(self):
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
