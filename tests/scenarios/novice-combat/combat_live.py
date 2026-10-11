"""Novice combat assist (docs/Novice-Combat-Assist-Plan.md): live cases on a disposable host with NoviceCombatProbe.dll loaded.

    python -u ShardContent/tests/scenarios/novice-combat/combat_live.py [stage ...]

Needs fresh ordinary characters logged in as Navrey sessions: Mara and Mia (Archer, profession 8), Mika (Swordsman, profession 15) and the `admin`
staff session, on a host whose shard-rules.json has featureFlags.noviceCombat off (the probe switches it in memory for each run). The probe runs
the real engine formulas (BaseWeapon.CheckHit, GetDelay, ScaleDamageOld); the stages compare the measured rates with the pre-AOS formulas.
Stages: baseline, delay, damage, hit, notfor, gain, fights.
"""

from __future__ import annotations

import json
import math
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(WORKSPACE, ".claude", "scripts"))

from navrey_session import connect, session  # noqa: E402
from staff_command import go_to, staff_target  # noqa: E402

STRENGTH, TACTICS_FLOOR, STAMINA_FLOOR = 0.66, 30.0, 60

adm = connect("admin")
C = {}
for _name in ("Mara", "Mia", "Mika"):
    try:
        C[_name] = connect(_name)
    except (RuntimeError, SystemExit):
        pass
results = []


def serial(name: str) -> str:
    return str(C[name].state["charID"])


def mark(name: str) -> int:
    with open(session(name)["log"], errors="replace") as handle:
        return len(handle.readlines())


def since(name: str, m: int) -> list:
    with open(session(name)["log"], errors="replace") as handle:
        return [ln.strip() for ln in handle.readlines()[m:]]


def record(case_id: str, expected: str, observed: str, ok: bool) -> None:
    results.append((case_id, ok))
    print(f"{'PASS' if ok else 'FAIL'} {case_id}: expected {expected}; observed {observed}", flush=True)


def stage(label: str, body) -> None:
    print(f"--- {label}", flush=True)
    try:
        body()
    except Exception as error:  # noqa: BLE001 - a harness fault must not hide later stages
        record(label, "stage completes", f"{type(error).__name__}: {error}", False)


def probe(command: str, key: str, timeout: float = 120.0) -> dict:
    """Runs a probe verb as staff and returns its report line as a dict of key=value pairs."""
    m = mark("admin")
    adm.say(command)
    pattern = re.compile(rf"\[SYSTEM\]\s*{key}\b(.*)")
    deadline = time.time() + timeout
    hit = None
    while time.time() < deadline and hit is None:
        time.sleep(0.4)
        for line in since("admin", m):
            hit = pattern.search(line) or hit
    fields = {}
    for k, v in re.findall(r"(\w+)=([^\s]+)", hit.group(1) if hit else ""):
        try:
            fields[k] = float(v) if "." in v else int(v)
        except ValueError:
            fields[k] = v
    return fields


def admin_say(command: str, wait: float = 1.0) -> None:
    adm.say(command)
    time.sleep(wait)


def sset(name: str, command: str) -> None:
    go_to(adm, C[name])
    staff_target(adm, command, serial(name))


def stock_chance(skill: float, defender: float) -> float:
    """skill and defender are the engine's effective values (Skill.Value: the base plus the stat bonus), as the probe reports them."""
    return min(1.0, (skill + 50.0) / ((defender + 50.0) * 2.0))


def lifted(skill: float, defender: float) -> float:
    raw = (skill + 50.0) / ((defender + 50.0) * 2.0)
    return 1.0 if raw >= 1.0 else min(1.0, raw * (1 + STRENGTH * max(0.0, 1 - skill / 100.0)))


def within(measured: int, n: int, p: float, sigmas: float = 4.5) -> bool:
    sd = math.sqrt(n * p * (1 - p))
    return abs(measured - n * p) <= sigmas * sd + 2


def hit(attacker: str, defender: str, skill: float, mode: str, n: int = 20000) -> dict:
    r = probe(f"[TestOnlyCombatHit {attacker} {defender} {skill} {n} {mode}", "CombatHit", timeout=180)
    if not r:
        raise RuntimeError(f"no CombatHit report for {attacker} vs {defender}")
    return r


def equip(name: str, kind: str) -> None:
    r = probe(f"[TestOnlyCombatEquip {serial(name)} {kind}", "CombatEquip")
    if not r or r.get("weapon") != r.get("held"):
        raise RuntimeError(f"could not equip a {kind} on {name}: {r}")


# ---------------------------------------------------------------- cases

def baseline() -> None:
    equip("Mara", "bow")
    equip("Mika", "katana")
    flag = probe("[TestOnlyNoviceFlag status", "NoviceFlag")
    record("B0 the shipped flag is off", "on=False", str(flag), flag.get("on") == "False")

    d = probe(f"[TestOnlyCombatDelay {serial('Mara')} 33 asis", "CombatDelay")
    expected = 15000.0 / ((33 + 100) * 20)
    record("B1 a fresh archer's Bow swing, flag off (the engine's pre-AOS formula)", f"{expected:.4f} s at stamina 33, speed 20",
           str(d), abs(d.get("seconds", 0) - expected) < 0.001 and d.get("stam") == 33 and d.get("speed") == 20)

    r = hit(serial("Mara"), "orc:60", 50.0, "asis", 20000)
    p = stock_chance(r["atkEff"], r["defSkill"])
    record("B2 a fresh archer's hit rate against an Orc (Wrestling 60), flag off", f"stock {p:.3f}", f"{r['hits'] / r['n']:.3f}; {r}",
           r["attacker"] == "player" and within(r["hits"], r["n"], p))


def delay() -> None:
    mara, mika = serial("Mara"), serial("Mika")
    for who, name, speed in ((mara, "Bow", 20), (mika, "Katana", 58)):
        for stamina in (33, 10):
            off = probe(f"[TestOnlyCombatDelay {who} {stamina} off", "CombatDelay")
            on = probe(f"[TestOnlyCombatDelay {who} {stamina} on", "CombatDelay")
            used = off["stam"]
            record(f"D1 {name} swing at stamina {used}: flag off is stock, flag on counts stamina as at least {STAMINA_FLOOR}",
                   f"off {15000.0 / ((used + 100) * speed):.4f} s, on {15000.0 / ((max(used, STAMINA_FLOOR) + 100) * speed):.4f} s",
                   f"off {off['seconds']}, on {on['seconds']}",
                   abs(off["seconds"] - 15000.0 / ((used + 100) * speed)) < 0.001 and
                   abs(on["seconds"] - 15000.0 / ((max(used, STAMINA_FLOOR) + 100) * speed)) < 0.001)

    sset("Mara", "[set Dex 100")
    time.sleep(1.5)
    off = probe(f"[TestOnlyCombatDelay {mara} 100 off", "CombatDelay")
    on = probe(f"[TestOnlyCombatDelay {mara} 100 on", "CombatDelay")
    record("D2 above the floor (Dex 100, stamina 100) the assist changes nothing", "3.75 s either way", f"off {off['seconds']}, on {on['seconds']}",
           abs(off["seconds"] - 3.75) < 0.001 and abs(on["seconds"] - 3.75) < 0.001)
    sset("Mara", "[set Dex 33")

    orc = probe("[TestOnlyCombatDelay orc:60 10 on", "CombatDelay")
    orc_off = probe("[TestOnlyCombatDelay orc:60 10 off", "CombatDelay")
    record("D3 a monster's swing is never touched", "on equals off", f"on {orc['seconds']}, off {orc_off['seconds']} ({orc['kind']})",
           orc["kind"] == "monster" and abs(orc["seconds"] - orc_off["seconds"]) < 1e-6)


def damage() -> None:
    mara = serial("Mara")
    for tactics in (0, 20, 30, 40, 100):
        off = probe(f"[TestOnlyCombatDamage {mara} {tactics} off", "CombatDamage")
        on = probe(f"[TestOnlyCombatDamage {mara} {tactics} on", "CombatDamage")

        def expect(t: float) -> int:
            d = 100.0 + 100.0 * ((t - 50.0) / 100.0)
            d += d * (off["str"] / 5.0 / 100.0 + off["anatomy"] / 5.0 / 100.0)
            return int(d)

        record(f"M1 damage modifier at Tactics {tactics}: flag off is stock, flag on counts Tactics as at least {TACTICS_FLOOR:.0f}",
               f"off {expect(tactics)}, on {expect(max(tactics, TACTICS_FLOOR))}", f"off {off['scaled']}, on {on['scaled']} (str {off['str']})",
               abs(off["scaled"] - expect(tactics)) <= 1 and abs(on["scaled"] - expect(max(tactics, TACTICS_FLOOR))) <= 1)

    orc = probe("[TestOnlyCombatDamage orc:60 0 on", "CombatDamage")
    orc_off = probe("[TestOnlyCombatDamage orc:60 0 off", "CombatDamage")
    record("M2 a monster's damage modifier is never touched", "on equals off", f"on {orc['scaled']}, off {orc_off['scaled']}", orc["scaled"] == orc_off["scaled"])


def hit_rates() -> None:
    mara, mika = serial("Mara"), serial("Mika")
    for skill, defender in ((0, 60), (20, 60), (50, 60), (70, 60), (90, 60), (100, 60), (0, 91), (50, 91), (100, 91), (50, 30)):
        off = hit(mara, f"orc:{defender}", skill, "off")
        on = hit(mara, f"orc:{defender}", skill, "on")
        d, a = off["defSkill"], off["atkEff"]
        p_off, p_on = stock_chance(a, d), lifted(a, d)
        record(f"H1 Archery {skill} vs a monster at {defender}: flag off is stock, flag on is the lift",
               f"off {p_off:.3f}, on {p_on:.3f}", f"off {off['hits'] / off['n']:.3f}, on {on['hits'] / on['n']:.3f}",
               within(off["hits"], off["n"], p_off) and within(on["hits"], on["n"], p_on))

    # The top end: at skill 100 the flag changes nothing at all.
    off = hit(mara, "orc:91", 100.0, "off")
    on = hit(mara, "orc:91", 100.0, "on")
    p = stock_chance(off["atkEff"], off["defSkill"])
    record("H2 Grandmaster Archery is untouched by the flag", f"both {p:.3f}", f"off {off['hits'] / off['n']:.3f}, on {on['hits'] / on['n']:.3f}",
           within(off["hits"], off["n"], p) and within(on["hits"], on["n"], p))

    # Against a player: the same rule (PvP is lifted too).
    for skill in (50, 70):
        on = hit(mara, mika, skill, "on")
        off = hit(mara, mika, skill, "off")
        d, a = off["defSkill"], off["atkEff"]
        record(f"H3 Archery {skill} against a player (defender weapon skill {d:.0f}): the lift applies to players too",
               f"off {stock_chance(a, d):.3f}, on {lifted(a, d):.3f}", f"off {off['hits'] / off['n']:.3f}, on {on['hits'] / on['n']:.3f} ({on['defender']})",
               on["defender"] == "player" and within(off["hits"], off["n"], stock_chance(a, d)) and within(on["hits"], on["n"], lifted(a, d)))

    # A melee weapon gets the same lift.
    on = hit(mika, "orc:60", 50.0, "on")
    off = hit(mika, "orc:60", 50.0, "off")
    d, a = off["defSkill"], off["atkEff"]
    record("H4 a Swordsman's Katana gets the same lift", f"off {stock_chance(a, d):.3f}, on {lifted(a, d):.3f} (skill {on['usedSkill']})",
           f"off {off['hits'] / off['n']:.3f}, on {on['hits'] / on['n']:.3f}",
           within(off["hits"], off["n"], stock_chance(a, d)) and within(on["hits"], on["n"], lifted(a, d)))


def not_for() -> None:
    mara = serial("Mara")
    for skill in (0, 50):
        off = hit("orc:60", mara, skill, "off")
        on = hit("orc:60", mara, skill, "on")
        d = off["defSkill"]
        p = stock_chance(off["atkEff"], d)
        record(f"N1 a monster attacking a player (Wrestling {skill} vs defender skill {d:.0f}) is never lifted", f"both {p:.3f}",
               f"off {off['hits'] / off['n']:.3f}, on {on['hits'] / on['n']:.3f} ({on['attacker']})",
               on["attacker"] == "monster" and within(off["hits"], off["n"], p) and within(on["hits"], on["n"], p))


def gain_odds() -> None:
    # Mia holds no weapon, so the swing uses Wrestling. Archery and the other weapon skills are under the stock anti-macro limiter, which
    # refuses repeat gains at one spot after a few, so tens of thousands of calls from one place measure nothing for them. The assist sits
    # after the skill check for every weapon alike, so the odds are the same question for any weapon skill.
    mia = serial("Mia")
    heal("Mia")  # a dead character gains nothing
    n = 40000
    off = hit(mia, "orc:60", 50.0, "off", n)
    on = hit(mia, "orc:60", 50.0, "on", n)
    p_off, p_on = off["gains"] / n, on["gains"] / n
    pooled = (off["gains"] + on["gains"]) / (2.0 * n)
    sd = math.sqrt(2.0 * n * pooled * (1 - pooled)) / n
    record(f"G1 weapon-skill gain odds ({on['usedSkill']}) are the same with the assist on and off (the stock skill check is untouched)",
           "equal within sampling error", f"off {p_off:.4f} ({off['gains']} gains), on {p_on:.4f} ({on['gains']} gains), 4.5 sigma {4.5 * sd:.4f}",
           off["gains"] > 100 and abs(p_off - p_on) <= 4.5 * sd)


# ---- real fights

def spawn_orc(wrestling: float = 60.0) -> str:
    r = probe(f"[TestOnlyCombatSpawn {serial('Mara')} {wrestling} 3", "CombatSpawn")
    return r["serial"]


def mobile_state(name: str, target_serial: str):
    path = os.path.join(session(name)["dir"], "cuoworld.json")
    for attempt in range(8):  # the client rewrites the file; a read can land on the swap
        try:
            world = json.loads(open(path, encoding="utf-8-sig").read())
            break
        except (PermissionError, json.JSONDecodeError):
            if attempt == 7:
                raise
            time.sleep(0.4)
    for m in world.get("mobiles", []):
        if str(m.get("serial")).lower().lstrip("0x") == target_serial.lower().lstrip("0x"):
            return m
    return None


def heal(name: str) -> None:
    sset(name, "[Resurrect")
    sset(name, f"[set Hits {C[name].state.get('maxHits', 77)}")
    sset(name, "[set Stam 33")
    time.sleep(1.0)


def log_seconds(line: str):
    m = re.match(r"\[(\d\d):(\d\d):(\d\d\.\d+)\]", line)
    return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3)) if m else None


def kill_seconds(log_mark: int, default: float) -> float:
    """From the first attack to the last swing at the Orc, read from Mara's log. The world file can keep a dead Orc for up to a minute, so
    the wall-clock time at which the Orc is seen dead overstates the kill by that lag."""
    first = last = None
    for line in since("Mara", log_mark):
        stamp = log_seconds(line)
        if stamp is None:
            continue
        if "Attack confirmed ->" in line and first is None:
            first = stamp
        elif "Swing: Mara ->" in line:
            last = stamp
    return (last - first) if first is not None and last is not None and last >= first else default


def fight(mode: str, timeout: float = 400.0) -> float:
    """Mara (a fresh archer) shoots a Wrestling-60 Orc until it dies; returns the seconds."""
    admin_say(f"[TestOnlyNoviceFlag {mode}", 0.8)
    heal("Mara")
    orc = spawn_orc()
    time.sleep(1.0)
    a = C["Mara"]
    a.war(True)
    time.sleep(0.6)
    log_mark = mark("Mara")
    start = time.time()
    a.commands.send(f"attack {orc} force")
    dead_since = None
    next_heal = start + 8.0
    while time.time() - start < timeout:
        time.sleep(1.0)
        if time.time() >= next_heal:
            # A fresh unarmored archer loses to an Orc in under a minute; only the time Mara needs to kill it is measured, so keep her up.
            sset("Mara", f"[set Hits {C['Mara'].state.get('maxHits', 77)}")
            next_heal = time.time() + 8.0
        swings = [s for s in (log_seconds(line) for line in since("Mara", log_mark) if "Swing: Mara ->" in line) if s is not None]
        now = time.localtime()
        now_seconds = now.tm_hour * 3600 + now.tm_min * 60 + now.tm_sec
        if len(swings) >= 3 and now_seconds - swings[-1] > 20:
            break  # she stopped shooting: the Orc is dead (a swing comes every 7 s at the slowest)
        state = mobile_state("Mara", orc)
        if state is None or state.get("isDead"):
            dead_since = dead_since or time.time()
            if time.time() - dead_since >= 2.0:
                break
        else:
            dead_since = None
            if not a.state.get("inWarMode", True):
                a.war(True)
                a.commands.send(f"attack {orc} force")
    a.war(False)
    a.commands.send("stop")
    return kill_seconds(log_mark, (dead_since or time.time()) - start)


def give_arrows() -> None:
    """A shot costs an arrow and a fresh archer carries about 75, which a few fights use up; a swing without ammunition does nothing."""
    go_to(adm, C["Mara"])
    staff_target(adm, "[Add Arrow 600", str(C["Mara"].state["charID"]))  # a stack at her feet: a container target puts nothing inside
    time.sleep(2.5)
    world = json.loads(open(os.path.join(session("Mara")["dir"], "cuoworld.json"), encoding="utf-8-sig").read())
    for item in world["items"]:
        if item.get("graphic") == 0xF3F and item.get("amount", 0) >= 100:
            C["Mara"].move(item["serial"], str(C["Mara"].state["backpackID"]), item["amount"])
    time.sleep(2.5)


def fights() -> None:
    equip("Mara", "bow")
    give_arrows()
    off_times, on_times = [], []
    for i in range(int(os.environ.get("FIGHT_PAIRS", "3"))):
        off_times.append(fight("off"))
        print(f"   fight {i + 1}: assist off, orc dead after {off_times[-1]:.0f} s", flush=True)
        on_times.append(fight("on"))
        print(f"   fight {i + 1}: assist on,  orc dead after {on_times[-1]:.0f} s", flush=True)
    admin_say("[TestOnlyNoviceFlag off", 0.8)
    mean_off, mean_on = sum(off_times) / len(off_times), sum(on_times) / len(on_times)
    # The engine's Orc has 96-120 hit points, not the 58-72 the first model used, so the absolute times are about 1.6 times the model's
    # (86 s off, 28 s on); the ratio is what the assist changes.
    record("F1 a fresh archer kills a Wrestling-60 Orc much faster with the assist", "model scaled to a 96-120 hp Orc: about 140 s off, about 45 s on; ratio about 3 (three fights each)",
           f"off {[round(t) for t in off_times]} mean {mean_off:.0f} s; on {[round(t) for t in on_times]} mean {mean_on:.0f} s; ratio {mean_off / max(mean_on, 1):.1f}",
           mean_on < mean_off / 1.8 and 60 <= mean_off <= 400 and 15 <= mean_on <= 150)


def main() -> int:
    stages = [("baseline", baseline), ("delay", delay), ("damage", damage), ("hit", hit_rates), ("notfor", not_for), ("gain", gain_odds), ("fights", fights)]
    only = sys.argv[1:] or [s for s, _ in stages]
    for label, body in stages:
        if label in only:
            stage(label, body)
    failed = [r for r in results if not r[1]]
    print(f"\n{len(results) - len(failed)}/{len(results)} cases passed", flush=True)
    for case_id, _ in failed:
        print("FAILED:", case_id)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
