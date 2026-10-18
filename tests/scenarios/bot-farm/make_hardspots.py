"""Generate hardspots.json: where the spawners of creatures too strong for a new fighter stand, as penalty circles for route planning (walkroute.py).
Read-only on the inputs; deterministic.

    python make_hardspots.py                  # writes hardspots.json next to this file
    python make_hardspots.py --check          # exit 1 if hardspots.json differs from what the inputs would produce
    python make_hardspots.py --data <Data> --mobiles <Mobiles source folder> --out <file>

Inputs: <Data>/BritanniaRenaissance/Alpha2b/Spawns/*.json (the world's spawners; the town vendor and townspeople files are skipped) and the stock creature
source (Projects/UOContent/Mobiles/**/*.cs: SetHits / SetStr / SetDamage per class). A creature's danger index is its average hit points and damage:
tier 3+ (more than 85 hit points or 16+ a hit, up to 230), tier 4 above 230 hit points = HARD (route factor 6); the kinds the farm's own fights showed beat
30-70 fighters about four times in five (orc, ratman, shade, lizardman, harpy, grizzly bear, gazer, wraith, spectre; work/botfarm-watch/creature-danger.md)
are SOFT (factor 3). A circle is the spawner's roaming reach: max(home range, walking range) + 8 tiles. Surface spawners only (x < 5120).
"""
import argparse
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
SKIP = {"Vendors.json", "TownsPeople.json", "britain-vendor-overrides.json"}
SOFT_KINDS = {"orc", "orcishmage", "orcishlord", "ratman", "ratmanmage", "ratmanarcher", "shade", "lizardman", "harpy", "grizzlybear", "gazer", "wraith", "spectre"}
HARMLESS = {"wanderinghealer", "bird", "cat", "dog", "rat", "chicken", "sheep", "goat", "pig", "cow", "rabbit", "squirrel"}


def parse_mobiles(root):
    stats = {}
    for p in glob.glob(root + "/**/*.cs", recursive=True):
        s = open(p, encoding="utf-8", errors="ignore").read()
        m = re.search(r"class\s+(\w+)\s*:\s*(\w+)", s)
        if not m:
            continue

        def rng(fn):
            r = re.search(fn + r"\(\s*(-?\d+)\s*(?:,\s*(-?\d+))?\s*\)", s)
            return None if not r else (int(r.group(1)) + int(r.group(2) or r.group(1))) / 2

        stats[m.group(1)] = dict(base=m.group(2), hits=rng("SetHits"), str=rng("SetStr"), dmg=rng("SetDamage"))
    return stats


def tier(name, stats, depth=0):
    s = stats.get(name)
    if s is None or depth > 6:
        return None
    hits = s["hits"] or s["str"]
    if hits is None:
        return tier(s["base"], stats, depth + 1) if s["base"] in stats else None
    dmg = s["dmg"] or 4
    if hits <= 12 and dmg <= 3:
        return 0
    if hits <= 45 and dmg <= 8:
        return 1
    if hits <= 85 and dmg <= 16:
        return 2
    return 3 if hits <= 230 else 4


def build(data, mobiles):
    stats = parse_mobiles(mobiles)
    low = {k.lower(): k for k in stats}
    circles, used = [], {}
    sdir = os.path.join(data, "BritanniaRenaissance", "Alpha2b", "Spawns")
    for f in sorted(os.listdir(sdir)):
        if not f.endswith(".json") or f in SKIP:
            continue
        for sp in json.load(open(os.path.join(sdir, f), encoding="utf-8")):
            if sp.get("map") != "Felucca" or sp["location"][0] >= 5120:
                continue
            hard, soft = [], []
            for e in sp["entries"]:
                k = e["name"].lower()
                if k in HARMLESS:
                    continue
                t = tier(low.get(k, e["name"]), stats)
                if t is not None and t >= 3:
                    hard.append(e["name"])
                elif k in SOFT_KINDS:
                    soft.append(e["name"])
            if not (hard or soft):
                continue
            reach = max(sp.get("homeRange", 0), sp.get("walkingRange", 0)) + 8
            circles.append(dict(x=sp["location"][0], y=sp["location"][1], r=min(reach, 48), factor=6.0 if hard else 3.0, kinds=sorted(set(hard + soft)), file=f))
            used[f] = used.get(f, 0) + 1
    circles.sort(key=lambda c: (c["x"], c["y"], c["file"]))
    return dict(schema=1, note="penalty circles for walkroute.penalty_circles: hard (tier 3+) x6, soft (orc, ratman, shade...) x3", files=used, circles=circles)


def dump(doc):
    return "{\n" + f'"schema":{doc["schema"]},\n"note":{json.dumps(doc["note"])},\n"files":{json.dumps(doc["files"], sort_keys=True, separators=(",", ":"))},\n"circles":[\n' \
        + ",\n".join(json.dumps(c, separators=(",", ":"), sort_keys=True) for c in doc["circles"]) + "\n]\n}\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=os.path.join(ROOT, "ModernUO", "Distribution", "Data"))
    ap.add_argument("--mobiles", default=os.path.join(ROOT, "ModernUO", "Projects", "UOContent", "Mobiles"))
    ap.add_argument("--out", default=os.path.join(HERE, "hardspots.json"))
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    text = dump(build(a.data, a.mobiles))
    if a.check:
        same = os.path.exists(a.out) and open(a.out, encoding="utf-8").read() == text
        print("hardspots.json is up to date" if same else "hardspots.json DIFFERS from the inputs: run make_hardspots.py")
        sys.exit(0 if same else 1)
    with open(a.out, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    doc = json.loads(text)
    hard = sum(1 for c in doc["circles"] if c["factor"] >= 6)
    print(f"wrote {a.out}: {len(doc['circles'])} circles ({hard} hard, {len(doc['circles']) - hard} soft)")


if __name__ == "__main__":
    main()
