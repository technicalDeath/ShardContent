"""Generate fightmodes.json: how each creature class behaves toward a stranger, from the server's own source, for the bots that only evade real threats (evade.py).
Read-only on the inputs; deterministic.

    python make_fightmodes.py                 # writes fightmodes.json next to this file
    python make_fightmodes.py --check         # exit 1 if fightmodes.json differs from what the inputs would produce

Input: ModernUO Projects/UOContent/Mobiles/{Animals,Monsters,Special}/**/*.cs: base(AIType.X, FightMode.Y, ...) in each BaseCreature subclass (no FightMode argument = the default, Closest). FightMode (BaseCreature.cs):
  None      never focuses on others          Aggressor  only attacks those who attacked it        Evil  an aggressor, or a negative-karma target
  Closest / Strongest / Weakest   attack on sight (what the creature picks first differs)
Keys are the brains' mkey() form, as in creature_stats.json: the class name lower case, and the display name without article and spaces when that is a different key.
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))


def build(mobiles):
    out = {}
    for folder in ("Animals", "Monsters", "Special"):
        for dirpath, _, files in os.walk(os.path.join(mobiles, folder)):
            for fn in sorted(files):
                if not fn.endswith(".cs"):
                    continue
                t = open(os.path.join(dirpath, fn), encoding="utf-8-sig", errors="replace").read()
                m = re.search(r"class (\w+)\s*:\s*BaseCreature", t)
                bm = re.search(r"base\(\s*AIType\.(\w+)(?:\s*,\s*FightMode\.(\w+))?", t)
                if not m or not bm:
                    continue
                entry = {"mode": bm.group(2) or "Closest", "ai": bm.group(1), "class": m.group(1)}       # BaseCreature's default mode is Closest
                out[m.group(1).lower()] = entry
                name = re.search(r'DefaultName\s*=>\s*"([^"]+)"', t) or re.search(r'Name\s*=\s*"([^"]+)"', t)
                if name:
                    key = re.sub(r"[^a-z]", "", re.sub(r"^(an?|the) ", "", name.group(1).lower()))
                    if key and key not in out:
                        out[key] = entry
    return out


def dump(doc):
    return "{\n" + ",\n".join(f"{json.dumps(k)}:{json.dumps(v, sort_keys=True, separators=(',', ':'))}" for k, v in sorted(doc.items())) + "\n}\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mobiles", default=os.path.join(ROOT, "ModernUO", "Projects", "UOContent", "Mobiles"))
    ap.add_argument("--out", default=os.path.join(HERE, "fightmodes.json"))
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    text = dump(build(a.mobiles))
    if a.check:
        same = os.path.exists(a.out) and open(a.out, encoding="utf-8").read() == text
        print("fightmodes.json is up to date" if same else "fightmodes.json DIFFERS from the inputs: run make_fightmodes.py")
        sys.exit(0 if same else 1)
    with open(a.out, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    doc = json.loads(text)
    modes = {}
    for v in doc.values():
        modes[v["mode"]] = modes.get(v["mode"], 0) + 1
    print(f"wrote {a.out}: {len(doc)} keys; modes {modes}")


if __name__ == "__main__":
    main()
