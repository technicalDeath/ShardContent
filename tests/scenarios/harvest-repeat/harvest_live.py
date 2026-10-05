"""Live checks for harvest auto-repeat on a disposable host named "harvest" with featureFlags.harvestAutoRepeat on,
HarvestProbe.dll loaded, and fresh characters HarvMine HarvTree HarvWater HarvStop (an `admin` staff session too).

    python harvest_live.py mine      # one targeting mines the bank dry; the stock "no metal" message ends it
    python harvest_live.py tree      # same for lumberjacking (hatchet equipped)
    python harvest_live.py water     # same for fishing
    python harvest_live.py cancel    # walking, another skill, war mode, damage and a fresh cursor each end the loop;
                                     # picking a new target mid-loop moves the loop onto it
    python harvest_live.py skill     # just the another-skill cancel (the cancel phase runs it too)
    python harvest_live.py off       # control: flag off in memory, one targeting is exactly one attempt (stock)

Each case takes a bank nobody has touched (the nearest untouched mountain, tree or shore from a hint that moves along
until the bank is full enough). Exits non-zero on any failure; results go to work/harvest-live/results-<phase>.json.
"""

from __future__ import annotations

import faulthandler
import json
import sys
import time
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(WORKSPACE / ".claude" / "scripts"))

from navrey_session import connect  # noqa: E402
from uo import Event  # noqa: E402

HOST = WORKSPACE / "work" / "hosts" / "harvest"
SESSIONS = WORKSPACE / "work" / "navrey-sessions"
OUT = WORKSPACE / "work" / "harvest-live"
HINTS = {"mine": (2570, 520), "tree": (1450, 1600), "water": (2900, 700)}
EXHAUSTED_TEXT = {"mine": "no metal here", "tree": "not enough wood", "water": "fish don"}
failures: list[str] = []
results: dict = {}


def check(case: str, ok: bool, detail: str = "") -> None:
    results[case] = {"ok": bool(ok), "detail": detail}
    print(("PASS " if ok else "FAIL ") + case + (f"  [{detail}]" if detail else ""), flush=True)
    if not ok:
        failures.append(case)


def hexs(serial) -> str:
    return serial[2:].upper().lstrip("0") if isinstance(serial, str) else f"{serial:X}"


def probe_json(staff, command: str, filename: str, timeout: float = 15.0) -> dict:
    path = HOST / filename
    before = path.stat().st_mtime if path.exists() else 0
    staff.say(command)
    deadline = time.time() + timeout
    while time.time() < deadline:
        if path.exists() and path.stat().st_mtime > before:
            time.sleep(0.2)
            return json.loads(path.read_text(encoding="utf-8"))
        time.sleep(0.3)
    raise RuntimeError(f"no fresh {filename} after: {command}")


def log_text(name: str) -> str:
    path = SESSIONS / name / "cuolog"
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def bank(staff, kind: str, x: int, y: int, leave: int = -1) -> dict:
    return probe_json(staff, f"[TestOnlyHarvestBank {kind} {x} {y} {leave}", "harvest-bank.json")


def status(staff) -> list[str]:
    start = len(log_text("admin"))
    staff.say("[HarvestRepeatStatus")
    time.sleep(2.0)
    return [line for line in log_text("admin")[start:].splitlines() if "oop" in line]


def loops_in_flight(staff) -> int:
    for line in status(staff):
        if "Loops in flight:" in line:
            return int(line.rsplit("Loops in flight:", 1)[1].strip(" ."))
    raise RuntimeError("no 'Loops in flight' line from [HarvestRepeatStatus")


def setup(staff, char, kind: str, hint_step: int = 0, need: int = 12) -> dict:
    """Move the character to an untouched bank with the tool; returns the setup JSON."""
    serial = hexs(char.state["charID"])
    hx, hy = HINTS[kind]
    for attempt in range(8):
        out = probe_json(
            staff,
            f"[TestOnlyHarvestSetup {serial} {kind} {hx + (hint_step + attempt) * 30} {hy}",
            f"harvest-setup-{serial}.json",
        )
        assert out["ok"], out
        if out["bank"] >= need:
            break
    else:
        raise RuntimeError(f"no {kind} bank with {need}+ left after 8 tries")

    stand = out["stand"]
    assert char.wait(lambda: (char.state["charPosX"], char.state["charPosY"]) == (stand["x"], stand["y"]), timeout=15), \
        f"character never arrived at {stand}: {char.state['charPosX']},{char.state['charPosY']}"
    time.sleep(1.0)
    return out


def answer_cursor_with_tile(char, tool_hex: str, tile: dict, timeout: float = 6.0) -> bool:
    char.events.drain()
    char.use("0x" + tool_hex)

    if char.wait_for(Event.TARGET_REQUEST, timeout=timeout) is None:
        return False

    char.commands.send(f"targettile {tile['x']} {tile['y']} {tile['z']} {tile['graphic']}")
    return True


def wait_bank(staff, kind: str, t: dict, predicate, timeout: float, every: float = 2.5):
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        last = bank(staff, kind, t["x"], t["y"])
        if predicate(last):
            return last
        time.sleep(every)
    return None


def repeat_case(staff, kind: str, char_name: str, leave: int) -> None:
    char = connect(char_name)
    s = setup(staff, char, kind)
    t, tool, consumed = s["target"], s["tool"], s["consumed"]
    start = bank(staff, kind, t["x"], t["y"], leave)
    check(f"{kind}:bank-seeded", start["after"] == leave, f"before {start['before']} after {start['after']}")

    char.events.drain()
    ok = answer_cursor_with_tile(char, tool, t)
    check(f"{kind}:one-targeting-starts-harvest", ok)
    if not ok:
        return

    began = time.time()
    done = wait_bank(staff, kind, t, lambda b: b["after"] < consumed, timeout=240)
    check(f"{kind}:bank-drained-by-one-targeting", done is not None,
          f"took {time.time() - began:.0f}s from {leave}; last {done}")
    time.sleep(4.0)
    check(f"{kind}:stock-exhausted-message", EXHAUSTED_TEXT[kind] in log_text(char_name).lower(),
          EXHAUSTED_TEXT[kind])
    late = [e for e in char.events.poll() if e.kind == Event.TARGET_REQUEST]
    check(f"{kind}:no-second-cursor-was-needed", not late, f"{len(late)} cursor request(s) after the first")
    check(f"{kind}:loop-ended-at-exhaustion", loops_in_flight(staff) == 0, "Loops in flight")


def cancel_case(staff, name: str, step: int, act) -> None:
    char = connect("HarvStop")
    s = setup(staff, char, "mine", hint_step=step)
    t, tool = s["target"], s["tool"]
    start = bank(staff, "mine", t["x"], t["y"], 30)
    b0 = start["after"]

    if not answer_cursor_with_tile(char, tool, t):
        check(f"cancel:{name}:starts", False, "no cursor")
        return

    got_going = wait_bank(staff, "mine", t, lambda b: b["after"] <= b0 - 2, timeout=40)
    check(f"cancel:{name}:loop-was-running", got_going is not None, f"from {b0}")
    if got_going is None:
        return

    act(char, s)
    time.sleep(6.0)  # the attempt already in flight still lands
    b1 = bank(staff, "mine", t["x"], t["y"])["after"]
    time.sleep(8.0)
    b2 = bank(staff, "mine", t["x"], t["y"])["after"]
    check(f"cancel:{name}:harvesting-stopped", b1 == b2 and b2 > 0, f"{b1} then {b2}")
    check(f"cancel:{name}:loop-ended", loops_in_flight(staff) == 0)


def act_walk(char, s) -> None:
    sx, sy = s["stand"]["x"], s["stand"]["y"]
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1)):
        char.gotoexact(sx + dx, sy + dy).wait()
        if (char.state["charPosX"], char.state["charPosY"]) != (sx, sy):
            return
    raise RuntimeError("could not step off the standing tile")


def act_skill(char, s) -> None:
    char.commands.send("useskill hiding")


def act_war(char, s) -> None:
    char.commands.send("war")


def act_hurt(char, s) -> None:
    connect("admin").say(f"[TestOnlyHarvestHurt {hexs(char.state['charID'])} 3")


def act_cursor(char, s) -> None:
    char.events.drain()
    char.use("0x" + s["tool"])
    char.wait_for(Event.TARGET_REQUEST, timeout=6)  # left open on purpose; the loop must stop at the next boundary
    time.sleep(8.0)
    char.commands.send("canceltarget")


def retarget_case(staff) -> None:
    char = connect("HarvStop")
    s = setup(staff, char, "mine", hint_step=6)
    t, tool = s["target"], s["tool"]
    alts = s["alts"]
    check("cancel:retarget:has-alternate-tile", len(alts) > 0, str(alts))
    if not alts:
        return
    alt = alts[0]
    b0 = bank(staff, "mine", t["x"], t["y"], 30)["after"]

    if not answer_cursor_with_tile(char, tool, t):
        check("cancel:retarget:starts", False, "no cursor")
        return
    time.sleep(1.0)
    ok = answer_cursor_with_tile(char, tool, alt)  # mid-attempt: stock refuses, the loop must carry it out
    check("cancel:retarget:second-targeting-answered", ok)
    time.sleep(10.0)
    lines = status(staff)
    where = f"{alt['x']},{alt['y']},{alt['z']}"
    check("cancel:retarget:loop-moved-to-new-tile", any(where in line for line in lines), f"{where} in {lines}")
    b1 = bank(staff, "mine", t["x"], t["y"])["after"]
    check("cancel:retarget:still-harvesting", b1 < b0, f"{b0} -> {b1}")
    act_walk(char, s)  # leave it tidy
    time.sleep(8.0)


def phase_off(staff) -> None:
    staff.say("[TestOnlyHarvestFlag off")
    time.sleep(1.0)
    try:
        char = connect("HarvStop")
        s = setup(staff, char, "mine", hint_step=7)
        t, tool = s["target"], s["tool"]
        b0 = bank(staff, "mine", t["x"], t["y"], 30)["after"]
        check("off:starts", answer_cursor_with_tile(char, tool, t))
        time.sleep(14.0)
        b1 = bank(staff, "mine", t["x"], t["y"])["after"]
        check("off:exactly-one-attempt-like-stock", b1 == b0 - 1, f"{b0} -> {b1}")
        check("off:no-loop", loops_in_flight(staff) == 0)
    finally:
        staff.say("[TestOnlyHarvestFlag on")
        time.sleep(1.0)


def main() -> int:
    faulthandler.dump_traceback_later(900, exit=True)
    phase = sys.argv[1] if len(sys.argv) > 1 else ""
    staff = connect("admin")
    OUT.mkdir(parents=True, exist_ok=True)

    if phase == "mine":
        repeat_case(staff, "mine", "HarvMine", leave=5)
    elif phase == "tree":
        repeat_case(staff, "tree", "HarvTree", leave=25)  # ten per chop, so two chops
    elif phase == "water":
        repeat_case(staff, "water", "HarvWater", leave=3)
    elif phase == "cancel":
        cases = [("walk", act_walk), ("skill", act_skill), ("war", act_war), ("hurt", act_hurt), ("cursor", act_cursor)]
        for i, (name, act) in enumerate(cases):
            cancel_case(staff, name, i, act)
        retarget_case(staff)
    elif phase == "skill":
        cancel_case(staff, "skill", 1, act_skill)
    elif phase == "off":
        phase_off(staff)
    else:
        print(__doc__)
        return 2

    (OUT / f"results-{phase}.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"{len(results) - len(failures)}/{len(results)} passed", flush=True)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
