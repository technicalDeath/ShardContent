"""The bot farm's release pipeline: one command that checks the brain tree, records a release line, and restarts a cohort of brains onto it.

    python farm_release.py --check [--smoke-hours 0.2] [--skip-patch-tests]
        (a) the gates in work/botfarm/patches (test_no_shadow, test_borrow, test_main_last), every other patch test there and the tree's own tests in
            tests/ (a patch test that fails under both folder conventions is STALE and only listed; a tree test that fails FAILS the check), (b) every brain class constructed and run for the smoke hours against the simulator's FakeClient
            (sim/farm_sim.py --smoke: any exception in a tick or a construction failure fails the check), (c) a release line appended to
            work/botfarm/releases.jsonl: the release id (git describe of ShardContent when a tag exists, always with a content hash of the brain tree), the
            gates' results, the patch-test tallies, the smoke scoreboard. Exit 1 when a gate, a smoke run or the construction of a brain fails.
    python farm_release.py --restart COHORT [--per-minute 3] [--reason TEXT] [--force]
        restarts the brains of a cohort (all | a feature name of work/botfarm/features.json | a comma list of bot names) at rule boundaries (the brain is paused,
        which it honours at the top of its next tick, then stopped by a PID checked against the process table; the supervisor starts it again on the current
        tree), at most --per-minute bots a minute, refusing while an A/B window file work/botfarm/ab-window.json is open (its "until" in the future, or no
        "until"). Nothing is restarted unless the last release line is a passing --check of the current tree (--force overrides). Writes operator.log.
    python farm_release.py --release [--cohort NAME]   the check, then the restart, in one go.
    python farm_release.py --status                    the last release lines, the A/B window, and whether the tree matches the last checked release.
    python farm_release.py --ab-open HOURS --ab-note TEXT / --ab-close    open or close the A/B window file.

The branch-and-tag flow (OPERATING.md, "Releases") pins a tag per release once the brain tree has a branch; until the owner says so, the release id is the
content hash and git describe of the ShardContent checkout as it is.
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
SCENARIOS = os.path.abspath(os.path.join(HERE, ".."))
ROOT = os.path.abspath(os.path.join(SCENARIOS, "..", "..", ".."))
SHARDCONTENT = os.path.join(ROOT, "ShardContent")
FARM = os.path.join(ROOT, "work", "botfarm")
PATCHES = os.path.join(FARM, "patches")
RELEASES = os.path.join(FARM, "releases.jsonl")
AB_WINDOW = os.path.join(FARM, "ab-window.json")
OPERATOR_LOG = os.path.join(FARM, "operator.log")
PY = sys.executable
GATES = ("test_no_shadow.py", "test_borrow.py", "test_main_last.py", "test_basics.py")     # test_basics: every brain on the shared basics (2026-10-30)
TREE_TESTS = os.path.join(HERE, "tests")                 # the brain tree's own tests (tests/test_*.py, the patch tests' convention), run with the patch tests
TEST_TIMEOUT = 120
TREE_FILES = sorted(glob.glob(os.path.join(HERE, "*.py")) + glob.glob(os.path.join(HERE, "sim", "*.py")) + [os.path.join(SCENARIOS, "new-mage-playtest", "mage_bot.py"),
                    os.path.join(SCENARIOS, "new-mage-playtest", "knowledge.py")])


# ---- identity ---------------------------------------------------------------------------------------------------------------------------------------

def tree_hash():
    """A content hash of every brain file: the release id when no branch or tag exists yet, and the check that a restart runs what was checked."""
    h = hashlib.sha1()
    for p in TREE_FILES:
        try:
            h.update(os.path.relpath(p, SCENARIOS).encode() + b"\0" + open(p, "rb").read() + b"\0")
        except OSError:
            pass
    return h.hexdigest()[:12]


def git_describe():
    try:
        r = subprocess.run(["git", "-C", SHARDCONTENT, "describe", "--tags", "--always", "--dirty", "--match", "farm-*"], capture_output=True, text=True, timeout=20)
        out = (r.stdout or "").strip()
        if not out:
            r = subprocess.run(["git", "-C", SHARDCONTENT, "describe", "--always", "--dirty"], capture_output=True, text=True, timeout=20)
            out = (r.stdout or "").strip()
        return out or None
    except (OSError, subprocess.SubprocessError):
        return None


def release_id():
    g = git_describe()
    return f"{g}+tree-{tree_hash()}" if g else f"tree-{tree_hash()}"


# ---- the gates and the patch tests ----------------------------------------------------------------------------------------------------------------------

def run_test(path, timeout=TEST_TIMEOUT):
    """A patch test takes the bot-farm folder, or the scenarios folder (the one with bot-farm and new-mage-playtest in it), or the folder with planner.py: the
    conventions differ by author, so the folder is tried first, then the scenarios folder. Returns (ok, tail, seconds, convention)."""
    best = None
    for conv, arg in (("bot-farm", HERE), ("scenarios", SCENARIOS)):
        t0 = time.time()
        try:
            r = subprocess.run([PY, path, arg, ROOT], capture_output=True, text=True, timeout=timeout, cwd=PATCHES, errors="replace")
            ok, out = r.returncode == 0, (r.stdout or "") + (r.stderr or "")
        except subprocess.TimeoutExpired:
            ok, out = False, f"timeout after {timeout} s"
        except OSError as e:
            ok, out = False, str(e)
        tail = out.strip().splitlines()[-1][:200] if out.strip() else ""
        rec = (ok, tail, round(time.time() - t0, 1), conv)
        if ok:
            return rec
        if best is None or "ModuleNotFoundError" not in tail:
            best = rec
    return best


def run_gates():
    results = {}
    for g in GATES:
        p = os.path.join(PATCHES, g)
        if not os.path.exists(p):
            results[g] = {"ok": False, "tail": "missing", "s": 0}
            continue
        ok, tail, s, conv = run_test(p)
        results[g] = {"ok": ok, "tail": tail, "s": s}
    return results


def test_paths():
    """The patch tests in work/botfarm/patches and the tree's own tests in tests/ (named tests/<file> to tell them apart)."""
    out = [(os.path.basename(p), p) for p in sorted(glob.glob(os.path.join(PATCHES, "test_*.py")))]
    out += [("tests/" + os.path.basename(p), p) for p in sorted(glob.glob(os.path.join(TREE_TESTS, "test_*.py")))]
    return out


def run_patch_tests(skip=()):
    out = {"pass": [], "stale": [], "detail": {}}
    for name, p in test_paths():
        if name in GATES or name in skip:
            continue
        ok, tail, s, conv = run_test(p)
        out["detail"][name] = {"ok": ok, "tail": tail, "s": s, "convention": conv}
        (out["pass"] if ok else out["stale"]).append(name)
    return out


# ---- the smoke run ----------------------------------------------------------------------------------------------------------------------------------------

def run_smoke(hours, out_dir=None):
    out_dir = out_dir or os.path.join(FARM, "sim", "smoke-" + time.strftime("%Y%m%d-%H%M%S"))
    t0 = time.time()
    r = subprocess.run([PY, os.path.join(HERE, "sim", "farm_sim.py"), "--smoke", "--hours", str(hours), "--out", out_dir, "--quiet"], capture_output=True, text=True,
                       timeout=1800, errors="replace")
    board = {}
    try:
        board = json.load(open(os.path.join(out_dir, "scoreboard.json"), encoding="utf-8"))
    except (OSError, ValueError):
        pass
    return {"ok": r.returncode == 0 and bool(board), "s": round(time.time() - t0, 1), "out": out_dir, "exceptions": board.get("exceptions", {}), "crashes": board.get("crashes", []),
            "world": board.get("world", {}), "groups": {g: {"time": v.get("time"), "kills_per_h": v.get("kills_per_h")} for g, v in board.get("groups", {}).items()},
            "tail": (r.stdout or r.stderr or "").strip().splitlines()[-1][:300] if (r.stdout or r.stderr) else ""}


# ---- release lines ------------------------------------------------------------------------------------------------------------------------------------------

def releases():
    out = []
    try:
        for line in open(RELEASES, encoding="utf-8"):
            try:
                out.append(json.loads(line))
            except ValueError:
                pass
    except OSError:
        pass
    return out


def cohort_names(cohort):
    """The bot names of a cohort: 'all' (the plan files farmctl uses), a feature of features.json, a plan file, or a comma list of names."""
    if cohort in (None, "", "all"):
        import farmctl
        return [b["name"] for b in farmctl.bots()]
    if os.path.exists(cohort):
        return [b["name"] for b in json.load(open(cohort, encoding="utf-8"))]
    try:
        table = json.load(open(os.path.join(FARM, "features.json"), encoding="utf-8"))
    except (OSError, ValueError):
        table = {}
    if cohort in table and isinstance(table[cohort], list):
        return list(table[cohort])
    return [n.strip() for n in cohort.split(",") if n.strip()]


def calibration(run=None):
    """The watcher's gap 8: the newest full-board simulator run (or `run`) against the live hour, measure by measure (sim/calibrate.py compare_run). Reported in the
    release line, not a gate: the check's own smoke run is seven bots for 0.2 hours and cannot be compared with a live hour. None when there is no such run."""
    try:
        sys.path.insert(0, os.path.join(HERE, "sim"))
        import calibrate
        if run is None:
            runs = [d for d in glob.glob(os.path.join(FARM, "sim", "*")) if os.path.isfile(os.path.join(d, "scoreboard.json"))]
            runs = [d for d in runs if (json.load(open(os.path.join(d, "scoreboard.json"), encoding="utf-8")).get("bots") or 0) >= 40]
            if not runs:
                return None
            run = max(runs, key=os.path.getmtime)
        rows, _m = calibrate.compare_run(run)
        return {"run": run, "rows": rows}
    except Exception as e:
        print(f"  calibration: {type(e).__name__}: {e}")
        return None


def check(a):
    t0 = time.time()
    rid = release_id()
    print(f"release {rid}: gates ...", flush=True)
    gates = run_gates()
    for g, r in gates.items():
        print(f"  {'OK  ' if r['ok'] else 'FAIL'} {g} ({r['s']} s) {r['tail']}")
    patch = {"pass": [], "stale": [], "detail": {}}
    if not a.skip_patch_tests:
        print("patch tests ...", flush=True)
        patch = run_patch_tests()
        print(f"  {len(patch['pass'])} pass, {len(patch['stale'])} stale: " + ", ".join(patch["stale"]))
    print(f"smoke run: every brain class for {a.smoke_hours} simulated hours ...", flush=True)
    smoke = run_smoke(a.smoke_hours)
    print(f"  {'OK  ' if smoke['ok'] else 'FAIL'} in {smoke['s']} s: world {smoke['world']}; exceptions {smoke['exceptions']}; crashes {len(smoke['crashes'])}")
    for c in smoke["crashes"]:
        print(f"    {c['bot']} ({c['class']}): {c['error']}")
    calib = calibration(getattr(a, "calib_run", None))
    if calib:
        print(f"calibration against the live hour ({os.path.basename(calib['run'])}, reported, not a gate): " + "; ".join(f"{r['measure']} {r['sim']} vs {r['live']} {'ok' if r['ok'] else 'OFF'}" for r in calib["rows"]))
    tree_failed = [n for n in patch["stale"] if n.startswith("tests/")]
    if tree_failed:
        print(f"  FAIL tree tests: {', '.join(tree_failed)}")
    ok = all(r["ok"] for r in gates.values()) and smoke["ok"] and not tree_failed
    line = {"t": time.strftime("%Y-%m-%dT%H:%M:%S"), "release": rid, "tree": tree_hash(), "git": git_describe(), "ok": ok, "gates": {g: r["ok"] for g, r in gates.items()},
            "patch_tests": {"pass": len(patch["pass"]), "stale": patch["stale"]}, "smoke": {k: smoke[k] for k in ("ok", "s", "exceptions", "world", "out")},
            "smoke_crashes": [{"bot": c["bot"], "class": c["class"], "error": c["error"]} for c in smoke["crashes"]], "cohort": a.cohort or None,
            "check_s": round(time.time() - t0, 1), "by": a.by,
            "calibration": {"run": calib["run"], "ok": sum(r["ok"] for r in calib["rows"]), "of": len(calib["rows"]), "off": [r["measure"] for r in calib["rows"] if not r["ok"]]} if calib else None}
    os.makedirs(FARM, exist_ok=True)
    with open(RELEASES, "a", encoding="utf-8") as f:
        f.write(json.dumps(line) + "\n")
    report = os.path.join(FARM, "sim", "release-check-latest.json")
    os.makedirs(os.path.dirname(report), exist_ok=True)
    json.dump({"line": line, "gates": gates, "patch_tests": patch, "smoke": smoke}, open(report, "w", encoding="utf-8"), indent=1)
    print(f"{'RELEASE OK' if ok else 'RELEASE FAILED'} {rid} in {line['check_s']} s (line appended to {os.path.relpath(RELEASES, ROOT)}; detail {os.path.relpath(report, ROOT)})")
    return ok, line


# ---- the A/B window -------------------------------------------------------------------------------------------------------------------------------------------

def ab_window():
    """The open A/B window, or None: {"opened", "until", "note"}; a file without "until" stays open until deleted."""
    try:
        w = json.load(open(AB_WINDOW, encoding="utf-8"))
    except (OSError, ValueError):
        return None
    until = w.get("until")
    if until and time.time() > float(until):
        return None
    return w


def ab_open(hours, note):
    w = {"opened": time.strftime("%Y-%m-%dT%H:%M:%S"), "until": round(time.time() + hours * 3600) if hours else None, "note": note}
    json.dump(w, open(AB_WINDOW, "w", encoding="utf-8"), indent=1)
    return w


def ab_close():
    try:
        os.remove(AB_WINDOW)
        return True
    except OSError:
        return False


# ---- the restart ------------------------------------------------------------------------------------------------------------------------------------------------

def operator(text):
    with open(OPERATOR_LOG, "a", encoding="utf-8") as f:
        f.write(f"[{time.strftime('%Y-%m-%d %H:%M')}] farm_release: {text}\n")


def restart(a):
    names = cohort_names(a.cohort)
    if not names:
        print(f"no bots in the cohort {a.cohort!r}")
        return False
    w = ab_window()
    if w and not a.force:
        print(f"REFUSED: an A/B window is open since {w.get('opened')} ({w.get('note', '')}); until {time.strftime('%H:%M', time.localtime(w['until'])) if w.get('until') else 'closed by hand'}. "
              f"--ab-close ends it, --force overrides.")
        return False
    last = next((r for r in reversed(releases()) if r.get("tree") and "ok" in r), None)     # the last --check line: a restart line (no "ok") read as a failed check (the Operator, 2026-10-29)
    tree = tree_hash()
    if not a.force and (last is None or not last.get("ok") or last.get("tree") != tree):
        why = "no release line" if last is None else ("the last check failed" if not last.get("ok") else f"the tree changed since the last check ({last.get('tree')} -> {tree})")
        print(f"REFUSED: {why}; run --check first (or --force).")
        return False
    import farmctl
    import farm_launch
    sys.path.insert(0, HERE)
    rid = (last or {}).get("release", f"tree-{tree}")
    per_min = max(1, a.per_minute)
    print(f"restarting {len(names)} brain(s) of {a.cohort or 'all'} onto {rid}, {per_min} a minute, at rule boundaries", flush=True)
    operator(f"restart {a.cohort or 'all'} ({len(names)} brains) onto {rid}, {per_min}/min{': ' + a.reason if a.reason else ''}")
    done, skipped = [], []
    for i, name in enumerate(names):
        if i and i % per_min == 0:
            time.sleep(60)
        pid = farmctl.brain_pid(name)
        table = farm_launch.process_table()
        if not farm_launch.is_brain(pid, name, table):
            skipped.append(name)
            print(f"  {name}: no running brain (pid {pid}); the supervisor will start it on the new tree anyway")
            continue
        pause = os.path.join(FARM, name, "pause")
        paused_before = os.path.exists(pause)
        open(pause, "w").close()                         # the brain idles at the top of its next tick: a rule boundary, nothing mid-walk or mid-fight
        waited = 0.0
        while waited < a.boundary_wait:
            st = farmctl.read_json(os.path.join(FARM, name, "status.json"), {}) or {}
            if st.get("activity") == "paused":
                break
            time.sleep(2)
            waited += 2
        table = farm_launch.process_table()
        if farm_launch.is_brain(pid, name, table):
            subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True)
            done.append(name)
            print(f"  {name}: brain {pid} stopped after {waited:.0f} s at the boundary; the supervisor restarts it")
        else:
            skipped.append(name)
            print(f"  {name}: pid {pid} is no longer this bot's brain; left alone")
        if not paused_before:
            try:
                os.remove(pause)
            except OSError:
                pass
    operator(f"restarted {len(done)}: {', '.join(done)}" + (f"; skipped {', '.join(skipped)}" if skipped else ""))
    with open(RELEASES, "a", encoding="utf-8") as f:
        f.write(json.dumps({"t": time.strftime("%Y-%m-%dT%H:%M:%S"), "release": rid, "tree": tree, "restart": {"cohort": a.cohort or "all", "done": done, "skipped": skipped,
                                                                                                             "reason": a.reason}, "by": a.by}) + "\n")
    return True


def status():
    rs = releases()
    print(f"tree now: {release_id()}")
    w = ab_window()
    print(f"A/B window: {'open since ' + w.get('opened', '?') + ' (' + str(w.get('note', '')) + ')' if w else 'none'}")
    for r in rs[-6:]:
        if "restart" in r:
            print(f"  {r['t']} restart {r['restart']['cohort']}: {len(r['restart']['done'])} brains onto {r['release']}")
        else:
            print(f"  {r['t']} check {r['release']}: {'OK' if r.get('ok') else 'FAILED'}; gates {sum(r['gates'].values())}/{len(r['gates'])}, "
                  f"patch tests {r['patch_tests']['pass']} pass / {len(r['patch_tests']['stale'])} stale, smoke {'ok' if r['smoke']['ok'] else 'FAILED'} in {r['smoke']['s']} s")
    last = next((r for r in reversed(rs) if r.get("tree") and "restart" not in r), None)
    if last:
        print("the tree " + ("matches" if last["tree"] == tree_hash() else "has CHANGED since") + f" the last check ({last['release']})")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--release", action="store_true", help="--check then --restart")
    ap.add_argument("--restart", metavar="COHORT", default=None)
    ap.add_argument("--cohort", default=None, help="with --check or --release: the cohort named in the release line / restarted")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--smoke-hours", type=float, default=0.2)
    ap.add_argument("--calib-run", default=None, help="the full-board simulator run the check compares with the live hour (default: the newest one of 40 bots or more)")
    ap.add_argument("--skip-patch-tests", action="store_true")
    ap.add_argument("--per-minute", type=int, default=3)
    ap.add_argument("--boundary-wait", type=float, default=90, help="seconds to wait for a brain to reach its tick boundary (pause) before stopping it")
    ap.add_argument("--reason", default="")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--by", default=os.environ.get("FARM_OPERATOR", "farm_release"))
    ap.add_argument("--ab-open", type=float, default=None, metavar="HOURS", help="open an A/B window for HOURS (0: until --ab-close)")
    ap.add_argument("--ab-note", default="")
    ap.add_argument("--ab-close", action="store_true")
    a = ap.parse_args(argv)
    if a.ab_open is not None:
        w = ab_open(a.ab_open, a.ab_note)
        operator(f"A/B window opened: {w}")
        print(f"A/B window opened: {w}")
        return 0
    if a.ab_close:
        print("A/B window closed" if ab_close() else "no A/B window was open")
        operator("A/B window closed")
        return 0
    if a.status or not (a.check or a.release or a.restart):
        status()
        return 0
    rc = 0
    if a.check or a.release:
        ok, _ = check(a)
        rc = 0 if ok else 1
    if a.release and rc == 0:
        a.restart = a.cohort or "all"
    if a.restart and rc == 0:
        a.cohort = a.restart
        rc = 0 if restart(a) else 1
    return rc


if __name__ == "__main__":
    sys.exit(main())
