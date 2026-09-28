from pathlib import Path
import re
import sys
import time

root = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(root / "Navrey" / "cli"))
from uo import Client


def open_client(role):
    directory = (root / "work" / "alpha3-starter-economy-clients" / role).resolve()
    value = Client(state_file=str(directory / "state2.json"), world_file=str(directory / "world2.json"),
                   cmd_file=str(directory / "cmd2.txt"), log_file=str(directory / "client2.log"))
    value.require_live()
    if not value.state.get("inGame") or time.time() * 1000 - value.state.get("updatedAtMs", 0) >= 5000:
        raise RuntimeError(f"{role} has no fresh in-game state")
    return value, directory


admin, ad = open_client("admin")
player, pd = open_client("tinker")
al, pl = ad / "client2.log", pd / "client2.log"
player.open_backpack(wait=4)
start = len(al.read_text(errors="replace").splitlines())
admin.call(f"say [StarterEconomyProbe craftcook {player.state['charID']}", timeout=6)
deadline = time.monotonic() + 8
fixture = None
while time.monotonic() < deadline:
    lines = al.read_text(errors="replace").splitlines()[start:]
    fixture = next((line for line in reversed(lines) if "Starter economy cooking targets:" in line), None)
    if fixture:
        break
    time.sleep(0.1)
if not fixture:
    raise RuntimeError("cooking fixture not reported")
serials = {key: "0x" + re.search(rf"{key}=(?:0x)?([0-9A-Fa-f]+)", fixture).group(1)
           for key in ("fish", "kindling", "skillet")}
before = [(i.serial, i.name, i.amount) for i in player.backpack]
if not player.wait(lambda: all(any(i.serial == s for i in player.backpack) for s in serials.values()), timeout=5):
    raise RuntimeError(f"cooking inputs missing: {fixture}; {player.backpack}")
before_fish_steak = sum(i.amount for i in player.backpack if i.name.lower() == "fish steak")
time.sleep(3)
player.use(serials["skillet"])
time.sleep(0.5)
make_start = len(al.read_text(errors="replace").splitlines())
admin.call(f"say [StarterEconomyProbe makecook {player.state['charID']}", timeout=6)
if not player.wait(lambda: sum(i.amount for i in player.backpack if i.name.lower() == "fish steak") > before_fish_steak, timeout=12):
    raise RuntimeError(f"stock FishSteak output missing; player log={pl.read_text(errors='replace').splitlines()[-20:]}")
after = [(i.serial, i.name, i.amount) for i in player.backpack]
fish_after = next((i.amount for i in player.backpack if i.serial == serials['fish']), 0)
kindling_after = next((i.amount for i in player.backpack if i.serial == serials['kindling']), 0)
if fish_after != 0 or kindling_after != 1:
    raise RuntimeError(f"wrong Cooking input deltas: fish={fish_after}, kindling={kindling_after}; {after}")
selection = next((line for line in al.read_text(errors="replace").splitlines()[make_start:] if "Starter economy cooking selection:" in line), "not reported")
print("CASE craftcook/makecook: PASS")
print(" fixture:", fixture)
print(" before:", before)
print(" after:", after)
print(" server:", selection)
