"""In-game gallery pages for the cosmetic reward catalog.

  (add --neutral to plan the era-neutral section: pages CN-<CAT>-<NN>)
  python galleries.py plan [CAT ...]            -> writes work/cosmetics/layouts/<CAT>-<NN>.json (+ .meta.json) and lists the pages
  python galleries.py finish <shot.png> <layout-name> <out.png>
                                                -> crops a real-client screenshot to the game view and numbers every item
  python galleries.py index                     -> writes docs/cosmetic-rewards/client-shots/README.md (page -> item legend)

Layouts are consumed by the test-only command  [TestOnlyDecor <player-serial> <layout-name>  (tests/scenarios/cosmetic-catalog/DecorProbe.cs)
on a disposable host. The camera character stands on a flat patch of Felucca (see flatspots.py); each page shows a shelf-packed
arrangement of the catalog items at native client scale, with the player at the middle of the view kept clear.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import catalog  # noqa: E402
import pngtools  # noqa: E402
import uoart  # noqa: E402

WORKSPACE = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
LAYOUTS = os.path.join(WORKSPACE, "work", "cosmetics", "layouts")

# Real-client screenshot geometry (Start-PlayerClient scratch profile, 1296x839 window): the game view inside the window.
CROP = (15, 58, 918, 603)                 # x0, y0, x1, y1 in the full screenshot
VIEW_W, VIEW_H = CROP[2] - CROP[0], CROP[3] - CROP[1]
ORIGIN_X, ORIGIN_Y = 451, 269             # cropped coords of the bottom vertex of the player's own tile
LEFT, RIGHT = 24, VIEW_W - 24
TOP, BOTTOM = 100, VIEW_H - 40            # keep clear of the top-left gump icons and the bottom text line
KEEP = (ORIGIN_X - 34, ORIGIN_X + 34, ORIGIN_Y - 78, ORIGIN_Y + 20)   # the player's own figure
GAP_X, GAP_Y = 22, 30
PAD = 0x109D        # plain grey carpet tile, laid under tiny single-graphic items in the gallery
TINY = 32           # px: items no larger than this in both directions get a pad


def entry_geometry(e):
    r = uoart.compose_anchored(uoart.parts_sorted(catalog.entry_parts(e)))
    w, h, _, minx, miny = r
    return w, h, minx, miny


def slot_width(e, w, h):
    """Horizontal room an item takes in a row: tiny single-graphic items sit on a 44px pad, so give them that much."""
    return max(w, 46) if (len(e["parts"]) == 1 and w <= TINY and h <= TINY) else w


def plan_pages(entries):
    pages, page = [], []
    y_cursor = TOP
    i = 0
    items = [(e,) + entry_geometry(e) for e in entries]
    while i < len(items):
        row = []
        x = LEFT
        row_h = 0
        while i < len(items):
            e, w, h, minx, miny = items[i]
            if w > RIGHT - LEFT:
                w = RIGHT - LEFT
            slot = slot_width(e, w, h)
            cur_h = max(row_h, h)
            span_top = y_cursor
            span_bot = y_cursor + cur_h
            if span_bot > KEEP[2] and span_top < KEEP[3] and x < KEEP[1] and x + slot > KEEP[0]:
                x = KEEP[1] + GAP_X
            if x + slot > RIGHT:
                break
            row.append((e, x, slot, w, h, minx, miny))
            row_h = cur_h
            x += slot + GAP_X
            i += 1
        if not row:           # an item wider than the view: put it alone
            e, w, h, minx, miny = items[i]
            row = [(e, LEFT, min(w, RIGHT - LEFT), min(w, RIGHT - LEFT), h, minx, miny)]
            row_h = h
            i += 1
        if y_cursor + row_h > BOTTOM and page:
            pages.append(page)
            page = []
            y_cursor = TOP
            # re-place this row at the top of a fresh page (rows are cheap to rebuild: step back)
            i -= len(row)
            continue
        base = y_cursor + row_h
        for e, x0, slot, w, h, minx, miny in row:
            page.append({"entry": e, "px": x0 + (slot - w) // 2, "py": base - h, "w": w, "h": h, "minx": minx, "miny": miny})
        y_cursor = base + GAP_Y
    if page:
        pages.append(page)
    return pages


def to_tiles(p):
    """Quantise a wanted image top-left (px,py) to a tile of the player's grid. -> (tx, ty, actual top-left x, y)."""
    vx = p["px"] - p["minx"]
    vy = p["py"] + 44 - p["miny"]
    a = round((vx - ORIGIN_X) / 22)
    b = round((vy - ORIGIN_Y) / 22)
    if (a - b) % 2:
        b += 1
    tx, ty = (a + b) // 2, (b - a) // 2
    ax = ORIGIN_X + 22 * a + p["minx"]
    ay = ORIGIN_Y + 22 * b - 44 + p["miny"]
    return tx, ty, ax, ay


def write_layouts(cat, entries, label_fn=None, prefix=None):
    os.makedirs(LAYOUTS, exist_ok=True)
    pages = plan_pages(entries)
    names = []
    for n, page in enumerate(pages, 1):
        name = "%s%s-%02d" % (catalog.PAGE_PREFIX if prefix is None else prefix, cat, n)
        items, meta = [], []
        for k, p in enumerate(page, 1):
            e = p["entry"]
            tx, ty, ax, ay = to_tiles(p)
            if len(e["parts"]) == 1 and p["w"] <= TINY and p["h"] <= TINY:
                items.append({"id": PAD, "x": tx, "y": ty, "z": 0, "hue": 0})   # grey carpet tile so a tiny item reads on the grass
            for part in catalog.entry_parts(e):
                pid, dx, dy, dz, hue = part
                items.append({"id": pid, "x": tx + dx, "y": ty + dy, "z": dz, "hue": hue})
            meta.append({"id": e["id"], "label": label_fn(e) if label_fn else e["id"].rsplit("-", 1)[1], "cx": ax + p["w"] // 2, "bottom": ay + p["h"], "w": p["w"], "h": p["h"],
                         "name": e["name"]})
        with open(os.path.join(LAYOUTS, name + ".json"), "w") as f:
            json.dump({"items": items}, f)
        with open(os.path.join(LAYOUTS, name + ".meta.json"), "w") as f:
            json.dump({"page": name, "category": cat, "set": catalog.MODE, "items": meta}, f, indent=1)
        names.append(name)
    return names


def finish(shot, layout, out):
    meta = json.load(open(os.path.join(LAYOUTS, layout + ".meta.json")))
    w, h, px = pngtools.read_png(shot)
    px = pngtools.crop(px, *CROP)
    for m in meta["items"]:
        label = m["label"]
        lw = len(label) * 8 + 3
        pngtools.draw_tag(px, m["cx"] - lw // 2, min(m["bottom"] + 3, VIEW_H - 16), label)
    pngtools.write_png(out, px)


def write_index():
    import sinkplan
    shots = os.path.join(catalog.DOCS, "client-shots")
    pages = sorted(f[:-10] for f in os.listdir(LAYOUTS) if f.endswith(".meta.json"))
    era = [n for n in pages if not n.startswith(("CN-", "GS-"))]
    neutral = [n for n in pages if n.startswith("CN-")]
    showroom = [n for n in pages if n.startswith("GS-")]
    lines = ["# In-game gallery shots", "",
             "Real ClassicUO client screenshots (client 7.0.117.0, the shard's own distribution) of every catalog item standing on the ground in Felucca, "
             "at native client scale, taken on a disposable test server. Each item is labelled with the number part of its id: the label `014` on a "
             "`FIG-01` page is `CR-FIG-014`, and on a `CN-NEC-01` page it is `CN-NEC-014`. What the pictures show is exactly what a player would see: "
             "Felucca runs the Desolation season, so leaf tiles are hidden (see the Felucca note in the catalog). Wall pieces are shown standing on the "
             "ground, not on a wall, and tiny items sit on a grey carpet pad so they can be seen.", "",
             "Part 1 is the main (era) catalog, part 2 the era-neutral section (`CN-` pages), part 3 the gold-sink showroom (`GS-` pages: the 100 "
             "decorations of Design Proposal 3, labelled with their showroom number, not the id number).", "",
             "Regenerate: `galleries.py plan` (add `--neutral` for part 2), then `Run-GalleryShots.ps1` (disposable host with `DecorProbe`, camera character in the real client), then `galleries.py index`.", ""]
    for title, group in (("Part 1 - main catalog", era), ("Part 2 - era-neutral section", neutral), ("Part 3 - gold-sink showroom", showroom)):
        if not any(os.path.exists(os.path.join(shots, n + ".png")) for n in group):
            continue
        lines += ["# " + title, ""]
        cur = None
        for name in group:
            if not os.path.exists(os.path.join(shots, name + ".png")):
                continue
            meta = json.load(open(os.path.join(LAYOUTS, name + ".meta.json")))
            if name.startswith("GS-"):
                cats = {w: sinkplan.WINGS[w][0] for w in sinkplan.WINGS}
            else:
                cats = catalog.CATEGORIES_NEUTRAL if name.startswith("CN-") else catalog.CATEGORIES_ERA
            if meta["category"] != cur:
                cur = meta["category"]
                lines += ["## %s - %s" % (cur, cats[cur]), ""]
            lines += ["### %s" % name, "", "![%s](%s.png)" % (name, name), "",
                      "| Label | Id | Name |", "| --- | --- | --- |"]
            for m in meta["items"]:
                lines.append("| %s | `%s` | %s |" % (m["label"], m["id"], m["name"]))
            lines.append("")
    with open(os.path.join(shots, "README.md"), "w", encoding="utf-8") as f:
        f.write(chr(10).join(lines))
    return len(pages)


def main(argv):
    if "--neutral" in argv:
        argv = [a for a in argv if a != "--neutral"]
        catalog.set_mode("neutral")
    if len(argv) < 2:
        print(__doc__)
        return 0
    if argv[1] == "index":
        print("indexed", write_index(), "pages")
        return 0
    if argv[1] == "plan":
        cats = argv[2:] or list(catalog.CATEGORIES)
        total = 0
        for cat in cats:
            entries = [e for e in catalog.load_category(cat) if not e.get("retired")]
            if not entries:
                continue
            names = write_layouts(cat, entries)
            total += len(names)
            print("%s: %d entries -> %d pages (%s .. %s)" % (cat, len(entries), len(names), names[0], names[-1]))
        print("pages:", total)
        return 0
    if argv[1] == "finish":
        finish(argv[2], argv[3], argv[4])
        print("wrote", argv[4])
        return 0
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
