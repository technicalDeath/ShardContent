"""Generate spellids.json: the Magery spell table (name, spell id 0-63, circle) the casters use to read their spellbook. Read-only on the inputs; deterministic.

    python make_spellids.py                 # writes spellids.json next to this file
    python make_spellids.py --check         # exit 1 if spellids.json differs from what the inputs would produce

Inputs: ModernUO Projects/UOContent/Spells/Initializer.cs (Register(NN, typeof(XSpell)): the server's own spell ids) and the caster knowledge
new-mage-playtest/game_data.json (name, circle, mana, file of every spell; the file name Spells/Second/Agility.cs gives the class AgilitySpell).
The id is what the spellbook's content packet lists: a book holds spell n when bit n of its content is set; the client shows each held spell as a child of
the book with Amount = id + 1.
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))


def build(init_cs, game_data):
    ids = {m.group(2): int(m.group(1)) for m in re.finditer(r"Register\((\d+),\s*typeof\((\w+)\)\)", open(init_cs, encoding="utf-8").read()) if int(m.group(1)) < 64}
    spells = json.load(open(game_data, encoding="utf-8"))["spells"]
    out = {}
    for name, s in sorted(spells.items()):
        cls = os.path.basename(s["file"])[:-3] + "Spell"
        if cls not in ids:
            raise SystemExit(f"no spell id for {name} ({cls})")
        out[name] = dict(id=ids[cls], circle=s["circle"], name=s["name"], mana=s["mana"])
    return dict(schema=1, note="Magery spells: name (lower case) -> server spell id, circle; scroll name is '<name> Scroll'", spells=out)


def dump(doc):
    return "{\n" + f'"schema":{doc["schema"]},\n"note":{json.dumps(doc["note"])},\n"spells":{{\n' + ",\n".join(f"{json.dumps(k)}:{json.dumps(v, separators=(',', ':'), sort_keys=True)}" for k, v in doc["spells"].items()) + "\n}\n}\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--init", default=os.path.join(ROOT, "ModernUO", "Projects", "UOContent", "Spells", "Initializer.cs"))
    ap.add_argument("--gamedata", default=os.path.join(HERE, "..", "new-mage-playtest", "game_data.json"))
    ap.add_argument("--out", default=os.path.join(HERE, "spellids.json"))
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    text = dump(build(a.init, a.gamedata))
    if a.check:
        same = os.path.exists(a.out) and open(a.out, encoding="utf-8").read() == text
        print("spellids.json is up to date" if same else "spellids.json DIFFERS from the inputs: run make_spellids.py")
        sys.exit(0 if same else 1)
    with open(a.out, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print(f"wrote {a.out}: {len(json.loads(text)['spells'])} spells")


if __name__ == "__main__":
    main()
