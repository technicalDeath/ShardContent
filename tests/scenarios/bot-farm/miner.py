"""Prospector: walks to the hills north of Britain, finds a mountain tile it can reach, mines it (the shard repeats the dig by itself), sells ore to the Miner
in town when it gets heavy, banks the money, and chops a tree now and then with its hatchet.

    python miner.py --name BotMinerA --profession 22 --for 3600
"""
from __future__ import annotations

import argparse
import re
import sys
import time

from bot_common import BotBase
from uo import Event

# mountain tiles north of Britain found by scanning the map (x, y, z, land graphic); the server's mining table accepts all of them
MOUNTAIN = [(1455, 1525, 20, 557), (1455, 1520, 20, 558), (1455, 1515, 20, 558), (1455, 1510, 20, 558), (1450, 1525, 60, 557), (1450, 1515, 40, 558),
            (1440, 1500, 43, 243), (1425, 1505, 11, 240), (1515, 1510, 42, 556), (1515, 1505, 3, 579)]
RING = [(0, 1), (1, 0), (-1, 0), (0, -1), (1, 1), (-1, 1), (1, -1), (-1, -1), (0, 2), (2, 0), (-2, 0), (0, -2)]


class MinerBot(BotBase):
    RULES = ["r_dead", "r_corpse", "r_flee", "r_retool", "r_sell", "r_bank", "r_mine", "r_idle"]
    KEEP = ("book", "gold", "candle", "bag", "scroll", "potion", "recall", "scissors", "bedroll", "kindling", "bandage", "pickaxe", "hatchet", "shovel", "dagger", "gem", "ruby", "sapphire", "emerald",
            "diamond", "amber", "citrine", "tourmaline", "star ")

    def __init__(self, name, profession):
        super().__init__(name, profession)
        self.spot = None
        self.dug = 0
        self.blocked = {}
        self.i = 0

    def ore(self):
        return sum((i.amount or 1) for i in self.c.backpack if "ore" in i.name.lower() or "ingot" in i.name.lower())

    def pick(self):
        return next((i for i in self.c.backpack if i.name.lower() in ("pickaxe", "shovel")), None) or next((i for i in self.c.equipped if "pickaxe" in i.name.lower()), None)

    def r_retool(self):
        """The pickaxe wore out (it does, silently): buy another from the Tinker."""
        self.c.open_backpack()
        if self.pick() or self.mobs(10) or time.time() - self.facts.get("retool_at", 0) < 120:
            return False
        self.facts["retool_at"] = time.time()
        self.activity = "buying a pickaxe"
        self.note("mine", "The pickaxe wore out after a short while of mining; no warning came before the last swing, and the player must find who sells another.", key="pickworn")
        if self.c.gold < 40 and self.facts["bank_balance"] >= 40:
            self.visit_bank("poor", withdraw=300)
        got = self.shop_at((1427, 1652), {"pickaxe": 1}, budget=max(self.c.gold - 5, 0))
        self.note("shop", f"Pickaxe bought: {got}", key="newpick")
        return True

    def r_sell(self):
        heavy = self.c.weight > self.c.max_weight * 0.8
        if not heavy or self.mobs(8) or time.time() - self.facts.get("sold_at", 0) < 240:
            return False
        self.facts["sold_at"] = time.time()
        self.activity = "selling ore"
        earned = self.sell_items((1420, 1582), ("ore", "ingot"))
        self.note("sell", f"The Miner buys ore: {earned} gold for a full load ({self.ore()} left).", key="oresell")
        return True

    def stand_near(self, tx, ty):
        """A tile within two steps of the mountain tile that the pathfinder can reach."""
        self.travel(tx, ty + 6, near=4, tries=10)
        for dx, dy in RING:
            res = self.c.gotoexact(tx + dx, ty + dy).wait(timeout=12)
            if max(abs(self.c.x - tx), abs(self.c.y - ty)) <= 2:
                return True
        return False

    def r_mine(self):
        if self.mobs(8) or self.hp_pct() < 50 or self.c.weight > self.c.max_weight * 0.88:
            return False
        tool = self.pick()
        if not tool:
            self.note("mine", "The pickaxe is gone or worn out; no warning came before the last use.", key="nopick")
            return False
        for _ in range(len(MOUNTAIN)):
            tx, ty, tz, g = MOUNTAIN[self.i % len(MOUNTAIN)]
            if self.blocked.get((tx, ty), 0) < time.time():
                break
            self.i += 1
        if max(abs(self.c.x - tx), abs(self.c.y - ty)) > 2:
            self.activity = f"walking to the hills at {tx},{ty}"
            if not self.stand_near(tx, ty):
                self.blocked[(tx, ty)] = time.time() + 600
                self.log(f"could not stand near {tx},{ty} (now at {self.c.x},{self.c.y})")
                self.note("mine", "A mountain tile on the map has no reachable spot within two steps; the miner has to look for another.", key="unreachable")
                self.i += 1
                return True
        self.activity = "mining"
        self.c.events.drain()
        self.c.use(tool.serial)
        if self.c.wait_for(Event.TARGET_REQUEST, timeout=4) is None:
            self.note("mine", "Double-clicking the pickaxe raised no target cursor.", key="nocursor")
            time.sleep(2)
            return True
        self.c.call(f"targettile {tx} {ty} {tz} 0", timeout=8)
        end = time.time() + 40
        n = 0
        while time.time() < end:
            time.sleep(2.5)
            lines = self.read_journal()
            for l in lines:
                if re.search(r"dig|ore|nothing|no metal|too far|worn|elsewhere|rock|stone", l, re.I):
                    n += 1
                    self.note("mine", f"Mining says: {l[:100]}", key=f"minemsg:{l[:40]}")
                if re.search(r"no metal|elsewhere|too far|cannot", l, re.I):
                    self.blocked[(tx, ty)] = time.time() + 900
                    self.i += 1
                    return True
            if self.mobs(8) or self.c.weight > self.c.max_weight * 0.85:
                self.cancel_repeat()
                self.note("mine", "Mining keeps repeating while the pack gets heavier; nothing stops it before the weight limit, so the miner must step away to end the loop.", key="heavyrepeat")
                break
        self.dug += n
        return True

    def r_idle(self):
        time.sleep(3)
        return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True)
    ap.add_argument("--profession", type=int, default=22)
    ap.add_argument("--for", dest="seconds", type=float, default=3600)
    a = ap.parse_args()
    bot = MinerBot(a.name, a.profession)
    bot.refresh_skills()
    bot.run(a.seconds)


if __name__ == "__main__":
    sys.exit(main())
