"""Private working set (the memory a process holds that no other process shares) of every Navrey client, and of the farm's server."""
import json, subprocess, sys
r = subprocess.run(["powershell", "-NoProfile", "-Command",
    "Get-CimInstance Win32_PerfFormattedData_PerfProc_Process | Where-Object { $_.Name -like 'dotnet*' } | Select-Object IDProcess,WorkingSetPrivate,WorkingSet,PrivateBytes | ConvertTo-Json -Compress"],
    capture_output=True, text=True)
rows = json.loads(r.stdout or "[]")
rows = [rows] if isinstance(rows, dict) else rows
sys.path.insert(0, ".")
import farm_launch as fl
t = fl.process_table()
for d in sorted(rows, key=lambda d: -d["WorkingSetPrivate"]):
    cl = t.get(d["IDProcess"], "")
    who = "server" if "ModernUO.dll" in cl else (cl.split("navrey-sessions\\")[1].split("\\")[0] if "navrey-sessions\\" in cl else "?")
    lean = "Release" if "bin\Release" in cl else "Debug"
    print(f"{d['IDProcess']:6} {who:12} {lean:7} private WS {d['WorkingSetPrivate'] // 1048576:4} MB  WS {d['WorkingSet'] // 1048576:4} MB  private bytes {d['PrivateBytes'] // 1048576:4} MB")
