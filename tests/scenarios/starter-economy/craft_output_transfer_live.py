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
seller, sd = open_client("tinker")
buyer, bd = open_client("player2")
if not seller.state.get("inGame"):
    seller.call("createcharacter StarterTinker 0 29 30", timeout=6)
    if not seller.wait(lambda: seller.state.get("inGame"), timeout=12):
        raise RuntimeError("StarterTinker did not enter the world")
if seller.state.get("charName") != "StarterTinker":
    raise RuntimeError(f"seller is {seller.state.get('charName')}, expected StarterTinker")
if not buyer.state.get("inGame"):
    buyer.call("createcharacter StarterBuyer 0 29 30", timeout=6)
    if not buyer.wait(lambda: buyer.state.get("inGame"), timeout=12):
        raise RuntimeError("StarterBuyer did not enter the world")
if buyer.state.get("charName") != "StarterBuyer":
    raise RuntimeError(f"buyer is {buyer.state.get('charName')}, expected StarterBuyer")
if seller.state["charID"] == buyer.state["charID"]:
    raise RuntimeError("paired clients do not represent separate characters")

admin_log = ad / "client2.log"
buyer_place_start = len(admin_log.read_text(errors="replace").splitlines())
admin.call(f"say [StarterEconomyProbe place {buyer.state['charID']}", timeout=6)
if not admin.wait(lambda: any("paired client placed" in line
                               for line in admin_log.read_text(errors="replace").splitlines()[buyer_place_start:]), timeout=5):
    raise RuntimeError("server did not confirm buyer placement")

seed_start = len(admin_log.read_text(errors="replace").splitlines())
admin.call(f"say [StarterEconomyProbe crafttinkerscissors {seller.state['charID']}", timeout=6)
deadline = time.monotonic() + 8
fixture = None
while time.monotonic() < deadline:
    fixture = next((line for line in reversed(admin_log.read_text(errors="replace").splitlines()[seed_start:])
                    if "Starter economy Tinkering scissors targets:" in line), None)
    if fixture:
        break
    time.sleep(0.1)
if not fixture:
    raise RuntimeError("Scissors crafting fixture missing")
ingots = "0x" + re.search(r"ingots=(?:0x)?([0-9A-Fa-f]+)", fixture).group(1)
tools = "0x" + re.search(r"tools=(?:0x)?([0-9A-Fa-f]+)", fixture).group(1)
if not seller.open_backpack(wait=4):
    raise RuntimeError("seller backpack did not open")
if not seller.wait(lambda: any(i.serial == ingots and i.amount == 6 for i in seller.backpack), timeout=5):
    raise RuntimeError("StarterIronIngot x6 missing")
time.sleep(3)
if not seller.use_on(tools, ingots, timeout=6):
    raise RuntimeError("bound Tinker Tools did not accept ingot target")
before_serials = {i.serial for i in seller.backpack}
admin.call(f"say [StarterEconomyProbe maketinkerscissors {seller.state['charID']}", timeout=6)
if not seller.wait(lambda: any(i.name.lower() == "scissors" and i.serial not in before_serials
                                for i in seller.backpack), timeout=12):
    raise RuntimeError("normal Scissors output not created")
scissors = next(i.serial for i in seller.backpack
                if i.name.lower() == "scissors" and i.serial not in before_serials)
if next((i.amount for i in seller.backpack if i.serial == ingots), 0) != 4:
    raise RuntimeError("crafted Scissors did not consume exactly two bound ingots")

time.sleep(2)
seller.drop(scissors, buyer.state["charID"])
deadline = time.monotonic() + 10
trade_lines = []
while time.monotonic() < deadline:
    trade_lines = seller.call("trades", timeout=5)
    if any("[TRADE]" in line for line in trade_lines):
        break
    time.sleep(0.1)
else:
    raise RuntimeError(f"ordinary Scissors did not open secure trade: {trade_lines}")
seller.call("accepttrade", timeout=5)
time.sleep(0.2)
buyer.call("accepttrade", timeout=5)
if not buyer.wait(lambda: any(i.serial == scissors for i in buyer.backpack), timeout=10):
    raise RuntimeError("ordinary Scissors did not arrive in buyer backpack")
if any(i.serial == scissors for i in seller.backpack):
    raise RuntimeError("Scissors remained with seller after both accepted")
print("CASE crafted ordinary Scissors secure trade: PASS")

time.sleep(1.5)
buyer.drop(scissors, seller.state["charID"])
deadline = time.monotonic() + 10
while time.monotonic() < deadline:
    trade_lines = buyer.call("trades", timeout=5)
    if any("[TRADE]" in line for line in trade_lines):
        break
    time.sleep(0.1)
else:
    raise RuntimeError("return trade for ordinary Scissors did not open")
buyer.call("accepttrade", timeout=5)
time.sleep(0.2)
seller.call("accepttrade", timeout=5)
if not seller.wait(lambda: any(i.serial == scissors for i in seller.backpack), timeout=10):
    raise RuntimeError("Scissors did not return to seller")

vendor_start = len(admin_log.read_text(errors="replace").splitlines())
admin.call(f"say [StarterEconomyProbe vendor {seller.state['charID']}", timeout=6)
deadline = time.monotonic() + 8
vendor_line = None
while time.monotonic() < deadline:
    vendor_line = next((line for line in reversed(admin_log.read_text(errors="replace").splitlines()[vendor_start:])
                        if "Starter economy player vendor:" in line), None)
    if vendor_line:
        break
    time.sleep(0.1)
if not vendor_line:
    raise RuntimeError("player vendor fixture missing")
vendor = "0x" + re.search(r"vendor=(?:0x)?([0-9A-Fa-f]+)", vendor_line).group(1)
time.sleep(1.5)
sell_start = len((sd / "client2.log").read_text(errors="replace").splitlines())
seller.drop(scissors, vendor)
if not seller.wait(lambda: any("Type in a price and description" in line
                                for line in (sd / "client2.log").read_text(errors="replace").splitlines()[sell_start:]), timeout=6):
    raise RuntimeError("player vendor did not request a price for ordinary Scissors")
seller.call("prompt 100 Crafted Scissors", timeout=5)
if not seller.wait(lambda: not any(i.serial == scissors for i in seller.backpack), timeout=8):
    raise RuntimeError("ordinary Scissors were not accepted into player-vendor stock")
verify_start = len(admin_log.read_text(errors="replace").splitlines())
admin.call(f"say [StarterEconomyProbe item {scissors}", timeout=6)
deadline = time.monotonic() + 6
verification = None
while time.monotonic() < deadline:
    verification = next((line for line in admin_log.read_text(errors="replace").splitlines()[verify_start:]
                         if "Starter economy output verify:" in line), None)
    if verification:
        break
    time.sleep(0.1)
if not verification or "type=Scissors" not in verification or "nontransferable=False" not in verification or "vendorStock=True" not in verification:
    raise RuntimeError(f"staff did not confirm ordinary Scissors in vendor stock: {verification}")
print("CASE crafted ordinary Scissors player-vendor intake: PASS")
print("fixture:", fixture)
print("secure_trade:", trade_lines)
print("vendor:", vendor_line)
print("server verification:", verification)
