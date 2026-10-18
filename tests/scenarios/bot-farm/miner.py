"""Prospector: walks to the hills north of Britain, finds a mountain tile it can reach, mines it (the shard repeats the dig by itself), sells ore to the Miner
in town when it gets heavy, banks the money, and chops a tree now and then with its hatchet.

    python miner.py --name BotMinerA --profession 22 --for 3600
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time

from bot_common import BotBase, load_features
from memory import cell_of
from uo import Event

# mountain tiles north of Britain found by scanning the map (x, y, z, land graphic); the server's mining table accepts all of them
MOUNTAIN = [(1455, 1525, 20, 557), (1455, 1520, 20, 558), (1455, 1515, 20, 558), (1455, 1510, 20, 558), (1450, 1525, 60, 557), (1450, 1515, 40, 558),
            (1440, 1500, 43, 243), (1425, 1505, 11, 240), (1515, 1510, 42, 556), (1515, 1505, 3, 579)]
RING = [(0, 1), (1, 0), (-1, 0), (0, -1), (1, 1), (-1, 1), (1, -1), (-1, -1), (0, 2), (2, 0), (-2, 0), (0, -2)]
try:
    # every mountain-rock edge around Britain, one per 8 x 8 ore bank (make_mountains.py reads them from the map): ten tiles on one hill were
    # shared by three miners and the smiths who dig their own ore, so every spot was often taken or dug out
    _known = {(m[0], m[1]) for m in MOUNTAIN}
    MOUNTAIN += [tuple(t[:4]) for t in json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "mountains.json"), encoding="utf-8"))
                 if (t[0], t[1]) not in _known]
except (OSError, ValueError):
    pass


from market import MinerMarket  # noqa: E402


class MinerBot(MinerMarket, BotBase):
    SHED_LAST = ("ingot", "ore")                          # the product: dropped only when nothing else is left (drop_excess)
    RULES = ["r_dead", "r_corpse", "r_gear", "r_cure", "r_flee", "r_evade", "r_market", "r_retool", "r_sell", "r_bank", "r_mine", "r_idle"]
    KEEP = ("book", "gold", "candle", "bag", "scroll", "potion", "recall", "scissors", "bedroll", "kindling", "bandage", "pickaxe", "hatchet", "shovel", "dagger", "gem", "ruby", "sapphire", "emerald",
            "diamond", "amber", "citrine", "tourmaline", "star ")

    def __init__(self, name, profession):
        super().__init__(name, profession)
        self.spot = None
        self.dug = 0
        self.blocked = {}
        self.i = 0

    def mountains(self):
        """The mountain tiles for this bot's home: Britain's list as before, or the home's own (geo.py, made on demand), nearest first."""
        m = self.__dict__.get("_mountain_list")
        if m is None:
            import geo
            m = self._mountain_list = [tuple(t[:4]) for t in geo.regional("mountains", self.home(), MOUNTAIN)]
        return m

    def ore(self):
        return sum((i.amount or 1) for i in self.c.backpack if "ore" in i.name.lower() or "ingot" in i.name.lower())

    def pick(self):
        return next((i for i in self.c.backpack if i.name.lower() in ("pickaxe", "shovel")), None) or next((i for i in self.c.equipped if "pickaxe" in i.name.lower()), None)

    @property
    def INGOT_BUYER(self):                               # a blacksmith (buys iron ingots at 4 gp)
        return self.where1(("smith",))

    def r_retool(self):
        """The pickaxe wore out (it does, silently): buy another from the Tinker."""
        self.c.open_backpack()
        if self.pick() or self.threats(10) or time.time() - self.facts.get("retool_at", 0) < 120:
            return False
        self.facts["retool_at"] = time.time()
        self.activity = "buying a pickaxe"
        self.note("mine", "The pickaxe wore out after a short while of mining; no warning came before the last swing, and the player must find who sells another.", key="pickworn")
        if self.c.gold < 40 and self.facts["bank_balance"] >= 40:
            self.visit_bank("poor", withdraw=300)
        got = self.shop_at(self.where1(("tinker",), item="pickaxe"), {"pickaxe": 1}, budget=max(self.c.gold - 5, 0))
        self.note("shop", f"Pickaxe bought: {got}", key="newpick")
        return True

    def r_sell(self):
        heavy = self.c.weight > self.c.max_weight * 0.8
        if not heavy or self.threats(8) or time.time() - self.facts.get("sold_at", 0) < 240:
            return False
        self.facts["sold_at"] = time.time()
        if self.ore_piles(smeltable=True):
            done = self.smelt()
            if done is None:
                self.note("sell", "A miner with a full load of ore could not reach the forge; no NPC buys raw ore, so the load is worth nothing until smelted.", key="noforgeload")
        if self.mkt_hold("iron ingot"):
            self.activity = "keeping ingots for a smith"          # a smith wants them at more than the NPC pays: r_market sells them
            return True
        self.activity = "selling ingots"
        earned = self.sell_items(self.INGOT_BUYER, ("ingot",))
        self.note("sell", f"A Blacksmith buys the smelted ingots: {earned} gold for a load ({self.ore()} ore and ingots left).", key="ingotsell")
        if not earned:
            self.note("sell", "Raw ore sells to no NPC (the Miner buys none), and a full pack of ore brings nothing until the miner learns to smelt it at a forge.", key="orenosale")
        return True

    def stand_near(self, tx, ty):
        """A tile within two steps of the mountain tile that the pathfinder can reach."""
        self.travel(tx, ty + 6, near=4, tries=10)
        for dx, dy in RING:
            if not self.mem.usable("tile", f"{tx + dx},{ty + dy}"):
                continue                               # a bot got stuck on this tile before (the server denied every step off it)
            res = self.c.gotoexact(tx + dx, ty + dy).wait(timeout=12)
            if max(abs(self.c.x - tx), abs(self.c.y - ty)) <= 2:
                return True
        return False

    def r_mine(self):
        if self.threats(8) or self.hp_pct() < 50 or self.c.weight > self.c.max_weight * 0.88:
            return False
        tool = self.pick()
        if not tool:
            self.note("mine", "The pickaxe is gone or worn out; no warning came before the last use.", key="nopick")
            return False
        def ok(t):
            # not blocked for this bot, nobody else digging it now (shared memory), not where bots die, and within 200 tiles of Britain (a
            # miner on its way to 1144,1855 died past the west-woods orcs)
            # (the area danger map does not refuse a digger a whole hill: it ranks the spots by risk and refuses only those above its ceiling)
            return (self.blocked.get((t[0], t[1]), 0) < time.time() and self.mem.usable("ore", f"{t[0]},{t[1]}")
                    and not self.gather_danger(cell_of(t[0], t[1]))
                    and max(abs(t[0] - self.work_centre()[0]), abs(t[1] - self.work_centre()[1])) <= (350 if time.time() < self.facts.get("mine_wide_until", 0) else 200))
        if self.spot is None or not ok(self.spot):
            cands = [t for t in self.mountains() if ok(t)]
            if not cands:
                # every spot blocked or taken: the old loop fell through to the last one anyway (BotMineAdv kept walking to 1450,1525, which has
                # nowhere to stand); let selling, banking and idling have the tick
                self.activity = "every mining spot is taken or blocked"
                return False
            self.spot = min(cands, key=lambda t: (round(self.gather_risk(cell_of(t[0], t[1])), 1), abs(t[0] - self.c.x) + abs(t[1] - self.c.y)))
        tx, ty, tz, g = self.spot
        if max(abs(self.c.x - tx), abs(self.c.y - ty)) > 2:
            self.activity = f"walking to the hills at {tx},{ty}"
            if not self.stand_near(tx, ty):
                # each failure doubles the wait (10 minutes, 20, 40 ... up to 6 hours): BotMineAdv walked back to 1450,1525 every ten minutes
                # for an hour and never once found a place to stand
                fails = self.facts.setdefault("stand_fails", {})
                fails[(tx, ty)] = fails.get((tx, ty), 0) + 1
                ttl = min(6 * 3600, 600 * 2 ** (fails[(tx, ty)] - 1))
                self.blocked[(tx, ty)] = time.time() + ttl
                self.mem.record("blocked", kind="ore", key=f"{tx},{ty}", ttl=max(1800, ttl))
                self.mem.record("res", kind="ore", key=f"{tx},{ty}", ok=False, reason="no reachable standing place")
                self.log(f"could not stand near {tx},{ty} (now at {self.c.x},{self.c.y})")
                self.note("mine", "A mountain tile on the map has no reachable spot within two steps; the miner has to look for another.", key="unreachable")
                self.i += 1
                return True
        self.activity = "mining"
        self.mem.record("claim", kind="ore", key=f"{tx},{ty}", ttl=240)
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
                if re.search(r"dig some|put it in your backpack", l, re.I):
                    self.work += 1
                    self.mem.record("res", kind="ore", key=f"{tx},{ty}", ok=True)
                if re.search(r"no metal|elsewhere|too far|cannot", l, re.I):
                    self.mem.record("res", kind="ore", key=f"{tx},{ty}", ok=False, reason=l[:60])
                    self.mem.record("blocked", kind="ore", key=f"{tx},{ty}", ttl=1500)
                    self.blocked[(tx, ty)] = time.time() + 900
                    self.i += 1
                    return True
            if self.threats(8) or self.c.weight > self.c.max_weight * 0.85:
                self.cancel_repeat()
                self.note("mine", "Mining keeps repeating while the pack gets heavier; nothing stops it before the weight limit, so the miner must step away to end the loop.", key="heavyrepeat")
                break
        self.dug += n
        return True

    def stall_switch(self, n):
        """The miner's way out of a stall (stall.py): every spot near is taken, worked out or blocked, so it looks for ore further out, as a
        player goes to the next hills (350 tiles from the work centre instead of 200, for 30 minutes)."""
        self.facts["mine_wide_until"] = time.time() + 1800
        self.spot = None
        return "look for ore up to 350 tiles out for 30 min (the near hills are taken or worked out)", ("r_mine",)

    def r_idle(self):
        time.sleep(3)
        return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True)
    ap.add_argument("--profession", type=int, default=22)
    ap.add_argument("--for", dest="seconds", type=float, default=3600)
    a = ap.parse_args()
    cls = MinerBot
    if "broke_plan" in load_features(a.name):                # the miner that can earn when its pickaxe and purse are gone (broke_gather.py)
        from broke_gather import BrokeMinerBot
        cls = BrokeMinerBot
    bot = cls(a.name, a.profession)
    bot.refresh_skills()
    bot.run(a.seconds)


if __name__ == "__main__":
    sys.exit(main())
