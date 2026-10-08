"""Real-client pictures of the blue travel fire (docs/Camp-Travel-Blue-Fire-Proposal.md), on the host of camp_travel_live.py.

    python -u blue_fire_realclient.py lighter    # CtLight is a real client: lights a blue and an ordinary fire; day, night, the name, the notices
    python -u blue_fire_realclient.py traveler   # CtTrav is a real client: the camp list (one camp for each lighter) and the guide page

Needs the host and characters of camp_travel_live.py with the staff session `admin` running and the Navrey session of the character that is
about to be the real client stopped first (Stop-NavreySession.ps1). Pictures go to work/blue-fire/real/<name>.png (the whole client window,
1296 x 839), then crop_game_view.ps1 cuts them to the game view.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import camp_travel_live as live  # noqa: E402
from camp_travel_live import CAMP, check  # noqa: E402

WORKSPACE = live.WORKSPACE
SCRIPTS = WORKSPACE / ".claude" / "scripts"
sys.path.insert(0, str(SCRIPTS))
from navrey_session import connect  # noqa: E402
from staff_command import staff_target  # noqa: E402

OUT = WORKSPACE / "work" / "blue-fire" / "real"
OUT.mkdir(parents=True, exist_ok=True)
SERIAL = {"CtLight": "0x0000A705", "CtTrav": "0x0000A706", "CtThird": "0x0000A707"}
PLAYER_AT = (466, 324)  # where the client centres the player's tile in the 1296 x 839 window


def ps(script: str, *args: str, timeout: int = 180) -> str:
    out = subprocess.run(["pwsh", "-NoProfile", "-File", str(SCRIPTS / script), *args], capture_output=True, text=True, timeout=timeout)
    return (out.stdout + out.stderr).strip()


class Shots:
    def __init__(self, who: str) -> None:
        self.who = who
        self.admin = connect("admin")

    def say(self, command: str, wait: float = 1.0) -> None:
        self.admin.say(command)
        time.sleep(wait)

    def probe(self, who: str, *args) -> None:
        self.say(f"[TestOnlyCamp {SERIAL[who]} " + " ".join(str(a) for a in args), 0.9)

    def report(self, who: str) -> dict:
        path = live.HOST / f"campprobe-{int(SERIAL[who], 16):X}.json"
        before = path.stat().st_mtime_ns if path.exists() else 0
        self.probe(who, "report")
        for _ in range(30):
            if path.exists() and path.stat().st_mtime_ns != before:
                break
            time.sleep(0.1)
        return json.loads(path.read_text())

    def shot(self, name: str, wait: float = 1.2) -> None:
        time.sleep(wait)
        path = ps("Get-PlayerClientShot.ps1", "-Name", self.who, "-Label", f"blue-{name}").splitlines()[-1].strip()
        shutil.copyfile(path, OUT / f"{name}.png")
        print("shot", name, flush=True)

    def click(self, x: int, y: int, right: bool = False) -> None:
        args = ["-Name", self.who, "-X", str(x), "-Y", str(y)] + (["-Right"] if right else [])
        ps("Send-PlayerClientInput.ps1", *args)
        time.sleep(0.8)

    def clear_gumps(self) -> None:
        for _ in range(2):
            self.click(230, 165, right=True)

    def ensure_alive(self, who: str) -> None:
        """An earlier scenario can leave a character dead (guards kill a criminal in Britain); a ghost sees a grey world and no fires."""
        if not self.report(who)["alive"]:
            self.say(f"[go {SERIAL[who]}", 1.5)
            staff_target(self.admin, "[Resurrect", SERIAL[who])
            time.sleep(2.0)
            self.probe(who, "cond", "clear")
            check(self.report(who)["alive"], f"{who} is alive again")


def stage_lighter() -> None:
    s = Shots("CtLight")
    s.ensure_alive("CtLight")
    s.clear_gumps()
    s.say("[TestOnlyFlagOverride CampTravelBlueFire true")
    s.say("[GlobalLight 0")
    s.probe("CtLight", "firekill")
    s.probe("CtLight", "skill", 100)
    s.probe("CtLight", "kindling", 5)
    s.probe("CtLight", "move", *live.ORIGIN)  # a town has no level bare patch, so look from the countryside
    s.say(f"[TestOnlyFires {SERIAL['CtLight']} flat", 3.0)
    me = s.report("CtLight")
    x0, y0 = me["x"] + 17, me["y"] - 5  # the open grass east of the farm plots, away from the rocks and crops
    s.probe("CtLight", "move", x0, y0)
    print("standing at", x0, y0, flush=True)

    # The real path: Kindling lights the first fire, which burns blue, and the lighter is told.
    def light_fire() -> bool:
        for _ in range(6):
            s.say(f"[TestOnlyDoubleClick {SERIAL['CtLight']} Kindling", 1.4)
            if s.report("CtLight")["fires"]:
                return True
        return False

    check(light_fire(), "the first fire is lit with Kindling")
    s.shot("1-lit-blue")
    first = s.report("CtLight")["fires"][0]
    check(first["travelFire"] and first["hue"] != 0, "the first fire burns blue", str(first))

    # Six tiles screen-left of it, a second fire: ordinary, and the lighter is told where the travel fire is.
    s.probe("CtLight", "move", x0 - 6, y0 + 6)
    before = len(s.report("CtLight")["fires"])
    for _ in range(6):
        s.say(f"[TestOnlyDoubleClick {SERIAL['CtLight']} Kindling", 1.4)
        if len(s.report("CtLight")["fires"]) > before:
            break
    fires = s.report("CtLight")["fires"]
    check(len(fires) == 2, "a second fire is lit", str(fires))
    s.shot("2-lit-ordinary")

    # Both in view, by day and at night.
    s.probe("CtLight", "move", x0 - 3, y0 + 3)
    time.sleep(10.0)  # the notices fade
    s.shot("3-both-day", 0.5)
    s.say("[GlobalLight 12", 1.5)
    s.shot("4-both-night", 0.5)
    s.say("[GlobalLight 0", 1.0)

    # The single-click name of the travel fire.
    me = s.report("CtLight")
    blue = next(f for f in me["fires"] if f["travelFire"])
    dx, dy = blue["x"] - me["x"], blue["y"] - me["y"]
    sx, sy = PLAYER_AT[0] + (dx - dy) * 22, PLAYER_AT[1] + (dx + dy) * 22 + 2
    print("blue fire on screen at", sx, sy, flush=True)
    s.click(sx, sy)
    s.shot("5-name", 0.3)
    print("done", flush=True)


def stage_traveler() -> None:
    s = Shots("CtTrav")
    s.ensure_alive("CtTrav")
    s.clear_gumps()
    s.say("[TestOnlyFlagOverride CampTravelBlueFire true")
    s.say("[GlobalLight 0")
    s.probe("CtLight", "firekill")
    for who in ("CtLight", "CtThird"):
        s.probe(who, "skill", 70)
        s.probe(who, "kindling", 5)
    s.probe("CtLight", "party", SERIAL["CtTrav"], SERIAL["CtThird"])
    s.probe("CtLight", "move", *CAMP)
    s.probe("CtLight", "fire")
    s.probe("CtThird", "move", CAMP[0] + 20, CAMP[1] + 20)
    s.probe("CtThird", "fire")
    s.probe("CtTrav", "move", *live.ORIGIN)
    s.probe("CtLight", "move", CAMP[0] + 6, CAMP[1] + 6)
    s.probe("CtLight", "fire")  # a second fire of the same lighter: ordinary, and not on the list
    time.sleep(10.0)  # secure
    s.clear_gumps()
    s.say(f"[TestOnlyCamp {SERIAL['CtTrav']} cmd [CampTravel", 3.0)
    s.shot("6-camp-list")
    s.clear_gumps()
    s.say(f"[TestOnlyShow {SERIAL['CtTrav']} welcome camp", 2.5)
    s.shot("7-guide-camp-travel")
    s.clear_gumps()
    print("done", flush=True)


if __name__ == "__main__":
    stages = {"lighter": stage_lighter, "traveler": stage_traveler}

    if len(sys.argv) != 2 or sys.argv[1] not in stages:
        print(__doc__)
        sys.exit(2)

    stages[sys.argv[1]]()
