"""Photographs a grid of campfires in candidate blue hues, by day and by night, in the real client (blue-fire colour spike, 2026-10-08).

    python -u sheet.py <serial-of-the-real-client-character> [hue ...]

Position 1 (top left) of the grid is the unhued fire, for comparison; rows run left to right, four to a row.
"""
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", ".."))
SCRIPTS = os.path.join(WORKSPACE, ".claude", "scripts")
sys.path.insert(0, SCRIPTS)

from navrey_session import connect  # noqa: E402
from staff_command import staff_target  # noqa: E402

serial = sys.argv[1]
hues = [int(h) for h in sys.argv[2:]] or [0, 2746, 1927, 1928, 1266, 1265, 3, 93, 98, 2790, 2796, 1366, 1282, 1264, 1195, 2747]
OUT = os.path.join(WORKSPACE, "work", "blue-fire", "shots")
os.makedirs(OUT, exist_ok=True)
adm = connect("admin")


def ps(script, *args, timeout=180):
    out = subprocess.run(["pwsh", "-NoProfile", "-File", os.path.join(SCRIPTS, script), *args], capture_output=True, text=True, timeout=timeout)
    return (out.stdout + out.stderr).strip()


def say(command, wait=1.0):
    adm.say(command)
    time.sleep(wait)


def shot(name, wait=15.0):
    time.sleep(wait)
    path = ps("Get-PlayerClientShot.ps1", "-Name", "Gwen", "-Label", name).splitlines()[-1].strip()
    shutil.copyfile(path, os.path.join(OUT, f"{name}.png"))
    print("shot", name, flush=True)


def light(level):
    say(f"[GlobalLight {level}", 1.5)


say(f"[TestOnlyFires {serial} flat", 3.0)
ps("Send-PlayerClientInput.ps1", "-Name", "Gwen", "-X", "230", "-Y", "165", "-Right")  # closes the paperdoll
time.sleep(0.6)

for name, level in (("sheet-day", 0), ("sheet-night", 12)):
    light(level)
    say(f"[TestOnlyFires {serial} step 2 " + " ".join(str(h) for h in hues), 1.0)
    shot(name)
    say(f"[TestOnlyFires {serial} clear", 0.8)

light(0)
print("done", flush=True)
