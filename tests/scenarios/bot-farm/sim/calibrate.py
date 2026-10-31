"""Compare the simulator with the farm: the farm's measures for one day (work/botfarm/metrics.jsonl, memory/world.jsonl) beside a simulator scoreboard.

    python calibrate.py --day 2026-10-19 [--sim work/botfarm/sim/run-.../scoreboard.json] [--out work/botfarm/sim/calibration-2026-10-19.md]

Farm side (per group: fighter, caster, crafter, gatherer, tamer, as work/botfarm-watch/scorecard.py groups them):
  time shares of the rules (work / travel / rest / dead / other), kills and deaths per bot-hour (the brains' own counters in metrics, first to last row of each
  bot in the window), carried gold per bot-hour, main-skill points and skill gains per bot-hour, and the walking speed (tiles per minute between rows a minute
  apart, median and 90th percentile of the rows that moved). Read-only on the farm's files.
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import statistics
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from farm_sim import FARM, MAIN, group, rule_cat  # noqa: E402


def day_window(day):
    t0 = time.mktime(time.strptime(day, "%Y-%m-%d"))
    return t0, t0 + 86400


def farm_measures(day, metrics=None):
    since, until = day_window(day)
    metrics = metrics or os.path.join(FARM, "metrics.jsonl")
    use = collections.defaultdict(collections.Counter)
    botmins = collections.Counter()
    first, last, prev = {}, {}, {}
    speeds = []
    prof_of = {}
    with open(metrics, encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                r = json.loads(line)
            except ValueError:
                continue
            t = r.get("t", 0)
            if not since <= t < until:
                continue
            b = r["bot"]
            prof_of[b] = r.get("prof") or prof_of.get(b)
            g = group(prof_of[b])
            use[g][rule_cat(g, r.get("rule"))] += 1
            botmins[g] += 1
            if b not in first or not first[b].get("all_skills"):
                first.setdefault(b, r)
                if r.get("all_skills") and not first[b].get("all_skills"):
                    first[b] = r
            if r.get("all_skills"):
                last[b] = r
            p = prev.get(b)
            if p and r.get("pos") and p.get("pos") and 30 <= t - p["t"] <= 90:
                d = max(abs(r["pos"][0] - p["pos"][0]), abs(r["pos"][1] - p["pos"][1]))
                if d > 0:
                    speeds.append(d / (t - p["t"]) * 60)
            prev[b] = r
    hours = {g: n / 60 for g, n in botmins.items()}
    memkills = memory_kills(since, until, prof_of, os.path.join(os.path.dirname(metrics), "memory"))
    out = {"day": day, "bots": len(prev), "bot_hours": {g: round(h, 2) for g, h in hours.items()}, "groups": {}}
    if speeds:
        speeds.sort()
        out["walk_tiles_per_min"] = {"median": round(statistics.median(speeds), 1), "p90": round(speeds[int(len(speeds) * 0.9)], 1), "rows": len(speeds)}
    for g in sorted(hours):
        bots = [b for b in last if group(prof_of.get(b)) == g and b in first]
        h = max(hours[g], 1e-6)
        n = sum(use[g].values()) or 1
        kills = sum((last[b].get("kills") or 0) - (first[b].get("kills") or 0) for b in bots)
        deaths = sum((last[b].get("deaths") or 0) - (first[b].get("deaths") or 0) for b in bots)
        gold = sum((last[b].get("gold") or 0) - (first[b].get("gold") or 0) for b in bots)
        gains = sum((last[b].get("gains") or 0) - (first[b].get("gains") or 0) for b in bots)
        main = 0.0
        for b in bots:
            ms = MAIN.get(prof_of.get(b))
            if ms and first[b].get("all_skills") and last[b].get("all_skills"):
                main += last[b]["all_skills"].get(ms, 0) - first[b]["all_skills"].get(ms, 0)
        out["groups"][g] = {"bots": len(bots), "bot_hours": round(h, 2), "time": {k: round(100 * v / n, 1) for k, v in use[g].most_common()},
                            "kills_per_h": round(kills / h, 2), "kills_mem_per_h": round(memkills.get(g, 0) / h, 2), "deaths_per_h": round(deaths / h, 3), "gold_per_h": round(gold / h, 1), "main_skill_per_h": round(main / h, 3),
                            "gains_per_h": round(gains / h, 2)}
    return out


def memory_kills(since, until, prof_of, memdir):
    """Kills per group from the shared memories' fight records (outcome kill), deduplicated by bot and second, as work/botfarm-watch/scorecard.py counts them:
    the casters' own kills counter in metrics is their brain's and reads near zero."""
    import glob
    out = collections.Counter()
    seen = set()
    for mp in glob.glob(os.path.join(memdir, "*.jsonl")) + glob.glob(memdir + "-newbie" + os.sep + "*.jsonl"):
        try:
            f = open(mp, encoding="utf-8", errors="replace")
        except OSError:
            continue
        with f:
            for line in f:
                if '"outcome":"kill"' not in line:
                    continue
                try:
                    e = json.loads(line)
                except ValueError:
                    continue
                if not since <= e.get("t", 0) < until:
                    continue
                k = (e.get("bot"), round(e.get("t", 0)))
                if k in seen:
                    continue
                seen.add(k)
                out[group(prof_of.get(e.get("bot")) or e.get("prof"))] += 1
    return out


def table(farm, sim):
    rows = ["| Group | Measure | Farm | Simulator | Sim / farm |", "| --- | --- | --- | --- | --- |"]
    for g in sorted(set(farm["groups"]) | set(sim.get("groups", {}))):
        f, s = farm["groups"].get(g, {}), sim.get("groups", {}).get(g, {})
        for key, label in (("work", "work share %"), ("travel", "travel share %"), ("rest", "rest share %"), ("dead", "dead share %"), ("other", "other share %")):
            fv, sv = f.get("time", {}).get(key, 0.0), s.get("time", {}).get(key, 0.0)
            rows.append(f"| {g} | {label} | {fv} | {sv} | {ratio(fv, sv)} |")
        for key, label in (("kills_per_h", "kills per bot-hour (brain counters)"), ("kills_mem_per_h", "kills per bot-hour (memory fights; sim: world)"), ("deaths_per_h", "deaths per bot-hour"), ("gold_per_h", "carried gold per bot-hour"),
                           ("main_skill_per_h", "main skill points per bot-hour"), ("gains_per_h", "skill gains per bot-hour")):
            fv, sv = f.get(key), s.get("kills_per_h" if key == "kills_mem_per_h" else key)
            rows.append(f"| {g} | {label} | {fv if fv is not None else '-'} | {sv if sv is not None else '-'} | {ratio(fv, sv)} |")
    return "\n".join(rows)


def ratio(a, b):
    if a is None or b is None:
        return "-"
    try:
        if abs(a) < 1e-9:
            return "-" if abs(b) < 1e-9 else "inf"
        return f"{b / a:.2f}"
    except (TypeError, ZeroDivisionError):
        return "-"


# ---- a simulator run against the live hour (the watcher's gap 8, 2026-10-21) ------------------------------------------------------------------------------------

LIVE_REF = os.path.join(os.path.dirname(os.path.abspath(__file__)), "live_reference.json")


def run_measures(run):
    """The fighters' measures of one full-board run folder: kills and deaths a bot-hour, lost fights (the run's own window), lost by kind, deaths by cause, the
    errands' unmet share and the hunts' expected against actual kills."""
    import collections as _c
    import glob as _g
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from farm_sim import FIGHTERS
    board = json.load(open(os.path.join(run, "scoreboard.json"), encoding="utf-8"))
    g = board["groups"].get("fighter", {})
    farm = os.path.join(run, "farm")
    rows = [json.loads(l) for l in open(os.path.join(farm, "metrics.jsonl"), encoding="utf-8") if l.strip()]
    t0 = (min(r["t"] for r in rows) if rows else 0) + float(board.get("warmup_h") or 0) * 3600.0
    prof = {r["bot"]: r.get("prof") for r in rows}
    fights, by_kind = _c.Counter(), _c.defaultdict(_c.Counter)
    for folder in ("memory", "memory-newbie"):                      # both: newbie-mode bots write to memory-newbie
        try:
            lines = open(os.path.join(farm, folder, "world.jsonl"), encoding="utf-8", errors="replace")
        except OSError:
            continue
        for l in lines:
            if '"k":"fight"' not in l:
                continue
            e = json.loads(l)
            if e.get("t", 0) >= t0 - 1 and prof.get(e.get("bot")) in FIGHTERS and e.get("outcome"):
                fights[e["outcome"]] += 1
                by_kind[e.get("m")][e["outcome"]] += 1
    causes, ends, exp_k, act_k = _c.Counter(), _c.Counter(), 0.0, 0.0
    for f in _g.glob(os.path.join(farm, "*", "decisions.jsonl")):
        if prof.get(os.path.basename(os.path.dirname(f))) not in FIGHTERS:
            continue
        for l in open(f, encoding="utf-8", errors="replace"):
            if '"type":"ev"' not in l:
                continue
            e = json.loads(l)
            if e.get("t", 0) < t0:
                continue
            if e.get("ev") == "death":
                causes["".join(ch for ch in str(e.get("killer", "")).lower().replace("a ", "", 1) if ch.isalpha())] += 1
            if e.get("ev") == "task_end":
                ends[e.get("why")] += 1
                if e.get("task") in ("hunt", "tour2") and e.get("work_min"):
                    exp_k += float((e.get("expected") or {}).get("kills", 0) or 0) * float(e["work_min"]) / 60.0
                    act_k += float((e.get("actual") or {}).get("kills", 0) or 0)
    lost = fights["lost"] + fights["flee"]
    return {"kills_per_h": g.get("kills_per_h"), "deaths_per_h": g.get("deaths_per_h"), "lost_pct": round(100.0 * lost / max(1, fights["kill"] + lost), 1),
            "unmet_share": round(ends["unmet"] / max(1, sum(ends.values())), 3), "predicted_over_actual_kills": round(exp_k / max(1.0, act_k), 2),
            "lost_by_kind": {k: round((v["lost"] + v["flee"]) / max(1, v["kill"] + v["lost"] + v["flee"]), 2) for k, v in by_kind.items() if sum(v.values()) >= 4},
            "deaths_by_cause": dict(causes.most_common(8)), "bots": g.get("bots"), "bot_hours": g.get("bot_hours")}


def compare_run(run, ref_path=LIVE_REF):
    """[{measure, live, sim, ok}] of a run against the live reference, with its tolerances (a ratio, or an absolute band for shares)."""
    ref = json.load(open(ref_path, encoding="utf-8"))
    m = run_measures(run)
    out = []
    for k, r in ref["measures"].items():
        v = m.get(k)
        if v is None:
            out.append({"measure": k, "live": r["live"], "sim": None, "ok": False})
            continue
        if "band" in r:
            ok = abs(float(v) - r["live"]) <= r["band"]
        else:
            ok = r["live"] / r["tol"] <= float(v) <= r["live"] * r["tol"]
        out.append({"measure": k, "live": r["live"], "sim": v, "ok": bool(ok)})
    for kind, live in ref.get("lost_by_kind", {}).items():
        v = m["lost_by_kind"].get(kind)
        out.append({"measure": f"lost share: {kind}", "live": live, "sim": v, "ok": v is not None and abs(v - live) <= 0.25})
    return out, m


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--day", default=time.strftime("%Y-%m-%d"))
    ap.add_argument("--sim", default=None, help="a simulator run's scoreboard.json")
    ap.add_argument("--metrics", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--run", default=None, help="a full-board run folder: its fighters against the live hour (live_reference.json), measure by measure")
    a = ap.parse_args(argv)
    if a.run:
        rows, m = compare_run(a.run)
        print("| Measure | Live | Simulator | Within tolerance |")
        print("| --- | --- | --- | --- |")
        for r in rows:
            print(f"| {r['measure']} | {r['live']} | {r['sim']} | {'yes' if r['ok'] else 'no'} |")
        print(f"deaths by cause: {m['deaths_by_cause']}")
        return 0 if all(r["ok"] for r in rows) else 1
    farm = farm_measures(a.day, a.metrics)
    farm_path = os.path.join(FARM, "sim", f"farm-{a.day}.json")
    os.makedirs(os.path.dirname(farm_path), exist_ok=True)
    json.dump(farm, open(farm_path, "w", encoding="utf-8"), indent=1)
    lines = [f"# Farm measures for {a.day}", "", f"Bots {farm['bots']}; bot-hours {farm['bot_hours']}; walking {farm.get('walk_tiles_per_min')} tiles per minute", ""]
    sim = json.load(open(a.sim, encoding="utf-8")) if a.sim else {"groups": {}}
    if a.sim:
        lines += [f"Simulator run: {a.sim} ({sim.get('bots')} bots, {sim.get('sim_hours')} simulated hours in {sim.get('real_seconds')} s)", ""]
    lines.append(table(farm, sim))
    text = "\n".join(lines) + "\n"
    print(text)
    if a.out:
        open(a.out, "w", encoding="utf-8").write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
