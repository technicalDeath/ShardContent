"""Writes the shard's world-generation data for the greater-Britain spawn areas and wildlife (signed off by the owner on
2026-10-18) from the plan's draft spawner records (plan.py):

  data/world-generation/alpha2b/greater-britain-spawn-areas.json   re-themed stock spawners (same GUID and place, so world
                                                                    generation replaces them), new wildlife and area
                                                                    spawners (fixed name-based GUIDs)

  python build_data.py PLAN-DRAFT.json [OUT-NAME]     (default greater-britain-spawn-areas.json; Cove: cove-spawn-areas.json)

2026-10-19 (owner sign-off): step-up and harder spawners split into groups of at most 3 spread over their areas (split_sites.py),
and the Cove plan (areas-cove.json) built the same way into its own file, listed before Britain's so Britain's wins.

The light scenery planned beside the areas was dropped the same day: the owner judged the scenes illogical to look at.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.normpath(os.path.join(HERE, "..", "..", "data", "world-generation", "alpha2b"))


def main(argv):
    draft = json.load(open(argv[0], encoding="utf-8"))
    name = argv[1] if len(argv) > 1 else "greater-britain-spawn-areas.json"
    json.dump(draft, open(os.path.join(DATA, name), "w", encoding="utf-8", newline="\n"), indent=2)
    print("spawners", len(draft))


if __name__ == "__main__":
    main(sys.argv[1:])
