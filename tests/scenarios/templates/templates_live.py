"""Live checks for the era character-creation tree (Beta 1 item 4) on a disposable host named "tpl" with the shard profession file
in use and one character per case already created (work/templates-live/live1.ps1):

    one character per profession (16), created with the profession's ID 8 to 23
    TplOldWar   profession 1  (the later official Warrior, undefined on this shard: falls back to Advanced)
    TplNec 4  TplPal 5  TplSam 6  TplNin 7   forged later-era professions, naming later-era skills
    TplElfRanger   an Elf Ranger (cosmetic Elf with a tree profession)

    python templates_live.py

Reads each character's skills and stats back from its running Navrey session, and asks the admin session what the creation
screens offer. Exits non-zero on any failure; results go to work/templates-live/results.json.
"""

from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[4]
SESSIONS = WORKSPACE / "work" / "navrey-sessions"
OUT = WORKSPACE / "work" / "templates-live"
failures: list[str] = []
results: dict = {}

# session -> (skills the profession starts with, template stats STR/DEX/INT). The client names skills as its skills command prints them.
ERA = {
    "TplArcher": ({"Archery": 50, "Bowcraft": 35, "Lumberjacking": 35}, (50, 15, 15)),
    "TplBard": ({"Musicianship": 50, "Provocation": 50, "Archery": 20}, (50, 15, 15)),
    "TplRanger": ({"Archery": 50, "Tracking": 35, "Animal Taming": 35}, (50, 15, 15)),
    "TplPureMage": ({"Magery": 50, "Evaluating Intelligence": 35, "Resisting Spells": 35}, (40, 15, 25)),
    "TplWarlock": ({"Swordsmanship": 48, "Magery": 48, "Resisting Spells": 24}, (40, 15, 25)),
    "TplMaceF": ({"Mace Fighting": 50, "Parrying": 35, "Anatomy": 35}, (50, 15, 15)),
    "TplFencer": ({"Fencing": 50, "Parrying": 35, "Anatomy": 35}, (50, 15, 15)),
    "TplSword": ({"Swordsmanship": 50, "Parrying": 35, "Anatomy": 35}, (50, 15, 15)),
    "TplSmith": ({"Blacksmithy": 50, "Mining": 50, "Tinkering": 20}, (50, 15, 15)),
    "TplCarp": ({"Carpentry": 50, "Lumberjacking": 50, "Bowcraft": 20}, (50, 15, 15)),
    "TplTailor": ({"Tailoring": 50, "Tracking": 50, "Healing": 20}, (50, 15, 15)),
    "TplTinker": ({"Tinkering": 50, "Mining": 35, "Lumberjacking": 35}, (50, 15, 15)),
    "TplTamer": ({"Animal Taming": 50, "Tracking": 35, "Animal Lore": 35}, (50, 15, 15)),
    "TplFisher": ({"Fishing": 50, "Cooking": 50, "Camping": 20}, (50, 15, 15)),
    "TplProsp": ({"Mining": 48, "Lumberjacking": 48, "Hiding": 24}, (55, 15, 10)),
    "TplSorc": ({"Alchemy": 42, "Inscription": 42, "Magery": 36}, (40, 15, 25)),
    "TplElfRanger": ({"Archery": 50, "Tracking": 35, "Animal Taming": 35}, (50, 15, 15)),
}
FORGED = ["TplOldWar", "TplNec", "TplPal", "TplSam", "TplNin"]
LATER_ERA = {"Necromancy", "Chivalry", "Focus", "Bushido", "Ninjitsu", "Spellweaving", "Mysticism", "Imbuing", "Throwing"}
TREE = ("Adventurer [Archer [Archer, Bard, Ranger], Magician [Pure Mage, Warlock], Warrior [Mace Fighter, Fencer, Swordsman]]; "
        "Merchant [Craftsman [Blacksmith, Carpenter, Tailor, Tinker], Tradesman [Animal Tamer, Fisherman, Prospector, Sorcerer]]; "
        "Advanced")
LATER_ERA_GEAR = ["plate", "bone harvester", "necro", "samurai", "ninja", "bokuto", "tessen", "shuriken", "daisho", "no-dachi"]


def check(case: str, ok: bool, detail: str = "") -> None:
    results[case] = {"ok": bool(ok), "detail": detail}
    print(("PASS " if ok else "FAIL ") + case + (f"  [{detail}]" if detail else ""), flush=True)
    if not ok:
        failures.append(case)


def norm(name: str) -> str:
    """Letters only, lower case; the client's own name for Bowcraft is 'Bowcraft/Fletching'."""
    return re.sub(r"[^a-z]", "", name.lower().replace("fletching", ""))


def command(session: str, text: str) -> str:
    """Send one command to a Navrey session and return the log text it produced."""
    log = SESSIONS / session / "cuolog"
    mark = log.stat().st_size
    with open(SESSIONS / session / "cuocmd", "a", encoding="ascii") as f:
        f.write(text + "\n")
    deadline = time.time() + 20
    while time.time() < deadline:
        time.sleep(0.5)
        data = log.read_bytes()[mark:].decode("utf-8", "replace")
        if "[CMD-END]" in data:
            time.sleep(0.5)
            return log.read_bytes()[mark:].decode("utf-8", "replace")
    return log.read_bytes()[mark:].decode("utf-8", "replace")


def skills_of(session: str) -> dict[str, float]:
    text = command(session, "skills")
    found: dict[str, float] = {}
    for m in re.finditer(r"\[SKILL\]\s+(.+?)\s+([\d.]+) \(base\s+([\d.]+)\)", text):
        found[m.group(1).strip()] = float(m.group(3))
    return found


def stats_of(session: str) -> tuple[int, int, int]:
    for _ in range(10):   # the client rewrites the file continuously; a read can race the write
        try:
            state = json.loads((SESSIONS / session / "cuostate.json").read_text(encoding="utf-8"))
            return state["str"], state["dex"], state["int"]
        except (PermissionError, json.JSONDecodeError):
            time.sleep(0.3)
    raise RuntimeError(f"could not read {session} state")


def allocate(template: tuple[int, int, int]) -> tuple[int, int, int]:
    """The server's 120-point rule: 30 each, the other 30 shared in proportion to each stat's points above 10."""
    weights = [max(0, s - 10) for s in template]
    total = sum(weights)
    result = [30, 30, 30]
    assigned = 0
    for i in range(3):
        share = 30 * weights[i] // total
        result[i] += share
        assigned += share
    while assigned < 30:
        best, best_remainder = -1, -1
        for i in range(3):
            remainder = 30 * weights[i] % total
            if remainder > best_remainder and result[i] < 60:
                best, best_remainder = i, remainder
        result[best] += 1
        assigned += 1
        weights[best] = 0
    return tuple(result)  # type: ignore[return-value]


def phase_screens() -> None:
    text = command("admin", "chartemplates")
    line = next((l for l in text.splitlines() if "Adventurer" in l), "")
    offered = line[line.find("Adventurer"):].strip() if line else ""
    check("screens:tree-offered", norm(offered) == norm(TREE), offered)
    for later in ("Necromancer", "Paladin", "Samurai", "Ninja", "Field Medic", "Battle Mage"):
        check(f"screens:{later}-not-offered", norm(later) not in norm(offered))

    text = command("admin", "charskills")
    line = next((l for l in text.splitlines() if "Alchemy" in l), "")
    offered_skills = {s.strip() for s in line.split("]")[-1].split(",")}
    check("screens:advanced-has-uor-skills", {"Alchemy", "Archery", "Magery", "Swordsmanship"} <= offered_skills,
          f"{len(offered_skills)} skills")
    check("screens:advanced-has-no-later-era-skills", not (offered_skills & LATER_ERA), str(sorted(offered_skills & LATER_ERA)))


def phase_professions() -> None:
    for session, (skills, template_stats) in ERA.items():
        got = skills_of(session)
        started = {norm(name): round(base) for name, base in got.items() if base >= 4.9}
        wanted = {norm(name): value for name, value in skills.items()}
        check(f"profession:{session}:skills", started == wanted, f"starting skills: {started}")
        expected = allocate(template_stats)
        check(f"profession:{session}:stats", stats_of(session) == expected, f"stats {stats_of(session)}, expected {expected}")


def gear_of(session: str) -> str:
    command(session, "backpack")
    time.sleep(2)
    return command(session, "inv").lower()


def phase_forged() -> None:
    for session in FORGED:
        got = skills_of(session)
        later = {name for name, base in got.items() if name in LATER_ERA and base > 0}
        stats = stats_of(session)
        check(f"forged:{session}:no-later-era-skill", not later, str(sorted(later)))
        check(f"forged:{session}:stats-valid", sum(stats) == 120 and min(stats) >= 30, str(stats))
        text = gear_of(session)
        found = [g for g in LATER_ERA_GEAR if g in text]
        check(f"forged:{session}:no-later-era-gear", not found, str(found))


def phase_gear() -> None:
    # Gear follows from the skills (stock and Alpha 3 starter grants). Printed for the evidence, with two sanity checks.
    for session in ("TplArcher", "TplFencer", "TplMaceF", "TplBard", "TplSmith", "TplPureMage"):
        text = gear_of(session)
        items = [l.strip().split(" ", 1)[-1] for l in text.splitlines() if "0x" in l]
        print(f"  {session}: " + ", ".join(items[:16]), flush=True)
    archer = gear_of("TplArcher")
    check("gear:Archer-has-a-bow", "bow" in archer)
    check("gear:Archer-has-arrows", "arrow" in archer)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, fn in (("screens", phase_screens), ("professions", phase_professions), ("forged", phase_forged), ("gear", phase_gear)):
        print(f"== {name} {time.strftime('%H:%M:%S')}", flush=True)
        fn()
    (OUT / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"{len(results) - len(failures)}/{len(results)} passed", flush=True)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
