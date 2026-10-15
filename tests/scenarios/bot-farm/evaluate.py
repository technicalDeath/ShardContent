"""Grades the bots' decisions from their decision logs (work/botfarm/<bot>/decisions.jsonl) and the shared memory, and lists what to fix first.

    python evaluate.py [--minutes 30]

Every bot logs each stretch of one rule (an "episode") with what it yielded: gold, kills, skill gains, hit points, deaths, distance walked. This script
adds them up per profession and rule, then looks for the patterns that mean a decision is wrong:
  - idle time:            rules that do nothing (waiting, idling) taking a large share of a bot's time;
  - fruitless effort:     long fight, craft, gather or tame episodes that earned nothing;
  - flip-flops:           two rules taking turns every few seconds (the bot cannot make up its mind);
  - deadly decisions:     the rule that was running when a bot died;
  - stuck walking:        explore or hunt episodes that moved almost no distance.
The result is work/botfarm/evaluation.md: a ranked "fix first" list (by minutes lost), per-profession tables, and a shared-memory health section.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import time
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
FARM = os.path.join(ROOT, "work", "botfarm")
MEM = os.path.join(FARM, "memory")

IDLE = {"r_wander", "r_idle", "-", "None"}
EFFORT = {"r_fight", "r_craft", "r_mine", "r_fish", "r_tame", "r_chop", "r_music", "r_earn", "r_hunt"}
WALK = {"r_explore", "r_hunt"}


def load(minutes):
    since = time.time() - minutes * 60
    eps, mems = [], []
    for p in glob.glob(os.path.join(FARM, "Bot*", "decisions.jsonl")):
        for line in open(p, encoding="utf-8"):
            try:
                e = json.loads(line)
            except ValueError:
                continue
            if e["t"] < since:
                continue
            if e["type"] == "ep":
                eps.append(e)
            elif e["type"] == "mem" and "m" in e:      # "choice" records (run to town, and so on) carry what/why, not a monster
                mems.append(e)
    return eps, mems


def memory_health(minutes):
    since = time.time() - minutes * 60
    out = []
    kinds = Counter()
    bots = defaultdict(Counter)
    total = 0
    size = 0
    for p in glob.glob(os.path.join(MEM, "*.jsonl")):
        size += os.path.getsize(p)
        for line in open(p, encoding="utf-8"):
            try:
                e = json.loads(line)
            except ValueError:
                continue
            total += 1
            if e["t"] >= since:
                kinds[(os.path.basename(p), e["k"])] += 1
                bots[e["bot"]][e["k"]] += 1
    out.append(f"{total} events in {len(glob.glob(os.path.join(MEM, '*.jsonl')))} files ({size // 1024} KB); in the last {minutes} min:")
    by_file = defaultdict(list)
    for (f, k), n in sorted(kinds.items()):
        by_file[f].append(f"{k} {n}")
    for f, items in sorted(by_file.items()):
        out.append(f"- {f}: " + ", ".join(items))
    silent = sorted(b for b in {os.path.basename(os.path.dirname(p)) for p in glob.glob(os.path.join(FARM, 'Bot*', 'status.json'))} if b not in bots)
    if silent:
        out.append(f"- bots that wrote nothing to the memory in this window: {', '.join(silent)}")
    return out, kinds


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--minutes", type=float, default=30)
    ap.add_argument("--out", default=os.path.join(FARM, "evaluation.md"))
    a = ap.parse_args()
    eps, mems = load(a.minutes)
    out = [f"# Bot decision evaluation ({time.strftime('%Y-%m-%d %H:%M')}, last {a.minutes:g} minutes)", ""]
    if not eps:
        out.append("No decision episodes logged yet.")
        open(a.out, "w", encoding="utf-8").write("\n".join(out))
        print("no episodes")
        return

    # ---- per bot: time per rule, yields --------------------------------------------------------------------
    per_bot = defaultdict(lambda: defaultdict(lambda: {"n": 0, "dur": 0.0, "gold": 0, "kills": 0, "gains": 0, "hp": 0, "died": 0, "moved": 0, "work": 0}))
    prof_of = {}
    seq = defaultdict(list)
    for e in sorted(eps, key=lambda e: e["t"]):
        r = per_bot[e["bot"]][e["rule"]]
        r["n"] += 1
        for k in ("dur", "gold", "kills", "gains", "hp", "died", "moved", "work"):
            r[k] += e.get(k, 0) or 0
        prof_of[e["bot"]] = e["prof"] + ("/newbie" if e.get("mode") == "newbie" else "")
        seq[e["bot"]].append(e)

    fixes = []          # (minutes lost, text)

    for bot, rules in per_bot.items():
        total = sum(r["dur"] for r in rules.values()) or 1
        idle = sum(r["dur"] for k, r in rules.items() if k in IDLE)
        if idle / total > 0.35 and idle > 120:
            top = max(((k, r["dur"]) for k, r in rules.items() if k in IDLE), key=lambda kv: kv[1])
            fixes.append((idle / 60, f"{bot} ({prof_of[bot]}) spent {idle / 60:.0f} of {total / 60:.0f} min idle ({top[0]}): it has nothing to do; give the brain a next step."))
        for k, r in rules.items():
            if k in EFFORT and r["dur"] > 180 and r["kills"] + r["gains"] + r["work"] == 0 and r["gold"] <= 0:
                fixes.append((r["dur"] / 60, f"{bot} ({prof_of[bot]}) spent {r['dur'] / 60:.0f} min in {k} over {r['n']} stretches and earned nothing (no kill, gain, gold or work done): the rule is chosen but does not work."))
            if k in WALK and r["dur"] > 240 and r["moved"] / max(1, r["n"]) < 3:
                fixes.append((r["dur"] / 60, f"{bot} ({prof_of[bot]}) ran {k} for {r['dur'] / 60:.0f} min but moved {r['moved'] / max(1, r['n']):.1f} tiles per stretch: it is stuck walking."))

    # ---- flip-flops: A B A B within short episodes ----------------------------------------------------------------
    for bot, s in seq.items():
        flips = Counter()
        for i in range(2, len(s)):
            if s[i]["rule"] == s[i - 2]["rule"] and s[i]["rule"] != s[i - 1]["rule"] and s[i]["dur"] < 15 and s[i - 1]["dur"] < 15:
                flips[tuple(sorted((s[i]["rule"], s[i - 1]["rule"])))] += 1
        for pair, n in flips.items():
            if n >= 8:
                fixes.append((n * 0.15, f"{bot} ({prof_of[bot]}) flips between {pair[0]} and {pair[1]} ({n} times): the two rules' conditions overlap; one should own the situation."))

    # ---- deaths: which rule was running -------------------------------------------------------------------------
    deadly = Counter()
    for e in eps:
        if e.get("died"):
            deadly[(e["prof"], e["rule"], e.get("act", ""))] += 1
    for (prof, rule, act), n in deadly.items():
        fixes.append((n * 5.0, f"{n} death(s) of a {prof} while in {rule} ({act}): check what that rule walks into."))

    fixes.sort(reverse=True)
    out.append("## Fix first (ranked by minutes lost)")
    out.append("")
    for mins, text in fixes[:25]:
        out.append(f"- **{mins:.0f}** {text}")
    if not fixes:
        out.append("- nothing flagged")
    out.append("")

    # ---- profession tables ----------------------------------------------------------------------------------------
    per_prof = defaultdict(lambda: defaultdict(lambda: {"dur": 0.0, "gold": 0, "kills": 0, "gains": 0, "hp": 0, "died": 0, "n": 0, "work": 0}))
    bots_of = defaultdict(set)
    for bot, rules in per_bot.items():
        bots_of[prof_of[bot]].add(bot)
        for k, r in rules.items():
            p = per_prof[prof_of[bot]][k]
            for f in ("dur", "gold", "kills", "gains", "hp", "died", "n", "work"):
                p[f] += r[f]
    out.append("## Time and yield by profession and rule")
    out.append("")
    out.append("Per rule: share of the profession's time, then per hour of that rule: skill gains, kills, work done (catches, crafts, ore, tames, meals, songs), gold (negative when buying or banking), and deaths.")
    out.append("")
    for prof in sorted(per_prof):
        rules = per_prof[prof]
        total = sum(r["dur"] for r in rules.values()) or 1
        gains = sum(r["gains"] for r in rules.values())
        out.append(f"### {prof} ({len(bots_of[prof])} bot(s), {total / 60:.0f} bot-minutes, {gains / (total / 3600):.0f} skill gains per hour)")
        out.append("")
        out.append("| Rule | Share | Gains/h | Kills/h | Work/h | Gold/h | Deaths |")
        out.append("| --- | --- | --- | --- | --- | --- | --- |")
        for k, r in sorted(rules.items(), key=lambda kv: -kv[1]["dur"]):
            h = max(r["dur"] / 3600, 1e-6)
            out.append(f"| {k} | {r['dur'] / total:.0%} | {r['gains'] / h:.0f} | {r['kills'] / h:.0f} | {r['work'] / h:.0f} | {r['gold'] / h:+.0f} | {r['died']} |")
        out.append("")

    # ---- the shared memory --------------------------------------------------------------------------------------
    out.append("## Shared memory health")
    out.append("")
    lines, kinds = memory_health(a.minutes)
    out += lines
    flips = Counter((m["m"], m["table"], m["final"]) for m in mems)
    out.append("")
    out.append(f"Decisions the memory changed in this window: {len(mems)}")
    for (m, t, f), n in flips.most_common(12):
        why = next((x["why"] for x in mems if x["m"] == m and x["final"] == f), "")
        out.append(f"- {m}: table said {'fight' if t else 'avoid'}, memory said {'fight' if f else 'avoid'} ({n}x) - {why}")
    out.append("")
    open(a.out, "w", encoding="utf-8").write("\n".join(out))
    print(f"{len(eps)} episodes, {len(mems)} memory decisions, {len(fixes)} findings -> {a.out}")


if __name__ == "__main__":
    main()
