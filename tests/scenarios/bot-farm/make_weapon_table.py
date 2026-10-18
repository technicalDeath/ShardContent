"""Generate weapon_table.json: what each weapon class does before AOS (this shard's era), from the server's own source, for the fighters' weapon upgrades (weaponup.py).
Read-only on the inputs; deterministic.

    python make_weapon_table.py                 # writes weapon_table.json next to this file
    python make_weapon_table.py --check         # exit 1 if weapon_table.json differs from what the inputs would produce

Input: ModernUO Projects/UOContent/Items/Weapons/**/*.cs. Per class: OldStrengthReq / OldMinDamage / OldMaxDamage / OldSpeed (the pre-AOS numbers: Core.AOS is false here), the skill
(DefSkill of the class or of its base: swords, axes, knives and pole arms Swordsmanship, maces and staves Mace Fighting, spears and forks Fencing, bows Archery), Layer.TwoHanded in
the constructor, AmmoType for ranged weapons. Keys are the lower-case class name without punctuation ("longsword", "warmace", "heavycrossbow"), which is also how the brains
normalise a shop's item names. value = average damage x speed: the swing delay is 15000 / ((dexterity + 100) x speed), so damage per second is proportional to it.
"""
import argparse
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
SRC = os.path.join(ROOT, "ModernUO", "Projects", "UOContent", "Items", "Weapons")
OUT = os.path.join(HERE, "weapon_table.json")
SKILLS = {"Swords": "Swordsmanship", "Macing": "Mace Fighting", "Fencing": "Fencing", "Archery": "Archery", "Wrestling": "Wrestling", "Throwing": "Throwing"}
# two-handed by the art (tiledata layer), not by a Layer assignment in the class: the source does not say, the era's list does
TWO_HANDED_ART = {"twohandedaxe", "compositebow", "halberd", "bardiche", "quarterstaff", "gnarledstaff", "blackstaff", "pike", "scythe", "lance", "largebattleaxe", "executionersaxe", "battleaxe",
                  "warhammer", "bow", "crossbow", "heavycrossbow"}
BASES = {"BaseSword": "Swords", "BaseAxe": "Swords", "BaseKnife": "Swords", "BasePoleArm": "Swords", "BaseBashing": "Macing", "BaseStaff": "Macing", "BaseSpear": "Fencing",
         "BaseRanged": "Archery"}


def norm(t):
    return re.sub(r"[^a-z]", "", t.lower())


def build():
    out = {}
    for f in sorted(glob.glob(os.path.join(SRC, "**", "*.cs"), recursive=True)):
        t = open(f, encoding="utf-8-sig", errors="replace").read()
        m = re.search(r"class (\w+)\s*:\s*(\w+)", t)
        if not m or m.group(2) not in BASES and not m.group(2).startswith("Base"):
            continue
        cls, base = m.group(1), m.group(2)
        if base not in BASES:
            continue
        g = lambda p: (re.search(p, t) or [None, None])[1]
        lo, hi, spd, st = g(r"OldMinDamage\s*=>\s*(\d+)"), g(r"OldMaxDamage\s*=>\s*(\d+)"), g(r"OldSpeed\s*=>\s*(\d+)"), g(r"OldStrengthReq\s*=>\s*(\d+)")
        if lo is None or hi is None or spd is None:
            continue
        skill = g(r"DefSkill\s*=>\s*SkillName\.(\w+)") or BASES[base]
        ammo = g(r"AmmoType\s*=>\s*typeof\((\w+)\)")
        out[norm(cls)] = {"class": cls, "skill": SKILLS.get(skill, skill), "str": int(st or 0), "min": int(lo), "max": int(hi), "speed": int(spd),
                          "two": "Layer.TwoHanded" in t or norm(cls) in TWO_HANDED_ART, "ammo": ammo.lower() if ammo else None, "value": round((int(lo) + int(hi)) / 2.0 * int(spd), 1)}
    return {"schema": 1, "note": "pre-AOS weapon stats by normalised class name (make_weapon_table.py); value = average damage x speed", "weapons": out}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    text = json.dumps(build(), indent=1, sort_keys=True) + "\n"
    if a.check:
        cur = open(OUT, encoding="utf-8").read() if os.path.exists(OUT) else ""
        if cur.replace("\r\n", "\n") != text:
            print("weapon_table.json differs from the inputs")
            return 1
        print("weapon_table.json is current")
        return 0
    open(OUT, "w", encoding="utf-8", newline="\n").write(text)
    print(f"{len(json.loads(text)['weapons'])} weapons")
    return 0


if __name__ == "__main__":
    sys.exit(main())
