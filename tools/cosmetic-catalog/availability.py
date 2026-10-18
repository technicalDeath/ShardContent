"""Which item graphics can players already get in the stock game?  (availability audit for the gold-sink decorations)

A graphic counts as *reachable* when a stock class that players can obtain by crafting, by buying from an NPC, or from the loot tables
carries it (directly, or through an addon deed that places addon components). The audit is built to over-report, not to miss: it reads
every craft menu (including the legacy T2A menus), every vendor stock list and the loot tables of the pinned ModernUO source, without
looking at expansion gates. A source scan cannot prove a negative, so sinkplan.py also re-checks the final picks with a raw scan for any
mention of their graphics anywhere in UOContent (see "rawscan" below).

  python availability.py            -> writes data/reachable_graphics.json  (graphic id -> list of channels)
  python availability.py rawscan    -> lists, for every gold-sink pick, any mention of its graphics in UOContent source (review by hand)
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
SRC = os.path.join(WORKSPACE, "ModernUO", "Projects", "UOContent")
OUT = os.path.join(HERE, "data", "reachable_graphics.json")

HEX = r"(0x[0-9A-Fa-f]{1,4}|\d{1,5})"
ID_PATTERNS = [
    re.compile(r"base\(\s*" + HEX + r"\s*[,)]"),
    re.compile(r"ItemID\s*=\s*" + HEX),
    re.compile(r"AddonComponent\(\s*" + HEX),
    re.compile(r"AddComponent\([^;]*?" + HEX + r"\s*\)\s*,"),
    re.compile(r"itemID\s*=\s*" + HEX),
    re.compile(r"Flippable\(\s*" + HEX + r"\s*,\s*" + HEX),
    re.compile(r"\bnew\s+(?:Static|LocalizedStatic|AddonComponent)\(\s*" + HEX),
]


def to_int(t):
    return int(t, 16) if t.lower().startswith("0x") else int(t)


def load_classes():
    classes = {}
    for root, _, files in os.walk(SRC):
        for f in files:
            if not f.endswith(".cs"):
                continue
            path = os.path.join(root, f)
            try:
                text = open(path, encoding="utf-8-sig", errors="ignore").read()
            except OSError:
                continue
            for m in re.finditer(r"\bclass\s+(\w+)\b", text):
                classes.setdefault(m.group(1), path)
    return classes


_cache = {}


def ids_for(name, classes, depth=0):
    """Graphic ids carried by a class (and, for deeds, by the addon it places)."""
    if name in _cache:
        return _cache[name]
    _cache[name] = set()
    path = classes.get(name)
    if not path or depth > 4:
        return set()
    text = open(path, encoding="utf-8-sig", errors="ignore").read()
    # restrict to this class body roughly: from "class Name" to the next top-level class declaration
    start = re.search(r"\bclass\s+" + re.escape(name) + r"\b", text).start()
    line_start = text.rfind("\n", 0, start) + 1
    while line_start > 0:                                   # pull in the attribute lines directly above the declaration
        prev_start = text.rfind("\n", 0, line_start - 1) + 1
        prev = text[prev_start:line_start].strip()
        if prev.startswith("["):
            line_start = prev_start
        else:
            break
    start_with_attrs = line_start
    m2 = re.search(r"\n\s*(?:public|internal)\s+(?:partial\s+|sealed\s+|abstract\s+)*class\s+(?!" + re.escape(name) + r"\b)\w+", text[start + 10:])
    body = text[start_with_attrs:start + 10 + m2.start()] if m2 else text[start_with_attrs:]
    found = set()
    for pat in ID_PATTERNS:
        for m in pat.finditer(body):
            for g in m.groups():
                if g:
                    try:
                        v = to_int(g)
                    except ValueError:
                        continue
                    if 0x100 <= v < 0x4000:      # smaller numbers are amounts, weights and wall pieces, not decor graphics
                        found.add(v)
    for m in re.finditer(r"Flippable\(([^)]*)\)", body):     # every id of a [Flippable(a, b, c, d)] attribute
        for g in re.findall(r"0[xX][0-9A-Fa-f]{1,4}", m.group(1)):
            v = int(g, 16)
            if 0x100 <= v < 0x4000:
                found.add(v)
    # sequential component runs such as "var itemID = 0x1731 ... itemID++" are caught by the itemID pattern (first id only);
    # extend by +/-24 when a class increments an itemID variable
    if re.search(r"itemID\+\+|\+\+itemID", body):
        for v in list(found):
            found.update(range(v, v + 24))
    # deed -> addon, class used as a type argument
    for m in re.finditer(r"\bnew\s+(\w+(?:Addon|Component|Container))\s*\(", body):
        if m.group(1) != name:
            found |= ids_for(m.group(1), classes, depth + 1)
    for m in re.finditer(r"=>\s*new\s+(\w+)\s*\(\s*\)", body):
        if m.group(1) != name and "Addon" in m.group(1):
            found |= ids_for(m.group(1), classes, depth + 1)
    # inheritance (item base classes such as BaseLight, Candelabra)
    m = re.search(r"\bclass\s+" + re.escape(name) + r"\b[^:{]*:\s*(\w+)", body)
    if m and m.group(1) in classes and m.group(1) not in ("Item", "BaseAddon", "BaseAddonDeed", "BaseCreature", "Mobile"):
        found |= ids_for(m.group(1), classes, depth + 1)
    _cache[name] = found
    return found


def typeof_names(path):
    text = open(path, encoding="utf-8-sig", errors="ignore").read()
    return set(re.findall(r"typeof\(\s*(\w+)\s*\)", text))


def main():
    classes = load_classes()
    channels = {}
    sources = []
    craft_dir = os.path.join(SRC, "Engines", "Craft")
    for f in sorted(os.listdir(craft_dir)):
        if f.startswith("Def") and f.endswith(".cs"):
            sources.append(("craft:" + f[3:-3], os.path.join(craft_dir, f)))
    t2a_dir = os.path.join(craft_dir, "T2A")
    if os.path.isdir(t2a_dir):
        for f in sorted(os.listdir(t2a_dir)):
            if f.endswith(".cs"):
                sources.append(("craft-t2a:" + f[:-3], os.path.join(t2a_dir, f)))
    sb_dir = os.path.join(SRC, "Mobiles", "Vendors", "SBInfo")
    for root, _, files in os.walk(sb_dir):
        for f in sorted(files):
            if f.endswith(".cs"):
                sources.append(("vendor:" + f[:-3], os.path.join(root, f)))
    sources.append(("loot:Loot", os.path.join(SRC, "Misc", "Loot.cs")))
    for extra in ("Items/TreasureChests", "Engines/Treasure Maps", "Engines/Fishing"):
        base = os.path.join(SRC, extra.replace("/", os.sep))
        if os.path.isdir(base):
            for root, _, files in os.walk(base):
                for f in files:
                    if f.endswith(".cs"):
                        sources.append(("loot:" + f[:-3], os.path.join(root, f)))
    for channel, path in sources:
        for name in typeof_names(path):
            for gid in ids_for(name, classes):
                channels.setdefault(gid, set()).add(channel)
    out = {"%d" % gid: sorted(ch)[:6] for gid, ch in sorted(channels.items())}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({"note": "graphic ids players can already reach by crafting, NPC vendors or loot tables (generous: ignores expansion gates)",
                   "count": len(out), "graphics": out}, f, indent=0)
    print("reachable graphics:", len(out), "from", len(sources), "sources,", len(classes), "classes")


def rawscan():
    """Any mention of a pick's graphic ids in UOContent source, with the files, for a human to review (tiny prop tiles are expected)."""
    import collections
    sel = json.load(open(os.path.join(WORKSPACE, "ShardContent", "docs", "cosmetic-rewards", "gold-sink", "selection.json"), encoding="utf-8"))["items"]
    full = {}
    for n in ("cosmetic-rewards.json", "cosmetic-rewards-neutral.json"):
        for r in json.load(open(os.path.join(WORKSPACE, "ShardContent", "docs", "cosmetic-rewards", n), encoding="utf-8"))["rewards"]:
            full[r["id"]] = r
    idx = collections.defaultdict(set)
    pat = re.compile(r"\b0[xX]([0-9A-Fa-f]{1,5})\b")
    for d, _, fs in os.walk(SRC):
        for f in fs:
            if f.endswith(".cs"):
                path = os.path.join(d, f)
                for m in pat.finditer(open(path, encoding="utf-8-sig", errors="ignore").read()):
                    idx[int(m.group(1), 16)].add(os.path.relpath(path, SRC))
    hits = 0
    for it in sel:
        gids = {num_id(g["id"]) for g in full[it["id"]]["graphics"]}
        h = {g: sorted(idx[g]) for g in gids if g in idx}
        if h:
            hits += 1
            print("%-11s %s" % (it["id"], it["name"]))
            for g, fl in h.items():
                print("     0x%04X: %s" % (g, ", ".join(fl[:3]) + (" ... +%d" % (len(fl) - 3) if len(fl) > 3 else "")))
    print("picks with any mention:", hits, "of", len(sel))


def num_id(v):
    return int(v, 16) if isinstance(v, str) else int(v)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "rawscan":
        rawscan()
    else:
        main()
