"""Escort quests (feature "escort"; owner, 2026-11-05: "adding NEW bot capabilities, I want them doing things they haven't done before"). UO:R's townsfolk who
want to travel: a noble, a merchant, a peasant or a mage (Mobiles/Townfolk/BaseEscortable.cs, the pre-ML speech system, questSystem.enableMLQuests off):
  - said within 3 tiles, "destination" makes one answer where it wants to go (1042807, "I'm looking to go somewhere:Vesper" in the client), and
    "I will take thee" makes it follow ("Lead on! Payment will be made when we arrive in Vesper."); a player takes one escort at a time, and 5 minutes
    must pass after taking one before the next (EscortDelay: "You must rest N minutes before we set out on this journey.");
  - it follows as a pet does (about 0.5 s a step behind a moving master, standing for good past 16 tiles: memory pets-keep-up), stays where it is
    while its escorter is over 30 tiles off, and leaves after 2 minutes of that (AbandonDelay: "You have lost the person you were escorting.");
  - in the destination town's region it pays 500-1000 gold into the pack (1042809 "We have arrived! I thank thee ... Here is thy pay.") and Fame 10.
Britain spawns them at the Noble/EscortableMage spawner by the south bank (1483,1760), the Merchant (1434,1717), the Peasant (1304,1826) and the mage
(1351,1816); the destinations are the other towns (TownNames). The walk is the trip ladder's own (first_trip.py, trip_now): the escort only picks a
town the bot already has a vetted-or-explore route to and the skill and health for, then holds the walk while the NPC falls behind (escort_hold, from
trip_step): short slices (ESCORT_SLICE s) and a wait until it is within ESCORT_NEAR tiles, so it never drops past 16.
In the town it took one to, the bot looks once for another going to its home (escort_return, from the trip's stay) and takes it back the same way.
Events: escort_ask {who, dest, taken, back}, escort_take {who, dest, back}, escort_paid {who, dest, gold, minutes}, escort_lost {who, dest, why, minutes}.
"""
from __future__ import annotations

import os
import re
import time

ESCORT_TYPES = ("EscortableMage", "Noble", "Merchant", "Peasant")     # SeekerOfAdventure goes to dungeons: not these trips
SPOTS = ((1483, 1760), (1434, 1717), (1304, 1826), (1351, 1816))        # Britain's spawners (Spawns/TownsPeople.json, Vendors.json), as well as the gazetteer's
SPOT_NEAR = 80             # tiles from the bot a spawner may be to be worth the walk
ESCORT_GAP = 900           # s between looks for an escort
ESCORT_RECHECK = 60        # s until the next look when no spawner was near or no town was open
REST_S = 300               # EscortDelay: after taking one, the next only after this
ESCORT_NEAR = 4            # tiles: the NPC this close, the walk goes on
ESCORT_SLICE = 3           # s of walking a tick with an escort (a runner makes ~15 tiles, the follower ~6)
ESCORT_WAIT_MAX = 120      # s of waiting for it before it is given up (its own AbandonDelay is 2 minutes)
ESCORT_MAX_S = 5400        # an escort not paid in 90 minutes is over
SLOW_TIMES = 3             # the trip's "too slow" limit, times this, with an escort
ASK_PER_SPOT = 6
SPOT_REACH = 6             # tiles: the spawner reached (its escorts wander about it); further, its people are not asked

DEST_RE = re.compile(r"looking to go (?:to |somewhere)[:\s]*([A-Z][A-Za-z' ]+?)\s*(?:[,.?!]|$)")
LEAD_RE = re.compile(r"Lead on!.*arrive in ([A-Z][A-Za-z' ]+?)\s*[.!]")
REST_RE = re.compile(r"must rest (\d+) minute", re.I)
PAID_RE = re.compile(r"We have arrived|Here is thy pay", re.I)
LOST_RE = re.compile(r"You have lost the person you were escorting", re.I)


def said(t):
    """(speaker, text) of a "[SAY] Name: text" journal line, else None."""
    m = re.match(r"\[SAY\] ([^:]+): (.*)$", t or "")
    return (m.group(1).strip(), m.group(2).strip()) if m else None


class EscortMixin:
    def escort_on(self):
        return self.feature("escort") and hasattr(self, "ladder_on") and self.ladder_on()

    def escort_feed(self, t):
        """Each journal line (bot_common.read_journal): what escorts say, kept for r_escort and escort_tick."""
        s = said(t)
        e = self.facts.get("escort") if isinstance(getattr(self, "facts", None), dict) else None
        if LOST_RE.search(t or "") and e:
            e["result"] = "lost"
            return
        if not s:
            return
        who, text = s
        heard = self.__dict__.setdefault("_escort_heard", {})
        m = DEST_RE.search(text)
        if m:
            heard[who] = ("dest", m.group(1).strip(), time.time())
            return
        m = LEAD_RE.search(text)
        if m:
            heard[who] = ("lead", m.group(1).strip(), time.time())
            return
        m = REST_RE.search(text)
        if m:
            heard[who] = ("rest", int(m.group(1)), time.time())
            return
        if e and who == e.get("who") and PAID_RE.search(text):
            e["result"] = "paid"

    # ---- taking one ----------------------------------------------------------------------------------------------------------

    def escort_dests(self, home):
        """{dest: trip} of the towns this bot may walk to now (first_trip's own checks: skill band, health, a safe route)."""
        out = {}
        try:
            power = self.trip_power()
            gate_on = hasattr(self, "gate_on") and self.gate_on()
            for t in self.trips_for_home(home):
                if t.get("kind") != "town" or (t.get("gate") and not gate_on):
                    continue
                town = t.get("town") or t["dest"]
                if town in out and not t.get("gate"):
                    continue                                    # the gate trip to a town is kept over the road (shorter, and past no road camp)
                if power >= t["band"] and self.c.max_hp >= t["hp"] and self.trip_ok_route(home, t):
                    out[town] = t
        except Exception:
            pass
        return out

    def escort_spots(self):
        """Escort spawners within SPOT_NEAR tiles, nearest first: the gazetteer's places of those types, and SPOTS."""
        pts = set(SPOTS)
        try:
            import gazetteer as gz
            for p in gz.get().places:
                if p.get("type") in ESCORT_TYPES:
                    pts.add((int(p["x"]), int(p["y"])))
        except Exception:
            pass
        x, y = int(self.c.x), int(self.c.y)
        near = [(max(abs(px - x), abs(py - y)), (px, py)) for px, py in pts]
        return [p for d, p in sorted(near) if d <= SPOT_NEAR]

    def escort_listen(self, who, kinds, secs=3.0):
        """Wait up to secs for who to say one of kinds (escort_feed's records), reading the journal meanwhile; the record or None."""
        end = time.time() + secs
        t0 = time.time()
        while time.time() < end:
            time.sleep(0.4)
            self.read_journal()
            h = (self.__dict__.get("_escort_heard") or {}).get(who)
            if h and h[0] in kinds and h[2] >= t0 - 0.5:
                return h
        return None

    def r_escort(self):
        """Feature escort: an escort under way is watched (escort_tick); else, in its home town, ready for a trip and with none under way, the bot goes to
        the nearest escort spawner, asks the people there their destination, and takes the first who is going to a town it has a route to."""
        if not self.escort_on() or self.c.ghost:
            return False
        e = self.facts.get("escort")
        if e:
            return self.escort_tick(e)
        now = time.time()
        if now < float(self.facts.get("escort_next", 0) or 0):
            return False
        try:
            if self.trip_load().get("trip") or os.path.exists(os.path.join(self.dir, "trip_now")):
                return False
        except Exception:
            return False
        home = self.trip_home_region()
        if not home or self.hp_pct() < 90 or self.threats(10) or self.c.weight >= self.c.max_weight * 0.7 or not self.trip_kit_ok():
            return False
        dests = self.escort_dests(home)
        spots = self.escort_spots()
        if not dests or not spots:
            # not here, or no town to go to: looked at again in a minute, as the bot moves through town (the gap set first made a bot elsewhere in
            # Britain's large region wait 15 minutes, and it passed the bank and the spawners in between: BotFenceAdvR, 2026-11-06 02:52)
            self.facts["escort_next"] = now + ESCORT_RECHECK
            if now - float(self.__dict__.get("_escort_none_at", 0) or 0) > 600:
                self.__dict__["_escort_none_at"] = now
                self.log(f"escort: none taken now: {'no town it has a safe trip to' if not dests else 'no escort spawner within ' + str(SPOT_NEAR) + ' tiles'}")
            return False
        self.facts["escort_next"] = now + ESCORT_GAP
        got = self.escort_seek(set(dests), spots)
        if got:
            got["trip_dest"] = dests[got["dest"]]["dest"]          # "Moonglow by gate" for a gate trip (gate.py)
            with open(os.path.join(self.dir, "trip_now"), "w", encoding="utf-8") as f:
                f.write(got["trip_dest"])
        return True

    def escort_seek(self, wanted, spots, back=False):
        """At the nearest two of spots, ask each person their destination and take the first going to a town in wanted: the new facts["escort"], or None."""
        now = time.time()
        asked = self.__dict__.setdefault("_escort_asked", {})
        for k in [k for k, v in asked.items() if v < now - 3600]:
            asked.pop(k, None)
        for sx, sy in spots[:2]:
            self.activity = "looking for someone to escort"
            res = str(self.goto_near(sx, sy, 3).wait(timeout=60))
            if max(abs(int(self.c.x) - sx), abs(int(self.c.y) - sy)) > SPOT_REACH:
                self.log(f"escort: did not reach the spawner at {sx},{sy} ({res[:30]}; at {self.c.x},{self.c.y})")
                continue
            # (the client's own list: BotBase.mobs keeps only the hostile-looking, Gray to Murderer, and no escort is ever there: 2026-11-06 03:30)
            people = [m for m in self.c.mobiles(within=10) if getattr(m, "notoriety", "") == "Innocent" and not (m.name or "").startswith("Bot")
                      and str(m.serial) not in asked and not self.peaceful_person_vendor(m)]
            if not people:
                self.log(f"escort: nobody new to ask at {sx},{sy}")
            for m in people[:ASK_PER_SPOT]:
                if self.threats(8):
                    return None
                if (getattr(m, "distance", 9) or 9) > 2:
                    self.c.goto(m.x, m.y).wait(timeout=10)
                self.read_journal()
                self.c.call("say destination", timeout=5)
                h = self.escort_listen(m.name, ("dest",))
                asked[str(m.serial)] = now
                if not h:
                    continue
                dest = h[1]
                take = dest in wanted
                self.ev("escort_ask", who=m.name, dest=dest, taken=take, back=back)
                if not take:
                    self.log(f"escort: {m.name} wants to go to {dest}: no route there for this bot")
                    continue
                self.c.call("say I will take thee", timeout=5)
                r = self.escort_listen(m.name, ("lead", "rest"))
                if not r or r[0] != "lead":
                    if r and r[0] == "rest":
                        self.facts["escort_next"] = time.time() + 60 * (int(r[1]) + 1)
                    self.log(f"escort: {m.name} did not set out ({'rest ' + str(r[1]) + ' min' if r else 'no answer'})")
                    return None
                e = self.facts["escort"] = {"serial": str(m.serial), "who": m.name, "dest": dest, "t0": time.time(), "gold0": int(self.c.gold or 0), "back": back}
                self.ev("escort_take", who=m.name, dest=dest, back=back)
                self.log(f"escort: taking {m.name} to {dest}{' on the way home' if back else ''} (pays 500-1000 gold on arrival)")
                return e
        return None

    def escort_return(self, t, now):
        """From trip_step's stay in a town: once a trip, with no escort under way, a townsperson there going to the trip's home is taken back, and the
        stay ends so the walk home starts (paid on arrival at home)."""
        if not self.escort_on():
            return False
        e0 = self.facts.get("escort")
        if e0:
            self.escort_tick(e0)                            # (r_escort does not run during a trip: the pay is settled here)
        if self.facts.get("escort") or t.get("escort_back_tried") or t.get("phase") != "stay":
            return False
        if ((t.get("def") or {}).get("kind") or "town") != "town" or now - float(t.get("t_arrive") or now) < 20:
            return False
        if self.hp_pct() < 80 or self.threats(10) or self.c.ghost:
            return False
        t["escort_back_tried"] = True                       # (EscortDelay counts from the last one taken, long ago by now; "must rest" is read if not)
        spots = self.escort_spots()
        if not spots or not t.get("home"):
            return False
        e = self.escort_seek({t["home"]}, spots, back=True)
        if e:
            t["stay_until"] = now                           # home now, with it
            try:
                self.trip_save()
            except Exception:
                pass
        return True

    def peaceful_person_vendor(self, m):
        """A vendor is not an escort: vendors are Invulnerable (yellow), and the shared memory's vendor names (talk.vendor_names) catch the rest."""
        try:
            import talk
            return m.name in talk.vendor_names(self)
        except Exception:
            return False

    # ---- under way -----------------------------------------------------------------------------------------------------------

    def escort_end(self, e, how, **kw):
        mins = round((time.time() - float(e.get("t0") or time.time())) / 60.0, 1)
        if how == "paid":
            gold = max(0, int(self.c.gold or 0) - int(e.get("gold0") or 0))
            self.ev("escort_paid", who=e.get("who"), dest=e.get("dest"), gold=gold, minutes=mins)
            self.log(f"escort: {e.get('who')} paid {gold} gold in {e.get('dest')} after {mins} min")
            try:
                self.note("escort", f"A noble, merchant, peasant or mage in town answers 'destination' with the town it wants; 'I will take thee' and it follows, and pays on arrival: {gold} gold for {e.get('dest')}.", key="escort")
            except Exception:
                pass
        else:
            self.ev("escort_lost", who=e.get("who"), dest=e.get("dest"), why=kw.get("why", how), minutes=mins)
            self.log(f"escort: lost {e.get('who')} on the way to {e.get('dest')} ({kw.get('why', how)}) after {mins} min")
        self.facts.pop("escort", None)
        self.facts["escort_next"] = time.time() + REST_S

    def escort_tick(self, e):
        """An escort under way: its result (paid, lost) or its time out; the walk itself is the trip's. Never acts: returns False."""
        res = e.get("result")
        if res == "paid":
            self.escort_end(e, "paid")
        elif res == "lost":
            self.escort_end(e, "lost", why="it lost sight of the bot")
        elif time.time() - float(e.get("t0") or 0) > ESCORT_MAX_S:
            self.escort_end(e, "lost", why="no arrival in 90 minutes")
        else:
            try:
                st = self.trip_load()
                if st.get("trip") or os.path.exists(os.path.join(self.dir, "trip_now")):
                    e.pop("gone_at", None)
                elif time.time() - float(e.setdefault("gone_at", time.time())) > 120 and time.time() - float(e.get("t0") or 0) > 120:
                    self.escort_end(e, "lost", why="the trip ended or never started")       # (120 s for the follower to walk in first)
            except Exception:
                pass
        return False

    def escorting(self, t=None):
        """The escort under way on this trip, else None."""
        e = self.facts.get("escort") if isinstance(getattr(self, "facts", None), dict) else None
        if not e or e.get("result"):
            return None
        want = e.get("dest") if e.get("back") else e.get("trip_dest", e.get("dest"))
        if t is not None and (t.get("home") if e.get("back") else t.get("dest")) != want:
            return None
        return e

    def escort_hold(self, t, now):
        """From trip_step, on the way out: True while the bot waits for its escort to come within ESCORT_NEAR tiles (the follower lags a running master and
        stands for good past 16), at most ESCORT_WAIT_MAX s; not while a monster is in notice range (the trip's run-past goes on)."""
        e0 = self.facts.get("escort") if isinstance(getattr(self, "facts", None), dict) else None
        if e0:
            self.escort_tick(e0)                            # pay, loss or time-out settled as they come (r_escort does not run during a trip)
        e = self.escorting(t)
        if not e or t.get("phase") != ("home" if e.get("back") else "out"):
            return False
        m = next((x for x in self.c.mobiles(within=24) if str(x.serial) == e["serial"]), None)      # (an escort is Innocent: not in BotBase.mobs)
        if m is not None and (getattr(m, "distance", 99) or 99) <= ESCORT_NEAR:
            e.pop("wait0", None)
            return False
        try:
            if self.trip_near():
                return False
        except Exception:
            pass
        w0 = e.setdefault("wait0", now)
        if now - w0 > ESCORT_WAIT_MAX:
            self.escort_end(e, "lost", why=f"not within {ESCORT_NEAR} tiles for {ESCORT_WAIT_MAX} s" + ("" if m is not None else " (out of sight)"))
            return False
        if now - w0 < 1.0:
            try:
                self.c.call("stop", timeout=3)
            except Exception:
                pass
        self.activity = f"waiting for {e['who']} to catch up"
        time.sleep(1.5)
        return True
