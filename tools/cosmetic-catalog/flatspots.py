"""Finds big flat, empty patches of Felucca (map 0) where a gallery of items can be laid out for client screenshots.

A block is 'clean' when it has no statics and all 64 land cells share one z and one of the plain grass/dirt tile ids.
Prints the largest runs of clean blocks (rectangles in tiles).

  python flatspots.py [min-blocks-wide] [min-blocks-high]
"""
import mmap
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import uoart  # noqa: E402

ROOT = uoart.ROOT
W_BLOCKS, H_BLOCKS = 896, 512


def load_blocks():
    f = open(os.path.join(ROOT, "map0LegacyMUL.uop"), "rb")
    mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
    magic, ver, sig, nxt, bsize, fcount = struct.unpack_from("<4sIIQII", mm, 0)
    by_hash = {}
    while nxt:
        n, nxt2 = struct.unpack_from("<IQ", mm, nxt)
        p = nxt + 12
        for _ in range(n):
            off, hlen, clen, dlen, h, crc, flag = struct.unpack_from("<QIIIQIH", mm, p)
            p += 34
            if off:
                by_hash[h] = (off + hlen, clen)
            nxt = nxt2
        nxt = nxt2
    chunks = []
    for i in range(200):
        e = by_hash.get(uoart.hashlittle2(("build/map0legacymul/%08d.dat" % i).encode()))
        if not e:
            break
        chunks.append(e)
    return mm, chunks


def main():
    mm, chunks = load_blocks()
    idx = open(os.path.join(ROOT, "staidx0.mul"), "rb").read()
    per_chunk = 0xC4000 // 196
    clean = bytearray(W_BLOCKS * H_BLOCKS)
    grass = {0x03, 0x04, 0x05, 0x06, 0x0D, 0x0E, 0x0F, 0x10, 0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17, 0x18, 0x19}
    for ci, (off, size) in enumerate(chunks):
        n = size // 196
        for b in range(n):
            block = ci * per_chunk + b
            if block >= W_BLOCKS * H_BLOCKS:
                break
            lookup, length, _ = struct.unpack_from("<III", idx, block * 12)
            if lookup != 0xFFFFFFFF and length not in (0, 0xFFFFFFFF):
                continue
            base = off + b * 196 + 4
            cells = struct.unpack_from("<" + "Hb" * 0 + "".join("Hb" for _ in range(64)), mm, base) if False else None
            z0 = None
            ok = True
            for c in range(64):
                tid, z = struct.unpack_from("<Hb", mm, base + c * 3)
                if tid not in grass or (z0 is not None and z != z0):
                    ok = False
                    break
                z0 = z
            if ok:
                clean[block] = 1
    # block index = bx * 512 + by ; find largest all-clean rectangles (greedy over a summed-area table)
    import itertools
    best = []
    grid = [[clean[bx * H_BLOCKS + by] for by in range(H_BLOCKS)] for bx in range(W_BLOCKS)]
    # histogram method per bx column strip
    heights = [0] * H_BLOCKS
    for bx in range(W_BLOCKS):
        for by in range(H_BLOCKS):
            heights[by] = heights[by] + 1 if grid[bx][by] else 0
        # largest rectangle in histogram (width along by, height along bx going back)
        stack = []
        for by in range(H_BLOCKS + 1):
            h = heights[by] if by < H_BLOCKS else 0
            start = by
            while stack and stack[-1][1] >= h:
                s, sh = stack.pop()
                width = by - s
                if sh >= 3 and width >= 3:
                    best.append((sh * width, bx - sh + 1, s, sh, width))
                start = s
            stack.append((start, h))
    best.sort(reverse=True)
    seen = []
    for area, bx0, by0, hx, wy in best:
        if any(abs(bx0 - a) < 8 and abs(by0 - b) < 8 for a, b in seen):
            continue
        seen.append((bx0, by0))
        print("blocks %dx%d (x %d..%d, y %d..%d tiles) centre (%d,%d)  area=%d blocks" % (
            hx, wy, bx0 * 8, (bx0 + hx) * 8, by0 * 8, (by0 + wy) * 8,
            (bx0 + hx / 2) * 8, (by0 + wy / 2) * 8, area))
        if len(seen) >= 12:
            break


if __name__ == "__main__":
    main()
