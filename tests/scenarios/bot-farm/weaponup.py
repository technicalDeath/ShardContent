"""Fighters buy a better weapon (G2, the second half of the fighters' upgrades; Operator / Watcher item 2026-10-17; the Helper). Mixin for HunterBot / BardBot, written into the bot-farm
folder by patch_weapons.py. Behind the feature "arms".

The armour half (r_upgrade) has a table of pieces and a price per piece; the weapon half had nothing: a fighter fights with the weapon its template gave it, whatever its gold. Now, with
gold beyond the reserve (pack and bank), once every ten minutes (r_arms, after r_upgrade):
 * the weapon worn (layer OneHanded / TwoHanded) is looked up in weapon_table.json (make_weapon_table.py: the server's pre-AOS damage, speed and strength requirement per class;
   value = average damage x speed, which is proportional to damage per second);
 * the candidates are the weapons the shops in the shared memory SELL (any shop whose list a bot has read: r_window reads the armourers', smiths', weaponsmiths' and bowyers' lists),
   of the bot's own main weapon skill, that its strength can wield, that stay in its hands (a one-handed weapon for a one-handed one, so a shield stays; a bow for a bow: arrows
   against bolts would leave it without ammunition), and that are at least 25% better;
 * the best gain in value per gold wins; a bot that sells it for less than the shop (an offer in the market, a smith's piece) is booked first (the same deal code as armour);
   otherwise the shop sells it. The old weapon is unequipped, the new one equipped, and the old one stays in the pack (r_gear does not put it back: another weapon is worn).
Events: weapon_buy {item, price, value_from, value_to, from} (from = shop / the seller's name), weapon_fail {item, why}.
"""
import json
import os
import re
import time

HERE = os.path.dirname(os.path.abspath(__file__))
_TABLE = None
BETTER = 1.25
EVERY = 600
ROLES = ("weaponsmith", "smith", "bowyer")


def norm(t):
    return re.sub(r"[^a-z]", "", t.lower())


def table():
    global _TABLE
    if _TABLE is None:
        try:
            _TABLE = json.load(open(os.path.join(HERE, "weapon_table.json"), encoding="utf-8")).get("weapons", {})
        except (OSError, ValueError):
            _TABLE = {}
    return _TABLE


class WeaponMixin:
    def weapon_now(self):
        """(table entry, item) of the weapon worn, or (None, None)."""
        for i in self.c.equipped:
            e = table().get(norm(i.name))
            if e and (i.layer or "").lower().replace(" ", "") in ("onehanded", "twohanded"):
                return e, i
        return None, None

    def shield_worn(self):
        return any("shield" in i.name.lower() or "buckler" in i.name.lower() for i in self.c.equipped)

    def shop_weapons(self):
        """[(table entry, price, xy, shop's item name)] for every weapon in a shop list the shared memory holds."""
        self.mem.refresh()
        out, seen = [], set()
        mems = [self.mem]
        news = getattr(self.mem, "news", None)                       # the other mode's memory (veteran and newbie bots keep separate folders): the Blacksmith's list was read in one only
        if news is not None:
            try:
                news.refresh()
                mems.append(news)
            except Exception:
                pass
        for m in mems:
            for xy, v in m.state["world"]["vendors"].items():
                for item, (price, qty) in v["stock"].items():
                    e = table().get(norm(item))
                    key = (xy, item.lower())
                    if e and qty > 0 and price > 0 and key not in seen:
                        seen.add(key)
                        out.append((e, price, tuple(int(c) for c in xy.split(",")), item.lower()))
        return out

    def weapons_unpriced(self):
        """Table weapons of this fighter's main skill (its ammunition, its strength) that no shop list read so far sells: r_window keeps reading lists while there are some."""
        skill = self.main_skill()
        cur, _ = self.weapon_now()
        strength = int(self.c.state.get("str") or 0)
        sold = {norm(item) for _, _, _, item in self.shop_weapons()}
        return [k for k, e in table().items() if e["skill"] == skill and e["str"] <= strength and k not in sold and (not cur or (e["ammo"] or None) == (cur["ammo"] or None))]

    WEAR_S = 3 * 3600            # a "badly worn" notice for the wielded weapon counts this long (or until a weapon is bought)

    def weapon_state(self):
        """What the fighter has in its weapon hand (the live round of 2026-10-21: five melee fighters hunted with their fists): "ok" (a weapon of its own skill wielded, or one in
        the pack that r_gear wields, or an archer in fist mode, which fix C handles), "none" (nothing of its skill wielded or carried), "wrong" (a weapon of another skill) or "worn"
        (the shard's wear notice, "Your club is badly worn: about a quarter of its durability is left", was read for the wielded item, or a journal line said a weapon broke).
        The check: the client's equipped list (layer OneHanded / TwoHanded, the weapon table) and those journal lines; the bots have no durability readout (the server sends it to the
        real client only, extended command 0xA9)."""
        if self.bow_kind() and self.facts.get("fists"):
            return "ok"
        cur, item = self.weapon_now()
        skill = self.main_skill()
        if skill == "Wrestling":
            return "ok"                                              # fists are its weapon (BardBR's best weapon skill is Wrestling): nothing to buy
        if cur is None:
            strength = int(self.c.state.get("str") or 0)
            if any((table().get(norm(i.name)) or {}).get("skill") == skill and (table().get(norm(i.name)) or {}).get("str", 999) <= max(strength, 1) for i in self.c.backpack):
                return "ok"
            return "none"
        if cur["skill"] != skill:
            if self.own_weapon_in_pack() is not None:
                return "ok"                                              # a weapon of its skill waits in the pack: rewield_own puts it in hand (WarAdvR and MaceAdvR held a dagger)
            return "wrong"
        worn = self.facts.get("weapon_worn") or {}
        t = worn.get((item.name or "").lower())
        if t and time.time() - t < self.WEAR_S:
            return "worn"
        return "ok"

    def own_weapon_in_pack(self):
        """The best weapon of the bot's skill in the pack that its strength can wield, else None."""
        skill = self.main_skill()
        strength = int(self.c.state.get("str") or 0)
        best = None
        for i in self.c.backpack:
            e = table().get(norm(i.name))
            if e and e.get("skill") == skill and e.get("str", 999) <= max(strength, 1):
                if best is None or e["value"] > best[0]["value"]:
                    best = (e, i)
        return best[1] if best else None

    def rewield_own(self):
        """A weapon of the bot's skill in the pack while another skill's weapon (the bridge dagger) is in hand: wield the own one. Once a minute."""
        if time.time() - self.__dict__.get("_rewield_at", 0) < 60 or self.threats(6):
            return False
        self.__dict__["_rewield_at"] = time.time()
        if self.bow_kind() and self.facts.get("fists"):
            return False
        cur, item = self.weapon_now()
        if cur is not None and cur["skill"] == self.main_skill():
            return False
        own = self.own_weapon_in_pack()
        if own is None:
            return False
        try:
            if self.wield(own):
                self.ev("rewield_own", item=own.name, was=(item.name if item is not None else None))
                return True
        except Exception:
            pass
        return False

    def next_weapon(self, money, replace=False, shops=None, avoid=()):
        """(score, entry, price, xy, name, current entry) for the weapon to buy now, or None. replace: the weapon in hand is worn out, so any weapon of its class replaces it.
        shops: standing spots of real weapon sellers (the gazetteer's smith, weaponsmith, bowyer): a list read at some other spot (the Tinker's, 100 tiles from the Blacksmith's
        club and long sword) is not a place to buy one, and the shop's own spot replaces the record's (the live round of 2026-10-21: WarAdvR walked to the Tinker twice and
        came back unarmed with 2,473 gold). avoid: spots that did not sell it lately."""
        cur, _ = self.weapon_now()
        skill = self.main_skill()
        if cur and cur.get("skill") != skill:
            # a weapon of another skill is no weapon to match: an archer whose bow broke draws its dagger, and "a bow stays a bow" below then skipped every bow
            # against the one-handed dagger, so needs() never offered the arm task (BotRangerBR hunted 25 hours with a skinning knife at Swordsmanship 8 and
            # Archery 97.9, and died boxed in by four animals, 2026-11-06 11:39)
            cur = None
        strength = int(self.c.state.get("str") or 0)
        cur_value = cur["value"] if cur and not replace else 0.0
        best = None
        for e, price, xy, name in self.shop_weapons():
            if e["skill"] != skill or e["str"] > strength or price > money:
                continue
            if shops is not None:
                near = min(shops, key=lambda s_: max(abs(s_[0] - xy[0]), abs(s_[1] - xy[1])), default=None)
                if near is None or max(abs(near[0] - xy[0]), abs(near[1] - xy[1])) > 12:
                    continue
                xy = tuple(near)
            if tuple(xy) in avoid:
                continue
            if cur and (e["two"] != cur["two"] or (e["ammo"] or None) != (cur["ammo"] or None)):
                continue                                      # a shield stays; a bow stays a bow (bolts are not arrows)
            if not cur and (e["two"] and self.shield_worn() or e["ammo"] and not self.ranged):
                continue
            if e["value"] < cur_value * BETTER or e["value"] <= cur_value:
                continue
            score = (e["value"] - cur_value) / max(price, 1)
            if best is None or score > best[0]:
                best = (score, e, price, xy, name, cur)
        return best

    def r_arms(self):
        if not self.feature("arms"):
            return False
        return self.arms_buy()

    def arms_buy(self):
        """r_arms without its cohort: a better weapon of the bot's main skill (also a hide-hunting tailor's first sword, crafter.hunt_armed)."""
        if self.c.ghost or self.mobs(10) or self.hp_pct() < 70 or time.time() - self.facts.get("arms_at", 0) < EVERY:
            return False
        self.facts["arms_at"] = time.time()
        money = self.mkt_money() - self.UPGRADE_RESERVE
        best = self.next_weapon(money)
        if not best:
            return False
        _, e, price, xy, name, cur = best
        self.activity = f"buying a {name}"
        vfrom, vto = (cur["value"] if cur else 0.0), e["value"]
        self.dlog("choice", what=f"upgrade weapon: {name}", why=f"{price} gold, value {vfrom:.0f} -> {vto:.0f} (damage x speed); money {money + self.UPGRADE_RESERVE}")
        offer = self.mem.best_offer(name, below=price, not_from=self.name)
        if offer:
            if self.c.gold < offer["price"] and self.facts.get("bank_balance", 0) > 0:
                self.visit_bank("trade", withdraw=offer["price"] + 60, reserve=0)
            if self.c.gold >= offer["price"]:
                did = f"{offer['bot']}-{self.name}-{int(time.time())}"
                self.mem.record("mkt", kind="deal", id=did, seller=offer["bot"], buyer=self.name, item=name, qty=1, unit=offer["price"], price=offer["price"], meet=list(self.MEET))
                self.ev("deal_booked", id=did, item=name, qty=1, price=offer["price"], role="buyer", **{"with": offer["bot"]})
                self.facts["arms_at"] = time.time() - 300
                self.facts["weapon_pending"] = {"name": name, "from": offer["bot"], "price": offer["price"], "value_from": vfrom, "value_to": vto}
                return True
        if self.c.gold < price + 10 and self.facts.get("bank_balance", 0) > 0:
            self.visit_bank("weapon", withdraw=price + 60, reserve=0)
        if self.c.gold < price:
            return True
        got = self.shop_at(xy, {"=" + name: 1}, budget=price + 5)
        if not got:
            self.ev("weapon_fail", item=name, why="the shop did not sell it")
            return True
        self.arms_wield(name, price, "shop", vfrom, vto)
        return True

    def arms_wield(self, name, price, source, vfrom, vto):     # not wield(): BotBase.wield(tool) is the hatchet and tool one (a clash, 23:03)
        """Put the bought weapon on in place of the worn one."""
        new = next((i for i in self.c.backpack if i.name.lower() == name), None)
        if not new:
            self.ev("weapon_fail", item=name, why="not in the pack after the purchase")
            return False
        _, old = self.weapon_now()
        if old:
            self.c.unequip(old.serial)
            self.facts.setdefault("gear_failed", {})[old.serial] = time.time() + 10 ** 9      # r_gear must not put the old one back
            time.sleep(0.8)
        try:
            self.c.call(f"equip {new.serial}", timeout=6)
        except Exception:
            pass
        time.sleep(0.8)
        worn = any(i.name.lower() == name for i in self.c.equipped)
        if worn:
            self.facts.pop("weapon_worn", None)                    # a new weapon: the wear notices were about the old one
        self.ev("weapon_buy", item=name, price=price, value_from=round(vfrom), value_to=round(vto), worn=worn, **{"from": source})
        self.log(f"weapon: bought a {name} for {price} gold ({source}); value {vfrom:.0f} -> {vto:.0f}; worn {worn}")
        self.note("gear", f"A {self.pname} bought a {name} for {price} gold and {'wielded it' if worn else 'could not wield it'}.", key=f"weapon:{name}:{worn}")
        return worn
