"""Live checks for pet restrictions (Beta 1 item 2) on a disposable host with featureFlags.petRestrictions on,
PetProbe.dll and TestOnlyProbe.dll loaded, and characters PetOwner BlueVic IntentVic CrimVic RedVic.

    python pet_live.py pvp        # no tamed pet attacks any player; pets still attack monsters
    python pet_live.py pvpoff     # control: flag forced off in memory, pets DO attack intent/criminal/red players
    python pet_live.py dungeon    # follow filter, tame/dismount in a dungeon, exemptions, unshrink rules
    python pet_live.py seed       # (flag forced off in memory) put a pet in a dungeon so a restart can sweep it
    python pet_live.py sweep      # after save + restart with the flag on: the seeded pet was shrunk

Exits non-zero on any failure; results go to work/pet-live/results-<phase>.json.
"""

from __future__ import annotations

import json
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

    # D8 a ridden mount is fine inside; dismounting inside shrinks it
    horse = tame(staff, "PetOwner", "Horse")
    owner.call(f"use 0x{horse.rjust(8, '0')}")
    time.sleep(2)
    go(staff, "PetOwner", DUNGEON_INSIDE)
    time.sleep(1.5)
    ridden = report(staff, horse)
    check("dungeon:mount:ridden-mount-not-in-dungeon-world", ridden["map"] == "Internal" and ridden["controlled"], str(ridden))
    staff.say(f"[TestOnlyPetDismount {owner.state['charID']}")
    time.sleep(3)
    dis = report(staff, horse)
    check("dungeon:mount:dismount-inside-shrinks-it",
          dis["map"] == "Internal" and not dis["controlled"] and dis["stabled"], str(dis))
    pack = owner_report()
    check("dungeon:mount:shrunken-item-in-pack", any(s["pet"] and s["pet"]["serial"] == horse for s in pack["shrunken"]))


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
    phases = {"pvp": phase_pvp, "pvpoff": phase_pvpoff, "dungeon": phase_dungeon, "seed": phase_seed, "sweep": phase_sweep}
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
