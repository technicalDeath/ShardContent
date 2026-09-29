"""K1 live boundary cases for the outdoor Hot Zones (disposable host with hotZones on).

    python ShardContent/tests/scenarios/hot-zones/hot_boundary_live.py <player-session> <staff-session>

The player must be an ordinary (AccessLevel.Player) fresh character; boundary messages go to players
only. Placement uses `[set Location` on the player; travel cases walk onto the real teleporters.
Exits non-zero when any case's observed entry/exit message differs from the expectation.
"""

from __future__ import annotations

import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", ".claude", "scripts")))

from navrey_session import connect, session  # noqa: E402
from staff_command import go_to, staff_target  # noqa: E402

FIRE = "Fire Island"
BUCC = "Buccaneer's Den island"


def main(argv: list) -> int:
    player_name, staff_name = argv[1], argv[2]
    player, admin = connect(player_name), connect(staff_name)
    serial = player.state["charID"]
    return run(player, admin, serial, session(player_name)["log"])


def lines_after(log_path: str, mark: int) -> list:
    with open(log_path, errors="replace") as handle:
        return handle.readlines()[mark:]


def run(player, admin, serial: str, log_path: str) -> int:
    results = []

    def mark() -> int:
        with open(log_path, errors="replace") as handle:
            return len(handle.readlines())

    def observe(m: int) -> str:
        time.sleep(2.5)
        found = []
        for line in lines_after(log_path, m):
            if "Hot Zone" in line and "have entered" in line:
                found.append("enter:" + line.split("have entered ")[1].split(",")[0])
            elif "Hot Zone initiation no longer applies" in line:
                found.append("leave:" + line.split("You have left ")[1].split(".")[0])
        return ",".join(found) or "none"

    def pos() -> tuple:
        s = player.state
        return (s["charPosX"], s["charPosY"], s["charPosZ"])

    def place(x: int, y: int, z: int) -> None:
        go_to(admin, player)
        staff_target(admin, f'[set Location "({x}, {y}, {z})"', serial)

    def case(label: str, expected: str, action) -> None:
        m = mark()
        action()
        got = observe(m)
        ok = got == expected
        results.append((label, expected, got, pos(), ok))
        print(f"{'PASS' if ok else 'FAIL'} {label}: expected {expected} got {got} at {pos()}", flush=True)

    def steps(*directions: str) -> None:
        for direction in directions:
            player.walk(direction)
            time.sleep(1.2)

    place(1430, 1690, 0)
    time.sleep(3)

    case("Fire Island shore (safe->Hot)", f"enter:{FIRE}", lambda: place(4600, 3500, 0))
    case("Fire Island back to town (Hot->safe)", f"leave:{FIRE}", lambda: place(1430, 1690, 0))
    case("Fire Island open ocean west of polygon", "none", lambda: place(4000, 3500, 0))
    case("B12 dock corner NW (safe->Hot)", f"enter:{BUCC}", lambda: place(2749, 2154, -2))
    case("B12 dock corner NE (Hot->Hot)", "none", lambda: place(2762, 2154, -2))
    case("B12 dock corner SE (Hot->Hot)", "none", lambda: place(2762, 2179, -2))
    case("B13 bay past the dock margin (Hot->safe)", f"leave:{BUCC}", lambda: place(2775, 2166, 0))
    case("B12 dock again (safe->Hot)", f"enter:{BUCC}", lambda: place(2755, 2166, -2))
    case("Buccaneer's Den town then ocean south", f"leave:{BUCC}", lambda: place(2711, 2400, 0))
    case("B5 stand on Fire Island south of Hythloth (safe->Hot)", f"enter:{FIRE}", lambda: place(4722, 3816, 0))
    case("B5 Hythloth entrance teleporter (Hot->dungeon)", f"leave:{FIRE}", lambda: steps("n", "n", "n", "n"))
    case(
        "B6 Hythloth exit teleporter (dungeon->Hot)", f"enter:{FIRE}",
        lambda: (place(5905, 17, 64), steps("n", "n", "n")),
    )
    case("Hythloth interior placement (Hot->dungeon)", f"leave:{FIRE}", lambda: place(5905, 22, 44))
    case("B3 teleporter (safe->Hot)", f"enter:{BUCC}", lambda: (place(2618, 980, 5), steps("n", "n", "n")))
    case("B4 reverse teleporter (Hot->safe)", f"leave:{BUCC}", lambda: steps("s", "s", "n", "n"))
    def use_gate(radio: int) -> None:
        time.sleep(1)
        player.call(f"gumpresponse 1 {radio}")

    place(2711, 2231, 0)
    time.sleep(3)
    case("B2 Buccaneer's Den moongate to Britain (Hot->safe)", f"leave:{BUCC}", lambda: (steps("s", "s", "s", "s"), use_gate(1)))
    place(1336, 1994, 5)
    time.sleep(3)
    case("B1 Britain moongate to Buccaneer's Den (safe->Hot)", f"enter:{BUCC}", lambda: (steps("s", "s", "s", "s"), use_gate(8)))
    place(2603, 2117, -20)
    time.sleep(3)
    case("B11 cellar teleporter (Hot->Hot)", "none", lambda: steps("s", "s", "s", "s", "s"))
    if not (2603 <= pos()[0] <= 2607 and pos()[1] >= 2129):
        results.append(("B11 teleporter did not fire", "arrival near (2605, 2130)", str(pos()), pos(), False))
        print("FAIL B11 teleporter did not fire; at", pos(), flush=True)

    failed = [r for r in results if not r[4]]
    print(f"\n{len(results) - len(failed)}/{len(results)} cases passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
