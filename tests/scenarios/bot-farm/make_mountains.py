"""Writes mountains.json: mineable mountain tiles around Britain, read straight from the Felucca land map (map0LegacyMUL.uop), one per mining
harvest bank (8 x 8 tiles share their ore), and only those at a mountain's edge: next to a walkable land tile a miner can stand on. The miners
had ten hard-coded tiles on one hill north of Britain, shared with the smiths who dig their own ore, so every spot was often taken or dug out.

    python make_mountains.py [x0 y0 x1 y1]

Mineable land ids are Mining.cs _mountainCaveTiles (pairs of inclusive ranges). The map UOP holds the classic map0.mul data in chunks of 4,096
blocks, stored in order; a block is 8 x 8 cells after a 4-byte header, a cell is a land tile id (ushort) and its z (sbyte); blocks are numbered
bx * 512 + by on the 7168 x 4096 map.
"""
import json
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
UODATA = os.path.join(ROOT, "UOData")
SRC = os.path.join(ROOT, "ModernUO", "Projects", "UOContent", "Engines", "Harvest", "Mining.cs")
BLOCKS_HIGH = 4096 // 8
BLOCK = 196


def rock_ids(ids):
    """Of the mineable land ids, the mountain rock itself (tiledata name "rock"): the list also has the dirt, forest, grass and sand tiles at a
    mountain's foot, and one of those in the middle of Britain was the "nearest mountain"."""
    d = open(os.path.join(UODATA, "tiledata.mul"), "rb").read()
    out = set()
    for i in ids:
        g, k = divmod(i, 32)
        off = g * (4 + 32 * 30) + 4 + k * 30
        if off + 30 <= len(d) and d[off + 10:off + 30].split(bytes(1))[0] == b"rock":
            out.add(i)
    return out


def mine_ids():
    text = open(SRC, encoding="utf-8").read()
    body = text[text.index("_mountainCaveTiles ="):text.index("};", text.index("_mountainCaveTiles ="))]
    body = re.sub(r"//.*", "", body)
    nums = [int(v, 16) if v.lower().startswith("0x") else int(v) for v in re.findall(r"0x[0-9A-Fa-f]+|\d+", body)]
    ids = set()
    for a, b in zip(nums[::2], nums[1::2]):
        ids.update(range(a, b + 1))
    return ids


def uop_hash(s):
    """The UOP name hash (ClassicUO.IO.UOFileUop.CreateHash, Bob Jenkins' hashlittle2), 32-bit arithmetic."""
    M = 0xFFFFFFFF
    b = [ord(ch) for ch in s]
    n = len(b)
    eax = ecx = edx = 0
    ebx = edi = esi = (n + 0xDEADBEEF) & M
    i = 0
    while i + 12 < n:
        edi = (((b[i + 7] << 24) | (b[i + 6] << 16) | (b[i + 5] << 8) | b[i + 4]) + edi) & M
        esi = (((b[i + 11] << 24) | (b[i + 10] << 16) | (b[i + 9] << 8) | b[i + 8]) + esi) & M
        edx = (((b[i + 3] << 24) | (b[i + 2] << 16) | (b[i + 1] << 8) | b[i]) - esi) & M
        edx = ((edx + ebx) & M) ^ (esi >> 28) ^ ((esi << 4) & M)
        esi = (esi + edi) & M
        edi = ((edi - edx) & M) ^ (edx >> 26) ^ ((edx << 6) & M)
        edx = (edx + esi) & M
        esi = ((esi - edi) & M) ^ (edi >> 24) ^ ((edi << 8) & M)
        edi = (edi + edx) & M
        ebx = ((edx - esi) & M) ^ (esi >> 16) ^ ((esi << 16) & M)
        esi = (esi + edi) & M
        edi = ((edi - ebx) & M) ^ (ebx >> 13) ^ ((ebx << 19) & M)
        ebx = (ebx + esi) & M
        esi = ((esi - edi) & M) ^ (edi >> 28) ^ ((edi << 4) & M)
        edi = (edi + ebx) & M
        i += 12
    rest = n - i
    if rest > 0:
        if rest >= 12: esi = (esi + (b[i + 11] << 24)) & M
        if rest >= 11: esi = (esi + (b[i + 10] << 16)) & M
        if rest >= 10: esi = (esi + (b[i + 9] << 8)) & M
        if rest >= 9: esi = (esi + b[i + 8]) & M
        if rest >= 8: edi = (edi + (b[i + 7] << 24)) & M
        if rest >= 7: edi = (edi + (b[i + 6] << 16)) & M
        if rest >= 6: edi = (edi + (b[i + 5] << 8)) & M
        if rest >= 5: edi = (edi + b[i + 4]) & M
        if rest >= 4: ebx = (ebx + (b[i + 3] << 24)) & M
        if rest >= 3: ebx = (ebx + (b[i + 2] << 16)) & M
        if rest >= 2: ebx = (ebx + (b[i + 1] << 8)) & M
        ebx = (ebx + b[i]) & M
        esi = ((esi ^ edi) - ((edi >> 18) ^ ((edi << 14) & M))) & M
        ecx = ((esi ^ ebx) - ((esi >> 21) ^ ((esi << 11) & M))) & M
        edi = ((edi ^ ecx) - ((ecx >> 7) ^ ((ecx << 25) & M))) & M
        esi = ((esi ^ edi) - ((edi >> 16) ^ ((edi << 16) & M))) & M
        edx = ((esi ^ ecx) - ((esi >> 28) ^ ((esi << 4) & M))) & M
        edi = ((edi ^ edx) - ((edx >> 18) ^ ((edx << 14) & M))) & M
        eax = ((esi ^ edi) - ((edi >> 8) ^ ((edi << 24) & M))) & M
        return (edi << 32) | eax
    return (esi << 32) | eax


def load_map():
    """The whole map's block data, in block order: chunk N is the UOP entry named build/map0legacymul/NNNNNNNN.dat (by its hash)."""
    f = open(os.path.join(UODATA, "map0LegacyMUL.uop"), "rb")
    magic, _version, _sig, nxt, _bsize, _count = struct.unpack("<4sIIqii", f.read(28))
    assert magic == b"MYP\x00", magic
    by_hash = {}
    while nxt:
        f.seek(nxt)
        n, nxt = struct.unpack("<iq", f.read(12))
        for _ in range(n):
            off, hlen, clen, dlen, h, _adler, flag = struct.unpack("<qiiiQIh", f.read(34))
            if off:
                by_hash[h] = (off, hlen, dlen, flag)
    data = bytearray()
    for i in range(len(by_hash)):
        e = by_hash.get(uop_hash(f"build/map0legacymul/{i:08d}.dat"))
        assert e is not None, f"map chunk {i} not found by its hash"
        off, hlen, dlen, flag = e
        assert flag == 0, "compressed map chunks are not handled"
        f.seek(off + hlen)
        data += f.read(dlen)
    return bytes(data)


def cell(data, x, y):
    bx, by = x // 8, y // 8
    o = (bx * BLOCKS_HIGH + by) * BLOCK + 4 + ((y % 8) * 8 + (x % 8)) * 3
    g, z = struct.unpack_from("<Hb", data, o)
    return g, z


def build(x0, y0, x1, y1, centre=(1470, 1620)):
    """The mineable mountain-edge tiles (one per 8 x 8 ore bank) in a box, nearest `centre` first."""
    ids = mine_ids()
    rock = rock_ids(ids)
    data = load_map()
    g, z = cell(data, 1455, 1525)
    assert g == 557, f"map parse check failed: 1455,1525 is land {g}, expected 557"
    banks = {}
    for x in range(x0, x1 + 1):
        for y in range(y0, y1 + 1):
            g, z = cell(data, x, y)
            if g not in rock:
                continue
            # a mountain's edge: a neighbouring land tile that is not mountain and not much higher, where a miner can stand
            stand = None
            for dx, dy in ((0, 1), (1, 0), (-1, 0), (0, -1)):
                ng, nz = cell(data, x + dx, y + dy)
                if ng not in ids and abs(nz - z) <= 20 and ng not in range(0xA8, 0xAC) and ng not in range(0x136, 0x138):   # not water
                    stand = (x + dx, y + dy)
                    break
            if stand:
                banks.setdefault((x // 8, y // 8), [x, y, z, g, stand[0], stand[1]])
    return sorted(banks.values(), key=lambda t: abs(t[0] - centre[0]) + abs(t[1] - centre[1]))


def main():
    x0, y0, x1, y1 = (int(v) for v in sys.argv[1:5]) if len(sys.argv) >= 5 else (1100, 1300, 1900, 2050)
    out = build(x0, y0, x1, y1)
    json.dump(out, open(os.path.join(HERE, "mountains.json"), "w", encoding="utf-8"))
    print(f"{len(out)} mineable edge tiles (one per 8x8 bank) in {x0},{y0}-{x1},{y1}; nearest {out[:3]}")


if __name__ == "__main__":
    main()
