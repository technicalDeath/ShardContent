"""Writes the shard's world-generation data for the greater-Britain spawn areas and wildlife (signed off by the owner on
2026-10-18) from the plan's draft spawner records (plan.py):

  data/world-generation/alpha2b/greater-britain-spawn-areas.json   re-themed stock spawners (same GUID and place, so world
                                                                    generation replaces them), new wildlife and area
                                                                    spawners (fixed name-based GUIDs)

  python build_data.py PLAN-DRAFT.json

The light scenery planned beside the areas was dropped the same day: the owner judged the scenes illogical to look at.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.normpath(os.path.join(HERE, "..", "..", "data", "world-generation", "alpha2b"))


def main(argv):
    draft = json.load(open(argv[0], encoding="utf-8"))
    json.dump(draft, open(os.path.join(DATA, "greater-britain-spawn-areas.json"), "w", encoding="utf-8", newline="\n"), indent=2)
    print("spawners", len(draft))


if __name__ == "__main__":
    main(sys.argv[1:])
