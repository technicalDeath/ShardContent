"""Live check of the Backpack Ward double-click status text (BACKPACK-WARD-DESIGN.md, Section 5).

Needs a disposable host that loaded WardProbe.dll (see ward_live.py), a staff session `admin` and an ordinary
session whose character was just created (it holds the starter Ward).

    python ward_inspect_live.py <player-session>

Prints one line per case, flushes as it goes, and exits non-zero on the first failed assertion.
"""

from __future__ import annotations

import re
import sys
import time
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(WORKSPACE / ".claude" / "scripts"))

from navrey_session import connect  # noqa: E402
from staff_command import go_to  # noqa: E402

WARD = 0x1F14  # BackpackWard; the client names it "recall rune"


def check(condition: bool, case: str, detail: str = "") -> None:
    print(f"{'PASS' if condition else 'FAIL'} {case}{': ' + detail if detail else ''}", flush=True)
    if not condition:
        sys.exit(1)


def main(player_session: str) -> None:
    p = connect(player_session)
    admin = connect("admin")
    plog = WORKSPACE / "work" / "navrey-sessions" / player_session / "cuolog"
    alog = WORKSPACE / "work" / "navrey-sessions" / "admin" / "cuolog"
    me = str(p.state["charID"])

    def lines(path: Path) -> list:
        return path.read_text(errors="replace").splitlines()

    def staff(command: str, pattern: str) -> str:
        mark = len(lines(alog))
        admin.say(command)
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            for line in lines(alog)[mark:]:
                found = re.search(pattern, line)
                if found:
                    return found.group(0)
            time.sleep(0.3)
        check(False, f"{command} answered", f"no line matching {pattern!r}")
        return ""

    def double_click(serial: str) -> str:
        mark = len(lines(plog))
        p.use(serial)
        time.sleep(2.0)
        return "\n".join(lines(plog)[mark:])

    def wards() -> list:
        p.open_backpack(wait=4)
        time.sleep(0.5)
        return [i for i in p.backpack if i.graphic == WARD]

    p.open_backpack(wait=4)
    time.sleep(1.0)
    go_to(admin, p)
    starter = wards()
    check(len(starter) == 1, "new character holds the starter Ward")
    starter_serial = starter[0].serial

    text = double_click(starter_serial)
    check("Your starter backpack ward" in text and "bound to you" in text and "Status: Unprimed" in text,
          "D1 starter Ward: says what it is (bound to you) and Unprimed")

    staff(f"[TestOnlyWardAdd {me}", r"WardAdd [0-9A-F]+")
    regular = next(i for i in wards() if i.serial != starter_serial)
    ward_hex = f"0x{int(str(regular.serial), 16):X}" if not str(regular.serial).startswith("0x") else str(regular.serial)
    text = double_click(regular.serial)
    check("A backpack ward: carried in your backpack" in text and "Status: Unprimed" in text
          and "starter" not in text, "D2 regular Ward: Unprimed, not the starter text")

    staff(f"[TestOnlyWardPrime {ward_hex} {me}", r"WardPrime [0-9A-F]+ Primed")
    text = double_click(regular.serial)
    check("Status: Primed" in text and "30 more quiet minutes" in text and "resets" in text,
          "D3 Primed Ward: phase and 30 minutes before it resets")

    staff(f"[TestOnlyWardAge {ward_hex} 10", r"WardAge [0-9A-F]+")
    text = double_click(regular.serial)
    check("20 more quiet minutes" in text, "D4 after ten minutes of quiet: 20 minutes left")

    p.call(f"dropground {regular.serial}", timeout=8)
    time.sleep(2.0)
    check(p.wait(lambda: any(i.graphic == WARD for i in p.items(within=2)), timeout=6), "D5 Ward dropped at the cook's feet")
    text = double_click(regular.serial)
    check("not in your backpack" in text and "timer keeps running" in text and "Status: Primed" in text,
          "D5 Ward on the ground: not protecting, timer keeps running")

    # D6: a Primed Ward whose 30 quiet minutes have passed resets to Unprimed the moment it is inspected.
    staff(f"[TestOnlyWardAge {ward_hex} 25", r"WardAge [0-9A-F]+")
    text = double_click(regular.serial)
    report = staff(f"[TestOnlyWardReport {ward_hex}", r"WardReport [0-9A-F]+ phase=\w+")
    check("Status: Unprimed" in text and "phase=Unprimed" in report,
          "D6 expired Primed Ward resets to Unprimed when inspected", report)

    print("ALL PASS", flush=True)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    main(sys.argv[1])
