"""Generate watergrid.bin: where the water is (Felucca surface, x < 5120), for the fisher's choice of a standing tile (fishspot.py). Read-only on the inputs; deterministic.

    python make_watergrid.py                 # writes watergrid.bin next to this file
    python make_watergrid.py --check         # exit 1 if watergrid.bin differs from what the inputs would produce

Input: the client's map (map0LegacyMUL.uop / map0.mul, read with make_walkgrid.load_map): a tile is water when its land tile is one of 0xA8-0xAB, the deep-water land
tiles the fishing target (targettile x y z 0) takes and the fisher's find_water looks for. Water tiles are almost all at z -5 (207,131 of 207,148 sampled).
File: b"WTR1", W (u16), H (u16), zlib(bits): bit i & 7 of byte i >> 3, index x * H + y, 1 = water.
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

WATER = set(range(0xA8, 0xAC))
W, H = mw.W, mw.H


def build(uodata):
    m = mw.load_map(uodata)
    bits = bytearray(W * H // 8)
    hb = H // 8
    for bx in range(W // 8):
        for by in range(hb):
            base = (bx * hb + by) * 196 + 4
            for cy in range(8):
                for cx in range(8):
                    if struct.unpack_from("<H", m, base + (cy * 8 + cx) * 3)[0] in WATER:
                        i = (bx * 8 + cx) * H + by * 8 + cy
                        bits[i >> 3] |= 1 << (i & 7)
    return b"WTR1" + struct.pack("<HH", W, H) + zlib.compress(bytes(bits), 9)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--uodata", default=os.path.join(mw.ROOT, "UOData"))
    ap.add_argument("--out", default=os.path.join(HERE, "watergrid.bin"))
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    data = build(a.uodata)
    if a.check:
        same = os.path.exists(a.out) and open(a.out, "rb").read() == data
        print("watergrid.bin is up to date" if same else "watergrid.bin DIFFERS from the inputs: run make_watergrid.py")
        sys.exit(0 if same else 1)
    with open(a.out, "wb") as f:
        f.write(data)
    print(f"wrote {a.out}: {len(data)} bytes, md5 {hashlib.md5(data).hexdigest()}")


if __name__ == "__main__":
    main()
