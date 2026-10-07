"""Faint Memories, the Skill Bank's 0.2 step, banking below the cap and Discard: live cases on a disposable host.

    python -u ShardContent/tests/scenarios/faint-memories/faint_live.py [phase2 | only <stage words> ...]

Start from work/faint-memories/setup.ps1 (host `faint-memories`, flag faintMemories on, characters Faye, Gus, Hal and Nia as Navrey
sessions plus `admin`), with TestOnlyProbe.dll and MasteryProbe.dll loaded. Skill uses are made with the probe's TestOnlySkillUse, which
runs SkillCheck.CheckSkill at a place the anti-macro check has not seen, so every use reaches the gain hook the way a real one does.
Time is rehearsed with TestOnlyFaintAge. Ivy is created here with the flag overridden off, to stand for a character created before
Faint Memories existed. Stage `phase2` runs after a server restart and checks what was saved.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(WORKSPACE, ".claude", "scripts"))

from navrey_session import connect, session  # noqa: E402
from staff_command import go_to, staff_target  # noqa: E402

STATE_FILE = os.path.join(WORKSPACE, "work", "faint-memories", "expect.json")
SKILL_ID = {"Anatomy": 1, "Hiding": 21, "Magery": 25, "Tactics": 27, "Cooking": 13}

adm = connect("admin")
C = {}
for _name in ("Faye", "Gus", "Hal", "Ivy", "Nia"):
    try:
        C[_name] = connect(_name)
    except (RuntimeError, SystemExit):
        pass
results = []
ONLY = [word.lower() for word in sys.argv[2:]] if len(sys.argv) > 2 and sys.argv[1] == "only" else []


def serial(name: str) -> str:
    return str(C[name].state["charID"])


def mark(name: str) -> int:
    with open(session(name)["log"], errors="replace") as handle:
        return len(handle.readlines())


def since(name: str, m: int) -> list:
    with open(session(name)["log"], errors="replace") as handle:
        return [ln.strip() for ln in handle.readlines()[m:]]


def admin(command: str, wait: float = 1.2) -> str:
    """Say a staff command and return the system messages it produced, joined."""
    m = mark("admin")
    adm.say(command)
    time.sleep(wait)
    return " | ".join(re.sub(r"^\[[\d:.]+\]\s*\[SYSTEM\]\s*", "", ln) for ln in since("admin", m) if "[SYSTEM]" in ln)


def record(case_id: str, expected: str, observed: str, ok: bool) -> None:
    results.append((case_id, ok))
    print(f"{'PASS' if ok else 'FAIL'} {case_id}: expected {expected}; observed {observed}", flush=True)


def stage(label: str, body) -> None:
    if ONLY and not any(word in label.lower() for word in ONLY):
        return
    print(f"--- {label}", flush=True)
    try:
        body()
    except Exception as error:  # noqa: BLE001 - a harness fault must not hide later stages
        record(label, "stage completes", f"{type(error).__name__}: {error}", False)


def gump_blocks(client) -> list:
    """[(server serial, title, [text lines])] for every window the character has open; the title is its first line of text."""
    blocks = []
    for line in client.call("gumps"):
        line = line.strip()
        head = re.match(r"\[GUMP\]\s*local 0x\w+ server (0x\w+)", line)
        if head:
            blocks.append([head.group(1), None, []])
            continue
        text = re.sub(r"^\[GUMP\]\s*", "", line)
        if text and blocks:
            if blocks[-1][1] is None:
                blocks[-1][1] = text
            blocks[-1][2].append(text)
    return blocks


def window_lines(client, title: str | None = None) -> list:
    """The text of the windows a client has open (only the ones with this title, if given), one string per piece of text."""
    return [text for _, t, lines in gump_blocks(client) if title is None or t == title for text in lines]


def respond(client, button: int, title: str, extra: str = "") -> None:
    """Press a button on the open window with this title (the Welcome guide is usually open too, so say which)."""
    for serial_, t, _ in gump_blocks(client):
        if t == title:
            client.call(f"gumpresponse {button} {extra} gump:{serial_}".replace("  ", " "))
            return
    raise RuntimeError(f"no open window titled {title!r}")


def close_gumps(client) -> None:
    """Close every window the character has open (the Welcome guide opens by itself for a new character and would take the replies)."""
    for serial_, _, _ in gump_blocks(client):
        client.call(f"gumpresponse 0 gump:{serial_}")
        time.sleep(0.3)


def open_skill_bank(client) -> None:
    close_gumps(client)
    client.say("[SkillBank")
    time.sleep(2.5)


def use(name: str, skill: str, count: int = 1):
    """(before, after, lock, total, cap) in tenths after `count` skill uses."""
    out = admin(f"[TestOnlySkillUse {serial(name)} {skill} {count}", wait=1.0 + count * 0.02)
    hit = re.search(r"SkillUse \w+ before=(\d+) after=(\d+) lock=(\w+) total=(\d+)/(\d+)", out)
    if not hit:
        raise RuntimeError(f"no SkillUse report for {name}/{skill}: {out[:200]}")
    return int(hit.group(1)), int(hit.group(2)), hit.group(3), int(hit.group(4)), int(hit.group(5))


def setskill(name: str, skill: str, value: float) -> None:
    go_to(adm, C[name])
    staff_target(adm, f"[SetSkill {skill} {value}", serial(name))


def lock(name: str, skill: str, mode: str) -> None:
    admin(f"[TestOnlyMasteryLock {serial(name)} {skill} {mode}", wait=0.6)


def status(name: str) -> str:
    return admin(f"[SkillBankStatus {serial(name)}", wait=1.5)


def pool(name: str):
    """(remaining points, 'ready' or 'locked', text) from the staff status, or None when the character has none."""
    text = status(name)
    hit = re.search(r"Faint Memories: (\d+\.\d) of (\d+\.\d) left, (ready|locked for [^;]+)", text)
    return (float(hit.group(1)), "ready" if hit.group(3) == "ready" else "locked", hit.group(3)) if hit else None


def bank(name: str) -> dict:
    """{skill: banked points} from the staff status."""
    return {m.group(1): float(m.group(2)) for m in re.finditer(r"(\w+) \(\d+\): active [\d.]+, banked ([\d.]+),", status(name))}


def total_cap(name: str):
    out = admin(f"[TestOnlyMasteryTotals {serial(name)}", wait=0.8)
    hit = re.search(r"MasteryTotals (\d+) (\d+)", out)
    return int(hit.group(1)), int(hit.group(2))


def seed(name: str, entries: str, add: bool = False) -> None:
    admin(f"[TestOnlySkillBankSeed {serial(name)} {'+ ' if add else ''}{entries}", wait=0.8)


def journal_since(name: str, m: int) -> str:
    return " ".join(since(name, m))


# ---------------------------------------------------------------------------------------------------------------------------------


def phase1() -> None:
    expect = {}
    admin("[TestOnlyFlagOverride FaintMemories true", wait=0.6)  # a stopped earlier run may have left it off

    def granted() -> None:
        for name in ("Faye", "Gus", "Hal", "Nia"):
            got = pool(name)
            record(
                f"F1 {name} starts with Faint Memories", "5.0 points, locked for about 24 hours",
                str(got), got is not None and got[0] == 5.0 and got[1] == "locked" and re.search(r"2[34] hours?", got[2]) is not None,
            )
        mine = admin(f"[SkillBankStatus {adm.state['charID']}", wait=1.2)
        record("F2 a staff character is not granted it", "no Faint Memories line", mine[-160:], "Faint Memories: 5.0" not in mine)

    stage("granted at creation", granted)

    def before_creation_flag() -> None:
        # Ivy stands for a character created before Faint Memories was switched on. The creation script starts a Navrey session that keeps
        # its output handles open, so its output goes to a file and the driver waits for the script itself, never for a pipe to close.
        if "Ivy" not in C:
            admin("[TestOnlyFlagOverride FaintMemories false", wait=0.6)
            pwsh = shutil.which("pwsh") or "pwsh"
            script = os.path.join(WORKSPACE, ".claude", "scripts", "New-TestCharacter.ps1")
            with open(os.path.join(WORKSPACE, "work", "faint-memories", "ivy.log"), "w") as out:
                created = subprocess.Popen(
                    [pwsh, "-NoProfile", "-File", script, "-HostName", "faint-memories", "-Name", "Ivy", "-Profession", "1", "-NoRestart"],
                    stdin=subprocess.DEVNULL, stdout=out, stderr=subprocess.STDOUT,
                )
                created.wait(timeout=240)
        admin("[TestOnlyFlagOverride FaintMemories true", wait=0.6)
        C["Ivy"] = connect("Ivy")
        record("F3 a character made before it was enabled has none", "none", str(pool("Ivy")), pool("Ivy") is None)
        first = admin(f"[GrantFaintMemories {serial('Ivy')}", wait=1.0)
        second = admin(f"[GrantFaintMemories {serial('Ivy')}", wait=1.0)
        record("F3b staff can grant it once", "Granted 5.0 points", first, "Granted 5.0 points of Faint Memories" in first)
        record("F3c and never twice", "already has", second, "already has Faint Memories" in second and "never granted twice" in second)
        got = pool("Ivy")
        record("F3d the granted pool shows", "5.0 locked", str(got), got is not None and got[0] == 5.0 and got[1] == "locked")

    stage("existing character and the staff grant", before_creation_flag)

    def locked_is_inert() -> None:
        setskill("Faye", "Anatomy", 50.0)
        before, after, _, _, _ = use("Faye", "Anatomy", 12)
        got = pool("Faye")
        record("F4 a locked pool is not touched", "still 5.0", f"{got}; Anatomy {before}->{after}", got is not None and got[0] == 5.0 and after - before <= 12)

    stage("locked", locked_is_inert)

    def unlock_and_use() -> None:
        admin(f"[TestOnlyFaintAge {serial('Faye')} 24.5", wait=0.8)
        got = pool("Faye")
        record("F5 24 hours after creation it unlocks", "ready", str(got), got is not None and got[1] == "ready")

        setskill("Faye", "Anatomy", 50.0)
        before, after, lk, _, _ = use("Faye", "Anatomy", 1)
        got = pool("Faye")
        record("F5b one use brings back exactly 0.2", "500 -> 502, 4.8 left", f"{before}->{after}; {got}", (before, after) == (500, 502) and got[0] == 4.8)

        m = mark("Faye")
        before, after, _, _, _ = use("Faye", "Anatomy", 24)
        got = pool("Faye")
        record("F6 25 uses use the 5.0 up", "502 -> 550, 0.0 left", f"{before}->{after}; {got}", (before, after) == (502, 550) and got[0] == 0.0)
        said = journal_since("Faye", m)
        record("F6b the player is told the last of it came back", "the last of them has come back", said[-200:], "the last of them has come back to you, into Anatomy" in said)

        before, after, _, _, _ = use("Faye", "Anatomy", 20)
        got = pool("Faye")
        record("F6c afterwards a use is the ordinary gain", "pool stays 0.0, at most +0.1 a use", f"{before}->{after}; {got}", got[0] == 0.0 and 0 <= after - before <= 20)

    stage("unlock and use", unlock_and_use)

    def windows() -> None:
        admin(f"[TestOnlyFaintAge {serial('Gus')} 25", wait=0.8)
        open_skill_bank(C["Gus"])
        text = " | ".join(window_lines(C["Gus"], "Skill Bank"))
        record("W1 a ready pool shows its banner", "Faint Memories, what is left, how to use it", text[:300],
               "Faint Memories" in text and ("of 5.0 left" in text or "5.0 points" in text)
               and "Train a skill set to Up: 0.2 per use" in text)
        close_gumps(C["Gus"])

        open_skill_bank(C["Hal"])
        text = " | ".join(window_lines(C["Hal"], "Skill Bank"))
        record("W2 a locked pool shows the countdown", "Unlocks in 23 hours 5x minutes or 24 hours", text[:300],
               re.search(r"Unlocks in (23 hours \d+ minutes?|24 hours)", text) is not None)
        close_gumps(C["Hal"])

        open_skill_bank(C["Faye"])
        text = " | ".join(window_lines(C["Faye"], "Skill Bank"))
        record("W3 a used-up pool is gone from the window", "no Faint Memories text", text[:240], "Faint Memories" not in text and "Skill Bank" in text)
        close_gumps(C["Faye"])

    stage("windows", windows)

    def ceiling_floor_locks() -> None:
        setskill("Gus", "Hiding", 89.8)
        before, after, _, _, _ = use("Gus", "Hiding", 1)
        record("G1 the last 0.2 before 90.0", "898 -> 900, 4.8 left", f"{before}->{after}; {pool('Gus')}", (before, after) == (898, 900) and pool("Gus")[0] == 4.8)

        left = pool("Gus")[0]
        use("Gus", "Hiding", 3)
        record("G2 at 90.0 the pool is left alone (Mastery's)", f"still {left}", str(pool("Gus")), pool("Gus")[0] == left)

        setskill("Gus", "Hiding", 89.9)
        before, after, _, _, _ = use("Gus", "Hiding", 1)
        record("G3 0.1 below 90.0 only 0.1 comes back", "899 -> 900", f"{before}->{after}; {pool('Gus')}", (before, after) == (899, 900) and pool("Gus")[0] == 4.7)

        setskill("Gus", "Cooking", 9.9)
        before, after, _, _, _ = use("Gus", "Cooking", 1)
        record("G4 below 10.0 the stock gain is left to run", "pool still 4.7", f"{before}->{after}; {pool('Gus')}", pool("Gus")[0] == 4.7 and after > before)

        setskill("Gus", "Cooking", 10.0)
        before, after, _, _, _ = use("Gus", "Cooking", 1)
        record("G5 at 10.0 it applies", "100 -> 102, 4.5 left", f"{before}->{after}; {pool('Gus')}", (before, after) == (100, 102) and pool("Gus")[0] == 4.5)

        for mode in ("down", "locked"):
            lock("Gus", "Cooking", mode)
            before, after, lk, _, _ = use("Gus", "Cooking", 4)
            record(f"G6 a {mode} skill gets nothing", "unchanged, pool 4.5", f"{before}->{after} {lk}; {pool('Gus')}", before == after and pool("Gus")[0] == 4.5)
        lock("Gus", "Cooking", "up")

    stage("ceiling, floor and locks", ceiling_floor_locks)

    def cap_and_priority() -> None:
        total, cap = total_cap("Gus")
        admin(f"[TestOnlySkillCap {serial('Gus')} {total}", wait=0.6)
        before, after, _, t, c = use("Gus", "Cooking", 3)
        record("G7 at the total cap the pool waits", "no change, pool 4.5", f"{before}->{after} {t}/{c}; {pool('Gus')}", pool("Gus")[0] == 4.5 and t <= c)
        admin(f"[TestOnlySkillCap {serial('Gus')} 7000", wait=0.6)

        seed("Gus", "Cooking=10")
        before, after, _, _, _ = use("Gus", "Cooking", 1)
        record("G8 a skill's own banked points come back first", "+0.2 from the bank, pool still 4.5", f"{before}->{after}; bank {bank('Gus')}; {pool('Gus')}",
               after - before == 2 and bank("Gus").get("Cooking") == 0.8 and pool("Gus")[0] == 4.5)

    stage("total cap and bank first", cap_and_priority)

    def bank_steps() -> None:
        setskill("Hal", "Tactics", 50.0)
        lock("Hal", "Tactics", "up")
        seed("Hal", "Tactics=10")
        before, after, _, _, _ = use("Hal", "Tactics", 1)
        record("B1 the bank returns 0.2 a use", "500 -> 502, 0.8 banked", f"{before}->{after}; {bank('Hal')}", (before, after) == (500, 502) and bank("Hal").get("Tactics") == 0.8)
        before, after, _, _, _ = use("Hal", "Tactics", 4)
        record("B2 four more empty it", "502 -> 510, nothing banked", f"{before}->{after}; {bank('Hal')}", (before, after) == (502, 510) and "Tactics" not in bank("Hal"))

        setskill("Hal", "Tactics", 50.0)
        seed("Hal", "Tactics=3")
        before, after, _, _, _ = use("Hal", "Tactics", 1)
        left = bank("Hal").get("Tactics")
        before2, after2, _, _, _ = use("Hal", "Tactics", 1)
        record("B3 the last odd tenth comes back alone", "+0.2 then +0.1", f"{after - before}, {after2 - before2}; left {left}; {bank('Hal')}",
               after - before == 2 and left == 0.1 and after2 - before2 == 1 and "Tactics" not in bank("Hal"))

        setskill("Hal", "Tactics", 99.9)
        seed("Hal", "Tactics=5")
        before, after, _, _, _ = use("Hal", "Tactics", 1)
        record("B4 with 0.1 of room under the skill's cap only 0.1 returns", "999 -> 1000, 0.4 banked", f"{before}->{after}; {bank('Hal')}",
               (before, after) == (999, 1000) and bank("Hal").get("Tactics") == 0.4)
        admin(f"[TestOnlySkillBankSeed {serial('Hal')} Tactics=0", wait=0.6)  # replaces the bank with an (empty) one

    stage("the 0.2 step", bank_steps)

    def at_cap_exchange() -> None:
        setskill("Hal", "Tactics", 50.0)
        setskill("Hal", "Magery", 50.0)
        lock("Hal", "Tactics", "up")
        lock("Hal", "Magery", "down")
        total, _ = total_cap("Hal")
        admin(f"[TestOnlySkillCap {serial('Hal')} {total}", wait=0.6)
        seed("Hal", "Tactics=10")
        before, after, _, t, c = use("Hal", "Tactics", 1)
        got = bank("Hal")
        record("B5 at the cap 0.2 comes out of a Down skill and is banked for it", "Tactics +0.2, Magery's 0.2 banked, total unchanged",
               f"{before}->{after} {t}/{c}; {got}", after - before == 2 and got.get("Tactics") == 0.8 and got.get("Magery") == 0.2 and t == total)
        admin(f"[TestOnlySkillCap {serial('Hal')} 7000", wait=0.6)
        lock("Hal", "Magery", "up")

    stage("the 0.2 step at the cap", at_cap_exchange)

    def below_cap_banking() -> None:
        admin(f"[TestOnlySkillBankSeed {serial('Hal')} Tactics=0", wait=0.6)
        setskill("Hal", "Hiding", 50.0)
        setskill("Hal", "Anatomy", 50.0)
        lock("Hal", "Hiding", "down")
        lock("Hal", "Anatomy", "up")
        lock("Hal", "Magery", "up")
        lock("Hal", "Tactics", "locked")
        total, _ = total_cap("Hal")
        admin(f"[TestOnlySkillCap {serial('Hal')} {total * 2}", wait=0.6)
        before, after, _, t, c = use("Hal", "Anatomy", 200)
        got = bank("Hal")
        hiding = None
        out = admin(f"[TestOnlySkillUse {serial('Hal')} Hiding 0", wait=0.8)
        hit = re.search(r"before=(\d+)", out)
        hiding = int(hit.group(1)) if hit else None
        lost = (500 - hiding) / 10.0 if hiding is not None else None
        record("B6 a Down skill's lost points are banked well below the cap",
               "Hiding banked = what it lost, more than 0, total below the cap",
               f"Anatomy {before}->{after}; Hiding {hiding}; bank {got}; {t}/{c}",
               lost is not None and lost > 0 and got.get("Hiding") == lost and t < c)

    stage("banking below the cap", below_cap_banking)

    def discard_flow() -> None:
        seed("Hal", "Anatomy=35 Hiding=12:down")
        open_skill_bank(C["Hal"])
        buttons = [b.strip() for b in C["Hal"].call("gumps") if "[button 30" in b]
        record("D1 each bank row has a Discard button", "two buttons, 3001 and 3021", str(buttons), len(buttons) == 2)

        respond(C["Hal"], 3000 + SKILL_ID["Anatomy"], "Skill Bank")
        time.sleep(1.5)
        text = " | ".join(window_lines(C["Hal"], "Discard banked points"))
        record("D2 it asks first, saying what goes", "question, 3.5 points, type discard",
               text[:300], "Discard the banked points of Anatomy?" in text and "3.5 banked points will be deleted for good" in text
               and "Type discard in the box to confirm:" in text)

        respond(C["Hal"], 1, "Discard banked points", "text:1=yes")
        time.sleep(1.5)
        text = " | ".join(window_lines(C["Hal"], "Skill Bank"))
        record("D3 the wrong word discards nothing", "Nothing was discarded; Anatomy still 3.5", f"{text[-200:]}; {bank('Hal')}",
               "Nothing was discarded: discard was not typed." in text and bank("Hal").get("Anatomy") == 3.5)

        respond(C["Hal"], 3000 + SKILL_ID["Anatomy"], "Skill Bank")
        time.sleep(1.2)
        respond(C["Hal"], 2, "Discard banked points")
        time.sleep(1.5)
        text = " | ".join(window_lines(C["Hal"], "Skill Bank"))
        record("D4 Keep them discards nothing", "Nothing was discarded; Anatomy still 3.5", f"{text[-200:]}; {bank('Hal')}",
               "Nothing was discarded. Anatomy keeps its 3.5 banked points." in text and bank("Hal").get("Anatomy") == 3.5)

        respond(C["Hal"], 3000 + SKILL_ID["Anatomy"], "Skill Bank")
        time.sleep(1.2)
        respond(C["Hal"], 1, "Discard banked points", "text:1=Discard")
        time.sleep(1.5)
        text = " | ".join(window_lines(C["Hal"], "Skill Bank"))
        got = bank("Hal")
        record("D5 typing discard discards that skill's points only", "Anatomy gone, Hiding 1.2 kept, notice",
               f"{text[-220:]}; {got}", "Discarded 3.5 banked points of Anatomy." in text and "Anatomy" not in got and got.get("Hiding") == 1.2)
        close_gumps(C["Hal"])
        admin(f"[TestOnlySkillCap {serial('Hal')} 7000", wait=0.5)

    stage("discard", discard_flow)

    def save_expectations() -> None:
        expect["Gus"] = pool("Gus")[0]
        expect["Nia"] = pool("Nia")[0]
        expect["Faye"] = pool("Faye")[0]
        expect["HalBank"] = bank("Hal")
        with open(STATE_FILE, "w") as handle:
            json.dump(expect, handle)
        print(f"saved expectations {expect}", flush=True)

    stage("save expectations for phase 2", save_expectations)


def phase2() -> None:
    with open(STATE_FILE) as handle:
        expect = json.load(handle)

    def persisted() -> None:
        for name in ("Gus", "Nia", "Faye"):
            got = pool(name)
            record(f"P1 {name}'s Faint Memories survived the restart", f"{expect[name]} left", str(got), got is not None and got[0] == expect[name])
        record("P2 Hal's bank (with the Discard) survived", str(expect["HalBank"]), str(bank("Hal")), bank("Hal") == expect["HalBank"])
        got = pool("Nia")
        record("P3 the unlock clock kept running from creation", "still locked, about 24 hours", str(got), got is not None and got[1] == "locked")

    stage("after the restart", persisted)


if __name__ == "__main__":
    (phase2 if len(sys.argv) > 1 and sys.argv[1] == "phase2" else phase1)()
    failed = [case for case, ok in results if not ok]
    print(f"\n{len(results) - len(failed)} passed, {len(failed)} failed", flush=True)
    sys.exit(1 if failed else 0)
