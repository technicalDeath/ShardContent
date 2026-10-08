"""Draws the shard's own buff icons and writes what the client needs.

  python make_buff_icons.py [preview.png]

Reads data/configuration/buff-icons.json (customIcons: name, slot, art) and writes, under data/client/:
  gumps/<art>.gump   the picture, in the format the client fork reads from <client>/Gumps/ (width, height, then run-length rows
                     of 16-bit colour, zero meaning transparent: the same rows the stock gump archive holds)
  buff-extra.txt     one art id per line in slot order; the client appends these to its buff icon table, so slot k is icon
                     0x4A6 + k

The icons copy the stock buff icons' look (28 x 28, a flat colour that glows toward the middle, a white halo and a dark outline
round a tan subject), so they sit beside the stock ones without looking foreign. Green is a help, red a harm, blue neither.
Standard library only. To add an icon: add it to customIcons, write a drawing function below and register it in DRAWINGS.
"""
import json
import math
import os
import struct
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
SIZE = 28
SS = 6  # samples per pixel side

# ---- shapes: each returns the distance from a point to its edge, negative inside, in icon pixels


def capsule(x1, y1, x2, y2, r):
    dx, dy = x2 - x1, y2 - y1
    ll = dx * dx + dy * dy

    def d(x, y):
        t = 0.0 if ll == 0 else max(0.0, min(1.0, ((x - x1) * dx + (y - y1) * dy) / ll))
        return math.hypot(x - (x1 + t * dx), y - (y1 + t * dy)) - r

    return d


def circle(cx, cy, r):
    return lambda x, y: math.hypot(x - cx, y - cy) - r


def ring(cx, cy, r, w):
    return lambda x, y: abs(math.hypot(x - cx, y - cy) - r) - w


def rbox(cx, cy, hw, hh, rad):
    def d(x, y):
        qx, qy = abs(x - cx) - (hw - rad), abs(y - cy) - (hh - rad)
        return math.hypot(max(qx, 0), max(qy, 0)) + min(max(qx, qy), 0) - rad

    return d


def poly(points):
    n = len(points)

    def d(x, y):
        inside = False
        best = 1e9
        for i in range(n):
            (ax, ay), (bx, by) = points[i], points[(i + 1) % n]
            if (ay > y) != (by > y) and x < (bx - ax) * (y - ay) / (by - ay) + ax:
                inside = not inside
            ex, ey = bx - ax, by - ay
            t = max(0.0, min(1.0, ((x - ax) * ex + (y - ay) * ey) / (ex * ex + ey * ey)))
            best = min(best, math.hypot(x - (ax + t * ex), y - (ay + t * ey)))
        return -best if inside else best

    return d


def part(shape, top, bottom=None):
    """A piece of the subject: its shape and its colour (a top and a bottom colour give it a little shading)."""
    return (shape, top, bottom or top)


# ---- the three drawings

STEEL = ((222, 228, 238), (150, 158, 172))
GOLD = ((255, 222, 110), (200, 150, 40))
LEATHER = ((205, 165, 105), (150, 108, 62))
DARKLEATHER = ((150, 105, 60), (104, 68, 36))
PAPER = ((246, 238, 205), (214, 200, 160))
INK = ((60, 44, 34), (60, 44, 34))


def sword(tip, hilt):
    tx, ty = tip
    hx, hy = hilt
    length = math.hypot(tx - hx, ty - hy)
    ux, uy = (tx - hx) / length, (ty - hy) / length
    gx, gy = hx + ux * 6.0, hy + uy * 6.0  # where the blade meets the guard
    px, py = -uy, ux
    return [
        part(capsule(hx, hy, gx, gy, 1.05), *DARKLEATHER),
        part(capsule(gx, gy, tx, ty, 0.95), *STEEL),
        part(capsule(gx + px * 3.2, gy + py * 3.2, gx - px * 3.2, gy - py * 3.2, 1.05), *GOLD),
        part(circle(hx - ux * 0.6, hy - uy * 0.6, 1.5), *GOLD),
    ]


def draw_criminal_intent():
    """Two crossed swords: you are willing to fight."""
    return "red", sword((22.0, 4.5), (6.5, 23.5)) + sword((6.0, 4.5), (21.5, 23.5))


def draw_backpack_ward():
    """A backpack with a ward sigil on its pocket."""
    parts = [
        part(capsule(9.6, 7.5, 9.6, 4.2, 1.05), *DARKLEATHER),
        part(capsule(9.6, 4.2, 18.4, 4.2, 1.05), *DARKLEATHER),
        part(capsule(18.4, 4.2, 18.4, 7.5, 1.05), *DARKLEATHER),
        part(rbox(14.0, 16.5, 8.0, 9.0, 3.6), *LEATHER),
        part(rbox(14.0, 10.6, 8.0, 3.6, 2.6), *DARKLEATHER),
        part(circle(14.0, 13.6, 1.1), *GOLD),
        part(rbox(14.0, 20.2, 5.4, 3.5, 1.6), (178, 138, 84), (132, 94, 52)),
        part(ring(14.0, 20.2, 2.1, 0.55), (236, 255, 240)),
        part(circle(14.0, 20.2, 0.7), (236, 255, 240)),
    ]
    return "green", parts


def draw_faint_memories():
    """A book with a spark rising from it: what was known comes back."""
    parts = [
        part(poly([(2.5, 17.0), (13.6, 19.6), (13.6, 26.0), (2.5, 23.4)]), *DARKLEATHER),
        part(poly([(25.5, 17.0), (14.4, 19.6), (14.4, 26.0), (25.5, 23.4)]), *DARKLEATHER),
        part(poly([(3.6, 16.2), (13.5, 18.6), (13.5, 24.6), (3.6, 22.2)]), *PAPER),
        part(poly([(24.4, 16.2), (14.5, 18.6), (14.5, 24.6), (24.4, 22.2)]), *PAPER),
        part(capsule(14.0, 18.6, 14.0, 25.0, 0.45), *INK),
        part(capsule(5.6, 19.0, 11.8, 20.6, 0.3), *INK),
        part(capsule(5.6, 21.0, 11.8, 22.6, 0.3), *INK),
        part(capsule(16.2, 20.6, 22.4, 19.0, 0.3), *INK),
        part(capsule(16.2, 22.6, 22.4, 21.0, 0.3), *INK),
        part(poly([(14.0, 2.0), (15.4, 8.0), (14.0, 14.0), (12.6, 8.0)]), *GOLD),
        part(poly([(7.6, 8.0), (14.0, 6.6), (20.4, 8.0), (14.0, 9.4)]), *GOLD),
        part(circle(14.0, 8.0, 1.2), (255, 255, 235)),
        part(circle(7.0, 4.6, 0.9), (255, 244, 180)),
        part(circle(21.2, 4.0, 0.8), (255, 244, 180)),
        part(circle(19.6, 12.6, 0.7), (255, 244, 180)),
    ]
    return "blue", parts


DRAWINGS = {
    "CriminalIntent": draw_criminal_intent,
    "BackpackWard": draw_backpack_ward,
    "FaintMemories": draw_faint_memories,
}

# the corner colour and the centre colour of each background (read off the stock icons)
BACKGROUNDS = {
    "green": ((0, 98, 0), (96, 236, 146)),
    "red": ((123, 8, 8), (236, 78, 78)),
    "blue": ((0, 32, 189), (84, 124, 232)),
}
OUTLINE = (30, 24, 32)
HALO = (255, 255, 255)


def lerp(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def render(kind, parts):
    low, high = BACKGROUNDS[kind]
    pixels = []

    for py in range(SIZE):
        row = []

        for px in range(SIZE):
            acc = [0.0, 0.0, 0.0]

            for sy in range(SS):
                for sx in range(SS):
                    x = px + (sx + 0.5) / SS
                    y = py + (sy + 0.5) / SS
                    colour = None
                    nearest = 1e9

                    for shape, top, bottom in parts:
                        d = shape(x, y)
                        nearest = min(nearest, d)

                        if d <= 0:
                            colour = lerp(top, bottom, max(0.0, min(1.0, (y - 3.0) / 22.0)))

                    if colour is None:
                        if nearest <= 0.45:
                            colour = OUTLINE
                        elif nearest <= 1.35:
                            colour = HALO
                        else:
                            r = min(1.0, math.hypot(x - SIZE / 2, y - SIZE / 2) / 19.5)
                            colour = lerp(high, low, r * r)

                    for i in range(3):
                        acc[i] += colour[i]

            n = SS * SS
            row.append(tuple(max(0, min(255, int(round(c / n)))) for c in acc))

        pixels.append(row)

    return pixels


# ---- the gump file and the preview

def to_555(rgb):
    value = ((rgb[0] >> 3) << 10) | ((rgb[1] >> 3) << 5) | (rgb[2] >> 3) | 0x8000
    return value


def gump_bytes(pixels):
    h, w = len(pixels), len(pixels[0])
    rows = []

    for row in pixels:
        runs = []
        for rgb in row:
            c = to_555(rgb)
            if runs and runs[-1][0] == c:
                runs[-1][1] += 1
            else:
                runs.append([c, 1])
        rows.append(b"".join(struct.pack("<HH", c, n) for c, n in runs))

    offsets, at = [], h
    for r in rows:
        offsets.append(at)
        at += len(r) // 4

    return struct.pack("<II", w, h) + struct.pack("<%dI" % h, *offsets) + b"".join(rows)


def png_bytes(pixels, scale):
    h, w = len(pixels), len(pixels[0])
    raw = b""
    for row in pixels:
        line = b"".join(bytes(rgb) * scale for rgb in row)
        raw += (b"\x00" + line) * scale

    def chunk(t, d):
        c = struct.pack(">I", len(d)) + t + d
        return c + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)

    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", w * scale, h * scale, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw, 6))
        + chunk(b"IEND", b"")
    )


def main():
    rules = json.load(open(os.path.join(ROOT, "data", "configuration", "buff-icons.json"), encoding="utf-8"))
    icons = sorted(rules["customIcons"], key=lambda i: i["slot"])
    assert [i["slot"] for i in icons] == list(range(len(icons))), "custom icon slots must run 0, 1, 2 ... without gaps"

    out = os.path.join(ROOT, "data", "client")
    os.makedirs(os.path.join(out, "gumps"), exist_ok=True)
    sheet = []

    for icon in icons:
        kind, parts = DRAWINGS[icon["name"]]()
        pixels = render(kind, parts)
        with open(os.path.join(out, "gumps", "%d.gump" % icon["art"]), "wb") as f:
            f.write(gump_bytes(pixels))
        sheet.append(pixels)
        print("wrote gumps/%d.gump (%s, %s)" % (icon["art"], icon["name"], kind))

    with open(os.path.join(out, "buff-extra.txt"), "w", newline="\n") as f:
        f.write("# Extra buff icon art, one gump id per line: line k is server-side icon 0x4A6 + k. Written by tools/buff-icon-art/make_buff_icons.py.\n")
        for icon in icons:
            f.write("%d\n" % icon["art"])
    print("wrote buff-extra.txt")

    if len(sys.argv) > 1:
        gap = 2
        combined = [sum((sheet[i][y] + [(40, 40, 40)] * gap for i in range(len(sheet))), []) for y in range(SIZE)]
        with open(sys.argv[1], "wb") as f:
            f.write(png_bytes(combined, 10))
        print("wrote preview", sys.argv[1])


if __name__ == "__main__":
    main()
