"""The fast check for a live brain edit (owner, 2026-10-21: no simulator; minutes per change): the three gates (test_no_shadow, test_borrow, test_main_last) and an import of
every brain module. Exit 0 and one line 'GATES OK <tree id>' when all pass.   python gates.py"""
import importlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
for p in (os.path.join(ROOT, "Navrey", "cli"), os.path.join(ROOT, ".claude", "scripts"), os.path.join(HERE, "..", "new-mage-playtest"), HERE):
    sys.path.insert(0, p)
import farm_release  # noqa: E402

MODULES = ("bot_common", "hunter", "caster", "crafter", "tamer", "fisher", "miner", "broke_gather", "tinkerside", "task_core", "hunt_tree", "errands", "spots", "travel", "think", "buddy", "party",
           "tele", "runes", "places", "memory", "farmdb", "measured")


def main():
    gates = farm_release.run_gates()
    bad = [f"gate {g}: {r['tail']}" for g, r in gates.items() if not r["ok"]]
    for m in MODULES:
        try:
            importlib.import_module(m)
        except Exception as e:
            bad.append(f"import {m}: {type(e).__name__}: {str(e)[:100]}")
    if bad:
        print("GATES FAILED\n  " + "\n  ".join(bad))
        return 1
    print(f"GATES OK {farm_release.release_id()} ({', '.join(gates)} and {len(MODULES)} imports)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
