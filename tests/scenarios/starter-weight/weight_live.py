"""Live checks of the starter weight budget (Starter-Weight-Budget.md) on a disposable host.

    python weight_live.py

Needs a host running the build under test with starterWeight on and fresh characters, logged in as Navrey sessions named
after them, plus the `admin` staff session:
    HArcher (profession 8), HCarp (17), HAdvCF (Advanced: Carpentry 11 and Fletching 8), HAlcCook (Advanced: Alchemy 0
    and Cooking 13), and the controls HSmith (16), HTailor (18), HTinker (19).

The client reports weight as carried plus 11 body weight; a character is overloaded above its limit + 4 and the budget is 85%
of the limit. Prints one line per case, flushes as it goes, and exits non-zero on the first failed assertion.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(WORKSPACE / ".claude" / "scripts"))

from navrey_session import connect  # noqa: E402

BOARD, FEATHER, BOTTLE, LAMB, CHICKEN = 0x1BD7, 0x1BD1, 0xF0E, 0x1609, 0x1607
INGOT, CLOTH, LEATHER, BEDROLL, KINDLING = 0x1BF2, 0x1766, 0x1081, 0xA57, 0xDE1
BUDGETED = ["HArcher", "HCarp", "HAdvCF", "HAlcCook"]
CONTROLS = {"HSmith": {INGOT: 450}, "HTailor": {CLOTH: 300, LEATHER: 50}, "HTinker": {INGOT: 200}}


def check(condition: bool, case: str, detail: str = "") -> None:
    print(f"{'PASS' if condition else 'FAIL'} {case}{': ' + detail if detail else ''}", flush=True)
    if not condition:
        sys.exit(1)


def amounts(p) -> dict:
    p.open_backpack(wait=4)
    time.sleep(1.0)
    out: dict = {}
    for item in p.backpack:
        out[item.graphic] = out.get(item.graphic, 0) + item.amount
    return out


def main() -> None:
    sessions = {name: connect(name) for name in BUDGETED + list(CONTROLS)}

    # L1: the heavy starts now fit the budget (and so are not overloaded).
    for name in BUDGETED:
        p = sessions[name]
        have = amounts(p)
        weight, limit = p.state["weight"], p.state["maxWeight"]
        budget = int(limit * 0.85)
        shown = {k: v for k, v in {"boards": have.get(BOARD), "feathers": have.get(FEATHER), "bottles": have.get(BOTTLE),
                                   "lamb": have.get(LAMB), "chicken": have.get(CHICKEN)}.items() if v}
        print(f" {name}: weight {weight}/{limit} (budget {budget})  {shown}", flush=True)
        # Every stack keeps a floor of 10 units, so Alchemy with Cooking (meat floors) can end a few stones above the budget;
        # it must still sit well inside the real limit.
        slack = 6 if name == "HAlcCook" else 1
        check(weight <= budget + slack, f"L1 {name}: starts within the 85% budget" + (" (floors may add a few stones)" if slack > 1 else ""),
              f"{weight} vs {budget}")
        check(weight <= limit + 4, f"L1 {name}: not overloaded", f"{weight} vs {limit + 4}")
        check(have.get(BEDROLL) == 1 and have.get(KINDLING, 0) >= 3, f"L4 {name}: the camping kit is intact",
              f"bedroll {have.get(BEDROLL)}, kindling {have.get(KINDLING)}")

    arch = amounts(sessions["HArcher"])
    check(60 <= arch.get(BOARD, 0) <= 130 and arch.get(BOARD, 0) < 200, "L1 the Archer keeps a useful number of boards (60 to 130)",
          f"{arch.get(BOARD)}")
    carp = amounts(sessions["HCarp"])
    check(70 <= carp.get(BOARD, 0) <= 160, "L1 the Carpenter keeps a useful number of boards (70 to 160)", f"{carp.get(BOARD)}")

    # L2: characters already within the budget get exactly their Phase H quantities.
    for name, wanted in CONTROLS.items():
        have = amounts(sessions[name])
        check(all(have.get(g) == n for g, n in wanted.items()), f"L2 {name}: supplies untouched",
              f"{ {hex(g): have.get(g) for g in wanted} } wanted {wanted}")

    # L3: the Archer can walk a long way: stamina is not drained to nothing.
    archer = sessions["HArcher"]
    x, y = archer.state["charPosX"], archer.state["charPosY"]
    stam_before = archer.state["stamina"]
    arrived = None
    for dx, dy in ((14, 0), (-14, 0), (0, 14), (0, -14)):
        result = archer.goto(x + dx, y + dy).wait()
        if result == "arrived":
            arrived = (dx, dy)
            break
    nx, ny = archer.state["charPosX"], archer.state["charPosY"]
    moved = max(abs(nx - x), abs(ny - y))
    print(f" Archer walked {moved} tiles; stamina {stam_before} -> {archer.state['stamina']}", flush=True)
    check(moved >= 10 and archer.state["stamina"] > 0, "L3 the Archer walks 10+ tiles without running out of stamina",
          f"moved {moved}, stamina {archer.state['stamina']}")

    print("ALL PASS", flush=True)


if __name__ == "__main__":
    main()
