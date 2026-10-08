"""Live checks of the blue travel fire (docs/Camp-Travel-Blue-Fire-Proposal.md) on a disposable host.

    python camp_travel_blue_fire_live.py blue

Needs the host and characters of camp_travel_live.py (CtLight, CtTrav, CtThird; work/hosts/camp-travel, built by work/camp-travel/host.ps1
or work/blue-fire/host.ps1), the TestOnlyProbe and CampTravelProbe loaded, and a staff session `admin`. The flag campTravelBlueFire is
switched in memory with [TestOnlyFlagOverride, as the file ships it off. Prints one line per case and exits non-zero on the first failure.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import camp_travel_live as live  # noqa: E402
from camp_travel_live import CAMP, Rig, check  # noqa: E402

sys.path.insert(0, str(live.WORKSPACE / ".claude" / "scripts"))
from staff_command import go_to, staff_target  # noqa: E402

LIGHT, TRAV, THIRD = "CtLight", "CtTrav", "CtThird"
SECOND = (CAMP[0] + 14, CAMP[1] + 14)
THIRD_SPOT = (CAMP[0] - 14, CAMP[1] - 14)
FLAG = "CampTravelBlueFire"
KINDLING = "Kindling"


def hue_of_config() -> int:
    rules = json.loads((live.HOST / "Configuration" / "shard-rules.json").read_text())
    return int(rules["campTravel"]["fireHue"])


def fires_by_spot(rig: Rig, name: str = LIGHT) -> dict:
    return {(f["x"], f["y"]): f for f in rig.rep(name)["fires"]}


def listed(rig: Rig, name: str, lighter: str) -> int:
    """How many entries of the camp list name this lighter (0 when no list opens)."""
    if rig.request(name) != "LIST":
        return 0
    g = rig.gump(name, "Travel to a party member's camp", timeout=3.0)
    return sum(f"{lighter}'s camp" in line for line in g["text"])


def hex_serial(value: int) -> str:
    return f"0x{value:08X}"


def put_out(rig: Rig, fire: dict, seconds: float = 190.0) -> None:
    """Age the fire at this spot until it is embers, as time would (a fire sets its own state from its age, so Status cannot be set)."""
    rig.probe(LIGHT, "move", fire["x"], fire["y"])
    check("aged 1 fires" in rig.probe(LIGHT, "age", seconds), "the fire is aged to embers")


def stage_blue() -> None:
    rig = Rig()
    hue = hue_of_config()

    # B1: the flag off is the old rule: every fire is a travel fire, two fires are two camps, and no fire is hued.
    rig.flag(FLAG, False)
    rig.reset(skill=65.0)
    for spot in (CAMP, SECOND):
        rig.probe(LIGHT, "move", *spot)
        rig.probe(LIGHT, "fire")
    time.sleep(9.5)
    fires = fires_by_spot(rig)
    check(len(fires) == 2, "B1 two fires burn", str(list(fires)))
    check(all(f["hue"] == 0 and f["travelFire"] and not f["name"] for f in fires.values()), "B1 flag off: both are travel fires, unhued and unnamed")
    check(listed(rig, TRAV, LIGHT) == 2, "B1 flag off: one lighter appears twice in the camp list")
    rig.close_gumps(TRAV)

    # B2: switched on with two fires already burning, the older takes the claim; the other is ordinary.
    rig.flag(FLAG, True)
    time.sleep(2.5)
    fires = fires_by_spot(rig)
    old, new = fires[CAMP], fires[SECOND]
    check(old["travelFire"] and old["hue"] == hue and old["name"] == "CtLight's travel campfire", "B2 the older fire is the blue travel fire",
          f"hue {old['hue']} name {old['name']}")
    check(not new["travelFire"] and new["hue"] == 0 and not new["name"], "B2 the newer fire is ordinary: unhued, unnamed")
    check(listed(rig, TRAV, LIGHT) == 1, "B2 the camp list shows one camp for the lighter")
    rig.close_gumps(TRAV)

    # B3: travel to the blue fire works and is counted on that fire only.
    trip = rig.travel(TRAV)
    check(rig.said(TRAV, trip["mark"], "You arrive at CtLight's camp.", timeout=8), "B3 a party member travels to the blue fire")
    fires = fires_by_spot(rig)
    check(fires[CAMP]["arrivals"] == 1 and fires[SECOND]["arrivals"] == 0, "B3 the arrival is counted on the blue fire only")

    # B4: when the blue fire goes to embers the claim passes to the other burning fire, and the lighter is told.
    mark = rig.mark(LIGHT)
    put_out(rig, fires[CAMP])
    time.sleep(2.5)
    fires = fires_by_spot(rig)
    check(fires[CAMP]["status"] == "Off" and fires[CAMP]["hue"] == 0 and not fires[CAMP]["name"] and not fires[CAMP]["travelFire"],
          "B4 the embers fire is no longer blue", str(fires[CAMP]))
    check(fires[SECOND]["travelFire"] and fires[SECOND]["hue"] == hue and fires[SECOND]["name"] == "CtLight's travel campfire",
          "B4 the other burning fire now holds the claim and burns blue")
    check(rig.said(LIGHT, mark, "Your travel fire is down to embers"), "B4 the lighter is told the travel fire is in embers")
    check(rig.said(LIGHT, mark, "Your campfire burns blue."), "B4 the lighter is told the other fire burns blue")
    check(listed(rig, TRAV, LIGHT) == 1, "B4 the list shows the one blue camp")
    rig.close_gumps(TRAV)

    # B5: embers fed back to life while another fire holds the claim come back ordinary.
    mark = rig.mark(LIGHT)
    rig.probe(LIGHT, "move", *CAMP)
    rig.probe(LIGHT, "kindling", 5)
    rig.admin.say(f"[TestOnlyDoubleClick {rig.hexid(LIGHT)} {KINDLING}")
    check(rig.said(LIGHT, mark, "The embers flare back to life."), "B5 the lighter feeds the embers")
    time.sleep(2.5)
    fires = fires_by_spot(rig)
    check(fires[CAMP]["status"] == "Burning" and not fires[CAMP]["travelFire"] and fires[CAMP]["hue"] == 0, "B5 the relit fire is ordinary: the other fire holds the claim")
    check(fires[SECOND]["travelFire"], "B5 the travel fire is still the other one")
    check(not rig.said(LIGHT, mark, "Your campfire burns blue.", timeout=2.0), "B5 no blue notice for the relit ordinary fire")

    # B6: a lighter whose Camping falls under 50 loses the blue; at 50 the oldest burning fire takes it back.
    mark = rig.mark(LIGHT)
    rig.probe(LIGHT, "skill", 45.0)
    time.sleep(2.5)
    fires = fires_by_spot(rig)
    check(not any(f["travelFire"] or f["hue"] for f in fires.values()), "B6 under Camping 50 no fire is blue")
    check(rig.said(LIGHT, mark, "no longer burns blue"), "B6 the lighter is told why")
    mark = rig.mark(LIGHT)
    rig.probe(LIGHT, "skill", 65.0)
    time.sleep(2.5)
    fires = fires_by_spot(rig)
    check(fires[CAMP]["travelFire"] and fires[CAMP]["hue"] == hue and not fires[SECOND]["travelFire"], "B6 at Camping 65 the oldest burning fire is blue again")
    check(rig.said(LIGHT, mark, "Your campfire burns blue."), "B6 the lighter is told it burns blue")

    # B7: a second lighter has a travel fire of their own; the list shows one camp for each of them.
    rig.probe(THIRD, "skill", 65.0)
    rig.probe(THIRD, "kindling", 5)
    rig.probe(THIRD, "move", *THIRD_SPOT)
    rig.probe(THIRD, "fire")
    time.sleep(2.5)
    mine = {(f["x"], f["y"]): f for f in rig.rep(THIRD)["fires"]}
    theirs = mine[THIRD_SPOT]
    check(theirs["travelFire"] and theirs["hue"] == hue and theirs["name"] == "CtThird's travel campfire", "B7 another lighter's fire is blue and named for them")
    check(fires_by_spot(rig)[CAMP]["travelFire"], "B7 the first lighter's travel fire is unaffected")
    rig.probe(TRAV, "move", *live.ORIGIN)
    camps = (listed(rig, TRAV, LIGHT), 0)
    g = rig.gump(TRAV, "Travel to a party member's camp", timeout=3.0)
    camps = (camps[0], sum("CtThird's camp" in line for line in g["text"]) if g else 0)
    check(camps == (1, 1), "B7 the list shows one camp for each lighter", str(camps))
    rig.close_gumps(TRAV)

    # B8: the real path, lighting with Kindling: the first fire burns blue, a second one lit elsewhere is ordinary.
    rig.reset(skill=100.0)
    rig.probe(LIGHT, "move", *CAMP)
    mark = rig.mark(LIGHT)
    for _ in range(6):
        rig.admin.say(f"[TestOnlyDoubleClick {rig.hexid(LIGHT)} {KINDLING}")
        time.sleep(1.2)
        if rig.rep(LIGHT)["fires"]:
            break
    time.sleep(2.0)
    lit = rig.rep(LIGHT)["fires"]
    check(len(lit) == 1 and lit[0]["travelFire"] and lit[0]["hue"] == hue, "B8 a fire lit with Kindling burns blue", str(lit))
    check(rig.said(LIGHT, mark, "Your campfire burns blue."), "B8 the lighter is told, with the one-at-a-time rule")
    check(rig.said(LIGHT, mark, "You can have one travel fire at a time."), "B8 the notice says there is one travel fire at a time")
    rig.probe(LIGHT, "move", CAMP[0] + 8, CAMP[1] + 8)
    mark = rig.mark(LIGHT)
    for _ in range(6):
        rig.admin.say(f"[TestOnlyDoubleClick {rig.hexid(LIGHT)} {KINDLING}")
        time.sleep(1.2)
        if len(rig.rep(LIGHT)["fires"]) > 1:
            break
    time.sleep(2.0)
    both = rig.rep(LIGHT)["fires"]
    ordinary = [f for f in both if not f["travelFire"]]
    check(len(both) == 2 and len(ordinary) == 1 and ordinary[0]["hue"] == 0, "B8 a second fire lit with Kindling is ordinary", str(both))
    check(rig.said(LIGHT, mark, "This is an ordinary campfire. Your travel fire is still burning near"), "B8 the lighter is told where the travel fire is")

    # B9: fires put out take the claim with them; the lighter is told, and the next fire burns blue.
    mark = rig.mark(LIGHT)
    rig.probe(LIGHT, "firekill")
    check(rig.said(LIGHT, mark, "The next fire you light will burn blue."), "B9 the lighter is told the next fire will burn blue")
    time.sleep(1.5)
    rig.probe(LIGHT, "move", *CAMP)
    rig.probe(LIGHT, "fire")
    time.sleep(2.5)
    again = rig.rep(LIGHT)["fires"]
    check(len(again) == 1 and again[0]["travelFire"] and again[0]["hue"] == hue, "B9 the next fire burns blue")

    # B10: under Camping 50 a fire is ordinary, takes nobody, and the list says no camp burns.
    rig.reset(skill=45.0)
    mark = rig.mark(LIGHT)
    rig.probe(LIGHT, "move", *CAMP)
    rig.probe(LIGHT, "fire")
    time.sleep(2.5)
    low = rig.rep(LIGHT)["fires"]
    check(len(low) == 1 and not low[0]["travelFire"] and low[0]["hue"] == 0, "B10 a fire lit under Camping 50 is ordinary")
    check(rig.said(LIGHT, mark, "once your Camping skill is 50 or higher"), "B10 the lighter is told what it takes")
    said = rig.request(TRAV)
    check(said != "LIST" and "None of your party has a campfire burning" in said, "B10 the list has nothing to offer", said.strip()[:120])

    rig.flag(FLAG, False)


STAGES = {"blue": stage_blue}

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in STAGES:
        print(__doc__)
        sys.exit(2)
    STAGES[sys.argv[1]]()
    print(f"ALL PASS: {sys.argv[1]}", flush=True)
