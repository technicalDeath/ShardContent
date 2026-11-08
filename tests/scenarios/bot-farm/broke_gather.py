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

from earn import EarnMixin
from packy import PackAnimalMixin
from hunter import HunterBot
from memory import cell_of
from wear import GATHER_ARMOR, GathererArmor  # noqa: E402
from miner import MinerBot
from market import MarketMixin, MinerMarket


class BrokeMinerBot(EarnMixin, PackAnimalMixin, HunterBot):
    HOME_DANGER_MOVES = True                              # a home that keeps killing it is left (patch_home_town)
    GATHER_ROAMS = True                                   # its work moves to another town when the ground near home is used up (patch_step3_fixes)
    RULES = ["r_dead", "r_corpse", "r_gear", "r_cure", "r_flee", "r_hide", "r_evade", "r_heal", "r_packy", "r_market", "r_stock", "r_upgrade", "r_retool", "r_sell", "r_bank", "r_mine", "r_earn", "r_idle"]
    KEEP = MinerBot.KEEP

    def r_flee(self):
        """Feature craft_guard: something it would hunt biting it from the next tile is fought to the end (crafter.CrafterBot.hold_fight: until it dies,
        steps off, or stops rating as a fight), as the guarded crafters do; otherwise the shared flight (BotBase.r_flee). BotMinerBR drank three Lesser
        Heals 17-20 s apart under a giant rat's teeth, stood between them (r_idle), was boxed in at 39 and died (2026-11-08 01:59-02:01)."""
        if self.feature("craft_guard"):
            th = self.threats(6)
            if th and self.hp_pct() < 90:
                biter = next((m for m in th if (getattr(m, "distance", 9) or 9) <= 1 and getattr(m, "in_war_mode", False) and self.is_prey(m)), None)
                if biter is not None:
                    self.activity = f"fighting back at {biter.name}"
                    return self.hold_fight(biter)
        from bot_common import BotBase
        return BotBase.r_flee(self)

    def hold_fight(self, m):
        import crafter
        return crafter.CrafterBot.hold_fight(self, m)

    def hold_cap(self, m):
        import crafter
        return crafter.CrafterBot.hold_cap(self, m)

    def hold_worth(self, m):
        import crafter
        return crafter.CrafterBot.hold_worth(self, m)

    HOLD_S, HOLD_TTK, HOLD_MAX_S, HOLD_STEP_S, HOLD_CHASE = 45, 1.5, 90, 0.8, 2       # crafter.CrafterBot's own (hold_fight reads them on self)

    def earn_tool(self):
        return self.pick()                                # the broke miner's tool is its pickaxe (earn.py)

    def earn_material(self, low):
        return "ingot" in low
    SHED_LAST = MinerBot.SHED_LAST                        # the product (ingots, ore) is dropped last when the pack is too heavy (drop_excess)
    LOOT_GEAR = ()                                        # a miner hunting vermin for coins does not carry weapons home to sell
    CARVE = False
    LOOT_MATERIALS = False

    # MinerBot's own functions, unchanged
    pick = MinerBot.pick
    ore = MinerBot.ore
    mountains = MinerBot.mountains
    far_cands = MinerBot.far_cands
    stock_list = MinerBot.stock_list                      # a miner's potions (stock.PotionStock), not a fighter's list with ammunition
    buy_dig_tools = MinerBot.buy_dig_tools                # shovels first (miner.SHOVEL_CARRY)
    FAR_PLANS, FAR_FOUND = MinerBot.FAR_PLANS, MinerBot.FAR_FOUND
    on_evade, EVADE_SKIP, EVADE_NEAR = MinerBot.on_evade, MinerBot.EVADE_SKIP, MinerBot.EVADE_NEAR     # a dig spot near a monster walked away from is left
    # the gatherer's light armour (wear.py, feature gather_armor): the miners run as this class, so MinerBot.r_sell's errand call found no armor_errand
    # and raised at every sale (2026-11-01); HunterBot's "weapon first" is set aside for the call (a miner's tool is no weapon)
    ARMOR_BUY = GATHER_ARMOR
    SHOP_FROM, ERRAND_PIECES = GathererArmor.SHOP_FROM, GathererArmor.ERRAND_PIECES
    armor_errand, in_town_now = GathererArmor.armor_errand, GathererArmor.in_town_now

    def r_upgrade(self):
        if not self.feature("gather_armor"):
            return False
        self.__dict__["weapon_state"] = lambda: "ok"
        try:
            return GathererArmor.r_upgrade(self)
        finally:
            self.__dict__.pop("weapon_state", None)

    far_spot_ok = MinerBot.far_spot_ok                    # a bank past miner.DIG_REACH needs a safe walk (the range west of Britain)
    horse_unsafe = MinerBot.horse_unsafe                  # a horse miner keeps off monster ground (miner.py)
    roam_spots = MinerBot.roam_spots                      # a move counts only the hills it can dig (miner.DIG_REACH, a place to stand)
    stand_near = MinerBot.stand_near
    INGOT_BUYER = MinerBot.INGOT_BUYER
    r_sell = MinerBot.r_sell
    r_mine = MinerBot.r_mine
    r_idle = MinerBot.r_idle
    r_market = MarketMixin.r_market                        # the market (post, match, deals): HunterBot's own older r_market is not it
    mkt_supply = MinerMarket.mkt_supply                    # the ingots in the pack are the offer
    mkt_make_supply = MinerMarket.mkt_make_supply          # smelt ahead when a smith wants ingots
    stall_switch = MinerBot.stall_switch                   # the wider ore search of a stalled miner (stall.py asks the class for it)

    PERSIST = HunterBot.PERSIST + ("retool_block_until", "retool_soldout_until", "scrap_try_at", "packy", "packy_lost_at", "packy_try_at", "horse_trap", "horse_trap_seen")
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
        """The cheapest shelf price of a dig tool: a shovel (12 at the Tinker) or a pickaxe."""
        prices = [p for w in ("shovel", self.TOOL_WORD) for p, xy, item, qty in self.mem.vendor_selling(w) if p > 0]
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
        import miner as _miner
        shovels = any(p > 0 for p, xy, item, qty in self.mem.vendor_selling("shovel"))
        want = price * (_miner.SHOVEL_CARRY if shovels else _miner.PICK_CARRY) + self.TOOL_RESERVE      # a set of tools (miner.SHOVEL_CARRY / PICK_CARRY), not one: a tool lasts under a minute
        if self.c.gold < want and self.facts.get("bank_balance", 0) > 0:     # at the harvest repeat's pace (2026-10-31)
            self.visit_bank("tool", withdraw=min(self.facts["bank_balance"], want - self.c.gold + 10))
        got = self.buy_dig_tools(self.where1(("tinker",), item="shovel"), max(self.c.gold - 1, 0))
        self.note("shop", f"Pickaxe bought: {got}", key="newpick")
        if not got:
            self.facts["retool_soldout_until"] = time.time() + 300 if self.c.gold >= price else 0
            if self.c.gold < price:
                self.facts["retool_block_until"] = time.time() + 900
        return True

    # ---- earning ---------------------------------------------------------------------------------------------------------------------------

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
