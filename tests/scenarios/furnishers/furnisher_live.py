"""Live check of the Furnisher (docs/Furnisher-Evidence.md). Needs a disposable host running the build under test with featureFlags.furnishers
on and FurnisherProbe loaded, a staff session `admin`, and a fresh ordinary character with a Navrey session (the buyer).

    python -u furnisher_live.py shop  <buyer-session> <buyer-hex-serial>     cases 1 to 8: the shelf, never buying, a cart of one piece per rarity
    python -u furnisher_live.py place <buyer-session> <buyer-hex-serial>     cases 9 to 16: lockdown, deed placement, turning, wall hanging, chopping
    python -u furnisher_live.py snapshot <buyer-hex-serial> <name>           saves the probe report to work/furnisher/<name>.json
    python -u furnisher_live.py compare <buyer-hex-serial> <name>            case 17: the report now equals the snapshot (after a restart)

Prints one line per case, flushes as it goes, and exits non-zero on the first failed assertion.
"""

from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(WORKSPACE / ".claude" / "scripts"))

from navrey_session import connect  # noqa: E402
from staff_command import go_to, staff_target  # noqa: E402
from uo import Event  # noqa: E402

HOST = WORKSPACE / "work" / "hosts" / "furnisher"
CONFIG = json.loads((WORKSPACE / "ShardContent" / "data" / "configuration" / "furnishers.json").read_text(encoding="utf-8"))
PIECES = {p["name"]: p for p in CONFIG["pieces"]}
SHELF_LINE = re.compile(r"0x([0-9A-Fa-f]+)\s+(\d+)gp\s+x(\d+)\s+(.*)")
OUT = WORKSPACE / "work" / "furnisher"
# one piece of each rarity, covering both kinds and every placement
CART = ["Pale Pine Chair", "Plain Olive Rug", "Gold-and-Green Floral Tapestry", "Slate-Roofed Hearth", "Gray Brick Fireplace",
        "Marble Banquet Table", "Fieldstone Home Hearth", "Great Hall Carpet"]


def check(condition: bool, case: str, detail: str = "") -> None:
    print(f"{'PASS' if condition else 'FAIL'} {case}{': ' + detail if detail else ''}", flush=True)
    if not condition:
        sys.exit(1)


def log_lines(session: str) -> list:
    return (WORKSPACE / "work" / "navrey-sessions" / session / "cuolog").read_text(errors="replace").splitlines()


def report(admin, hex_serial: str) -> dict:
    path = HOST / f"furnisher-report-{hex_serial}.json"
    before = path.stat().st_mtime if path.exists() else 0
    admin.say(f"[TestOnlyFurnisherReport {hex_serial}")
    deadline = time.monotonic() + 8
    while time.monotonic() < deadline:
        if path.exists() and path.stat().st_mtime > before:
            time.sleep(0.2)
            return json.loads(path.read_text())
        time.sleep(0.2)
    check(False, "the probe wrote its report")
    return {}


def open_list(p, session: str, name: str, kind: str) -> bool:
    mark = len(log_lines(session))
    p.say(f"{name} {kind}")
    deadline = time.monotonic() + 8
    while time.monotonic() < deadline:
        if any(re.search(rf"\[SHOP\].*{kind} list", line, re.I) for line in log_lines(session)[mark:]):
            return True
        time.sleep(0.3)
    return False


def shelf(p, session: str, name: str) -> list:
    check(open_list(p, session, name, "buy"), "the buy list arrived")
    return [m.groups() for m in map(SHELF_LINE.search, p.call("shop", timeout=8)) if m]


def stand(admin, p, x: int, y: int, z: int) -> None:
    go_to(admin, p)
    staff_target(admin, f'[set Location "({x}, {y}, {z})"', p.state["charID"])
    time.sleep(1.5)


def sold_line(admin) -> str:
    admin.say("[FurnisherStatus")
    time.sleep(1.5)
    lines = [l for l in log_lines("admin") if "Sold since start" in l]
    return lines[-1] if lines else ""


def shop(session: str, hex_serial: str) -> None:
    p, admin = connect(session), connect("admin")
    base = report(admin, hex_serial)
    vendor = base["vendors"][0]
    name = vendor["name"]
    check(len(base["vendors"]) == 1 and base["displayItems"] == 229, "1 one Furnisher and 229 display items stand in the hall",
          f"{len(base['vendors'])} vendor, {base['displayItems']} items")
    check((vendor["x"], vendor["y"], vendor["z"]) == (1631, 1668, 15) and vendor["title"] == "the furnisher" and vendor["cantWalk"] and vendor["invulnerable"],
          "1 at the configured spot, titled, stationary and invulnerable", f"{name} {vendor['title']}")
    check(not vendor["activeBuyer"] and vendor["sellTypes"] == 0 and vendor["entries"] == 37, "2 buys nothing back, sells 37 pieces",
          f"buyer={vendor['activeBuyer']} sellTypes={vendor['sellTypes']} entries={vendor['entries']}")

    stand(admin, p, 1631, 1670, 15)
    admin.say(f"[TestOnlyFurnisherGold {hex_serial} 700000")
    time.sleep(1.5)

    entries = shelf(p, session, name)
    check(len(entries) == 37, "3 the buy list shows 37 pieces", f"{len(entries)} lines")
    by_name = {label.strip(): (serial, int(price), int(stock)) for serial, price, stock, label in entries}
    # Needs a Navrey built after 2026-10-10: before that `shop` kept a buy-list price in 16 bits (66,500 showed as 964).
    wrong = [(n, by_name.get(n), c["price"]) for n, c in PIECES.items()
             if n not in by_name or by_name[n][1] != c["price"] or by_name[n][2] != 999]
    check(not wrong, "3 every piece is listed at its configured price and 999 in stock", str(wrong[:3]))
    shelf_prices = {e["name"]: e["price"] for e in vendor["prices"]}
    check(shelf_prices == {n: c["price"] for n, c in PIECES.items()}, "3 the server's shelf holds the exact configured prices, up to the ceiling",
          f"max {max(shelf_prices.values())}")
    check(max(shelf_prices.values()) == 80000, "3 the dearest piece costs the 80,000 gp ceiling")

    # 4: nothing is bought back. A Furnisher's sell list never opens, and an item it would not take stays with the player.
    check(not open_list(p, session, name, "sell"), "4 the Furnisher opens no sell list")

    # 5-7: one cart of one piece per rarity, in a single purchase
    entries = shelf(p, session, name)
    serials = {label.strip(): serial for serial, price, stock, label in entries}
    total = sum(PIECES[n]["price"] for n in CART)
    cart = " ".join(f"0x{serials[n]} 1" for n in CART)
    mark = len(log_lines(session))
    p.call(f"buy {cart}", timeout=12)
    time.sleep(4)
    text = "\n".join(log_lines(session)[mark:])
    check(f"{total}" in text, "5 the vendor names the total of the purchase", f"expected {total}")
    line = sold_line(admin)
    check(f"{len(CART)} piece(s), {total:,} gp" in line, "5 the server's ledger counts exactly the cart", line.split("]")[-1].strip()[:120])

    after = report(admin, hex_serial)
    carried = {c["piece"]: c for c in after["carried"]}
    check(set(carried) == {PIECES[n]["id"] for n in CART}, "6 the backpack holds exactly the bought pieces", str(sorted(carried)))
    for n in CART:
        piece, got = PIECES[n], carried[PIECES[n]["id"]]
        check(got["kind"] == piece["kind"], f"6 {n}: a {piece['kind']}", got["kind"])
    check(all(c["loot"] == "Regular" for c in carried.values()), "6 none of them is newbied: tradeable and lootable", str({c["loot"] for c in carried.values()}))
    deed = carried[PIECES["Gray Brick Fireplace"]["id"]]
    chair = carried[PIECES["Pale Pine Chair"]["id"]]
    check(deed["name"] == "Gray Brick Fireplace (deed)" and chair["name"] == "Pale Pine Chair", "6 named as the catalog names them", f"{deed['name']} / {chair['name']}")
    check(chair["graphic"] == PIECES["Pale Pine Chair"]["facings"][0]["parts"][0]["id"], "6 the chair has the catalog graphic")

    # 7: the shelf is full again after buying
    again = shelf(p, session, name)
    check(all(int(stock) == 999 for _, _, stock, _ in again), "7 every line is back to 999 after the purchase")

    # 8: the rarity ladder holds in what was charged (the ledger rows)
    check("rarity 1:" in line and "rarity 6:" in line, "8 the ledger splits the gold by rarity", line.split("(")[-1][:140])
    print("DONE shop", flush=True)


def place(session: str, hex_serial: str) -> None:
    p, admin = connect(session), connect("admin")
    me = p.state["charID"]
    cx, cy, cz = 1566, 1566, 20
    floor = cz + 7
    if not report(admin, hex_serial)["houses"]:       # a rerun after a failed case carries on in the house already built
        admin.say(f"[TestOnlyFurnisherHouse {hex_serial} {cx} {cy} {cz}")
        time.sleep(1.5)
    house = json.loads((HOST / f"furnisher-house-{hex_serial}.json").read_text())
    # the floor tile the client targets: the graphic of the multi's surface tile at the room's centre
    floor_at = {(s["x"], s["y"]): s for s in house["surfaces"] if s["z"] == floor}
    centre = floor_at[(cx, cy)]
    check(centre["z"] == floor and len(floor_at) >= 25, "9 the house stands and its floor is at 27", f"{len(floor_at)} floor tiles; centre {centre}")
    stand(admin, p, cx, cy, floor)

    p.open_backpack(wait=4)
    time.sleep(0.5)
    rep = report(admin, hex_serial)
    held = {c["piece"]: c for c in rep["carried"]}

    def serial_of(name: str) -> str:
        # fresh each time: a chopped piece comes back as a new deed with a new serial
        now = {c["piece"]: c for c in report(admin, hex_serial)["carried"]}
        return now[PIECES[name]["id"]]["serial"]

    def say_lock(serial: str) -> None:
        admin.events.drain()
        p.events.drain()
        p.say("I wish to lock this down")
        check(p.wait_for(Event.TARGET_REQUEST, timeout=6) is not None, "  the lockdown cursor appeared")
        p.target(f"0x{serial}")
        time.sleep(1.5)

    def drop_at(serial: str, x: int, y: int) -> None:
        p.call(f"dropground 0x{serial} 1 {x} {y} {floor}", timeout=6)
        time.sleep(1.5)

    def place_deed(name: str, x: int, y: int) -> None:
        p.events.drain()
        p.use(f"0x{serial_of(name)}")
        check(p.wait_for(Event.TARGET_REQUEST, timeout=6) is not None, f"  {name}: the deed raised a target cursor")
        # the server accepts a tile target only if a static or multi tile of that graphic stands at that z, so name the real floor tile
        p.call(f"targettile {x} {y} {floor} {floor_at[(x, y)]['id']}", timeout=6)
        time.sleep(2.0)

    # 10: a one-graphic piece is locked down like any furniture
    already = {i["piece"] for i in rep["houses"][0]["lockedDown"]}
    if PIECES["Pale Pine Chair"]["id"] not in already:
        drop_at(serial_of("Pale Pine Chair"), cx + 1, cy - 1)
        say_lock(serial_of("Pale Pine Chair"))
    rep = report(admin, hex_serial)
    locked = [i for i in rep["houses"][0]["lockedDown"] if i["piece"] == PIECES["Pale Pine Chair"]["id"]]
    check(len(locked) == 1, "10 the chair is locked down in the house", str(rep["houses"][0]["lockedDown"]))
    if PIECES["Slate-Roofed Hearth"]["id"] not in already:
        drop_at(serial_of("Slate-Roofed Hearth"), cx - 1, cy)
        say_lock(serial_of("Slate-Roofed Hearth"))
    rep = report(admin, hex_serial)
    check(len(rep["houses"][0]["lockedDown"]) == 2, "10 so is the hearth", str(len(rep["houses"][0]["lockedDown"])))

    # 11: a deed places a multi-graphic piece through the stock addon rules
    left = cx - 2  # interior is x cx-2..cx+2, y cy-2..cy+2; the door is at (cx, cy+3), so the row cy+2 beside it is off limits
    def placed(r: dict) -> dict:
        return {a["piece"]: a for a in r["houses"][0]["addons"]}

    if PIECES["Plain Olive Rug"]["id"] not in placed(rep):    # a rerun carries on from what is already in the house
        place_deed("Plain Olive Rug", left, cy - 2)
    rep = report(admin, hex_serial)
    addons = {a["piece"]: a for a in rep["houses"][0]["addons"]}
    rug = addons.get(PIECES["Plain Olive Rug"]["id"])
    check(rug is not None and len(rug["components"]) == 16, "11 the olive rug (16 tiles) is placed", str(rug and len(rug["components"])))
    check(PIECES["Plain Olive Rug"]["id"] not in {c["piece"] for c in rep["carried"]}, "11 and its deed is used up")
    check(all(c["name"] == "Plain Olive Rug" for c in rug["components"]), "11 every tile is named for the piece")

    # 12: a wall hanging needs a wall; the stock message when there is none, placed where there is
    if PIECES["Gold-and-Green Floral Tapestry"]["id"] not in placed(rep):
        place_deed("Gold-and-Green Floral Tapestry", cx, cy)  # the middle of the room: no wall behind
        rep = report(admin, hex_serial)
        check(PIECES["Gold-and-Green Floral Tapestry"]["id"] not in placed(rep), "12 the tapestry is refused in the middle of the room (no wall)")
        check(PIECES["Gold-and-Green Floral Tapestry"]["id"] in {c["piece"] for c in rep["carried"]}, "12 and the deed stays with the player")
        place_deed("Gold-and-Green Floral Tapestry", cx, cy - 2)  # against the north wall
    rep = report(admin, hex_serial)
    tap = {a["piece"]: a for a in rep["houses"][0]["addons"]}.get(PIECES["Gold-and-Green Floral Tapestry"]["id"])
    check(tap is not None and all(c["needsWall"] for c in tap["components"]), "12 and accepted against the north wall", str(tap and tap["direction"]))

    # 13: a two-graphic floor piece is placed; turned into the chair it would overlap it is refused and put back
    fid = PIECES["Gray Brick Fireplace"]["id"]
    if fid not in placed(rep) and not any(c["piece"] == fid for c in rep["carried"]):
        check(False, "13 the fireplace is neither placed nor carried")
    if fid not in placed(rep):
        place_deed("Gray Brick Fireplace", cx + 2, cy - 1)
    rep = report(admin, hex_serial)
    fire = placed(rep).get(fid)
    check(fire is not None and len(fire["components"]) == 2, "13 the fireplace is placed", str(fire and fire["direction"]))

    def tool(graphic: int, add: str):
        """The character's own tool of that graphic, worn or carried; added once by staff when there is none (a rerun reuses it)."""
        for _ in range(2):
            p.open_backpack(wait=4)
            time.sleep(0.5)
            found = [i for i in list(p.equipped) + list(p.backpack) if i.graphic == graphic]   # the worn one first: a hatchet only chops when worn
            if found:
                return found[0]
            staff_target(admin, f"[AddToPack {add}", me)
            time.sleep(1.5)
        raise SystemExit(f"no {add}")

    deco = tool(0x0FC1, "InteriorDecorator")
    axe = tool(0x0F43, "Hatchet")

    def decorator_gump() -> str | None:
        """The serial of the Interior Decorator's window: the newest opened gump that offers Turn. It stays open between uses (the decorator only
        re-sends it when it is closed), and the new character's welcome window is open too, so it is named by serial."""
        lines = log_lines(session)
        found = None
        for i, l in enumerate(lines):
            m = re.search(r"\[GUMP\] opened local \S+ server (0x[0-9A-Fa-f]+)", l)
            if m and any("Turn" in x for x in lines[i + 1:i + 4]):
                found = m.group(1)
        return found

    def cursor_since(mark: int, wait: float = 6.0) -> bool:
        """Whether the server raised a target cursor after log line `mark` (read from the log: a cursor can arrive while a call is still returning)."""
        deadline = time.monotonic() + wait
        while time.monotonic() < deadline:
            if any("[TARGET] Server wants a target" in l for l in log_lines(session)[mark:]):
                return True
            time.sleep(0.25)
        return False

    def turn(serial: str) -> str:
        """Turn the piece with the Interior Decorator; returns what the server said afterwards. The decorator remembers its command, so a second
        use raises the cursor at once; the first use needs the Turn button."""
        mark = len(log_lines(session))
        p.use(deco.serial)
        if not cursor_since(mark, wait=2.0):
            gump = decorator_gump()
            check(gump is not None, "  the Interior Decorator has its window open")
            p.call(f"gumpresponse 1 gump:{gump}", timeout=6)  # Turn
            check(cursor_since(mark), "  the decorator raised a target cursor")
        mark = len(log_lines(session))
        p.target(f"0x{serial}")
        time.sleep(2.0)
        return "\n".join(log_lines(session)[mark:])

    def chop(serial: str) -> None:
        # only an equipped axe chops ("The axe must be equipped for any serious wood chopping")
        if not any(str(e.get("id", e.get("serial", ""))).lower().endswith(axe.serial.lower()[-8:]) for e in (p.state.get("equipped") or [])):
            for layer in ("0x02", "0x01"):          # a hatchet is a two-handed item here
                p.call(f"equip {axe.serial} {layer}", timeout=6)
                time.sleep(2.0)
                if any(str(e.get("id", e.get("serial", ""))).lower().endswith(axe.serial.lower()[-8:]) for e in (p.state.get("equipped") or [])):
                    break
        mark = len(log_lines(session))
        p.use(axe.serial)
        check(cursor_since(mark), "  the hatchet raised a target cursor")
        p.target(f"0x{serial}")
        time.sleep(2.5)

    said = turn(fire["components"][0]["serial"])
    rep = report(admin, hex_serial)
    still = placed(rep)[fid]
    check(still["direction"] == fire["direction"] and "You cannot build that there" in said,
          "13 turning it into the locked-down chair's tile is refused and the fireplace is put back as it was", f"{fire['direction']} -> {still['direction']}")
    check(len(still["components"]) == 2 and sorted(c["id"] for c in still["components"]) == sorted(c["id"] for c in fire["components"]),
          "13 with both graphics where they were")

    # 14: chopping a two-graphic piece gives its deed back; placed where both facings fit it turns and turns back
    chop(still["components"][0]["serial"])
    rep = report(admin, hex_serial)
    check(fid not in placed(rep) and sum(c["piece"] == fid and c["kind"] == "deed" for c in rep["carried"]) == 1,
          "14 chopping the fireplace removed it and returned its deed to the owner")
    place_deed("Gray Brick Fireplace", cx + 2, cy + 1)
    rep = report(admin, hex_serial)
    fire = placed(rep)[fid]
    start_dir, start_ids = fire["direction"], sorted(c["id"] for c in fire["components"])
    turn(fire["components"][0]["serial"])
    rep = report(admin, hex_serial)
    fire2 = placed(rep)[fid]
    ids2 = sorted(c["id"] for c in fire2["components"])
    check(fire2["direction"] != start_dir and ids2 != start_ids and len(fire2["components"]) == 2,
          "14 the Interior Decorator turned the fireplace", f"{start_dir} -> {fire2['direction']}; {start_ids} -> {ids2}")
    turn(fire2["components"][0]["serial"])
    rep = report(admin, hex_serial)
    fire3 = placed(rep)[fid]
    check(fire3["direction"] == start_dir and sorted(c["id"] for c in fire3["components"]) == start_ids, "14 and turned it back round to where it began")
    check(len(rep["houses"][0]["addons"]) == len(placed(rep)), "14 nothing was duplicated by turning", str(len(rep["houses"][0]["addons"])))

    # 15: a one-graphic piece turns through its facings
    chair = next(i for i in rep["houses"][0]["lockedDown"] if i["piece"] == PIECES["Pale Pine Chair"]["id"])
    turn(chair["serial"])
    rep = report(admin, hex_serial)
    chair2 = next(i for i in rep["houses"][0]["lockedDown"] if i["piece"] == PIECES["Pale Pine Chair"]["id"])
    check(chair2["graphic"] != chair["graphic"], "15 the Interior Decorator turned the chair", f"{hex(chair['graphic'])} -> {hex(chair2['graphic'])}")

    # the 59,500 gp hearth beside the door wall
    if PIECES["Fieldstone Home Hearth"]["id"] not in placed(rep):
        place_deed("Fieldstone Home Hearth", cx - 2, cy + 1)
    rep = report(admin, hex_serial)
    hearth = placed(rep).get(PIECES["Fieldstone Home Hearth"]["id"])
    check(hearth is not None and len(hearth["components"]) == 2, "15 the 59,500 gp Fieldstone Home Hearth (rarity 6) is placed", str(hearth and hearth["direction"]))

    # 16: every piece of the shop fits the stock rule in principle (a fit scan over the large pieces, in a 5x5 room they need not all fit)
    admin.say(f"[TestOnlyFurnisherFit {hex_serial} {PIECES['Great Hall Carpet']['id']} {cx - 2} {cy - 2} {floor}")
    time.sleep(1.5)
    fit = json.loads((HOST / f"furnisher-fit-{hex_serial}.json").read_text())
    check(fit["results"][0]["parts"] == 48, "16 the 48-tile Great Hall Carpet builds all its tiles", str(fit["results"]))
    print(f"INFO great hall carpet in a 5x5 room: {fit['results'][0]['fit']}", flush=True)
    print("DONE place", flush=True)


def snapshot(hex_serial: str, name: str) -> None:
    admin = connect("admin")
    OUT.mkdir(parents=True, exist_ok=True)
    rep = report(admin, hex_serial)
    (OUT / f"{name}.json").write_text(json.dumps(rep, indent=1, sort_keys=True))
    print(f"saved {name}: {len(rep['houses'][0]['addons'])} addons, {len(rep['houses'][0]['lockedDown'])} locked down, {len(rep['carried'])} carried", flush=True)


def compare(hex_serial: str, name: str) -> None:
    admin = connect("admin")
    before = json.loads((OUT / f"{name}.json").read_text())
    after = report(admin, hex_serial)
    check(after["displayItems"] == before["displayItems"] == 229 and len(after["vendors"]) == 1, "17 still one Furnisher and 229 display items (none duplicated)",
          f"{len(after['vendors'])} vendors, {after['displayItems']} items")
    check(after["vendors"][0]["name"] == before["vendors"][0]["name"], "17 the same Furnisher, not a new one")
    check(after["carried"] == before["carried"], "17 the backpack is unchanged")
    check(after["houses"] == before["houses"], "17 the placed addons and locked-down furniture are unchanged")
    print("DONE compare", flush=True)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "shop" and len(sys.argv) == 4:
        shop(sys.argv[2], sys.argv[3])
    elif cmd == "place" and len(sys.argv) == 4:
        place(sys.argv[2], sys.argv[3])
    elif cmd == "snapshot" and len(sys.argv) == 4:
        snapshot(sys.argv[2], sys.argv[3])
    elif cmd == "compare" and len(sys.argv) == 4:
        compare(sys.argv[2], sys.argv[3])
    else:
        print(__doc__)
        sys.exit(2)
