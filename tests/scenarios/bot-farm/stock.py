"""Consumables on a shopping list (G3; Operator / Watcher item 2026-10-17; the Helper). Mixins for HunterBot / BardBot / TamerBot (StockMixin) and CasterBot (CasterStock), written into
the bot-farm folder by patch_stock.py. Behind the feature "stock".

The finding: r_resupply bought potions only when the PACK held 200 gold (the bank was never touched: the fighters have 300-4,000 banked and 0-190 in the pack), looked for the Cure
(Orange) potion nowhere, and the mage's shop trip ran once in a character's life (facts["shopped"]) or after a cast failed for want of reagents, so casters always ended up out of them.

What changes, every ten minutes while nothing hostile is near (r_stock, before r_resupply):
 * FIGHTERS: Heal (Yellow) potions 3 and Cure (Orange) 2 once pack + bank hold 200 gold, Refresh (Red) 2 from 250, bandages to 30, and for an archer who does not make its own arrows
   100 arrows (150 bought, when under 60) or the bolts of its crossbow. TAMERS: bandages to 30 where Veterinary is 20+ (to bandage the pet).
 * MONEY: the list is priced from the shared memory (the cheapest shop that sells the item; a guess where none is known), cut from the end (Heal, bandages, ammunition, Cure, Refresh)
   until pack + bank covers it above a 50 gold floor and the goal layer allows it (goals.idle_ok); gold comes out of the bank first when the pack is short.
 * SHOP: the cheapest shop in the memory that sells it, else the Healer (potions, bandages, reagents) or the Bowyer (arrows, bolts); a Cure potion with no known seller tries the
   Alchemist once (its list is then read and remembered). An item that one visit did not get is not asked for again for an hour after two misses: no buy loop.
 * CASTERS: the reagents their held spells use (spell_ok, castable at their Magery) to 20 each (the old fixed plan was 24 / 16 / 14 / 14 / 14 / 8): when any is under 10, the mage
   shop trip of mage_bot.r_resupply is triggered (it ran only after a failed cast), with gold fetched from the bank if the pack is poor.
Events: restock {item, qty, price, from} for every purchase (price = gold per unit, from = shop), consumable_used {item, hp} where the brains drink or bandage, stock_miss {item, why}.
"""
import time

PRICE = {"yellow potion": 15, "red potion": 15, "orange potion": 20, "bandage": 3, "arrow": 2, "crossbow bolt": 3}
EVERY = 600
FLOOR = 50
BACKOFF = 3600
POTIONS = {"yellow potion": "Yellow Potion", "orange potion": "Orange Potion", "red potion": "Red Potion"}


class StockMixin:
    # ---- counts ---------------------------------------------------------------------------------------------------------------------------------------------

    def stock_count(self, item):
        if item == "bandage":
            return sum((i.amount or 1) for i in self.c.backpack if "bandage" in i.name.lower())
        if item in ("arrow", "crossbow bolt"):
            word = "arrow" if item == "arrow" else "bolt"
            return sum((i.amount or 1) for i in self.c.backpack if i.name.lower() in (word, word + "s"))
        want = POTIONS.get(item)
        return sum((i.amount or 1) for i in self.c.backpack if want and i.name == want)

    def stock_list(self):
        """[(item, target total, buy when under)] in priority order for this bot."""
        money = self.mkt_money()
        out = []
        if money >= 200:
            out.append(("yellow potion", 3, 3))
        out.append(("bandage", 30, 15))
        ammo = self.stock_ammo()
        if ammo:
            out.append((ammo[0], ammo[1], ammo[2]))
        if money >= 200:
            out.append(("orange potion", 2, 2))
        if money >= 250:
            out.append(("red potion", 2, 2))
        return out

    def stock_ammo(self):
        return None

    # ---- prices and shops --------------------------------------------------------------------------------------------------------------------------------

    def stock_shop(self, item):
        """(unit price, shop xy or None) for the cheapest shop in the memory that sells it."""
        rows = [r for r in self.mem.vendor_selling(item) if r[0] > 0 and item in r[2].lower() and r[3] > 0]
        if rows:
            price, xy, _, _ = rows[0]
            return price, tuple(int(v) for v in xy.split(","))
        return PRICE.get(item, 10), None

    def stock_default_shop(self, item):
        if item in ("arrow", "crossbow bolt"):
            return self.FLETCH_SHOP
        if item == "orange potion":
            return self.where1(("alchemist", "healer"))
        return self.where1(("healer",))

    # ---- the rule ---------------------------------------------------------------------------------------------------------------------------------------------

    def r_stock(self):
        if not self.feature("stock") or self.c.ghost or self.mobs(10) or self.hp_pct() < 60:
            return False
        now = time.time()
        if now - self.facts.get("stock_at", 0) < EVERY or now - self.facts.get("shop_at", 0) < 120:
            return False
        miss = self.facts.setdefault("stock_miss", {})
        todo = []
        for item, target, under in self.stock_list():
            have = self.stock_count(item)
            if have >= under or miss.get(item, [0, 0])[0] >= 2 and now - miss[item][1] < BACKOFF:
                continue
            todo.append((item, target, have))
        self.facts["stock_at"] = now
        if not todo:
            return False
        # price the list, cut it from the end until it is affordable and the goal allows it
        plan = []
        for item, target, have in todo:
            price, xy = self.stock_shop(item)
            plan.append({"item": item, "target": target, "have": have, "price": price, "xy": xy})
        money = self.mkt_money() - FLOOR
        try:
            import goals
            ok = lambda cost: goals.idle_ok(self, cost)
        except Exception:
            ok = lambda cost: True
        while plan:
            cost = sum((p["target"] - p["have"]) * p["price"] for p in plan)
            if cost <= money and ok(cost):
                break
            last = plan[-1]
            rest = cost - (last["target"] - last["have"]) * last["price"]
            afford = (min(money, money) - rest) // max(last["price"], 1) if ok(rest) else 0
            if afford >= max(3, (last["target"] - last["have"]) // 3) and last["have"] + int(afford) < last["target"]:
                last["target"] = last["have"] + int(afford)          # a part of it: all the money buys
                continue
            # (a part only when it is smaller: money covered the whole of it while the goal fund (idle_ok) did not, the target stayed the same and the loop
            # never ended; the supervisor killed BotTamerAR's brain every 15 minutes, 16 times, 2026-11-01)
            plan.pop()
            self.ev("stock_miss", item=last["item"], why=f"cost {cost} over money {money}")
        if not plan:
            return False
        cost = sum((p["target"] - p["have"]) * p["price"] for p in plan)
        self.activity = "restocking"
        if self.c.gold < cost + 10 and self.facts.get("bank_balance", 0) > 0:
            self.visit_bank("stock", withdraw=min(self.facts["bank_balance"], cost + 30 - self.c.gold), reserve=0)
        # one shop at a time: group by the shop that sells it
        shops = {}
        for p in plan:
            xy = p["xy"] or self.stock_default_shop(p["item"])
            shops.setdefault(tuple(xy), []).append(p)
        did = False
        for xy, items in shops.items():
            wanted = {("=" + p["item"]) if p["item"] != "bandage" else "bandage": p["target"] for p in items}
            before = {p["item"]: self.stock_count(p["item"]) for p in items}
            self.facts["shop_at"] = time.time()
            self.shop_at(xy, wanted, budget=max(self.c.gold - 10, 0))
            self.c.open_backpack()
            for p in items:
                got = self.stock_count(p["item"]) - before[p["item"]]
                if got > 0:
                    miss.pop(p["item"], None)
                    self.ev("restock", item=p["item"], qty=got, price=self.stock_shop(p["item"])[0], **{"from": "shop"})
                    did = True
                else:
                    n = miss.get(p["item"], [0, 0])[0] + 1
                    miss[p["item"]] = [n, time.time()]
                    self.ev("stock_miss", item=p["item"], why="the shop did not sell it" if n < 2 else "not sold there: asking again in an hour")
        return did


class FighterStock(StockMixin):
    def stock_ammo(self):
        if not getattr(self, "ranged", False) or (hasattr(self, "fletcher") and self.fletcher()):
            return None
        bolt = any("crossbow" in i.name.lower() for i in self.c.equipped)
        return ("crossbow bolt" if bolt else "arrow", 150, 60)


class PotionStock(StockMixin):
    """A bot that does not fight for a living (a tamer, a miner): the shared potions, bandages only with the skill to use them."""

    def stock_list(self):
        """The shared list (heal and cure potions from 200 gold, refresh from 250), bandages only with Veterinary or Healing to use them on: BotTamerAR
        carried no potion, was poisoned by a snake while taming at 1377,1911, drank a refresh to run and died of the poison (2026-10-31)."""
        out = StockMixin.stock_list(self)
        import skillplan
        if max(self.skill_values.get("Veterinary", 0), self.skill_values.get("Healing", 0)) < 20 and not (skillplan.wants(self, "Healing") or skillplan.wants(self, "Veterinary")):
            out = [r for r in out if r[0] != "bandage"]           # (a skill plan with Healing or Veterinary: bandages from 0, or the skill never starts, 2026-11-01)
        return out



class TamerStock(PotionStock):
    pass

class CasterStock:
    """CasterBot: the reagents the held spells use, to 20 each; triggers mage_bot.r_resupply's shop trip when any is under 10."""

    TARGET = 20
    DUNGEON_TARGET = 80                                  # a dungeon caster's stock: its mana over a stay (DUNGEON_HUNT_S 40 min at the UOR regen of (Int + Meditation)
                                                         # / 2 ~ 86, one point every 1.35 s: ~1,780 mana, + the pool 85) / 11 for a Lightning = ~170 casts, fighting
                                                         # about half the stay = ~85; 20 lasted five or six lizardmen (2026-11-09)
    HEAL_REGS = ("Garlic", "Ginseng", "SpidersSilk")   # Heal, Greater Heal and Cure all take Garlic and Ginseng, Reactive Armor Garlic and Spider's Silk
    HEAL_STOCK = 40                                      # a stay's bouts at the stair hold: a Greater Heal and a Reactive Armor below for each, about 15
    STAY_CASTS = 85                                      # the casts a stay fights (DUNGEON_TARGET's note): the share-based plan's scale
    PLAN_MIN_CASTS = 50                                  # casts on record before the plan goes by shares (else DUNGEON_TARGET for every reagent)
    PURSE_BASE = 50                                      # mage_bot.r_resupply never spends below this (patch_caster_budget.py)

    @property
    def PURSE_FLOOR(self):
        """A scribe keeps a scribing session's money (scribe.RESERVE + 30), other casters 50 (patch_scribe_floor.py)."""
        try:
            if self.feature("scribe"):
                import scribe
                keep = scribe.RESERVE + 30
                if (self.c.gold or 0) >= keep:
                    return keep                              # the session money, once it is there (patch_scribe_floor2.py)
        except Exception:
            pass
        return self.PURSE_BASE

    def reagent_plan(self):
        if not self.feature("stock"):
            return super().reagent_plan()
        keys = set()
        skill = getattr(self, "skill", 0.0)
        for s in self.k.spells.values():
            if s["min_skill"] <= skill and self.spell_ok(s["name"]):
                keys.update(s["reagents"])
        if not keys:
            return super().reagent_plan()
        if not self.feature("ladder_dungeon"):
            return {k: self.TARGET for k in sorted(keys)}
        return self.dungeon_reagent_plan(keys, skill)

    def dungeon_reagent_plan(self, keys, skill):
        """80 of every reagent of every held spell was 640 reagents (about 2,200 gold) a caster, and eight casters emptied Britain's sellers (20 a line,
        30-minute restock) so that most waited for hours at "kit (5-8 casts)" (2026-11-09 01:56-04:37). The plan instead: the best attack spell's reagents
        to DUNGEON_TARGET; every other reagent to STAY_CASTS x the share of the bot's own casts that use it (stats["casts"]: MageBR 40% Poison, 21%
        Lightning, 14% Magic Arrow, 12% Greater Heal), never under TARGET nor over DUNGEON_TARGET."""
        import math
        plan = {k: self.DUNGEON_TARGET for k in sorted(keys)}
        casts = dict((getattr(self, "stats", None) or {}).get("casts") or {})
        total = sum(int(n or 0) for n in casts.values())
        if total < self.PLAN_MIN_CASTS:
            return plan
        use = {}
        for name, n in casts.items():
            s = self.k.spell(str(name)) if hasattr(self.k, "spell") else None
            for r in (s or {}).get("reagents") or ():
                use[r] = use.get(r, 0) + int(n or 0)
        best = set()
        try:
            pick = self.k.best_attack(skill, 999, {r: 999 for r in keys})
            best = set((pick or {}).get("spell", {}).get("reagents") or ())
        except Exception:
            pass
        for k in plan:
            if k in best:
                continue
            plan[k] = max(self.TARGET, min(self.DUNGEON_TARGET, int(math.ceil(self.STAY_CASTS * use.get(k, 0) / total))))
            if k in self.HEAL_REGS:
                plan[k] = max(plan[k], self.HEAL_STOCK)     # the stair hold's Greater Heal and Reactive Armor every bout (stairhold.py)
        return plan

    POTION_KIT = (("yellow potion", 3), ("orange potion", 2))   # StockMixin.stock_list's Heal and Cure lines, from 200 gold in pack and bank

    def caster_potions(self, now):
        """Heal and Cure potions as the fighters keep them (StockMixin.stock_list), every EVERY seconds: a caster's flight drinks a Heal potion beside an
        attacker before it casts (CasterBot.r_flee), and every caster left for Despise with none ("0 Heal potions", 2026-11-09 05:22-06:26). True when
        it went shopping."""
        if now - float(self.facts.get("potion_stock_at", 0) or 0) < EVERY:
            return False
        self.facts["potion_stock_at"] = now
        bank = int(self.facts.get("bank_balance", 0) or 0)
        if (self.c.gold or 0) + bank < 200:
            return False
        did = False
        for item, n in self.POTION_KIT:
            have = StockMixin.stock_count(self, item)
            if have >= n:
                continue
            price, xy = StockMixin.stock_shop(self, item)
            xy = xy or StockMixin.stock_default_shop(self, item)
            cost = (n - have) * price
            if (self.c.gold or 0) < cost + 10 and bank > 0:
                self.visit_bank("stock", withdraw=min(bank, cost + 30 - (self.c.gold or 0)), reserve=0)
            if (self.c.gold or 0) < cost:
                self.ev("stock_miss", item=item, why=f"gold {self.c.gold}, bank {bank}")
                continue
            self.activity = "restocking potions"
            self.shop_at(tuple(xy), {"=" + item: n}, budget=max((self.c.gold or 0) - 10, 0))
            try:
                self.c.open_backpack()
            except Exception:
                pass
            got = StockMixin.stock_count(self, item) - have
            if got > 0:
                self.ev("restock", item=item, qty=got, price=price, **{"from": "shop"})
            did = True
        return did

    def r_stock(self):
        if not self.feature("stock") or self.c.ghost or self.dangers(10) or self.hp_pct() < 60:
            return False
        now = time.time()
        if self.caster_potions(now):
            return True
        if now - self.facts.get("stock_at", 0) < EVERY:
            return False
        self.facts["stock_at"] = now
        self.refresh_state(force=True)
        plan = self.reagent_plan()
        low = [k for k, n in plan.items() if self.regs.get(k, 0) < n // 2]
        if not low:
            return False
        need = sum((plan[k] - self.regs.get(k, 0)) * 4 for k in low)
        if self.c.gold < min(need, 400) and self.facts.get("bank_balance", 0) >= 40:
            self.visit_bank("stock", withdraw=min(self.facts["bank_balance"], need + 40))
        if self.c.gold < 40:
            self.ev("stock_miss", item="reagents", why=f"gold {self.c.gold}, bank {self.facts.get('bank_balance', 0)}")
            return False
        self.facts["last_fail"] = ("reagents", "restock: " + ",".join(sorted(low)), now)         # mage_bot.r_resupply goes to the mage shop on this
        return False
