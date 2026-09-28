from pathlib import Path
import re
import sys
import time

root = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(root / "Navrey" / "cli"))
from uo import Client


def open_client(role, require_game=True):
    d = (root / "work" / "alpha3-starter-economy-clients" / role).resolve()
    c = Client(state_file=str(d / "state2.json"), world_file=str(d / "world2.json"),
               cmd_file=str(d / "cmd2.txt"), log_file=str(d / "client2.log"))
    c.require_live()
    if time.time() * 1000 - c.state.get("updatedAtMs", 0) >= 5000 or (require_game and not c.state.get("inGame")):
        raise RuntimeError(f"{role} does not have a fresh usable state")
    return c, d


admin, ad = open_client("admin")
player, pd = open_client("tinker", False)
if not player.state.get("inGame"):
    player.call("createcharacter StarterTinker 0 29 30", timeout=6)
    if not player.wait(lambda: player.state.get("inGame"), timeout=12):
        raise RuntimeError("StarterTinker did not enter the world")
al, pl = ad / "client2.log", pd / "client2.log"
player.open_backpack(wait=4)

seed_start = len(al.read_text(errors="replace").splitlines())
admin.call(f"say [StarterEconomyProbe craftbowyer {player.state['charID']}", timeout=6)
deadline = time.monotonic() + 8
fixture = None
while time.monotonic() < deadline:
    fixture = next((line for line in reversed(al.read_text(errors="replace").splitlines()[seed_start:])
                    if "Starter economy bowyer targets:" in line), None)
    if fixture:
        break
    time.sleep(0.1)
if not fixture:
    raise RuntimeError("Bowyer inputs were not seeded")
serials = {key: "0x" + re.search(rf"{key}=(?:0x)?([0-9A-Fa-f]+)", fixture).group(1)
           for key in ("boards", "feathers", "tools")}
if not player.wait(lambda: all(any(i.serial == s and i.amount == 1 for i in player.backpack)
                                for s in serials.values()), timeout=5):
    raise RuntimeError(f"Bowyer fixture missing: {fixture}; {player.backpack}")
before = [(i.serial, i.name, i.amount) for i in player.backpack]
time.sleep(3)
if not player.use_on(serials["tools"], serials["boards"], timeout=6):
    raise RuntimeError("Fletcher Tools did not accept the bound StarterBoard target")
shaft_start = len(pl.read_text(errors="replace").splitlines())
admin_start = len(al.read_text(errors="replace").splitlines())
admin.call(f"say [StarterEconomyProbe makebowyer {player.state['charID']}", timeout=6)
if not player.wait(lambda: any(i.name.lower() == "shaft" for i in player.backpack), timeout=12):
    raise RuntimeError(f"bound StarterBoard did not make a stock Shaft: {pl.read_text(errors='replace').splitlines()[-20:]}")
board_left = next((i.amount for i in player.backpack if i.serial == serials["boards"]), 0)
if board_left != 0:
    raise RuntimeError(f"StarterBoard amount after Shaft was {board_left}; {player.backpack}")
shaft_serial = next(i.serial for i in player.backpack if i.name.lower() == "shaft")
print("CASE bowyer-wood: PASS")
print(" fixture:", fixture)
print(" before:", before)
print(" after_shaft:", [(i.serial, i.name, i.amount) for i in player.backpack])
print(" server:", next((line for line in al.read_text(errors="replace").splitlines()[admin_start:]
                       if "bowyer selection:" in line), "not reported"))

time.sleep(3)
if not player.use_on(serials["tools"], serials["feathers"], timeout=6):
    raise RuntimeError("Fletcher Tools did not accept the bound StarterFeather target")
arrow_player_start = len(pl.read_text(errors="replace").splitlines())
arrow_admin_start = len(al.read_text(errors="replace").splitlines())
arrows_before = sum(i.amount for i in player.backpack if "arrow" in i.name.lower() and "fletching" not in i.name.lower())
admin.call(f"say [StarterEconomyProbe makearrow {player.state['charID']}", timeout=6)
deadline = time.monotonic() + 15
responded = False
while time.monotonic() < deadline:
    lines = pl.read_text(errors="replace").splitlines()[arrow_player_start:]
    if not responded and any("Do you wish to place your maker's mark" in line for line in lines):
        player.call("gumpresponse 1", timeout=5)
        responded = True
    arrows_now = sum(i.amount for i in player.backpack if "arrow" in i.name.lower() and "fletching" not in i.name.lower())
    if arrows_now > arrows_before:
        break
    time.sleep(0.1)
after = [(i.serial, i.name, i.amount) for i in player.backpack]
if sum(i.amount for i in player.backpack if "arrow" in i.name.lower() and "fletching" not in i.name.lower()) <= arrows_before:
    raise RuntimeError(f"StarterFeather did not produce ordinary Arrow: {after}")
shaft_left = next((i.amount for i in player.backpack if i.serial == shaft_serial), 0)
feather_left = next((i.amount for i in player.backpack if i.serial == serials["feathers"]), 0)
if shaft_left != 0 or feather_left != 0:
    raise RuntimeError(f"wrong Arrow inputs: shaft={shaft_left}, feather={feather_left}; {after}")
print("CASE bowyer-feather: PASS")
print(" after_arrow:", after)
print(" server:", next((line for line in al.read_text(errors="replace").splitlines()[arrow_admin_start:]
                       if "bowyer selection:" in line), "not reported"))
