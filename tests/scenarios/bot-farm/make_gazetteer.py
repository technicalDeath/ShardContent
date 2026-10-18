"""Generate gazetteer.json (the lookup table behind gazetteer.py) from the world's own data. Read-only on the inputs; run it again whenever the world
data changes, and on another shard or map with --data pointing at that shard's Data folder.

    python make_gazetteer.py                  # writes gazetteer.json next to this file
    python make_gazetteer.py --check          # exit 1 if gazetteer.json differs from what the inputs would produce
    python make_gazetteer.py --data <Data> --uodata <client data> --moongen <PublicMoongate.cs> --out <file>

Inputs (defaults are this workspace's dev distribution):
  <Data>/regions.json                                   town, dungeon and other regions of the map (Felucca)
  <Data>/BritanniaRenaissance/Alpha2b/Spawns/{Vendors,TownsPeople,britain-vendor-overrides}.json    NPC spawners: the vendors, healers, guards...
  <Data>/BritanniaRenaissance/Alpha2b/Decoration/*.cfg  decoration items: forges, anvils, looms, ankhs... (also found by type name)
  <UOData>/{tiledata.mul,staidx0.mul,statics0.mul}      the map's own statics: the forges, anvils, looms, ovens... the decoration files lack
  <Data>/BritanniaRenaissance/Alpha2b/teleporters.json  teleporter definitions (entry -> landing; "back" adds the reverse), else <Data>/teleporters.json
  PublicMoongate.cs                                     the Felucca public moongate list (what MoonGen generates)
  <Data>/Locations/felucca.json                         named dungeon entrances
Not typed anywhere: every coordinate in the output comes from one of these. Output is deterministic (no timestamps), so --check works.
"""
import argparse
import hashlib
import json
import math
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gazetteer as gz                                 # noqa: E402  (side_of)

ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
MAP = "Felucca"
FARM = re.compile(r"field|farm|wheat|cotton|onion|carrot|cabbage|turnip|orchard|garden|pasture", re.I)

ROLE_OF = {
    "Banker": "bank", "Minter": "bank", "Healer": "healer", "Blacksmith": "smith", "Weaponsmith": "weaponsmith", "Armorer": "armorer",
    "Bowyer": "bowyer", "Tailor": "tailor", "Weaver": "weaver", "Carpenter": "carpenter", "Butcher": "butcher", "Baker": "baker",
    "Provisioner": "provisioner", "Alchemist": "alchemist", "Mage": "mage", "Herbalist": "herbalist", "Tinker": "tinker", "Tanner": "tanner",
    "Cobbler": "cobbler", "Jeweler": "jeweler", "Scribe": "scribe", "InnKeeper": "inn", "TavernKeeper": "tavern", "Fisherman": "fisherman",
    "AnimalTrainer": "animal_trainer", "Furtrader": "furtrader", "Mapmaker": "mapmaker", "Shipwright": "shipwright", "Architect": "architect",
    "RealEstateBroker": "broker", "HarborMaster": "harbormaster", "OrderGuard": "guard", "ChaosGuard": "guard", "TownCrier": "crier",
    "Miner": "miner", "Waiter": "waiter", "Cook": "cook", "Artist": "artist", "Bard": "bard", "Merchant": "merchant", "Noble": "noble",
    "Peasant": "peasant",
}
SKIP_TYPES = {"escortablemage", "escortablewanderinghealer", "wanderinghealer", "rat", "cat", "dog", "bird", "chicken", "sheep", "cow", "bull"}
TYPE_PATTERNS = [("soulforge", None), ("forge", "forge"), ("anvil", "anvil"), ("loom", "loom"), ("spinningwheel", "spinning_wheel"), ("oven", "oven"),
                 ("archerybutte", "butte"), ("trainingdummy", "dummy"), ("ankh", "ankh"), ("flourmill", "mill")]
TILE_ROLE = {"forge": "forge", "anvil": "anvil", "upright loom": "loom", "spinning wheel": "spinning_wheel", "oven": "oven", "flour mill": "mill",
             "ankh of sacrifice": "ankh", "training dummy": "dummy", "archery butte": "butte"}
FACILITY_ROLES = set(TILE_ROLE.values())


def snake(s):
    return re.sub(r"(?<!^)(?=[A-Z])", "_", s).lower()


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()[:12]


# ---- regions -------------------------------------------------------------------------------------------------------------------------------------

def load_regions(data):
    raw = json.load(open(os.path.join(data, "regions.json"), encoding="utf-8"))
    out, used = [], {}
    for r in raw:
        if r.get("Map") != MAP or not r.get("Area"):
            continue
        t = r["$type"]
        name = r.get("Name")
        if t == "DungeonRegion":
            kind = "dungeon"
        elif t == "TownRegion" and name:
            kind = "farm" if FARM.search(name) else "town"
        else:
            kind = "other"
        if not name:
            name = f"{t}@{r['Area'][0]['x1']},{r['Area'][0]['y1']}"
        n = used.get(name, 0)
        used[name] = n + 1
        if n:
            name = f"{name}#{n + 1}"
        go = r.get("GoLocation")
        rects = [[a["x1"], a["y1"], a["x2"], a["y2"]] for a in r["Area"]]
        if go:
            centre = [go["x"], go["y"], go.get("z", 0)]
        else:
            a = rects[0]
            centre = [(a[0] + a[2]) // 2, (a[1] + a[3]) // 2, 0]
        out.append(dict(name=name, type=t, kind=kind, priority=r.get("Priority", 0), centre=centre, rects=rects))
    return out


def town_of(regions, x, y):
    hits = [r for r in regions if r["kind"] in ("town", "dungeon") and gz._in_rects(r["rects"], x, y)]
    if not hits:
        return None
    return sorted(hits, key=lambda r: (-r.get("priority", 0), gz._area(r["rects"])))[0]["name"]


# ---- places --------------------------------------------------------------------------------------------------------------------------------------

class Builder:
    def __init__(self, regions):
        self.regions = regions
        self.places = []

    def add(self, role, roles, typ, x, y, z, src, radius=0, name=None, **extra):
        p = dict(role=role, roles=sorted(set(r.lower() for r in roles)), type=typ, x=int(x), y=int(y), z=int(z), radius=int(radius), src=src,
                 region=town_of(self.regions, x, y), side=gz.side_of(self.regions, x, y))
        if name:
            p["name"] = name
        p.update(extra)
        self.places.append(p)
        return p


def vendor_places(b, spawn_dir):
    files = ["Vendors.json", "TownsPeople.json", "britain-vendor-overrides.json"]
    used = []
    for f in files:
        path = os.path.join(spawn_dir, f)
        if not os.path.exists(path):
            continue
        used.append(path)
        for sp in json.load(open(path, encoding="utf-8")):
            if sp.get("map") != MAP:
                continue
            x, y, z = sp["location"][:3]
            radius = max(sp.get("walkingRange", 0), sp.get("homeRange", 0))
            for e in sp["entries"]:
                typ = e["name"]
                if typ.lower() in SKIP_TYPES:
                    continue
                if typ.endswith("Guildmaster") and len(typ) > 11:
                    base = typ[:-11]
                    role = f"{ROLE_OF.get(base, snake(base))}_guildmaster"
                    roles = [role, "guildmaster", typ]
                else:
                    role = ROLE_OF.get(typ, snake(typ))
                    roles = [role, typ]
                b.add(role, roles, typ, x, y, z, "spawner:" + f, radius)
    return used


def load_names(uodata):
    """item id -> lower-case name from tiledata.mul (the 7.0 layout: 512 land groups of 32 x 30 bytes, then item groups of 32 x 41 bytes)."""
    raw = open(os.path.join(uodata, "tiledata.mul"), "rb").read()
    o = 512 * (4 + 32 * 30)
    names = {}
    for g in range(2048):
        o += 4
        for i in range(32):
            names[g * 32 + i] = raw[o + 21:o + 41].split(b"\0")[0].decode("latin1").lower()
            o += 41
    return names


def decor_role(typ, hexid, names):
    t = typ.lower()
    for pat, role in TYPE_PATTERNS:
        if pat in t:
            return role
    if hexid:
        return TILE_ROLE.get(names.get(int(hexid, 16), ""))
    return None


def parse_cfg(path):
    cur = None
    for line in open(path, encoding="utf-8", errors="ignore"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"^(-?\d+)\s+(-?\d+)\s+(-?\d+)(\s|$)", line)
        if m and cur:
            yield cur, int(m.group(1)), int(m.group(2)), int(m.group(3))
        elif not m:
            tok = line.split()
            cur = (tok[0], tok[1] if len(tok) > 1 and tok[1].lower().startswith("0x") else None)


def raw_facilities(decor_dir, uodata, names, regions):
    """[(role, type, x, y, z, src)] from the decoration files and, when the client data is there, the map's statics inside or near a town."""
    out = []
    if os.path.isdir(decor_dir):
        for f in sorted(os.listdir(decor_dir)):
            if f.lower().endswith(".cfg"):
                for (typ, hexid), x, y, z in parse_cfg(os.path.join(decor_dir, f)):
                    role = decor_role(typ, hexid, names)
                    if role:
                        out.append((role, typ if typ != "Static" else (names.get(int(hexid, 16), typ) if hexid else typ), x, y, z, "decor"))
    idx_p, st_p = os.path.join(uodata, "staidx0.mul"), os.path.join(uodata, "statics0.mul")
    if os.path.exists(idx_p) and os.path.exists(st_p):
        ids = {i: TILE_ROLE[n] for i, n in names.items() if n in TILE_ROLE}
        towns = [r for r in regions if r["kind"] == "town"]
        zones = [[t[0] - 30, t[1] - 30, t[2] + 30, t[3] + 30] for r in towns for t in r["rects"]]
        idx, st = open(idx_p, "rb").read(), open(st_p, "rb").read()
        for bi in range(len(idx) // 12):
            off, ln, _ = struct.unpack_from("<iii", idx, bi * 12)
            if off < 0 or ln <= 0:
                continue
            bx, by = divmod(bi, 512)
            if bx * 8 >= gz.SURFACE_X:
                continue
            for k in range(ln // 7):
                tid, xo, yo, z, _h = struct.unpack_from("<HBBbH", st, off + k * 7)
                role = ids.get(tid)
                if role:
                    x, y = bx * 8 + xo, by * 8 + yo
                    if gz._in_rects(zones, x, y):
                        out.append((role, names[tid], x, y, z, "static"))
    return out


def cluster(items, dist=3):
    """Merge same-role facility tiles within `dist` tiles of each other (a forge is several tiles) into one place; keeps the count. A forge and an
    anvil side by side stay two places: they differ by role."""
    out = []
    by_role = {}
    for it in items:
        by_role.setdefault(it[0], []).append(it)
    for role in sorted(by_role):
        groups = []
        for it in sorted(by_role[role], key=lambda t: (t[2], t[3])):
            hit = [g for g in groups if any(abs(m[2] - it[2]) <= dist and abs(m[3] - it[3]) <= dist for m in g)]
            if not hit:
                groups.append([it])
                continue
            hit[0].append(it)
            for g in hit[1:]:                                   # the tile joins two groups: merge them
                hit[0].extend(g)
                groups.remove(g)
        for g in groups:
            xs = sorted(m[2] for m in g)
            ys = sorted(m[3] for m in g)
            types = sorted({m[1] for m in g})[:3]
            out.append((role, "/".join(types), xs[len(xs) // 2], ys[len(ys) // 2], g[0][4], "+".join(sorted({m[5] for m in g})), len(g)))
    return out


def moongates(path):
    text = open(path, encoding="utf-8").read()
    m = re.search(r"public static readonly PMList Felucca\s*=\s*new\((.*?)\]\s*\);", text, re.S)
    out = []
    for line in m.group(1).splitlines():
        p = re.search(r"Point3D\((\d+),\s*(\d+),", line)
        if p:
            nm = re.search(r"//\s*(.*)$", line)
            out.append((int(p.group(1)), int(p.group(2)), re.sub(r"^\(New\)\s*", "", nm.group(1).strip()) if nm else "moongate"))
    return out


# ---- teleporters ---------------------------------------------------------------------------------------------------------------------------------

def transitions(path, regions):
    raw = json.load(open(path, encoding="utf-8"))
    seen, out = set(), []

    def add(src, dst, derived):
        key = (tuple(src), tuple(dst))
        if key in seen:
            return
        seen.add(key)
        ss, ds = gz.side_of(regions, src[0], src[1]), gz.side_of(regions, dst[0], dst[1])
        if ss == "surface" and ds != "surface":
            kind = "enter"
        elif ss != "surface" and ds == "surface":
            kind = "exit"
        elif ss == ds == "surface":
            kind = "surface"
        else:
            kind = "inner" if ss == ds else "link"
        out.append(dict(src=list(src), dst=list(dst), kind=kind, src_side=ss, dst_side=ds, src_region=town_of(regions, src[0], src[1]),
                        dst_region=town_of(regions, dst[0], dst[1]), derived=derived))

    for e in raw:
        if e["src"]["map"] != MAP or e["dst"]["map"] != MAP:
            continue
        add(e["src"]["loc"], e["dst"]["loc"], False)
        if e.get("back"):
            add(e["dst"]["loc"], e["src"]["loc"], True)
    out.sort(key=lambda t: (t["src"], t["dst"]))
    return out


def location_entrances(path):
    data = json.load(open(path, encoding="utf-8"))
    out = []

    def walk(cat, trail):
        for c in cat.get("categories", []):
            walk(c, trail + [c["name"]])
        if trail and trail[0] == "Dungeons" and len(trail) >= 2:
            for loc in cat.get("locations", []):
                if re.search(r"entrance|entryway", loc["name"], re.I) and not re.search(r"level", loc["name"], re.I):
                    out.append((trail[1], loc["name"], loc["location"]))

    for c in data.get("categories", []):
        walk(c, [c["name"]])
    return out


# ---- assemble ------------------------------------------------------------------------------------------------------------------------------------

def build(data, uodata, moongen, out_path=None):
    alpha = os.path.join(data, "BritanniaRenaissance", "Alpha2b")
    regions = load_regions(data)
    b = Builder(regions)
    sources = {"regions.json": sha(os.path.join(data, "regions.json"))}
    for p in vendor_places(b, os.path.join(alpha, "Spawns")):
        sources[os.path.basename(p)] = sha(p)
    names = load_names(uodata) if os.path.exists(os.path.join(uodata, "tiledata.mul")) else {}
    if names:
        sources["tiledata.mul"] = sha(os.path.join(uodata, "tiledata.mul"))
        for f in ("staidx0.mul", "statics0.mul"):
            if os.path.exists(os.path.join(uodata, f)):
                sources[f] = sha(os.path.join(uodata, f))
    decor = os.path.join(alpha, "Decoration")
    if os.path.isdir(decor):
        sources["Decoration"] = hashlib.sha256(b"".join(open(os.path.join(decor, f), "rb").read() for f in sorted(os.listdir(decor)) if f.endswith(".cfg"))).hexdigest()[:12]
    for role, typ, x, y, z, src, n in cluster(raw_facilities(decor, uodata, names, regions)):
        b.add(role, [role, typ], typ, x, y, z, src, n=n)
    mg = moongen if moongen and os.path.exists(moongen) else None
    if mg:
        sources["PublicMoongate.cs"] = sha(mg)
        for x, y, nm in moongates(mg):
            b.add("moongate", ["moongate", "gate"], "PublicMoongate", x, y, 0, "moongen", name=nm)
    tpath = os.path.join(alpha, "teleporters.json")
    if not os.path.exists(tpath):
        tpath = os.path.join(data, "teleporters.json")
    sources[os.path.relpath(tpath, data).replace("\\", "/")] = sha(tpath)
    trans = transitions(tpath, regions)
    # dungeon entrances: where the surface meets a different side, one place per cluster of entry tiles with the same destination side
    groups = []
    for t in trans:
        if t["kind"] != "enter":
            continue
        for g in groups:
            if g["dst_side"] == t["dst_side"] and abs(g["tiles"][0][0] - t["src"][0]) <= 12 and abs(g["tiles"][0][1] - t["src"][1]) <= 12:
                g["tiles"].append(t["src"])
                break
        else:
            groups.append(dict(dst_side=t["dst_side"], tiles=[t["src"]], landing=t["dst"], town=t["src_region"]))
    locs = []
    lpath = os.path.join(data, "Locations", "felucca.json")
    if os.path.exists(lpath):
        sources["Locations/felucca.json"] = sha(lpath)
        locs = location_entrances(lpath)
    for g in groups:
        xs = sorted(t[0] for t in g["tiles"])
        ys = sorted(t[1] for t in g["tiles"])
        x, y = xs[len(xs) // 2], ys[len(ys) // 2]
        name = g["dst_side"]
        for cat, _nm, loc in locs:
            if abs(loc[0] - x) <= 12 and abs(loc[1] - y) <= 12:
                name = cat
        if name.startswith("interior@"):                # an unnamed level: the nearest named dungeon entrance within 60 tiles, else say where it is
            near = sorted((math.hypot(loc[0] - x, loc[1] - y), cat) for cat, _nm, loc in locs if math.hypot(loc[0] - x, loc[1] - y) <= 60)
            name = near[0][1] if near else f"cave near {x},{y}"
        b.add("dungeon_entrance", ["dungeon_entrance", "entrance"], "teleporter", x, y, g["tiles"][0][2], "teleporters", name=name, dungeon=g["dst_side"],
              landing=g["landing"], tiles=g["tiles"])
    for cat, _nm, loc in locs:
        if not any(abs(p["x"] - loc[0]) <= 12 and abs(p["y"] - loc[1]) <= 12 for p in b.places if p["role"] == "dungeon_entrance"):
            b.add("dungeon_entrance", ["dungeon_entrance", "entrance"], "location", loc[0], loc[1], loc[2], "locations", name=cat)
    merged = {}
    for p in b.places:                                   # a spawner with two entries of one role (Banker and Minter) is one place
        k = (p["role"], p["x"], p["y"], p["z"])
        if k in merged:
            q = merged[k]
            q["roles"] = sorted(set(q["roles"]) | set(p["roles"]))
            if p["type"] not in q["type"].split("/"):
                q["type"] += "/" + p["type"]
            q["n"] = q.get("n", 1) + p.get("n", 1)
        else:
            merged[k] = p
    b.places = sorted(merged.values(), key=lambda p: (p["role"], p["x"], p["y"], p["type"]))
    return dict(schema=1, map=MAP, sources=dict(sorted(sources.items())), regions=regions, places=b.places, transitions=trans)


def dump(doc):
    parts = []
    for key, val in doc.items():
        if isinstance(val, list):
            parts.append(f'"{key}":[\n' + ",\n".join(json.dumps(v, separators=(",", ":"), sort_keys=True) for v in val) + "\n]")
        else:
            parts.append(f'"{key}":' + json.dumps(val, separators=(",", ":"), sort_keys=True))
    return "{\n" + ",\n".join(parts) + "\n}\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=os.path.join(ROOT, "ModernUO", "Distribution", "Data"))
    ap.add_argument("--uodata", default=os.path.join(ROOT, "UOData"))
    ap.add_argument("--moongen", default=os.path.join(ROOT, "ModernUO", "Projects", "UOContent", "Items", "Misc", "PublicMoongate.cs"))
    ap.add_argument("--out", default=os.path.join(HERE, "gazetteer.json"))
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    text = dump(build(a.data, a.uodata, a.moongen))
    if a.check:
        same = os.path.exists(a.out) and open(a.out, encoding="utf-8").read() == text
        print("gazetteer.json is up to date" if same else "gazetteer.json DIFFERS from the inputs: run make_gazetteer.py")
        sys.exit(0 if same else 1)
    with open(a.out, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    doc = json.loads(text)
    roles = {}
    for p in doc["places"]:
        roles[p["role"]] = roles.get(p["role"], 0) + 1
    print(f"wrote {a.out}: {len(doc['regions'])} regions, {len(doc['places'])} places, {len(doc['transitions'])} teleporters")
    print("roles:", dict(sorted(roles.items(), key=lambda kv: -kv[1])))


if __name__ == "__main__":
    main()
