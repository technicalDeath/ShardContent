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

    def r_cdungeon(self):
        dh = self.facts.get("dungeon_hunt")
        if not dh or self.c.ghost:
            self.__dict__.pop("_cd", None)
            return False
        st = self.cd_state()
        now = time.time()
        if self.kite_attackers(12) or self.prey(10):
            st["seen"] = now
            return False                                        # the fight rules take them (r_fight, r_avoid, r_flee are earlier)
        if (self.c.mana or 0) < 20 and self.hp_pct() >= 50:
            return False                                        # mana first: r_rest (mage_bot) meditates
        spot = st.get("spot")
        if spot is None or self.cd_rested(spot["id"]):
            spot = self.cd_pick()
            if spot is None:
                self.activity = "no dungeon spot open"
                return False
            st.clear()
            st.update(spot=spot, t0=now, seen=now, plan=None, leg=0, legst={}, fails=0)
        here = (int(self.c.x), int(self.c.y))
        sx, sy = int(spot["x"]), int(spot["y"])
        if max(abs(here[0] - sx), abs(here[1] - sy)) <= max(CD_HOLD, int(spot.get("home") or 0) // 2):
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
            self.activity = f"waiting at {spot['id']} for its spawn"
            r = int(spot.get("home") or CD_HOLD)
            self.c.goto(sx + random.randint(-r // 2, r // 2), sy + random.randint(-r // 2, r // 2)).wait(timeout=CD_SLICE)
            return True
        return self.cd_walk(st, spot, here)

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
