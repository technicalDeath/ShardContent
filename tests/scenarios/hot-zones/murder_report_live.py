"""Live cases for the murder-report rule: a blue killed by a player who had no right to attack is offered the report.

    python ShardContent/tests/scenarios/hot-zones/murder_report_live.py

Needs ten fresh Warrior characters (New-TestCharacter.ps1 -HostName <host> -Name Kara,Vale,Vex,Vim,Tavi,Pike,Elin,Wren,Rook,Nell
-Profession 1) on a disposable host with hotZones, safeWorld and knockedOut on and the TestOnlyProbe loaded
(TestOnlyFlagOverride). Standard reporting (automaticMurderAdjudication off), as deployed: the victim's report gump decides.

The cases say what each side of the law looks like to the victim (owner rulings 2026-10-06, K-5 amended):
  R1  an attacker with no right to attack strikes first, the victim fights back, the attacker Knocks Out and Executes: offered
  R2  the same, the victim never fights back (control): offered
  R3  a blue strikes a criminal first (lawful), the criminal fights back, Knocks the blue out and Executes: offered (an Execute is murder)
  R3b the same outside a Hot Zone: offered
  R4  the victim has Criminal Intent on (outside Hot) and a criminal Executes: NOT offered (Intent makes an Execute lawful)
  R5  Knocked Out switched off, an attacker with no right kills a blue who fought back: offered (the plain death path)
Before the Execute ruling R3 and R3b expected no report; run against that build they fail, and against the new build every case passes.
"""

from __future__ import annotations

import glob
import os
import re
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
HOT = (2764, 2166, 0)        # inside the Buccaneer's Den Hot Zone (the K3 placements)
OUTSIDE = (2775, 2166, 0)    # outside it

adm = None
C: dict = {}
results: list = []
SERVER_LOG = max(glob.glob(os.path.join(WORKSPACE, "work", "dev-server", "logs", "server-*.log")), key=os.path.getmtime)


def audit(category: str, decision: str, subject: str) -> int:
    """How many times the server audit log holds this decision for the subject (Alpha2 <category> <decision>: subject=...)."""
    with open(SERVER_LOG, errors="replace") as handle:
        text = handle.read()
    return len(re.findall(rf"Alpha2 {re.escape(category)} {re.escape(decision)}: subject=\S+?/{re.escape(subject)};", text))


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


def mark(name: str) -> int:
    with open(session(name)["log"], errors="replace") as handle:
        return len(handle.readlines())


def since(name: str, m: int) -> list:
    with open(session(name)["log"], errors="replace") as handle:
        return [ln.strip() for ln in handle.readlines()[m:]]


def wait_until(condition, timeout: float, step: float = 0.4) -> bool:
    end = time.time() + timeout
    while time.time() < end:
        if condition():
            return True
        time.sleep(step)
    return False


def record(case_id: str, expected: str, observed: str, ok: bool) -> None:
    results.append((case_id, expected, observed, ok))
    print(f"{'PASS' if ok else 'FAIL'} {case_id}: expected {expected}; observed {observed}", flush=True)


def revive(name: str) -> None:
    if ghost(name):
        sset(name, "[Resurrect")
        wait_until(lambda: not ghost(name), 10)
    sset(name, f"[set Hits {C[name].state.get('maxHits', 60)}")
    time.sleep(1)


def fight(attacker: str, victim: str, seconds: float) -> bool:
    """The attacker hits the victim until the victim's hit points drop."""
    start = hits(victim)
    a = C[attacker]
    a.war(True)
    time.sleep(0.6)
    a.commands.send(f"attack {serial(victim)} force")
    dropped = wait_until(lambda: hits(victim) < start, seconds)
    a.war(False)
    a.commands.send("stop")
    return dropped


def finish(attacker: str, victim: str, knocked_out: bool = True, timeout: float = 40) -> bool:
    """Victim to 1 hit point, then the attacker lands the lethal blow; True once the victim is Knocked Out (or dead)."""
    before = audit("knocked-out", "entered", victim)
    sset(victim, "[set Hits 1")
    a = C[attacker]
    a.war(True)
    time.sleep(0.6)
    a.commands.send(f"attack {serial(victim)} force")
    done = (lambda: audit("knocked-out", "entered", victim) > before) if knocked_out else (lambda: ghost(victim))
    ok = wait_until(done, timeout)
    a.war(False)
    a.commands.send("stop")
    return ok


def execute(name: str, victim: str) -> str:
    c = C[name]
    m = mark(name)
    c.events.drain()
    c.say("[Execute")
    if c.wait_for(Event.TARGET_REQUEST, timeout=5) is None:
        return "no-cursor"
    c.target(serial(victim))
    time.sleep(3)
    text = " ".join(since(name, m))
    return "executed" if "has been executed" in text else ("refused" if "not eligible" in text else "other")


def flags(victim: str) -> str:
    """The victim's aggressor records as the test-only probe reports them: attacker:can=<report would be offered>:crim=..."""
    m = mark("admin")
    adm.say(f"[TestOnlyReportFlags {serial(victim)}")
    time.sleep(1.5)
    text = " ".join(since("admin", m))
    hit = re.search(r"ReportFlags target=\w+ aggressors=(\S+)", text)
    return hit.group(1) if hit else f"(no reply: {text[-100:]})"


def report_offered(victim: str, killer: str, wait: float = 9.0) -> bool:
    """The stock report gump arrives about four seconds after death; look for it naming the killer."""
    end = time.time() + wait
    while time.time() < end:
        try:
            text = " ".join(C[victim].call("gumps"))
        except Exception:  # noqa: BLE001 - a busy client answers on the next poll
            text = ""
        if killer in text and re.search(r"report .*as a murderer", text, re.IGNORECASE):
            return True
        time.sleep(1.0)
    return False


def answer_report(victim: str, killer: str) -> tuple:
    """Press Yes on the report gump; True once the killer is told they were reported. Returns (told, what the gump listing showed)."""
    m = mark(killer)
    gumps = C[victim].call("gumps")
    shown = " || ".join(line.strip()[:110] for line in gumps if re.search(r"murderer|gump", line, re.IGNORECASE))
    # a gump is listed as "[GUMP] local 0x00000001 server 0xCBCD7BC5 <title>" followed by its text lines; the response goes to the
    # server id of the gump whose text asks about reporting (other gumps, like the guide, may be open too)
    ident = None
    for index, line in enumerate(gumps):
        if re.search(r"report .*as a murderer", line, re.IGNORECASE):
            for earlier in reversed(gumps[: index + 1]):
                ident = re.search(r"server (0x[0-9A-Fa-f]+)", earlier)
                if ident:
                    break
            break
    if ident is None:
        return False, f"no gump id in: {shown}"
    C[victim].commands.send(f"gumpresponse 1 gump:{ident.group(1)}")
    told = wait_until(lambda: any("reported for a murder" in ln for ln in since(killer, m)), 8)
    return told, f"{shown}; sent button 1 to {ident.group(1)}"


def stage(label: str, body) -> None:
    print(f"--- {label}", flush=True)
    try:
        body()
    except Exception as error:  # noqa: BLE001 - a harness fault must not hide later stages
        record(label, "stage completes", f"{type(error).__name__}: {error}", False)


def reset(*names: str) -> None:
    for name in names:
        revive(name)
        sset(name, "[set Criminal false")
        sset(name, "[set Kills 0")


def unlawful_fight(attacker: str, victim: str, fights_back: bool) -> tuple:
    """The attacker strikes first; the victim may hit back; the attacker hits again, Knocks Out and Executes."""
    reset(attacker, victim)
    place(attacker, *HOT)
    place(victim, HOT[0] + 1, HOT[1], HOT[2])
    time.sleep(3)
    first = fight(attacker, victim, 30)
    struck = notoriety(attacker)
    after_first = flags(victim)
    landed = False
    if fights_back:
        landed = fight(victim, attacker, 30) or fight(victim, attacker, 30)
        sset(attacker, f"[set Hits {C[attacker].state.get('maxHits', 60)}")
        second = fight(attacker, victim, 30)
    else:
        second = None
    after_reply = flags(victim)
    sset(attacker, f"[set Hits {C[attacker].state.get('maxHits', 60)}")
    finish(attacker, victim)
    result = execute(attacker, victim)
    detail = (f"first strike landed {first} (attacker {struck}); victim fought back {fights_back}, counter-hit landed {landed}, attacker's next hit landed {second}; "
              f"flags after the first strike [{after_first}] and after the exchange [{after_reply}]; {result}")
    return detail, ((landed and second) or not fights_back)


def r1() -> None:
    detail, valid = unlawful_fight("Kara", "Vim", True)
    offered = report_offered("Vim", "Kara")
    record("R1 no right to attack, the victim fights back", "report offered (and the counter-hit landed)", f"{detail}; offered {offered}", offered and valid)
    if offered:
        told, shown = answer_report("Vim", "Kara")
        record("R1b answering Yes tells the killer", "You have been reported for a murder!", f"told {told}; {shown}", told)


def r2() -> None:
    detail, valid = unlawful_fight("Pike", "Wren", False)
    offered = report_offered("Wren", "Pike")
    record("R2 no right to attack, the victim never fights back", "report offered", f"{detail}; offered {offered}", offered and valid)


def r3() -> None:
    reset("Rook", "Tavi")
    sset("Tavi", "[set Criminal true")
    place("Tavi", *HOT)
    place("Rook", HOT[0] + 1, HOT[1], HOT[2])
    time.sleep(3)
    first = fight("Rook", "Tavi", 30)
    sset("Tavi", "[set Criminal true")
    sset("Tavi", f"[set Hits {C['Tavi'].state.get('maxHits', 60)}")
    finish("Tavi", "Rook")
    result = execute("Tavi", "Rook")
    offered = report_offered("Rook", "Tavi", 9)
    record("R3 the blue struck a criminal first (Hot Zone), the criminal Executes", "report offered (an Execute is murder)",
           f"blue's first strike landed {first}; {result}; offered {offered}", result == "executed" and offered)


def r3b() -> None:
    """The same outside a Hot Zone: the blue attacks a criminal (lawful), the criminal answers, Knocks the blue out and Executes."""
    reset("Rook", "Tavi")
    sset("Tavi", "[set Criminal true")
    place("Tavi", *OUTSIDE)
    place("Rook", OUTSIDE[0] + 1, OUTSIDE[1], OUTSIDE[2])
    time.sleep(3)
    first = fight("Rook", "Tavi", 30)
    sset("Tavi", "[set Criminal true")
    sset("Tavi", f"[set Hits {C['Tavi'].state.get('maxHits', 60)}")
    finish("Tavi", "Rook")
    result = execute("Tavi", "Rook")
    offered = report_offered("Rook", "Tavi", 9)
    record("R3b the blue struck a criminal first (outside a Hot Zone), the criminal Executes", "report offered (an Execute is murder)",
           f"blue's first strike landed {first}; {result}; offered {offered}", result == "executed" and offered)


def r4() -> None:
    reset("Elin", "Nell")
    C["Nell"].say("[Intent")
    time.sleep(1.5)
    sset("Elin", "[set Criminal true")
    place("Elin", *OUTSIDE)
    place("Nell", OUTSIDE[0] + 1, OUTSIDE[1], OUTSIDE[2])
    time.sleep(3)
    first = fight("Elin", "Nell", 30)
    fight("Nell", "Elin", 30)
    sset("Elin", "[set Criminal true")
    sset("Elin", f"[set Hits {C['Elin'].state.get('maxHits', 60)}")
    finish("Elin", "Nell")
    result = execute("Elin", "Nell")
    offered = report_offered("Nell", "Elin", 9)
    record("R4 the victim has Criminal Intent on", "no report offered",
           f"criminal's strike landed {first}; {result}; offered {offered}", result == "executed" and not offered)
    C["Nell"].say("[Intent")


def r5() -> None:
    adm.say("[TestOnlyFlagOverride KnockedOut false")
    time.sleep(1.5)
    try:
        reset("Vale", "Vex")
        place("Vale", *HOT)
        place("Vex", HOT[0] + 1, HOT[1], HOT[2])
        time.sleep(3)
        first = fight("Vale", "Vex", 30)
        after_first = flags("Vex")
        landed = fight("Vex", "Vale", 30) or fight("Vex", "Vale", 30)
        sset("Vale", f"[set Hits {C['Vale'].state.get('maxHits', 60)}")
        second = fight("Vale", "Vex", 30)
        after_reply = flags("Vex")
        sset("Vale", f"[set Hits {C['Vale'].state.get('maxHits', 60)}")
        finish("Vale", "Vex", knocked_out=False)
        dead = wait_until(lambda: ghost("Vex"), 10)
        offered = report_offered("Vex", "Vale")
        record("R5 Knocked Out off: no right to attack, the victim fights back, a plain death", "victim dead, report offered (and the counter-hit landed)",
               f"first strike landed {first}; counter-hit landed {landed}, attacker's next hit landed {second}; flags after the first strike [{after_first}] and after the exchange [{after_reply}]; "
               f"victim dead {dead}; offered {offered}", dead and offered and landed and second)
    finally:
        adm.say("[TestOnlyFlagOverride KnockedOut true")
        time.sleep(1.5)


def main() -> int:
    global adm
    adm = connect("admin")
    wanted = [a.upper() for a in sys.argv[1:]]
    # only the characters the selected cases use need to exist and be connected
    pairs = {"R1": ("Kara", "Vim"), "R2": ("Pike", "Wren"), "R3": ("Rook", "Tavi"), "R3B": ("Rook", "Tavi"), "R4": ("Elin", "Nell"), "R5": ("Vale", "Vex")}
    needed = sorted({n for case, names in pairs.items() if not wanted or case in wanted for n in names})
    for name in needed:
        C[name] = connect(name)
        assert C[name].state.get("connected", True), f"{name} not connected"
    for name in ("Kara", "Pike", "Vale", "Tavi", "Elin"):
        if name in C:
            sset(name, "[SetSkill Wrestling 100")
    for label, body in (("R1", r1), ("R2", r2), ("R3", r3), ("R3B", r3b), ("R4", r4), ("R5", r5)):
        if not wanted or label in wanted:
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
