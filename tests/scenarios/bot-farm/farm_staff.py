"""Runs staff commands on the farm host from a lean admin client, for world changes while the farm is up (new spawners from the world-generation
config, counts, audits), and stops the client afterwards: a Debug admin client costs about 600 MB, which the farm does not have spare.

    python farm_staff.py "[Alpha2bWorldGen audit" ["[global count where Rabbit" ...] [--wait 90]
    python farm_staff.py "[go 1301 1760 10" "[go 1191 1780 3" --look 20     (lists the creatures around each place)

The admin account is Navrey's own (Navrey/.env), copied into the session folder as Start-NavreySession.ps1 does, never printed. Each command is
said in turn; every system line that arrives while it runs is printed, and the next command waits until the journal has been quiet for 8 seconds
(an audit prints many lines over several seconds) or --wait seconds have passed.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path[:0] = [os.path.join(HERE, "..", "..", "..", "..", "Navrey", "cli"), os.path.join(HERE, "..", "..", "..", "..", ".claude", "scripts")]
import farm_launch as fl  # noqa: E402

NAME = "FarmAdmin"


def start():
    d = os.path.join(fl.SESSIONS, NAME)
    rec_path = os.path.join(d, "session.json")
    if os.path.exists(rec_path):
        old = json.load(open(rec_path, encoding="utf-8"))
        if fl.is_client(old["pid"], NAME):
            return old["pid"]
    os.makedirs(d, exist_ok=True)
    shutil.copyfile(os.path.join(fl.NAVREY, ".env"), os.path.join(d, ".env"))
    settings = json.load(open(fl.SETTINGS, encoding="utf-8"))
    settings.update(fps=8, login_music=False, window_size={"X": 320, "Y": 240})
    json.dump(settings, open(os.path.join(d, "settings.json"), "w", encoding="utf-8"), indent=2)
    files = {k: os.path.join(d, v) for k, v in dict(cmd="cuocmd", log="cuolog", state="cuostate.json", world="cuoworld.json").items()}
    for p in list(files.values()) + [files["cmd"] + ".pid"]:
        if os.path.exists(p):
            os.remove(p)
    env = dict(os.environ, DOTNET_ROOT=os.path.dirname(fl.DOTNET), DOTNET_GCConserveMemory="9", DOTNET_TieredPGO="0", **fl.LEAN_ENV)
    proc = subprocess.Popen([fl.DOTNET, fl.LEAN_CUO, "-cmdfile", files["cmd"], "-logfile", files["log"], "-statefile", files["state"], "-worldfile", files["world"], "-headless"],
                            cwd=d, stdout=open(os.path.join(d, "stdout.log"), "wb"), stderr=open(os.path.join(d, "stderr.log"), "wb"), env=env, creationflags=0x08000000)
    json.dump(dict(name=NAME, pid=proc.pid, dir=d, cmd=files["cmd"], log=files["log"], state=files["state"], world=files["world"]), open(rec_path, "w", encoding="utf-8"))
    deadline = time.time() + 90
    while time.time() < deadline and proc.poll() is None:
        if fl.in_game(files["state"]):
            return proc.pid
        time.sleep(1)
    if proc.poll() is None:
        proc.kill()
    raise SystemExit("the admin client did not get in game")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("commands", nargs="+")
    ap.add_argument("--wait", type=float, default=90)
    ap.add_argument("--keep", action="store_true", help="leave the admin client running")
    ap.add_argument("--look", type=int, default=0, help="after each [go, list the creatures within this many tiles")
    ap.add_argument("--settle", type=float, default=3, help="seconds to let the client load the place before --look")
    args = ap.parse_args()
    pid = start()
    time.sleep(5)
    from navrey_session import connect
    c = connect(NAME)
    try:
        for cmd in args.commands:
            c.events.drain()
            print(f">>> {cmd}", flush=True)
            target = None
            if cmd.startswith("@"):
                # "@0x0000ABCD [set Location (x, y, z)": say the command, then answer its target cursor with that character
                target, cmd = cmd[1:].split(" ", 1)
            c.say(cmd)
            if target:
                from uo import Event
                if c.wait_for(Event.TARGET_REQUEST, timeout=5) is None:
                    print("    no target cursor came", flush=True)
                else:
                    c.target(target)
            started = last = time.time()
            while time.time() - started < args.wait and time.time() - last < 8:
                time.sleep(0.5)
                for ev in c.events.poll():
                    if ev.text and not ev.text.startswith("[SAY] Bot"):
                        print("   ", ev.text, flush=True)
                        last = time.time()
            if args.look and cmd.lower().startswith("[go "):
                # what stands around the place the staff character went to: the proof that a spawner there is spawning
                time.sleep(args.settle)
                seen = {}
                for m in c.mobiles(within=args.look):
                    if not (m.name or "").startswith("Bot"):
                        seen[m.name] = seen.get(m.name, 0) + 1
                print(f"    within {args.look} of {c.x},{c.y}: {dict(sorted(seen.items()))}", flush=True)
    finally:
        if not args.keep and fl.is_client(pid, NAME):
            subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True)
            print("admin client stopped", flush=True)


if __name__ == "__main__":
    sys.exit(main())
