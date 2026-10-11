"""Shared helpers for the decorating test rig (Start-DecorRig.ps1 writes work/decorating/rig.json; these read it).

  rig.py state                       print the rig record
  rig.py say "<staff command>"       run a staff command from the rig's admin session (retries while the snapshot is stale)

Library use:
  import rig; rig.tp(1450, 1588, 20); rig.say("[GlobalLight 0"); rig.lay("site4-v8"); rig.shot("door", OUT_DIR)
"""
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.normpath(os.path.join(HERE, "..", "..", "..", ".."))
STATE = os.path.join(WORKSPACE, "work", "decorating", "rig.json")
sys.path.insert(0, os.path.join(WORKSPACE, ".claude", "scripts"))
sys.path.insert(0, os.path.join(WORKSPACE, "ShardContent", "tools", "cosmetic-catalog"))


def state():
    if not os.path.exists(STATE):
        raise SystemExit("no rig: run ShardContent/tools/world-decorating/rig/Start-DecorRig.ps1 first")
    return json.load(open(STATE, encoding="utf-8-sig"))


def save(s):
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    json.dump(s, open(STATE, "w"), indent=1)


def staff(tries=8):
    """The admin Navrey session. Right after a server command its snapshot can look stale or from the future, so retry."""
    from navrey_session import connect
    err = None
    for _ in range(tries):
        try:
            return connect("admin", max_age_ms=15000)
        except Exception as e:      # noqa: BLE001
            err = e
            time.sleep(2)
    raise err


def say(command, wait=1.0):
    staff().say(command)
    time.sleep(wait)


def tp(x, y, z=0):
    """Move the camera character. The staff character must first stand where the camera character IS NOW so its client knows the entity,
    otherwise [set Location silently does nothing."""
    from staff_command import staff_target
    s = state()
    cur = s.get("cam", [633, 858, 0])
    st = staff()
    st.say("[go %d %d %d" % tuple(cur))
    time.sleep(1.8)
    staff_target(st, '[set Location "(%d, %d, %d)"' % (x, y, z), s["serial"])
    time.sleep(0.6)
    s["cam"] = [x, y, z]
    save(s)


def lay(layout, wait=4.0):
    """Lay a placement file from work/cosmetics/layouts/<layout>.json, or 'clear' to remove what the last lay created."""
    say("[TestOnlyDecor %s %s" % (state()["serial"], layout), wait)


def walkgrid(x, y, w, h, dumps=3, gap=6.0):
    """Ask the server for the walkable floor and every server item in a rectangle: work/cosmetics/walkgrid.json.

    A creature (an NPC, a pet, the camera character) blocks the tile it stands on in the server's floor check, so one dump can lose floor cells.
    It first clears any laid layout (laid furniture blocks cells too). This takes `dumps` dumps `gap` seconds apart and keeps a cell as walkable if ANY dump found it so. Move the camera character out of the
    rectangle first."""
    path = os.path.join(WORKSPACE, "work", "cosmetics", "walkgrid.json")
    lay("clear", 2.0)            # furniture laid by an earlier lay would block floor cells and corrupt the grid
    merged = None
    for i in range(dumps):
        if i:
            time.sleep(gap)
        say("[TestOnlyWalkGrid %d %d %d %d" % (x, y, w, h), 3.0)
        g = json.load(open(path))
        if merged is None:
            merged = g
        else:
            for j, row in enumerate(g["rows"]):
                for k, z in enumerate(row):
                    if merged["rows"][j][k] is None and z is not None:
                        merged["rows"][j][k] = z
    json.dump(merged, open(path, "w"))
    return path


def shot(name, out_dir, settle=3.0):
    """Screenshot the real client and save the cropped game view (15,58)-(918,603) as <out_dir>/<name>.png."""
    import pngtools
    r = subprocess.run(["powershell.exe", "-NoProfile", "-File", os.path.join(WORKSPACE, ".claude", "scripts", "Get-PlayerClientShot.ps1"),
                        "-Name", state()["camera"]], capture_output=True, text=True, timeout=120)
    lines = [l.strip() for l in r.stdout.splitlines() if l.strip().lower().endswith(".png")]
    if not lines:
        raise RuntimeError("no screenshot path in: " + r.stdout + r.stderr)
    _w, _h, px = pngtools.read_png(lines[-1])
    os.makedirs(out_dir, exist_ok=True)
    dest = os.path.join(out_dir, name + ".png")
    pngtools.write_png(dest, pngtools.crop(px, 15, 58, 918, 603))
    return dest


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "state":
        print(json.dumps(state(), indent=1))
    elif len(sys.argv) >= 3 and sys.argv[1] == "say":
        say(sys.argv[2])
    else:
        print(__doc__)
