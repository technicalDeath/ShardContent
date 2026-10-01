"""Live checks for pet restrictions (Beta 1 item 2) on a disposable host with featureFlags.petRestrictions on,
PetProbe.dll and TestOnlyProbe.dll loaded, and characters PetOwner BlueVic IntentVic CrimVic RedVic.

    python pet_live.py pvp        # no tamed pet attacks any player; pets still attack monsters
    python pet_live.py pvpoff     # control: flag forced off in memory, pets DO attack intent/criminal/red players
    python pet_live.py refusal    # the owner is told when a pet refuses an Attack order against a player
    python pet_live.py mount      # one mount may be dismounted inside; it fights monsters; everything else is shrunk
    python pet_live.py tame       # real Animal Taming in a dungeon; refused up front when the pack is full
    python pet_live.py fallback   # pack full after the check: the shrunken pet lands at the owner's feet, not the bank
    python pet_live.py inside     # taming and unshrinking inside a dungeon follow the one-mount rule
    python pet_live.py mountsweep # after save + restart: the standing mount is untouched
    python pet_live.py dungeon    # follow filter, tame/dismount in a dungeon, exemptions, unshrink rules
    python pet_live.py seed       # (flag forced off in memory) put a pet in a dungeon so a restart can sweep it
    python pet_live.py sweep      # after save + restart with the flag on: the seeded pet was shrunk

Exits non-zero on any failure; results go to work/pet-live/results-<phase>.json.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(WORKSPACE / ".claude" / "scripts"))

from navrey_session import connect  # noqa: E402
from staff_command import go_to, staff_target  # noqa: E402
from uo import Event  # noqa: E402

HOST = WORKSPACE / "work" / "hosts" / "pets"
OUT = WORKSPACE / "work" / "pet-live"
DUNGEON_OUTSIDE = (4108, 430, 5)   # two tiles west of the real Deceit teleporter at (4110, 430)
DUNGEON_INSIDE = (5187, 639, 0)    # where that teleporter leads (inside Deceit)
failures: list[str] = []
results: dict = {}


def check(case: str, ok: bool, detail: str = "") -> None:
    results[case] = {"ok": bool(ok), "detail": detail}
    print(("PASS " if ok else "FAIL ") + case + (f"  [{detail}]" if detail and not ok else ""))
    if not ok:
        failures.append(case)


def hexs(serial) -> str:
    return serial[2:].upper().lstrip("0") if isinstance(serial, str) else f"{serial:X}"


def probe_json(staff, command: str, filename: str, timeout: float = 10.0) -> dict:
    path = HOST / filename
    before = path.stat().st_mtime if path.exists() else 0
    staff.say(command)
    deadline = time.time() + timeout
    while time.time() < deadline:
        if path.exists() and path.stat().st_mtime > before:
            time.sleep(0.2)
            return json.loads(path.read_text(encoding="utf-8"))
        time.sleep(0.3)
    raise RuntimeError(f"no fresh {filename} after: {command}")


def report(staff, serial_hex: str) -> dict:
    return probe_json(staff, f"[TestOnlyPetReport {serial_hex}", f"pet-report-{serial_hex}.json")


def tame(staff, owner_name: str, type_name: str) -> str:
    owner = connect(owner_name).state["charID"]
    out = probe_json(staff, f"[TestOnlyPetTame {owner} {type_name}", f"pet-tame-{hexs(owner)}.json")
    assert out["ok"], out
    return out["pet"]


def go(staff, owner_name: str, xyz, pets: bool = False) -> None:
    client = connect(owner_name)
    try:
        client.call("stop")   # a leftover goto would keep walking the character after the teleport
    except Exception:
        pass
    owner = client.state["charID"]
    staff.say(f"[TestOnlyPetGo {owner} {xyz[0]} {xyz[1]} {xyz[2]}" + (" pets" if pets else ""))
    time.sleep(1.5)


def order_attack(owner_client, target_serial: str) -> None:
    # A rejected target can leave the AI-control cursor open on the server, and a second "all kill" then
    # raises no new cursor; cancel any stale one first.
    try:
        owner_client.call("canceltarget")
    except Exception:
        pass
    time.sleep(0.5)
    owner_client.events.drain()
    owner_client.say("all kill")
    if owner_client.wait_for(Event.TARGET_REQUEST, timeout=5) is None:
        raise RuntimeError("all kill raised no target cursor")
    owner_client.target(target_serial)


def near_rat(owner_name: str) -> str | None:
    session = json.loads((WORKSPACE / "work" / "navrey-sessions" / owner_name / "cuoworld.json").read_text(encoding="utf-8"))
    for m in session["mobiles"]:
        if m["name"] == "a rat" and not m["isDead"] and m["distance"] <= 4:
            return m["serial"]
    return None


def spawn_rat(staff, owner_name: str) -> str:
    owner = connect(owner_name)
    staff_target(staff, "[add rat", owner.state["charID"])
    for _ in range(10):
        time.sleep(0.5)
        found = near_rat(owner_name)
        if found:
            return found
    raise RuntimeError("the spawned rat is not in view")


def followers_on(staff, owner_name: str, target_hex: str) -> list:
    rep = report(staff, hexs(connect(owner_name).state["charID"]))
    return [f["serial"] for f in rep["followers"] if f["combatant"] == target_hex]


def seen_notoriety(observer_name: str, subject_name: str) -> str | None:
    world = json.loads((WORKSPACE / "work" / "navrey-sessions" / observer_name / "cuoworld.json").read_text(encoding="utf-8"))
    for m in world["mobiles"]:
        if m["name"] == subject_name:
            return m["notoriety"]
    return None


def ensure_intent_on(victim_name: str, observer_name: str = "PetOwner") -> None:
    """[Intent is a toggle: flip it until the observer sees the victim as grey, and fail loudly otherwise."""
    for _ in range(3):
        time.sleep(1.5)
        if seen_notoriety(observer_name, victim_name) in ("Gray", "Grey", "CanBeAttacked"):
            return
        connect(victim_name).say("[Intent")
    time.sleep(1.5)
    if seen_notoriety(observer_name, victim_name) not in ("Gray", "Grey", "CanBeAttacked"):
        raise RuntimeError(f"{victim_name} never showed as Intent-grey ({seen_notoriety(observer_name, victim_name)})")


def clear_followers(staff, owner_name: str) -> None:
    """Server-side: dismount and delete every follower and shrunken pet (stuck pets swallow 'all kill')."""
    staff.say(f"[TestOnlyPetClear {connect(owner_name).state['charID']}")
    time.sleep(1.0)


def phase_pvp(staff) -> None:
    owner = connect("PetOwner")
    clear_followers(staff, "PetOwner")
    # Make the victims: Intent on, grey criminal, red murderer.
    ensure_intent_on("IntentVic")
    staff_target(staff, "[set Criminal true", connect("CrimVic").state["charID"])
    staff_target(staff, "[set Kills 5", connect("RedVic").state["charID"])
    time.sleep(1.0)

    def fresh_pet_order(target_serial: str, settle: float = 5.0) -> str:
        pet = tame(staff, "PetOwner", "Dog")
        time.sleep(1.0)
        order_attack(owner, target_serial)
        time.sleep(settle)
        return pet

    # Control: the same command on a monster does set a combatant.
    rat = spawn_rat(staff, "PetOwner")
    pet = fresh_pet_order(rat, settle=3.0)
    check("pvp:control-pet-attacks-a-monster", report(staff, pet)["combatant"] == hexs(rat),
          str(report(staff, pet)["combatant"]))

    for name in ("BlueVic", "IntentVic", "CrimVic", "RedVic"):
        victim = connect(name)
        go(staff, name, tuple(owner.state[k] for k in ("charPosX", "charPosY", "charPosZ")))
        vserial = victim.state["charID"]
        hits_before = victim.state.get("hits")
        if name == "CrimVic":  # the criminal flag expires after a couple of minutes; refresh it
            staff_target(staff, "[set Criminal true", vserial)
        pet = fresh_pet_order(vserial)
        attackers = followers_on(staff, "PetOwner", hexs(vserial))
        check(f"pvp:{name}:no-pet-targets-the-player", not attackers, str(attackers))
        check(f"pvp:{name}:victim-unharmed", victim.state.get("hits") == hits_before,
              f"{hits_before} -> {victim.state.get('hits')}")

    # A player who strikes a pet is not fought back.
    victim = connect("BlueVic")
    clear_followers(staff, "PetOwner")
    pet = tame(staff, "PetOwner", "Dog")
    time.sleep(1.0)
    victim.call(f"attack 0x{pet.rjust(8, '0')}")
    time.sleep(5)
    check("pvp:no-retaliation-against-a-player", report(staff, pet)["combatant"] != hexs(victim.state["charID"]),
          str(report(staff, pet)["combatant"]))


def phase_pvpoff(staff) -> None:
    """Control for phase_pvp: with the flag off, the old rules apply and these victims are attackable, so the
    'no pet targets the player' results above are caused by the flag and not by test setup."""
    owner = connect("PetOwner")
    ensure_intent_on("IntentVic")
    staff.say("[TestOnlyFlagOverride PetRestrictions false")
    time.sleep(1)
    try:
        for name in ("IntentVic", "CrimVic", "RedVic"):
            clear_followers(staff, "PetOwner")
            victim = connect(name)
            go(staff, name, tuple(owner.state[k] for k in ("charPosX", "charPosY", "charPosZ")))
            vserial = victim.state["charID"]
            hits_before = victim.state.get("hits")
            if name == "CrimVic":  # the criminal flag expires after a couple of minutes; refresh it
                staff_target(staff, "[set Criminal true", vserial)
            tame(staff, "PetOwner", "Dog")
            time.sleep(1.0)
            order_attack(owner, vserial)
            time.sleep(6)
            attackers = followers_on(staff, "PetOwner", hexs(vserial))
            hurt = (victim.state.get("hits") or 0) < (hits_before or 0)
            check(f"pvpoff:{name}:pet-DOES-attack-with-the-flag-off", bool(attackers) or hurt,
                  f"combatants={attackers} hits {hits_before}->{victim.state.get('hits')}")
    finally:
        staff.say("[TestOnlyFlagOverride PetRestrictions true")
        time.sleep(1)
        clear_followers(staff, "PetOwner")


def reset_owner(staff, owner_name: str = "PetOwner") -> None:
    """Clear followers and shrunken pets, and stand outside, so a run starts clean."""
    clear_followers(staff, owner_name)
    go(staff, owner_name, DUNGEON_OUTSIDE)


def phase_refusal(staff) -> None:
    """Needs PetOwner and BlueVic only. The refusal text reaches the owner (it is in the owner's client log),
    the pet's standing order is unchanged, and the same command on a monster produces no refusal."""
    owner = connect("PetOwner")
    log = WORKSPACE / "work" / "navrey-sessions" / "PetOwner" / "cuolog"
    text = "Your pet refuses to attack other players."
    clear_followers(staff, "PetOwner")
    victim = connect("BlueVic")
    go(staff, "BlueVic", tuple(owner.state[k] for k in ("charPosX", "charPosY", "charPosZ")))
    pets = [tame(staff, "PetOwner", os.environ.get("PET_TYPE", "Dog")) for _ in range(2)]
    time.sleep(1.0)
    before_orders = [report(staff, p)["combatant"] for p in pets]

    # The owner's own harm check stops a harmful cursor on an innocent before the pet is asked, so use a target
    # the owner may attack: a criminal grey.
    staff_target(staff, "[set Criminal true", victim.state["charID"])
    mark = log.stat().st_size
    order_attack(owner, victim.state["charID"])
    time.sleep(3)
    new = log.read_bytes()[mark:].decode("utf-8", "replace")
    check("refusal:owner-sees-the-message", text in new, new[-300:])
    check("refusal:one-message-per-pet", new.count(text) == len(pets), f"{new.count(text)} for {len(pets)} pets")
    check("refusal:no-pet-targets-the-player", not followers_on(staff, "PetOwner", hexs(victim.state["charID"])))

    clear_followers(staff, "PetOwner")
    rat = spawn_rat(staff, "PetOwner")
    pet = tame(staff, "PetOwner", os.environ.get("PET_TYPE", "Dog"))
    time.sleep(1.0)
    mark = log.stat().st_size
    order_attack(owner, rat)
    time.sleep(3)
    new = log.read_bytes()[mark:].decode("utf-8", "replace")
    check("refusal:control-no-message-for-a-monster", text not in new, new[-200:])
    check("refusal:control-pet-attacks-the-monster", report(staff, pet)["combatant"] == hexs(rat))


def phase_dungeon(staff) -> None:
    owner = connect("PetOwner")
    reset_owner(staff)
    oserial = hexs(owner.state["charID"])

    def owner_report():
        return report(staff, oserial)

    # D1 a real teleporter: a pet standing beside the owner (Follow order) is left outside.
    go(staff, "PetOwner", DUNGEON_OUTSIDE)
    time.sleep(1)
    pet1 = tame(staff, "PetOwner", "Dog")   # spawns on the owner, ordered to follow
    time.sleep(1)
    check("dungeon:teleporter:pet-starts-beside-the-owner",
          abs(report(staff, pet1)["x"] - DUNGEON_OUTSIDE[0]) <= 1 and not report(staff, pet1)["inDungeon"])
    owner.call("gotoexact 4110 430")   # onto the real Deceit teleporter tile
    for _ in range(10):
        time.sleep(1.0)
        if owner.state["charPosX"] > 5000:
            break
    time.sleep(3)
    here = owner_report()
    check("dungeon:teleporter:owner-went-in", here["inDungeon"], str((here["x"], here["y"])))
    p1 = report(staff, pet1)
    check("dungeon:teleporter:pet-stayed-outside", not p1["inDungeon"] and p1["map"] == "Felucca" and p1["controlled"],
          str(p1))

    # D2 the probe's teleporter-style move (all pets within 3 tiles) is filtered the same way.
    go(staff, "PetOwner", DUNGEON_OUTSIDE)
    pet2 = tame(staff, "PetOwner", "Dog")
    go(staff, "PetOwner", DUNGEON_INSIDE, pets=True)
    time.sleep(1.5)
    check("dungeon:teleport-pets:filtered", not report(staff, pet2)["inDungeon"], str(report(staff, pet2)))

    # D3 taming inside a dungeon: the pet is shrunk into the pack.
    clear_followers(staff, "PetOwner")
    before = owner_report()
    pet3 = tame(staff, "PetOwner", "Dog")
    time.sleep(2.5)
    after = owner_report()
    pet3_state = report(staff, pet3)
    new_items = [s for s in after["shrunken"] if s["pet"] and s["pet"]["serial"] == pet3]
    check("dungeon:tame:shrunk-into-pack", len(new_items) == 1, str(after["shrunken"]))
    check("dungeon:tame:pet-out-of-play",
          pet3_state["map"] == "Internal" and not pet3_state["controlled"] and pet3_state["stabled"],
          str(pet3_state))
    check("dungeon:tame:item-protected",
          bool(new_items) and new_items[0]["loot"] == "Blessed" and new_items[0]["nontransferable"], str(new_items))
    check("dungeon:tame:follower-slots-freed", after["followerCount"] <= before["followerCount"], f"{before['followerCount']} -> {after['followerCount']}")
    shrunk_serial = new_items[0]["serial"] if new_items else None

    # D4 unshrink refused inside a dungeon
    if shrunk_serial:
        owner.call(f"use 0x{shrunk_serial.rjust(8, '0')}")
        time.sleep(2)
        still = [s for s in owner_report()["shrunken"] if s["serial"] == shrunk_serial]
        check("dungeon:unshrink-refused-inside", len(still) == 1)

    # D6 exemptions stay: pack llama and a hireling-style follower are not shrunk
    llama = tame(staff, "PetOwner", "PackLlama")
    time.sleep(2.5)
    check("dungeon:exempt:pack-llama-stays", report(staff, llama)["inDungeon"] and report(staff, llama)["controlled"],
          str(report(staff, llama)))

    # D5 dying keeps the item (Blessed): the owner dies (outside; [res does not work in this dungeon) and still holds it
    go(staff, "PetOwner", DUNGEON_OUTSIDE)
    time.sleep(1)
    staff_target(staff, "[kill", owner.state["charID"])
    time.sleep(2)
    go(staff, "PetOwner", (633, 858, 0))   # [res does not take near Deceit; do it in town
    for _ in range(4):
        staff_target(staff, "[res", owner.state["charID"])
        time.sleep(2)
        if not owner.state.get("charGhost"):
            break
    assert not owner.state.get("charGhost"), "the owner could not be resurrected"
    go(staff, "PetOwner", DUNGEON_OUTSIDE)
    if shrunk_serial:
        kept = [s for s in owner_report()["shrunken"] if s["serial"] == shrunk_serial]
        check("dungeon:item-survives-death", len(kept) == 1)

    # D7 unshrink outside: the pet comes back under control, the item is gone
    go(staff, "PetOwner", DUNGEON_OUTSIDE)
    time.sleep(1)
    if shrunk_serial:
        owner.call(f"use 0x{shrunk_serial.rjust(8, '0')}")
        time.sleep(2)
        rep = owner_report()
        check("dungeon:unshrink-outside:item-consumed", not [s for s in rep["shrunken"] if s["serial"] == shrunk_serial])
        back = report(staff, pet3)
        check("dungeon:unshrink-outside:pet-back-under-control",
              back["controlled"] and back["master"] == oserial and back["map"] == "Felucca" and not back["stabled"],
              str(back))

    # D8 a ridden mount is not in the dungeon world (the dismount rules are phase_mount)
    horse = tame(staff, "PetOwner", "Horse")
    owner.call(f"use 0x{horse.rjust(8, '0')}")
    time.sleep(2)
    go(staff, "PetOwner", DUNGEON_INSIDE)
    time.sleep(1.5)
    ridden = report(staff, horse)
    check("dungeon:mount:ridden-mount-not-in-dungeon-world", ridden["map"] == "Internal" and ridden["controlled"], str(ridden))


def standing(r: dict) -> bool:
    return r["inDungeon"] and r["controlled"] and not r["stabled"] and r["map"] == "Felucca"


def shrunk(r: dict) -> bool:
    return r["map"] == "Internal" and not r["controlled"] and r["stabled"]


def phase_mount(staff) -> None:
    """Owner rule: ride ONE mount in, dismount inside, and it stays; it fights monsters, never players. Any other
    pet, a second mount, or a mount while the owner rides another is shrunk."""
    owner = connect("PetOwner")
    oserial = hexs(owner.state["charID"])
    reset_owner(staff)
    mount_a = tame(staff, "PetOwner", "Horse")
    owner.call(f"use 0x{mount_a.rjust(8, '0')}")          # ride it
    time.sleep(2)
    go(staff, "PetOwner", DUNGEON_INSIDE)                    # a mounted rider moves; the mount is off the map
    time.sleep(1.5)
    staff.say(f"[TestOnlyPetDismount {owner.state['charID']}")
    time.sleep(3)
    a = report(staff, mount_a)
    check("mount:lone-mount-dismounted-inside-stays", standing(a), str(a))
    check("mount:nothing-shrunk", not report(staff, oserial)["shrunken"])

    # PvE: the standing mount fights a monster inside the dungeon (a rat spawned beside the owner)
    rat = probe_json(staff, f"[TestOnlyPetSpawn {owner.state['charID']} Rat", f"pet-spawn-{oserial}.json")["serial"]
    time.sleep(2)
    order_attack(owner, "0x" + rat.rjust(8, "0"))
    time.sleep(3)
    check("mount:attacks-monsters-in-the-dungeon", report(staff, mount_a)["combatant"] == rat,
          str(report(staff, mount_a)["combatant"]))

    # Any other pet, and a second mount, are shrunk while the first stands
    dog = tame(staff, "PetOwner", "Dog")
    mount_b = tame(staff, "PetOwner", "Horse")
    time.sleep(3)
    check("mount:another-pet-shrunk", shrunk(report(staff, dog)), str(report(staff, dog)))
    check("mount:second-mount-shrunk", shrunk(report(staff, mount_b)), str(report(staff, mount_b)))
    check("mount:first-mount-still-standing", standing(report(staff, mount_a)))

    # Owner rides the standing mount again, then a mount is tamed while mounted: shrunk (already on a mount)
    owner.call(f"use 0x{mount_a.rjust(8, '0')}")
    time.sleep(2)
    mount_c = tame(staff, "PetOwner", "Horse")
    time.sleep(3)
    check("mount:mount-tamed-while-owner-mounted-shrunk", shrunk(report(staff, mount_c)), str(report(staff, mount_c)))

    # Dismount again and leave it standing for the restart check
    staff.say(f"[TestOnlyPetDismount {owner.state['charID']}")
    time.sleep(3)
    check("mount:redismount-stays", standing(report(staff, mount_a)))
    (OUT / "mount-a.json").write_text(json.dumps({"mount": mount_a, "extra": [dog, mount_b, mount_c]}))


def shrunken_item(staff, owner_hex: str, pet_hex: str):
    for item in report(staff, owner_hex)["shrunken"]:
        if item["pet"] and item["pet"]["serial"] == pet_hex:
            return item["serial"]
    return None


def release(owner, item_serial: str) -> None:
    owner.call("use 0x" + item_serial.rjust(8, "0"))
    time.sleep(2.5)


def phase_inside(staff) -> None:
    """Taming and unshrinking INSIDE a dungeon follow the one-mount rule."""
    owner = connect("PetOwner")
    oserial = hexs(owner.state["charID"])
    reset_owner(staff)
    go(staff, "PetOwner", DUNGEON_INSIDE)
    time.sleep(1)

    mount_x = tame(staff, "PetOwner", "Horse")           # tamed inside, no mount standing: it stays
    time.sleep(3)
    check("inside:lone-mount-tamed-inside-stays", standing(report(staff, mount_x)), str(report(staff, mount_x)))
    mount_y = tame(staff, "PetOwner", "Horse")           # a mount is already standing: shrunk
    dog = tame(staff, "PetOwner", "Dog")                 # not a mount: shrunk
    time.sleep(3)
    check("inside:second-mount-tamed-shrunk", shrunk(report(staff, mount_y)))
    check("inside:non-mount-tamed-shrunk", shrunk(report(staff, dog)))
    check("inside:first-mount-still-standing", standing(report(staff, mount_x)))

    item_y = shrunken_item(staff, oserial, mount_y)
    item_dog = shrunken_item(staff, oserial, dog)
    release(owner, item_y)
    check("inside:unshrink-refused-while-another-mount-stands", shrunk(report(staff, mount_y)))

    staff.say(f"[TestOnlyPetDelete {mount_x}")               # now no mount is standing
    time.sleep(1.5)
    release(owner, item_y)
    y = report(staff, mount_y)
    check("inside:unshrink-mount-allowed-when-none-stands", standing(y), str(y))
    check("inside:unshrink-consumed-the-item", shrunken_item(staff, oserial, mount_y) is None)

    release(owner, item_dog)
    check("inside:unshrink-non-mount-still-refused", shrunk(report(staff, dog)))

    # while the owner rides, a shrunken mount cannot be released in the dungeon
    mount_z = tame(staff, "PetOwner", "Horse")           # mount_y stands, so z is shrunk
    time.sleep(3)
    item_z = shrunken_item(staff, oserial, mount_z)
    owner.call(f"use 0x{mount_y.rjust(8, '0')}")          # ride y; it leaves the world
    time.sleep(2)
    release(owner, item_z)
    check("inside:unshrink-refused-while-owner-rides", shrunk(report(staff, mount_z)))
    staff.say(f"[TestOnlyPetDismount {owner.state['charID']}")
    time.sleep(3)
    check("inside:dismounted-mount-stays-again", standing(report(staff, mount_y)))


def wild_spawn(staff, owner_name: str, type_name: str) -> str:
    owner = connect(owner_name)
    return probe_json(staff, f"[TestOnlyPetSpawn {owner.state['charID']} {type_name}",
                      f"pet-spawn-{hexs(owner.state['charID'])}.json")["serial"]


def real_tame(owner, staff, wild_hex: str, wait: float = 12.0) -> None:
    owner.call("useskill animal taming")   # the call returns after the cursor is already open
    time.sleep(0.5)
    owner.target("0x" + wild_hex.rjust(8, "0"))
    time.sleep(wait)


def phase_tame(staff) -> None:
    """Real Animal Taming inside a dungeon: refused up front when the shrunken pet would not fit in the pack."""
    owner = connect("PetOwner")
    oserial = hexs(owner.state["charID"])
    log = WORKSPACE / "work" / "navrey-sessions" / "PetOwner" / "cuolog"
    text = "You need room in your backpack for a shrunken pet"
    reset_owner(staff)
    staff.say(f"[TestOnlyPetSkill {owner.state['charID']} AnimalTaming 100")
    staff.say(f"[TestOnlyPetFillPack {owner.state['charID']} clear")
    go(staff, "PetOwner", DUNGEON_INSIDE)
    time.sleep(1)

    # 1. real tame of a lone mount, nothing standing: succeeds and stays standing (no pack room needed)
    staff.say(f"[TestOnlyPetFillPack {owner.state['charID']}")      # pack completely full
    time.sleep(1)
    horse = wild_spawn(staff, "PetOwner", "Horse")
    time.sleep(1)
    mark = log.stat().st_size
    real_tame(owner, staff, horse)
    new = log.read_bytes()[mark:].decode("utf-8", "replace")
    st = report(staff, horse)
    check("tame:full-pack-lone-mount-tames-and-stands", standing(st) and text not in new, f"{st['controlled']} {st['map']} | {new[-200:]}")

    # 2. a full pack and a mount that would be shrunk (one already stands): refused before the attempt
    horse2 = wild_spawn(staff, "PetOwner", "Horse")
    time.sleep(1)
    mark = log.stat().st_size
    real_tame(owner, staff, horse2, wait=4)
    new = log.read_bytes()[mark:].decode("utf-8", "replace")
    st2 = report(staff, horse2)
    check("tame:full-pack-second-mount-refused-up-front", text in new and not st2["controlled"], new[-200:])

    # 3. a full pack and a non-mount: refused before the attempt
    dog = wild_spawn(staff, "PetOwner", "Dog")
    time.sleep(1)
    mark = log.stat().st_size
    real_tame(owner, staff, dog, wait=4)
    new = log.read_bytes()[mark:].decode("utf-8", "replace")
    check("tame:full-pack-non-mount-refused-up-front", text in new and not report(staff, dog)["controlled"], new[-200:])

    # 4. with room in the pack the same non-mount is tamed and then shrunk
    staff.say(f"[TestOnlyPetFillPack {owner.state['charID']} clear")
    time.sleep(1)
    dog = wild_spawn(staff, "PetOwner", "Dog")   # a fresh one: the first has wandered out of range
    for _ in range(4):   # a tame attempt can fail on its roll
        real_tame(owner, staff, dog)
        st = report(staff, dog)
        if st["controlled"] or shrunk(st):
            break
    check("tame:room-in-pack-non-mount-tamed-then-shrunk", shrunk(st) and shrunken_item(staff, oserial, dog) is not None, str(st))
    staff.say(f"[TestOnlyPetFillPack {owner.state['charID']} clear")


def phase_fallback(staff) -> None:
    """The shrink fallback when the pack is full (the up-front check passed, then the pack filled): at the owner's
    feet, never the bank, and only the owner can lift it. The probe tame skips the up-front check."""
    owner = connect("PetOwner")
    oserial = hexs(owner.state["charID"])
    reset_owner(staff)
    go(staff, "PetOwner", DUNGEON_INSIDE)
    staff.say(f"[TestOnlyPetFillPack {owner.state['charID']}")
    time.sleep(1)
    dog = tame(staff, "PetOwner", "Dog")
    time.sleep(3)
    rep = report(staff, oserial)
    check("fallback:pet-shrunk", shrunk(report(staff, dog)))
    check("fallback:item-at-the-feet", len(rep["groundShrunken"]) == 1, str(rep["groundShrunken"]))
    check("fallback:nothing-in-the-bank", rep["bankShrunken"] == 0, str(rep["bankShrunken"]))
    check("fallback:not-in-the-pack", not rep["shrunken"])
    staff.say(f"[TestOnlyPetFillPack {owner.state['charID']} clear")


def phase_mountsweep(staff) -> None:
    """After save + restart: the lone standing mount is left alone by the boot sweep; the shrunken ones stay shrunk."""
    saved = json.loads((OUT / "mount-a.json").read_text())
    check("mountsweep:standing-mount-survives-restart", standing(report(staff, saved["mount"])),
          str(report(staff, saved["mount"])))
    check("mountsweep:shrunken-extras-still-shrunk", all(shrunk(report(staff, p)) for p in saved["extra"]))


def phase_seed(staff) -> None:
    """Control plus seeding: with the flag off in memory a following pet DOES go through the real Deceit
    teleporter, and stays in the dungeon. Save and restart with the flag on to test the boot sweep."""
    owner = connect("PetOwner")
    staff.say("[TestOnlyFlagOverride PetRestrictions false")
    time.sleep(1)
    reset_owner(staff)
    go(staff, "PetOwner", DUNGEON_OUTSIDE)
    pet = tame(staff, "PetOwner", "Dog")
    time.sleep(1)
    owner.call("gotoexact 4110 430")
    for _ in range(10):
        time.sleep(1.0)
        if owner.state["charPosX"] > 5000:
            break
    time.sleep(3)
    state = report(staff, pet)
    check("seed:control:pet-follows-through-the-real-teleporter-with-the-flag-off",
          state["inDungeon"] and state["controlled"], str(state))
    (OUT / "seeded-pet.json").write_text(json.dumps({"pet": pet}))


def phase_sweep(staff) -> None:
    pet = json.loads((OUT / "seeded-pet.json").read_text())["pet"]
    state = report(staff, pet)
    check("sweep:seeded-pet-shrunk-at-boot",
          state["map"] == "Internal" and not state["controlled"] and state["stabled"], str(state))
    owner = report(staff, hexs(connect("PetOwner").state["charID"]))
    check("sweep:item-in-owners-pack", any(s["pet"] and s["pet"]["serial"] == pet for s in owner["shrunken"]),
          str(owner["shrunken"]))


def main(argv: list) -> int:
    phases = {"pvp": phase_pvp, "pvpoff": phase_pvpoff, "mount": phase_mount, "inside": phase_inside, "fallback": phase_fallback, "tame": phase_tame, "mountsweep": phase_mountsweep, "refusal": phase_refusal, "dungeon": phase_dungeon, "seed": phase_seed, "sweep": phase_sweep}
    if len(argv) != 2 or argv[1] not in phases:
        print(__doc__)
        return 2
    OUT.mkdir(parents=True, exist_ok=True)
    staff = connect("admin")
    phases[argv[1]](staff)
    (OUT / f"results-{argv[1]}.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"{len(results) - len(failures)}/{len(results)} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
