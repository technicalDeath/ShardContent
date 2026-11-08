"""Far service walks as routed, resumable travel (Operator's drop-test finding, 13:09-13:10; the Helper). Mixin for BotBase and CasterBot, written into the bot-farm
folder by patch_far.py.

The finding: BotCarpBR, dropped in Trinsic, wanted the carpenter shop (only Britain has services here: 1,100 tiles away). shop_at did goto(...).wait(timeout=90) -> "timeout",
the next rules walked on through the woods and a brown bear killed it at 1678,2359. Nothing planned the way, nothing checked for threats between legs, nothing asked whether a
1,100-tile walk was worth it, and nothing could resume it.

What a far service walk is now (a target more than FAR = 120 tiles away; nearer walks are untouched):
 * DECIDED first (far_worth, ev far_service {role, dist, decided go|skip, why}): a healer for a ghost is always worth it; a corpse only for 300+ gold lost within 800 tiles;
   the bank only for carried gold of at least max(400, dist / 2); a sell trip for at least max(12, dist / 30) items (or a pack over 85% of its weight); a shop only when the
   bot cannot gather what it needs near home (crafters: can_gather()); anything else up to 600 tiles. A skip is remembered for ten minutes (not re-planned, not re-logged), and
   the caller sets its own throttle (far_after).
 * ROUTED: walkroute.plan(here -> there, penalty) where the penalty is what first_trip uses: cells where bots died (shared memory) merged with the strong spawners' circles
   (hardspots.json). No land route (an island, a sea between): not attempted, logged once (ev far_service decided skip why "no land route").
 * WALKED IN LEGS: waypoints at most 40 tiles apart, every straight leg clear; between legs far_check looks for hostiles within 9 tiles (the usual rules then fight, flee or
   avoid; the trip carries on afterwards), a hurt bot (below 60%) and a ghost (only a healer walk goes on). The walk is a state in facts["far"] {dest, role, wps, i, t0, budget,
   fails}; far_goto returns "moving" after its slice, and rule r_far (after the safety and fight rules, before the economy rules) keeps walking every tick, so a far trip is
   never one 90-second goto. facts["far"] is in BotBase.PERSIST: a restarted brain resumes from the nearest waypoint. Budget: steps // 25 minutes (at least 12), like limit_of.
 * ARRIVAL clears the trip and the throttles the walk made the callers set (stocked_at, soldout_until, sold_at, meat_sold_at, gear_sold_at, sell_skip_until, bank_fail), so the
   rule that wanted the shop, the buyer or the bank runs again at once, now near it. ev far_service decided "arrived" {role, minutes}.
far_goto returns "arrived", "moving", "interrupted: <why>", "skipped: <why>", "timeout: far budget" or "nopath: far"; callers stop on the first four (far_after).
Without walkroute / its grid the walk is the old plain goto.
"""
import basics  # noqa: E402  (shared helpers)
import json
import os
import time

HERE = os.path.dirname(os.path.abspath(__file__))
FAR = 120                  # tiles (Chebyshev) from which a walk is a far walk (the client planner gives up around 150-200 tiles: 60,000 nodes)
NEAR = 6
LEG_TIMEOUT = 25
REACHED = 8
STRAY = 60                 # farther than this from every waypoint: plan again
SAFE_BLOCK = ("r_dead", "r_corpse", "r_gear", "r_cure", "r_flee", "r_avoid", "r_evade", "r_sewer_out", "r_heal", "r_loot", "r_fight", "r_trip")
THROTTLES = {
    "shop": ("stocked_at", "soldout_until"),
    "sell": ("sold_at", "meat_sold_at", "gear_sold_at", "sell_skip_until", "market_at"),
    "bank": ("bank_fail",),
}
_PEN = None


def cheb(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


_wr = basics.walkroute_mod                   # (basics.py: one copy, one loaded grid)


def _circle_pen(wr):
    global _PEN
    if _PEN is None:
        try:
            d = json.load(open(os.path.join(HERE, "hardspots.json"), encoding="utf-8"))
            _PEN = wr.penalty_circles([(c["x"], c["y"], c["r"], c["factor"]) for c in d["circles"]])
        except (OSError, ValueError, KeyError):
            _PEN = {}
    return _PEN



JOURNEY_FROM = 150    # tiles: a far walk this long asks the travel planner first (travel.GATE_SAVE: a gate must save this much)
TELE_CLEAR = 3        # tiles round a known teleporter that a far walk's plan avoids (a cost, not a wall: a walk that wants the teleporter still gets there)
RESTOCK_WAITS_S = 400 # s: a restock refused for weight this recently makes any sell walk worth it (far_worth); twice crafter.RESTOCK_GAP (200 s),
                      # as the restock re-stamps it every gap while it still waits

class FarMixin:
    _far_last = ""
    _far_pen = None
    _far_rules = None

    # ---- the rule list gets r_far -----------------------------------------------------------------------------------------------------------------

    def far_rules(self):
        """The brain's RULES with r_far before the first rule that is not a safety or fight rule (cached)."""
        if self._far_rules is None:
            rules = list(self.RULES)
            if "r_far" not in rules:
                at = next((i for i, r in enumerate(rules) if r not in SAFE_BLOCK), len(rules))
                rules.insert(at, "r_far")
            self._far_rules = rules
        return self._far_rules

    # ---- deciding -----------------------------------------------------------------------------------------------------------------------------------

    def far_penalty(self):
        got = self._far_pen
        if got is None or time.time() - got[0] > 600:
            wr = _wr()
            try:
                mine = wr.penalty_from_memory(self.mem) if getattr(self, "mem", None) is not None else {}
            except Exception:
                mine = {}
            own = []                                              # this bot's own death spots: walks go round them too (repeat deaths walking through)
            try:
                spots = list(getattr(self, "death_spots", None) or []) + [tuple(p) for p in self.facts.get("death_spots", [])]
                own = wr.penalty_circles([(int(x), int(y), 40, 4.0) for x, y in spots[-6:]]) if spots else {}
            except Exception:
                own = {}
            box = {}
            try:
                import task_core
                if task_core.box_bot(self):                          # the undead box north of Britain: a bot under 120 hit points walks round it (RangerAR died inside, 2026-10-21)
                    x0, y0, x1, y1 = task_core.UNDEAD_BOX
                    box = wr.penalty_circles([(cx, 1400, 50, 12.0) for cx in range(x0 + 20, x1, 40)] + [((x0 + x1) // 2, (y0 + y1) // 2, 100, 12.0)])
            except Exception:
                box = {}
            kill = {}
            try:                                                      # spawners holding a kind that kills this group (measured): walks go round their home range
                import spots as _sp
                kill = wr.penalty_circles([(o["x"], o["y"], max(int(o.get("home") or 10), 1) + task_core.PULL_CLEAR, 8.0) for o, _k in _sp.deadly_spawners(self)])   # its creatures notice a walker 14 tiles past the home range (perception 16 - aggro 2), as the spot and prey rules count it (2026-10-29)
            except Exception:
                kill = {}
            tele = {}
            try:                                                      # a teleporter tile on the way sends the walker elsewhere: BotFisherAR, walking Vesper to Britain,
                import bot_common as _bc                              # crossed 2618,977 and landed on Buccaneer's Den with no land route back (2026-10-31)
                tele = wr.penalty_circles([(tx, ty, TELE_CLEAR, 50.0) for tx, ty in _bc.teleporter_tiles()])
            except Exception:
                tele = {}
            got = self._far_pen = (time.time(), wr.penalty_merge(mine, _circle_pen(wr), own, box, kill, tele))
        live = self.live_caster_penalty(_wr()) if hasattr(self, "live_caster_penalty") else {}
        return _wr().penalty_merge(got[1], live) if live else got[1]       # the casters any bot saw in the last 20 min, fresh at every plan

    def runner_penalty(self):
        """far_penalty for a running trip (first_trip, feature trip_run): the casters' lairs only, out to their home range (first_trip.RUN_EDGE), and no
        cost for deaths in memory; the undead box, this bot's death spots and teleporter tiles as far_penalty. A runner outpaces melee, so the melee
        lairs (the sand flats' earth elementals) and the snake cells must not push it round into casters: BotHealAdvR's Covetous trip, planned round
        all of them, ran into the North-west Peaks' air elementals and was refused (2026-11-03)."""
        got = self.__dict__.get("_run_pen")
        if got is None or time.time() - got[0] > 600:
            wr = _wr()
            import first_trip
            import spots as _sp
            import task_core
            parts = [_circle_pen(wr)]
            try:
                spots_ = list(getattr(self, "death_spots", None) or []) + [tuple(p) for p in self.facts.get("death_spots", [])]
                if spots_:
                    parts.append(wr.penalty_circles([(int(x), int(y), 40, 4.0) for x, y in spots_[-6:]]))
            except Exception:
                pass
            try:
                if task_core.box_bot(self):
                    x0, y0, x1, y1 = task_core.UNDEAD_BOX
                    parts.append(wr.penalty_circles([(cx, 1400, 50, 12.0) for cx in range(x0 + 20, x1, 40)] + [((x0 + x1) // 2, (y0 + y1) // 2, 100, 12.0)]))
            except Exception:
                pass
            try:
                parts.append(wr.penalty_circles([(o["x"], o["y"], max(int(o.get("home") or 10), 1) + first_trip.RUN_EDGE, 8.0)
                                                 for o, k in _sp.deadly_spawners(self) if self.trip_caster(k)]))
            except Exception:
                pass
            try:
                import bot_common as _bc
                parts.append(wr.penalty_circles([(tx, ty, TELE_CLEAR, 50.0) for tx, ty in _bc.teleporter_tiles()]))
            except Exception:
                pass
            got = self.__dict__["_run_pen"] = (time.time(), wr.penalty_merge(*parts))
        live = self.live_caster_penalty(_wr()) if hasattr(self, "live_caster_penalty") else {}
        return _wr().penalty_merge(got[1], live) if live else got[1]

    def far_worth(self, role, xy, value=None):
        """(go, why) for a service walk of more than FAR tiles."""
        d = cheb((self.c.x, self.c.y), xy)
        if role == "healer":
            return True, "a ghost needs the healer"
        if role == "corpse":
            ok = (value or 0) >= 300 and d <= 800
            return ok, f"{value or 0} gold on the corpse, {d} tiles away"
        if role == "bank" and value is True:
            # a withdrawal for a purchase the bot is about to make (visit_bank with withdraw): the purchase is the purpose, and its own rule decided it.
            # The deposit floor below refused BotTamerAR its own 170 banked gold for a bow, 206 tiles off, all afternoon (2026-11-01)
            return True, "a withdrawal for a purchase"
        if role == "bank":
            need = max(250, d // 2)                                                # 400 left a saver's purse unbanked (goals)
            heavy = self.c.weight >= 0.8 * self.c.max_weight                       # a full pack is worth the walk too (a heavy fisher idled 15 min)
            return heavy or (value or 0) >= need, f"{value or 0} gold carried, {need} needed for {d} tiles" + (", pack heavy" if heavy else "")
        if role == "sell":
            heavy = self.c.weight >= 0.85 * self.c.max_weight
            if time.time() - float((self.facts or {}).get("restock_heavy_at", 0) or 0) < RESTOCK_WAITS_S:
                # the restock refused for want of room (crafter.too_heavy_to_restock: "selling what it made first"), so the products must go, however few:
                # with the two rules waiting on each other BotSmithBR, its pack at 359-384 of 450, stood 29 minutes in r_wander ("10 items, 12 needed
                # for 139 tiles", 2026-11-03 20:01-20:31)
                heavy = True
            need = max(12, d // 30)
            return heavy or (value or 0) >= need, f"{value or 0} items, {need} needed for {d} tiles" + (", pack heavy" if heavy else "")
        if role == "shop":
            gather = getattr(self, "can_gather", None)
            # (only when gathering may run now: with the planner on "craft" the gather rules are off, and BotSmithBR and BotCarpAR stood waiting with
            # neither material nor a walk to the shop, 70-80% of an hour, 2026-10-30)
            steered = callable(getattr(self, "planner_acts", None)) and self.planner_acts()
            may_gather = not steered or getattr(self, "plan_current", lambda: "gather")() == "gather"
            if getattr(self, "current_rule", "") == "r_restock" and callable(gather) and gather() and may_gather and value is not True:
                # a crafter restocking prefers to chop, dig or fish: the shelves are passed by for that while (soldout_until, which r_chop and r_dig
                # read; trains_on_own_ore's OWN_ORE_FOR). Without it the gather rules waited on the shop ("still has money and the shop has boards")
                # and the shop on the gathering: BotSmithAdvR and BotCarpBR stood 37-40% of an hour in r_wander (2026-11-07 23:12-00:12)
                facts = getattr(self, "facts", None)
                if isinstance(facts, dict):
                    facts["soldout_until"] = max(float(facts.get("soldout_until", 0) or 0), time.time() + float(getattr(self, "OWN_ORE_FOR", 900)))
                return False, "it can gather the material near home"
            return True, "it cannot work without the shop"
        if role == "travel":
            return True, "already decided"
        return d <= 600, f"{d} tiles"

    def far_worth_corpse(self, xy, gold):
        """Is a corpse worth fetching? Near ones always; one more than 120 tiles away only for 300+ gold within 800."""
        d = cheb((self.c.x, self.c.y), xy)
        if d <= FAR:
            return True
        go, why = self.far_worth("corpse", xy, gold)
        self.far_log("corpse", xy, d, "go" if go else "skip", why)
        return go

    def far_log(self, role, xy, d, decided, why, **kw):
        seen = self.facts.setdefault("far_logged", {})
        key = f"{role}|{xy[0] // 20},{xy[1] // 20}|{decided}"
        if time.time() - seen.get(key, 0) > 600 or decided == "arrived":
            seen[key] = time.time()
            try:                                                    # logging must never stop a walk
                self.ev("far_service", role=role, dist=d, decided=decided, why=why, dest=[xy[0], xy[1]], **kw)
                self.log(f"far {role} walk to {xy} ({d} tiles): {decided} - {why}")
            except Exception:
                pass

    # ---- walking --------------------------------------------------------------------------------------------------------------------------------------

    def far_goto(self, xy, role, timeout=90, value=None, near=NEAR):
        """goto(...).wait(timeout) for a place that may be far: near places are the plain goto; far ones are decided, routed and walked in legs (see the module doc)."""
        xy = (int(xy[0]), int(xy[1]))
        here = (self.c.x, self.c.y)
        d = cheb(here, xy)
        wr = _wr()
        other_side = (xy[0] >= 5120) != (here[0] >= 5120)          # a dungeon end: the land grid's plan cannot cross sides (walkroute knows the dungeon grid since item 5), the goto wrapper's teleporter crossing does
        if d <= FAR or other_side or wr is None or wr.get().snap(*xy, 30) is None or wr.get().snap(here[0], here[1], 30) is None:
            self._far_last = ""
            st0 = self.facts.get("far")
            if st0 and d <= FAR and cheb(st0["dest"], xy) <= 12:
                self.facts.pop("far", None)
                self.far_arrived(st0)
            return str(self.c.goto(*xy).wait(timeout=timeout))
        bring = getattr(self, "packy_bring", None)
        if bring is not None:
            bring()                                               # a pack horse comes along on a long walk (packy.py)
        key = f"{role}|{xy[0] // 20},{xy[1] // 20}"
        skips = self.facts.setdefault("far_skip", {})
        if skips.get(key, 0) > time.time():
            self._far_last = "skipped"
            return "skipped: far"
        st = self.facts.get("far")
        if not st or cheb(st["dest"], xy) > 12:
            go, why = self.far_worth(role, xy, value)
            if not go:
                skips[key] = time.time() + 600
                self.far_log(role, xy, d, "skip", why)
                self._far_last = "skipped"
                return "skipped: far"
            st = self.far_plan(role, xy, d)
            if st is None:
                skips[key] = time.time() + 600
                self._far_last = "skipped"
                return "skipped: no land route"
            self.far_log(role, xy, d, "go", why, steps=st["steps"], legs=len(st["wps"]))
        res = self.far_run(st, timeout)
        if res == "arrived":
            self.far_arrived(st)
        self._far_last = res
        return res

    def far_front(self, xy, role, timeout=90, value=None):
        """The guard a caller puts before its own walk to a service: None when the place is near (or the routed walk just arrived, or there is no walkroute) and the caller
        goes on with its own code; else the far_goto result ("moving", "interrupted: ...", "skipped: ...", ...) and the caller stops (far_after sets its throttle)."""
        xy = (int(xy[0]), int(xy[1]))
        if _wr() is None or cheb((self.c.x, self.c.y), xy) <= FAR:
            if cheb((self.c.x, self.c.y), xy) <= FAR:
                self._far_last = ""
            return None
        res = self.far_goto(xy, role, timeout, value)
        if res == "arrived" or cheb((self.c.x, self.c.y), xy) <= FAR:
            return None
        return res or "moving"

    def far_plan(self, role, xy, d, journey=True):
        if journey and d >= JOURNEY_FROM:
            st = self.far_journey(role, xy, d)
            if st is not None:
                return st
        wr = _wr()
        try:
            r = wr.get().plan((self.c.x, self.c.y), xy, self.far_penalty())
        except Exception as e:
            self.log(f"far walk: planning failed ({type(e).__name__}: {e})")
            return None
        if r is None:
            self.far_log(role, xy, d, "skip", "no land route")
            return None
        st = {"dest": [xy[0], xy[1]], "role": role, "wps": [list(p) for p in r["waypoints"]], "i": 0, "t0": time.time(), "steps": r["steps"], "from": [self.c.x, self.c.y],
              "budget": max(12, r["steps"] // 25) * 60 * (2 if role == "healer" else 1), "fails": 0, "replan_at": 0}
        self.facts["far"] = st
        return st

    def far_journey(self, role, xy, d):
        """A far walk the travel planner beats (travel.plan_journey: a public moongate, a marked rune, a party's camp fire): its legs, walked in far_run, or None
        when walking is the cheapest. BotFisherAR, homed in Vesper, walked 1,449 tiles of wilds toward Britain's Fisherman (a grizzly, a slime and two bears
        later it ran back) past Vesper's moongate, which lands 230 tiles from that shop (2026-10-31): every far service walk now asks the planner first."""
        try:
            import travel
            j = travel.plan_journey(self, xy)
        except Exception as e:
            self.log(f"far walk: journey planning failed ({type(e).__name__}: {e})")
            return None
        if not j or j.get("kind") == "walk" or not j.get("legs"):
            return None
        legs = j["legs"]
        first = legs[0]
        st = {"dest": [xy[0], xy[1]], "role": role, "wps": first.get("wps") or [[self.c.x, self.c.y]], "i": 0, "t0": time.time(),
              "steps": int(sum(len(l.get("wps") or []) for l in legs) * 25), "from": [self.c.x, self.c.y],
              "budget": max(12, int(j["minutes"] * 2)) * 60 * (2 if role == "healer" else 1), "fails": 0, "replan_at": 0,
              "legs": legs, "seg": 0, "gst": {}}
        self.facts["far"] = st
        self.log(f"far {role} walk to {xy}: {j['kind']} journey, {j['minutes']} min against {j.get('walk_minutes')} on foot ({len(legs)} legs)")
        self.ev("journey", dest=list(xy), how=j["kind"], minutes=j["minutes"], walk_minutes=j.get("walk_minutes"), legs=len(legs), role=role, options=j.get("options"))
        return st

    def far_journey_step(self, st):
        """The journey's current leg when it is not a walk (or a walk to the next leg that is done): "moving" while it runs, a failure string, or None for a
        walk leg still to walk (far_run walks it). A failed leg blocks that kind (travel.block) and the trip is planned again on foot from here."""
        import travel
        seg = st["legs"][st["seg"]]
        last = st["seg"] >= len(st["legs"]) - 1
        if seg["kind"] == "walk":
            if not last and cheb((self.c.x, self.c.y), tuple(seg["to"])) <= FAR - 20:
                return self.far_next_leg(st)              # near the gate (or the next leg's start): the leg's own step takes the last stretch
            return None
        res = travel.STEPS[seg["kind"]](self, seg, st.setdefault("gst", {}))
        if res == "done":
            return self.far_next_leg(st)
        if res == "running":
            self.facts["far"] = st
            return "moving"
        travel.block(self, seg["kind"], res)
        self.log(f"far walk: the {seg['kind']} leg failed ({res}); on foot from here")
        nst = self.far_plan(st["role"], tuple(st["dest"]), cheb((self.c.x, self.c.y), tuple(st["dest"])), journey=False)
        return "moving" if nst else "nopath: far"

    def far_next_leg(self, st):
        st["seg"] += 1
        st["gst"] = {}
        if st["seg"] < len(st["legs"]):
            nxt = st["legs"][st["seg"]]
            if nxt.get("wps"):
                st["wps"], st["i"], st["replan_at"], st["fails"] = nxt["wps"], 0, 0, 0
        else:
            st.pop("legs", None)
        self.facts["far"] = st
        return "moving"

    def far_threat_coming(self, m):
        return self.threat_coming(m)                      # basics.BasicsMixin.threat_coming (shared with crafting)

    def far_check(self, st):
        """Why the trip must stop now, or None: a hostile near, a hurt bot, a ghost (except on the way to a healer)."""
        if st["role"] == "healer":
            return None
        if self.c.ghost:
            return "ghost"
        corpse_run = bool((self.facts.get("corpse") or {}).get("await_far")) and self.feature("materializing") and self.materializing()      # corpse_run: unseen, so walk on
        if corpse_run:
            return "hurt" if self.hp_pct() < 15 else None
        near = (getattr(self, "threats", None) or self.dangers)(9)          # BotBase.threats: hostiles that can hurt, without the town animals
        near = [m for m in near if self.far_threat_coming(m)]
        if near:
            return "threat: " + str(getattr(near[0], "name", "?"))
        if self.hp_pct() < 60:
            return "hurt"
        return None

    def far_run(self, st, timeout):
        end = time.time() + timeout
        if st.get("legs"):
            if self.far_check(st) is None:
                r = self.far_journey_step(st)
                if r is not None:
                    return r
            st = self.facts.get("far") or st
        wps = st["wps"]
        dest = tuple(st["dest"])
        if st.get("legs") and st["seg"] < len(st["legs"]) - 1:
            seg = st["legs"][st["seg"]]
            # a walk to the gate (or the next leg's start), not yet the place itself; a gate, recall or camp leg has no "to" (travel.plan_journey): its "at"
            # or landing (KeyError 'to' every 2 s on BotTailorBR's house trek, 2026-11-01 20:13)
            to = seg.get("to") or seg.get("at") or seg.get("land")
            if to:
                dest = tuple(to)
            st["hopped"] = True
        if not st.get("hopped") and getattr(self, "rune_hop", None):
            st["hopped"] = True                                 # once per trip: a rune near the destination first (runes.py, feature runes); a refusal walks as before
            if self.rune_hop(dest, st["role"]):
                st["replan_at"] = 0
        while True:
            here = (self.c.x, self.c.y)
            if cheb(here, dest) <= FAR - 20:                    # the far part is done: the last stretch is the caller's own plain walk to the place
                if st.get("legs") and st["seg"] < len(st["legs"]) - 1:
                    return self.far_next_leg(st)            # only the walk to the next leg is done
                self.facts.pop("far", None)
                return "arrived"
            if time.time() - st["t0"] > st["budget"]:
                self.facts.pop("far", None)
                self.far_log(st["role"], dest, cheb(here, dest), "abort", "out of time")
                return "timeout: far budget"
            nxt = wps[min(st.get("i", 0), len(wps) - 1)]
            leg = self.walk_detour(nxt) if hasattr(self, "walk_detour") and not self.c.ghost else None
            if leg is not None:
                # a danger it does not fight in notice range: a short leg round it (bot_common.walk_detour), the walk goes on after it, as a player
                # walks round a camp instead of stopping at it (far_check's "threat" stop, then the flee rules)
                self.c.goto(int(leg.to[0]), int(leg.to[1])).wait(timeout=min(2.0, max(0.5, end - time.time())))
                if time.time() >= end:
                    self.facts["far"] = st
                    return "moving"
                continue
            why = self.far_check(st)
            if why:
                self.facts["far"] = st
                return f"interrupted: {why}"
            # where on the route are we: the first waypoint not yet reached, measured from the nearest one (a bot that fled or died resumes from where it is)
            near_i = min(range(len(wps)), key=lambda k: cheb(here, wps[k]))
            if cheb(here, wps[near_i]) > STRAY and time.time() - st.get("replan_at", 0) > 120:
                st["replan_at"] = time.time()
                r = _wr().get().plan(here, dest, self.far_penalty())
                if r is None:
                    self.facts.pop("far", None)
                    return "nopath: far"
                st["wps"] = wps = [list(p) for p in r["waypoints"]]
                near_i = 0
                st["i"] = 0
            i = max(near_i, min(st.get("i", 0), len(wps) - 1))          # forward only: the nearest waypoint flips where a route doubles back
            while i < len(wps) - 1 and cheb(here, wps[i]) <= REACHED:
                i += 1
            st["i"] = i
            left = end - time.time()
            if left <= 1:
                self.facts["far"] = st
                return "moving"
            res = str(self.c.goto(*wps[i]).wait(timeout=min(LEG_TIMEOUT, left)))
            if res == "teleported":
                self.facts.pop("far", None)
                return "interrupted: teleport"
            if res.startswith(("nopath", "blocked")):
                st["fails"] += 1
                final = i >= len(wps) - 1 and self.feature("walk_fix")       # the last leg cannot be walked: nothing more to try on this route
                if st["fails"] >= (1 if final else 3):
                    self.facts.pop("far", None)
                    if self.feature("walk_fix"):
                        self.facts.setdefault("far_skip", {})[st["role"] + "|" + str(dest[0] // 20) + "," + str(dest[1] // 20)] = time.time() + 600          # as for a shop that is not worth the walk: not again at once
                        self.far_log(st["role"], dest, cheb((self.c.x, self.c.y), dest), "abort", "nopath on " + ("the last leg" if final else "three legs"))
                    return "nopath: far"
            else:
                st["fails"] = 0

    def far_arrived(self, st):
        role = st["role"]
        for k in THROTTLES.get(role, ()):
            self.facts.pop(k, None)
        self.far_log(role, tuple(st["dest"]), 0, "arrived", f"{round((time.time() - st['t0']) / 60, 1)} minutes", minutes=round((time.time() - st["t0"]) / 60, 1))
        mins = (time.time() - st["t0"]) / 60.0
        start = st.get("from")
        covered = cheb(tuple(start), (self.c.x, self.c.y)) if start else 0
        if mins >= 1.0 and covered >= 100:
            rate = covered / mins                             # this bot's own walking speed, by the ground covered (bw.py plans Between Worlds with it)
            old = self.facts.get("walk_rate")
            if old and old > 120:
                old = None                                    # an impossible old reading (planned steps over a teleport)
            if rate <= 120:                                   # faster is a teleport or a moongate, not walking
                self.facts["walk_rate"] = round(rate if not old else old + 0.3 * (rate - old), 1)

    def far_pending(self):
        """True while the last far_goto did not arrive (moving, interrupted or skipped): the caller must not read that as a failure of the place."""
        return str(self._far_last).startswith(("moving", "interrupted", "skipped"))

    def far_after(self, res, role):
        """For callers after far_goto: True when they must stop here (the walk is still on, or was not worth it). A skip sets the caller's own throttle."""
        res = str(res)
        if res.startswith(("moving", "interrupted")):
            return True
        if res.startswith("skipped"):
            now = time.time()
            if role == "sell":
                # a far trip not worth it bars far trips only (r_sell reads it for a buyer over FAR tiles away): as sell_skip_until it also barred the sale
                # from beside the buyer, so BotTinkBR took 12 stacks out of its full bank box every visit and sold none of them (2026-11-05 23:40-00:15)
                self.facts["sell_far_skip_until"] = now + 1800
                self.facts["meat_sold_at"] = now + 1500
                self.facts["gear_sold_at"] = now + 1500
            elif role == "bank":
                self.facts["bank_fail"] = now + 1500
            elif role == "shop":
                self.facts["soldout_until"] = now + 600
            return True
        return False

    def r_far(self):
        if getattr(self, "home_danger", None):
            self.home_danger()                            # a home that keeps killing it: move house (patch_home_town)
        if self.facts.get("rehome_walk") and not self.c.ghost:
            self.facts.pop("rehome_walk", None)
            h = self.home() if getattr(self, "home", None) else None
            if h and not self.in_britain():               # in_britain: in its home town (the name is from the Britain-only days)
                res = self.far_goto(self.home_centre(), "travel", timeout=4)
                self.log(f"home: walking to {h['name']} ({res})")
                return True
        st = self.facts.get("far")
        if not st or self.c.ghost and st["role"] != "healer":
            return False
        if time.time() - st["t0"] > st["budget"]:
            self.facts.pop("far", None)
            return False
        self.activity = f"far {st['role']} walk to {st['dest'][0]},{st['dest'][1]}"
        res = self.far_run(st, 30)
        if res == "arrived":
            self.far_arrived(st)
            return True
        return res == "moving"
