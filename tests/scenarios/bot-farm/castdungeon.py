"""A caster's hunt on a dungeon stay (owner, 2026-11-08: casters hunting "the top and bottom levels of despise effectively"). Mixin for CasterBot.

The fighters' stay is the decision core's tour of the dungeon's spots (task_core, hunt_tree); a caster runs mage_bot's rule list, whose patrol (r_explore,
r_hunt) is the surface's, so on a stay it walked back out. r_cdungeon is the stay's patrol for any dungeon, nothing in it knows Despise:
 * the spots are the stay's own (spots.all_spots with facts["dungeon_hunt"]: the dungeon's beginner floor, and the deep spots the rating opened, deep_ok);
 * the pick: the most monsters for the walk, count / (1 + tiles / CD_TILES), skipping a spot another bot works (hunter.HunterBot.ground_load) and one this
   caster rested (an empty spot task_core.REST_S["empty"], one that drove it out twice REST_S["danger"]);
 * the walk: travel.plan_journey (walk legs, and the inner stairs between levels as tele legs, travel.tele_step), a slice a tick so the fight rules
   (earlier in the list) take every monster that comes;
 * at the spot it holds within the spawner's home, and after hunt_tree.EMPTY seconds with nothing to fight the spot rests and the next is picked.
The fight itself is the caster's (r_fight, castfight.py: kiting, the spell that fits, Reactive Armor, Greater Heal); r_dungeon_out (first_trip) still takes
the stair out of a pack it loses. Events: cd_pick {spot, kinds, count, tiles}, cd_rest {spot, why}, cd_arrive {spot, mins}.
"""
from __future__ import annotations

import random
import time

CD_TILES = 40                 # tiles of walk that halve a spot's worth (the core's walk_min weighting, a stay is 40 minutes)
CD_SLICE = 6.0                # s a walk slice runs before the fight rules look again
CD_HOLD = 4                   # tiles round the spawner's centre it stands within
CD_FAIL = 3                   # walk slices in a row without progress that rest the spot "unreachable"
STAIR_POST = 14               # tiles short of the spawn's centre a post stands, toward the stair out: inside a creature's sight (BaseCreature.DefaultRangePerception 16)
POST_MIN = 3                  # and at least this far from the stair's tile (not on it)
POST_HOLD = 2                 # tiles round the post it stands within


class CasterDungeonMixin:

    def cd_state(self):
        return self.__dict__.setdefault("_cd", {})

    def cd_rested(self, sid):
        return float((self.facts.get("cd_rest") or {}).get(str(sid), 0) or 0) > time.time()

    def cd_rest(self, sid, why):
        try:
            import task_core
            secs = float(task_core.REST_S.get(why, task_core.REST_S["empty"]))
        except Exception:
            secs = 1800.0
        self.facts.setdefault("cd_rest", {})[str(sid)] = time.time() + secs
        self.ev("cd_rest", spot=sid, why=why, secs=int(secs))

    def cd_spawn_ok(self, s):
        """spots.spawn_ok cached a minute per spot (the deep spots have it already in all_spots, deep_ok)."""
        cache = self.__dict__.setdefault("_cd_spawn", {})
        hit = cache.get(s["id"])
        now = time.time()
        if hit and now - hit[0] < 60:
            return hit[1]
        import spots
        ok = spots.spawn_ok(self, s)
        cache[s["id"]] = (now, ok)
        return ok

    def ground_load(self, cell):
        import hunter
        return hunter.HunterBot.ground_load(self, cell)

    def cd_pick(self):
        """The spot to walk to, or None."""
        import spots
        here = (int(self.c.x), int(self.c.y))
        best = None
        for s in spots.all_spots(self):
            if self.cd_rested(s["id"]):
                continue
            if not self.cd_spawn_ok(s):
                continue                                        # its whole spawn rates no fight (spots.spawn_ok)
            try:
                import first_trip
                if s.get("side") not in (None, "surface") and not spots.outward_stairs(s.get("side"), (s["x"], s["y"]), first_trip.RETREAT_REACH):
                    continue                                    # no stair out within a retreat's run: Despise's west lizardman spots (93-118 tiles from the
            except Exception:                                   # stair up) were where four casters were boxed in and died (2026-11-09 02:41-04:05)
                pass
            try:
                if self.ground_load(s["cell"]) >= 1:
                    continue                                    # another bot works it
            except Exception:
                pass
            d = max(abs(s["x"] - here[0]), abs(s["y"] - here[1]))
            v = float(s.get("count") or 1) / (1.0 + d / CD_TILES)
            if best is None or v > best[0]:
                best = (v, s, d)
        if best is None:
            return None
        _, s, d = best
        self.ev("cd_pick", spot=s["id"], kinds=list(s.get("kinds") or [])[:4], count=int(s.get("count") or 1), tiles=int(d))
        try:
            self.mem.record("claim", kind="ground", key=f"{s['cell']}#{self.name}", ttl=900)
        except Exception:
            pass
        return s

    def cd_post(self, spot):
        """Where a caster holds for this spot: on the line from the nearest outward stair (spots.outward_stairs within first_trip.RETREAT_REACH) toward the
        spawn's centre, STAIR_POST tiles short of the centre and at least POST_MIN from the stair, on the spot's walkable component; the centre itself with
        no stair in reach. Its monsters see it from their ground and come across the open, one or two ahead of the rest; when the fight turns, the stair
        is a few tiles behind (r_dungeon_out) and no creature follows through it (Teleporter.OnMoveOver: Creatures is off). In the spawn's middle the
        casters were boxed in by five to thirteen lizardmen and died (Despise, 2026-11-09 01:35-05:30)."""
        c = (int(spot["x"]), int(spot["y"]))
        try:
            import first_trip
            import spots
            side = spot.get("side") or (self.facts.get("dungeon_hunt") or {}).get("side")
            out = spots.outward_stairs(side, c, first_trip.RETREAT_REACH)
            if not out:
                return c
            sx, sy = int(out[0][1]["src"][0]), int(out[0][1]["src"][1])
            d = max(abs(c[0] - sx), abs(c[1] - sy))
            comp = spots.component_near(c[0], c[1], side)
            for k in range(max(POST_MIN, d - STAIR_POST), d + 1):
                f = k / float(d or 1)
                p = (int(round(sx + (c[0] - sx) * f)), int(round(sy + (c[1] - sy) * f)))
                if comp is None or spots.component_near(p[0], p[1], side) == comp:
                    return p
        except Exception:
            pass
        return c

    def cd_own_threats(self):
        """The attackers near that are this caster's to deal with: not one another bot stands beside and fights (BotBase.taken_by_other). A lizardman
        BotSorcBR was fighting 12 tiles off held BotMageBR and BotWarlockBR at Despise's stair for minutes, every rule passing (2026-11-09 07:37)."""
        att = self.kite_attackers(12)
        if not att:
            return []
        try:
            others = self.other_bots(16)
            mine = self.fight["serial"] if self.fight else None
            return [m for m in att if not self.taken_by_other(m, others, mine)]
        except Exception:
            return att

    def r_cdungeon(self):
        dh = self.facts.get("dungeon_hunt")
        if not dh or self.c.ghost:
            self.__dict__.pop("_cd", None)
            return False
        st = self.cd_state()
        now = time.time()
        if self.cd_own_threats() or self.prey(10):
            st["seen"] = now
            return False                                        # the fight rules take them (r_fight, r_avoid, r_flee are earlier)
        if (self.c.mana or 0) < 20 and self.hp_pct() >= 50:
            return False                                        # mana first: r_rest (mage_bot) meditates
        try:
            from castfight import HEAL_OUT
        except Exception:
            HEAL_OUT = 65
        if self.hp_pct() < HEAL_OUT:
            # health first: BotWarlockAR's stay resumed at 32 of 93, it walked down the stair to its spot and five lizardmen killed it (2026-11-09 06:44-06:46)
            self.activity = "healing before the walk"
            return bool(self.caster_heal())                     # else r_rest (mage_bot) rests
        spot = st.get("spot")
        if spot is None or self.cd_rested(spot["id"]):
            spot = self.cd_pick()
            if spot is None:
                self.activity = "no dungeon spot open"
                dh.setdefault("nothing_open_since", now)       # first_trip ends the stay "nothing open" after task_core.WAIT_S: BotSorcAR stood at
                return False                                    # Despise's landing for the last 18 minutes of its stay, no spot rating a fight (2026-11-09)
            dh.pop("nothing_open_since", None)
            st.clear()
            st.update(spot=spot, t0=now, seen=now, plan=None, leg=0, legst={}, fails=0, post=self.cd_post(spot))
        here = (int(self.c.x), int(self.c.y))
        sx, sy = st.get("post") or (int(spot["x"]), int(spot["y"]))
        if max(abs(here[0] - sx), abs(here[1] - sy)) <= POST_HOLD:
            if not st.get("arrived"):
                st["arrived"] = now
                st["seen"] = now
                self.ev("cd_arrive", spot=spot["id"], mins=round((now - st["t0"]) / 60.0, 1))
            try:
                import hunt_tree
                empty = float(hunt_tree.EMPTY)
            except Exception:
                empty = 75.0
            if now - float(st.get("seen", now)) > empty:
                self.cd_rest(spot["id"], "empty")
                self.__dict__.pop("_cd", None)
                return True
            if st.get("hold"):
                # the stair hold (stairhold.py): out toward the spawn until one sees it, else stand still (a random step beside the stair is a step on it)
                if self.hold_lure(st, spot, now):
                    return True
                if max(abs(here[0] - sx), abs(here[1] - sy)) > 0:
                    self.c.gotoexact(sx, sy).wait(timeout=CD_SLICE)
                else:
                    time.sleep(1.0)
                self.activity = f"holding the stair for {spot['id']}'s spawn"
                return True
            self.activity = f"waiting by the stair for {spot['id']}'s spawn"
            self.c.goto(sx + random.randint(-1, 1), sy + random.randint(-1, 1)).wait(timeout=CD_SLICE)
            return True
        return self.cd_walk(st, dict(spot, x=sx, y=sy), here)

    def cd_walk(self, st, spot, here):
        """One slice of the journey to the spot: a walk leg toward its end, or a stair (travel.tele_step)."""
        import travel
        if st.get("plan") is None:
            st["plan"] = travel.plan_journey(self, (int(spot["x"]), int(spot["y"])))
            st["leg"], st["legst"] = 0, {}
            if st["plan"] is None:
                self.cd_rest(spot["id"], "unreachable")
                self.__dict__.pop("_cd", None)
                return False
        legs = st["plan"].get("legs") or []
        if st["leg"] >= len(legs):
            st["plan"] = None                                   # the journey ended short of the spot: plan again from here
            st["fails"] = st.get("fails", 0) + 1
            if st["fails"] >= CD_FAIL:
                self.cd_rest(spot["id"], "unreachable")
                self.__dict__.pop("_cd", None)
            return True
        leg = legs[st["leg"]]
        self.activity = f"walking to {spot['id']} (leg {st['leg'] + 1} of {len(legs)})"
        if leg.get("kind") == "tele":
            src = (int(leg["t"]["src"][0]), int(leg["t"]["src"][1]))
            if max(abs(src[0] - here[0]), abs(src[1] - here[1])) > 2:
                # to the stair's entry in slices first: tele_hop's own walk (exit path replays, up to two minutes) holds every other rule, and BotSorcAR
                # came out of one at 17 of 92 with four lizardmen on it and died (Despise, 2026-11-09 01:33-01:35)
                try:
                    self.c.goto(src[0], src[1]).wait(timeout=CD_SLICE)
                except Exception:
                    pass
                if (int(self.c.x), int(self.c.y)) == here:
                    st["fails"] = st.get("fails", 0) + 1
                    if st["fails"] >= CD_FAIL:
                        self.cd_rest(spot["id"], "unreachable")
                        self.__dict__.pop("_cd", None)
                return True
            res = travel.tele_step(self, leg, st["legst"])
            if res == "done":
                st["leg"] += 1
                st["legst"] = {}
            elif res != "done" and st["legst"].get("tele_tried"):
                self.cd_rest(spot["id"], "unreachable")
                self.__dict__.pop("_cd", None)
            return True
        to = leg.get("to") or [spot["x"], spot["y"]]
        wps = [tuple(int(v) for v in p[:2]) for p in (leg.get("wps") or [])] + [tuple(int(v) for v in to[:2])]
        # the next waypoint AFTER the nearest one: "the first one more than 2 tiles off" walked back to the path's start and forward again, BotMageBR
        # bouncing 5574,629 <-> 5582,631 in Despise's landing hall for seven minutes (2026-11-09 02:27-02:34)
        near_i = min(range(len(wps)), key=lambda i: max(abs(wps[i][0] - here[0]), abs(wps[i][1] - here[1])))
        nxt = next((p for p in wps[near_i:] if max(abs(p[0] - here[0]), abs(p[1] - here[1])) > 2), None)
        if nxt is None:
            st["leg"] += 1
            return True
        before = here
        try:
            self.c.goto(int(nxt[0]), int(nxt[1])).wait(timeout=CD_SLICE)
        except Exception:
            pass
        if (int(self.c.x), int(self.c.y)) == before:
            st["fails"] = st.get("fails", 0) + 1
            if st["fails"] >= CD_FAIL:
                self.cd_rest(spot["id"], "unreachable")
                self.__dict__.pop("_cd", None)
        else:
            st["fails"] = 0
        return True

    def retreat_tally(self, now):
        """A caster has no core task: two retreats from the spot it hunts rest that spot "danger" (first_trip.retreat_tally's rule)."""
        st = self.cd_state()
        spot = st.get("spot")
        if not spot:
            return
        st["retreats"] = st.get("retreats", 0) + 1
        if st["retreats"] >= getattr(self, "RETREATS_SPOT", 2):
            self.log(f"castdungeon: {st['retreats']} retreats from {spot['id']}: that ground is given up for now")
            self.cd_rest(spot["id"], "danger")
            self.__dict__.pop("_cd", None)
