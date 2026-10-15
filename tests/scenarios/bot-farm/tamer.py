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
from uo import Event

HERE = os.path.dirname(os.path.abspath(__file__))
TAME = json.load(open(os.path.join(HERE, "tame_data.json"), encoding="utf-8"))
WILD_DANGER = 14      # average damage per hit at which a tame attempt is not worth the bandage bill for a 77 hit point character


def norm(t):
    return re.sub(r"[^a-z]", "", re.sub(r"^(an?|the) ", "", t.lower()))


class TamerBot(BotBase):
    RULES = ["r_dead", "r_corpse", "r_flee", "r_heal", "r_tame", "r_bank", "r_explore"]
    # no r_evade here: wild animals are what a tamer walks up to

    def __init__(self, name, profession):
        super().__init__(name, profession)
        self.spots = list(SPOTS)
        random.Random(name).shuffle(self.spots)
        self.tamed = 0
        self.failed = 0
        self.ignored = {}

    def skill(self):
        return self.skill_values.get("Animal Taming", 50.0)

    def candidates(self):
        out = []
        sk = self.skill()
        for m in self.c.mobiles(within=16):
            if m.notoriety == "Innocent" or self.ignored.get(m.serial, 0) > time.time():
                continue
            t = TAME.get(norm(m.name))
            if not t or t["min"] > sk + 1 or t["min"] < sk - 46:
                continue                      # unreachable, or so easy that taming it cannot teach anything
            seen = self.mem.res_stats("tame", norm(m.name))
            if seen and seen["fail"] >= 6 and seen["ok"] == 0:
                continue                      # bots have tried this kind many times and never tamed one: not worth the time
            dmg = (t.get("dmg") or [0, 0])
            if sum(dmg) / 2 > WILD_DANGER and t["min"] > sk - 8:
                continue
            out.append((t["min"], -m.distance, m, t))
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
        if m.distance > 2:
            self.c.goto(m.x, m.y).wait(timeout=5)
            return True
        self.c.events.drain()
        self.c.call("useskill animal taming", timeout=6)
        if self.c.wait_for(Event.TARGET_REQUEST, timeout=4) is None:
            self.note("tame", "Using Animal Taming raised no target cursor.", key="notamecursor")
            time.sleep(2)
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
        self.mem.record("res", kind="tame", key=norm(m.name), ok=bool(re.search(r"accept you", result, re.I)), reason=result[:60])
        if re.search(r"accept you", result, re.I):
            self.work += 1
            self.tamed += 1
            self.note("tame", f"A successful tame says: {result[:100]}", key="tamemsg")
            self.after_tame(m)
        else:
            self.failed += 1
            self.ignored[m.serial] = time.time() + 60
            self.note("tame", f"A failed or refused tame says: {result[:100] or 'nothing'}", key=f"tamefail:{result[:30]}")
        self.refresh_skills()
        return True

    def after_tame(self, m):
        """Animal Lore on the new pet, then let it go so the next animal can be tamed."""
        self.c.events.drain()
        self.c.call("useskill animal lore", timeout=6)
        if self.c.wait_for(Event.TARGET_REQUEST, timeout=4) is not None:
            self.c.target(m.serial)
            time.sleep(3)
            for l in self.read_journal()[-4:]:
                self.note("tame", f"Animal Lore on a pet answers: {l[:100]}", key="loremsg")
            self.c.call("gumps", timeout=6)
        self.c.say("all release")
        time.sleep(2)
        for l in self.read_journal():
            self.note("tame", f"Releasing a pet answers: {l[:100]}", key="releasemsg")

    def r_explore(self):
        for _ in range(len(self.spots)):
            x, y = self.spots[0]
            if self.near_death_spot(x, y, 60):
                self.spots.append(self.spots.pop(0))
            else:
                break
        x, y = self.spots[0]
        self.activity = f"looking for animals toward {x},{y}"
        res = self.c.goto(x, y).wait(timeout=6)
        if abs(self.c.x - x) < 6 and abs(self.c.y - y) < 6 or str(res).startswith(("nopath", "blocked")):
            self.spots.append(self.spots.pop(0))
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
