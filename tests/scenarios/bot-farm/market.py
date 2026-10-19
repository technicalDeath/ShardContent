"""A market between the farm's bots: quantity offers and wants, priced against the NPCs, settled in a secure trade at the bank (G4 economy; Watcher's item 2026-10-17; the Helper).
Mixin for BotBase, written into the bot-farm folder by patch_market.py. Behind the feature "trade".

Why: the three smiths sat idle with 0-8 ingots (and 400-2400 gold in the bank) while the miners smelted ingots and sold them to the NPC Blacksmith at 4 gold; no shop sells
ingots at all. The old market (crafters post one-piece offers, fighters book a deal) had no wants, no quantity, and its offers were things nobody wanted.

The rules (no coordinates, no per-item numbers: the same code prices any item in ITEMS):
 * seller floor   = the best price an NPC pays for the item + 25% (at least +1 gold);
 * buyer ceiling  = one gold under the cheapest NPC price for the item when an NPC sells it; when nobody sells it, twice what an NPC pays (never below the floor);
 * the offer asks the floor + 20% (at least +1), inside floor..ceiling. A deal is struck at the offer's unit price when it is within the buyer's ceiling.
 * offers / wants live in shared memory (mkt kind offer / want, qty and unit price in gold, the meeting spot of the poster's home), fresh for 15 minutes, re-posted every 5.
   Either side can notice the match: the buyer takes the cheapest offer under its ceiling, the seller takes the best want at or above its floor; the one who notices books
   the deal (mkt kind deal: seller, buyer, item, qty, unit, price = qty * unit, meet).
 * DEAL = meet at the bank spot (places.meet_spot), the seller drops the agreed quantity on the buyer (opens the secure-trade window), the buyer puts the gold into its box, both
   accept once the other box holds what was agreed; the result is checked by counts (seller's gold up by the price, buyer's item count up by the quantity). Verified live on
   Navrey Lean7 on a disposable host (2026-10-17): a part of a stack dropped on a mobile opens the window, gold coins go into the box, both accept, goods and gold change hands.
 * a bot starts at most one deal per 10 minutes (5 after a success); nothing waits for a trade: wants and offers are posted while the bot keeps digging / mining.
Events: offer_posted {item, qty, price}, want_posted {item, qty, price}, deal_booked {id, with, item, qty, price, role}, trade {with, item, qty, price, total, role}, deal_failed {id, with, item,
why, role}. (price = gold per unit.) Roles: miners / prospectors supply ingots (MinerBot), smiths and tinkers want them (CrafterBot with iron ingots as material).
"""
import math
import time

ITEMS = {
    "iron ingot": {"word": "iron ingot", "min_qty": 10, "plain": True, "chunk": 100, "low": 40},
}
OFFER_EVERY = 300
MATCH_EVERY = 60
FRESH = 900
DEAL_LIFE = 420
COOL_FAIL = 600
COOL_OK = 300
HOLD_EXTRA = 30


class MarketMixin:
    # ---- prices: rules from the NPC lists in shared memory ------------------------------------------------------------------------------------------------

    def mkt_npc(self, item):
        word = ITEMS[item]["word"]
        buy = [p for p, xy, i in self.mem.vendor_buying(word) if p > 0]
        sell = [p for p, xy, i, q in self.mem.vendor_selling(word) if p > 0]
        return (max(buy) if buy else None), (min(sell) if sell else None)

    def mkt_floor(self, item):
        buy, _ = self.mkt_npc(item)
        if buy is None:
            return None
        return max(buy + 1, math.ceil(buy * 1.25))

    def mkt_ceiling(self, item):
        buy, sell = self.mkt_npc(item)
        floor = self.mkt_floor(item)
        if floor is None:
            return None
        if sell is not None:
            return sell - 1
        return max(floor, 2 * buy)

    def mkt_ask(self, item):
        """The unit price an offer asks: floor + 20% (at least +1) inside floor..ceiling; None when there is no gain to share."""
        floor, ceil = self.mkt_floor(item), self.mkt_ceiling(item)
        if floor is None or ceil is None or ceil < floor:
            return None
        return max(floor, min(ceil, floor + max(1, round(floor * 0.2))))

    # ---- what this bot has / needs -----------------------------------------------------------------------------------------------------------------------

    def mkt_stacks(self, item):
        spec = ITEMS[item]
        out = []
        for i in self.c.backpack:
            if i.name.lower() == item and not (spec.get("plain") and getattr(i, "hue", 0)):
                out.append(i)
        return out

    def mkt_count(self, item):
        return sum((i.amount or 1) for i in self.mkt_stacks(item))

    def mkt_supply(self):
        """{item: quantity this bot would sell}: overridden by the roles that make surplus (MinerBot: its ingots)."""
        return {}

    def mkt_demand(self):
        """{item: quantity this bot wants to buy}: overridden by the roles that need material (CrafterBot on iron ingots)."""
        return {}

    def mkt_money(self):
        return self.c.gold + self.facts.get("bank_balance", 0)

    # ---- memory views -------------------------------------------------------------------------------------------------------------------------------------

    def mkt_view(self):
        self.mem.refresh()
        mk = self.mem.state["world"]["market"]
        return mk.setdefault("offers", {}), mk.setdefault("wants", {}), mk.setdefault("deals", {})

    def mkt_busy(self, bot, now=None):
        now = now or time.time()
        for d in self.mkt_view()[2].values():
            if d["state"] == "agreed" and now - d["t"] < DEAL_LIFE and bot in (d["seller"], d["buyer"]):
                return True
        return False

    def mkt_open(self, table, item, not_from, fresh=FRESH):
        now = time.time()
        return [o for o in table.values() if o["item"] == item and o["bot"] != not_from and now - o["t"] < fresh and o.get("qty", 1) > 0 and not self.mkt_busy(o["bot"], now)]

    # ---- posting -------------------------------------------------------------------------------------------------------------------------------------------

    def mkt_post(self):
        now = time.time()
        if now - self.facts.get("mkt_posted_at", 0) < OFFER_EVERY:
            return
        self.facts["mkt_posted_at"] = now
        posted = self.facts.setdefault("mkt_posted", {})
        meet = list(self.MEET)
        supply = self.mkt_supply()
        demand = self.mkt_demand()
        for item in ITEMS:
            qty, ask = supply.get(item, 0), self.mkt_ask(item)
            if qty >= ITEMS[item]["min_qty"] and ask is not None:
                self.mem.record("mkt", kind="offer", item=item, price=ask, qty=qty, meet=meet)
                self.mkt_log_post("offer_posted", f"o:{item}", item, qty, ask, posted)
            elif posted.pop(f"o:{item}", None):
                self.mem.record("mkt", kind="unoffer", item=item)
            qty, ceil = demand.get(item, 0), self.mkt_ceiling(item)
            if qty >= ITEMS[item]["min_qty"] and ceil is not None:
                self.mem.record("mkt", kind="want", item=item, price=ceil, qty=qty, meet=meet)
                self.mkt_log_post("want_posted", f"w:{item}", item, qty, ceil, posted)
            elif posted.pop(f"w:{item}", None):
                self.mem.record("mkt", kind="unwant", item=item)

    def mkt_log_post(self, name, key, item, qty, price, posted):
        was = posted.get(key)
        posted[key] = (qty, price, time.time())
        if not was or was[0] != qty or was[1] != price or time.time() - was[2] > 1800:
            self.ev(name, item=item, qty=qty, price=price)

    # ---- matching ------------------------------------------------------------------------------------------------------------------------------------------

    def mkt_match(self):
        now = time.time()
        if now - self.facts.get("mkt_match_at", 0) < MATCH_EVERY or now < self.facts.get("deal_cool_until", 0) or self.mkt_busy(self.name, now):
            return False
        self.facts["mkt_match_at"] = now
        offers, wants, _ = self.mkt_view()
        for item in ITEMS:
            spec = ITEMS[item]
            ceil, floor = self.mkt_ceiling(item), self.mkt_floor(item)
            if ceil is None or floor is None:
                continue
            need = self.mkt_demand().get(item, 0)
            if need >= spec["min_qty"]:
                cands = [o for o in self.mkt_open(offers, item, self.name) if o["price"] <= ceil and o.get("qty", 1) >= spec["min_qty"]]
                if cands:
                    o = min(cands, key=lambda o: (o["price"], -o.get("qty", 1)))
                    qty = min(o.get("qty", 1), need, int(self.mkt_money() // max(o["price"], 1)))
                    if qty >= spec["min_qty"]:
                        return self.mkt_book(item, seller=o["bot"], buyer=self.name, qty=qty, unit=o["price"], meet=o.get("meet"))
                    self.ev("deal_failed", id="", item=item, why=f"cannot afford {spec['min_qty']} at {o['price']}: money {self.mkt_money()}", role="buyer", **{"with": o["bot"]})
            have = self.mkt_supply().get(item, 0)
            if have >= spec["min_qty"]:
                cands = [w for w in self.mkt_open(wants, item, self.name) if w["price"] >= floor and w.get("qty", 1) >= spec["min_qty"]]
                if cands:
                    w = max(cands, key=lambda w: (w["price"], w.get("qty", 1)))
                    ask = self.mkt_ask(item) or floor
                    unit = max(floor, min(w["price"], ask))
                    qty = min(have, w.get("qty", 1))
                    if qty >= spec["min_qty"]:
                        return self.mkt_book(item, seller=self.name, buyer=w["bot"], qty=qty, unit=unit, meet=list(self.MEET))
        return False

    def mkt_book(self, item, seller, buyer, qty, unit, meet):
        me_buyer = buyer == self.name
        total = qty * unit
        if me_buyer and self.c.gold < total:
            if self.facts.get("bank_balance", 0) > 0:
                self.visit_bank("trade", withdraw=total + 30, reserve=0)        # the money into the pack before anyone walks to the bank
            if self.c.gold < total:
                self.ev("deal_failed", id="", item=item, why=f"gold {self.c.gold} short of {total} after the bank", role="buyer", **{"with": seller})
                return False
        did = f"{seller}-{buyer}-{int(time.time())}"
        meet = list(meet) if meet else list(self.MEET)
        self.mem.record("mkt", kind="deal", id=did, seller=seller, buyer=buyer, item=item, qty=qty, unit=unit, price=total, meet=meet)
        self.ev("deal_booked", id=did, item=item, qty=qty, price=unit, role="buyer" if me_buyer else "seller", **{"with": seller if me_buyer else buyer})
        self.facts["deal_cool_until"] = time.time() + COOL_FAIL
        self.mem.refresh(force=True)
        return True

    # ---- the rule --------------------------------------------------------------------------------------------------------------------------------------------

    def market_tick(self):
        """Post offers / wants, make the supply (a miner smelts when a smith wants ingots) and look for a match. True when a deal was booked."""
        if not self.feature("trade") or self.c.ghost:
            return False
        try:
            self.mkt_post()
            self.mkt_make_supply()
            return self.mkt_match()
        except Exception as e:
            self.log(f"market: {type(e).__name__}: {e}")
            return False

    def mkt_make_supply(self):
        return False

    def r_market(self):
        """A booked deal first; otherwise the market (post, match). The old one-piece offers of the crafters stay in their own r_market."""
        d = self.mem.deal_for(self.name)
        if d:
            return self.do_deal(d)
        return self.market_tick()

    def mkt_hold(self, item):
        """A miner keeps its ingots (does not sell them to an NPC) while a smith wants them: an open want for the item and not much more in the pack than it asks for."""
        if not self.feature("trade"):
            return False
        wants = self.mkt_view()[1]
        ws = self.mkt_open(wants, item, self.name)
        return bool(ws) and self.mkt_count(item) <= sum(w.get("qty", 1) for w in ws) + HOLD_EXTRA

    # ---- the deal ----------------------------------------------------------------------------------------------------------------------------------------------

    def mkt_fail(self, d, role, other, why, st=None):
        self.mem.record("mkt", kind="fail", id=d["id"], why=why)
        self.ev("deal_failed", id=d["id"], item=d["item"], qty=d.get("qty", 1), why=why, role=role, **{"with": other})
        self.log(f"trade {d.get('qty', 1)} {d['item']} with {other} failed: {why}")
        self.facts["deal_cool_until"] = time.time() + COOL_FAIL
        self.facts.get("deals", {}).pop(d["id"], None)
        return True

    def market_deal(self, d):
        """One tick of a deal as seller or buyer (see the module doc). Always returns True: the deal owns the tick."""
        role = "seller" if d["seller"] == self.name else "buyer"
        other = d["buyer"] if role == "seller" else d["seller"]
        qty, total, item = int(d.get("qty") or 1), int(d["price"]), d["item"]
        unit = d.get("unit") or (total // max(qty, 1))
        meet = tuple(d["meet"]) if d.get("meet") else tuple(self.MEET)
        st = self.facts.setdefault("deals", {}).setdefault(d["id"], {"gold0": self.c.gold, "n0": self.mkt_count(item) if item in ITEMS else sum((i.amount or 1) for i in self.c.backpack if i.name.lower() == item),
                                                                        "opened": False, "t0": time.time()})
        self.activity = f"trading {qty} {item} with {other}"
        if time.time() - d["t"] > DEAL_LIFE - 20:
            self.mkt_fail(d, role, other, f"{role} timed out ({'window opened' if st['opened'] else 'no window'})")
            self.c.goto(self.c.x + 8, self.c.y + 8).wait(timeout=5)             # walk off: an open trade window closes when the traders part
            return True
        count = (lambda: self.mkt_count(item)) if item in ITEMS else (lambda: sum((i.amount or 1) for i in self.c.backpack if i.name.lower() == item))
        tr = [t for t in self.trades() if t["with"].startswith(other)]
        if not tr:
            if st["opened"]:
                ok = (role == "seller" and self.c.gold >= st["gold0"] + total - 1) or (role == "buyer" and count() >= st["n0"] + qty)
                if not ok:
                    return self.mkt_fail(d, role, other, f"{role}: the window closed without the goods")
                self.mem.record("mkt", kind="done", id=d["id"], why="")
                self.ev("trade", item=item, qty=qty, price=unit, total=total, role=role, **{"with": other})
                self.log(f"trade done: {qty} {item} for {total} gold with {other}")
                self.note("trade", f"{d['seller']} sold {qty} {item} to {d['buyer']} for {total} gold through the secure-trade window.", key="trade:ok")
                self.facts["deal_cool_until"] = time.time() + COOL_OK
                self.facts.get("deals", {}).pop(d["id"], None)
                if role == "buyer" and hasattr(self, "wear_bought") and item not in ITEMS:
                    self.wear_bought(item)
                return True
            if max(abs(self.c.x - meet[0]), abs(self.c.y - meet[1])) > 2:
                self.c.goto(*meet).wait(timeout=6)
                return True
            them = next((m for m in self.c.mobiles(within=3) if m.name == other), None)
            if role == "seller" and them:
                stacks = self.mkt_stacks(item) if item in ITEMS else [i for i in self.c.backpack if i.name.lower() == item]
                stack = next((i for i in stacks if (i.amount or 1) >= qty), None)
                if not stack and not st.get("merged") and sum((i.amount or 1) for i in stacks) >= qty:
                    # Enough in all, but split over several stacks (each smelt makes its own pile): a player drops the piles
                    # on each other first. The server merges a stack dropped on an identical one. 19 of 29 failed deals on
                    # 2026-10-18 were "seller has no stack of 20 iron ingot" with the ingots in the pack.
                    stacks.sort(key=lambda i: -(i.amount or 1))
                    for extra in stacks[1:]:
                        self.c.drop(extra.serial, stacks[0].serial, extra.amount or 1)
                        time.sleep(0.7)
                    st["merged"] = True
                    self.log(f"trade: merged {len(stacks)} stacks of {item} into one before handing over {qty}")
                    return True
                if not stack:
                    self.mem.record("mkt", kind="unoffer", item=item)
                    return self.mkt_fail(d, role, other, f"seller has no stack of {qty} {item}")
                self.c.drop(stack.serial, them.serial, qty)
                time.sleep(2)
            else:
                time.sleep(1.5)
            return True
        t = tr[0]
        st["opened"] = True
        theirs = self.box_items(t["theirbox"])
        if role == "buyer":
            got = sum((i.amount or 1) for i in theirs if i.name.lower() == item)
            if got < qty:
                time.sleep(1.5)
                return True
            mine_gold = sum((i.amount or 1) for i in self.box_items(t["mybox"]) if i.name.lower().startswith("gold"))
            if mine_gold < total:
                gold = next((i for i in self.c.backpack if i.name.lower().startswith("gold coin")), None)
                if not gold or (gold.amount or 1) < total - mine_gold:
                    return self.mkt_fail(d, role, other, "buyer short of gold")
                self.c.drop(gold.serial, t["mybox"], total - mine_gold)
                time.sleep(1.5)
                return True
            if not t["mine_ok"]:
                self.c.call(f"accepttrade {t['local']}", timeout=5)
        else:
            mine = sum((i.amount or 1) for i in self.box_items(t["mybox"]) if i.name.lower() == item)
            their_gold = sum((i.amount or 1) for i in theirs if i.name.lower().startswith("gold"))
            if mine != qty:
                return self.mkt_fail(d, role, other, f"my box holds {mine} {item}, the deal says {qty}")
            if their_gold >= total and not t["mine_ok"]:
                self.c.call(f"accepttrade {t['local']}", timeout=5)
        time.sleep(1.5)
        return True


class MinerMarket(MarketMixin):
    """MinerBot: sells its ingots to smiths; smelts ahead of a full pack when a smith is waiting; keeps ingots back from the NPC while a want is open."""

    def mkt_supply(self):
        return {"iron ingot": self.mkt_count("iron ingot")}

    def mkt_make_supply(self):
        now = time.time()
        if now - self.facts.get("mkt_smelt_at", 0) < 600 or self.threats(8):
            return False
        wants = self.mkt_open(self.mkt_view()[1], "iron ingot", self.name)
        if not wants:
            return False
        want = sum(w.get("qty", 1) for w in wants)
        ore = sum((i.amount or 1) for i in self.ore_piles(smeltable=True))
        if self.mkt_count("iron ingot") >= min(want, 40) or ore < 20:
            return False
        self.facts["mkt_smelt_at"] = now
        self.log(f"market: a smith wants {want} ingots, {self.mkt_count('iron ingot')} in the pack, {ore} ore: smelting now")
        self.smelt()
        return True


class CrafterMarket(MarketMixin):
    """CrafterBot whose material is iron ingots (Blacksmith, Tinker): wants ingots below 40 and buys up to 100."""

    def mkt_demand(self):
        if self.cfg.get("mat") != "iron ingot":
            return {}
        have = self.mkt_count("iron ingot")
        spec = ITEMS["iron ingot"]
        if have >= spec["low"]:
            return {}
        return {"iron ingot": spec["chunk"] - have}


class FighterMarket(MarketMixin):
    """HunterBot / BardBot (G2): look at what the armourers sell before saving for it, and tell the smiths which piece a fighter would buy."""

    WINDOW_EVERY = 1200
    WANT_EVERY = 600

    def r_window(self):
        """Window shopping. The fighters' upgrade rule only knows a piece's price once some bot has opened the shop's list, and no bot ever opened an armourer's (the shared memory
        held no price for any armour piece, so next_upgrade found nothing for a whole night). With 300+ gold (pack and bank) and an armour piece with no known price, one visit
        per 20 minutes: the nearest armourer / smith / weaponsmith nobody has looked at, the list is read and recorded (nothing is bought); the shop is claimed for 30 minutes."""
        if not self.feature("trade") or self.c.ghost:
            return False
        now = time.time()
        if now - self.facts.get("window_at", 0) < self.WINDOW_EVERY or self.mobs(10) or self.hp_pct() < 70 or self.mkt_money() < 300:
            return False
        names = [o[0] for opts in self.ARMOR_BUY.values() for o in opts]
        more = self.feature("arms") and bool(self.weapons_unpriced())                     # weapons a fighter could buy that no read list has
        if all(self.mem.vendor_selling(n) for n in names) and not more:
            return False
        self.facts["window_at"] = now
        self.mem.refresh()
        state = self.mem.state["world"]
        shops = []
        for xy in self.find_places(("armorer", "smith", "weaponsmith", "bowyer"), n=8, per=2):
            key = f"{xy[0]},{xy[1]}"
            claim = state["res"].get("window", {}).get(key)
            if claim and claim["claim_until"] > now and claim["claim_by"] != self.name:
                continue                                          # another fighter is looking at it
            if state["vendors"].get(key, {}).get("stock"):
                continue                                          # its list is already known
            shops.append(xy)
        if not shops:
            return False
        xy = shops[0]
        self.mem.record("claim", kind="window", key=f"{xy[0]},{xy[1]}", ttl=1800)
        self.activity = "looking at the armour in a shop"
        self.shop_at(xy, {}, budget=0)
        known = sum(1 for n in names if self.mem.vendor_selling(n))
        self.ev("window_shop", shop=[xy[0], xy[1]], pieces_priced=known, of=len(names))
        return True

    def fighter_want(self):
        """Every ten minutes, with money beyond the reserve: the armour piece next_upgrade would buy is posted as a want at one gold under the shop's price, so a smith that can make it does."""
        now = time.time()
        if not self.feature("trade") or now - self.facts.get("want_gear_at", 0) < self.WANT_EVERY:
            return False
        self.facts["want_gear_at"] = now
        best = self.next_upgrade(self.mkt_money() - self.UPGRADE_RESERVE)
        old = self.facts.get("want_gear")
        if not best:
            if old:
                self.mem.record("mkt", kind="unwant", item=old)
                self.facts.pop("want_gear", None)
            return False
        _, layer, name, price, xy, cur, ar = best
        if old and old != name:
            self.mem.record("mkt", kind="unwant", item=old)
        self.mem.record("mkt", kind="want", item=name, price=price - 1, qty=1, meet=list(self.MEET))
        if old != name:
            self.ev("want_posted", item=name, qty=1, price=price - 1)
        self.facts["want_gear"] = name
        return False


class CrafterDemand:
    """CrafterBot: a piece a fighter wants (an open want in the market) is made before the piece that teaches the most, two at a time."""

    DEMAND_FRESH = 1800

    def demand_pick(self):
        if not self.feature("trade") or getattr(self, "mode", "") == "newbie" or not getattr(self, "items", None):
            return None
        wants = self.mkt_view()[1]
        now = time.time()
        have = self.count(self.cfg["mat"])
        for w in sorted(wants.values(), key=lambda w: -w["price"]):
            name = w["item"]
            if w["bot"] == self.name or now - w["t"] > self.DEMAND_FRESH or name not in self.menu_map or name in self.bad_items:
                continue
            if any(i.name.lower() == name for i in self.c.backpack):
                continue                                          # one is already in the pack, waiting for its buyer
            it = self.items.get(name)
            if not it or it["resource"] != self.cfg["res"] or it["amount"] > have:
                continue
            ch = self.chance(it, self.skill)
            if ch < 0.5:
                continue
            self.facts["demand_item"] = name
            return ((2, w["price"]), name, it, ch)
        return None

    def craft_batch(self, name):
        return 2 if self.facts.get("demand_item") == name else 12
