"""Writes loot_value.json: what a kill of each creature is worth, from the server's own classes (owner 2026-10-19: casters are too poor; "carving corpses to get
leather and meat can make good money").

    python make_loot_value.py [out.json]       (reads ModernUO/Projects/UOContent/Mobiles; writes loot_value.json beside this file by default)

One entry per BaseCreature subclass, keyed like creature_stats.json and the brains' mkey() (the class name, lower case: "greathart", "zombie"):
  gold        the average gold of its GenerateLoot packs, pre-AOS (LootPack Old*: Poor 1d25, Meager 5d10+25, Average 10d10+50, Rich 10d10+250,
              FilthyRich 2d125+400, UltraRich and SuperBoss 5d100+500), times the pack's count
  extras      the other packs it rolls: scrolls, potions, gems, magic (OldMagicItems in Meager and up)
  hides       Hides, hide_type (Regular / Spined / Horned / Barbed), meat (Meat), meat_type (Ribs / LambLeg / Bird)
  hits        SetHits [min, max] (else SetStr), damage SetDamage, poison_immune (the PoisonImmune level: None, Lesser, Regular, Greater, Deadly, Lethal)
  carve       hides and meat at Britain's prices: plain leather (the hides cut with scissors) 5 at the Tanner, raw ribs 8, lamb leg 4, a bird 3 at the Butcher;
              spined/horned/barbed hides 0 (no Britain shop buys them)
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
if not os.path.isdir(os.path.join(ROOT, "ModernUO")):
    ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
UO = os.path.join(ROOT, "ModernUO", "Projects", "UOContent")

PACK_GOLD = {"Poor": 13.0, "Meager": 52.5, "Average": 105.0, "Rich": 305.0, "FilthyRich": 525.0, "UltraRich": 750.0, "SuperBoss": 750.0}
EXTRA = {"LowScrolls": "scrolls", "MedScrolls": "scrolls", "HighScrolls": "scrolls", "Potions": "potions", "Gems": "gems"}
MAGIC = {"Meager", "Average", "Rich", "FilthyRich", "UltraRich", "SuperBoss"}
LEATHER, MEAT = 5, {"Ribs": 8, "LambLeg": 4, "Bird": 3}
RANGE = r"\(\s*(-?[\d.]+)(?:\s*,\s*(-?[\d.]+))?\s*\)"


def rng(t, name):
    m = re.search(name + RANGE, t)
    if not m:
        return None
    a = float(m.group(1))
    return [a, float(m.group(2)) if m.group(2) else a]


def main(out):
    classes = {}
    for dirpath, _, files in os.walk(os.path.join(UO, "Mobiles")):
        for f in files:
            if f.endswith(".cs"):
                t = open(os.path.join(dirpath, f), encoding="utf-8", errors="replace").read()
                for m in re.finditer(r"class (\w+)\s*:\s*(\w+)", t):
                    classes.setdefault(m.group(1), (t, m.group(2)))
    res = {}
    for cls, (t, base) in classes.items():
        if "GenerateLoot" not in t and "Hides" not in t and "Meat" not in t:
            continue
        m = re.search(r"GenerateLoot\(\)\s*\{(.*?)\n\s*\}", t, re.S)
        packs = re.findall(r"LootPack\.(\w+)(?:\s*,\s*(\d+))?", m.group(1)) if m else []
        gold = sum(PACK_GOLD.get(p, 0.0) * (int(n) if n else 1) for p, n in packs)
        extras = sorted({EXTRA[p] for p, _ in packs if p in EXTRA} | ({"magic"} if any(p in MAGIC for p, _ in packs) else set()))
        hides = int(re.search(r"int Hides\s*=>\s*(\d+)", t).group(1)) if re.search(r"int Hides\s*=>\s*(\d+)", t) else 0
        meat = int(re.search(r"int Meat\s*=>\s*(\d+)", t).group(1)) if re.search(r"int Meat\s*=>\s*(\d+)", t) else 0
        ht = re.search(r"HideType\s*=>\s*HideType\.(\w+)", t)
        mt = re.search(r"MeatType\s*=>\s*MeatType\.(\w+)", t)
        hide_type, meat_type = (ht.group(1) if ht else "Regular"), (mt.group(1) if mt else "Ribs")
        pi = re.search(r"PoisonImmune\s*=>\s*Poison\.(\w+)", t)
        hits = rng(t, r"SetHits") or rng(t, r"SetStr")
        if not (gold or hides or meat):
            continue
        carve = (hides * LEATHER if hide_type == "Regular" else 0) + meat * MEAT.get(meat_type, 3)
        res[cls.lower()] = {"class": cls, "gold": round(gold, 1), "extras": extras, "hides": hides, "hide_type": hide_type, "meat": meat, "meat_type": meat_type,
                            "carve": carve, "hits": hits, "damage": rng(t, r"SetDamage"), "poison_immune": pi.group(1) if pi else None}
    json.dump({"about": __doc__.strip().splitlines()[0], "leather": LEATHER, "meat": MEAT, "pack_gold": PACK_GOLD, "kinds": res},
              open(out, "w", encoding="utf-8"), indent=1, sort_keys=True)
    print(f"{len(res)} creature kinds -> {out}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "loot_value.json"))
