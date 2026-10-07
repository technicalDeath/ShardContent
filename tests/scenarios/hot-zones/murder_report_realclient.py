"""Stage a blue's murder for the real ClassicUO client (skill player-client-shots): the victim is logged in through the real client,
the attacker and staff run on Navrey.

    # on the disposable host used by murder_report_live.py: stand the victim in the Hot Zone (next to Pike) through Navrey, stop the
    # victim's Navrey session, log the real client in as them, then
    python ShardContent/tests/scenarios/hot-zones/murder_report_realclient.py <victim-serial> <victim-name> <attacker-name> --placed

Pike strikes first in the Buccaneer's Den Hot Zone (no right to attack, so the strike is criminal), Knocks the victim Out and
Executes. The victim's client then shows the stock report gump; take the screenshots with Get-PlayerClientShot.ps1.
"""

from __future__ import annotations

import glob
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(WORKSPACE, ".claude", "scripts"))

from navrey_session import connect, session  # noqa: E402
from staff_command import staff_target  # noqa: E402
from uo import Event  # noqa: E402

HOT = (2764, 2166, 0)
SERVER_LOG = max(glob.glob(os.path.join(WORKSPACE, "work", "dev-server", "logs", "server-*.log")), key=os.path.getmtime)


def audit(category: str, decision: str, subject: str) -> int:
    with open(SERVER_LOG, errors="replace") as handle:
        text = handle.read()
    return len(re.findall(rf"Alpha2 {re.escape(category)} {re.escape(decision)}: subject=\S+?/{re.escape(subject)};", text))


def wait_until(condition, timeout: float, step: float = 0.4) -> bool:
    end = time.time() + timeout
    while time.time() < end:
        if condition():
            return True
        time.sleep(step)
    return False


def main() -> int:
    victim_serial = sys.argv[1]
    victim = sys.argv[2] if len(sys.argv) > 2 else "Wren"
    attacker = sys.argv[3] if len(sys.argv) > 3 else "Pike"
    adm, killer = connect("admin"), connect(attacker)
    killer_serial = str(killer.state["charID"])
    adm.say(f"[go {HOT[0]} {HOT[1]} {HOT[2]}")
    time.sleep(2)
    if "--placed" not in sys.argv:  # the victim has no Navrey session to read a position from, so place them beforehand
        staff_target(adm, f'[set Location "({HOT[0] + 1}, {HOT[1]}, {HOT[2]})"', victim_serial)
    staff_target(adm, f'[set Location "({HOT[0]}, {HOT[1]}, {HOT[2]})"', killer_serial)
    staff_target(adm, "[set Criminal false", killer_serial)
    staff_target(adm, "[set Kills 0", killer_serial)
    staff_target(adm, f"[set Hits {killer.state.get('maxHits', 60)}", killer_serial)
    time.sleep(3)

    killer.war(True)
    time.sleep(0.6)
    killer.commands.send(f"attack {victim_serial} force")
    time.sleep(8)
    print(f"{attacker} struck first; notoriety now {killer.state.get('notoriety')}", flush=True)

    before = audit("knocked-out", "entered", victim)
    staff_target(adm, "[set Hits 1", victim_serial)
    killer.commands.send(f"attack {victim_serial} force")
    knocked = wait_until(lambda: audit("knocked-out", "entered", victim) > before, 40)
    killer.war(False)
    killer.commands.send("stop")
    print(f"{victim} Knocked Out: {knocked}", flush=True)
    if not knocked:
        return 1

    time.sleep(2)
    killer.events.drain()
    killer.say("[Execute")
    if killer.wait_for(Event.TARGET_REQUEST, timeout=5) is None:
        print("no execute cursor", flush=True)
        return 1
    killer.target(victim_serial)
    time.sleep(3)
    print(f"{attacker} executed {victim}; the report gump follows in about four seconds", flush=True)
    return 0


if __name__ == "__main__":
    code = main()
    sys.stdout.flush()
    os._exit(code)
