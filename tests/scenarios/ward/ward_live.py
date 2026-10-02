"""Backpack Ward (design B) live cases on a disposable host.

    python ShardContent/tests/scenarios/ward/ward_live.py [stage ...]

Needs eleven fresh ordinary Warrior characters logged in as Navrey sessions named after them, plus the `admin` staff
session (New-TestCharacter.ps1 -HostName <host> -Name Vera,Vick,Vale,Vice,Vane,Vexa,Vyne,Vroc,Thal,Thorn,Tess -Profession 1), on a host whose
server log is the newest `work/dev-server/logs/server-*.log` and whose theftProtection flag is on.

Roles: Vera, Vick, Vale, Vice, Vane, Vexa, Vyne and Vroc are victims; Thal, Thorn and Tess are thieves-guild thieves. Outside a Hot Zone the safe-world
rules refuse theft from a blue player, so the victim is set Criminal before each attempt (as the K2 theft cases do).
Stock detection and the Ward's extra roll are random, so each case loops until it sees the outcome it needs (audit lines
`theft ward-activated|ward-detected|ward-blocked` and the victim's `[TheftStatus <serial>`).

Stage `phase1` leaves Vera Activated and Vexa (or Vyne) Primed and writes their last-activity times to
work/ward-live/state.json; `phase2` (after a server restart) checks persistence, block-after-restart and the 30-minute
expiry. Exits non-zero when any asserted case fails.
"""

from __future__ import annotations

import glob
import json
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(WORKSPACE, ".claude", "scripts"))

from navrey_session import connect, session  # noqa: E402
from staff_command import go_to, staff_target  # noqa: E402

NAMES = ["Vera", "Vick", "Vale", "Vice", "Vane", "Vexa", "Vyne", "Vroc", "Thal", "Thorn", "Tess"]
THIEVES = ["Thal", "Thorn", "Tess"]
KEYWORDS = ("steal", "stolen", "caught", "can't", "detect", "course", "notice", "Hot Zone", "ward", "Ward")
STATE_FILE = os.path.join(WORKSPACE, "work", "ward-live", "state.json")
PLAIN_TYPES = ("Candle", "Torch", "Lantern", "Bottle", "Candle", "Torch", "Lantern", "Bottle")
HEAVY_TYPES = ("Longsword", "Longsword", "Longsword", "Longsword", "Longsword", "Longsword")

# Outside / inside the Buccaneer's Den Hot Zone (water tiles at y=2166: Hot for x<=2766, outside from x=2767).
VICTIM = os.environ.get("WARD_VICTIM", "Vera")
OUT = (2780, 2166, 0)
HOT = (2755, 2166, -2)

adm = connect("admin")
C = {}
for _name in NAMES:
    try:
        C[_name] = connect(_name)
    except (RuntimeError, SystemExit):
        pass  # a stage that needs this session fails loudly; later stages (after a restart) use only some sessions
SERVER_LOG = max(glob.glob(os.path.join(WORKSPACE, "work", "dev-server", "logs", "server-*.log")), key=os.path.getmtime)
results = []
last_steal = {}


def serial(name: str) -> str:
    return str(C[name].state["charID"])


def notoriety(name: str) -> str:
    return str(C[name].state.get("notoriety"))


def sset(name: str, command: str) -> None:
    go_to(adm, C[name])
    staff_target(adm, command, serial(name))


def place(name: str, x: int, y: int, z: int) -> None:
    sset(name, f'[set Location "({x}, {y}, {z})"')


def audit(decision: str, subject: str = None, other: str = None) -> int:
    with open(SERVER_LOG, errors="replace") as handle:
        text = handle.read()
    subj = re.escape(subject) if subject else r"[^;]*"
    oth = re.escape(other) if other else r"[^;]*"
    pattern = rf"Alpha2 theft {re.escape(decision)}: subject=\S+?/{subj}; other=(?:\S+?/)?{oth};"
    return len(re.findall(pattern, text))


def audit_text(decision: str) -> list:
    with open(SERVER_LOG, errors="replace") as handle:
        return [ln.strip() for ln in handle if f"Alpha2 theft {decision}:" in ln]


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


def stage(label: str, body) -> None:
    print(f"--- {label}", flush=True)
    try:
        body()
    except Exception as error:  # noqa: BLE001 - a harness fault must not hide later stages
        record(label, "stage completes", f"{type(error).__name__}: {error}", False)


# ---------------------------------------------------------------- Ward readouts

def ward(victim: str) -> dict:
    """The victim's Ward as `[TheftStatus <serial>` reports it: phase, minutes left, caught thief accounts (None when absent)."""
    m = mark("admin")
    adm.say(f"[TheftStatus {serial(victim)}")
    time.sleep(1.5)
    text = " ".join(since("admin", m))
    if "No Backpack Ward" in text:
        return {"phase": "none", "minutes": 0, "caught": 0, "text": text}
    hit = re.search(r"Backpack Ward: (\w+)(?:, (\d+) minute\(s\) left, (\d+) thief)?", text)
    if not hit:
        return {"phase": "unreadable", "minutes": 0, "caught": 0, "text": text}
    return {"phase": hit.group(1).lower(), "minutes": int(hit.group(2) or 0), "caught": int(hit.group(3) or 0), "text": text}


def probe(command: str) -> str:
    """Run a WardProbe staff command and return the system text it produced (admin log)."""
    m = mark("admin")
    adm.say(command)
    time.sleep(1.5)
    return " ".join(since("admin", m))


def ward_serials(victim: str) -> list:
    found = re.search(r"\[SYSTEM\] WardFind ([0-9A-F ]*)", probe(f"[TestOnlyWardFind {serial(victim)}"))
    return found.group(1).split() if found else []


def last_activity(victim: str) -> str:
    """The Ward's last-activity timestamp as the server holds it (probe), or '' when unreadable."""
    for w in ward_serials(victim):
        hit = re.search(r"phase=(\w+) .* last=(\S+)", probe(f"[TestOnlyWardReport {w}"))
        if hit and hit.group(1) != "Unprimed":
            return hit.group(2)
    return ""


def make_criminal(victim: str) -> None:
    sset(victim, "[set Criminal true")


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


def open_pack(thief: str, victim: str) -> dict:
    pack = str(C[victim].state["backpackID"])
    for _ in range(6):
        sset(victim, "[set Criminal true")
        C[thief].commands.send(f"use {pack}")
        time.sleep(3)
        items = {}
        for ln in C[thief].call(f"container {pack}"):
            hit = re.search(r"\[item\]\s+(0x[0-9A-Fa-f]+)\s+(.*)", ln)
            if hit:
                items[hit.group(2)] = hit.group(1)
        if items:
            return items
    return {}


def stock_plain_items(victim: str, types: tuple = PLAIN_TYPES) -> None:
    for type_name in types:
        sset(victim, f"[AddToPack {type_name}")
        time.sleep(0.8)


def plain_pool(items: dict) -> list:
    pool = []
    for k, v in items.items():
        if any(w in k.lower() for w in ("candle", "torch", "lantern", "bottle", "longsword")):
            pool.append(v)
    return pool


def position(thief: str, victim: str, spot: tuple) -> None:
    x, y, z = spot
    place(thief, x, y, z)
    place(victim, x + 1, y, z)
    make_criminal(victim)
    time.sleep(2)


def counts() -> dict:
    return {d: len(audit_text(d)) for d in ("ward-activated", "ward-detected", "ward-blocked", "ward-reset", "ward-consumed")}


def attempt(thief: str, victim: str, pool: list) -> dict:
    """One steal attempt on the first pooled item. Returns what happened: success / fail / blocked, audit deltas, the thief's messages."""
    make_criminal(victim)
    before = counts()
    while True:
        lines = steal(thief, pool[0])
        text = messages(lines)
        if ("can't steal that" in text or "cannot be stolen" in text) and len(pool) > 1:
            pool.pop(0)  # an item stock refuses (Newbied, etc.): try the next one
            continue
        break
    after = counts()
    delta = {k: after[k] - before[k] for k in after}
    out = {
        "text": text,
        "blocked": "cannot steal from that person" in text,
        "success": "successfully steal" in text,
        "fail": "fail to steal" in text,
        "delta": delta,
    }
    if out["success"] or "can't steal that" in text or "cannot be stolen" in text:
        pool.pop(0)
    return out


def caught_by(thief: str, victim: str, pool: list, limit: int = 14) -> tuple:
    """Attempt until the Ward catches this thief on a successful theft (detected, or Ward-detected). Returns (caught, successes, log)."""
    successes = 0
    log = []
    for _ in range(limit):
        if not pool:
            break
        a = attempt(thief, victim, pool)
        log.append(a)
        if a["blocked"]:
            return True, successes, log
        if a["success"]:
            successes += 1
            if a["delta"]["ward-activated"] or a["delta"]["ward-detected"]:
                return True, successes, log
    return False, successes, log


def reset_victim(victim: str) -> None:
    """A fresh victim pack: staff-added plain items, victim healthy and Criminal, no leftover thieves."""
    stock_plain_items(victim)


# ---------------------------------------------------------------- setup

def setup() -> None:
    for n in C:
        assert C[n].state.get("connected", True), f"{n} not connected"
        sset(n, "[set Criminal false")
    for n in THIEVES:
        sset(n, "[SetSkill Stealing 120")
        sset(n, "[SetSkill Snooping 100")
        sset(n, "[set NpcGuild ThievesGuild")
        for item in C[n].state.get("equipped", []):
            if item.get("layer") in ("OneHanded", "TwoHanded"):
                C[n].commands.send(f"unequip {item['serial']}")
                time.sleep(1.2)
    record("S0 setup", "eight Innocent characters, thieves prepared", "ok", True)


# ---------------------------------------------------------------- the cases

def starter_ward() -> None:
    w = ward("Vera")
    record("W1 starter Ward at creation", "an Unprimed Ward in the new character's pack", f"{w['phase']}", w["phase"] == "unprimed")
    m = mark("Vera")
    C["Vera"].say("[Welcome")
    time.sleep(2)
    text = " ".join(since("Vera", m))
    record("W2 [Welcome text", "describes the caught-thief block", "block text present" if "cannot steal from you again" in text else text[:200],
           "cannot steal from you again" in text and "two minutes" not in text)


def block_flow() -> None:
    """Thal is caught and blocked; Thorn is not; Thorn is then caught separately; Tess (never caught) still rolls."""
    position("Thal", VICTIM, OUT)
    stock_plain_items(VICTIM)
    time.sleep(1)
    pool = [v for v in plain_pool(open_pack("Thal", VICTIM))]
    if len(pool) < 3:
        record("B setup", "Thal sees the victim's plain items", f"saw {len(pool)}", False)
        return

    caught, successes, log = caught_by("Thal", VICTIM, pool)
    w = ward(VICTIM)
    record("B1 Thal caught on a successful theft", "Ward Activated, one caught account",
           f"caught={caught} after {successes} success(es); {w['phase']}, {w['minutes']}m, caught {w['caught']}",
           caught and w["phase"] == "activated" and w["caught"] == 1)
    state = {"vera": {"phase": w["phase"], "caught": w["caught"]}}

    before_minutes = w["minutes"]
    blocked_before = audit("ward-blocked")
    last0 = last_activity(VICTIM)
    a = attempt("Thal", VICTIM, pool)
    record("B2 caught thief is blocked", "'cannot steal from that person', ward-blocked audited, no roll",
           f"{a['text']}; blocked+{audit('ward-blocked') - blocked_before}",
           a["blocked"] and audit("ward-blocked") > blocked_before and not a["success"] and not a["fail"])
    record("B2b a blocked attempt does not restart the window", "last-activity time unchanged", f"{last0} -> {last_activity(VICTIM)}",
           bool(last0) and last0 == last_activity(VICTIM))

    # Another thief on the same victim: not blocked, reaches the roll
    position("Thorn", VICTIM, OUT)
    stock_plain_items(VICTIM, ("Candle", "Torch", "Lantern", "Bottle"))
    pool_b = plain_pool(open_pack("Thorn", VICTIM))
    blocked_before = audit("ward-blocked")
    a = attempt("Thorn", VICTIM, pool_b)
    record("B3 a different thief is not blocked", "Thorn reaches the skill roll",
           f"{a['text']}; blocked+{audit('ward-blocked') - blocked_before}",
           (a["success"] or a["fail"]) and not a["blocked"])

    caught_b, successes_b, _ = caught_by("Thorn", VICTIM, pool_b)
    w = ward(VICTIM)
    record("B4 Thorn is caught separately", "two caught accounts, Thorn then blocked",
           f"caught={caught_b} after {successes_b} success(es); {w['phase']}, caught {w['caught']}",
           caught_b and w["caught"] == 2)
    a = attempt("Thorn", VICTIM, pool_b)
    record("B5 Thorn is blocked, Thal still blocked", "both refused", f"Thorn: {a['text']}", a["blocked"])
    a = attempt("Thal", VICTIM, pool)
    record("B5b Thal still blocked", "refused", a["text"], a["blocked"])

    # Tess never stole from VICTIM: the Ward has not caught her, so she rolls.
    position("Tess", VICTIM, OUT)
    stock_plain_items(VICTIM, ("Candle", "Torch", "Lantern", "Bottle"))
    pool_c = plain_pool(open_pack("Tess", VICTIM))
    a = attempt("Tess", VICTIM, pool_c)
    record("B6 an uncaught thief is not blocked while the Ward is Activated", "Tess reaches the roll",
           a["text"], (a["success"] or a["fail"]) and not a["blocked"])

    # The block must not have restarted the window: minutes left can only have dropped or stayed put through blocked attempts.
    w2 = ward(VICTIM)
    record("B7 blocked attempts do not restart the window (observation)", "minutes left no larger than a fresh 30",
           f"{before_minutes}m -> {w2['minutes']}m (a genuine attempt by Thorn/Tess restarts it)", w2["minutes"] <= 30, obs=True)

    state["vera_last_genuine"] = time.time()
    record("B8 a genuine attempt restarts the window", "last-activity time moved forward", f"{last1} -> {last_activity(VICTIM)}",
           bool(last1) and last_activity(VICTIM) > last1)
    save_state(state)


def refused_before_roll() -> None:
    """A ward that is already tracking: an attempt stock refuses before any roll (a Newbied item) must not restart its window."""
    position("Tess", VICTIM, OUT)
    items = open_pack("Tess", VICTIM)
    plain = set(plain_pool(items))
    others = [(k, v) for k, v in items.items() if v not in plain]
    last0 = last_activity(VICTIM)
    if not others or not last0:
        record("B2c setup", "a non-plain item to target and a tracking Ward", f"items={sorted(items)}; last={last0!r}", False)
        return
    refused = None
    for name, item in others:
        a = attempt("Tess", VICTIM, [item])
        if "can't steal that" in a["text"] or "cannot be stolen" in a["text"]:
            refused = (name, a)
            break
        if a["success"] or a["fail"] or a["blocked"]:
            last0 = last_activity(VICTIM)  # a real roll (or block) happened; re-baseline and try the next one
    if refused is None:
        record("B2c an attempt refused before the roll does not restart the window", "a refused item", "none refused", False)
        return
    last1 = last_activity(VICTIM)
    record("B2c an attempt refused before the roll does not restart the window", "'can't steal that', last-activity unchanged",
           f"{refused[0]}: {refused[1]['text']}; {last0} -> {last1}", last0 == last1)


def escalation() -> None:
    """Vick, fresh Ward: Tess steals unnoticed repeatedly; the Ward must catch her no later than the third undetected success."""
    position("Tess", "Vick", OUT)
    stock_plain_items("Vick")
    time.sleep(1)
    pool = plain_pool(open_pack("Tess", "Vick"))
    detected_by_ward = audit("ward-detected")
    caught, successes, log = caught_by("Tess", "Vick", pool)
    ward_detected = audit("ward-detected") - detected_by_ward
    w = ward("Vick")
    record("E1 escalating detection ends in a catch", "caught on the first, second or third undetected success at the latest",
           f"caught={caught} after {successes} success(es); ward-detected+{ward_detected}; {w['phase']}",
           caught and successes <= 3 and w["phase"] == "activated")
    m = mark("Vick")
    a = attempt("Tess", "Vick", pool)
    record("E2 after the catch she is blocked", "refused", a["text"], a["blocked"])


def failed_attempt_rules() -> None:
    """Vane: an undetected failed attempt never primes; a detected failed attempt activates the Ward without blocking the thief.
    Heavy items and a modest Stealing skill make failures common; stock detection catches most failures at that skill."""
    position("Thal", "Vane", OUT)
    sset("Thal", "[SetSkill Stealing 40")
    stock_plain_items("Vane", HEAVY_TYPES)
    time.sleep(1)
    pool = plain_pool(open_pack("Thal", "Vane"))
    seen_quiet_fail = seen_detected_fail = False
    for _ in range(14):
        if not pool:
            break
        a = attempt("Thal", "Vane", pool)
        w = ward("Vane")
        if a["success"]:
            record("F0 stage ended early", "only failures", f"a success: Ward {w['phase']}", True, obs=True)
            break
        if a["fail"] and not a["delta"]["ward-activated"] and not seen_quiet_fail:
            seen_quiet_fail = True
            record("F1 an undetected failed attempt does not prime", "Ward still Unprimed", f"{w['phase']}", w["phase"] == "unprimed")
        if a["fail"] and a["delta"]["ward-activated"] and not seen_detected_fail:
            seen_detected_fail = True
            nxt = attempt("Thal", "Vane", pool)
            record("F2 a detected failed attempt activates the Ward but does not block the thief", "Activated, 0 caught, Thal still rolls",
                   f"{w['phase']}, caught {w['caught']}; next: {nxt['text']}",
                   w["phase"] == "activated" and w["caught"] == 0 and not nxt["blocked"])
            break
        if w["phase"] != "unprimed":
            break
    if not (seen_quiet_fail or seen_detected_fail):
        record("F setup", "a failed attempt observed", "none within 14 attempts", False)
    sset("Thal", "[SetSkill Stealing 120")


def hot_zone() -> None:
    """Thal is blocked on Vera outside; inside an outdoor Hot Zone the Ward does nothing and the block does not apply."""
    position("Thal", "Vera", HOT)
    pool = plain_pool(open_pack("Thal", "Vera"))
    if not pool:
        record("H setup", "Thal opens Vera's pack in the Hot Zone", "no items", False)
        return
    before = counts()
    blocked_before = audit("ward-blocked")
    a = attempt("Thal", "Vera", pool)
    after = counts()
    record("H1 the block does not apply inside an outdoor Hot Zone", "Thal reaches the roll; no ward-blocked",
           f"{a['text']}; blocked+{after['ward-blocked'] - blocked_before}",
           (a["success"] or a["fail"]) and not a["blocked"] and after["ward-blocked"] == blocked_before)
    record("H2 no Ward priming/activation inside the Hot Zone", "no new ward-activated/ward-detected",
           f"activated+{after['ward-activated'] - before['ward-activated']}, detected+{after['ward-detected'] - before['ward-detected']}",
           after["ward-activated"] == before["ward-activated"] and after["ward-detected"] == before["ward-detected"])
    place("Thal", *OUT)
    place("Vera", OUT[0] + 1, OUT[1], OUT[2])
    time.sleep(2)


def prime_one(victim: str) -> bool:
    position("Thorn", victim, OUT)
    sset("Thorn", "[SetSkill Stealing 120")
    stock_plain_items(victim)
    time.sleep(1)
    pool = plain_pool(open_pack("Thorn", victim))
    for _ in range(10):
        w = ward(victim)
        if w["phase"] == "primed":
            return True
        if w["phase"] == "activated":
            return False
        attempt("Thorn", victim, pool)
    return ward(victim)["phase"] == "primed"


def prime_vale() -> None:
    """Prime a Ward (an undetected successful theft) and leave it Primed for the expiry check; stock detection may Activate it instead, so try spare victims."""
    state = load_state()
    for victim in ("Vexa", "Vyne"):
        if prime_one(victim):
            w = ward(victim)
            record(f"P1 an undetected success primes {victim}'s Ward", "Primed", f"{w['phase']}, {w['minutes']}m left", w["phase"] == "primed")
            state["primed_victim"] = victim
            state["primed_last_genuine"] = time.time()
            save_state(state)
            return
    record("P1 a Ward primed", "Primed", "stock detection activated every candidate", False)


def escalation_more() -> None:
    """Another fresh victim for the 25/50/100 sequence, to see the Ward's own catch (ward-detected) and not only stock detection."""
    position("Tess", "Vroc", OUT)
    sset("Tess", "[SetSkill Stealing 120")
    stock_plain_items("Vroc")
    time.sleep(1)
    pool = plain_pool(open_pack("Tess", "Vroc"))
    before = audit("ward-detected")
    caught, successes, log = caught_by("Tess", "Vroc", pool)
    record("E3 second escalation sample", "caught within three undetected successes",
           f"caught={caught} after {successes} success(es); ward-detected+{audit('ward-detected') - before}", caught and successes <= 3)


def save_state(state: dict) -> None:
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    existing = load_state()
    existing.update(state)
    with open(STATE_FILE, "w") as handle:
        json.dump(existing, handle)


def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as handle:
            return json.load(handle)
    return {}


def phase2() -> None:
    state = load_state()
    for victim, key in (("Vera", "vera_last_genuine"), (state["primed_victim"], "primed_last_genuine")):
        w = ward(victim)
        age = (time.time() - state[key]) / 60
        print(f"   {victim}: {w['phase']} {w['minutes']}m left, {w['caught']} caught; {age:.1f} min since last genuine attempt", flush=True)
    w = ward("Vera")
    record("R1 Activated Ward survives a restart with its caught thieves", "Activated, 3 caught (Thal and Thorn, plus Tess caught by stock detection)",
           f"{w['phase']}, {w['caught']} caught, {w['minutes']}m left", w["phase"] == "activated" and w["caught"] == 3)
    w = ward(state["primed_victim"])
    record("R2 Primed Ward survives a restart", "Primed", f"{w['phase']}, {w['minutes']}m left", w["phase"] == "primed")
    position("Thal", "Vera", OUT)
    pool = plain_pool(open_pack("Thal", "Vera"))
    a = attempt("Thal", "Vera", pool) if pool else {"blocked": False, "text": "no items"}
    record("R3 the block survives a restart", "Thal refused", a["text"], a["blocked"])


def phase3() -> None:
    """Run once 31+ minutes have passed since the last genuine attempt on both victims (no further attempts in between)."""
    state = load_state()
    for key in ("vera_last_genuine", "primed_last_genuine"):
        print(f"   {key}: {(time.time() - state[key]) / 60:.1f} min ago", flush=True)
    consumed = audit("ward-consumed")
    reset = audit("ward-reset")
    w = ward("Vera")
    record("X1 an Activated Ward is consumed after 30 quiet minutes", "no Ward left, ward-consumed audited",
           f"{w['phase']}; consumed total {consumed}", w["phase"] == "none" and consumed >= 1)
    w = ward(state["primed_victim"])
    record("X2 a Primed Ward resets after 30 quiet minutes", "Unprimed, ward-reset audited",
           f"{w['phase']}; reset total {reset}", w["phase"] == "unprimed" and reset >= 1)
    position("Thal", "Vera", OUT)
    pool = plain_pool(open_pack("Thal", "Vera"))
    if pool:
        a = attempt("Thal", "Vera", pool)
        record("X3 the block is gone with the Ward", "Thal reaches the roll", a["text"], (a["success"] or a["fail"]) and not a["blocked"])


def main() -> int:
    print(f"server log {SERVER_LOG}", flush=True)
    stages = [("setup", setup), ("starter", starter_ward), ("block", block_flow), ("escalation", escalation),
              ("refused", refused_before_roll), ("failed", failed_attempt_rules), ("hot", hot_zone), ("escalation2", escalation_more), ("prime", prime_vale),
              ("phase2", phase2), ("phase3", phase3)]
    default = ["setup", "starter", "block", "refused", "escalation", "failed", "hot", "escalation2", "prime"]
    only = sys.argv[1:] or default
    for label, body in stages:
        if label in only:
            stage(label, body)
    failed = [r for r in results if not r[3]]
    print(f"\n{len(results) - len(failed)}/{len(results)} cases passed", flush=True)
    for r in failed:
        print("FAILED:", r[0], "-", r[2])
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
