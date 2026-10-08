"""Photographs every restyled shard window in the real client, for the before and after pictures of the gump style pass (2026-10-07).

    python -u restyle_shots.py <label> <serial-of-the-real-client-character> [stage] [window ...]

  <label>   "before" or "after": the pictures go to work/gump-style-pass/restyle-<label>/<window>.png
  stage     (word) first puts the character in the state the windows need: skills in Mastery, a seeded Skill Bank, a Mastery cycle
  window    which windows to photograph (default: all)

The character is a real ClassicUO client (Start-PlayerClient.ps1); the staff work is done by the `admin` Navrey session through the test-only
commands [TestOnlyShow, [TestOnlySkillBankSeed and [TestOnlyMasterySeed (see TestOnlyProbe.cs, MasteryProbe.cs).
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

label = sys.argv[1]
serial = sys.argv[2]
rest = sys.argv[3:]
stage = "stage" in rest
wanted = [w for w in rest if w != "stage"]
NAME = "Gwen"
OUT = os.path.join(WORKSPACE, "work", "gump-style-pass", f"restyle-{label}")
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
    out = ps("Get-PlayerClientShot.ps1", "-Name", NAME, "-Label", f"{label}-{name}")
    path = out.splitlines()[-1].strip()
    shutil.copyfile(path, os.path.join(OUT, f"{name}.png"))
    print("shot", name, flush=True)
    return path


def close() -> None:
    ps("Send-PlayerClientInput.ps1", "-Name", NAME, "-X", "230", "-Y", "165", "-Right")
    time.sleep(0.6)


def click(x: int, y: int) -> None:
    ps("Send-PlayerClientInput.ps1", "-Name", NAME, "-X", str(x), "-Y", str(y))
    time.sleep(1.2)


def show(window: str, arg: str = "") -> None:
    say(f"[TestOnlyShow {serial} {window} {arg}".rstrip(), 0.8)


def window(name: str, opener, *, after_close: bool = True, wait: float = 2.2) -> None:
    if wanted and name not in wanted:
        return
    opener()
    shot(name, wait)
    if after_close:
        close()


if stage:
    print("staging", flush=True)
    for skill, value in (("Anatomy", 93), ("Swords", 91), ("Tactics", 96), ("Magery", 90), ("Healing", 99), ("Parry", 92), ("Hiding", 94)):
        target(f"[SetSkill {skill} {value}")
    say(f"[TestOnlyMasterySeed {serial} 7.5 Anatomy=20:1 Swords=6:0 Tactics=10:1 Magery=6:0", 1.0)
    say(f"[TestOnlyMasterySeed {serial} 7.5 + Healing=0:1 Parry=10:0 Hiding=3:1", 1.0)
    say(f"[TestOnlySkillBankSeed {serial} Swords=62 Anatomy=40:down Tactics=22 Magery=15:down Healing=8", 1.0)
    say(f"[TestOnlySkillBankSeed {serial} + Parry=30 Hiding=12:down Wrestling=44", 1.0)

window("welcome", lambda: show("welcome"))
window("welcome-fighting", lambda: show("welcome", "fighting"))
window("welcome-commands", lambda: show("welcome", "commands"))
window("skillclasses", lambda: show("skillclasses"))
window("intent-off", lambda: show("intent"))
if not wanted or "intent-on" in wanted:
    ps("Send-PlayerClientInput.ps1", "-Name", NAME, "-Text", "[Intent")
    time.sleep(1.5)
    window("intent-on", lambda: show("intent"))
    ps("Send-PlayerClientInput.ps1", "-Name", NAME, "-Text", "[Intent")
    time.sleep(1.5)
window("travelwarning", lambda: show("travelwarning"))
window("ward", lambda: show("ward"))
window("skillbank", lambda: show("skillbank", "Anatomy is now Locked: its banked points are safe."))
window("discard", lambda: show("discard", "1"))
if not wanted or "discard" in wanted:
    close()  # closing the Discard dialog re-opens the Skill Bank behind it by design: close that too
window("mastery", lambda: show("mastery"))
window("camplist", lambda: show("camplist"))
window("campconfirm", lambda: show("campconfirm"))
window("campconfirmhot", lambda: show("campconfirmhot"))
window("hotzone", lambda: show("hotzone"))
print("done", flush=True)
