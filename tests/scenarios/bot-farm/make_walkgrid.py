"""Generate walkgrid.bin, the walkability map behind walkroute.py, from the client's own map data. Read-only on the inputs; deterministic.

    python make_walkgrid.py                     # writes walkgrid.bin next to this file (about 40 s)
    python make_walkgrid.py --check             # exit 1 if walkgrid.bin differs from what the inputs would produce
    python make_walkgrid.py --uodata <client data folder> --out <file>

Inputs (UOData): map0LegacyMUL.uop (or map0.mul) = the Felucca land tiles and their heights; statics0.mul + staidx0.mul = the fixed objects on the map;
tiledata.mul = what each land tile and object is (impassable, surface, bridge, height).
A tile is walkable when a character could stand on it: its land is not impassable, or a floor / bridge static stands there, and no impassable static
(wall, tree, boulder) occupies the 16 height units above the floor. Only the surface (x < 5120) is written. NOT known to this file: houses and other
multis placed by the server, doors, other mobiles; a route built on it still has to be walked by the real client planner (a hint, with the water, cliffs,
trees and walls handled).
File layout: b"WGRD1", W (u16), H (u16), len of the bit part (u32), zlib(bits, index x * H + y, bit i & 7 of byte i >> 3, 1 = walkable),
zlib(coarse): one byte per 4x4 tiles = how many of the 16 are walkable.
"""
import argparse
import hashlib
import os
import struct
import sys
import zlib
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
W, H = 5120, 4096                                        # the Britannia surface of Felucca (the map is 7168 wide; the rest is dungeons and T2A)
MAP_W, MAP_H = 7168, 4096
CELL = 4
M32 = 0xFFFFFFFF


def uop_hash(s):
    s = [ord(c) for c in s]
    n = len(s)
    ebx = edi = esi = (n + 0xDEADBEEF) & M32
    eax = ecx = edx = 0
    i = 0
    while i + 12 < n:
        edi = (((s[i + 7] << 24) | (s[i + 6] << 16) | (s[i + 5] << 8) | s[i + 4]) + edi) & M32
        esi = (((s[i + 11] << 24) | (s[i + 10] << 16) | (s[i + 9] << 8) | s[i + 8]) + esi) & M32
        edx = (((s[i + 3] << 24) | (s[i + 2] << 16) | (s[i + 1] << 8) | s[i]) - esi) & M32
        edx = ((edx + ebx) & M32) ^ (esi >> 28) ^ ((esi << 4) & M32)
        esi = (esi + edi) & M32
        edi = ((edi - edx) & M32) ^ (edx >> 26) ^ ((edx << 6) & M32)
        edx = (edx + esi) & M32
        esi = ((esi - edi) & M32) ^ (edi >> 24) ^ ((edi << 8) & M32)
        edi = (edi + edx) & M32
        ebx = ((edx - esi) & M32) ^ (esi >> 16) ^ ((esi << 16) & M32)
        esi = (esi + edi) & M32
        edi = ((edi - ebx) & M32) ^ (ebx >> 13) ^ ((ebx << 19) & M32)
        ebx = (ebx + esi) & M32
        esi = ((esi - edi) & M32) ^ (edi >> 28) ^ ((edi << 4) & M32)
        edi = (edi + ebx) & M32
        i += 12
    r = n - i
    if r > 0:
        if r >= 12: esi = (esi + (s[i + 11] << 24)) & M32
        if r >= 11: esi = (esi + (s[i + 10] << 16)) & M32
        if r >= 10: esi = (esi + (s[i + 9] << 8)) & M32
        if r >= 9: esi = (esi + s[i + 8]) & M32
        if r >= 8: edi = (edi + (s[i + 7] << 24)) & M32
        if r >= 7: edi = (edi + (s[i + 6] << 16)) & M32
        if r >= 6: edi = (edi + (s[i + 5] << 8)) & M32
        if r >= 5: edi = (edi + s[i + 4]) & M32
        if r >= 4: ebx = (ebx + (s[i + 3] << 24)) & M32
        if r >= 3: ebx = (ebx + (s[i + 2] << 16)) & M32
        if r >= 2: ebx = (ebx + (s[i + 1] << 8)) & M32
        if r >= 1: ebx = (ebx + s[i]) & M32
        esi = ((esi ^ edi) - (((edi >> 18) ^ (edi << 14)) & M32)) & M32
        ecx = ((esi ^ ebx) - (((esi >> 21) ^ (esi << 11)) & M32)) & M32
        edi = ((edi ^ ecx) - (((ecx >> 7) ^ (ecx << 25)) & M32)) & M32
        esi = ((esi ^ edi) - (((edi >> 16) ^ (edi << 16)) & M32)) & M32
        edx = ((esi ^ ecx) - (((esi >> 28) ^ (esi << 4)) & M32)) & M32
        edi = ((edi ^ edx) - (((edx >> 18) ^ (edx << 14)) & M32)) & M32
        eax = ((esi ^ edi) - (((edi >> 8) ^ (edi << 24)) & M32)) & M32
        return (edi << 32) | eax
    return (esi << 32) | eax


def load_map(uodata):
    """The Felucca land block data (map0), 196 bytes per 8x8 block, block index = bx * (MAP_H / 8) + by."""
    mul = os.path.join(uodata, "map0.mul")
    if os.path.exists(mul):
        return open(mul, "rb").read()
    b = open(os.path.join(uodata, "map0LegacyMUL.uop"), "rb").read()
    assert b[:4] == b"MYP\0"
    nxt = struct.unpack_from("<Q", b, 12)[0]
    ents = []
    while nxt:
        n, nx = struct.unpack_from("<iQ", b, nxt)
        o = nxt + 12
        for _ in range(n):
            off, hl, cl, dl, h, crc, flag = struct.unpack_from("<QIIIQIH", b, o)
            o += 34
            if off:
                ents.append((h, off + hl, cl, dl, flag))
        nxt = nx
    order = {uop_hash("build/map0legacymul/%08d.dat" % i): i for i in range(len(ents) + 5)}
    ents.sort(key=lambda e: order[e[0]])
    out = bytearray()
    for h, off, cl, dl, flag in ents:
        assert flag == 0 and cl == dl, "compressed map chunks are not supported"
        out += b[off:off + cl]
    return bytes(out)


def load_tiledata(uodata):
    raw = open(os.path.join(uodata, "tiledata.mul"), "rb").read()
    land = {}
    o = 0
    for g in range(512):
        o += 4
        for i in range(32):
            land[g * 32 + i] = struct.unpack_from("<Q", raw, o)[0]
            o += 30
    flags, height = {}, {}
    for g in range(2048):
        o += 4
        for i in range(32):
            flags[g * 32 + i] = struct.unpack_from("<Q", raw, o)[0]
            height[g * 32 + i] = raw[o + 20]
            o += 41
    return land, flags, height


def build(uodata):
    m = load_map(uodata)
    land, iflags, iheight = load_tiledata(uodata)
    idx = open(os.path.join(uodata, "staidx0.mul"), "rb").read()
    st = open(os.path.join(uodata, "statics0.mul"), "rb").read()
    bits = bytearray(W * H // 8)
    coarse = bytearray((W // CELL) * (H // CELL))
    hb = H // 8
    for bx in range(W // 8):
        for by in range(hb):
            bi = bx * hb + by
            off, ln, _ = struct.unpack_from("<iii", idx, bi * 12)
            per = defaultdict(list)
            if off >= 0 and ln > 0:
                for k in range(ln // 7):
                    tid, xo, yo, z, _h = struct.unpack_from("<HBBbH", st, off + k * 7)
                    per[(xo, yo)].append((z, iheight.get(tid, 0), iflags.get(tid, 0)))
            base = bi * 196 + 4
            for cy in range(8):
                for cx in range(8):
                    tid, lz = struct.unpack_from("<Hb", m, base + (cy * 8 + cx) * 3)
                    surfaces, obst = [], []
                    if not (land.get(tid, 0) & 0x40):                  # land that is not impassable (water and rock are)
                        surfaces.append(lz)
                    for z, h, f in per.get((cx, cy), ()):
                        bridge = f & 0x400
                        hh = h // 2 if bridge else h
                        if f & 0x40 and not bridge:
                            obst.append((z, z + hh))                   # impassable (a wall, a tree; a table is both surface and impassable)
                        elif f & 0x200 or bridge:
                            surfaces.append(z + hh)
                    ok = any(all(not (oz < s + 16 and ot > s) for oz, ot in obst) for s in surfaces)
                    if ok:
                        i = (bx * 8 + cx) * H + by * 8 + cy
                        bits[i >> 3] |= 1 << (i & 7)
    # coarse: walkable count per 4x4 tiles
    for cxx in range(W // CELL):
        for cyy in range(H // CELL):
            n = 0
            for dx in range(CELL):
                i0 = (cxx * CELL + dx) * H + cyy * CELL
                for dy in range(CELL):
                    i = i0 + dy
                    n += (bits[i >> 3] >> (i & 7)) & 1
            coarse[cxx * (H // CELL) + cyy] = n
    zb, zc = zlib.compress(bytes(bits), 9), zlib.compress(bytes(coarse), 9)
    return b"WGRD1" + struct.pack("<HHI", W, H, len(zb)) + zb + zc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--uodata", default=os.path.join(ROOT, "UOData"))
    ap.add_argument("--out", default=os.path.join(HERE, "walkgrid.bin"))
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    data = build(a.uodata)
    if a.check:
        same = os.path.exists(a.out) and open(a.out, "rb").read() == data
        print("walkgrid.bin is up to date" if same else "walkgrid.bin DIFFERS from the inputs: run make_walkgrid.py")
        sys.exit(0 if same else 1)
    with open(a.out, "wb") as f:
        f.write(data)
    print(f"wrote {a.out}: {len(data)} bytes, md5 {hashlib.md5(data).hexdigest()}")


if __name__ == "__main__":
    main()
