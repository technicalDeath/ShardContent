"""Reads the client's item art (artLegacyMUL.uop), tile data (tiledata.mul) and hues (hues.mul) straight from UOData.

Used by the cosmetic reward catalog, but standalone and pure Python (no Pillow).

  python uoart.py names <regex> [minId maxId]     -> id, name, flags, height, art size for item tiles whose name matches
  python uoart.py range <lo> <hi>                  -> every non-empty item id in [lo, hi] with name and art size
  python uoart.py sheet out.png id|lo-hi ...       -> labelled contact sheet (ids are hex or decimal, ranges allowed)
                                                      env: COLS=10 SCALE=2 CELL=96 BG=70,70,70 HUE=0
  python uoart.py info id                          -> one tile in full
  python uoart.py png out.png id [hue] [scale]     -> one transparent PNG
"""
import mmap
import os
import re
import struct
import sys
import zlib

ROOT = os.environ.get("UO_ROOT") or os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "UOData"))
ART_UOP = os.path.join(ROOT, "artLegacyMUL.uop")
TILEDATA = os.path.join(ROOT, "tiledata.mul")
HUES = os.path.join(ROOT, "hues.mul")

M = 0xFFFFFFFF

FLAGS = {
    0x1: "Background", 0x2: "Weapon", 0x4: "Transparent", 0x8: "Translucent", 0x10: "Wall", 0x20: "Damaging",
    0x40: "Impassable", 0x80: "Wet", 0x200: "Surface", 0x400: "Bridge", 0x800: "Generic", 0x1000: "Window",
    0x2000: "NoShoot", 0x4000: "ArticleA", 0x8000: "ArticleAn", 0x10000: "Internal", 0x20000: "Foliage",
    0x40000: "PartialHue", 0x80000: "NoHouse", 0x100000: "Map", 0x200000: "Container", 0x400000: "Wearable",
    0x800000: "LightSource", 0x1000000: "Animation", 0x2000000: "NoDiagonal", 0x8000000: "Armor",
    0x10000000: "Roof", 0x20000000: "Door", 0x40000000: "StairBack", 0x80000000: "StairRight",
}
SHORT = {"Background": "bg", "Weapon": "wpn", "Transparent": "tr", "Translucent": "tl", "Wall": "wall",
         "Damaging": "dmg", "Impassable": "imp", "Wet": "wet", "Surface": "surf", "Bridge": "br", "Generic": "gen",
         "Window": "win", "NoShoot": "nosh", "Foliage": "foli", "PartialHue": "phue", "Container": "cont",
         "Wearable": "wear", "LightSource": "light", "Animation": "anim", "Armor": "armor", "Roof": "roof",
         "Door": "door", "StairBack": "stairB", "StairRight": "stairR", "NoHouse": "nohouse", "Map": "map"}


def _rot(x, r):
    return ((x << r) | (x >> (32 - r))) & M


def hashlittle2(s: bytes):
    length = len(s)
    a = b = c = (0xDEADBEEF + length) & M
    k = 0
    while length > 12:
        a = (a + struct.unpack_from("<I", s, k)[0]) & M
        b = (b + struct.unpack_from("<I", s, k + 4)[0]) & M
        c = (c + struct.unpack_from("<I", s, k + 8)[0]) & M
        a = (a - c) & M; a ^= _rot(c, 4); c = (c + b) & M
        b = (b - a) & M; b ^= _rot(a, 6); a = (a + c) & M
        c = (c - b) & M; c ^= _rot(b, 8); b = (b + a) & M
        a = (a - c) & M; a ^= _rot(c, 16); c = (c + b) & M
        b = (b - a) & M; b ^= _rot(a, 19); a = (a + c) & M
        c = (c - b) & M; c ^= _rot(b, 4); b = (b + a) & M
        length -= 12
        k += 12
    tail = s[k:] + b"\x00" * 12
    if length > 0:
        if length >= 12: c = (c + struct.unpack_from("<I", tail, 8)[0]) & M
        elif length > 8: c = (c + (struct.unpack_from("<I", tail, 8)[0] & (0xFFFFFFFF >> (8 * (12 - length))))) & M
        if length >= 8: b = (b + struct.unpack_from("<I", tail, 4)[0]) & M
        elif length > 4: b = (b + (struct.unpack_from("<I", tail, 4)[0] & (0xFFFFFFFF >> (8 * (8 - length))))) & M
        if length >= 4: a = (a + struct.unpack_from("<I", tail, 0)[0]) & M
        else: a = (a + (struct.unpack_from("<I", tail, 0)[0] & (0xFFFFFFFF >> (8 * (4 - length))))) & M
        c ^= b; c = (c - _rot(b, 14)) & M
        a ^= c; a = (a - _rot(c, 11)) & M
        b ^= a; b = (b - _rot(a, 25)) & M
        c ^= b; c = (c - _rot(b, 16)) & M
        a ^= c; a = (a - _rot(c, 4)) & M
        b ^= a; b = (b - _rot(a, 14)) & M
        c ^= b; c = (c - _rot(b, 24)) & M
    return (b << 32) | c


class Tile:
    __slots__ = ("id", "flags", "weight", "layer", "count", "anim", "hue", "light", "height", "name")

    def flag_names(self):
        return [n for bit, n in FLAGS.items() if self.flags & bit]

    def short_flags(self):
        return ",".join(SHORT[n] for n in self.flag_names() if n in SHORT)


_tiles = None


def tiles():
    """All 0x10000 item tiles from tiledata.mul (high-seas layout: 41-byte item records)."""
    global _tiles
    if _tiles is not None:
        return _tiles
    data = open(TILEDATA, "rb").read()
    land = 512 * (4 + 32 * 30)
    n_items = (len(data) - land) // (4 + 32 * 41) * 32
    out = []
    pos = land
    for i in range(n_items):
        if i % 32 == 0:
            pos += 4
        t = Tile()
        t.id = i
        t.flags, t.weight, t.layer, t.count, t.anim, t.hue, t.light, t.height = struct.unpack_from("<QBBiHHHB", pos and data, pos)
        t.name = data[pos + 21:pos + 41].split(b"\x00")[0].decode("latin-1")
        pos += 41
        out.append(t)
    _tiles = out
    return out


class Art:
    def __init__(self):
        self.f = open(ART_UOP, "rb")
        self.mm = mmap.mmap(self.f.fileno(), 0, access=mmap.ACCESS_READ)
        self.index = self._load_index()

    def _load_index(self):
        mm = self.mm
        magic, ver, sig, nxt, bsize, fcount = struct.unpack_from("<4sIIQII", mm, 0)
        assert magic == b"MYP\x00", "not a UOP file"
        by_hash = {}
        while nxt:
            n, nxt2 = struct.unpack_from("<IQ", mm, nxt)
            p = nxt + 12
            for _ in range(n):
                off, hlen, clen, dlen, h, crc, flag = struct.unpack_from("<QIIIQIH", mm, p)
                p += 34
                if off:
                    by_hash[h] = (off + hlen, clen, dlen, flag)
            nxt = nxt2
        index = {}
        for i in range(0x14000):
            h = hashlittle2(("build/artlegacymul/%08d.tga" % i).encode())
            e = by_hash.get(h)
            if e:
                index[i] = e
        return index

    def raw_static(self, item_id):
        e = self.index.get(0x4000 + item_id)
        if not e:
            return None
        off, clen, dlen, flag = e
        data = self.mm[off:off + clen]
        if flag == 1:
            data = zlib.decompress(data)
        return data

    def static(self, item_id):
        """-> (width, height, rows) where rows[y] = {x: rgb555 value}, or None if the id has no art."""
        raw = self.raw_static(item_id)
        if not raw or len(raw) < 8:
            return None
        w, h = struct.unpack_from("<HH", raw, 4)
        if w == 0 or h == 0 or w > 1024 or h > 1024:
            return None
        look = struct.unpack_from("<%dH" % h, raw, 8)
        base = 8 + h * 2
        rows = []
        for y in range(h):
            pos = base + look[y] * 2
            x = 0
            row = {}
            while pos + 4 <= len(raw):
                xo, run = struct.unpack_from("<HH", raw, pos)
                pos += 4
                if xo + run == 0:
                    break
                x += xo
                if pos + run * 2 > len(raw):
                    break
                for px in struct.unpack_from("<%dH" % run, raw, pos):
                    row[x] = px
                    x += 1
                pos += run * 2
            rows.append(row)
        return w, h, rows


_art = None


def art():
    global _art
    if _art is None:
        _art = Art()
    return _art


_hues = None


def hue_table(h):
    """32-entry colour table of hue number h (1-based like the client), or None for hue 0."""
    global _hues
    if h <= 0:
        return None
    if _hues is None:
        d = open(HUES, "rb").read()
        _hues = []
        pos = 0
        while pos + 708 <= len(d):
            pos += 4
            for _ in range(8):
                _hues.append(struct.unpack_from("<32H", d, pos))
                pos += 88
    h -= 1
    return _hues[h] if h < len(_hues) else None


def rgb(c555):
    return (((c555 >> 10) & 31) * 255 // 31, ((c555 >> 5) & 31) * 255 // 31, (c555 & 31) * 255 // 31)


def to_rgba(item_id, hue=0, partial=None):
    """-> (w, h, [[(r,g,b,a)...]...]) cropped to the opaque bounding box, or None."""
    s = art().static(item_id)
    if not s:
        return None
    w, h, rows = s
    tab = hue_table(hue & 0x7FFF)
    if partial is None:
        t = tiles()[item_id]
        partial = bool(t.flags & 0x40000)
    full = bool(hue & 0x8000) or not partial
    minx, maxx, miny, maxy = w, -1, h, -1
    for y, row in enumerate(rows):
        for x in row:
            if row[x]:
                minx, maxx, miny, maxy = min(minx, x), max(maxx, x), min(miny, y), max(maxy, y)
    if maxx < 0:
        return None
    out = []
    for y in range(miny, maxy + 1):
        line = []
        for x in range(minx, maxx + 1):
            c = rows[y].get(x, 0)
            if not c:
                line.append((0, 0, 0, 0))
                continue
            c &= 0x7FFF
            if tab:
                r5, g5, b5 = (c >> 10) & 31, (c >> 5) & 31, c & 31
                if full or (r5 == g5 == b5):
                    c = tab[r5] & 0x7FFF
            r, g, b = rgb(c)
            line.append((r, g, b, 255))
        out.append(line)
    return maxx - minx + 1, maxy - miny + 1, out


def _layer(item_id, hue):
    """Uncropped pixels of one item: -> (w, h, {(x,y): (r,g,b)}) or None."""
    s = art().static(item_id)
    if not s:
        return None
    w, h, rows = s
    tab = hue_table(hue & 0x7FFF)
    t = tiles()[item_id]
    full = bool(hue & 0x8000) or not (t.flags & 0x40000)
    px = {}
    for y, row in enumerate(rows):
        for x, c in row.items():
            if not c:
                continue
            c &= 0x7FFF
            if tab:
                r5, g5, b5 = (c >> 10) & 31, (c >> 5) & 31, c & 31
                if full or (r5 == g5 == b5):
                    c = tab[r5] & 0x7FFF
            px[(x, y)] = rgb(c)
    return w, h, px


def compose(parts):
    """parts = [(item_id, dx, dy, dz, hue), ...] laid out like a multi/addon (22px per tile step, 4px per z).
    Sprites are bottom-centred on their tile (bottom edge at the tile's lower corner).
    Draw order follows the list order unless sorted by the caller. -> (w, h, rows) cropped, or None."""
    r = compose_anchored(parts)
    return None if r is None else r[:3]


def compose_anchored(parts):
    """Like compose, but also returns where the cropped image sits relative to tile (0,0):
    -> (w, h, rows, minx, miny) with minx/miny measured from the tile's centre line (x) and top corner (y); the tile's bottom
    vertex is at x=0, y=44 in that system."""
    canvas = {}
    for part in parts:
        item_id, dx, dy, dz = part[:4]
        hue = part[4] if len(part) > 4 else 0
        lay = _layer(item_id, hue)
        if not lay:
            continue
        w, h, px = lay
        cx = (dx - dy) * 22
        top = (dx + dy) * 22 - dz * 4
        left = cx - w // 2
        y0 = top + 44 - h
        for (x, y), c in px.items():
            canvas[(left + x, y0 + y)] = c
    if not canvas:
        return None
    xs = [k[0] for k in canvas]
    ys = [k[1] for k in canvas]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    rows = []
    for y in range(miny, maxy + 1):
        rows.append([canvas[(x, y)] + (255,) if (x, y) in canvas else (0, 0, 0, 0) for x in range(minx, maxx + 1)])
    return maxx - minx + 1, maxy - miny + 1, rows, minx, miny


def parts_sorted(parts):
    """Painter's order for a multi: back (small dx+dy) first, lower z first."""
    return sorted(parts, key=lambda p: (p[1] + p[2], p[3]))


def write_png(path, width, height, pixels):
    raw = b"".join(b"\x00" + b"".join(bytes(p) for p in row) for row in pixels)

    def chunk(t, d):
        c = struct.pack(">I", len(d)) + t + d
        return c + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)

    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        f.write(chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)))
        f.write(chunk(b"IDAT", zlib.compress(raw, 6)))
        f.write(chunk(b"IEND", b""))


def scaled(pix, scale):
    if scale == 1:
        return pix
    out = []
    for row in pix:
        r2 = [p for p in row for _ in range(scale)]
        for _ in range(scale):
            out.append(r2)
    return out


def item_png(path, item_id, hue=0, scale=2, pad=4):
    r = to_rgba(item_id, hue)
    if not r:
        return False
    w, h, pix = r
    pix = scaled(pix, scale)
    pw, ph = w * scale, h * scale
    blank = (0, 0, 0, 0)
    canvas = [[blank] * (pw + 2 * pad) for _ in range(pad)]
    for row in pix:
        canvas.append([blank] * pad + row + [blank] * pad)
    canvas += [[blank] * (pw + 2 * pad) for _ in range(pad)]
    write_png(path, pw + 2 * pad, ph + 2 * pad, canvas)
    return True


# 3x5 label font
FONT = {
    "0": "111101101101111", "1": "010110010010111", "2": "111001111100111", "3": "111001111001111",
    "4": "101101111001001", "5": "111100111001111", "6": "111100111101111", "7": "111001001001001",
    "8": "111101111101111", "9": "111101111001111", "A": "010101111101101", "B": "110101110101110",
    "C": "011100100100011", "D": "110101101101110", "E": "111100110100111", "F": "111100110100100",
    "x": "000101010101000", "X": "101101010101101", "h": "100100110101101", "-": "000000111000000",
    ".": "000000000000010", "/": "001001010100100", "#": "101111101111101", " ": "000000000000000",
}


def label(canvas, x, y, text, color=(255, 235, 120, 255), scale=2):
    for ch in text:
        g = FONT.get(ch, FONT[" "])
        for gy in range(5):
            for gx in range(3):
                if g[gy * 3 + gx] == "1":
                    for dy in range(scale):
                        for dx in range(scale):
                            px, py = x + gx * scale + dx, y + gy * scale + dy
                            if 0 <= py < len(canvas) and 0 <= px < len(canvas[0]):
                                canvas[py][px] = color
        x += 4 * scale


def parse_ids(args):
    ids = []
    for a in args:
        if "-" in a:
            lo, hi = a.split("-", 1)
            ids.extend(range(int(lo, 0), int(hi, 0) + 1))
        else:
            ids.append(int(a, 0))
    return ids


def sheet(out, ids, cols=10, scale=2, cell=96, bg=(70, 70, 70), hue=0, skip_empty=False, hues=None):
    cells = []
    for i in ids:
        hh = (hues or {}).get(i, hue)
        r = to_rgba(i, hh)
        if r is None and skip_empty:
            continue
        cells.append((i, r))
    if not cells:
        raise SystemExit("nothing to draw")
    rows_n = (len(cells) + cols - 1) // cols
    cw, ch = cell, cell + 14
    W, H = cols * cw, rows_n * ch
    bgc = tuple(bg) + (255,)
    canvas = [[bgc] * W for _ in range(H)]
    for n, (i, r) in enumerate(cells):
        cx, cy = (n % cols) * cw, (n // cols) * ch
        for x in range(cx, cx + cw):
            canvas[cy][x] = (40, 40, 40, 255)
        for y in range(cy, cy + ch):
            canvas[y][cx] = (40, 40, 40, 255)
        label(canvas, cx + 3, cy + 3, "0x%04X" % i, scale=2)
        if r:
            w, h, pix = r
            s = scale
            while s > 1 and (w * s > cw - 6 or h * s > cell - 8):
                s -= 1
            if w * s > cw - 6 or h * s > cell - 8:
                # too big even at 1x: crop to the cell
                pass
            px0 = cx + max(2, (cw - w * s) // 2)
            py0 = cy + 14 + max(0, (cell - 8 - h * s) // 2)
            for y, row in enumerate(pix):
                for x, p in enumerate(row):
                    if p[3]:
                        for dy in range(s):
                            for dx in range(s):
                                yy, xx = py0 + y * s + dy, px0 + x * s + dx
                                if cy < yy < cy + ch and cx < xx < cx + cw:
                                    canvas[yy][xx] = p
    write_png(out, W, H, canvas)
    return W, H, len(cells)


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return
    cmd = argv[1]
    T = tiles()
    if cmd == "names":
        rx = re.compile(argv[2], re.I)
        lo = int(argv[3], 0) if len(argv) > 3 else 0
        hi = int(argv[4], 0) if len(argv) > 4 else 0xFFFF
        a = art()
        for t in T[lo:hi + 1]:
            if t.name and rx.search(t.name):
                s = a.static(t.id)
                size = "%dx%d" % (s[0], s[1]) if s else "-"
                print("0x%04X  %-22s h=%-2d %-8s %s" % (t.id, t.name, t.height, size, t.short_flags()))
    elif cmd == "range":
        lo, hi = int(argv[2], 0), int(argv[3], 0)
        a = art()
        for t in T[lo:hi + 1]:
            s = a.static(t.id)
            if s:
                print("0x%04X  %-22s h=%-2d %dx%d %s" % (t.id, t.name, t.height, s[0], s[1], t.short_flags()))
    elif cmd == "sheet":
        out = argv[2]
        ids = parse_ids(argv[3:])
        W, H, n = sheet(out, ids, cols=int(os.environ.get("COLS", "10")), scale=int(os.environ.get("SCALE", "2")),
                        cell=int(os.environ.get("CELL", "96")),
                        bg=tuple(int(v) for v in os.environ.get("BG", "70,70,70").split(",")),
                        hue=int(os.environ.get("HUE", "0")), skip_empty=os.environ.get("SKIP_EMPTY") == "1")
        print("wrote", out, W, H, n, "cells")
    elif cmd == "info":
        t = T[int(argv[2], 0)]
        s = art().static(t.id)
        print("id=0x%04X name=%r flags=0x%X (%s) weight=%d layer=%d count=%d anim=%d hue=%d light=%d height=%d art=%s" % (
            t.id, t.name, t.flags, ",".join(t.flag_names()), t.weight, t.layer, t.count, t.anim, t.hue, t.light,
            t.height, "%dx%d" % (s[0], s[1]) if s else "none"))
    elif cmd == "compose":
        # compose out.png id:dx:dy:dz[:hue] ...   (a multi/addon laid out like the client does)
        parts = []
        for a in argv[3:]:
            f = [int(v, 0) for v in a.split(":")]
            parts.append(tuple(f))
        r = compose(parts_sorted(parts))
        if not r:
            print("no art")
            return
        w, h, pix = r
        sc = int(os.environ.get("SCALE", "2"))
        write_png(argv[2], w * sc, h * sc, scaled(pix, sc))
        print("wrote", argv[2], w * sc, h * sc)
    elif cmd == "png":
        ok = item_png(argv[2], int(argv[3], 0), int(argv[4], 0) if len(argv) > 4 else 0,
                      int(argv[5]) if len(argv) > 5 else 2)
        print("wrote" if ok else "no art", argv[2])
    else:
        print(__doc__)


if __name__ == "__main__":
    main(sys.argv)
