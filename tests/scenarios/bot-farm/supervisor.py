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
LOW_MB, OK_MB = 450, 1700
shed = set()


def log(msg):
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def alive(pid):
    return farm_launch.alive(pid) if pid else False


def brain_pid(name):
    try:
        return int(open(os.path.join(FARM, name, "brain.pid")).read().strip())
    except (OSError, ValueError):
        return 0


def start_brain(name, profession, seconds):
    script = BRAINS.get(profession)
    if not script or not os.path.exists(os.path.join(HERE, script)):
        return None
    d = os.path.join(FARM, name)
    os.makedirs(d, exist_ok=True)
    env = dict(os.environ, PYTHONUNBUFFERED="1")
    p = subprocess.Popen([PY, "-u", os.path.join(HERE, script), "--name", name, "--profession", str(profession), "--for", str(int(seconds))],
                         cwd=d, stdout=open(os.path.join(d, "out.log"), "ab"), stderr=open(os.path.join(d, "err.log"), "ab"), env=env, creationflags=0x08000000)
    open(os.path.join(d, "brain.pid"), "w").write(str(p.pid))
    return p.pid


def client_pid(name):
    try:
        return json.load(open(os.path.join(farm_launch.SESSIONS, name, "session.json"), encoding="utf-8"))["pid"]
    except (OSError, ValueError, KeyError):
        return 0


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
        out.append(f"{b['name']:13} {s.get('profession', '?'):12} hp {s.get('hp', '?')}/{s.get('max_hp', '?')} kills {s.get('kills', 0):3} deaths {s.get('deaths', 0):2} gold {s.get('gold', 0):5} "
                   f"{str(s.get('rule', '')):12} {str(s.get('activity', ''))[:34]:34} age {age}s skills {s.get('skills', '')}")
    open(os.path.join(FARM, "dashboard.txt"), "w", encoding="utf-8").write(time.strftime("%H:%M:%S") + "\n" + "\n".join(out) + "\n")
    json.dump(rows, open(os.path.join(FARM, "dashboard.json"), "w"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", nargs="+", required=True)
    ap.add_argument("--hours", type=float, default=6)
    a = ap.parse_args()
    bots = []
    for p in a.plan:
        bots += json.load(open(p, encoding="utf-8"))
    end = time.time() + a.hours * 3600
    restarts = {}
    pool = cf.ThreadPoolExecutor(max_workers=2)
    pending = {}
    log(f"supervising {len(bots)} bots for {a.hours} h")
    last_metrics = 0.0
    last_report = 0.0
    while time.time() < end:
        avail = farm_launch.free_mb()
        if avail < LOW_MB:
            victim = next((n for n in SHED_ORDER if n not in shed and any(b["name"] == n for b in bots)), None)
            if victim:
                shed.add(victim)
                log(f"available memory {avail} MB is under {LOW_MB}: stopping {victim}")
                for pid in (brain_pid(victim), client_pid(victim)):
                    if alive(pid):
                        subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True)
        elif avail > OK_MB and shed:
            back = sorted(shed, key=SHED_ORDER.index)[0]
            shed.discard(back)
            log(f"available memory {avail} MB: bringing {back} back")
        for b in bots:
            name, prof = b["name"], b["profession"]
            if name in shed:
                continue
            fut = pending.get(name)
            if fut is not None:
                if not fut.done():
                    continue
                log(f"{name}: client restart -> {fut.result()}")
                pending.pop(name)
            if not alive(client_pid(name)):
                log(f"{name}: client is gone; restarting it")
                pending[name] = pool.submit(farm_launch.start, name, prof)
                restarts[name] = restarts.get(name, 0) + 1
                continue
            if not alive(brain_pid(name)):
                st = status_of(name)
                left = end - time.time()
                if left > 60:
                    pid = start_brain(name, prof, left)
                    if pid:
                        log(f"{name}: brain started (pid {pid}); previous status age {int(time.time() - st['t']) if st else 'none'}s")
                        restarts[name] = restarts.get(name, 0) + 1
        dashboard(bots)
        if time.time() - last_metrics > 60:
            last_metrics = time.time()
            with open(os.path.join(FARM, "metrics.jsonl"), "a", encoding="utf-8") as f:
                for b in bots:
                    st = status_of(b["name"])
                    if st:
                        f.write(json.dumps({"t": int(time.time()), "bot": b["name"], "prof": st.get("profession"), "hp": st.get("hp"), "gold": st.get("gold"), "kills": st.get("kills"), "deaths": st.get("deaths"),
                                            "gains": sum((st.get("gains") or {}).values()), "skills": st.get("skills"), "rule": st.get("rule"), "pos": st.get("pos")}) + "\n")
        if time.time() - last_report > 300:
            last_report = time.time()
            subprocess.run([PY, os.path.join(HERE, "aggregate.py")], capture_output=True, creationflags=0x08000000)
        time.sleep(15)


if __name__ == "__main__":
    sys.exit(main())
