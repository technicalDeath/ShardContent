"""A `uo.Client` that is served by the simulated world instead of a Navrey client's files.

It IS the real Client class (Navrey/cli/uo/client.py) with its three file-backed parts replaced: the state and world JSON files by in-memory documents the
world keeps current, the command file by a dispatcher that answers every command the brains send, the log tail by the player's journal. So `backpack`,
`mobiles()`, `containers()`, `find()`, `use_on()`, `container()` and the rest run the library's own code, and a brain cannot tell the difference except by
timing: the walk handle and the waits advance the virtual clock instead of polling it every 50 ms.

Commands answered (the ones the brains use, from the farm's client logs): goto, gotoexact, stop, walk, runmode, attack, use, click, hp, war, say, target,
canceltarget, targettile, drop, get, dropground, equip, unequip, gumps, gumpresponse, skills, container, shop, selllist, buy, sell, menus, menuresponse,
useskill, cast, items, allitems, los, tiles, path, trades, accepttrade, partyinfo, guild, opendoor, help, pos, meminfo, memcensus.
"""
from __future__ import annotations

import re
import time

from uo.client import Client, Walk
from uo.events import Event, LogEvent, classify

from .world import cheb


class MemFile:
    """What JsonFile is to the client: a document that is always fresh."""

    def __init__(self, provider):
        self._provider = provider
        self._frozen = None

    def read(self):
        return self._frozen if self._frozen is not None else self._provider()

    def freeze(self):
        self._frozen = self._provider()

    def thaw(self):
        self._frozen = None

    @property
    def age_ms(self):
        return 0.0

    @property
    def snapshot_age_ms(self):
        return 0.0

    def is_live(self, max_age_ms=5000):
        return True


class FakeTail:
    def __init__(self, player, world):
        self.player = player
        self.world = world
        self.path = f"<journal of {player.name}>"

    def _take(self):
        """The journal lines whose reply has reached the log by now; the rest stay pending."""
        pending = self.player.journal
        if not pending:
            return []
        now = self.world.now()
        if pending[-1][0] <= now:
            lines = [t for _, t in pending]
            self.player.journal = []
        else:
            lines = [t for at, t in pending if at <= now]
            self.player.journal = [e for e in pending if e[0] > now]
        return lines

    def poll(self):
        lines = self._take()
        if not lines:
            return []
        out = []
        stamp = self.world.stamp()
        log = self.player.cuolog
        if log is not None:
            log.write("".join(stamp + t + "\n" for t in lines))
        for text in lines:
            e = classify(text)
            e.raw = stamp + text
            out.append(e)
        return out

    def drain(self):
        self._take()


class _Combat:
    last_combat_time = None
    since_combat = float("inf")
    since_damage_taken = float("inf")
    since_attacked = float("inf")
    since_swing = float("inf")


class FakeCombatWatch:
    def update(self):
        return _Combat()


class SimWalk(Walk):
    def wait(self, timeout=300.0, poll=0.1):
        end = time.monotonic() + timeout
        step = max(poll, 0.5)
        while time.monotonic() < end:
            nav = self.client.nav
            if not nav.active:
                return nav.status
            time.sleep(min(step, max(0.05, end - time.monotonic())))
        nav = self.client.nav
        return nav.status if not nav.active else "timeout"


class FakeCommands:
    def __init__(self, client):
        self.client = client
        self.cmd_file = f"<commands of {client.player.name}>"
        self.log_file = f"<log of {client.player.name}>"
        self.sent = 0

    # every command costs a round trip through the client's command worker (6-20 ms live); charging it here also means no brain can spin in zero time
    COST = 0.02

    def send(self, line):
        self.sent += 1
        time.sleep(self.COST)
        self.client.dispatch(line)

    def call(self, line, timeout=10.0, poll=0.002):
        self.sent += 1
        time.sleep(self.COST)
        return self.client.dispatch(line)


class FakeClient(Client):
    def __init__(self, world, player):
        self.world_ = world
        self.player = player
        self._state = MemFile(self._state_doc)
        self._world = MemFile(self._world_doc)
        self.commands = FakeCommands(self)
        self.events = FakeTail(player, world)
        self._combat = FakeCombatWatch()
        self.runtime = None

    # ---- documents ----------------------------------------------------------------------------------------------------------------------------------

    def _state_doc(self):
        p = self.player
        w = self.world_
        if p.state_version != w.version or w.now() - p.state_at >= 0.25:
            p.refresh()
            p.state_version, p.state_at = w.version, w.now()
        return p.state

    def _world_doc(self):
        p = self.player
        if p.view_version != self.world_.version and self.world_.now() - getattr(p, "view_at", -1) >= 0.5:
            self.world_.build_view(p)
        return p.view

    def is_live(self, max_age_ms=5000):
        return True

    def require_live(self):
        return None

    # ---- overrides that would otherwise poll the clock ---------------------------------------------------------------------------------------------

    def goto(self, x, y, z=None):
        self.world_.start_walk(self.player, x, y, exact=False)
        return SimWalk(self, (x, y))

    def gotoexact(self, x, y, z=None):
        self.world_.start_walk(self.player, x, y, exact=True)
        return SimWalk(self, (x, y))

    def goto_poi(self, query):
        return SimWalk(self, query)

    def open_backpack(self, wait=2.0):
        return True

    def wait(self, predicate, timeout=10.0, poll=0.05):
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            if predicate():
                return True
            time.sleep(max(poll, 0.25))
        return predicate()

    def wait_for(self, kinds, timeout=15.0, poll=0.05):
        wanted = {kinds} if isinstance(kinds, Event) else set(kinds)
        end = time.monotonic() + timeout
        self.events.drain()
        while True:
            for e in self.events.poll():
                if e.kind in wanted:
                    return e
            if time.monotonic() >= end:
                return None
            time.sleep(max(poll, 0.25))

    # ---- the dispatcher -----------------------------------------------------------------------------------------------------------------------------

    def dispatch(self, line):
        w = self.world_
        p = self.player
        parts = line.strip().split()
        if not parts:
            return []
        cmd, args = parts[0].lower(), parts[1:]
        w.version += 1                              # whatever the command did, the next state read is fresh
        try:
            return self._dispatch(cmd, args, line) or []
        except Exception as e:                      # a fault in the fake, not in the brain: say so in the reply, never raise into the brain
            p.say_line(f"[ERROR] fake client: {cmd}: {type(e).__name__}: {e}")
            return [f"[ERROR] {type(e).__name__}: {e}"]

    def _dispatch(self, cmd, a, line):
        w, p = self.world_, self.player
        if cmd in ("goto", "gotoexact"):
            if len(a) >= 2:
                w.start_walk(p, int(a[0]), int(a[1]), exact=cmd == "gotoexact")
            return [f"Walking to ({a[0]}, {a[1]}) - not waiting"]
        if cmd == "stop":
            w.stop_walk(p)
            return ["Stopped"]
        if cmd == "walk":
            ok = w.step_dir(p, a[0]) if a else False
            return [f"Walked {a[0]}" if ok else "Walk refused"]
        if cmd == "runmode":
            p.runmode = a[0] if a else "auto"
            return [f"run mode: {p.runmode}"]
        if cmd == "attack":
            w.attack(p, a[0] if a else "")
            return [f"Attacking {a[0] if a else ''}"]
        if cmd == "use":
            w.use(p, a[0] if a else "")
            return [f"Used {a[0] if a else ''}"]
        if cmd == "click":
            m = w.mobile(a[0]) if a else None
            return [f"[LABEL] {m.name}: {m.name}"] if m else []
        if cmd == "hp":
            return []
        if cmd == "war":
            p.war = not p.war
            if not p.war:
                p.target = None
            p.say_line(f"War mode: {'ON' if p.war else 'off'}")
            return [f"War mode requested: {'ON' if p.war else 'off'}"]
        if cmd == "say":
            w.say(p, line.strip()[4:])
            return []
        if cmd == "target":
            if a and a[0] == "self":
                w.target(p, "self")
            elif a:
                w.target(p, a[0])
            return ["Targeted"]
        if cmd == "canceltarget":
            p.cursor = None
            return ["Target cancelled"]
        if cmd == "targettile":
            x, y = int(a[0]), int(a[1])
            z = int(a[2]) if len(a) > 2 else 0
            w.target(p, None, tile=(x, y, z))
            return [f"Targeted tile {x},{y},{z} graphic {a[3] if len(a) > 3 else 0}"]
        if cmd == "drop":
            w.drop(p, a[0], a[1], int(a[2]) if len(a) > 2 else None)
            return ["Dropped"]
        if cmd == "get":
            w.get_item(p, a[0], int(a[1]) if len(a) > 1 else None)
            return ["Grabbed"]
        if cmd == "dropground":
            return w.dropground(p, a[0], int(a[1]) if len(a) > 1 else 1)
        if cmd == "equip":
            return w.equip(p, a[0], a[1] if len(a) > 1 else None)
        if cmd == "unequip":
            return w.unequip(p, a[0])
        if cmd == "gumps":
            return w.gumps(p)
        if cmd == "gumpresponse":
            button = int(a[0]) if a else 0
            serial = next((x[5:] for x in a[1:] if x.startswith("gump:")), None)
            switches = [int(x) for x in a[1:] if x.isdigit()]
            return w.gumpresponse(p, button, serial, switches)
        if cmd == "skills":
            return [f"[SKILL] {name:<16} {v:6.1f} (base {v:5.1f}) up" for name, v in sorted(p.skills.items())]
        if cmd == "container":
            serial = a[0] if a else p.backpack_serial
            if serial == p.backpack_serial:
                items, label = p.backpack, "backpack"
            elif serial == p.bank_serial:
                items, label = (p.bank if p.bank_open else []), "bank box"
            else:
                c = w.corpses.get(serial)
                if c is None:
                    return [f"No container {serial}"]
                items, label = c.items, c.name
            out = [f"[CONTAINER] {serial} {label}:"]
            out += [f"  [item]      {i['serial']} {i['name']}" + (f" x{i['amount']}" if (i.get('amount') or 1) > 1 else "") for i in items]
            return out
        if cmd in ("shop", "selllist"):
            if p.last_shop and p.last_shop[1] == ("sell" if cmd == "selllist" else "buy"):
                return list(p.last_shop[2])
            return ["No shop list"]
        if cmd == "buy":
            return w.buy(p, [(a[i], int(a[i + 1])) for i in range(0, len(a) - 1, 2)])
        if cmd == "sell":
            return w.sell(p, [(a[i], int(a[i + 1])) for i in range(0, len(a) - 1, 2)])
        if cmd == "menus":
            return w.menus(p)
        if cmd == "menuresponse":
            return w.menuresponse(p, a[0], a[1], int(a[2]) if len(a) > 2 else 0)
        if cmd == "useskill":
            return w.useskill(p, " ".join(a))
        if cmd == "cast":
            return w.cast(p, " ".join(a))
        if cmd in ("items", "allitems"):
            r = int(a[0]) if a else 8
            out = []
            for f in w.fixtures:
                d = cheb(f["x"], f["y"], p.x, p.y)
                if d <= r:
                    out.append(f"  [fixed] {f['serial']} {f['name']:<34} d={d:<3} ({f['x']}, {f['y']}, {f['z']})")
            for c in w.corpses.values():
                d = cheb(c.x, c.y, p.x, p.y)
                if d <= r:
                    out.append(f"  [fixed] {c.serial} {c.name:<34} d={d:<3} ({c.x}, {c.y}, 0)")
            for it in w.ground.values():
                d = cheb(it["x"], it["y"], p.x, p.y)
                if d <= r:
                    out.append(f"  [item]  {it['serial']} {it['name']:<34} d={d:<3} ({it['x']}, {it['y']}, 0)")
            return out
        if cmd == "los":
            r = int(a[0]) if a else 10
            doc = self._world_doc()
            return [f"  YES {m['serial']} {m['name']:<28} d={m['distance']}" for m in doc["mobiles"] if m["distance"] <= r]
        if cmd == "tiles":
            x, y = int(a[0]), int(a[1])
            if w.data.is_water(x, y):
                return [f"Tile ({x}, {y}):", "  land   0x00A8 z=-5   Impassable, Wet"]
            return [f"Tile ({x}, {y}):", f"  land   0x0003 z=0   {'' if w.data.walkable(x, y) else 'Impassable'}"]
        if cmd == "path":
            return ["path: ok"]
        if cmd in ("trades", "accepttrade"):
            return []
        if cmd == "partyinfo":
            return w.party_info(p)
        if cmd == "partyinvite":
            p.cursor = ("party", None)
            p.say_line("[TARGET] Server wants a target (cursor 0x00000001, object) - use 'target <serial|self>'")
            return ["Party invite: target the player"]
        if cmd == "partyaccept":
            return w.party_accept(p)
        if cmd == "partydecline":
            p.party_invite = None
            return ["Party invitation declined"]
        if cmd == "partyleave":
            return w.party_leave(p)
        if cmd == "partyloot":
            g = w.parties.get(p.party) if p.party else None
            if g is not None:
                g["loot"] = not a or a[0].lower() in ("on", "yes", "1")
            return ["Party loot " + ("on" if g and g["loot"] else "off")]
        if cmd == "guild":
            return []
        if cmd == "opendoor":
            p.system("Opening door...")
            return []
        if cmd == "pos":
            return [f"({p.x}, {p.y}, {p.z})"]
        if cmd in ("help", "meminfo", "memcensus"):
            return []
        return [f"Unknown command: {cmd}"]
