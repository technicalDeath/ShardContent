"""Coloured armour between the bots (feature "colour_craft"; owner, 2026-11-02: "For colored ingots - yes, have them craft and sell armor to other bots who
can use it").

A smith works the best coloured metal its Blacksmithy allows (DefBlacksmithy AddSubRes: dull copper 65 ... valorite 99), makes the armour pieces fighters
wear, and offers them in the bots' market; a fighter weighs a coloured piece by the armour it adds (BaseArmor.ArmorRating under UOR: +2 dull copper ... +16
valorite, items.COLOURS) against the shops' iron pieces, books a deal for the piece by its serial and wears it. Gold moves from the fighters (over 900,000
banked, nothing to spend it on) to the smiths; no NPC buys coloured ingots, and an NPC pays the same for a coloured piece as for an iron one (crafted-goods
pricing is by item type), so the market is where coloured metal is worth something.

The price: the shop's price for the iron piece per point of armour, times the coloured piece's armour (a valorite platemail tunic, 56 points, at 56/40 of the
iron tunic's price), so a fighter's next_upgrade compares it with the shops' pieces on the same armour-per-gold scale.
"""
from __future__ import annotations

import re
import time

import items

# the smithing menu's armour pieces (crafter DATA names) the fighters wear: menu name -> (paperdoll layer, the fighters' shop name in HunterBot.ARMOR_BUY)
PIECES = {
    "plate chest": ("Torso", "platemail tunic"), "plate legs": ("Pants", "platemail legs"), "plate arms": ("Arms", "platemail arms"),
    "plate gloves": ("Gloves", "platemail gloves"), "plate gorget": ("Necklace", "platemail gorget"), "plate helm": ("Helmet", "plate helm"),
    "chain chest": ("Torso", "chainmail tunic"), "chain legs": ("Pants", "chainmail leggings"), "chain coif": ("Helmet", "chainmail coif"),
    "close helm": ("Helmet", "close helm"),
}
OFFER_FRESH = 900          # s an offer counts (memory's market freshness)
STOCK = 3                  # coloured pieces a smith holds unsold before making more
STOCK_DAYS = 0.25          # a coloured piece unsold this long (days) goes to the NPC as an ordinary product
MIN_CHANCE = 0.25          # the floor of a coloured piece's success chance (a failure consumes half the material, CraftItem; colour_choice ranks by
                           # armour per expected ingot)


def shop_entry(bot, shop_name):
    """(layer, armour, strength needed, dexterity cost) of a shop piece in the fighters' ARMOR_BUY table, else None."""
    for layer, opts in getattr(bot, "ARMOR_BUY", {}).items():
        for name, ar, need, dex in opts:
            if name == shop_name:
                return layer, ar, need, dex
    return None


class ColourBuyer:
    """HunterBot: coloured pieces the smiths offer, weighed against the shops' (next_upgrade), bought by serial through a market deal, and worn."""

    def colour_buy_on(self):
        return self.feature("colour_craft")

    def colour_candidates(self, money):
        """[(score, layer, item, price, meet, cur, ar, offer)] of the coloured pieces on offer that this bot can wear, beat what it wears and can pay for."""
        if not self.colour_buy_on():
            return []
        try:
            self.mem.refresh()
            offers = list(self.mem.state["world"]["market"]["offers"].values())
        except Exception:
            return []
        strength = int(self.c.state.get("str") or 0)
        now = time.time()
        out = []
        for o in offers:
            if not o.get("hue") or o.get("bot") == self.name or now - float(o.get("t", 0) or 0) > OFFER_FRESH or not o.get("shop_name"):
                continue
            e = shop_entry(self, o["shop_name"])
            if not e:
                continue
            layer, base, need, dex = e
            ar = base + int(o.get("bonus") or 0)
            cur, _ = self.worn_ar(layer)
            price = int(o.get("price") or 0)
            if ar <= cur or need > strength or (getattr(self, "ranged", False) and dex < -2) or price <= 0 or price > money:
                continue
            out.append(((ar - cur) * self.SLOT_SHARE[layer] / max(price, 1), layer, o["item"], price, tuple(o.get("meet") or self.MEET), cur, ar, o))
        if now - self.__dict__.get("_colour_seen_at", 0) > 600:
            self.__dict__["_colour_seen_at"] = now                   # what the buyer sees, live (the canary raised no upgrade for two hours)
            seen = [o for o in offers if o.get("hue")]
            try:
                self.log(f"colour: {len(seen)} coloured offers in the market ({sum(1 for o in seen if now - float(o.get('t', 0) or 0) <= OFFER_FRESH)} fresh), "
                         f"{len(out)} I would buy (money {money})")
            except Exception:
                pass
        return out

    def colour_pick(self, best, money):
        """next_upgrade's best, or a coloured piece on offer when it gives more armour per gold; the offer is kept for r_upgrade (_colour_pick)."""
        self.__dict__.pop("_colour_pick", None)
        cands = self.colour_candidates(money)
        if not cands:
            return best
        top = max(cands, key=lambda c: c[0])
        if best is None or top[0] > best[0]:
            self.__dict__["_colour_pick"] = top[7]
            return top[:7]
        return best

    def colour_book(self, name):
        """r_upgrade with a coloured offer picked: book the deal for that piece (its serial), remember the layer for wear_bought. True when booked."""
        o = self.__dict__.pop("_colour_pick", None)
        if not o or o.get("item") != name:
            return False
        if self.c.gold < o["price"] and self.facts.get("bank_balance", 0) > 0:
            self.visit_bank("trade", withdraw=o["price"] + 60, reserve=0)
        if self.c.gold < o["price"]:
            return False
        did = f"{o['bot']}-{self.name}-{int(time.time())}"
        self.mem.record("mkt", kind="deal", id=did, seller=o["bot"], buyer=self.name, item=o["item"], price=o["price"], serial=o.get("serial"),
                        hue=o.get("hue"), meet=list(o.get("meet") or self.MEET))
        e = shop_entry(self, o.get("shop_name", "")) or (None,)
        self.facts["colour_buy"] = {"serial": o.get("serial"), "layer": e[0], "item": o["item"], "price": o["price"], "t": time.time()}
        self.log(f"upgrade: booked a {o.get('metal', 'coloured')} {o['item']} from {o['bot']} for {o['price']} gold (armour +{o.get('bonus')})")
        self.ev("colour_deal", item=o["item"], metal=o.get("metal"), price=o["price"], seller=o["bot"], bonus=o.get("bonus"))
        self.facts["upgrade_at"] = time.time() - 300
        return True

    def colour_wear(self):
        """After a trade: put on the coloured piece bought (by its serial) in place of what its layer held. True when it handled the trade."""
        cb = self.facts.get("colour_buy")
        if not cb or not cb.get("serial"):
            return False
        new = next((i for i in self.c.backpack if str(i.serial) == str(cb["serial"])), None)
        if not new:
            return False
        self.facts.pop("colour_buy", None)
        if cb.get("layer"):
            _, old = self.worn_ar(cb["layer"])
            if old:
                self.c.unequip(old.serial)
                self.facts.setdefault("gear_failed", {})[old.serial] = time.time() + 10 ** 9
                time.sleep(0.8)
        try:
            self.c.call(f"equip {new.serial}", timeout=6)
        except Exception:
            pass
        time.sleep(0.8)
        worn = any(str(i.serial) == str(new.serial) for i in self.c.equipped)
        self.log(f"upgrade: wearing the coloured {cb['item']} bought for {cb['price']} gold: worn {worn}")
        self.ev("colour_worn", item=cb["item"], worn=worn, price=cb["price"])
        return True


class ColourSmith:
    """CrafterBot (Blacksmithy): coloured armour made from the best metal the skill allows, kept out of the NPC sales, offered to the fighters."""

    def colour_on(self):
        return self.feature("colour_craft") and self.cfg.get("craft") == "Blacksmith"

    def colour_stock(self):
        """{serial: record} of the coloured pieces this smith made and has not sold (facts colour_made), pieces no longer in the pack dropped."""
        made = self.facts.setdefault("colour_made", {})
        held = {str(i.serial) for i in self.c.backpack}
        for s in [s for s in made if s not in held]:
            made.pop(s, None)
        # a coloured armour piece in the pack with no record (a brain from before the record was kept across restarts): adopted, so it is offered and
        # not sold to an NPC at the iron price. Pack names: the menu's own (made_as) or the shop name the client also uses ("plate helm")
        names = {shop: menu for menu, (layer, shop) in PIECES.items()}
        for menu, packs in (getattr(self, "made_as", None) or {}).items():
            if menu in PIECES:
                for pn in packs:
                    names[pn] = menu
        for i in self.c.backpack:
            c = items.colour(i)
            menu = names.get((i.name or "").lower())
            if c and c[1] == "Blacksmithy" and menu and str(i.serial) not in made:
                layer, shop_name = PIECES[menu]
                made[str(i.serial)] = {"menu": menu, "hue": int(i.hue), "metal": c[0], "bonus": c[3], "shop_name": shop_name, "layer": layer,
                                       "name": (i.name or "").lower(), "t": time.time()}
        return made

    def colour_kept(self):
        """Serials products() leaves out: the coloured pieces on offer, younger than STOCK_DAYS."""
        if not self.colour_on():
            return set()
        now = time.time()
        return {s for s, r in self.colour_stock().items() if now - float(r.get("t", 0)) < STOCK_DAYS * 86400}

    def metal_skill(self):
        """The craft skill a coloured metal's gate reads: its base, without bonuses (CraftItem: Skills[MainSkill].Base < RequiredSkill refuses the metal).
        BotSmithBR read 81.3 on a base of 79.3 and was refused bronze (80), 2026-11-05."""
        try:
            b = (self.__dict__.get("skill_bases") or {}).get(self.cfg.get("skill"))
        except Exception:
            b = None
        return min(float(self.skill), float(b)) if b is not None else float(self.skill)

    def colour_metals(self):
        """[(bonus, hue, name, stack)] of the coloured ingots in the pack this smith's Blacksmithy can work, best first."""
        out = []
        skill = self.metal_skill()
        for i in self.c.backpack:
            c = items.colour(i)
            if c and c[1] == "Blacksmithy" and "ingot" in (i.name or "").lower() and skill >= c[2]:
                out.append((c[3], int(i.hue), c[0], i))
        return sorted(out, key=lambda t: (-t[0], -(t[3].amount or 1)))

    COLOUR_TAKE = 60           # coloured ingots taken out of the bank at a visit: two plate pieces' worth (a plate legs is 20, a failure costs half)

    def bank_colour_out(self, box):
        """At a bank visit, with fewer than STOCK pieces held: the coloured ingots this smith can work come out, best metal first, up to COLOUR_TAKE in
        all (hues read from the client's reply, basics.box_contents). The smiths' coloured ingots sit in the bank (the overloaded shed puts them there),
        so a smith with 21 bronze in the pack and more banked made one piece and stopped (2026-11-02 15:06-15:21). Returns how many were taken."""
        if not self.colour_on() or len(self.colour_stock()) >= STOCK:
            return 0
        try:
            stacks = [i for i in self.box_contents(box, timeout=6) if items.colour(i) and items.colour(i)[1] == "Blacksmithy"
                      and "ingot" in (i.name or "").lower() and self.metal_skill() >= items.colour(i)[2]]
        except Exception:
            return 0
        held = sum((i.amount or 1) for i in self.c.backpack if items.colour(i) and "ingot" in (i.name or "").lower())
        want = self.COLOUR_TAKE - held
        taken = 0
        for st in sorted(stacks, key=lambda i: (-items.colour(i)[3], -(i.amount or 1))):
            if want <= 0:
                break
            n = min(int(st.amount or 1), want)
            self.c.get_item(st.serial, n if (st.amount or 1) > 1 else None)
            time.sleep(1.2)
            taken += n
            want -= n
        if taken:
            self.log(f"colour: took {taken} coloured ingots out of the bank for armour")
            self.ev("colour_unbanked", taken=taken)
        return taken

    def colour_choice(self):
        """(menu name, hue, metal, bonus) to make next, or None: the piece worth most to a fighter (its armour plus the metal's, by the slot's share) that the
        smith makes at MIN_CHANCE or better, has the ingots for, and does not already hold."""
        if len(self.colour_stock()) >= STOCK:
            return None
        held = {(r.get("menu"), r.get("hue")) for r in self.colour_stock().values()}
        try:
            import hunter
            share, table = hunter.HunterBot.SLOT_SHARE, hunter.HunterBot
        except Exception:
            return None
        best = None
        for bonus, hue, metal, stack in self.colour_metals():
            for menu, (layer, shop_name) in PIECES.items():
                it = self.items.get(menu)
                if not it or menu not in self.menu_map or (menu, hue) in held or (stack.amount or 1) < it["amount"]:
                    continue
                if self.chance(it, self.skill) < MIN_CHANCE:
                    continue
                e = shop_entry(table, shop_name)
                if not e:
                    continue
                # worth only what it adds over the best iron piece of the slot, which any fighter can buy at a shop: a bronze chain chest (28 + 8 = 36)
                # is worth nothing to a fighter in iron plate (40). BotSmithAR made one for two fighters in full plate (2026-11-02 15:06)
                iron_best = max(o[1] for o in table.ARMOR_BUY.get(layer, [])) if table.ARMOR_BUY.get(layer) else 0
                value = (e[1] + bonus - iron_best) * share[layer]
                if value <= 0:
                    continue
                # per coloured ingot it is expected to use: a failure consumes half the material (CraftItem, ConsumeType.Half), so a piece made at chance p
                # costs amount x (1 + (1 - p) / (2p)) on average. Coloured ingots have no other use, so the hard plate pieces (a smith at 84 makes plate
                # gorgets at 56%, legs at 31%) are worth making; the floor keeps the hardest from eating the pile
                p = self.chance(it, self.skill)
                value /= it["amount"] * (1 + (1 - p) / (2 * p))
                if best is None or value > best[0]:
                    best = (value, menu, hue, metal, bonus)
        return best[1:] if best else None

    def colour_price(self, shop_name, bonus):
        """The shop's price for the iron piece per point of armour, times the coloured piece's armour; None when no shop price is known."""
        try:
            import hunter
            e = shop_entry(hunter.HunterBot, shop_name)
            offers = [o for o in self.mem.vendor_selling(shop_name) if o[2] == shop_name]
        except Exception:
            return None
        if not e or not offers:
            return None
        return int(round(offers[0][0] * (e[1] + bonus) / e[1]))

    def r_colour(self):
        """Make one coloured armour piece (the best metal and piece colour_choice names), and offer what is held."""
        if not self.colour_on():
            return False
        self.colour_offer()                               # before the checks: offers last OFFER_FRESH, and a smith heavy most of the time (375/450 at 16:38) let them
                                                          # lapse while the fighters chose their next task (2026-11-02)
        if self.threats(10) or self.c.weight > self.c.max_weight * self.CRAFT_WEIGHT:
            return False
        if time.time() - self.facts.get("colour_try_at", 0) < 60:
            return False
        ch = self.colour_choice()
        if not ch:
            return False
        menu, hue, metal, bonus = ch
        st = self.station_xy()
        if st and not self.at_station(st):
            # the smithing menu opens only beside an anvil and a forge: "You must be near an anvil and a forge to smith items." (BotSmithAR's first try,
            # 2026-11-02 15:05). The walk r_craft makes, then no craft until it is there
            self.activity = "walking to the forge"
            if max(abs(self.c.x - st[0]), abs(self.c.y - st[1])) > 100 and hasattr(self, "far_goto"):
                self.far_goto(st, "forge", timeout=90)
            else:
                self.c.gotoexact(*st).wait(timeout=100)
            if not self.at_station(st):
                return True
        self.facts["colour_try_at"] = time.time()
        it = self.items[menu]
        before = {str(i.serial) for i in self.c.backpack}
        self.__dict__["_colour_hue"] = hue
        self._need = it["amount"]
        self.activity = f"making a {metal} {menu}"
        try:
            res = self.craft_once(menu, True)
        finally:
            self.__dict__.pop("_colour_hue", None)
        time.sleep(1.0)
        new = [i for i in self.c.backpack if str(i.serial) not in before and items.colour(i) and items.colour(i)[1] == "Blacksmithy" and "ingot" not in (i.name or "").lower()]
        ok = bool(new)
        self.log(f"colour: made a {metal} {menu}: {'ok' if ok else 'no'} ({str(res)[-80:]})")
        self.ev("colour_made", piece=menu, metal=metal, ok=ok)
        if ok:
            layer, shop_name = PIECES[menu]
            self.colour_stock()[str(new[0].serial)] = {"menu": menu, "hue": hue, "metal": metal, "bonus": bonus, "shop_name": shop_name, "layer": layer,
                                                       "name": (new[0].name or "").lower(), "t": time.time()}
            self.facts["colour_offer_at"] = 0
            self.colour_offer()
        return True

    def colour_offer(self):
        """Every 5 minutes: one market offer per coloured piece held (by its pack name: one per name), with its serial, metal and price."""
        if time.time() - self.facts.get("colour_offer_at", 0) < 300:
            return
        self.facts["colour_offer_at"] = time.time()
        done = set()
        for serial, r in sorted(self.colour_stock().items(), key=lambda kv: -int(kv[1].get("bonus", 0))):
            if r["name"] in done:
                continue
            price = self.colour_price(r["shop_name"], int(r["bonus"]))
            if not price:
                continue
            done.add(r["name"])
            self.mem.record("mkt", kind="offer", item=r["name"], price=price, qty=1, meet=list(self.MEET), serial=serial, hue=r["hue"], metal=r["metal"],
                            bonus=r["bonus"], shop_name=r["shop_name"], layer=r["layer"])
            self.ev("offer_posted", item=f"{r['metal']} {r['name']}", qty=1, price=price)
