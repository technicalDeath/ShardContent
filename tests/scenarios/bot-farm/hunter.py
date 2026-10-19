"""Melee fighters and archers (Mace Fighter, Fencer, Swordsman, Archer, Ranger, Bard): the bot walks the countryside around Britain, fights what the
server's own numbers say it can beat, loots, heals with bandages, buys what it ran out of and goes to the bank when it is rich.

    python hunter.py --name BotMaceA --profession 13 --for 3600

What it knows comes from knowledge.py (the shard's monster table: hit points, damage, armor). What it learns on the way is kept in
work/botfarm/<name>/knowledge.json: the places and the kinds of monster that killed it, so it does not go back to them.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import random
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from bot_common import ROOT, TOWN, BotBase  # noqa: E402
from memory import cell_center, cell_of, choose_spot  # noqa: E402
from first_trip import FirstTrip  # noqa: E402
from places import SEED_SPOTS  # noqa: E402
import danger  # noqa: E402
import goals  # noqa: E402
import townguard  # noqa: E402

sys.path.insert(0, os.path.join(HERE, "..", "new-mage-playtest"))
from knowledge import Knowledge, norm  # noqa: E402

SPOTS = SEED_SPOTS["Britain"]           # an alias for importers: the brains ask Places.patrol_spots() for their home's
SAFE_NAMES = ("rat", "cat", "magpie", "crow", "rabbit", "hind", "sheep", "chicken", "pig", "goat", "cow", "gull", "bird", "dog", "lizard", "toad", "frog", "squirrel", "snake", "eagle", "mongbat", "gorilla", "slime", "bull", "swallow", "sparrow", "pigeon", "finch", "owl", "raven", "parrot", "turkey", "duck", "ostrich", "llama", "walrus", "panther", "jackrabbit", "bunny", "mouse", "mud")
def safe_name(name):
    n = name.lower()
    return "greater" not in n and any(re.search(rf"\b{w}\b", n) for w in SAFE_NAMES)


DANGEROUS_WORDS = ("bear", "wolf", "cougar", "panther", "snake", "serpent", "spider", "scorpion", "orc", "troll", "ogre", "lizardman", "ettin", "skeleton", "zombie", "ghoul", "wraith",
                   "spectre", "shade", "gazer", "harpy", "imp", "daemon", "drake", "dragon", "wyrm", "elemental", "lich", "mummy", "reaper", "golem", "giant", "alligator", "bull", "boar",
                   "leopard", "lion", "tiger", "ratman", "bone", "mage", "executioner", "brigand", "rogue")
SWING_SECONDS = 2.0
ENGAGED = 0.7
ARMOR_CUT = {"Mace Fighter": 0.3, "Fencer": 0.3, "Swordsman": 0.3, "Archer": 0.15, "Ranger": 0.15, "Bard": 0.15, "Warlock": 0.05}
ARCHERS = ("Archer", "Ranger", "Bard")
FACILITIES = {"melee": "dummy", "ranged": "butte"}          # the fixture to try, by role: places.spots_for finds the nearest ones


from market import FighterMarket  # noqa: E402
from weaponup import WeaponMixin  # noqa: E402


from stock import FighterStock  # noqa: E402
from livelihood import LivelihoodMixin  # noqa: E402
class HunterBot(LivelihoodMixin, FighterStock, WeaponMixin, FighterMarket, FirstTrip, BotBase):
    RULES = ["r_dead", "r_corpse", "r_gear", "r_cure", "r_flee", "r_avoid", "r_sewer_out", "r_heal", "r_loot", "r_fight", "r_lighten", "r_fletch", "r_wood", "r_resupply", "r_upgrade", "r_bank", "r_facility", "r_hunt",
             "r_rest", "r_camp", "r_sewer_in", "r_explore"]
    LOOT_MATERIALS = False
    REST_BELOW = 65

    def r_lighten(self):
        """A fighter over three quarters of its weight with crafting material in the pack (hides from the cows it killed, mostly) leaves the heaviest of
        it on the ground: no Britain shop buys hides, and weight slows it, drains its stamina and finally stops it."""
        if self.c.weight < self.c.max_weight * 0.75 or self.mobs(6) or time.time() < self.facts.get("drop_refused_until", 0):
            return False                                  # drops refused a moment ago (overloaded): r_bank takes it from here
        # an archer with Bowcraft starts with boards for its own shafts and arrows (the starter kit fills 85% of the weight limit): keep them
        fletcher = self.skill_values.get("Bowcraft/Fletching", 0) >= 25
        mats = sorted((i for i in self.c.backpack if any(w in i.name.lower() for w in self.MATERIALS)
                       and not (fletcher and any(w in i.name.lower() for w in ("board", "feather", "shaft")))),
                      key=lambda i: next(k for k, w in enumerate(self.MATERIALS) if w in i.name.lower()))
        mats += [i for i in self.c.backpack if i.name.lower() == "arrow fletching"][1:]
        if not mats:
            return False
        self.activity = "dropping dead weight"
        refused = 0
        for it in mats[:3]:
            self.c.call(f"dropground {it.serial} {it.amount or 1}", timeout=8)
            time.sleep(1.2)
            if any(i.serial == it.serial for i in self.c.backpack):
                refused += 1
                continue
            self.log(f"left {it.amount or 1} {it.name} on the ground (weight {self.c.weight}/{self.c.max_weight})")
        if refused == len(mats[:3]):
            self.facts["drop_refused_until"] = time.time() + 600
            self.facts["bank_heavy"] = True
            self.log(f"the ground refused every drop (weight {self.c.weight}/{self.c.max_weight}): off to the bank")
            return False
        carried = sorted({it.name for it in mats[:3]})
        self.note("weight", f"A {self.pname} reached {self.c.weight}/{self.c.max_weight} stones carrying crafting material it does not use ({', '.join(carried)}); "
                            "nothing tells a new fighter which loot is worth carrying.", key=f"deadweight:{','.join(carried)}")
        return True

    def __init__(self, name, profession):
        super().__init__(name, profession)
        self.k = Knowledge(os.path.join(HERE, "..", "new-mage-playtest", "game_data.json"))
        self.ranged = self.pname in ARCHERS
        self.spots = list(self.patrol_spots())
        random.Random(name).shuffle(self.spots)
        self.avoid_types = set()
        try:
            known = json.load(open(self.know_path, encoding="utf-8"))
            self.avoid_types = set(known.get("avoid_types", []))
            self.facts["facility_done"] = bool(known.get("facility_done"))      # tried once in this character's life is enough
        except (OSError, ValueError):
            pass
        self.recent_threats = []
        self.fight = None
        self.cur_spot = None
        self.spot_since = 0.0
        self.target = None
        self.target_since = 0.0
        self.target_hp = 0
        self.ignored = {}
        self.pose = {}

    # ---- knowledge --------------------------------------------------------------------------------------------

    def save_knowledge(self):
        json.dump({"death_spots": self.death_spots, "avoid_types": sorted(self.avoid_types), "facility_done": bool(self.facts.get("facility_done"))},
                  open(self.know_path, "w", encoding="utf-8"))

    def my_dps(self):
        skill = max([v for k, v in self.skill_values.items() if k in ("Archery", "Maces", "Mace Fighting", "Fencing", "Swordsmanship", "Wrestling")] or [50.0])
        measured = self.mem.measured_dps()
        if measured:
            return max(0.8, measured)               # what bots of this profession have actually dealt, from their own kills
        return (2.0 if self.ranged else 2.6) + 0.03 * (skill - 50)

    NEWBIE_HARMLESS = ("rat", "rabbit", "bird", "cat", "dog", "chicken", "cow", "sheep", "pig", "goat", "hind", "deer", "crow", "magpie", "sparrow", "toad", "frog")

    def _assess_naive(self, m):
        """What a new player goes by: the name, and what has happened to newbies before. Anything called 'a something' is worth a try until it kills one."""
        n = m.name.lower()
        key = self.mkey(m)
        if key in self.avoid_types:
            return {"known": False, "fight": False, "reason": "newbie: it killed me before"}
        if any(w in n for w in self.NEWBIE_HARMLESS):
            return {"known": False, "fight": True, "reason": "newbie: looks harmless"}
        return {"known": False, "fight": n.startswith(("a ", "an ")), "reason": "newbie: never met one, worth a try" if n.startswith(("a ", "an ")) else "newbie: a person, leave it"}

    def _assess_table(self, m):
        if self.mode == "newbie":
            return self._assess_naive(m)
        mon = self.k.monster(m)
        if mon is None:
            n = m.name.lower()
            ok = n.startswith(("a ", "an ")) and not any(w in n for w in DANGEROUS_WORDS) and norm(m.name) not in self.avoid_types
            return {"known": False, "fight": ok, "reason": "not in the monster table, " + ("an animal by its name" if ok else "dangerous by its name or by experience")}
        if norm(mon.get("class") or mon.get("name") or "") in self.avoid_types:
            return {"known": True, "fight": False, "reason": "it has killed this bot before", "monster": mon}
        hits = (mon["hits"][0] + mon["hits"][1]) / 2.0
        ttk = hits / self.my_dps()
        swing = (mon["damage"][0] + mon["damage"][1]) / 2.0
        engaged = 0.35 if self.ranged else ENGAGED
        taken = ttk / SWING_SECONDS * swing * engaged * (1 - ARMOR_CUT.get(self.pname, 0.1))
        casts = mon.get("casts")
        fight = taken < 0.5 * self.c.hp and not casts and mon["hits"][1] <= 140
        return {"known": True, "fight": fight, "monster": mon, "taken": round(taken), "reason": f"~{ttk:.0f}s to kill, ~{taken:.0f} damage taken of {self.c.hp}" + (", casts spells" if casts else "")}

    def assess(self, m):
        """The table's estimate, corrected by what bots like this one have actually met: a kind that has killed them is a danger, a kind they beat cheaply is prey."""
        a = self._assess_table(m)
        b = self._assess_memory(m, a)
        if b["fight"] != a["fight"]:
            logged = self.facts.setdefault("mem_logged", {})
            key = self.mkey(m)
            if time.time() - logged.get(key, 0) > 300:
                logged[key] = time.time()
                self.dlog("mem", m=key, table=a["fight"], final=b["fight"], why=b["reason"][:120])
        return b

    def _assess_memory(self, m, a):
        key = self.mkey(m)
        deadly = self.mem.deadly_kinds()
        stats, src = self.mem.fight_stats(key)
        casts = bool((a.get("monster") or {}).get("casts"))
        if key in deadly:
            return dict(a, fight=False, reason=f"memory: killed {deadly[key]} bots like this one")
        if stats:
            if stats["death_rate"] >= 0.25 or stats["flee_rate"] >= 0.5:
                return dict(a, fight=False, reason=f"memory ({src}): {stats['n']} fights, {stats['death_rate']:.0%} deaths, {stats['flee_rate']:.0%} fled")
            if stats["death"] == 0 and stats["flee_rate"] < 0.2 and stats["avg_dmgpct"] <= 0.45 and not casts:
                return dict(a, fight=True, reason=f"memory ({src}): {stats['n']} fights, lost {stats['avg_dmgpct']:.0%} of hit points on average, none died")
        return a

    def begin_fight(self, t):
        f = self.fight
        if f and f["serial"] == t.serial:
            return
        if f:
            self.end_fight("kill" if self.target_died(f) else "lost")
        mon = self.k.monster(t)
        self.fight = {"serial": t.serial, "key": self.mkey(t), "t0": time.time(), "hp0": self.c.hp, "hpmin": self.c.hp, "kills0": self.kills,
                      "mhits": (sum(mon["hits"]) / 2.0) if mon else 0, "cell": cell_of(t.x, t.y), "xy": (t.x, t.y), "pct": 100,
                      "near": sum(1 for o in self.mobs(14) if o.serial != t.serial and max(abs(o.x - t.x), abs(o.y - t.y)) <= 10),
                      "corpses0": {c.serial for c in self.c.containers(within=14)}}

    def target_died(self, f):
        """The fight's own target died, not just any corpse in view: a new corpse where the target last stood, or the target gone when last seen badly hurt."""
        x, y = f.get("xy", (None, None))
        for c in self.c.containers(within=16):
            if "corpse" in c.name.lower() and c.serial not in f.get("corpses0", set()) and x is not None and abs(c.x - x) <= 2 and abs(c.y - y) <= 2:
                return True
        return f.get("pct", 100) <= 25

    def end_fight(self, outcome):
        f, self.fight = self.fight, None
        if not f:
            return
        if outcome == "kill":
            self.kills += 1
            self.note_kill_at(*(f.get("xy") or (self.c.x, self.c.y)), kind=f["key"])
        ttk = time.time() - f["t0"]
        if (ttk < 0.3 or outcome == "lost" and ttk < 3) and outcome != "death":
            return
        for scope in ("world", "prof"):
            self.mem.record("fight", scope=scope, m=f["key"], grp=self.mem.grp, outcome=outcome, ttk=round(ttk, 1), dmg=max(0, f["hp0"] - f["hpmin"]), hp=self.c.max_hp, cell=f["cell"], mhits=f["mhits"],
                            skill=round(self.skill_values.get(self.main_skill(), 0), 1), near=f.get("near"))

    def on_flee(self):
        self.end_fight("flee")

    # kinds that spawn in groups and beat the bots in run 1 and 2b fights (work/botfarm-watch/creature-danger.md): one at a time at 50+, never a pack
    def danger_ok(self, m):
        """Feature danger_model: is this kind acceptable prey for this skill band and the pack around it, by what fights have shown (danger.py)?"""
        cache = self.facts.setdefault("danger_cache", {})
        hit = cache.get(m.serial)
        if hit and time.time() - hit[0] < 4:
            return hit[1]
        near = sum(1 for o in self.mobs(14) if o.serial != m.serial and max(abs(o.x - m.x), abs(o.y - m.y)) <= 10)
        near = max(0, near - self.party_help())                  # a party's members at hand take their share of the pack
        skill = self.skill_values.get(self.main_skill(), 0)
        r = danger.risk(self.mem, self.mkey(m), skill, near)
        ok = danger.acceptable(r, "prey")
        cache[m.serial] = (time.time(), ok)
        if len(cache) > 200:
            cache.clear()
        if not ok:
            logged = self.facts.setdefault("danger_logged", {})
            key = f"{self.mkey(m)}|{danger.sband(skill)}|{danger.nband(near)}"
            if time.time() - logged.get(key, 0) > 300:
                logged[key] = time.time()
                self.dlog("choice", what=f"avoid {self.mkey(m)}", why=f"danger model: die {r['die']:.0%}, flee {r['flee']:.0%}, win {r['win']:.0%} "
                          f"(n {r['n']:.0f}/{r['n_kind']:.0f}, {r['src']}, pack {near}, skill {skill:.0f})")
        return ok

    TIER2_GROUP = ("orc", "ratman", "shade", "wraith", "spectre", "lizardman", "harpy")
    TIER2_SKILL = 50

    def is_prey(self, m):
        if self.sewer_avoid(m):
            return False                                       # the sewers: an alligator below skill 50 is a danger
        if self.feature("danger_model") and m.distance > 1 and not self.danger_ok(m):
            return False                                       # learned risk for this skill band and pack (danger.py)
        if not self.feature("danger_model") and m.distance > 1 and self.mkey(m) in self.TIER2_GROUP:
            # the owner beat most of them easily at 55 archery: the danger is the pack, so one alone is prey at 50+, one with company is not
            company = [o for o in self.mobs(14) if o.serial != m.serial and max(abs(o.x - m.x), abs(o.y - m.y)) <= 10]
            if company or self.skill_values.get(self.main_skill(), 0) < self.TIER2_SKILL:
                return False
        a = self.facts.setdefault("assess", {})
        cached = a.get(m.serial)
        if cached and time.time() - cached[0] < 8:
            return cached[1]
        r = self.assess(m)["fight"]
        a[m.serial] = (time.time(), r)
        seen = self.facts.setdefault("sightings", set())
        if m.name not in seen:
            seen.add(m.name)
            self.log(f"first sight of {m.name!r} ({m.notoriety}): {'prey' if r else 'DANGER'} - {self.assess(m)['reason']}")
        return r

    def safe_ground(self, m):
        cell = cell_of(m.x, m.y)
        return not (self.mem.dangerous_cell(cell) or self.camp_for_me(cell))

    # what a fight is worth, per minute: weapon-skill gains, secondary gains (less as those skills pass 50), gold (more while short), less risk
    W_MAIN, W_SEC, W_GOLD, W_GOLD_SHORT, W_RISK = 1.0, 0.3, 0.05, 0.15, 8.0
    WORTH_FLOOR = 1.5          # below this a known kind is not worth a fight (cats are a chase, birds give nothing)
    WORTH_UNKNOWN = 6.0        # a kind not yet measured is worth trying (the Britain step-ups: orcs, ratmen, lizardmen)
    WEAPON_SKILLS = ("Archery", "Swordsmanship", "Mace Fighting", "Fencing", "Wrestling")

    def kill_worth_ok(self, kind):
        """Is a kind worth camping for: not a cat or a bird, and (once measured) worth 3 or more a minute to this bot."""
        if kind in ("cat", "bird", "magpie", "crow", "raven", "sparrow", "pigeon", "chicken"):
            return False
        w = self.mem.prey_worth(kind, self.main_skill())
        if not w:
            return True
        secs = [self.skill_values.get(k, 0) for k in ("Tactics", "Anatomy")]
        sec_w = self.W_SEC * min(1.0, max(0.1, (80 - sum(secs) / len(secs)) / 30))
        return self.W_MAIN * w["main"] + sec_w * w["sec"] + self.W_GOLD * w["gold"] / max(0.05, w["min_per_kill"]) - self.W_RISK * w["dmgpct"] >= 3

    def main_skill(self):
        return max(self.WEAPON_SKILLS, key=lambda k: self.skill_values.get(k, 0))

    def worth(self, m):
        """What fighting this kind is worth per minute to this bot, from what its profession has measured; None until five fights are known."""
        w = self.mem.prey_worth(self.mkey(m), self.main_skill())
        if not w:
            return None
        secs = [self.skill_values.get(k, 0) for k in ("Tactics", "Anatomy")]
        sec_w = self.W_SEC * min(1.0, max(0.1, (80 - sum(secs) / len(secs)) / 30))
        short = self.c.gold < 200 or (self.ranged and self.ammo() < 40) or self.bandages() < 10
        gold = (self.W_GOLD_SHORT if short else self.W_GOLD) * w["gold"] / max(0.05, w["min_per_kill"])
        return self.W_MAIN * w["main"] + sec_w * w["sec"] + gold - self.W_RISK * w["dmgpct"]

    def prey(self, within=9):
        others = self.other_bots(within + 4)
        mine = getattr(self, "target", None)
        ps = [m for m in self.mobs(within) if self.is_prey(m) and self.ignored.get(m.serial, 0) < time.time()
              and (m.distance <= 2 or self.safe_ground(m)) and not self.taken_by_other(m, others, mine) and not self.critter_skip(m)]
        scored = []
        for m in ps:
            w = self.worth(m)
            if w is not None and w < self.WORTH_FLOOR and m.distance > 1:
                skipped = self.facts.setdefault("skipped_kinds", set())
                if self.mkey(m) not in skipped:
                    skipped.add(self.mkey(m))
                    self.dlog("choice", what=f"skip {self.mkey(m)}", why=f"worth {w:.1f} per minute, under {self.WORTH_FLOOR}")
                continue                                   # still fought when it is on top of us (distance 1)
            stick = 3.0 if m.serial == getattr(self, "target", None) else 1.0
            scored.append((-(w if w is not None else self.WORTH_UNKNOWN) * stick / (1 + m.distance / 6.0), m.distance, m))
        return townguard.filter_prey(self, [m for _, _, m in sorted(scored, key=lambda s: (s[0], s[1]))])       # inside a guarded region the guards take the monsters (feature town_guards)

    def dangers(self, within=8):
        now = time.time()
        return [m for m in self.mobs(within) if not self.is_prey(m) and self.ignored.get(m.serial, 0) < now]     # an unreachable one is left out (patch_cornered_stuck.py)

    # ---- equipment --------------------------------------------------------------------------------------------

    def ammo(self):
        return sum((i.amount or 1) for i in self.c.backpack if i.name.lower() in ("arrow", "bolt"))

    def bandages(self):
        return sum((i.amount or 1) for i in self.c.backpack if "bandage" in i.name.lower())

    # ---- rules -----------------------------------------------------------------------------------------------

    def observe(self):
        super().observe()
        th = []
        for m in self.mobs(10):
            mon = self.k.monster(m)
            avg = (sum(mon["damage"]) / 2) if mon else 0
            th.append((m.distance, m.name, norm((mon or {}).get("class") or m.name), avg))
        if th:
            self.recent_threats = sorted(th)
        if self.facts.get("anchor") and any(self.kill_worth_ok(self.mkey(m)) for m in self.prey(14)):
            self.anchor_seen()
        if self.c.overloaded:
            self.note("weight", f"A {self.pname} is overloaded ({self.c.weight}/{self.c.max_weight}) and cannot move at full pace.", key="overload")
        f = self.fight
        if f:
            f["hpmin"] = min(f["hpmin"], self.c.hp)
            target = next((m for m in self.c.mobiles(within=16) if m.serial == f["serial"]), None)
            if target and not target.is_dead:
                f["xy"] = (target.x, target.y)
                if target.max_hits:
                    f["pct"] = target.hp_pct
            else:
                self.end_fight("kill" if self.target_died(f) else "lost")
            if self.fight is f and time.time() - f["t0"] > 90:
                self.end_fight("lost")

    def r_dead(self):
        was = self.facts["ghost_since"]
        if self.c.ghost and was is None:
            if self.fight:
                self.end_fight("death")
            elif self.recent_threats:
                self.mem.record("fight", scope="world", m=self.recent_threats[0][2], grp=self.mem.grp, outcome="death", ttk=0, dmg=self.c.max_hp, hp=self.c.max_hp, cell=cell_of(self.c.x, self.c.y))
        if self.c.ghost and was is None:
            self.facts.pop("anchor", None)                # a camp that killed us is no camp
        r = super().r_dead()
        if r and was is None:
            threats = [t for t in self.recent_threats if not safe_name(t[1])] or self.recent_threats
            for i, (dist, name, key, avg) in enumerate(threats):
                # the nearest threat at death is the killer, named or not ("Tekchichak" is a ratman); a newbie has no damage table to blame others by
                killer = i == 0 and dist <= 6
                if killer or (name.lower().startswith(("a ", "an ")) and (dist <= 4 or (avg >= 10 and self.mode != "newbie"))):
                    self.avoid_types.add(key)
            self.save_knowledge()
            self.log(f"learned: avoid {sorted(self.avoid_types)} (threats were {self.recent_threats[:3]})")
        return r

    def r_avoid(self):
        ds = self.dangers(7)
        if not ds:
            return False
        d = ds[0]
        self.facts["avoided_until"] = time.time() + 45      # a commitment: once it runs, it does not turn back to hunt for a while
        a = self.assess(d)
        hopeless = bool((a.get("monster") or {}).get("casts")) or a.get("taken", 0) > 0.6 * max(1, self.c.hp)
        hopeless = hopeless or self.mkey(d) in self.avoid_types or self.near_death_spot(self.c.x, self.c.y, 15)
        if hopeless and d.distance <= 6:
            # learned from a Mace Fighter killed by a wraith while "cornered": against a caster or something that out-damages us, standing to fight is death;
            # run for the town guards at once, before the health is gone
            self.activity = f"running from {d.name}"
            self.end_fight("flee")
            self.dlog("choice", what="run to town", why=f"{d.name}: {a.get('reason', '')}"[:120])
            self.sprint()
            self.call_guards(d)
            self.c.goto(*self.flee_point(d)).wait(timeout=6)
            return True
        if d.distance <= 3 and self.hp_pct() > 40:
            cn = self.facts.get("cornered")
            now = time.time()
            if not cn or cn.get("serial") != d.serial:
                cn = self.facts["cornered"] = {"serial": d.serial, "since": now, "its": d.hits, "mine": self.c.hp}
            elif now - cn["since"] > 30 and (d.hits or 0) >= (cn["its"] or 0) and self.c.hp >= cn["mine"]:
                self.ignored[d.serial] = now + 180                 # 30 s with no hit either way: it cannot reach us, nor we it (an alligator in the water)
                self.facts.pop("cornered", None)
                self.end_fight("lost")
                self.log(f"{d.name} cornered us for 30 s but neither side was hurt: ignoring it for 3 minutes")
                self.dlog("choice", what=f"ignore {self.mkey(d)}", why="cornered 30 s, no hit either way (unreachable)")
                self.step_away(d, 8)
                return True
            if not self.c.war_mode:
                self.c.war(True)
            self.c.attack(d.serial)
            self.activity = f"cornered by {d.name}"
            self.note("combat", f"A {d.name} caught up with a new {self.pname} at {self.c.x},{self.c.y} ({'inside Britain' if 1420 <= self.c.x <= 1650 and 1540 <= self.c.y <= 1720 else 'in the wilds'}): it cannot be outrun and the player must fight it with starting gear.", key=f"followed:{d.name}")
            time.sleep(1.2)
            return True
        self.activity = f"avoiding {d.name}"
        if self.k.monster(d) is not None:
            self.note("danger", f"Hostile {d.name!r} within {d.distance} tiles of a new {self.pname}: nothing warns the player.", key=f"danger:{d.name}")
        self.step_away(d, 8)
        return True

    def r_heal(self):
        threats = self.mobs(3)
        pct = self.hp_pct()
        want = 55 if threats else 85
        if pct >= want:
            return False
        healing = self.skill_values.get("Healing", 0)
        if self.c.poisoned and healing < 60:
            return False                      # r_cure handles poison; a bandage only cures from Healing 60
        if pct < 45 and (healing < 30 or threats) and time.time() - self.facts.get("drank", 0) > 12:
            pot = next((i for i in self.c.backpack if i.name == "Yellow Potion"), None)
            if pot:
                self.facts["drank"] = time.time()
                before = self.c.hp
                self.c.use(pot.serial)
                time.sleep(2)
                self.log(f"drank a Yellow Potion at {before}/{self.c.max_hp}: now {self.c.hp}")
                self.ev("consumable_used", item="yellow potion", hp=self.hp_pct())
                self.note("potions", f"The Yellow Potion (the only way to tell the Heal potion is its color) raised hit points {before} -> {self.c.hp}.", key="yellow")
                return True
        if self.bandages() == 0 or threats and pct >= 30:
            return False
        self.activity = "bandaging"
        self.bandage_self_force()
        return True

    def bandage_self_force(self):
        b = self.c.find("bandage")
        if not b:
            return False
        self.c.events.drain()
        before = self.c.hp
        self.c.use_on(b.serial, "self")
        from uo import Event
        deadline = time.time() + 20
        text = ""
        while time.time() < deadline:
            time.sleep(1.0)
            for l in self.read_journal():
                if re.search(r"bandage|heal", l, re.I):
                    text = l
            if re.search(r"barely help|finish applying|apply the bandages|you heal|cannot|not injured|interrupt", text, re.I):
                break
        healing = self.skill_values.get("Healing", 0)
        self.log(f"bandage at {before}/{self.c.max_hp} (Healing {healing:.1f}): {text[:70] or 'no answer'} -> {self.c.hp}")
        if "barely help" in text:
            self.note("healing", f"A bandage applied with Healing {healing:.0f} takes about 14 seconds and heals about 1 hit point ('{text[-48:]}'); the 50 starting bandages are a Healing trainer, not a healer, and the message does not say why.", key="barely")
        return True

    def flee_below(self):
        """Losing (below half health while the target has clearly more of its own left): run at 50%, while there is health to run with.
        At 40% the bots that fled from ettins, ogres and trolls were caught at hp 0-15."""
        f = self.fight
        return 50 if f and f.get("pct", 100) > self.hp_pct() + 20 else 40

    def step_away(self, m, dist=3):
        self.sprint()
        dx = self.c.x - m.x
        dy = self.c.y - m.y
        self.c.goto(self.c.x + (dist if dx >= 0 else -dist), self.c.y + (dist if dy >= 0 else -dist)).wait(timeout=3)

    def r_fight(self):
        if self.hp_pct() < 45:
            return False
        ps = self.prey(9)
        if not ps:
            self.target = None
            return False
        if self.ranged and self.ammo() == 0:
            self.note("combat", f"The {self.pname} ran out of ammunition mid-hunt; nothing warns the player before the last arrow.", key="noammo")
            return False
        t = ps[0]
        if not self.c.war_mode:
            self.c.war(True)
        if t.serial != self.target:
            self.target, self.target_since, self.target_hp = t.serial, time.time(), t.hits
        elif time.time() - self.target_since > 40 and t.hits >= self.target_hp:
            self.ignored[t.serial] = time.time() + 90
            self.log(f"gave up on {t.name} (no progress in 40 s)")
            self.note("combat", f"A {t.name} could not be reached or hurt for 40 s; the bot gave up.", key=f"unreachable:{t.name}")
            self.target = None
            return True
        self.activity = f"fighting {t.name}"
        self.begin_fight(t)
        if self.ranged and t.distance > 1 and not self.los(t.serial):
            blocked = self.facts.setdefault("nolos", {})
            blocked[t.serial] = blocked.get(t.serial, 0) + 1
            if blocked[t.serial] == 1:
                self.note("combat", "An archer cannot shoot a monster behind a wall and nothing says so; it has to walk round until it can see it.", key="nolos")
            if blocked[t.serial] > 6:
                self.ignored[t.serial] = time.time() + 120
            self.c.goto(t.x, t.y).wait(timeout=3)
            return True
        if self.ranged:
            if t.distance <= 1:
                self.step_away(t, 4)
                return True
            if t.distance > 8:
                self.c.goto(t.x, t.y).wait(timeout=2)
                return True
        else:
            if t.distance > 1:
                self.c.goto(t.x, t.y).wait(timeout=2)
                return True
        self.c.attack(t.serial)
        time.sleep(1.4)
        return True

    LOOT_GEAR = ("bow", "crossbow", "mace", "club", "kryss", "katana", "sword", "cutlass", "scimitar", "axe", "spear", "fork", "hammer", "maul", "staff",
                 "dagger", "knife", "shield", "helm", "coif", "tunic", "leggings", "sleeves", "gloves", "gorget", "arms", "chainmail", "ringmail", "platemail",
                 "studded", "boots")
    @property
    def GEAR_SHOPS(self):                                # the Blacksmith (armour and weapons), the Weaponsmith / Armorer, the Cobbler (boots)
        return self.find_places(("smith", "weaponsmith", "armorer", "cobbler"), n=4, per=1)
    CARVE = True
    CARVE_KINDS = ("cow", "bull", "deer", "hart", "hind", "sheep", "goat", "chicken", "pig", "boar", "rabbit", "bear", "bird")
    BLADES = ("sword", "kryss", "katana", "cutlass", "scimitar", "dagger", "knife", "axe", "cleaver")
    @property
    def BUTCHER(self):
        return self.where1(("butcher",))
    KEEP = BotBase.KEEP + ("raw ",)                 # meat waits for the Butcher, not the bank box

    def carving_blade(self):
        """Something to carve with: the blade in hand (a sword, a kryss, an axe), else a dagger, knife or cleaver in the pack."""
        return next((i for i in self.c.equipped if any(b in i.name.lower() for b in self.BLADES)), None) or \
            next((i for i in self.c.backpack if any(b in i.name.lower() for b in ("dagger", "knife", "cleaver"))), None)

    def sale_due(self, key):
        """Twenty minutes since the last sale of this kind, or, for a bot that never sold, twenty minutes played in all (the totals' uptime plus
        this brain): counting from the brain's start reset the timer at every restart and no fighter ever reached it."""
        last = self.facts.get(key)
        if last:
            return time.time() - last > 1200
        return self.base.get("uptime", 0) + time.time() - self.started > 1200

    def r_sellmeat(self):
        """Carved meat to the Butcher: a dozen pieces, or when heavy, or when down to the last 60 gold."""
        meat = [i for i in self.c.backpack if i.name.lower().startswith("raw ")]
        if not meat or self.mobs(10) or time.time() - self.facts.get("meat_sold_at", 0) < 300:
            return False
        n = sum((i.amount or 1) for i in meat)
        due = self.sale_due("meat_sold_at")             # twenty minutes out with meat in the pack: sell it
        if n < 6 and self.c.weight < self.c.max_weight * 0.7 and self.c.gold >= 60 and not due:
            return False
        self.facts["meat_sold_at"] = time.time()
        self.activity = "selling meat to the Butcher"
        gold0 = self.c.gold
        self.sell_items(self.BUTCHER, ("raw ",))
        earned = self.c.gold - gold0
        self.log(f"sold {n} pieces of meat for {earned} gold")
        self.dlog("choice", what="sell meat", why=f"{n} pieces for {earned} gold")
        self.note("loot", f"A {self.pname} carved its kills and sold {n} pieces of raw meat to the Butcher for {earned} gold.", key="meatsold")
        if earned <= 0:
            for it in meat:
                self.c.call(f"dropground {it.serial} {it.amount or 1}", timeout=8)
                time.sleep(1.0)
        return True

    TOWN_CORE = (1400, 1540, 1700, 1770)          # the city itself (its east side too, where town cats and dogs drew 40% of the first grounds)
    TOWN_PETS = ("cat", "dog", "bird", "magpie", "crow", "raven", "sparrow", "pigeon")
    HEAVY_CAMP = ("ettin", "troll", "ogre", "gazer", "gargoyle", "shade", "wraith", "spectre", "lich", "reaper", "harpy")

    def camp_for_me(self, cell):
        """A camp is a camp for this bot: four or more sightings there of kinds it avoids, that have killed bots like it, or that are too heavy
        for anyone near Britain. The shared camp test counted every orc, ratman, lizardman and zombie, so the new beginner spawn sites and the
        farms (with their step-up kinds) were all camps, and fighters left the prey there alone."""
        now = time.time()
        if now - self.facts.get("deadly_at", 0) > 60:
            self.facts["deadly"], self.facts["deadly_at"] = self.mem.deadly_kinds(), now
        deadly = self.facts["deadly"]
        c = self.mem.state["world"]["cells"].get(cell)
        if not c:
            return False
        heavy = self.HEAVY_CAMP
        if self.skill_values.get(self.main_skill(), 0) >= self.TIER2_SKILL:
            heavy = tuple(h for h in heavy if h not in self.TIER2_GROUP)          # step-up packs are its ground now; the danger map judges the pack (patch_camp_tiers.py)
        n = sum(v for k, v in c["sights"].items() if k in self.avoid_types or k in deadly or any(h in k for h in heavy))
        return n >= 4

    def worth_kind(self, k, deadly):
        """G12's worth of a kind seen on the map, for choosing ground: 0 for what has killed bots like this one or looks dangerous unmeasured."""
        if k in self.avoid_types or k in deadly:
            return 0.0
        w = self.mem.prey_worth(k, self.main_skill())
        if not w:
            return 0.0 if any(d in k for d in DANGEROUS_WORDS) else self.WORTH_UNKNOWN
        secs = [self.skill_values.get(s, 0) for s in ("Tactics", "Anatomy")]
        sec_w = self.W_SEC * min(1.0, max(0.1, (80 - sum(secs) / len(secs)) / 30))
        short = self.c.gold < 200
        return max(0.0, self.W_MAIN * w["main"] + sec_w * w["sec"] + (self.W_GOLD_SHORT if short else self.W_GOLD) * w["gold"] / max(0.05, w["min_per_kill"])
                   - self.W_RISK * w["dmgpct"])

    def best_ground(self, near=None):
        """The best hunting ground in range: the cell whose sighted kinds are worth most to this bot, plus its recent kills, less crowding and
        distance; never a camp or death cell, never the town core, never a ground reached in the last few patrols."""
        # around Britain, at least 220 tiles: a bot's own home range is centred on its last kills, often far from the farms and spawn sites
        center, radius = self.home_range()
        reach = 220 if self.mode == "newbie" else 320         # the owner: explore further out (veterans)
        hx, hy = self.home_centre()
        if max(abs(center[0] - hx), abs(center[1] - hy)) > 60 or radius < reach:
            center, radius = (hx, hy), max(radius, reach)
        core = self.home_core()
        self.mem.refresh()
        deadly = self.mem.deadly_kinds()
        recent = self.facts.get("spots_reached", [])[-3:]
        now = time.time()
        scored = []
        for cell, c in list(self.mem.state["world"]["cells"].items()):
            x, y = cell_center(cell)
            if max(abs(x - center[0]), abs(y - center[1])) > radius:
                continue
            if near and max(abs(x - self.c.x), abs(y - self.c.y)) > near:
                continue                                  # pushed off a crowded ground: the next one close by
            x0, y0 = (int(v) for v in cell.split(","))
            if x0 < core[2] and x0 + 40 > core[0] and y0 < core[3] and y0 + 40 > core[1]:
                continue                                  # any part of the city: its centre test let 1520,1760 through
            if any(abs(x - rx) < 20 and abs(y - ry) < 20 for rx, ry in recent):
                continue
            if self.mem.dangerous_cell(cell) or self.camp_for_me(cell) or self.near_death_spot(x, y, 40):
                continue
            if self.facts.get("crowded", {}).get(cell, 0) > now or self.ground_load(cell) > self.ground_cap(cell):
                continue                                  # three other bots on it already: the next ground
            prey = sum(min(n, 10) / 10.0 * self.worth_kind(k, deadly) for k, n in c["sights"].items() if k not in self.TOWN_PETS)
            self.mem._decay_cell(c, now)
            if prey <= 0 and c["kills"] < 0.5:
                continue
            score = prey + 3.0 * c["kills"] - 4.0 * self.mem.crowd(cell) - max(abs(x - self.c.x), abs(y - self.c.y)) / 40.0 + self.gr_bonus(cell)   # measured (ground_rates.py)
            scored.append((score, x, y, cell))
        if not scored:
            return None
        # any ground within 65% of the best: twenty fighters picking the single best cell all walk to the same farm
        top = max(s[0] for s in scored)
        if top <= 0:
            return None                                   # nothing worth going to: explore instead (a player goes further out)
        return random.choice([s for s in scored if s[0] >= 0.65 * top])

    def ground_load(self, cell):
        """Other bots on this ground: present in the last five minutes, or on their way (a ground claim, 300 s)."""
        now = time.time()
        c = self.mem.state["world"]["cells"].get(cell)
        mine = self.party_names() if self.feature("party") else set()                  # the party is one claim on a ground
        bots = {b for t, b in (c["pres"] if c else ()) if now - t < 300 and b != self.name and b not in mine}
        for key, r in self.mem.state["world"]["res"].get("ground", {}).items():
            if key.split("#")[0] == cell and r["claim_until"] > now and r["claim_by"] != self.name and r["claim_by"] not in mine:
                bots.add(r["claim_by"])
        return len(bots)

    def gear_loot(self):
        looted = self.facts.get("gear_looted", set())
        return [i for i in self.c.backpack if i.serial in looted]

    def r_sellgear(self):
        """Looted weapons and armour to the shops that buy them: with three pieces or more, when heavy, or when down to the last 60 gold.
        What no shop takes is left on the ground (it is only weight)."""
        gear = self.gear_loot()
        if not gear or self.mobs(10) or time.time() - self.facts.get("gear_sold_at", 0) < 300:
            return False
        due = self.sale_due("gear_sold_at")             # twenty minutes out with loot in the pack: sell it
        if len(gear) < 3 and self.c.weight < self.c.max_weight * 0.7 and self.c.gold >= 60 and not due:
            return False
        self.facts["gear_sold_at"] = time.time()
        self.activity = "selling looted gear"
        shops = []
        for n in sorted({i.name.lower() for i in gear}):
            for p, xy, item in self.mem.vendor_buying(n):
                pt = tuple(int(v) for v in xy.split(","))
                if item == n and p > 0 and pt not in shops:
                    shops.append(pt)
        shops += [xy for xy in self.GEAR_SHOPS if xy not in shops]
        gold0 = self.c.gold
        for xy in shops[:3]:
            left = self.gear_loot()
            if not left:
                break
            self.sell_items(xy, sorted({i.name.lower() for i in left}))
        earned = self.c.gold - gold0
        unsold = self.gear_loot()
        self.log(f"sold looted gear for {earned} gold; unsold {[i.name for i in unsold]}")
        self.dlog("choice", what="sell looted gear", why=f"{len(gear)} pieces for {earned} gold, {len(unsold)} unsold")
        self.note("loot", f"A {self.pname} sold weapons and armour looted from monsters for {earned} gold.", key="gearsold")
        for it in unsold:
            self.c.call(f"dropground {it.serial} {it.amount or 1}", timeout=8)
            time.sleep(1.0)
            self.facts["gear_looted"].discard(it.serial)
        return True

    # the era's armour (Items/Armor, pre-AOS values): per paperdoll layer, (shop name, armour value, strength needed, dexterity cost); the
    # slot's share of the body's armour rating; and the armour value of what is worn, read from its name
    SLOT_SHARE = {"Torso": 0.35, "Pants": 0.22, "Arms": 0.14, "Helmet": 0.14, "Gloves": 0.07, "Necklace": 0.07}
    ARMOR_BUY = {
        "Torso": [("ringmail tunic", 22, 20, -2), ("chainmail tunic", 28, 20, -5), ("platemail tunic", 40, 60, -8)],
        "Pants": [("ringmail leggings", 22, 20, -1), ("chainmail leggings", 28, 20, -3), ("platemail legs", 40, 60, -6)],
        "Arms": [("ringmail sleeves", 22, 20, -1), ("platemail arms", 40, 40, -2)],
        "Gloves": [("ringmail gloves", 22, 20, -1), ("platemail gloves", 40, 30, -2)],
        "Helmet": [("chainmail coif", 28, 20, 0), ("close helm", 30, 40, 0), ("plate helm", 40, 40, -1)],
        "Necklace": [("platemail gorget", 40, 30, -1)],
    }
    WORN_AR = (("plate", 40), ("chainmail", 28), ("ringmail", 22), ("helm", 30), ("bascinet", 30), ("bone", 30), ("studded", 16), ("leather", 13))
    UPGRADE_RESERVE = 250      # gold kept for arrows, bandages and potions after an upgrade

    def worn_ar(self, layer):
        it = next((i for i in self.c.equipped if i.layer == layer), None)
        if not it:
            return 0, None
        n = it.name.lower()
        return next((ar for w, ar in self.WORN_AR if w in n), 10), it

    def next_upgrade(self, money):
        """The best armour buy now: the most armour (weighted by how much of the body the slot covers) per gold, among the pieces this bot is
        strong enough to wear and can afford; an archer takes nothing that costs more than 2 dexterity (dexterity is its swing speed)."""
        strength = int(self.c.state.get("str") or 0)
        best = None
        for layer, options in self.ARMOR_BUY.items():
            cur, _ = self.worn_ar(layer)
            for name, ar, need, dex in options:
                if ar <= cur or need > strength or (self.ranged and dex < -2):
                    continue
                offers = [o for o in self.mem.vendor_selling(name) if o[2] == name]
                if not offers or offers[0][0] > money:
                    continue
                price, xy = offers[0][0], tuple(int(v) for v in offers[0][1].split(","))
                score = (ar - cur) * self.SLOT_SHARE[layer] / max(price, 1)
                if best is None or score > best[0]:
                    best = (score, layer, name, price, xy, cur, ar)
        return best

    def r_upgrade(self):
        """G2: once every ten minutes, with gold beyond the reserve (pack and bank), buy the best armour upgrade and wear it."""
        if self.mobs(10) or self.hp_pct() < 70 or time.time() - self.facts.get("upgrade_at", 0) < 600:
            return False
        self.facts["upgrade_at"] = time.time()
        money = self.c.gold + self.facts.get("bank_balance", 0) - self.UPGRADE_RESERVE
        best = goals.upgrade_choice(self, money) if goals.active(self) else self.next_upgrade(money)       # saving for a gear piece: only that piece
        if not best:
            return False
        _, layer, name, price, xy, cur, ar = best
        self.activity = f"buying a {name}"
        self.dlog("choice", what=f"upgrade {layer}: {name}", why=f"{price} gold for armour {cur} -> {ar}; money {money + self.UPGRADE_RESERVE}")
        offer = self.mem.best_offer(name, below=price, not_from=self.name)
        if offer:
            # a player sells it for less than the shop: book a deal; r_market meets the seller at the bank
            if self.c.gold < offer["price"] and self.facts.get("bank_balance", 0) > 0:
                self.visit_bank("trade", withdraw=offer["price"] + 60, reserve=0)
            if self.c.gold >= offer["price"]:
                did = f"{offer['bot']}-{self.name}-{int(time.time())}"
                self.mem.record("mkt", kind="deal", id=did, seller=offer["bot"], buyer=self.name, item=name, price=offer["price"])
                self.dlog("choice", what=f"buy {name} from {offer['bot']}", why=f"{offer['price']} gold against the shop's {price}")
                self.facts["upgrade_at"] = time.time() - 300         # look again in five minutes if the deal falls through
                return True
        if self.c.gold < price + 10 and self.facts.get("bank_balance", 0) > 0:
            self.visit_bank("upgrade", withdraw=price + 60, reserve=0)
        if self.c.gold < price:
            return True
        got = self.shop_at(xy, {"=" + name: 1}, budget=price + 5)
        if not got:
            self.note("gear", f"A {self.pname} went to buy a {name} for {price} gold at {xy} and came back without it.", key=f"upgradefail:{name}")
            return True
        new = next((i for i in self.c.backpack if i.name.lower() == name), None)
        _, old = self.worn_ar(layer)
        if new:
            if old:
                self.c.unequip(old.serial)
                # the old piece stays in the pack (newbied starter armour cannot be sold) and goes to the bank on the next trip; r_gear must not
                # put it back on
                self.facts.setdefault("gear_failed", {})[old.serial] = time.time() + 10 ** 9
                time.sleep(0.8)
            try:
                self.c.call(f"equip {new.serial}", timeout=6)
            except Exception:
                pass
            time.sleep(0.8)
        worn = any(i.name.lower() == name for i in self.c.equipped)
        self.facts.setdefault("upgrades", []).append((round(time.time()), name, price))
        self.log(f"upgrade: bought a {name} for {price} gold (armour {cur} -> {ar}); worn {worn}")
        self.note("gear", f"A {self.pname} bought a {name} for {price} gold and {'wore it' if worn else 'could not put it on'}.", key=f"upgrade:{name}:{worn}")
        return True

    def r_market(self):
        """A booked market deal: go and do it; otherwise tell the smiths which armour piece this fighter would buy."""
        d = self.mem.deal_for(self.name)
        return self.do_deal(d) if d else self.fighter_want()

    def wear_bought(self, name):
        """Put on a piece bought from a player, in place of what that layer had."""
        new = next((i for i in self.c.backpack if i.name.lower() == name), None)
        layer = next((l for l, opts in self.ARMOR_BUY.items() if any(o[0] == name for o in opts)), None)
        if new and not layer and self.facts.get("weapon_pending", {}).get("name") == name:
            pend = self.facts.pop("weapon_pending")
            self.arms_wield(name, pend.get("price", 0), pend["from"], pend["value_from"], pend["value_to"])        # a weapon bought from a player
            return
        if not new or not layer:
            return
        _, old = self.worn_ar(layer)
        if old:
            self.c.unequip(old.serial)
            self.facts.setdefault("gear_failed", {})[old.serial] = time.time() + 10 ** 9
            time.sleep(0.8)
        try:
            self.c.call(f"equip {new.serial}", timeout=6)
        except Exception:
            pass
        time.sleep(0.8)

    @property
    def FLETCH_SHOP(self):                               # the Bowyer: fletcher's tools ("Arrow Fletching") and arrows
        return self.where1(("bowyer",), item="arrow")

    def fletcher(self):
        """An archer whose template makes its own arrows (Archer: Archery, Lumberjacking and Bowcraft)."""
        return self.ranged and self.skill_values.get("Bowcraft/Fletching", 0) >= 25 and self.feature("fletch")     # A/B: features.json

    def fletch_stock(self):
        """(arrows, shafts, feathers, wood) in the pack; boards and logs both make shafts."""
        def n(*names):
            return sum((i.amount or 1) for i in self.c.backpack if i.name.lower() in names)
        return n("arrow", "arrows"), n("shaft", "shafts"), n("feather", "feathers"), n("board", "boards", "log", "logs")

    def can_make_arrows(self):
        """How many arrows the pack could become: every shaft or piece of wood needs one feather."""
        if not self.fletcher():
            return 0
        _, shafts, feathers, wood = self.fletch_stock()
        return min(shafts + wood, feathers)

    def r_fletch(self):
        """An archer makes its own arrows, as the Archer template says: wood into shafts, then shafts and feathers into arrows, with the fletcher's
        tools and the era's menu (each choice uses the whole stack). It buys arrows only when it has nothing to make them from (r_resupply)."""
        if not self.fletcher() or self.mobs(10) or time.time() < self.facts.get("fletch_wait", 0):
            return False
        arrows, shafts, feathers, wood = self.fletch_stock()
        if arrows >= 200 or not feathers or not (shafts or wood):
            return False
        want = "Arrows" if shafts else "Shafts"
        tool = next((i for i in self.c.backpack if i.name.lower() == "arrow fletching"), None)
        if not tool:
            self.facts["fletch_wait"] = time.time() + 1800
            if self.c.gold < 30:
                return False
            self.activity = "buying fletcher's tools"
            got = self.shop_at(self.FLETCH_SHOP, {"=arrow fletching": 1}, budget=20)
            self.log(f"bought fletcher's tools at the Bowyer: {got}")
            return True
        self.activity = f"fletching {want.lower()}"
        self.close_menus()
        self.read_journal()
        self.c.events.drain()
        self.c.use(tool.serial)
        # the era's fletcher's tools first ask "Target the wood or feathers you wish to use."; the menu opens only after the material is targeted
        from uo import Event
        names = ("shaft", "shafts") if want == "Arrows" else ("board", "boards", "log", "logs")
        mat = next((i for i in self.c.backpack if i.name.lower() in names), None)
        end = time.time() + 4
        asked = busy = False
        while time.time() < end and not asked and not busy:
            for e in self.c.events.poll():
                asked = asked or e.kind == Event.TARGET_REQUEST
                busy = busy or "must wait to perform" in (e.text or "")
            time.sleep(0.1)
        if busy:
            self.facts["fletch_wait"] = time.time() + 3             # "You must wait to perform another action": the tool comes back in a moment
            return False
        if asked and mat:
            self.c.target(mat.serial)
        menu = self.read_menu(wait=4)
        idx = self.index_of(menu, want) if menu else None
        if idx is None:
            if menu:
                self.close_menus([menu])
            self.facts["fletch_wait"] = time.time() + 600
            offered = [t for _, t in menu[2]] if menu else "no menu"
            self.log(f"the fletcher's tools offered {offered}, not {want} ({shafts} shafts, {feathers} feathers, {wood} wood)")
            self.note("fletch", f"With {shafts} shafts, {feathers} feathers and {wood} boards or logs, the fletcher's tools offered {offered}, not {want}.",
                      key=f"fletchmenu:{want}")
            return False
        self.c.call(f"menuresponse {menu[0]} {menu[1]} {idx}", timeout=8)
        time.sleep(3.5)
        lines = self.read_journal()
        a2, s2, f2, w2 = self.fletch_stock()
        said = next((l for l in reversed(lines) if re.search(r"create|fail|lost|cannot|must", l, re.I)), "")
        self.log(f"fletched {want.lower()}: arrows {arrows} -> {a2}, shafts {shafts} -> {s2}, feathers {feathers} -> {f2}, wood {wood} -> {w2}; {said[:80]}")
        self.ev("fletch", made=want.lower(), arrows=a2 - arrows, shafts=s2 - shafts, feathers=f2 - feathers, wood=w2 - wood)
        self.facts["fletch_wait"] = time.time() + 15
        self.note("fletch", "An archer makes arrows with the fletcher's tools (the Bowyer lists them as 'Arrow Fletching'): Shafts from boards or logs, then "
                            "Arrows from shafts and feathers, a whole stack at a time. Feathers come from carving chickens and birds.", key="howfletch")
        return True

    def r_wood(self):
        """Out of wood with feathers to spare: an archer chops logs for shafts with its starter hatchet (the template has Lumberjacking), then
        takes its bow back in hand. Not while it has arrows enough, and not more than once in a while: hunting comes first."""
        if not self.fletcher() or self.threats(10) or self.hp_pct() < 60 or time.time() < self.facts.get("wood_wait", 0):
            return False
        arrows, shafts, feathers, wood = self.fletch_stock()
        if arrows >= 120 or wood >= 20 or feathers < shafts + wood + 20 or self.c.weight > self.c.max_weight * 0.8:
            return False
        self.facts["wood_wait"] = time.time() + 900
        hat = next((i for i in self.c.backpack if "hatchet" in i.name.lower()), None) or \
            next((i for i in self.c.equipped if "hatchet" in i.name.lower()), None)
        if not hat:
            self.note("fletch", "An archer out of wood for shafts has no hatchet to cut its own.", key="nohatchet")
            return False
        bow = next((i for i in self.c.equipped if i.layer in ("OneHanded", "TwoHanded")), None)
        self.activity = "chopping wood for shafts"
        before = wood
        got = self.chop_trees(hat)
        if bow and bow.serial != hat.serial:
            self.wield(bow)                               # the bow back in hand before anything finds it holding a hatchet
        wood = self.fletch_stock()[3]
        self.ev("chop", wood=wood - before, worked=got)
        self.log(f"chopped for shafts: wood {before} -> {wood} ({'worked a tree' if got else 'no tree near could be worked' if got is False else 'the hatchet would not go in hand'})")
        if got and wood > before:
            self.note("fletch", "An archer chops its own logs for shafts with the starter hatchet: the hatchet has to be in hand (the bow goes in the pack), "
                                "and the bow back in hand afterwards.", key="archerchop")
        return bool(got)

    def r_resupply(self):
        if self.mobs(10) or self.hp_pct() < 60 or time.time() - self.facts.get("shop_at", 0) < 300:
            return False
        low_ammo = self.ranged and self.ammo() < 25 and self.can_make_arrows() < 25   # an archer who can make arrows makes them (r_fletch)
        low_band = self.bandages() < 8
        heals = sum(1 for i in self.c.backpack if i.name == "Yellow Potion")
        refreshes = sum(1 for i in self.c.backpack if i.name == "Red Potion")
        want = {}
        if self.c.gold >= 200 and heals < 3 and goals.idle_ok(self, 100):
            want["=yellow potion"] = 3                     # Heal, yellow as in the era
        if self.c.gold >= 250 and refreshes < 2 and goals.idle_ok(self, 60):
            want["=red potion"] = 2                        # Refresh, red
        if not (low_ammo or low_band or want):
            return False
        if self.c.gold < 40:
            if self.facts["bank_balance"] >= 40 and time.time() - self.facts.get("banked_at", 0) > 240:
                self.activity = "fetching gold"
                self.visit_bank("poor", withdraw=300)
            return False
        self.facts["shop_at"] = time.time()
        self.activity = "resupplying"
        if low_ammo:
            got = self.shop_at(self.FLETCH_SHOP, {"=arrow": 150}, budget=self.c.gold // 2)
            self.note("shop", f"Ammunition sold at the Bowyer: bought {got}.", key="arrows")
        if low_band or want:
            if low_band:
                want["bandage"] = 40
            got = self.shop_at(self.where1(("healer",)), want, budget=self.c.gold // 2)
            self.note("shop", f"At the Healer: bought {got}.", key="healershop")
        return True

    def r_facility(self):
        """Once, early: a player walks to the training dummy or the archery butte and tries it (the starting skill is 50, above what they teach)."""
        if self.facts.get("facility_done") or self.tick_no < 15 or self.mobs(10) or self.hp_pct() < 80:
            return False
        self.facts["facility_done"] = True
        self.save_knowledge()
        word = FACILITIES["ranged" if self.ranged else "melee"]
        spots = self.spots_for(word, n=2)
        self.activity = f"trying the {word}"
        for xy in spots:
            if self.far_front(xy, "facility", 100):
                break                                         # a dummy or butte more than 120 tiles away is not worth the walk
            res = self.c.goto(*xy).wait(timeout=100)
            for it in self.ground_items(8):
                if word in it.name.lower():
                    self.c.events.drain()
                    self.c.use(it.serial)
                    time.sleep(5)
                    lines = self.read_journal()
                    self.note("training", f"Double-clicking the {it.name} at 50 skill: {lines[-3:] or 'no message at all'}", key=f"facility:{word}")
                    self.log(f"tried the {it.name}: {lines[-3:]}")
                    return True
            here = [f"{i.name}@{i.x},{i.y}" for i in self.ground_items(12)][:25]
            self.log(f"no {word} found at {xy} ({res}); standing at {self.c.x},{self.c.y}; items near: {here}")
        self.note("training", f"No {word} was found where the map marker says; a new player is told the marker exists, not what it does.", key=f"nofacility:{word}")
        return True

    def r_hunt(self):
        if time.time() < self.facts.get("avoided_until", 0):
            return False
        ps = [m for m in self.prey(18) if m.distance > 8 and not self.near_death_spot(m.x, m.y, 40) and self.safe_ground(m)]
        if not ps or self.hp_pct() < 70:
            return False
        t = ps[0]
        self.activity = f"approaching {t.name}"
        self.c.goto(t.x, t.y).wait(timeout=4)
        return True

    # ---- the Britain sewers as a newbie hunting ground (feature "sewers"; see patch_sewers.py) -----------------------------------------------------------

    # rat / sewer rat / bull frog spawner sites (BritainSewer.json): (x, y)
    SEWER_SPOTS = [(6065, 1459), (6112, 1462), (6048, 1487), (6061, 1490), (6059, 1438), (6091, 1491), (6039, 1438), (6049, 1447), (6092, 1448),
                   (6034, 1467), (6049, 1470), (6041, 1486), (6084, 1470), (6107, 1452)]
    # alligator spawner sites: (x, y, reach) with reach = the larger of home and walking range
    SEWER_GATORS = [(6052, 1463, 25), (6090, 1483, 25), (6087, 1443, 10), (6108, 1471, 10), (6037, 1494, 10), (6077, 1492, 10)]

    SEWER_GATOR_SKILL = 50                                   # main weapon skill under which an alligator is a danger (tier 2: 53 hp, ~10 a hit); raise it to keep newbies out longer

    # Owner 2026-10-18: "Please have bots avoid the Britain sewers. It's terrible hunting grounds and 1 lane corridors make it awful to navigate."
    # No bot goes down, whatever features.json or an ambition grants; a bot that logs in below climbs out (r_sewer_out, why "off"). The code stays for the way out.
    SEWERS_BANNED = True

    def sewer_side(self):
        """The level the sewer spots are on: the gazetteer's side of their coordinates."""
        return self.tele_side_of(*self.SEWER_SPOTS[0])

    def in_sewer(self):
        return self.tele_side() == self.sewer_side()

    def tele_allowed(self, side):
        """Into the sewer level only when the brain wants to be there (feature, newbie, not stood down); other sides as the base."""
        if side == self.sewer_side():
            return self.sewer_wanted() and time.time() >= self.facts.get("sewer_off_until", 0)
        return super().tele_allowed(side)

    def sewer_in(self):
        """Cross to the sewer level through whichever teleporter the route finds; True when below."""
        if self.in_sewer():
            return True
        if self.c.ghost:
            return False
        if not self.tele_enter(self.SEWER_SPOTS[0], "sewers"):
            self.log(f"sewers: could not get down from {self.c.x},{self.c.y}")
            return False
        self.facts["sewer_in_at"], self.facts["sewer_kills0"] = time.time(), getattr(self, "kills", 0)
        self.ev("sewer_enter", skill=round(self.sewer_main_skill(), 1), hp=self.hp_pct(), kills=getattr(self, "kills", 0))
        return True

    def sewer_out(self, why="walk"):
        """Cross back to the surface; True when out. ev sewer_exit with the reason; a bot that cannot get out stays out of the sewers for 6 hours."""
        if not self.in_sewer():
            return True
        if not self.tele_leave("sewers", why):
            tries = self.facts.get("sewer_stuck_n", 0) + 1
            self.facts["sewer_stuck_n"] = tries
            now = time.time()
            fails = self.facts["sewer_out_fails"] = self.facts.get("sewer_out_fails", 0) + 1
            first = self.facts.setdefault("sewer_out_first", now)
            delay = min(60 * 2 ** (fails - 1), 600)                      # 60 s, doubling to 10 minutes: the bot hunts and defends meanwhile
            self.facts["sewer_out_next"] = now + delay
            self.facts["sewer_off_until"] = now + 6 * 3600
            self.ev("sewer_stuck", where=[self.c.x, self.c.y], tries=tries, why=why, backoff=delay)
            self.log(f"sewers: no way out from {self.c.x},{self.c.y} (why {why}), tries {tries}; next try in {delay} s")
            if fails >= 3 and now - first >= 300:
                self.request_unstick("sewers: no way out")                  # like a player using Help > Stuck: ask for a move, and stand still until it comes
            return False
        for k in ("sewer_out_fails", "sewer_out_next", "sewer_out_first", "wedged_hold"):
            self.facts.pop(k, None)
        t_in = self.facts.pop("sewer_in_at", None)
        self.ev("sewer_exit", why=why, minutes=round((time.time() - t_in) / 60, 1) if t_in else None,
                kills=getattr(self, "kills", 0) - self.facts.pop("sewer_kills0", getattr(self, "kills", 0)), hp=self.hp_pct())
        return True

    def sewer_main_skill(self):
        return self.skill_values.get(self.main_skill(), 0)

    def sewer_gator_safe(self, x, y):
        return not any(max(abs(x - gx), abs(y - gy)) <= reach + 4 for gx, gy, reach in self.SEWER_GATORS)

    def sewer_wanted(self):
        return not self.SEWERS_BANNED and self.feature("sewers") and self.mode == "newbie"

    def sewer_skip(self, why):
        if time.time() - self.facts.get("sewer_skip_at", 0) > 300:
            self.facts["sewer_skip_at"] = time.time()
            self.ev("sewer_skip", why=why)

    def sewer_spot(self, claim=True):
        """The next patrol point in the sewer: a rat spawner site no other bot holds, not in an alligator's reach below skill 50; None when there is none."""
        low = self.sewer_main_skill() < self.SEWER_GATOR_SKILL
        now = time.time()
        held = self.facts.get("ground")
        if held and now < held["until"] and self.tele_side_of(held["x"], held["y"]) == self.sewer_side() and max(abs(self.c.x - held["x"]), abs(self.c.y - held["y"])) <= 40 \
                and not self.crowded_here():
            return held["x"] + random.randint(-6, 6), held["y"] + random.randint(-6, 6)          # patrol the ground before looking elsewhere
        recent = self.facts.get("spots_reached", [])[-3:]
        cands = []
        for x, y in self.SEWER_SPOTS:
            cell = cell_of(x, y)
            if low and not self.sewer_gator_safe(x, y):
                continue
            if any(abs(x - rx) < 12 and abs(y - ry) < 12 for rx, ry in recent):
                continue
            if self.facts.get("crowded", {}).get(cell, 0) > now or self.ground_load(cell) > self.ground_cap(cell):
                continue
            if not self.mem.usable("spot", cell) or self.mem.dangerous_cell(cell) or self.near_death_spot(x, y, 12):
                continue
            cands.append((max(abs(x - self.c.x), abs(y - self.c.y)) + random.random() * 25, x, y, cell))
        if not cands:
            return None
        cands.sort()
        _, x, y, cell = cands[0]
        if not claim:
            return x, y                                       # only asking whether there is one (r_sewer_in)
        self.facts["ground"] = {"x": x, "y": y, "until": now + 300}
        self.mem.record("claim", kind="ground", key=f"{cell}#{self.name}", ttl=300)
        self.ev("sewer_spot", x=x, y=y, gator_safe=self.sewer_gator_safe(x, y))
        return x, y

    def sewer_avoid(self, m):
        """An alligator below main weapon skill 50 (in the sewer): a danger, not prey."""
        return self.sewer_wanted() and self.in_sewer() and self.sewer_main_skill() < self.SEWER_GATOR_SKILL and "alligator" in (m.name or "").lower()

    def r_sewer_in(self):
        if not self.sewer_wanted() or self.in_sewer() or self.c.ghost:
            return False
        if time.time() < self.facts.get("sewer_off_until", 0):
            return False
        if time.time() - self.facts.get("sewer_entered_at", 0) < 300:
            return False                                      # went down less than 5 minutes ago: not straight back (the 14:20 ping-pong)
        if self.hp_pct() < (80 if self.feature("sewer_stay") else 70):                  # (sewer_stay: down only when well)
            return False
        if self.c.weight > self.c.max_weight * 0.8:
            self.sewer_skip("weight")
            return False
        if self.mobs(8):
            return False
        if not any(self.sewer_gator_safe(x, y) or self.sewer_main_skill() >= self.SEWER_GATOR_SKILL for x, y in self.SEWER_SPOTS):
            self.sewer_skip("no spot")
            return False
        if self.sewer_spot(claim=False) is None:
            self.sewer_skip("no free spot")                        # every spot crowded or held: going down would only bring it back up
            return False
        self.activity = "off to the sewers"
        self.facts["sewer_entered_at"] = time.time()
        if not self.sewer_in():
            self.facts["sewer_off_until"] = time.time() + 600                 # the hatch would not take it: the normal rules for a while
            self.sewer_skip("hatch failed")
            return False
        self.facts.pop("anchor", None)
        return True

    def r_wedged(self):
        """Waiting for a staff move (request_unstick): stand still, 3 s at a time, instead of wandering; fights, heals and flights come first (they are above this rule).
        Over when the character has been moved more than 6 tiles, or is a ghost."""
        h = self.facts.get("wedged_hold")
        if not h:
            return False
        if self.c.ghost or max(abs(self.c.x - h["x"]), abs(self.c.y - h["y"])) > 6:
            self.facts.pop("wedged_hold", None)
            return False
        self.activity = "stuck: waiting to be moved"
        time.sleep(3)
        return True

    def sewer_flee(self):
        """Feature sewer_stay, called by r_flee: under the flee line in the sewers the flight is the way out (the exit path), not a loop of potions. True when it acted (out, or trying)."""
        if not self.feature("sewer_stay") or not self.in_sewer() or self.c.ghost or time.time() < self.facts.get("sewer_out_next", 0):
            return False
        self.activity = "leaving the sewers (flee)"
        self.sprint()
        self.facts.pop("ground", None)
        self.facts.pop("anchor", None)
        self.log(f"sewers: fleeing out at hp {self.c.hp}/{self.c.max_hp}")
        self.sewer_out("flee")
        return True

    def r_sewer_out(self):
        if not self.in_sewer() or self.c.ghost:
            return False
        if time.time() < self.facts.get("sewer_out_next", 0):
            return False                                      # backing off after a failed exit
        now = time.time()
        why = None
        if not self.sewer_wanted():
            why = "off"
        elif self.hp_pct() < (50 if self.feature("sewer_stay") else 40):
            why = "hurt"
        else:
            seen = self.facts.setdefault("gators_seen", {})
            for m in self.mobs(10):
                if "alligator" in (m.name or "").lower() and self.sewer_main_skill() < self.SEWER_GATOR_SKILL:
                    seen[m.serial] = now
            for s in [s for s, t in seen.items() if now - t > 300]:
                del seen[s]
            if len(seen) >= 3:
                why = "alligators"
            elif self.crowded_here():
                n = self.facts.get("sewer_crowded", 0) + 1
                self.facts["sewer_crowded"] = n
                self.mark_crowded(self.c.x, self.c.y, "sewer")
                if n >= 3:
                    why = "crowded"
                    self.facts["sewer_off_until"] = now + 900
            else:
                self.facts["sewer_crowded"] = 0
                t_in = self.facts.get("sewer_in_at", now)
                if now - t_in > 720 and now - self.facts.get("last_kill_at", 0) > 480:
                    why = "dry"
                    self.facts["sewer_off_until"] = now + 1200
        if not why:
            return False
        self.activity = f"leaving the sewers ({why})"
        self.facts.pop("sewer_crowded", None)
        self.facts.pop("gators_seen", None)
        self.facts.pop("ground", None)
        self.facts.pop("anchor", None)
        self.sewer_out(why)
        return True

    def next_spot(self):
        if self.sewer_wanted() and self.in_sewer():
            s = self.sewer_spot()
            if s:
                return s
        back = self.revisit_anchor()
        if back:
            return back
        held = self.facts.get("ground")
        if held and time.time() < held["until"] and max(abs(self.c.x - held["x"]), abs(self.c.y - held["y"])) <= 20 and self.crowded_here():
            self.mark_crowded(held["x"], held["y"], "hunting ground")
            self.facts["ground"] = held = None
        if held and time.time() < held["until"]:
            return held["x"] + random.randint(-12, 12), held["y"] + random.randint(-12, 12)     # patrol the ground before looking elsewhere
        if random.random() < 0.85:
            g = self.best_ground(near=60) if time.time() - self.facts.get("pushed_at", 0) < 120 else None
            g = g or self.best_ground()
            if g:
                self.dlog("choice", what="hunting ground", why=f"cell {g[3]} score {g[0]:.1f}")
                self.facts["ground"] = {"x": g[1], "y": g[2], "until": time.time() + 300}
                self.mem.record("claim", kind="ground", key=f"{g[3]}#{self.name}", ttl=300)      # the others count it (ground_load)
                return g[1], g[2]
        recent = self.facts.setdefault("spots_reached", [])
        center, radius = self.home_range()
        if self.mode != "newbie":
            center, radius = self.home_centre(), max(radius, 380)      # the owner: new country further out, not the same farms
        crowded = self.facts.get("crowded", {})                 # an area the stall sense left (stall.py) or a crowded one: not again for a while
        return choose_spot(self.mem, self.patrol_spots(), lambda x, y: self.near_death_spot(x, y, 60) or crowded.get(cell_of(x, y), 0) > time.time(),
                           here=(self.c.x, self.c.y), recent=recent[-4:],
                           center=center, radius=radius, on_fallback=lambda spot, why: self.ev("spot_fallback", spot=list(spot), why=why), camp=self.camp_for_me)

    def r_explore(self):
        held = self.facts.get("ground")
        if held and time.time() < held["until"] and max(abs(self.c.x - held["x"]), abs(self.c.y - held["y"])) <= 12 and not self.crowded_here():
            # on its hunting ground with nothing to fight: a player stands and watches for the next spawn, with a step now and then; the
            # +-12 patrol walked 7.7 tiles a minute and burned stamina (the owner, 2026-10-15)
            self.activity = f"watching the ground at {held['x']},{held['y']}"
            if time.time() - self.facts.get("ground_step", 0) < 60:
                time.sleep(3.5)
                return True
            self.facts["ground_step"] = time.time()
            self.c.goto(held["x"] + random.randint(-3, 3), held["y"] + random.randint(-3, 3)).wait(timeout=5)
            return True
        if self.cur_spot is None or time.time() - self.spot_since > self.explore_limit():
            self.cur_spot = self.next_spot()
            self.spot_since = time.time()
        x, y = self.cur_spot
        self.activity = f"exploring toward {x},{y}"
        res = self.goto_near(x, y, 5).wait(timeout=5)
        if abs(self.c.x - x) < 5 and abs(self.c.y - y) < 5 or (res and str(res).startswith(("nopath", "blocked"))):
            if abs(self.c.x - x) < 5 and abs(self.c.y - y) < 5:
                self.patrol_visit(bool(self.prey(14)))
            self.facts.setdefault("spots_reached", []).append((x, y))
            if str(res).startswith("nopath"):
                # a planner's own nopath on the surface (sea, rock) blocks the spot for 6 h; a walk that only stopped short at the closest reachable tile, or one
                # below ground (stacked floors), for 20 minutes (BotRangerBR closed every sewer spot for 6 h, 13:31-13:52)
                short = "closest" in str(res) or self.off_surface()
                self.mem.record("blocked", kind="spot", key=cell_of(x, y), ttl=1200 if short else 6 * 3600)
            self.cur_spot = None
        return True


class BardBot(HunterBot):
    """A bard also practises its instrument skills: Peacemaking at its own feet, Discordance and Provocation on monsters when some are near."""
    RULES = ["r_dead", "r_corpse", "r_gear", "r_cure", "r_flee", "r_avoid", "r_sewer_out", "r_heal", "r_loot", "r_fight", "r_music", "r_instrument", "r_lighten", "r_resupply", "r_upgrade", "r_bank", "r_facility",
             "r_hunt", "r_rest", "r_camp", "r_sewer_in", "r_explore"]

    def instrument(self):
        return next((i for i in self.c.backpack if any(w in i.name.lower() for w in ("harp", "drum", "lute", "tambourine", "flute"))), None)

    def play(self, skill, targets):
        """Use an instrument skill and answer its prompts in order: the instrument, then each creature (or self)."""
        inst = self.instrument()
        if not inst:
            # a client that has just logged in knows nothing of the pack until it is opened (after the client rollout every bard "had no
            # instrument" and played nothing for an hour); the server picks the instrument by itself anyway, so play on when the pack still says none
            self.c.open_backpack()
            time.sleep(1.2)
            inst = self.instrument()
            if not inst and self.feature("bard_instrument"):
                self.facts["no_instrument"] = True              # the server would only ask "What instrument shall you play?": used up, see patch_bard_instrument
                if not self.facts.get("no_tool_ev"):
                    self.facts["no_tool_ev"] = True
                    self.dlog("ev", ev="no_tool", tool="instrument")
                    self.log("no instrument in the pack: no music until one is bought")
                return ""
            if not inst:
                self.note("music", "The bard's pack shows no instrument; it plays anyway, and the server picks one if there is one.", key="noinstrument")
        # measured 2026-10-14: the server picks the instrument from the pack itself and raises the "Whom do you wish to ..." cursor in the same
        # instant, so the cursor event is gone before a wait could see it; answer the prompts in order after a short pause instead
        self.c.events.drain()
        self.c.call(f"useskill {skill}", timeout=6)
        seen = ""
        for t in targets:
            time.sleep(0.7)
            lines = self.read_journal()
            seen += " | ".join(lines)
            if any("instrument" in l.lower() for l in lines):
                if not inst:
                    self.c.call("canceltarget", timeout=4)
                    return seen[-200:]
                self.c.target(inst.serial)
                time.sleep(0.7)
            self.c.target_self() if t == "self" else self.c.target(t)
        time.sleep(4)
        lines = self.read_journal()
        seen += " | ".join(lines)
        if "last tune" in seen.lower() and self.feature("bard_instrument"):
            self.log("the instrument is spent (played its last tune)")
        # the prompts themselves say "calm" and "incite" ("Whom do you wish to calm?"), so only the outcome lines count as work
        if any(w in seen.lower() for w in ("you play", "stopping the battle", "succeed", "you begin")) and "fail" not in seen.lower():
            self.work += 1
        return seen[-200:]

    INSTRUMENTS = ("tambourine", "drum", "lute", "lap harp")        # cheapest and lightest first (about 21 gold each at the Bard)

    def r_instrument(self):
        """Feature bard_instrument: an instrument has a limited number of uses; with none in the pack, buy one at the Bard (the bank first when poor)."""
        if not self.feature("bard_instrument") or not self.facts.get("no_instrument"):
            return False
        if self.instrument():
            self.facts["no_instrument"] = False
            return False
        if self.mobs(10) or self.hp_pct() < 60 or time.time() - self.facts.get("instr_try", 0) < 300:
            return False
        self.c.open_backpack()
        time.sleep(1.2)
        if self.instrument():                                              # the pack had not been read yet
            self.facts["no_instrument"] = False
            return False
        if self.c.gold < 40:
            if self.facts.get("bank_balance", 0) >= 40 and time.time() - self.facts.get("banked_at", 0) > 240:
                self.activity = "fetching gold"
                self.visit_bank("an instrument", withdraw=100)
            return False
        self.facts["instr_try"] = time.time()
        self.activity = "buying an instrument"
        gold0 = self.c.gold
        shops = self.find_places(("bard",), n=1) + self.find_places(("carpenter",), n=1)
        opened, got = False, {}
        for xy in shops:
            for want in self.INSTRUMENTS:
                got = self.shop_at(xy, {want: 1}, budget=min(self.c.gold, 150))
                opened = opened or bool(self.facts.get("shop_list_opened"))
                if got:
                    break
                if not self.facts.get("shop_list_opened"):
                    break                                                   # the list did not open here: the next shop
            if got:
                break
        self.c.open_backpack()
        time.sleep(1.2)
        if self.instrument():
            self.facts["no_instrument"] = False
            self.facts["no_tool_ev"] = False
            self.dlog("ev", ev="tool_bought", tool="instrument", gold=gold0 - self.c.gold)
            self.log(f"bought an instrument for {gold0 - self.c.gold} gold")
            self.note("music", f"A bard whose instrument wore out bought another at the Bard for {gold0 - self.c.gold} gold.", key="instrbought")
        elif opened:
            self.dlog("ev", ev="tool_missing", tool="instrument")
        return True

    def r_music(self):
        if self.feature("bard_instrument") and self.facts.get("no_instrument") and not self.instrument():
            return False                                                    # nothing to play (r_instrument buys one)
        if self.mobs(9) and not self.facts.get("music_with_mobs") or self.hp_pct() < 60:
            pass
        if time.time() - self.facts.get("music_at", 0) < 22 or self.hp_pct() < 60:
            return False
        self.facts["music_at"] = time.time()
        hostile = [m for m in self.mobs(8) if self.is_prey(m)]
        if len(hostile) >= 2:
            self.activity = "provoking"
            res = self.play("provocation", [hostile[0].serial, hostile[1].serial])
            self.note("music", f"Provocation on two monsters says: {res[-120:]}", key="provmsg")
        elif hostile:
            self.activity = "discording"
            res = self.play("discordance", [hostile[0].serial])
            self.note("music", f"Discordance says: {res[-120:]}", key="discmsg")
        elif not self.mobs(10):
            self.activity = "peacemaking"
            res = self.play("peacemaking", ["self"])
            self.note("music", f"Peacemaking with nobody near says: {res[-120:]}", key="peacemsg")
        else:
            return False
        self.log(f"music ({self.activity}): {res[-100:]}")
        return True


for _cls in (HunterBot, BardBot):
    if "r_sellgear" not in _cls.RULES:
        _cls.RULES.insert(_cls.RULES.index("r_resupply"), "r_sellgear")
    if "r_sellmeat" not in _cls.RULES:
        _cls.RULES.insert(_cls.RULES.index("r_resupply"), "r_sellmeat")


for _cls in (HunterBot, BardBot):
    if "r_stock" not in _cls.RULES:
        _cls.RULES.insert(_cls.RULES.index("r_resupply"), "r_stock")      # stock.py: the shopping list, from the bank too


for _cls in (HunterBot, BardBot):
    if "r_sellloot" not in _cls.RULES:
        _cls.RULES.insert(_cls.RULES.index("r_resupply"), "r_sellloot")      # livelihood.py: gems to the Jeweler


for _cls in (HunterBot, BardBot):
    if "r_arms" not in _cls.RULES:
        _cls.RULES.insert(_cls.RULES.index("r_upgrade") + 1, "r_arms")      # weaponup.py: a better weapon


for _cls in (HunterBot, BardBot):
    if "r_window" not in _cls.RULES:
        _cls.RULES.insert(_cls.RULES.index("r_upgrade"), "r_window")      # market.py: read the armourers' lists


for _cls in (HunterBot, BardBot):
    if "r_market" not in _cls.RULES:
        _cls.RULES.insert(_cls.RULES.index("r_resupply"), "r_market")


for _cls in (HunterBot, BardBot):
    if "r_trip" not in _cls.RULES:
        _cls.RULES.insert(_cls.RULES.index("r_fight") + 1, "r_trip")          # first_trip: the outing waits behind fights, flights and heals


for _cls in (HunterBot, BardBot):
    if "r_wedged" not in _cls.RULES:
        _cls.RULES.insert(_cls.RULES.index("r_hunt"), "r_wedged")        # standing still while a staff move is awaited


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True)
    ap.add_argument("--profession", type=int, required=True)
    ap.add_argument("--for", dest="seconds", type=float, default=3600)
    a = ap.parse_args()
    bot = (BardBot if a.profession == 9 else HunterBot)(a.name, a.profession)
    bot.refresh_skills()
    bot.run(a.seconds)


if __name__ == "__main__":
    sys.exit(main())


for _cls in (HunterBot, BardBot):
    for _name, _before in (("r_rune_mark", "r_fight"), ("r_rune_buy", "r_resupply")):
        if _name not in _cls.RULES:
            _cls.RULES.insert(_cls.RULES.index(_before), _name)          # runes.py: mark a rune when quiet, buy blank runes (feature runes; Magery decides who)
