"""Mastery from 80.0, layered on ordinary gain (docs/Mastery-Layered-Plan.md): live cases on a disposable host with the probes loaded.

    python -u ShardContent/tests/scenarios/mastery/mastery_live.py [stage ...]

Needs three fresh ordinary characters logged in as Navrey sessions named Mara, Mika and Mia, plus the `admin` staff session
(New-TestCharacter.ps1 -HostName <host> -Name Mara,Mika,Mia -Profession 1), on a host that loaded TestOnlyProbe.dll and MasteryProbe.dll,
and whose copy of shard-rules.json lists Poisoning as a veryHard skill (no shipped skill is veryHard, and the class needs a live check too).
Stage `phase2` runs after a server restart (sessions restarted) and checks persistence.

Stages `entry`, `cycles`, `below`, `labels`, `legacy` and `cap` use real Anatomy checks on the other test character: Anatomy is an
Easy skill (2.0 allowance, 20 tenths), and at 80.0 a check still has a real chance to fail, so it reaches the gain hook. Stage `chance` measures
the gain-by-chance path with the probe's TestOnlyMasteryRolls (thousands of real skill checks, the skill held at one value) against the same
formula the server uses. Stage `climb` is the exit test: with only the day's allowance of valid uses, an Easy, a Standard, a Hard and a
VeryHard skill go 80.0 to 100.0 in 10, 15, 20 and 25 shifted daily cycles. Time passing is rehearsed with the probe, which moves the Mastery anchor into the past.
"""

from __future__ import annotations

import math
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
for _name in ("Mara", "Mika", "Mia"):
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


def window_lines(client) -> list:
    """The text of the windows a client has open, one string per piece of text (a window's header line is dropped)."""
    out = []
    for line in client.call("gumps"):
        text = re.sub(r"^\[GUMP\]\s*", "", line.strip())
        if text and "local 0x" not in text:
            out.append(text)
    return out


def status(name: str) -> list:
    """The `[Mastery <serial>` window for a character, as seen by the staff session: the cycle lines, then one line per skill
    in the shape the cases below read ("Anatomy 82.0 (easy): 2.0 per cycle, 0.0 stored (holds up to 6.0), claimed this cycle, 18.0 points to reach 100.0.")."""
    adm.say(f"[Mastery {serial(name)}")
    time.sleep(2.5)
    pieces = window_lines(adm)
    lines = [p for p in pieces if p.startswith(("Your next cycle", "Your first cycle", "No skill is in Mastery", "A skill's first valid"))]

    for i, piece in enumerate(pieces):
        hit = re.fullmatch(r"(\w[\w ]*), (\d+\.\d) a cycle", piece)
        if hit and i >= 1 and i + 5 < len(pieces):
            stored = re.fullmatch(r"(\d+\.\d) of (\d+\.\d)", pieces[i + 3])
            if stored:
                lines.append(
                    f"{pieces[i - 1]} {pieces[i + 1]} ({hit.group(1).lower()}): {hit.group(2)} per cycle, {stored.group(1)} stored "
                    f"(holds up to {stored.group(2)}), {'claimed this cycle' if pieces[i + 4] == 'Claimed' else 'not claimed this cycle'}, "
                    f"{pieces[i + 5]} points to reach 100.0."
                )

    return lines


def skill_line(name: str, skill: str) -> str:
    return next((ln for ln in status(name) if ln.startswith(skill + " ")), "")


def skill_value(line: str) -> float:
    hit = re.match(r"\w[\w ]*? (\d+\.\d) \(", line)
    return float(hit.group(1)) if hit else float("nan")


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


def probe(command: str, key: str, wait: float = 2.0) -> dict:
    """Runs a probe verb as staff and returns its report as a dict of key=value pairs (numbers where they are numbers)."""
    m = mark("admin")
    adm.say(command)
    deadline = time.time() + max(wait, 90.0)
    pattern = re.compile(rf"\[SYSTEM\]\s*{key}\b(.*)")
    hit = None
    while time.time() < deadline and hit is None:
        time.sleep(0.5)
        for line in since("admin", m):
            hit = pattern.search(line) or hit
    fields = {}
    for k, v in re.findall(r"(\w+)=([^\s]+)", hit.group(1) if hit else ""):
        try:
            fields[k] = float(v) if "." in v else int(v)
        except ValueError:
            fields[k] = v
    return fields


def expected_gain_probability(value: float, total: float, cap: float, factor: float, chance: float) -> float:
    """The stock gain chance for one check (SkillCheck.CheckSkill, UOR: a failure counts 0.2), times the class multiplier in `factor`."""
    base = ((cap - total) / cap + (100.0 - value) / 100.0) / 2.0
    expected = 0.0
    for success, weight in ((True, chance), (False, 1.0 - chance)):
        gc = (base + (1.0 - chance) * (0.5 if success else 0.2)) / 2.0 * factor
        expected += weight * min(max(gc, 0.01), 1.0)
    return expected


# ---------------------------------------------------------------- cases

def entry_and_exhaust() -> None:
    sset("Mara", "[SetSkill Anatomy 80")
    time.sleep(1)
    first = use_until("Mara", lambda m: any("claims this cycle" in x for x in m), 6)
    text = " | ".join(first)
    record("M1 first valid use at 80 begins Mastery, claims the cycle and gains 0.1",
           "entry message with the daily uses, claim of 2.0, +0.1",
           text[:320],
           any("has reached 80.0: Mastery begins. Your first 20 valid, successful uses each day are guaranteed gains" in x for x in first)
           and any("allowance of 2.0" in x for x in first) and gains(first) >= 1)

    out = use_until("Mara", lambda m: any("Allowance left: 0.0" in x for x in m), 80)
    total = gains(first) + gains(out)
    line = skill_line("Mara", "Anatomy")
    value = skill_value(line)
    record("M2 the bank empties after twenty guaranteed gains", "20 Mastery gains, 0.0 stored, claimed this cycle, Anatomy 82.0 or a little more",
           f"{total} gains; {line}",
           total == 20 and 82.0 <= value <= 83.0 and "0.0 stored (holds up to 6.0)" in line and "claimed this cycle" in line and "not claimed" not in line)

    extra = use_anatomy("Mara", 6)
    line = skill_line("Mara", "Anatomy")
    record("M3 with the allowance spent, valid uses are no longer guaranteed (they gain only by chance)",
           "no Mastery gain or claim message, still 82.0 or a hair more",
           f"{gains(extra)} guaranteed gains; {line}",
           gains(extra) == 0 and not any("claims this cycle" in x for x in extra) and 82.0 <= skill_value(line) <= 83.0)

    lines = status("Mara")
    record("M4 [Mastery window", "cycle length, next cycle, class and allowance per cycle, no 90",
           " / ".join(lines)[:400],
           any("24 hours" in x for x in lines) and any("Your next cycle begins in" in x for x in lines) and not any("UTC" in x for x in lines)
           and any("(easy): 2.0 per cycle" in x for x in lines) and not any("90" in x for x in lines))


def next_cycle_and_bank() -> None:
    admin(f"[TestOnlyMasteryAge {serial('Mara')} 24")
    out = use_until("Mara", lambda m: any("claims this cycle" in x for x in m), 8)
    record("M5 a new cycle lets the skill claim again", "claim of 2.0 and a gain", " | ".join(out)[:260],
           any("allowance of 2.0" in x for x in out) and gains(out) >= 1)

    for cycle in range(3):
        admin(f"[TestOnlyMasteryAge {serial('Mara')} 24")
        use_until("Mara", lambda m: any("claims this cycle" in x for x in m), 8)
    line = skill_line("Mara", "Anatomy")
    # After the claim in cycle 0 and three more: the allowance is capped at three cycles (6.0) at each claim, less the gain of the claiming use.
    record("M6 the bank never holds more than three cycles", "stored at most 6.0, about 5.9", line,
           bool(re.search(r"\b(5\.[89]|6\.0) stored \(holds up to 6\.0\)", line)))


def below_threshold_and_back() -> None:
    sset("Mara", "[SetSkill Anatomy 79")
    out = use_anatomy("Mara", 3)
    record("M7 below 80 Mastery does not act", "no Mastery messages", " | ".join(out)[:200], not any("Mastery" in x for x in out))
    sset("Mara", "[SetSkill Anatomy 80")
    out = use_until("Mara", lambda m: gains(m) >= 1, 8)
    record("M8 back at 80 in the same cycle: no second claim, no second entry message, a gain from the bank",
           "gain only", " | ".join(out)[:260],
           gains(out) >= 1 and not any("claims this cycle" in x for x in out) and not any("has reached 80.0" in x for x in out))


def legacy_state() -> None:
    admin(f"[TestOnlyMasteryPoison {serial('Mara')}")
    lines = status("Mara")
    record("M9 earlier-mechanic state is discarded", "fresh state: no anchor", " / ".join(lines)[-160:],
           any("begins with your next successful use" in x for x in lines))
    out = use_until("Mara", lambda m: any("claims this cycle" in x for x in m), 8)
    record("M10 and Mastery starts fresh at the next use", "entry message and a new claim", " | ".join(out)[:240],
           any("has reached 80.0" in x for x in out) and any("claims this cycle" in x for x in out))


def total_cap() -> None:
    """Mika at the 700-point total cap: no Down skill means nothing is granted; a Down skill is lowered as stock does."""
    admin(f"[TestOnlyMasteryLock {serial('Mika')} Fishing up")
    sset("Mika", "[SetSkill Anatomy 80")
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
    C["Mika"].say("[SkillBank")
    time.sleep(2.5)
    pieces = window_lines(C["Mika"])
    bank = " ".join(pieces)
    row = pieces.index("Fishing") if "Fishing" in pieces else -1
    banked = pieces[row + 2] if row >= 0 and row + 2 < len(pieces) else ""
    record("C3 the displaced point reached the Skill Bank", "Fishing banked in the window", bank[-160:], row >= 0 and banked not in ("", "0.0"))


def hard_class_labels() -> None:
    sset("Mara", "[SetSkill Alchemy 80")
    sset("Mara", "[SetSkill Magery 80")
    lines = status("Mara")
    alch = next((x for x in lines if x.startswith("Alchemy")), "")
    mag = next((x for x in lines if x.startswith("Magery")), "")
    record("M11 each skill shows its class and allowance", "Alchemy hard 1.0, Magery standard 1.4", f"{alch} || {mag}",
           "(hard): 1.0 per cycle" in alch and "(standard): 1.4 per cycle" in mag)
    # A skill set to Down cannot gain, so it cannot claim: the login reminder after the restart must not count it.
    admin(f"[TestOnlyMasteryLock {serial('Mara')} Magery down", wait=0.8)


def chance_path() -> None:
    """The layered rule on the server's own path: stored allowance is spent as guaranteed gains, everything else rolls at the class rate."""
    mia = serial("Mia")
    for skill in ("Anatomy", "Tactics", "Alchemy"):
        sset("Mia", f"[SetSkill {skill} 85")

    # L3 a stored allowance of 5 and a claimed cycle: five sure successes are five gains, exactly, and the bank is then empty.
    admin(f"[TestOnlyMasterySeed {mia} 1 Tactics=5:1 Anatomy=0:1 Alchemy=0:1")
    r = probe(f"[TestOnlyMasteryRolls {mia} Tactics 850 1.0 5", "MasteryRolls")
    record("L3 five sure successes with 0.5 stored are five guaranteed gains", "gains=5 over=0 bank=0", str(r),
           r.get("gains") == 5 and r.get("over") == 0 and r.get("bank") == 0)

    # L5 a failed check claims and spends nothing.
    admin(f"[TestOnlyMasterySeed {mia} 1 + Tactics=5:1")
    r = probe(f"[TestOnlyMasteryRolls {mia} Tactics 850 0.0 60", "MasteryRolls")
    record("L5 sixty failed checks spend nothing from the store", "successes=0 bank=5 over=0", str(r),
           r.get("successes") == 0 and r.get("bank") == 5 and r.get("over") == 0)

    # L4 with the store empty and the cycle claimed, every check rolls at the class rate for its value; never more than +0.1.
    admin(f"[TestOnlyMasterySeed {mia} 1 Tactics=0:1 Anatomy=0:1 Alchemy=0:1")
    n = 20000
    for skill, cls, mult in (("Tactics", "standard", 0.10), ("Anatomy", "easy", 0.15), ("Alchemy", "hard", 0.075)):
        r = probe(f"[TestOnlyMasteryRolls {mia} {skill} 850 0.5 {n}", "MasteryRolls", wait=60.0)
        total = r.get("total", "0/7000")
        used, cap = (int(x) for x in str(total).split("/"))
        p = expected_gain_probability(85.0, used / 10.0, cap / 10.0, r.get("factor", 1.0) * r.get("multiplier", 1.0), 0.5)
        mean = n * p
        sigma = math.sqrt(n * p * (1 - p))
        gains_seen = r.get("gains", -1)
        record(f"L4 {cls} skill at 85.0, store empty: gains by chance at the class rate",
               f"multiplier {mult}; gains {mean:.0f} +/- {4 * sigma + 3:.0f}, none above 0.1, bank untouched",
               f"{r}; expected p={p:.4f}",
               abs(r.get("multiplier", 0) - mult) < 1e-9 and abs(gains_seen - mean) <= 4 * sigma + 3 and r.get("over") == 0 and r.get("bank") == 0)


def climb_to_grandmaster() -> None:
    """The exit test: only the day's allowance of valid uses, one shifted daily cycle at a time, 80.0 to 100.0."""
    mia = serial("Mia")
    plan = [("Anatomy", "easy", 20, 10), ("Tactics", "standard", 14, 15), ("Alchemy", "hard", 10, 20), ("Poisoning", "veryHard", 8, 25)]
    for skill, _, _, _ in plan:
        sset("Mia", f"[SetSkill {skill} 80")
    admin(f"[TestOnlyMasterySeed {mia} 1")  # a clean state: no stored allowance, nothing claimed

    done = {}
    odd = []
    for day in range(1, 31):
        for skill, cls, allowance, days in plan:
            if skill in done:
                continue
            r = probe(f"[TestOnlySkillUse {mia} {skill} {allowance}", "SkillUse", wait=1.2)
            before, after = r.get("before", -1), r.get("after", -1)
            if after >= 1000:
                done[skill] = (day, before, after)
            elif after - before != allowance:
                odd.append(f"{skill} day {day}: {before}->{after}")
        if len(done) == len(plan):
            break
        admin(f"[TestOnlyMasteryAge {mia} 24", wait=0.8)

    for skill, cls, allowance, days in plan:
        got = done.get(skill)
        record(f"L7 a {cls} skill ({allowance / 10.0:.1f} a day) goes 80.0 to 100.0 on the allowance alone in {days} daily cycles",
               f"100.0 on day {days}", f"day {got[0]} ({got[1]}->{got[2]})" if got else "not finished",
               got is not None and got[0] == days and got[2] == 1000)
    record("L7b every day before the last gave exactly the allowance", "no surprises", "; ".join(odd) or "none", not odd)


def faint_ceiling() -> None:
    """Faint Memories now stops where Mastery begins: 80.0 (these are faint_live.py's G1 to G3 at the new ceiling)."""
    mia = serial("Mia")

    def pool():
        text = admin(f"[SkillBankStatus {mia}", 1.5)
        hit = re.search(r"Faint Memories: (\d+\.\d) of (\d+\.\d) left, (ready|locked)", text)
        return (float(hit.group(1)), hit.group(3)) if hit else None

    admin(f"[TestOnlyFaintAge {mia} 25", wait=1.0)
    start = pool()
    record("F0 the pool is ready 25 hours after creation", "5.0, ready", str(start), start == (5.0, "ready"))

    sset("Mia", "[SetSkill Hiding 79.8")
    r = probe(f"[TestOnlySkillUse {mia} Hiding 1", "SkillUse")
    record("F1 the last 0.2 before 80.0 comes back in one step", "798 -> 800, 4.8 left", f"{r.get('before')}->{r.get('after')}; {pool()}",
           (r.get("before"), r.get("after")) == (798, 800) and pool() == (4.8, "ready"))

    left = pool()
    probe(f"[TestOnlySkillUse {mia} Hiding 3", "SkillUse")
    record("F2 at 80.0 the pool is left alone (Mastery's)", f"still {left}", str(pool()), pool() == left)

    sset("Mia", "[SetSkill Hiding 79.9")
    r = probe(f"[TestOnlySkillUse {mia} Hiding 1", "SkillUse")
    record("F3 0.1 below 80.0 only 0.1 comes back", "799 -> 800, 4.7 left", f"{r.get('before')}->{r.get('after')}; {pool()}",
           (r.get("before"), r.get("after")) == (799, 800) and pool() == (4.7, "ready"))


def phase2() -> None:
    lines = status("Mara")
    line = next((x for x in lines if x.startswith("Anatomy")), "")
    record("R1 Mastery state survives a restart", "Anatomy line with claimed state", line, "claimed this cycle" in line)
    m = mark("Mara")
    print("   (login reminder is read from the session log below)")
    with open(session("Mara")["log"], errors="replace") as handle:
        text = handle.read()
    reminder = re.findall(r"Mastery: (\d+) of your Mastery skills can claim this cycle's allowance", text)
    record("R2 login reminder counts only the skills that can claim", "1 (Alchemy is Up and unclaimed; Magery is Down; Anatomy has claimed)",
           f"reminders {reminder}", bool(reminder) and reminder[-1] == "1")


def main() -> int:
    stages = [("entry", entry_and_exhaust), ("cycles", next_cycle_and_bank), ("below", below_threshold_and_back),
              ("labels", hard_class_labels), ("legacy", legacy_state), ("cap", total_cap), ("chance", chance_path),
              ("climb", climb_to_grandmaster), ("faint", faint_ceiling), ("phase2", phase2)]
    default = ["entry", "cycles", "below", "labels", "legacy", "cap", "chance", "climb", "faint"]
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
