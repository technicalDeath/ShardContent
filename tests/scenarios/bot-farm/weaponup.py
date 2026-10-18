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
        out = []
        for xy, v in self.mem.state["world"]["vendors"].items():
            for item, (price, qty) in v["stock"].items():
                e = table().get(norm(item))
                if e and qty > 0 and price > 0:
                    out.append((e, price, tuple(int(c) for c in xy.split(",")), item.lower()))
        return out

    def weapons_unpriced(self):
        """Table weapons of this fighter's main skill (its ammunition, its strength) that no shop list read so far sells: r_window keeps reading lists while there are some."""
        skill = self.main_skill()
        cur, _ = self.weapon_now()
        strength = int(self.c.state.get("str") or 0)
        sold = {norm(item) for _, _, _, item in self.shop_weapons()}
        return [k for k, e in table().items() if e["skill"] == skill and e["str"] <= strength and k not in sold and (not cur or (e["ammo"] or None) == (cur["ammo"] or None))]

    def next_weapon(self, money):
        """(score, entry, price, xy, name, current entry) for the weapon to buy now, or None."""
        cur, _ = self.weapon_now()
        skill = self.main_skill()
        strength = int(self.c.state.get("str") or 0)
        cur_value = cur["value"] if cur else 0.0
        best = None
        for e, price, xy, name in self.shop_weapons():
            if e["skill"] != skill or e["str"] > strength or price > money:
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
        if not self.feature("arms") or self.c.ghost or self.mobs(10) or self.hp_pct() < 70 or time.time() - self.facts.get("arms_at", 0) < EVERY:
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
        self.ev("weapon_buy", item=name, price=price, value_from=round(vfrom), value_to=round(vto), worn=worn, **{"from": source})
        self.log(f"weapon: bought a {name} for {price} gold ({source}); value {vfrom:.0f} -> {vto:.0f}; worn {worn}")
        self.note("gear", f"A {self.pname} bought a {name} for {price} gold and {'wielded it' if worn else 'could not wield it'}.", key=f"weapon:{name}:{worn}")
        return worn
