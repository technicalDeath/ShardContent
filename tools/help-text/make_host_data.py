"""Writes the help data a test host loads: the shipped files, with a placeholder page for every skill that has none yet (host only, never shipped)."""
import json, sys
from pathlib import Path

src = Path(sys.argv[1]); dst = Path(sys.argv[2]); dst.mkdir(parents=True, exist_ok=True)
skills = json.loads((src / "skills.json").read_text(encoding="utf-8"))
have = {s["skill"] for s in skills["skills"]}
for cat in skills["categories"]:
    for name in cat["skills"]:
        if name not in have:
            skills["skills"].append({"skill": name, "items": [], "paragraphs": ["# What it is", "This page is not written yet."]})
(dst / "skills.json").write_text(json.dumps(skills, indent=2), encoding="utf-8")
(dst / "items.json").write_text((src / "items.json").read_text(encoding="utf-8"), encoding="utf-8")
print("host help data written:", len(skills["skills"]), "skill pages")
