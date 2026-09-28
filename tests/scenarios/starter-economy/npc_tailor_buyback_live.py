"""Live ordinary Shirt sale and buyback with a stock Tailor."""
from pathlib import Path
import re
import sys
import time

root = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(root / "Navrey" / "cli"))
from uo import Client


def open_client(role):
    d = (root / "work" / "alpha3-starter-economy-clients" / role).resolve()
    c = Client(state_file=str(d / "npc_state.json"), world_file=str(d / "npc_world.json"),
               cmd_file=str(d / "npc_cmd.txt"), log_file=str(d / "npc_client.log"))
    c.require_live()
    if not c.wait(lambda: c.state.get("updatedAtMs", 0) and
                  0 <= time.time() * 1000 - c.state["updatedAtMs"] < 5000, timeout=8):
        raise RuntimeError(f"{role} has no fresh snapshot")
    return c, d


def wait_line(log, start, fragment, timeout=8):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        rows = log.read_text(errors="replace").splitlines()[start:]
        line = next((x for x in reversed(rows) if fragment in x), None)
        if line:
            return line
        time.sleep(.1)
    raise RuntimeError(f"missing server/client result: {fragment}")


admin, ad = open_client("admin")
player, pd = open_client("player2")
if not player.state.get("inGame"):
    player.call("createcharacter StarterTinker 0 29 30", timeout=6)
    if not player.wait(lambda: player.state.get("inGame") and player.state.get("charName") == "StarterTinker", timeout=15):
        raise RuntimeError("ordinary Tailor customer did not enter the world")
if player.state.get("charName") != "StarterTinker":
    raise RuntimeError(f"ordinary client selected {player.state.get('charName')}")
if not player.open_backpack(wait=4):
    raise RuntimeError("ordinary backpack did not open")

al = ad / "npc_client.log"
pl = pd / "npc_client.log"
start = len(al.read_text(errors="replace").splitlines())
admin.call("say [ShardRulesStatus", timeout=6)
wait_line(al, start, "Alpha 3 enablement acknowledged: False", timeout=6)

start = len(al.read_text(errors="replace").splitlines())
admin.call(f"say [StarterEconomyProbe craftcloth {player.state['charID']}", timeout=6)
fixture = wait_line(al, start, "Starter economy tailoring targets:")
cloth = "0x" + re.search(r"cloth=(?:0x)?([0-9A-Fa-f]+)", fixture).group(1)
kit = "0x" + re.search(r"kit=(?:0x)?([0-9A-Fa-f]+)", fixture).group(1)
if not player.wait(lambda: any(i.serial == cloth and i.amount == 100 for i in player.backpack) and
                    any(i.serial == kit for i in player.backpack), timeout=5):
    raise RuntimeError("bound tailoring inputs did not appear")
time.sleep(3)
if not player.use_on(kit, cloth, timeout=6):
    raise RuntimeError("bound Sewing Kit did not accept bound StarterCloth target")
before_shirts = {i.serial for i in player.backpack if i.name.lower() == "shirt"}
start = len(al.read_text(errors="replace").splitlines())
craft_start = len(pl.read_text(errors="replace").splitlines())
admin.call(f"say [StarterEconomyProbe makecloth {player.state['charID']}", timeout=6)
end = time.monotonic() + 15
marked = False
while time.monotonic() < end:
    rows = pl.read_text(errors="replace").splitlines()[craft_start:]
    if not marked and any("Do you wish to place your maker's mark" in x for x in rows):
        player.call("gumpresponse 1", timeout=5)
        marked = True
    if any(i.name.lower() == "shirt" and i.serial not in before_shirts for i in player.backpack):
        break
    time.sleep(.1)
shirt = next((i for i in player.backpack if i.name.lower() == "shirt" and i.serial not in before_shirts), None)
if shirt is None or not player.wait(lambda: next((i.amount for i in player.backpack if i.serial == cloth), 0) == 92, timeout=5):
    raise RuntimeError("stock Shirt was not crafted or eight bound cloth were not consumed")
selection = wait_line(al, start, "Starter economy tailoring selection:")

start = len(al.read_text(errors="replace").splitlines())
admin.call(f"say [StarterEconomyProbe tailornpc {player.state['charID']}", timeout=6)
npc = wait_line(al, start, "Starter economy Tailor NPC:")
time.sleep(2)
before_gold = player.state.get("gold", 0)
start = len(pl.read_text(errors="replace").splitlines())
player.call("say A3 test tailor sell", timeout=6)
wait_line(pl, start, "[SHOP] Sell list from", timeout=8)
sell_list = player.call("selllist", timeout=6)
line = next((x for x in sell_list if shirt.serial in x and "shirt" in x.lower()), None)
if not line:
    raise RuntimeError(f"stock Tailor sell list omitted ordinary Shirt: {sell_list}")
price = int(re.search(r"([0-9]+)gp", line).group(1))
player.call(f"sell {shirt.serial} 1", timeout=6)
if not player.wait(lambda: player.state.get("gold", 0) == before_gold + price and
                    not any(i.serial == shirt.serial for i in player.backpack), timeout=8):
    raise RuntimeError("ordinary Shirt sale did not complete at the listed price")
start = len(pl.read_text(errors="replace").splitlines())
player.call("say A3 test tailor buy", timeout=6)
wait_line(pl, start, "[SHOP] Buy list from", timeout=8)
buy_list = player.call("shop", timeout=6)
buy_line = next((x for x in buy_list if shirt.serial in x and "shirt" in x.lower()), None)
if not buy_line:
    raise RuntimeError(f"Tailor buyback list omitted sold Shirt {shirt.serial}: {buy_list}")
buy_price = int(re.search(r"([0-9]+)gp", buy_line).group(1))
gold_before_buyback = player.state.get("gold", 0)
player.call(f"buy {shirt.serial} 1", timeout=6)
if not player.wait(lambda: player.state.get("gold", 0) == gold_before_buyback - buy_price and
                    any(i.serial == shirt.serial for i in player.backpack), timeout=8):
    raise RuntimeError("same ordinary Shirt did not return from Tailor buyback at listed price")

verify_start = len(al.read_text(errors="replace").splitlines())
admin.call(f"say [StarterEconomyProbe item {shirt.serial}", timeout=6)
state = wait_line(al, verify_start, "Starter economy output verify:")
if "type=Shirt" not in state or "nontransferable=False" not in state or "vendorStock=False" not in state:
    raise RuntimeError(f"staff did not confirm unrestricted stock Shirt: {state}")
print("CASE stock Tailor ordinary Shirt sale/buyback: PASS")
print("fixture:", fixture)
print("craft:", selection)
print("npc:", npc)
print("sell:", line)
print("buyback:", buy_line)
print("server verification:", state)
