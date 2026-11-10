"""Leather armour for casters (feature "caster_armor"; owner, 2026-11-09: "Are casters wearing armor and using mounts?"). All eight casters wore a robe and
nothing else.

The engine's rules (pre-AOS): leather does not slow a caster's mana. RegenRates.GetArmorOffset adds a piece's armour rating to the mana regeneration delay
by its MeditationAllowance: leather is All (no penalty: Items/Armor/Leather, DefMedAllowance All), studded Half, metal and bone None; casting itself is
never hindered by armour before AOS. A hit lands on one body part and that piece absorbs half to all of its rating (BaseArmor.OnHit, wear.py): leather
(13, absorbing 6-13 on its part) takes most of a lizardman's 4-5 on a player and much of an ettin's 5-10, so the stair hold's bouts last longer.

The buying is the gatherers' (wear.GathererArmor: HunterBot.r_upgrade in town with real threats only, the most armour per gold among the shelves the
shared memory knows), on a leather-only list.
"""
from __future__ import annotations

from hunter import HunterBot
from wear import GATHER_ARMOR, GathererArmor

# per paperdoll layer: the leather piece only (studded halves Meditation's work, metal stops it)
CASTER_ARMOR = {layer: [p for p in pieces if p[0].startswith("leather")] for layer, pieces in GATHER_ARMOR.items()}


class CasterArmor:
    ARMOR_BUY = CASTER_ARMOR
    SLOT_SHARE = HunterBot.SLOT_SHARE
    WORN_AR = HunterBot.WORN_AR
    worn_ar = HunterBot.worn_ar
    next_upgrade = HunterBot.next_upgrade
    UPGRADE_RESERVE = HunterBot.UPGRADE_RESERVE
    SHOP_FROM = GathererArmor.SHOP_FROM
    ERRAND_PIECES = GathererArmor.ERRAND_PIECES
    in_town_now = GathererArmor.in_town_now
    armor_errand = GathererArmor.armor_errand
    ranged = False

    def bow_kind(self):
        return None

    def weapon_state(self):
        return "ok"                                       # a caster's weapon is its spellbook

    def r_upgrade(self):
        """In town (within SHOP_FROM of a bank), nothing hostile about, never inside a dungeon: the next leather piece (HunterBot.r_upgrade)."""
        if not self.feature("caster_armor") or self.facts.get("dungeon_hunt") or self.threats(10):
            return False
        if not self.in_town_now():
            return False
        self.__dict__["mobs"] = lambda r: []
        try:
            return HunterBot.r_upgrade(self)
        finally:
            self.__dict__.pop("mobs", None)
