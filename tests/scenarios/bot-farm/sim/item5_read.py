"""The item 5 read of a simulator run (docs/Bot-Farm-Decision-Core-Evidence.md, "Item 5"): the fighters' scoreboard row, the lost-fight share from the run's
OWN window (the scoreboard's lost column counts the seeded memory's history too), the core's events by kind (rung, gate_used, tele_used, journey by kind,
tour2 tasks, camp_travel) and where the fighters stood (sides and towns seen).

    python sim/item5_read.py <run folder> [<run folder> ...]
"""
from __future__ import annotations

import collections
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..")))
sys.path.insert(0, HERE)

from farm_sim import FIGHTERS  # noqa: E402


def read(run):
    farm = os.path.join(run, "farm")
    board = json.load(open(os.path.join(run, "scoreboard.json"), encoding="utf-8"))
    rows = []
    for line in open(os.path.join(farm, "metrics.jsonl"), encoding="utf-8"):
        try:
            rows.append(json.loads(line))
        except ValueError:
            pass
    t0 = min(r["t"] for r in rows) if rows else 0
    prof_of = {r["bot"]: r.get("prof") for r in rows}
    fights = collections.Counter()
    try:
        for line in open(os.path.join(farm, "memory", "world.jsonl"), encoding="utf-8", errors="replace"):
            if '"k":"fight"' not in line:
                continue
            try:
                ev = json.loads(line)
            except ValueError:
                continue
            if ev.get("t", 0) >= t0 - 1 and prof_of.get(ev.get("bot")) in FIGHTERS and ev.get("outcome"):
                fights[ev["outcome"]] += 1
    except OSError:
        pass
    evs = collections.Counter()
    journeys = collections.Counter()
    sides = collections.Counter()
    towns = collections.Counter()
    rung_to = collections.Counter()
    for path in glob.glob(os.path.join(farm, "*", "decisions.jsonl")):
        bot = os.path.basename(os.path.dirname(path))
        if prof_of.get(bot) not in FIGHTERS:
            continue
        for line in open(path, encoding="utf-8", errors="replace"):
            if '"type":"ev"' not in line:
                continue
            try:
                ev = json.loads(line)
            except ValueError:
                continue
            k = ev.get("ev")
            if k in ("rung", "gate_used", "tele_used", "journey", "leg_failed", "rune_recall", "camp_travel", "tour2_alone", "loot_turn", "party_form", "party_join", "party_heal", "party_invite"):
                evs[k] += 1
            if k == "journey":
                journeys[ev.get("how")] += 1
            if k == "rung":
                rung_to[ev.get("to")] += 1
            if k == "task_start":
                evs["task_start:" + str(ev.get("task"))] += 1
                if ev.get("side") and ev["side"] != "surface":
                    sides[ev["side"]] += 1
                if ev.get("town") and ev["town"] != "Britain":
                    towns[ev["town"]] += 1
            if k == "task_end" and ev.get("task") in ("hunt", "tour2"):
                evs["kills_tier" + str(ev.get("tier") or "?")] += int((ev.get("actual") or {}).get("kills", 0) or 0)
    g = board["groups"].get("fighter", {})
    t = g.get("time", {})
    return {"run": os.path.basename(run.rstrip("\\/")), "bots": g.get("bots"), "bot_h": g.get("bot_hours"), "work": t.get("work", 0), "travel": t.get("travel", 0), "rest": t.get("rest", 0),
            "kills_h": g.get("kills_per_h"), "deaths_h": g.get("deaths_per_h"), "gold_h": g.get("gold_per_h"), "lost_pct": round(100.0 * fights["lost"] / max(1, fights["kill"] + fights["lost"]), 1),
            "fights": dict(fights), "flips_h": g.get("rule_flips_per_h"), "list_rules": g.get("list_rules_acted"), "exceptions": board.get("exceptions"),
            "events": dict(evs), "journeys": dict(journeys), "rung_to": dict(rung_to), "sides": dict(sides), "towns": dict(towns), "world": board.get("world")}


def main(argv):
    out = [read(r) for r in argv]
    print("| Run | Work | Travel | Rest | Kills / bot-h | Deaths / bot-h | Net worth / bot-h | Lost fights (own window) | Flips / bot-h | Exceptions |")
    print("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for r in out:
        print(f"| {r['run']} | {r['work']}% | {r['travel']}% | {r['rest']}% | {r['kills_h']} | {r['deaths_h']} | {r['gold_h']:+} | {r['lost_pct']}% of {r['fights'].get('kill', 0) + r['fights'].get('lost', 0)} | {r['flips_h']} | {sum((r['exceptions'] or {}).values())} |")
    for r in out:
        print(f"\n{r['run']}: events {json.dumps(r['events'], sort_keys=True)}\n  journeys {r['journeys']}  rung {r['rung_to']}  dungeon tasks by side {r['sides']}  errands in other towns {r['towns']}\n  world {r['world']}")
    json.dump(out, open(os.path.join(argv[0], "item5_read.json"), "w", encoding="utf-8"), indent=1)


if __name__ == "__main__":
    main(sys.argv[1:])
