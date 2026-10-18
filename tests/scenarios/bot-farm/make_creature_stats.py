"""Writes creature_stats.json: what the server's own creature classes say about every monster, for the danger model's prior (danger.py).

    python make_creature_stats.py [out.json]       (reads ModernUO/Projects/UOContent/Mobiles; writes creature_stats.json beside this file by default)

One entry per BaseCreature subclass, keyed like the brains' mkey() (the body species / name without spaces or articles, lower case: "grizzlybear", "orc", "acidelemental"):
  hits [min, max]            SetHits (else SetStr: a creature's hit points follow its strength)
  str, dex, int [min, max]   SetStr / SetDex / SetInt
  damage [min, max]          SetDamage (its natural attack: wrestling damage)
  wrestling, tactics, resist, magery, evalint   [min, max]   SetSkill(Wrestling / Tactics / MagicResist / Magery / EvalInt)
  armor                      VirtualArmor
  poison                     HitPoison (a property: Lesser, Regular, Greater, Deadly, Lethal; the worst one named) or null
  abilities                  MonsterAbilities.* named in the class (FireBreath, ColdBreath, ...)
  breath                     one of them is a breath (dragons, drakes, ...)
  ai                         AI_Melee, AI_Mage, AI_Archer, AI_Animal, AI_Predator, AI_Thief ...
  casts                      Magery skill set (it throws spells)
  name, class, folder, fame, karma
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
if not os.path.isdir(os.path.join(ROOT, "ModernUO")):                    # installed beside the brains (ShardContent/tests/scenarios/bot-farm)
    ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
UO = os.path.join(ROOT, "ModernUO", "Projects", "UOContent")
RANGE = r"\(\s*(-?[\d.]+)(?:\s*,\s*(-?[\d.]+))?\s*\)"


def read(path):
    with open(path, encoding="utf-8-sig", errors="replace") as f:
        return f.read()


def rng(text, call):
    m = re.search(call + RANGE, text)
    if not m:
        return None
    a = float(m.group(1))
    b = float(m.group(2)) if m.group(2) else a
    return [a, b]


def skill(text, name):
    m = re.search(r"SetSkill\(\s*SkillName\." + name + r"\s*,\s*([\d.]+)(?:\s*,\s*([\d.]+))?\s*\)", text)
    if not m:
        return None
    a = float(m.group(1))
    return [a, float(m.group(2)) if m.group(2) else a]


def creatures():
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
                dmg = rng(t, r"SetDamage")
                hits = rng(t, r"SetHits")
                strength = rng(t, r"SetStr")
                if not dmg or not (hits or strength):
                    continue
                name = re.search(r'DefaultName\s*=>\s*"([^"]+)"', t) or re.search(r'Name\s*=\s*"([^"]+)"', t)
                hp_stmt = re.search(r"HitPoison\s*(?:=>|=)\s*([^;]*);", t)
                kinds = re.findall(r"Poison\.(\w+)", hp_stmt.group(1)) if hp_stmt else []
                order = ["Lesser", "Regular", "Greater", "Deadly", "Lethal"]
                poison = max(kinds, key=lambda k: order.index(k) if k in order else -1) if kinds else None      # the worst named (a creature may roll between two)
                ai = re.search(r"AIType\.(\w+)", t)
                armor = re.search(r"VirtualArmor\s*=\s*(\d+)", t)
                fame = re.search(r"Fame\s*=\s*(\d+)", t)
                karma = re.search(r"Karma\s*=\s*(-?\d+)", t)
                entry = {
                    "class": m.group(1), "name": name.group(1) if name else None, "folder": folder,
                    "hits": hits or strength, "str": strength, "dex": rng(t, r"SetDex"), "int": rng(t, r"SetInt"), "damage": dmg,
                    "wrestling": skill(t, "Wrestling"), "tactics": skill(t, "Tactics"), "resist": skill(t, "MagicResist"),
                    "magery": skill(t, "Magery"), "evalint": skill(t, "EvalInt"),
                    "armor": int(armor.group(1)) if armor else 0,
                    "poison": poison,
                    "abilities": sorted(set(re.findall(r"MonsterAbilities\.(\w+)", t))),
                    "breath": bool(re.search(r"MonsterAbilities\.\w*Breath", t)) or bool(re.search(r"HasBreath\s*(?:=|=>)\s*true", t)),
                    "ai": ai.group(1) if ai else None,
                    "casts": skill(t, "Magery") is not None,
                    "fame": int(fame.group(1)) if fame else 0, "karma": int(karma.group(1)) if karma else 0,
                }
                out[m.group(1).lower()] = entry
                if name:
                    key = re.sub(r"[^a-z]", "", re.sub(r"^(an?|the) ", "", name.group(1).lower()))
                    if key and key not in out:
                        out[key] = entry                                  # the name without article, spaces: the brains' mkey() for a creature whose species is unknown
    return out


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "creature_stats.json")
    data = creatures()
    with open(out, "w", encoding="utf-8") as f:                       # one creature per line
        f.write("{"+"\n" + (","+"\n").join(f"{json.dumps(k)}: {json.dumps(v, sort_keys=True)}" for k, v in sorted(data.items())) + "\n}\n")
    print(f"{len({e['class'] for e in data.values()})} creatures ({len(data)} keys) -> {out}")


if __name__ == "__main__":
    main()
