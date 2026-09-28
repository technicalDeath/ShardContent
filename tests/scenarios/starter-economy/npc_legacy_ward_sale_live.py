from pathlib import Path
import re
import sys
import time

root = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(root / "Navrey" / "cli"))
from uo import Client


def open_client(role):
    directory = (root / "work" / "alpha3-legacyward-sale-20260928" / role).resolve()
    client = Client(state_file=str(directory / "state2.json"),
                    world_file=str(directory / "world2.json"),
                    cmd_file=str(directory / "cmd2.txt"),
                    log_file=str(directory / "client2.log"))
    client.require_live()
    if not client.wait(lambda: client.state.get("updatedAtMs", 0) and
                       0 <= time.time() * 1000 - client.state["updatedAtMs"] < 5000,
                       timeout=8):
        raise RuntimeError(f"{role} has no fresh game snapshot")
    return client, directory


def wait_line(client, log, start, marker, timeout=8):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        rows = log.read_text(errors="replace").splitlines()[start:]
        line = next((row for row in reversed(rows) if marker in row), None)
        if line:
            return line
        time.sleep(0.1)
    raise RuntimeError(f"missing response: {marker}")


admin, ad = open_client("admin")
player, pd = open_client("player")
admin_log = ad / "client2.log"
player_log = pd / "client2.log"

if not admin.state.get("inGame"):
    raise RuntimeError("staff client is not in game")
if not player.state.get("inGame"):
    player.call("createcharacter StarterWardSale 0 29 30", timeout=6)
    if not player.wait(lambda: player.state.get("inGame") and
                       player.state.get("charName") == "StarterWardSale", timeout=15):
        raise RuntimeError("ordinary test character did not enter the world")
if player.state.get("charName") != "StarterWardSale":
    raise RuntimeError("ordinary role is not the dedicated Ward-sale character")

status_start = len(admin_log.read_text(errors="replace").splitlines())
admin.call("say [ShardRulesStatus", timeout=6)
wait_line(admin, admin_log, status_start, "Alpha 3 enablement acknowledged: False")

fixture_start = len(admin_log.read_text(errors="replace").splitlines())
admin.call(f"say [StarterEconomyProbe npcward {player.state['charID']}", timeout=6)
fixture = wait_line(admin, admin_log, fixture_start, "Starter economy legacy Ward NPC targets:")
serials = {key: "0x" + re.search(rf"{key}=(?:0x)?([0-9A-Fa-f]+)", fixture).group(1)
           for key in ("legacy", "starter", "vendor")}
if "price=10" not in fixture:
    raise RuntimeError(f"unexpected disposable vendor price: {fixture}")

if not player.open_backpack(wait=4):
    raise RuntimeError("ordinary backpack did not open")
if not player.wait(lambda: all(any(item.serial == serial for item in player.backpack)
                               for serial in (serials["legacy"], serials["starter"])), timeout=6):
    raise RuntimeError("both Ward fixtures were not present in the ordinary backpack")

before_gold = player.state["gold"]
sell_start = len(player_log.read_text(errors="replace").splitlines())
player.call("say A3 test blacksmith sell", timeout=6)
wait_line(player, player_log, sell_start, "[SHOP] Sell list from", timeout=8)
sell_list = player.call("selllist", timeout=6)
sell_text = "\n".join(sell_list)
if serials["legacy"] not in sell_text:
    raise RuntimeError(f"unmarked legacy Ward was omitted from the sell list: {sell_list}")
if serials["starter"] in sell_text:
    raise RuntimeError("marked starter Ward appeared in the NPC sell list")

player.call(f"sell {serials['legacy']} 1", timeout=6)
if not player.wait(lambda: player.state.get("gold", 0) == before_gold + 10 and
                   not any(item.serial == serials["legacy"] for item in player.backpack), timeout=8):
    raise RuntimeError("legacy Ward sale did not complete for the listed value")
if not any(item.serial == serials["starter"] for item in player.backpack):
    raise RuntimeError("marked starter Ward left the player's backpack")

buy_start = len(player_log.read_text(errors="replace").splitlines())
player.call("say A3 test blacksmith buy", timeout=6)
wait_line(player, player_log, buy_start, "[SHOP] Buy list from", timeout=8)
buy_list = player.call("shop", timeout=6)
ward_line = next((line for line in buy_list
                  if serials["legacy"] in line and "legacy Ward sale control" in line), None)
if not ward_line:
    raise RuntimeError(f"sold legacy Ward was absent from NPC repurchase stock: {buy_list}")
buy_price = int(re.search(r"([0-9]+)gp", ward_line).group(1))
gold_before_buy = player.state["gold"]
player.call(f"buy {serials['legacy']} 1", timeout=6)
if not player.wait(lambda: any(item.serial == serials["legacy"] for item in player.backpack) and
                   player.state.get("gold", 0) == gold_before_buy - buy_price, timeout=8):
    raise RuntimeError("legacy Ward repurchase did not restore the same item and charge its price")

verify_start = len(admin_log.read_text(errors="replace").splitlines())
admin.call(f"say [StarterEconomyProbe item {serials['legacy']}", timeout=6)
verified = wait_line(admin, admin_log, verify_start, "Starter economy output verify:")
if ("type=BackpackWard" not in verified or "nontransferable=False" not in verified or
        "root=PlayerMobile" not in verified):
    raise RuntimeError(f"server did not verify repurchased ordinary Ward ownership: {verified}")

print("CASE legacy Ward NPC sell-list exclusion, sale, and same-serial repurchase: PASS")
print("fixture:", fixture)
print("NPC sell list:", sell_list)
print("NPC repurchase:", ward_line)
print("server verification:", verified)
