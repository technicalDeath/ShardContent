"""Live checks of guild chat (docs/Guild-Chat-Plan.md) on a disposable host, with real Guild and Alliance packets from Navrey.

    python -u guild_chat_live.py chat

Needs a host built by work/guild-chat/host.ps1 (the hooked UOContent, the shard DLL under test, TestOnlyProbe loaded, guildChat false in the
file), characters GcAlpha, GcBeta and GcGamma, and a staff session named GC_ADMIN (default `admin`; set GC_ADMIN to use another name). The
flag is switched in memory with [TestOnlyFlagOverride. Prints one line per case and exits non-zero on the first failure.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(WORKSPACE / ".claude" / "scripts"))

from navrey_session import connect  # noqa: E402
from staff_command import staff_target  # noqa: E402

ADMIN = os.environ.get("GC_ADMIN", "admin")
ALPHA, BETA, GAMMA = "GcAlpha", "GcBeta", "GcGamma"
HERE = (633, 858)      # where the characters start, in the open
FAR = (1394, 1716)     # Britain, a long way from HERE
HOT = (2760, 2166)      # inside a Hot Zone (Buccaneer's Den), where a lethal blow can Knock a player out
NEAR_GUILDLESS = (634, 858)


def check(condition: bool, case: str, detail: str = "") -> None:
    print(f"{'PASS' if condition else 'FAIL'} {case}{': ' + detail if detail else ''}", flush=True)
    if not condition:
        sys.exit(1)


class Rig:
    def __init__(self) -> None:
        self.admin = connect(ADMIN)
        self.p = {n: connect(n) for n in (ALPHA, BETA, GAMMA)}
        self.logs = {n: WORKSPACE / "work" / "navrey-sessions" / n / "cuolog" for n in (ALPHA, BETA, GAMMA, ADMIN)}

    def serial(self, name: str) -> str:
        return str(self.p[name].state["charID"])

    # ---- journals
    def lines(self, name: str) -> list:
        return self.logs[name].read_text(errors="replace").splitlines()

    def mark(self, name: str) -> int:
        return len(self.lines(name))

    def since(self, name: str, mark: int) -> str:
        return "\n".join(self.lines(name)[mark:])

    def said(self, name: str, mark: int, text: str, timeout: float = 6.0) -> bool:
        end = time.time() + timeout
        while time.time() < end:
            if text in self.since(name, mark):
                return True
            time.sleep(0.25)
        return text in self.since(name, mark)

    def silent(self, name: str, mark: int, text: str, seconds: float = 3.0) -> bool:
        time.sleep(seconds)
        return text not in self.since(name, mark)

    # ---- staff work
    def staff(self, command: str, who: str) -> None:
        self.admin.say(f"[go {self.serial(who)}")
        time.sleep(1.6)
        staff_target(self.admin, command, self.serial(who))

    def place(self, who: str, x: int, y: int) -> None:
        """Move a character to open ground at x, y: the admin finds the ground height there first."""
        self.admin.say(f"[go {x} {y}")
        time.sleep(2.2)
        z = int(self.admin.state["charPosZ"])
        self.staff(f'[set Location "({x}, {y}, {z})"', who)
        time.sleep(0.8)

    def flag(self, value: bool) -> None:
        mark = self.mark(ADMIN)
        self.admin.say(f"[TestOnlyFlagOverride GuildChat {'true' if value else 'false'}")
        check(self.said(ADMIN, mark, f"GuildChat in-memory = {value}"), f"flag GuildChat = {value}")

    def gumps(self, name: str) -> list:
        return [line for line in self.p[name].call("gumps") if line.strip()]

    def close_gumps(self, name: str) -> None:
        import re

        for line in self.p[name].call("gumps"):
            m = re.match(r"\[GUMP\] local (0x\w+) server (0x\w+)", line)
            if m:
                self.p[name].call(f"gumpresponse 0 gump:{m.group(2)}")
        time.sleep(0.4)


def stage_chat() -> None:
    rig = Rig()
    alpha, beta, gamma = rig.serial(ALPHA), rig.serial(BETA), rig.serial(GAMMA)

    rig.flag(False)

    # Setup: a guild of Alpha and Beta; Gamma has none. Alpha and Gamma stand together, Beta far away.
    mark = rig.mark(ADMIN)
    rig.admin.say(f"[TestOnlyGuild {alpha} Testers {beta}")
    check(rig.said(ADMIN, mark, "Guild Testers members=2"), "setup: a guild of two (Alpha, Beta)")
    for who in (ALPHA, BETA, GAMMA):
        rig.close_gumps(who)
    rig.place(ALPHA, *HERE)
    rig.place(GAMMA, *NEAR_GUILDLESS)
    rig.place(BETA, *FAR)
    rig.admin.say(f"[go {HERE[0] + 3} {HERE[1]}")
    time.sleep(2.0)

    # G1: the flag off (as shipped): today's behaviour, the line is said aloud to whoever is near, guild or not, and the far guildmate hears nothing.
    ma, mb, mg = rig.mark(ALPHA), rig.mark(BETA), rig.mark(GAMMA)
    rig.p[ALPHA].call("guild baseline line")
    check(rig.said(GAMMA, mg, "[GUILD] GcAlpha: baseline line"), "G1 flag off: a guildless neighbour hears the Guild line aloud (stock)")
    check(rig.silent(BETA, mb, "baseline line"), "G1 flag off: the far guildmate hears nothing (stock)")
    mark = rig.mark(ALPHA)
    rig.p[ALPHA].say("[g not available yet")
    check(rig.said(ALPHA, mark, "Guild chat is not available."), "G1 flag off: [g says guild chat is not available")

    rig.flag(True)

    # G2: on: the line goes to the whole guild wherever they are, back to the sender, and to nobody else.
    ma, mb, mg = rig.mark(ALPHA), rig.mark(BETA), rig.mark(GAMMA)
    rig.p[ALPHA].call("guild hello far guild")
    check(rig.said(BETA, mb, "[GUILD] GcAlpha: hello far guild"), "G2 the far guildmate hears it")
    check(rig.said(ALPHA, ma, "[GUILD] GcAlpha: hello far guild"), "G2 the sender sees it too")
    check(rig.silent(GAMMA, mg, "hello far guild"), "G2 the guildless neighbour hears nothing")

    # G3: and the other way, from the far one.
    ma, mg = rig.mark(ALPHA), rig.mark(GAMMA)
    rig.p[BETA].call("guild reply from afar")
    check(rig.said(ALPHA, ma, "[GUILD] GcBeta: reply from afar"), "G3 a reply from the far guildmate reaches Alpha")
    check(rig.silent(GAMMA, mg, "reply from afar"), "G3 the neighbour still hears nothing")

    # G4: no guild: told, and nothing is said aloud.
    ma, mb, mg = rig.mark(ALPHA), rig.mark(BETA), rig.mark(GAMMA)
    rig.p[GAMMA].call("guild I have no guild")
    check(rig.said(GAMMA, mg, "You are not in a guild."), "G4 a guildless speaker is told so")
    check(rig.silent(ALPHA, ma, "I have no guild") and rig.silent(BETA, mb, "I have no guild", 0.5), "G4 nobody hears it, near or far")

    # G5: a line that looks like a command or a guard call is only chat.
    rig.close_gumps(ALPHA)
    mb = rig.mark(BETA)
    rig.p[ALPHA].call("guild [Welcome")
    check(rig.said(BETA, mb, "[GUILD] GcAlpha: [Welcome"), "G5 a line starting with [ reaches the guild as text")
    time.sleep(1.5)
    check(not any("UO Rekindled" in line for line in rig.gumps(ALPHA)), "G5 and ran no command (the guide did not open)")

    # G6: [g does the same, and [g alone says how to use it.
    mb, ma = rig.mark(BETA), rig.mark(ALPHA)
    rig.p[ALPHA].say("[g from the keyboard")
    check(rig.said(BETA, mb, "[GUILD] GcAlpha: from the keyboard"), "G6 [g reaches the far guildmate")
    rig.p[ALPHA].say("[g")
    check(rig.said(ALPHA, ma, "Type [g followed by your message"), "G6 [g alone says how to use it", "")
    check(rig.said(ALPHA, ma, "Guild chat is logged for moderation."), "G6 and says that it is logged")
    mg = rig.mark(GAMMA)
    rig.p[GAMMA].say("[g without a guild")
    check(rig.said(GAMMA, mg, "You are not in a guild."), "G6 [g without a guild is refused")

    # G7: Alliance is not available, and not shouted at the neighbours.
    ma, mb, mg = rig.mark(ALPHA), rig.mark(BETA), rig.mark(GAMMA)
    rig.p[ALPHA].call("alliance to my allies")
    check(rig.said(ALPHA, ma, "Alliance chat is not available here."), "G7 an Alliance line is answered not available")
    check(rig.silent(GAMMA, mg, "to my allies") and rig.silent(BETA, mb, "to my allies", 0.5), "G7 and is said aloud to nobody")

    # G8: a muted speaker.
    rig.staff("[set Squelched true", ALPHA)
    ma, mb = rig.mark(ALPHA), rig.mark(BETA)
    rig.p[ALPHA].call("guild muted line")
    check(rig.said(ALPHA, ma, "You can not say anything, you have been squelched."), "G8 a muted speaker is refused")
    check(rig.silent(BETA, mb, "muted line"), "G8 and nothing is sent")
    rig.staff("[set Squelched false", ALPHA)

    # G9: a hidden speaker stays hidden.
    rig.staff("[set Hidden true", ALPHA)
    time.sleep(1.0)
    mb = rig.mark(BETA)
    rig.p[ALPHA].call("guild from hiding")
    check(rig.said(BETA, mb, "[GUILD] GcAlpha: from hiding"), "G9 a hidden speaker is heard by the guild")
    time.sleep(1.0)
    check(bool(rig.p[ALPHA].state.get("isHidden")), "G9 and stays hidden")
    rig.staff("[set Hidden false", ALPHA)

    # G10: a ghost can use it.
    rig.staff("[kill", ALPHA)
    time.sleep(2.5)
    check(bool(rig.p[ALPHA].state.get("charGhost")), "G10 setup: Alpha is a ghost")
    mb = rig.mark(BETA)
    rig.p[ALPHA].call("guild I died at the bridge")
    check(rig.said(BETA, mb, "[GUILD] GcAlpha: I died at the bridge"), "G10 a ghost reaches the living guild")
    rig.staff("[Resurrect", ALPHA)
    time.sleep(2.0)
    check(not bool(rig.p[ALPHA].state.get("charGhost")), "G10 cleanup: Alpha is alive again")

    # G11: a Knocked Out speaker. An entry needs the victim in a Hot Zone (or an Intent encounter), so both stand in Buccaneer's Den's, and Gamma
    # knocks Alpha out through the probe (a double-click in the client cannot land the blow on cue).
    rig.place(ALPHA, *HOT)
    rig.place(GAMMA, HOT[0] + 1, HOT[1])
    mark = rig.mark(ADMIN)
    rig.admin.say(f"[TestOnlyState {alpha} kofrom {gamma}")
    check(rig.said(ADMIN, mark, "KnockedOut entered=True"), "G11 setup: Alpha is Knocked Out")
    time.sleep(1.0)
    ma, mb = rig.mark(ALPHA), rig.mark(BETA)
    rig.p[ALPHA].call("guild knocked out line")
    check(rig.said(ALPHA, ma, "You cannot speak while you are Knocked Out."), "G11 a Knocked Out speaker is refused")
    check(rig.silent(BETA, mb, "knocked out line"), "G11 and nothing is sent")

    # G12: staff near the speaker see the line; staff far away do not. (Alpha is still Knocked Out for about 30 seconds: wait it out.)
    time.sleep(32.0)
    rig.place(ALPHA, *HERE)
    rig.place(GAMMA, *NEAR_GUILDLESS)
    rig.admin.say(f"[go {HERE[0] + 3} {HERE[1]}")
    time.sleep(2.0)
    mm = rig.mark(ADMIN)
    rig.p[ALPHA].call("guild watched line")
    check(rig.said(ADMIN, mm, "[Guild]: watched line"), "G12 staff within 8 tiles see the line the engine's way")
    rig.admin.say(f"[go {FAR[0]} {FAR[1]}")
    time.sleep(2.5)
    mm = rig.mark(ADMIN)
    rig.p[ALPHA].call("guild unwatched line")
    check(rig.silent(ADMIN, mm, "unwatched line"), "G12 staff far away do not")

    # G13: every line is in the server log, once, with the guild and the text.
    log = Path(json.loads((WORKSPACE / "work" / "dev-server" / "current.json").read_text(encoding="utf-8-sig"))["log"]).read_text(errors="replace")
    check("guild-chat message" in log and "text=hello far guild" in log and "guild=Testers" in log and "GcAlpha" in log, "G13 the server log carries the guild chat lines")
    check("text=I have no guild" not in log and "text=muted line" not in log, "G13 refused lines are not logged")

    # G14: switched off again, the stock behaviour is back.
    rig.flag(False)
    rig.admin.say(f"[go {HERE[0] + 3} {HERE[1]}")
    time.sleep(2.0)
    mg, mb = rig.mark(GAMMA), rig.mark(BETA)
    rig.p[ALPHA].call("guild stock again")
    check(rig.said(GAMMA, mg, "[GUILD] GcAlpha: stock again"), "G14 flag off again: the neighbour hears it aloud (stock)")
    check(rig.silent(BETA, mb, "stock again"), "G14 and the far guildmate does not")


STAGES = {"chat": stage_chat}

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in STAGES:
        print(__doc__)
        sys.exit(2)
    STAGES[sys.argv[1]]()
    print(f"ALL PASS: {sys.argv[1]}", flush=True)
