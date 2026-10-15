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
                self.end_fight("kill" if self.kills > self.fight["kills0"] else "lost")
            mon = self.k.monster(m)
            self.fight = {"serial": m.serial, "key": BotBase.mkey(m), "t0": time.time(), "hp0": self.c.hp, "hpmin": self.c.hp, "kills0": self.kills,
                          "mhits": (sum(mon["hits"]) / 2.0) if mon else 0, "cell": cell_of(m.x, m.y)}
        return super().attack(m, train)

    def end_fight(self, outcome):
        f, self.fight = self.fight, None
        if not f:
            return
        ttk = time.time() - f["t0"]
        if (ttk < 0.3 or outcome == "lost" and ttk < 3) and outcome != "death":
            return
        for scope in ("world", "prof"):
            self.mem.record("fight", scope=scope, m=f["key"], grp=self.mem.grp, outcome=outcome, ttk=round(ttk, 1), dmg=max(0, f["hp0"] - f["hpmin"]), hp=self.c.max_hp, cell=f["cell"], mhits=f["mhits"])

    def r_dead(self):
        first = self.c.ghost and self.facts["ghost_since"] is None
        if first:
            self.log(f"DEAD at {self.c.x},{self.c.y} (killed by {self.fight['key'] if self.fight else 'nothing seen'})")
            self.end_fight("death")
            self.mem.record("death", cell=cell_of(self.c.x, self.c.y), killers=[self.fight["key"]] if self.fight else [])
        return super().r_dead()

    def r_flee(self):
        r = super().r_flee()
        if r:
            self.end_fight("flee")
        return r

    def r_explore(self):
        if self.cur_spot is None or time.time() - self.spot_since > 240:
            recent = self.facts.setdefault("spots_reached", [])
            self.cur_spot = choose_spot(self.mem, [tuple(s) for s in self.spots], lambda x, y: any(abs(x - dx) < 70 and abs(y - dy) < 70 for dx, dy in self.facts.get("death_spots", [])),
                                        here=(self.c.x, self.c.y), recent=recent[-4:])
            self.spot_since = time.time()
        x, y = self.cur_spot
        res = self.c.goto(x, y).wait(timeout=4)
        if abs(self.c.x - x) < 4 and abs(self.c.y - y) < 4 or (res and str(res).startswith(("nopath", "blocked"))):
            self.facts.setdefault("spots_reached", []).append((x, y))
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
        f = self.fight
        if f:
            f["hpmin"] = min(f["hpmin"], self.c.hp)
            if not any(m.serial == f["serial"] and not m.is_dead for m in self.c.mobiles(within=16)):
                self.end_fight("kill" if self.kills > f["kills0"] else "lost")
            elif time.time() - f["t0"] > 90:
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
