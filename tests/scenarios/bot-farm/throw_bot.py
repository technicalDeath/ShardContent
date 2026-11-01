"""Throws a farm bot somewhere else in the world, as a new character of that profession would start there: the drop test for "the bots should
work if thrown most places in the world" (owner, 2026-10-31). The bot's brain is paused and stopped by its recorded PID (a brain inside a far
walk would go on issuing legs), the client's walk is stopped, the lean admin client (farm_staff) moves the character with [set Location, the
facts that tie it to its old home (home_region, roam_rested, unsafe_homes, rehome_walk, far) are dropped, and the pause is lifted: the new brain
chooses its home from where it stands (the town it is in, or for a trade with HOME_NEEDS the nearest town that has them).

    python throw_bot.py BotFisherAR 2895 676          (x y on the surface; the admin's own [go there gives the floor's z)
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path[:0] = [os.path.join(HERE, "..", "..", "..", "..", "Navrey", "cli"), os.path.join(HERE, "..", "..", "..", "..", ".claude", "scripts")]
import farm_launch as fl  # noqa: E402
import farm_staff as fs  # noqa: E402
from bot_common import FARM  # noqa: E402
from unstick import mark_staff_move, state  # noqa: E402

HOME_FACTS = ("home_region", "roam_rested", "unsafe_homes", "unsafe_count", "rehome_walk", "far", "anchor", "travel_blocked")


def brain_pid(name):
    try:
        return int(open(os.path.join(FARM, name, "brain.pid"), encoding="utf-8").read().strip())
    except (OSError, ValueError):
        return None


def main():
    name, x, y = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    s = state(name)
    if not s or not s.get("inGame"):
        raise SystemExit(f"{name} is not in game")
    pause = os.path.join(FARM, name, "pause")
    open(pause, "w").close()
    time.sleep(4)                                              # the brain finishes its tick
    pid = brain_pid(name)
    if pid and fl.is_brain(pid, name):
        subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True)       # by its recorded PID, checked to be this bot's brain: a brain inside a
                                                                                        # far walk issues legs for up to 90 s before it reads the pause
    from navrey_session import connect as _connect
    try:
        _connect(name).call("stop", timeout=5)                 # a walk the client was doing goes on without the brain: stop it, or the admin
    except Exception:                                          # arrives where the bot was (BotFisherAR walked off to 1696,1595, 2026-10-31)
        pass
    time.sleep(2)
    s = state(name) or s
    admin = fs.start()
    time.sleep(5)
    from navrey_session import connect
    from uo import Event
    c = connect(fs.NAME)
    try:
        c.say(f"[go {x} {y}")
        time.sleep(4)
        tx, ty, tz = c.x, c.y, c.z
        c.say(f"[go {s['charPosX']} {s['charPosY']}")
        time.sleep(4)
        c.events.drain()
        mark_staff_move(name)
        c.say(f"[set Location ({tx},{ty},{tz})")
        if c.wait_for(Event.TARGET_REQUEST, timeout=5) is None:
            raise SystemExit("no target cursor")
        c.target(s["charID"])
        for _ in range(15):
            time.sleep(1)
            n = state(name) or {}
            if max(abs((n.get("charPosX") or 0) - tx), abs((n.get("charPosY") or 0) - ty)) <= 3:
                break
        n = state(name) or {}
        print(f"{name}: {s['charPosX']},{s['charPosY']} -> {n.get('charPosX')},{n.get('charPosY')} (asked {tx},{ty},{tz})", flush=True)
        mark_staff_move(name)
    finally:
        if fl.is_client(admin, fs.NAME):
            subprocess.run(["taskkill", "/PID", str(admin), "/F"], capture_output=True)     # the lean admin client costs memory the farm needs
    pid2 = brain_pid(name)
    if pid2 and pid2 != pid and fl.is_brain(pid2, name):
        subprocess.run(["taskkill", "/PID", str(pid2), "/F"], capture_output=True)     # the supervisor's new one (it idled, paused): its facts are rewritten below
    p = os.path.join(FARM, name, "facts.json")
    try:
        facts = json.load(open(p, encoding="utf-8"))
        gone = [k for k in HOME_FACTS if facts.pop(k, None) is not None]
        json.dump(facts, open(p, "w", encoding="utf-8"))
        print(f"{name}: brain {pid} stopped; dropped {gone}", flush=True)
    except (OSError, ValueError) as e:
        print(f"{name}: facts not edited ({e})", flush=True)
    time.sleep(2)
    os.remove(pause)
    print(f"{name}: unpaused; the supervisor starts a new brain, which chooses its home from where it stands", flush=True)


if __name__ == "__main__":
    main()
