"""Ward item cases that need server-side inspection: blessing, transfer reset, the aged-out timer (WardProbe.dll loaded).

    python ShardContent/tests/scenarios/ward/ward_probe_live.py

Needs the `admin` session and the Vyne and Vroc sessions on a disposable host that loaded WardProbe.dll
(see ward_live.py). Reports come back as admin system messages and are read from the admin log.
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

adm = connect("admin")
C = {n: connect(n) for n in ("Vyne", "Vroc")}
results = []


def serial(name: str) -> str:
    return str(C[name].state["charID"])


def mark() -> int:
    with open(session("admin")["log"], errors="replace") as handle:
        return len(handle.readlines())


def say(command: str, wait: float = 1.5) -> str:
    m = mark()
    adm.say(command)
    time.sleep(wait)
    with open(session("admin")["log"], errors="replace") as handle:
        return " ".join(ln.strip() for ln in handle.readlines()[m:])


def report(ward: str) -> dict:
    text = say(f"[TestOnlyWardReport {ward}")
    hit = re.search(r"WardReport (\w+) phase=(\w+) protected=(\w+) loot=(\w+) blessedFor=(\w+) holder=(\S+)", text)
    if not hit:
        return {"raw": text}
    return {"phase": hit.group(2), "protected": hit.group(3), "loot": hit.group(4), "blessedFor": hit.group(5), "holder": hit.group(6), "raw": text}


def record(case_id: str, expected: str, observed: str, ok: bool) -> None:
    results.append((case_id, ok))
    print(f"{'PASS' if ok else 'FAIL'} {case_id}: expected {expected}; observed {observed}", flush=True)


def main() -> int:
    vyne, vroc = serial("Vyne"), serial("Vroc")
    text = say(f"[TestOnlyWardAdd {vyne}")
    ward = re.search(r"\[SYSTEM\] WardAdd (\w+)", text)
    if not ward:
        print("FAIL could not add a Ward:", text)
        return 1
    ward = ward.group(1)

    r = report(ward)
    record("I1 a new regular Ward is an ordinary Unprimed item", "Unprimed, Regular, no blessing", f"{r.get('phase')}/{r.get('loot')}/{r.get('blessedFor')}",
           r.get("phase") == "Unprimed" and r.get("loot") == "Regular" and r.get("blessedFor") == "none")

    say(f"[TestOnlyWardPrime {ward} {vyne}")
    r = report(ward)
    record("I2 a Primed Ward is blessed to the protected character", "Primed, Blessed, blessedFor Vyne",
           f"{r.get('phase')}/{r.get('loot')}/{r.get('blessedFor')} (Vyne {int(vyne):X8})" if str(vyne).isdigit() else f"{r.get('phase')}/{r.get('loot')}/{r.get('blessedFor')}",
           r.get("phase") == "Primed" and r.get("loot") == "Blessed" and r.get("blessedFor") != "none")

    say(f"[TestOnlyWardMove {ward} {vroc}")
    r = report(ward)
    record("I3 moving the Ward to another character resets it completely", "Unprimed, Regular, no blessing, held by Vroc",
           f"{r.get('phase')}/{r.get('loot')}/{r.get('blessedFor')}/{r.get('holder')}",
           r.get("phase") == "Unprimed" and r.get("loot") == "Regular" and r.get("blessedFor") == "none" and "Vroc" in r.get("holder", ""))

    say(f"[TestOnlyWardPrime {ward} {vroc}")
    say(f"[TestOnlyWardAge {ward} 29")
    time.sleep(35)  # past a sweep
    r = report(ward)
    record("I4 a Primed Ward 29 quiet minutes old is still Primed", "Primed", r.get("phase"), r.get("phase") == "Primed")

    say(f"[TestOnlyWardAge {ward} 2")
    time.sleep(35)
    r = report(ward)
    record("I5 past 30 quiet minutes the sweep resets it", "Unprimed, Regular", f"{r.get('phase')}/{r.get('loot')}/{r.get('blessedFor')}",
           r.get("phase") == "Unprimed" and r.get("loot") == "Regular" and r.get("blessedFor") == "none")

    failed = [c for c, ok in results if not ok]
    print(f"\n{len(results) - len(failed)}/{len(results)} cases passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
