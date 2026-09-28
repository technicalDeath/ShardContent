from pathlib import Path
import re
import sys
import time

root = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(root / "Navrey" / "cli"))
from uo import Client


def open_client(role):
    directory = (root / "work" / "alpha3-starter-economy-clients" / role).resolve()
    client = Client(state_file=str(directory / "state2.json"),
                    world_file=str(directory / "world2.json"),
                    cmd_file=str(directory / "cmd2.txt"),
                    log_file=str(directory / "client2.log"))
    client.require_live()
    if time.time() * 1000 - client.state.get("updatedAtMs", 0) >= 5000:
        raise RuntimeError(f"{role} state is stale")
    return client, directory


admin, ad = open_client("admin")
player, pd = open_client("tinker")
if not player.state.get("inGame"):
    player.call("createcharacter StarterTinker 0 29 30", timeout=6)
    if not player.wait(lambda: player.state.get("inGame"), timeout=12):
        raise RuntimeError("StarterTinker did not enter the world")
if player.state.get("charName") != "StarterTinker":
    raise RuntimeError("ordinary buyer/seller is not StarterTinker")

admin_log = ad / "client2.log"
player_log = pd / "client2.log"
status_start = len(admin_log.read_text(errors="replace").splitlines())
admin.call("say [ShardRulesStatus", timeout=6)
if not admin.wait(lambda: any("Alpha 3 enablement acknowledged: False" in line
                              for line in admin_log.read_text(errors="replace").splitlines()[status_start:]), timeout=5):
    raise RuntimeError("Alpha 3 acknowledgment was not reported false")

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
    raise RuntimeError("bound craft fixture missing")
ingots = "0x" + re.search(r"ingots=(?:0x)?([0-9A-Fa-f]+)", fixture).group(1)
tools = "0x" + re.search(r"tools=(?:0x)?([0-9A-Fa-f]+)", fixture).group(1)
if not player.open_backpack(wait=4):
    raise RuntimeError("ordinary backpack did not open")
if not player.wait(lambda: any(i.serial == ingots and i.amount == 6 for i in player.backpack), timeout=5):
    raise RuntimeError("StarterIronIngot x6 missing")

npc_start = len(admin_log.read_text(errors="replace").splitlines())
admin.call(f"say [StarterEconomyProbe tinkernpc {player.state['charID']}", timeout=6)
deadline = time.monotonic() + 6
npc_line = None
while time.monotonic() < deadline:
    npc_line = next((line for line in reversed(admin_log.read_text(errors="replace").splitlines()[npc_start:])
                     if "Starter economy Tinker NPC:" in line), None)
    if npc_line:
        break
    time.sleep(0.1)
if not npc_line:
    raise RuntimeError("stock Tinker NPC fixture missing")

time.sleep(3)
if not player.use_on(tools, ingots, timeout=6):
    raise RuntimeError("bound Tinker Tools did not accept ingot target")
scissors_before = {i.serial for i in player.backpack if i.name.lower() == "scissors"}
admin.call(f"say [StarterEconomyProbe maketinkerscissors {player.state['charID']}", timeout=6)
if not player.wait(lambda: any(i.name.lower() == "scissors" and i.serial not in scissors_before
                                for i in player.backpack), timeout=12):
    raise RuntimeError("ordinary stock Scissors craft output missing")
scissors = next(i for i in player.backpack
                if i.name.lower() == "scissors" and i.serial not in scissors_before)
if next((i.amount for i in player.backpack if i.serial == ingots), 0) != 4:
    raise RuntimeError("bound ingot input did not change from six to four")

before_gold = player.state["gold"]
sell_start = len(player_log.read_text(errors="replace").splitlines())
player.call("say A3 test tinker sell", timeout=6)
if not player.wait(lambda: any("[SHOP] Sell list from" in line
                               for line in player_log.read_text(errors="replace").splitlines()[sell_start:]), timeout=8):
    raise RuntimeError("stock Tinker did not send its sell list")
sell_list = player.call("selllist", timeout=6)
line = next((x for x in sell_list if scissors.serial in x and "scissors" in x.lower()), None)
if not line:
    raise RuntimeError(f"stock Tinker sell list omitted ordinary Scissors: {sell_list}")
price = int(re.search(r"([0-9]+)gp", line).group(1))
player.call(f"sell {scissors.serial} 1", timeout=6)
if not player.wait(lambda: player.state.get("gold", 0) == before_gold + price and
                    not any(i.serial == scissors.serial for i in player.backpack), timeout=8):
    raise RuntimeError("NPC Scissors sale did not complete with the listed price")
admin.call(f"say [StarterEconomyProbe item {scissors.serial}", timeout=6)
if not admin.wait(lambda: any(f"serial={scissors.serial}" in line and "root=Tinker" in line and
                              "nontransferable=False" in line
                              for line in admin_log.read_text(errors="replace").splitlines()), timeout=5):
    raise RuntimeError("staff probe did not observe ordinary Scissors in stock Tinker inventory")
print("CASE Tinker live sell list and ordinary Scissors sale: PASS", line)

buy_start = len(player_log.read_text(errors="replace").splitlines())
player.call("say A3 test tinker buy", timeout=6)
if not player.wait(lambda: any("[SHOP] Buy list from" in line
                               for line in player_log.read_text(errors="replace").splitlines()[buy_start:]), timeout=8):
    raise RuntimeError("stock Tinker did not send its repurchase list")
buy_list = player.call("shop", timeout=6)
stock_line = next((x for x in buy_list if scissors.serial in x and "scissors" in x.lower()), None)
if not stock_line:
    raise RuntimeError(f"sold Scissors were absent from Tinker repurchase list: {buy_list}")
repurchase_price = int(re.search(r"([0-9]+)gp", stock_line).group(1))
gold_before_repurchase = player.state["gold"]
player.call(f"buy {scissors.serial} 1", timeout=6)
if not player.wait(lambda: any(i.name.lower() == "scissors" for i in player.backpack) and
                    player.state.get("gold", 0) == gold_before_repurchase - repurchase_price, timeout=8):
    raise RuntimeError("NPC repurchase did not restore Scissors and charge its listed price")
print("CASE Tinker Scissors repurchase: PASS", stock_line)
print("fixture:", fixture)
print("NPC:", npc_line)
print("NPC sell list:", sell_list)
print("NPC repurchase list:", buy_list)
