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
        self.fight = None
        self.cur_spot = None
        self.spot_since = 0.0
        self.dir = d
        self.started = time.time()
        self.last_status = 0.0
        self.activity = ""

    # ---- shared memory: what was met, how fights went, where to hunt ------------------------------------------------

    def is_prey(self, m):
        r = super().is_prey(m)
        key = BotBase.mkey(m)
        if key in self.mem.deadly_kinds():
            return False
        stats, _ = self.mem.fight_stats(key)
        if stats:
            if stats["death_rate"] >= 0.25 or stats["flee_rate"] >= 0.5:
                return False
            if not r and stats["death"] == 0 and stats["flee_rate"] < 0.2 and stats["avg_dmgpct"] <= 0.4:
                return True
        return r

    def attack(self, m, train=False):
        if not (self.fight and self.fight["serial"] == m.serial):
            self.end_fight("lost")
            mon = self.k.monster(m)
            self.fight = {"serial": m.serial, "key": BotBase.mkey(m), "t0": time.time(), "hp0": self.c.hp, "hpmin": self.c.hp, "kills0": self.kills,
                          "mhits": (sum(mon["hits"]) / 2.0) if mon else 0, "cell": cell_of(m.x, m.y)}
        return super().attack(m, train)

    def end_fight(self, outcome):
        f, self.fight = self.fight, None
        if not f:
            return
        ttk = time.time() - f["t0"]
        if ttk < 1.0 and outcome != "death":
            return
        for scope in ("world", "prof"):
            self.mem.record("fight", scope=scope, m=f["key"], grp=self.mem.grp, outcome=outcome, ttk=round(ttk, 1), dmg=max(0, f["hp0"] - f["hpmin"]), hp=self.c.max_hp, cell=f["cell"], mhits=f["mhits"])

    def r_dead(self):
        first = self.c.ghost and self.facts["ghost_since"] is None
        if first:
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
            self.cur_spot = choose_spot(self.mem, [tuple(s) for s in self.spots], lambda x, y: any(abs(x - dx) < 70 and abs(y - dy) < 70 for dx, dy in self.facts.get("death_spots", [])))
            self.spot_since = time.time()
        x, y = self.cur_spot
        res = self.c.goto(x, y).wait(timeout=4)
        if abs(self.c.x - x) < 4 and abs(self.c.y - y) < 4 or (res and str(res).startswith(("nopath", "blocked"))):
            self.cur_spot = None
        return True

    def observe(self):
        for m in self.c.mobiles(within=14):
            if m.notoriety in ("Gray", "Criminal", "Enemy", "Murderer") and m.name != "Generic Player" and not self.c.ghost:
                self.mem.sight(BotBase.mkey(m), m.x, m.y)
        f = self.fight
        if f:
            f["hpmin"] = min(f["hpmin"], self.c.hp)
            if not any(m.serial == f["serial"] for m in self.c.mobiles(within=16)):
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
