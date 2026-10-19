"""Generate hunt_spots.json: where creatures a caster can fight live, from the shard's own spawner files. Read-only on inputs; deterministic.

    python make_hunt_spots.py            # writes hunt_spots.json next to this file
    python make_hunt_spots.py --check    # exit 1 if it differs from what the inputs produce

One entry per spawner location within 260 tiles of Britain (Felucca surface): x, y, home (roam radius), kinds [{cls, n, hits, dmg}] for every creature kind in
creature_stats.json (vendors and town animals that are no prey are left to the bot's own scoring: cls names are kept as they are).
"""
import argparse, glob, json, os, re, sys
import spawners

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE
while not os.path.isdir(os.path.join(ROOT, "ModernUO")) and os.path.dirname(ROOT) != ROOT:
    ROOT = os.path.dirname(ROOT)
SPAWNS = os.path.join(ROOT, "ModernUO", "Distribution", "Data", "BritanniaRenaissance", "Alpha2b", "Spawns")
OUT = os.path.join(HERE, "hunt_spots.json")
BRITAIN = (1470, 1620)
RADIUS = 260


def build():
    st = json.load(open(os.path.join(HERE if os.path.exists(os.path.join(HERE, "creature_stats.json")) else os.path.join(ROOT, "ShardContent", "tests", "scenarios", "bot-farm"), "creature_stats.json"), encoding="utf-8"))
    spots = {}
    for _f, s in spawners.canonical(SPAWNS):            # each spawner once, as the server makes it (a re-themed one by its last definition)
        loc = s.get("location")
        if not loc or s.get("map") != "Felucca" or loc[0] >= 5120 or max(abs(loc[0] - BRITAIN[0]), abs(loc[1] - BRITAIN[1])) > RADIUS:
            continue
        sp = spots.setdefault((loc[0], loc[1]), {"x": loc[0], "y": loc[1], "home": 0, "kinds": {}})
        sp["home"] = max(sp["home"], int(s.get("homeRange") or 0), int(s.get("walkingRange") or 0))
        for e in s.get("entries", []):
            c = re.sub(r"[^a-z]", "", str(e.get("name", "")).lower())
            if c not in st:
                continue
            h, d = st[c].get("hits") or [0, 0], st[c].get("damage") or [0, 0]
            k = sp["kinds"].setdefault(c, {"cls": c, "n": 0, "hits": round(sum(h) / 2.0, 1), "dmg": round(sum(d) / 2.0, 1)})
            k["n"] = max(k["n"], int(e.get("maxCount") or 1))
    out = []
    for key in sorted(spots):
        sp = spots[key]
        if sp["kinds"]:
            out.append({"x": sp["x"], "y": sp["y"], "home": max(sp["home"], 8), "kinds": sorted(sp["kinds"].values(), key=lambda k: k["cls"])})
    return {"schema": 1, "note": "creature kinds by spawner near Britain (make_hunt_spots.py)", "spots": out}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    text = json.dumps(build(), indent=1, sort_keys=True) + "\n"
    if a.check:
        cur = open(OUT, encoding="utf-8").read() if os.path.exists(OUT) else ""
        if cur.replace("\r\n", "\n") != text:
            print("hunt_spots.json differs from the inputs")
            return 1
        print("hunt_spots.json is current")
        return 0
    open(OUT, "w", encoding="utf-8", newline="\n").write(text)
    print(f"{len(json.loads(text)['spots'])} spots")
    return 0


if __name__ == "__main__":
    sys.exit(main())
