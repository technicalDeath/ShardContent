"""Measures what one headless Navrey client costs under different settings, so the farm can fit more bots on one PC.

    python memprobe.py [variant ...]

Each variant starts the probe bot's client (BotProbeA, created on first use), lets it sit in the world for --settle seconds, reads its working set and
private bytes, and stops it by PID. Variants are named in VARIANTS below (environment variables and settings.json overrides).
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import farm_launch as fl  # noqa: E402

VARIANTS = {
    "base": ({}, {}),
    "opengl": ({"FNA3D_FORCE_DRIVER": "OpenGL"}, {}),
    "d3d11": ({"FNA3D_FORCE_DRIVER": "D3D11"}, {}),
    "heap256": ({"DOTNET_GCHeapHardLimit": "0x10000000"}, {}),
    "opengl-heap256": ({"FNA3D_FORCE_DRIVER": "OpenGL", "DOTNET_GCHeapHardLimit": "0x10000000"}, {}),
    "lean": ({"NAVREY_LEAN": "1"}, {}),
    "lean-opengl": ({"NAVREY_LEAN": "1", "FNA3D_FORCE_DRIVER": "OpenGL"}, {}),
    "lean-d3d11": ({"NAVREY_LEAN": "1", "FNA3D_FORCE_DRIVER": "D3D11"}, {}),
    "lean-gen0": ({"NAVREY_LEAN": "1", "FNA3D_FORCE_DRIVER": "D3D11", "DOTNET_GCgen0size": "0x1000000"}, {}),
    "lean-noconc": ({"NAVREY_LEAN": "1", "FNA3D_FORCE_DRIVER": "D3D11", "DOTNET_gcConcurrent": "0"}, {}),
    "lean-gen0-noconc": ({"NAVREY_LEAN": "1", "FNA3D_FORCE_DRIVER": "D3D11", "DOTNET_GCgen0size": "0x1000000", "DOTNET_gcConcurrent": "0"}, {}),
}


def measure(pid):
    r = subprocess.run(["powershell", "-NoProfile", "-Command",
                        f"$p = Get-Process -Id {pid}; '{{0}} {{1}}' -f [int]($p.WorkingSet64/1MB), [int]($p.PrivateMemorySize64/1MB)"], capture_output=True, text=True)
    try:
        ws, priv = (int(v) for v in r.stdout.split())
        return ws, priv
    except ValueError:
        return None, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("variants", nargs="*", default=["base"])
    ap.add_argument("--name", default="BotProbeA")
    ap.add_argument("--settle", type=float, default=60)
    ap.add_argument("--cuo", help="a different client build, e.g. Navrey/bin/Release/net10.0/cuo.dll")
    a = ap.parse_args()
    if a.cuo:
        fl.CUO = os.path.abspath(a.cuo)
    results = {}
    for v in a.variants:
        env, settings = VARIANTS[v]
        r = fl.start(a.name, 13, extra_env=env, settings=settings)
        if not r.get("ok"):
            print(v, "did not get in game:", r)
            if r.get("pid"):
                subprocess.run(["taskkill", "/PID", str(r["pid"]), "/F"], capture_output=True)
            continue
        time.sleep(a.settle)
        ws, priv = measure(r["pid"])
        print(f"   free commit now {fl.commit_free_mb()} MB", flush=True)
        results[v] = {"ws_mb": ws, "private_mb": priv}
        print(f"{v:16} working set {ws} MB, private {priv} MB", flush=True)
        if fl.is_client(r["pid"], a.name):
            subprocess.run(["taskkill", "/PID", str(r["pid"]), "/F"], capture_output=True)
        time.sleep(3)
    json.dump(results, open(os.path.join(fl.ROOT, "work", "botfarm", "memprobe.json"), "a", encoding="utf-8"))


if __name__ == "__main__":
    main()
