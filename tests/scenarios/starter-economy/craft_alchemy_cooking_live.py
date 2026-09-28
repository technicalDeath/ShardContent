from pathlib import Path
import re
import sys
import time

root = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(root / "Navrey" / "cli"))
from uo import Client


def client(role):
    directory = (root / "work" / "alpha3-starter-economy-clients" / role).resolve()
    value = Client(
        state_file=str(directory / "state2.json"), world_file=str(directory / "world2.json"),
        cmd_file=str(directory / "cmd2.txt"), log_file=str(directory / "client2.log"),
    )
    value.require_live()
    if not value.state.get("inGame") or time.time() * 1000 - value.state.get("updatedAtMs", 0) >= 5000:
        raise RuntimeError(f"{role} has no fresh in-game state")
    return value, directory


admin, ad = client("admin")
player, pd = client("tinker")
admin_log, player_log = ad / "client2.log", pd / "client2.log"
player.open_backpack(wait=4)


def run_case(seed, marker, make, inputs, output, tool=None):
    start = len(admin_log.read_text(errors="replace").splitlines())
    admin.call(f"say [StarterEconomyProbe {seed} {player.state['charID']}", timeout=6)
    deadline = time.monotonic() + 8
    fixture = None
    while time.monotonic() < deadline:
        lines = admin_log.read_text(errors="replace").splitlines()[start:]
        fixture = next((line for line in reversed(lines) if marker in line), None)
        if fixture:
            break
        time.sleep(0.1)
    if not fixture:
        raise RuntimeError(f"fixture message missing for {seed}")
    serials = {}
    for key, amount in inputs.items():
        match = re.search(rf"{key}=(?:0x)?([0-9A-Fa-f]+)", fixture)
        if not match:
            raise RuntimeError(f"serial for {key} missing in {fixture}")
        serials[key] = "0x" + match.group(1)
        if not player.wait(lambda s=serials[key], n=amount: any(i.serial == s and i.amount == n for i in player.backpack), timeout=5):
            raise RuntimeError(f"expected {key} x{amount} absent; {player.backpack}")
    before = [(i.serial, i.name, i.amount) for i in player.backpack]
    before_output = sum(i.amount for i in player.backpack if output in i.name.lower())
    time.sleep(3)
    if tool:
        player.use(serials[tool])
        time.sleep(0.5)
    make_start = len(admin_log.read_text(errors="replace").splitlines())
    admin.call(f"say [StarterEconomyProbe {make} {player.state['charID']}", timeout=6)
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        count = sum(i.amount for i in player.backpack if output in i.name.lower())
        if count > before_output:
            break
        time.sleep(0.1)
    after = [(i.serial, i.name, i.amount) for i in player.backpack]
    if sum(i.amount for i in player.backpack if output in i.name.lower()) <= before_output:
        raise RuntimeError(f"{make} failed; player log={player_log.read_text(errors='replace').splitlines()[-20:]}; inventory={after}")
    for key, initial in inputs.items():
        expected = initial - 1 if key in ("bottle", "fish") else initial
        if key == "ginseng":
            expected -= 1
        serial = serials[key]
        actual = next((i.amount for i in player.backpack if i.serial == serial), 0)
        if actual != expected:
            raise RuntimeError(f"{make} {key} became {actual}, expected {expected}; {after}")
    selection = next((line for line in admin_log.read_text(errors="replace").splitlines()[make_start:] if "selection:" in line), "not reported")
    print(f"CASE {seed}/{make}: PASS")
    print(" fixture:", fixture)
    print(" before:", before)
    print(" after:", after)
    print(" server:", selection)


run_case("craftalchemy", "Starter economy alchemy targets:", "makealchemy",
         {"bottle": 1, "ginseng": 3, "tool": 1}, "yellow potion", "tool")
run_case("craftcook", "Starter economy cooking targets:", "makecook",
         {"fish": 1, "kindling": 1}, "fish steak")
