"""Snapshot the farm's characters as the simulator's seed roster: for every bot of the plan, its last known position, hit points, gold, skills (metrics.jsonl
last row with all_skills), backpack and worn items (the session's cuostate.json), its profession and mode. Writes work/botfarm/sim/roster.json.

    python snapshot_farm.py [--plan work/botfarm/plan-run2b.json] [--out work/botfarm/sim/roster.json]

Read-only on the farm's files. The simulator reads the roster so a calibration run starts the same 50 characters at the same skills as the farm day it is
compared with; without a roster it builds characters from profession templates (sim/world_data.py, TEMPLATES)."""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", ".."))
FARM = os.path.join(ROOT, "work", "botfarm")
SESSIONS = os.path.join(ROOT, "work", "navrey-sessions")


def last_metrics(names, path):
    """The last metrics row with all_skills per bot (one pass over the file, from the end would need the whole file anyway on Windows)."""
    last = {}
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                i = line.find('"bot": "')
                if i < 0:
                    continue
                j = line.find('"', i + 8)
                name = line[i + 8:j]
                if name in names and '"all_skills": {' in line:
                    last[name] = line
    except OSError:
        pass
    out = {}
    for n, line in last.items():
        try:
            out[n] = json.loads(line)
        except ValueError:
            pass
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", default=os.path.join(FARM, "plan-run2b.json"))
    ap.add_argument("--out", default=os.path.join(FARM, "sim", "roster.json"))
    ap.add_argument("--metrics", default=os.path.join(FARM, "metrics.jsonl"))
    a = ap.parse_args()
    plan = json.load(open(a.plan, encoding="utf-8"))
    names = {b["name"] for b in plan}
    rows = last_metrics(names, a.metrics)
    roster = []
    for b in plan:
        rec = {"name": b["name"], "profession": b["profession"], "mode": b.get("mode", "veteran"), "create": b.get("create")}
        m = rows.get(b["name"])
        if m:
            rec.update(skills=m.get("all_skills") or {}, gold=m.get("gold") or 0, pos=m.get("pos"), kills=m.get("kills") or 0, deaths=m.get("deaths") or 0, metrics_t=m.get("t"))
        try:
            s = json.load(open(os.path.join(SESSIONS, b["name"], "cuostate.json"), encoding="utf-8"))
            rec.update(backpack=[{k: i.get(k) for k in ("name", "graphic", "amount", "hue")} for i in s.get("backpack") or []],
                       equipped=[{k: i.get(k) for k in ("name", "graphic", "amount", "hue", "layer")} for i in s.get("equipped") or [] if i.get("layer") not in ("Backpack", "Bank")],
                       hp=s.get("maxHits"), max_hp=s.get("maxHits"), max_mana=s.get("maxMana"), max_stam=s.get("maxStam"),
                       str=s.get("str"), dex=s.get("dex"), int=s.get("int"), max_weight=s.get("maxWeight"), sex=s.get("sex"),
                       pos=rec.get("pos") or [s.get("charPosX"), s.get("charPosY")])
            if not rec.get("gold"):
                rec["gold"] = s.get("gold") or 0
        except (OSError, ValueError):
            pass
        roster.append(rec)
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    json.dump(roster, open(a.out, "w", encoding="utf-8"), indent=1)
    have = sum(1 for r in roster if r.get("backpack"))
    skilled = sum(1 for r in roster if r.get("skills"))
    print(f"{len(roster)} bots -> {a.out}; {have} with a backpack snapshot, {skilled} with skills from metrics")
    return 0


if __name__ == "__main__":
    sys.exit(main())
