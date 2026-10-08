"""Real-client checks for the lying-down Knocked Out look, the countdowns and the Execute menu entry (2026-10-07).

    python -u knocked_out_lying_realclient.py placeeda        # Eda, Vik and Bea onto the Buccaneer's Den dock (QOL_SPOT moves the spot)
    python -u knocked_out_lying_realclient.py ko menu         # Knock Vik out (Eda the attacker), Eda clicks the lying figure: the menu
    python -u knocked_out_lying_realclient.py ko exec X Y     # same, then click Execute at screen X,Y: countdown, death, corpse
    python -u knocked_out_lying_realclient.py ko cancel X Y   # same, then move Eda away mid-countdown
    python -u knocked_out_lying_realclient.py ko wake         # shots at about 26 s (still lying) and 31 s (standing)
    python -u knocked_out_lying_realclient.py arrive          # Bea walks into view mid-knockout and sees Vik already lying
    python -u knocked_out_lying_realclient.py mounted         # a rider (ethereal horse statuette) is knocked off and lies down

Eda and Bea are real ClassicUO clients (Start-PlayerClient.ps1); Vik is a Navrey session started with -EnvFrom work\\accounts\\Vik.env; the
admin Navrey session does the staff work. EDA and BEA are the characters' serials on the host (QOL_EDA, QOL_BEA); QOL_VIK_XY is where the
lying victim is drawn in Eda's window. The Knock Out comes from the probe verb `[TestOnlyState <victim> kofrom <attacker>`, which calls
KnockedOutService.TryInterceptLethalDamage (a double-click in the real client could not be made to land the finishing blow on cue).
A staff recover followed by a new Knock Out inside the first one's 30 s ends the new one early only on a build without
KnockedOutService.SupersededRecovery; wait out the old one between runs on such a build.
"""
import os
import re
import subprocess
import sys
import time

ARGS = sys.argv[1:]
sys.argv = [sys.argv[0], "NONE"]
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "execute_countdown_live.py"), encoding="utf-8").read().split("CASES = [")[0]
src = src.replace('NAMES = ["Eda", "Vik", "Bea", "Pru", "Gus"]', 'NAMES = ["Vik"]')
exec(src)

HOT = tuple(int(v) for v in os.environ.get("QOL_SPOT", "2760,2166,0").split(","))   # where the fight is staged (inside the Hot Zone)
PW = "pwsh"
VIK_XY = tuple(int(v) for v in os.environ.get("QOL_VIK_XY", "470,350").split(","))   # where the victim is drawn in the executor client
EDA = os.environ.get("QOL_EDA", "0x0000A665")
BEA = os.environ.get("QOL_BEA", "0x0000A667")
SCRIPTS_DIR = SCRIPTS


def ps(script: str, *args: str, timeout: int = 180) -> str:
    out = subprocess.run([PW, "-NoProfile", "-File", os.path.join(SCRIPTS_DIR, script), *args], capture_output=True, text=True, timeout=timeout)
    return (out.stdout + out.stderr).strip()


def click(name: str, x: int, y: int, **kw) -> None:
    extra = [f"-{k}" for k, v in kw.items() if v]
    ps("Send-PlayerClientInput.ps1", "-Name", name, "-X", str(x), "-Y", str(y), *extra)


def key(name: str, k: str) -> None:
    ps("Send-PlayerClientInput.ps1", "-Name", name, "-Key", k)


def shot(name: str, label: str) -> str:
    out = ps("Get-PlayerClientShot.ps1", "-Name", name, "-Label", label)
    path = out.splitlines()[-1].strip()
    print("shot", name, label, path, flush=True)
    return path


def admin_target(command: str, serial_hex: str, near=None) -> None:
    if isinstance(near, str):          # a serial: go to that character wherever it is
        adm.say(f"[go {near}")
        time.sleep(1.5)
    elif near is not None:
        adm.say(f"[go {near[0]} {near[1]} {near[2]}")
        time.sleep(1.5)
    staff_target(adm, command, serial_hex)


def place_serial(serial_hex: str, x: int, y: int, z: int, near) -> None:
    admin_target(f'[set Location "({x}, {y}, {z})"', serial_hex, near)


def stage() -> None:
    # Eda outside the Hot Zone, so that she logs back in where she stands
    reset("Vik")
    adm.say(f"[KnockedOutRecover {serial('Vik')}")
    time.sleep(1)
    sset("Vik", f"[set Hits {max_hits('Vik')}")
    c = connect("Eda")
    print("Eda state", c.state["charPosX"], c.state["charPosY"], flush=True)
    sset_eda = lambda cmd: (go_to(adm, c), staff_target(adm, cmd, str(c.state["charID"])))
    sset_eda("[set Criminal false")
    sset_eda(f'[set Location "({OUTSIDE[0]}, {OUTSIDE[1]}, {OUTSIDE[2]})"')
    time.sleep(1)
    print(ps("Stop-NavreySession.ps1", "-Name", "Eda"), flush=True)
    time.sleep(3)
    print(ps("Start-PlayerClient.ps1", "-Name", "Eda", timeout=240)[-300:], flush=True)
    time.sleep(2)
    # into the Hot Zone: Vik one tile east of Eda, Bea two tiles south-east
    place_serial(EDA, HOT[0], HOT[1], HOT[2], EDA)
    place("Vik", HOT[0] + 1, HOT[1], HOT[2])
    place_serial(BEA, HOT[0] + 1, HOT[1] + 2, HOT[2], (1434, 1699, 2))
    print("staged", flush=True)


def knock_out(timeout: float = 45) -> float:
    adm.say(f"[KnockedOutRecover {serial('Vik')}")
    time.sleep(1.2)
    revive("Vik")
    place("Vik", HOT[0] + 1, HOT[1], HOT[2])
    place_serial(EDA, HOT[0], HOT[1], HOT[2], EDA)
    admin_target("[set Criminal true", EDA, EDA)
    before = audit("knocked-out", "entered", "Vik")
    # the real Knocked Out entry with Eda as the attacker (a person at a keyboard cannot land the blow on cue)
    adm.say(f"[TestOnlyState {serial('Vik')} kofrom {EDA}")
    ok = wait_until(lambda: audit("knocked-out", "entered", "Vik") > before, timeout, 0.2)
    t0 = time.time()
    print("knocked out", ok, flush=True)
    if not ok:
        raise RuntimeError("Vik was not Knocked Out")
    return t0


def ko(mode: str, ex: int = 0, ey: int = 0) -> None:
    t0 = knock_out()
    shot("Bea", "bystander-ko-0")
    click("Eda", *VIK_XY)
    time.sleep(1.4)
    shot("Eda", f"executor-menu-{mode}")
    if mode == "wake":
        time.sleep(max(0.0, 26.0 - (time.time() - t0)))
        shot("Bea", "wake-before")
        time.sleep(max(0.0, 31.5 - (time.time() - t0)))
        shot("Bea", "wake-after")
        shot("Eda", "wake-after-eda")
    elif mode == "cancel":
        click("Eda", ex, ey)
        place_serial(EDA, HOT[0] - 6, HOT[1], HOT[2], EDA)    # the executor is moved away mid-countdown (about 3 s in)
        time.sleep(0.8)
        shot("Eda", "executor-cancelled")
        shot("Bea", "bystander-cancelled")
        place_serial(EDA, HOT[0], HOT[1], HOT[2], EDA)
        shot("Eda", "executor-back")
    elif mode == "exec":
        click("Eda", ex, ey)
        time.sleep(1.3)
        shot("Eda", "executor-countdown")
        shot("Bea", "bystander-countdown")
        time.sleep(3.0)
        shot("Eda", "executor-after")
    else:
        time.sleep(max(0.0, 6.0 - (time.time() - t0)))
        shot("Bea", "bystander-ko-5")
    print(f"elapsed since the Knock Out: {time.time() - t0:.1f} s", flush=True)


if ARGS[0] == "stage":
    stage()
elif ARGS[0] == "ko":
    ko(ARGS[1], *(int(a) for a in ARGS[2:4]))
elif ARGS[0] == "placeeda":
    place_serial(EDA, HOT[0], HOT[1], HOT[2], EDA)
    place("Vik", HOT[0] + 1, HOT[1], HOT[2])
    place_serial(BEA, HOT[0] + 1, HOT[1] + 2, HOT[2], BEA)
    print("placed", flush=True)
elif ARGS[0] == "get":
    m = mark("admin")
    admin_target(f"[get {ARGS[2]}", {"eda": EDA, "bea": BEA}.get(ARGS[1].lower(), ARGS[1]), None)
    time.sleep(1)
    print("\n".join(since("admin", m)[-6:]), flush=True)
elif ARGS[0] == "attack":
    sset("Vik", "[set Hits 40")
    hover_x, hover_y = (int(ARGS[1]), int(ARGS[2])) if len(ARGS) > 2 else (487, 330)
    click("Eda", hover_x, hover_y)
    time.sleep(float(ARGS[3]) if len(ARGS) > 3 else 1.0)
    click("Eda", hover_x, hover_y, Double=True)
    for i in range(4):
        time.sleep(2.0)
        m = mark("admin")
        staff_target(adm, "[get Combatant", EDA)
        staff_target(adm, "[get Hits", "0x0000A616")
        print(i, " | ".join(l[-40:] for l in since("admin", m) if "SYSTEM" in l), flush=True)
    shot("Eda", "attack-test")
elif ARGS[0] == "mounted":
    import json
    adm.say(f"[KnockedOutRecover {serial('Vik')}")
    time.sleep(1.2)
    revive("Vik")
    place("Vik", HOT[0] + 1, HOT[1], HOT[2])
    place_serial(EDA, HOT[0], HOT[1], HOT[2], EDA)
    place_serial(BEA, HOT[0] + 1, HOT[1] + 2, HOT[2], BEA)
    time.sleep(1.5)
    staff_target(adm, "[add EtherealHorse", serial("Vik"))
    time.sleep(2)
    items = json.load(open(os.path.join(WORKSPACE, "work", "navrey-sessions", "Vik", "cuoworld.json")))["items"]
    horse = [i for i in items if i["graphic"] == 0x20DD or "ethereal" in i["name"].lower() or "statuette" in i["name"].lower()]
    print("statuettes near Vik:", horse, flush=True)
    C["Vik"].open_backpack()
    C["Vik"].drop(horse[0]["serial"], C["Vik"].backpack_serial)
    time.sleep(2.0)
    C["Vik"].use(horse[0]["serial"])
    time.sleep(2.5)
    print("Vik mounted:", C["Vik"].state.get("mounted"), flush=True)
    shot("Bea", "mounted-before")
    adm.say(f"[TestOnlyState {serial('Vik')} kofrom {EDA}")
    time.sleep(2.5)
    shot("Bea", "mounted-after-ko")
    shot("Eda", "mounted-after-ko-eda")
    m = mark("Vik")
    time.sleep(0.2)
    print("Vik log:", " | ".join(l[-90:] for l in since("Vik", 0)[-6:]), flush=True)
elif ARGS[0] == "arrive":
    place_serial(BEA, HOT[0] - 40, HOT[1], HOT[2], BEA)
    time.sleep(2.5)
    adm.say(f"[KnockedOutRecover {serial('Vik')}")
    time.sleep(1.2)
    revive("Vik")
    place("Vik", HOT[0] + 1, HOT[1], HOT[2])
    place_serial(EDA, HOT[0], HOT[1], HOT[2], EDA)
    admin_target("[set Criminal true", EDA, EDA)
    adm.say(f"[TestOnlyState {serial('Vik')} kofrom {EDA}")
    time.sleep(2.0)
    place_serial(BEA, HOT[0] + 1, HOT[1] + 2, HOT[2], BEA)
    time.sleep(0.8)
    shot("Bea", "arrive-a")
    time.sleep(1.5)
    shot("Bea", "arrive-b")
