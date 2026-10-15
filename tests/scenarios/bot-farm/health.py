"""Prints one line per bot from the supervisor's metrics: what it has been doing, whether it is moving, and how much it has achieved. Run it to find stuck bots.

    python health.py [minutes]
"""
import collections
import json
import os
import sys
import time

FARM = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")), "work", "botfarm")
minutes = float(sys.argv[1]) if len(sys.argv) > 1 else 10
rows = [json.loads(l) for l in open(os.path.join(FARM, "metrics.jsonl"))]
now = max(r["t"] for r in rows)
by = collections.defaultdict(list)
for r in rows:
    if now - r["t"] <= minutes * 60:
        by[r["bot"]].append(r)
print(f"{len(by)} bots, last {minutes:g} min (metrics at {time.strftime('%H:%M:%S', time.localtime(now))})")
for b, rs in sorted(by.items()):
    rules = collections.Counter(r["rule"] or "-" for r in rs)
    pos = {tuple(r["pos"]) for r in rs if r["pos"]}
    first, last = rs[0], rs[-1]
    flag = "  <-- NOT MOVING" if len(pos) <= 1 and len(rs) >= 5 and last["rule"] not in ("r_fish", "r_music") else ""
    print(f"{b:12} {last['prof'] or '':11} kills {last['kills'] - first['kills']:+3d} deaths {last['deaths'] - first['deaths']:+2d} gold {last['gold']:5} gains {last['gains'] - first['gains']:+4d} pos {len(pos):2d}  {dict(rules.most_common(3))}{flag}")
