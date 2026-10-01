"""Elf-only gear is refused for a cosmetic Elf and allowed for a Human; plain gear is allowed for both
(Beta 1 item 1, live). Uses [TestOnlyElfEquip, which calls Mobile.EquipItem (the CanEquip path a client
equip takes) on a freshly made item and records whether it ended up worn.

Needs ElfSmith, HumSmith, ElfMage, HumMage (no Cloak worn) and the staff session on the elf-on host.
"""
import json
import sys
import time
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(WORKSPACE / ".claude" / "scripts"))
from navrey_session import connect  # noqa: E402

HOST = WORKSPACE / "work" / "hosts" / "elf-on"
staff = connect("admin")

# (character, item type, expected equipped). Elven items are refused for the Human too; stock refuses
# them by race, and the cosmetic Elf must behave the same.
CASES = [
    ("ElfSmith", "ElvenShirt", False),
    ("ElfSmith", "ElvenBoots", False),
    ("HumSmith", "ElvenShirt", False),
    ("HumSmith", "ElvenBoots", False),
    # plain Human gear in a free layer (Cloak) is worn by both races; note an item that is worn stays
    # worn, so run this script once per host state
    ("ElfMage", "Cloak", True),
    ("HumMage", "Cloak", True),
]
results, failed = {}, []
for name, type_name, expected in CASES:
    serial = connect(name).state["charID"]
    hexserial = serial[2:].upper().lstrip("0")
    path = HOST / f"elf-equip-{hexserial}-{type_name}.json"
    before = path.stat().st_mtime if path.exists() else 0
    staff.say(f"[TestOnlyElfEquip {serial} {type_name}")
    deadline = time.time() + 10
    while time.time() < deadline and not (path.exists() and path.stat().st_mtime > before):
        time.sleep(0.3)
    got = json.loads(path.read_text(encoding="utf-8"))
    ok = got["equipped"] == expected
    results[f"{name}:{type_name}"] = {"ok": ok, **got}
    print(("PASS " if ok else "FAIL ") + f"equip:{name}:{type_name} equipped={got['equipped']} expected={expected}")
    if not ok:
        failed.append(f"{name}:{type_name}")

(WORKSPACE / "work" / "elf-live" / "results-equip.json").write_text(json.dumps(results, indent=2))
sys.exit(1 if failed else 0)
