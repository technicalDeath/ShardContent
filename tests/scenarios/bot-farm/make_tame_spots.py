"""Generate tame_spots.json: where the animals a tamer can tame live, from the shard's own spawner files (so the tamers need no random search).
Read-only on the inputs; deterministic.

    python make_tame_spots.py                 # writes tame_spots.json next to this file
    python make_tame_spots.py --check         # exit 1 if tame_spots.json differs from what the inputs would produce

Inputs: ModernUO/Distribution/Data/BritanniaRenaissance/Alpha2b/Spawns/*.json (what the server spawns: Felucca, surface only, x < 5120), tame_data.json (taming minimums per
class), creature_stats.json (what the other kinds in a spawner can do). One entry per spawner location (spawners on the same spot are merged):
  x, y, z, home (the larger of homeRange and walkingRange: the area its animals roam), kinds [{key, cls, min, n}] (tameable kinds with the spawner's maxCount),
  others [{cls, hits, dmg}] (non-tameable creatures that spawn there; names that are neither creature nor tameable, vendors and healers, are ignored),
  danger_gap (tiles from the edge of this spot's range to the nearest dangerous spawner's range, tameable animals or not: the walk about and the route start there), threat (the highest average hit among the others, 0 for none), safe (threat under 6.5 and hits under 40 for every other: mongbats, rats and slimes are tolerable, orcs,
  ogres, ettins, reapers and the undead are not). Dangerous spawners are everywhere in this world (every WildLife spawner's range overlaps or lies within 60 tiles of one), so danger_gap
  is a score for the tamers, not a filter (tamefind.py).
A spot is listed when its tameable animals add up to 3 or more.
"""
import argparse
import glob
import json
import os
import re
import spawners
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
SPAWNS = os.path.join(ROOT, "ModernUO", "Distribution", "Data", "BritanniaRenaissance", "Alpha2b", "Spawns")
OUT = os.path.join(HERE, "tame_spots.json")



def build():
    tame = json.load(open(os.path.join(HERE, "tame_data.json"), encoding="utf-8"))
    stats = json.load(open(os.path.join(HERE, "creature_stats.json"), encoding="utf-8"))
    byclass = {v["class"].lower(): (k, v) for k, v in tame.items()}
    spots = {}
    threats = []                                          # every surface spawner with something that hits hard, tameable animals or not: (x, y, home)
    for _f, s in spawners.canonical(SPAWNS):            # each spawner once, as the server makes it (a re-themed one by its last definition)
        loc = s.get("location")
        if not loc or s.get("map") != "Felucca" or loc[0] >= 5120:
            continue
        kinds, others = {}, {}
        hard = False
        for e in s.get("entries", []):
            cls = re.sub(r"[^a-z]", "", str(e.get("name", "")).lower())
            n = int(e.get("maxCount") or 1)
            if cls in byclass:
                key, v = byclass[cls]
                k = kinds.setdefault(cls, {"key": key, "cls": v["class"], "min": v["min"], "n": 0})
                k["n"] = max(k["n"], n)
            elif cls in stats:
                c = stats[cls]
                if sum(c.get("damage") or [0, 0]) / 2.0 >= 6.5 or sum(c.get("hits") or [0, 0]) / 2.0 >= 40:
                    hard = True
                d = c.get("damage") or [0, 0]
                h = c.get("hits") or [0, 0]
                others[cls] = {"cls": c["class"], "hits": round(sum(h) / 2.0, 1), "dmg": round(sum(d) / 2.0, 1)}
        if hard:
            threats.append((loc[0], loc[1], max(int(s.get("homeRange") or 0), int(s.get("walkingRange") or 0))))
        if not kinds:
            continue
        key = (loc[0], loc[1])
        sp = spots.setdefault(key, {"x": loc[0], "y": loc[1], "z": loc[2], "home": 0, "kinds": {}, "others": {}})
        sp["home"] = max(sp["home"], int(s.get("homeRange") or 0), int(s.get("walkingRange") or 0))
        for cls, k in kinds.items():
            cur = sp["kinds"].setdefault(cls, dict(k))
            cur["n"] = max(cur["n"], k["n"])
        sp["others"].update(others)
    out = []
    for key in sorted(spots):
        sp = spots[key]
        kinds = sorted(sp["kinds"].values(), key=lambda k: (k["min"], k["key"]))
        if sum(k["n"] for k in kinds) < 3:
            continue
        others = sorted(sp["others"].values(), key=lambda o: o["cls"])
        threat = max([o["dmg"] for o in others] or [0])
        own_safe = all(o["dmg"] < 6.5 and o["hits"] < 40 for o in others)
        home = max(sp["home"], 8)
        gap = min([max(abs(sp["x"] - tx), abs(sp["y"] - ty)) - th - home for tx, ty, th in threats if (tx, ty) != (sp["x"], sp["y"])] or [999])
        out.append({"x": sp["x"], "y": sp["y"], "z": sp["z"], "home": home, "kinds": kinds, "others": others, "threat": threat, "danger_gap": gap,
                    "safe": own_safe})
    return {"schema": 1, "note": "tameable animals by spawner (make_tame_spots.py); min = the taming skill needed, n = the spawner's maxCount", "spots": out}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    text = json.dumps(build(), indent=1, sort_keys=True) + "\n"
    if a.check:
        cur = open(OUT, encoding="utf-8").read() if os.path.exists(OUT) else ""
        if cur.replace("\r\n", "\n") != text:
            print("tame_spots.json differs from the inputs")
            return 1
        print("tame_spots.json is current")
        return 0
    open(OUT, "w", encoding="utf-8", newline="\n").write(text)
    d = json.loads(text)
    print(f"{len(d['spots'])} spots, {sum(1 for s in d['spots'] if s['safe'])} safe")
    return 0


if __name__ == "__main__":
    sys.exit(main())
