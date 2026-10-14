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
from bot_common import FARM, PROFESSIONS, Notes  # noqa: E402

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
        self.dir = d
        self.started = time.time()
        self.last_status = 0.0
        self.activity = ""

    def observe(self):
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
