"""Live check that the real character-creation screens produce correct characters (Beta 1 item 5, trimmed by the owner to one
profession template and Advanced). Characters UiRanger and UiAdvanced are created by work/templates-live/live3.ps1 with the
Navrey command createui, which drives the real gumps through their own handlers (name and Next, the folders and card, or Advanced
with its drop-downs and sliders, Finish). Usage: python ui_live.py"""
import json, re, sys, time
from pathlib import Path

SESSIONS = Path(__file__).resolve().parents[4] / "work" / "navrey-sessions"
failures = []


def check(case, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + case + (f"  [{detail}]" if detail else ""), flush=True)
    if not ok:
        failures.append(case)


def log_text(session):
    return (SESSIONS / session / "cuolog").read_bytes().decode("utf-8", "replace")


def command(session, text):
    log = SESSIONS / session / "cuolog"
    mark = log.stat().st_size
    with open(SESSIONS / session / "cuocmd", "a", encoding="ascii") as f:
        f.write(text + "\n")
    deadline = time.time() + 20
    while time.time() < deadline:
        time.sleep(0.5)
        if "[CMD-END]" in log.read_bytes()[mark:].decode("utf-8", "replace"):
            time.sleep(0.3)
            break
    return log.read_bytes()[mark:].decode("utf-8", "replace")


def state(session):
    for _ in range(10):
        try:
            return json.loads((SESSIONS / session / "cuostate.json").read_text(encoding="utf-8"))
        except (PermissionError, json.JSONDecodeError):
            time.sleep(0.3)
    raise RuntimeError(session)


def skills(session):
    text = command(session, "skills")
    return {m.group(1).strip(): float(m.group(3)) for m in re.finditer(r"\[SKILL\]\s+(.+?)\s+([\d.]+) \(base\s+([\d.]+)\)", text)}


def norm(n):
    return re.sub(r"[^a-z]", "", n.lower().replace("fletching", ""))


print("== UiRanger: Adventurer > Archer > Ranger")
log = log_text("UiRanger")
check("ranger:walked-the-folders", all(f"picked {s}" in log for s in ("Adventurer", "Archer", "Ranger")),
      ", ".join(re.findall(r"picked (\w+)", log)))
check("ranger:finished-the-screens", "Finished the creation screens for 'UiRanger'" in log)
s = state("UiRanger")
check("ranger:in-the-world-with-its-name", s["inGame"] and s["charName"] == "UiRanger", s["charName"])
got = {norm(n): round(b) for n, b in skills("UiRanger").items() if b >= 4.9}
check("ranger:era-skills", got == {"archery": 50, "tracking": 35, "animaltaming": 35}, str(got))
stats = (s["str"], s["dex"], s["int"])
check("ranger:stats-120-with-30-minimum", stats == (54, 33, 33), str(stats))

print("== UiAdvanced: Advanced with Magery, Meditation, Evaluating Intelligence, Wrestling and stats 60/30/30")
log = log_text("UiAdvanced")
held = re.search(r"Advanced screen held: (.*)", log)
print("  ", held.group(1) if held else "(no line)")
check("advanced:picked-advanced", "picked Advanced" in log)
check("advanced:screen-held-the-stats", bool(held) and "stats 60/30/30" in held.group(1), held.group(1) if held else "")
check("advanced:finished-the-screens", "Finished the creation screens for 'UiAdvanced'" in log)
s = state("UiAdvanced")
check("advanced:in-the-world-with-its-name", s["inGame"] and s["charName"] == "UiAdvanced", s["charName"])
stats = (s["str"], s["dex"], s["int"])
check("advanced:stats-exactly-as-assigned", stats == (60, 30, 30) and sum(stats) == 120, str(stats))
got = {norm(n): round(b) for n, b in skills("UiAdvanced").items() if b >= 4.9}
check("advanced:chosen-skills", set(got) == {"magery", "meditation", "evaluatingintelligence", "wrestling"}, str(got))
check("advanced:skill-points", sum(got.values()) in (100, 120), f"{sum(got.values())} points: {got}")

print("all passed" if not failures else "FAILED")
sys.exit(1 if failures else 0)
