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
from memory import cell_of, choose_spot  # noqa: E402

sys.path.insert(0, os.path.join(HERE, "..", "new-mage-playtest"))
from knowledge import Knowledge, norm  # noqa: E402

SPOTS = [(1380, 1560), (1300, 1520), (1260, 1495), (1450, 1450), (1600, 1500), (1650, 1700), (1450, 1850), (1330, 1650), (1530, 1520), (1560, 1650)]
SAFE_NAMES = ("rat", "cat", "magpie", "crow", "rabbit", "hind", "sheep", "chicken", "pig", "goat", "cow", "gull", "bird", "dog", "lizard", "toad", "frog", "squirrel", "snake", "eagle", "mongbat", "gorilla", "slime", "bull", "swallow", "sparrow", "pigeon", "finch", "owl", "raven", "parrot", "turkey", "duck", "ostrich", "llama", "walrus", "panther", "jackrabbit", "bunny", "mouse", "mud")
DANGEROUS_WORDS = ("bear", "wolf", "cougar", "panther", "snake", "serpent", "spider", "scorpion", "orc", "troll", "ogre", "lizardman", "ettin", "skeleton", "zombie", "ghoul", "wraith",
                   "spectre", "shade", "gazer", "harpy", "imp", "daemon", "drake", "dragon", "wyrm", "elemental", "lich", "mummy", "reaper", "golem", "giant", "alligator", "bull", "boar",
                   "leopard", "lion", "tiger", "ratman", "bone", "mage", "executioner", "brigand", "rogue")
SWING_SECONDS = 2.0
ENGAGED = 0.7
ARMOR_CUT = {"Mace Fighter": 0.3, "Fencer": 0.3, "Swordsman": 0.3, "Archer": 0.15, "Ranger": 0.15, "Bard": 0.15, "Warlock": 0.05}
ARCHERS = ("Archer", "Ranger", "Bard")
FACILITIES = {"melee": ("dummy", [(1589, 1554), (1528, 1431)]), "ranged": ("butte", [(1468, 1579)])}


class HunterBot(BotBase):
    RULES = ["r_dead", "r_corpse", "r_gear", "r_cure", "r_flee", "r_avoid", "r_heal", "r_loot", "r_fight", "r_lighten", "r_resupply", "r_bank", "r_facility", "r_hunt", "r_rest",
             "r_explore"]
    LOOT_MATERIALS = False

    def r_lighten(self):
        """A fighter over three quarters of its weight with crafting material in the pack (hides from the cows it killed, mostly) leaves the heaviest of
        it on the ground: no Britain shop buys hides, and weight slows it, drains its stamina and finally stops it."""
        if self.c.weight < self.c.max_weight * 0.75 or self.mobs(6) or time.time() < self.facts.get("drop_refused_until", 0):
            return False                                  # drops refused a moment ago (overloaded): r_bank takes it from here
        mats = sorted((i for i in self.c.backpack if any(w in i.name.lower() for w in self.MATERIALS)),
                      key=lambda i: next(k for k, w in enumerate(self.MATERIALS) if w in i.name.lower()))
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
        self.note("weight", f"A {self.pname} filled its pack with hides and other crafting material that no shop in Britain buys; nothing tells a new player which loot is worth carrying.",
                  key="deadweight")
        return True

    def __init__(self, name, profession):
        super().__init__(name, profession)
        self.k = Knowledge(os.path.join(HERE, "..", "new-mage-playtest", "game_data.json"))
        self.ranged = self.pname in ARCHERS
        self.spots = list(SPOTS)
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
        ttk = time.time() - f["t0"]
        if (ttk < 0.3 or outcome == "lost" and ttk < 3) and outcome != "death":
            return
        for scope in ("world", "prof"):
            self.mem.record("fight", scope=scope, m=f["key"], grp=self.mem.grp, outcome=outcome, ttk=round(ttk, 1), dmg=max(0, f["hp0"] - f["hpmin"]), hp=self.c.max_hp, cell=f["cell"], mhits=f["mhits"])

    def on_flee(self):
        self.end_fight("flee")

    def is_prey(self, m):
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

    def prey(self, within=9):
        return [m for m in self.mobs(within) if self.is_prey(m) and self.ignored.get(m.serial, 0) < time.time()]

    def dangers(self, within=8):
        return [m for m in self.mobs(within) if not self.is_prey(m)]

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
        r = super().r_dead()
        if r and was is None:
            for i, (dist, name, key, avg) in enumerate(self.recent_threats):
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
        a = self.assess(d)
        hopeless = bool((a.get("monster") or {}).get("casts")) or a.get("taken", 0) > 0.6 * max(1, self.c.hp)
        hopeless = hopeless or self.mkey(d) in self.avoid_types or self.near_death_spot(self.c.x, self.c.y, 15)
        if hopeless and d.distance <= 6:
            # learned from a Mace Fighter killed by a wraith while "cornered": against a caster or something that out-damages us, standing to fight is death;
            # run for the town guards at once, before the health is gone
            self.activity = f"running from {d.name}"
            self.end_fight("flee")
            self.dlog("choice", what="run to town", why=f"{d.name}: {a.get('reason', '')}"[:120])
            self.call_guards(d)
            self.c.goto(*self.refuge_from(d)).wait(timeout=6)
            return True
        if d.distance <= 3 and self.hp_pct() > 40:
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

    def step_away(self, m, dist=3):
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

    def r_resupply(self):
        if self.mobs(10) or self.hp_pct() < 60 or time.time() - self.facts.get("shop_at", 0) < 300:
            return False
        low_ammo = self.ranged and self.ammo() < 25
        low_band = self.bandages() < 8
        if not (low_ammo or low_band):
            return False
        if self.c.gold < 40:
            if self.facts["bank_balance"] >= 40 and time.time() - self.facts.get("banked_at", 0) > 240:
                self.activity = "fetching gold"
                self.visit_bank("poor", withdraw=300)
            return False
        self.facts["shop_at"] = time.time()
        self.activity = "resupplying"
        if low_ammo:
            got = self.shop_at((1470, 1579), {"arrow": 150}, budget=self.c.gold // 2)
            self.note("shop", f"Ammunition sold at the Bowyer: bought {got}.", key="arrows")
        if low_band:
            got = self.shop_at((1472, 1613), {"bandage": 40}, budget=self.c.gold // 2)
            self.note("shop", f"Bandages: bought {got}.", key="bandages")
        return True

    def r_facility(self):
        """Once, early: a player walks to the training dummy or the archery butte and tries it (the starting skill is 50, above what they teach)."""
        if self.facts.get("facility_done") or self.tick_no < 15 or self.mobs(10) or self.hp_pct() < 80:
            return False
        self.facts["facility_done"] = True
        self.save_knowledge()
        word, spots = FACILITIES["ranged" if self.ranged else "melee"]
        self.activity = f"trying the {word}"
        for xy in spots:
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
        ps = [m for m in self.mobs(18) if self.is_prey(m) and m.distance > 8 and not self.near_death_spot(m.x, m.y, 40)]
        if not ps or self.hp_pct() < 70:
            return False
        t = ps[0]
        self.activity = f"approaching {t.name}"
        self.c.goto(t.x, t.y).wait(timeout=4)
        return True

    def next_spot(self):
        recent = self.facts.setdefault("spots_reached", [])
        return choose_spot(self.mem, SPOTS, lambda x, y: self.near_death_spot(x, y, 60), here=(self.c.x, self.c.y), recent=recent[-4:])

    def r_explore(self):
        if self.cur_spot is None or time.time() - self.spot_since > 240:
            self.cur_spot = self.next_spot()
            self.spot_since = time.time()
        x, y = self.cur_spot
        self.activity = f"exploring toward {x},{y}"
        res = self.c.goto(x, y).wait(timeout=5)
        if abs(self.c.x - x) < 5 and abs(self.c.y - y) < 5 or (res and str(res).startswith(("nopath", "blocked"))):
            self.facts.setdefault("spots_reached", []).append((x, y))
            if str(res).startswith("nopath"):
                self.mem.record("blocked", kind="spot", key=cell_of(x, y), ttl=6 * 3600)   # sea or rock: no bot need try it again tonight
            self.cur_spot = None
        return True


class BardBot(HunterBot):
    """A bard also practises its instrument skills: Peacemaking at its own feet, Discordance and Provocation on monsters when some are near."""
    RULES = ["r_dead", "r_corpse", "r_gear", "r_cure", "r_flee", "r_avoid", "r_heal", "r_loot", "r_fight", "r_music", "r_lighten", "r_resupply", "r_bank", "r_facility", "r_hunt",
             "r_rest", "r_explore"]

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
        # the prompts themselves say "calm" and "incite" ("Whom do you wish to calm?"), so only the outcome lines count as work
        if any(w in seen.lower() for w in ("you play", "stopping the battle", "succeed", "you begin")) and "fail" not in seen.lower():
            self.work += 1
        return seen[-200:]

    def r_music(self):
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
