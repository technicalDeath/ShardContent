"""Live check of the Advanced stat rule (120 points, 30 to 60 each) on a disposable host named "tpl", with the characters created
by work/templates-live/live2.ps1. Usage: python stats_live.py"""
import json, re, sys, time
from pathlib import Path

SESSIONS = Path(__file__).resolve().parents[4] / "work" / "navrey-sessions"
failures = []

def check(case, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + case + (f"  [{detail}]" if detail else ""), flush=True)
    if not ok:
        failures.append(case)

def command(session, text):
    log = SESSIONS / session / "cuolog"
    mark = log.stat().st_size
    with open(SESSIONS / session / "cuocmd", "a", encoding="ascii") as f:
        f.write(text + "\n")
    deadline = time.time() + 20
    while time.time() < deadline:
        time.sleep(0.5)
        data = log.read_bytes()[mark:].decode("utf-8", "replace")
        if "[CMD-END]" in data:
            time.sleep(0.3)
            break
    return log.read_bytes()[mark:].decode("utf-8", "replace")

def stats_of(session):
    for _ in range(10):
        try:
            s = json.loads((SESSIONS / session / "cuostate.json").read_text(encoding="utf-8"))
            return s["str"], s["dex"], s["int"]
        except (PermissionError, json.JSONDecodeError):
            time.sleep(0.3)
    raise RuntimeError(session)

# What the player assigned on the screen (str,dex,int as the client sends them) -> what the character ends with.
CASES = {
    "AdvExact": ((60, 30, 30), (60, 30, 30)),     # a valid 120-point choice is kept exactly
    "AdvDefault": ((40, 40, 40), (40, 40, 40)),
    "AdvLow": ((30, 30, 60), (30, 30, 60)),
    "AdvOldNinety": ((60, 15, 15), (55, 33, 32)),     # an old-style 90-point packet is rescaled to 120
    "AdvBad": ((61, 30, 29), None),               # out of range: rescaled, still 120 with a 30 minimum
}
print("== screen")
text = command("admin", "charstats")
line = next((l for l in text.splitlines() if "range" in l), "")
print(" ", line[line.find("range"):])
check("screen:range-30-60", "range 30-60" in line)
check("screen:starts-40-40-40-total-120", "start 40/40/40 (total 120)" in line)
tails = re.findall(r"\(total (\d+)\)", line)
check("screen:total-holds-at-120-when-a-slider-moves", len(tails) == 3 and all(t == "120" for t in tails), str(tails))
m = re.search(r"first slider to max: (\d+)/(\d+)/(\d+)", line)
check("screen:others-stay-at-or-above-30", bool(m) and min(int(x) for x in m.groups()) >= 30, str(m.groups() if m else None))
print("== characters")
for session, (sent, expected) in CASES.items():
    got = stats_of(session)
    if expected is None:
        check(f"create:{session}", sum(got) == 120 and min(got) >= 30 and max(got) <= 60, f"sent {sent}, got {got}")
    else:
        check(f"create:{session}", got == expected, f"sent {sent}, got {got}, expected {expected}")
archer = stats_of("AdvArcher")
check("create:AdvArcher-template-unchanged", archer == (54, 33, 33), str(archer))
print(f"{'FAILED' if failures else 'all passed'}")
sys.exit(1 if failures else 0)
