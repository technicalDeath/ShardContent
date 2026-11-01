"""Writes fishstands.json: every place on the Felucca surface a fisher can fish from, one per 8x8 fish bank (the server keeps fish per bank:
HarvestDefinition BankWidth/BankHeight 8 in Fishing.cs). A stand is a walkable tile (walkgrid.bin) with deep water (watergrid.bin) within the cast
range whose line from the stand runs over water only (fishspot.clear_water: a ledge or a bank's lip in between is what makes the server say "cannot be
seen"). For each bank the stand nearest its water is kept.

    python make_fishstands.py            # about a minute; writes fishstands.json next to this file

The fisher reads it through fishspot.world_stands(): the coastline anywhere in the world, so a fisher dropped in any town (or none) finds water by
distance and route from where it stands, not from a town's hand list (owner, 2026-10-31: "explore the coastline for fishing spots anywhere in the world").
File: {"made": <unix time>, "cast_range": 4, "stands": [[bank_x, bank_y, stand_x, stand_y, water_x, water_y], ...]} sorted by bank.
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fishspot  # noqa: E402
import walkroute  # noqa: E402

OUT = os.path.join(HERE, "fishstands.json")


def build(r=fishspot.CAST_RANGE):
    water, walk = fishspot.water(), walkroute.get()
    if water is None or walk is None:
        raise SystemExit("needs watergrid.bin and walkgrid.bin")
    W, H = 5120, water.H
    t0 = time.time()
    wat = [0] * W
    # the bit layout is the same in both files (index x * H + y), so a column is a slice of the bit string
    for x in range(W):
        lo, hi = x * H, (x + 1) * H
        wat[x] = int.from_bytes(water.bits[lo >> 3:hi >> 3], "little")
    wlk = [0] * W
    for x in range(W):
        lo, hi = x * walk.H, (x + 1) * walk.H
        wlk[x] = int.from_bytes(walk.bits[lo >> 3:hi >> 3], "little")
    mask = (1 << H) - 1
    near_y = []
    for v in wat:
        d = v
        for k in range(1, r + 1):
            d |= (v << k) | (v >> k)
        near_y.append(d & mask)
    stands = {}
    for x in range(W):
        near = 0
        for dx in range(-r, r + 1):
            if 0 <= x + dx < W:
                near |= near_y[x + dx]
        cand = wlk[x] & near & ~wat[x]
        while cand:
            low = cand & -cand
            y = low.bit_length() - 1
            cand ^= low
            p = fishspot.clear_water(x, y, r)
            if p is None:
                continue
            b = (p[0] // 8 * 8, p[1] // 8 * 8)
            d = max(abs(p[0] - x), abs(p[1] - y))
            if b not in stands or d < stands[b][0]:
                stands[b] = (d, x, y, p[0], p[1])
    rows = sorted([b[0], b[1], s[1], s[2], s[3], s[4]] for b, s in stands.items())
    return rows, time.time() - t0


def main():
    rows, s = build()
    json.dump({"made": int(time.time()), "cast_range": fishspot.CAST_RANGE, "stands": rows}, open(OUT, "w", encoding="utf-8"))
    print(f"{len(rows)} fish banks with a stand in {s:.0f} s -> {OUT}")


if __name__ == "__main__":
    main()
