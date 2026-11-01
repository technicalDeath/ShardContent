"""Armour for the trades that do not fight for a living (feature "gather_armor"): a miner, fisher or tamer buys leather and studded armour and a helm, as a
Renaissance player working the hills did. A player asks "why does a giant rat kill my miner?" and the answer is that the miner walks the wilds in a robe.

The engine's rules (pre-AOS): a hit lands on one body part (BaseWeapon.AbsorbDamage: neck 7%, hands 7%, arms 14%, head 15%, legs 22%, chest 35%) and the
armour piece there absorbs half to all of its armour rating (BaseArmor.OnHit: ArmorRating/2 + ArmorRating/2 x random). A giant rat hits for 4-8, a slime
1-5, a snake 1-4 (creature_stats.json): studded armour (16, absorbing 8-16) takes the whole of such a hit, leather (13) nearly all of it. The miners died
to giant rats 16 times, to slimes, snakes, mongbats and rabbits besides (2026-10-31), with 100 strength and no armour at all.

Why leather and studded, not ringmail: weight is carried ore (a ringmail suit is 47 stones, studded 19, leather 14: Items/Armor DefaultWeight), and metal
costs dexterity (ringmail -5 for the suit, plate -19: OldDexBonus), which before AOS is the stamina a gatherer runs on. The head takes a close helm (30, 5
stones, no dexterity cost) where the strength allows, else a leather cap. Britain's armourers and its tanner sell them (Armorer: one of four stock sets,
two with leather and studded; prices from the shared memory, 158 for a studded tunic on this shard).

The buying itself is HunterBot's (r_upgrade, next_upgrade, worn_ar): once in ten minutes, the most armour per gold among the pieces it can wear and the
shelves it knows, with UPGRADE_RESERVE kept for potions and bandages; saving for a goal (goals.py), only the goal's piece.
"""
from __future__ import annotations

import time

from hunter import HunterBot

# per paperdoll layer: (shop name, armour rating, strength needed, dexterity cost), from Items/Armor (ArmorBase, OldStrReq, OldDexBonus)
GATHER_ARMOR = {
    "Torso": [("leather tunic", 13, 15, 0), ("studded tunic", 16, 35, 0)],
    "Pants": [("leather leggings", 13, 10, 0), ("studded leggings", 16, 35, 0)],
    "Arms": [("leather sleeves", 13, 15, 0), ("studded sleeves", 16, 25, 0)],
    "Gloves": [("leather gloves", 13, 10, 0), ("studded gloves", 16, 25, 0)],
    "Necklace": [("leather gorget", 13, 10, 0), ("studded gorget", 16, 25, 0)],
    "Helmet": [("leather cap", 13, 15, 0), ("close helm", 30, 40, 0)],
}


class GathererArmor:
    ARMOR_BUY = GATHER_ARMOR
    SLOT_SHARE = HunterBot.SLOT_SHARE
    WORN_AR = HunterBot.WORN_AR
    worn_ar = HunterBot.worn_ar
    next_upgrade = HunterBot.next_upgrade
    UPGRADE_RESERVE = HunterBot.UPGRADE_RESERVE
    ranged = False

    def bow_kind(self):
        return None                                       # (HunterBot.r_upgrade and UPGRADE_RESERVE ask)

    def weapon_state(self):
        return "ok"                                       # a gatherer's tool is not a weapon: no weapon before armour

    SHOP_FROM = 150           # tiles from a bank: a player buys armour on a town visit, not as a walk of its own from the hills (Britain's north smiths, where
                              # the miners sell, are 143 from its main bank; the gazetteer's town area takes in the western hills and cannot be the test)

    def in_town_now(self):
        """Within SHOP_FROM of a bank."""
        try:
            return any(max(abs(self.c.x - bx), abs(self.c.y - by)) <= self.SHOP_FROM for bx, by in self.bank_xys())
        except Exception:
            return False

    def r_upgrade(self):
        """HunterBot.r_upgrade, asked as a working player asks it: in town (SHOP_FROM of the bank), with no threat about. HunterBot's own test is "no mobile
        of grey notoriety within 10", which in the hills is always a rabbit or a hind: the miners never once got past it (2026-10-31)."""
        if not self.feature("gather_armor") or self.threats(10):
            return False
        if not self.in_town_now():
            return False
        self.__dict__["mobs"] = lambda r: []
        try:
            return HunterBot.r_upgrade(self)
        finally:
            self.__dict__.pop("mobs", None)

    ERRAND_PIECES = 6         # the suit: torso, legs, arms, gloves, gorget, helm

    def armor_errand(self):
        """After a bank visit, the pieces it can afford, one shop walk each (BotBase.visit_bank calls it). A miner banks inside its selling and digging rules
        and walks straight back to the hills, so the armour rule never had a tick in town (2026-10-31); a player buys the suit on the bank trip."""
        if not self.feature("gather_armor") or self.__dict__.get("_armor_errand"):
            return 0
        th = self.threats(10)
        if th:
            if time.time() - self.__dict__.get("_errand_logged", 0) > 600:
                self.__dict__["_errand_logged"] = time.time()
                self.log(f"armour errand skipped: threats near the bank {[getattr(m, 'name', '?') for m in th][:3]}")
            return 0
        self.__dict__["_armor_errand"] = True
        bought = 0
        try:
            for _ in range(self.ERRAND_PIECES):
                n = len(self.facts.get("upgrades") or [])
                self.facts["upgrade_at"] = 0
                if not self.r_upgrade() or len(self.facts.get("upgrades") or []) == n:
                    break
                bought += 1
        finally:
            self.__dict__.pop("_armor_errand", None)
        if time.time() - self.__dict__.get("_errand_logged", 0) > 600:
            self.__dict__["_errand_logged"] = time.time()
            self.log(f"armour errand at {getattr(self.c, 'x', '?')},{getattr(self.c, 'y', '?')}: {bought} piece(s) bought")
        return bought
