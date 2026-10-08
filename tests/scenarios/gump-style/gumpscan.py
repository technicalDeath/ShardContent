"""Reads gumpartLegacyMUL.uop: lists every gump art id with its size, renders contact sheets (PNG) of chosen ids.

  python gumpscan.py list [minW maxW minH maxH]     -> id width height
  python gumpscan.py sheet out.png id id id ...      -> contact sheet, each labelled with its id
"""
import struct, sys, os, zlib

UOP = r"C:\Users\brend\Documents\Britannia Renaissance\UOData\gumpartLegacyMUL.uop"


def hashlittle2(s: bytes):
    length = len(s)
    a = b = c = (0xDEADBEEF + length) & 0xFFFFFFFF
    k = 0
    M = 0xFFFFFFFF

    def rot(x, r):
        return ((x << r) | (x >> (32 - r))) & M

    while length > 12:
        a = (a + struct.unpack_from("<I", s, k)[0]) & M
        b = (b + struct.unpack_from("<I", s, k + 4)[0]) & M
        c = (c + struct.unpack_from("<I", s, k + 8)[0]) & M
        a = (a - c) & M; a ^= rot(c, 4); c = (c + b) & M
        b = (b - a) & M; b ^= rot(a, 6); a = (a + c) & M
        c = (c - b) & M; c ^= rot(b, 8); b = (b + a) & M
        a = (a - c) & M; a ^= rot(c, 16); c = (c + b) & M
        b = (b - a) & M; b ^= rot(a, 19); a = (a + c) & M
        c = (c - b) & M; c ^= rot(b, 4); b = (b + a) & M
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
        c ^= b; c = (c - rot(b, 14)) & M
        a ^= c; a = (a - rot(c, 11)) & M
        b ^= a; b = (b - rot(a, 25)) & M
        c ^= b; c = (c - rot(b, 16)) & M
        a ^= c; a = (a - rot(c, 4)) & M
        b ^= a; b = (b - rot(a, 14)) & M
        c ^= b; c = (c - rot(b, 24)) & M
    return (b << 32) | c


GUMPS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gumps")


class Uop:
    """Reads the gumps the C# dump tool decoded (GumpDump) instead of the archive."""

    def __init__(self, path=None):
        pass

    def gump(self, i):
        p = os.path.join(GUMPS, "%d.gump" % i)
        if not os.path.exists(p):
            return None
        data = open(p, "rb").read()
        w, hgt = struct.unpack_from("<II", data, 0)
        return w, hgt, data[8:]


def decode(w, h, data):
    """Returns a list of rows, each a list of (r,g,b,a)."""
    rows = []
    look = struct.unpack_from("<%dI" % h, data, 0)
    for y in range(h):
        pos = look[y] * 4
        x = 0
        row = [(0, 0, 0, 0)] * w
        row = list(row)
        while x < w and pos + 4 <= len(data):
            color, run = struct.unpack_from("<HH", data, pos)
            pos += 4
            if color:
                r = ((color >> 10) & 31) * 255 // 31
                g = ((color >> 5) & 31) * 255 // 31
                b = (color & 31) * 255 // 31
                px = (r, g, b, 255)
            else:
                px = (0, 0, 0, 0)
            for _ in range(run):
                if x < w:
                    row[x] = px
                x += 1
        rows.append(row)
    return rows


def png(path, width, height, pixels):
    raw = b"".join(b"\x00" + b"".join(bytes(p) for p in row) for row in pixels)

    def chunk(t, d):
        c = struct.pack(">I", len(d)) + t + d
        return c + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)

    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        f.write(chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)))
        f.write(chunk(b"IDAT", zlib.compress(raw, 6)))
        f.write(chunk(b"IEND", b""))


# 3x5 digit font for the id labels
FONT = {
    "0": ["111", "101", "101", "101", "111"], "1": ["010", "110", "010", "010", "111"], "2": ["111", "001", "111", "100", "111"],
    "3": ["111", "001", "111", "001", "111"], "4": ["101", "101", "111", "001", "001"], "5": ["111", "100", "111", "001", "111"],
    "6": ["111", "100", "111", "101", "111"], "7": ["111", "001", "001", "001", "001"], "8": ["111", "101", "111", "101", "111"],
    "9": ["111", "101", "111", "001", "111"],
}


def label(canvas, x, y, text, color=(255, 255, 0, 255)):
    for ch in text:
        g = FONT[ch]
        for gy in range(5):
            for gx in range(3):
                if g[gy][gx] == "1":
                    for dy in range(2):
                        for dx in range(2):
                            px, py = x + gx * 2 + dx, y + gy * 2 + dy
                            if 0 <= py < len(canvas) and 0 <= px < len(canvas[0]):
                                canvas[py][px] = color
        x += 8


def main():
    u = Uop(UOP)
    cmd = sys.argv[1]
    if cmd == "list":
        lim = [int(v) for v in sys.argv[2:6]] if len(sys.argv) >= 6 else [0, 99999, 0, 99999]
        for i in range(0, 0x10000):
            g = u.gump(i)
            if g and lim[0] <= g[0] <= lim[1] and lim[2] <= g[1] <= lim[3]:
                print(i, g[0], g[1])
    elif cmd == "sheet":
        out = sys.argv[2]
        ids = [int(v) for v in sys.argv[3:]]
        cols = int(os.environ.get("COLS", "4"))
        bg = tuple(int(v) for v in os.environ.get("BG", "60,60,60").split(",")) + (255,)
        cells = []
        for i in ids:
            g = u.gump(i)
            cells.append((i, g))
        SC = int(os.environ.get("SCALE", "1"))
        cw = max([g[0] for _, g in cells if g] + [40]) * SC + 12
        ch = max([g[1] for _, g in cells if g] + [20]) * SC + 22
        cw = min(cw, int(os.environ.get("CELLW", "9999")))
        ch = min(ch, int(os.environ.get("CELLH", "9999")))
        rowsn = (len(cells) + cols - 1) // cols
        W, H = cols * cw, rowsn * ch
        canvas = [[bg for _ in range(W)] for _ in range(H)]
        for n, (i, g) in enumerate(cells):
            cx, cy = (n % cols) * cw, (n // cols) * ch
            label(canvas, cx + 2, cy + 2, str(i))
            if g:
                w, h, data = g
                for y, row in enumerate(decode(w, h, data)):
                    for x, px in enumerate(row):
                        if px[3]:
                            for dy in range(SC):
                                for dx in range(SC):
                                    yy, xx = cy + 16 + y * SC + dy, cx + 4 + x * SC + dx
                                    if yy < H and xx < W:
                                        canvas[yy][xx] = px
        png(out, W, H, canvas)
        print("wrote", out, W, H)


main()
