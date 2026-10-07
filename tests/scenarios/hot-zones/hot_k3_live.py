"""K3 live cases for the outdoor Hot Zones: Execute/looting consequences, K-5 both orders, dungeon control, login/restart.

    python ShardContent/tests/scenarios/hot-zones/hot_k3_live.py phase1     # consequences + persistence seeds
    # then: Stop-DevServer.ps1 (saves), Start-DevServer.ps1 -DistributionPath <host>
    python ShardContent/tests/scenarios/hot-zones/hot_k3_live.py phase2     # post-restart assertions

Needs ten fresh Warrior characters (New-TestCharacter.ps1 -HostName <host> -Name Kara,Vale,Vex,Vim,Tavi,Pike,Elin,Wren,Rook,Nell
-Profession 1) on a disposable host with hotZones on and the TestOnlyProbe loaded (TestOnlyCorpseAggressors).
Placement is by `[set Location`. Case order matters: several cases spend a character's Innocent status or a KO window.
Exits non-zero when any asserted case fails. Cases marked OBS record an observation only.
"""

from __future__ import annotations

import glob
import json
import os
import re
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
SCRIPTS = os.path.join(WORKSPACE, ".claude", "scripts")
sys.path.insert(0, SCRIPTS)

from navrey_session import connect, session  # noqa: E402
from staff_command import go_to, staff_target  # noqa: E402
from uo import Event  # noqa: E402

NAMES = ["Kara", "Vale", "Vex", "Vim", "Tavi", "Pike", "Elin", "Wren", "Rook", "Nell"]
STATE_FILE = os.path.join(WORKSPACE, "work", "k3-state.json")
KEYWORDS = ("steal", "Knocked", "execut", "eligible", "can't", "caught", "Hot Zone", "murder", "recover")
PLAIN_TYPES = ("Candle", "Torch", "Lantern", "Bottle")
FIRE_ISLAND = (4600, 3500, 0)

adm = None
C: dict = {}
results: list = []
SERVER_LOG = ""


def refresh_log() -> None:
    global SERVER_LOG
    SERVER_LOG = max(glob.glob(os.path.join(WORKSPACE, "work", "dev-server", "logs", "server-*.log")), key=os.path.getmtime)


def serial(name: str) -> str:
    return str(C[name].state["charID"])


def hits(name: str) -> int:
    return int(C[name].state.get("hits", 0))


def notoriety(name: str) -> str:
    return str(C[name].state.get("notoriety"))


def ghost(name: str) -> bool:
    return bool(C[name].state.get("charGhost"))


def sset(name: str, command: str) -> None:
    go_to(adm, C[name])
    staff_target(adm, command, serial(name))


def place(name: str, x: int, y: int, z: int) -> None:
    sset(name, f'[set Location "({x}, {y}, {z})"')


def log_text() -> str:
    with open(SERVER_LOG, errors="replace") as handle:
        return handle.read()


def audit(category: str, decision: str, subject: str = None, other: str = None) -> int:
    subj = re.escape(subject) if subject else r"[^;]*"
    oth = re.escape(other) if other else r"[^;]*"
    pattern = rf"Alpha2 {re.escape(category)} {re.escape(decision)}: subject=\S+?/{subj}; other=(?:\S+?/)?{oth};"
    if subject is None:
        pattern = rf"Alpha2 {re.escape(category)} {re.escape(decision)}:"
    return len(re.findall(pattern, log_text()))


def audit_lines(category: str, decision: str, subject: str, other: str) -> list:
    pattern = rf"Alpha2 {re.escape(category)} {re.escape(decision)}: subject=\S+?/{re.escape(subject)}; other=(?:\S+?/)?{re.escape(other)};[^\n]*"
    return re.findall(pattern, log_text())


def mark(name: str) -> int:
    with open(session(name)["log"], errors="replace") as handle:
        return len(handle.readlines())


def since(name: str, m: int) -> list:
    with open(session(name)["log"], errors="replace") as handle:
        return [ln.strip() for ln in handle.readlines()[m:]]


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
    results.append((case_id, expected, observed, ok or obs))
    print(f"{label} {case_id}: expected {expected}; observed {observed}", flush=True)


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


def knock_out(attacker: str, victim: str, timeout: float = 40) -> bool:
    """Victim to 1 hit point, then the attacker lands the lethal blow; True once the KO is audited."""
    sset(victim, "[set Hits 1")
    before = audit("knocked-out", "entered", victim, attacker)
    a = C[attacker]
    a.war(True)
    time.sleep(0.6)
    a.commands.send(f"attack {serial(victim)} force")
    ok = wait_until(lambda: audit("knocked-out", "entered", victim, attacker) > before, timeout)
    a.war(False)
    a.commands.send("stop")
    return ok


def unequip_weapon(name: str) -> None:
    for item in C[name].state.get("equipped", []):
        if item.get("layer") in ("OneHanded", "TwoHanded"):
            C[name].commands.send(f"unequip {item['serial']}")
            time.sleep(1.2)


def revive(name: str) -> None:
    if ghost(name):
        sset(name, "[Resurrect")
        wait_until(lambda: not ghost(name), 10)
    sset(name, f"[set Hits {C[name].state.get('maxHits', 60)}")
    time.sleep(1)


def add_to_pack(victim: str, type_name: str) -> None:
    sset(victim, f"[AddToPack {type_name}")
    time.sleep(1.5)


def loot(thief: str, victim: str, item: str) -> None:
    """Open the victim's pack and drag one item into the thief's own pack: corpse-style looting, no skill."""
    C[thief].commands.send(f"use {C[victim].state.get('backpackID')}")
    time.sleep(2)
    C[thief].commands.send(f"drop {item} {C[thief].state.get('backpackID')}")
    time.sleep(2.5)


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


def corpse_aggressors(victim: str) -> tuple:
    """Server-side Corpse._aggressors of the victim's newest corpse, via the test-only probe command."""
    m = mark("admin")
    adm.say(f"[TestOnlyCorpseAggressors {serial(victim)}")
    time.sleep(2)
    text = " ".join(since("admin", m))
    hit = re.search(r"CorpseAggressors owner=\w+ corpse=(\w+) aggressors=([\d,]+|none)", text)
    if not hit:
        return None, text
    return ([] if hit[2] == "none" else [int(s) for s in hit[2].split(",")]), hit[1]


def pack_items(name: str) -> list:
    """(type, serial, lootType) for each backpack item of the player, via the test-only inspect command."""
    m = mark("admin")
    adm.say(f"[TestOnlyInventoryInspect {serial(name)}")
    time.sleep(2.5)
    text = " ".join(since("admin", m))
    return re.findall(r"backpack: (\w+) serial=(0x[0-9A-Fa-f]+) amount=\d+ lootType=(\w+)", text)


def plain_item_serials(victim: str) -> list:
    return [serial_ for type_, serial_, loot_type in pack_items(victim) if type_ in PLAIN_TYPES and loot_type == "Regular"]


def stage(label: str, body) -> None:
    print(f"--- {label}", flush=True)
    try:
        body()
    except Exception as error:  # noqa: BLE001 - a harness fault must not hide later stages
        record(label, "stage completes", f"{type(error).__name__}: {error}", False)


def pwsh(script: str, *args: str) -> None:
    exe = shutil.which("pwsh") or shutil.which("powershell")
    subprocess.run([exe, "-NoProfile", "-File", os.path.join(SCRIPTS, script), *args], cwd=WORKSPACE, check=True,
                   stdout=subprocess.DEVNULL)


def relog(name: str, start: bool = True) -> None:
    pwsh("Stop-NavreySession.ps1", "-Name", name)
    if start:
        time.sleep(2)
        pwsh("Start-NavreySession.ps1", "-Name", name, "-EnvFrom", os.path.join("work", "accounts", f"{name}.env"))
        C[name] = connect(name)


# ---------------------------------------------------------------- phase 1

def setup() -> None:
    for name in NAMES:
        assert C[name].state.get("connected", True), f"{name} not connected"
        assert notoriety(name) == "Innocent", f"{name} is {notoriety(name)}"
    for name in ("Elin", "Tavi"):
        sset(name, "[SetSkill Snooping 0")
        sset(name, "[SetSkill Stealing 0")
        unequip_weapon(name)
    sset("Tavi", "[set Criminal true")
    m = mark("admin")
    adm.say("[TestOnlyCorpseAggressors 0x0")
    time.sleep(1.5)
    probe = "CorpseAggressors" in " ".join(since("admin", m))
    record("S0 setup", "ten Innocent characters, thieves prepared, probe command loaded", f"probe={probe}", probe)


def hot_group() -> None:
    for name in ("Tavi", "Kara", "Pike"):
        sset(name, "[SetSkill Wrestling 100")
    revive("Vale")
    place("Tavi", 2755, 2166, -2)
    place("Vale", 2756, 2166, -2)
    place("Elin", 2757, 2166, -2)
    place("Pike", 2756, 2167, -2)
    time.sleep(3)
    for type_name in PLAIN_TYPES * 3:
        add_to_pack("Vale", type_name)
    ko =knock_out("Tavi", "Vale")
    t0 = time.time()
    record("KO Tavi knocks out Vale in Hot", "Vale Knocked Out", f"KO audit {ko}, hits {hits('Vale')}", ko)

    murders = audit("murder", "automatic-count", "Pike", "Vale")
    result, text = execute("Pike", "Vale")
    gained = audit("murder", "automatic-count", "Pike", "Vale") - murders
    record("X1 blue bystander executes a Knocked Out blue in Hot", "refused, Vale alive, no murder count",
           f"{result}; {text}; murder+{gained}; KO age {time.time() - t0:.0f}s",
           result == "refused" and not ghost("Vale") and gained == 0)

    before = audit("knocked-out-loot", "authorized", "Elin", "Vale")
    taken = next(serial_ for type_, serial_, loot_type in pack_items("Vale") if type_ == "Torch" and loot_type == "Regular")
    loot("Elin", "Vale", taken)
    gained = audit("knocked-out-loot", "authorized", "Elin", "Vale") - before
    flagged = audit("knocked-out-loot", "blue-flagged-criminal", "Elin", "Vale")
    moved = taken in [item[1] for item in pack_items("Elin")] and taken not in plain_item_serials("Vale")
    record("L1 blue looter opens a Knocked Out blue's pack (no Snooping) and takes an item in Hot",
           "authorized, item moved to Elin, Elin becomes criminal",
           f"authorized+{gained}; moved {moved}; Elin {notoriety('Elin')}; flagged {flagged}; KO age {time.time() - t0:.0f}s",
           gained >= 1 and moved and flagged >= 1 and notoriety("Elin") == "Criminal")

    newbied = [item[1] for item in pack_items("Vale") if item[2] == "Newbied"]
    before = audit("knocked-out-loot", "authorized", "Elin", "Vale")
    if newbied:
        loot("Elin", "Vale", newbied[0])
    still = bool(newbied) and newbied[0] in [item[1] for item in pack_items("Vale")]
    gained = audit("knocked-out-loot", "authorized", "Elin", "Vale") - before
    record("L5 a Newbied starter item cannot be lifted from a Knocked Out pack", "item stays, no authorized audit",
           f"newbied items {len(newbied)}; stayed {still}; authorized+{gained}", still and gained == 0)

    before = audit("knocked-out-loot", "authorized", "Elin", "Vale")
    second = next(serial_ for type_, serial_, loot_type in pack_items("Vale") if type_ == "Lantern" and loot_type == "Regular")
    place("Vale", 2775, 2166, 0)
    place("Elin", 2776, 2166, 0)
    time.sleep(3)
    loot("Elin", "Vale", second)
    gained = audit("knocked-out-loot", "authorized", "Elin", "Vale") - before
    kept = second in plain_item_serials("Vale")
    record("L6 criminal without recorded rights cannot lift outside Hot", "item stays, no authorized audit",
           f"stayed {kept}; authorized+{gained}", kept and gained == 0)
    place("Vale", 2756, 2166, -2)
    place("Elin", 2757, 2166, -2)
    place("Tavi", 2755, 2166, -2)
    time.sleep(3)

    age = time.time() - t0
    murders = audit("murder", "automatic-count", "Tavi", "Vale")
    result, text = execute("Tavi", "Vale")
    gained = audit("murder", "automatic-count", "Tavi", "Vale") - murders
    ok = result == "executed" and wait_until(lambda: ghost("Vale"), 5)
    record("XR red-with-rights executor Executes in Hot", "executed, Vale ghost, murder +1",
           f"{result}; {text}; murder+{gained}; KO age {age:.0f}s", ok and gained == 1)
    time.sleep(2)
    record("XR2 executor is red afterwards", "Tavi Murderer", notoriety("Tavi"), notoriety("Tavi") == "Murderer")

    aggressors, corpse = corpse_aggressors("Vale")
    tavi = int(serial("Tavi"), 16)
    record("X4 corpse aggressor list holds the executor (no criminal-action warning for the executor)",
           "Tavi's serial in the corpse's aggressors", f"aggressors={aggressors}; corpse={corpse}",
           aggressors is not None and tavi in aggressors)


def k5_red_first() -> None:
    """Blue Vex attacks red Tavi first, Tavi retaliates, Knocks Out and Executes Vex: still murder (owner ruling 2026-10-06 amending K-5).

    The blue may lawfully attack a red and the red may fight back and Knock them out, but an Execute is murder unless the victim had
    Criminal Intent on or the two were at guild war. Before that ruling this case counted no murder."""
    revive("Tavi")
    place("Tavi", 2760, 2166, 0)
    place("Vex", 2761, 2166, 0)
    time.sleep(3)
    dropped, start, end = fight("Vex", "Tavi", 30)
    record("X5a-1 blue attacks red first in Hot", "damage lands, Vex stays Innocent (stock: attacking a red is not criminal)",
           f"Tavi hits {start}->{end}; Vex {notoriety('Vex')}", dropped and notoriety("Vex") == "Innocent")
    sset("Tavi", f"[set Hits {C['Tavi'].state.get('maxHits', 60)}")
    ko = knock_out("Tavi", "Vex")
    murders = audit("murder", "automatic-count", "Tavi", "Vex")
    result, text = execute("Tavi", "Vex")
    gained = audit("murder", "automatic-count", "Tavi", "Vex") - murders
    lines = audit_lines("knocked-out", "executed", "Tavi", "Vex")
    exempt = "no murder count" in " ".join(lines[-1:])
    record("X5a red Executes a blue who attacked the red first", "executed, murder +1 (the blue's right to attack the red does not make an Execute lawful)",
           f"KO {ko}; {result}; murder+{gained}; audit: {(lines[-1:] or ['none'])[0][-90:]}",
           ko and result == "executed" and gained == 1 and not exempt)


def k5_grey_first() -> None:
    """Grey Kara attacks blue Vim first, Knocks Out and Executes it: counts as murder, 24 h red."""
    place("Kara", 2764, 2166, 0)
    place("Vim", 2765, 2166, 0)
    time.sleep(3)
    dropped, start, end = fight("Kara", "Vim", 30)
    grey = notoriety("Kara")
    record("X5b-1 blue attacks blue first in Hot", "damage lands, Kara becomes Criminal",
           f"Vim hits {start}->{end}; Kara {grey}", dropped and grey == "Criminal")
    sset("Kara", f"[set Hits {C['Kara'].state.get('maxHits', 60)}")
    ko = knock_out("Kara", "Vim")
    murders = audit("murder", "automatic-count", "Kara", "Vim")
    result, text = execute("Kara", "Vim")
    gained = audit("murder", "automatic-count", "Kara", "Vim") - murders
    time.sleep(2)
    record("X5b grey Executes a victim who never attacked", "executed, murder +1, Kara red",
           f"KO {ko}; {result}; murder+{gained}; Kara {notoriety('Kara')}",
           ko and result == "executed" and gained == 1 and notoriety("Kara") == "Murderer")


def dungeon() -> None:
    place("Wren", 5905, 22, 44)
    place("Rook", 5906, 22, 44)
    time.sleep(4)
    m = mark("Wren")
    before = audit("hostility", "denied", "Wren", "Rook")
    dropped, start, end = fight("Wren", "Rook", 8)
    denied = audit("hostility", "denied", "Wren", "Rook") - before
    record("D1 blue attacks blue inside Hythloth", "refused, denial audited, both Innocent",
           f"hits {start}->{end}; denied+{denied}; Wren {notoriety('Wren')}",
           not dropped and denied >= 1 and notoriety("Wren") == "Innocent")
    go_to(adm, C["Wren"])
    am = mark("admin")
    adm.say("[HotZoneStatus")
    time.sleep(2)
    status = " ".join(since("admin", am))
    region = re.search(r"outdoor Hot region: ([^.\n]+)\.", status)
    record("D2 status inside Hythloth", "outdoor Hot region: none",
           region[0] if region else status[-160:], bool(region) and region[1].strip() == "none")
    hot_msgs = [ln for ln in since("Wren", m) if "Hot Zone" in ln]
    record("D3 no Hot boundary message in the dungeon", "none", f"{len(hot_msgs)} message(s)", not hot_msgs)


def persistence_seeds() -> None:
    state = {}
    place("Wren", 1430, 1690, 0)
    time.sleep(4)
    m = mark("Wren")
    place("Wren", *FIRE_ISLAND)
    entered = wait_until(lambda: any("entered" in ln and "Hot Zone" in ln for ln in since("Wren", m)), 15)
    record("P1 Fire Island entry message", "entry message", messages(since("Wren", m))[:120], entered)
    relog("Wren")
    again = wait_until(lambda: any("entered" in ln and "Hot Zone" in ln for ln in since("Wren", 0)), 20)
    record("P2 relog inside Fire Island", "entry message again after login", f"{again}; at {C['Wren'].state.get('charPosX')},{C['Wren'].state.get('charPosY')}", again)

    place("Rook", 2755, 2166, -2)
    place("Pike", 2756, 2166, -2)
    time.sleep(3)
    ko = knock_out("Pike", "Rook")
    state["rook_ko"] = time.time()
    record("P3 Rook Knocked Out in Hot", "KO audited", f"{ko}", ko)
    relog("Rook")
    time.sleep(6)
    rook_hits = hits("Rook")
    entered = audit("knocked-out", "entered", "Rook", "Pike")
    dropped, start, end = fight("Pike", "Rook", 8)
    extra = audit("knocked-out", "entered", "Rook", "Pike") - entered
    record("P4 relog inside the 90 s window", "still Knocked Out: hits stay 1 (a wake sets half), attack refused, no second KO",
           f"login hits {rook_hits}; attack {start}->{end}; extra KO {extra}; login text: {messages(since('Rook', 0))[:60]}",
           rook_hits <= 5 and not dropped and extra == 0)
    relog("Rook", start=False)

    wait = 45 - (time.time() - state["rook_ko"])
    if wait > 0:
        time.sleep(wait)
    place("Nell", 2757, 2166, -2)
    time.sleep(3)
    ko = knock_out("Pike", "Nell")
    state["nell_ko"] = time.time()
    record("P5 Nell Knocked Out right before the save", "KO audited", f"{ko}", ko)
    with open(STATE_FILE, "w") as handle:
        json.dump(state, handle)
    print("phase1 seeds written; saving and restarting the host", flush=True)
    pwsh("Stop-DevServer.ps1")
    pwsh("Start-DevServer.ps1", "-DistributionPath", os.path.join("work", "hosts", "phase-k3"))
    state["restarted"] = time.time()
    with open(STATE_FILE, "w") as handle:
        json.dump(state, handle)
    print("host restarted", flush=True)


# ---------------------------------------------------------------- phase 2

def phase2() -> None:
    state = json.load(open(STATE_FILE))
    def start(name: str) -> None:
        pwsh("Stop-NavreySession.ps1", "-Name", name)
        pwsh("Start-NavreySession.ps1", "-Name", name, "-EnvFrom", os.path.join("work", "accounts", f"{name}.env"))
        C[name] = connect(name)

    start("Nell")
    age = time.time() - state["nell_ko"]
    time.sleep(6)
    nell_hits, nell_max = hits("Nell"), int(C["Nell"].state.get("maxHits", 60))
    nell = "still Knocked Out" if nell_hits <= 5 else ("recovered" if nell_hits >= nell_max // 2 - 3 else "unclear")
    record("R1 Nell state after the restart", "still Knocked Out if under 90 s since the KO, recovered (half hits) if over",
           f"login {age:.0f}s after the KO; hits {nell_hits}/{nell_max} -> {nell}; login text: {messages(since('Nell', 0))[:80]}",
           (age < 88 and nell == "still Knocked Out") or (age >= 92 and nell == "recovered") or (88 <= age < 92 and nell != "unclear"))

    start("Wren")
    entered = wait_until(lambda: any("entered" in ln and "Hot Zone" in ln for ln in since("Wren", 0)), 20)
    record("R2 Fire Island entry message after restart", "entry message on login",
           f"{entered}; at {C['Wren'].state.get('charPosX')},{C['Wren'].state.get('charPosY')}", entered)

    wait = 100 - (time.time() - state["rook_ko"])
    if wait > 0:
        time.sleep(wait)
    start("Rook")
    time.sleep(6)
    rook_hits, rook_max = hits("Rook"), int(C["Rook"].state.get("maxHits", 60))
    record("R3 expired KO clears on login after restart (Rook)", "recovered at half hits",
           f"hits {rook_hits}/{rook_max}; age {time.time() - state['rook_ko']:.0f}s; login text: {messages(since('Rook', 0))[:80]}",
           rook_hits >= rook_max // 2 - 3)


def main() -> int:
    global adm
    phase = sys.argv[1] if len(sys.argv) > 1 else ""
    refresh_log()
    print(f"server log {SERVER_LOG}", flush=True)
    if phase == "phase1":
        adm = connect("admin")
        for name in NAMES:
            try:
                C[name] = connect(name)
            except Exception:  # noqa: BLE001 - a session stopped by an earlier run is started again
                relog(name)
        stages = [("S0 setup", setup), ("Hot group (X1 L1 XR X4)", hot_group), ("X5a", k5_red_first), ("X5b", k5_grey_first),
                  ("Dungeon", dungeon), ("Persistence seeds", persistence_seeds)]
        if len(sys.argv) > 2:
            stages = [s for s in stages if any(s[0].lower().startswith(o.lower()) for o in sys.argv[2:])]
    elif phase == "phase2":
        stages = [("Phase 2", phase2)]
    else:
        print(__doc__)
        return 2
    for label, body in stages:
        stage(label, body)
    failed = [r for r in results if not r[3]]
    print(f"\n{len(results) - len(failed)}/{len(results)} cases passed", flush=True)
    for r in failed:
        print("FAILED:", r[0], "-", r[2])
    return 1 if failed else 0


if __name__ == "__main__":
    code = main()
    sys.stdout.flush()
    os._exit(code)
