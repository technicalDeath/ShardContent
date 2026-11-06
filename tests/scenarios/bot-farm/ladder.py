"""The exploration ladder (A4 adventure; Watcher 2026-10-17, Helper 2; feature "ladder", and "ladder_dungeon" for the last rung): a fighter widens its world a rung at a time, each rung gated on
strength, supplies, a way back and the OUTCOME of the rung before it (never a timer). Mixin for HunterBot and CasterBot, written into the bot-farm folder by patch_ladder.py; it rides on first_trip.py
(routes, the walk, the abort rules, the arrival look) and replaces only its "who goes where, and how often".

  rung 1  Britain's ring     hunt within RING (70) tiles of the home centre: ok after 15 kills there or beyond it, nothing died on it in the last 30 minutes, main skill >= 25
  rung 2  the outskirts      hunt beyond the ring, outside every town and dungeon: ok after 10 kills, again no death in 30 minutes, main skill >= 40, rung 1 ok
  rung 3  another town       a trip to a town (the gazetteer's: the vetted Skara Brae and Trinsic seeds, then straight-line trips to the nearest others) once rung 2 is ok, main skill >= 50, the
                             kit (bandages or Heal potions, ammunition for archers), 300 gold carried or banked, hit points for the trip, a planned land route that passes no death cell, a refuge in
                             the destination town (where it can be healed and resurrected) and one at home. REPEATABLE: the town it has seen least (then the nearest) after TOWN_GAP (45 min) from the
                             last trip; after a failed trip it rests TOWN_FAIL (60 min) times its failures, and after FAIL_LIMIT (3) failures at the same strength it waits for 5 more skill.
  rung 4  Despise, level 1 (feature ladder_dungeon; Covetous 2026-11-03/04) once a town trip has been completed twice, main skill >= 65, 80 hit points, 3 Heal potions and 15 bandages, 500 gold: walk to the dungeon's
                             entrance (the gazetteer's dungeon entrance on the surface), step through, look around DUNGEON_STAY (8) minutes at the landing, and walk out. At most one visit per
                             DUNGEON_GAP (3 h). A casualty or an abort is a failed rung. The step through the door is the one new action; the rest is first_trip's walk and abort rules.
Events (decisions.jsonl): region_first {region, at} the first time the bot stands in a named region (a town or dungeon); rung {n, result: ok | fail, dest, why, minutes} when a rung is passed (1, 2:
once) or a trip of the rung ends (3, 4: each time). Trips keep first_trip's own trip_start / trip_arrive / trip_abort / trip_home events (trip_start carries the rung in its trip_kind).
State: <bot>/ladder.json (survives a restart). Hooks in first_trip.py (patch_ladder.py): trips_allowed, trip_pick's choice, r_trip's once-only flag, trip_end, and the arrival.
"""
import items  # noqa: E402  (the shared item table)
import json
import os
import time



class _FT:
    """first_trip, imported on first use (first_trip imports this module for its base class)."""

    def __getattr__(self, name):
        import first_trip
        return getattr(first_trip, name)


ft = _FT()

RING = 70
RING_KILLS = 15
OUT_KILLS = 10
QUIET = 1800                  # seconds without a death before a ring or outskirts rung counts
POWER = {1: 25, 2: 40, 3: 50, 4: 65}
TOWN_GAP = 2700
TOWN_FAIL = 3600
FAIL_LIMIT = 3
SKILL_CAP = 100               # a skill's cap in this era (no power scrolls): a rest 'until 5 more skill' past it never ends
MASTERY_FROM = 80            # from 80 a skill rises by Mastery's daily allowance (2.0 / 1.4 / 1.0 / 0.8 a day, docs/Mastery-Layered-Evidence.md): 5 more
                             # takes days, so a failure there rests by time too (BotArchAdvR failed at 95 and waited for 100)
DUNGEON = "Despise"           # owner 2026-11-04: "Despise is probably the better beginner dungeon to send bots to" (its upper floor is lizardmen,
                              # Despise.json); Covetous 2026-11-03/04 (main door 2499,916). The troll camp at Despise's door (1325,1071, Outdoors) is run past
                              # (first_trip.trip_end_threat: a teleporter door is stepped on at a run)
DUNGEON_DOOR = (1296, 1081)   # its one surface entrance (teleporters.json 1296,1080-1082 -> 5588,630-632)
DUNGEON_STAY = 8
DUNGEON_GAP = 10800
DUNGEON_HP = 80
MIN_WORTH = 300
DUNGEON_WORTH = 500
TICK_EVERY = 10


def cheb(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


class LadderMixin:
    # ---- state ------------------------------------------------------------------------------------------------------------------------------------

    def ladder_on(self):
        """The cohort feature "ladder" AND an adventurer's persona (A4, main or second): the same rule that grants first_trip (ambition.py)."""
        try:
            return bool(self.feature("ladder") and self.ambition_wants("A4"))
        except Exception:
            return False

    def ladder_path(self):
        return os.path.join(self.dir, "ladder.json")

    def ladder_state(self):
        st = self.__dict__.get("_ladder")
        if st is None:
            st = {"ok": {}, "fails": {}, "visits": {}, "regions": [], "ring_kills": 0, "out_kills": 0, "last_death": 0, "trips_ok": 0, "last_trip_end": 0, "last_dungeon": 0,
                  "fail_power": {}, "kills_seen": None, "deaths_seen": None}
            try:
                st.update(json.load(open(self.ladder_path(), encoding="utf-8")))
            except (OSError, ValueError, TypeError):
                pass
            self._ladder = st
        return st

    def ladder_save(self):
        try:
            with open(self.ladder_path() + ".tmp", "w", encoding="utf-8") as f:
                json.dump(self.ladder_state(), f)
            os.replace(self.ladder_path() + ".tmp", self.ladder_path())
        except (OSError, TypeError, ValueError):
            pass

    # ---- watching: regions, kills on the ring and outside, deaths, the first two rungs ------------------------------------------------------------

    def ladder_tick(self):
        """After every tick (every 10 s of it does anything): region_first, kill counts by place, rungs 1 and 2."""
        if not self.ladder_on() or self.c.ghost:
            return
        now = time.time()
        if now - self.__dict__.get("_ladder_at", 0) < TICK_EVERY:
            return
        self.__dict__["_ladder_at"] = now
        st = self.ladder_state()
        changed = False
        gz = ft._gz()
        try:
            r = gz.home_region(self.c.x, self.c.y) if gz else None
        except Exception:
            r = None
        if r and r["name"] not in st["regions"]:
            st["regions"].append(r["name"])
            self.ev("region_first", region=r["name"], at=[int(self.c.x), int(self.c.y)])
            self.log(f"ladder: first time in {r['name']}")
            changed = True
        kills, deaths = getattr(self, "kills", 0), getattr(self, "deaths", 0)
        if st["kills_seen"] is None or kills < st["kills_seen"]:
            st["kills_seen"] = kills                                         # first sample, or a counter that restarted
        if st["deaths_seen"] is None or deaths < st["deaths_seen"]:
            st["deaths_seen"] = deaths
        if deaths > st["deaths_seen"]:
            st["deaths_seen"] = deaths
            st["last_death"] = now
            changed = True
        if kills > st["kills_seen"]:
            n = kills - st["kills_seen"]
            st["kills_seen"] = kills
            hx, hy = self.home_centre()
            if cheb((self.c.x, self.c.y), (hx, hy)) <= RING and not (r and r["kind"] == "dungeon"):
                st["ring_kills"] += n
            elif not (r and r["kind"] in ("town", "dungeon")) and not (gz and gz.in_town(self.c.x, self.c.y)):
                st["out_kills"] += n
            changed = True
        if self.ladder_rung_check(st, now):
            changed = True
        if changed:
            self.ladder_save()

    def ladder_quiet(self, st, now):
        return now - st.get("last_death", 0) >= QUIET

    def ladder_rung_check(self, st, now):
        power = self.trip_power()
        changed = False
        # a kill beyond the ring counts for the ring too: a bot that hunts the outskirts without dying has outgrown it (2026-11-01: the four ladder bots had
        # 5-9 ring kills against 170-900 beyond it, so rung 1, and every rung after it, never passed)
        done1 = st["ring_kills"] + st["out_kills"]
        if "1" not in st["ok"] and done1 >= RING_KILLS and self.ladder_quiet(st, now) and power >= POWER[1]:
            st["ok"]["1"] = now
            self.ev("rung", n=1, result="ok", dest="ring", why=f"{done1} kills on the ring or beyond it", power=round(power, 1))
            self.log("ladder: rung 1 (Britain's ring) done")
            changed = True
        if "1" in st["ok"] and "2" not in st["ok"] and st["out_kills"] >= OUT_KILLS and self.ladder_quiet(st, now) and power >= POWER[2]:
            st["ok"]["2"] = now
            self.ev("rung", n=2, result="ok", dest="outskirts", why=f"{st['out_kills']} kills beyond the ring", power=round(power, 1))
            self.log("ladder: rung 2 (the outskirts) done")
            changed = True
        return changed

    # ---- the gates of the trips ---------------------------------------------------------------------------------------------------------------------

    def ladder_rested(self, st, rung, now):
        """False while a failed rung is being rested: TOWN_FAIL minutes per failure, and after FAIL_LIMIT failures at this strength until 5 more skill."""
        fails = st["fails"].get(str(rung), 0)
        if not fails:
            return True
        last = st.get("last_trip_end", 0)
        if fails >= FAIL_LIMIT:
            need = st["fail_power"].get(str(rung), 0) + 5
            if need <= SKILL_CAP and need - 5 < MASTERY_FROM:
                return self.trip_power() >= need
            # failed at the cap: no skill is left to gain, so the rest is the time one (what is left to get better is the brain). BotFenceAdvR
            # failed Trinsic and Skara Brae at 100 before the detour (2026-11-03 00:29-02:41) and was offered no trip for 17 hours
        return now - last >= TOWN_FAIL * fails

    def ladder_retreat(self, home, trip):
        """A way back and a place to be mended: a refuge at home, and one in the destination town (a dungeon's way back is its entrance, checked by the route)."""
        gz = ft._gz()
        if gz is None:
            return False
        try:
            if not gz.refuges(home, n=1):
                return False
            if trip["kind"] == "town":
                dest = gz.region(trip["dest"])
                return bool(dest and gz.refuges(dest, n=1))
            return True
        except Exception:
            return False

    def ladder_worth(self):
        return (self.c.gold or 0) + self.facts.get("bank_balance", 0)

    def ladder_kit_strict(self):
        if hasattr(self, "bandages"):
            yellow = sum((i.amount or 1) for i in self.c.backpack if items.potion_kind(i.name) == "heal")
            return self.bandages() >= 15 and yellow >= 3
        return self.trip_kit_ok()

    def ladder_town_ready(self, st, now):
        return ("2" in st["ok"] and self.trip_power() >= POWER[3] and now - st.get("last_trip_end", 0) >= TOWN_GAP and self.ladder_rested(st, 3, now)
                and self.ladder_quiet(st, now) and self.ladder_worth() >= MIN_WORTH)

    def ladder_dungeon_ready(self, st, now):
        return (self.feature("ladder_dungeon") and st.get("trips_ok", 0) >= 2 and self.trip_power() >= POWER[4] and self.c.max_hp >= DUNGEON_HP
                and now - st.get("last_dungeon", 0) >= DUNGEON_GAP and now - st.get("last_trip_end", 0) >= TOWN_GAP and self.ladder_rested(st, 4, now)
                and self.ladder_quiet(st, now) and self.ladder_worth() >= DUNGEON_WORTH and self.ladder_kit_strict())

    def ladder_dungeon_trip(self, home):
        """The trip to the dungeon's surface entrance (gazetteer role dungeon_entrance, the one named DUNGEON), or None."""
        gz = ft._gz()
        if gz is None:
            return None
        cache = self.__dict__.setdefault("_ladder_dungeon", {})
        if home["name"] in cache:
            return cache[home["name"]]
        out = None
        try:
            refuges = gz.refuges(home, n=1)
            start = tuple(refuges[0]) if refuges else (home["centre"][0], home["centre"][1])
            side = gz.side(*start)
            doors = [p for p in gz.near("dungeon_entrance", start[0], start[1], n=40, same_side=True) if p.get("dungeon") == DUNGEON and p.get("side") == side]
            doors.sort(key=lambda p: cheb(DUNGEON_DOOR, (int(p["x"]), int(p["y"]))))          # the chosen door first, then the nearest to it
            if doors:
                d = doors[0]
                end = (int(d["x"]), int(d["y"]))
                if cheb(start, end) <= 1600:
                    out = self.trip_straight(home, DUNGEON, "dungeon", start, end, POWER[4], DUNGEON_HP, DUNGEON_STAY, "ladder_dungeon")
                    out["enter"] = [end[0], end[1], int(d.get("z", 0))]
                    out["rung"] = 4
        except Exception as e:
            self.log(f"ladder: the {DUNGEON} trip could not be built ({type(e).__name__}: {e})")
        cache[home["name"]] = out
        return out

    def ladder_trips(self, home):
        """The trips this bot may take now, by the rungs' gates: towns (rung 3) and the dungeon (rung 4); [] when no rung is open."""
        if not self.ladder_on():
            return []
        st = self.ladder_state()
        now = time.time()
        out = []
        if self.ladder_town_ready(st, now):
            gate_on = hasattr(self, "gate_on") and self.gate_on()
            for t in self.trips_for_home(home):
                if t.get("gate") and not gate_on:
                    continue                                    # a moongate trip only with gate_travel (gate.py)
                if t["kind"] == "town" and self.ladder_retreat(home, t):
                    out.append(dict(t, rung=3))
        if self.ladder_dungeon_ready(st, now):
            d = self.ladder_dungeon_trip(home)
            if d and self.ladder_retreat(home, d):
                out.append(dict(d))
        return out

    def ladder_choose(self, ok):
        """From the trips that passed every gate: the dungeon when it is open, else the town seen least, then the nearest (fewest steps)."""
        st = self.ladder_state()
        dungeon = [t for t in ok if t.get("rung") == 4]
        if dungeon:
            return dungeon[0]
        # a failed trip counts against its town as a visit does: BotHealAdvR, never let into Trinsic (0 visits), chose it over Minoc and Vesper (1 each)
        # three times and turned back each time at 1570,2152 (a pack, then a reaper twice, 2026-11-02 15:59-19:13); a player tries another road
        dest_fails = st.get("dest_fails") or {}
        mem = getattr(self, "mem", None)

        def fleet_blocked(dest):
            try:
                return mem is not None and not mem.usable("trip_dest", dest)
            except Exception:
                return False
        # a town another bot was just turned back from comes last for everyone (ladder_trip_end's fleet block, TOWN_FAIL): every Trinsic trip met the
        # troll and ettin camp by 1516,2125 or the reaper by 1570,2152, and each ladder bot found it out twice for itself (2026-11-02 21:2x-23:23)
        return min(ok, key=lambda t: (fleet_blocked(t["dest"]), st["visits"].get(t["dest"], 0) + dest_fails.get(t["dest"], 0), ft.steps_of(t["wps"])))

    def ladder_again(self):
        """r_trip's once-only flag does not hold for a ladder bot: another trip after TOWN_GAP minutes."""
        if not self.ladder_on():
            return False
        return time.time() - self.ladder_state().get("last_trip_end", 0) >= TOWN_GAP

    # ---- the door and the outcome --------------------------------------------------------------------------------------------------------------------

    def ladder_arrive(self, t, trip):
        """At the last waypoint of a dungeon trip: step through the door. A door that did not take the bot ends the visit (home at once)."""
        enter = trip.get("enter") if self.ladder_on() else None
        if not enter:
            return
        gz = ft._gz()
        before = gz.side(self.c.x, self.c.y) if gz else None
        try:
            self.c.gotoexact(enter[0], enter[1], enter[2]).wait(timeout=25)
        except Exception as e:
            self.log(f"ladder: stepping through the door failed ({type(e).__name__}: {e})")
        time.sleep(1.5)
        after = gz.side(self.c.x, self.c.y) if gz else before
        if gz and after == before and hasattr(self, "tele_hop"):
            # the walk stopped beside the door: at Despise Navrey "arrived" at 1297,1080 for 1296,1081 and the bot never stood on the teleporter
            # (BotWarAdvR, 2026-11-04 10:44:55). tele_hop ends with a plain step onto the entry (tele_step_dir), as at the Britain sewer hatches
            tr = next((x for x in gz.get().trans if (int(x["src"][0]), int(x["src"][1])) == (int(enter[0]), int(enter[1])) and x.get("src_side") == before), None)
            if tr is not None:
                try:
                    self.tele_allow(tr["dst_side"])
                    self.tele_hop(tr)
                except Exception as e:
                    self.log(f"ladder: the step onto the door failed ({type(e).__name__}: {e})")
                after = gz.side(self.c.x, self.c.y)
        t["entered"] = bool(gz and after != before)
        self.log(f"ladder: the door at {enter[0]},{enter[1]}: {'entered ' + str(after) if t['entered'] else 'did not take the bot'}")
        if not t["entered"]:
            t["enter_failed"] = True

    def ladder_trip_end(self, t, how, completed):
        """first_trip.trip_end: the rung of the finished trip is passed or failed."""
        rung = (t.get("def") or {}).get("rung")
        if not rung or not self.ladder_on():
            return
        st = self.ladder_state()
        now = time.time()
        dest = t["dest"]
        if t.get("aborted") == "restart" and how != "death":
            # a new brain drops the outing it did not start (first_trip.trip_abort("restart")): that says nothing of the road, so no pass, no
            # failure, no fleet block. BotFairArcherVR's 'rung 3 failed at Trinsic (restart)' was the operator's restart (2026-11-02 23:48).
            st["last_trip_end"] = now
            self.log(f"ladder: rung {rung} trip to {dest} ended by a restart: not counted")
            self.ladder_save()
            return
        if rung == 4 and t.get("hunt_cut") and how != "death":
            # the hunt ended out of the dungeon within first_trip.DH_CUT_S: the bot walked itself out (a surface task left running), which says nothing
            # of the dungeon. BotHealAdvR's 'rung 4 passed at Despise' after 0 minutes inside (2026-11-05 06:06)
            st["last_trip_end"] = now
            self.log(f"ladder: rung {rung} trip to {dest} cut short inside: not counted")
            self.ev("rung", n=rung, result="uncounted", dest=dest, why="hunt cut", minutes=round((now - t["t0"]) / 60, 1))
            self.ladder_save()
            return
        ok = how == "home" and bool(completed) and not t.get("aborted") and not t.get("enter_failed") and (rung != 4 or t.get("entered"))
        why = "" if ok else (t.get("aborted") or ("could not enter" if t.get("enter_failed") else how))
        st["last_trip_end"] = now
        if rung == 4:
            st["last_dungeon"] = now
        if ok:
            st["visits"][dest] = st["visits"].get(dest, 0) + 1
            if rung == 3:
                st["trips_ok"] = st.get("trips_ok", 0) + 1
            st["ok"][str(rung)] = now
            st["fails"][str(rung)] = 0
        else:
            st["fails"][str(rung)] = st["fails"].get(str(rung), 0) + 1
            st["fail_power"][str(rung)] = round(self.trip_power(), 1)
            st.setdefault("dest_fails", {})[dest] = st.get("dest_fails", {}).get(dest, 0) + 1      # (ladder_choose)
            if rung == 3 and how != "death" and getattr(self, "mem", None) is not None:
                try:
                    self.mem.record("blocked", kind="trip_dest", key=dest, ttl=TOWN_FAIL)    # the road is news to every ladder bot for the rest's length
                except Exception:
                    pass
            if how == "death":
                st["last_death"] = now
        self.ev("rung", n=rung, result="ok" if ok else "fail", dest=dest, why=why, minutes=round((now - t["t0"]) / 60, 1))
        self.log(f"ladder: rung {rung} {'passed' if ok else 'failed'} at {dest}" + (f" ({why})" if why else ""))
        self.ladder_save()
