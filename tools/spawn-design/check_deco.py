"""Checks that no decoration piece in deco.json shares its art with something a player can own or pick up: every art id
is searched for in ModernUO's content code (UOContent), and any hit that is not in deco.json's 'allowed' list fails.
Also fails ids at 0x2000 or above (after the shard's era) and ids with no art. Exit 1 on any failure.

  python check_deco.py
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", "..", "..", "ModernUO", "Projects", "UOContent"))
sys.path.insert(0, os.path.join(HERE, "..", "cosmetic-catalog"))
import uoart  # noqa: E402


def main():
    d = json.load(open(os.path.join(HERE, "deco.json"), encoding="utf-8"))
    allowed = {int(k, 16) for k in d.get("allowed", {})}
    used = {}
    for key, t in d.get("flavor", {}).items():
        for name, hexid in t["pieces"]:
            used.setdefault(int(hexid, 16), []).append("%s (flavor %s)" % (name, key))
            if hexid in d.get("assemblies", {}):
                used[int(hexid, 16)].append("MULTI-PIECE")
    for key, t in d["themes"].items():
        for role in ("anchor", "supports", "accents"):
            for name, hexid in t[role]:
                used.setdefault(int(hexid, 16), []).append("%s (%s)" % (name, key))
                for _, _, part in d.get("assemblies", {}).get(hexid, {}).get("parts", []):
                    used.setdefault(int(part, 16), []).append("part of %s (%s)" % (name, key))
    hits = {}
    pat = re.compile(r"0x([0-9A-Fa-f]{3,4})\b")
    for dp, _, files in os.walk(ROOT):
        for f in files:
            if f.endswith(".cs"):
                for m in pat.finditer(open(os.path.join(dp, f), encoding="utf-8", errors="ignore").read()):
                    v = int(m.group(1), 16)
                    if v in used:
                        hits.setdefault(v, set()).add(f)
    bad = 0
    for v, who in sorted(used.items()):
        why = []
        if "MULTI-PIECE" in who:
            why.append("multi-piece art cannot stand alone")
        if v >= 0x2000:
            why.append("after the era")
        if uoart.to_rgba(v) is None:
            why.append("no art")
        if v in hits and v not in allowed:
            why.append("used by " + ", ".join(sorted(hits[v])[:4]))
        if why:
            bad += 1
            print("FAIL 0x%04X %s: %s" % (v, "; ".join(who), "; ".join(why)))
    print("checked %d pieces, %d failed" % (len(used), bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
