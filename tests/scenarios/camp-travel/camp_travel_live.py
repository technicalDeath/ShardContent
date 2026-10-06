"""Live checks of camp travel and the Hot Zone travel warning (docs/Beta-2b-Camp-Travel-Evidence.md) on a disposable host.

    python camp_travel_live.py camp    # travel, refusals, capacity, pets, cancels, lighter notices   (L1-L5, L7)
    python camp_travel_live.py hot     # Hot Zone camps, the warning, the checkbox                      (L8)
    python camp_travel_live.py warn    # Recall, gates and public moongates into a Hot Zone             (L9)
    python camp_travel_live.py off     # flags overridden off: nothing changes                          (L6)

Needs a host built by work/camp-travel/host.ps1 (flags campingFires, campingTravel and hotZoneTravelWarning on; campTravel
secureSeconds 8 and channelSeconds 3; camping lit 60 s + 1 s per skill point, embers 30 s + 0.5 s per point), the
TestOnlyProbe and CampTravelProbe loaded, a staff session `admin`, and characters CtLight, CtTrav and CtThird (all Mace
Fighters, 13). The probe writes campprobe-<hex>.json beside the host's Server.dll; the driver reads that, the clients'
journals and the gumps the clients receive. Prints one line per case, flushes as it goes, exits non-zero on the first failure.
"""

from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(WORKSPACE / ".claude" / "scripts"))

from navrey_session import connect  # noqa: E402

HOST = WORKSPACE / "work" / "hosts" / "camp-travel"
ORIGIN = (633, 858)              # far from the camp, outdoors, not Hot (where the characters start)
CAMP = (1393, 1715)              # Britain
HOT = (2711, 2234)               # Buccaneer's Den, inside the Buccaneer's Den island Hot Zone
HOT_FAR = (2720, 2243)           # another place in the same Hot Zone
OUT = (1394, 1716)               # open ground beside the camp, outside any Hot Zone (nobody stands there)
DUNGEON = (5137, 650)            # Deceit, a Felucca dungeon
KINDLING, SCROLL_RECALL = 0xDE1, 0x1F4C
RUNES = (0x1F14, 0x1F15, 0x1F16, 0x1F17)
NAMES = ("CtLight", "CtTrav", "CtThird")
HOT_WARNING = "Hot Zone"
CHECKBOX = "Do not show me this warning again when traveling"


def check(condition: bool, case: str, detail: str = "") -> None:
    print(f"{'PASS' if condition else 'FAIL'} {case}{': ' + detail if detail else ''}", flush=True)
    if not condition:
        sys.exit(1)


class Rig:
    def __init__(self) -> None:
        self.admin = connect("admin")
        self.p = {n: connect(n) for n in NAMES}
        self.logs = {n: WORKSPACE / "work" / "navrey-sessions" / n / "cuolog" for n in (*NAMES, "admin")}

    # ---- journals
    def lines(self, name: str) -> list:
        return self.logs[name].read_text(errors="replace").splitlines()

    def mark(self, name: str) -> int:
        return len(self.lines(name))

    def since(self, name: str, mark: int) -> str:
        return "\n".join(self.lines(name)[mark:])

    def said(self, name: str, mark: int, text: str, timeout: float = 6.0) -> bool:
        """Wait until the journal after `mark` contains `text`."""
        end = time.time() + timeout
        while time.time() < end:
            if text in self.since(name, mark):
                return True
            time.sleep(0.25)
        return text in self.since(name, mark)

    def silent(self, name: str, mark: int, text: str, seconds: float = 4.0) -> bool:
        time.sleep(seconds)
        return text not in self.since(name, mark)

    # ---- the probe
    def hexid(self, name: str) -> str:
        return str(self.p[name].state["charID"])

    def probe(self, name: str, *args) -> str:
        mark = self.mark("admin")
        verb = str(args[0])
        self.admin.say(f"[TestOnlyCamp {self.hexid(name)} " + " ".join(str(a) for a in args))
        end = time.time() + 6.0
        while time.time() < end:
            for line in self.lines("admin")[mark:]:
                if f"TestOnlyCamp {verb}" in line and "[SYSTEM]" in line:
                    return line.split("TestOnlyCamp ", 1)[1]
            time.sleep(0.15)
        check(False, f"probe {name} {verb} answered")
        return ""

    def rep(self, name: str) -> dict:
        path = HOST / f"campprobe-{int(self.hexid(name), 16):X}.json"
        before = path.stat().st_mtime_ns if path.exists() else 0
        self.probe(name, "report")
        for _ in range(20):
            if path.exists() and path.stat().st_mtime_ns != before:
                break
            time.sleep(0.1)
        return json.loads(path.read_text())

    def flag(self, flag_name: str, value: bool) -> None:
        mark = self.mark("admin")
        self.admin.say(f"[TestOnlyFlagOverride {flag_name} {'true' if value else 'false'}")
        check(self.said("admin", mark, f"{flag_name} in-memory = {value}"), f"flag {flag_name} = {value}")

    # ---- gumps
    def gumps(self, name: str) -> list:
        """Open server gumps as dicts: server serial and the lines of text."""
        out, current = [], None
        for line in self.p[name].call("gumps"):
            m = re.match(r"\[GUMP\] local (0x\w+) server (0x\w+)", line)
            if m:
                current = {"server": m.group(2), "text": []}
                out.append(current)
            elif current is not None:
                current["text"].append(line.strip())
        return out

    def gump(self, name: str, needle: str, timeout: float = 6.0):
        end = time.time() + timeout
        while time.time() < end:
            for g in self.gumps(name):
                if needle in "\n".join(g["text"]):
                    return g
            time.sleep(0.4)
        return None

    def respond(self, name: str, g: dict, button: int, *switches: int) -> None:
        self.p[name].call(" ".join(["gumpresponse", str(button), *map(str, switches), f"gump:{g['server']}"]))

    def close_gumps(self, name: str) -> None:
        for g in self.gumps(name):
            self.respond(name, g, 0, )
        time.sleep(0.4)

    # ---- scenario helpers
    def reset(self, skill: float = 65.0, kindling: int = 5) -> None:
        """A known state: a party of all three, nobody hurt or hindered, nothing on cooldown, no fires, the warning on."""
        self.close_gumps("CtTrav")
        self.probe("CtLight", "firekill")
        for n in NAMES:
            self.probe(n, "cond", "clear")
            self.probe(n, "cond", "light")
            self.probe(n, "cond", "unparalyze")
            self.probe(n, "cooldown", "clear")
            self.probe(n, "warning", "on")
            self.probe(n, "kindling", kindling)
        self.probe("CtLight", "skill", skill)
        self.probe("CtLight", "party", self.hexid("CtTrav"), self.hexid("CtThird"))
        for n in ("CtTrav", "CtThird"):
            self.probe(n, "move", *ORIGIN)
        self.probe("CtLight", "move", *CAMP)

    def fire(self, at: tuple = CAMP, wait_secure: bool = True) -> dict:
        self.probe("CtLight", "move", *at)
        self.probe("CtLight", "fire")
        if wait_secure:
            time.sleep(9.5)
        fires = self.rep("CtLight")["fires"]
        check(len(fires) == 1, "one fire burns", str(fires))
        return fires[0]

    def request(self, name: str) -> str:
        """`[CampTravel`; returns the journal text that followed, plus 'LIST' if the camp list opened."""
        self.close_gumps(name)
        mark = self.mark(name)
        self.p[name].say("[CampTravel")
        g = self.gump(name, "Travel to a party member's camp", timeout=3.0)
        return "LIST" if g else self.since(name, mark)

    def pick(self, name: str, button: int = 1):
        """Press a camp in the list; returns (confirm gump or None, journal text since)."""
        g = self.gump(name, "Travel to a party member's camp", timeout=3.0)
        check(g is not None, f"{name}: the camp list is open")
        mark = self.mark(name)
        self.respond(name, g, button)
        confirm = self.gump(name, "Stand still for", timeout=2.5)
        return confirm, self.since(name, mark)

    def refused(self, name: str, text: str, case: str) -> None:
        """Ask for travel and expect the list, a pick, and `text` in the journal with no confirmation."""
        listed = self.request(name)
        check(listed == "LIST", f"{case}: the list opens", listed)
        confirm, said = self.pick(name)
        check(confirm is None and text in said, case, said.strip()[:140])

    def travel(self, name: str, switches: tuple = ()) -> dict:
        """Ask, pick, confirm; return the confirmation gump text read before pressing Travel."""
        listed = self.request(name)
        check(listed == "LIST", f"{name}: the list opens", listed)
        confirm, said = self.pick(name)
        check(confirm is not None, f"{name}: asked to confirm", said.strip()[:140])
        mark = self.mark(name)
        self.respond(name, confirm, 1, *switches)
        return {"text": "\n".join(confirm["text"]), "mark": mark}


# ------------------------------------------------------------------------------------------------ camp

def stage_camp() -> None:
    rig = Rig()
    camp_basic(rig)
    camp_pet(rig)
    camp_refusals(rig)
    camp_criminal(rig)
    camp_cancels(rig)


def camp_basic(rig: Rig) -> None:
    t, third = "CtTrav", "CtThird"

    # L2a and L1: a young fire is refused, a secure one takes the traveler, who pays 2 Kindling and starts the cooldown.
    rig.reset(skill=65.0)
    rig.probe("CtLight", "move", *CAMP)
    lit_mark = rig.mark("CtLight")             # before the fire: the lit notice can arrive before the probe answers
    rig.probe("CtLight", "fire")
    rig.refused(t, "not secure yet", "L2 a fire younger than secureSeconds refuses")
    time.sleep(9.0)
    fire = rig.rep("CtLight")["fires"][0]
    check(fire["secure"], "the fire is secure after its secure time")
    lighter = rig.rep("CtLight")
    check(2 == int((lighter["camping"] - 40) // 10), "Camping 60 to 69 gives 2 places", f"skill {lighter['camping']}")
    trip = rig.travel(t)
    check("Travel to CtLight's camp?" in trip["text"] and "It costs 2 Kindling" in trip["text"], "L1 the confirmation names the camp and the cost")
    check(HOT_WARNING not in trip["text"] and CHECKBOX not in trip["text"], "L1 no Hot Zone warning for an ordinary camp")
    check(rig.said(t, trip["mark"], "You arrive at CtLight's camp.", timeout=8), "L1 the traveler arrives")
    r = rig.rep(t)
    check(0 < max(abs(r["x"] - fire["x"]), abs(r["y"] - fire["y"])) <= 2 and (r["x"], r["y"]) != (fire["x"], fire["y"]),
          "L1 lands within 2 tiles of the fire, not on it", f"{r['x']},{r['y']} vs {fire['x']},{fire['y']}")
    check(r["kindling"] == 3, "L1 costs 2 Kindling", str(r["kindling"]))
    check(r["cooldownTag"] is not None, "L1 starts the cooldown", str(r["cooldownTag"]))
    check(rig.rep("CtLight")["fires"][0]["arrivals"] == 1, "L1 the fire counts 1 arrival")
    check(rig.said("CtLight", lit_mark, "CtTrav has travelled to your camp (1 of 2 places used)"), "L7 the lighter is told of the arrival with the count")
    check(rig.said("CtLight", lit_mark, "[CampTravel (your Camping skill gives 2 places)"), "L7 the lighter was told the command and the places when it was lit")
    check(rig.said("CtLight", lit_mark, "Your camp is secure. Party members can travel to it with [CampTravel"), "L7 the lighter was told when it became secure")

    # L5: the cooldown, shared by the account (the tag lives on the account), then capacity.
    rig.probe(t, "move", *ORIGIN)
    rig.refused(t, "cannot use camp travel again for", "L5 the cooldown refuses a second trip")
    check(rig.rep(t)["kindling"] == 3, "L5 a refused trip costs nothing")
    mark = rig.mark("CtLight")
    trip = rig.travel(third)
    check(rig.said(third, trip["mark"], "You arrive at CtLight's camp.", timeout=8), "L5 a second party member arrives (2 of 2)")
    check(rig.said("CtLight", mark, "no places left"), "L5 the lighter is told the camp is full")
    rig.probe(t, "cooldown", "clear")
    rig.probe(t, "move", *ORIGIN)
    rig.refused(t, "no places left (2 of 2 used)", "L5 the third traveler finds the camp full")

    # L5: a lighter under Camping 50 takes nobody; Camping 100 takes six.
    rig.reset(skill=45.0)
    mark = rig.mark("CtLight")
    fire = rig.fire()
    check(rig.said("CtLight", mark, "once your Camping skill is 50 or higher"), "L7 a lighter under 50 is told what it takes")
    rig.refused(t, "needs Camping 50 or higher", "L5 a fire lit under Camping 50 takes nobody")
    rig.reset(skill=100.0)
    mark = rig.mark("CtLight")
    rig.fire()
    check(rig.said("CtLight", mark, "gives 6 places"), "L5 Camping 100 gives 6 places")
    check(rig.said("CtLight", mark, "6 of 6 places left"), "L7 the secure notice counts the places left")

def camp_pet(rig: Rig) -> None:
    """L5: a bonded pet that is following comes with the traveler, as with Recall; one told to stay does not."""
    t = "CtTrav"
    rig.reset(skill=65.0)
    came = int(re.search(r"pet=(0x\w+)", rig.probe(t, "pet")).group(1), 16)
    rig.fire()
    pets = {pet["serial"]: pet for pet in rig.rep(t)["pets"]}
    check(came in pets and pets[came]["order"] == "Follow", "L5 staged a bonded pet that follows", str(pets.get(came)))
    stays = [serial for serial, pet in pets.items() if serial != came and pet["order"] != "Follow"]
    trip = rig.travel(t)
    check(rig.said(t, trip["mark"], "You arrive at CtLight's camp.", timeout=8), "L5 the pet owner arrives")
    time.sleep(1.0)
    r = rig.rep(t)
    pets = {pet["serial"]: pet for pet in r["pets"]}
    close = max(abs(pets[came]["x"] - r["x"]), abs(pets[came]["y"] - r["y"]))
    check(pets[came]["map"] == "Felucca" and close <= 2 and abs(pets[came]["x"] - 633) > 100,
          "L5 the following bonded pet arrived beside the traveler", f"pet {pets[came]['x']},{pets[came]['y']} traveler {r['x']},{r['y']}")
    for serial in stays:
        check(abs(pets[serial]["x"] - 633) < 100, "L5 a pet that was told to stay did not come", str(pets[serial]))


def camp_refusals(rig: Rig) -> None:
    """L3: every refusal, one at a time, each at no cost."""
    t, third = "CtTrav", "CtThird"
    rig.reset(skill=65.0)
    rig.fire()
    for cond, text, case in (("heavy", "too encumbered", "overloaded"), ("paralyze", "unable to move", "unable to move")):
        rig.probe(t, "cond", cond)
        rig.refused(t, text, f"L3 {case} is refused")
        rig.probe(t, "cond", {"heavy": "light", "paralyze": "unparalyze"}[cond])
    rig.probe(t, "cond", "combat", rig.hexid(third))
    rig.refused(t, "heat of battle", "L3 recent player-versus-player combat is refused")
    rig.probe(t, "cond", "clear")
    rig.probe(t, "kindling", 1)
    rig.refused(t, "You need 2 Kindling", "L3 too little Kindling is refused")
    rig.probe(t, "kindling", 5)
    rig.probe(t, "move", *HOT)
    check(rig.rep(t)["hot"], "L3 staged the traveler inside a Hot Zone")
    rig.refused(t, "leave a Hot Zone", "L3 leaving a Hot Zone by camp travel is refused")
    rig.probe(t, "move", *DUNGEON)
    r = rig.rep(t)
    check(r["dungeon"], "L3 staged the traveler inside a Felucca dungeon", str(r["region"]))
    rig.refused(t, "cannot travel from this place", "L3 leaving a Felucca dungeon is refused")
    rig.probe(t, "move", *ORIGIN)
    rig.probe("CtLight", "firekill")
    rig.probe("CtLight", "move", *DUNGEON)
    rig.probe("CtLight", "fire")
    time.sleep(9.5)
    rig.refused(t, "cannot travel to that camp", "L3 a camp inside a Felucca dungeon is refused")
    check(rig.rep(t)["kindling"] == 5, "L3 no refusal cost any Kindling")

def camp_criminal(rig: Rig) -> None:
    """L3 (owner ruling 2026-10-06): a criminal may use camp travel; recent player combat still stops them."""
    t = "CtTrav"
    rig.reset(skill=65.0)
    rig.fire()
    rig.probe(t, "cond", "criminal")
    check(rig.rep(t)["criminal"], "L3 staged a criminal traveler")
    rig.probe(t, "cond", "combat", rig.hexid("CtThird"))
    rig.refused(t, "heat of battle", "L3 a criminal in recent player combat is refused")
    rig.probe(t, "cond", "clear")
    rig.probe(t, "cond", "criminal")
    trip = rig.travel(t)
    check(rig.said(t, trip["mark"], "You arrive at CtLight's camp.", timeout=8), "L3 a criminal outside combat travels to the camp")
    r = rig.rep(t)
    check(r["kindling"] == 3, "L3 the criminal paid 2 Kindling", str(r["kindling"]))
    rig.probe(t, "cond", "clear")


def camp_cancels(rig: Rig) -> None:
    """L4: the wait is cancelled by moving, by damage, by the party breaking up and by the fire going out; nothing is spent."""
    t, third = "CtTrav", "CtThird"
    rig.reset(skill=100.0)
    rig.fire()
    trip = rig.travel(t)
    rig.p[t].gotoexact(ORIGIN[0] + 2, ORIGIN[1]).wait()
    check(rig.said(t, trip["mark"], "You move, and the travel is cancelled."), "L4 moving cancels the wait")
    rig.probe(t, "move", *ORIGIN)
    trip = rig.travel(t)
    rig.probe(t, "hurt", 10)
    check(rig.said(t, trip["mark"], "The pain breaks your concentration"), "L4 damage cancels the wait")
    trip = rig.travel(t)
    rig.probe("CtLight", "leave")
    check(rig.said(t, trip["mark"], "no longer in your party"), "L4 the lighter leaving the party cancels it")
    rig.probe("CtLight", "party", rig.hexid(t), rig.hexid(third))
    trip = rig.travel(t)
    rig.probe("CtLight", "firekill")
    check(rig.said(t, trip["mark"], "burned out"), "L4 the fire going out cancels it")
    r = rig.rep(t)
    check(r["kindling"] == 5, "L4 no cancel cost any Kindling", f"{r['kindling']} at {r['x']},{r['y']}")


# --------------------------------------------------------------------------------------- lighter notices

def stage_notices() -> None:
    """L7: the lighter hears each moment of a fire's life once. Camping 55 gives a fire lit 115 s, dim from 77 s, embers 115 s, gone 172 s."""
    rig = Rig()
    t, third = "CtTrav", "CtThird"
    rig.reset(skill=55.0)
    rig.probe(third, "kindling", 5)
    mark = rig.mark("CtLight")
    start = time.time()
    rig.probe("CtLight", "fire")
    check(rig.said("CtLight", mark, "Your campfire is lit."), "L7 lit notice")
    check(rig.said("CtLight", mark, "Your camp is secure.", timeout=15), "L7 secure notice")
    check(rig.said("CtLight", mark, "Your campfire is burning low.", timeout=100), "L7 burning low notice", f"{time.time() - start:.0f} s in")
    check(rig.said("CtLight", mark, "Your campfire is down to embers.", timeout=70), "L7 embers notice", f"{time.time() - start:.0f} s in")
    rig.refused(t, "down to embers", "L2 a fire at embers refuses travel")
    rig.probe(third, "move", CAMP[0], CAMP[1] + 1)
    mark_relit = rig.mark("CtLight")
    pack = rig.p[third]
    pack.open_backpack(wait=4)
    time.sleep(0.8)
    stack = next(i for i in pack.backpack if i.graphic == KINDLING)
    pack.use(stack.serial)
    check(rig.said("CtLight", mark_relit, "Your campfire burns brightly again."), "L7 a party member feeding the fire is told to the lighter")
    check(rig.said("CtLight", mark_relit, "Party members can travel to it with [CampTravel"), "L7 the relit notice repeats the command")
    mark_out = rig.mark("CtLight")
    rig.probe("CtLight", "firekill")
    check(rig.said("CtLight", mark_out, "Your campfire has burned out."), "L7 burned out notice")
    texts = rig.since("CtLight", mark)
    for fragment in ("Your campfire is lit.", "Your camp is secure.", "burning low", "down to embers", "burns brightly again", "burned out"):
        check(texts.count(fragment) == 1, f"L7 '{fragment}' told exactly once", str(texts.count(fragment)))


# ------------------------------------------------------------------------------------------------- hot

def stage_hot() -> None:
    """L8: a Hot Zone camp is tagged and warned about; the checkbox switches the warning off on the account."""
    rig = Rig()
    t = "CtTrav"
    rig.reset(skill=100.0)
    rig.fire(at=HOT)
    r = rig.rep("CtLight")
    check(r["hot"] and r["fires"][0]["hot"], "L8 staged a camp inside the Hot Zone", str(r["region"]))
    listed = rig.request(t)
    check(listed == "LIST", "L8 the list opens")
    g = rig.gump(t, "Travel to a party member's camp")
    check("[HOT ZONE]" in "\n".join(g["text"]), "L8 the Hot Zone camp is tagged in the list", "\n".join(g["text"]))
    confirm, said = rig.pick(t)
    text = "\n".join(confirm["text"])
    check("WARNING" in text and HOT_WARNING in text and CHECKBOX in text, "L8 the confirmation warns and offers the checkbox", text[:160])
    mark = rig.mark(t)
    rig.respond(t, confirm, 1)
    check(rig.said(t, mark, "You arrive at CtLight's camp.", timeout=8), "L8 confirming without the box travels to the Hot Zone")
    check(rig.said(t, mark, "inside a Hot Zone"), "L8 the arrival repeats the warning")
    r = rig.rep(t)
    check(r["hot"] and r["warningTag"] is None, "L8 the traveler is in the Hot Zone and the warning is still on")

    # With the box ticked the choice is saved on the account; the next trip is not warned; [TravelWarning on brings it back.
    rig.probe(t, "cooldown", "clear")
    rig.probe(t, "kindling", 5)
    rig.probe(t, "move", *ORIGIN)
    rig.request(t)
    confirm, said = rig.pick(t)
    check(confirm is not None and CHECKBOX in "\n".join(confirm["text"]), "L8 the warning is shown again")
    mark = rig.mark(t)
    rig.respond(t, confirm, 1, 1)
    check(rig.said(t, mark, "You will not be warned again"), "L8 ticking the box is acknowledged with how to undo it")
    check(rig.said(t, mark, "You arrive at CtLight's camp.", timeout=8), "L8 the trip goes ahead")
    check(rig.rep(t)["warningTag"] == "off", "L8 the choice is saved on the account")
    rig.probe(t, "cooldown", "clear")
    rig.probe(t, "kindling", 5)
    rig.probe(t, "move", *ORIGIN)
    rig.request(t)
    confirm, said = rig.pick(t)
    text = "\n".join(confirm["text"])
    check("WARNING" not in text and CHECKBOX not in text and "Travel to CtLight's camp?" in text, "L8 a suppressed warning leaves the plain confirmation", text[:120])
    rig.close_gumps(t)
    mark = rig.mark(t)
    t_say = rig.p[t]
    t_say.say("[TravelWarning on")
    check(rig.said(t, mark, "warning is on"), "L8 [TravelWarning on says it is on")
    check(rig.rep(t)["warningTag"] is None, "L8 [TravelWarning on clears the saved choice")
    mark = rig.mark(t)
    t_say.say("[TravelWarning off")
    check(rig.said(t, mark, "warning is off"), "L8 [TravelWarning off says it is off")
    check(rig.rep(t)["warningTag"] == "off", "L8 [TravelWarning off saves it")


# ----------------------------------------------------------------------------------------------- warn

def pack_graphics(rig: Rig, name: str, graphics) -> list:
    p = rig.p[name]
    p.open_backpack(wait=4)
    time.sleep(0.8)
    return [i for i in p.backpack if i.graphic in graphics]


def stage_warn() -> None:
    """L9: Recall, a gate and a public moongate warn a blue player on the way into a Hot Zone; nothing else is asked."""
    rig = Rig()
    t = "CtTrav"
    rig.reset()
    rig.probe(t, "magic")
    hot_rune = re.search(r"rune=(0x\w+)", rig.probe(t, "rune", *HOT)).group(1)
    out_rune = re.search(r"rune=(0x\w+)", rig.probe(t, "rune", *OUT)).group(1)

    def scrolls() -> int:
        return rig.rep(t)["recallScrolls"]

    def go(label: str, rune: str, expect_gump: bool, button: int = 1, switches: tuple = ()) -> tuple:
        rig.probe(t, "magic")                     # full mana, Magery 100, 10 more scrolls
        before = scrolls()
        scroll = pack_graphics(rig, t, (SCROLL_RECALL,))[0]
        rig.p[t].use_on(scroll.serial, rune)
        g = rig.gump(t, "Hot Zone Warning", timeout=7.0 if expect_gump else 5.0)
        if expect_gump:
            check(g is not None, f"{label}: the Hot Zone warning opens")
            text = "\n".join(g["text"])
            check("You are about to travel into a Hot Zone." in text and "attack" in text and CHECKBOX in text,
                  f"{label}: it says what the risk is and offers the checkbox", text[:140])
            check(scrolls() == before, f"{label}: nothing is spent while the warning is up")
            rig.respond(t, g, button, *switches)
            time.sleep(3.5)
        else:
            check(g is None, f"{label}: no warning")
            time.sleep(3.0)
        return before, rig.rep(t)

    # Recall into a Hot Zone from outside: asked; cancelling spends nothing, confirming travels and uses the scroll.
    before, r = go("L9 Recall into a Hot Zone, cancelled", hot_rune, True, button=0)
    check(not r["hot"] and r["recallScrolls"] == before, "L9 cancelling goes nowhere and spends no scroll", f"hot {r['hot']}, scrolls {r['recallScrolls']} (before {before})")
    before, r = go("L9 Recall into a Hot Zone, confirmed", hot_rune, True)
    check(r["hot"] and r["recallScrolls"] == before - 1, "L9 confirming travels into the Hot Zone and uses one scroll", f"hot {r['hot']}, scrolls {r['recallScrolls']} (before {before})")
    # From inside the Hot Zone to outside, and from the Hot Zone to itself: not asked.
    before, r = go("L9 Recall out of a Hot Zone", out_rune, False)
    check(not r["hot"], "L9 leaving a Hot Zone by Recall is not asked about and works", f"hot {r['hot']}")
    rig.probe(t, "move", *HOT_FAR)
    check(rig.rep(t)["hot"], "L9 staged the traveler inside the Hot Zone")
    before, r = go("L9 Recall from a Hot Zone to a Hot Zone", hot_rune, False)
    check(r["hot"] and (r["x"], r["y"]) != HOT_FAR, "L9 travel between Hot Zone places is not warned about and works")
    rig.probe(t, "move", *ORIGIN)

    # The checkbox saves the choice; the next trip is not warned; [TravelWarning on brings the warning back.
    before, r = go("L9 the checkbox trip", hot_rune, True, 1, (1,))
    check(r["hot"] and r["warningTag"] == "off", "L9 ticking the box travels and saves the choice", str(r["warningTag"]))
    rig.probe(t, "move", *ORIGIN)
    before, r = go("L9 a suppressed warning", hot_rune, False)
    check(r["hot"], "L9 with the warning off Recall goes straight in")
    rig.probe(t, "move", *ORIGIN)
    mark = rig.mark(t)
    rig.p[t].say("[TravelWarning on")
    check(rig.said(t, mark, "warning is on"), "L9 [TravelWarning on turns it back on")
    before, r = go("L9 the warning is back", hot_rune, True, button=0)
    rig.probe(t, "move", *ORIGIN)

    # A gate (any Moongate) into a Hot Zone warns; a criminal is not warned (and the plain gate lets criminals through).
    gate = re.search(r"gate=(0x\w+)", rig.probe(t, "gate", *HOT)).group(1)
    rig.p[t].use(gate)                             # an immovable item is not in the client's item list, so use it by serial
    g = rig.gump(t, "Hot Zone Warning", timeout=6.0)
    check(g is not None, "L9 entering a gate into a Hot Zone warns")
    rig.respond(t, g, 1)
    time.sleep(3.0)
    check(rig.rep(t)["hot"], "L9 confirming takes the traveler through the gate")
    rig.probe(t, "move", *ORIGIN)
    rig.probe(t, "cond", "criminal")
    gate = re.search(r"gate=(0x\w+)", rig.probe(t, "gate", *HOT)).group(1)
    rig.p[t].use(gate)
    check(rig.gump(t, "Hot Zone Warning", timeout=3.5) is None, "L9 a criminal is not warned")
    stock = rig.gump(t, "step into the moongate", timeout=2.0)       # the stock leaving-town prompt, unchanged
    check(stock is not None, "L9 the stock moongate prompt still appears for a criminal")
    rig.respond(t, stock, 1)
    time.sleep(3.0)
    check(rig.rep(t)["hot"], "L9 the criminal goes through")
    rig.probe(t, "cond", "clear")
    rig.probe(t, "move", *ORIGIN)

    # A public moongate: its list offers Buccaneer's Den, which is inside a Hot Zone.
    gate = re.search(r"pgate=(0x\w+)", rig.probe(t, "pgate")).group(1)
    rig.p[t].use(gate)
    g = rig.gump(t, "Pick your destination", timeout=6.0)
    check(g is not None, "L9 the public moongate list opens")
    listing = g["text"]
    radio = None
    for i, line in enumerate(listing):
        if line.startswith("[radio") and i + 1 < len(listing) and "Buccaneer" in listing[i + 1]:
            radio = int(line.split()[1].rstrip("]"))
    check(radio is not None, "L9 the list offers Buccaneer's Den", "\n".join(listing)[:300])
    rig.respond(t, g, 1, radio)
    w = rig.gump(t, "Hot Zone Warning", timeout=6.0)
    check(w is not None, "L9 choosing Buccaneer's Den at a public moongate warns")
    rig.respond(t, w, 1)
    time.sleep(3.0)
    check(rig.rep(t)["hot"], "L9 confirming takes the traveler to Buccaneer's Den")

    # Flag off: no warning for Recall.
    rig.probe(t, "move", *ORIGIN)
    rig.flag("HotZoneTravelWarning", False)
    try:
        before, r = go("L9 the flag off", hot_rune, False)
        check(r["hot"], "L9 with hotZoneTravelWarning off Recall goes straight in")
    finally:
        rig.flag("HotZoneTravelWarning", True)


# ------------------------------------------------------------------------------------------------- off

def stage_off() -> None:
    """L6: with campingTravel overridden off the command refuses and the lighter is told nothing."""
    rig = Rig()
    rig.reset(skill=65.0)
    rig.flag("CampingTravel", False)
    try:
        mark = rig.mark("CtTrav")
        rig.p["CtTrav"].say("[CampTravel")
        check(rig.said("CtTrav", mark, "Camp travel is not available."), "L6 the command refuses with the flag off")
        mark = rig.mark("CtLight")
        rig.probe("CtLight", "fire")
        check(rig.silent("CtLight", mark, "Your campfire is lit", 4.0), "L6 the lighter is told nothing with the flag off")
    finally:
        rig.flag("CampingTravel", True)


STAGES = {"camp": stage_camp,
          "pet": lambda: camp_pet(Rig()), "refusals": lambda: camp_refusals(Rig()), "criminal": lambda: camp_criminal(Rig()), "cancels": lambda: camp_cancels(Rig()), "notices": stage_notices, "hot": stage_hot, "warn": stage_warn, "off": stage_off}


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in STAGES:
        print(__doc__)
        sys.exit(2)
    STAGES[sys.argv[1]]()
    print(f"ALL PASS: {sys.argv[1]}", flush=True)
