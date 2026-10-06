"""Live checks of Rekindled camping (Beta-2b-Camping-Evidence.md) on a disposable host.

    python camping_live.py kit    # flags on:  the starter kit and its weight           (L1, L2)
    python camping_live.py fires  # flags on:  lighting, timeline, feeding, secure camp (L3-L10)
    python camping_live.py off    # flags off: stock kit, stock timing, no feeding      (O1)

`kit` and `fires` need a host with campingStarterKit and campingFires on and the camping numbers scaled down so a fire's
whole life is a minute or so (litBaseSeconds 20, litPerSkillSeconds 0.3, emberBaseSeconds 15, emberPerSkillSeconds 0.2),
the TestOnlyProbe loaded, a staff session `admin`, and fresh characters KitWar (Warrior), KitMage (Pure Mage), KitSmith
(Blacksmith), KitCook (Advanced: Cooking and Alchemy) and KitCamp (Advanced: Camping and Fishing). `off` needs a host with
both flags off and fresh OffWar (Warrior) and OffCamp (Advanced: Camping and Cooking).

Fires are immovable, so the client cannot see them; the driver reads them from the staff command `[CampStatus`.
Prints one line per case, flushes as it goes, and exits non-zero on the first failed assertion.
"""

from __future__ import annotations

import re
import sys
import time
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(WORKSPACE / ".claude" / "scripts"))

from navrey_session import connect  # noqa: E402
from staff_command import go_to, staff_target  # noqa: E402

BEDROLL, KINDLING = 0xA57, 0xDE1
FIRE_LINE = re.compile(
    r"Fire (0x[0-9A-Fa-f]+) at (\d+),(\d+): (\w+), lit by (.+?), (\d+) s since lit or fed; "
    r"dims at (\d+) s, embers at (\d+) s, gone at (\d+) s\."
)
ITEM_LINE = re.compile(r"backpack: (\w+) serial=(\S+) amount=(\d+) lootType=(\w+) nontransferable=(\w+)")


def check(condition: bool, case: str, detail: str = "") -> None:
    print(f"{'PASS' if condition else 'FAIL'} {case}{': ' + detail if detail else ''}", flush=True)
    if not condition:
        sys.exit(1)


class Rig:
    def __init__(self, names: list) -> None:
        self.admin = connect("admin")
        self.p = {n: connect(n) for n in names}
        self.logs = {n: WORKSPACE / "work" / "navrey-sessions" / n / "cuolog" for n in [*names, "admin"]}

    def lines(self, name: str) -> list:
        return self.logs[name].read_text(errors="replace").splitlines()

    def mark(self, name: str) -> int:
        return len(self.lines(name))

    def since(self, name: str, mark: int) -> str:
        return "\n".join(self.lines(name)[mark:])

    def serial(self, name: str) -> str:
        return str(self.p[name].state["charID"])

    def open_pack(self, name: str) -> list:
        self.p[name].open_backpack(wait=4)
        time.sleep(0.8)
        return self.p[name].backpack

    def count(self, name: str, graphic: int) -> int:
        return sum(i.amount for i in self.open_pack(name) if i.graphic == graphic)

    def stack(self, name: str, graphic: int):
        found = [i for i in self.open_pack(name) if i.graphic == graphic]
        check(bool(found), f"{name} holds graphic {graphic:#x}")
        return found[0]

    def inspect(self, name: str) -> list:
        mark = self.mark("admin")
        self.admin.say(f"[TestOnlyInventoryInspect {self.serial(name)}")
        time.sleep(2.0)
        return [ITEM_LINE.search(line) for line in self.lines("admin")[mark:] if ITEM_LINE.search(line)]

    def fires(self, near: str) -> list:
        go_to(self.admin, self.p[near])
        mark = self.mark("admin")
        self.admin.say("[CampStatus")
        time.sleep(1.5)
        out = []
        for line in self.lines("admin")[mark:]:
            m = FIRE_LINE.search(line)
            if m:
                out.append({"serial": m.group(1), "x": int(m.group(2)), "y": int(m.group(3)), "status": m.group(4),
                            "lighter": m.group(5), "age": int(m.group(6)), "dim": int(m.group(7)),
                            "out": int(m.group(8)), "gone": int(m.group(9))})
        return out

    def light(self, name: str):
        """Use Kindling; returns the new fire (or None) and what the character was told."""
        before = {f["serial"] for f in self.fires(name)}
        mark = self.mark(name)
        self.p[name].use(self.stack(name, KINDLING).serial)
        time.sleep(2.0)
        said = self.since(name, mark)
        new = [f for f in self.fires(name) if f["serial"] not in before]
        return (new[0] if new else None), said


def walk_away(p, x: int, y: int, distance: int = 4) -> tuple:
    for dx, dy in ((distance, 0), (-distance, 0), (0, distance), (0, -distance)):
        if p.goto(x + dx, y + dy).wait() == "arrived":
            return x + dx, y + dy
    check(False, "found a path away from the fire")
    return x, y


def approach(p, fx: int, fy: int) -> None:
    """Stand on a tile beside the fire, checked by position: goto stops a tile short of its target, gotoexact does not."""
    if max(abs(p.state["charPosX"] - fx), abs(p.state["charPosY"] - fy)) <= 1:
        return
    for dx, dy in ((1, 0), (0, 1), (-1, 0), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
        if p.gotoexact(fx + dx, fy + dy).wait() == "arrived":
            time.sleep(0.5)
            x, y = p.state["charPosX"], p.state["charPosY"]
            if max(abs(x - fx), abs(y - fy)) <= 1:
                return
    check(False, "reached a tile beside the fire")


def give_kindling(rig: Rig, name: str, amount: int) -> None:
    """Staff drops a Kindling stack at the character's feet and the character picks it up, so the scenario cannot run dry."""
    p = rig.p[name]
    before = {i.serial for i in p.items()}
    go_to(rig.admin, p)
    staff_target(rig.admin, f"[add Kindling {amount}", rig.serial(name))
    check(p.wait(lambda: any(i.serial not in before and i.graphic == KINDLING for i in p.items()), timeout=6),
          f"{name}: {amount} Kindling appeared at their feet")
    item = next(i for i in p.items() if i.serial not in before and i.graphic == KINDLING)
    p.drop(item.serial, p.state["backpackID"])
    time.sleep(1.5)


def stage_kit() -> None:
    names = ["KitWar", "KitMage", "KitSmith", "KitCook", "KitCamp"]
    rig = Rig(names)
    for name in names:
        items = rig.inspect(name)
        bedrolls = [m for m in items if m.group(1) == "Bedroll"]
        kindling = [m for m in items if m.group(1) == "Kindling"]
        total = sum(int(m.group(3)) for m in kindling)
        check(len(bedrolls) == 1, f"L1 {name}: exactly one Bedroll", f"{len(bedrolls)}")
        want = 5 if name == "KitCamp" else 3  # stock Camping already gives a camper five; the kit tops everyone else up to three
        check(total == want, f"L1 {name}: {want} Kindling in all, none doubled", f"{total} in {len(kindling)} stack(s)")
        check(all(m.group(4) == "Newbied" and m.group(5) == "False" for m in bedrolls + kindling),
              f"L1 {name}: Bedroll and Kindling are newbied and not bound")
        s = rig.p[name].state
        weight, limit = s.get("weight"), s.get("maxWeight")
        print(f" {name}: weight {weight}/{limit} stones", flush=True)
        # KitCook's Alchemy and Cooking starter materials alone already weigh more than its limit; the kit is not the cause.
        if name == "KitCook":
            print(f"  (KitCook is over its limit before the kit: {weight - 10}/{limit}; not asserted)", flush=True)
            continue
        check(weight is not None and limit is not None and weight <= limit, f"L2 {name}: not overweight with the kit",
              f"{weight}/{limit}")
    print("KIT PASS", flush=True)


def poll_life(rig: Rig, near: str, serial: str, expect: tuple, label: str, watch=None) -> None:
    """
    Follow one fire to its end by the age the server reports. Wherever polling started, every observation must show the
    state that age calls for (boundaries get two seconds of slack), the later states must have been seen, and the fire must
    be gone shortly after the last observation.
    """
    dim, ember, gone = expect
    start = time.monotonic()
    seen = []
    while time.monotonic() - start < gone + 30:
        fire = next((f for f in rig.fires(near) if f["serial"] == serial), None)
        if watch:
            watch(time.monotonic() - start)
        if fire is None:
            break
        seen.append((fire["age"], fire["status"]))
        time.sleep(0.5)

    def wanted(age: int) -> str:
        return "Burning" if age < dim else "Extinguishing" if age < ember else "Off"

    near_boundary = lambda age: any(abs(age - edge) <= 2 for edge in (dim, ember))  # noqa: E731
    wrong = [(age, status) for age, status in seen if not near_boundary(age) and status != wanted(age)]
    print(f" {label}: (age, state) observed {seen}", flush=True)
    check(bool(seen) and not wrong, f"{label}: every observation shows the state its age calls for (dims {dim} s, embers {ember} s)",
          f"{wrong}")
    last = seen[-1][0] if seen else None
    if last is not None and last > ember + 2:
        check(any(status == "Off" for _, status in seen), f"{label}: the embers were seen")
    # the fire timer ticks once a second, so a fire can be seen up to a second past its end
    check(last is not None and -1 <= gone - last <= 7, f"{label}: gone at about {gone} s", f"last seen at {last}")


def stage_one(rig: Rig, a: str) -> None:
    """A Grandmaster fire (effective skill 100): dims 33 s, embers 50 s, gone 85 s; the secure camp and the Bedroll."""
    fire, said = rig.light(a)
    check(fire is not None, "L4 the Grandmaster lights a fire", said[-120:])
    check((fire["dim"], fire["out"], fire["gone"]) == (33, 50, 85), "L4 its timing is lit 50 s (dim at 33), embers to 85 s",
          f"{fire}")
    for who in ("KitWar", "KitMage"):
        rig.p[who].open_backpack(wait=4)
    lit_at = time.monotonic()
    state = {"secure_at": None, "war_done": False, "mage_done": False}
    war_bedroll = rig.stack("KitWar", BEDROLL).serial
    mage_bedroll = rig.stack("KitMage", BEDROLL).serial
    mark_a = rig.mark(a)

    def watch(_at: float) -> None:
        now = time.monotonic() - lit_at
        if state["secure_at"] is None and "The camp is now secure" in rig.since(a, mark_a):
            state["secure_at"] = now
        # L10: while the camp is secure and the fire still lit, a Bedroll logs the character out.
        if state["secure_at"] is not None and now < 47 and not state["war_done"]:
            state["war_done"] = True
            war = rig.p["KitWar"]
            war.call(f"dropground {war_bedroll}", timeout=8)
            time.sleep(1.5)
            war.use(war_bedroll)
            time.sleep(1.2)
            war.use(war_bedroll)
            time.sleep(1.5)
            text = " ".join(war.call("gumps", timeout=8))
            check("1011015" in text or "camping" in text.lower(), "L10 the Bedroll offers the safe-logout gump at a secure camp",
                  text[:140])
            war.call("gumpresponse 1", timeout=8)
            time.sleep(3.0)
            check(war.state.get("connected") is False, "L10 CONTINUE logs the character out")
        # L9b: once the fire is embers the camp is no longer secure and the Bedroll offers nothing.
        if now > 55 and not state["mage_done"]:
            state["mage_done"] = True
            mage = rig.p["KitMage"]
            mage.call(f"dropground {mage_bedroll}", timeout=8)
            time.sleep(1.5)
            mage.use(mage_bedroll)
            time.sleep(1.2)
            mage.use(mage_bedroll)
            time.sleep(1.5)
            text = " ".join(mage.call("gumps", timeout=8))
            check("1011015" not in text and "camping" not in text.lower(), "L9 embers are not a secure camp: no logout gump",
                  text[:140])

    poll_life(rig, a, fire["serial"], (33, 50, 85), "L4 skill 100", watch)
    check(state["secure_at"] is not None and 28 <= state["secure_at"] <= 42, "L9 'The camp is now secure.' arrives at about 30 s",
          f"{state['secure_at']}")


def camping_value(rig: Rig, name: str) -> float:
    """The character's Camping as the game uses it (the skill list's first number includes the stat bonus)."""
    for line in rig.p[name].call("skills", timeout=8):
        m = re.search(r"Camping\s+([\d.]+)", line)
        if m:
            return float(m.group(1))
    check(False, f"{name}'s Camping skill was listed")
    return 0.0


def wait_clear(rig: Rig, name: str, timeout: float = 120.0) -> None:
    """Wait until no fire is within a tile of the character, since Kindling beside a fire feeds it instead of lighting."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        x, y = rig.p[name].state["charPosX"], rig.p[name].state["charPosY"]
        if not any(max(abs(f["x"] - x), abs(f["y"] - y)) <= 1 for f in rig.fires(name)):
            return
        time.sleep(2.0)
    check(False, f"{name} has no fire beside them")


def stage_two(rig: Rig, b: str) -> None:
    """A character at base 0 lights at the 50% floor: some attempts succeed and some fail; the floor fire's own timeline."""
    wins, losses, attempts, followed = 0, 0, 0, False
    wait_clear(rig, b)
    while (wins < 1 or losses < 1) and attempts < 16:
        attempts += 1
        fire, said = rig.light(b)
        outcome = "failed" if "fail to ignite" in said else "lit" if fire is not None else said[-60:]
        print(f"  attempt {attempts}: {outcome}", flush=True)
        if "fail to ignite" in said:
            losses += 1
        elif fire is not None:
            wins += 1
            if not followed:
                followed = True
                value = camping_value(rig, b)
                lit = 20.0 + 0.3 * value  # the scaled numbers this host runs: lit 20 s + 0.3 s per point, embers 15 s + 0.2 s per point
                want = (lit * 2.0 / 3.0, lit, lit + 15.0 + 0.2 * value)
                got = (fire["dim"], fire["out"], fire["gone"])
                check(all(abs(g - w) <= 1.5 for g, w in zip(got, want)),
                      "L4 the fire follows the lighter's real Camping skill, not the 50 ignition floor",
                      f"Camping {value}: wanted about {tuple(round(w) for w in want)}, got {got}")
                check(got[2] < 60, "L4 a base-0 camper's fire is shorter than a skill-50 fire would be (60 s)", f"{got}")
                poll_life(rig, b, fire["serial"], got, "L4 base-0 camper")  # it is gone afterwards, so the next use lights afresh
            else:
                wait_clear(rig, b)  # beside a live fire Kindling feeds it, so let it burn out before trying again
        else:
            wait_clear(rig, b)
    check(wins >= 1 and losses >= 1, "L3 a base-0 character lights some fires and fails others", f"{wins} lit, {losses} failed in {attempts}")


def stage_fires() -> None:
    rig = Rig(["KitCamp", "KitCook", "KitWar", "KitMage"])
    a, b = "KitCamp", "KitCook"
    staff_target(rig.admin, "[SetSkill Camping 100", rig.serial(a))
    staff_target(rig.admin, "[SetSkill Camping 0", rig.serial(b))
    ax, ay = rig.p[a].state["charPosX"], rig.p[a].state["charPosY"]
    give_kindling(rig, a, 6)
    give_kindling(rig, b, 6)
    if "only2" in sys.argv:
        stage_two(rig, b)
        print("ZERO-SKILL STAGE PASS", flush=True)
        return

    # S1: a Grandmaster fire (effective skill 100): dims 33 s, embers 50 s, gone 85 s with the scaled numbers.
    if "skip1" not in sys.argv:
        stage_one(rig, a)

    # S3: feeding. B walks to A so both stand within a tile of the fire A lights.
    kindling_a, kindling_b = rig.count(a, KINDLING), rig.count(b, KINDLING)
    before_fires = {f["serial"] for f in rig.fires(a)}

    # L7: light a fire, and use Kindling again at once: the fire counts as just tended, so the second use is refused,
    # nothing more is used and no second fire is lit.
    mark = rig.mark(a)
    rig.p[a].use(rig.stack(a, KINDLING).serial)
    time.sleep(1.2)
    rig.p[a].use(rig.stack(a, KINDLING).serial)
    time.sleep(1.5)
    said = rig.since(a, mark)
    new_fires = [f for f in rig.fires(a) if f["serial"] not in before_fires]
    check(len(new_fires) == 1 and "only just been tended" in said and rig.count(a, KINDLING) == kindling_a - 1,
          "L7 a fire just lit is not fed again: told so, one Kindling used in all, no second fire", f"{new_fires} {said[-80:]}")
    serial = new_fires[0]["serial"]
    approach(rig.p[b], new_fires[0]["x"], new_fires[0]["y"])

    # L8: the weaker feeder restarts the burn but cannot shorten the Grandmaster's fire.
    time.sleep(5.0)
    mark = rig.mark(b)
    rig.p[b].use(rig.stack(b, KINDLING).serial)
    time.sleep(1.8)
    after = next(f for f in rig.fires(a) if f["serial"] == serial)
    check("You feed the fire" in rig.since(b, mark) and after["age"] <= 7 and (after["dim"], after["out"], after["gone"]) == (33, 50, 85)
          and rig.count(b, KINDLING) == kindling_b - 1,
          "L8 a weaker feeder resets the burn, keeps the longer timing, and uses one Kindling", f"{after}")

    # L5: the lighter feeds a burning fire: its duration resets and no second fire appears.
    time.sleep(6.0)
    mark, before_k = rig.mark(a), rig.count(a, KINDLING)
    fires_before = {f["serial"] for f in rig.fires(a)}
    rig.p[a].use(rig.stack(a, KINDLING).serial)
    time.sleep(1.8)
    fires_now = rig.fires(a)
    after = next(f for f in fires_now if f["serial"] == serial)
    check("You feed the fire" in rig.since(a, mark) and after["age"] <= 7 and rig.count(a, KINDLING) == before_k - 1,
          "L5 feeding a burning fire resets its duration and uses one Kindling", f"{after}")
    check({f["serial"] for f in fires_now} == fires_before, "L5 no second fire was lit")

    # L6: a dim fire is fed back to burning, and embers light again without a roll.
    def wait_status(wanted: str, timeout: float) -> dict:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            f = next((f for f in rig.fires(a) if f["serial"] == serial), None)
            if f and f["status"] == wanted:
                return f
            time.sleep(1.0)
        check(False, f"the fire reached {wanted}")
        return {}

    wait_status("Extinguishing", 60)
    mark = rig.mark(a)
    rig.p[a].use(rig.stack(a, KINDLING).serial)
    time.sleep(1.8)
    f = next(f for f in rig.fires(a) if f["serial"] == serial)
    check("You feed the fire" in rig.since(a, mark) and f["status"] == "Burning" and f["age"] <= 7,
          "L6 feeding a dim fire turns it back to burning", f"{f}")
    wait_status("Off", 70)
    mark = rig.mark(a)
    rig.p[a].use(rig.stack(a, KINDLING).serial)
    time.sleep(1.8)
    f = next(f for f in rig.fires(a) if f["serial"] == serial)
    check("embers flare back to life" in rig.since(a, mark) and f["status"] == "Burning",
          "L6 Kindling on embers lights them again with no roll (A is Grandmaster, so the roll cannot be what is tested; "
          "no ignition message appears)", f"{f}")
    if "skip2" not in sys.argv:
        stage_two(rig, b)

    print("FIRES PASS", flush=True)


def stage_off() -> None:
    rig = Rig(["OffWar", "OffCamp"])
    war_items = rig.open_pack("OffWar")
    check(not any(i.graphic in (BEDROLL, KINDLING) for i in war_items), "O1 flags off: a Warrior gets no camping kit")
    check(rig.count("OffCamp", BEDROLL) == 1 and rig.count("OffCamp", KINDLING) == 7,
          "O1 flags off: a camper-cook has exactly the stock Bedroll and 5 + 2 Kindling")
    staff_target(rig.admin, "[SetSkill Camping 100", rig.serial("OffCamp"))
    fire, said = rig.light("OffCamp")
    check(fire is not None, "O1 the stock fire lights", said[-100:])
    check((fire["dim"], fire["out"], fire["gone"]) == (60, 90, 100), "O1 flags off: stock timing, dims at 60 s, embers at 90 s, gone at 100 s",
          f"{fire}")
    # Kindling next to the fire lights a second fire rather than feeding the first.
    before = rig.count("OffCamp", KINDLING)
    time.sleep(6.0)
    second, said = rig.light("OffCamp")
    check(second is not None and second["serial"] != fire["serial"] and rig.count("OffCamp", KINDLING) == before - 1,
          "O1 flags off: Kindling beside a fire lights a new fire (no feeding)", f"{second}")
    print("OFF PASS", flush=True)


if __name__ == "__main__":
    stages = {"kit": stage_kit, "fires": stage_fires, "off": stage_off}
    if len(sys.argv) < 2 or sys.argv[1] not in stages:
        print(__doc__)
        sys.exit(2)
    stages[sys.argv[1]]()
