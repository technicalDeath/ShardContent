"""Moongate travel (feature "gate_travel"; owner, 2026-11-05: "adding NEW bot capabilities"). A trip to a town by its moongate: the walk to the home town's
gate, the gate, then the walk from the far gate into the town, and back the same way. The public moongate (Items/Misc/PublicMoongate.cs):
  - double-clicked from within 1 tile it opens "Pick your destination:" with one radio per Felucca gate (live probe 2026-11-06 00:58, BotHealAdvR,
    Britain -> Trinsic -> Britain): Moonglow 0, Britain 1, Jhelom 2, Yew 3, Minoc 4, Trinsic 5, Skara Brae 6, New Magincia 7, Buccaneer's Den 8;
    OKAY is button 1, and the gump answer carries the radio as its switch;
  - refused for a criminal ("Thou'rt a criminal and cannot escape so easily") and in combat ("Wouldst thou flee during the heat of battle??");
  - a controlled follower within 3 tiles goes through with its master (BaseCreature.TeleportPets): an escort comes along when it is that close.
The island towns (Moonglow, Jhelom, Magincia) have no land route from Britain; Trinsic by its gate is 373 + 419 steps against 1,486 by the road past
the camp where BotWarAdvR died (2026-11-05 23:27). Gate trips are offered to escorts first (escort.py, escort_dests). Events: gate_hop {from, to, ok, why}.
"""
from __future__ import annotations

import re
import time

# town: (gate x, y, radio); the gazetteer's moongates, the gump's radios
GATES = {
    "Moonglow": (4467, 1283, 0),
    "Britain": (1336, 1997, 1),
    "Jhelom": (1499, 3771, 2),
    "Yew": (771, 752, 3),
    "Minoc": (2701, 692, 4),
    "Trinsic": (1828, 2948, 5),
    "Skara Brae": (643, 2067, 6),
    "Magincia": (3563, 2139, 7),
    "Buccaneer's Den": (2711, 2234, 8),
}
GATE_DESTS = ("Moonglow", "Jhelom", "Magincia", "Trinsic", "Minoc", "Yew", "Skara Brae")
SUFFIX = " by gate"
BAND, HP, STAY = 50, 70, 10            # the town trips' own skill band and health at Trinsic's level (first_trip TRIPS)
HOP_TRIES = 4                          # gate attempts on the way out before the trip turns back
HOME_TRIES = 20                        # and on the way home (from an island there is no other way)
FOLLOW_NEAR = 2                        # tiles: an escort this close goes through with the bot (TeleportPets: 3)
FOLLOW_WAIT = 60                       # s at the gate for it to come that close


def town_of(dest):
    return dest[:-len(SUFFIX)] if dest.endswith(SUFFIX) else dest


class GateMixin:
    def gate_on(self):
        return self.feature("gate_travel")

    def gate_trips(self, home, start):
        """The gate trips from this home (its town has a gate): to each of GATE_DESTS, a trip whose waypoints are start, the home gate, the far gate and
        the town's centre; trip_plan routes the two walks and marks the hop (jump)."""
        hg = GATES.get(home["name"])
        if not hg:
            return []
        try:
            import gazetteer as gz
            towns = {r["name"]: r for r in gz.get().towns()}
        except Exception:
            return []
        # the home's own surveyed walk to its gate (first_trip.TRIPS, kind "gate": Britain's "britain-gate-walk"), as its first leg: a fresh plan from the
        # bank crossed 1320,1920, where two bots no stronger died, and every gate trip was refused there (2026-11-06 01:26)
        seed = None
        try:
            import first_trip as _ft
            seed = next((t["wps"] for t in _ft.TRIPS if t.get("kind") == "gate" and t.get("home", "Britain") == home["name"]), None)
        except Exception:
            seed = None
        out = []
        for name in GATE_DESTS:
            g, r = GATES.get(name), towns.get(name)
            if not g or not r or name == home["name"]:
                continue
            end = (int(r["centre"][0]), int(r["centre"][1]))
            out.append({"id": f"{home['name']}-{name}-gate".lower().replace(" ", "-"), "feature": "gate_travel", "dest": name + SUFFIX, "town": name, "kind": "town",
                        "band": BAND, "hp": HP, "stay": STAY, "home": home["name"], "vetted": False, "source": "gate",
                        "gate": {"from": [hg[0], hg[1]], "to": [g[0], g[1]], "radio": g[2], "back": hg[2], "seed_leg": [list(p) for p in seed] if seed else None},
                        "wps": [tuple(start), (hg[0], hg[1]), (g[0], g[1]), end]})
        return out

    def gate_find(self, x, y):
        """The serial of the moongate at x,y (Navrey "items": "0x40019CE4 blue moongate ... (1828, 2948, -20)"), or None."""
        try:
            for line in self.c.call("items", timeout=8):
                if "moongate" not in line.lower():
                    continue
                s = re.search(r"0x[0-9A-Fa-f]+", line)
                p = re.search(r"\((\d+), (\d+)", line)
                if s and (not p or max(abs(int(p.group(1)) - x), abs(int(p.group(2)) - y)) <= 2):
                    return s.group(0)
        except Exception:
            pass
        return None

    def gate_follower_close(self, t):
        """True when no escort is under way on this trip, or it stands within FOLLOW_NEAR tiles (else it stays behind at the gate)."""
        e = self.escorting(t) if hasattr(self, "escorting") else None
        if not e:
            return True
        m = next((x for x in self.mobs(16) if str(x.serial) == e["serial"]), None)
        return m is not None and (getattr(m, "distance", 99) or 99) <= FOLLOW_NEAR

    def gate_hop(self, frm, to, radio, t=None):
        """Through the gate at frm to the one at to: True once the bot stands by the far gate. Waits up to FOLLOW_WAIT s for an escort first."""
        fx, fy = int(frm[0]), int(frm[1])
        self.activity = "taking the moongate"
        self.c.goto(fx, fy).wait(timeout=20)
        end = time.time() + FOLLOW_WAIT
        while not self.gate_follower_close(t) and time.time() < end:
            time.sleep(1.5)
        serial = self.gate_find(fx, fy)
        why = None
        if not serial:
            why = "no gate seen"
        else:
            if hasattr(self, "read_journal"):
                self.read_journal()
            self.c.call(f"use {serial}", timeout=5)
            time.sleep(1.5)
            dump = self.c.call("gumps", timeout=8) or []
            gump = None
            head = None
            for l in dump:
                h = re.search(r"server (0x[0-9A-Fa-f]+)", l)
                if h:
                    head = h.group(1)
                if "Pick your destination" in l and head:
                    gump = head
                    break
            if not gump:
                why = "the gate opened no list"
            else:
                self.c.call(f"gumpresponse 1 {radio} gump:{gump}", timeout=5)
                time.sleep(2.5)
                lines = self.read_journal() if hasattr(self, "read_journal") else []
                said = " ".join(lines or [])
                if re.search(r"flee during the heat of battle", said, re.I):
                    why = "in combat"
                elif re.search(r"criminal and cannot escape", said, re.I):
                    why = "criminal"
        ok = max(abs(int(self.c.x) - int(to[0])), abs(int(self.c.y) - int(to[1]))) <= 3
        if ok:
            why = None
        elif why is None:
            why = "not moved"
        self.ev("gate_hop", frm=[fx, fy], to=[int(to[0]), int(to[1])], ok=ok, why=why)
        self.log(f"moongate {fx},{fy} -> {int(to[0])},{int(to[1])}: {'through' if ok else 'not through (' + why + ')'}")
        return ok

    def trip_gate_step(self, t, trip, idx, phase):
        """From trip_step at a reached waypoint: at the hop (the home gate on the way out, the far gate on the way home) take the gate; None elsewhere,
        True when the tick was spent there."""
        jump = trip.get("jump")
        g = trip.get("gate")
        if jump is None or not g:
            return None
        if phase == "out" and idx == jump:
            frm, to, radio, nxt = g["from"], g["to"], g["radio"], jump + 1
        elif phase == "home" and idx == jump + 1:
            frm, to, radio, nxt = g["to"], g["from"], g["back"], jump
        else:
            return None
        if self.gate_hop(frm, to, radio, t):
            t.update(i=nxt, best=1e9, best_at=time.time(), fails=0, gate_fails=0)
        else:
            t["gate_fails"] = int(t.get("gate_fails") or 0) + 1
            if phase == "out" and t["gate_fails"] >= HOP_TRIES:
                self.trip_abort("the moongate did not take it")
            elif phase == "home" and t["gate_fails"] >= HOME_TRIES:
                self.trip_end("stranded", completed=False)           # (an island has no land route home: it tries far longer first)
                return False
            else:
                time.sleep(5 if phase == "out" else 15)
        self.trip_save()
        return True
