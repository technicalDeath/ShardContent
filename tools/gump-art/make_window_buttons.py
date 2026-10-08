"""Builds the shard's own window buttons as the client's gump files, from the stock art (owner rulings 2026-10-07):

  One family of ovals, told apart by colour (Gump-Style-Guide.md section 3.2). The stock green OKAY (2450) and red CANCEL (2453) stay
  as they are, for accepting and declining a question. This script makes the two blank ovals that carry our own words:
    BLUE   menu actions (Close, Back, Next, window links)
    PURPLE game actions ("Turn Criminal Intent on", "Discard", "Travel")
    CHOSEN the chosen one of a pick-one group: the same purple as a game action (a picture, not a button)  } the radio ovals,
    STONE  the others in the group (a dull button)                                                        } 22 px wide, round
  All are cut from the stock red CANCEL oval (art 2453 normal, 2454 pressed): its own gold rim and glossy ends, the word removed,
  the red recoloured.

  set GUMP_DUMP_DIR=<folder of decoded stock gumps "<id>.gump", from work/qol/GumpDump>
  python make_window_buttons.py [out folder]        (default: ShardContent/data/client/gumps)

The result is committed in data/client/gumps, so a deploy needs neither the stock art nor this script.

Art ids (above the stock archive's last id 61728; the buff icons use 50000-50999); for width k, base + 2k is normal and base + 2k + 1 pressed:
  blue ovals    62010, k = 0..4, widths 56, 88, 128, 176, 232, height 21
  purple ovals  62020, the same widths
  chosen radio  62030, one width (22), only the normal picture is used: the chosen one is not clickable
  stone radio   62040, one width (22), normal and pressed
"""
import os
import random
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
_argv = sys.argv
sys.argv = ["x", "none"]
import importlib.util

_spec = importlib.util.spec_from_file_location("gs", os.path.join(HERE, "gumpscan.py"))
gs = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gs)
sys.argv = _argv

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "..", "data", "client", "gumps")
OVAL_WIDTHS = [56, 88, 128, 176, 232]
# ovals by colour: blue for menu actions; purple for game actions (the owner's idea, 2026-10-07, shown beside the gold banner)
OVAL_BASES = {"blue": 62010, "purple": 62020, "chosen": 62030, "stone": 62040}
# the radio pills are small empty ovals with the label beside them, so they need one small width only
PILL_WIDTHS = [int(w) for w in os.environ.get("PILL_WIDTHS", "22").split(",")]       # several only while choosing the width
FAMILY_WIDTHS = {"blue": OVAL_WIDTHS, "purple": OVAL_WIDTHS, "chosen": PILL_WIDTHS, "stone": PILL_WIDTHS}
u = gs.Uop()


def source(art):
    w, h, data = u.gump(art)
    return w, h, gs.decode(w, h, data)


def clamp(v):
    return max(0, min(255, int(v)))


def lerp(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


# ---------------------------------------------------------------- menu-action ovals

TEXT_X0, TEXT_X1 = 8, 47          # the stock CANCEL word sits between its glossy ends


def is_word(p):
    r, g, b = p
    return (r >= 0xe0 and g >= 0xe0 and b >= 0xe0) or (r <= 0x30 and g <= 0x30 and b <= 0x30)


def recolour_blue(r, g, b):
    lum = 0.30 * r + 0.59 * g + 0.11 * b
    return tuple(clamp(c * 0.8 + lum * 0.2) for c in (g * 0.9 + 6, g + 0.30 * (r - g) + 4, r * 0.80 + 12))


def recolour_purple(r, g, b):
    t = r - g
    lum = 0.30 * r + 0.59 * g + 0.11 * b
    return tuple(clamp(c * 0.85 + lum * 0.15) for c in (g + 0.62 * t + 4, g * 0.85, g + 0.88 * t + 8))


def recolour_stone(r, g, b):
    """A dull slate, for the others in the group."""
    lum = 0.30 * r + 0.59 * g + 0.11 * b
    return tuple(clamp(c) for c in (lum * 0.62 + 8, lum * 0.64 + 9, lum * 0.72 + 14))


RECOLOUR = {"blue": recolour_blue, "purple": recolour_purple, "chosen": recolour_purple, "stone": recolour_stone}


def blank_oval(state, colour="blue"):
    """The stock CANCEL oval with its word taken out and its red turned to another colour; 56 x 21."""
    sw, sh, px = source(2454 if state == "pressed" else 2453)
    img = [[px[y][x][:3] if px[y][x][3] else None for x in range(sw)] for y in range(sh)]

    # the rows the word occupies
    band = [y for y in range(4, sh - 4) if any(img[y][x] and is_word(img[y][x]) and img[y][x][0] >= 0xe0 for x in range(TEXT_X0, TEXT_X1 + 1))]
    top, bottom = min(band) - 1, max(band) + 1
    for y in band:
        t = (y - top) / (bottom - top)
        for x in range(TEXT_X0, TEXT_X1 + 1):
            a, b = img[top][x], img[bottom][x]
            img[y][x] = tuple(clamp(a[i] + (b[i] - a[i]) * t + (hash((x, y)) % 5 - 2)) for i in range(3))

    # a stray bit of the word's shadow next to the right-hand gloss
    for y in range(4, sh - 4):
        for x in range(TEXT_X1 - 3, TEXT_X1 + 4):
            p = img[y][x]
            if p and p[0] <= 0x30 and p[1] <= 0x30 and p[2] <= 0x30 and top <= y <= bottom:
                img[y][x] = tuple(clamp((img[y][x - 4][i] + img[y][x + 4][i]) / 2) for i in range(3))

    # the red to the new colour, only where the pixel is really red (the gold rim and the white and grey stay)
    for y in range(sh):
        for x in range(sw):
            p = img[y][x]
            if not p:
                continue
            r, g, b = p
            if r > 1.4 * max(g, b) and r > 0x50:
                img[y][x] = RECOLOUR[colour](r, g, b)

    # smooth the flat middle so a wider button shows no stripes
    for y in range(3, sh - 3):
        row = [img[y][x] for x in range(sw)]
        for x in range(TEXT_X0, TEXT_X1 + 1):
            win = [row[k] for k in range(x - 3, x + 4) if row[k]]
            img[y][x] = tuple(clamp(sum(c[i] for c in win) / len(win)) for i in range(3))
    return img


def build_oval(width, state, colour="blue"):
    base = blank_oval(state, colour)
    sh, sw = len(base), len(base[0])
    if width == sw:
        return base
    if width < sw:
        # a small oval: the glossy left end and the glossy right end, with none of the middle between them
        half = width // 2
        cols = list(range(0, half)) + list(range(sw - (width - half), sw))
        small = [[base[y][x] for x in cols] for y in range(sh)]
        # the two ends were not made to meet: soften the inside so the join and the gloss spots do not show as blocks
        inner = range(6, width - 6)
        for _ in range(2):
            for y in range(3, sh - 3):
                row = list(small[y])
                for x in inner:
                    win = [row[k] for k in range(x - 2, x + 3) if row[k]]
                    small[y][x] = tuple(clamp(sum(c[i] for c in win) / len(win)) for i in range(3))
            for x in inner:
                col = [small[y][x] for y in range(sh)]
                for y in range(4, sh - 4):
                    win = [col[k] for k in range(y - 1, y + 2) if col[k]]
                    small[y][x] = tuple(clamp(sum(c[i] for c in win) / len(win)) for i in range(3))
        return small
    extra = width - sw
    cut = 24
    pool = list(range(14, 36))                      # columns that are only rim texture and flat blue
    mid = []
    for i in range(extra):
        k = i % (2 * len(pool) - 2)
        mid.append(pool[k] if k < len(pool) else pool[2 * len(pool) - 2 - k])
    cols = list(range(0, cut)) + mid + list(range(cut, sw))
    return [[base[y][x] for x in cols] for y in range(sh)]


# ---------------------------------------------------------------- the gump file and a preview

def gump_bytes(pixels):
    h, w = len(pixels), len(pixels[0])
    rows = []
    for row in pixels:
        runs = []
        for rgb in row:
            c = 0 if rgb is None else (((rgb[0] >> 3) << 10) | ((rgb[1] >> 3) << 5) | (rgb[2] >> 3) | 0x8000)
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


def main():
    os.makedirs(OUT, exist_ok=True)
    sheet = []
    for colour, base in OVAL_BASES.items():
        for k, width in enumerate(FAMILY_WIDTHS[colour]):
            for s, state in enumerate(("normal", "pressed")):
                pixels = build_oval(width, state, colour)
                art = base + 2 * k + s
                open(os.path.join(OUT, "%d.gump" % art), "wb").write(gump_bytes(pixels))
                sheet.append((art, pixels))
    if os.environ.get("PREVIEW_DIR"):                  # a contact sheet, for looking at the result
        SC = 3
        W = max(len(p[0]) for _, p in sheet) * SC + 20
        H = sum(len(p) * SC + 12 for _, p in sheet) + 8
        canvas = [[(60, 60, 60, 255)] * W for _ in range(H)]
        oy = 8
        for art, pixels in sheet:
            for y, row in enumerate(pixels):
                for x, p in enumerate(row):
                    if p is None:
                        continue
                    for dy in range(SC):
                        for dx in range(SC):
                            canvas[oy + y * SC + dy][10 + x * SC + dx] = (p[0], p[1], p[2], 255)
            gs.label(canvas, 12, oy - 6, str(art))
            oy += len(pixels) * SC + 12
        gs.png(os.path.join(os.environ["PREVIEW_DIR"], "preview.png"), W, H, canvas)
    print("wrote", len(sheet), "pictures")


main()
