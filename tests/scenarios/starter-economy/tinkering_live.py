from pathlib import Path
import re
import sys
import time

root = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(root / "Navrey" / "cli"))
from uo import Client


def open_client(role):
    directory = (root / "work" / "alpha3-starter-economy-clients" / role).resolve()
    client = Client(
        state_file=str(directory / "state2.json"),
        world_file=str(directory / "world2.json"),
        cmd_file=str(directory / "cmd2.txt"),
        log_file=str(directory / "client2.log"),
    )
    client.require_live()
    if time.time() * 1000 - client.state.get("updatedAtMs", 0) >= 5000:
        raise RuntimeError(f"{role} state is stale")
    return client, directory


admin, admin_dir = open_client("admin")
player, player_dir = open_client("tinker")
if not player.state.get("inGame"):
    player.call("createcharacter StarterTinker 0 29 30", timeout=6)
    if not player.wait(lambda: player.state.get("inGame"), timeout=12):
        raise RuntimeError("StarterTinker did not enter the world")
if player.state.get("charName") != "StarterTinker":
    raise RuntimeError("ordinary client is not StarterTinker")

admin_log = admin_dir / "client2.log"
player_log = player_dir / "client2.log"
status_start = len(admin_log.read_text(errors="replace").splitlines())
admin.call("say [ShardRulesStatus", timeout=6)
time.sleep(0.3)
status_lines = admin_log.read_text(errors="replace").splitlines()[status_start:]
if not any("Alpha 3" in line for line in status_lines):
    raise RuntimeError(f"effective rules status was not observed: {status_lines}")

seed_start = len(admin_log.read_text(errors="replace").splitlines())
admin.call(f"say [StarterEconomyProbe crafttinker {player.state['charID']}", timeout=6)
deadline = time.monotonic() + 8
fixture = None
while time.monotonic() < deadline:
    lines = admin_log.read_text(errors="replace").splitlines()
    fixture = next((line for line in reversed(lines[seed_start:]) if "Starter economy tinkering targets:" in line), None)
    if fixture:
        break
    time.sleep(0.1)
if not fixture:
    raise RuntimeError("server did not report Tinkering fixtures")
ingots = "0x" + re.search(r"ingots=(?:0x)?([0-9A-Fa-f]+)", fixture).group(1)
tools = "0x" + re.search(r"tools=(?:0x)?([0-9A-Fa-f]+)", fixture).group(1)
if not player.open_backpack(wait=4):
    raise RuntimeError("ordinary backpack did not open")
if not player.wait(lambda: any(i.serial == ingots and i.amount == 100 for i in player.backpack), timeout=5):
    raise RuntimeError("StarterIronIngot x100 did not arrive")
before = [(i.serial, i.name, i.amount) for i in player.backpack]
time.sleep(3)  # Let the server's character-creation/stat-change action delay expire.
if not player.use_on(tools, ingots, timeout=6):
    raise RuntimeError("bound Tinker Tools did not request and accept the StarterIronIngot target")
player_start = len(player_log.read_text(errors="replace").splitlines())
recipe_start = len(admin_log.read_text(errors="replace").splitlines())
admin.call(f"say [StarterEconomyProbe maketinker {player.state['charID']}", timeout=6)
deadline = time.monotonic() + 12
while time.monotonic() < deadline:
    lines = player_log.read_text(errors="replace").splitlines()
    if any("Do you wish to place your maker's mark" in line for line in lines[player_start:]):
        player.call("gumpresponse 1", timeout=5)
        break
    if any("You create" in line for line in lines[player_start:]):
        break
    time.sleep(0.1)
if not player.wait(lambda: any("gears" in i.name.lower() for i in player.backpack), timeout=8):
    raise RuntimeError("stock Gears output did not appear")
after = [(i.serial, i.name, i.amount) for i in player.backpack]
ingots_after = next((i.amount for i in player.backpack if i.serial == ingots), None)
if ingots_after != 98:
    raise RuntimeError(f"StarterIronIngot amount was {ingots_after}, expected 98; inventory={after}")
selection = next((line for line in admin_log.read_text(errors="replace").splitlines()[recipe_start:] if "Starter economy tinkering selection:" in line), "not reported")
print("effective rules:", " | ".join(status_lines))
print("fixture:", fixture)
print("before:", before)
print("after:", after)
print("server recipe:", selection)
print("tinkering bound-input result=PASS; StarterIronIngot 100->98 and ordinary stock Gears received")
