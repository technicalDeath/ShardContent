"""Live check of the Tinkering Ward recipe and the Tinker buy-back (docs/Beta-2d-Ward-Crafting-Readiness.md).

Needs a disposable host that loaded WardProbe.dll (see ward_live.py; it supplies `[TestOnlyWardPrime`), a staff session
`admin`, and a fresh ordinary character (it holds the free starter Ward).

    python -u ward_craft_live.py craft <player-session>      # recipe, crafting, skill gate, buy-back, audit
    python -u ward_craft_live.py restart <player-session>    # after a save and restart: both still work
    python -u ward_craft_live.py off <player-session>        # with wardCraft.enabled false and buyBackPrice 0: neither exists

`craft` spawns and names a Tinker beside the character and writes it to work/ward-craft/live-state.json for the later
passes. Crafting is driven the way this era's client does it: use the tinker's tools, target the iron ingots, then answer
the legacy item-list menus (`menus` / `menuresponse`): Miscellaneous, then the ward. Prints one line per case, flushes as it
goes, and exits non-zero on the first failed assertion.
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
INGOT = 0x1BF2
TOOLS = (0x1EB8, 0x1EBC)
BUY_BACK = 110
INGOTS = 20
STATE = WORKSPACE / "work" / "ward-craft" / "live-state.json"
SHOP_LINE = re.compile(r"0x([0-9A-Fa-f]+)\s+(\d+)gp\s+x(\d+)\s+(.*)")
MENU_HEAD = re.compile(r"\[MENU\] local (0x[0-9A-Fa-f]+) server (0x[0-9A-Fa-f]+) (.*)")
MENU_OPTION = re.compile(r"\[option (\d+)\] graphic 0x[0-9A-Fa-f]+ hue 0x[0-9A-Fa-f]+ (.*)")


def check(condition: bool, case: str, detail: str = "") -> None:
    print(f"{'PASS' if condition else 'FAIL'} {case}{': ' + detail if detail else ''}", flush=True)
    if not condition:
        sys.exit(1)


class Session:
    def __init__(self, name: str):
        self.name = name
        self.p = connect(name)
        self.admin = connect("admin")
        self.me = str(self.p.state["charID"])
        self.log = WORKSPACE / "work" / "navrey-sessions" / name / "cuolog"
        self.alog = WORKSPACE / "work" / "navrey-sessions" / "admin" / "cuolog"

    def lines(self, path: Path) -> list:
        return path.read_text(errors="replace").splitlines()

    def staff(self, command: str, pattern: str) -> str:
        mark = len(self.lines(self.alog))
        self.admin.say(command)
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            for line in self.lines(self.alog)[mark:]:
                found = re.search(pattern, line)
                if found:
                    return found.group(0)
            time.sleep(0.3)
        check(False, f"{command} answered", f"no line matching {pattern!r}")
        return ""

    def backpack(self) -> list:
        self.p.open_backpack(wait=4)
        time.sleep(0.5)
        return self.p.backpack

    def wards(self) -> list:
        return [i for i in self.backpack() if i.graphic == WARD]

    def ingots(self) -> int:
        return sum(i.amount for i in self.backpack() if i.graphic == INGOT)

    def gold(self) -> int:
        return self.p.state["gold"]

    def new_vendor(self, command: str, name: str) -> str:
        before = {m.serial for m in self.p.mobiles()}
        staff_target(self.admin, command, self.me)
        time.sleep(1.5)
        added = [m for m in self.p.mobiles(within=6) if m.serial not in before]
        check(len(added) == 1, f"{command} spawned one vendor beside the character", f"{len(added)} new mobiles")
        staff_target(self.admin, f"[set Name {name}", added[0].serial)
        return added[0].serial

    def open_list(self, name: str, kind: str, required: bool = True) -> bool:
        """Say '<name> buy|sell' and wait for the vendor's list; a vendor with nothing to say sends none."""
        mark = len(self.lines(self.log))
        self.p.say(f"{name} {kind}")
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            if any(re.search(rf"\[SHOP\].*{kind} list", line, re.I) for line in self.lines(self.log)[mark:]):
                return True
            time.sleep(0.3)
        if required:
            check(False, f"{name} {kind} list arrived", "no [SHOP] list line within 8 s")
        return False

    def entries(self, command: str) -> list:
        return [m.groups() for m in map(SHOP_LINE.search, self.p.call(command, timeout=8)) if m]

    # ---- the legacy Tinkering menus

    def menu(self, wait: float = 8.0):
        """The open legacy menu as (local, server, title, [(index, text)]), or None if none opens in time."""
        deadline = time.monotonic() + wait
        while time.monotonic() < deadline:
            out = self.p.call("menus", timeout=8)
            head = next((MENU_HEAD.search(line) for line in out if MENU_HEAD.search(line)), None)
            if head:
                options = [(int(m.group(1)), m.group(2)) for line in out for m in [MENU_OPTION.search(line)] if m]
                return head.group(1), head.group(2), head.group(3), options
            time.sleep(0.5)
        return None

    def pick(self, menu, text: str):
        local, server, _, options = menu
        index = next((i for i, label in options if text.lower() in label.lower()), None)
        check(index is not None, f"the menu offers '{text}'", str([label for _, label in options]))
        self.p.call(f"menuresponse {local} {server} {index}", timeout=8)
        return self.menu()

    def miscellaneous_menu(self):
        """Use the tools on the ingots and open Miscellaneous; None when the Tinkering menu does not open."""
        backpack = self.backpack()
        tools = next((i for i in backpack if i.graphic in TOOLS), None)
        ingots = next((i for i in backpack if i.graphic == INGOT), None)
        check(tools is not None and ingots is not None, "the character holds tinker's tools and iron ingots")
        # Right after a login or a staff action the server holds actions back for a moment, so try again a few times.
        started = False
        for _ in range(4):
            started = self.p.use_on(tools.serial, ingots.serial, timeout=6)
            if started:
                break
            time.sleep(2.5)
        check(started, "using the tools on the ingots raised a target and took it")
        main = self.menu()
        check(main is not None, "the Tinkering menu opened", "no legacy menu within 8 s")
        misc = self.pick(main, "Miscellaneous")
        check(misc is not None, "the Miscellaneous list opened")
        return misc

    def ward_option(self, misc):
        return next(((i, label) for i, label in misc[3] if "backpack ward" in label.lower()), None)

    def craft_ward(self) -> bool:
        """Craft one ward through the menus; True when the pack gained one."""
        misc = self.miscellaneous_menu()
        option = self.ward_option(misc)
        check(option is not None, "the Miscellaneous list offers a backpack ward", str([label for _, label in misc[3]]))
        before = len(self.wards())
        self.p.call(f"menuresponse {misc[0]} {misc[1]} {option[0]}", timeout=8)
        deadline = time.monotonic() + 12
        while time.monotonic() < deadline:
            if len(self.wards()) > before:
                return True
            time.sleep(0.5)
        return False


def craft(player: str) -> None:
    s = Session(player)
    STATE.parent.mkdir(parents=True, exist_ok=True)
    go_to(s.admin, s.p)
    s.p.open_backpack(wait=4)
    starter = s.wards()
    check(len(starter) == 1, "start: the character holds only the free starter Ward")
    starter_serial = starter[0].serial

    staff_target(s.admin, "[AddToPack TinkerTools", s.me)
    staff_target(s.admin, "[AddToPack IronIngot 200", s.me)
    staff_target(s.admin, "[SetSkill Tinkering 100", s.me)
    time.sleep(3.0)  # let the staff actions' action delay pass before using the tools
    ingots_start = s.ingots()
    check(ingots_start >= 200, "start: tinker's tools, 200+ iron ingots and Tinkering 100", f"ingots={ingots_start}")

    # L1/L2: the recipe is in the Miscellaneous list, and its label shows the ingot cost.
    misc = s.miscellaneous_menu()
    option = s.ward_option(misc)
    check(option is not None, "L1 the Miscellaneous list offers a backpack ward", str([label for _, label in misc[3]]))
    check(f"({INGOTS} ingots)" in option[1], "L2 its label shows the ingot cost", option[1])
    s.p.call(f"menuresponse {misc[0]} {misc[1]} 0", timeout=8)  # cancel

    # L3: at skill 100 crafting costs exactly the ingots and yields a regular Unprimed Ward, with no maker's-mark prompt.
    time.sleep(1.0)
    mark = len(s.lines(s.log))
    ingots_before = s.ingots()
    check(s.craft_ward(), "L3 crafting at skill 100 delivered a ward")
    check(s.ingots() == ingots_before - INGOTS, "L3 it cost exactly the ingots", f"{ingots_before} -> {s.ingots()}")
    check(not any("maker's mark" in line for line in s.lines(s.log)[mark:]),
          "L3 no exceptional or maker's-mark prompt for a ward")
    crafted = [w for w in s.wards() if w.serial != starter_serial]
    check(len(crafted) == 1, "L3 exactly one new ward in the pack")
    mark = len(s.lines(s.log))
    s.p.use(crafted[0].serial)
    time.sleep(2.0)
    text = "\n".join(s.lines(s.log)[mark:])
    check("A backpack ward: carried in your backpack" in text and "Status: Unprimed" in text and "starter" not in text,
          "L3 the crafted ward is a regular Unprimed one")

    # L4: below the minimum skill the menu does not offer it at all.
    staff_target(s.admin, "[SetSkill Tinkering 30", s.me)
    time.sleep(3.0)
    low = s.miscellaneous_menu()
    check(s.ward_option(low) is None, "L4 at skill 30 the Miscellaneous list does not offer a backpack ward",
          str([label for _, label in low[3]]))
    s.p.call(f"menuresponse {low[0]} {low[1]} 0", timeout=8)
    staff_target(s.admin, "[SetSkill Tinkering 100", s.me)
    time.sleep(3.0)

    # A second crafted ward, to prime with the probe so a Primed ward and an Unprimed one can be told apart in the sell list.
    check(s.craft_ward(), "L5 a second ward was crafted")
    both = [w for w in s.wards() if w.serial != starter_serial]
    check(len(both) == 2, "L5 two crafted wards plus the starter in the pack", f"{len(both)} crafted")
    primed, unprimed = both[0], both[1]
    primed_hex = f"0x{int(str(primed.serial), 16):X}"
    s.staff(f"[TestOnlyWardPrime {primed_hex} {s.me}", r"WardPrime [0-9A-F]+ Primed")

    # L6 to L9: a Tinker buys only the Unprimed crafted ward, for the configured price, and never re-lists it.
    tinker = s.new_vendor("[add Tinker", "Wardtinker")
    STATE.write_text(json.dumps({"tinker": tinker, "name": "Wardtinker"}))
    s.open_list("Wardtinker", "sell")
    sell = s.entries("selllist")
    sold_serials = {int(serial, 16): int(price) for serial, price, _, _ in sell}
    check(int(str(unprimed.serial), 16) in sold_serials, "L6 the Unprimed crafted ward is on the Tinker's sell list", str(sell))
    check(sold_serials[int(str(unprimed.serial), 16)] == BUY_BACK, "L6 at the buy-back price",
          f"{sold_serials[int(str(unprimed.serial), 16)]}gp")
    check(int(str(primed.serial), 16) not in sold_serials, "L7 a Primed (tracking) ward is not on the sell list")
    check(int(str(starter_serial), 16) not in sold_serials, "L7 the starter ward is not on the sell list")

    gold_before = s.gold()
    s.p.call(f"sell {unprimed.serial} 1", timeout=8)
    check(s.p.wait(lambda: s.gold() == gold_before + BUY_BACK, timeout=8), "L8 selling paid exactly the buy-back price",
          f"{gold_before} -> {s.gold()}")
    check(all(w.serial != unprimed.serial for w in s.wards()), "L8 the ward left the pack")

    s.open_list("Wardtinker", "buy")
    shelf = [e for e in s.entries("shop") if "backpack ward" in e[3].lower()]
    check(len(shelf) == 1 and int(shelf[0][1]) == 2000 and int(shelf[0][2]) == 20,
          "L9 the Tinker did not re-list it: still only the 2000 gp shelf entry, full", str(shelf))

    # L10: the buy-back is in the audit log.
    server_log = max((WORKSPACE / "work" / "dev-server" / "logs").glob("server-*.log"), key=lambda p: p.stat().st_mtime)
    sold = [line for line in server_log.read_text(errors="replace").splitlines() if "theft ward-sold" in line]
    vendor_serial = int(str(tinker), 16)
    check(len(sold) == 1 and f"vendor={vendor_serial}; count=1; paid={BUY_BACK}" in sold[0],
          "L10 exactly one buy-back was audited", sold[0].strip() if sold else "none")
    print("CRAFT PASS (save and restart the server, then run: restart)", flush=True)


def restart(player: str) -> None:
    s = Session(player)
    state = json.loads(STATE.read_text())
    check(s.p.state.get("connected", True), "session is connected to the restarted server")

    misc = s.miscellaneous_menu()
    check(s.ward_option(misc) is not None, "L11 after a restart the Miscellaneous list still offers the backpack ward",
          str([label for _, label in misc[3]]))
    s.p.call(f"menuresponse {misc[0]} {misc[1]} 0", timeout=8)

    s.staff(f"[TestOnlyWardAdd {s.me}", r"WardAdd [0-9A-F]+")
    gold_before = s.gold()
    s.open_list(state["name"], "sell")
    sell = s.entries("selllist")
    check(any(price == str(BUY_BACK) for _, price, _, _ in sell), "L12 after a restart the Tinker still buys an unused ward", str(sell))
    target = next(serial for serial, price, _, _ in sell if price == str(BUY_BACK))
    s.p.call(f"sell 0x{target} 1", timeout=8)
    check(s.p.wait(lambda: s.gold() == gold_before + BUY_BACK, timeout=8), "L12 and paid the buy-back price",
          f"{gold_before} -> {s.gold()}")
    print("RESTART PASS", flush=True)


def off(player: str) -> None:
    s = Session(player)
    state = json.loads(STATE.read_text())
    check(s.p.state.get("connected", True), "session is connected to the restarted server")

    misc = s.miscellaneous_menu()
    check(s.ward_option(misc) is None, "L13 with wardCraft.enabled false the Miscellaneous list has no backpack ward",
          str([label for _, label in misc[3]]))
    s.p.call(f"menuresponse {misc[0]} {misc[1]} 0", timeout=8)

    s.staff(f"[TestOnlyWardAdd {s.me}", r"WardAdd [0-9A-F]+")
    ward = s.wards()[-1]  # with the buy-back off no ward can be sold, so any one in the pack will do
    wards_before = len(s.wards())
    # The tinker's tools in the pack are something a Tinker does buy, so a sell list arrives; the ward must not be on it.
    check(s.open_list(state["name"], "sell"), "L14 setup: the Tinker sent a sell list (it buys the tinker's tools)")
    sell = s.entries("selllist")
    check(not any("ward" in label.lower() for _, _, _, label in sell),
          "L14 with buyBackPrice 0 the Tinker's sell list has no ward", str(sell))
    gold_before = s.gold()
    s.p.call(f"sell {ward.serial} 1", timeout=8)
    time.sleep(3.0)
    check(s.gold() == gold_before and len(s.wards()) == wards_before,
          "L14 forcing a sale of the ward changes nothing: no gold, ward kept")
    print("OFF PASS", flush=True)


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else ""

    if mode in ("craft", "restart", "off") and len(sys.argv) == 3:
        {"craft": craft, "restart": restart, "off": off}[mode](sys.argv[2])
    else:
        print(__doc__)
        sys.exit(2)
