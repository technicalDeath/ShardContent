"""Starts the probe bot on a client build, asks it `meminfo` and `memcensus` (what the managed heap holds, by static root and by type) once it has
settled, again after a long walk, and stops it.

    python census_probe.py <path to cuo.dll> [--walk X Y] [--top 30] [KEY=VALUE env ...]
"""
import argparse
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path[:0] = [os.path.join(HERE, "..", "..", "..", "..", "Navrey", "cli"), os.path.join(HERE, "..", "..", "..", "..", ".claude", "scripts")]
import farm_launch as fl  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("cuo")
ap.add_argument("env", nargs="*")
ap.add_argument("--walk", nargs=2, type=int, default=None)
ap.add_argument("--top", type=int, default=30)
ap.add_argument("--settle", type=float, default=45)
a = ap.parse_args()
fl.LEAN_CUO = os.path.abspath(a.cuo)
r = fl.start("BotProbeA", 13, extra_env=dict(e.split("=", 1) for e in a.env))
print(r)
time.sleep(a.settle)
from navrey_session import connect  # noqa: E402
c = connect("BotProbeA")
try:
    for l in c.call("meminfo", timeout=8):
        print(l)
    for l in c.call(f"memcensus {a.top}", timeout=600):
        print(l)
    if a.walk:
        print("walking to", a.walk, c.goto(*a.walk).wait(timeout=240), (c.x, c.y))
        for l in c.call("meminfo", timeout=8):
            print(l)
        for l in c.call(f"memcensus {a.top}", timeout=600):
            print(l)
finally:
    if fl.is_client(r["pid"], "BotProbeA"):
        subprocess.run(["taskkill", "/PID", str(r["pid"]), "/F"], capture_output=True)
