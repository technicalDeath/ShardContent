"""Cosmetic reward catalog: validate, preview and build.

Source of truth: ShardContent/docs/cosmetic-rewards/catalog/<CAT>.json  (a JSON array of entries, one file per category).

  python catalog.py validate [CAT ...]             -> schema + art checks (exit 1 on errors); warns on duplicate graphics
  python catalog.py sheet CAT [out.png]            -> contact sheet of a category's entries, numbered like the listing it prints
  python catalog.py build                          -> (maintainers) assign ids, write images, sheets, markdown and JSON

Add --neutral to any command to work on the era-neutral section instead (catalog-neutral/<CAT>.json, ids CN-<CAT>-<NNN>): rewards whose
art or object falls outside the main catalog's April-2000 era grading but whose theme is era neutral.

Entry fields (see ShardContent/docs/cosmetic-rewards/README.md for the meaning of each):
  slug, name, category, subcategory, parts[{id,dx,dy,dz,hue?}], hue, placement, facing, altFacings[], footprint,
  tier, tags[], blurb, era{grade,note,sources[]}, impl, implNote, variantOf, id (assigned by build, never by hand)
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import uoart  # noqa: E402

DOCS = os.environ.get("COSMETIC_DOCS_DIR") or os.path.normpath(os.path.join(HERE, "..", "..", "docs", "cosmetic-rewards"))
CATALOG_DIR = os.environ.get("COSMETIC_CATALOG_DIR") or os.path.join(DOCS, "catalog")

CATEGORIES = {
    "FIG": "Monster Figurines",
    "TRO": "Trophies, Mounted Heads and Pelts",
    "CUR": "Curios and Rarities",
    "STA": "Statues and Busts",
    "GRV": "Graveyard and Funerary",
    "REL": "Shrines, Altars and Sacred Symbols",
    "FLO": "Flora and Gardens",
    "WTR": "Water Features",
    "ANM": "Animal Husbandry and Beasts' Furnishings",
    "FRN": "Seating and Beds",
    "TBL": "Tables, Cabinets and Shelving",
    "RUG": "Rugs and Floor Coverings",
    "WLH": "Wall Hangings",
    "HER": "Heraldry, Banners and Flags",
    "TWN": "Town Fixtures and Signs",
    "LGT": "Lighting and Fire",
    "SEA": "Seasonal and Festive",
    "MUS": "Instruments and Performance",
    "NAU": "Nautical and Fishing",
    "CMP": "Camp and Wilderness",
    "TRS": "Treasure and Hoards",
    "ARM": "Martial Displays",
    "CRF": "Workshop and Trade Tools",
    "GAM": "Games and Pastimes",
    "LIB": "Library and Study",
    "ALC": "Alchemy and Arcana",
    "FOO": "Food and Drink Displays",
    "DNG": "Dungeon Dressing and Lairs",
    "ARC": "Architecture and Masonry",
}
CATEGORIES_ERA = dict(CATEGORIES)
CATEGORIES_NEUTRAL = dict(CATEGORIES, NEC="Necromantic Curiosities")
ERA_DIR = CATALOG_DIR
NEUTRAL_DIR = os.environ.get("COSMETIC_NEUTRAL_DIR") or os.path.join(DOCS, "catalog-neutral")
MODE = "era"          # "era" or "neutral"
ID_PREFIX = "CR"
PAGE_PREFIX = ""      # prefix of in-game gallery page names (CN- for the neutral section)
SHEET_PREFIX = ""
OUT_MD = "Cosmetic-Reward-Catalog.md"
OUT_JSON = "cosmetic-rewards.json"


def set_mode(mode):
    """Switch every function in this module (and modules that call catalog.*) to the era or the era-neutral catalog."""
    global MODE, CATEGORIES, CATALOG_DIR, ID_PREFIX, PAGE_PREFIX, SHEET_PREFIX, OUT_MD, OUT_JSON
    MODE = mode
    if mode == "neutral":
        CATEGORIES, CATALOG_DIR, ID_PREFIX = CATEGORIES_NEUTRAL, NEUTRAL_DIR, "CN"
        PAGE_PREFIX, SHEET_PREFIX = "CN-", "neutral-"
        OUT_MD, OUT_JSON = "Era-Neutral-Reward-Catalog.md", "cosmetic-rewards-neutral.json"
    else:
        CATEGORIES, CATALOG_DIR, ID_PREFIX = CATEGORIES_ERA, ERA_DIR, "CR"
        PAGE_PREFIX, SHEET_PREFIX = "", ""
        OUT_MD, OUT_JSON = "Cosmetic-Reward-Catalog.md", "cosmetic-rewards.json"


# Era-neutral section: art may come from any id; the theme must not belong to a later expansion. (Elven pieces are allowed: the shard has cosmetic
# Elves, owner ruling 2026-10-08.) Tile names containing these words are
# refused unless the entry's era.themeOverride explains why the object is nevertheless generic.
NEUTRAL_BLOCKED = re.compile(
    r"\b(?:samurai|ninja|bushido|ninjitsu|shoji|tatami|goza|katana|kama|nunchaku|daisho|no-dachi|wakizashi|tessen|lajatang|bokuto|tetsubo|yumi|kimono|kappa|oni|kitsune|ronin|yomotsu|rai-ju|tokuno|gargoyle|gargish|spellweav\w*|mysticism|imbuing|ter mur|eodon|sidhe|minotaur|satyr|centaur|dryad|fey|myrmidex|juka|meer|exodus|chaos dragoon|champion|doom|faction|virtue stone|bulletin|ethereal|treasure of|heritage|mount statue|pet statue)\b",
    re.I)
NEUTRAL_ART_ERAS = ["T2A-or-earlier", "UOR-LBR", "AoS", "SE", "ML", "SA", "HS", "KR", "unknown"]
TIERS = ["common", "uncommon", "scarce", "rare", "extremely-rare"]
PLACEMENTS = ["floor", "floor-multi", "surface", "wall", "wall-north", "wall-west", "ceiling", "ground-cover", "any"]
FACINGS = ["none", "south", "east", "north", "west", "both"]
IMPLS = ["static", "stock-class", "addon", "crafted-variant", "custom"]
GRADES = ["A", "B", "C"]
TAG_RE = re.compile(r"^[a-z0-9]+([-:][a-z0-9]+)*$")
SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


# Era fences from the era evidence pack (docs/cosmetic-rewards/Era-Evidence.md, section 5b): graphics in these blocks are later
# than April 2000 (Publish 5, "the Renaissance publish") and are rejected outright.
HARD_FENCES = [
    (0x2328, 0x2378, "2003 winter-gift art (snowman, gift box, wreath, poinsettia, mistletoe, topiary, holiday candle)"),
    (0x2440, 0x24FF, "Samurai Empire / Tokuno garden art"),
    (0x2554, 0x2635, "second creature and weapon icon set (SE weapons, LBR and AoS creatures)"),
    (0x2700, 0x28FF, "Samurai Empire (2004)"),
    (0x2D00, 0x31FF, "Mondain's Legacy block (elven and arcane items)"),
    (0x210C, 0x210D, "Elf male/female icons (Mondain's Legacy)"),
    (0x2BD9, 0x2BDC, "2003 holiday stockings"),
]
# Blocks that mix old art with later fills: a dated reason is needed. Grade B is only accepted for a graphic the original
# Britannia map uses at least MIXED_MIN_STATICS times; otherwise use grade C (with a note) or grade A with sources.
MIXED_RANGES = [
    (0x2000, 0x20C7), (0x2138, 0x2327), (0x2379, 0x2439), (0x2500, 0x2553),
    (0x2636, 0x26FF), (0x2900, 0x2CFF), (0x3200, 0x3FFF),
]
MIXED_MIN_STATICS = 50
_statics = None


def statics_count(item_id):
    global _statics
    if _statics is None:
        path = os.path.join(HERE, "data", "statics_usage.json")
        _statics = json.load(open(path)) if os.path.exists(path) else {}
    return _statics.get(str(item_id), 0)


_species = None


def species_in_game(tag_value):
    """True when the creature named by a `monster:<value>` tag is spawned by the shard's world (data/species_in_game.json, made by
    speciesingame.py): the value's words appear in order inside the kebab-case name of some spawned creature."""
    global _species
    if _species is None:
        path = os.path.join(HERE, "data", "species_in_game.json")
        _species = [v["kebab"].split("-") for v in json.load(open(path))["creatures"].values()] if os.path.exists(path) else None
    if _species is None:
        return True
    words = tag_value.split("-")
    n = len(words)
    for cw in _species:
        for i in range(len(cw) - n + 1):
            if cw[i:i + n] == words:
                return True
    return False


def hard_fence(item_id):
    for lo, hi, why in HARD_FENCES:
        if lo <= item_id <= hi:
            return why
    return None


def in_mixed_range(item_id):
    return any(lo <= item_id <= hi for lo, hi in MIXED_RANGES)


def num(v):
    return int(v, 0) if isinstance(v, str) else int(v)


def entry_parts(e, alt=None):
    parts = alt if alt is not None else e["parts"]
    out = []
    for p in parts:
        hue = p.get("hue", e.get("hue", 0))
        out.append((num(p["id"]), p.get("dx", 0), p.get("dy", 0), p.get("dz", 0), num(hue)))
    return out


def foliage_flag(item_id):
    return bool(uoart.tiles()[item_id].flags & 0x20000)


def foliage_summary(e):
    """Felucca runs the Desolation season: the client hides every tile flagged Foliage (leaf canopies, many bushes).
    -> (total parts, hidden parts)."""
    parts = entry_parts(e)
    return len(parts), sum(1 for p in parts if foliage_flag(p[0]))


def render_entry(e, alt=None, hide_foliage=False):
    parts = entry_parts(e, alt)
    if hide_foliage:
        parts = [p for p in parts if not foliage_flag(p[0])]
    return uoart.compose(uoart.parts_sorted(parts)) if parts else None


def load_category(cat):
    path = os.path.join(CATALOG_DIR, cat + ".json")
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_era_entries():
    """The main (era) catalog's live entries, read straight from its folder (used to keep the neutral section free of duplicates)."""
    out = []
    for cat in CATEGORIES_ERA:
        path = os.path.join(ERA_DIR, cat + ".json")
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                out.extend(e for e in json.load(f) if not e.get("retired"))
    return out


def load_all():
    out = []
    for cat in CATEGORIES:
        out.extend(load_category(cat))
    return out


def validate(entries, cat=None):
    errors, warnings = [], []
    seen_slug = {}
    seen_name = {}
    tiles = uoart.tiles()
    for i, e in enumerate(entries):
        where = "%s #%d (%s)" % (e.get("category", cat), i + 1, e.get("slug", "?"))

        def err(m):
            errors.append("%s: %s" % (where, m))

        def warn(m):
            warnings.append("%s: %s" % (where, m))

        for k in ("slug", "name", "category", "subcategory", "parts", "placement", "tier", "tags", "blurb", "era", "impl"):
            if k not in e:
                err("missing field %r" % k)
        if errors and errors[-1].startswith(where) and "missing field" in errors[-1]:
            continue
        if not SLUG_RE.match(e["slug"]):
            err("slug must be kebab-case")
        if e["slug"] in seen_slug:
            err("duplicate slug (also #%d)" % seen_slug[e["slug"]])
        seen_slug[e["slug"]] = i + 1
        nkey = e["name"].lower()
        if nkey in seen_name:
            warn("same name as #%d" % seen_name[nkey])
        seen_name[nkey] = i + 1
        if e["category"] not in CATEGORIES:
            err("unknown category %r" % e["category"])
        elif cat and e["category"] != cat:
            err("category %s does not match file %s" % (e["category"], cat))
        if e["tier"] not in TIERS:
            err("tier must be one of %s" % TIERS)
        if e["placement"] not in PLACEMENTS:
            err("placement must be one of %s" % PLACEMENTS)
        if e.get("facing", "none") not in FACINGS:
            err("facing must be one of %s" % FACINGS)
        if e["impl"] not in IMPLS:
            err("impl must be one of %s" % IMPLS)
        if not isinstance(e["tags"], list) or not e["tags"]:
            err("tags must be a non-empty list")
        else:
            for t in e["tags"]:
                if not TAG_RE.match(t):
                    err("bad tag %r (lowercase, hyphens, optional kind:value)" % t)
        if e.get("category") == "FIG" and isinstance(e["tags"], list):
            sp = [t.split(":", 1)[1] for t in e["tags"] if t.startswith("monster:")]
            if not sp:
                err("a figurine needs a monster:<species> tag naming a creature that is present in our game")
            for v in sp:
                if not species_in_game(v):
                    err("figurine species %r is not spawned in our game (Species-In-Game.md); owner rule: a figurine is fine "
                        "only if its creature is present in our game" % v)
        if not (10 <= len(e["blurb"]) <= 200):
            err("blurb should be 10-200 characters")
        era = e["era"]
        if MODE == "neutral":
            if not isinstance(era, dict) or era.get("grade") != "N" or not era.get("note"):
                err('era-neutral entries need era {"grade": "N", "note": why the object is era neutral, "artEra": ...}')
            elif era.get("artEra") not in NEUTRAL_ART_ERAS:
                err("era.artEra must be one of %s (when the art first appeared, best knowledge)" % NEUTRAL_ART_ERAS)
        elif not isinstance(era, dict) or era.get("grade") not in GRADES or not era.get("note"):
            err("era needs grade A|B|C and a note")
        elif era["grade"] == "A" and not era.get("sources"):
            err("era grade A needs sources[]")
        hue = e.get("hue", 0)
        if not (0 <= num(hue) <= 3000):
            err("hue out of range")
        if not e["parts"]:
            err("parts is empty")
        sets = [("parts", e["parts"])] + [("altFacings[%s]" % a.get("facing"), a["parts"]) for a in e.get("altFacings", [])]
        for label, plist in sets:
            for p in plist:
                try:
                    pid = num(p["id"])
                except Exception:
                    err("%s: bad part id %r" % (label, p))
                    continue
                if MODE == "neutral":
                    if not (0 <= pid < 0x10000):
                        err("%s: part id 0x%X is outside 0x0000-0xFFFF" % (label, pid))
                        continue
                elif not (0 <= pid < 0x4000):
                    err("%s: part id 0x%X is outside the era range 0x0000-0x3FFF" % (label, pid))
                    continue
                if not uoart.art().static(pid):
                    err("%s: part id 0x%04X has no art" % (label, pid))
                if MODE == "neutral":
                    nm = tiles[pid].name if pid < len(tiles) else ""
                    if e.get("category") != "FIG" and NEUTRAL_BLOCKED.search(nm) and not (isinstance(era, dict) and era.get("themeOverride")):
                        err("%s: tile 0x%04X is named %r, which belongs to a later expansion's theme; drop it or explain "
                            "in era.themeOverride why this graphic is generic" % (label, pid, nm))
                    why = None
                else:
                    why = hard_fence(pid)
                if MODE == "neutral":
                    pass
                elif why:
                    err("%s: part id 0x%04X is fenced out as post-UOR (%s)" % (label, pid, why))
                elif in_mixed_range(pid):
                    grade = era.get("grade") if isinstance(era, dict) else None
                    if grade == "B" and statics_count(pid) < MIXED_MIN_STATICS:
                        err("%s: part id 0x%04X is in a mixed-era block and the Britannia map uses it only %d times; "
                            "grade it C (or A with dated sources)" % (label, pid, statics_count(pid)))
                if "hue" in p and not (0 <= num(p["hue"]) <= 3000):
                    err("%s: part hue out of range" % label)
        try:
            if render_entry(e) is None:
                err("renders to nothing")
        except Exception as ex:  # noqa: BLE001
            err("render failed: %s" % ex)
        if e.get("variantOf") and e["variantOf"] not in {x["slug"] for x in entries}:
            warn("variantOf %r is not a slug in this file (fine if it lives in another category)" % e["variantOf"])
        # names that look like they belong to a different thing than the graphic
        first = num(e["parts"][0]["id"]) if e.get("parts") else -1
        if 0 <= first < len(tiles) and not tiles[first].name:
            warn("first graphic 0x%04X has an empty tiledata name (check it is a real item and not a blank/placeholder)" % first)
    return errors, warnings


def cross_duplicates(entries):
    """Entries whose first part graphic + hue collide, across the whole catalog."""
    seen = {}
    dups = []
    for e in entries:
        key = tuple(sorted((num(p["id"]), p.get("dx", 0), p.get("dy", 0), p.get("dz", 0), num(p.get("hue", e.get("hue", 0))))
                           for p in e["parts"]))
        if key in seen:
            dups.append((seen[key], e))
        else:
            seen[key] = e
    return dups


def fit(pix, w, h, cw, ch):
    """Nearest-neighbour fit of a pixel block into cw x ch (up to 2x, down by decimation)."""
    s = 1
    if w * 2 <= cw and h * 2 <= ch:
        s = 2
    if s == 2:
        return uoart.scaled(pix, 2), w * 2, h * 2
    k = 1
    while w // k > cw or h // k > ch:
        k += 1
    if k == 1:
        return pix, w, h
    out = [row[::k] for row in pix[::k]]
    return out, len(out[0]), len(out)


def sheet_entries(out, entries, cols=8, cell=120, bg=(70, 70, 70), numbered=True):
    cells = []
    for e in entries:
        r = render_entry(e)
        cells.append(r)
    ch = cell + 14
    rows_n = (len(cells) + cols - 1) // cols
    W, H = cols * cell, rows_n * ch
    bgc = tuple(bg) + (255,)
    canvas = [[bgc] * W for _ in range(H)]
    for n, r in enumerate(cells):
        cx, cy = (n % cols) * cell, (n // cols) * ch
        for x in range(cx, cx + cell):
            canvas[cy][x] = (40, 40, 40, 255)
        for y in range(cy, cy + ch):
            canvas[y][cx] = (40, 40, 40, 255)
        uoart.label(canvas, cx + 3, cy + 3, "#%d" % (n + 1) if numbered else "", scale=2)
        if not r:
            continue
        w, h, pix = r
        pix, w, h = fit(pix, w, h, cell - 6, cell - 6)
        px0 = cx + (cell - w) // 2
        py0 = cy + 14 + (cell - h) // 2
        for y, row in enumerate(pix):
            for x, p in enumerate(row):
                if p[3]:
                    canvas[py0 + y][px0 + x] = p
    uoart.write_png(out, W, H, canvas)
    return W, H


IMAGES = os.path.join(DOCS, "images")
SHEETS = os.path.join(DOCS, "sheets")
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
TIER_COLOUR = {"common": "#8a8f98", "uncommon": "#3fa34d", "scarce": "#3a7bd5", "rare": "#a24bd6", "extremely-rare": "#e0a020"}


def pool_owners():
    """id -> pool name, from pools/*.json (suggested allocations; see Reward-Pools.md)."""
    owners = {}
    folder = os.path.join(DOCS, "pools")
    if os.path.isdir(folder):
        for name in os.listdir(folder):
            if name.endswith(".json"):
                with open(os.path.join(folder, name), encoding="utf-8") as f:
                    data = json.load(f)
                for en in data.get("entries", []):
                    owners[en["id"]] = data["pool"]
    return owners


def category_path(cat):
    return os.path.join(CATALOG_DIR, cat + ".json")


def assign_ids(cat, entries):
    """Keeps any id already written; new entries get the next number. Returns True if anything changed."""
    used = [int(e["id"].rsplit("-", 1)[1]) for e in entries if e.get("id")]
    nxt = max(used + [0]) + 1
    changed = False
    for e in entries:
        if not e.get("id"):
            e["id"] = "%s-%s-%03d" % (ID_PREFIX, cat, nxt)
            nxt += 1
            changed = True
    return changed


def write_item_png(e, hide_foliage=False):
    r = render_entry(e, hide_foliage=hide_foliage)
    if r is None:
        return None, None
    w, h, pix = r
    scale = 2 if w * 2 <= 640 and h * 2 <= 640 else 1
    pix = uoart.scaled(pix, scale)
    pad = 4
    blank = (0, 0, 0, 0)
    canvas = [[blank] * (w * scale + 2 * pad) for _ in range(pad)]
    for row in pix:
        canvas.append([blank] * pad + row + [blank] * pad)
    canvas += [[blank] * (w * scale + 2 * pad) for _ in range(pad)]
    folder = os.path.join(IMAGES, e["category"])
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, e["id"] + ("-fel" if hide_foliage else "") + ".png")
    uoart.write_png(path, w * scale + 2 * pad, h * scale + 2 * pad, canvas)
    return path, (w, h)


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def sheet_html(cat, entries, path, cols=8, fel=None):
    fel = fel or {}
    cards = []
    for e in entries:
        cards.append(
            '<div class="c"><div class="im"><img src="../images/%s/%s.png"></div><div class="id">%s</div><div class="nm">%s</div>'
            '<div class="tr" style="background:%s">%s</div>%s</div>'
            % (e["category"], e["id"], e["id"], esc(e["name"]), TIER_COLOUR[e["tier"]], e["tier"],
               '<div class="fo">leaves hidden in Felucca</div>' if e["id"] in fel else ""))
    html = (
        '<!doctype html><meta charset="utf-8"><style>'
        "body{margin:0;background:#1e1f22;color:#e6e6e6;font:14px Segoe UI,Arial,sans-serif}"
        "h1{margin:0;padding:14px 18px;font-size:22px;background:#2b2d31;border-bottom:2px solid #444}"
        "h1 small{font-size:14px;color:#aaa;margin-left:12px}"
        ".g{display:grid;grid-template-columns:repeat(%d,1fr);gap:6px;padding:10px}"
        ".c{background:#2b2d31;border:1px solid #3a3c41;border-radius:4px;height:206px;display:flex;flex-direction:column;align-items:center;padding:4px;overflow:hidden}"
        ".im{height:130px;width:100%%;display:flex;align-items:center;justify-content:center;background:#46484d;border-radius:3px}"
        ".im img{max-width:96%%;max-height:126px;image-rendering:pixelated}"
        ".id{font:12px Consolas,monospace;color:#ffe27a;margin-top:5px}"
        ".nm{font-size:12px;text-align:center;line-height:1.15;margin-top:2px;height:28px;overflow:hidden}"
        ".tr{font-size:10px;color:#fff;border-radius:8px;padding:1px 8px;margin-top:3px}"
        ".fo{font-size:9px;color:#d9a35c;margin-top:2px}"
        "</style><h1>%s <small>%s &middot; %d rewards</small></h1><div class=\"g\">%s</div>"
        % (cols, esc(CATEGORIES[cat]), cat, len(entries), "".join(cards)))
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    return 80 + ((len(entries) + cols - 1) // cols) * 222 + 24


def shoot(html_path, png_path, width, height):
    import subprocess
    import tempfile
    import time
    url = "file:///" + html_path.replace("\\", "/")
    if os.path.exists(png_path):
        os.remove(png_path)
    profile = os.path.join(tempfile.gettempdir(), "cosmetic-catalog-edge")
    subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1",
                    "--user-data-dir=" + profile, "--screenshot=" + png_path, "--window-size=%d,%d" % (width, height), url],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
    for _ in range(20):
        if os.path.exists(png_path) and os.path.getsize(png_path) > 0:
            return
        time.sleep(0.5)
    raise SystemExit("Edge did not produce " + png_path)


def graphic_text(e):
    ids = []
    for p in e["parts"]:
        t = "0x%04X" % num(p["id"])
        if t not in ids:
            ids.append(t)
    text = ", ".join(ids[:3]) + (" +%d" % (len(ids) - 3) if len(ids) > 3 else "")
    hue = num(e.get("hue", 0))
    return text + (" hue %d" % hue if hue else "")


def build(shoot_sheets=True):
    all_entries = []
    for cat in CATEGORIES:
        entries = load_category(cat)
        if not entries:
            continue
        errors, _ = validate(entries, cat)
        if errors:
            print("\n".join(errors))
            raise SystemExit("fix validation errors first")
        if assign_ids(cat, entries):
            with open(category_path(cat), "w", encoding="utf-8") as f:
                json.dump(entries, f, indent=1, ensure_ascii=False)
                f.write("\n")
        all_entries.extend(entries)
    live = [e for e in all_entries if not e.get("retired")]
    dups = cross_duplicates(live + (load_era_entries() if MODE == "neutral" else []))
    for a, b in dups:
        print("DUPLICATE graphic: %s and %s" % (a.get("id", a["slug"]), b.get("id", b["slug"])))
    os.makedirs(SHEETS, exist_ok=True)
    sizes = {}
    fel = {}
    for e in live:
        path, sz = write_item_png(e)
        sizes[e["id"]] = sz
        tot, hid = foliage_summary(e)
        if hid:
            fel[e["id"]] = (tot, hid)
            if hid < tot:
                write_item_png(e, hide_foliage=True)
    print("wrote %d item images (%d with foliage tiles the Felucca client hides)" % (len(live), len(fel)))
    by_cat = {c: [e for e in live if e["category"] == c] for c in CATEGORIES}
    for cat, entries in by_cat.items():
        if not entries:
            continue
        html = os.path.join(SHEETS, SHEET_PREFIX + cat + ".html")
        height = sheet_html(cat, entries, html, fel=fel)
        if shoot_sheets:
            shoot(html, os.path.join(SHEETS, SHEET_PREFIX + cat + ".png"), 1700, height)
    write_json(live, sizes, fel)
    write_markdown(live, by_cat, sizes, fel)
    print("built", len(live), "rewards in", len([c for c in by_cat if by_cat[c]]), "categories")


def estimate_art_era(e):
    """Coarse estimate of when the art first appeared, from the id blocks in Era-Evidence.md (used when a curator wrote 'unknown').
    The latest block any part falls into wins. A rule of thumb, not a dated fact."""
    best = 0
    label = "mixed or unknown (low id block: later expansions back-filled empty slots)"
    blocks = [(0x4000, 0xFFFF, "SA-or-later (id 0x4000 and up)", 6), (0x2D00, 0x31FF, "ML block (2005)", 5),
              (0x2700, 0x2CFF, "SE-or-later block (2004)", 4), (0x2328, 0x26FF, "AoS-or-later block (2003)", 3),
              (0x3200, 0x3FFF, "ML-or-later block", 5)]
    for p in e["parts"]:
        pid = num(p["id"])
        for lo, hi, text, rank in blocks:
            if lo <= pid <= hi and rank > best:
                best, label = rank, text
    return label


def write_json(live, sizes, fel):
    import datetime
    owners = pool_owners() if MODE == "era" else {}
    rewards = []
    for e in live:
        r = dict(e)
        r["eraClass"] = "neutral" if MODE == "neutral" else "era"
        r["image"] = "images/%s/%s.png" % (e["category"], e["id"])
        r["suggestedPool"] = owners.get(e["id"])
        if MODE == "neutral":
            r["artEraEstimate"] = estimate_art_era(e)
        r["graphics"] = [{"id": "0x%04X" % num(p["id"]), "dx": p.get("dx", 0), "dy": p.get("dy", 0), "dz": p.get("dz", 0),
                          "hue": num(p.get("hue", e.get("hue", 0)))} for p in e["parts"]]
        r["pixelSize"] = {"width": sizes[e["id"]][0], "height": sizes[e["id"]][1]}
        if e["id"] in fel:
            tot, hid = fel[e["id"]]
            r["felucca"] = {"seasonHidesFoliage": True, "totalTiles": tot, "hiddenTiles": hid, "visibleInFelucca": hid < tot,
                            "image": ("images/%s/%s-fel.png" % (e["category"], e["id"])) if hid < tot else None}
        else:
            r["felucca"] = {"seasonHidesFoliage": False}
        rewards.append(r)
    doc = {
        "schema": "uo-rekindled-cosmetic-rewards-neutral/1" if MODE == "neutral" else "uo-rekindled-cosmetic-rewards/1",
        "eraClass": "neutral" if MODE == "neutral" else "era",
        "generated": datetime.date.today().isoformat(),
        "count": len(rewards),
        "categories": {c: CATEGORIES[c] for c in CATEGORIES},
        "tiers": TIERS,
        "rewards": rewards,
    }
    with open(os.path.join(DOCS, OUT_JSON), "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=1, ensure_ascii=False)
        f.write("\n")


def write_markdown(live, by_cat, sizes, fel):
    import datetime
    owners = pool_owners() if MODE == "era" else {}
    tags = {}
    for e in live:
        for t in e["tags"]:
            tags.setdefault(t, []).append(e["id"])
    lines = []
    out = lines.append
    if MODE == "neutral":
        out("# Era-Neutral Reward Catalog")
        out("")
        out("*Generated %s by `ShardContent/tools/cosmetic-catalog/catalog.py build --neutral`. Edit the category files in `catalog-neutral/`, not this page.*" % datetime.date.today().isoformat())
        out("")
        out("**%d rewards in %d categories.** Machine-readable copy: [`%s`](%s). Every reward has a permanent id `CN-<CAT>-<NNN>`; "
            "the `CN-` prefix marks them as era-neutral so a system that must stay strictly inside April 2000 can ignore them by prefix." %
            (len(live), len([c for c in by_cat if by_cat[c]]), OUT_JSON, OUT_JSON))
        out("")
        out("> **What era neutral means here.** These rewards fall *outside* the main catalog's era grading (`Cosmetic-Reward-Catalog.md`): their art, or the object itself, "
            "first appeared after April 2000 (or was never documented for the era). They are kept because the *thing* is generic: nothing in its look or lore ties it to a "
            "later expansion, creature, race, skill or event, so it would not seem out of place in 2000 Britannia (a jack-o'-lantern, a weapon rack, a ship's wheel, a mirror, "
            "or necromancy-flavoured props such as skulls and jars of eyeballs). Items that *do* belong to later content (samurai or ninja pieces, elven or gargoyle furnishings, "
            "figurines of creatures that did not exist, gear for skills the era lacks) are deliberately not here. Each entry's era note says why it is neutral and when its art first appeared (`artEra`).")
        out("")
    else:
        out("# Cosmetic Reward Catalog")
        out("")
        out("*Generated %s by `ShardContent/tools/cosmetic-catalog/catalog.py build`. Edit the category files in `catalog/`, not this page.*" % datetime.date.today().isoformat())
        out("")
        out("**%d rewards in %d categories.** Machine-readable copy: [`cosmetic-rewards.json`](cosmetic-rewards.json). "
            "Every reward has a permanent id `CR-<CAT>-<NNN>`; other systems should refer to rewards by that id and nothing else. "
            "Rewards that fall outside the era grading but are era neutral are in [`Era-Neutral-Reward-Catalog.md`](Era-Neutral-Reward-Catalog.md) (ids `CN-...`)." %
            (len(live), len([c for c in by_cat if by_cat[c]])))
        out("")
    out("> **Felucca note.** Felucca runs the client's *Desolation* season, which hides every tile flagged *Foliage* (leaf canopies, many bushes). "
        "Entries that contain such tiles say so below and show an *as seen in Felucca* picture; the owner can change the map season if full leaves are wanted. "
        "The in-game gallery shots in `client-shots/` are taken in Felucca and show exactly what a player sees.")
    out("")
    out("## Category index")
    out("")
    out("| Code | Category | Rewards | Common | Uncommon | Scarce | Rare | Extremely rare |")
    out("| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |")
    for cat, entries in by_cat.items():
        if not entries:
            continue
        cnt = [sum(1 for e in entries if e["tier"] == t) for t in TIERS]
        out("| [%s](#%s) | %s | %d | %s |" % (cat, cat.lower(), CATEGORIES[cat], len(entries), " | ".join(str(c) for c in cnt)))
    out("| | **Total** | **%d** | %s |" % (len(live), " | ".join("**%d**" % sum(1 for e in live if e["tier"] == t) for t in TIERS)))
    out("")
    for cat, entries in by_cat.items():
        if not entries:
            continue
        out('<a id="%s"></a>' % cat.lower())
        out("## %s — %s" % (cat, CATEGORIES[cat]))
        out("")
        out("![%s](sheets/%s%s.png)" % (CATEGORIES[cat], SHEET_PREFIX, cat))
        out("")
        out("| Id | Picture | Name | Tier | Placement | Graphic | Tags | Era | Impl | Suggested pool |")
        out("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
        for e in entries:
            w, h = sizes[e["id"]]
            ph = min(64, h)
            note = ""
            if e["id"] in fel:
                tot, hid = fel[e["id"]]
                note = ("<br><sub>Felucca client hides all of this item (foliage tiles).</sub>" if hid == tot else
                        "<br><sub>Felucca client hides %d of %d tiles (leaves): <img src=\"images/%s/%s-fel.png\" height=\"%d\"></sub>" % (
                            hid, tot, cat, e["id"], ph))
            out("| `%s` | <img src=\"images/%s/%s.png\" height=\"%d\"> | **%s**<br><sub>%s</sub>%s | %s | %s | %s | %s | %s | %s | %s |" % (
                e["id"], cat, e["id"], ph, e["name"], e["blurb"].replace("|", "/"), note, e["tier"], e["placement"], graphic_text(e),
                ", ".join(e["tags"]), (e["era"]["grade"] + " (" + e["era"]["artEra"] + ")") if MODE == "neutral" else e["era"]["grade"],
                e["impl"], owners.get(e["id"], "")))
        out("")
    out("## Tag index")
    out("")
    for t in sorted(tags):
        out("- `%s` (%d): %s" % (t, len(tags[t]), ", ".join(tags[t][:60]) + (" ..." if len(tags[t]) > 60 else "")))
    out("")
    with open(os.path.join(DOCS, OUT_MD), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main(argv):
    if "--neutral" in argv:
        argv = [a for a in argv if a != "--neutral"]
        set_mode("neutral")
    if len(argv) < 2:
        print(__doc__)
        return 0
    cmd = argv[1]
    if cmd == "build":
        build(shoot_sheets="--no-sheets" not in argv)
        return 0
    if cmd == "validate":
        cats = argv[2:] or list(CATEGORIES)
        bad = False
        total = 0
        for cat in cats:
            entries = load_category(cat)
            if not entries:
                print("%s: (no file or empty)" % cat)
                continue
            errors, warnings = validate(entries, cat)
            total += len(entries)
            print("%s: %d entries, %d errors, %d warnings" % (cat, len(entries), len(errors), len(warnings)))
            for m in errors:
                print("  ERROR   " + m)
            for m in warnings:
                print("  warn    " + m)
            bad = bad or bool(errors)
        mine = [e for c in cats for e in load_category(c)]
        dups = cross_duplicates(mine + (load_era_entries() if MODE == "neutral" else []))
        for a, b in dups:
            print("  DUPLICATE graphic: %s/%s and %s/%s" % (a["category"], a["slug"], b["category"], b["slug"]))
        print("total entries checked:", total)
        return 1 if bad else 0
    if cmd == "sheet":
        cat = argv[2]
        out = argv[3] if len(argv) > 3 else os.path.join(os.environ.get("TEMP", "."), cat + "_sheet.png")
        entries = load_category(cat)
        W, H = sheet_entries(out, entries, cols=int(os.environ.get("COLS", "8")), cell=int(os.environ.get("CELL", "120")))
        print("wrote", out, W, H)
        for i, e in enumerate(entries):
            print("#%d  %-34s %s" % (i + 1, e["slug"], e["name"]))
        return 0
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
