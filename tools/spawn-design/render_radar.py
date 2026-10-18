"""Renders a rectangle of Felucca (map 0) as a radar map: one pixel per tile, coloured from the client's radarcol.mul
(the topmost static on a tile, else the land tile), the way the client's own world map draws it.

  python render_radar.py X0 Y0 X1 Y1 OUT.png [--scale 2]
"""
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "world-decorating"))
import uo_world  # noqa: E402
import uoart  # noqa: E402  (on the path through uo_world)


def radar_colours():
    raw = open(os.path.join(uoart.ROOT, "radarcol.mul"), "rb").read()
    vals = struct.unpack("<%dH" % (len(raw) // 2), raw)

    def rgb(c):
        return (((c >> 10) & 31) * 255 // 31, ((c >> 5) & 31) * 255 // 31, (c & 31) * 255 // 31, 255)

    return [rgb(c) for c in vals]


def main(argv):
    x0, y0, x1, y1 = (int(v) for v in argv[:4])
    out = argv[4]
    scale = int(argv[argv.index("--scale") + 1]) if "--scale" in argv else 1
    col = radar_colours()
    r = uo_world.Region(x0, y0, x1, y1)
    rows = []
    for y in range(y0, y1):
        row = []
        for x in range(x0, x1):
            st = r.stat.get((x, y))
            if st:
                tid = max(st, key=lambda s: s[1])[0]
                c = col[0x4000 + tid] if 0x4000 + tid < len(col) else col[r.lid(x, y)]
            else:
                c = col[r.lid(x, y) & 0x3FFF]
            row.extend([c] * scale)
        for _ in range(scale):
            rows.append(row)
    uoart.write_png(out, (x1 - x0) * scale, (y1 - y0) * scale, rows)
    print("wrote", out, (x1 - x0) * scale, (y1 - y0) * scale)


if __name__ == "__main__":
    main(sys.argv[1:])
