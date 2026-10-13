"""Draws the two icons of the main backpack's size button as the client's gump files (owner ruling 2026-10-12: an icon, not text, matching the pack).

A small brass diamond like the one the pack art carries to minimise it, with a gold plus (make the pack larger) or minus (make it smaller) inside.

  python make_pack_icons.py [out folder]        (default: ShardContent/data/client/gumps; a preview PNG goes beside this script)

Art ids: 62050 plus, 62051 minus, 62052 options gear (62010-62041 are the window buttons, 50000-50999 the buff icons).
"""
import os
import struct
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "..", "data", "client", "gumps")
SIZE = 23          # odd, so the diamond has a centre pixel
C = SIZE // 2

OUTLINE = (28, 20, 8)
GOLD_LIGHT = (246, 214, 112)
GOLD = (214, 170, 66)
GOLD_DARK = (132, 96, 30)
INSIDE_TOP = (78, 54, 26)
INSIDE_BOTTOM = (44, 28, 12)
GLYPH = (240, 204, 96)
GLYPH_SHADOW = (24, 14, 4)


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def diamond(glyph):
    """Rows of (r, g, b) or None for transparent."""
    rows = [[None] * SIZE for _ in range(SIZE)]

    for y in range(SIZE):
        for x in range(SIZE):
            dx, dy = x - C, y - C
            d = abs(dx) + abs(dy)

            if d > C:
                continue

            if d == C:
                rows[y][x] = OUTLINE
            elif d >= C - 3:
                # the brass rim, lit from the upper left: light on the two upper-left edges, dark on the two lower-right edges
                lit = (dx + dy) / float(C)                 # -1 upper left .. +1 lower right
                ring = (d - (C - 3)) / 2.0                 # 0 inner .. 1 outer
                base = lerp(GOLD_LIGHT, GOLD_DARK, (lit + 1.0) / 2.0)
                rows[y][x] = lerp(base, GOLD, 0.35 * (1.0 - ring)) if d < C - 1 else lerp(base, OUTLINE, 0.25)
            else:
                rows[y][x] = lerp(INSIDE_TOP, INSIDE_BOTTOM, (dy + C) / (2.0 * C))

    marks = []

    for k in range(-4, 5):
        for t in (-1, 0, 1):
            marks.append((k, t))                               # the horizontal bar
            if glyph == "plus":
                marks.append((t, k))                           # and the vertical one

    for dx, dy in marks:                                       # a shadow one pixel down and right, then the gold
        x, y = C + dx + 1, C + dy + 1
        if 0 <= x < SIZE and 0 <= y < SIZE and abs(x - C) + abs(y - C) < C - 3 and rows[y][x] is not None:
            rows[y][x] = GLYPH_SHADOW

    for dx, dy in marks:
        rows[C + dy][C + dx] = GLYPH

    return rows


def gear():
    """The options button of the potion and combat bars: a small brass gear (a cog with eight teeth and a hole), lit from the upper left like the diamonds."""
    import math

    rows = [[None] * SIZE for _ in range(SIZE)]
    teeth, body, hole = 8, 6.4, 2.6

    for y in range(SIZE):
        for x in range(SIZE):
            dx, dy = x - C, y - C
            r = math.hypot(dx, dy)
            angle = math.atan2(dy, dx)
            tooth = abs(math.sin(angle * teeth / 2.0)) > 0.62
            edge = body + (3.6 if tooth else 0.0)

            if r > edge + 0.6 or r < hole - 0.6:
                continue

            lit = (dx + dy) / (2.0 * max(r, 1.0)) if r else 0.0
            shade = (lit + 1.0) / 2.0

            if r >= edge - 0.5 or r <= hole + 0.5:
                rows[y][x] = OUTLINE
            elif r > body - 1.4 and not tooth:
                rows[y][x] = lerp(GOLD_LIGHT, GOLD_DARK, shade)
            else:
                rows[y][x] = lerp(GOLD_LIGHT, GOLD, 0.4 + 0.5 * shade) if not tooth else lerp(GOLD_LIGHT, GOLD_DARK, shade)

    return rows


def gump_bytes(pixels):
    h, w = len(pixels), len(pixels[0])
    out = []

    for row in pixels:
        runs = []
        for rgb in row:
            c = 0 if rgb is None else (((rgb[0] >> 3) << 10) | ((rgb[1] >> 3) << 5) | (rgb[2] >> 3) | 0x8000)
            if runs and runs[-1][0] == c:
                runs[-1][1] += 1
            else:
                runs.append([c, 1])
        out.append(b"".join(struct.pack("<HH", c, n) for c, n in runs))

    offsets, at = [], h
    for r in out:
        offsets.append(at)
        at += len(r) // 4

    return struct.pack("<II", w, h) + struct.pack("<%dI" % h, *offsets) + b"".join(out)


def png(path, sheet, scale=8, gap=2):
    w = sum(len(p[0]) for p in sheet) * scale + gap * scale * (len(sheet) + 1)
    h = (len(sheet[0]) + 2 * gap) * scale
    raw = bytearray()
    back = (92, 66, 36, 255)

    for y in range(h):
        raw.append(0)
        for x in range(w):
            px = back
            xx = x // scale - gap
            for p in sheet:
                pw = len(p[0])
                if 0 <= xx < pw:
                    yy = y // scale - gap
                    if 0 <= yy < len(p) and p[yy][xx] is not None:
                        px = p[yy][xx] + (255,)
                    break
                xx -= pw + gap
            raw.extend(px)

    def chunk(kind, data):
        body = kind + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)

    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b""))


def main():
    os.makedirs(OUT, exist_ok=True)
    plus, minus = diamond("plus"), diamond("minus")

    for art, pixels in ((62050, plus), (62051, minus)):
        with open(os.path.join(OUT, "%d.gump" % art), "wb") as f:
            f.write(gump_bytes(pixels))

    cog = gear()

    with open(os.path.join(OUT, "62052.gump"), "wb") as f:
        f.write(gump_bytes(cog))

    png(os.path.join(HERE, "pack-icons-preview.png"), [plus, minus, cog])
    print("62050 plus, 62051 minus and 62052 gear written to", os.path.abspath(OUT))


if __name__ == "__main__":
    main()
