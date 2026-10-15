"""Fisherman: walks to the lake south of Britain, fishes (the shard repeats the cast by itself), lights a campfire with kindling and cooks what it caught
and the raw food it started with, banks the leftovers.

    python fisher.py --name BotFisherA --profession 21 --for 3600
"""
from __future__ import annotations

import argparse
import re
import sys
import time

from bot_common import BotBase
from uo import Event

SHORE = (1453, 1756)
WATER_LAND = (0xA8, 0xA9, 0xAA, 0xAB)


class FisherBot(BotBase):
    RULES = ["r_dead", "r_corpse", "r_flee", "r_bank", "r_cut", "r_cook", "r_fish", "r_idle"]
    KEEP = ("book", "gold", "candle", "bag", "scroll", "potion", "recall", "scissors", "bedroll", "kindling", "bandage", "pole", "dagger", "flour", "water", "pitcher", "cooked", "fish steak",
            "leg of lamb", "chicken leg", "bread", "pie")

    def __init__(self, name, profession):
        super().__init__(name, profession)
        self.water = None
        self.catches = 0
        self.cooked = 0

    def raw_food(self):
        return [i for i in self.c.backpack if i.name.lower().startswith("raw ") or i.name.lower() in ("fish", "big fish", "small fish")]

    def find_water(self):
        near = []
        for x in range(self.c.x - 5, self.c.x + 6):
            for y in range(self.c.y - 5, self.c.y + 6):
                for l in self.c.call(f"tiles {x} {y}", timeout=5):
                    m = re.match(r"\s+land\s+0x([0-9A-Fa-f]+)\s+z=(-?\d+)", l)
                    if m and int(m.group(1), 16) in WATER_LAND:
                        near.append((max(abs(x - self.c.x), abs(y - self.c.y)), x, y, int(m.group(2))))
        near.sort()
        return near[0][1:] if near else None

    def pole(self):
        for i in self.c.equipped:
            if "fishing pole" in i.name.lower():
                return i
        return self.c.find("fishing pole")

    def r_cut(self):
        """Whole fish are cut into steaks with a knife before they can be cooked."""
        fish = [i for i in self.c.backpack if i.name.lower() in ("fish", "big fish", "small fish")]
        if len(fish) < 4 or self.mobs(8):
            return False
        knife = self.c.find("dagger") or self.c.find("knife")
        if not knife:
            return False
        self.activity = "cutting fish"
        for f in fish[:12]:
            self.c.events.drain()
            self.c.use(knife.serial)
            if self.c.wait_for(Event.TARGET_REQUEST, timeout=4) is None:
                return False
            self.c.target(f.serial)
            time.sleep(1.6)
            for l in self.read_journal():
                self.note("cook", f"Cutting a fish with a dagger says: {l[:100]}", key="fishcut")
        return True

    def r_cook(self):
        raw = self.raw_food()
        total = sum((i.amount or 1) for i in raw)
        heavy = self.c.weight > self.c.max_weight * 0.75
        if total < 8 and not (heavy and total):
            return False
        if self.mobs(8):
            return False
        self.activity = "cooking"
        fires = [i for i in self.ground_items(6) if "campfire" in i.name.lower()]
        if not fires:
            self.c.open_backpack()
            k = self.c.find("kindling")
            if not k:
                self.note("cook", "Out of kindling: a fisherman cannot cook without a fire and nothing says where to get more.", key="nokindling")
                return False
            self.c.events.drain()
            self.c.use(k.serial)
            time.sleep(4)
            self.read_journal()
            fires = [i for i in self.ground_items(6) if "campfire" in i.name.lower()]
            if not fires:
                return False
        fire = fires[0]
        for item in raw[:4]:
            self.c.events.drain()
            self.c.use(item.serial)
            n = 0
            while n < 25 and self.c.wait_for(Event.TARGET_REQUEST, timeout=5) is not None:
                self.c.target(fire.serial)
                n += 1
                time.sleep(2.2)
                self.read_journal()
            self.cooked += n
            self.log(f"cooked {n} x {item.name}")
        self.note("cook", "Raw food is cooked by double-clicking it and targeting a campfire; the shard asks for the next target by itself until the stack is used up.", key="howcook")
        self.c.cancel_walk()
        self.c.call("canceltarget", timeout=4)
        return True

    def r_fish(self):
        if self.mobs(8) or self.hp_pct() < 50:
            return False
        if self.c.weight > self.c.max_weight * 0.9:
            return False
        if max(abs(self.c.x - SHORE[0]), abs(self.c.y - SHORE[1])) > 3:
            self.activity = "walking to the lake"
            self.travel(*SHORE, near=1)
            return True
        if self.water is None:
            self.water = self.find_water()
            self.log(f"water tile: {self.water}")
            if self.water is None:
                self.note("fish", "No water tile found by the shore.", key="nowater")
                return False
        pole = self.pole()
        if not pole:
            self.note("fish", "The fishing pole is gone or worn out.", key="nopole")
            return False
        self.activity = "fishing"
        before = self.skill_values.get("Fishing", 0)
        self.c.events.drain()
        self.c.use(pole.serial)
        if self.c.wait_for(Event.TARGET_REQUEST, timeout=4) is None:
            self.note("fish", "Double-clicking the pole raised no target cursor.", key="nocursor")
            time.sleep(2)
            return True
        x, y, z = self.water
        self.c.call(f"targettile {x} {y} {z} 0", timeout=8)
        deadline = time.time() + 30
        while time.time() < deadline:
            if self.c.weight > self.c.max_weight * 0.88:
                self.cancel_repeat()
                break
            time.sleep(2)
            lines = self.read_journal()
            for l in lines:
                if "pull out" in l:
                    self.catches += 1
                    self.note("fish", f"A catch reads: {l[:90]}", key="catchmsg")
        self.read_journal()
        return True

    def r_idle(self):
        time.sleep(3)
        return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True)
    ap.add_argument("--profession", type=int, default=21)
    ap.add_argument("--for", dest="seconds", type=float, default=3600)
    a = ap.parse_args()
    bot = FisherBot(a.name, a.profession)
    bot.refresh_skills()
    bot.run(a.seconds)


if __name__ == "__main__":
    sys.exit(main())
