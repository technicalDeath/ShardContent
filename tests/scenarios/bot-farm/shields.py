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
        held = [i for i in self.c.equipped if (getattr(i, "layer", "") or "").lower().replace(" ", "") in ("onehanded", "twohanded")]
        return bool(held) and all((i.layer or "").lower().replace(" ", "") == "onehanded" for i in held)

    def r_shield(self):
        import skillplan
        if (self.c.ghost or getattr(self, "ranged", False) or self.mobs(10) or "Parrying" not in (skillplan.plan_of(self) or {})
                or not self.feature("skill_plan")):
            return False
        now = time.time()
        if now - self.facts.get("shield_at", 0) < SHIELD_GAP:
            return False
        sh = self.shield_held()
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
        self.shop_at(where, {name: 1}, budget=max((self.c.gold or 0) - 5, 0))
        time.sleep(1.0)
        sh = self.shield_held()
        if sh is not None:
            self.c.call(f"equip {sh.serial}", timeout=6)
            self.ev("shield_bought", shield=sh.name, price=price)
            self.log(f"shield: bought and wore a {sh.name} (Parrying works only with a shield)")
        return True
