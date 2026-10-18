"""Writes shores.json: places to fish around Britain, read from the Felucca land map: an edge tile of deep water (land 0xA8-0xAB) per 8 x 8
fishing bank, nearest Britain first; the fisher walks toward it and fishes from where the path ends. Three fishers shared six hard-coded spots on one stretch of the
lake shore, fished it out, and cycled those spots every two seconds.

    python make_shores.py [x0 y0 x1 y1]

Uses make_mountains.py's map reader; a land tile is walkable unless tiledata marks it impassable (flag 0x40).
"""
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_mountains as mm  # noqa: E402

WATER = set(range(0xA8, 0xAC))


def impassable_land():
    d = open(os.path.join(mm.UODATA, "tiledata.mul"), "rb").read()
    out = set()
    for i in range(0x4000):
        g, k = divmod(i, 32)
        off = g * (4 + 32 * 30) + 4 + k * 30
        if off + 8 > len(d):
            break
        flags = struct.unpack_from("<Q", d, off)[0]
        if flags & 0x40:
            out.add(i)
    return out


def build(x0, y0, x1, y1, centre=(1470, 1620)):
    """The shore spots (one per 8 x 8 water bank) in a box, nearest `centre` first."""
    data = mm.load_map()
    banks = {}
    for x in range(x0, x1 + 1):
        for y in range(y0, y1 + 1):
            if (x // 8, y // 8) in banks:
                continue
            g, z = mm.cell(data, x, y)
            if g not in WATER:
                continue
            # edge water: next to something that is not water. The shore itself is often walkable statics laid over impassable land (the lake
            # south of Britain is ringed by land 0x64), so the fisher walks toward the water and stops where the path does.
            if any(mm.cell(data, x + dx, y + dy)[0] not in WATER for dx, dy in ((0, 1), (1, 0), (-1, 0), (0, -1))):
                banks[(x // 8, y // 8)] = [x, y, z]
    return sorted(banks.values(), key=lambda t: abs(t[0] - centre[0]) + abs(t[1] - centre[1]))


def main():
    x0, y0, x1, y1 = (int(v) for v in sys.argv[1:5]) if len(sys.argv) >= 5 else (1100, 1300, 1900, 2050)
    out = build(x0, y0, x1, y1)
    json.dump(out, open(os.path.join(HERE, "shores.json"), "w", encoding="utf-8"))
    print(f"{len(out)} shore spots (one per 8x8 water bank) in {x0},{y0}-{x1},{y1}; nearest {[t[:2] for t in out[:6]]}")


if __name__ == "__main__":
    main()
