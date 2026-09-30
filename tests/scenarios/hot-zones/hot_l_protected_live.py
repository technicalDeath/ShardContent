"""Phase L group 3: protected items x Knocked Out x Execute, plus the live rerun of the repeat-kill murder count.

    python ShardContent/tests/scenarios/hot-zones/hot_l_protected_live.py

Needs fresh Warrior characters Vale, Tavi, Elin (New-TestCharacter.ps1 -HostName <host> -Name ... -Profession 1) on a
disposable host with hotZones, alpha3StarterScissors and alpha3StarterBag on and TestOnlyProbe loaded
(TestOnlyInventoryInspect, TestOnlyCorpseInventory). Reuses the K3 driver's helpers.
"""

from __future__ import annotations

import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import hot_k3_live as k  # noqa: E402
from navrey_session import connect  # noqa: E402
from staff_command import go_to, staff_target  # noqa: E402

HOT = {"Tavi": (2755, 2166, -2), "Vale": (2756, 2166, -2), "Elin": (2757, 2166, -2)}


def stamp(item: str, command: str) -> None:
    go_to(k.adm, k.C["Vale"])
    staff_target(k.adm, command, item)
    time.sleep(1)


def corpse_items(victim: str) -> list:
    m = k.mark("admin")
    k.adm.say(f"[TestOnlyCorpseInventory {k.serial(victim)}")
    time.sleep(2.5)
    text = " ".join(k.since("admin", m))
    return re.findall(r"corpse: (\w+) serial=(0x[0-9A-Fa-f]+) amount=\d+ lootType=(\w+) nontransferable=(\w+)", text)


def setup() -> None:
    for name in ("Elin", "Tavi"):
        k.sset(name, "[SetSkill Snooping 0")
        k.sset(name, "[SetSkill Stealing 0")
        k.sset(name, "[SetSkill Wrestling 100")
        k.unequip_weapon(name)
    k.sset("Tavi", "[set Criminal true")
    # Stock Spellbook is Blessed; the starter scissors and Ward are the Nontransferable pair; Lantern is a plain control.
    k.add_to_pack("Vale", "Spellbook")
    k.add_to_pack("Vale", "Lantern")
    items = k.pack_items("Vale")
    kinds = {}
    for type_, serial, loot in items:
        kinds.setdefault(loot, []).append(type_)
    m = k.mark("admin")
    k.adm.say(f"[TestOnlyInventoryInspect {k.serial('Vale')}")
    time.sleep(2.5)
    text = " ".join(k.since("admin", m))
    nontransfer = len(re.findall(r"nontransferable=True", text))
    k.record("P0 Vale carries Newbied, Blessed and Nontransferable items plus a plain one",
             "Newbied>=1, Blessed>=1, Nontransferable>=1, Regular>=1",
             f"lootTypes { {a: len(b) for a, b in kinds.items()} }; nontransferable={nontransfer}",
             len(kinds.get("Newbied", [])) >= 1 and len(kinds.get("Blessed", [])) >= 1 and nontransfer >= 1
             and len(kinds.get("Regular", [])) >= 1)


def place_all() -> None:
    for name, pos in HOT.items():
        k.place(name, *pos)
    time.sleep(3)


def protected_loot() -> None:
    k.revive("Vale")
    place_all()
    ko = k.knock_out("Tavi", "Vale")
    k.record("P1 Tavi knocks out Vale in Hot", "Vale Knocked Out", f"KO audit {ko}, hits {k.hits('Vale')}", ko)
    items = k.pack_items("Vale")
    groups = {
        "Newbied": [i for i in items if i[2] == "Newbied"],
        "Blessed": [i for i in items if i[2] == "Blessed"],
    }
    nontransfer = re.findall(r"serial=(0x[0-9A-Fa-f]+) amount=\d+ lootType=\w+ nontransferable=True",
                             _inspect_text("Vale"))
    groups["Nontransferable"] = [("?", s, "?") for s in nontransfer]
    for label, found in groups.items():
        before = k.audit("knocked-out-loot", "authorized", "Elin", "Vale")
        if found:
            k.loot("Elin", "Vale", found[0][1])
        still = bool(found) and found[0][1] in [i[1] for i in k.pack_items("Vale")]
        gained = k.audit("knocked-out-loot", "authorized", "Elin", "Vale") - before
        k.record(f"P2 a {label} item cannot be lifted from a Knocked Out pack", "item stays, no authorized audit",
                 f"items {len(found)}; stayed {still}; authorized+{gained}", still and gained == 0)
    plain = next(i[1] for i in k.pack_items("Vale") if i[0] == "Lantern" and i[2] == "Regular")
    before = k.audit("knocked-out-loot", "authorized", "Elin", "Vale")
    k.loot("Elin", "Vale", plain)
    gained = k.audit("knocked-out-loot", "authorized", "Elin", "Vale") - before
    moved = plain in [i[1] for i in k.pack_items("Elin")]
    k.record("P3 control: a plain item is lifted", "authorized+1 and moved", f"authorized+{gained}; moved {moved}",
             gained >= 1 and moved)


def _inspect_text(name: str) -> str:
    m = k.mark("admin")
    k.adm.say(f"[TestOnlyInventoryInspect {k.serial(name)}")
    time.sleep(2.5)
    return " ".join(k.since("admin", m))


def execute_and_corpse() -> None:
    before_items = k.pack_items("Vale")
    protected_serials = [i[1] for i in before_items if i[2] in ("Newbied", "Blessed")]
    protected_serials += re.findall(r"serial=(0x[0-9A-Fa-f]+) amount=\d+ lootType=\w+ nontransferable=True",
                                    _inspect_text("Vale"))
    murders = k.audit("murder", "automatic-count", "Tavi", "Vale")
    result, text = k.execute("Tavi", "Vale")
    gained = k.audit("murder", "automatic-count", "Tavi", "Vale") - murders
    ok = result == "executed" and k.wait_until(lambda: k.ghost("Vale"), 5)
    k.record("P4 Tavi Executes Vale", "executed, Vale ghost, murder +1", f"{result}; murder+{gained}", ok and gained == 1)
    time.sleep(2)
    on_corpse = corpse_items("Vale")
    corpse_serials = {i[1].lower() for i in on_corpse}
    leaked = [s for s in protected_serials if s.lower() in corpse_serials]
    k.record("P5 no protected item is on the corpse", "none of the Newbied/Blessed/Nontransferable serials on the corpse",
             f"protected {len(protected_serials)}; on corpse {len(on_corpse)}; leaked {leaked}",
             bool(protected_serials) and not leaked)
    kept = [s for s in protected_serials if s in [i[1] for i in k.pack_items("Vale")]]
    k.record("P6 protected items are kept by the dead player", "all protected serials still in Vale's pack",
             f"kept {len(kept)}/{len(protected_serials)}", len(kept) == len(protected_serials))


def repeat_kill() -> None:
    k.revive("Vale")
    place_all()
    time.sleep(3)
    ko = k.knock_out("Tavi", "Vale")
    murders = k.audit("murder", "automatic-count", "Tavi", "Vale")
    result, text = k.execute("Tavi", "Vale")
    gained = k.audit("murder", "automatic-count", "Tavi", "Vale") - murders
    k.record("P7 repeat Execute of the same non-aggressor victim counts again",
             "executed, murder +1 (second count)", f"KO {ko}; {result}; {text}; murder+{gained}",
             ko and result == "executed" and gained == 1)


def main() -> int:
    k.refresh_log()
    k.adm = connect("admin")
    for name in ("Vale", "Tavi", "Elin"):
        k.C[name] = connect(name)
    for label, body in (("Setup", setup), ("Protected loot", protected_loot),
                        ("Execute and corpse", execute_and_corpse), ("Repeat kill", repeat_kill)):
        k.stage(label, body)
    failed = [r for r in k.results if not r[3]]
    print(f"\n{len(k.results) - len(failed)}/{len(k.results)} cases passed", flush=True)
    for r in failed:
        print("FAILED:", r[0], "-", r[2])
    return 1 if failed else 0


if __name__ == "__main__":
    code = main()
    sys.stdout.flush()
    os._exit(code)
