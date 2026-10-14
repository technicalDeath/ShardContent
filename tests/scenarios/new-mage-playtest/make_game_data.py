"""Builds game_data.json for the mage bot from the ModernUO source, so its decisions rest on the server's own numbers.

    python make_game_data.py        (run from anywhere; reads ModernUO/Projects/UOContent, writes game_data.json beside this file)

monsters: every creature class: default name, hits and damage ranges, virtual armor, fame, karma (what the server will hit the mage with).
spells:   every first to eighth circle Magery spell: circle, mantra, reagents, mana (the 1st..8th table in MagerySpell), the minimum and maximum
          skill of the Magery check (UOR table, Spell.GetCastSkills: min = required[circle + 2], max = min + 40 when cast from a book), and for
          the attack spells the pre-AoS damage range (the Utility.Random(a, b) in the non-AoS branch is a..a+b-1).
Skill gain facts used by the bot (stock SkillCheck.CheckLocation): when the skill is at or above the check's maximum there is no challenge and
no gain roll; below the minimum the check fails; in between the chance is (value - min) / (max - min).
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
UO = os.path.join(ROOT, "ModernUO", "Projects", "UOContent")

MANA = [4, 6, 9, 11, 14, 20, 40, 50]
REQUIRED = [-50.0, -30.0, 0.0, 10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0]  # Core.ML off
CIRCLES = ["First", "Second", "Third", "Fourth", "Fifth", "Sixth", "Seventh", "Eighth"]


def read(path):
    with open(path, encoding="utf-8-sig", errors="replace") as f:
        return f.read()


def monsters():
    out = {}
    base = os.path.join(UO, "Mobiles")
    for folder in ("Animals", "Monsters", "Special"):
        for dirpath, _, files in os.walk(os.path.join(base, folder)):
            for fn in files:
                if not fn.endswith(".cs"):
                    continue
                t = read(os.path.join(dirpath, fn))
                m = re.search(r"class (\w+)\s*:\s*BaseCreature", t)
                if not m:
                    continue
                hits = re.search(r"SetHits\((\d+)(?:,\s*(\d+))?\)", t)
                dmg = re.search(r"SetDamage\((\d+)(?:,\s*(\d+))?\)", t)
                if not hits or not dmg:
                    continue
                name = re.search(r'DefaultName\s*=>\s*"([^"]+)"', t) or re.search(r'Name\s*=\s*"([^"]+)"', t)
                armor = re.search(r"VirtualArmor\s*=\s*(\d+)", t)
                fame = re.search(r"Fame\s*=\s*(\d+)", t)
                karma = re.search(r"Karma\s*=\s*(-?\d+)", t)
                h0 = int(hits.group(1))
                h1 = int(hits.group(2) or h0)
                d0 = int(dmg.group(1))
                d1 = int(dmg.group(2) or d0)
                out[m.group(1).lower()] = {
                    "class": m.group(1),
                    "name": name.group(1) if name else None,
                    "hits": [h0, h1],
                    "damage": [d0, d1],
                    "armor": int(armor.group(1)) if armor else 0,
                    "fame": int(fame.group(1)) if fame else 0,
                    "karma": int(karma.group(1)) if karma else 0,
                    "folder": folder,
                    "casts": bool(re.search(r"Mage|Spell|Magery", t)) and "SetSkill(SkillName.Magery" in t,
                }
    return out


def spells():
    out = {}
    for ci, circle in enumerate(CIRCLES):
        folder = os.path.join(UO, "Spells", circle)
        if not os.path.isdir(folder):
            continue
        for fn in sorted(os.listdir(folder)):
            if not fn.endswith(".cs"):
                continue
            t = read(os.path.join(folder, fn))
            info = re.search(r'new\(\s*"([^"]+)",\s*"([^"]+)"(.*?)\);', t, re.S)
            if not info:
                continue
            reagents = re.findall(r"Reagent\.(\w+)", info.group(3))
            dmg = None
            # the non-AoS damage line is the first plain Utility.Random(a, b) after "else" in Target/OnCast
            mm = re.search(r"damage = Utility\.Random\((\d+),\s*(\d+)\)", t)
            if mm:
                a, b = int(mm.group(1)), int(mm.group(2))
                dmg = [a, a + b - 1]
            mind = re.search(r"Math\.Min\(\(int\)\(\(Caster\.Skills\.Magery\.Value \+ Caster\.Int\) / 5\), 60\)", t)
            mn = REQUIRED[ci + 2]
            out[info.group(1).lower()] = {
                "name": info.group(1),
                "mantra": info.group(2),
                "circle": ci + 1,
                "mana": MANA[ci],
                "reagents": reagents,
                "min_skill": mn,
                "max_skill": mn + 40,
                "damage": dmg,
                "damage_formula": "(Magery + Int) / 5, +0..4" if mind else None,
                "file": f"Spells/{circle}/{fn}",
            }
    return out


def main():
    data = {"monsters": monsters(), "spells": spells(), "reagent_gold": {"SulfurousAsh": 3, "SpidersSilk": 3, "Nightshade": 3, "MandrakeRoot": 3, "Ginseng": 3, "Garlic": 3, "Bloodmoss": 5, "BlackPearl": 5}}
    path = os.path.join(HERE, "game_data.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1, sort_keys=True)
    print(f"{len(data['monsters'])} monsters, {len(data['spells'])} spells -> {path}")


if __name__ == "__main__":
    main()
