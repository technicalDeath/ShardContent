"""Live check of era cooking: use raw food, target a heat source (Cooking-Era-Restore-Research.md).

Needs a disposable host running the build under test, a staff session and an ordinary session whose
character was created as Advanced with Cooking and Camping (the stock Cooking starter pack: 20 raw
fish steaks, lamb legs and chicken legs). Heat sources are movable items given a heat-source graphic
by `[add item <graphic>`, because Navrey can only target things it can see by serial.

    python cooking_live.py <player-session> <staff-session>

Prints one line per case, flushes as it goes, and exits non-zero on the first failed assertion.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(WORKSPACE / ".claude" / "scripts"))

from navrey_session import connect  # noqa: E402
from staff_command import go_to, staff_target  # noqa: E402

RAW_FISH, FISH = 0x97A, 0x97B
RAW_LAMB, LAMB = 0x1609, 0x160A
RAW_CHICKEN, CHICKEN = 0x1607, 0x1608
COOK_WAIT = 10.0  # the cook timer is 5 s; allow for client refresh

HEAT = {
    "campfire": 0xDE3,
    "sandstone oven": 0x461,
    "stone oven": 0x92B,
    "fire pit": 0xFAC,
    "heating stand": 0x184A,
    "fire field": 0x398C,
    "small forge": 0xFB1,
    "large forge": 0x197A,
}
NOT_HEAT = {"anvil": 0xFB0}


def check(condition: bool, case: str, detail: str = "") -> None:
    print(f"{'PASS' if condition else 'FAIL'} {case}{': ' + detail if detail else ''}", flush=True)
    if not condition:
        sys.exit(1)


def main(player_session: str, staff_session: str) -> None:
    p = connect(player_session)
    staff = connect(staff_session)
    me = p.state["charID"]
    log = WORKSPACE / "work" / "navrey-sessions" / player_session / "cuolog"

    def lines_since(mark: int) -> list:
        return log.read_text(errors="replace").splitlines()[mark:]

    def log_mark() -> int:
        return len(log.read_text(errors="replace").splitlines())

    def count(graphic: int) -> int:
        return sum(i.amount for i in p.backpack if i.graphic == graphic)

    def stack(graphic: int):
        found = [i for i in p.backpack if i.graphic == graphic]
        check(bool(found), f"pack holds graphic {graphic:#x}")
        return found[0]

    def skill_line(name: str) -> str:
        return next((line for line in p.call("skills", timeout=8) if name in line), "")

    def make_heat(label: str, graphic: int) -> str:
        before = {i.serial for i in p.items()}
        staff_target(staff, f"[add item {graphic:#x}", me)
        check(p.wait(lambda: any(i.serial not in before and i.graphic == graphic for i in p.items()), timeout=6),
              f"staff created {label} ({graphic:#x}) at the cook's feet")
        return next(i.serial for i in p.items() if i.serial not in before and i.graphic == graphic)

    p.open_backpack(wait=4)
    time.sleep(1.0)
    go_to(staff, p)
    x, y = p.state["charPosX"], p.state["charPosY"]
    check(count(RAW_FISH) == 20 and count(RAW_LAMB) == 20 and count(RAW_CHICKEN) == 20,
          "starter cook holds 20 raw fish, lamb and chicken")

    # A Cooking skill of 100 cannot fail, so the heat-source cases isolate the target rule.
    staff_target(staff, "[SetSkill Cooking 100", me)
    print(" skill:", skill_line("Cooking"), flush=True)

    # H1-H8: every heat source cooks one raw fish steak into one fish steak.
    serials = {label: make_heat(label, graphic) for label, graphic in HEAT.items()}
    for label, heat in serials.items():
        raw_before, cooked_before = count(RAW_FISH), count(FISH)
        started = p.use_on(stack(RAW_FISH).serial, heat, timeout=5)
        check(started, f"H {label}: a target cursor opens")
        cooked = p.wait(lambda: count(FISH) > cooked_before, timeout=COOK_WAIT)
        check(cooked and count(RAW_FISH) == raw_before - 1 and count(FISH) == cooked_before + 1,
              f"H {label}: one raw fish steak became one fish steak",
              f"raw {raw_before}->{count(RAW_FISH)}, cooked {cooked_before}->{count(FISH)}")

    # N1: a tile that is not a heat source consumes nothing and does not lock the next cook.
    anvil = make_heat("anvil", NOT_HEAT["anvil"])
    raw_before, cooked_before = count(RAW_FISH), count(FISH)
    p.use_on(stack(RAW_FISH).serial, anvil, timeout=5)
    time.sleep(COOK_WAIT - 2)
    check(count(RAW_FISH) == raw_before and count(FISH) == cooked_before,
          "N1 anvil as target: nothing consumed, nothing cooked")

    # W1: a second cook during the five seconds is refused, and only the first food is used.
    mark = log_mark()
    raw_before, cooked_before = count(RAW_FISH), count(FISH)
    p.use_on(stack(RAW_FISH).serial, serials["campfire"], timeout=5)
    p.use_on(stack(RAW_FISH).serial, serials["campfire"], timeout=5)
    check(p.wait(lambda: count(FISH) > cooked_before, timeout=COOK_WAIT), "W1 the first cook completes")
    time.sleep(1.0)
    waited = any("must wait to perform another action" in line for line in lines_since(mark))
    check(waited and count(RAW_FISH) == raw_before - 1 and count(FISH) == cooked_before + 1,
          "W1 second cook refused with the wait message; one raw fish steak used",
          f"raw {raw_before}->{count(RAW_FISH)}, cooked {cooked_before}->{count(FISH)}")

    # M1/M2: lamb and chicken cook as well.
    for label, raw, cooked_graphic in (("lamb leg", RAW_LAMB, LAMB), ("chicken leg", RAW_CHICKEN, CHICKEN)):
        before = count(cooked_graphic)
        check(p.use_on(stack(raw).serial, serials["campfire"], timeout=5), f"M {label}: a target cursor opens")
        check(p.wait(lambda: count(cooked_graphic) > before, timeout=COOK_WAIT) and count(raw) == 19,
              f"M {label}: cooked on the campfire", f"raw {count(raw)}, cooked {count(cooked_graphic)}")

    # R1: raw food lying more than two tiles away cannot be cooked.
    staff_target(staff, "[add RawFishSteak", me)
    check(p.wait(lambda: any(i.graphic == RAW_FISH for i in p.items(within=0)), timeout=6), "R1 raw fish steak on the ground")
    ground = next(i for i in p.items(within=0) if i.graphic == RAW_FISH)

    def walk_away() -> tuple:
        for dx, dy in ((6, 0), (-6, 0), (0, 6), (0, -6)):
            if p.goto(x + dx, y + dy).wait() == "arrived":
                return x + dx, y + dy
        check(False, "walked six tiles from the heat source (path found)")
        return x, y

    walk_away()
    mark = log_mark()
    p.events.drain()
    p.use(ground.serial)
    time.sleep(1.5)
    reach = any("reach that" in line for line in lines_since(mark))
    check(reach, "R1 distant raw food: \"I can't reach that\" and no cook")
    p.goto(x, y).wait()

    # B1: walking more than three tiles from the heat source before the timer ends burns the food.
    raw_before, cooked_before = count(RAW_FISH), count(FISH)
    mark = log_mark()
    check(p.use_on(stack(RAW_FISH).serial, serials["campfire"], timeout=5), "B1 a target cursor opens")
    walk_away()
    time.sleep(COOK_WAIT - 3)
    burned = any("burn the food to a crisp" in line for line in lines_since(mark))
    check(burned and count(RAW_FISH) == raw_before - 1 and count(FISH) == cooked_before,
          "B1 walking away burns the food",
          f"raw {raw_before}->{count(RAW_FISH)}, cooked {cooked_before}->{count(FISH)}")
    p.goto(x, y).wait()

    # E1: the era chance is the skill itself and food can be tried at zero skill. At a base of 0 stock
    # RunUO's per-food minimum (10) would make every cook burn until the skill had grown ten points.
    staff_target(staff, "[SetSkill Cooking 0", me)
    before_line = skill_line("Cooking")
    print(" skill after [SetSkill Cooking 0:", before_line, flush=True)
    first_success = None
    attempts = 0
    for raw, cooked_graphic in ((RAW_FISH, FISH), (RAW_CHICKEN, CHICKEN), (RAW_LAMB, LAMB)):
        while count(raw) > 0 and attempts < 30 and first_success is None:
            attempts += 1
            before = count(cooked_graphic)
            if not p.use_on(stack(raw).serial, serials["campfire"], timeout=5):
                time.sleep(1.0)
                continue
            if p.wait(lambda: count(cooked_graphic) > before, timeout=COOK_WAIT):
                first_success = attempts
            else:
                time.sleep(0.5)
            print(f"  attempt {attempts}: {'cooked' if first_success else 'burned'}", flush=True)
    after_line = skill_line("Cooking")
    print(" skill after the attempts:", after_line, flush=True)
    check(first_success is not None, "E1 a cook with base skill 0 succeeds within 30 attempts",
          f"first success on attempt {first_success}")
    check(before_line != after_line, "E2 attempts at base skill 0 raise Cooking", f"{before_line!r} -> {after_line!r}")

    print("ALL PASS", flush=True)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    main(sys.argv[1], sys.argv[2])
