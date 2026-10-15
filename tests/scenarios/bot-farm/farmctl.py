"""One command-line interface to the bot farm for people and other agents: look at it, read what the bots wrote, and steer it safely.

    python farmctl.py status                      the server, the supervisor, every bot's line, free memory
    python farmctl.py health [--minutes 10]       what each bot has been doing, flags bots that are not moving
    python farmctl.py eval [--minutes 30]         grade the bots' decisions (writes work/botfarm/evaluation.md) and print the fix-first list
    python farmctl.py report                      rebuild work/botfarm/report.md (findings, skill gains, shared memory) and print its headings
    python farmctl.py bot NAME                    one bot: status, last log lines, last notes, last decisions
    python farmctl.py tail NAME [-n 40]           the end of a bot's run.log
    python farmctl.py notes [--bot B] [--category C] [-n 30]   the newest findings
    python farmctl.py memory [--kind K] [-n 20]   the shared memory: summary, or the newest events of one kind
    python farmctl.py pause NAME | resume NAME    hand a character to a human or a script (its brain idles), and give it back
    python farmctl.py restart NAME... | all       stop brains by their recorded PID (after checking the PID is that brain); the supervisor starts them again
    python farmctl.py shed NAME | unshed NAME     stop a bot (client and brain) through the supervisor's shed list, or bring it back
    python farmctl.py cmd NAME COMMAND...         run one Navrey command as that bot (pauses its brain around the command), e.g.  cmd BotMaceA skills
    python farmctl.py supervisor start|stop|status
    python farmctl.py restart-server --reason TEXT [--deploy-shard] [--deploy-engine]
                                                  a planned, controlled restart of the farm's game server: maintenance.txt, every bot stopped by checked
                                                  PID, save and stop, optional deploy of the tested DLLs (old ones backed up), start, supervisor start,
                                                  wait for the bots to log back in, maintenance.txt removed

Everything here goes through files the farm already uses; nothing kills a process without first checking its PID belongs to the farm.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
FARM = os.path.join(ROOT, "work", "botfarm")
SESSIONS = os.path.join(ROOT, "work", "navrey-sessions")
PY = sys.executable
PLANS = ["plan-all.json", "plan-more.json", "plan-adv.json", "plan-50.json"]


def cmdline(pid):
    """The command line of a process, or "" if it is gone (PowerShell's CIM query, so it works for any process the user can see)."""
    if not pid:
        return ""
    r = subprocess.run(["powershell", "-NoProfile", "-Command", f"(Get-CimInstance Win32_Process -Filter 'ProcessId={int(pid)}').CommandLine"],
                       capture_output=True, text=True)
    return (r.stdout or "").strip()


def free_mb():
    sys.path.insert(0, HERE)
    import farm_launch
    return farm_launch.free_mb()


def read_json(p, default=None):
    try:
        return json.load(open(p, encoding="utf-8"))
    except (OSError, ValueError):
        return default


def bots():
    out = []
    for p in PLANS:
        out += read_json(os.path.join(FARM, p), []) or []
    return out


def brain_pid(name):
    try:
        return int(open(os.path.join(FARM, name, "brain.pid")).read().strip())
    except (OSError, ValueError):
        return 0


def client_pid(name):
    return (read_json(os.path.join(SESSIONS, name, "session.json"), {}) or {}).get("pid", 0)


def supervisor_pids():
    r = subprocess.run(["powershell", "-NoProfile", "-Command",
                        "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object { $_.CommandLine -match 'supervisor.py' } | ForEach-Object { $_.ProcessId }"],
                       capture_output=True, text=True)
    return [int(x) for x in r.stdout.split() if x.strip().isdigit()]


def shed_list():
    try:
        return [l.strip() for l in open(os.path.join(FARM, "shed.txt"), encoding="utf-8") if l.strip() and not l.startswith("#")]
    except OSError:
        return []


def write_shed(names):
    with open(os.path.join(FARM, "shed.txt"), "w", encoding="utf-8") as f:
        f.write("# names here are stopped by the supervisor (one per line)\n" + "".join(n + "\n" for n in names))


# ---- commands ------------------------------------------------------------------------------------------------

def c_status(a):
    sup = supervisor_pids()
    print(f"supervisor: {'running pid ' + ','.join(map(str, sup)) if sup else 'NOT RUNNING'}")
    srv = subprocess.run(["powershell", "-NoProfile", "-Command",
                          "Get-CimInstance Win32_Process -Filter \"Name='dotnet.exe'\" | Where-Object { $_.CommandLine -match 'ModernUO.dll' } | ForEach-Object { $_.ProcessId }"],
                         capture_output=True, text=True).stdout.split()
    print(f"server (ModernUO.dll): {'pid ' + ','.join(srv) if srv else 'NOT RUNNING'}")
    try:
        auto = [l.strip() for l in open(os.path.join(FARM, "shed-auto.txt"), encoding="utf-8") if l.strip()]
    except OSError:
        auto = []
    print(f"available memory: {free_mb()} MB; shed by hand: {', '.join(shed_list()) or 'none'}; shed for low memory: {', '.join(auto) or 'none'}")
    try:
        print(open(os.path.join(FARM, "dashboard.txt"), encoding="utf-8").read())
    except OSError:
        print("no dashboard yet")


def c_health(a):
    subprocess.run([PY, os.path.join(HERE, "health.py"), str(a.minutes)])


def c_eval(a):
    subprocess.run([PY, os.path.join(HERE, "evaluate.py"), "--minutes", str(a.minutes)])
    text = open(os.path.join(FARM, "evaluation.md"), encoding="utf-8").read()
    part = text.split("## Time and yield")[0]
    print(part)


def c_report(a):
    subprocess.run([PY, os.path.join(HERE, "aggregate.py")])
    for line in open(os.path.join(FARM, "report.md"), encoding="utf-8"):
        if line.startswith("#"):
            print(line.rstrip())


def c_bot(a):
    st = read_json(os.path.join(FARM, a.name, "status.json"))
    if not st:
        print("no status.json for", a.name)
    else:
        age = int(time.time() - st["t"])
        print(json.dumps({k: st.get(k) for k in ("name", "profession", "rule", "activity", "hp", "max_hp", "pos", "gold", "kills", "deaths", "skills", "gains", "uptime")}, indent=1), f"\n(status written {age}s ago)")
    print(f"brain pid {brain_pid(a.name)}, client pid {client_pid(a.name)}, paused: {os.path.exists(os.path.join(FARM, a.name, 'pause'))}")
    print("--- run.log")
    c_tail(argparse.Namespace(name=a.name, n=15))
    print("--- last decisions")
    try:
        for line in open(os.path.join(FARM, a.name, "decisions.jsonl"), encoding="utf-8").readlines()[-8:]:
            print(line.rstrip()[:220])
    except OSError:
        pass
    print("--- last notes")
    c_notes(argparse.Namespace(bot=a.name, category=None, n=8))


def c_tail(a):
    try:
        lines = open(os.path.join(FARM, a.name, "run.log"), encoding="utf-8", errors="replace").readlines()
    except OSError:
        print("no run.log")
        return
    for l in lines[-a.n:]:
        print(l.rstrip()[:260])


def c_notes(a):
    rows = []
    try:
        for line in open(os.path.join(FARM, "notes.jsonl"), encoding="utf-8"):
            try:
                n = json.loads(line)
            except ValueError:
                continue
            if a.bot and n.get("bot") != a.bot:
                continue
            if a.category and n.get("category") != a.category:
                continue
            rows.append(n)
    except OSError:
        pass
    for n in rows[-a.n:]:
        print(f"{n['t']} {n['bot']:12} [{n['category']}] {n['text'][:220]}")


def c_memory(a):
    sys.path.insert(0, HERE)
    import memory as M
    if not a.kind:
        print(M.SharedMemory("farmctl", "farmctl").summary())
        return
    rows = []
    for p in glob.glob(os.path.join(M.MEMDIR, "*.jsonl")):
        for line in open(p, encoding="utf-8"):
            try:
                e = json.loads(line)
            except ValueError:
                continue
            if e.get("k") == a.kind:
                rows.append((e["t"], os.path.basename(p), e))
    for t, f, e in sorted(rows, key=lambda r: r[0])[-a.n:]:
        print(time.strftime("%H:%M:%S", time.localtime(t)), f, json.dumps({k: v for k, v in e.items() if k not in ("t",)})[:220])


def c_pause(a):
    open(os.path.join(FARM, a.name, "pause"), "w").close()
    print(f"{a.name}: paused (its brain idles at the next tick; the character stands still)")


def c_resume(a):
    try:
        os.remove(os.path.join(FARM, a.name, "pause"))
    except OSError:
        pass
    print(f"{a.name}: resumed")


def c_restart(a):
    names = [b["name"] for b in bots()] if a.names == ["all"] else a.names
    for i, n in enumerate(names):
        pid = brain_pid(n)
        line = cmdline(pid)
        if pid and "bot-farm" in line and "python" in line.lower() and f"--name {n} " in line + " ":
            subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True)
            print(f"{n}: stopped brain {pid}; the supervisor starts it again within ~20 s")
        else:
            print(f"{n}: pid {pid} is not this bot's brain (gone or reused); the supervisor will start a new one")
        if a.names == ["all"] and i % 6 == 5:
            time.sleep(20)              # starting 20 brains at once costs a burst of memory; go in batches


def c_shed(a):
    names = shed_list()
    if a.name not in names:
        names.append(a.name)
    write_shed(names)
    print(f"{a.name}: in shed.txt; the supervisor stops its client and brain within ~20 s")


def c_unshed(a):
    write_shed([n for n in shed_list() if n != a.name])
    print(f"{a.name}: removed from shed.txt; the supervisor starts it again")


def c_cmd(a):
    sys.path[:0] = [os.path.join(ROOT, "Navrey", "cli"), os.path.join(ROOT, ".claude", "scripts")]
    from navrey_session import connect
    pause = os.path.join(FARM, a.name, "pause")
    was_paused = os.path.exists(pause)
    open(pause, "w").close()
    try:
        time.sleep(0 if was_paused else 4)          # let the brain finish its tick so two drivers do not interleave commands
        c = connect(a.name)
        for line in c.call(" ".join(a.command), timeout=a.timeout):
            print(line)
    finally:
        if not was_paused and not a.keep_paused:
            os.remove(pause)


def c_supervisor(a):
    pids = supervisor_pids()
    if a.action == "status":
        print("running: " + ", ".join(map(str, pids)) if pids else "not running")
        try:
            print("".join(open(os.path.join(FARM, "supervisor.log"), encoding="utf-8").readlines()[-10:]))
        except OSError:
            pass
    elif a.action == "stop":
        for p in pids:
            subprocess.run(["taskkill", "/PID", str(p), "/F"], capture_output=True)
            print(f"stopped supervisor {p} (bots keep running; nothing restarts them until it is started again)")
    elif a.action == "start":
        if pids:
            print("already running:", pids)
            return
        plans = [p for p in PLANS if os.path.exists(os.path.join(FARM, p))]
        subprocess.Popen([PY, "-u", os.path.join(HERE, "supervisor.py"), "--plan", *plans, "--hours", str(a.hours)], cwd=FARM,
                         stdout=open(os.path.join(FARM, "supervisor.out"), "ab"), stderr=open(os.path.join(FARM, "supervisor.err"), "ab"), creationflags=0x08000000)
        print(f"started the supervisor for {a.hours} h with {plans}")


def pwsh(script, *args):
    """Run one of the workspace's .claude/scripts with PowerShell 7 through the toolchain helper."""
    # PowerShell 7 itself (the workspace scripts and Use-Toolchain.ps1 need it; Windows PowerShell 5 fails on them): on PATH, or the Store alias
    import shutil
    exe = shutil.which("pwsh") or os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "WindowsApps", "pwsh.exe")
    r = subprocess.run([exe, "-NoProfile", "-File", os.path.join(ROOT, ".claude", "scripts", script), *args], cwd=ROOT, capture_output=True, text=True)
    out = (r.stdout or "") + (r.stderr or "")
    if r.returncode != 0:
        raise SystemExit(f"{script} failed ({r.returncode}): {out[-400:]}")
    return out


def c_restart_server(a):
    sys.path.insert(0, HERE)
    import farm_launch as fl
    marker = os.path.join(FARM, "maintenance.txt")
    open(marker, "w", encoding="utf-8").write(f"{time.strftime('%Y-%m-%d %H:%M')} expected 10 min: {a.reason}\n")
    with open(os.path.join(FARM, "operator.log"), "a", encoding="utf-8") as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M')} farmctl: START planned server restart: {a.reason}\n")
    print("maintenance.txt written")
    c_supervisor(argparse.Namespace(action="stop", hours=8))
    table = fl.process_table()
    n = 0
    for b in bots():
        name = b["name"]
        for pid, ok in ((brain_pid(name), fl.is_brain(brain_pid(name), name, table)), (client_pid(name), fl.is_client(client_pid(name), name, table))):
            if ok:
                subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True)
                n += 1
    print(f"stopped {n} bot processes")
    print(pwsh("Stop-DevServer.ps1").strip().splitlines()[-1:])
    asm = os.path.join(ROOT, "work", "hosts", "farm", "Assemblies")
    if a.deploy_shard or a.deploy_engine:
        backup = os.path.join(ROOT, "work", "hosts", "farm", "Assemblies-backup-" + time.strftime("%Y%m%d-%H%M%S"))
        os.makedirs(backup, exist_ok=True)
        import shutil
        for dll, src, wanted in (("BritanniaRenaissance.Content.dll", os.path.join(ROOT, "ShardContent", "src", "BritanniaRenaissance.Content", "bin", "Release", "net10.0", "BritanniaRenaissance.Content.dll"), a.deploy_shard),
                                 ("UOContent.dll", os.path.join(ROOT, "work", "agent-verification", "modernuo-output", "UOContent.dll"), a.deploy_engine)):
            if wanted:
                shutil.copy2(os.path.join(asm, dll), backup)
                shutil.copy2(src, os.path.join(asm, dll))
                print(f"deployed {dll} (old one in {backup})")
    for sess in glob.glob(os.path.join(SESSIONS, "Bot*", "cuocmd.pid")):
        os.remove(sess)                  # no bot client is running now: every agent lock is stale
    print(pwsh("Start-DevServer.ps1", "-DistributionPath", "work/hosts/farm").strip().splitlines()[-1:])
    c_supervisor(argparse.Namespace(action="start", hours=a.hours))
    deadline = time.time() + 600
    want = [b["name"] for b in bots() if b["name"] not in shed_list()]
    while time.time() < deadline:
        time.sleep(15)
        live = [nm for nm in want if (read_json(os.path.join(SESSIONS, nm, "cuostate.json"), {}) or {}).get("inGame")]
        print(f"{len(live)} of {len(want)} bots back in game")
        if len(live) >= len(want) - 2:
            break
    os.remove(marker)
    with open(os.path.join(FARM, "operator.log"), "a", encoding="utf-8") as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M')} farmctl: END planned server restart\n")
    print("maintenance.txt removed")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status").set_defaults(f=c_status)
    p = sub.add_parser("health"); p.add_argument("--minutes", type=float, default=10); p.set_defaults(f=c_health)
    p = sub.add_parser("eval"); p.add_argument("--minutes", type=float, default=30); p.set_defaults(f=c_eval)
    sub.add_parser("report").set_defaults(f=c_report)
    p = sub.add_parser("bot"); p.add_argument("name"); p.set_defaults(f=c_bot)
    p = sub.add_parser("tail"); p.add_argument("name"); p.add_argument("-n", type=int, default=40); p.set_defaults(f=c_tail)
    p = sub.add_parser("notes"); p.add_argument("--bot"); p.add_argument("--category"); p.add_argument("-n", type=int, default=30); p.set_defaults(f=c_notes)
    p = sub.add_parser("memory"); p.add_argument("--kind"); p.add_argument("-n", type=int, default=20); p.set_defaults(f=c_memory)
    p = sub.add_parser("pause"); p.add_argument("name"); p.set_defaults(f=c_pause)
    p = sub.add_parser("resume"); p.add_argument("name"); p.set_defaults(f=c_resume)
    p = sub.add_parser("restart"); p.add_argument("names", nargs="+"); p.set_defaults(f=c_restart)
    p = sub.add_parser("shed"); p.add_argument("name"); p.set_defaults(f=c_shed)
    p = sub.add_parser("unshed"); p.add_argument("name"); p.set_defaults(f=c_unshed)
    p = sub.add_parser("cmd"); p.add_argument("name"); p.add_argument("command", nargs=argparse.REMAINDER); p.add_argument("--timeout", type=float, default=10)
    p.add_argument("--keep-paused", action="store_true"); p.set_defaults(f=c_cmd)
    p = sub.add_parser("supervisor"); p.add_argument("action", choices=["start", "stop", "status"]); p.add_argument("--hours", type=float, default=8); p.set_defaults(f=c_supervisor)
    p = sub.add_parser("restart-server"); p.add_argument("--reason", required=True); p.add_argument("--deploy-shard", action="store_true")
    p.add_argument("--deploy-engine", action="store_true"); p.add_argument("--hours", type=float, default=8); p.set_defaults(f=c_restart_server)
    a = ap.parse_args()
    a.f(a)


if __name__ == "__main__":
    main()
