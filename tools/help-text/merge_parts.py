"""Merges work/help-gumps/parts/*.skills.json and *.items.json onto base/ (the Alchemy slice) and writes ShardContent/data/help. Repeatable.

    python merge_parts.py            # dry run: report only
    python merge_parts.py --write    # backup, then write
"""
import json
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(r"C:\Users\brend\Documents\Britannia Renaissance")
PARTS = ROOT / "work" / "help-gumps" / "parts"
DATA = ROOT / "ShardContent" / "data" / "help"
BASE = ROOT / "work" / "help-gumps" / "base"   # the Alchemy slice; the merge always starts from it, so it can be repeated
write = "--write" in sys.argv

skills = json.loads((BASE / "skills.json").read_text(encoding="utf-8"))
items = json.loads((BASE / "items.json").read_text(encoding="utf-8"))
order = [name for c in skills["categories"] for name in c["skills"]]
have_skill = {s["skill"] for s in skills["skills"]}
have_key = {i["key"] for i in items["items"]}
problems = []

for path in sorted(PARTS.glob("*.skills.json")):
    part = json.loads(path.read_text(encoding="utf-8"))
    for page in part["skills"]:
        if page["skill"] in have_skill:
            problems.append(f"{path.name}: skill {page['skill']} already has a page")
            continue
        if page["skill"] not in order:
            problems.append(f"{path.name}: {page['skill']} is in no category")
        have_skill.add(page["skill"])
        skills["skills"].append(page)
    print(f"{path.name}: {len(part['skills'])} pages")

for path in sorted(PARTS.glob("*.items.json")):
    part = json.loads(path.read_text(encoding="utf-8"))
    for topic in part["items"]:
        if topic["key"] in have_key:
            problems.append(f"{path.name}: topic key {topic['key']} already exists")
            continue
        have_key.add(topic["key"])
        items["items"].append(topic)
    print(f"{path.name}: {len(part['items'])} topics")

skills["skills"].sort(key=lambda s: order.index(s["skill"]) if s["skill"] in order else 999)
missing = [n for n in order if n not in have_skill]
print("skills without a page:", missing)
print("totals:", len(skills["skills"]), "pages,", len(items["items"]), "topics")
for p in problems:
    print("PROBLEM", p)

if write:
    (DATA / "skills.json").write_text(json.dumps(skills, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    (DATA / "items.json").write_text(json.dumps(items, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    print("written to", DATA)
