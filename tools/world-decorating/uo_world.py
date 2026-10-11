"""Reads the Felucca map (land + statics) and the shard's own generated world data, to find and measure places to decorate.

  python uo_world.py buildings X0 Y0 X1 Y1 [--min-roof 100]   roofed buildings in the rectangle: bbox, roof area, floor tiles, signs, spawners, placed items
  python uo_world.py plan X0 Y0 X1 Y1 OUT.png [--scale 16] [--mark x0,y0,x1,y1] ...   top-down plan (walls black, floors tan, carpet red, furniture blue,
                                                                                       roofs pink, doors yellow, white = signs, red = spawners)
  python uo_world.py open X0 Y0 X1 Y1 [--min-w 12] [--min-h 12] [--town x0,y0,x1,y1 ...]  biggest clear flat rectangles (no walls, roofs, fixtures, trees)
  python uo_world.py signs X0 Y0 X1 Y1                         shop signs with their names

What it can and cannot tell you:
  * Walls, floors, roofs, windows, doors and most fixed furniture are MAP STATICS (client files). The server cannot remove or move them.
  * Crates, barrels, chairs, bookcases, beds and the like in the shard's towns are SERVER ITEMS placed from Decoration/*.cfg. They can be cleared
    with a world-generation rule. `buildings` lists those separately so you know what a site really holds.
  * 'floor-static tiles' counts only floors that are statics (carpet, paving, some planks). Many interiors use LAND-layer plank floors, which this
    count misses (the east guild hall shows 144 here and has 211 walkable cells). The roof area and bbox are the reliable size cues; for the exact
    walkable floor dump the server's own view with [TestOnlyWalkGrid on the probe (see the skill).
"""
import collections
import json
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(WORKSPACE, "ShardContent", "tools", "cosmetic-catalog"))
import uoart  # noqa: E402
import flatspots  # noqa: E402

ROOT = uoart.ROOT
DATA = os.path.join(WORKSPACE, "ModernUO", "Distribution", "Data", "BritanniaRenaissance", "Alpha2b")
H_BLOCKS = 512

tiles = uoart.tiles()
FL = {v: k for k, v in uoart.FLAGS.items()}
WALL, WINDOW, DOOR, ROOF, SURF, IMP, FOLI = (FL[n] for n in ("Wall", "Window", "Door", "Roof", "Surface", "Impassable", "Foliage"))
WATER = set(range(0xA8, 0xAC))
ROAD = [(0x71, 0x78), (0xE8, 0xEB), (0x7AE, 0x7B1), (0x3FF4, 0x3FF4), (0x3FF8, 0x3FFB), (0x442, 0x479), (0x501, 0x510)]   # stock house-placement road ids
GRASS = set(range(0x03, 0x07)) | set(range(0x0D, 0x1A)) | set(range(0x150, 0x15D)) | set(range(0x9, 0x16))
FLOOR_NAMES = ("wooden boards", "wooden plank", "carpet", "marble", "stone pavers", "flagstone")


class Region:
    """Land and statics of a rectangle of map 0, loaded once."""

    def __init__(self, x0, y0, x1, y1):
        self.x0, self.y0, self.x1, self.y1 = x0, y0, x1, y1
        self.w, self.h = x1 - x0, y1 - y0
        mm, chunks = flatspots.load_blocks()
        per_chunk = 0xC4000 // 196
        idx = open(os.path.join(ROOT, "staidx0.mul"), "rb").read()
        sf = open(os.path.join(ROOT, "statics0.mul"), "rb")
        self.land_id = [[0] * self.h for _ in range(self.w)]
        self.land_z = [[0] * self.h for _ in range(self.w)]
        self.stat = {}
        for bx in range(x0 // 8, (x1 + 7) // 8):
            for by in range(y0 // 8, (y1 + 7) // 8):
                block = bx * H_BLOCKS + by
                ci, b = divmod(block, per_chunk)
                off, _size = chunks[ci]
                base = off + b * 196 + 4
                for c in range(64):
                    tid, z = struct.unpack_from("<Hb", mm, base + c * 3)
                    x, y = bx * 8 + c // 8, by * 8 + c % 8
                    if x0 <= x < x1 and y0 <= y < y1:
                        self.land_id[x - x0][y - y0] = tid
                        self.land_z[x - x0][y - y0] = z
                lookup, length, _ = struct.unpack_from("<III", idx, block * 12)
                if lookup == 0xFFFFFFFF or length in (0, 0xFFFFFFFF):
                    continue
                sf.seek(lookup)
                buf = sf.read(length)
                for k in range(0, len(buf) - 6, 7):
                    tid, sx, sy, z, _hue = struct.unpack_from("<HBBbH", buf, k)
                    x, y = bx * 8 + sx, by * 8 + sy
                    if x0 <= x < x1 and y0 <= y < y1:
                        self.stat.setdefault((x, y), []).append((tid, z))

    def inside(self, x, y):
        return self.x0 <= x < self.x1 and self.y0 <= y < self.y1

    def lz(self, x, y):
        return self.land_z[x - self.x0][y - self.y0]

    def lid(self, x, y):
        return self.land_id[x - self.x0][y - self.y0]

    def flags_at(self, x, y):
        return [(tiles[t], z) for t, z in self.stat.get((x, y), []) if t < len(tiles)]


def is_floor(t):
    n = t.name.lower()
    return bool(t.flags & SURF) and not (t.flags & (IMP | ROOF)) and t.height <= 2 and n.startswith(FLOOR_NAMES)


def is_road(lid):
    return any(a <= lid <= b for a, b in ROAD)


# ---- the shard's generated world data -------------------------------------------------------------------------------------------------
def load_signs(rect):
    import cliloc
    cl = cliloc.load()
    out = []
    path = os.path.join(DATA, "signs.cfg")
    for line in open(path, encoding="utf-8"):
        m = re.match(r"\s*(\d+)\s+(\d+)\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+#(\d+)", line)
        if not m:
            continue
        _map, _gid, x, y, z, name = map(int, m.groups())
        if rect[0] <= x <= rect[2] and rect[1] <= y <= rect[3]:
            out.append((x, y, z, cl.get(name, "#%d" % name)))
    return out


def load_spawners(rect):
    out = []
    folder = os.path.join(DATA, "Spawns")

    def walk(o):
        if isinstance(o, dict):
            if o.get("location") and "entries" in o and o.get("map") == "Felucca":
                x, y, z = o["location"]
                if rect[0] <= x <= rect[2] and rect[1] <= y <= rect[3]:
                    out.append((x, y, z, [e["name"] for e in o["entries"]]))
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    for f in sorted(os.listdir(folder)):
        if f.endswith(".json"):
            try:
                walk(json.load(open(os.path.join(folder, f), encoding="utf-8-sig")))
            except Exception:
                pass
    return out


def load_decoration(rect):
    """Server items placed from Decoration/*.cfg: [(class, name, x, y, z)]."""
    out = []
    folder = os.path.join(DATA, "Decoration")
    for f in sorted(os.listdir(folder)):
        if not f.endswith(".cfg"):
            continue
        name = cls = None
        for line in open(os.path.join(folder, f), encoding="utf-8", errors="replace"):
            line = line.strip()
            if not line:
                continue
            if line.startswith("#"):
                name = line[1:].strip()
                continue
            m = re.fullmatch(r"(-?\d+)\s+(-?\d+)\s+(-?\d+)(?:\s+(-?\w+))?", line)
            if m and cls:
                x, y, z = int(m.group(1)), int(m.group(2)), int(m.group(3))
                if rect[0] <= x <= rect[2] and rect[1] <= y <= rect[3]:
                    out.append((cls, name, x, y, z))
            else:
                cls = line
    return out


# ---- commands -------------------------------------------------------------------------------------------------------------------------
def cmd_buildings(a):
    rect = tuple(int(v) for v in a[:4])
    min_roof = int(a[a.index("--min-roof") + 1]) if "--min-roof" in a else 100
    r = Region(rect[0], rect[1], rect[2] + 1, rect[3] + 1)
    roofed = {p for p, lst in r.stat.items() if any(t.flags & ROOF for t, _ in r.flags_at(*p))}
    seen, comps = set(), []
    for t in sorted(roofed):
        if t in seen:
            continue
        stack, cells = [t], []
        seen.add(t)
        while stack:
            c = stack.pop()
            cells.append(c)
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    n = (c[0] + dx, c[1] + dy)
                    if n in roofed and n not in seen:
                        seen.add(n)
                        stack.append(n)
        if len(cells) >= min_roof:
            comps.append(cells)
    comps.sort(key=len, reverse=True)
    signs, spawners, deco = load_signs(rect), load_spawners(rect), load_decoration(rect)
    print("%d roofed buildings of at least %d roof tiles in %s" % (len(comps), min_roof, rect))
    for i, cells in enumerate(comps):
        xs, ys = [c[0] for c in cells], [c[1] for c in cells]
        bb = (min(xs), min(ys), max(xs), max(ys))
        floor = sum(1 for x in range(bb[0], bb[2] + 1) for y in range(bb[1], bb[3] + 1) if any(is_floor(t) for t, _ in r.flags_at(x, y)))
        fixed = sum(1 for x in range(bb[0], bb[2] + 1) for y in range(bb[1], bb[3] + 1)
                    if any((t.flags & IMP) and not (t.flags & (ROOF | WALL | WINDOW | DOOR)) and t.height <= 22 for t, _ in r.flags_at(x, y)))
        near = sorted({s[3] for s in signs if bb[0] - 3 <= s[0] <= bb[2] + 3 and bb[1] - 3 <= s[1] <= bb[3] + 3})
        npcs = collections.Counter(n for s in spawners if bb[0] <= s[0] <= bb[2] and bb[1] <= s[1] <= bb[3] for n in s[3])
        items = collections.Counter(d[1] for d in deco if bb[0] <= d[2] <= bb[2] and bb[1] <= d[3] <= bb[3])
        print("%2d  bbox %s  %dx%d  roof %d  floor-static tiles %d  fixed furniture tiles %d" % (i, bb, bb[2] - bb[0] + 1, bb[3] - bb[1] + 1, len(cells), floor, fixed))
        print("      signs: %s" % (", ".join(near) or "-"))
        print("      npcs: %s" % (dict(npcs) or "-"))
        print("      server items (clearable): %d  %s" % (sum(items.values()), dict(items.most_common(6)) or ""))


def cmd_signs(a):
    rect = tuple(int(v) for v in a[:4])
    for s in sorted(load_signs(rect), key=lambda s: (s[1], s[0])):
        print(s)


def cmd_plan(a):
    rect = tuple(int(v) for v in a[:4])
    out = a[4]
    S = int(a[a.index("--scale") + 1]) if "--scale" in a else 16
    marks = [tuple(int(v) for v in a[i + 1].split(",")) for i, x in enumerate(a) if x == "--mark"]
    r = Region(rect[0], rect[1], rect[2] + 1, rect[3] + 1)
    w, h = r.w * S, r.h * S
    px = [[(0, 0, 0, 255)] * w for _ in range(h)]

    def put(x, y, col, inset=0):
        for dy in range(inset, S - inset):
            for dx in range(inset, S - inset):
                px[(y - r.y0) * S + dy][(x - r.x0) * S + dx] = col

    for x in range(r.x0, r.x1):
        for y in range(r.y0, r.y1):
            lid = r.lid(x, y)
            put(x, y, (84, 84, 92, 255) if is_road(lid) else (40, 80, 160, 255) if lid in WATER else (52, 104, 48, 255) if lid in GRASS else (140, 112, 78, 255))
            best = None
            for t, z in r.flags_at(x, y):
                fl = t.flags
                if fl & WALL:
                    cand = (6, (24, 24, 28, 255), 0)
                elif fl & DOOR:
                    cand = (6, (240, 200, 60, 255), 0)
                elif fl & WINDOW:
                    cand = (6, (110, 160, 200, 255), 0)
                elif fl & FOLI:
                    cand = (4, (20, 80, 20, 255), 2)
                elif (fl & IMP) and not (fl & ROOF) and t.height <= 22:
                    cand = (5, (90, 100, 190, 255), 2)
                elif is_floor(t):
                    cand = (3, (150, 70, 70, 255) if t.name.lower().startswith("carpet") else (206, 172, 120, 255), 0)
                elif fl & ROOF:
                    cand = (1, (190, 110, 90, 255), 2)
                else:
                    continue
                if best is None or cand[0] > best[0]:
                    best = cand
            if best:
                put(x, y, best[1], best[2])
    for sx, sy, _z, _n in load_signs(rect):
        put(sx, sy, (255, 255, 255, 255), 5)
    for sx, sy, _z, _n in load_spawners(rect):
        put(sx, sy, (240, 40, 40, 255), 5)
    for (a0, b0, a1, b1) in marks:
        for t in range(2):
            for x in range(a0 - t, a1 + t + 1):
                for yy in (b0 - t, b1 + t):
                    if r.inside(x, yy):
                        put(x, yy, (80, 255, 120, 255), 0)
            for y in range(b0 - t, b1 + t + 1):
                for xx in (a0 - t, a1 + t):
                    if r.inside(xx, y):
                        put(xx, y, (80, 255, 120, 255), 0)
    for x in range(r.x0, r.x1):
        if x % 4 == 0:
            uoart.label(px, (x - r.x0) * S + 2, 2, str(x)[-2:], (255, 255, 0, 255), 2)
    for y in range(r.y0, r.y1):
        if y % 4 == 0:
            uoart.label(px, 2, (y - r.y0) * S + 2, str(y)[-2:], (255, 255, 0, 255), 2)
    uoart.write_png(out, w, h, px)
    print("wrote", out, w, h)


def cmd_open(a):
    rect = tuple(int(v) for v in a[:4])
    min_w = int(a[a.index("--min-w") + 1]) if "--min-w" in a else 12
    min_h = int(a[a.index("--min-h") + 1]) if "--min-h" in a else 12
    towns = [tuple(int(v) for v in a[i + 1].split(",")) for i, x in enumerate(a) if x == "--town"]
    r = Region(rect[0], rect[1], rect[2] + 1, rect[3] + 1)

    def ok(x, y):
        if towns and not any(t[0] <= x <= t[2] and t[1] <= y <= t[3] for t in towns):
            return False
        if r.lid(x, y) in WATER:
            return False
        z = r.lz(x, y)
        for dx, dy in ((1, 0), (0, 1), (-1, 0), (0, -1)):
            nx, ny = x + dx, y + dy
            if r.inside(nx, ny) and abs(r.lz(nx, ny) - z) > 3:
                return False
        for t, _ in r.flags_at(x, y):
            if t.flags & (WALL | WINDOW | DOOR | ROOF | IMP | FOLI) or ((t.flags & SURF) and t.height > 3):
                return False
        return True

    grid = [[1 if ok(x, y) else 0 for y in range(r.y0, r.y1)] for x in range(r.x0, r.x1)]
    best, heights = [], [0] * r.w
    for yy in range(r.h):
        for xx in range(r.w):
            heights[xx] = heights[xx] + 1 if grid[xx][yy] else 0
        stack = []
        for xx in range(r.w + 1):
            hh = heights[xx] if xx < r.w else 0
            start = xx
            while stack and stack[-1][1] >= hh:
                sx, sh = stack.pop()
                width = xx - sx
                if width >= min_w and sh >= min_h:
                    best.append((width * sh, r.x0 + sx, r.y0 + yy - sh + 1, r.x0 + xx - 1, r.y0 + yy))
                start = sx
            stack.append((start, hh))
    best.sort(reverse=True)
    seen = []
    for area, x0, y0, x1, y1 in best:
        if any(not (x1 < s[1] - 1 or x0 > s[3] + 1 or y1 < s[2] - 1 or y0 > s[4] + 1) for s in seen):
            continue
        seen.append((area, x0, y0, x1, y1))
        print("area %4d  (%d,%d)-(%d,%d)  %dx%d  z=%d" % (area, x0, y0, x1, y1, x1 - x0 + 1, y1 - y0 + 1, r.lz((x0 + x1) // 2, (y0 + y1) // 2)))
        if len(seen) >= 12:
            break
    if not seen:
        print("no clear rectangle of at least %dx%d" % (min_w, min_h))


COMMANDS = {"buildings": cmd_buildings, "plan": cmd_plan, "open": cmd_open, "signs": cmd_signs}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(__doc__)
        sys.exit(2)
    COMMANDS[sys.argv[1]](sys.argv[2:])
