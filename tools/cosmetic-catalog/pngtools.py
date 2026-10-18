"""Minimal PNG reader / cropper / label overlay (pure Python, no Pillow) for the in-game gallery screenshots.

Reads 8-bit RGB / RGBA non-interlaced PNGs (what the client screenshot tool writes), crops, draws numbered labels, and writes RGBA.
"""
import struct
import sys
import zlib

sys.path.insert(0, __file__.rsplit("\\", 1)[0] if "\\" in __file__ else __file__.rsplit("/", 1)[0])
import uoart  # noqa: E402


def read_png(path):
    data = open(path, "rb").read()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "not a PNG"
    pos = 8
    idat = b""
    width = height = depth = ctype = interlace = None
    while pos < len(data):
        n, typ = struct.unpack_from(">I4s", data, pos)
        chunk = data[pos + 8:pos + 8 + n]
        pos += 12 + n
        if typ == b"IHDR":
            width, height, depth, ctype, _, _, interlace = struct.unpack(">IIBBBBB", chunk)
        elif typ == b"IDAT":
            idat += chunk
        elif typ == b"IEND":
            break
    assert depth == 8 and ctype in (2, 6) and interlace == 0, "unsupported PNG layout (depth %s type %s interlace %s)" % (depth, ctype, interlace)
    bpp = 3 if ctype == 2 else 4
    raw = zlib.decompress(idat)
    stride = width * bpp
    rows = []
    prev = bytearray(stride)
    p = 0
    for _ in range(height):
        f = raw[p]
        line = bytearray(raw[p + 1:p + 1 + stride])
        p += 1 + stride
        if f == 1:
            for i in range(bpp, stride):
                line[i] = (line[i] + line[i - bpp]) & 255
        elif f == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 255
        elif f == 3:
            for i in range(stride):
                left = line[i - bpp] if i >= bpp else 0
                line[i] = (line[i] + ((left + prev[i]) >> 1)) & 255
        elif f == 4:
            for i in range(stride):
                a = line[i - bpp] if i >= bpp else 0
                b = prev[i]
                c = prev[i - bpp] if i >= bpp else 0
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + pr) & 255
        rows.append(line)
        prev = line
    px = []
    for line in rows:
        if bpp == 4:
            px.append([tuple(line[i:i + 4]) for i in range(0, stride, 4)])
        else:
            px.append([tuple(line[i:i + 3]) + (255,) for i in range(0, stride, 3)])
    return width, height, px


def crop(px, x0, y0, x1, y1):
    return [row[x0:x1] for row in px[y0:y1]]


def draw_tag(px, x, y, text, fg=(255, 235, 120, 255), bg=(0, 0, 0, 200), scale=2):
    """Draws text on a dark chip with its top-left at x,y."""
    w = len(text) * 4 * scale + 3
    h = 5 * scale + 4
    for yy in range(max(0, y), min(len(px), y + h)):
        for xx in range(max(0, x), min(len(px[0]), x + w)):
            r, g, b, a = px[yy][xx]
            k = bg[3] / 255.0
            px[yy][xx] = (int(r * (1 - k) + bg[0] * k), int(g * (1 - k) + bg[1] * k), int(b * (1 - k) + bg[2] * k), 255)
    uoart.label(px, x + 2, y + 2, text, color=fg, scale=scale)


def write_png(path, px):
    uoart.write_png(path, len(px[0]), len(px), px)


if __name__ == "__main__":
    w, h, px = read_png(sys.argv[1])
    print(w, h)
