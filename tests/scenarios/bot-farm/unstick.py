"""Moves wedged bots out with a staff command, the way a player gets out with Help > "I'm stuck" (which the bots cannot press: Navrey has no
command for the client's Help button). A bot writes a line to work/botfarm/wedged.jsonl when no step in any direction has moved it three times in
ten minutes (bot_common.step_out); this takes each recent request whose bot is still on that tile, sends the lean admin client there (farm_staff)
and sets the bot's Location to the front of the west bank. Bots can also be named on the command line.

    python unstick.py [BotName ...]
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

WEDGED = os.path.join(FARM, "wedged.jsonl")
DONE = os.path.join(FARM, "unstuck.json")
SAFE_FALLBACK = (1426, 1692)            # in front of the west bank (a wall tile of the walk map: used only when the map is not available)


def safe_spot():
    """The walkable tile nearest the bank's standing spot (the gazetteer and the walk map), else the old constant."""
    try:
        import gazetteer as gz
        import walkroute
        bank = gz.near("bank", SAFE_FALLBACK[0], SAFE_FALLBACK[1], n=1)
        bank = bank[0] if bank else None
        bx, by = (bank["x"], bank["y"]) if isinstance(bank, dict) else (bank[0], bank[1]) if bank else SAFE_FALLBACK
        s = walkroute.get().snap(bx, by, 8)
        return (int(s[0]), int(s[1])) if s else SAFE_FALLBACK
    except Exception:
        return SAFE_FALLBACK


SAFE = safe_spot()


def mark_staff_move(name):
    """Touch <bot dir>/staff_moved: the brain's teleport watcher then ignores the jump (it is a staff move, not a teleporter; see tele.py)."""
    try:
        d = os.path.join(FARM, name)
        if os.path.isdir(d):
            open(os.path.join(d, "staff_moved"), "w").write(str(time.time()))
    except OSError:
        pass


def state(name):
    try:
        return json.load(open(os.path.join(fl.SESSIONS, name, "cuostate.json"), encoding="utf-8"))
    except (OSError, ValueError):
        return None


def relog(name):
    """The player's other way out: log out and back in. A client whose walker is wedged (every step only turns the character, as BotTailorBR's at
    1448,1690 for half an hour, on open ground) gets a fresh one; the supervisor restarts a client that is gone."""
    try:
        pid = json.load(open(os.path.join(fl.SESSIONS, name, "session.json"), encoding="utf-8"))["pid"]
    except (OSError, ValueError, KeyError):
        return False
    if not fl.is_client(pid, name):
        return False
    subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True)
    print(f"{name}: client {pid} stopped; the supervisor logs it back in", flush=True)
    return True


def wanted(names):
    """[(name, serial, x, y)] of bots to move: the named ones, else recent wedge requests whose bot has not moved since."""
    out = []
    if names:
        for n in names:
            s = state(n)
            if s:
                out.append((n, s["charID"], s["charPosX"], s["charPosY"]))
        return out
    try:
        done = json.load(open(DONE, encoding="utf-8"))
    except (OSError, ValueError):
        done = {}
    seen = set()
    for line in open(WEDGED, encoding="utf-8") if os.path.exists(WEDGED) else []:
        try:
            r = json.loads(line)
        except ValueError:
            continue
        key = f"{r['bot']}|{r['x']},{r['y']}|{int(r['t']) // 600}"
        if time.time() - r["t"] > 1800 or key in done or r["bot"] in seen:
            continue
        s = state(r["bot"])
        if s and abs(s["charPosX"] - r["x"]) <= 1 and abs(s["charPosY"] - r["y"]) <= 1:
            out.append((r["bot"], s["charID"], s["charPosX"], s["charPosY"]))
            seen.add(r["bot"])
            done[key] = time.time()
    json.dump(done, open(DONE, "w", encoding="utf-8"))
    return out


def main():
    todo = wanted(sys.argv[1:])
    if not todo:
        print("nobody to unstick")
        return 0
    pid = fs.start()
    time.sleep(5)
    from navrey_session import connect
    from uo import Event
    c = connect(fs.NAME)
    try:
        c.say(f"[go {SAFE[0]} {SAFE[1]}")
        time.sleep(4)
        sx, sy, sz = c.x, c.y, c.z
        for name, serial, x, y in todo:
            c.say(f"[go {x} {y}")
            time.sleep(4)
            c.events.drain()
            mark_staff_move(name)
            c.say(f"[set Location ({sx},{sy},{sz})")
            if c.wait_for(Event.TARGET_REQUEST, timeout=5) is None:
                print(f"{name}: no target cursor")
                continue
            c.target(serial)
            # did it move? Its own state file says, within a few seconds; a 2 s look once called BotTailorBR moved when it never left 1448,1690
            s = {}
            for _ in range(12):
                time.sleep(1)
                s = state(name) or {}
                if max(abs((s.get("charPosX") or x) - x), abs((s.get("charPosY") or y) - y)) > 3:
                    break
            moved = max(abs((s.get("charPosX") or x) - x), abs((s.get("charPosY") or y) - y)) > 3
            mark_staff_move(name)
            print(f"{name}: {x},{y} -> {s.get('charPosX')},{s.get('charPosY')}{'' if moved else ': not moved, relogging'}", flush=True)
            if not moved:
                relog(name)
    finally:
        if fl.is_client(pid, fs.NAME):
            subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
