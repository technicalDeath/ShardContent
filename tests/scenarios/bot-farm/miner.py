"""Prospector: walks to the hills north of Britain, finds a mountain tile it can reach, mines it (the shard repeats the dig by itself), sells ore to the Miner
in town when it gets heavy, banks the money, and chops a tree now and then with its hatchet.

    python miner.py --name BotMinerA --profession 22 --for 3600
"""
from __future__ import annotations

import items  # noqa: E402  (the shared item table)
import argparse
import json
import os
import re
import sys
import time

from bot_common import BotBase, load_features, HOME_DEATHS
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
from wear import GathererArmor  # noqa: E402  (leather and studded armour, feature gather_armor)

REPEAT_GAP = 6.0     # s after the last dig line with no new one: the harvest repeat has stopped, so dig again. A dig takes 1.6-2.5 s (Mining.cs EffectDelay 1.6,
                     # the line came 0.9 s after the target) and the journal is read every 2.5 s; BotMinerAR waited out the whole 40 s after every single dig
                     # (85 digs in an hour, BotMinerBR 335) when the repeat stopped after each one (2026-10-31)
SPOT_BAND = 150       # tiles: dig spots within one band count as equally near and the risk decides among them (the risk ranking of nearby hills, test_gather_risk,
                     # spots 40-120 apart); past it the walk decides: about 25 s a band at the bots' measured 0.14-0.18 s a tile running
SHOVEL_CARRY = 8     # shovels bought at a time: 5 stones each, 40 in all, about a tenth of a 390-stone limit, for some 400 digs; with the harvest repeat at a
                     # dig every 0.9 s, 50 uses last under a minute, and the miners spent 9-20% of their time on tool trips (2026-10-31)
PICK_CARRY = 3       # pickaxes bought at a time: 50 uses each (Pickaxe.cs), about 10 minutes of mining, and the trip back from the western range took
                     # about 5 minutes (283 tiles, 2026-10-31), some 55 gold of a miner's hour against 25 gold and 11 stones for a spare
DIG_REACH = 200       # r_mine digs within this many tiles of the work centre (350 while mine_wide); a module name, as the smith runs MinerBot.r_mine too
FAR_REACH = 460       # ... and up to this far where the walk passes far_spot_ok: the safe banks of the range west of Britain are 445 tiles from its centre


def has_stand(t):
    """The walk map has a walkable tile in RING of the mountain tile (True without map data). The six Britain tiles with none (1455,1510, 1450,1525,
    1511,1503, 1736,1597, 1755,1584, 1755,1583) gave no ore in about 490 tries over the farm's life (shared memory, 2026-10-30): 'could not stand near'."""
    try:
        import walkroute
        walk = walkroute.get()
    except Exception:
        return True
    return any(walk.walkable(t[0] + dx, t[1] + dy) for dx, dy in RING)


from stock import PotionStock  # noqa: E402
from packy import PackAnimalMixin  # noqa: E402

class MinerBot(MinerMarket, PotionStock, PackAnimalMixin, GathererArmor, BotBase):
    PERSIST = BotBase.PERSIST + ("packy", "packy_lost_at", "packy_try_at", "horse_trap", "horse_trap_seen")      # the pack horse (and the forges that shut it in) outlive a brain restart (packy.py)
    HOME_DANGER_MOVES = True                              # a home that keeps killing it is left (patch_home_town)
    GATHER_ROAMS = True                                   # its work moves to another town when the ground near home is used up (patch_step3_fixes)
    SHED_LAST = ("ingot", "ore")                          # the product: dropped only when nothing else is left (drop_excess)
    RULES = ["r_dead", "r_corpse", "r_gear", "r_cure", "r_flee", "r_hide", "r_evade", "r_heal", "r_packy", "r_market", "r_stock", "r_upgrade", "r_retool", "r_sell", "r_bank", "r_mine", "r_idle"]
    # (r_stock: heal and cure potions, stock.PotionStock. A miner has no Healing and no potions, and after a hit it stood fleeing from rabbits and giant
    # rats at a third of its hit points for minutes, 32% of BotMinerAR's hour idle; r_flee drinks a Heal potion when it has one, 2026-10-31)
    KEEP = ("book", "gold", "candle", "bag", "scroll", "potion", "recall", "scissors", "bedroll", "kindling", "bandage", "pickaxe", "hatchet", "shovel", "dagger", "gem", "ruby", "sapphire", "emerald",
            "diamond", "amber", "citrine", "tourmaline", "star ", "tongs", "smith's hammer") + items.GOODS_WORDS          # goods a shop buys are never banked (items.py); tongs: minersmith.py

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
            m = [tuple(t[:4]) for t in geo.regional("mountains", self.home(), MOUNTAIN) if has_stand(t)]
            if geo.is_britain(self.home()):
                # the range west of Britain (the owner's pointer, 2026-10-30): its banks from the map, beyond the old hand list; far_spot_ok() decides each
                banks = {(t[0] // 8, t[1] // 8) for t in m}
                try:
                    import make_mountains
                    c = geo.centre_of(self.home())
                    west = make_mountains.build(c[0] - FAR_REACH, c[1] - FAR_REACH // 2, c[0] - DIG_REACH, c[1] + FAR_REACH // 2, centre=c)
                except Exception:
                    west = []
                m += [tuple(t[:4]) for t in west if has_stand(t) and (t[0] // 8, t[1] // 8) not in banks]
            self._mountain_list = m
        return m

    FAR_PLANS = 3              # new route plans a far_cands call may make (about 0.7 s each); with the mountain feet (make_mountains.FOOT) there are about
    FAR_FOUND = 6              # 290 far banks round Britain, and testing them all froze the simulator's miners for minutes; stop once this many pass

    def far_cands(self, ok_far):
        """The far banks ok_far accepts, nearest the bot first, planning at most FAR_PLANS new routes a call (far_spot_ok caches each for 30 min)."""
        cache = self.__dict__.setdefault("_far_ok", {})
        rows = sorted(self.mountains(), key=lambda t: max(abs(t[0] - self.c.x), abs(t[1] - self.c.y)))
        out, plans, t_call = [], 0, time.time()
        for t in rows:
            key = (t[0] // 8, t[1] // 8)
            hit = cache.get(key)
            if plans >= self.FAR_PLANS and not (hit is not None and t_call - hit[0] < 1800):
                continue                                     # (cached answers still count; new plans wait for the next call)
            if ok_far(t):
                out.append(t)
            if cache.get(key) is not hit:
                plans += 1                                   # far_spot_ok planned this one now (a new cache entry)
            if len(out) >= self.FAR_FOUND:
                break
        return out

    def far_spot_ok(self, t):
        """A bank past DIG_REACH (up to FAR_REACH): the walk there from the work centre, planned as a far walk is, must pass route_danger (the gatherer rule
        and 14 days of deaths), as a move of home must. Cached per bank for 30 min (the deaths and the danger map change)."""
        cache = self.__dict__.setdefault("_far_ok", {})
        key = (t[0] // 8, t[1] // 8)
        hit = cache.get(key)
        if hit and time.time() - hit[0] < 1800:
            return hit[1]
        ok = False
        try:
            import walkroute
            r = walkroute.get().plan(tuple(self.work_centre()), (t[0], t[1] + 2), self.far_penalty() if hasattr(self, "far_penalty") else None)
            ok = r is not None and not self.route_danger(r)
        except Exception:
            ok = False
        cache[key] = (time.time(), ok)
        return ok

    def horse_unsafe(self, t):
        """A dig spot where a monster that attacks on sight could reach the pack horse: within an aggressive spawner's home range plus task_core.PULL_CLEAR
        (its creatures notice a mobile that far beyond their range). Both horses were lost in the western hills, at 1190,1435 and 1173,1358, each with
        700-800 stones of ore, while the miner evaded and the horse fought on (2026-11-01): a miner with a pack animal works quieter ground."""
        cache = self.__dict__.setdefault("_horse_unsafe", {})
        key = (t[0], t[1])
        if key not in cache:
            import spots as _sp
            import task_core
            cache[key] = any(max(abs(o["x"] - t[0]), abs(o["y"] - t[1])) <= max(int(o.get("home") or 10), 1) + task_core.PULL_CLEAR
                             and any(task_core.aggressive(k) for k in o["kinds"]) for o in _sp.spawner_spots())
        return cache[key]

    def roam_spots(self, kind, town, spots):
        """The spots a move to `town` would really give: the ones r_mine digs (within DIG_REACH of the centre, with a place to stand). Vesper had 8
        mountain tiles within 300, none within 200, and the miners moved there and could never dig (2026-10-21)."""
        c = town["centre"]
        return [s for s in spots if max(abs(s[0] - c[0]), abs(s[1] - c[1])) <= DIG_REACH and has_stand(s)]

    def ore(self):
        return sum((i.amount or 1) for i in self.c.backpack if "ore" in i.name.lower() or "ingot" in i.name.lower())

    def pick(self):
        return next((i for i in self.c.backpack if i.name.lower() in ("pickaxe", "shovel")), None) or next((i for i in self.c.equipped if "pickaxe" in i.name.lower()), None)

    @property
    def INGOT_BUYER(self):                               # a blacksmith (buys iron ingots at 4 gp)
        return self.where1(("smith",))

    def buy_dig_tools(self, shop, budget):
        """Shovels (SHOVEL_CARRY), else pickaxes (PICK_CARRY) at that shop: the same 50 uses for 12 gold and 5 stones against 25 and 11 (Shovel.cs,
        Pickaxe.cs; SBTinker and SBMiner sell both). Returns what was bought."""
        got = self.shop_at(shop, {"shovel": SHOVEL_CARRY}, budget=budget)
        if not got:
            got = self.shop_at(shop, {"pickaxe": PICK_CARRY}, budget=budget)
        return got

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
        got = self.buy_dig_tools(self.where1(("tinker",), item="shovel"), max(self.c.gold - 5, 0))
        self.note("shop", f"Pickaxe bought: {got}", key="newpick")
        return True

    def r_sell(self):
        heavy = self.c.weight > self.c.max_weight * 0.8
        # every spot taken or worked out: the banks refill 10-20 min later (Mining.cs MinRespawn/MaxRespawn) and the forge and smith are about 60 tiles
        # from the hills, so the load is smelted and sold in the wait instead of after it (three miners stood idle beside 300 stones of ore, 2026-10-30)
        waiting = time.time() - self.facts.get("spots_out_at", 0) < 90 and self.ore() > 0
        if not (heavy or waiting) or self.threats(8) or time.time() - self.facts.get("sold_at", 0) < 240:
            return False
        if heavy and not waiting and self.packy_load():
            return True                                   # the load went onto the pack horse: dig on (packy.py)
        self.facts["sold_at"] = time.time()
        if self.ore_piles(smeltable=True):
            done = self.smelt()
            if done is None:
                self.note("sell", "A miner with a full load of ore could not reach the forge; no NPC buys raw ore, so the load is worth nothing until smelted.", key="noforgeload")
            for _ in range(8):                            # the horse's ore, a load at a time (it cannot be smelted in the horse's pack)
                if done is None or not self.packy_unload():
                    break
                done = self.smelt()
        if self.mkt_hold("iron ingot"):
            self.activity = "keeping ingots for a smith"          # a smith wants them at more than the NPC pays: r_market sells them
            return True
        made = []
        if self.feature("miner_smith"):
            try:
                import minersmith                         # (here, not at the top: minersmith imports crafter, which imports this module)
                made = minersmith.smith(self)             # at the anvil beside the forge: ingots into goods when that pays over selling them
            except Exception as e:
                self.log(f"miner-smith: {type(e).__name__}: {e}")
        self.activity = "selling ingots"
        buyer = self.INGOT_BUYER
        earned = self.sell_items(buyer, ("ingot",) + tuple(made))      # the goods go to the same Blacksmith (SBBlacksmith buys shields, weapons, armour)
        if made:
            minersmith.after_sale(self, buyer)
        self.note("sell", f"A Blacksmith buys the smelted ingots: {earned} gold for a load ({self.ore()} ore and ingots left).", key="ingotsell")
        if not earned:
            self.note("sell", "Raw ore sells to no NPC (the Miner buys none), and a full pack of ore brings nothing until the miner learns to smelt it at a forge.", key="orenosale")
        elif earned > 0:
            self.armor_errand()                           # in town with gold from the sale: the armour on the way (wear.py; a miner's bank trip is often skipped)
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
                    and not self.gather_danger(cell_of(t[0], t[1])) and self.cell_deaths(cell_of(t[0], t[1])) < HOME_DEATHS
                    and max(abs(t[0] - self.work_centre()[0]), abs(t[1] - self.work_centre()[1])) <= (350 if time.time() < self.facts.get("mine_wide_until", 0) else DIG_REACH))

        def ok_far(t):
            # past the near hills, only when none of those is free: each far bank's walk is planned once per 30 min (far_spot_ok), about 0.7 s a plan
            return (self.blocked.get((t[0], t[1]), 0) < time.time() and self.mem.usable("ore", f"{t[0]},{t[1]}") and not self.gather_danger(cell_of(t[0], t[1]))
                    and self.cell_deaths(cell_of(t[0], t[1])) < HOME_DEATHS and DIG_REACH < max(abs(t[0] - self.work_centre()[0]), abs(t[1] - self.work_centre()[1])) <= FAR_REACH and self.far_spot_ok(t))
        if self.spot is None or not (ok(self.spot) or ok_far(self.spot)):
            cands = [t for t in self.mountains() if ok(t)] or self.far_cands(ok_far)
            if self.facts.get("packy"):
                calm = [t for t in cands if not self.horse_unsafe(t)]
                cands = calm or cands                     # a loaded horse is kept off monster ground; with no calm spot, the usual choice
            if self.gather_roam("mountains", bool(cands)):
                return True                               # the hills near home are used up: work moves to another town (patch_gather_roam)
            if not cands:
                # every spot blocked or taken: the old loop fell through to the last one anyway (BotMineAdv kept walking to 1450,1525, which has
                # nowhere to stand); let selling, banking and idling have the tick
                self.activity = "every mining spot is taken or blocked"
                self.facts["spots_out_at"] = time.time()             # r_sell smelts and sells the load in the wait
                return False
            # nearest first in SPOT_BAND bands, the risk only between spots about as near: every candidate has passed the danger and death checks, and ranked by
            # risk first BotMinerBR walked 300-550 tiles between the western range, the south-west hills and 1722,1603 for 1-2 minutes of digging each (2026-10-31)
            self.spot = min(cands, key=lambda t: (max(abs(t[0] - self.c.x), abs(t[1] - self.c.y)) // SPOT_BAND, round(self.gather_risk(cell_of(t[0], t[1])), 1),
                                                  abs(t[0] - self.c.x) + abs(t[1] - self.c.y)))
        tx, ty, tz, g = self.spot
        if max(abs(self.c.x - tx), abs(self.c.y - ty)) > 2:
            self.activity = f"walking to the hills at {tx},{ty}"
            if not self.stand_near(tx, ty):
                # each failure doubles the wait (10 minutes, 20, 40 ... up to 6 hours): BotMineAdv walked back to 1450,1525 every ten minutes
                # for an hour and never once found a place to stand
                fails = self.facts.setdefault("stand_fails", {})
                k = f"{tx},{ty}"                                   # a string key: a tuple key never reached facts.json, so every restart began again at 10 minutes
                fails[k] = fails.get(k, 0) + 1
                ttl = min(6 * 3600, 600 * 2 ** (fails[k] - 1))
                self.blocked[(tx, ty)] = time.time() + ttl
                self.mem.record("blocked", kind="ore", key=f"{tx},{ty}", ttl=max(1800, ttl))
                self.mem.record("res", kind="ore", key=f"{tx},{ty}", ok=False, reason="no reachable standing place")
                self.log(f"could not stand near {tx},{ty} (now at {self.c.x},{self.c.y})")
                self.note("mine", "A mountain tile on the map has no reachable spot within two steps; the miner has to look for another.", key="unreachable")
                self.i += 1
                return True
        self.activity = "mining"
        self.mem.record("claim", kind="ore", key=f"{tx},{ty}", ttl=240)
        self.harvest_peace()                               # bot_common: the gather repeat stops in war mode
        self.c.events.drain()
        self.c.use(tool.serial)
        if self.c.wait_for(Event.TARGET_REQUEST, timeout=4) is None:
            self.note("mine", "Double-clicking the pickaxe raised no target cursor.", key="nocursor")
            time.sleep(2)
            return True
        self.c.call(f"targettile {tx} {ty} {tz} 0", timeout=8)
        end = time.time() + 40
        n = 0
        last = time.time()
        while time.time() < end:
            time.sleep(2.5)
            if time.time() - last > REPEAT_GAP:
                break                                         # the shard's repeat did not dig again: dig again ourselves (r_mine runs at once)
            lines = self.read_journal()
            for l in lines:
                if re.search(r"dig|ore|nothing|no metal|too far|worn|elsewhere|rock|stone", l, re.I):
                    n += 1
                    last = time.time()
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

    EVADE_SKIP = 600          # s a dig spot is left after a monster near it was walked away from
    EVADE_NEAR = 15           # tiles from the spot

    def on_evade(self, m):
        """The dig spot near the monster is left for EVADE_SKIP: kept, r_mine walked straight back to it past the same monster (10-19 runs of three or more
        evade-mine turns each in the miners' logs, 2026-10-31; a tamer died the same way)."""
        spot = getattr(self, "spot", None)
        if not spot or not hasattr(self, "blocked"):
            return
        tx, ty = spot[0], spot[1]
        if max(abs(m.x - tx), abs(m.y - ty)) <= self.EVADE_NEAR:
            self.blocked[(tx, ty)] = max(self.blocked.get((tx, ty), 0), time.time() + self.EVADE_SKIP)
            self.ev("dig_spot_evaded", spot=[tx, ty], m=self.mkey(m))
            self.spot = None

    def stall_switch(self, n):
        """The miner's way out of a stall (stall.py): every spot near is taken, worked out or blocked, so it looks for ore further out, as a
        player goes to the next hills (350 tiles from the work centre instead of 200, for 30 minutes)."""
        self.facts["mine_wide_until"] = time.time() + 1800
        self.spot = None
        return "look for ore up to 350 tiles out for 30 min (the near hills are taken or worked out)", ("r_mine",)

    def r_idle(self):
        if self.hide_practice():                          # idle and safe: Hiding practised (basics.py, skill plan)
            return True
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
