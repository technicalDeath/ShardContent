"""Counts how often each item id is placed as a static in a UO facet's map data.

A rough 'where does this graphic belong' signal for era and theme checks: ids used thousands of times by the original Britannia map
are classic world dressing; ids used only in Tokuno (map 4), Ter Mur (map 5), Malas (map 3) or Ilshenar (map 2) carry that facet's theme.

  python staticsusage.py out.json [map]       map 0 (default) Felucca/Trammel, 1 Trammel, 2 Ilshenar, 3 Malas, 4 Tokuno, 5 Ter Mur
  python staticsusage.py annotate out.txt      -> every item tile with art: id | name | height | size | flags | counts per facet
"""
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("UO_ROOT") or os.path.normpath(os.path.join(HERE, "..", "..", "..", "UOData"))
FACETS = {0: "Felucca", 1: "Trammel", 2: "Ilshenar", 3: "Malas", 4: "Tokuno", 5: "Ter Mur"}


def count_map(m):
    idx = open(os.path.join(ROOT, "staidx%d.mul" % m), "rb").read()
    counts = {}
    with open(os.path.join(ROOT, "statics%d.mul" % m), "rb") as f:
        n = len(idx) // 12
        for i in range(n):
            lookup, length, _ = struct.unpack_from("<III", idx, i * 12)
            if lookup == 0xFFFFFFFF or length == 0xFFFFFFFF or length == 0:
                continue
            f.seek(lookup)
            buf = f.read(length)
            for k in range(0, len(buf) - 6, 7):
                item = buf[k] | (buf[k + 1] << 8)
                counts[item] = counts.get(item, 0) + 1
    return counts


def main(argv):
    if argv[1] == "annotate":
        sys.path.insert(0, HERE)
        import uoart
        data = os.path.join(HERE, "data")
        use = {}
        for m in (0, 2, 3, 4, 5):
            path = os.path.join(data, "statics_usage_m%d.json" % m) if m else os.path.join(data, "statics_usage.json")
            use[m] = json.load(open(path)) if os.path.exists(path) else {}
        art = uoart.art()
        tiles = uoart.tiles()
        with open(argv[2], "w", encoding="utf-8") as out:
            out.write("id | name | height | size | flags | map0 Felucca | map2 Ilshenar | map3 Malas | map4 Tokuno | map5 TerMur\n")
            for t in tiles:
                s = art.static(t.id)
                if not s:
                    continue
                out.write("0x%04X | %s | h=%d | %dx%d | %s | %d | %d | %d | %d | %d\n" % (
                    t.id, t.name, t.height, s[0], s[1], t.short_flags(), use[0].get(str(t.id), 0), use[2].get(str(t.id), 0),
                    use[3].get(str(t.id), 0), use[4].get(str(t.id), 0), use[5].get(str(t.id), 0)))
        print("wrote", argv[2])
        return
    out = argv[1]
    m = int(argv[2]) if len(argv) > 2 else 0
    counts = count_map(m)
    with open(out, "w") as o:
        json.dump({str(k): v for k, v in sorted(counts.items())}, o)
    print("map", m, FACETS.get(m), "ids used:", len(counts), "placements:", sum(counts.values()))


if __name__ == "__main__":
    main(sys.argv)
