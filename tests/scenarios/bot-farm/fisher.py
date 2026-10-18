"""Fisherman: walks to the lake south of Britain, fishes (the shard repeats the cast by itself), lights a campfire with kindling and cooks what it caught
and the raw food it started with, banks the leftovers.

    python fisher.py --name BotFisherA --profession 21 --for 3600
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time

from bot_common import BotBase
from memory import cell_of
from uo import Event

SHORE = (1453, 1756)
SHORES = [(1453, 1756), (1440, 1757), (1466, 1756), (1478, 1757), (1490, 1765), (1447, 1772)]   # tried in turn when the fish near one stop biting
LAKE_SHORES = tuple(SHORES)                      # the hard-coded lake south of Britain, before the map shores are added
WATER_LAND = (0xA8, 0xA9, 0xAA, 0xAB)
try:
    # an edge tile of deep water per 8 x 8 fishing bank around Britain (make_shores.py, from the map): the river and bay north of town, the
    # lake, the coast. Three fishers shared six spots on one stretch of the lake, fished it out and cycled them every two seconds.
    SHORES += [tuple(t[:2]) for t in json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "shores.json"), encoding="utf-8"))
               if max(abs(t[0] - 1470), abs(t[1] - 1620)) <= 300 and (t[0], t[1]) not in SHORES]
except (OSError, ValueError):
    pass


class FisherBot(BotBase):
    RULES = ["r_dead", "r_corpse", "r_gear", "r_cure", "r_flee", "r_evade", "r_bank", "r_unload", "r_cut", "r_cook", "r_fish", "r_idle"]
    KEEP = ("book", "gold", "candle", "bag", "scroll", "potion", "recall", "scissors", "bedroll", "kindling", "bandage", "pole", "dagger", "flour", "water", "pitcher", "cooked", "fish steak",
            "leg of lamb", "chicken leg", "bread", "pie")

    def __init__(self, name, profession):
        super().__init__(name, profession)
        self.water = None
        self.shore = 0
        self.cur_shore = None
        self.catches = 0
        self.cooked = 0

    def shores(self):
        """The shore spots for this bot's home: Britain's list as before, or the home's own (geo.py, made on demand), nearest first."""
        s = self.__dict__.get("_shore_list")
        if s is None:
            import geo
            s = self._shore_list = geo.regional("shores", self.home(), SHORES)
            try:
                import fishspot
                s = self._shore_list = [sh for sh in s if fishspot.has_stand(sh)]           # a canal's water-edge point with no walkable tile near it is no place to fish from
            except Exception:
                pass
        return s

    def raw_food(self):
        return [i for i in self.c.backpack if i.name.lower().startswith("raw ") or i.name.lower() in ("fish", "big fish", "small fish")]

    @staticmethod
    def bank_of(x, y):
        return f"{x // 8 * 8},{y // 8 * 8}"          # the server keeps fish per 8x8 block of water

    def find_water(self):
        import fishspot
        if fishspot.water() is not None:                                    # the water map: no 121 tile queries
            unseen = self.facts.get("water_unseen", {})
            spot = fishspot.nearest_water(self.c.x, self.c.y, fishspot.CAST_RANGE, lambda x, y: self.mem.usable("fish", self.bank_of(x, y))
                                          and unseen.get(f"{x},{y}", 0) < time.time())
            if spot is None:
                return None
            z = -5                                                          # deep water is at z -5; the client says if this tile is not
            for l in self.c.call(f"tiles {spot[0]} {spot[1]}", timeout=5):
                m = re.match(r"\s+land\s+0x([0-9A-Fa-f]+)\s+z=(-?\d+)", l)
                if m and int(m.group(1), 16) in WATER_LAND:
                    z = int(m.group(2))
                    break
            return (spot[0], spot[1], z)
        near = []
        for x in range(self.c.x - 5, self.c.x + 6):
            for y in range(self.c.y - 5, self.c.y + 6):
                for l in self.c.call(f"tiles {x} {y}", timeout=5):
                    m = re.match(r"\s+land\s+0x([0-9A-Fa-f]+)\s+z=(-?\d+)", l)
                    if m and int(m.group(1), 16) in WATER_LAND and self.mem.usable("fish", self.bank_of(x, y)):
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
        refused = self.facts.setdefault("uncuttable", set())
        fish = [i for i in self.c.backpack if i.name.lower() in ("fish", "big fish", "small fish") and i.serial not in refused]
        if len(fish) < 4 or self.threats(8):
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
                if "can't use a bladed item" in l or "cannot use a bladed item" in l:
                    refused.add(f.serial)              # BotFisherAR tried the same three 505 times: a big fish is not cut into steaks
                    self.log(f"{f.name} cannot be cut: left alone")
        return True

    def r_cook(self):
        raw = self.raw_food()
        total = sum((i.amount or 1) for i in raw)
        heavy = self.c.weight > self.c.max_weight * 0.75
        if total < 8 and not (heavy and total):
            return False
        if self.threats(8):
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
        for item in raw[:2]:                                 # at most about 20 cooks a tick, so a tick stays well under the 150 s hang watchdog
            self.c.events.drain()
            self.c.use(item.serial)
            n = 0
            while n < 10 and self.c.wait_for(Event.TARGET_REQUEST, timeout=5) is not None:
                self.c.target(fire.serial)
                n += 1
                time.sleep(2.2)
                self.read_journal()
            self.cooked += n
            self.work += n
            self.log(f"cooked {n} x {item.name}")
        self.note("cook", "Raw food is cooked by double-clicking it and targeting a campfire; the shard asks for the next target by itself until the stack is used up.", key="howcook")
        self.c.cancel_walk()
        self.c.call("canceltarget", timeout=4)
        return True

    def r_unload(self):
        """Heavy with the catch itself (cooked steaks are kept, so the ordinary bank trip found no junk to leave and BotFisherA stood idle at
        90% of its weight for forty minutes): take the fish and steaks to the bank box."""
        if self.c.weight <= self.c.max_weight * 0.85 or self.threats(8) or time.time() - self.facts.get("unloaded_at", 0) < 300:
            return False
        self.facts["unloaded_at"] = time.time()
        self.activity = "taking the catch to the bank"
        return self.visit_bank("catch", extra=("fish", "steak", "lobster", "crab", "cooked")) or True

    # ---- stay on a shore that works (feature "fisher_stay") ---------------------------------------------------------------

    PERSIST = BotBase.PERSIST + ("good_shores",)        # a restart keeps where the fish were caught

    def shore_known(self, key):
        """Fish were caught here, by this bot (facts) or by any fisher (shared memory)."""
        if key in self.facts.get("good_shores", {}):
            return True
        r = self.mem.res_stats("shore_ok", key)
        return bool(r and r["ok"] > 0)

    def shore_caught(self, shore):
        key = f"{shore[0]},{shore[1]}"
        good = self.facts.setdefault("good_shores", {})
        if key not in good:
            self.mem.record("res", kind="shore_ok", key=key, ok=True)             # the others learn it too (once per bot per shore)
        good[key] = time.time()
        self.ev("fish_catch", shore=list(shore))

    def shore_why(self, sh, others, mine, current):
        """None when the shore can be fished, else why not: blocked (this bot's own block), claimed (blocked or claimed in shared memory), fish_bank
        (fished out), others (another fisher within 3 tiles; for the shore the bot stands on, only one whose name sorts before ours counts),
        danger."""
        key_ = f"{sh[0]},{sh[1]}"
        if mine.get(key_, 0) >= time.time():
            return "blocked"
        if not self.mem.usable("shore", key_):
            return "claimed"
        if not self.mem.usable("fish", self.bank_of(*sh)):
            return "fish_bank"
        if any(max(abs(m.x - sh[0]), abs(m.y - sh[1])) <= 3 and not (current and self.name < m.name) for m in others):
            return "others"
        if self.gather_danger(cell_of(*sh)):
            return "danger"
        return None

    def pick_shore(self, others, mine):
        """Keep the shore while it is fine; else the next one by tier (known good, the lake, a new one). False when there is none to try now."""
        cur = self.cur_shore
        if cur is not None:
            why = self.shore_why(cur, others, mine, True)
            if why is None:
                return True
            self.ev("shore_leave", shore=list(cur), why=why)
            self.cur_shore, self.water = None, None
        cands = [tuple(sh[:2]) for sh in self.shores() if self.shore_why(tuple(sh[:2]), others, mine, False) is None]
        if not cands:
            self.activity = "every shore is taken"
            return False
        known = [sh for sh in cands if self.shore_known(f"{sh[0]},{sh[1]}")]
        lake = [sh for sh in cands if sh in LAKE_SHORES]
        if known:
            pool, tier = known, "known"
        elif lake:
            pool, tier = lake, "lake"
        else:
            if time.time() - self.facts.get("shore_explore_at", 0) < 120:
                self.activity = "waiting to try a new shore"
                return False
            self.facts["shore_explore_at"] = time.time()
            pool, tier = [sh for sh in cands if max(abs(sh[0] - 1470), abs(sh[1] - 1620)) <= 150] or cands, "explore"
        self.cur_shore = min(pool, key=lambda sh: abs(sh[0] - self.c.x) + abs(sh[1] - self.c.y))
        self.water = None
        self.ev("shore_pick", shore=list(self.cur_shore), tier=tier, dist=max(abs(self.cur_shore[0] - self.c.x), abs(self.cur_shore[1] - self.c.y)))
        return True

    def shore_walk(self, shore, near=4, tries=8, per=60):
        """BotBase.travel with the reason it failed: "ok", "nopath" (the planner found no path: stop at the first), "blocked" (something in the way,
        no step made), "threat" (a hostile or death cut it short) or "tries" (hopped out, still not there)."""
        for _ in range(tries):
            if max(abs(self.c.x - shore[0]), abs(self.c.y - shore[1])) <= near:
                return "ok"
            before = (self.c.x, self.c.y)
            res = str(self.c.goto(*shore).wait(timeout=per))
            if self.c.ghost or self.mobs(5):
                return "threat"
            if max(abs(self.c.x - shore[0]), abs(self.c.y - shore[1])) <= near:
                return "ok"
            if res.startswith("nopath"):
                return "nopath"
            if res.startswith("blocked") and (self.c.x, self.c.y) == before:
                return "blocked"
        return "tries"

    def stay_walk(self, shore, key, mine, goal=None):
        why = self.shore_walk(goal, near=2) if goal else self.shore_walk(shore)
        if why in ("ok", "threat"):
            return True                                   # on its way, or cut short for a reason that is not the shore's
        if why in ("nopath", "tries", "blocked") and self.fish_from_here(shore):
            return True                                   # the walk ended short but there is water in range here: fish from here
        known = self.shore_known(key)
        fails = self.facts.setdefault("shore_fails", {})
        fails[key] = fails.get(key, 0) + 1
        ttl = (30 * 60 if known else 6 * 3600) if why == "nopath" else min(6 * 3600, 600 * 2 ** (fails[key] - 1))
        self.mem.record("blocked", kind="shore", key=key, ttl=ttl)
        mine[key] = time.time() + ttl
        self.log(f"cannot reach the shore at {shore} ({why}); blocked for {ttl // 60} min, trying the next")
        self.ev("shore_nopath", shore=list(shore), block_min=ttl // 60, known=known, how=why)
        self.cur_shore = None
        return True

    # ---- a place to stand (fishspot.py): a reachable tile with water in range, not the water's edge --------------------------------------------------------

    def fish_goal(self, shore):
        """(x, y) of a reachable walkable tile within 3 tiles of the shore point; False when none can be walked to from here; None where there is no map data (the old walk)."""
        import fishspot
        key = f"{shore[0]},{shore[1]}"
        cache = self.__dict__.setdefault("_fish_goal", {})
        hit = cache.get(key)
        if hit and time.time() - hit[1] < 1800:
            return hit[0]
        res = fishspot.stand_for(shore, (self.c.x, self.c.y))
        cache[key] = (res, time.time())
        if res is not None:
            self.ev("fish_stand", shore=list(shore), stand=list(res) if res else None)
        return res

    def fish_ready(self, shore, goal):
        """At the place to fish: within 2 tiles of the stand tile (or, without map data, within 4 of the shore point), or standing where water is in range after a walk that ended short."""
        here = (self.c.x, self.c.y)
        if goal:
            if max(abs(here[0] - goal[0]), abs(here[1] - goal[1])) <= 2:
                return True
        elif max(abs(here[0] - shore[0]), abs(here[1] - shore[1])) <= 4:
            return True
        h = self.facts.get("fish_here")
        return bool(h and h["shore"] == f"{shore[0]},{shore[1]}" and time.time() - h["t"] < 1200 and max(abs(here[0] - h["xy"][0]), abs(here[1] - h["xy"][1])) <= 3)

    def fish_from_here(self, shore):
        """A walk to the shore ended short: is there water in range of where the bot stands (a bank that is not fished out)? Then it fishes from here."""
        import fishspot
        spot = fishspot.nearest_water(self.c.x, self.c.y, fishspot.CAST_RANGE, lambda x, y: self.mem.usable("fish", self.bank_of(x, y)))
        if spot is None:
            return False
        self.facts["fish_here"] = {"shore": f"{shore[0]},{shore[1]}", "xy": [self.c.x, self.c.y], "t": time.time()}
        self.ev("fish_stand", shore=list(shore), stand=[self.c.x, self.c.y], how="here")
        return True

    def r_fish(self):
        if self.threats(8) or self.hp_pct() < 50:
            return False
        if self.c.weight > self.c.max_weight * 0.9:
            return False
        # one fisher to a shore spot (three once fished side by side, and with water on one side and each other on the rest none could step
        # away): the nearest shore that is not blocked, fished out, crowded or deadly
        others = [m for m in self.c.mobiles(within=24) if m.name and m.name.startswith("Bot") and m.name != self.name]
        mine = self.facts.setdefault("shore_block", {})       # this bot's own blocks count at once (the shared memory is re-read every 20 s)

        def ok(sh):
            key_ = f"{sh[0]},{sh[1]}"
            return (mine.get(key_, 0) < time.time() and self.mem.usable("shore", key_) and self.mem.usable("fish", self.bank_of(*sh))
                    and not any(max(abs(m.x - sh[0]), abs(m.y - sh[1])) <= 3 for m in others)
                    and not self.gather_danger(cell_of(*sh)))
        if self.feature("fisher_stay"):
            if not self.pick_shore(others, mine):
                return False
        elif self.cur_shore is None or not ok(self.cur_shore):
            cands = [tuple(sh[:2]) for sh in self.shores() if ok(tuple(sh[:2]))]
            if not cands:
                # every shore taken, crowded or blocked: the old loop came back round to the one that had just failed (BotFisherA tried
                # 1447,1772 75 times a minute for twelve minutes)
                self.activity = "every shore is taken"
                return False
            self.cur_shore = min(cands, key=lambda sh: abs(sh[0] - self.c.x) + abs(sh[1] - self.c.y))
            self.water = None
        shore = self.cur_shore
        key = f"{shore[0]},{shore[1]}"
        self.mem.record("claim", kind="shore", key=key, ttl=300)
        goal = self.fish_goal(shore)
        if goal is False:
            ttl = 6 * 3600                                # no tile near this shore point can be walked to from here: do not walk at it
            self.mem.record("blocked", kind="shore", key=key, ttl=ttl)
            mine[key] = time.time() + ttl
            self.ev("shore_nopath", shore=list(shore), block_min=ttl // 60, known=self.shore_known(key), how="no_stand")
            self.cur_shore = None
            return True
        if not self.fish_ready(shore, goal):
            self.activity = "walking to the water"
            if self.feature("fisher_stay"):
                return self.stay_walk(shore, key, mine, goal)
            if not (self.travel(*goal, near=2) if goal else self.travel(*shore, near=4)) and not self.fish_from_here(shore):      # a stand tile, else the water's edge
                fails = self.facts.setdefault("shore_fails", {})
                fails[key] = fails.get(key, 0) + 1
                ttl = min(6 * 3600, 600 * 2 ** (fails[key] - 1))        # 10 minutes, doubling, up to 6 hours
                self.mem.record("blocked", kind="shore", key=key, ttl=ttl)
                mine[key] = time.time() + ttl
                self.log(f"cannot reach the shore at {shore}; blocked for {ttl // 60} min, trying the next")
                self.ev("shore_nopath", shore=list(shore), block_min=ttl // 60, known=self.shore_known(key), how="blocked")
                self.cur_shore = None
            return True
        if self.water is None:
            self.water = self.find_water()
            self.log(f"water tile: {self.water}")
            if self.water is None:
                self.note("fish", "Every water tile in reach of this shore is fished out; the fisherman has to walk along the shore.", key="nowater")
                self.mem.record("blocked", kind="shore", key=key, ttl=1200)     # as long as a fished-out bank (BotFisherA re-tried every 2 s)
                mine[key] = time.time() + 1200
                self.cur_shore = None
                return True
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
                if "cannot be seen" in l:
                    bad = self.facts.setdefault("water_unseen", {})
                    bad[f"{x},{y}"] = time.time() + 1800                 # cast at water it cannot see: another tile (it tried one 90 times)
                    self.log(f"the water at {x},{y} cannot be seen from here: another tile")
                    self.water = None
                    deadline = 0
                    break
                if "pull out" in l:
                    self.catches += 1
                    self.work += 1
                    self.mem.record("res", kind="fish", key=self.bank_of(x, y), ok=True)
                    self.shore_caught(shore)
                    self.note("fish", f"A catch reads: {l[:90]}", key="catchmsg")
                if "not be biting" in l or "don't seem to be biting" in l:
                    self.mem.record("res", kind="fish", key=self.bank_of(x, y), ok=False, reason="the fish are not biting")
                    self.mem.record("blocked", kind="fish", key=self.bank_of(x, y), ttl=1200)
                    self.note("fish", "'The fish don't seem to be biting here.' means this patch of water is fished out for a while; the player must move along the shore (nothing says how far).", key="notbiting")
                    self.water = None
                    deadline = 0
        self.read_journal()
        return True

    def stall_switch(self, n):
        """The fisher's way out of a stall (stall.py): this shore is not paying (taken, fished out, unseeable water, heavy pack it cannot unload):
        block it for this bot for 30 minutes, forget the water tile and go to another shore, as a player moves along the coast."""
        shore = getattr(self, "cur_shore", None)
        if shore:
            self.facts.setdefault("shore_block", {})[f"{shore[0]},{shore[1]}"] = time.time() + 1800
        self.cur_shore, self.water = None, None
        self.facts.pop("water_unseen", None)
        return (f"another shore (left {shore[0]},{shore[1]} for 30 min)" if shore else "another shore"), ("r_fish",)

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
