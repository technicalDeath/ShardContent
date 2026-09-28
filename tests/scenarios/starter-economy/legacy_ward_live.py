"""Live old-world Ward population and ordinary-client transfer rehearsal."""
from pathlib import Path
import re
import sys
import time

root = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(root / "Navrey" / "cli"))
from uo import Client


def open_client(role):
    d = (root / "work" / "alpha3-starter-economy-clients" / role).resolve()
    c = Client(state_file=str(d / "state2.json"), world_file=str(d / "world2.json"),
               cmd_file=str(d / "cmd2.txt"), log_file=str(d / "client2.log"))
    c.require_live()
    if not c.wait(lambda: c.state.get("updatedAtMs", 0) and
                  0 <= time.time() * 1000 - c.state["updatedAtMs"] < 5000, timeout=8):
        raise RuntimeError(f"{role} has no fresh game snapshot")
    return c, d


def wait_line(log, start, marker, timeout=8):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        rows = log.read_text(errors="replace").splitlines()[start:]
        line = next((x for x in reversed(rows) if marker in x), None)
        if line:
            return line
        time.sleep(.1)
    raise RuntimeError(f"missing server outcome: {marker}")


admin, ad = open_client("admin")
owner, od = open_client("tinker")
buyer, bd = open_client("player2")
for c, name in ((owner, "StarterTinker"), (buyer, "StarterBuyer")):
    if not c.state.get("inGame"):
        c.call(f"createcharacter {name} 0 29 30", timeout=6)
        if not c.wait(lambda: c.state.get("inGame") and c.state.get("charName") == name, timeout=15):
            raise RuntimeError(f"{name} did not enter the world")
    if c.state.get("charName") != name:
        raise RuntimeError(f"wrong ordinary client role: {c.state.get('charName')}")
if owner.state["charID"] == buyer.state["charID"]:
    raise RuntimeError("paired clients must use distinct characters/accounts")

al = ad / "client2.log"
start = len(al.read_text(errors="replace").splitlines())
admin.call("say [StarterEconomyProbe wardscan", timeout=6)
baseline = wait_line(al, start, "Backpack Ward population scan:")
start = len(al.read_text(errors="replace").splitlines())
admin.call(f"say [StarterEconomyProbe legacyward {owner.state['charID']}", timeout=6)
fixture = wait_line(al, start, "Starter economy legacy Ward fixture:")
ward = "0x" + re.search(r"serial=(?:0x)?([0-9A-Fa-f]+)", fixture).group(1)
if "starterIssued=False" not in fixture or "nontransferable=False" not in fixture:
    raise RuntimeError(f"legacy Ward fixture was not ordinary/unmarked: {fixture}")
if not owner.open_backpack(wait=4):
    raise RuntimeError("owner backpack did not open")
if not owner.wait(lambda: any(i.serial == ward for i in owner.backpack), timeout=5):
    raise RuntimeError("unmarked Ward missing from owner backpack")

for client in (owner, buyer):
    start = len(al.read_text(errors="replace").splitlines())
    admin.call(f"say [StarterEconomyProbe place {client.state['charID']}", timeout=6)
    wait_line(al, start, "paired client placed")
time.sleep(1.5)
owner.drop(ward, buyer.state["charID"])
end = time.monotonic() + 10
while time.monotonic() < end:
    trade = owner.call("trades", timeout=5)
    if any("[TRADE]" in x for x in trade):
        break
    time.sleep(.1)
else:
    raise RuntimeError("unmarked Ward did not open ordinary secure trade")
owner.call("accepttrade", timeout=5)
time.sleep(.2)
buyer.call("accepttrade", timeout=5)
if not buyer.wait(lambda: any(i.serial == ward for i in buyer.backpack), timeout=10):
    raise RuntimeError("unmarked Ward did not arrive on buyer")
print("CASE legacy unmarked BackpackWard ordinary secure trade: PASS")

start = len(al.read_text(errors="replace").splitlines())
admin.call(f"say [StarterEconomyProbe vendor {buyer.state['charID']}", timeout=6)
vendor_line = wait_line(al, start, "Starter economy player vendor:")
vendor = "0x" + re.search(r"vendor=(?:0x)?([0-9A-Fa-f]+)", vendor_line).group(1)
time.sleep(1.5)
blog = bd / "client2.log"
prompt_start = len(blog.read_text(errors="replace").splitlines())
buyer.drop(ward, vendor)
wait_line(blog, prompt_start, "Type in a price and description", timeout=8)
buyer.call("prompt 100 Legacy Backpack Ward", timeout=5)
if not buyer.wait(lambda: not any(i.serial == ward for i in buyer.backpack), timeout=8):
    raise RuntimeError("player vendor did not accept unmarked Ward")
start = len(al.read_text(errors="replace").splitlines())
admin.call(f"say [StarterEconomyProbe item {ward}", timeout=6)
state = wait_line(al, start, "Starter economy output verify:")
if ("type=BackpackWard" not in state or "nontransferable=False" not in state or
        "vendorStock=True" not in state or "root=PlayerVendor" not in state):
    raise RuntimeError(f"server did not confirm ordinary unmarked Ward stock: {state}")
print("CASE legacy unmarked BackpackWard player-vendor intake: PASS")
print("baseline:", baseline)
print("fixture:", fixture)
print("trade:", trade)
print("server verification:", state)
