"""Moves running bots onto the current lean client (farm_launch.LEAN_CUO) in small batches: stops each bot's older client by its checked PID, and
the supervisor relaunches it with the farm's default client (restart the supervisor first when LEAN_CUO changes, so it launches the new build). Waits for each batch to be back in game before the next, and stops if available memory falls under --floor-mb.

    python rollout_lean.py [--batch 4] [--floor-mb 500]
"""
import argparse
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import farm_launch as fl  # noqa: E402

FARM = os.path.join(fl.ROOT, "work", "botfarm")


def bots():
    out = []
    for p in ("plan-all.json", "plan-more.json", "plan-adv.json", "plan-50.json"):
        try:
            out += json.load(open(os.path.join(FARM, p), encoding="utf-8"))
        except OSError:
            pass
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", type=int, default=4)
    ap.add_argument("--floor-mb", type=int, default=500)
    a = ap.parse_args()
    todo = []
    t = fl.process_table()
    for b in bots():
        n = b["name"]
        try:
            pid = json.load(open(os.path.join(fl.SESSIONS, n, "session.json")))["pid"]
        except (OSError, ValueError, KeyError):
            continue
        if fl.is_client(pid, n, t) and os.path.dirname(fl.LEAN_CUO).lower() not in t.get(pid, "").lower():
            todo.append((n, pid))
    print(f"{len(todo)} bots not on the current lean client ({fl.LEAN_CUO})", flush=True)
    for i in range(0, len(todo), a.batch):
        batch = todo[i:i + a.batch]
        for n, pid in batch:
            subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True)
        print(time.strftime("%H:%M:%S"), "stopped", [n for n, _ in batch], flush=True)
        deadline = time.time() + 150
        while time.time() < deadline:
            time.sleep(10)
            t = fl.process_table()
            back = 0
            for n, _ in batch:
                try:
                    pid = json.load(open(os.path.join(fl.SESSIONS, n, "session.json")))["pid"]
                except (OSError, ValueError, KeyError):
                    continue
                if fl.is_client(pid, n, t) and fl.in_game(os.path.join(fl.SESSIONS, n, "cuostate.json")):
                    back += 1
            if back == len(batch):
                break
        free = fl.free_mb()
        print(time.strftime("%H:%M:%S"), f"{back} of {len(batch)} back in game; available memory {free} MB", flush=True)
        if free < a.floor_mb:
            print("available memory is under the floor: stopping the rollout here", flush=True)
            break
    print("done", flush=True)


if __name__ == "__main__":
    main()
