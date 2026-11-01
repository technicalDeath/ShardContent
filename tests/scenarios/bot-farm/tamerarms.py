"""A tamer that fights beside its pet (feature "tamer_weapon"; owner, 2026-11-01: "A tamer could use their pets to hunt, and hunt themselves with a weapon,
so them plus pets hunt to get gold"). The tamer-archer of the era (Stratics archer templates: Archery, Tactics, Taming, Lore, Veterinary, Anatomy,
Healing): the pet holds the monster, the tamer shoots it from behind, and the pet's damage and its own both count for the loot (Publish 5).
docs/Bot-Farm-Skill-Plans.md.

    r_tamer_arms   no bow: buy one (SBRangedWeapon: Bow 40) and ARROWS_BUY arrows (2 each) once carried and banked gold covers them and ARMS_RESERVE;
                   a bow but fewer than ARROWS_MIN arrows: buy arrows. At the nearest Bowyer, by the shared shop_at.
    tamer_shoot    while the pet fights a hunt target (pethunt.r_pet_hunt), the bow in hand and the same target attacked: once per target
    Veterinary     tamefind.r_pet_heal bandages the pet; with this feature it does so from Veterinary 0 (it needed 20, so the skill never started)
Events: tamer_armed {what, gold}, tamer_shot {target}.
"""
from __future__ import annotations

import re
import time

BOW_PRICE = 40            # SBRangedWeapon: GenericBuyInfo(typeof(Bow), 40, ...)
ARROW_PRICE = 2           # SBRangedWeapon: Arrow 2
ARROWS_BUY = 50
ARROWS_MIN = 15
ARMS_RESERVE = 60         # gold kept back after the purchase (a bandage restock, the healer's walk)
ARMS_GAP = 900            # s between purchase tries (a sold-out shelf restocks hourly, GenericBuyInfo.OnRestock)


class TamerArmsMixin:

    def tamer_bow(self):
        """The bow in hand or in the pack."""
        for it in list(self.c.equipped) + list(self.c.backpack):
            if re.search(r"\bbow\b", (it.name or "").lower()) and "crossbow" not in (it.name or "").lower():
                return it
        return None

    def tamer_arrows(self):
        return sum((i.amount or 1) for i in self.c.backpack if re.fullmatch(r"arrows?", (i.name or "").strip().lower()))      # not "Arrow Fletching" (a tool)

    def r_tamer_arms(self):
        if not self.feature("tamer_weapon") or self.c.ghost or self.mobs(10):
            return False
        now = time.time()
        if now - self.facts.get("tamer_arms_at", 0) < ARMS_GAP:
            return False
        bow, arrows = self.tamer_bow(), self.tamer_arrows()
        want = {}
        if bow is None:
            want = {"=bow": 1, "=arrow": ARROWS_BUY}
        elif arrows < ARROWS_MIN:
            want = {"=arrow": ARROWS_BUY}
        if not want:
            return False
        # exact names ("=", shop_at): "arrow" alone matched the Bowyer's "Arrow Fletching" (a fletcher's tool) and the tamer bought 20 of those as arrows
        # (2026-11-01 16:58)
        cost = (BOW_PRICE if "=bow" in want else 0) + ARROW_PRICE * want["=arrow"]
        funds = (self.c.gold or 0) + self.facts.get("bank_balance", 0)
        if funds < cost + ARMS_RESERVE:
            return False
        self.facts["tamer_arms_at"] = now
        if (self.c.gold or 0) < cost and self.facts.get("bank_balance", 0) > 0:
            self.visit_bank("a bow and arrows", withdraw=min(self.facts["bank_balance"], cost + 20))
        if (self.c.gold or 0) < cost:
            # the bank walk can be refused (far.py: too poor for a long walk), and then the shop walk was made with 30 gold for nothing (BotTamerAR,
            # 252 tiles to the Bowyer, "bought {}", 2026-11-01): no shop without the money in the pack
            self.log(f"tamer arms: {self.c.gold} gold carried, {cost} needed: not now")
            return False
        where = self.where1(("bowyer",), item="arrow")
        if not where:
            self.log("tamer arms: no Bowyer known")
            return False
        self.activity = "buying a bow and arrows to fight beside the pet"
        got = self.shop_at(where, want, budget=max((self.c.gold or 0) - 5, 0))
        self.log(f"tamer arms: bought {got} for the hunt")
        self.ev("tamer_armed", what=want, gold=self.c.gold)
        return True

    def tamer_shoot(self, target):
        """Called while the pet fights target (pethunt): bow in hand, the target attacked; once per target (the client keeps attacking it)."""
        if not self.feature("tamer_weapon"):
            return
        h = self.facts.get("pet_target") or {}
        if h.get("shot") == target.serial:
            return
        bow = self.tamer_bow()
        if bow is None or self.tamer_arrows() <= 0:
            return
        if not any(i.serial == bow.serial for i in self.c.equipped):
            self.c.call(f"equip {bow.serial}", timeout=6)
        self.c.attack(target.serial)
        h["shot"] = target.serial
        self.ev("tamer_shot", target=target.name)
