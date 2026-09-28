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
    age = time.time() * 1000 - client.state.get("updatedAtMs", 0)
    if not 0 <= age < 5000:
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
if not admin.wait(lambda: any("Alpha 3 enablement acknowledged: False" in line
                              for line in admin_log.read_text(errors="replace").splitlines()[status_start:]), timeout=5):
    raise RuntimeError("Alpha 3 acknowledgment status was not observed as false")
seed_start = len(admin_log.read_text(errors="replace").splitlines())
admin.call(f"say [StarterEconomyProbe crafttinkerscissors {player.state['charID']}", timeout=6)
deadline = time.monotonic() + 8
fixture = None
while time.monotonic() < deadline:
    fixture = next((line for line in reversed(admin_log.read_text(errors="replace").splitlines()[seed_start:])
                    if "Starter economy Tinkering scissors targets:" in line), None)
    if fixture:
        break
    time.sleep(0.1)
if not fixture:
    raise RuntimeError("Tinkering scissors fixture was not seeded")
serials = {key: "0x" + re.search(rf"{key}=(?:0x)?([0-9A-Fa-f]+)", fixture).group(1)
           for key in ("ingots", "tools", "cloth")}
if not player.open_backpack(wait=4):
    raise RuntimeError("ordinary backpack did not open")
if not player.wait(lambda: all(any(i.serial == serial for i in player.backpack)
                                for serial in serials.values()), timeout=5):
    raise RuntimeError(f"fixture items were not visible: {fixture}; {player.backpack}")
before = [(i.serial, i.name, i.amount) for i in player.backpack]
existing_scissors = {i.serial for i in player.backpack if i.name.lower() == "scissors"}
time.sleep(3)
if not player.use_on(serials["tools"], serials["ingots"], timeout=6):
    raise RuntimeError("bound Tinker Tools did not accept the ingot target")
selection_start = len(admin_log.read_text(errors="replace").splitlines())
player_start = len(player_log.read_text(errors="replace").splitlines())
admin.call(f"say [StarterEconomyProbe maketinkerscissors {player.state['charID']}", timeout=6)
if not player.wait(lambda: any(i.name.lower() == "scissors" and i.serial not in existing_scissors
                               for i in player.backpack), timeout=12):
    raise RuntimeError(f"stock Scissors output missing: {player.backpack}")
after_craft = [(i.serial, i.name, i.amount) for i in player.backpack]
if next((i.amount for i in player.backpack if i.serial == serials["ingots"]), 0) != 4:
    raise RuntimeError(f"StarterIronIngot was not consumed 6->4: {after_craft}")
scissors = next(i.serial for i in player.backpack
                if i.name.lower() == "scissors" and i.serial not in existing_scissors)
if not player.use_on(scissors, serials["cloth"], timeout=6):
    raise RuntimeError("ordinary Scissors did not accept the StarterCloth target")
deadline = time.monotonic() + 5
while time.monotonic() < deadline:
    if any("scissors cannot be used on that to produce anything" in line.lower()
           for line in player_log.read_text(errors="replace").splitlines()[player_start:]):
        break
    time.sleep(0.1)
else:
    raise RuntimeError("client did not report the bound Scissors refusal")
after_refusal = [(i.serial, i.name, i.amount) for i in player.backpack]
if next((i.amount for i in player.backpack if i.serial == serials["cloth"]), 0) != 5:
    raise RuntimeError(f"Scissors changed bound StarterCloth: {after_refusal}")
selection = next((line for line in admin_log.read_text(errors="replace").splitlines()[selection_start:]
                  if "Starter economy Tinkering scissors selection:" in line), "not reported")
print("CASE starter-ingot-to-scissors: PASS")
print(" fixture:", fixture)
print(" before:", before)
print(" after_craft:", after_craft)
print(" after_bound-cloth-refusal:", after_refusal)
print(" server:", selection)
