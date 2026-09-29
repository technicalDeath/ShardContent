"""K2 live consequence cases for the outdoor Hot Zones (disposable host with hotZones on).

    python ShardContent/tests/scenarios/hot-zones/hot_consequences_live.py

Needs nine fresh ordinary Warrior characters logged in as Navrey sessions named after them, plus the
`admin` staff session (New-TestCharacter.ps1 -HostName <host> -Name Kara,Vona,Vale,Vesh,Elin,Tavi,Rook,Wren,Pike
-Profession 1), on a host whose server log is the newest `work/dev-server/logs/server-*.log`.

Roles: Kara attacker, Vona/Vale/Vesh victims, Elin thieves-guild thief (blue), Tavi criminal thief and
attacker, Rook/Wren the H6 pair, Pike the X1 executor. Case order matters: several cases spend a character's
Innocent status or a KO window. Placement is by `[set Location` (water tiles inside/outside the Buccaneer's
Den polygon at y=2166: Hot for x<=2766, outside from x=2767), so boundary crossing is by placement, not walking.

Exits non-zero when any asserted case fails. Cases marked OBS record an observation only.
"""

from __future__ import annotations

import glob
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(WORKSPACE, ".claude", "scripts"))

from navrey_session import connect, session  # noqa: E402
from staff_command import go_to, staff_target  # noqa: E402
from uo import Event  # noqa: E402

NAMES = ["Kara", "Vona", "Vale", "Vesh", "Elin", "Tavi", "Rook", "Wren", "Pike"]
KEYWORDS = ("steal", "protected", "take the item", "Knocked", "execut", "eligible", "can't", "caught", "Hot Zone", "murder")

adm = connect("admin")
C = {n: connect(n) for n in NAMES}
SERVER_LOG = max(glob.glob(os.path.join(WORKSPACE, "work", "dev-server", "logs", "server-*.log")), key=os.path.getmtime)
results = []
last_steal = {}
state = {}


def serial(name: str) -> str:
    return str(C[name].state["charID"])


def hits(name: str) -> int:
    return int(C[name].state.get("hits", 0))


def notoriety(name: str) -> str:
    return str(C[name].state.get("notoriety"))


def sset(name: str, command: str) -> None:
    go_to(adm, C[name])
    staff_target(adm, command, serial(name))


def place(name: str, x: int, y: int, z: int) -> None:
    sset(name, f'[set Location "({x}, {y}, {z})"')


def audit(category: str, decision: str, subject: str = None, other: str = None) -> int:
    with open(SERVER_LOG, errors="replace") as handle:
        text = handle.read()
    subj = re.escape(subject) if subject else r"[^;]*"
    oth = re.escape(other) if other else r"[^;]*"
    pattern = rf"Alpha2 {re.escape(category)} {re.escape(decision)}: subject=\S+?/{subj}; other=(?:\S+?/)?{oth};"
    if subject is None:
        pattern = rf"Alpha2 {re.escape(category)} {re.escape(decision)}:"
    return len(re.findall(pattern, text))


def mark(name: str) -> int:
    with open(session(name)["log"], errors="replace") as handle:
        return len(handle.readlines())


def since(name: str, m: int) -> list:
    with open(session(name)["log"], errors="replace") as handle:
        return [ln.strip() for ln in handle.readlines()[m:]]


def messages(lines: list) -> str:
    kept = [re.sub(r"^\[[\d:.]+\]\s*", "", ln) for ln in lines if any(k in ln for k in KEYWORDS)]
    return " | ".join(kept) or "(no relevant messages)"


def wait_until(condition, timeout: float, step: float = 0.4) -> bool:
    end = time.time() + timeout
    while time.time() < end:
        if condition():
            return True
        time.sleep(step)
    return False


def record(case_id: str, expected: str, observed: str, ok: bool, obs: bool = False) -> None:
    label = "OBS " if obs else ("PASS" if ok else "FAIL")
    results.append((case_id, expected, observed, ok or obs))
    print(f"{label} {case_id}: expected {expected}; observed {observed}", flush=True)


def fight(attacker: str, victim: str, seconds: float) -> tuple:
    """Attacker forces an attack on the victim; returns (victim hits dropped, start, end)."""
    start = hits(victim)
    a = C[attacker]
    a.war(True)
    time.sleep(0.6)
    a.commands.send(f"attack {serial(victim)} force")
    dropped = wait_until(lambda: hits(victim) < start, seconds)
    a.war(False)
    return dropped, start, hits(victim)


def heal(name: str) -> None:
    sset(name, f"[set Hits {C[name].state.get('maxHits', 60)}")


def unequip_weapon(name: str) -> None:
    for item in C[name].state.get("equipped", []):
        if item.get("layer") in ("OneHanded", "TwoHanded"):
            C[name].commands.send(f"unequip {item['serial']}")
            time.sleep(1.2)


def open_pack(thief: str, victim: str) -> dict:
    """Snoop the victim's pack (thief needs Snooping); returns {name: serial}."""
    pack = str(C[victim].state["backpackID"])
    for _ in range(4):
        C[thief].commands.send(f"use {pack}")
        time.sleep(3)
        lines = C[thief].call(f"container {pack}")
        items = {}
        for ln in lines:
            hit = re.search(r"\[item\]\s+(0x[0-9A-Fa-f]+)\s+(.*)", ln)
            if hit:
                items[hit.group(2)] = hit.group(1)
        if items:
            return items
    return {}


def gold_of(items: dict) -> str:
    return next(v for k, v in items.items() if k.startswith("gold coin"))


def add_to_pack(victim: str, type_name: str) -> None:
    """Staff adds a plain (non-Newbied) item to the victim's pack; starter items are Newbied, so stock Stealing refuses them."""
    sset(victim, f"[AddToPack {type_name}")
    time.sleep(1.5)


def lootable(items: dict) -> str:
    return next(v for k, v in items.items() if "candle" in k.lower())


PLAIN_TYPES = ("Candle", "Torch", "Lantern", "Bottle")


def stock_plain_items(victim: str) -> None:
    for type_name in PLAIN_TYPES:
        add_to_pack(victim, type_name)


def plain_pool(items: dict) -> list:
    """Serials of the staff-added plain items, in PLAIN_TYPES order."""
    pool = []
    for keyword in ("candle", "torch", "lantern", "bottle"):
        hit = next((v for k, v in items.items() if keyword in k.lower()), None)
        if hit:
            pool.append(hit)
    return pool


def attempt(thief: str, pool: list) -> list:
    """One steal attempt on the first pooled item; a successful steal removes it from the pool."""
    lines = steal(thief, pool[0])
    if "successfully steal" in messages(lines):
        pool.pop(0)
    return lines


def revive(name: str) -> None:
    if ghost(name):
        sset(name, "[Resurrect")
        wait_until(lambda: not ghost(name), 10)
    sset(name, f"[set Hits {C[name].state.get('maxHits', 60)}")
    time.sleep(1)


def rolled(text: str) -> bool:
    return bool(re.search(r"fail to steal|steal the item|succe?ssfully steal|You stole", text)) and "can't steal" not in text


def pair_last_act(a: str, b: str) -> float:
    """Wall-clock time of the last encounter audit line involving both characters (server log is local time)."""
    with open(SERVER_LOG, errors="replace") as handle:
        lines = [ln for ln in handle if "Alpha2 encounter" in ln and f"/{a};" in ln and f"/{b};" in ln]
    if not lines:
        return 0.0
    stamp = re.match(r"\[(\d\d):(\d\d):(\d\d)", lines[-1])
    now = time.localtime()
    return time.mktime((now.tm_year, now.tm_mon, now.tm_mday, int(stamp[1]), int(stamp[2]), int(stamp[3]), 0, 0, -1))


def steal(thief: str, item: str) -> list:
    wait = 11.5 - (time.time() - last_steal.get(thief, 0))
    if wait > 0:
        time.sleep(wait)
    m = mark(thief)
    C[thief].commands.send("useskill stealing")
    time.sleep(1.5)
    C[thief].commands.send(f"target {item}")
    time.sleep(3)
    last_steal[thief] = time.time()
    return since(thief, m)


def execute(name: str, victim: str) -> tuple:
    c = C[name]
    m = mark(name)
    c.events.drain()
    c.say("[Execute")
    if c.wait_for(Event.TARGET_REQUEST, timeout=5) is None:
        return "no-cursor", ""
    c.target(serial(victim))
    time.sleep(3)
    text = " ".join(since(name, m))
    if "has been executed" in text:
        return "executed", messages(since(name, m))
    if "not eligible" in text:
        return "refused", messages(since(name, m))
    return "other", messages(since(name, m))


def ghost(name: str) -> bool:
    return bool(C[name].state.get("charGhost"))


def stage(label: str, body) -> None:
    print(f"--- {label}", flush=True)
    try:
        body()
    except Exception as error:  # noqa: BLE001 - a harness fault must not hide later stages
        record(label, "stage completes", f"{type(error).__name__}: {error}", False)


# ---------------------------------------------------------------- setup

def setup() -> None:
    for name in NAMES:
        assert C[name].state.get("connected", True), f"{name} not connected"
        assert notoriety(name) == "Innocent", f"{name} is {notoriety(name)}"
    for name in ("Elin", "Tavi"):
        sset(name, "[SetSkill Snooping 100")
        sset(name, "[set NpcGuild ThievesGuild")
        unequip_weapon(name)
    record("S0 setup", "nine Innocent characters, thieves prepared", "ok", True)


# ---------------------------------------------------------------- H6 arm

def arm_h6() -> None:
    place("Rook", 2764, 2166, 0)
    place("Wren", 2765, 2166, 0)
    revive("Rook")
    revive("Wren")
    time.sleep(3)
    dropped, start, end = fight("Rook", "Wren", 30)
    # The client keeps swinging at its last target, so both sides must stop or the retaliation window never lapses.
    for name in ("Rook", "Wren"):
        C[name].war(False)
        C[name].commands.send("stop")
    time.sleep(3)
    place("Rook", 2780, 2166, 0)
    place("Wren", 2781, 2166, 0)
    time.sleep(3)
    state["h6_last_act"] = pair_last_act("Rook", "Wren")
    record("H6 arm (fight begun in Hot)", "Wren takes damage", f"hits {start}->{end}, Rook {notoriety('Rook')}", dropped)


# ---------------------------------------------------------------- H2 H3 H4

def h2_h3_h4() -> None:
    place("Kara", 1430, 1690, 0)
    place("Vona", 1431, 1690, 0)
    time.sleep(3)
    before = audit("hostility", "denied", "Kara", "Vona")
    dropped, start, end = fight("Kara", "Vona", 8)
    record("H2 same pair in Britain refused (control)", "no damage, Kara stays Innocent",
           f"hits {start}->{end}, Kara {notoriety('Kara')}, denied+{audit('hostility', 'denied', 'Kara', 'Vona') - before}",
           not dropped and notoriety("Kara") == "Innocent")

    place("Kara", 2766, 2166, 0)
    place("Vona", 2767, 2166, 0)
    time.sleep(3)
    before = audit("hostility", "denied", "Kara", "Vona")
    dropped, start, end = fight("Kara", "Vona", 8)
    denied = audit("hostility", "denied", "Kara", "Vona") - before
    record("H3 attacker in Hot, victim one tile outside", "refused, denial audited",
           f"hits {start}->{end}, denied+{denied}, Kara {notoriety('Kara')}", not dropped and denied >= 1)

    place("Kara", 2767, 2166, 0)
    place("Vona", 2766, 2166, 0)
    time.sleep(3)
    before = audit("hostility", "denied", "Kara", "Vona")
    dropped, start, end = fight("Kara", "Vona", 8)
    denied = audit("hostility", "denied", "Kara", "Vona") - before
    record("H4 attacker outside, victim in Hot", "refused, denial audited",
           f"hits {start}->{end}, denied+{denied}, Kara {notoriety('Kara')}", not dropped and denied >= 1)


# ---------------------------------------------------------------- H1 H5 KO2

def h1_h5_ko2() -> None:
    place("Kara", 2764, 2166, 0)
    place("Vona", 2765, 2166, 0)
    time.sleep(3)
    dropped, start, end = fight("Kara", "Vona", 30)
    record("H1 blue attacks blue in the same Hot region", "damage lands, attacker becomes Criminal",
           f"hits {start}->{end}, Kara {notoriety('Kara')}", dropped and notoriety("Kara") != "Innocent")

    place("Kara", 2768, 2166, 0)
    place("Vona", 2769, 2166, 0)
    place("Elin", 2770, 2166, 0)
    time.sleep(3)
    before = audit("hostility", "denied", "Elin", "Vona")
    dropped, start, end = fight("Elin", "Vona", 8)
    denied = audit("hostility", "denied", "Elin", "Vona") - before
    record("H5a bystander outside may not join the carried-over fight", "refused, denial audited, Elin Innocent",
           f"hits {start}->{end}, denied+{denied}, Elin {notoriety('Elin')}",
           not dropped and denied >= 1 and notoriety("Elin") == "Innocent")

    dropped, start, end = fight("Kara", "Vona", 30)
    record("H5b original attacker may continue outside", "damage lands", f"hits {start}->{end}", dropped)

    sset("Vona", "[set Hits 1")
    entered = audit("knocked-out", "entered", "Vona", "Kara")
    C["Kara"].war(True)
    time.sleep(0.6)
    C["Kara"].commands.send(f"attack {serial('Vona')} force")
    ko = wait_until(lambda: audit("knocked-out", "entered", "Vona", "Kara") > entered, 30)
    C["Kara"].war(False)
    state["ko2_time"] = time.time()
    record("KO2 lethal blow outside after carryover", "Vona Knocked Out (attacker Kara)",
           f"KO audit {ko}, Vona hits {hits('Vona')}", ko)


# ---------------------------------------------------------------- L3 X2 X3

def l3_x2_x3() -> None:
    sset("Tavi", "[set Criminal true")
    place("Tavi", 2769, 2165, 0)
    unequip_weapon("Kara")
    pack = str(C["Vona"].state["backpackID"])

    for thief in ("Elin", "Tavi", "Kara"):
        before = audit("knocked-out-loot", "authorized", thief, "Vona")
        steal(thief, pack)
        gained = audit("knocked-out-loot", "authorized", thief, "Vona") - before
        expected = 1 if thief == "Kara" else 0
        who = {"Elin": "blue bystander", "Tavi": "criminal, not the recorded attacker", "Kara": "criminal recorded attacker"}[thief]
        record(f"L3 KO'd victim outside, {who}", "authorized" if expected else "denied", f"authorized+{gained}",
               (gained >= 1) == bool(expected))

    age = time.time() - state.get("ko2_time", 0)
    result, text = execute("Elin", "Vona")
    record("X2 blue bystander executes outside", "refused", f"{result}; {text}", result == "refused" and not ghost("Vona"))
    result, text = execute("Kara", "Vona")
    ok = result == "executed" and wait_until(lambda: ghost("Vona"), 5)
    record("X3 criminal recorded attacker executes outside", "executed, Vona ghost", f"{result}; {text}; KO age {age:.0f}s", ok)


# ---------------------------------------------------------------- KO1 KO3 L1 L2 X1

def ko_group() -> None:
    place("Tavi", 2755, 2166, -2)
    place("Vale", 2756, 2166, -2)
    place("Elin", 2757, 2166, -2)
    place("Pike", 2756, 2167, -2)
    time.sleep(3)
    stock_plain_items("Vale")
    sset("Vale", "[set Hits 1")
    before = audit("knocked-out", "entered", "Vale", "Tavi")
    weapon = [i for i in C["Tavi"].state.get("equipped", []) if i.get("layer") in ("OneHanded", "TwoHanded")]
    C["Tavi"].war(True)
    time.sleep(0.6)
    C["Tavi"].commands.send(f"attack {serial('Vale')} force")
    ko = wait_until(lambda: audit("knocked-out", "entered", "Vale", "Tavi") > before, 40)
    C["Tavi"].war(False)
    t0 = time.time()
    record("KO1 lethal blow in Hot", "Vale Knocked Out (attacker Tavi)", f"KO audit {ko}, hits {hits('Vale')}, unarmed={not weapon}", ko)

    entered = audit("knocked-out", "entered", "Vale")
    dropped, start, end = fight("Tavi", "Vale", 8)
    record("KO3 attacking a Knocked Out player", "refused, hits unchanged, no second KO",
           f"hits {start}->{end}, extra KO {audit('knocked-out', 'entered', 'Vale') - entered}",
           not dropped and audit("knocked-out", "entered", "Vale") == entered)

    before = audit("knocked-out-loot", "authorized", "Elin", "Vale")
    for _ in range(8):
        steal("Elin", serial("Vale"))  # a Mobile target picks a random pack item; starter items are Newbied and refused
        if audit("knocked-out-loot", "blue-flagged-criminal", "Elin", "Vale"):
            break
    gained = audit("knocked-out-loot", "authorized", "Elin", "Vale") - before
    flagged = audit("knocked-out-loot", "blue-flagged-criminal", "Elin", "Vale")
    record("L1 blue looter of Knocked Out blue in Hot (K-4 follow-up ruling 2026-09-29)", "authorized, looter becomes criminal",
           f"authorized+{gained}; Elin {notoriety('Elin')}; flagged total {flagged}",
           gained >= 1 and flagged >= 1 and notoriety("Elin") == "Criminal")

    m = mark("Tavi")
    C["Tavi"].commands.send(f"use {C['Vale'].state['backpackID']}")
    time.sleep(3)
    text = " ".join(since("Tavi", m))
    record("L2a criminal snoops a Knocked Out victim's pack", "observation: stock Snooping refuses harmful acts on a Knocked Out target",
           "refused ('negative acts')" if "negative acts" in text else f"opened or other: {messages(since('Tavi', m))}", True, obs=True)

    age = time.time() - t0
    murders = audit("murder", "automatic-count", "Pike", "Vale")
    result, text = execute("Pike", "Vale")
    gained = audit("murder", "automatic-count", "Pike", "Vale") - murders
    record("X1 blue bystander executes a Knocked Out blue in Hot (K-4 ruling 2026-09-29)", "refused, Vale alive, no murder count",
           f"{result}; {text}; murder+{gained}; KO age {age:.0f}s", result == "refused" and not ghost("Vale") and gained == 0)


# ---------------------------------------------------------------- theft

def theft() -> None:
    victim = "Vona"  # Vona still carries her starter Backpack Ward; a character that died criminal outside a Knocked Out window may not
    revive(victim)
    sset(victim, "[set Criminal false")
    sset("Elin", "[SetSkill Stealing 0")
    place("Elin", 2755, 2166, -2)
    place(victim, 2756, 2166, -2)
    stock_plain_items(victim)
    time.sleep(1)
    pool = plain_pool(open_pack("Elin", victim))
    if len(pool) < len(PLAIN_TYPES):
        record("T setup", "Elin opens the victim's pack and sees the plain items", f"saw {len(pool)} of {len(PLAIN_TYPES)}", False)
        return

    place("Elin", 2768, 2166, 0)
    place(victim, 2769, 2166, 0)
    time.sleep(3)
    consumed = audit("theft", "ward-consumed", "Elin", victim)
    denied = audit("hostility", "denied", "Elin", victim)
    lines = attempt("Elin", pool)
    text = messages(lines)
    record("T2 same attempt outside on a blue (control)", "no roll, hostility denied, no ward consumed",
           f"{text}; denied+{audit('hostility', 'denied', 'Elin', victim) - denied}; Elin {notoriety('Elin')}",
           not rolled(text) and "can't steal" not in text and audit("hostility", "denied", "Elin", victim) > denied
           and audit("theft", "ward-consumed", "Elin", victim) == consumed)

    place("Elin", 2755, 2166, -2)
    place(victim, 2756, 2166, -2)
    time.sleep(3)
    consumed = audit("theft", "ward-consumed", "Elin", victim)
    lines = attempt("Elin", pool)
    text = messages(lines)
    record("T1 thieves-guild thief in Hot reaches the skill roll", "roll message", text, rolled(text) and "protected" not in text)
    record("T4 caught theft in Hot", "ward not consumed",
           f"ward-consumed+{audit('theft', 'ward-consumed', 'Elin', victim) - consumed}",
           audit("theft", "ward-consumed", "Elin", victim) == consumed)

    place("Elin", 2768, 2166, 0)
    place(victim, 2769, 2166, 0)
    sset(victim, "[set Criminal true")
    time.sleep(2)
    consumed = audit("theft", "ward-consumed", "Elin", victim)
    lines = attempt("Elin", pool)
    tries = 1
    while audit("theft", "ward-consumed", "Elin", victim) == consumed and tries < 5 and pool:
        lines += attempt("Elin", pool)
        tries += 1
    seeded = time.time()
    text = messages(lines)
    record("T3a caught theft on a criminal outside seeds the Ward", "roll, ward consumed",
           f"{text}; ward-consumed+{audit('theft', 'ward-consumed', 'Elin', victim) - consumed}",
           audit("theft", "ward-consumed", "Elin", victim) > consumed)

    protected = audit("theft", "protected-denied", "Elin", victim)
    lines = attempt("Elin", pool)
    record("T3b second attempt within 120s outside", "protected-denied",
           f"{messages(lines)}; protected-denied+{audit('theft', 'protected-denied', 'Elin', victim) - protected}",
           audit("theft", "protected-denied", "Elin", victim) > protected)

    place("Elin", 2755, 2166, -2)
    place(victim, 2756, 2166, -2)
    time.sleep(3)
    protected = audit("theft", "protected-denied", "Elin", victim)
    lines = attempt("Elin", pool)
    text = messages(lines)
    record("T3c same victim moved into Hot while Warded", "allowed to the roll (Hot bypass)", f"{text}",
           audit("theft", "protected-denied", "Elin", victim) == protected and rolled(text) and "protected" not in text)

    place("Elin", 2768, 2166, 0)
    place(victim, 2769, 2166, 0)
    time.sleep(3)
    protected = audit("theft", "protected-denied", "Elin", victim)
    lines = attempt("Elin", pool)
    age = time.time() - seeded
    record("T3d back outside, still inside 120s", "protected-denied again",
           f"{messages(lines)}; protected-denied+{audit('theft', 'protected-denied', 'Elin', victim) - protected}; {age:.0f}s after the Ward seeded",
           age < 118 and audit("theft", "protected-denied", "Elin", victim) > protected)

# ---------------------------------------------------------------- L2 loot

def loot() -> None:
    """Knocked Out loot that actually moves an item: the looter must have opened the pack before the victim went down."""
    victim = "Vona"
    revive(victim)
    sset(victim, "[set Criminal false")
    place("Tavi", 2755, 2166, -2)
    place(victim, 2756, 2166, -2)
    add_to_pack(victim, "Candle")
    time.sleep(2)
    items = open_pack("Tavi", victim)
    if not items or not any("candle" in k.lower() for k in items):
        record("L2 setup", "Tavi opens the victim's pack before the KO", f"saw {sorted(items)}", False)
        return
    candle = lootable(items)
    sset(victim, "[set Hits 1")
    before_ko = audit("knocked-out", "entered", victim, "Tavi")
    C["Tavi"].war(True)
    time.sleep(0.6)
    C["Tavi"].commands.send(f"attack {serial(victim)} force")
    ko = wait_until(lambda: audit("knocked-out", "entered", victim, "Tavi") > before_ko, 40)
    C["Tavi"].war(False)
    C["Tavi"].commands.send("stop")
    if not ko:
        record("L2 setup", f"{victim} Knocked Out by Tavi", f"no KO; {victim} {notoriety(victim)}, ghost={ghost(victim)}", False)
        return
    before = audit("knocked-out-loot", "authorized", "Tavi", victim)
    lines = steal("Tavi", candle)
    gained = audit("knocked-out-loot", "authorized", "Tavi", victim) - before
    text = messages(lines)
    record("L2 criminal looter in Hot takes a plain item", "authorized, item taken",
           f"authorized+{gained}; {text}", gained >= 1 and "take the item" in text)


# ---------------------------------------------------------------- H6 check

def h6_check() -> None:
    revive("Rook")
    revive("Wren")
    last = pair_last_act("Rook", "Wren")
    idle = time.time() - last
    if idle < 130:
        time.sleep(130 - idle)
    wait_until(lambda: notoriety("Rook") == "Innocent", 60)
    before = audit("hostility", "denied", "Rook", "Wren")
    dropped, start, end = fight("Rook", "Wren", 8)
    denied = audit("hostility", "denied", "Rook", "Wren") - before
    record("H6 same fight after the window lapses", "refused, denial audited",
           f"idle {time.time() - last:.0f}s, Rook {notoriety('Rook')}, hits {start}->{end}, denied+{denied}",
           not dropped and denied >= 1)


# ---------------------------------------------------------------- B10 C1

def b10_c1() -> None:
    m = mark("Vale")
    place("Vale", 2775, 2166, 0)
    time.sleep(3)
    text = messages(since("Vale", m)) + " " + " ".join(l for l in since("Vale", m) if "Hot Zone" in l)
    left = "no longer applies" in text or "have left" in text or "left" in text
    record("B10 ghost leaves Hot", "exit message", text.strip(), left)
    m = mark("Vale")
    place("Vale", 2755, 2166, -2)
    time.sleep(3)
    record("B10b ghost re-enters Hot", "entry message (observation)", " ".join(l for l in since("Vale", m) if "Hot Zone" in l) or "none", True, obs=True)

    corpse = [l for l in C["Tavi"].call("items") if "corpse" in l.lower()]
    record("C1 corpse in Hot", "observation only", f"corpses in view: {corpse[:3] or 'none listed'}", True, obs=True)


def main() -> int:
    print(f"server log {SERVER_LOG}", flush=True)
    stages = [("S0 setup", setup), ("H6 arm", arm_h6), ("H2 H3 H4", h2_h3_h4), ("H1 H5 KO2", h1_h5_ko2),
              ("L3 X2 X3", l3_x2_x3), ("KO1 KO3 L1 X1", ko_group), ("T1 T2 T3 T4", theft), ("L2 loot", loot),
              ("H6 check", h6_check), ("B10 C1", b10_c1)]
    only = sys.argv[1:]
    for label, body in stages:
        if not only or any(label.lower().startswith(o.lower()) for o in only):
            stage(label, body)
    failed = [r for r in results if not r[3]]
    print(f"\n{len(results) - len(failed)}/{len(results)} cases passed", flush=True)
    for r in failed:
        print("FAILED:", r[0], "-", r[2])
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
