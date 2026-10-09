"""Live checks for the sub-95 skill-gain curve (Beta 1 item 3) on a disposable host with featureFlags.skillGainCurve on,
GainProbe.dll loaded, and one Player-level character named GainPlayer (plus the staff session "admin").

    python gain_live.py all

Cases:
  rates     measured gain rate with the curve vs the same server with the curve switched off, per class and band below
            Mastery's 80.0: the ratio must equal the approved multiplier (1.5, 1.0) within sampling error. From 80.0 the rate is
            Mastery's chance path beside its guaranteed gains, measured by tests/scenarios/mastery/mastery_live.py stage `chance`
  sub10     below 10.0 gain stays unconditional and identical
  mastery   (retired: Mastery no longer suppresses the stock roll from its threshold; see mastery_live.py stage `chance`)
  staff     a staff character gets stock gain (ratio 1.0)
  bank      Skill Bank restoration is exact and identical with the curve on and off
  off       with the flag off, the multiplier is 1.0 and [SkillClasses says gain is stock
  command   a player's [SkillClasses lists every class with its bands
  training  real Spirit Speak uses through the client gain skill with the curve on

Exits non-zero on any failure; results go to work/gain-live/results.json.
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

HOST = WORKSPACE / "work" / "hosts" / "gain"
OUT = WORKSPACE / "work" / "gain-live"
N = 6000
failures: list[str] = []
results: dict = {}


def check(case: str, ok: bool, detail: str = "") -> None:
    results[case] = {"ok": bool(ok), "detail": detail}
    print(("PASS " if ok else "FAIL ") + case + (f"  [{detail}]" if detail else ""), flush=True)
    if not ok:
        failures.append(case)


def hexs(serial) -> str:
    return serial[2:].upper().lstrip("0") if isinstance(serial, str) else f"{serial:X}"


def probe_json(staff, command: str, filename: str, timeout: float = 30.0) -> dict:
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


def run(staff, serial: str, skill: str, base: float, mode: str, n: int = N, chance: float = 0.5, reset: int = 1) -> dict:
    return probe_json(
        staff,
        f"[TestOnlyGainRun {serial} {skill} {base} {n} {chance} {mode} {reset}",
        f"gain-run-{serial}.json", timeout=180,
    )


def ratio(staff, serial: str, skill: str, base: float) -> tuple[float, dict, dict]:
    curve = run(staff, serial, skill, base, "curve")
    stock = run(staff, serial, skill, base, "stock")
    return curve["rate"] / stock["rate"], curve, stock


def phase_rates(staff, serial: str) -> None:
    cases = [
        ("Archery", "easy", 30.0, 1.5), ("Archery", "easy", 79.0, 1.5),
        ("Swords", "standard", 30.0, 1.5), ("Swords", "standard", 65.0, 1.5),
        ("Swords", "standard", 75.0, 1.0), ("Swords", "standard", 79.5, 1.0),
        ("Blacksmith", "hard", 30.0, 1.5), ("Blacksmith", "hard", 75.0, 1.0),
    ]
    for skill, cls, base, mult in cases:
        r, curve, stock = ratio(staff, serial, skill, base)
        # Sampling error on a ratio of two rates near 0.3 with n=6000 each is about 4%; allow three times that.
        check(f"rates:{cls}:{skill}@{base}:x{mult}", abs(r / mult - 1) < 0.12,
              f"ratio {r:.3f}, curve rate {curve['rate']:.4f}, stock rate {stock['rate']:.4f}, mult@start {curve['multiplierAtStart']}")


def phase_sub10(staff, serial: str) -> None:
    for mode in ("curve", "stock"):
        out = run(staff, serial, "Archery", 5.0, mode, n=500)
        check(f"sub10:{mode}:every-check-gains", out["gainEvents"] == 500, str(out))


def phase_mastery(staff, serial: str) -> None:
    # Retired: from 80.0 Mastery hands every use that is not a guaranteed gain back to the stock roll, so the rate there is measured
    # (against the formula, with the allowance spent) by mastery_live.py stage `chance`.
    return


def phase_staff(staff, admin_serial: str) -> None:
    curve = run(staff, admin_serial, "Swords", 30.0, "curve")
    stock = run(staff, admin_serial, "Swords", 30.0, "stock")
    check("staff:multiplier-is-1", curve["multiplierAtStart"] == 1.0, str(curve))
    # The staff character may not gain at all (locked skills); when it does, the two modes must match.
    if stock["rate"] > 0:
        check("staff:stock-gain-with-curve-on", abs(curve["rate"] / stock["rate"] - 1) < 0.12,
              f"curve {curve['rate']:.4f}, stock {stock['rate']:.4f}")


def phase_bank(staff, serial: str) -> None:
    for mode in ("curve", "stock"):
        probe_json(staff, f"[TestOnlyGainSet {serial} Swords 40", f"gain-set-{serial}.json")
        probe_json(staff, f"[TestOnlyGainBank {serial} Swords 20", f"gain-bank-{serial}.json")
        out = run(staff, serial, "Swords", 40.0, mode, n=20, reset=0)
        rep = probe_json(staff, f"[TestOnlyGainReport {serial} Swords", f"gain-report-{serial}.json")
        check(f"bank:{mode}:restores-exactly-the-banked-tenths", out["gainedTenths"] == 20 and rep["bankTenths"] == 0,
              f"{out}  bank after {rep['bankTenths']}")


def journal(owner_name: str) -> Path:
    return WORKSPACE / "work" / "navrey-sessions" / owner_name / "cuolog"


def phase_command(staff, serial: str) -> None:
    player = connect("GainPlayer")
    log = journal("GainPlayer")
    player.say("[SkillClasses")
    time.sleep(3)
    text = " ".join(line.strip() for line in player.call("gumps"))
    # The window is the guide's: an overview with each class's speeds, then a page per class with its skills.
    for line in ("Easy skills (19)", "1.5x stock speed from 10 to 80, 0.15x stock speed from 80 to 100",
                 "Standard skills (26)", "1.5x stock speed from 10 to 70, stock speed from 70 to 80, 0.1x stock speed from 80 to 100",
                 "Hard skills (4)", "1.5x stock speed from 10 to 70, stock speed from 70 to 80, 0.075x stock speed from 80 to 100"):
        check(f"command:lists:{line[:14]}", line in text, text[-300:])
    for name in ("Animal Taming", "Blacksmithy", "Alchemy", "Poisoning", "Archery", "Magery", "Swords"):
        check(f"command:names:{name}", name in text)
    check("command:no-veryhard-page", "Very hard" not in text and "VeryHard" not in text, text[-200:])


def phase_off(staff, serial: str) -> None:
    staff.say("[TestOnlyGainFlag off")
    time.sleep(1)
    try:
        asis = run(staff, serial, "Archery", 30.0, "asis")
        stock = run(staff, serial, "Archery", 30.0, "stock")
        check("off:multiplier-is-1", asis["multiplierAtStart"] == 1.0, str(asis))
        check("off:rate-equals-stock", abs(asis["rate"] / stock["rate"] - 1) < 0.12,
              f"flag-off rate {asis['rate']:.4f}, stock rate {stock['rate']:.4f}")
        player = connect("GainPlayer")
        log = journal("GainPlayer")
        mark = log.stat().st_size
        player.say("[SkillClasses")
        time.sleep(3)
        text = log.read_bytes()[mark:].decode("utf-8", "replace")
        check("off:command-says-stock", "Skills gain at the stock rate" in text, text[-200:])
    finally:
        staff.say("[TestOnlyGainFlag on")
        time.sleep(1)


def phase_training(staff, serial: str) -> None:
    player = connect("GainPlayer")
    probe_json(staff, f"[TestOnlyGainSet {serial} SpiritSpeak 30", f"gain-set-{serial}.json")
    before = probe_json(staff, f"[TestOnlyGainReport {serial} SpiritSpeak", f"gain-report-{serial}.json")
    uses = 120
    for i in range(uses):
        player.call("useskill spirit speak")
        time.sleep(1.2)
        if i % 20 == 19:
            print(f"  training {i + 1}/{uses}", flush=True)
    after = probe_json(staff, f"[TestOnlyGainReport {serial} SpiritSpeak", f"gain-report-{serial}.json")
    gained = after["baseTenths"] - before["baseTenths"]
    check("training:real-uses-gain-skill", gained >= 5, f"gained {gained / 10:.1f} over {uses} uses; multiplier {after['multiplier']}")


def main(argv: list) -> int:
    if len(argv) != 2 or argv[1] != "all":
        print(__doc__)
        return 2
    OUT.mkdir(parents=True, exist_ok=True)
    faulthandler.dump_traceback_later(90, repeat=True, file=sys.stderr)
    staff = connect("admin")
    player = connect("GainPlayer").state["charID"]
    serial = hexs(player)
    admin_serial = hexs(staff.state["charID"])
    print(f"player {serial}, staff {admin_serial}", flush=True)
    for name, fn, who in (
        ("rates", phase_rates, serial), ("sub10", phase_sub10, serial), ("mastery", phase_mastery, serial),
        ("staff", phase_staff, admin_serial), ("bank", phase_bank, serial), ("command", phase_command, serial),
        ("off", phase_off, serial), ("training", phase_training, serial),
    ):
        print(f"== {name} {time.strftime('%H:%M:%S')}", flush=True)
        fn(staff, who)
    (OUT / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"{len(results) - len(failures)}/{len(results)} passed", flush=True)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

