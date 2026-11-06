"""A shield for a one-handed melee fighter (skill plans, docs/Bot-Farm-Skill-Plans.md; owner, 2026-11-01: "making bots more capable, specifically using more
skills to be more effective"). The dexxer of the era carried a heater: Parrying blocks blows only with a shield, and rises only with one (a sword, mace or
fencer bot had 60-75 Parrying and no shield, so the skill did nothing and never rose, 2026-11-01). The shield's own armour counts too.

    r_shield   a one-handed weapon in hand, no shield in hand or in the pack, the plan holding Parrying: the best shield carried and banked gold buys with
               SHIELD_RESERVE to spare, from the Blacksmith (SBBlacksmith / SBMetalShields), then worn
Events: shield_bought {shield, price}.
"""
from __future__ import annotations

import re
import time

# (client name, price, armour): SBBlacksmith / SBMetalShields prices, ArmorBase of each shield class
SHIELDS = (("heater shield", 231, 23), ("metal kite shield", 123, 16), ("wooden kite shield", 70, 12), ("buckler", 50, 7))
SHIELD_RESERVE = 300
SHIELD_GAP = 1800


def is_shield(name):
    n = (name or "").lower()
    return "shield" in n or "buckler" in n


class ShieldMixin:

    def shield_held(self):
        return next((i for i in list(self.c.equipped) + list(self.c.backpack) if is_shield(i.name)), None)

    def one_handed(self):
        """The weapon in hand is one-handed (a shield, on the two-handed layer, is not the weapon: a worn one in hand must not block its replacement)."""
        held = [i for i in self.c.equipped if (getattr(i, "layer", "") or "").lower().replace(" ", "") in ("onehanded", "twohanded") and not is_shield(i.name)]
        return bool(held) and all((i.layer or "").lower().replace(" ", "") == "onehanded" for i in held)

    def r_shield(self):
        import skillplan
        if (self.c.ghost or getattr(self, "ranged", False) or self.mobs(10) or "Parrying" not in (skillplan.plan_of(self) or {})
                or not self.feature("skill_plan")):
            return False
        now = time.time()
        if now - self.facts.get("shield_at", 0) < SHIELD_GAP:
            return False
        if self.facts.get("dungeon_hunt"):
            # no bank trip out of a dungeon stay: BotHealAdvR's heater broke 5 minutes into Despise and r_shield walked it out to the bank, ending a
            # 40-minute stay that was looting 50 gold a lizardman (2026-11-06 17:44). The stay's own checks (health, kit) say when to leave
            return False
        sh = self.shield_held()
        worn = bool(sh is not None and (self.facts.get("weapon_worn") or {}).get((sh.name or "").lower()))
        if sh is not None and worn and any(i.serial == sh.serial for i in self.c.equipped):
            # the shard's wear notice ("Your heater shield is badly worn: about a quarter of its durability is left"): replaced in town, before it breaks in
            # a dungeon (BotHealAdvR read it at 06:15 and carried it 11 hours, into Despise, where it broke)
            sh = None
        if sh is not None:
            if not any(i.serial == sh.serial for i in self.c.equipped) and self.one_handed():
                self.c.call(f"equip {sh.serial}", timeout=6)          # bought before, or picked up: worn
                self.facts["shield_at"] = now
                return True
            return False
        if not self.one_handed():
            return False
        funds = (self.c.gold or 0) + self.facts.get("bank_balance", 0)
        pick = next((s for s in SHIELDS if funds >= s[1] + SHIELD_RESERVE), None)
        self.facts["shield_at"] = now
        if pick is None:
            return False
        name, price, _ar = pick
        if (self.c.gold or 0) < price and self.facts.get("bank_balance", 0) > 0:
            self.visit_bank("a shield", withdraw=min(self.facts["bank_balance"], price + 20))
        if (self.c.gold or 0) < price:
            return False
        where = self.where1(("blacksmith", "armourer"), item=name)
        if not where:
            return False
        self.activity = f"buying a {name}"
        old = next((i for i in self.c.equipped if is_shield(i.name)), None)        # a worn one still in hand (above)
        self.shop_at(where, {name: 1}, budget=max((self.c.gold or 0) - 5, 0))
        time.sleep(1.0)
        sh = next((i for i in self.c.backpack if is_shield(i.name) and (old is None or i.serial != old.serial)), None) or self.shield_held()
        if sh is not None and (old is None or sh.serial != old.serial):
            if old is not None:
                self.c.unequip(old.serial)
                self.facts.setdefault("gear_failed", {})[old.serial] = time.time() + 10 ** 9      # r_gear must not put the worn one back
                time.sleep(0.8)
            (self.facts.get("weapon_worn") or {}).pop((sh.name or "").lower(), None)          # the notice was about the old one
            self.c.call(f"equip {sh.serial}", timeout=6)
            self.ev("shield_bought", shield=sh.name, price=price)
            self.log(f"shield: bought and wore a {sh.name} (Parrying works only with a shield)")
        return True
