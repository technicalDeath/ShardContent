"""Walks the probe bot to each proposed spawner site and prints where it ended up (with z) and whether the walk arrived, so a new spawner's
location is a reachable, walkable tile with its real height.

    python spawn_site_probe.py <cuo.dll> x,y [x,y ...]
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
sites = [tuple(int(v) for v in a.split(",")) for a in sys.argv[2:]]
r = fl.start("BotProbeA", 13, extra_env={"NAVREY_LEAN": "1", "FNA3D_FORCE_DRIVER": "D3D11", "NAVREY_RUN": "always"})
time.sleep(30)
from navrey_session import connect  # noqa: E402
c = connect("BotProbeA")
try:
    for x, y in sites:
        res = c.goto(x, y).wait(timeout=300)
        hostile = [f"{m.name}@{m.distance}" for m in c.mobiles(within=14) if m.notoriety in ("Gray", "Criminal", "Enemy", "Murderer")][:4]
        print(f"site {x},{y}: {res} at {c.x},{c.y},{c.z} hp {c.hp}/{c.max_hp} ghost {c.ghost} near: {hostile}", flush=True)
        if c.ghost:
            break
finally:
    if fl.is_client(r["pid"], "BotProbeA"):
        subprocess.run(["taskkill", "/PID", str(r["pid"]), "/F"], capture_output=True)
