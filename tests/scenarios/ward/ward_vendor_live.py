"""Live check of the Tinker Backpack Ward sale (docs/Beta-2a-Ward-Vendor-Readiness.md, matrix cases 6 to 14).

Needs a disposable host running the deployed build, a staff session `admin`, and fresh ordinary characters (each holds
the free starter Ward and the starter gold).

    python -u ward_vendor_live.py buy <buyer-session> <poor-session>   # cases 6 to 11 and 13
    python -u ward_vendor_live.py shelf <buyer-session> [absent]       # after a save and restart: cases 12 and 14

`buy` spawns a Tinker and an Alchemist beside the buyer, names them, and writes their serials to
work/ward-vendor/live-state.json for `shelf`. Prints one line per case, flushes as it goes, and exits non-zero on the
first failed assertion.
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

WARD = 0x1F14  # BackpackWard; the client names it "recall rune"
PRICE = 2000
STOCK = 20
STATE = WORKSPACE / "work" / "ward-vendor" / "live-state.json"
SHELF_LINE = re.compile(r"0x([0-9A-Fa-f]+)\s+(\d+)gp\s+x(\d+)\s+(.*)")


def check(condition: bool, case: str, detail: str = "") -> None:
    print(f"{'PASS' if condition else 'FAIL'} {case}{': ' + detail if detail else ''}", flush=True)
    if not condition:
        sys.exit(1)


def log_lines(session: str) -> list:
    path = WORKSPACE / "work" / "navrey-sessions" / session / "cuolog"
    return path.read_text(errors="replace").splitlines()


def newest_server_log() -> Path:
    logs = sorted((WORKSPACE / "work" / "dev-server" / "logs").glob("server-*.log"))
    return logs[-1]


def wards(p) -> list:
    p.open_backpack(wait=4)
    time.sleep(0.5)
    return [i for i in p.backpack if i.graphic == WARD]


def open_list(p, session: str, name: str, kind: str) -> None:
    """Say '<name> buy' or '<name> sell' and wait for the vendor's list to arrive."""
    mark = len(log_lines(session))
    p.say(f"{name} {kind}")
    deadline = time.monotonic() + 8
    while time.monotonic() < deadline:
        if any(re.search(rf"\[SHOP\].*{kind} list", line, re.I) for line in log_lines(session)[mark:]):
            return
        time.sleep(0.3)
    check(False, f"{name} {kind} list arrived", "no [SHOP] list line within 8 s")


def shelf(p, session: str, name: str) -> list:
    open_list(p, session, name, "buy")
    return [m.groups() for m in map(SHELF_LINE.search, p.call("shop", timeout=8)) if m]


def ward_line(entries: list):
    return next(((s, int(price), int(stock)) for s, price, stock, label in entries if "backpack ward" in label.lower()), None)


def new_vendor(admin, p, command: str, name: str) -> str:
    before = {m.serial for m in p.mobiles()}
    staff_target(admin, command, p.state["charID"])
    time.sleep(1.5)
    added = [m for m in p.mobiles(within=6) if m.serial not in before]
    check(len(added) == 1, f"{command} spawned one vendor beside the buyer", f"{len(added)} new mobiles")
    serial = added[0].serial
    staff_target(admin, f"[set Name {name}", serial)
    return serial


def buy(buyer_session: str, poor_session: str) -> None:
    p, poor, admin = connect(buyer_session), connect(poor_session), connect("admin")
    me = p.state["charID"]
    STATE.parent.mkdir(parents=True, exist_ok=True)

    go_to(admin, p)
    p.open_backpack(wait=4)
    starter = wards(p)
    check(len(starter) == 1, "start: the buyer holds only the free starter Ward")
    starter_serial = starter[0].serial
    staff_target(admin, f"[AddToPack Gold {PRICE * 2 + 500}", me)
    time.sleep(1.0)
    gold = p.state["gold"]
    check(gold >= PRICE * 2, "start: the buyer has the gold for two Wards", f"gold={gold}")

    tinker = new_vendor(admin, p, "[add Tinker", "Wardtester")
    alchemist = new_vendor(admin, p, "[add Alchemist", "Controlalch")
    STATE.write_text(json.dumps({"tinker": tinker, "name": "Wardtester", "buyer": buyer_session}))

    # 6: a plain Tinker offers the Ward at the configured price and shelf; another vendor does not.
    entries = shelf(p, buyer_session, "Wardtester")
    found = ward_line(entries)
    check(found is not None, "6 a Tinker's buy list offers a backpack ward", str(entries))
    check(found[1] == PRICE and found[2] == STOCK, "6 at the configured price and shelf", f"{found[1]}gp x{found[2]}")
    control = ward_line(shelf(p, buyer_session, "Controlalch"))
    check(control is None, "6 an Alchemist's buy list does not offer it")

    # 7 and 8: buying takes the price, delivers one regular Unprimed Ward, and the shelf drops by one.
    entries = shelf(p, buyer_session, "Wardtester")
    item_serial = next(s for s, price, stock, label in entries if "backpack ward" in label.lower())
    gold_before = p.state["gold"]
    p.call(f"buy 0x{item_serial} 1", timeout=8)
    check(p.wait(lambda: p.state["gold"] == gold_before - PRICE, timeout=8), "7 buying takes exactly the price",
          f"{gold_before} -> {p.state['gold']}")
    time.sleep(1.0)
    owned = wards(p)
    check(len(owned) == 2, "7 a second Ward arrived in the backpack", f"{len(owned)} wards")
    bought = next(i for i in owned if i.serial != starter_serial)
    mark = len(log_lines(buyer_session))
    p.use(bought.serial)
    time.sleep(2.0)
    text = "\n".join(log_lines(buyer_session)[mark:])
    check("A backpack ward: carried in your backpack" in text and "Status: Unprimed" in text and "starter" not in text,
          "7 the bought Ward is a regular, Unprimed one (case 13: shows the activation lines)")
    check("It activates when a theft against you is noticed" in text and "30 minutes pass" in text,
          "13 the double-click text explains activation and the 30 minutes")
    found = ward_line(shelf(p, buyer_session, "Wardtester"))
    check(found is not None and found[2] == STOCK - 1, "8 the shelf dropped by one", str(found))

    # 9: the vendor will not buy a Ward back. Tongs are something a Tinker does buy, so a real sell list is sent and the
    # Ward can be seen to be missing from it (with nothing sellable the vendor just says it is not interested).
    staff_target(admin, "[AddToPack Tongs", me)
    time.sleep(1.0)
    open_list(p, buyer_session, "Wardtester", "sell")
    sell_text = "\n".join(p.call("selllist", timeout=8))
    check("tongs" in sell_text.lower(), "9 control: the Tinker's sell list is real and takes Tongs", sell_text.strip()[:160])
    check(bought.serial not in sell_text and "ward" not in sell_text.lower() and "recall rune" not in sell_text.lower(),
          "9 the Tinker's sell list does not include the Ward")
    gold_before = p.state["gold"]
    p.call(f"sell {bought.serial} 1", timeout=8)
    time.sleep(3.0)
    check(p.state["gold"] == gold_before and any(i.serial == bought.serial for i in wards(p)),
          "9 forcing a sale of the Ward with the list open changes nothing: no gold, Ward kept")

    # 10: too little gold is refused with nothing taken and nothing delivered.
    staff_target(admin, f'[set Location "({p.state["charPosX"]}, {p.state["charPosY"]}, {p.state["charPosZ"]})"',
                 poor.state["charID"])
    time.sleep(2.0)
    poor.open_backpack(wait=4)
    poor_gold, poor_wards = poor.state["gold"], len(wards(poor))
    check(poor_gold < PRICE, "10 setup: the second character cannot afford a Ward", f"gold={poor_gold}")
    entries = shelf(poor, poor_session, "Wardtester")
    item_serial = next(s for s, price, stock, label in entries if "backpack ward" in label.lower())
    poor.call(f"buy 0x{item_serial} 1", timeout=8)
    time.sleep(3.0)
    check(poor.state["gold"] == poor_gold and len(wards(poor)) == poor_wards,
          "10 buying without the gold takes nothing and delivers nothing")

    # 11: the purchase is in the audit log with the buyer, vendor, count and price.
    server_log = newest_server_log().read_text(errors="replace")
    audit = [line for line in server_log.splitlines() if "theft ward-bought" in line]
    check(len(audit) == 1, "11 exactly one purchase was audited", f"{len(audit)} lines")
    vendor_serial = int(str(tinker), 16)  # the audit line prints the vendor's serial in decimal
    check(f"vendor={vendor_serial}; count=1; unitPrice={PRICE}" in audit[0],
          "11 the audit line names the vendor, count and unit price", audit[0].strip())
    print("BUY PASS (save and restart the server, then run: shelf)", flush=True)


def after_restart(buyer_session: str, expect_absent: bool) -> None:
    state = json.loads(STATE.read_text())
    p = connect(buyer_session)
    check(p.state.get("connected", True), "session is connected to the restarted server")
    entries = shelf(p, buyer_session, state["name"])
    found = ward_line(entries)

    if expect_absent:
        check(found is None, "14 with stockPerVendor 0 the Tinker offers no Ward after a restart", str(entries))
    else:
        check(found is not None and found[1] == PRICE and found[2] == STOCK,
              "12 after a restart the same Tinker lists the Ward again, at the full shelf", str(found))

    print("SHELF PASS", flush=True)


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else ""

    if mode == "buy" and len(sys.argv) == 4:
        buy(sys.argv[2], sys.argv[3])
    elif mode == "shelf" and len(sys.argv) in (3, 4):
        after_restart(sys.argv[2], len(sys.argv) == 4 and sys.argv[3] == "absent")
    else:
        print(__doc__)
        sys.exit(2)
