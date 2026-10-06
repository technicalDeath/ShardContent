"""Live checks for action auto-repeat (taming, lockpicking, spinning wheel, loom, cooking) on a disposable host named
"actions" with featureFlags.actionAutoRepeat on, ActionProbe.dll loaded, and fresh characters ActTame ActLock ActSpin
ActCook (an `admin` staff session too).

    python action_live.py tame      # one targeting keeps trying the same horse until it accepts; no second cursor
    python action_live.py lock      # one targeting keeps working the same chest until it yields
    python action_live.py lockout   # an impossible lock: the loop ends when the last pick breaks; the chest stays locked
    python action_live.py spin      # one targeting spins the whole stack, one 3-second spin at a time
    python action_live.py loom      # one targeting feeds the whole stack (stock has no timer there)
    python action_live.py cook      # one targeting cooks the whole stack, one 5-second attempt at a time
    python action_live.py cancel    # a step ends the taming loop and the cooking loop after the attempt in flight
    python action_live.py off       # control: flag off in memory, one targeting is exactly one attempt

Exits non-zero on any failure; results go to work/action-live/results-<phase>.json.
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

HOST = WORKSPACE / "work" / "hosts" / "actions"
SESSIONS = WORKSPACE / "work" / "navrey-sessions"
OUT = WORKSPACE / "work" / "action-live"
TAMING_SKILL_INDEX = 35
TAME_START = "start to tame"
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


def setup(staff, char, args: str) -> dict:
    serial = hexs(char.state["charID"])
    out = probe_json(staff, f"[TestOnlyActionSetup {serial} {args}", f"action-setup-{serial}.json")
    assert out["ok"], out
    time.sleep(1.0)
    return out


def report(staff, char) -> dict:
    serial = hexs(char.state["charID"])
    return probe_json(staff, f"[TestOnlyActionReport {serial}", f"action-report-{serial}.json")


def log_text(name: str) -> str:
    path = SESSIONS / name / "cuolog"
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def count_since(name: str, mark: int, needle: str) -> int:
    return log_text(name)[mark:].lower().count(needle.lower())


def use_on(char, item_hex: str, target_hex: str, timeout: float = 6.0) -> bool:
    char.events.drain()
    char.use("0x" + item_hex)
    if char.wait_for(Event.TARGET_REQUEST, timeout=timeout) is None:
        return False
    char.target("0x" + target_hex)
    return True


def skill_on(char, target_hex: str, timeout: float = 6.0) -> bool:
    char.events.drain()
    char.commands.send(f"useskill {TAMING_SKILL_INDEX}")
    if char.wait_for(Event.TARGET_REQUEST, timeout=timeout) is None:
        return False
    char.target("0x" + target_hex)
    return True


def later_cursors(char) -> int:
    return sum(1 for e in char.events.poll() if e.kind == Event.TARGET_REQUEST)


def no_pending_cursor(char) -> bool:
    """A restart through the stock cursor sends the client a cursor and then the cancel; nothing may be left asking."""
    reply = " ".join(char.call("target self")).lower()
    return "nothing is asking" in reply


def wait_report(staff, char, predicate, timeout: float, every: float = 3.0):
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        last = report(staff, char)
        if predicate(last):
            return last
        time.sleep(every)
    return last if last is not None and predicate(last) else None


def step_aside(char) -> None:
    x, y = char.state["charPosX"], char.state["charPosY"]
    for dx, dy in ((-1, 0), (0, 1), (0, -1), (-1, -1), (-1, 1)):
        char.gotoexact(x + dx, y + dy).wait()
        if (char.state["charPosX"], char.state["charPosY"]) != (x, y):
            return
    raise RuntimeError("could not step off the tile")


def phase_tame(staff) -> None:
    char = connect("ActTame")
    s = setup(staff, char, "tame 8")
    mark = len(log_text("ActTame"))
    check("tame:starts", skill_on(char, s["creature"]))
    began = time.time()
    done = wait_report(staff, char, lambda r: r["controlled"], timeout=300)
    attempts = count_since("ActTame", mark, TAME_START)
    check("tame:accepted-after-one-targeting", done is not None, f"{time.time() - began:.0f}s, {attempts} attempt(s), {done}")
    check("tame:no-cursor-left-pending", no_pending_cursor(char))
    check("tame:loop-ended", report(staff, char)["loops"] == 0)
    results["tame:attempts"] = {"ok": True, "detail": str(attempts)}
    if attempts == 1:
        print("NOTE tame: accepted on the first try, so the retry itself was not exercised here", flush=True)


def phase_lock(staff) -> None:
    char = connect("ActLock")
    s = setup(staff, char, "lock 42 122 40 20")  # one chance in ten per try
    mark = len(log_text("ActLock"))
    check("lock:starts", use_on(char, s["picks"], s["chest"]))
    began = time.time()
    done = wait_report(staff, char, lambda r: not r["locked"], timeout=150)
    fails = count_since("ActLock", mark, "unable to pick")
    check("lock:yields-after-one-targeting", done is not None, f"{time.time() - began:.0f}s, {fails} miss(es), {done}")
    results["lock:misses"] = {"ok": True, "detail": str(fails)}
    if fails == 0:
        print("NOTE lock: yielded on the first try, so the retry itself was not exercised here", flush=True)
    check("lock:no-second-cursor", later_cursors(char) == 0)
    check("lock:loop-ended", report(staff, char)["loops"] == 0)


def phase_lockout(staff) -> None:
    char = connect("ActLock")
    s = setup(staff, char, "lock 60 160 40 1")
    mark = len(log_text("ActLock"))
    check("lockout:starts", use_on(char, s["picks"], s["chest"]))
    done = wait_report(staff, char, lambda r: r["picks"] == 0, timeout=150)
    fails = count_since("ActLock", mark, "unable to pick")
    check("lockout:ends-when-the-last-pick-breaks", done is not None, f"{fails} miss(es), {done}")
    check("lockout:chest-still-locked", done is not None and done["locked"])
    time.sleep(4.0)
    check("lockout:loop-ended", report(staff, char)["loops"] == 0)


def phase_spin(staff) -> None:
    char = connect("ActSpin")
    n = 5
    s = setup(staff, char, f"spin {n}")
    check("spin:starts", use_on(char, s["material"], s["component"]))
    began = time.time()
    done = wait_report(staff, char, lambda r: r["wool"] == 0 and r["yarn"] == 3 * n, timeout=n * 3 + 20)
    check("spin:whole-stack-from-one-targeting", done is not None, f"{time.time() - began:.0f}s, {done}")
    check("spin:paced-by-the-stock-spin", time.time() - began >= (n - 1) * 3 - 1, f"{time.time() - began:.0f}s for {n}")
    check("spin:no-second-cursor", later_cursors(char) == 0)
    check("spin:loop-ended", report(staff, char)["loops"] == 0)


def phase_loom(staff) -> None:
    char = connect("ActSpin")
    n = 12
    s = setup(staff, char, f"loom {n}")
    check("loom:starts", use_on(char, s["material"], s["component"]))
    time.sleep(2.0)
    r = report(staff, char)
    check("loom:whole-stack-on-one-use", r["thread"] == 0 and r["bolts"] == n // 5, str(r))


def phase_cook(staff) -> None:
    char = connect("ActCook")
    n = 5
    s = setup(staff, char, f"cook {n}")
    mark = len(log_text("ActCook"))
    check("cook:starts", use_on(char, s["food"], s["fire"]))
    began = time.time()
    done = wait_report(staff, char, lambda r: r["raw"] == 0, timeout=n * 5 + 20)
    check("cook:whole-stack-from-one-targeting", done is not None, f"{time.time() - began:.0f}s, {done}")
    time.sleep(7.0)  # the last steak is consumed as its attempt begins; its result lands five seconds later
    done = report(staff, char)
    burns = count_since("ActCook", mark, "burn the food")
    check("cook:every-item-cooked-or-burned", done["cooked"] + burns == n, f"cooked {done['cooked']} burned {burns}")
    check("cook:no-cursor-left-pending", no_pending_cursor(char))
    check("cook:loop-ended", report(staff, char)["loops"] == 0)


def phase_cancel(staff) -> None:
    tamer = connect("ActTame")
    s = setup(staff, tamer, "tame 0")  # about one chance in five hundred: the loop would run until stopped
    mark = len(log_text("ActTame"))
    check("cancel:tame:starts", skill_on(tamer, s["creature"]))
    time.sleep(3.0)
    step_aside(tamer)
    time.sleep(25.0)  # the attempt in flight (at most 12 s) ends; no new one may begin
    attempts = count_since("ActTame", mark, TAME_START)
    check("cancel:tame:a-step-ends-the-loop", attempts == 1, f"{attempts} attempt(s)")
    check("cancel:tame:loop-ended", report(staff, tamer)["loops"] == 0)

    cook = connect("ActCook")
    n = 5
    s = setup(staff, cook, f"cook {n}")
    check("cancel:cook:starts", use_on(cook, s["food"], s["fire"]))
    time.sleep(1.0)
    step_aside(cook)  # still within three tiles, so the attempt in flight is not burned by distance
    time.sleep(20.0)
    r = report(staff, cook)
    check("cancel:cook:a-step-ends-the-loop", r["raw"] == n - 1, str(r))
    check("cancel:cook:loop-ended", r["loops"] == 0)


def phase_off(staff) -> None:
    staff.say("[TestOnlyActionFlag off")
    time.sleep(1.0)
    try:
        tamer = connect("ActTame")
        s = setup(staff, tamer, "tame 0")
        mark = len(log_text("ActTame"))
        check("off:tame:starts", skill_on(tamer, s["creature"]))
        time.sleep(30.0)
        check("off:tame:exactly-one-attempt", count_since("ActTame", mark, TAME_START) == 1)

        spinner = connect("ActSpin")
        s = setup(staff, spinner, "spin 3")
        check("off:spin:starts", use_on(spinner, s["material"], s["component"]))
        time.sleep(10.0)
        check("off:spin:exactly-one-spin", report(staff, spinner)["wool"] == 2)

        s = setup(staff, spinner, "loom 12")
        check("off:loom:starts", use_on(spinner, s["material"], s["component"]))
        time.sleep(2.0)
        check("off:loom:exactly-one-thread", report(staff, spinner)["thread"] == 11)

        cook = connect("ActCook")
        s = setup(staff, cook, "cook 3")
        check("off:cook:starts", use_on(cook, s["food"], s["fire"]))
        time.sleep(15.0)
        r = report(staff, cook)
        check("off:cook:exactly-one-attempt", r["raw"] == 2 and r["loops"] == 0, str(r))
    finally:
        staff.say("[TestOnlyActionFlag on")
        time.sleep(1.0)


def main() -> int:
    faulthandler.dump_traceback_later(900, exit=True)
    phase = sys.argv[1] if len(sys.argv) > 1 else ""
    staff = connect("admin")
    OUT.mkdir(parents=True, exist_ok=True)
    phases = {
        "tame": phase_tame, "lock": phase_lock, "lockout": phase_lockout, "spin": phase_spin,
        "loom": phase_loom, "cook": phase_cook, "cancel": phase_cancel, "off": phase_off,
    }
    if phase not in phases:
        print(__doc__)
        return 2
    phases[phase](staff)
    (OUT / f"results-{phase}.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"{len(results) - len(failures)}/{len(results)} passed", flush=True)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
