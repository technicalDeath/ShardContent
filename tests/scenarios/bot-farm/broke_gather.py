"""A miner that can earn money when its pickaxe is gone and its purse is empty (feature "broke_plan"; patch_miner_broke.py).

BotMinerBR died with about 674 gold, came back with no pickaxe and no gold, and MinerBot has no fallback: r_retool walked to the Tinker every 2 minutes with nothing to pay with ("buying a
pickaxe" forever), and r_mine returned False with no pickaxe. CrafterBot's broke_plan (patch_crafter_broke, _v2) solved the same for crafters; this is the same plan for a MinerBot, kept in its
own class so a miner without the feature runs exactly the old code:

  class BrokeMinerBot(HunterBot)   chosen by miner.main() when the bot has the feature "broke_plan" (the class is picked at the brain's start). It is a HunterBot like CrafterBot is, so it
                                   has the fighting rules a coin hunt needs; its own rules are MinerBot's (r_mine, r_sell, r_idle, pick, mountains, stand_near are MinerBot's functions).
  RULES                            MinerBot's, with r_earn between r_mine and r_idle.
  r_retool                         the pickaxe's price is the cheapest shelf price in the shared memory (else 20); gold + bank under it: no walk, retool_block_until = now + 15 min (kept across
                                   a brain restart; it lifts as soon as the funds cover the price); funds enough: the bank is visited for the shortfall, then the shop; a sold-out shelf blocks 5 min.
  r_earn                           when there is no pickaxe and the funds do not cover one (or with a pickaxe but nowhere to mine and under 60 gold): (1) sell scraps (pack items a known shop buys, never
                                   tools, bandages, potions, runes; ingots too when toolless and short), (2) hunt for coins: only kinds that pay by the shared memory (loot gold per kill, 0 for
                                   a kind with 6+ fights and no loot), on the earn ground with the best looted gold within 150 tiles of home (outside the town core, not dangerous - the danger map filters
                                   it -, not a camp), a spot with nothing to fight for 2 minutes is left for 15.
Nothing names a town: prices, buyers, kinds, ground and danger come from the shared memory and the home table.
"""
from __future__ import annotations

import time

from hunter import HunterBot
from memory import cell_of
from miner import MinerBot
from market import MarketMixin, MinerMarket


class BrokeMinerBot(HunterBot):
    RULES = ["r_dead", "r_corpse", "r_gear", "r_cure", "r_flee", "r_evade", "r_market", "r_retool", "r_sell", "r_bank", "r_mine", "r_earn", "r_idle"]
    KEEP = MinerBot.KEEP
    SHED_LAST = MinerBot.SHED_LAST                        # the product (ingots, ore) is dropped last when the pack is too heavy (drop_excess)
    LOOT_GEAR = ()                                        # a miner hunting vermin for coins does not carry weapons home to sell
    CARVE = False
    LOOT_MATERIALS = False

    # MinerBot's own functions, unchanged
    pick = MinerBot.pick
    ore = MinerBot.ore
    mountains = MinerBot.mountains
    stand_near = MinerBot.stand_near
    INGOT_BUYER = MinerBot.INGOT_BUYER
    r_sell = MinerBot.r_sell
    r_mine = MinerBot.r_mine
    r_idle = MinerBot.r_idle
    r_market = MarketMixin.r_market                        # the market (post, match, deals): HunterBot's own older r_market is not it
    mkt_supply = MinerMarket.mkt_supply                    # the ingots in the pack are the offer
    mkt_make_supply = MinerMarket.mkt_make_supply          # smelt ahead when a smith wants ingots
    stall_switch = MinerBot.stall_switch                   # the wider ore search of a stalled miner (stall.py asks the class for it)

    PERSIST = HunterBot.PERSIST + ("retool_block_until", "retool_soldout_until", "scrap_try_at")
    TOOL_WORD = "pickaxe"
    TOOL_PRICE_GUESS = 20                                 # a pickaxe no bot has seen on a shelf
    TOOL_RESERVE = 3
    SCRAP_PROTECT = ("gold", "book", "bandage", "potion", "recall", "rune", "bedroll", "kindling", "backpack", "bag", "candle", "scroll", "tongs", "hammer", "tool", "kit", "saw",
                     "sewing", "scissors", "pickaxe", "shovel", "hatchet", "dagger", "fishing", "mortar", "gem", "ruby", "sapphire", "emerald", "diamond", "amber", "citrine",
                     "tourmaline", "star ")
    EARN_REACH = 150
    EARN_MIN_GOLD = 8
    EARN_STAND = 120
    EARN_EMPTY = 900
    _coin_only = False

    def __init__(self, name, profession):
        super().__init__(name, profession)
        self.spot = None                                  # MinerBot's chosen mountain spot
        self.dug = 0
        self.blocked = {}
        self.i = 0

    # ---- the tool --------------------------------------------------------------------------------------------------------------------------

    def tool_price(self):
        prices = [p for p, xy, item, qty in self.mem.vendor_selling(self.TOOL_WORD) if p > 0]
        return min(prices) if prices else None

    def funds(self):
        return self.c.gold + max(0, self.facts.get("bank_balance", 0))

    def r_retool(self):
        if not self.feature("broke_plan"):
            return MinerBot.r_retool(self)
        self.c.open_backpack()
        if self.pick() or self.threats(10):
            return False
        now = time.time()
        price = self.tool_price() or self.TOOL_PRICE_GUESS
        funds = self.funds()
        if now < self.facts.get("retool_soldout_until", 0) or now - self.facts.get("retool_at", 0) < 120:
            return False
        if funds < price:
            if now >= self.facts.get("retool_block_until", 0):
                self.facts["retool_block_until"] = now + 900
                self.log(f"no pickaxe and {funds} gold in all (pack {self.c.gold}, bank {self.facts.get('bank_balance', 0)}) against {price}: the shop can wait, earning first")
                self.dlog("choice", what="skip the retool", why=f"gold {self.c.gold} + bank {self.facts.get('bank_balance', 0)} under the {price} gold a pickaxe costs; not again for 15 min")
                self.note("money", f"The {self.pname} could not pay for a new pickaxe ({price} gold), so it earns first instead of walking to the shop again and again.", key="retoolwait")
            return False
        self.facts["retool_at"] = now
        self.activity = "buying a pickaxe"
        self.note("mine", "The pickaxe wore out after a short while of mining; no warning came before the last swing, and the player must find who sells another.", key="pickworn")
        if self.c.gold < price + self.TOOL_RESERVE and self.facts.get("bank_balance", 0) > 0:
            self.visit_bank("tool", withdraw=min(self.facts["bank_balance"], price + self.TOOL_RESERVE - self.c.gold + 10))
        got = self.shop_at(self.where1(("tinker",), item="pickaxe"), {self.TOOL_WORD: 1}, budget=max(self.c.gold - 1, 0))
        self.note("shop", f"Pickaxe bought: {got}", key="newpick")
        if not got:
            self.facts["retool_soldout_until"] = time.time() + 300 if self.c.gold >= price else 0
            if self.c.gold < price:
                self.facts["retool_block_until"] = time.time() + 900
        return True

    # ---- earning ---------------------------------------------------------------------------------------------------------------------------

    def coin_value(self, kind):
        """Gold a kill of this kind pays, from every bot's loot over the fights seen; 0.0 for a kind fought 6+ times that never paid, None when not measured."""
        w = self.mem.state["world"]
        kl = w["kloot"]
        fights = sum(g["n"] for g in w["fights"].get(kind, {}).values()) if kind in w["fights"] else 0
        hit = kl.get(kind) or kl.get(kind + "s")
        if hit and hit["n"] >= 2:
            return hit["gold"] / max(fights, hit["n"])
        if any(k != kind and (k.startswith(kind) or kind.startswith(k)) for k in kl):
            return None
        return 0.0 if fights >= 6 and not hit else None

    def prey(self, within=9):
        ps = super().prey(within)
        if not self._coin_only:
            return ps
        keep = []
        for m in ps:
            v = self.coin_value(self.mkey(m))
            if m.distance <= 1 or v is None or v >= 1.0:
                keep.append(m)
            else:
                skipped = self.facts.setdefault("coin_skipped", set())
                if self.mkey(m) not in skipped:
                    skipped.add(self.mkey(m))
                    self.dlog("choice", what=f"skip {self.mkey(m)} for coins", why=f"{v:.1f} gold a kill in the shared memory")
        return keep

    def scraps(self):
        """[(name, price, xy, amount)] of pack items some known shop buys at a price; ingots only when the pickaxe is gone and the funds are short."""
        out = []
        toolless = not self.pick()
        for it in self.c.backpack:
            low = it.name.lower()
            is_ingot = "ingot" in low
            if any(w in low for w in self.SCRAP_PROTECT) or (is_ingot and not (toolless and self.funds() < (self.tool_price() or self.TOOL_PRICE_GUESS))):
                continue
            offers = [(p, xy) for p, xy, item in self.mem.vendor_buying(low) if p > 0 and item in (low, low + "s")]
            if offers:
                p, xy = offers[0]
                out.append((low, p, tuple(int(v) for v in xy.split(",")), it.amount or 1))
        return out

    def earn_candidates(self):
        home = self.home_centre()
        core = self.home_core() if getattr(self, "home_core", None) else (home[0] - 60, home[1] - 60, home[0] + 60, home[1] + 60)
        cells = self.mem.state["world"]["cells"]
        cand = {}
        for x, y in self.earn_spots():
            cand[(x, y)] = cells[cell_of(x, y)]["gold"] if cell_of(x, y) in cells else 0.0
        for cell, c in cells.items():
            if c["gold"] < self.EARN_MIN_GOLD:
                continue
            cx, cy = (int(v) for v in cell.split(","))
            x, y = cx + 20, cy + 20
            if max(abs(x - home[0]), abs(y - home[1])) > self.EARN_REACH or (core[0] <= x <= core[2] and core[1] <= y <= core[3]):
                continue
            if self.mem.dangerous_cell(cell) or self.mem.camp_cell(cell):
                continue
            cand[(x, y)] = max(cand.get((x, y), 0.0), c["gold"])
        empty = self.facts.get("earn_empty", {})
        now = time.time()
        out = []
        for (x, y), g in cand.items():
            if self.near_death_spot(x, y, 40) or empty.get((x, y), 0) > now or self.mem.dangerous_cell(cell_of(x, y)):
                continue
            out.append((x, y, g - max(abs(x - self.c.x), abs(y - self.c.y)) / 30.0))
        return out

    def earn_ground(self):
        cand = self.earn_candidates()
        if not cand:
            self.facts.pop("earn_empty", None)
            spots = [s for s in self.earn_spots() if not self.near_death_spot(*s, 40) and not self.mem.dangerous_cell(cell_of(*s))] or [self.home_centre()]
            return spots[int(time.time() // 240) % len(spots)]
        best = max(cand, key=lambda c: c[2])
        if best[2] > 0:
            return best[0], best[1]
        pool = sorted(cand, key=lambda c: (c[0], c[1]))
        return pool[int(time.time() // 240) % len(pool)][:2]

    def r_earn(self):
        """No pickaxe (or no place to dig) and not enough money: sell scraps, then hunt the vermin that pay."""
        if not self.feature("broke_plan") or self.threats(10) or self.hp_pct() < 60 or self.c.weight > self.c.max_weight * 0.8:
            return False
        now = time.time()
        if self.pick():
            if self.c.gold >= 60 or self.facts.get("bank_balance", 0) >= 60:
                return False
        elif self.funds() >= (self.tool_price() or self.TOOL_PRICE_GUESS) + self.TOOL_RESERVE:
            return False                                  # r_retool buys it (its own rule comes first)
        scraps = self.scraps()
        if scraps and now - self.facts.get("scrap_try_at", 0) > 900:
            self.facts["scrap_try_at"] = now
            worth = sum(p * n for _, p, _, n in scraps)
            self.activity = "selling scraps"
            self.dlog("choice", what="sell scraps", why=f"{[(n, a, p) for n, p, _, a in scraps]} are bought for about {worth} gold")
            gold0 = self.c.gold
            for xy in sorted({s[2] for s in scraps}, key=lambda xy: -sum(p * n for _, p, x, n in scraps if x == xy))[:2]:
                self.sell_items(xy, [s[0] for s in scraps if s[2] == xy])
            self.log(f"sold scraps: gold {gold0} -> {self.c.gold}")
            return True
        self.note("money", f"The {self.pname} has no money for {'a new pickaxe' if not self.pick() else 'anything'} and nothing to sell, so it hunts the vermin that pay (rats), not cats and birds.", key="earnhunt")
        self.activity = "broke: hunting for coins"
        self._coin_only = True
        try:
            for rule in ("r_loot", "r_heal", "r_fight", "r_hunt"):
                if getattr(HunterBot, rule)(self):
                    self.facts.pop("earn_at", None)
                    return True
        finally:
            self._coin_only = False
        x, y = self.earn_ground()
        self.activity = f"broke: looking for vermin toward {x},{y}"
        at = self.facts.get("earn_at")
        if max(abs(self.c.x - x), abs(self.c.y - y)) <= 6:
            if not at or at[0] != (x, y):
                self.facts["earn_at"] = ((x, y), now)
            elif now - at[1] > self.EARN_STAND:
                self.facts.setdefault("earn_empty", {})[(x, y)] = now + self.EARN_EMPTY
                self.facts.pop("earn_at", None)
                self.dlog("choice", what="leave the earn spot", why=f"{int(now - at[1])} s at {x},{y} with nothing to fight; not again for {self.EARN_EMPTY // 60} min")
        else:
            self.facts.pop("earn_at", None)
        self.c.goto(x, y).wait(timeout=5)
        return True
