"""Live cases for the 2026-10-07 rulings on Intent, Knocked Out and Execute.

    python tests/scenarios/hot-zones/execute_countdown_live.py

Needs five fresh Warrior characters (New-TestCharacter.ps1 -HostName <host> -Name Eda,Vik,Bea,Pru,Gus -Profession 1) on a disposable host
with hotZones, safeWorld and knockedOut on (the shipped numbers) and the TestOnlyProbe loaded.

  I1  an Intent player a blue hit first hits back and does not become a criminal (outside a Hot Zone)
  K1  Knocked Out lasts 30 seconds and the countdown labels read 30, 25, 20, 15, 10, 5, 4, 3, 2, 1 over the victim
  E1  an executor who is not next to the victim is refused at once, no countdown
  E2  a blue is refused at once, no countdown
  E3  an executor next to the victim: the countdown runs 5 to 1, then the victim is dead
  E4  walking away during the countdown cancels it and the victim lives
  E5  the victim recovered during the countdown: cancelled
  E6  a victim who would wake before it ends: refused at once
"""

from __future__ import annotations

import glob
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.abspath(os.path.join(HERE, "..", ".."))
SCRIPTS = os.path.join(WORKSPACE, ".claude", "scripts")
sys.path.insert(0, SCRIPTS)

from navrey_session import connect, session  # noqa: E402
from staff_command import go_to, staff_target  # noqa: E402
from uo import Event  # noqa: E402

NAMES = ["Eda", "Vik", "Bea", "Pru", "Gus"]
HOT = (2764, 2166, 0)        # inside the Buccaneer's Den Hot Zone
OUTSIDE = (2775, 2166, 0)    # outside it

adm = connect("admin")
C = {n: connect(n) for n in NAMES}
results: list = []
SERVER_LOG = max(glob.glob(os.path.join(WORKSPACE, "work", "dev-server", "logs", "server-*.log")), key=os.path.getmtime)


def audit(category: str, decision: str, subject: str) -> int:
    with open(SERVER_LOG, errors="replace") as handle:
        text = handle.read()
    return len(re.findall(rf"Alpha2 {re.escape(category)} {re.escape(decision)}: subject=\S+?/{re.escape(subject)};", text))


def serial(name: str) -> str:
    return str(C[name].state["charID"])


def hits(name: str) -> int:
    return int(C[name].state.get("hits", 0))


def ghost(name: str) -> bool:
    return bool(C[name].state.get("charGhost"))


def sset(name: str, command: str) -> None:
    go_to(adm, C[name])
    staff_target(adm, command, serial(name))


def place(name: str, x: int, y: int, z: int) -> None:
    sset(name, f'[set Location "({x}, {y}, {z})"')


def mark(name: str) -> int:
    with open(session(name)["log"], errors="replace") as handle:
        return len(handle.readlines())


def since(name: str, m: int) -> list:
    with open(session(name)["log"], errors="replace") as handle:
        return [ln.strip() for ln in handle.readlines()[m:]]


def wait_until(condition, timeout: float, step: float = 0.3) -> bool:
    end = time.time() + timeout
    while time.time() < end:
        if condition():
            return True
        time.sleep(step)
    return False


def record(case_id: str, expected: str, observed: str, ok: bool) -> None:
    results.append((case_id, expected, observed, ok))
    print(f"{'PASS' if ok else 'FAIL'} {case_id}: expected {expected}; observed {observed}", flush=True)


def max_hits(name: str) -> int:
    return int(C[name].state.get("maxHits", 60))


def revive(name: str) -> None:
    if ghost(name):
        sset(name, "[Resurrect")
        wait_until(lambda: not ghost(name), 10)
    sset(name, f"[set Hits {max_hits(name)}")
    time.sleep(1)


def reset(*names: str) -> None:
    for name in names:
        revive(name)
        sset(name, "[set Criminal false")
        sset(name, "[set Kills 0")


def fight(attacker: str, victim: str, seconds: float) -> bool:
    start = hits(victim)
    a = C[attacker]
    a.war(True)
    time.sleep(0.6)
    a.commands.send(f"attack {serial(victim)} force")
    dropped = wait_until(lambda: hits(victim) < start, seconds)
    a.war(False)
    a.commands.send("stop")
    return dropped


def finish(attacker: str, victim: str, timeout: float = 40) -> bool:
    """Victim to 1 hit point, then the attacker lands the lethal blow; True once the victim is Knocked Out."""
    before = audit("knocked-out", "entered", victim)
    sset(victim, "[set Hits 1")
    a = C[attacker]
    a.war(True)
    time.sleep(0.6)
    a.commands.send(f"attack {serial(victim)} force")
    ok = wait_until(lambda: audit("knocked-out", "entered", victim) > before, timeout)
    a.war(False)
    a.commands.send("stop")
    return ok


def start_execute(name: str, victim: str, wait: float) -> list:
    """Says [Execute, targets the victim, and returns what the executor's session logged in the next <wait> seconds."""
    c = C[name]
    m = mark(name)
    c.events.drain()
    c.say("[Execute")
    if c.wait_for(Event.TARGET_REQUEST, timeout=5) is None:
        return ["no-cursor"]
    c.target(serial(victim))
    time.sleep(wait)
    return since(name, m)


def knocked_out_pair(executor: str, victim: str) -> float:
    """Executor and victim side by side in the Hot Zone, the victim Knocked Out by the executor; returns the time the Knock Out began."""
    # a victim still Knocked Out from the case before cannot be Knocked Out again
    adm.say(f"[KnockedOutRecover {serial(victim)}")
    time.sleep(1.5)
    reset(executor, victim)
    place(executor, *HOT)
    place(victim, HOT[0] + 1, HOT[1], HOT[2])
    time.sleep(2)
    fight(executor, victim, 25)
    sset(executor, f"[set Hits {max_hits(executor)}")
    ok = finish(executor, victim)
    t0 = time.time()
    if not ok:
        raise RuntimeError(f"{victim} was not Knocked Out")
    sset(executor, "[set Criminal true")
    return t0


def stage(label: str, body) -> None:
    print(f"--- {label}", flush=True)
    try:
        body()
    except Exception as error:  # noqa: BLE001 - a harness fault must not hide later stages
        record(label, "stage completes", f"{type(error).__name__}: {error}", False)


def lines_with(lines: list, *words: str) -> list:
    return [ln for ln in lines if any(w.lower() in ln.lower() for w in words)]


def i1() -> None:
    reset("Pru", "Bea")
    C["Pru"].say("[Intent")
    time.sleep(1.5)
    place("Pru", *OUTSIDE)
    place("Bea", OUTSIDE[0] + 1, OUTSIDE[1], OUTSIDE[2])
    time.sleep(2)
    first = fight("Bea", "Pru", 30)        # the blue strikes the Intent player first (lawful: Intent exposes them)
    adm_m = mark("admin")
    adm.say(f"[TestOnlyState {serial('Bea')} describe")
    time.sleep(1.2)
    bea_state = " ".join(since("admin", adm_m))
    sset("Pru", f"[set Hits {max_hits('Pru')}")
    back = fight("Pru", "Bea", 30)         # the Intent player hits back
    adm_m = mark("admin")
    adm.say(f"[TestOnlyState {serial('Pru')} describe")
    time.sleep(1.2)
    pru_state = " ".join(since("admin", adm_m))
    criminal = "CriminalStatus" in pru_state
    record("I1 an Intent player the blue hit first hits back", "the blow lands and Pru is not a criminal afterwards",
           f"blue's first strike landed {first}; Pru's counter landed {back}; Pru criminal {criminal} ({pru_state[-120:]}); Bea criminal {'CriminalStatus' in bea_state}",
           first and back and not criminal)


def k1_and_e3() -> None:
    t0 = knocked_out_pair("Eda", "Vik")
    m = mark("Eda")
    refused = start_execute("Eda", "Vik", 1.2)
    # the countdown runs: collect for the rest of the five seconds and a little more
    time.sleep(5.5)
    lines = since("Eda", m)
    labels = lines_with(lines, "Execution")
    dead = wait_until(lambda: ghost("Vik"), 6)
    record("E3 next to the victim: the countdown runs 5 to 1, then the victim dies",
           "begins, labels 5..1, executed, victim dead",
           f"begin line {bool(lines_with(refused, 'You begin to execute'))}; labels {[re.sub(r'.*Execution: ', '', l) for l in labels]}; "
           f"executed {bool(lines_with(lines, 'has been executed'))}; victim dead {dead}",
           bool(lines_with(refused, "You begin to execute")) and len(labels) >= 4 and bool(lines_with(lines, "has been executed")) and dead)


def k1() -> None:
    reset("Eda", "Vik")
    place("Eda", *HOT)
    place("Vik", HOT[0] + 1, HOT[1], HOT[2])
    time.sleep(2)
    fight("Eda", "Vik", 25)
    sset("Eda", f"[set Hits {max_hits('Eda')}")
    before = audit("knocked-out", "recovered", "Vik")
    m = mark("Eda")
    ok = finish("Eda", "Vik")
    t0 = time.time()
    recovered = wait_until(lambda: audit("knocked-out", "recovered", "Vik") > before, 40)
    took = time.time() - t0
    lines = since("Eda", m)
    labels = lines_with(lines, "Knocked Out:")
    numbers = sorted({int(re.search(r"Knocked Out: (\d+)", l).group(1)) for l in labels if re.search(r"Knocked Out: (\d+)", l)}, reverse=True)
    record("K1 Knocked Out lasts 30 seconds with a countdown anyone nearby can read",
           "recovered after about 30 s; labels 30, 25, 20, 15, 10, 5, 4, 3, 2, 1",
           f"knocked out {ok}; recovered after {took:.1f} s ({recovered}); labels seen by the executor {numbers}",
           ok and recovered and 27 <= took <= 33 and numbers[:1] == [30] and 5 in numbers and 1 in numbers)


def e1() -> None:
    t0 = knocked_out_pair("Eda", "Vik")
    place("Eda", HOT[0] + 6, HOT[1], HOT[2])
    time.sleep(1.5)
    lines = start_execute("Eda", "Vik", 1.5)
    labels = lines_with(lines, "Execution")
    record("E1 not next to the victim: refused at once", "You must stand next to them; no countdown",
           f"{lines_with(lines, 'stand next to', 'not Knocked', 'wake')}; labels {len(labels)}", bool(lines_with(lines, "stand next to them to execute them")) and not labels)


def e2() -> None:
    reset("Bea", "Vik")
    t0 = knocked_out_pair("Eda", "Vik")
    sset("Eda", "[set Criminal false")
    lines = start_execute("Eda", "Vik", 1.5)
    record("E2 a blue is refused at once", "Only a criminal or a murderer can execute; no countdown",
           f"{lines_with(lines, 'criminal or a murderer')}; labels {len(lines_with(lines, 'Execution'))}",
           bool(lines_with(lines, "Only a criminal or a murderer")) and not lines_with(lines, "Execution"))


def e4() -> None:
    t0 = knocked_out_pair("Eda", "Vik")
    m = mark("Eda")
    first = start_execute("Eda", "Vik", 2.2)
    place("Eda", HOT[0] + 6, HOT[1], HOT[2])
    time.sleep(1.5)
    lines = since("Eda", m)
    alive = not ghost("Vik") and hits("Vik") > 0
    record("E4 walking away cancels the countdown", "You step away, and the execution is cancelled; the victim lives",
           f"began {bool(lines_with(first, 'You begin'))}; {lines_with(lines, 'step away')}; victim alive {alive}",
           bool(lines_with(lines, "step away")) and alive)


def e5() -> None:
    t0 = knocked_out_pair("Eda", "Vik")
    m = mark("Eda")
    start_execute("Eda", "Vik", 1.5)
    adm.say(f"[KnockedOutRecover {serial('Vik')}")
    time.sleep(2.0)
    lines = since("Eda", m)
    record("E5 the victim recovered during the countdown", "no longer Knocked Out; execution cancelled; victim alive",
           f"{lines_with(lines, 'no longer Knocked Out')}; executed {bool(lines_with(lines, 'has been executed'))}; victim dead {ghost('Vik')}",
           bool(lines_with(lines, "no longer Knocked Out")) and not ghost("Vik"))


def e6() -> None:
    t0 = knocked_out_pair("Eda", "Vik")
    wait = 25.6 - (time.time() - t0)
    if wait > 0:
        time.sleep(wait)
    lines = start_execute("Eda", "Vik", 1.2)
    record("E6 a victim who would wake before it ends is refused at once", "They will get up before you could finish",
           f"{lines_with(lines, 'get up', 'not Knocked')}", bool(lines_with(lines, "get up before you could finish")))


CASES = [("I1", i1), ("K1", k1), ("E3", k1_and_e3), ("E1", e1), ("E2", e2), ("E4", e4), ("E5", e5), ("E6", e6)]
chosen = set(sys.argv[1:])

for label, body in CASES:
    if not chosen or label in chosen:
        stage(label, body)

print("\n" + "=" * 70)
failed = [r for r in results if not r[3]]
print(f"{len(results) - len(failed)} of {len(results)} cases passed")
for r in failed:
    print(f"  FAILED {r[0]}")
sys.exit(1 if failed else 0)
