"""Stage the guard-call and [Intent]-tag screenshots: Pru (Intent on) and Bea stand next to each other in Britain. Bea's session is then
left for the real client."""
import re
import sys
import time

sys.argv = [sys.argv[0], "NONE"]  # no cases: import the helpers only
import os
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "execute_countdown_live.py"), encoding="utf-8").read().split("CASES = [")[0])

adm.say("[go 1434 1699")
time.sleep(3)
s = adm.state
x, y, z = s["charPosX"], s["charPosY"], s["charPosZ"]
print("Britain spot", x, y, z, flush=True)

reset("Pru", "Bea")
place("Pru", x, y, z)
place("Bea", x + 1, y, z)
time.sleep(2)

m = mark("admin")
adm.say(f"[TestOnlyState {serial('Pru')} describe")
time.sleep(1.5)
text = " ".join(since("admin", m))
if "Criminal Intent" not in text:
    C["Pru"].say("[Intent")
    time.sleep(2)
    m = mark("admin")
    adm.say(f"[TestOnlyState {serial('Pru')} describe")
    time.sleep(1.5)
    text = " ".join(since("admin", m))
print("Pru Intent on:", "Criminal Intent" in text, flush=True)
print("Bea at", C["Bea"].state["charPosX"], C["Bea"].state["charPosY"], flush=True)
