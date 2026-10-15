"""Seeds the shared memory from what earlier runs left behind: shop lists (work/botfarm/shops.json) and every bot's remembered death spots.

    python seed_memory.py
Run it once on a fresh memory folder; it only appends events, so running it twice counts the same things twice.
"""
import glob
import json
import os
import re

import memory as M

FARM = os.path.join(M.ROOT, "work", "botfarm")
mem = M.SharedMemory("Seed", "seed")
n = 0
try:
    shops = json.load(open(os.path.join(FARM, "shops.json"), encoding="utf-8"))
except (OSError, ValueError):
    shops = {}
for xy, lines in shops.items():
    x, y = (int(v) for v in re.findall(r"\d+", xy)[:2])
    rows = []
    for l in lines:
        m = re.search(r"(\d+)gp\s+x(\d+)\s+(.+)", l)
        if m and not m.group(3).strip().lower() in ("cloak",):
            rows.append([m.group(3).strip(), int(m.group(1)), int(m.group(2))])
    if rows:
        mem.record("vendor", xy=f"{x},{y}", name="seed", stock=rows)
        n += 1
for p in glob.glob(os.path.join(FARM, "Bot*", "knowledge.json")):
    try:
        k = json.load(open(p, encoding="utf-8"))
    except (OSError, ValueError):
        continue
    for x, y in k.get("death_spots", []):
        mem.record("death", cell=M.cell_of(x, y), killers=[])
        n += 1
print(f"seeded {n} events into {M.MEMDIR}")
