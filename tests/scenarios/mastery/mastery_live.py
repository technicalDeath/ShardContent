"""Mastery (Beta 2a) live cases on a disposable host with MasteryProbe.dll loaded.

    python -u ShardContent/tests/scenarios/mastery/mastery_live.py [stage ...]

Needs two fresh ordinary Warrior characters logged in as Navrey sessions named Mara and Mika, plus the `admin`
staff session (New-TestCharacter.ps1 -HostName <host> -Name Mara,Mika -Profession 1), on a host that loaded
MasteryProbe.dll. Stage `phase2` runs after a server restart (sessions restarted) and checks persistence.

Valid uses are real Anatomy checks on the other test character: Anatomy is an Easy skill (2.0 allowance per cycle,
20 tenths), and at 90.0 a check still has a 10% chance to fail, so it reaches the stock gain hook. Time passing is
rehearsed with the probe, which moves the character's Mastery anchor into the past.
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

adm = connect("admin")
C = {}
for _name in ("Mara", "Mika"):
    try:
        C[_name] = connect(_name)
    except (RuntimeError, SystemExit):
        pass
results = []


def serial(name: str) -> str:
    return str(C[name].state["charID"])


def mark(name: str) -> int:
    with open(session(name)["log"], errors="replace") as handle:
        return len(handle.readlines())


def since(name: str, m: int) -> list:
    with open(session(name)["log"], errors="replace") as handle:
        return [ln.strip() for ln in handle.readlines()[m:]]


def sset(name: str, command: str) -> None:
    go_to(adm, C[name])
    staff_target(adm, command, serial(name))


def admin(command: str, wait: float = 1.5) -> str:
    m = mark("admin")
    adm.say(command)
    time.sleep(wait)
    return " ".join(since("admin", m))


def record(case_id: str, expected: str, observed: str, ok: bool) -> None:
    results.append((case_id, ok))
    print(f"{'PASS' if ok else 'FAIL'} {case_id}: expected {expected}; observed {observed}", flush=True)


def stage(label: str, body) -> None:
    print(f"--- {label}", flush=True)
    try:
        body()
    except Exception as error:  # noqa: BLE001 - a harness fault must not hide later stages
        record(label, "stage completes", f"{type(error).__name__}: {error}", False)


def status(name: str) -> list:
    """The `[MasteryStatus <serial>` lines for a character, as system messages seen by the staff session."""
    m = mark("admin")
    adm.say(f"[MasteryStatus {serial(name)}")
    time.sleep(2)
    return [re.sub(r"^\[[\d:.]+\]\s*\[SYSTEM\]\s*", "", ln) for ln in since("admin", m) if "[SYSTEM]" in ln]


def skill_line(name: str, skill: str) -> str:
    return next((ln for ln in status(name) if ln.startswith(skill + " ")), "")


def use_anatomy(name: str, count: int, gap: float = 1.6) -> list:
    """Real Anatomy checks on the other test character; returns every system message produced."""
    other = "Mika" if name == "Mara" else "Mara"  # Anatomy cannot be used on oneself
    m = mark(name)
    for _ in range(count):
        C[name].commands.send("useskill anatomy")
        time.sleep(0.8)
        C[name].commands.send(f"target {serial(other)}")
        time.sleep(gap)
    return [re.sub(r"^\[[\d:.]+\]\s*\[SYSTEM\]\s*", "", ln) for ln in since(name, m) if "[SYSTEM]" in ln]


def gains(messages: list) -> int:
    return sum(1 for ln in messages if ln.startswith("Mastery advanced"))


def use_until(name: str, predicate, limit: int = 40) -> list:
    out = []
    for _ in range(limit):
        out += use_anatomy(name, 1)
        if predicate(out):
            break
    return out


# ---------------------------------------------------------------- cases

def entry_and_exhaust() -> None:
    sset("Mara", "[SetSkill Anatomy 90")
    time.sleep(1)
    first = use_until("Mara", lambda m: any("claims this cycle" in x for x in m), 6)
    text = " | ".join(first)
    record("M1 first valid use at 90 begins Mastery, claims the cycle and gains 0.1",
           "entry message, claim of 2.0, +0.1",
           text[:300],
           any("has reached 90.0" in x for x in first) and any("allowance of 2.0" in x for x in first) and gains(first) >= 1)

    out = use_until("Mara", lambda m: any("Allowance left: 0.0" in x for x in m), 70)
    total = gains(first) + gains(out)
    line = skill_line("Mara", "Anatomy")
    record("M2 the bank empties after twenty gains", "Anatomy 92.0, 0.0 stored, claimed this cycle", f"{total} gains; {line}",
           total == 20 and "92.0" in line and "0.0 stored (holds up to 6.0)" in line and "claimed this cycle" in line and "not claimed" not in line)

    extra = use_anatomy("Mara", 5)
    line = skill_line("Mara", "Anatomy")
    record("M3 with the allowance spent, further valid uses grant nothing", "no gain, still 92.0", f"{gains(extra)} gains; {line}",
           gains(extra) == 0 and "92.0" in line)

    lines = status("Mara")
    record("M4 [MasteryStatus text", "cycle length, next cycle, class and allowance per cycle",
           " / ".join(lines)[:400],
           any("24 hours" in x for x in lines) and any("Your next cycle begins in" in x for x in lines) and not any("UTC" in x for x in lines) and any("real chance of failing" in x for x in lines) and any("(easy): 2.0 per cycle" in x for x in lines) and any("at 90.0 or above" in x for x in lines))


def next_cycle_and_bank() -> None:
    admin(f"[TestOnlyMasteryAge {serial('Mara')} 24")
    out = use_until("Mara", lambda m: any("claims this cycle" in x for x in m), 8)
    record("M5 a new cycle lets the skill claim again", "claim of 2.0 and a gain", " | ".join(out)[:260],
           any("allowance of 2.0" in x for x in out) and gains(out) >= 1)

    for cycle in range(3):
        admin(f"[TestOnlyMasteryAge {serial('Mara')} 24")
        use_until("Mara", lambda m: any("claims this cycle" in x for x in m), 8)
    line = skill_line("Mara", "Anatomy")
    # After the claim cycle 0 and three more: allowance is capped at three cycles (3.0) at each claim.
    record("M6 the bank never holds more than three cycles", "stored at most 6.0, about 5.9", line,
           bool(re.search(r"\b(5\.[89]|6\.0) stored \(holds up to 6\.0\)", line)))


def below_threshold_and_back() -> None:
    sset("Mara", "[SetSkill Anatomy 89")
    out = use_anatomy("Mara", 3)
    record("M7 below 90 Mastery does not act", "no Mastery messages", " | ".join(out)[:200], not any("Mastery" in x for x in out))
    sset("Mara", "[SetSkill Anatomy 90")
    out = use_until("Mara", lambda m: gains(m) >= 1, 8)
    record("M8 back at 90 in the same cycle: no second claim, no second entry message, a gain from the bank",
           "gain only", " | ".join(out)[:260],
           gains(out) >= 1 and not any("claims this cycle" in x for x in out) and not any("has reached 90.0" in x for x in out))


def legacy_state() -> None:
    admin(f"[TestOnlyMasteryPoison {serial('Mara')}")
    lines = status("Mara")
    record("M9 earlier-mechanic state is discarded", "fresh state: no anchor", " / ".join(lines)[-160:],
           any("begins with your next valid use" in x for x in lines))
    out = use_until("Mara", lambda m: any("claims this cycle" in x for x in m), 8)
    record("M10 and Mastery starts fresh at the next use", "entry message and a new claim", " | ".join(out)[:240],
           any("has reached 90.0" in x for x in out) and any("claims this cycle" in x for x in out))


def total_cap() -> None:
    """Mika at the 700-point total cap: no Down skill means nothing is granted; a Down skill is lowered as stock does."""
    admin(f"[TestOnlyMasteryLock {serial('Mika')} Fishing up")
    sset("Mika", "[SetSkill Anatomy 90")
    for skill in ("Swords", "Tactics", "Parry", "Healing", "Magery", "MagicResist"):
        sset("Mika", f"[SetSkill {skill} 100")
    sset("Mika", "[SetSkill Fishing 5")
    totals = admin(f"[TestOnlyMasteryTotals {serial('Mika')}")
    hit = re.search(r"MasteryTotals (\d+) (\d+)", totals)
    total, cap = int(hit.group(1)), int(hit.group(2))
    if total > cap:
        sset("Mika", f"[SetSkill Magery {100 - (total - cap) / 10.0}")  # trim so the total is exactly the cap
    elif total < cap:
        sset("Mika", f"[SetSkill Cooking {(cap - total) / 10.0}")
    totals = admin(f"[TestOnlyMasteryTotals {serial('Mika')}")
    hit = re.search(r"MasteryTotals (\d+) (\d+)", totals)
    total, cap = int(hit.group(1)), int(hit.group(2))
    record("C0 Mika is exactly at the total cap", "total == cap", f"{total}/{cap}", total == cap)

    allowance = lambda ln: re.search(r"([\d.]+) stored", ln).group(1) if re.search(r"([\d.]+) stored", ln) else ""
    before = skill_line("Mika", "Anatomy")
    out = use_anatomy("Mika", 6)
    line = skill_line("Mika", "Anatomy")
    record("C1 at the cap with no Down skill: nothing is granted or spent", "no gain, allowance unchanged, not newly claimed",
           f"{gains(out)} gains; {line}",
           gains(out) == 0 and (allowance(before) or "0.0") == allowance(line) and ("not claimed" in line or "not claimed" not in before))

    admin(f"[TestOnlyMasteryLock {serial('Mika')} Fishing down")
    out = use_until("Mika", lambda m: gains(m) >= 1, 10)
    after = admin(f"[TestOnlyMasteryTotals {serial('Mika')}")
    hit2 = re.search(r"MasteryTotals (\d+) (\d+)", after)
    line = skill_line("Mika", "Anatomy")
    record("C2 with a Down skill the gain displaces it as stock does", "+0.1 Anatomy, total unchanged, claimed",
           f"{gains(out)} gains; total {hit2.group(1)}/{hit2.group(2)}; {line}",
           gains(out) >= 1 and int(hit2.group(1)) <= cap and "claimed this cycle" in line and "not claimed" not in line)
    m = mark("Mika")
    C["Mika"].say("[SkillBank")
    time.sleep(2)
    bank = " ".join(since("Mika", m))
    record("C3 the displaced point reached the Skill Bank", "Fishing banked", bank[-160:], "Fishing" in bank and "banked 0.0" not in bank)


def hard_class_labels() -> None:
    sset("Mara", "[SetSkill Alchemy 90")
    sset("Mara", "[SetSkill Magery 90")
    lines = status("Mara")
    alch = next((x for x in lines if x.startswith("Alchemy")), "")
    mag = next((x for x in lines if x.startswith("Magery")), "")
    record("M11 each skill shows its class and allowance", "Alchemy hard 0.6, Magery standard 1.0", f"{alch} || {mag}",
           "(hard): 0.6 per cycle" in alch and "(standard): 1.0 per cycle" in mag)


def phase2() -> None:
    lines = status("Mara")
    line = next((x for x in lines if x.startswith("Anatomy")), "")
    record("R1 Mastery state survives a restart", "Anatomy line with claimed state", line, "claimed this cycle" in line)
    m = mark("Mara")
    print("   (login reminder is read from the session log below)")
    with open(session("Mara")["log"], errors="replace") as handle:
        text = handle.read()
    record("R2 login reminder when skills can still claim", "reminder line present (Alchemy and Magery unclaimed)",
           "present" if "can claim this cycle's allowance" in text else "not shown", "can claim this cycle's allowance" in text)


def main() -> int:
    stages = [("entry", entry_and_exhaust), ("cycles", next_cycle_and_bank), ("below", below_threshold_and_back),
              ("labels", hard_class_labels), ("legacy", legacy_state), ("cap", total_cap), ("phase2", phase2)]
    default = ["entry", "cycles", "below", "labels", "legacy", "cap"]
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
