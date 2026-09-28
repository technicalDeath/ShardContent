"""Live check of the owner's 2026-09-28 starter rulings on a disposable host.

- Starter-issued items (including the free Backpack Ward) are newbied and permanently
  nontransferable. Stock ModernUO keeps nontransferable items loose in the owner's backpack only
  (no bags) and keeps them through every death, murderer or not.
- The starter bag is a plain stock Bag.
- Ordinary newbied items stay protected inside bags (KeptItemDeathRouting); a murderer still loses
  them, as stock UOR.

Needs a disposable host with alpha3EnablementAcknowledged, alpha3StarterBag and
alpha3StarterScissors on, and automaticMurderAdjudication/knockedOut off so [set Kills 5 makes a
murderer. Sessions come from .claude/scripts/Start-NavreySession.ps1: a staff session and an
ordinary session whose character was just created with those flags on.

    python starter_death_live.py <player-session> <staff-session>

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
BAG_GRAPHIC = 0xE76


def check(condition: bool, case: str, detail: str = "") -> None:
    print(f"{'PASS' if condition else 'FAIL'} {case}{': ' + detail if detail else ''}", flush=True)
    if not condition:
        sys.exit(1)


def pack(client) -> dict:
    """Top-level backpack contents by serial, after (re)opening the backpack."""
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

    # ModernUO's Young system (on by default) keeps every item of a new account through death,
    # which would mask the rules under test. Clear it for this character only.
    staff.say(f"[go {x} {y} {z}")
    time.sleep(1.5)
    staff_target(staff, "[set Young false", me)

    # E1: creation issues one plain (regular) bag, one pair of scissors and the Ward.
    items = pack(p)
    bag = one(items, lambda i: i["graphic"] == BAG_GRAPHIC, "plain bag")
    check(items[bag]["name"] == "bag", "bag is a stock Bag (no starter name)", items[bag]["name"])
    scissors = one(items, lambda i: i["name"] == "scissors", "scissors")
    ward = one(items, lambda i: i["graphic"] == WARD_GRAPHIC, "starter Backpack Ward")
    katana = one(items, lambda i: i["name"] == "katana", "stock newbied katana")
    dagger = one(items, lambda i: i["name"] == "dagger", "stock newbied dagger")

    # E2: stock nontransferable rule. Starter items cannot enter any bag, even inside the backpack.
    check(not p.move(scissors, bag, timeout=4), "scissors refused by the plain bag")
    check(not p.move(ward, bag, timeout=4), "starter Ward refused by the plain bag (no special exception)")
    items = pack(p)
    check(scissors in items and ward in items, "refused starter items stayed loose in the backpack")

    # E3: ordinary death. The newbied katana comes back out of the bag; the regular bag goes to
    # the corpse; nontransferable starter items stay.
    check(p.move(katana, bag), "stock newbied katana moved into the plain bag")
    staff_target(staff, "[kill", me)
    wait_state(p, lambda s: s.get("charGhost") is True, "player died (ghost)")
    after = pack(p)
    check(katana in after, "newbied katana kept even though it was inside a bag")
    check(dagger in after, "newbied dagger kept")
    check(scissors in after, "starter scissors kept")
    check(ward in after, "starter Ward kept, not destroyed")
    check(bag not in after, "regular plain bag went to the corpse")

    # E4: murderer death. Stock UOR: newbied items drop; nontransferable starter items still stay.
    staff_target(staff, "[res", me)
    wait_state(p, lambda s: s.get("charGhost") is False, "player resurrected")
    staff_target(staff, "[set Kills 5", me)
    wait_state(p, lambda s: s.get("notoriety") == "Murderer", "player is a murderer")
    staff_target(staff, "[kill", me)
    wait_state(p, lambda s: s.get("charGhost") is True, "murderer died (ghost)")
    after = pack(p)
    check(katana not in after and dagger not in after, "murderer's newbied katana and dagger went to the corpse")
    check(scissors in after, "murderer's starter scissors kept (nontransferable)")
    check(ward in after, "murderer's starter Ward kept (nontransferable)")

    # Leave the disposable character alive and not red.
    staff_target(staff, "[res", me)
    staff_target(staff, "[set Kills 0", me)
    print("DONE starter death ruling cases", flush=True)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    main(sys.argv[1], sys.argv[2])
