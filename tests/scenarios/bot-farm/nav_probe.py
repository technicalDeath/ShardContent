"""Compares path planning between client builds: starts the probe bot on a build, walks it to each start tile, and asks `path` (plan only) to each
destination, printing the result and how many nodes the search used. A build that plans "nopath" from a tile another build plans out of is broken.

    python nav_probe.py <cuo.dll> [<cuo.dll> ...]
"""
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path[:0] = [os.path.join(HERE, "..", "..", "..", "..", "Navrey", "cli"), os.path.join(HERE, "..", "..", "..", "..", ".claude", "scripts")]
import farm_launch as fl  # noqa: E402

CASES = [((1472, 1608), [(1470, 1579), (1427, 1652)]), ((1457, 1526), [(1427, 1652), (1424, 1558), (1418, 1550)])]

for cuo in sys.argv[1:]:
    fl.LEAN_CUO = os.path.abspath(cuo)
    r = fl.start("BotProbeA", 13, extra_env={"NAVREY_LEAN": "1", "FNA3D_FORCE_DRIVER": "D3D11"})
    print("==", cuo, r.get("ok"), flush=True)
    time.sleep(30)
    from navrey_session import connect  # noqa: E402
    c = connect("BotProbeA")
    try:
        for start, dests in CASES:
            res = c.goto(*start).wait(timeout=240)
            print(f"  walk to {start}: {res} at {c.x},{c.y}", flush=True)
            for d in dests:
                lines = c.call(f"path {d[0]} {d[1]}", timeout=60)
                print(f"    path {d}: " + " | ".join(l.strip() for l in lines if l.strip())[:300], flush=True)
    finally:
        if fl.is_client(r["pid"], "BotProbeA"):
            subprocess.run(["taskkill", "/PID", str(r["pid"]), "/F"], capture_output=True)
        time.sleep(3)
