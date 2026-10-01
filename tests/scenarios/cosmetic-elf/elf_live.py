"""Live checks for cosmetic Elf creation (Beta 1 item 1) on a disposable host with the
CharacterListFlags.ML bit on and ElfProbe.dll loaded.

    python elf_live.py create     # after the characters exist: creation, parity, appearance, forged packets
    python elf_live.py death      # kill + resurrect the two Elves, report ghost/alive bodies
    python elf_live.py persist    # after save + restart: every report must equal its last one

Characters (session names): HumWar ElfWar ElfWarF HumMage ElfMage HumSmith ElfSmith HumAdv ElfAdv
ElfBad ElfMisfit GargReq. Reports come from [TestOnlyElfReport, written beside the host's Server.dll.
Exits non-zero on the first set of failures; results are written to work/elf-live/results-<phase>.json.
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

HOST = WORKSPACE / "work" / "hosts" / "elf-on"
OUT = WORKSPACE / "work" / "elf-live"
STAFF = "admin"
ALL = ["HumWar", "ElfWar", "ElfWarF", "HumMage", "ElfMage", "HumSmith", "ElfSmith", "HumAdv", "ElfAdv",
       "ElfBad", "ElfMisfit", "GargReq"]
PAIRS = [("HumWar", "ElfWar"), ("HumMage", "ElfMage"), ("HumSmith", "ElfSmith"), ("HumAdv", "ElfAdv")]
APPEARANCE_FIELDS = ("race", "female", "alive", "body", "hue", "hairItemID", "hairHue", "facialHairItemID", "facialHairHue")
PARITY_FIELDS = ("rawStr", "rawDex", "rawInt", "hitsMax", "stamMax", "manaMax", "maxWeight", "racialSkillBonus",
                 "skillsTotal", "skills", "resistances", "gold")

failures: list[str] = []
results: dict = {}


def check(case: str, ok: bool, detail: str = "") -> None:
    results[case] = {"ok": bool(ok), "detail": detail}
    print(("PASS " if ok else "FAIL ") + case + (f"  [{detail}]" if detail and not ok else ""))
    if not ok:
        failures.append(case)


def report(staff, name: str) -> dict:
    serial = connect(name).state["charID"]
    hexserial = serial[2:].upper().lstrip("0") if isinstance(serial, str) else f"{serial:X}"
    path = HOST / f"elf-report-{hexserial}.json"
    before = path.stat().st_mtime if path.exists() else 0
    staff.say(f"[TestOnlyElfReport {serial}")
    deadline = time.time() + 10
    while time.time() < deadline:
        if path.exists() and path.stat().st_mtime > before:
            break
        time.sleep(0.3)
    else:
        raise RuntimeError(f"no fresh report for {name} ({path})")
    return json.loads(path.read_text(encoding="utf-8"))


# Stock profession kits roll random shirts, pants, scrolls and tinker parts, so two Humans differ too.
# Normalise exactly those stock-random categories, then compare the rest exactly.
RANDOM_TOPS = {"Shirt", "FancyShirt", "Doublet"}
RANDOM_PANTS = {"LongPants", "ShortPants"}
TINKER_PARTS = {"Gears", "Axle", "Hinge", "Springs"}


def normalise(items):
    out: dict = {}
    for i in items or []:
        kind = i["type"]
        layer = i.get("layer")
        if kind.endswith("Scroll"):
            kind = "<random scroll>"
        elif kind in RANDOM_TOPS:
            kind, layer = "<random top>", "Top" if layer in ("Shirt", "MiddleTorso") else layer
        elif kind in RANDOM_PANTS:
            kind = "<random pants>"
        elif kind in TINKER_PARTS:
            kind = "<tinker part>"
        key = (layer, kind, i["loot"])
        out[key] = out.get(key, 0) + i.get("amount", 1)
    return sorted((str(k), v) for k, v in out.items())


def strip_hue(items):
    return normalise(items)


def appearance(r: dict) -> dict:
    return {k: r[k] for k in APPEARANCE_FIELDS}


def snapshot(staff) -> dict:
    return {n: report(staff, n) for n in ALL}


def phase_create(staff) -> None:
    reports = snapshot(staff)
    (OUT / "reports-create.json").write_text(json.dumps(reports, indent=2), encoding="utf-8")

    def expect(name, **fields):
        r = reports[name]
        bad = {k: (r[k], v) for k, v in fields.items() if r[k] != v}
        check(f"appearance:{name}", not bad, f"(actual, expected) {bad}")

    expect("ElfWar", race="Elf", female=False, alive=True, body=605, hue=0x4DE | 0x8000, hairItemID=0x2FC0,
           hairHue=0x34, facialHairItemID=0, facialHairHue=0)
    expect("ElfWarF", race="Elf", female=True, alive=True, body=606, hue=0x3DE | 0x8000, hairItemID=0x2FCC,
           hairHue=0x853, facialHairItemID=0, facialHairHue=0)
    expect("ElfMage", race="Elf", body=605, hue=0x4DE | 0x8000, hairItemID=0x2FC0)
    expect("ElfSmith", race="Elf", body=605, hue=0x4DE | 0x8000, hairItemID=0x2FC0)
    expect("ElfAdv", race="Elf", body=605, hue=0x4DE | 0x8000, hairItemID=0x2FC0)
    # forged values: a Human skin hue, Human hair and a beard must not survive on an Elf
    expect("ElfBad", race="Elf", body=605, hue=0xBF | 0x8000, hairItemID=0, hairHue=0, facialHairItemID=0,
           facialHairHue=0)
    # a female-only style on a male Elf is dropped
    expect("ElfMisfit", race="Elf", female=False, body=605, hairItemID=0)
    # Gargoyle stays unavailable (SA off): the request falls back to a stock Human
    expect("GargReq", race="Human", body=400, hairItemID=0)
    for human in ("HumWar", "HumMage", "HumSmith", "HumAdv"):
        expect(human, race="Human", body=400, alive=True)

    for human, elf in PAIRS:
        h, e = reports[human], reports[elf]
        diffs = {k: (h[k], e[k]) for k in PARITY_FIELDS if h[k] != e[k]}
        check(f"parity:{human}/{elf}:stats-skills-gold", not diffs, str(diffs))
        check(f"parity:{human}/{elf}:equipped", strip_hue(h["equipped"]) == strip_hue(e["equipped"]),
              f"{strip_hue(h['equipped'])} vs {strip_hue(e['equipped'])}")
        check(f"parity:{human}/{elf}:pack", strip_hue(h["pack"]) == strip_hue(e["pack"]),
              f"{strip_hue(h['pack'])} vs {strip_hue(e['pack'])}")

    # Elf-only entitlements are not granted: no ML racial numbers at all.
    for name in ("ElfWar", "ElfWarF", "ElfMage"):
        r = reports[name]
        check(f"era:{name}:no-ml-racial-bonus", r["racialSkillBonus"] == 0 and r["accessLevel"] == "Player")

    # What another client sees: body graphic and hue of each Elf in the observer's world file.
    observer = connect("HumWar")
    world = observer.world if hasattr(observer, "world") else {}
    (OUT / "observer-world.json").write_text(json.dumps(world, indent=2, default=str), encoding="utf-8")


def phase_death(staff) -> None:
    for name in ("ElfWar", "ElfWarF"):
        before = report(staff, name)
        target = connect(name)
        serial = target.state["charID"]
        go_to(staff, target)
        staff_target(staff, "[kill", serial)
        time.sleep(1.5)
        dead = report(staff, name)
        ghost = 607 if not before["female"] else 608
        alive = 605 if not before["female"] else 606
        check(f"death:{name}:ghost-body-and-still-elf",
              not dead["alive"] and dead["body"] == ghost and dead["race"] == "Elf",
              str(appearance(dead)))
        staff_target(staff, "[res", serial)
        time.sleep(2.0)
        back = report(staff, name)
        same = {k: (before[k], back[k]) for k in APPEARANCE_FIELDS if before[k] != back[k]}
        check(f"death:{name}:resurrected-appearance-unchanged", back["alive"] and back["body"] == alive and not same,
              str(same))
    (OUT / "reports-death.json").write_text(json.dumps(snapshot(staff), indent=2), encoding="utf-8")


def phase_persist(staff) -> None:
    last = {}
    for candidate in ("reports-death.json", "reports-create.json"):
        path = OUT / candidate
        if path.exists():
            last = json.loads(path.read_text(encoding="utf-8"))
            break
    now = snapshot(staff)
    # A character that was killed and resurrected passively gains Meditation afterwards; a Human control
    # (kill + [res on HumWar) does the same, so it is stock behaviour, not race. Their skills are not compared.
    died = {"ElfWar", "ElfWarF"}
    # HumWar and HumMage were killed and resurrected afterwards as Human controls (gear reordered), so only
    # their race and appearance are compared.
    controls = {"HumWar", "HumMage"}
    for name in ALL:
        skip = {"serial"} | ({"skills", "skillsTotal"} if name in died else set())
        keys = APPEARANCE_FIELDS if name in controls else [k for k in last[name] if k not in skip]
        diffs = {k: (last[name][k], now[name][k]) for k in keys if last[name][k] != now[name][k]}
        check(f"persist:{name}:report-unchanged-after-restart", not diffs, str(diffs))
    (OUT / "reports-persist.json").write_text(json.dumps(now, indent=2), encoding="utf-8")


def main(argv: list) -> int:
    if len(argv) != 2 or argv[1] not in ("create", "death", "persist"):
        print(__doc__)
        return 2
    OUT.mkdir(parents=True, exist_ok=True)
    staff = connect(STAFF)
    {"create": phase_create, "death": phase_death, "persist": phase_persist}[argv[1]](staff)
    (OUT / f"results-{argv[1]}.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"{len(results) - len(failures)}/{len(results)} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
