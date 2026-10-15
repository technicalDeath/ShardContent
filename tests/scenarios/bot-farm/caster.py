"""Pure Mage, Warlock and Sorcerer: the new-mage playtest bot (tests/scenarios/new-mage-playtest/mage_bot.py) run as one of the farm's bots.

    python caster.py --name BotMageA --profession 11 --for 3600

The mage bot keeps its own log, knowledge and stats in a per-bot folder (work/botfarm/<name>/); its notes go to the farm's shared notes.jsonl, tagged with the
bot and profession, and a status.json heartbeat is written every ten seconds for the supervisor's dashboard.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "new-mage-playtest"))
from bot_common import FARM, PROFESSIONS, BotBase, Notes  # noqa: E402
from memory import SharedMemory, cell_of, choose_spot  # noqa: E402

import mage_bot  # noqa: E402


class CasterBot(mage_bot.Bot):
    RICH_GOLD = 900

    def __init__(self, name, profession):
        d = os.path.join(FARM, name)
        os.makedirs(d, exist_ok=True)
        mage_bot.OUT = d
        super().__init__(name, None)
        self.profession = profession
        self.pname = PROFESSIONS.get(profession, str(profession))
        self.notes = Notes(name, self.pname)
        self.mem = SharedMemory(self.pname, name)
        self.episode = None
        self.work = 0
        if self.c.ghost:
            self.facts["ghost_since"] = time.time()          # already dead when this brain started: not a new death
        self.decisions_path = os.path.join(d, "decisions.jsonl")
        self.last_presence = 0.0
        self.fight = None
        self.cur_spot = None
        self.spot_since = 0.0
        self.dir = d
        self.started = time.time()
        self.last_status = 0.0
        self.activity = ""

    # ---- shared memory: what was met, how fights went, where to hunt ------------------------------------------------

    # the decision log is the hunters' one (bot_common.BotBase), borrowed as plain functions
    dlog = BotBase.dlog
    note_kill_at = BotBase.note_kill_at
    home_range = BotBase.home_range
    track_episode = BotBase.track_episode
    close_episode = BotBase.close_episode

    def total_gains(self):
        return sum(self.stats.get("gains", {}).values())

    def is_prey(self, m):
        r = super().is_prey(m)
        key = BotBase.mkey(m)
        final, why = r, ""
        if key in self.mem.deadly_kinds():
            final, why = False, "memory: this kind has killed casters"
        else:
            stats, src = self.mem.fight_stats(key)
            if stats:
                if stats["death_rate"] >= 0.25 or stats["flee_rate"] >= 0.5:
                    final, why = False, f"memory ({src}): {stats['n']:.0f} fights, {stats['death_rate']:.0%} deaths, {stats['flee_rate']:.0%} fled"
                elif not r and stats["death"] < 0.5 and stats["flee_rate"] < 0.2 and stats["avg_dmgpct"] <= 0.4:
                    final, why = True, f"memory ({src}): {stats['n']:.0f} fights, lost {stats['avg_dmgpct']:.0%} on average, none died"
        if final != r:
            logged = self.facts.setdefault("mem_logged", {})
            if time.time() - logged.get(key, 0) > 300:
                logged[key] = time.time()
                self.dlog("mem", m=key, table=r, final=final, why=why[:120])
        return final

    def attack(self, m, train=False):
        if not (self.fight and self.fight["serial"] == m.serial):
            if self.fight:
                self.end_fight("kill" if self.target_died(self.fight) else "lost")
            mon = self.k.monster(m)
            self.fight = {"serial": m.serial, "key": BotBase.mkey(m), "t0": time.time(), "hp0": self.c.hp, "hpmin": self.c.hp, "kills0": self.kills,
                          "mhits": (sum(mon["hits"]) / 2.0) if mon else 0, "cell": cell_of(m.x, m.y), "xy": (m.x, m.y), "pct": 100,
                          "corpses0": {c.serial for c in self.c.containers(within=14)}}
        return super().attack(m, train)

    def target_died(self, f):
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
            self.note_kill_at(self.c.x, self.c.y)
            self.log(f"kill #{self.kills}: {f['key']}")
        ttk = time.time() - f["t0"]
        if (ttk < 0.3 or outcome == "lost" and ttk < 3) and outcome != "death":
            return
        for scope in ("world", "prof"):
            self.mem.record("fight", scope=scope, m=f["key"], grp=self.mem.grp, outcome=outcome, ttk=round(ttk, 1), dmg=max(0, f["hp0"] - f["hpmin"]), hp=self.c.max_hp, cell=f["cell"], mhits=f["mhits"])

    def r_dead(self):
        first = self.c.ghost and self.facts["ghost_since"] is None
        if first:
            # the killer: the fight's target, or else the nearest hostile seen in the last ticks (casters often die before a spell lands)
            threats = getattr(self, "recent_threats", [])
            killer = self.fight["key"] if self.fight else (threats[0][2] if threats else None)
            self.log(f"DEAD at {self.c.x},{self.c.y} (killed by {killer or 'nothing seen'}; threats near: {[t[1] for t in threats[:3]]})")
            if self.fight:
                self.end_fight("death")
            elif killer:
                for scope in ("world", "prof"):
                    self.mem.record("fight", scope=scope, m=killer, grp=self.mem.grp, outcome="death", ttk=0, dmg=self.c.max_hp, hp=self.c.max_hp, cell=cell_of(self.c.x, self.c.y))
            self.mem.record("death", cell=cell_of(self.c.x, self.c.y), killers=[killer] if killer else [])
        return super().r_dead()

    RULES = ["r_dead", "r_cure"] + [r for r in mage_bot.Bot.RULES if r != "r_dead"]

    def r_cure(self):
        """Poisoned: cast Cure if there is mana, else drink the Orange potion. A Heal spell fails on a poisoned character ("You cannot heal yourself in your
        current state."), which is how three casters died in four minutes."""
        if self.c.ghost or not self.c.poisoned or time.time() - self.facts.get("cured_at", 0) < 6:
            return False
        self.facts["cured_at"] = time.time()
        if self.c.mana >= 6:
            self.cast("cure", "self")
            self.notes.add("poison", "A poisoned caster cures itself first: a Heal spell does not work while poisoned, and the message does not say to cure.", key="cure:spell")
            return True
        pot = next((i for i in self.c.backpack if i.name == "Orange Potion"), None)
        if pot:
            self.c.use(pot.serial)
            time.sleep(1.5)
            return True
        return False

    def r_heal(self):
        if self.c.poisoned:
            return False
        return super().r_heal()

    def r_flee(self):
        r = super().r_flee()
        if r:
            self.end_fight("flee")
        return r

    def r_explore(self):
        if self.cur_spot is None or time.time() - self.spot_since > 240:
            recent = self.facts.setdefault("spots_reached", [])
            center, radius = self.home_range()
            self.cur_spot = choose_spot(self.mem, [tuple(s) for s in self.spots], lambda x, y: any(abs(x - dx) < 70 and abs(y - dy) < 70 for dx, dy in self.facts.get("death_spots", [])),
                                        here=(self.c.x, self.c.y), recent=recent[-4:], center=center, radius=radius)
            self.spot_since = time.time()
        x, y = self.cur_spot
        res = self.c.goto(x, y).wait(timeout=4)
        if abs(self.c.x - x) < 4 and abs(self.c.y - y) < 4 or (res and str(res).startswith(("nopath", "blocked"))):
            self.facts.setdefault("spots_reached", []).append((x, y))
            if str(res).startswith("nopath"):
                self.mem.record("blocked", kind="spot", key=cell_of(x, y), ttl=6 * 3600)   # sea or rock: no bot need try it again tonight
            self.cur_spot = None
        return True

    def observe(self):
        self.activity = self.last_rule or ""
        self.track_episode()
        if time.time() - self.last_presence > 60 and not self.c.ghost:
            self.last_presence = time.time()
            self.mem.record("presence", cell=cell_of(self.c.x, self.c.y), rule=self.last_rule)
        for m in self.c.mobiles(within=14):
            if m.notoriety in ("Gray", "Criminal", "Enemy", "Murderer") and m.name != "Generic Player" and not self.c.ghost:
                self.mem.sight(BotBase.mkey(m), m.x, m.y)
        threats = sorted((m.distance, m.name, BotBase.mkey(m)) for m in self.mobs(12))
        if threats:
            self.recent_threats = threats
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
        super().observe()
        if time.time() - self.last_status < 10:
            return
        self.last_status = time.time()
        s = {
            "name": self.name, "profession": self.pname, "t": time.time(), "uptime": int(time.time() - self.started), "rule": self.last_rule, "activity": self.last_rule,
            "hp": self.c.hp, "max_hp": self.c.max_hp, "mana": self.c.mana, "stam": self.c.stamina, "pos": [self.c.x, self.c.y], "gold": self.c.gold,
            "weight": [self.c.weight, self.c.max_weight], "ghost": self.c.ghost, "kills": self.kills, "deaths": self.deaths,
            "gains": {k.split(":")[0]: v for k, v in self.stats.get("gains", {}).items()}, "skills": self.stats.get("skill_gains", {}), "tick": self.tick_no,
            "all_skills": {k: v for k, v in sorted(self.stats.get("skill_gains", {}).items()) if v > 0},
        }
        with open(os.path.join(self.dir, "status.json"), "w", encoding="utf-8") as f:
            json.dump(s, f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True)
    ap.add_argument("--profession", type=int, default=11)
    ap.add_argument("--for", dest="seconds", type=float, default=3600)
    a = ap.parse_args()
    CasterBot(a.name, a.profession).run(a.seconds)


if __name__ == "__main__":
    sys.exit(main())
