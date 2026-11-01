"""Generate watergrid.bin: where the water is (Felucca surface, x < 5120), for the fisher's choice of a standing tile (fishspot.py). Read-only on the inputs; deterministic.

    python make_watergrid.py                 # writes watergrid.bin next to this file
    python make_watergrid.py --check         # exit 1 if watergrid.bin differs from what the inputs would produce

Input: the client's map (map0LegacyMUL.uop / map0.mul, read with make_walkgrid.load_map) and its statics (statics0.mul + staidx0.mul): a tile is water when
the engine lets a fisher cast at it (Fishing.cs): its land tile is one of 0xA8-0xAB or 0x136-0x137 (targettile x y z 0), or a static on it is one of
0x1797-0x179C, 0x346E-0x3485, 0x3490-0x34AB, 0x34B5-0x35D5 (rivers, ponds and much of the coast are drawn as statics; targettile x y z <graphic>).
Until 2026-10-31 only the 0xA8-0xAB land counted, and the world held 387 fish banks with a stand.
Land water is almost all at z -5 (207,131 of 207,148 sampled).
Files: watergrid.bin = b"WTR1", W (u16), H (u16), zlib(bits): bit i & 7 of byte i >> 3, index x * H + y, 1 = water;
waterstatics.bin = b"WST1", n (u32), zlib(n records of x u16, y u16, z i8, graphic u16): the tiles that are water only by a static, for the cast's target.
"""
import argparse
import hashlib
import os
import struct
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_walkgrid as mw  # noqa: E402

WATER = set(range(0xA8, 0xAC)) | {0x136, 0x137}                                   # Fishing.cs _waterLandTiles
WATER_STATICS = set(range(0x1797, 0x179D)) | set(range(0x346E, 0x3486)) | set(range(0x3490, 0x34AC)) | set(range(0x34B5, 0x35D6))   # waterStaticTiles
W, H = mw.W, mw.H


def build(uodata):
    """(watergrid.bin bytes, waterstatics.bin bytes)."""
    m = mw.load_map(uodata)
    idx = open(os.path.join(uodata, "staidx0.mul"), "rb").read()
    st = open(os.path.join(uodata, "statics0.mul"), "rb").read()
    bits = bytearray(W * H // 8)
    statics = []
    hb = H // 8
    for bx in range(W // 8):
        for by in range(hb):
            bi = bx * hb + by
            base = bi * 196 + 4
            sw = {}
            off, ln, _ = struct.unpack_from("<iii", idx, bi * 12)
            if off >= 0 and ln > 0:
                for k in range(ln // 7):
                    tid, xo, yo, z, _h = struct.unpack_from("<HBBbH", st, off + k * 7)
                    if tid in WATER_STATICS and ((xo, yo) not in sw or z > sw[(xo, yo)][0]):
                        sw[(xo, yo)] = (z, tid)                                     # the top one: that is the one a cursor lands on
            for cy in range(8):
                for cx in range(8):
                    land = struct.unpack_from("<H", m, base + (cy * 8 + cx) * 3)[0] in WATER
                    if land or (cx, cy) in sw:
                        i = (bx * 8 + cx) * H + by * 8 + cy
                        bits[i >> 3] |= 1 << (i & 7)
                        if not land:
                            z, tid = sw[(cx, cy)]
                            statics.append(struct.pack("<HHbH", bx * 8 + cx, by * 8 + cy, z, tid))
    grid = b"WTR1" + struct.pack("<HH", W, H) + zlib.compress(bytes(bits), 9)
    side = b"WST1" + struct.pack("<I", len(statics)) + zlib.compress(b"".join(statics), 9)
    return grid, side


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--uodata", default=os.path.join(mw.ROOT, "UOData"))
    ap.add_argument("--out", default=os.path.join(HERE, "watergrid.bin"))
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    data, side = build(a.uodata)
    side_out = os.path.join(os.path.dirname(a.out), "waterstatics.bin")
    if a.check:
        same = os.path.exists(a.out) and open(a.out, "rb").read() == data and os.path.exists(side_out) and open(side_out, "rb").read() == side
        print("watergrid.bin is up to date" if same else "watergrid.bin DIFFERS from the inputs: run make_watergrid.py")
        sys.exit(0 if same else 1)
    with open(a.out, "wb") as f:
        f.write(data)
    with open(side_out, "wb") as f:
        f.write(side)
    n = struct.unpack_from("<I", side, 4)[0]
    print(f"wrote {a.out}: {len(data)} bytes, md5 {hashlib.md5(data).hexdigest()}; {side_out}: {n} static water tiles")


if __name__ == "__main__":
    main()
