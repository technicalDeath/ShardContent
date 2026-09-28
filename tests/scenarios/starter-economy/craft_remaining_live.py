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


admin, ad = open_client("admin")
player, pd = open_client("tinker")
alog, plog = ad / "client2.log", pd / "client2.log"
player.open_backpack(wait=4)


def run_case(seed, marker, make, expected_input_fields, output_name, tool_field=None, target_field=None):
    start = len(alog.read_text(errors="replace").splitlines())
    admin.call(f"say [StarterEconomyProbe {seed} {player.state['charID']}", timeout=6)
    deadline = time.monotonic() + 8
    fixture = None
    while time.monotonic() < deadline:
        lines = alog.read_text(errors="replace").splitlines()[start:]
        fixture = next((line for line in reversed(lines) if marker in line), None)
        if fixture:
            break
        time.sleep(0.1)
    if not fixture:
        raise RuntimeError(f"no fixture output for {seed}")
    serials = {}
    for key in expected_input_fields:
        match = re.search(rf"{key}=(?:0x)?([0-9A-Fa-f]+)", fixture)
        if match:
            serials[key] = "0x" + match.group(1)
    if not player.wait(lambda: all(any(i.serial == s for i in player.backpack) for s in serials.values()), timeout=5):
        raise RuntimeError(f"seeded inventory incomplete: {fixture}; {player.backpack}")
    before = [(i.serial, i.name, i.amount) for i in player.backpack]
    before_output = sum(i.amount for i in player.backpack if output_name in i.name.lower())
    time.sleep(3)
    if tool_field and target_field:
        if not player.use_on(serials[tool_field], serials[target_field], timeout=6):
            raise RuntimeError(f"{seed} target cursor failed")
    elif tool_field:
        player.use(serials[tool_field])
        time.sleep(0.6)
    make_start = len(alog.read_text(errors="replace").splitlines())
    player_start = len(plog.read_text(errors="replace").splitlines())
    admin.call(f"say [StarterEconomyProbe {make} {player.state['charID']}", timeout=6)
    deadline = time.monotonic() + 15
    mark_done = False
    while time.monotonic() < deadline:
        lines = plog.read_text(errors="replace").splitlines()[player_start:]
        if not mark_done and any("Do you wish to place your maker's mark" in line for line in lines):
            player.call("gumpresponse 1", timeout=5)
            mark_done = True
        if any("You create" in line or "You mark the item" in line for line in lines):
            if sum(i.amount for i in player.backpack if output_name in i.name.lower()) > before_output:
                break
        time.sleep(0.1)
    after = [(i.serial, i.name, i.amount) for i in player.backpack]
    if sum(i.amount for i in player.backpack if output_name in i.name.lower()) <= before_output:
        raise RuntimeError(f"{make} did not create {output_name}; player log={plog.read_text(errors='replace').splitlines()[-20:]}; after={after}")
    for key, expected in expected_input_fields.items():
        want = expected
        if key in ("blank", "blankRune", "recall", "gate", "bottle", "fish"):
            want = 0
        elif key == "ginseng":
            want -= 1
        elif key == "kindling":
            want = expected  # FishSteak uses raw fish; kindling is retained.
        serial = serials[key]
        observed = next((i.amount for i in player.backpack if i.serial == serial), 0)
        if observed != want:
            raise RuntimeError(f"{make} {key} ended {observed}, expected {want}; after={after}")
    lines = alog.read_text(errors="replace").splitlines()[make_start:]
    selection = next((line for line in lines if "selection:" in line and "Starter economy" in line), "not reported")
    print(f"CASE {seed}/{make}: PASS")
    print(" fixture:", fixture)
    print(" before:", before)
    print(" after:", after)
    print(" server:", selection)


run_case(
    "craftscribe", "Starter economy inscription targets:", "makescribe",
    {"blank": 8, "pen": 1, "recall": 1, "gate": 1, "blankRune": 1}, "spellbook", "pen", "blank",
)
run_case(
    "craftalchemy", "Starter economy alchemy targets:", "makealchemy",
    {"bottle": 1, "ginseng": 3, "tool": 1}, "yellow potion", "tool", "ginseng",
)
run_case(
    "craftcook", "Starter economy cooking targets:", "makecook",
    {"fish": 1, "kindling": 1}, "fish steak",
)
