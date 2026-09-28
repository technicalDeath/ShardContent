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
    if (role == "admin" and not client.state.get("inGame")) or time.time() * 1000 - client.state.get("updatedAtMs", 0) >= 5000:
        raise RuntimeError(f"{role} has no fresh in-game state")
    return client, directory


admin, admin_dir = open_client("admin")
player, player_dir = open_client("tinker")
if player.state.get("charName") != "StarterTinker":
    player.call("createcharacter StarterTinker 0 29 30", timeout=6)
    if not player.wait(lambda: player.state.get("inGame"), timeout=12):
        raise RuntimeError("ordinary client did not enter as StarterTinker")
admin_log = admin_dir / "client2.log"
player_log = player_dir / "client2.log"
if not player.open_backpack(wait=4):
    raise RuntimeError("ordinary backpack did not open")

status_start = len(admin_log.read_text(errors="replace").splitlines())
admin.call("say [ShardRulesStatus", timeout=6)
deadline = time.monotonic() + 5
while time.monotonic() < deadline:
    status_lines = admin_log.read_text(errors="replace").splitlines()[status_start:]
    if any("Alpha 3 enablement acknowledged: False" in line for line in status_lines):
        break
    time.sleep(0.1)
if not any("Alpha 3 enablement acknowledged: False" in line for line in status_lines):
    raise RuntimeError(f"Alpha 3 remained unverified in ShardRulesStatus: {status_lines}")


def inventory():
    return list(player.backpack)


def amount(serial):
    item = next((item for item in inventory() if item.serial == serial), None)
    return item.amount if item else 0


def count_name(keyword):
    return sum(item.amount for item in inventory() if keyword.lower() in item.name.lower())


def run_case(seed_action, marker, make_action, fixture_fields, input_expectations, output_name, tool_field=None, target_field=None):
    admin_start = len(admin_log.read_text(errors="replace").splitlines())
    admin.call(f"say [StarterEconomyProbe {seed_action} {player.state['charID']}", timeout=6)
    deadline = time.monotonic() + 8
    fixture = None
    while time.monotonic() < deadline:
        lines = admin_log.read_text(errors="replace").splitlines()[admin_start:]
        fixture = next((line for line in reversed(lines) if marker in line), None)
        if fixture:
            break
        time.sleep(0.1)
    if not fixture:
        raise RuntimeError(f"{seed_action} fixture was not observed in staff log")
    serials = {}
    for field in fixture_fields:
        match = re.search(rf"{field}=(?:0x)?([0-9A-Fa-f]+)", fixture)
        if match:
            serials[field] = "0x" + match.group(1)
    if not player.wait(lambda: all(any(item.serial == serial for item in inventory()) for serial in serials.values()), timeout=5):
        raise RuntimeError(f"{seed_action} seeded items are absent: {fixture}; inventory={inventory()}")
    before = [(item.serial, item.name, item.amount) for item in inventory()]
    for field, expected in input_expectations.items():
        if amount(serials[field]) != expected:
            raise RuntimeError(f"{seed_action} expected {field} amount {expected}: {before}")
    time.sleep(3)
    if tool_field and target_field:
        if not player.use_on(serials[tool_field], serials[target_field], timeout=6):
            raise RuntimeError(f"{seed_action} tool target cursor failed; check action cooldown")
    elif tool_field:
        player.use(serials[tool_field])
        time.sleep(0.5)
    player_start = len(player_log.read_text(errors="replace").splitlines())
    make_start = len(admin_log.read_text(errors="replace").splitlines())
    admin.call(f"say [StarterEconomyProbe {make_action} {player.state['charID']}", timeout=6)
    deadline = time.monotonic() + 15
    responded = False
    while time.monotonic() < deadline:
        lines = player_log.read_text(errors="replace").splitlines()[player_start:]
        if any("Do you wish to place your maker's mark" in line for line in lines):
            player.call("gumpresponse 1", timeout=5)
            responded = True
            break
        if any("You create" in line or "You mark the item" in line for line in lines):
            break
        time.sleep(0.1)
    if not player.wait(lambda: count_name(output_name) > sum(amount for _, name, amount in before if output_name.lower() in name.lower()), timeout=10):
        tail = player_log.read_text(errors="replace").splitlines()[-25:]
        raise RuntimeError(f"{make_action} did not create {output_name}; output={tail}; inventory={inventory()}")
    after = [(item.serial, item.name, item.amount) for item in inventory()]
    for field, current in input_expectations.items():
        want = current
        if field == "leather":
            want -= 2
        elif field in ("recall", "gate"):
            want = 0
        elif field == "boards":
            want = 0
        elif field == "feathers":
            want = 0
        elif field == "blank":
            want = 0
        elif field == "bottle":
            want = 0
        elif field == "ginseng":
            want -= 1
        elif field == "fish":
            want = 0
        if amount(serials[field]) != want:
            raise RuntimeError(f"{make_action} input {field} ended at {amount(serials[field])}, expected {want}: {after}")
    staff_lines = admin_log.read_text(errors="replace").splitlines()[make_start:]
    selection = next((line for line in staff_lines if "Starter economy " in line and "selection:" in line), "not reported")
    print(f"CASE {seed_action}/{make_action}: PASS")
    print(" fixture:", fixture)
    print(" before:", before)
    print(" after:", after)
    print(" server:", selection)
    print(" maker_mark_accepted:", responded)


run_case(
    "craftleather", "Starter economy leather tailoring targets:", "makeleather",
    ("leather", "kit"), {"leather": 20, "kit": 1}, "leather cap", "kit", "leather",
)
run_case(
    "craftbowyer", "Starter economy bowyer targets:", "makebowyer",
    ("boards", "feathers", "tools"), {"boards": 1, "feathers": 1, "tools": 1}, "shaft", "tools", "boards",
)
time.sleep(3)
bowyer_line = next(line for line in reversed(admin_log.read_text(errors="replace").splitlines()) if "Starter economy bowyer targets:" in line)
feather_serial = "0x" + re.search(r"feathers=(?:0x)?([0-9A-Fa-f]+)", bowyer_line).group(1)
arrow_count = count_name("arrow")
arrow_start = len(admin_log.read_text(errors="replace").splitlines())
admin.call(f"say [StarterEconomyProbe makearrow {player.state['charID']}", timeout=6)
deadline = time.monotonic() + 15
arrow_mark_responded = False
while time.monotonic() < deadline and count_name("arrow") <= arrow_count:
    lines = player_log.read_text(errors="replace").splitlines()[-20:]
    if not arrow_mark_responded and any("Do you wish to place your maker's mark" in line for line in lines):
        player.call("gumpresponse 1", timeout=5)
        arrow_mark_responded = True
    time.sleep(0.1)
if count_name("arrow") <= arrow_count or amount(feather_serial) != 0:
    raise RuntimeError(f"makearrow did not consume StarterFeather/create stock arrows: {inventory()}")
print("CASE craftbowyer/makearrow: PASS; StarterFeather consumed and stock arrows received")

run_case(
    "craftscribe", "Starter economy inscription targets:", "makescribe",
    ("blank", "pen", "recall", "gate"), {"blank": 8, "pen": 1, "recall": 1, "gate": 1}, "runebook", "pen",
)
run_case(
    "craftalchemy", "Starter economy alchemy targets:", "makealchemy",
    ("bottle", "ginseng", "tool"), {"bottle": 1, "ginseng": 3, "tool": 1}, "lesser heal potion", "tool",
)
run_case(
    "craftcook", "Starter economy cooking targets:", "makecook",
    ("fish", "kindling"), {"fish": 1, "kindling": 1}, "fish steak",
)
