"""Stage "a blue attacks a criminal first, is Knocked Out, and is executed" for the real ClassicUO client (skill player-client-shots).

    python ShardContent/tests/scenarios/hot-zones/murder_report_realclient_blue.py <victim-name> <criminal-name>

The victim and the criminal run on Navrey until the blue is Knocked Out (the 90-second state is kept in the account, so it survives
the victim logging out). The script then prints HANDOVER and waits for the file work/murder-report/go.flag: stop the victim's Navrey
session, log the real client in as the victim, create the file. The criminal then Executes the victim and the victim's real client
shows the stock report gump (an Execute is murder even though the blue attacked first). Run on a disposable host.
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

from navrey_session import connect  # noqa: E402
from staff_command import go_to, staff_target  # noqa: E402
from uo import Event  # noqa: E402

OUTSIDE = (2775, 2166, 0)    # outside the Hot Zone: the blue's attack on the criminal is lawful and so is the criminal's answer
START = (2800, 2297, 6)      # where a character comes back after a logout and a real-client login
FLAG = os.path.join(WORKSPACE, "work", "murder-report", "go.flag")
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


def hit(attacker, victim_serial: str, victim_hits, seconds: float = 30) -> bool:
    start = victim_hits()
    attacker.war(True)
    time.sleep(0.6)
    attacker.commands.send(f"attack {victim_serial} force")
    landed = wait_until(lambda: victim_hits() < start, seconds)
    attacker.war(False)
    attacker.commands.send("stop")
    return landed


def main() -> int:
    victim_name, criminal_name = sys.argv[1], sys.argv[2]
    adm, blue, red = connect("admin"), connect(victim_name), connect(criminal_name)
    blue_serial, red_serial = str(blue.state["charID"]), str(red.state["charID"])
    for who in (blue, red):
        go_to(adm, who)
        s = str(who.state["charID"])
        if who.state.get("charGhost"):
            staff_target(adm, "[Resurrect", s)
        staff_target(adm, "[set Criminal false", s)
        staff_target(adm, "[set Kills 0", s)
        staff_target(adm, f"[set Hits {who.state.get('maxHits', 60)}", s)
        # the staff session can only target what it can see, so each character is placed while it stands beside them
        x = OUTSIDE[0] if who is red else OUTSIDE[0] + 1
        staff_target(adm, f'[set Location "({x}, {OUTSIDE[1]}, {OUTSIDE[2]})"', s)
    go_to(adm, red)
    staff_target(adm, "[set Criminal true", red_serial)
    time.sleep(3)

    struck = hit(blue, red_serial, lambda: int(red.state.get("hits", 0)))
    print(f"{victim_name} struck {criminal_name} first, landed {struck}; {victim_name} is {blue.state.get('notoriety')}", flush=True)
    staff_target(adm, "[set Criminal true", red_serial)
    staff_target(adm, f"[set Hits {red.state.get('maxHits', 60)}", red_serial)
    before = audit("knocked-out", "entered", victim_name)
    staff_target(adm, "[set Hits 1", blue_serial)
    red.war(True)
    time.sleep(0.6)
    red.commands.send(f"attack {blue_serial} force")
    knocked = wait_until(lambda: audit("knocked-out", "entered", victim_name) > before, 40)
    red.war(False)
    red.commands.send("stop")
    print(f"{victim_name} Knocked Out: {knocked}", flush=True)
    if not knocked:
        return 1

    if os.path.exists(FLAG):
        os.remove(FLAG)
    print("HANDOVER: stop the victim's Navrey session, log the real client in as them, then create", FLAG, flush=True)
    if not wait_until(lambda: os.path.exists(FLAG), 80, 1.0):
        print("no handover within 80 seconds", flush=True)
        return 1

    # a real-client login puts the character at the start area: bring the criminal there rather than the other way round
    go_to(adm, red)
    staff_target(adm, f'[set Location "({START[0]}, {START[1] + 1}, {START[2]})"', red_serial)
    adm.say(f"[go {START[0]} {START[1]} {START[2]}")
    time.sleep(2.5)
    staff_target(adm, "[set Criminal true", red_serial)
    red.events.drain()
    red.say("[Execute")
    if red.wait_for(Event.TARGET_REQUEST, timeout=5) is None:
        print("no execute cursor", flush=True)
        return 1
    red.target(blue_serial)
    time.sleep(3)
    print(f"{criminal_name} executed {victim_name}; the report gump follows in about four seconds", flush=True)
    return 0


if __name__ == "__main__":
    code = main()
    sys.stdout.flush()
    os._exit(code)
