"""Live death/murderer check for Feature G (2026-09-28 newbied-only starter combat gear).

Confirms the stock Item.OnInventoryDeath/OnParentDeath routing (unchanged engine code, already
proven for other starter systems in Phase D/E) also applies correctly to G's plain-stock,
Newbied-only combat gear: kept through an ordinary death, lost on a murderer's death. The
BackpackWard stays Nontransferable regardless (Phase F/E scope, unaffected by G).

Young must already be globally disabled (2026-09-28 ruling) so no per-character clearing is
needed. automaticMurderAdjudication/knockedOut must be off so [set Kills 5 makes a murderer.

    python starter_combat_death_live.py <player-session> <staff-session>

Prints one line per case and exits non-zero on the first failed assertion.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(WORKSPACE / ".claude" / "scripts"))

from navrey_session import connect  # noqa: E402
from uo import Event  # noqa: E402

WARD_GRAPHIC = 0x1F14  # BackpackWard; the client names it "recall rune" from the graphic


def check(condition: bool, case: str, detail: str = "") -> None:
    print(f"{'PASS' if condition else 'FAIL'} {case}{': ' + detail if detail else ''}", flush=True)
    if not condition:
        sys.exit(1)


def pack(client) -> dict:
    client.use(client.state["backpackID"])
    time.sleep(1.0)
    return {i["serial"]: i for i in client.state.get("backpack", [])}


def one(items: dict, predicate, what: str) -> str:
    found = [s for s, i in items.items() if predicate(i)]
    check(len(found) == 1, f"exactly one {what} at top level", f"found {found}")
    return found[0]


def staff_target(staff, command: str, serial: str) -> None:
    staff.events.drain()
    staff.say(command)
    if staff.wait_for(Event.TARGET_REQUEST, timeout=5) is None:
        raise RuntimeError(f"{command}: no target cursor")
    staff.target(serial)
    time.sleep(1.0)


def wait_state(client, predicate, what: str, timeout: float = 10) -> None:
    check(client.wait(lambda: predicate(client.state), timeout=timeout), what)


def main(player_session: str, staff_session: str) -> None:
    p = connect(player_session)
    staff = connect(staff_session)
    me = p.state["charID"]
    x, y, z = p.state["charPosX"], p.state["charPosY"], p.state["charPosZ"]
    staff.say(f"[go {x} {y} {z}")
    time.sleep(1.5)

    items = pack(p)
    bandage = one(items, lambda i: i["name"] == "clean bandage", "bandage stack")
    check(items[bandage]["amount"] == 50, "bandage stack is 50", str(items[bandage]["amount"]))
    ward = one(items, lambda i: i["graphic"] == WARD_GRAPHIC, "starter Backpack Ward")
    weapon_serial = next(
        (s for s, i in items.items() if i["name"] in ("wooden shield",)),
        None,
    )
    check(weapon_serial is not None, "shield present for the ordinary death case")
    shield = weapon_serial

    # Ordinary death: G's plain Newbied gear (no Nontransferable) survives, same stock routing
    # already proven for other starter systems.
    staff_target(staff, "[kill", me)
    wait_state(p, lambda s: s.get("charGhost") is True, "player died (ghost)")
    after = pack(p)
    check(bandage in after, "Newbied bandage stack kept on an ordinary death")
    check(shield in after, "Newbied shield kept on an ordinary death")
    check(ward in after, "Nontransferable starter Ward kept (unaffected by G)")

    # Murderer death: G's Newbied (not Nontransferable) gear now goes to the corpse; the
    # Nontransferable Ward still stays, per the unchanged F/E rule.
    staff_target(staff, "[res", me)
    wait_state(p, lambda s: s.get("charGhost") is False, "player resurrected")
    staff_target(staff, "[set Kills 5", me)
    wait_state(p, lambda s: s.get("notoriety") == "Murderer", "player is a murderer")
    staff_target(staff, "[kill", me)
    wait_state(p, lambda s: s.get("charGhost") is True, "murderer died (ghost)")
    after = pack(p)
    check(bandage not in after, "murderer's Newbied bandage stack went to the corpse")
    check(shield not in after, "murderer's Newbied shield went to the corpse")
    check(ward in after, "murderer's Nontransferable starter Ward still kept")

    staff_target(staff, "[res", me)
    staff_target(staff, "[set Kills 0", me)
    print("DONE starter combat death ruling cases", flush=True)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    main(sys.argv[1], sys.argv[2])
