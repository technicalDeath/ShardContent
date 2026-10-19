"""Writes the shard's map patches into copies of the map's statics files, so added pieces are real map statics: drawn like the
map's own decoration, never highlighted or clickable, and seen by the server's walking and house placement exactly as the client
sees them (owner, 2026-10-18).

  python apply_statics_patch.py PRISTINE-DIR OUT-DIR PATCH.json [PATCH.json ...]

Reads statics{m}.mul / staidx{m}.mul (and the statics{m}x.mul / staidx{m}x.mul pair when present) from PRISTINE-DIR, the
untouched client files, and writes patched copies to OUT-DIR. Each touched 8x8 block gets its original statics plus the new
ones, appended as a fresh block record at the end of the statics file with its index entry pointing there; untouched blocks
keep their bytes and offsets. A piece already present (same graphic, tile and height) is not added twice. Always patch from
the pristine files: patching a patched file again would only skip duplicates, but the pristine copy is the record.

Format: staidx entries are 12 bytes (offset u32, length u32, extra u32), one per block, block = bx * height_blocks + by;
statics entries are 7 bytes (graphic u16, x u8, y u8 within the block, z s8, hue u16).
"""
import hashlib
import json
import os
import struct
import sys

HEIGHT_BLOCKS = {0: 512, 1: 512, 2: 200, 3: 320, 4: 181, 5: 256}


def patch_pair(src_dir, out_dir, idx_name, mul_name, height_blocks, pieces):
    idx = bytearray(open(os.path.join(src_dir, idx_name), "rb").read())
    mul = bytearray(open(os.path.join(src_dir, mul_name), "rb").read())
    by_block = {}
    for graphic, x, y, z, hue in pieces:
        by_block.setdefault((x >> 3) * height_blocks + (y >> 3), []).append((graphic, x & 7, y & 7, z, hue))
    added = 0
    for block, new in sorted(by_block.items()):
        lookup, length, extra = struct.unpack_from("<III", idx, block * 12)
        have = b"" if lookup == 0xFFFFFFFF or length in (0, 0xFFFFFFFF) else bytes(mul[lookup:lookup + length])
        present = {struct.unpack_from("<HBBb", have, k) for k in range(0, len(have) - 6, 7)}
        extra_bytes = b""
        for graphic, bx, by, z, hue in new:
            if (graphic, bx, by, z) in present:
                continue
            extra_bytes += struct.pack("<HBBbH", graphic, bx, by, z, hue)
            present.add((graphic, bx, by, z))
            added += 1
        if not extra_bytes:
            continue
        data = have + extra_bytes
        offset = len(mul)
        mul += data
        struct.pack_into("<III", idx, block * 12, offset, len(data), 0 if extra == 0xFFFFFFFF else extra)
    os.makedirs(out_dir, exist_ok=True)
    open(os.path.join(out_dir, idx_name), "wb").write(idx)
    open(os.path.join(out_dir, mul_name), "wb").write(mul)
    return added, hashlib.sha256(mul).hexdigest()[:16], hashlib.sha256(idx).hexdigest()[:16]


def main(argv):
    src, out = argv[0], argv[1]
    by_map = {}
    for path in argv[2:]:
        p = json.load(open(path, encoding="utf-8"))
        by_map.setdefault(p["map"], []).extend(tuple(s) for s in p["statics"])
    for m, pieces in by_map.items():
        for suffix in ("", "x"):
            idx_name, mul_name = "staidx%d%s.mul" % (m, suffix), "statics%d%s.mul" % (m, suffix)
            if not os.path.exists(os.path.join(src, idx_name)):
                continue
            added, mul_hash, idx_hash = patch_pair(src, out, idx_name, mul_name, HEIGHT_BLOCKS[m], pieces)
            print("%s: %d of %d pieces added (statics sha256 %s, index %s)" % (mul_name, added, len(pieces), mul_hash, idx_hash))


if __name__ == "__main__":
    main(sys.argv[1:])
