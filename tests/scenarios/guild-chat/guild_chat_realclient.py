"""Real-client pictures of guild chat (docs/Guild-Chat-Plan.md), on the host of guild_chat_live.py.

    python -u guild_chat_realclient.py pictures

Needs GcAlpha and GcBeta running as real clients (Start-PlayerClient.ps1; stop their Navrey sessions first), GcGamma and the staff session
`admin` on Navrey. Pictures (the whole 1296 x 839 client window) go to work/guild-chat/real/<name>.png; crop_game_view.ps1 cuts them to the game view.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import time
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[4]
SCRIPTS = WORKSPACE / ".claude" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from navrey_session import connect  # noqa: E402
from staff_command import staff_target  # noqa: E402

OUT = WORKSPACE / "work" / "guild-chat" / "real"
OUT.mkdir(parents=True, exist_ok=True)
SERIAL = {"GcAlpha": "0x0000A755", "GcBeta": "0x0000A756", "GcGamma": "0x0000A757"}
HERE = (633, 858)
FAR = (1394, 1716)   # Britain


def ps(script: str, *args: str, timeout: int = 180) -> str:
    out = subprocess.run(["pwsh", "-NoProfile", "-File", str(SCRIPTS / script), *args], capture_output=True, text=True, timeout=timeout)
    return (out.stdout + out.stderr).strip()


admin = connect("admin")


def say(command: str, wait: float = 1.0) -> None:
    admin.say(command)
    time.sleep(wait)


def place(who: str, x: int, y: int) -> None:
    admin.say(f"[go {x} {y}")
    time.sleep(2.2)
    z = int(admin.state["charPosZ"])
    admin.say(f"[go {SERIAL[who]}")
    time.sleep(1.8)
    staff_target(admin, f'[set Location "({x}, {y}, {z})"', SERIAL[who])
    time.sleep(1.0)


def shot(who: str, name: str, wait: float = 1.5) -> None:
    time.sleep(wait)
    path = ps("Get-PlayerClientShot.ps1", "-Name", who, "-Label", f"gc-{name}").splitlines()[-1].strip()
    shutil.copyfile(path, OUT / f"{name}.png")
    print("shot", name, flush=True)


def type_line(who: str, text: str, wait: float = 2.0) -> None:
    ps("Send-PlayerClientInput.ps1", "-Name", who, "-Text", text)
    time.sleep(wait)


def close_gumps(who: str) -> None:
    for _ in range(2):
        ps("Send-PlayerClientInput.ps1", "-Name", who, "-X", "230", "-Y", "165", "-Right")
        time.sleep(0.6)


def stage_pictures() -> None:
    say("[TestOnlyFlagOverride GuildChat true")
    say(f"[TestOnlyGuild {SERIAL['GcAlpha']} Testers {SERIAL['GcBeta']}", 1.5)
    place("GcAlpha", *HERE)
    place("GcGamma", HERE[0] + 1, HERE[1])
    place("GcBeta", *FAR)
    for who in ("GcAlpha", "GcBeta"):
        close_gumps(who)

    # 1-2: Alpha, with a guildless neighbour beside them, talks to Beta, who is in Britain. Both see the line; the neighbour sees nothing.
    type_line("GcAlpha", "\\ Anyone near the Britain bank? We are meeting at the gate.")
    shot("GcBeta", "1-far-guildmate-hears")
    shot("GcAlpha", "2-sender-sees-it")

    # 3: Beta answers with the keyboard command from the other end of the world.
    type_line("GcBeta", "[g On my way, I will be there in a minute.")
    shot("GcAlpha", "3-reply-from-afar")

    # 4: [g alone says how to use it, and that it is logged.
    type_line("GcAlpha", "[g")
    shot("GcAlpha", "4-usage")

    # 5: the Commands page of the guide.
    say(f"[TestOnlyShow {SERIAL['GcAlpha']} welcome commands", 2.5)
    shot("GcAlpha", "5-guide-commands")
    close_gumps("GcAlpha")

    # 6: someone with no guild is told so, and nothing is said aloud.
    say(f"[TestOnlyGuild {SERIAL['GcBeta']} none", 1.5)
    type_line("GcBeta", "\\ Is anyone there?")
    shot("GcBeta", "6-no-guild")
    say(f"[TestOnlyGuild {SERIAL['GcAlpha']} Testers {SERIAL['GcBeta']}", 1.5)
    print("done", flush=True)


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] != "pictures":
        print(__doc__)
        sys.exit(2)

    stage_pictures()
