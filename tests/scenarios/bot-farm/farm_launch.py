"""Starts many Navrey sessions at once (one headless client per bot), creating each bot's account and character on first login.

    python farm_launch.py --plan plan.json [--parallel 6] [--max 50]

plan.json is a list of {"name": "BotArcherA", "profession": 8}. A session is the same thing Start-NavreySession.ps1 makes (work/navrey-sessions/<name>/
with session.json), so `navrey_session.connect(name)` and the other tools see it. Accounts are created by the server's auto account creation on the
first login (the host must allow it, as every disposable host does); the password is random and kept only in work/accounts/<name>.env.

RAM is the limit on one PC: each headless client costs a few hundred MB. The launcher watches free memory and stops starting clients when less than
--reserve-mb is left, so "as many as fit" is what you get.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import ctypes
import json
import os
import random
import string
import subprocess
import sys
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
SESSIONS = os.path.join(ROOT, "work", "navrey-sessions")
ACCOUNTS = os.path.join(ROOT, "work", "accounts")
NAVREY = os.path.join(ROOT, "Navrey")
CUO = os.path.join(NAVREY, "bin", "Debug", "net10.0", "cuo.dll")
DOTNET = os.path.join(ROOT, "dotnet", "dotnet.exe")
SETTINGS = os.path.join(NAVREY, "settings.json")


class MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong), ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong), ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong), ("sullAvailExtendedVirtual", ctypes.c_ulonglong)]


def free_mb() -> int:
    s = MEMORYSTATUSEX()
    s.dwLength = ctypes.sizeof(s)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(s))
    return int(s.ullAvailPhys / 1048576)


def alive(pid: int) -> bool:
    try:
        out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"], capture_output=True, text=True).stdout
        return str(pid) in out
    except OSError:
        return False


def read_state(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def in_game(state_path) -> bool:
    s = read_state(state_path)
    return bool(s and s.get("inGame") and (time.time() * 1000 - s.get("updatedAtMs", 0)) < 8000)


def password_for(name: str) -> str:
    os.makedirs(ACCOUNTS, exist_ok=True)
    path = os.path.join(ACCOUNTS, f"{name}.env")
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            if line.startswith("UO_PASS="):
                return line.strip().split("=", 1)[1]
    pw = "".join(random.choice("abcdefghijkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789") for _ in range(12))
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"UO_USER={name}\nUO_PASS={pw}\n")
    return pw


def start(name: str, profession: int, create: str | None = None, timeout_login=25, timeout_create=70) -> dict:
    d = os.path.join(SESSIONS, name)
    rec_path = os.path.join(d, "session.json")
    if os.path.exists(rec_path):
        old = json.load(open(rec_path, encoding="utf-8"))
        if alive(old["pid"]):
            return {"name": name, "ok": True, "pid": old["pid"], "note": "already running"}
    os.makedirs(d, exist_ok=True)
    pw = password_for(name)
    with open(os.path.join(d, ".env"), "w", encoding="utf-8") as f:
        f.write(f"UO_USER={name}\nUO_PASS={pw}\n")
    lean = json.load(open(SETTINGS, encoding="utf-8"))
    lean.update(fps=8, login_music=False, window_size={"X": 320, "Y": 240})   # a headless bot needs no frame rate or window: saves memory and CPU
    with open(os.path.join(d, "settings.json"), "w", encoding="utf-8") as dst:
        json.dump(lean, dst, indent=2)
    files = {k: os.path.join(d, v) for k, v in dict(cmd="cuocmd", log="cuolog", state="cuostate.json", world="cuoworld.json").items()}
    for p in files.values():
        if os.path.exists(p):
            os.remove(p)
    env = dict(os.environ, DOTNET_ROOT=os.path.dirname(DOTNET), DOTNET_GCConserveMemory="9", DOTNET_TieredPGO="0")
    out = open(os.path.join(d, "stdout.log"), "wb")
    err = open(os.path.join(d, "stderr.log"), "wb")
    proc = subprocess.Popen([DOTNET, CUO, "-cmdfile", files["cmd"], "-logfile", files["log"], "-statefile", files["state"], "-worldfile", files["world"], "-headless"],
                            cwd=d, stdout=out, stderr=err, env=env, creationflags=0x08000000)  # CREATE_NO_WINDOW
    rec = dict(name=name, pid=proc.pid, dir=d, cmd=files["cmd"], log=files["log"], state=files["state"], world=files["world"], startedAt=time.strftime("%Y-%m-%dT%H:%M:%S"))
    with open(rec_path, "w", encoding="utf-8") as f:
        json.dump(rec, f)
    deadline = time.time() + timeout_login
    while time.time() < deadline and proc.poll() is None:
        if in_game(files["state"]):
            return {"name": name, "ok": True, "pid": proc.pid, "note": "existing character"}
        time.sleep(0.7)
    if proc.poll() is not None:
        return {"name": name, "ok": False, "note": f"client exited ({proc.returncode})"}
    # the character-creation screen only answers once the client has reached character selection, which a loaded PC takes a while to do: ask again until it is in game
    deadline = time.time() + timeout_create + 60
    while time.time() < deadline and proc.poll() is None:
        with open(files["cmd"], "a", encoding="ascii") as f:
            f.write((create.format(name=name) if create else f"createcharacter {name} {profession}") + "\n")
        for _ in range(14):
            time.sleep(1.0)
            if in_game(files["state"]):
                return {"name": name, "ok": True, "pid": proc.pid, "note": "created"}
    return {"name": name, "ok": False, "pid": proc.pid, "note": "not in game after createcharacter"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True)
    ap.add_argument("--parallel", type=int, default=6)
    ap.add_argument("--max", type=int, default=50)
    ap.add_argument("--reserve-mb", type=int, default=1200, help="stop starting clients when free RAM falls below this")
    args = ap.parse_args()
    plan = json.load(open(args.plan, encoding="utf-8"))[: args.max]
    results = []
    started = 0
    with cf.ThreadPoolExecutor(max_workers=args.parallel) as ex:
        pending = []
        for item in plan:
            while True:
                free = free_mb()
                if free >= args.reserve_mb:
                    break
                print(f"free RAM {free} MB is under the reserve; stopping at {started} clients", flush=True)
                plan = None
                break
            if plan is None:
                break
            pending.append(ex.submit(start, item["name"], item["profession"], item.get("create")))
            started += 1
            # stagger so the memory reading reflects the clients already loading
            time.sleep(1.5)
            while sum(1 for p in pending if not p.done()) >= args.parallel:
                time.sleep(0.5)
        for p in pending:
            r = p.result()
            results.append(r)
            print(f"{'OK ' if r['ok'] else 'FAIL'} {r['name']:18} {r.get('note', '')}", flush=True)
    ok = [r for r in results if r["ok"]]
    print(f"\n{len(ok)} of {len(results)} clients in game; free RAM now {free_mb()} MB", flush=True)
    with open(os.path.join(ROOT, "work", "botfarm-roster.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, indent=1)


if __name__ == "__main__":
    sys.exit(main())
