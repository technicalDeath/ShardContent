"""Gold-sink decorations: candidate pool, wings, coolness score and rarity ladder.

  python sinkplan.py supply            -> prints how many furnishing candidates each category x catalog-tier has
  python sinkplan.py candidates CAT    -> prints the scored candidates of one catalog category (id, tier, score, name)
  python sinkplan.py build [--no-sheets] -> writes selection.json, Gold-Sink-Items.csv, pricing-sandbox.html and (unless --no-sheets) the picture sheets
                                           from gold-sink/picks.json and collections.json
  (vendors.json lists the Britain Furnisher's selection; BASE_PRICE, TIER_UNITS and PRICE_CAP set the illustrative price curve)
  python sinkplan.py showroom          -> plans the real-client showroom pages (GS-<WING>-NN); then Run-GalleryShots.ps1 -Category GS and galleries.py index

A candidate is a reward that (1) is not in any suggested reward pool, (2) is not reachable by crafting / NPC vendors / loot (availability.py),
(3) is era grade A or B (main catalog) or era-neutral (CN), (4) is not retired, (5) is not hidden entirely by the Felucca foliage rule, and
(6) passes the furnishing rule (owner, 2026-10-08): a standard home furnishing (FURNISHING_CATS plus the FURNISHING_EXTRA outliers), with no
seasonal or holiday theme and nothing macabre, crypt, dungeon, necromantic, camp, military or monster-themed (BLOCK_TAGS, BLOCK_WORDS).
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import catalog  # noqa: E402

DOCS = catalog.DOCS
SINK = os.path.join(DOCS, "gold-sink")

WINGS = {
    "BEDCHAMBER": ("Bedchamber", "Bedchamber"),
    "PARLOUR": ("Parlour & Music Room", "Parlour"),
    "DINING": ("Dining & Kitchen", "Dining"),
    "FLOORS": ("Rugs & Carpets", "Rugs"),
    "HEARTH": ("Hearth & Light", "Hearth"),
    "STUDY": ("Study & Observatory", "Study"),
    "WALLS": ("Walls & Hangings", "Walls"),
    "CURIOS": ("Hall Curios", "Curios"),
}
# the furnishing rule: whole categories that hold standard home furnishings, plus a few single outliers from other categories
FURNISHING_CATS = {"FRN", "TBL", "RUG", "FOO", "LGT", "LIB", "CUR", "WLH", "MUS", "GAM"}
FURNISHING_EXTRA = {"CN-ANM-001", "CN-ANM-002", "CN-ANM-003", "CN-ANM-004", "CN-ANM-017", "CN-ANM-018", "CN-ANM-019", "CN-ANM-020",
                    "CN-ANM-021", "CN-ANM-022", "CN-FLO-004", "CN-FLO-006", "CN-FLO-009", "CN-FLO-022", "CN-ALC-001", "CN-ALC-006",
                    "CN-CMP-007", "CN-CMP-008", "CR-TRO-014", "CR-ARM-019", "CR-ARM-020", "CN-TRS-012", "CN-TRS-015", "CN-TRS-017",
                    "CN-TRS-020", "CN-TRS-023", "CN-TRS-024"}
BLOCK_TAGS = {"festive", "macabre", "undead", "demonic", "season:halloween", "season:winter", "season:harvest", "season:spring", "dungeon"}
BLOCK_WORDS = ("skull", "bone", "blood", "coffin", "casket", "grave", "tomb", "pumpkin", "jack-o", "snowman", "holly", "wreath", "ghost",
               "spider", "web", "mourning", "gibbet", "dagger", "witch", "cauldron", "pentagram", "candy", "easter", "valentine", "heart on",
               "death", "crypt", "torture", "turkey", "holiday")
BASE_PRICE = 2000    # owner's starting base (Common anchor) price, 2026-10-08; the real prices are his
TIER_BASE = {"common": 12, "uncommon": 28, "scarce": 46, "rare": 64, "extremely-rare": 82}
TIER_ORDER = ["common", "uncommon", "scarce", "rare", "extremely-rare"]
# borderline entries the owner has not ruled on (README of the neutral section): never part of a launch set
HOLD_NEUTRAL = {"CN-WLH-001", "CN-WLH-002", "CN-WLH-003", "CN-WLH-004", "CN-WLH-005", "CN-WLH-029", "CN-WTR-003", "CN-WTR-005",
                "CN-LGT-018", "CN-LGT-019", "CN-MUS-008", "CN-NEC-042", "CN-NEC-038", "CN-NEC-039", "CN-NEC-040", "CN-NEC-041",
                "CN-ALC-025"}


def num(v):
    return int(v, 0) if isinstance(v, str) else int(v)


def load_rewards(name):
    return json.load(open(os.path.join(DOCS, name), encoding="utf-8"))["rewards"]


def pool_ids():
    out = set()
    folder = os.path.join(DOCS, "pools")
    for f in os.listdir(folder):
        if f.endswith(".json"):
            for en in json.load(open(os.path.join(folder, f), encoding="utf-8"))["entries"]:
                out.add(en["id"])
    return out


def reachable():
    path = os.path.join(HERE, "data", "reachable_graphics.json")
    return {int(k) for k in json.load(open(path))["graphics"]}


def coolness(r):
    s = TIER_BASE[r["tier"]]
    tiles = len(r["graphics"])
    s += 12 if tiles >= 15 else 8 if tiles >= 6 else 4 if tiles >= 2 else 0
    h = r["pixelSize"]["height"]
    s += 8 if h >= 200 else 4 if h >= 120 else 0
    if any(g["hue"] for g in r["graphics"]):
        s += 3
    if r.get("altFacings"):
        s += 2
    tags = set(r["tags"])
    s += 2 * bool(tags & {"dragon", "demonic"}) + bool(tags & {"noble", "macabre", "arcane", "treasure"})
    fel = r.get("felucca", {})
    if fel.get("seasonHidesFoliage"):
        s -= 5
    return max(0, min(100, s))


def curation_flags(r):
    """Why a reward fails the furnishing rule (empty list when it passes): seasonal or macabre tags, blocked words in the name."""
    flags = sorted(set(r["tags"]) & BLOCK_TAGS)
    low = r["name"].lower()
    flags += ["name:" + w for w in BLOCK_WORDS if re.search(r"" + re.escape(w), low)]       # word starts only ("Ribboned" is not "bone")
    return flags


def furnishing(r):
    return (r["category"] in FURNISHING_CATS or r["id"] in FURNISHING_EXTRA) and not curation_flags(r)


def candidates():
    pools = pool_ids()
    reach = reachable()
    out = []
    for source, name in (("era", "cosmetic-rewards.json"), ("neutral", "cosmetic-rewards-neutral.json")):
        for r in load_rewards(name):
            if r.get("retired") or r["id"] in pools or r["id"] in HOLD_NEUTRAL:
                continue
            if source == "era" and r["era"]["grade"] == "C":
                continue
            if any(num(g["id"]) in reach for g in r["graphics"]):
                continue
            fel = r.get("felucca", {})
            if fel.get("seasonHidesFoliage") and not fel.get("visibleInFelucca"):
                continue
            if not furnishing(r):
                continue
            out.append({"id": r["id"], "name": r["name"], "category": r["category"], "catalogTier": r["tier"],
                        "coolness": coolness(r), "source": source, "tiles": len(r["graphics"]), "height": r["pixelSize"]["height"],
                        "placement": r["placement"], "tags": r["tags"], "image": r["image"]})
    return out


def main(argv):
    cmd = argv[1] if len(argv) > 1 else ""
    cands = candidates()
    if cmd == "supply":
        print("candidates:", len(cands), "(era %d, neutral %d)" % (sum(c["source"] == "era" for c in cands), sum(c["source"] == "neutral" for c in cands)))
        print("%-10s %s" % ("category", "  ".join("%-6s" % t[:6] for t in TIER_ORDER)))
        for cat in sorted({c["category"] for c in cands}):
            row = [sum(1 for c in cands if c["category"] == cat and c["catalogTier"] == t) for t in TIER_ORDER]
            print("%-10s %s   total %d" % (cat, "  ".join("%-6d" % n for n in row), sum(row)))
    elif cmd == "candidates":
        cat = argv[2].upper()
        for c in sorted((c for c in cands if c["category"] == cat), key=lambda c: -c["coolness"]):
            print("%-11s %-15s %3d %-2s %2dt h%-3d %s" % (c["id"], c["catalogTier"], c["coolness"], c["source"][0], c["tiles"], c["height"], c["name"]))
    elif cmd == "sheet":
        # sheet CAT hi|lo|all [N] out.png   (hi = scarce and above, lo = common/uncommon)
        wing, band, n, out = argv[2].upper(), argv[3], int(argv[4]), argv[5]
        want = {"hi": ("scarce", "rare", "extremely-rare"), "lo": ("common", "uncommon"), "all": tuple(TIER_ORDER)}[band]
        picks = [c for c in sorted(cands, key=lambda c: -c["coolness"]) if c["category"] == wing and c["catalogTier"] in want][:n]
        full = {}
        for name in ("cosmetic-rewards.json", "cosmetic-rewards-neutral.json"):
            for r in load_rewards(name):
                full[r["id"]] = r
        entries = [full[c["id"]] for c in picks]
        catalog.sheet_entries(out, entries, cols=8, cell=120)
        for i, c in enumerate(picks, 1):
            print("#%-2d %-11s %-14s %3d %s %2dt  %s" % (i, c["id"], c["catalogTier"], c["coolness"], c["source"][0], c["tiles"], c["name"]))
    elif cmd == "build":
        build(cands, shoot_sheets="--no-sheets" not in argv)
    elif cmd == "showroom":
        showroom()
    else:
        print(__doc__)


TIER_NAMES = {1: "Common", 2: "Uncommon", 3: "Scarce", 4: "Rare", 5: "Extremely Rare", 6: "Wonder"}
TIER_UNITS = {1: 1, 2: 2, 3: 4, 4: 8, 5: 16, 6: 35}            # the suggested price curve, in units of the Tier 1 anchor price (owner: tone it down, top out at 80k)
PRICE_CAP = 80000      # nothing sells for more than this (owner, 2026-10-08)
PRICE_ROUND = 50
TIER_COLOUR = {1: "#8a8f98", 2: "#3fa34d", 3: "#3a7bd5", 4: "#a24bd6", 5: "#e0a020", 6: "#e0502a"}
CATALOG_TIER_RANK = {t: i for i, t in enumerate(TIER_ORDER)}


def piece_price(it):
    """Illustrative price: base x rarity units x (0.85 .. 1.15 by position in the rarity), rounded, never above PRICE_CAP."""
    raw = BASE_PRICE * TIER_UNITS[it["tier"]] * (0.85 + 0.30 * it["positionInTier"])
    return min(PRICE_CAP, int(round(raw / PRICE_ROUND)) * PRICE_ROUND)


def britain_ids():
    path = os.path.join(SINK, "vendors.json")
    if not os.path.exists(path):
        return set()
    cfg = json.load(open(path, encoding="utf-8"))["furnisher-britain"]
    return {rid for ids in cfg.values() for rid in ids}


def load_full():
    full = {}
    for name in ("cosmetic-rewards.json", "cosmetic-rewards-neutral.json"):
        for r in load_rewards(name):
            full[r["id"]] = r
    return full


def load_selection(cands=None):
    cfg = json.load(open(os.path.join(SINK, "picks.json"), encoding="utf-8"))
    colls = json.load(open(os.path.join(SINK, "collections.json"), encoding="utf-8"))["collections"]
    coll_of = {rid: name for name, ids in colls.items() for rid in ids}
    full = load_full()
    wing_order = list(WINGS)
    items = []
    for wing in wing_order:
        for t, ids in cfg["picks"].get(wing, {}).items():
            for rid in ids:
                r = full[rid]
                items.append({"id": rid, "name": r["name"], "blurb": r["blurb"], "wing": wing, "wingName": WINGS[wing][0],
                              "tier": int(t), "tierName": TIER_NAMES[int(t)], "catalogTier": r["tier"], "source": "neutral" if rid.startswith("CN") else "era",
                              "eraGrade": r["era"]["grade"], "coolness": coolness(r), "tags": r["tags"], "placement": r["placement"],
                              "footprint": r.get("footprint", ""), "tiles": len(r["graphics"]), "pixelWidth": r["pixelSize"]["width"],
                              "pixelHeight": r["pixelSize"]["height"], "category": r["category"], "image": r["image"],
                              "felucca": r.get("felucca", {}), "collection": coll_of.get(rid)})
    items.sort(key=lambda x: (x["tier"], wing_order.index(x["wing"]), x["name"]))
    for i, it in enumerate(items, 1):
        it["no"] = i
    # position inside the tier (0 = plainest, 1 = coolest) by coolness, ties by name
    for t in TIER_NAMES:
        grp = sorted((it for it in items if it["tier"] == t), key=lambda it: (it["coolness"], it["name"]))
        for k, it in enumerate(grp):
            it["positionInTier"] = round(k / (len(grp) - 1), 3) if len(grp) > 1 else 0.5
    shop = britain_ids()
    missing = shop - {it["id"] for it in items}
    if missing:
        print("BRITAIN SELECTION NOT PICKED:", sorted(missing))
    for it in items:
        it["soldAt"] = "britain" if it["id"] in shop else "later"
        it["price"] = piece_price(it)
    return items, full, colls


def strict_alternates(items, cands):
    """For each era-neutral pick, the nearest era-graded furnishing candidate (same catalog category only) that is not already picked."""
    picked = {it["id"] for it in items}
    for it in items:
        it["strictEraAlternate"] = None
        if it["source"] != "neutral":
            continue
        pool = [c for c in cands if c["source"] == "era" and c["category"] == it["category"] and c["id"] not in picked]
        want = CATALOG_TIER_RANK[it["catalogTier"]]
        pool.sort(key=lambda c: (abs(CATALOG_TIER_RANK[c["catalogTier"]] - want), abs(c["coolness"] - it["coolness"])))
        if pool:
            c = pool[0]
            picked.add(c["id"])
            it["strictEraAlternate"] = {"id": c["id"], "name": c["name"], "catalogTier": c["catalogTier"], "coolness": c["coolness"]}


def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def sheet_page(title, sub, items, out_html, cols):
    cards = []
    for it in items:
        cards.append(
            '<div class="c"><div class="im"><img src="../%s"></div><div class="no">No. %d &middot; <span class="id">%s</span></div>'
            '<div class="nm">%s</div><div class="tr" style="background:%s">%s</div><div class="sub">%s</div></div>'
            % (it["image"], it["no"], it["id"], esc(it["name"]), TIER_COLOUR[it["tier"]], it["tierName"],
               ("era-neutral" if it["source"] == "neutral" else "era grade " + it["eraGrade"])))
    html = (
        '<!doctype html><meta charset="utf-8"><style>'
        "body{margin:0;background:#1e1f22;color:#e6e6e6;font:14px Segoe UI,Arial,sans-serif}"
        "h1{margin:0;padding:14px 18px;font-size:22px;background:#2b2d31;border-bottom:2px solid #444}"
        "h1 small{font-size:14px;color:#aaa;margin-left:12px}"
        ".g{display:grid;grid-template-columns:repeat(%d,1fr);gap:6px;padding:10px}"
        ".c{background:#2b2d31;border:1px solid #3a3c41;border-radius:4px;height:222px;display:flex;flex-direction:column;align-items:center;padding:4px;overflow:hidden}"
        ".im{height:136px;width:100%%;display:flex;align-items:center;justify-content:center;background:#46484d;border-radius:3px}"
        ".im img{max-width:96%%;max-height:132px;image-rendering:pixelated}"
        ".no{font:12px Consolas,monospace;color:#ffe27a;margin-top:5px}.id{color:#b9b9b9}"
        ".nm{font-size:12px;text-align:center;line-height:1.15;margin-top:2px;height:28px;overflow:hidden}"
        ".tr{font-size:10px;color:#fff;border-radius:8px;padding:1px 9px;margin-top:3px}"
        ".sub{font-size:9px;color:#9aa0a6;margin-top:2px}"
        "</style><h1>%s <small>%s</small></h1><div class=\"g\">%s</div>" % (cols, esc(title), esc(sub), "".join(cards)))
    with open(out_html, "w", encoding="utf-8") as f:
        f.write(html)
    return 80 + ((len(items) + cols - 1) // cols) * 232 + 70


def build(cands, shoot_sheets=True):
    items, full, colls = load_selection(cands)
    strict_alternates(items, cands)
    os.makedirs(SINK, exist_ok=True)
    unassigned = [it["id"] for it in items if not it["collection"]]
    if unassigned:
        print("NOT IN A COLLECTION:", unassigned)
    stray = [rid for ids in colls.values() for rid in ids if rid not in {it["id"] for it in items}]
    if stray:
        print("COLLECTION ENTRIES NOT PICKED:", stray)
    with open(os.path.join(SINK, "selection.json"), "w", encoding="utf-8") as f:
        json.dump({"schema": "uo-rekindled-gold-sink-selection/1", "count": len(items), "tiers": TIER_NAMES, "tierUnits": TIER_UNITS,
                   "basePrice": BASE_PRICE, "priceCap": PRICE_CAP, "wings": {w: WINGS[w][0] for w in WINGS}, "items": items}, f, indent=1, ensure_ascii=False)
        f.write("\n")
    # pricing worksheet: price left blank on purpose
    with open(os.path.join(SINK, "Gold-Sink-Items.csv"), "w", encoding="utf-8", newline="") as f:
        f.write("no,catalogId,name,wing,tier,tierName,coolness,positionInTier,tierUnits,illustrativePriceAt2000,price,soldAt,source,eraGrade,tiles,pixelHeight,collection\n")
        for it in items:
            f.write('%d,%s,"%s",%s,%d,%s,%d,%.3f,%s,%d,,%s,%s,%s,%d,%d,"%s"\n' % (
                it["no"], it["id"], it["name"].replace('"', ""), WINGS[it["wing"]][1].upper(), it["tier"], it["tierName"], it["coolness"],
                it["positionInTier"], TIER_UNITS[it["tier"]], it["price"], it["soldAt"], it["source"], it["eraGrade"], it["tiles"], it["pixelHeight"], it["collection"] or ""))
    # sheets
    pages = [("Everything: the 100 decorations", "ordered by rarity, then wing", items, "overview", 10)]
    for w in WINGS:
        grp = [it for it in items if it["wing"] == w]
        pages.append((WINGS[w][0], "%d decorations" % len(grp), grp, "wing-" + w, 6))
    for t in TIER_NAMES:
        grp = [it for it in items if it["tier"] == t]
        pages.append(("Tier %d: %s" % (t, TIER_NAMES[t]), "%d decorations" % len(grp), grp, "tier-%d" % t, 6 if len(grp) > 6 else max(len(grp), 1)))
    for title, sub, grp, name, cols in pages:
        html = os.path.join(SINK, name + ".html")
        height = sheet_page(title, sub, grp, html, cols)
        if shoot_sheets:
            catalog.shoot(html, os.path.join(SINK, name + ".png"), 232 * cols + 30, height)
    for w in os.listdir(SINK):
        if w.startswith("wing-") and w.rsplit(".", 1)[0][5:] not in WINGS:
            os.remove(os.path.join(SINK, w))
    for it in items:
        flags = curation_flags(full[it["id"]])
        if flags or not (it["category"] in FURNISHING_CATS or it["id"] in FURNISHING_EXTRA):
            print("CURATION CHECK:", it["id"], it["name"], flags or "category %s is not a furnishing category" % it["category"])
    write_sandbox(items)
    bt = {t: sum(1 for it in items if it["tier"] == t and it["soldAt"] == "britain") for t in TIER_NAMES}
    print("Britain Furnisher sells", sum(bt.values()), "of", len(items), "pieces by rarity", bt, "| dearest piece", max(it["price"] for it in items))
    print("built selection of", len(items), "items;", sum(it["source"] == "neutral" for it in items), "era-neutral;",
          "tiers", {t: sum(1 for it in items if it["tier"] == t) for t in TIER_NAMES})


def write_sandbox(items):
    """gold-sink/pricing-sandbox.html: the owner's price-curve playground (data/pricing-sandbox.template.html with the selection embedded)."""
    keep = ("no", "id", "name", "wing", "tier", "tierName", "positionInTier", "image", "collection", "soldAt")
    data = {"tiers": {str(t): n for t, n in TIER_NAMES.items()}, "wings": {w: WINGS[w][0] for w in WINGS},
            "base": BASE_PRICE, "cap": PRICE_CAP, "units": {str(t): u for t, u in TIER_UNITS.items()},
            "items": [{k: it[k] for k in keep} for it in items]}
    with open(os.path.join(HERE, "data", "pricing-sandbox.template.html"), encoding="utf-8") as f:
        text = f.read().replace("__DATA__", json.dumps(data, ensure_ascii=False))
    with open(os.path.join(SINK, "pricing-sandbox.html"), "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def showroom():
    """Plans real-client gallery pages (GS-<WING>-NN) with the 100 items; labels are the sink numbers."""
    import galleries
    items, full, _ = load_selection()
    total = 0
    for w in WINGS:
        entries = [full[it["id"]] for it in items if it["wing"] == w]
        nos = {it["id"]: it["no"] for it in items}
        names = galleries.write_layouts(w, entries, label_fn=lambda e: "%03d" % nos[e["id"]], prefix="GS-")
        total += len(names)
        print("%s: %d items -> %s" % (w, len(entries), ", ".join(names)))
    print("pages:", total)


if __name__ == "__main__":
    main(sys.argv)
