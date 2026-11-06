"""Keeps the farm running unattended: starts each bot's brain, restarts a brain that exited and a client that died, and writes a dashboard.

    python supervisor.py --plan plan.json [--hours 6]

plan.json is the launcher's list of {"name", "profession"} (several files can be given: --plan a.json b.json). The clients themselves are started by
farm_launch.py; the supervisor only revives one whose process is gone. The dashboard is work/botfarm/dashboard.txt (text) and dashboard.json.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import farm_launch  # noqa: E402

ROOT = farm_launch.ROOT
FARM = os.path.join(ROOT, "work", "botfarm")
PY = sys.executable
BRAINS = {
    **{p: "hunter.py" for p in (8, 9, 10, 13, 14, 15)},
    **{p: "caster.py" for p in (11, 12, 23)},
    **{p: "crafter.py" for p in (16, 17, 18, 19)},
    20: "tamer.py", 21: "fisher.py", 22: "miner.py",
}
log_path = os.path.join(FARM, "supervisor.log")
SHED_ORDER = ["BotTamerB", "BotMageB", "BotArcherB", "BotSorcA", "BotTinkA"]     # stopped first when memory runs short, brought back when it recovers
try:
    # the extra bots of plan-50.json go first, last-added first, and their veterans before their newbies: the newbie/veteran pairs are the measurement,
    # and the original roster keeps every profession covered
    _extra = list(reversed(json.load(open(os.path.join(FARM, "plan-50.json"), encoding="utf-8"))))
    SHED_ORDER = [b["name"] for b in _extra if b.get("mode") != "newbie"] + [b["name"] for b in _extra if b.get("mode") == "newbie"] + SHED_ORDER
except (OSError, ValueError):
    pass
# floors to stop a bot at, and the room needed to bring one back; the clients got slimmer (Lean3, about 180-250 MB), so the return bar came down
COMMIT_LOW_MB, COMMIT_OK_MB = 2500, 3300
LOW_MB, OK_MB = 450, 1100
BACK_EVERY = 180          # seconds between bring-backs: a returning client needs about 30 s to reach its full size
last_back = 0.0
shed = set()
manual_done = set()


def log(msg):
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def alive(pid, image=None):
    """Is this PID a running process (and, when `image` is given, that program)? A recorded PID can be reused by an unrelated process after the original dies."""
    if not pid:
        return False
    try:
        out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH", "/FO", "CSV"], capture_output=True, text=True).stdout
    except OSError:
        return False
    rows = [r.split('","') for r in out.strip().splitlines() if r.startswith('"')]
    rows = [r for r in rows if len(r) > 1 and r[1].strip('"') == str(pid)]
    if not rows:
        return False
    return image is None or rows[0][0].strip('"').lower() == image.lower()


def cohort_bots():
    """Every bot named in features.json (a feature's treatment list, and the \"_planned\" and \"_control\" tables): the A/B measurement."""
    try:
        table = json.load(open(os.path.join(FARM, "features.json"), encoding="utf-8"))
    except (OSError, ValueError):
        return set()
    names = set()
    for k, v in table.items():
        if isinstance(v, list):
            names |= set(v)
        elif isinstance(v, dict) and k in ("_planned", "_control"):
            for lst in v.values():
                names |= set(lst)
    return names


def shed_order():
    """SHED_ORDER with the cohort bots moved to the end: losing a control or treatment bot to a memory dip spoils a comparison."""
    keep = cohort_bots()
    return [n for n in SHED_ORDER if n not in keep] + [n for n in SHED_ORDER if n in keep]


SHED_RISKY_RULES = ("r_fight", "r_flee", "r_avoid", "r_evade", "r_dungeon_out", "r_trip", "r_heal")
SHED_RISKY_HP = 0.6        # below this share of its hit points a bot is not stopped while another can be


def shed_risky(name):
    """True when stopping this bot now leaves its character in harm's way: a stopped client leaves the character standing for the logout delay,
    5 minutes (Region.DefaultLogoutDelay; zero only for Young characters, PlayerMobile.GetLogoutDelay). Fighting, fleeing, on a trip, in a dungeon
    (x 5120 and up) or hurt. BotHealAdvR, stopped at 13:04:40 18 s into a fight on Despise's lizardman floor, died there (2026-11-05)."""
    try:
        st = json.load(open(os.path.join(FARM, name, "status.json"), encoding="utf-8"))
    except (OSError, ValueError):
        return False
    if st.get("ghost"):
        return False                                       # nothing left to lose
    rule = str(st.get("rule") or "")
    pos = st.get("pos") or [0, 0]
    hp, mx = st.get("hp") or 0, st.get("max_hp") or 0
    try:
        deep = int(pos[0]) >= 5120
    except (TypeError, ValueError, IndexError):
        deep = False
    return rule in SHED_RISKY_RULES or rule.endswith(":fight") or deep or (mx > 0 and hp < SHED_RISKY_HP * mx)


def shed_victim(bots, shed):
    """The next bot to stop for memory: the first in shed_order() that is safe to stop (shed_risky), else the first."""
    names = {b["name"] for b in bots}
    cands = [n for n in shed_order() if n not in shed and n in names]
    return next((n for n in cands if not shed_risky(n)), cands[0] if cands else None)


def brain_pid(name):
    try:
        return int(open(os.path.join(FARM, name, "brain.pid")).read().strip())
    except (OSError, ValueError):
        return 0


def start_brain(name, profession, seconds, mode="veteran"):
    script = BRAINS.get(profession)
    if not script or not os.path.exists(os.path.join(HERE, script)):
        return None
    d = os.path.join(FARM, name)
    os.makedirs(d, exist_ok=True)
    env = dict(os.environ, PYTHONUNBUFFERED="1", BOT_MODE=mode)
    p = subprocess.Popen([PY, "-u", os.path.join(HERE, script), "--name", name, "--profession", str(profession), "--for", str(int(seconds))],
                         cwd=d, stdout=open(os.path.join(d, "out.log"), "ab"), stderr=open(os.path.join(d, "err.log"), "ab"), env=env, creationflags=0x08000000)
    open(os.path.join(d, "brain.pid"), "w").write(str(p.pid))
    return p.pid


def client_pid(name):
    try:
        return json.load(open(os.path.join(farm_launch.SESSIONS, name, "session.json"), encoding="utf-8"))["pid"]
    except (OSError, ValueError, KeyError):
        return 0


CLIENT_STALE = 180      # s without a fresh state file (updatedAtMs) from a live client: its writer has stopped (the client writes it many times a second)
CLIENT_SETTLE = 240     # s after the client's launch before the check applies (login and character load)
CLIENT_OFFLINE = 60     # s of fresh states saying connected False before the client counts as stale (a brief drop is not)
_offline_since = {}     # name: when its state first said connected False


def client_stale(name):
    """A live client whose cuostate.json has not been refreshed for CLIENT_STALE s, CLIENT_SETTLE s or more after its launch."""
    d = os.path.join(farm_launch.SESSIONS, name)
    try:
        launched = os.path.getmtime(os.path.join(d, "session.json"))
    except OSError:
        return False
    if time.time() - launched < CLIENT_SETTLE:
        return False
    s = farm_launch.read_state(os.path.join(d, "cuostate.json"))
    if not s or not s.get("updatedAtMs"):
        return False                                    # mid-write or not in the world yet: no verdict
    if time.time() - s["updatedAtMs"] / 1000.0 > CLIENT_STALE:
        return True
    if s.get("connected") is False:
        # a fresh state from a client the server dropped: it runs on, and its bot walks for minutes with "no step in any direction moved the
        # character" (13 clients after the farm restart's login rush, 2026-11-02 20:51)
        since = _offline_since.setdefault(name, time.time())
        return time.time() - since > CLIENT_OFFLINE
    _offline_since.pop(name, None)
    return False


def status_of(name):
    try:
        return json.load(open(os.path.join(FARM, name, "status.json"), encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def dashboard(bots):
    rows = []
    out = []
    for b in bots:
        s = status_of(b["name"])
        age = int(time.time() - s["t"]) if s else -1
        rows.append({**{k: s.get(k) for k in ("name", "profession", "rule", "activity", "hp", "max_hp", "mana", "pos", "gold", "kills", "deaths", "gains", "skills", "uptime")}, "age": age})
        if b["name"] in shed:
            out.append(f"{b['name']:13} SHED (stopped by the supervisor: {'by hand, shed.txt' if b['name'] in manual_done else 'low memory'})")
            rows[-1]["shed"] = True
            continue
        out.append(f"{b['name']:13} {s.get('profession', '?'):12} hp {s.get('hp', '?')}/{s.get('max_hp', '?')} kills {s.get('kills', 0):3} deaths {s.get('deaths', 0):2} gold {s.get('gold', 0):5} "
                   f"{str(s.get('rule', '')):12} {str(s.get('activity', ''))[:34]:34} age {age}s skills {s.get('skills', '')}")
    open(os.path.join(FARM, "dashboard.txt"), "w", encoding="utf-8").write(time.strftime("%H:%M:%S") + "\n" + "\n".join(out) + "\n")
    json.dump(rows, open(os.path.join(FARM, "dashboard.json"), "w"))


def main():
    global last_back
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", nargs="+", required=True)
    ap.add_argument("--hours", type=float, default=6)
    a = ap.parse_args()
    bots = []
    for p in a.plan:
        bots += json.load(open(p, encoding="utf-8"))
    # bots the fixed order does not name (a fresh roster such as plan-run2.json) are shed last-planned first, veterans before newbies
    global SHED_ORDER
    rest = [b for b in reversed(bots) if b["name"] not in SHED_ORDER]
    SHED_ORDER = SHED_ORDER + [b["name"] for b in rest if b.get("mode") != "newbie"] + [b["name"] for b in rest if b.get("mode") == "newbie"]
    end = time.time() + a.hours * 3600
    restarts = {}
    pool = cf.ThreadPoolExecutor(max_workers=2)
    pending = {}
    retry_at = {}
    log(f"supervising {len(bots)} bots for {a.hours} h")
    last_metrics = 0.0
    last_report = 0.0
    while time.time() < end:
        # work/botfarm/shed.txt: names (one per line) to stop by hand, e.g. to make room for a watching client; delete the line to bring the bot back
        try:
            manual = {l.strip() for l in open(os.path.join(FARM, "shed.txt"), encoding="utf-8") if l.strip() and not l.startswith("#")}
        except OSError:
            manual = set()
        for n in manual - shed - manual_done:
            manual_done.add(n)
            shed.add(n)
            log(f"{n}: stopped by shed.txt")
            table = farm_launch.process_table()
            for pid, ok in ((brain_pid(n), farm_launch.is_brain(brain_pid(n), n, table)), (client_pid(n), farm_launch.is_client(client_pid(n), n, table))):
                if ok:
                    subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True)
        for n in manual_done - manual:
            manual_done.discard(n)
            shed.discard(n)
            log(f"{n}: back in play (removed from shed.txt)")
        avail = farm_launch.free_mb()
        commit_free = farm_launch.commit_free_mb()
        with open(os.path.join(FARM, "shed-auto.txt"), "w", encoding="utf-8") as f:
            f.write("".join(n + "\n" for n in sorted(shed - manual_done)))
        if avail < LOW_MB or commit_free < COMMIT_LOW_MB:
            victim = shed_victim(bots, shed)              # a bot in no danger first (shed_risky)
            if victim:
                shed.add(victim)
                log(f"available memory {avail} MB, free commit {commit_free} MB (floors {LOW_MB}, {COMMIT_LOW_MB}): stopping {victim}")
                table = farm_launch.process_table()
                for pid, ok in ((brain_pid(victim), farm_launch.is_brain(brain_pid(victim), victim, table)), (client_pid(victim), farm_launch.is_client(client_pid(victim), victim, table))):
                    if ok:
                        subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True)
        elif avail > OK_MB and commit_free > COMMIT_OK_MB and (shed - manual_done) and time.time() - last_back > BACK_EVERY:
            last_back = time.time()
            back = sorted(shed - manual_done, key=SHED_ORDER.index)[0]
            shed.discard(back)
            log(f"available memory {avail} MB: bringing {back} back")
        table = farm_launch.process_table()           # one query per pass; every check below matches PID and command line
        for b in bots:
            name, prof = b["name"], b["profession"]
            if name in shed:
                continue
            fut = pending.get(name)
            if fut is not None:
                if not fut.done():
                    continue
                try:
                    res = fut.result()
                except Exception as e:
                    # one launch that failed must not end the supervisor: a PermissionError on a client log held by an unrecorded second client
                    # ended five supervisors in ten minutes, and every bot lost its relaunches (2026-11-02 21:00-21:09)
                    res = {"name": name, "ok": False, "note": f"{type(e).__name__}: {e}"[:200]}
                log(f"{name}: client restart -> {res}")
                pending.pop(name)
                if not res.get("ok"):
                    retry_at[name] = time.time() + 120          # a launch that failed waits two minutes before the next try
                continue                                        # the process table is from before the launch; look again next pass
            if time.time() < retry_at.get(name, 0):
                continue
            if not farm_launch.is_client(client_pid(name), name, table):
                log(f"{name}: client is gone; restarting it")
                pending[name] = pool.submit(farm_launch.start, name, prof, b.get("create"), client=b.get("client"))
                restarts[name] = restarts.get(name, 0) + 1
                continue
            if client_stale(name):
                # the client lives but its state file stopped: the brain reads a frozen world (BotWarAdvR stood "at" the bank for 10 minutes, its client log
                # showing it 10 tiles away, 2026-11-02 08:35-08:45). Both go; the next pass starts the client again ("client is gone") and then the brain
                log(f"{name}: client {client_pid(name)} has written no state for {CLIENT_STALE}+ s; stopping it and its brain")
                for pid, ok in ((brain_pid(name), farm_launch.is_brain(brain_pid(name), name, table)), (client_pid(name), farm_launch.is_client(client_pid(name), name, table))):
                    if ok and pid:
                        subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True)
                restarts[name] = restarts.get(name, 0) + 1
                continue
            bp = brain_pid(name)
            st0 = status_of(name)
            started_at = os.path.getmtime(os.path.join(FARM, name, "brain.pid")) if os.path.exists(os.path.join(FARM, name, "brain.pid")) else 0
            st_path = os.path.join(FARM, name, "status.json")
            # a status.json read mid-write (the brains truncate, then write) is empty; its mtime still says when the brain last wrote it
            last_t = st0["t"] if st0 else (os.path.getmtime(st_path) if os.path.exists(st_path) else 0)
            if farm_launch.is_brain(bp, name, table) and time.time() - started_at > 240 and time.time() - last_t > 240 and not os.path.exists(os.path.join(FARM, name, "pause")):
                log(f"{name}: brain {bp} has written no status for {int(time.time() - last_t) if last_t else 'ever'} s; killing it")
                subprocess.run(["taskkill", "/PID", str(bp), "/F"], capture_output=True)
            if not farm_launch.is_brain(brain_pid(name), name, table):
                st = status_of(name)
                left = end - time.time()
                if left > 60:
                    pid = start_brain(name, prof, left, b.get("mode", "veteran"))
                    if pid:
                        log(f"{name}: brain started (pid {pid}); previous status age {int(time.time() - st['t']) if st else 'none'}s")
                        restarts[name] = restarts.get(name, 0) + 1
        dashboard(bots)
        if time.time() - last_metrics > 60:
            last_metrics = time.time()
            with open(os.path.join(FARM, "metrics.jsonl"), "a", encoding="utf-8") as f:
                for b in bots:
                    st = status_of(b["name"])
                    if st and b["name"] not in shed and time.time() - st["t"] < 300:
                        f.write(json.dumps({"t": int(time.time()), "bot": b["name"], "prof": st.get("profession"), "hp": st.get("hp"), "gold": st.get("gold"), "kills": st.get("kills"), "deaths": st.get("deaths"),
                                            "gains": sum((st.get("gains") or {}).values()), "skills": st.get("skills"), "all_skills": st.get("all_skills"), "menus": st.get("menus"),
                                            "rule": st.get("rule"), "pos": st.get("pos")}) + "\n")
        if time.time() - last_report > 300:
            last_report = time.time()
            subprocess.run([PY, os.path.join(HERE, "aggregate.py")], capture_output=True, creationflags=0x08000000)
            subprocess.run([PY, os.path.join(HERE, "evaluate.py"), "--minutes", "30"], capture_output=True, creationflags=0x08000000)
        time.sleep(15)


if __name__ == "__main__":
    sys.exit(main())
