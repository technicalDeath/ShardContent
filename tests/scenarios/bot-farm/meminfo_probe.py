"""Starts the probe bot on a given client build, waits, asks it `meminfo` (managed heap against native memory), and stops it."""
import os, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path[:0] = [os.path.join(HERE, "..", "..", "..", "..", "Navrey", "cli"), os.path.join(HERE, "..", "..", "..", "..", ".claude", "scripts")]
import farm_launch as fl
fl.LEAN_CUO = os.path.abspath(sys.argv[1])
env = dict(e.split("=", 1) for e in sys.argv[2:])
r = fl.start("BotProbeA", 13, extra_env=env)
print(r)
time.sleep(45)
from navrey_session import connect
c = connect("BotProbeA")
for l in c.call("meminfo", timeout=8): print(l)
if fl.is_client(r["pid"], "BotProbeA"):
    subprocess.run(["taskkill", "/PID", str(r["pid"]), "/F"], capture_output=True)
