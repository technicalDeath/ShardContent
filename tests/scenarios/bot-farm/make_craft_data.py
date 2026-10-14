"""Reads the server's crafting definitions (DefBlacksmithy/Tailoring/Tinkering/Carpentry.cs) and writes craft_data.json: for each craft, every item's name
(spaced the way the legacy craft menu spells it), the skill window it can teach in, and the material it costs.

    python make_craft_data.py
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
CRAFT = os.path.join(HERE, "..", "..", "..", "..", "ModernUO", "Projects", "UOContent", "Engines", "Craft")
FILES = {"Blacksmith": "DefBlacksmithy.cs", "Tailoring": "DefTailoring.cs", "Tinkering": "DefTinkering.cs", "Carpentry": "DefCarpentry.cs"}
PAT = re.compile(r"AddCraft\(typeof\((\w+)\),\s*[^,]+,\s*[^,]+,\s*(?:\d+,\s*)?(-?[\d.]+),\s*(-?[\d.]+),\s*typeof\((\w+)\),\s*[^,]+,\s*(\d+)")


def spaced(name):
    return re.sub(r"(?<!^)(?=[A-Z])", " ", name).lower()


out = {}
for craft, fn in FILES.items():
    text = open(os.path.join(CRAFT, fn), encoding="utf-8").read()
    items = {}
    for m in PAT.finditer(text):
        t, lo, hi, res, amount = m.groups()
        items[spaced(t)] = {"type": t, "min": float(lo), "max": float(hi), "resource": res, "amount": int(amount)}
    out[craft] = items
    print(craft, len(items))
json.dump(out, open(os.path.join(HERE, "craft_data.json"), "w"), indent=1, sort_keys=True)
