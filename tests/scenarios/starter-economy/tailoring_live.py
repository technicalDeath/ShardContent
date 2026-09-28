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
    if not client.state.get("inGame") or time.time() * 1000 - client.state.get("updatedAtMs", 0) >= 5000:
        raise RuntimeError(f"{role} has no fresh in-game state")
    return client, directory


admin, admin_dir = open_client("admin")
player, player_dir = open_client("player1")
if player.state.get("charName") != "StarterTailor":
    raise RuntimeError("ordinary client is not the disposable StarterTailor character")
admin_log = admin_dir / "client2.log"
player_log = player_dir / "client2.log"
start = len(admin_log.read_text(errors="replace").splitlines())
admin.call(f"say [StarterEconomyProbe craftcloth {player.state['charID']}", timeout=6)
deadline = time.monotonic() + 8
fixture = None
while time.monotonic() < deadline:
    lines = admin_log.read_text(errors="replace").splitlines()
    fixture = next((line for line in reversed(lines[start:]) if "Starter economy tailoring targets:" in line), None)
    if fixture:
        break
    time.sleep(0.1)
if not fixture:
    raise RuntimeError("server did not report tailoring fixtures")
cloth = "0x" + re.search(r"cloth=(?:0x)?([0-9A-Fa-f]+)", fixture).group(1)
kit = "0x" + re.search(r"kit=(?:0x)?([0-9A-Fa-f]+)", fixture).group(1)
if not player.open_backpack(wait=4):
    raise RuntimeError("ordinary client backpack did not open")
if not player.wait(lambda: any(i.serial == cloth and i.amount == 100 for i in player.backpack), timeout=5):
    raise RuntimeError("StarterCloth x100 did not arrive in player backpack")
before = [(i.serial, i.name, i.amount) for i in player.backpack]
if not player.use_on(kit, cloth, timeout=6):
    raise RuntimeError("bound Sewing Kit did not request and accept the StarterCloth target")
player_start = len(player_log.read_text(errors="replace").splitlines())
admin_start = len(admin_log.read_text(errors="replace").splitlines())
admin.call(f"say [StarterEconomyProbe makecloth {player.state['charID']}", timeout=6)
deadline = time.monotonic() + 12
gump = False
while time.monotonic() < deadline:
    lines = player_log.read_text(errors="replace").splitlines()
    if any("Do you wish to place your maker's mark" in line for line in lines[player_start:]):
        player.call("gumpresponse 1", timeout=5)
        gump = True
        break
    if any("You create an exceptional quality item." in line for line in lines[player_start:]):
        break
    time.sleep(0.1)
if gump and not player.wait(
    lambda: any("shirt" in i.name.lower() for i in player.backpack), timeout=5
):
    raise RuntimeError("maker's mark response did not produce the stock Shirt")
after = [(i.serial, i.name, i.amount) for i in player.backpack]
cloth_after = next((i.amount for i in player.backpack if i.serial == cloth), None)
if cloth_after != 92:
    raise RuntimeError(f"bound StarterCloth amount was {cloth_after}, expected 92; inventory={after}")
new_items = [entry for entry in after if entry[0] not in {item[0] for item in before}]
if not any("shirt" in name.lower() for _, name, _ in new_items):
    raise RuntimeError(f"stock Shirt output missing; new items={new_items}")
lines = admin_log.read_text(errors="replace").splitlines()[admin_start:]
print("fixture:", fixture)
print("before:", before)
print("after:", after)
print("server recipe:", next((line for line in lines if "Starter economy tailoring selection:" in line), "not reported"))
print("tailoring bound-input result=PASS; StarterCloth 100->92 and ordinary stock Shirt received")
