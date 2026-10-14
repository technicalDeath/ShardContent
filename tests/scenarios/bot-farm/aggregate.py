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
import time
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
FARM = os.path.join(ROOT, "work", "botfarm")

ORDER = ["death", "danger", "combat", "healing", "potions", "bank", "shop", "sell", "money", "loot", "craft", "cook", "fish", "mine", "tame", "training", "weight", "stuck", "bot", "message"]


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
