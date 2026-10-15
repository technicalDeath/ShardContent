"""Folds the farm's notes (work/botfarm/notes.jsonl) and the bots' status files into one report: work/botfarm/report.md.

    python aggregate.py [--out report.md]

Each note is a finding one bot made on its way (a message it met, a thing it had to work out, a death, a stall). The report groups them by category and
counts how many bots met each one, so what many professions trip over rises to the top.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import time
from collections import defaultdict
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
FARM = os.path.join(ROOT, "work", "botfarm")

ORDER = ["death", "danger", "combat", "healing", "potions", "bank", "shop", "sell", "money", "loot", "craft", "cook", "fish", "mine", "tame", "training", "weight", "stuck", "bot", "message"]


NOISE = re.compile(r"world is saving|World save|Your skill in|has increased|begins to rain|stops raining|Thy current bank balance|Bot\w+: (bank|balance|withdraw)|has changed by|You have (gained|lost) a little|Opening door|"
                   r"protection of the town guards|bank guard protection|protected from theft|You begin applying|You finish applying|You create the item|You failed to create", re.I)


def load_notes():
    rows = []
    try:
        for line in open(os.path.join(FARM, "notes.jsonl"), encoding="utf-8"):
            try:
                rows.append(json.loads(line))
            except ValueError:
                pass
    except OSError:
        pass
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(FARM, "report.md"))
    a = ap.parse_args()
    notes = load_notes()
    by_key = defaultdict(lambda: {"bots": set(), "profs": set(), "text": "", "cat": "", "t": ""})
    for n in notes:
        if "that follows a new" in n.get("text", ""):
            continue                                  # the early wording claimed every cornering happened in Britain
        if n.get("key") == "ghostwalk":
            continue                                  # an early wrong explanation (the cause is war mode, key ghostwar)
        if n.get("category") == "message" and NOISE.search(n.get("text", "")):
            continue
        g = by_key[(n.get("category"), n.get("key"))]
        g["bots"].add(n["bot"])
        g["profs"].add(n["profession"])
        g["text"] = g["text"] or n["text"]
        g["cat"] = n.get("category")
        g["t"] = g["t"] or n.get("t")
    out = [f"# Bot farm report ({time.strftime('%Y-%m-%d %H:%M:%S')})", ""]
    out.append("## Bots")
    out.append("")
    out.append("| Bot | Profession | Up | Kills | Deaths | Gold | Best skills (value, gains) |")
    out.append("| --- | --- | --- | --- | --- | --- | --- |")
    for p in sorted(glob.glob(os.path.join(FARM, "Bot*", "status.json"))):
        try:
            s = json.load(open(p, encoding="utf-8"))
        except (OSError, ValueError):
            continue
        sk = ", ".join(f"{k} {v}" for k, v in list((s.get("skills") or {}).items())[:3])
        g = sum((s.get("gains") or {}).values())
        out.append(f"| {s['name']} | {s['profession']} | {s['uptime'] // 60} min | {s.get('kills', 0)} | {s.get('deaths', 0)} | {s.get('gold', 0)} | {sk}; {g} gains |")
    out.append("")
    # skill gains over every bot's life, so slow and fast skills show side by side
    gains = defaultdict(lambda: [0, set()])
    for p in glob.glob(os.path.join(FARM, "Bot*", "status.json")):
        try:
            st = json.load(open(p, encoding="utf-8"))
        except (OSError, ValueError):
            continue
        for k, v in (st.get("gains") or {}).items():
            gains[k][0] += v
            gains[k][1].add(st["name"])
    if gains:
        out.append("## Skill gains (count of +0.1..+0.4 messages across all bots)")
        out.append("")
        for k, (n, bots) in sorted(gains.items(), key=lambda kv: -kv[1][0])[:25]:
            out.append(f"- {k}: {n} gains by {len(bots)} bot(s)")
        out.append("")
    out.append("## Shared memory (what the bots have learned and now use)")
    out.append("")
    try:
        import memory as M
        mem = M.SharedMemory("report", "report")
        out.append("```")
        out.append(mem.summary())
        out.append("```")
        out.append("")
        w = mem.state["world"]
        out.append("Shops seen (position: name, items on sale, items bought):")
        for xy, v in sorted(w["vendors"].items()):
            out.append(f"- {xy} {v['name']}: sells {len(v['stock'])} kinds ({', '.join(list(v['stock'])[:6])}), buys {len(v['buys'])} kinds ({', '.join(f'{k} {p}gp' for k, p in list(v['buys'].items())[:6])})")
        out.append("")
        out.append("Gathering spots (kind, spot: worked / failed, last reason):")
        for kind, spots in w["res"].items():
            for key, r in spots.items():
                out.append(f"- {kind} {key}: {r['ok']} / {r['fail']} {r['reason']}")
        out.append("")
        out.append("Crafts (craft, item: attempts, successes, skill gains), by every profession that logged them:")
        for scope in ("prof",):
            pass
        import glob as _g
        crafts = defaultdict(lambda: [0, 0, 0])
        for pth in _g.glob(os.path.join(M.MEMDIR, "prof-*.jsonl")):
            for line in open(pth, encoding="utf-8"):
                try:
                    e = json.loads(line)
                except ValueError:
                    continue
                if e.get("k") == "craft":
                    c = crafts[(e["craft"], e["item"])]
                    c[0] += 1
                    c[1] += 1 if e.get("ok") else 0
                    c[2] += 1 if e.get("gain") else 0
        for (craft, item), (n, ok, gain) in sorted(crafts.items(), key=lambda kv: -kv[1][0])[:25]:
            out.append(f"- {craft} / {item}: {n} tries, {ok} made ({ok * 100 // max(n, 1)}%), {gain} gains ({gain * 100 // max(n, 1)}%)")
        out.append("")
        out.append("Skill gains by what the bot was doing when it rose:")
        gains = defaultdict(lambda: defaultdict(int))
        for pth in _g.glob(os.path.join(M.MEMDIR, "prof-*.jsonl")):
            for line in open(pth, encoding="utf-8"):
                try:
                    e = json.loads(line)
                except ValueError:
                    continue
                if e.get("k") == "gain":
                    gains[e["skill"]][e.get("action", "?")] += 1
        for skill, acts in sorted(gains.items(), key=lambda kv: -sum(kv[1].values()))[:15]:
            out.append(f"- {skill}: " + ", ".join(f"{a} x{n}" for a, n in sorted(acts.items(), key=lambda kv: -kv[1])[:4]))
        out.append("")
    except Exception as exc:  # the report must still be written
        out.append(f"(memory summary failed: {exc})")
        out.append("")
    cats = sorted({g["cat"] for g in by_key.values()}, key=lambda c: ORDER.index(c) if c in ORDER else 99)
    for cat in cats:
        rows = sorted((g for g in by_key.values() if g["cat"] == cat), key=lambda g: -len(g["bots"]))
        out.append(f"## {cat} ({len(rows)})")
        out.append("")
        for g in rows[:40]:
            out.append(f"- [{len(g['bots'])} bot(s): {', '.join(sorted(g['profs']))}] {g['text'][:260]}")
        out.append("")
    open(a.out, "w", encoding="utf-8").write("\n".join(out))
    print(f"{len(notes)} notes, {len(by_key)} distinct -> {a.out}")


if __name__ == "__main__":
    main()
