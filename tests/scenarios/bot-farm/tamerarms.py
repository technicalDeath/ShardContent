"""A tamer that fights beside its pet (feature "tamer_weapon"; owner, 2026-11-01: "A tamer could use their pets to hunt, and hunt themselves with a weapon,
so them plus pets hunt to get gold"). The tamer-archer of the era (Stratics archer templates: Archery, Tactics, Taming, Lore, Veterinary, Anatomy,
Healing): the pet holds the monster, the tamer shoots it from behind, and the pet's damage and its own both count for the loot (Publish 5).
docs/Bot-Farm-Skill-Plans.md.

    r_tamer_arms   no bow: buy one (SBRangedWeapon: Bow 40) and ARROWS_BUY arrows (2 each) once carried and banked gold covers them and ARMS_RESERVE;
                   a bow but fewer than ARROWS_MIN arrows: buy arrows. Arrows sold out at every shop known: a crossbow (55) and bolts (3) instead.
                   At the nearest Bowyer, by the shared shop_at.
    tamer_shoot    while the pet fights a hunt target (pethunt.r_pet_hunt), the bow in hand and the same target attacked: once per target
    Veterinary     tamefind.r_pet_heal bandages the pet; with this feature it does so from Veterinary 0 (it needed 20, so the skill never started)
Events: tamer_armed {what, gold}, tamer_shot {target}.
"""
from __future__ import annotations

import re
import time

BOW_PRICE = 40            # SBRangedWeapon: GenericBuyInfo(typeof(Bow), 40, ...)
ARROW_PRICE = 2           # SBRangedWeapon: Arrow 2
CROSSBOW_PRICE = 55       # SBRangedWeapon: Crossbow 55 (Archery, like the bow: 8-43 damage, speed 18 against the bow's 9-41, 20)
BOLT_PRICE = 3            # SBRangedWeapon: Bolt 3
ARROWS_BUY = 50
ARROWS_MIN = 15
ARMS_RESERVE = 60         # gold kept back after the purchase (a bandage restock, the healer's walk)
ARMS_GAP = 900            # s between purchase tries (a sold-out shelf restocks hourly, GenericBuyInfo.OnRestock)

# the two kits a tamer-archer can use: (shop name of the launcher, its price, shop name of the ammunition, its price, the ammunition's name in the pack).
# Every Bowyer near Britain was out of arrows (the archers buy them; memory qty 0 at 1469,1668, 1470,1578 and 1602,1712) while the same shelf held 38
# bolts, 2026-11-01: a real player takes the crossbow then.
KITS = {"bow": ("=bow", BOW_PRICE, "=arrow", ARROW_PRICE, r"arrows?"),
        "crossbow": ("=crossbow", CROSSBOW_PRICE, "=crossbow bolt", BOLT_PRICE, r"(crossbow )?bolts?")}


def launcher_kind(name):
    n = (name or "").strip().lower()
    if n == "crossbow":
        return "crossbow"                                 # not the heavy crossbow (slower, 9 stones)
    if re.search(r"\bbow\b", n) and "crossbow" not in n:
        return "bow"
    return None


class TamerArmsMixin:

    def tamer_bow(self):
        """The bow or crossbow in hand or in the pack."""
        for it in list(self.c.equipped) + list(self.c.backpack):
            if launcher_kind(it.name):
                return it
        return None

    def tamer_ammo(self, kind):
        pat = KITS[kind][4]
        return sum((i.amount or 1) for i in self.c.backpack if re.fullmatch(pat, (i.name or "").strip().lower()))   # not "Arrow Fletching" (a tool)

    def tamer_arrows(self):
        bow = self.tamer_bow()
        return self.tamer_ammo(launcher_kind(bow.name)) if bow is not None else 0

    def ammo_sold_out(self, kind):
        """The shared memory has the ammunition on record at some shop and none of them has any (memory.vendor_selling counts qty > 0 only)."""
        mem = getattr(self, "mem", None)
        if mem is None:
            return False
        word = KITS[kind][2]
        try:
            if mem.vendor_selling(word):
                return False
            vendors = mem.state["world"]["vendors"].values()
            return any(word[1:] in (v.get("stock") or {}) for v in vendors)
        except Exception:
            return False

    def r_tamer_arms(self):
        if not self.feature("tamer_weapon") or self.c.ghost or self.mobs(10):
            return False
        now = time.time()
        if now - self.facts.get("tamer_arms_at", 0) < ARMS_GAP:
            return False
        bow = self.tamer_bow()
        have = launcher_kind(bow.name) if bow is not None else None
        if have and self.tamer_ammo(have) >= ARROWS_MIN:
            return False
        funds = (self.c.gold or 0) + self.facts.get("bank_balance", 0)
        # the kit in hand first (ammunition only), then the other (launcher and ammunition); a kit whose ammunition is sold out at every shop known is passed over
        order = [have, "crossbow" if have == "bow" else "bow"] if have else ["bow", "crossbow"]
        pick = None
        for kind in order:
            if self.ammo_sold_out(kind):
                continue
            launcher, lprice, ammo, aprice, _ = KITS[kind]
            want = {ammo: ARROWS_BUY} if kind == have else {launcher: 1, ammo: ARROWS_BUY}
            cost = (0 if kind == have else lprice) + aprice * ARROWS_BUY
            if funds >= cost + ARMS_RESERVE:
                pick = (kind, want, cost)
                break
        if pick is None:
            return False
        kind, want, cost = pick
        # exact names ("=", shop_at): "arrow" alone matched the Bowyer's "Arrow Fletching" (a fletcher's tool) and the tamer bought 20 of those as arrows
        # (2026-11-01 16:58)
        self.facts["tamer_arms_at"] = now
        if (self.c.gold or 0) < cost and self.facts.get("bank_balance", 0) > 0:
            self.visit_bank("a bow and arrows", withdraw=min(self.facts["bank_balance"], cost + 20))
        if (self.c.gold or 0) < cost:
            # the bank walk can be refused (far.py: too poor for a long walk), and then the shop walk was made with 30 gold for nothing (BotTamerAR,
            # 252 tiles to the Bowyer, "bought {}", 2026-11-01): no shop without the money in the pack
            self.log(f"tamer arms: {self.c.gold} gold carried, {cost} needed: not now")
            return False
        # an exact ammunition name: "arrow" found a mage's shop by its Magic Arrow scroll (1590,1654, 2026-11-01)
        where = self.where1(("bowyer",), item=KITS[kind][2])
        if not where:
            self.log("tamer arms: no Bowyer known")
            return False
        self.activity = f"buying a {kind} kit to fight beside the pet"
        got = self.shop_at(where, want, budget=max((self.c.gold or 0) - 5, 0))
        self.log(f"tamer arms: bought {got} for the hunt ({kind})")
        self.ev("tamer_armed", what=want, kit=kind, got=got, gold=self.c.gold)
        if got and kind != have:
            new = next((i for i in self.c.backpack if launcher_kind(i.name) == kind), None)
            if new is not None:
                self.c.call(f"equip {new.serial}", timeout=6)
        return True

    def tamer_shoot(self, target):
        """Called while the pet fights target (pethunt): the bow or crossbow in hand, the target attacked; once per target (the client keeps attacking it)."""
        if not self.feature("tamer_weapon"):
            return
        h = self.facts.get("pet_target") or {}
        if h.get("shot") == target.serial:
            return
        bow = self.tamer_bow()
        if bow is None or self.tamer_ammo(launcher_kind(bow.name)) <= 0:
            return
        if not any(i.serial == bow.serial for i in self.c.equipped):
            self.c.call(f"equip {bow.serial}", timeout=6)
        self.c.attack(target.serial)
        h["shot"] = target.serial
        self.ev("tamer_shot", target=target.name)
