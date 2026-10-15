"""Checks a client build's run mode: starts the probe bot with NAVREY_RUN=auto, walks it a long way, and samples stamina and whether it is running
every few seconds (it should run while stamina is at least half and walk below), then stops it.

    python runmode_probe.py <cuo.dll> [X Y]
"""
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path[:0] = [os.path.join(HERE, "..", "..", "..", "..", "Navrey", "cli"), os.path.join(HERE, "..", "..", "..", "..", ".claude", "scripts")]
import farm_launch as fl  # noqa: E402

fl.LEAN_CUO = os.path.abspath(sys.argv[1])
tx, ty = (int(sys.argv[2]), int(sys.argv[3])) if len(sys.argv) >= 4 else (1600, 1700)
r = fl.start("BotProbeA", 13, extra_env={"NAVREY_LEAN": "1", "FNA3D_FORCE_DRIVER": "D3D11", "NAVREY_RUN": "auto"})
print(r)
time.sleep(30)
from navrey_session import connect  # noqa: E402
c = connect("BotProbeA")
try:
    print(c.call("runmode", timeout=6))
    for target in ((tx, ty), (1470, 1620)):
        w = c.goto(*target)
        end = time.time() + 120
        while time.time() < end and c.nav.active:
            time.sleep(4)
            print(f"  at {c.x},{c.y} stamina {c.stamina}/{c.state.get('maxStam')} running {c.state.get('isRunning')}")
        print("walk", w.wait(timeout=5), "at", c.x, c.y)
finally:
    if fl.is_client(r["pid"], "BotProbeA"):
        subprocess.run(["taskkill", "/PID", str(r["pid"]), "/F"], capture_output=True)
