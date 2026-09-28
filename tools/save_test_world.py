"""Request an administrator save through Navrey and await a NEW published snapshot.

The caller owns the session: bind the admin's four files and the matching server
stdout log explicitly. This utility never launches, stops, or cleans up a process.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
import time

_ANSI = re.compile(r"\x1b\[[0-9;]*m")
_WORLD = re.compile(r"^\[[^\]]+\] (.*?) <s:Server\.World>$")


def save_world(client, server_log: Path, timeout: float = 30.0) -> dict:
    if timeout <= 0:
        raise ValueError("timeout must be positive")
    client.require_live()
    state = client.state
    age = time.time() * 1000 - state.get("updatedAtMs", 0)
    if not state.get("inGame") or not 0 <= age <= 5000:
        raise RuntimeError("Administrator client must have a fresh in-game snapshot")

    started = time.monotonic()
    deadline = started + timeout
    # Keep a handle to this log: rotation/truncation must not make old saves count.
    with server_log.open("rb") as log:
        log.seek(0, 2)
        offset = log.tell()
        pending = b""
        saw_start = False
        requests = 0

        def request():
            nonlocal requests
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("No new published world save before timeout")
            client.call("say [Save", timeout=min(10.0, remaining))
            requests += 1

        request()
        while time.monotonic() < deadline:
            if server_log.stat().st_size < offset:
                raise RuntimeError("Server log was truncated; save outcome is unverified")
            chunk = log.read()
            offset = log.tell()
            lines = (pending + chunk).split(b"\n")
            pending = lines.pop()
            retry = False
            for raw in lines:
                match = _WORLD.match(_ANSI.sub("", raw.decode("utf-8", "replace").strip()))
                if not match:
                    continue
                message = match.group(1)
                if "failed" in message.lower():
                    raise RuntimeError("Server reported a world-save failure; inspect its private log")
                if message == "Saving world":
                    saw_start = True
                if message.startswith("Writing world save snapshot done ("):
                    if saw_start:
                        return {"status": "published", "requests": requests,
                                "elapsedSeconds": round(time.monotonic() - started, 3)}
                    # [Save can be ignored while an earlier snapshot is writing.
                    # Its completion cannot prove our cleanup was included.
                    retry = True
            if retry and not saw_start and requests < 2:
                time.sleep(0.1)  # let FinishWorldSave return the world to Running
                request()
            time.sleep(0.05)
    raise TimeoutError("No new published world save before timeout; do not stop the server")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("state", "world", "cmd", "log", "server-log"):
        parser.add_argument("--" + name, required=True, type=Path)
    parser.add_argument("--timeout", type=float, default=30)
    args = parser.parse_args()
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "Navrey" / "cli"))
    from uo import Client
    client = Client(state_file=str(args.state), world_file=str(args.world),
                    cmd_file=str(args.cmd), log_file=str(args.log))
    try:
        print(json.dumps(save_world(client, args.server_log, args.timeout)))
    except (OSError, RuntimeError, TimeoutError, ValueError) as error:
        parser.exit(1, f"Save unverified: {error}\n")


if __name__ == "__main__":
    main()
