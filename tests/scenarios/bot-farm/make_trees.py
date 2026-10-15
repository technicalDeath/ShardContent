"""Writes trees.json: the choppable trees around Britain, read straight from the Felucca statics (staidx0.mul / statics0.mul), one per lumberjacking
harvest bank (4 x 3 tiles share their wood), so a carpenter can go to the nearest tree that still has wood instead of three hard-coded ones.

    python make_trees.py [x0 y0 x1 y1]

Tree ids are Lumberjacking.cs m_TreeTiles. A static is 7 bytes (graphic, x, y, z, hue); a block is 8 x 8 tiles; staidx has 12 bytes per block
(offset, length, extra), blocks numbered bx * 512 + by on the 7168 x 4096 map.
"""
import json
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
UODATA = os.path.join(ROOT, "UOData")
SRC = os.path.join(ROOT, "ModernUO", "Projects", "UOContent", "Engines", "Harvest", "Lumberjacking.cs")
BLOCKS_HIGH = 4096 // 8


def tree_ids():
    text = open(SRC, encoding="utf-8").read()
    body = text[text.index("m_TreeTiles ="):text.index("};", text.index("m_TreeTiles ="))]
    return {int(h, 16) for h in re.findall(r"0x([0-9A-Fa-f]{4})", body)}


def main():
    x0, y0, x1, y1 = (int(v) for v in sys.argv[1:5]) if len(sys.argv) >= 5 else (1150, 1400, 1800, 1950)
    ids = tree_ids()
    idx = open(os.path.join(UODATA, "staidx0.mul"), "rb")
    sta = open(os.path.join(UODATA, "statics0.mul"), "rb")
    banks = {}
    for bx in range(x0 // 8, x1 // 8 + 1):
        for by in range(y0 // 8, y1 // 8 + 1):
            idx.seek((bx * BLOCKS_HIGH + by) * 12)
            off, length, _ = struct.unpack("<iii", idx.read(12))
            if off < 0 or length <= 0:
                continue
            sta.seek(off)
            data = sta.read(length)
            for i in range(0, length - 6, 7):
                g, sx, sy, z, _hue = struct.unpack("<HBBbH", data[i:i + 7])
                if g in ids:
                    x, y = bx * 8 + sx, by * 8 + sy
                    if x0 <= x <= x1 and y0 <= y <= y1:
                        banks.setdefault((x // 4, y // 3), (x, y, z, g))
    trees = sorted(banks.values())
    out = os.path.join(HERE, "trees.json")
    json.dump(trees, open(out, "w", encoding="utf-8"))
    print(f"{len(trees)} trees (one per harvest bank) in {x0},{y0}-{x1},{y1} from {len(ids)} tree ids -> {out}")


if __name__ == "__main__":
    main()
