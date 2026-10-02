"""Beta 2a: Hythloth follows the permanent Hot Zone rules. Live cases on a disposable host.

    python -u ShardContent/tests/scenarios/hot-zones/hythloth_live.py [stage ...]

Needs seven fresh ordinary Warrior characters logged in as Navrey sessions named after them, plus the `admin` staff
session (New-TestCharacter.ps1 -HostName <host> -Name Kara,Vona,Elin,Tavi,Pike,Rook,Wren -Profession 1), on a host
with featureFlags.hythlothHotZone on (stages phase1, phase2) or off (stage flagoff), whose server log is the newest
`work/dev-server/logs/server-*.log`.

Roles: Kara attacks and later executes Vona; Elin is a thieves-guild thief (also a blue looter); Pike is a blue
bystander and theft victim; Tavi and Pike are left inside Hythloth for the restart checks; Rook and Wren are only used
for the flag-off control. Shame and Ice (both a few tiles from Hythloth's rectangle) are the "still ordinary" controls.
Entry and exit use the real stock teleporter at 4722,3813 (Fire Island) <-> 5905,16 (Hythloth).
"""

from __future__ import annotations

import glob
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(WORKSPACE, ".claude", "scripts"))

from navrey_session import connect, session  # noqa: E402
from staff_command import go_to, staff_target  # noqa: E402
from uo import Event  # noqa: E402

NAMES = ["Kara", "Vona", "Elin", "Tavi", "Pike", "Rook", "Wren"]
KEYWORDS = ("steal", "stolen", "take the item", "Knocked", "execut", "eligible", "can't", "caught", "Hot Zone",
            "murder", "entered", "left")

HYTH = (5905, 22, 44)        # Hythloth's stock go-location, 26+ tiles from the nearest spawner
HYTH_DOOR = (5905, 16)       # inside end of the entrance teleporter
FIRE_DOOR = (4722, 3813)     # Fire Island end of the entrance teleporter
SHAME = (5395, 126, 0)     # Shame's go-location (33 tiles from its nearest spawner; keep visits short)
ICE = (5763, 189, 0)       # 26 tiles from the nearest Ice creature spawner (Ice's stock go-location is outside its own rectangles)

adm = connect("admin")
C = {}
for _n in NAMES:
    try:
        C[_n] = connect(_n)
    except (RuntimeError, SystemExit):
        pass
SERVER_LOG = max(glob.glob(os.path.join(WORKSPACE, "work", "dev-server", "logs", "server-*.log")), key=os.path.getmtime)
results = []
last_steal = {}


def serial(name: str) -> str:
    return str(C[name].state["charID"])


def notoriety(name: str) -> str:
    return str(C[name].state.get("notoriety"))


def hits(name: str) -> int:
    return int(C[name].state.get("hits", 0))


def pos(name: str) -> tuple:
    s = C[name].state
    return int(s.get("charPosX", 0)), int(s.get("charPosY", 0))


def sset(name: str, command: str) -> None:
    go_to(adm, C[name])
    staff_target(adm, command, serial(name))


def place(name: str, x: int, y: int, z: int) -> None:
    sset(name, f'[set Location "({x}, {y}, {z})"')


def pair(a: str, b: str, spot: tuple) -> None:
    x, y, z = spot
    place(a, x, y, z)
    place(b, x + 1, y, z)
    time.sleep(2.5)


def audit(category: str, decision: str, subject: str = None, other: str = None) -> int:
    with open(SERVER_LOG, errors="replace") as handle:
        text = handle.read()
    if subject is None:
        return len(re.findall(rf"Alpha2 {re.escape(category)} {re.escape(decision)}:", text))
    oth = re.escape(other) if other else r"[^;]*"
    return len(re.findall(
        rf"Alpha2 {re.escape(category)} {re.escape(decision)}: subject=\S+?/{re.escape(subject)}; other=(?:\S+?/)?{oth};", text))


def mark(name: str) -> int:
    with open(session(name)["log"], errors="replace") as handle:
        return len(handle.readlines())


def since(name: str, m: int) -> list:
    with open(session(name)["log"], errors="replace") as handle:
        return [ln.strip() for ln in handle.readlines()[m:]]


def system(lines: list) -> list:
    return [re.sub(r"^\[[\d:.]+\]\s*\[SYSTEM\]\s*", "", ln) for ln in lines if "[SYSTEM]" in ln]


def messages(lines: list) -> str:
    kept = [re.sub(r"^\[[\d:.]+\]\s*", "", ln) for ln in lines if any(k in ln for k in KEYWORDS)]
    return " | ".join(kept) or "(no relevant messages)"


def wait_until(condition, timeout: float, step: float = 0.4) -> bool:
    end = time.time() + timeout
    while time.time() < end:
        if condition():
            return True
        time.sleep(step)
    return False


def record(case_id: str, expected: str, observed: str, ok: bool, obs: bool = False) -> None:
    label = "OBS " if obs else ("PASS" if ok else "FAIL")
    results.append((case_id, ok or obs))
    print(f"{label} {case_id}: expected {expected}; observed {observed}", flush=True)


def stage(label: str, body) -> None:
    print(f"--- {label}", flush=True)
    try:
        body()
    except Exception as error:  # noqa: BLE001 - a harness fault must not hide later stages
        record(label, "stage completes", f"{type(error).__name__}: {error}", False)


def heal(name: str) -> None:
    sset(name, f"[set Hits {C[name].state.get('maxHits', 60)}")


def unequip_weapon(name: str) -> None:
    for item in C[name].state.get("equipped", []):
        if item.get("layer") in ("OneHanded", "TwoHanded"):
            C[name].commands.send(f"unequip {item['serial']}")
            time.sleep(1.2)


def fight(attacker: str, victim: str, seconds: float) -> tuple:
    start = hits(victim)
    a = C[attacker]
    a.war(True)
    time.sleep(0.6)
    a.commands.send(f"attack {serial(victim)} force")
    dropped = wait_until(lambda: hits(victim) < start, seconds)
    a.war(False)
    a.commands.send("stop")
    return dropped, start, hits(victim)


def hot_status(name: str) -> str:
    """`[HotZoneStatus` is staff-only and describes the caller's own tile, so the staff session stands on the player's."""
    go_to(adm, C[name])
    m = mark("admin")
    adm.say("[HotZoneStatus")
    time.sleep(2)
    return " ".join(system(since("admin", m)))


def walk_to(name: str, x: int, y: int, timeout: float = 12) -> bool:
    C[name].commands.send(f"gotoexact {x} {y}")
    return wait_until(lambda: abs(pos(name)[0] - x) > 50 or pos(name) == (x, y), timeout)


def steal(thief: str, item: str) -> list:
    wait = 11.5 - (time.time() - last_steal.get(thief, 0))
    if wait > 0:
        time.sleep(wait)
    m = mark(thief)
    C[thief].commands.send("useskill stealing")
    time.sleep(1.5)
    C[thief].commands.send(f"target {item}")
    time.sleep(3)
    last_steal[thief] = time.time()
    return since(thief, m)


def open_pack(thief: str, victim: str) -> dict:
    pack = str(C[victim].state["backpackID"])
    for _ in range(5):
        C[thief].commands.send(f"use {pack}")
        time.sleep(3)
        items = {}
        for ln in C[thief].call(f"container {pack}"):
            hit = re.search(r"\[item\]\s+(0x[0-9A-Fa-f]+)\s+(.*)", ln)
            if hit:
                items[hit.group(2)] = hit.group(1)
        if items:
            return items
    return {}


def rolled(text: str) -> bool:
    return bool(re.search(r"fail to steal|steal the item|succe?ssfully steal", text)) and "can't steal" not in text


def execute(name: str, victim: str) -> tuple:
    c = C[name]
    m = mark(name)
    c.events.drain()
    c.say("[Execute")
    if c.wait_for(Event.TARGET_REQUEST, timeout=5) is None:
        return "no-cursor", ""
    c.target(serial(victim))
    time.sleep(3)
    text = " ".join(since(name, m))
    if "has been executed" in text:
        return "executed", messages(since(name, m))
    if "not eligible" in text:
        return "refused", messages(since(name, m))
    return "other", messages(since(name, m))


def ghost(name: str) -> bool:
    return bool(C[name].state.get("charGhost"))


# ---------------------------------------------------------------- phase 1

def setup() -> None:
    for n in C:
        assert C[n].state.get("connected", True), f"{n} not connected"
        assert notoriety(n) == "Innocent", f"{n} is {notoriety(n)}"
    sset("Elin", "[SetSkill Snooping 100")
    sset("Elin", "[SetSkill Stealing 100")
    sset("Elin", "[set NpcGuild ThievesGuild")
    unequip_weapon("Elin")
    record("S0 setup", "Innocent characters, thief prepared", ", ".join(C), True)


def entry_exit() -> None:
    """Vona walks onto the real entrance teleporter from Fire Island, then back out."""
    place("Vona", FIRE_DOOR[0], FIRE_DOOR[1] + 3, 0)
    time.sleep(3)
    m = mark("Vona")
    inside = walk_to("Vona", *FIRE_DOOR)
    time.sleep(3)
    lines = system(since("Vona", m))
    text = " | ".join(x for x in lines if "entered" in x or "left" in x)
    record("Y1 walking into Hythloth through the stock entrance", "left Fire Island., entered Hythloth, a PvP Hot Zone",
           f"at {pos('Vona')}; {text}",
           pos("Vona")[0] >= 5898 and any(x == "You have left Fire Island." for x in lines)
           and any("entered Hythloth, a PvP Hot Zone" in x for x in lines))

    walk_to("Vona", HYTH_DOOR[0], HYTH_DOOR[1] + 3)
    time.sleep(2)
    m = mark("Vona")
    walk_to("Vona", *HYTH_DOOR)
    time.sleep(3)
    lines = system(since("Vona", m))
    text = " | ".join(x for x in lines if "entered" in x or "left" in x)
    record("Y3 walking out onto Fire Island", "left Hythloth. (no 'no longer applies'), entered Fire Island",
           f"at {pos('Vona')}; {text}",
           pos("Vona")[0] < 5000 and any(x == "You have left Hythloth." for x in lines)
           and any("entered Fire Island" in x for x in lines) and not any("no longer applies" in x for x in lines))


def hostility() -> None:
    revive("Kara")
    revive("Vona")
    sset("Kara", "[set Criminal false")
    pair("Kara", "Vona", HYTH)
    heal("Vona")
    before = audit("hostility", "denied", "Kara", "Vona")
    dropped, start, end = fight("Kara", "Vona", 30)
    record("Y4 blue attacks blue inside Hythloth", "damage lands, attacker becomes Criminal, no denial",
           f"hits {start}->{end}, Kara {notoriety('Kara')}, denied+{audit('hostility', 'denied', 'Kara', 'Vona') - before}",
           dropped and notoriety("Kara") != "Innocent")

    revive("Elin")
    revive("Pike")
    for label, spot in (("Y5 control: the same attack in Shame", SHAME), ("Y6 control: the same attack in Ice", ICE)):
        pair("Elin", "Pike", spot)
        before = audit("hostility", "denied", "Elin", "Pike")
        dropped, start, end = fight("Elin", "Pike", 8)
        status = hot_status("Elin")
        denied = audit("hostility", "denied", "Elin", "Pike") - before
        record(label, "refused, denial audited, Elin Innocent, not Hot",
               f"hits {start}->{end}, denied+{denied}, Elin {notoriety('Elin')}, {status[-60:]}",
               not dropped and denied >= 1 and notoriety("Elin") == "Innocent" and "Hot region: none" in status)


def revive(name: str) -> None:
    if ghost(name):
        sset(name, "[Resurrect")
        wait_until(lambda: not ghost(name), 10)
    heal(name)


def knocked_out() -> None:
    """Kara knocks Vona out inside Hythloth. Everyone stands on Hythloth's go-location row (the row south of it is the
    slope down from the entrance, out of line of sight). The 90-second Knocked Out window bounds the whole stage."""
    for n in ("Kara", "Vona", "Elin", "Pike"):
        revive(n)
    pair("Kara", "Vona", HYTH)
    place("Elin", HYTH[0] + 2, HYTH[1], HYTH[2])  # adjacent to Vona (pair puts her one east of Kara)
    place("Pike", HYTH[0] + 3, HYTH[1], HYTH[2])
    heal("Vona")
    time.sleep(2)
    for t in ("Candle", "Torch", "Lantern"):
        sset("Vona", f"[AddToPack {t}")
    time.sleep(1)
    sset("Vona", "[set Hits 1")
    before = audit("knocked-out", "entered", "Vona", "Kara")
    C["Kara"].war(True)
    time.sleep(0.6)
    C["Kara"].commands.send(f"attack {serial('Vona')} force")
    ko = wait_until(lambda: audit("knocked-out", "entered", "Vona", "Kara") > before, 40)
    C["Kara"].war(False)
    C["Kara"].commands.send("stop")
    t0 = time.time()
    record("Y7 lethal blow inside Hythloth", "Vona Knocked Out (attacker Kara)", f"KO audit {ko}, hits {hits('Vona')}", ko)
    if not ko:
        return

    # K-4 corpse-style looting: an eligible looter opens the Knocked Out pack (no Snooping roll) and drags items out.
    pack = str(C["Vona"].state["backpackID"])
    items = {}
    for _ in range(3):
        C["Elin"].commands.send(f"use {pack}")
        time.sleep(2.5)
        for ln in C["Elin"].call(f"container {pack}"):
            hit = re.search(r"\[item\]\s+(0x[0-9A-Fa-f]+)\s+(.*)", ln)
            if hit:
                items[hit.group(2)] = hit.group(1)
        if items:
            break
    loot = [v for k, v in items.items() if any(w in k.lower() for w in ("candle", "torch", "lantern"))]
    before = audit("knocked-out-loot", "authorized", "Elin", "Vona")
    m = mark("Elin")
    if loot:
        C["Elin"].commands.send(f"get {loot[0]}")
        wait_until(lambda: audit("knocked-out-loot", "authorized", "Elin", "Vona") > before, 6)
        time.sleep(1.5)
    gained = audit("knocked-out-loot", "authorized", "Elin", "Vona") - before
    flagged = audit("knocked-out-loot", "blue-flagged-criminal", "Elin", "Vona")
    record("Y8 a blue loots a Knocked Out blue inside Hythloth (K-4)",
           "pack opens without Snooping, item taken, authorized, looter becomes criminal",
           f"saw {len(items)} items; authorized+{gained}; flagged {flagged}; Elin {notoriety('Elin')}; {messages(since('Elin', m))[-120:]}",
           bool(loot) and gained >= 1 and flagged >= 1 and notoriety("Elin") == "Criminal")

    result, text = execute("Pike", "Vona")
    record("Y9 a blue bystander may not Execute (K-4)", "refused, Vona alive", f"{result}; {text}",
           result == "refused" and not ghost("Vona"))

    # Kara turned criminal by attacking a blue, but that flag lasts two minutes; keep her grey for the Execute.
    if notoriety("Kara") != "Criminal":
        sset("Kara", "[set Criminal true")
    murders = audit("murder", "automatic-count", "Kara", "Vona")
    result, text = execute("Kara", "Vona")
    ok = result == "executed" and wait_until(lambda: ghost("Vona"), 5)
    record("Y10 the criminal recorded attacker may Execute (K-4)", "executed, Vona a ghost",
           f"{result}; {text}; {time.time() - t0:.0f}s into the 90s window", ok)
    record("Y11 murder count for executing an ordinary blue (K-5, observation)", "counted unless Vona attacked first",
           f"murder automatic-count +{audit('murder', 'automatic-count', 'Kara', 'Vona') - murders}", True, obs=True)


def theft() -> None:
    """Elin steals from blue Pike inside Hythloth: the roll happens and Pike's Ward does nothing; in Shame it is refused."""
    revive("Elin")
    revive("Pike")
    pair("Elin", "Pike", HYTH)
    for t in ("Candle", "Torch", "Lantern", "Bottle"):
        sset("Pike", f"[AddToPack {t}")
    time.sleep(1)
    items = open_pack("Elin", "Pike")
    pool = [v for k, v in items.items() if any(w in k.lower() for w in ("candle", "torch", "lantern", "bottle"))]
    if not pool:
        record("Y12 setup", "Elin opens Pike's pack inside Hythloth (snooping a blue is allowed in Hot)", f"saw {sorted(items)}", False)
        return
    record("Y12 snooping a blue inside Hythloth", "pack opens", f"{len(items)} items seen", True)

    ward_before = audit("theft", "ward-activated") + audit("theft", "ward-detected") + audit("theft", "ward-blocked")
    text = messages(steal("Elin", pool[0]))
    ward_after = audit("theft", "ward-activated") + audit("theft", "ward-detected") + audit("theft", "ward-blocked")
    record("Y13 stealing from a blue inside Hythloth reaches the roll; the Ward does nothing (K-6)",
           "roll message, no ward audit", f"{text}; ward audits +{ward_after - ward_before}",
           rolled(text) and ward_after == ward_before)

    pair("Elin", "Pike", SHAME)
    sset("Elin", "[set Criminal false")
    time.sleep(1)
    denied = audit("hostility", "denied", "Elin", "Pike")
    text = ""
    for _ in range(6):  # a Mobile target picks a random pack item; a Newbied one is refused before any hostility check
        text = messages(steal("Elin", serial("Pike")))
        if "can't steal that" not in text:
            break
    record("Y14 control: the same theft in Shame", "no roll, hostility denied",
           f"{text}; denied+{audit('hostility', 'denied', 'Elin', 'Pike') - denied}",
           not rolled(text) and audit("hostility", "denied", "Elin", "Pike") > denied)
    pair("Elin", "Pike", HYTH)  # out of Shame before its elementals arrive


def leave_inside() -> None:
    """Tavi and Pike stay inside Hythloth for the restart and login checks."""
    pair("Tavi", "Pike", HYTH)
    heal("Pike")
    record("Y15 Tavi and Pike parked inside Hythloth for the restart", "placed", f"{pos('Tavi')} {pos('Pike')}",
           pos("Tavi")[0] >= 5898 and pos("Pike")[0] >= 5898)


def status_checks() -> None:
    """[HotZoneStatus readings for the entry and control cases (staff session on each tile)."""
    place("Rook", *HYTH)
    time.sleep(2)
    status = hot_status("Rook")
    record("Y2 [HotZoneStatus inside Hythloth", "Hot region: Hythloth", status[-170:], "Hot region: Hythloth" in status)
    for label, spot, name in (("Y5b Shame is not Hot", SHAME, "Shame"), ("Y6b Ice is not Hot", ICE, "Ice")):
        place("Rook", *spot)
        time.sleep(2)
        status = hot_status("Rook")
        record(label, f"stock region: {name}; Hot region: none", status[-110:],
               f"stock region: {name}; Hot region: none" in status)
    place("Rook", *HYTH)


# ---------------------------------------------------------------- phase 2 (after a restart, flag still on)

def phase2() -> None:
    # Restarting a session starts a new client log, so every line in it is from after the restart.
    with open(session("Pike")["log"], errors="replace") as handle:
        login = [ln for ln in handle if "entered Hythloth" in ln]
    record("R1 logging in inside Hythloth shows the Hot Zone warning", "entered Hythloth message after login",
           login[-1].strip()[-120:] if login else "none", bool(login))
    status = hot_status("Tavi")
    record("R2 membership after a restart", "Hot region: Hythloth", status[-120:], "Hot region: Hythloth" in status)
    pair("Tavi", "Pike", HYTH)
    heal("Pike")
    dropped, start, end = fight("Tavi", "Pike", 30)
    record("R3 blue-on-blue inside Hythloth after a restart", "damage lands", f"hits {start}->{end}, Tavi {notoriety('Tavi')}", dropped)


# ---------------------------------------------------------------- flag off (after a restart with hythlothHotZone false)

def flag_off() -> None:
    pair("Rook", "Wren", HYTH)
    status = hot_status("Rook")
    before = audit("hostility", "denied", "Rook", "Wren")
    dropped, start, end = fight("Rook", "Wren", 8)
    denied = audit("hostility", "denied", "Rook", "Wren") - before
    record("F1 with hythlothHotZone off, Hythloth is ordinary", "refused, denial audited, not Hot",
           f"hits {start}->{end}, denied+{denied}, {status[-120:]}",
           not dropped and denied >= 1 and "Hot region: none" in status and "(hythlothHotZone): False" in status)


def main() -> int:
    print(f"server log {SERVER_LOG}", flush=True)
    stages = [("setup", setup), ("entry", entry_exit), ("status", status_checks), ("hostility", hostility), ("ko", knocked_out), ("theft", theft),
              ("park", leave_inside), ("phase2", phase2), ("flagoff", flag_off)]
    default = ["setup", "entry", "status", "hostility", "ko", "theft", "park"]
    only = sys.argv[1:] or default
    for label, body in stages:
        if label in only:
            stage(label, body)
    failed = [r for r in results if not r[1]]
    print(f"\n{len(results) - len(failed)}/{len(results)} cases passed", flush=True)
    for case_id, _ in failed:
        print("FAILED:", case_id)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
