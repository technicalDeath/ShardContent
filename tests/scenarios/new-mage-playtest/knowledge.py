"""What the mage bot knows about the game, taken from the server's code (game_data.json, built by make_game_data.py) and from what it has seen.

Everything here is arithmetic on those numbers; nothing talks to the game. The bot asks it three questions:

  * which attack spell is best right now?           (attack_options / best_attack)
  * is this monster worth fighting, or must I leave? (assess)
  * which of my actions can still raise Magery?       (gain_window)

The server facts behind it (see make_game_data.py):
  - A Magery check passes with chance (skill - min) / (max - min), min = 0, 10, 20 ... 70 for circles 1 to 8 and max = min + 40. At or above max the
    check is "no challenge": it always passes and rolls no skill gain at all. Below min it always fails (the spell fizzles, mana and reagents gone).
  - Spell damage before the evaluating-intelligence scalar: Magic Arrow 4-7, Harm 1-15, Fireball 10-16, Lightning 12-20, Energy Bolt 24-41.
  - Mana per circle 4, 6, 9, 11, 14, 20, 40, 50. Cast delay 0.5 + 0.25 * circle seconds.
"""
from __future__ import annotations

import json
import math
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
REAGENT_KEYS = {
    "sulfurousash": "SulfurousAsh", "spiderssilk": "SpidersSilk", "spidersilk": "SpidersSilk", "nightshade": "Nightshade", "mandrakeroot": "MandrakeRoot",
    "ginseng": "Ginseng", "garlic": "Garlic", "bloodmoss": "Bloodmoss", "blackpearl": "BlackPearl",
}
SWING_SECONDS = 2.0          # a typical monster's swing speed
ENGAGED = 0.7                # share of the fight a chasing monster is actually in reach


def norm(text: str) -> str:
    return re.sub(r"[^a-z]", "", text.lower())


class Knowledge:
    def __init__(self, path: str | None = None):
        path = path or os.path.join(HERE, "game_data.json")
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        self.monsters = data["monsters"]
        self.spells = data["spells"]
        self.price = data["reagent_gold"]
        self.damage_seen: dict[str, list[float]] = {}    # spell -> [sum, count] of damage numbers the game showed

    # ---- spells -----------------------------------------------------------------------------------------------

    def spell(self, name: str):
        return self.spells.get(name.lower())

    @staticmethod
    def success(spell: dict, skill: float) -> float:
        lo, hi = spell["min_skill"], spell["max_skill"]
        if skill >= hi:
            return 1.0
        if skill < lo:
            return 0.0
        return (skill - lo) / (hi - lo)

    @staticmethod
    def challenging(spell: dict, skill: float) -> bool:
        """True when casting this can still raise the skill: below the maximum (no challenge above it) and not hopeless."""
        return spell["min_skill"] <= skill < spell["max_skill"]

    def avg_damage(self, spell: dict) -> float:
        name = spell["name"].lower()
        seen = self.damage_seen.get(name)
        if seen and seen[1] >= 3:
            return seen[0] / seen[1]            # what the game actually showed beats the formula: the evaluating-intelligence scalar is in it
        d = spell.get("damage")
        return (d[0] + d[1]) / 2.0 if d else 0.0

    def record_damage(self, spell_name: str, amount: float):
        rec = self.damage_seen.setdefault(spell_name.lower(), [0.0, 0])
        rec[0] += amount
        rec[1] += 1

    @staticmethod
    def cast_seconds(spell: dict) -> float:
        return 0.5 + 0.25 * spell["circle"] + 1.0        # the delay plus the bot's own round trip

    def reagent_ok(self, spell: dict, regs: dict) -> bool:
        return all(regs.get(r, 0) > 0 for r in spell["reagents"])

    def gold_per_cast(self, spell: dict) -> int:
        return sum(self.price.get(r, 3) for r in spell["reagents"])

    def attack_options(self, skill: float, mana: int, regs: dict, min_success: float = 0.5):
        """Attack spells the mage can cast right now, best damage per second first."""
        out = []
        for s in self.spells.values():
            if not s.get("damage") and not s.get("damage_formula"):
                continue
            if s["mana"] > mana or not self.reagent_ok(s, regs):
                continue
            ok = self.success(s, skill)
            if ok < min_success:
                continue
            dmg = self.avg_damage(s) or (skill + 39) / 5 + 2
            out.append({
                "spell": s, "success": ok, "dmg": dmg,
                "dps": dmg * ok / self.cast_seconds(s),
                "dmg_per_mana": dmg * ok / s["mana"],
                "gold_per_dmg": self.gold_per_cast(s) / max(dmg * ok, 0.1),
            })
        out.sort(key=lambda o: (-o["dps"], o["gold_per_dmg"]))
        return out

    def best_attack(self, skill, mana, regs, train=False, min_success=0.5):
        """The spell to cast. For training, the highest circle that can still teach (success at least min_success); otherwise the quickest kill."""
        options = self.attack_options(skill, mana, regs, min_success)
        if not options:
            return None
        if train:
            teaching = [o for o in options if self.challenging(o["spell"], skill)]
            if teaching:
                teaching.sort(key=lambda o: -o["spell"]["circle"])
                return teaching[0]
        return options[0]

    # ---- monsters ---------------------------------------------------------------------------------------------

    def monster(self, mobile) -> dict | None:
        """The table entry for a mobile: its body species first ("Ratman"), then its name ("a troll"); None when unknown."""
        for key in (norm(getattr(mobile, "species", None) or ""), norm(re.sub(r"^(an?|the) ", "", mobile.name.lower()))):
            if key and key in self.monsters:
                return self.monsters[key]
        return None

    def assess(self, mobile, hp: int, mana: int, skill: float, regs: dict) -> dict:
        """Can the mage kill this before it kills the mage? expected_damage is what the mage takes while casting the kill."""
        m = self.monster(mobile)
        pick = self.best_attack(skill, mana, regs, min_success=0.8) or self.best_attack(skill, mana, regs, min_success=0.4)
        if m is None or pick is None:
            return {"known": m is not None, "fight": m is not None and m["hits"][1] <= 25 and pick is not None, "reason": "unknown monster" if m is None else "no spell", "monster": m}
        hits = (m["hits"][0] + m["hits"][1]) / 2.0
        armor_factor = 1.0
        casts = math.ceil(hits / max(pick["dmg"] * pick["success"], 0.1))
        seconds = casts * self.cast_seconds(pick["spell"])
        swing = (m["damage"][0] + m["damage"][1]) / 2.0
        taken = seconds / SWING_SECONDS * swing * ENGAGED * armor_factor
        mana_needed = casts * pick["spell"]["mana"]
        fight = taken < 0.6 * hp and mana_needed <= mana
        return {
            "known": True, "fight": fight, "casts": casts, "seconds": round(seconds, 1), "expected_damage": round(taken, 1),
            "mana_needed": mana_needed, "spell": pick["spell"]["name"], "monster": m,
            "reason": f"{casts} x {pick['spell']['name']} ({mana_needed} mana, {seconds:.0f}s) while it hits for ~{swing:.0f}: ~{taken:.0f} damage taken",
        }

    # ---- training ---------------------------------------------------------------------------------------------

    def gain_window(self, skill: float):
        """Spells in order of how useful they are for raising Magery now, with the reason the useless ones are useless."""
        out = []
        for s in sorted(self.spells.values(), key=lambda s: (s["circle"], s["name"])):
            if s["circle"] > 8:
                continue
            if skill >= s["max_skill"]:
                why = "no challenge: always succeeds, never gains"
            elif skill < s["min_skill"]:
                why = "too hard: always fizzles"
            else:
                why = f"can teach: succeeds {self.success(s, skill):.0%}"
            out.append((s["circle"], s["name"], why))
        return out
