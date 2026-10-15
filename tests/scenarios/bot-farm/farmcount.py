"""One line on the farm's size: clients in game by client build, and free RAM and commit. `python farmcount.py`"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import farm_launch as fl  # noqa: E402

t = fl.process_table()
builds, n, ingame = {}, 0, 0
for p in ("plan-all.json", "plan-more.json", "plan-adv.json", "plan-50.json"):
    try:
        plan = json.load(open(os.path.join(fl.ROOT, "work", "botfarm", p), encoding="utf-8"))
    except OSError:
        continue
    for b in plan:
        try:
            pid = json.load(open(os.path.join(fl.SESSIONS, b["name"], "session.json")))["pid"]
        except (OSError, ValueError, KeyError):
            continue
        if fl.is_client(pid, b["name"], t):
            n += 1
            ingame += bool(fl.in_game(os.path.join(fl.SESSIONS, b["name"], "cuostate.json")))
            build = next((d for d in ("Lean3", "Lean2", "Release", "Debug") if f"\\{d}\\" in t[pid]), "?")
            builds[build] = builds.get(build, 0) + 1
print(f"clients {n} ({ingame} in game) {builds}; free RAM {fl.free_mb()} MB, free commit {fl.commit_free_mb()} MB")
