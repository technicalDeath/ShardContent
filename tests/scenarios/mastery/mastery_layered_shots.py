"""Photographs the Mastery-from-80 windows and texts in the real ClassicUO client (docs/Mastery-Layered-Evidence.md).

    python -u mastery_layered_shots.py <serial-of-the-real-client-character> [name ...]

The character is a real ClassicUO client named Gwen (Start-PlayerClient.ps1); the staff work is done by the `admin` Navrey session through
the test-only commands [TestOnlyShow, [TestOnlyMasterySeed and [TestOnlySkillUse. The pictures go to work/mastery-layered/shots/<name>.png.

Names: mastery-empty, mastery-waiting, mastery-p1, mastery-p2, guide-mastery(-2), guide-training, guide-locks, guide-firsthour(-2),
guide-commands, guide-skillbank(-2), classes-overview, classes-standard, journal-entry, journal-guaranteed, journal-chance.
"""
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
SCRIPTS = os.path.join(WORKSPACE, ".claude", "scripts")
sys.path.insert(0, SCRIPTS)

from navrey_session import connect  # noqa: E402
from staff_command import staff_target  # noqa: E402

serial = sys.argv[1]
wanted = sys.argv[2:]
NAME = "Gwen"
OUT = os.path.join(WORKSPACE, "work", "mastery-layered", "shots")
os.makedirs(OUT, exist_ok=True)

adm = connect("admin")


def ps(script: str, *args: str, timeout: int = 180) -> str:
    out = subprocess.run(["pwsh", "-NoProfile", "-File", os.path.join(SCRIPTS, script), *args], capture_output=True, text=True, timeout=timeout)
    return (out.stdout + out.stderr).strip()


def say(command: str, wait: float = 1.0) -> None:
    adm.say(command)
    time.sleep(wait)


def target(command: str) -> None:
    say(f"[go {serial}", 1.5)
    staff_target(adm, command, serial)


def shot(name: str, wait: float = 2.2) -> str:
    time.sleep(wait)
    out = ps("Get-PlayerClientShot.ps1", "-Name", NAME, "-Label", f"mastery-{name}")
    path = out.splitlines()[-1].strip()
    shutil.copyfile(path, os.path.join(OUT, f"{name}.png"))
    print("shot", name, flush=True)
    return path


def close() -> None:
    ps("Send-PlayerClientInput.ps1", "-Name", NAME, "-X", "230", "-Y", "165", "-Right")
    time.sleep(0.6)


def scroll(notches: int, x: int = 640, y: int = 480) -> None:
    ps("Send-PlayerClientInput.ps1", "-Name", NAME, "-Scroll", str(notches), "-X", str(x), "-Y", str(y))
    time.sleep(0.8)


def show(window: str, arg: str = "") -> None:
    say(f"[TestOnlyShow {serial} {window} {arg}".rstrip(), 0.8)


def want(name: str) -> bool:
    return not wanted or name in wanted


def window(name: str, opener, *, scrolled: bool = False) -> None:
    if not want(name):
        return
    opener()
    shot(name)
    if scrolled and want(name + "-2"):
        scroll(-8)
        shot(name + "-2", 0.6)
    close()


# 1. The Mastery window with nothing in it, then with a skill waiting for its first use.
window("mastery-empty", lambda: show("mastery"))

if want("mastery-waiting"):
    target("[SetSkill Anatomy 80")
    window("mastery-waiting", lambda: show("mastery"))

# 2. The journal as a skill enters Mastery, claims, gains for certain, and (with the store empty) gains by chance.
if want("journal-entry") or want("journal-guaranteed") or want("journal-chance"):
    target("[SetSkill Tactics 80")
    say(f"[TestOnlyMasterySeed {serial} 1", 0.8)  # a clean state: nothing claimed
    say(f"[TestOnlySkillUse {serial} Tactics 2", 2.5)
    if want("journal-entry"):
        shot("journal-entry", 0.5)
    say(f"[TestOnlySkillUse {serial} Tactics 3", 2.0)
    if want("journal-guaranteed"):
        shot("journal-guaranteed", 0.5)

# 3. The window with a full set of skills (two pages).
if want("mastery-p1") or want("mastery-p2"):
    for skill, value in (("Anatomy", 83), ("Swords", 80), ("Tactics", 88.4), ("Magery", 80.4), ("Healing", 99.2), ("Parry", 92), ("Hiding", 94), ("Alchemy", 81.6)):
        target(f"[SetSkill {skill} {value}")
    say(f"[TestOnlyMasterySeed {serial} 7.5 Anatomy=20:1 Swords=14:0 Tactics=9:1 Magery=14:0", 1.0)
    say(f"[TestOnlyMasterySeed {serial} 7.5 + Healing=0:1 Parry=10:0 Hiding=3:1 Alchemy=10:1", 1.0)
    if want("mastery-p1"):
        show("mastery")
        shot("mastery-p1")
        ps("Send-PlayerClientInput.ps1", "-Name", NAME, "-X", "561", "-Y", "524")  # the pager's Next
        time.sleep(1.0)
        if want("mastery-p2"):
            shot("mastery-p2", 0.6)
        close()

# 4. The guide's pages.
window("guide-mastery", lambda: show("welcome", "mastery"), scrolled=True)
window("guide-training", lambda: show("welcome", "training"))
window("guide-locks", lambda: show("welcome", "locks"), scrolled=True)
window("guide-firsthour", lambda: show("welcome", "firsthour"), scrolled=True)
window("guide-commands", lambda: show("welcome", "commands"), scrolled=True)
window("guide-skillbank", lambda: show("welcome", "skillbank"), scrolled=True)

# 5. [SkillClasses: the overview and a class page.
window("classes-overview", lambda: show("skillclasses"))
if want("classes-standard"):
    show("skillclasses")
    time.sleep(1.5)
    ps("Send-PlayerClientInput.ps1", "-Name", NAME, "-X", "150", "-Y", "242")
    shot("classes-standard", 1.0)
    close()

print("done", flush=True)
