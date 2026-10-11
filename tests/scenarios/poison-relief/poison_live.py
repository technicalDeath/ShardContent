"""Poison relief (docs/Poison-Relief-Plan.md): live cases on a disposable host with PoisonReliefProbe.dll loaded and featureFlags.poisonRelief on.

    python -u ShardContent/tests/scenarios/poison-relief/poison_live.py [stage ...]

Needs two fresh ordinary characters created on the host while the flag was on (Pip and Pam, Archer profession 8) logged in as Navrey sessions, and the
`admin` staff session. Stages: potions, hint, grace, nohint, flagoff, death. Reports come back from the probe as system messages to the staff session.
"""

from __future__ import annotations

import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(WORKSPACE, ".claude", "scripts"))

from navrey_session import connect, session  # noqa: E402
from staff_command import go_to, staff_target  # noqa: E402

HINT = "While you are poisoned a bandage only tries to cure you"
GRACE = "You are still shaking off the last poison"

adm = connect("admin")
C = {name: connect(name) for name in ("Pip", "Pam")}
results = []


def serial(name: str) -> str:
    return str(C[name].state["charID"])


def lines(name: str) -> list:
    with open(session(name)["log"], errors="replace") as handle:
        return [ln.strip() for ln in handle.readlines()]


def mark(name: str) -> int:
    return len(lines(name))


def record(case_id: str, expected: str, observed: str, ok: bool) -> None:
    results.append((case_id, ok))
    print(f"{'PASS' if ok else 'FAIL'} {case_id}: expected {expected}; observed {observed}", flush=True)


def stage(label: str, body) -> None:
    print(f"--- {label}", flush=True)
    try:
        body()
    except Exception as error:  # noqa: BLE001 - a harness fault must not hide later stages
        record(label, "stage completes", f"{type(error).__name__}: {error}", False)


def probe(command: str, key: str, timeout: float = 15.0) -> dict:
    m = mark("admin")
    adm.say(command)
    pattern = re.compile(rf"\[SYSTEM\]\s*{key}\b(.*)")
    deadline = time.time() + timeout
    hit = None
    while time.time() < deadline and hit is None:
        time.sleep(0.3)
        for line in lines("admin")[m:]:
            hit = pattern.search(line) or hit
    fields = {}
    for k, v in re.findall(r"(\w+)=([^\s]+)", hit.group(1) if hit else ""):
        fields[k] = v
    if not fields:
        raise RuntimeError(f"no {key} report for: {command}")
    return fields


def apply(name: str, level: int, source: str) -> dict:
    return probe(f"[TestOnlyPoisonApply {serial(name)} {level} {source}", "PoisonApply")


def cure(name: str) -> dict:
    return probe(f"[TestOnlyPoisonCure {serial(name)}", "PoisonCure")


def pack(name: str) -> dict:
    return probe(f"[TestOnlyPoisonPack {serial(name)}", "PoisonPack")


def count(name: str, text: str, since: int) -> int:
    return sum(1 for ln in lines(name)[since:] if text in ln)


def wait_for(name: str, text: str, since: int, timeout: float = 6.0) -> bool:
    end = time.time() + timeout
    while time.time() < end:
        if count(name, text, since):
            return True
        time.sleep(0.4)
    return False


def sset(name: str, command: str) -> None:
    go_to(adm, C[name])
    staff_target(adm, command, serial(name))


# ---------------------------------------------------------------- cases

def potions() -> None:
    flag = probe("[TestOnlyPoisonFlag status", "PoisonFlag")
    record("P0 the flag is on for this run", "on=True", str(flag), flag.get("on") == "True")
    for name in ("Pip", "Pam"):
        p = pack(name)
        weight, limit = int(p["weight"]), int(p["max"])
        record(f"P1 {name} starts with five newbied Lesser Cure potions", "potions=5 newbied=5", str(p), p["potions"] == "5" and p["newbied"] == "5")
        record(f"P2 {name}'s load stays inside the starter weight budget (85% of the limit)", f"weight <= {int(limit * 0.85)}", f"weight {weight} of {limit}", weight <= int(limit * 0.85))


def hint() -> None:
    m = mark("Pip")
    r = apply("Pip", 0, "orc")
    record("H1 a Lesser poison from a monster lands on a fresh character", "result=Poisoned", str(r), r["result"] == "Poisoned" and r["poisoned"] == "True")
    shown = wait_for("Pip", HINT, m)
    record("H2 the first poisoning of a character who cannot cure with a bandage is explained", "the hint is in the journal", f"found={shown}", shown)
    c = cure("Pip")
    record("H3 the poison can be cured by staff (the end the watcher sees)", "cured=True", str(c), c["cured"] == "True")
    time.sleep(2.5)
    record("H4 the hint was shown once", "1 line", f"{count('Pip', HINT, m)} lines", count("Pip", HINT, m) == 1)


def grace() -> None:
    m = mark("Pip")
    r = apply("Pip", 0, "orc")
    record("G1 inside the window a Lesser poison from a monster is refused", "result=Immune poisoned=False", str(r), r["result"] == "Immune" and r["poisoned"] == "False")
    record("G2 the player is told why", "the grace line is in the journal", f"found={wait_for('Pip', GRACE, m, 4)}", count("Pip", GRACE, m) >= 1)

    r = apply("Pip", 1, "orc")
    record("G3 a stronger poison (Regular) is stock: it lands", "result=Poisoned level=1", str(r), r["result"] == "Poisoned" and r["level"] == "1")
    cure("Pip")
    time.sleep(2.5)

    r = apply("Pip", 0, "player")
    record("G4 poison from a player is never refused", "result=Poisoned", str(r), r["result"] == "Poisoned")
    cure("Pip")
    print("   waiting 33 s for the window to run out", flush=True)
    time.sleep(33.0)

    r = apply("Pip", 0, "orc")
    record("G5 after the window a Lesser poison from a monster lands again", "result=Poisoned", str(r), r["result"] == "Poisoned")
    cure("Pip")
    record("G6 the hint was not repeated through all of this", "1 line since the start of the run", f"{count('Pip', HINT, 0)} lines", count("Pip", HINT, 0) == 1)


def no_hint() -> None:
    probe(f"[TestOnlyPoisonSkills {serial('Pam')} 60 60", "PoisonSkills")
    m = mark("Pam")
    r = apply("Pam", 0, "orc")
    time.sleep(3.0)
    record("N1 a character whose bandage can cure is poisoned and not told", "result=Poisoned, 0 hint lines", f"{r['result']}, {count('Pam', HINT, m)} lines", r["result"] == "Poisoned" and count("Pam", HINT, m) == 0)
    cure("Pam")


def flag_off() -> None:
    probe("[TestOnlyPoisonFlag off", "PoisonFlag")
    cure("Pip")
    time.sleep(2.5)
    m = mark("Pip")
    r = apply("Pip", 0, "orc")
    time.sleep(2.0)
    record("F1 with the flag off a Lesser poison lands straight after a cure, and nothing is said", "result=Poisoned, no grace line", f"{r['result']}, {count('Pip', GRACE, m)} grace lines", r["result"] == "Poisoned" and count("Pip", GRACE, m) == 0)
    cure("Pip")
    probe("[TestOnlyPoisonFlag on", "PoisonFlag")


def death() -> None:
    sset("Pip", "[kill")
    time.sleep(4.0)
    sset("Pip", "[Resurrect")
    time.sleep(2.0)
    p = pack("Pip")
    record("D1 the starter potions survive a death", "potions=5 newbied=5", str(p), p["potions"] == "5" and p["newbied"] == "5")


def main() -> int:
    stages = [("potions", potions), ("hint", hint), ("grace", grace), ("nohint", no_hint), ("flagoff", flag_off), ("death", death)]
    only = sys.argv[1:] or [s for s, _ in stages]
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
