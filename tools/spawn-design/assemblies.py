"""Learns how multi-piece art fits together from the client's own Felucca map: for each art id asked about, it finds
every place the map uses it and counts which ids stand on the neighbouring tiles at the same height. A neighbour that
appears beside the piece nearly every time (share >= 0.7) is part of the same object. Prints each id's object as
(dx, dy, id) parts, ready for deco.json.

  python assemblies.py 0x1350 0x0CF3 ...       (or no ids: every id in deco.json)
"""
import collections
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "cosmetic-catalog"))
import uoart  # noqa: E402

H_BLOCKS = 512
W_BLOCKS = 640          # the Britannia surface, x < 5120
SHARE = 0.7
REACH = 3


def statics_by_block():
    idx = open(os.path.join(uoart.ROOT, "staidx0.mul"), "rb").read()
    sf = open(os.path.join(uoart.ROOT, "statics0.mul"), "rb").read()
    for bx in range(W_BLOCKS):
        for by in range(H_BLOCKS):
            lookup, length, _ = struct.unpack_from("<III", idx, (bx * H_BLOCKS + by) * 12)
            if lookup == 0xFFFFFFFF or length in (0, 0xFFFFFFFF):
                continue
            yield bx, by, sf[lookup:lookup + length]


def learn(targets):
    blocks = {}
    hits = collections.defaultdict(list)
    for bx, by, buf in statics_by_block():
        lst = []
        for k in range(0, len(buf) - 6, 7):
            tid, sx, sy, z, _ = struct.unpack_from("<HBBbH", buf, k)
            lst.append((bx * 8 + sx, by * 8 + sy, z, tid))
            if tid in targets:
                hits[tid].append((bx * 8 + sx, by * 8 + sy, z))
        blocks[(bx, by)] = lst
    at = collections.defaultdict(list)
    for lst in blocks.values():
        for x, y, z, tid in lst:
            at[(x, y)].append((tid, z))
    out = {}
    for tid in targets:
        occ = hits.get(tid, [])
        count = collections.Counter()
        for x, y, z in occ:
            seen = set()
            for dx in range(-REACH, REACH + 1):
                for dy in range(-REACH, REACH + 1):
                    if dx == dy == 0:
                        continue
                    for nid, nz in at.get((x + dx, y + dy), []):
                        if abs(nz - z) <= 3 and (dx, dy, nid) not in seen:
                            seen.add((dx, dy, nid))
                            count[(dx, dy, nid)] += 1
        parts = sorted((k for k, n in count.items() if occ and n / len(occ) >= SHARE), key=lambda k: (k[1], k[0]))
        out[tid] = {"uses": len(occ), "parts": [[dx, dy, "0x%04X" % nid] for dx, dy, nid in parts]}
    return out


def main(argv):
    if argv:
        targets = {int(a, 16) for a in argv}
    else:
        d = json.load(open(os.path.join(HERE, "deco.json"), encoding="utf-8"))
        targets = {int(h, 16) for t in d["themes"].values() for r in ("anchor", "supports", "accents") for _, h in t[r]}
    tiles = uoart.tiles()
    res = learn(targets)
    for tid in sorted(res):
        r = res[tid]
        print("0x%04X %-18s uses %5d  parts %s" % (tid, tiles[tid].name, r["uses"], r["parts"] or "-"))
    json.dump({"0x%04X" % k: v for k, v in res.items()}, open(os.path.join(HERE, "assemblies.json"), "w"), indent=1)


if __name__ == "__main__":
    main(sys.argv[1:])
