"""The hunt task as a py_trees behaviour tree (decision core phase 1, docs/Bot-Farm-Decision-Core-Plan.md; the trade_tree.py pattern): one tick per
brain tick, every step re-checked, nothing blocks on a walk (a goto is issued once and .nav is read each tick), and the state lives in
facts["task"]["state"] so a restarted brain resumes.

    hunt [Sequence, re-checked every tick]
      guard                 the task is still the chosen one (facts["task"] is this task)
      steps [Sequence, resumes the running step]
        travel              route from walkroute.py as legs of at most 40 tiles, one goto per leg, .nav read each tick; nopath: a step out and the leg
                            again (three in a row, or no land route, or ETA + 3 min passed: FAILURE "unreachable")
        work [Loop]         the cycle below, again and again, until the monitor (task_core.py) ends the task
          cycle [Sequence, resumes the running step]
            pick            prey by HunterBot.prey (danger model, worth, other bots' fights, the town guards); two or more other bots on the pack:
                            FAILURE "crowded"; nothing in sight for EMPTY s (a kill or a sighting resets it): FAILURE "empty"; meanwhile it roams the
                            area (a point near one of its spawners every ROAM_S) and rests when hurt with nothing about
            pursue          up to PURSUE_TILES and PURSUE_S from where the chase began; the goto is re-issued when the target moves or the line of
                            sight is lost; beyond the limits the target is dropped (ignored 90 s), never the task
            fight           attack until the target is dead or gone; a hit-point check that yields to r_heal / r_flee happens above the core (the
                            reflexes), the fight resumes after; 40 s without hurting it: dropped
            loot            the kill's own corpse only (a corpse that appeared where the target fell), BotBase.loot_corpse (gold, reagents, gear,
                            carving with a blade carried); pending corpses wait while a hostile is near
A step sets ctx.step ("travel", "roam", "rest", "pick", "pursue", "fight", "loot") for the acted-rule name task:hunt:<step>.
The shared tour (item 5, task kind "tour2"): the same tree with a Buddy step at the head of the cycle (stay within BUDDY_STAY tiles of the partner, bandage
it under buddy.py's HEAL_BELOW, the follower takes prey beside the leader: one pulls, one heals) and the loot by turns (Fight.finish: every second kill is
the partner's to loot; the party loot flag lets either open the other's kill).
"""
from __future__ import annotations

import os
import random
import time

import py_trees
from py_trees.common import Status

NEAR = 15                       # arrived: this close to one of the area's spawners
REACHED = 8                     # a leg's waypoint counts as reached this close
LEG_MAX = 40
TRAVEL_SLACK = 180.0            # seconds over the walk's estimate before "unreachable"
ISSUE_RETRY = 3                 # gotos re-issued for one waypoint (or nopaths) before "unreachable"
EMPTY = 75.0                    # nothing in sight this long since arriving, nothing ever seen here: "empty", the area rests 30 min (the plan's rule)
STALE = 360.0                   # an area that paid and went quiet: no kill this long and nothing in sight for EMPTY s: "stale", a 10 min rest (fields.STALE)
ROAM_S = 40.0
IN_VIEW = 14                    # tiles: what a bot standing at a roam point sees of the next spot
CAMP_WALK = 20.0                # seconds a roam walk may take beyond ROAM_S before the next point is chosen
AROUND = 20
CAMP_S = 0.0                    # (the fallback when task_core.camp_seconds fails; no standing, as there: 2026-10-29)
SHOT_SETTLE_S = 2.5             # seconds after the last arrow left before "no damage" is believed (the arrow is in flight, the damage packet follows)
LOW_HP = 40                     # below this health, with the target within 3 tiles: heal or walk away, never keep fighting (the Watcher, 2026-10-21)
RETREAT_HP = 60                 # a fight going badly (our health under this and the target's share of its health 15 points above ours): leave it before the reflexes' flee line
RETREAT_MARGIN = 15
RETREAT_IGNORE = 300
AVOID_AFTER = 2                 # retreats from one kind in a task: the kind is left alone for the rest of the task
# (CAMP_S above is the fallback when the spawner delay is unknown)
CAMP_NEAR = 8
CROWD_PACK = 2                  # other bots within CROWD_R of the prey: the pack is crowded
CROWD_R = 10
PURSUE_TILES = 25
PURSUE_S = 20.0
RANGED_REACH = 8                # (the crossbow's range; see weapon_reach: a bow fires from 10)
BOW_RANGE, CROSSBOW_RANGE = 10, 8   # Bow.DefMaxRange 10, Crossbow.DefMaxRange 8 (UOContent Items/Weapons/Ranged): the archer stands at its weapon's reach, outside the target's
                                    # approach range (BaseCreature.AcquireOnApproachRange 10 less the shard's monsterAggro.rangeReduction 2 = 8), so the first arrow pulls it alone
                                    # (the owner, 2026-10-29: "A real player would walk just into engagement range to pull a single monster")


def weapon_reach(bot):
    try:
        w = next((i for i in bot.c.equipped if getattr(i, "layer", "") in ("OneHanded", "TwoHanded")), None)
        if w is not None and "crossbow" in (w.name or "").lower():
            return CROSSBOW_RANGE
    except Exception:
        pass
    return BOW_RANGE
NO_HURT_S = 10.0                # a target not hurt in this long is dropped and left alone FLEE_IGNORE s (was 40 s: a rabbit was shot at for 40 s without a hit)
ATTACK_EVERY = 2.5
FIGHT_FROM = 9                  # a target this close on the road is taken; the fight itself is booked (begin_fight) when it is engaged, in reach
LOOT_WALK_S = 15.0
CORPSE_KEEP = 300.0
REST_BELOW = 65
DEBUG = bool(os.environ.get("TASK_CORE_DEBUG"))
ENGAGE_HP = 50                  # no new target is taken under this health unless it is on top of the bot
FIGHT_GAP = 6.0                 # seconds without a fight tick (the reflexes held the tick): the no-hurt clock starts again
FLEE_DROP_S = 10.0              # a target that has been running away this long (not nearer than when the chase began) is dropped and ignored FLEE_IGNORE s
FLEE_IGNORE = 300
BUDDY_STAY = 15                 # the shared tour: walk back to the partner when farther than this with no target in hand
BUDDY_LOST = 180.0              # seconds without the partner in sight: the tour goes on alone (the task is not failed)


def cheb(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


class Ctx:
    def __init__(self, bot, task):
        self.bot, self.task = bot, task
        self.step = "pick"
        self.why = ""

    @property
    def st(self):
        return self.task.setdefault("state", {})

    def fail(self, step, why):
        self.step, self.why = step, why
        return Status.FAILURE

    def here(self):
        return (int(self.bot.c.x), int(self.bot.c.y))

    def nav(self):
        try:
            return self.bot.c.nav
        except Exception:
            return None

    def issue(self, x, y, exact=False):
        """A goto, not waited on: .nav says how it went on the next ticks."""
        st = self.st
        try:
            (self.bot.c.gotoexact if exact else self.bot.c.goto)(int(x), int(y))
        except Exception as e:
            self.bot.log(f"hunt tree: goto {x},{y} raised {type(e).__name__}: {e}")
        st["goto"] = [int(x), int(y), round(time.time(), 1)]

    def walking(self):
        n = self.nav()
        return bool(n and n.active)

    def mobile(self, serial, within=20):
        try:
            return next((m for m in self.bot.c.mobiles(within=within) if m.serial == serial), None)
        except Exception:
            return None

    def partner(self, within=30):
        """The shared tour's partner as a mobile in view, else None."""
        name = self.task.get("partner")
        if not name:
            return None
        try:
            return next((m for m in self.bot.c.mobiles(within=within) if m.name == name and not getattr(m, "is_dead", False)), None)
        except Exception:
            return None

    def reach(self):
        return weapon_reach(self.bot) if getattr(self.bot, "ranged", False) else 1

    def in_reach(self, m):
        d = cheb(self.here(), (m.x, m.y))
        if getattr(self.bot, "ranged", False):
            return d <= weapon_reach(self.bot) and (d <= 1 or self.bot.los(m.serial))
        return d <= 1

    def drop_target(self, why, ignore=90):
        st = self.st
        t = st.get("target")
        if t:
            self.bot.ignored[t["serial"]] = time.time() + ignore
            self.bot.log(f"hunt tree: dropped {t['name']}: {why}")
        st["target"] = None
        self.bot.target = None


class Step(py_trees.behaviour.Behaviour):
    def __init__(self, name, ctx):
        super().__init__(name)
        self.ctx = ctx


class Guard(Step):
    def update(self):
        return Status.SUCCESS if self.ctx.bot.facts.get("task") is self.ctx.task else Status.FAILURE


class Travel(Step):
    """The journey to the area's first spot (travel.py: walk, gate, recall or camp fire, the cheapest safe one), its walk legs one goto at a time with .nav
    read each tick, its other legs one tick at a time; prey met on the road is fought with the cycle's own pursue / fight / loot steps, then the walk goes on."""

    def __init__(self, name, ctx):
        super().__init__(name, ctx)
        self.road = py_trees.composites.Sequence("road", memory=True, children=[Pursue("road pursue", ctx), Fight("road fight", ctx), Loot("road loot", ctx)])

    def update(self):
        c, b, st, task = self.ctx, self.ctx.bot, self.ctx.st, self.ctx.task
        here = c.here()
        spots = task.get("spots") or []
        if not task.get("arrived") and not task.get("_no_road"):
            fight = self.road_fight()
            if fight is not None:
                return fight
        if task.get("arrived") or any(cheb(here, (s[0], s[1])) <= task.get("near", NEAR) for s in spots):
            if not task.get("arrived"):
                task["arrived"] = time.time()
                st["seen_at"] = time.time()
                b.ev("task_arrived", task=task["task"], area=task["area"], mins=round((time.time() - task["t0"]) / 60, 1), journey=(st.get("journey") or {}).get("kind"))
                b.log(f"hunt tree: at {task['area']} after {round((time.time() - task['t0']) / 60, 1)} min")
            return Status.SUCCESS
        c.step = "travel"
        b.activity = f"walking to {task['area']}"
        if not spots:
            return c.fail("travel", "unreachable")
        try:
            import task_core
            if b.hp_pct() < task_core.WALK_HP and not b.threats(10) and not st.get("journey") and time.time() - st.setdefault("hurt_wait", time.time()) < 240:
                c.step = "rest"                              # M1: no far walk below WALK_HP percent health: bandage or wait first (at most four minutes)
                b.activity = "resting before the walk"
                if not b.bandage_self():
                    time.sleep(3.0)
                return Status.RUNNING
        except Exception:
            pass
        eta = task["t0"] + task.get("walk_min", 0.0) * 60.0 + TRAVEL_SLACK
        near_d = min(cheb(here, (s[0], s[1])) for s in spots)
        if "best_d" not in st:
            st["best_d"], st["best_t"] = near_d, task["t0"]           # the first look: the clock runs from the task's start
        elif near_d < st["best_d"] - 3:
            st["best_d"], st["best_t"] = near_d, time.time()        # progress: the destination is 3 tiles nearer than it has been
        stalled = time.time() - st.get("best_t", task["t0"]) > TRAVEL_SLACK
        if time.time() > eta and stalled:                            # past the estimate and no nearer for TRAVEL_SLACK s: a walk still closing in goes on (BotRangerAR's
                                                                     # 280-tile sell walk was estimated at 1.0 min, cut at 4.0 as "unreachable", and the sell banned, 2026-10-29)
            b.log(f"hunt tree: {task['area']} not reached in {round((time.time() - task['t0']) / 60, 1)} min (estimate {task.get('walk_min', 0)}): unreachable")
            return c.fail("travel", "unreachable")
        if st.get("journey") is None:
            dest = min(spots, key=lambda s: cheb(here, (s[0], s[1])))
            dx, dy = dest[0], dest[1]
            if not task.get("_no_road"):                          # a hunting spot is scattered so twenty bots do not stand on one tile; an errand goes to the counter
                try:
                    import places
                    dx, dy = places.scatter(b.name, dest[0], dest[1], r=6)
                except Exception:
                    pass
            j = self.journey(here, (int(dx), int(dy)))
            if j is None:
                return c.fail("travel", "unreachable")
            st["journey"], st["seg"] = j, 0
            task["walk_min"] = max(float(task.get("walk_min") or 0.0), float(j["minutes"]))
            self.load_seg(st)
            b.ev("journey", dest=j["dest"], how=j["kind"], minutes=j["minutes"], walk_minutes=j.get("walk_minutes"), legs=len(j["legs"]), options=j.get("options"))
            if j["kind"] != "walk":
                try:
                    import think
                    think.say(b, {"gate": "Taking the moongate", "recall": "Recalling on my rune", "camp": "Going to my partner's campfire",
                                  "tele": "Heading for the dungeon entrance"}.get(j["kind"], "On my way"))
                except Exception:
                    pass
            b.log(f"hunt tree: journey to {task['area']} ({dx},{dy}): {j['kind']}, {j['minutes']} min (walk {j.get('walk_minutes')}), {len(j['legs'])} legs")
        j = st["journey"]
        seg = j["legs"][st["seg"]]
        if seg["kind"] != "walk":
            import travel
            res = travel.STEPS[seg["kind"]](b, seg, st)
            if res == "running":
                return Status.RUNNING
            if res == "done":
                return self.next_seg(st)
            travel.block(b, seg["kind"], res)
            st["journey"] = None                                  # planned again from here, without that leg kind
            return Status.RUNNING
        route = st.get("route") or []
        if not route:
            return self.next_seg(st)
        if c.walking():
            return Status.RUNNING
        n = c.nav()
        status = n.status if n else "idle"
        last = st.get("goto")
        tgt = tuple(n.target) if n is not None and getattr(n, "target", None) else None
        if last and tgt is not None and cheb(tgt, tuple(last[:2])) > 3:
            last = None                                     # the last walk was a reflex's (flee, avoid, step away), not this leg: issue the leg again, uncounted
        leg = int(st.get("leg", 0))
        while leg < len(route) - 1 and cheb(here, tuple(route[leg])) <= REACHED:
            leg += 1
        last_seg = st["seg"] + 1 >= len(j["legs"])
        done_r = min(REACHED, int(task.get("near", NEAR))) if last_seg else REACHED      # the journey's end is reached at the task's own radius (an errand: 3 tiles)
        if leg == len(route) - 1 and cheb(here, tuple(route[leg])) <= done_r:
            return self.next_seg(st)                          # this walk leg is done
        st["leg"] = leg
        wp = tuple(route[leg])
        if last and status == "nopath" and tuple(last[:2]) == wp:
            if leg < len(route) - 1:
                st["leg"] = leg = leg + 1                       # a waypoint the client cannot reach: the next one (the route is a guide, the client's planner the judge)
                wp = tuple(route[leg])
                st["issued"] = 0
            else:
                st["issued"] = int(st.get("issued", 0)) + 1
                if st["issued"] >= ISSUE_RETRY:
                    b.log(f"hunt tree: no path to {wp} three times: unreachable")
                    self.door_unreachable(j, st)
                    return c.fail("travel", "unreachable")
                try:
                    b.step_out()
                except Exception:
                    pass
        elif last and tuple(last[:2]) == wp and status in ("arrived", "idle", "stopped", "failed") and cheb(here, wp) > REACHED:
            st["issued"] = int(st.get("issued", 0)) + 1
            if st["issued"] >= ISSUE_RETRY:
                b.log(f"hunt tree: the walk to {wp} ended at {here} three times: unreachable")
                self.door_unreachable(j, st)
                return c.fail("travel", "unreachable")
        else:
            st["issued"] = 0
        leg = b.walk_detour(wp) if hasattr(b, "walk_detour") else None
        if leg is not None:
            c.issue(*leg.to)                                  # a danger it does not fight near the way: a short leg round it first (bot_common.walk_detour)
            return Status.RUNNING
        c.issue(*wp)
        return Status.RUNNING

    def journey(self, here, dest):
        try:
            import travel
            return travel.plan_journey(self.ctx.bot, dest)
        except Exception as e:
            self.ctx.bot.log(f"hunt tree: journey: {type(e).__name__}: {e}")
            wps = self.plan(here, dest)
            if wps is None:
                return None
            return {"kind": "walk", "minutes": cheb(here, dest) * 1.3 / 55.0, "walk_minutes": None, "dest": list(dest), "legs": [{"kind": "walk", "to": list(dest), "wps": [list(p) for p in wps]}]}

    DOOR_BLOCK = 6 * 3600     # s a teleporter entry the client could not walk to stays out of every bot's plans

    def door_unreachable(self, j, st):
        """The walk that failed led to a teleporter (the next leg hops): that entry is blocked for every bot (shared memory, tele_entry), so the next plan
        takes another door. tele_route picks the entry nearest the bot, and Covetous's mountain entries (2384,836, 2420,883, 2455,858, 2544,850) lie on ground
        the walk grid calls open and the client cannot walk: BotFenceAdvR and BotSwordBR never got in; through the main door (2498-2500,916) a hand test
        did at once (2026-10-31). A player who cannot reach one door takes the next."""
        try:
            nxt = j["legs"][st["seg"] + 1]
        except (IndexError, KeyError, TypeError):
            return
        if nxt.get("kind") != "tele" or not nxt.get("t"):
            return
        sx, sy = nxt["t"]["src"][0], nxt["t"]["src"][1]
        b = self.ctx.bot
        key = f"{sx},{sy}"
        b.facts.setdefault("tele_bad", {})[key] = time.time() + self.DOOR_BLOCK
        try:
            b.mem.record("blocked", kind="tele_entry", key=key, ttl=self.DOOR_BLOCK)
        except Exception:
            pass
        b.log(f"hunt tree: the teleporter at {key} cannot be walked to: blocked for every bot for {self.DOOR_BLOCK // 3600} h")
        b.ev("door_unreachable", entry=[sx, sy], to=nxt.get("to_side"))

    def load_seg(self, st):
        seg = st["journey"]["legs"][st["seg"]]
        st["route"] = [tuple(p) for p in seg["wps"]] if seg["kind"] == "walk" else []
        st["leg"], st["issued"], st["goto"] = 0, 0, None
        for k in ("gate_goto", "gate_t0", "gate_waits", "gate_radio", "tele_tried", "tele_done"):
            st.pop(k, None)

    def next_seg(self, st):
        j = st["journey"]
        if st["seg"] + 1 >= len(j["legs"]):
            st["journey"] = None                                  # the last leg ended short of the spot: planned again from here (the arrival check comes first)
            st["route"] = None
            return Status.RUNNING
        st["seg"] += 1
        self.load_seg(st)
        return Status.RUNNING

    def road_fight(self):
        """RUNNING while a fight on the road runs (the target or a corpse of ours pending), None when the walk may go on."""
        c, b, st = self.ctx, self.ctx.bot, self.ctx.st
        now = time.time()
        pend = [p for p in st.get("corpses", []) if now - p[4] < CORPSE_KEEP and p[0] not in b.facts["looted"]]
        if not st.get("target") and not pend:
            if b.hp_pct() < ENGAGE_HP:
                return None
            ps = [m for m in b.prey(18) if not b.near_death_spot(m.x, m.y, 40) and not _boxed(b, m) and (m.distance <= 8 or b.safe_ground(m)) and worth_it(b, m)]
            if not ps:
                return None
            m = ps[0]
            st["target"] = {"serial": m.serial, "name": m.name, "t0": now, "xy0": list(c.here()), "txy": [m.x, m.y], "hp0": m.hits, "since": now}
            b.target = m.serial
            b.log(f"hunt tree: {m.name} on the road to {self.ctx.task['area']}: fighting it first")
            self.road.stop(Status.INVALID)
        self.road.tick_once()
        if self.road.status == Status.RUNNING:
            return Status.RUNNING
        self.road.stop(Status.INVALID)
        st["goto"] = None                                       # the fight's walks were not a leg: the next tick issues the leg again, uncounted
        return None

    def plan(self, here, dest):
        """[(x, y)] legs of at most LEG_MAX tiles: walkroute's waypoints, else a straight goto for a near spot; None for no land route."""
        try:
            import walkroute
            try:
                pen = self.ctx.bot.far_penalty()
            except Exception:
                pen = None
            r = walkroute.get().plan(here, dest, pen, step=LEG_MAX)
            if r is not None and r.get("waypoints"):
                wps = [tuple(int(v) for v in p[:2]) for p in r["waypoints"]]
                if cheb(wps[-1], dest) > REACHED:
                    wps.append(dest)
                return wps
            if r is None and cheb(here, dest) > 120:
                return None
        except Exception:
            pass
        return [dest]

def no_hurt_s(b, kind):
    """Seconds with no damage to the target before it is dropped: the swings it takes for a run of misses to be rarer than 1 in 100, at the weapon's pre-AOS
    delay (BaseWeapon.GetDelay: 15000 / ((Stam + 100) x speed) s) and the bot's hit chance against the kind (BaseWeapon.CheckHit: (skill + 50) / ((its
    Wrestling + 50) x 2), the top of creature_stats' range), plus the arrow's settle time for a bow. A flat 10 s gave a bow (speed 20: 3.75 s a shot) two
    shots, and two misses happen 11% of the time at a 0.67 chance (the Watcher, 2026-10-29). NO_HURT_S when anything is unknown."""
    import math
    try:
        e, _ = b.weapon_now()
        speed = float((e or {}).get("speed") or 0)
        skill = float(b.skill_values.get((e or {}).get("skill") or "Wrestling", 0) or 0)
        if speed <= 0:
            return NO_HURT_S
        delay = 15000.0 / ((float(b.c.stamina or 0) + 100.0) * speed)
        import task_core
        task_core.aggressive("cow")                                  # loads creature_stats into task_core._CS
        wr = (task_core._CS.get(kind) or {}).get("wrestling") or [50.0, 50.0]
        h = min(0.98, max(0.05, (skill + 50.0) / ((float(max(wr)) + 50.0) * 2.0)))
        n = math.ceil(math.log(0.01) / math.log(1.0 - h))
        return n * delay + (SHOT_SETTLE_S if (e or {}).get("ammo") else 0.5)
    except Exception:
        return NO_HURT_S


def _escapes(b, m):
    try:
        import task_core as _tc
        return _tc.escapes(b, b.mkey(m))
    except Exception:
        return False


def fights_back(m):
    """A monster, or a creature already in war mode: one that fights whether the bot likes it or not (a peaceful animal beside the bot is still judged by its
    worth: the core camped among rabbits and lost 29 of 44 rabbit fights in the 2026-10-21 simulator read, the rule list 4 of 20)."""
    return bool(getattr(m, "known_monster", False) or getattr(m, "in_war_mode", False))


def _reject_reasons(b, seen, avoid):
    """{reason: count}: the first test (prey() then worth_it(), in their order) that turns each creature in view away (the Watcher, 2026-10-29)."""
    import collections
    out = collections.Counter()
    now = time.time()
    try:
        hostile = {m.serial for m in b.mobs(18)}
        others = b.other_bots(22)
        mine = getattr(b, "target", None)
        import task_core as _tc
        import measured
    except Exception as e:
        return {"diag_error": type(e).__name__}
    for m in seen:
        k = b.mkey(m)
        try:
            if m.serial not in hostile:
                why = "not hostile (notoriety/floor)"
            elif not b.is_prey(m):
                why = "is_prey false"
            elif b.ignored.get(m.serial, 0) >= now:
                why = "ignored"
            elif not (m.distance <= 2 or b.safe_ground(m)):
                why = "unsafe ground"
            elif b.taken_by_other(m, others, mine):
                why = "another bot's"
            elif b.critter_skip(m):
                why = "critter_skip"
            elif m.distance > 1 and b.skip_kind(k):
                why = "skip_kind"
            elif k in _tc.NO_PREY:
                why = "NO_PREY"
            elif _tc.escapes(b, k):
                why = "escapes"
            elif not measured.allowed(b, k)[0]:
                why = "measured EV"
            elif m.distance > 1 and __import__("hunter").in_losing_range(b, m.x, m.y):
                why = "in a losing spawner's range"
            elif (b.facts.get("fists") or _tc.unarmed(b)) and not b.fist_prey(k):
                why = "unarmed: fist prey only"
            elif (measured.net(b, k) is None):
                why = "no measured data: old worth"
            else:
                why = "ok"
        except Exception as e:
            why = f"err {type(e).__name__}"
        out[f"{k}:{why}"] += 1
    return dict(out.most_common(12))


def worth_it(b, m):
    """A target beyond arm's reach must be worth the walk: its measured worth at the floor or more, else a kind the loot table rates above the floor (the
    Watcher's read of the live A/B: rabbits, birds and rats were the core's most-fought kinds), the worth counted at the kind's kill share (learning 4: a
    rabbit escapes three fights in four). A bot fighting with its hands takes what its hands can kill."""
    try:
        import task_core as _tc
        if b.mkey(m) in _tc.NO_PREY or _tc.escapes(b, b.mkey(m)):
            return False                                        # before the fist rule
        import measured
        if not measured.allowed(b, b.mkey(m))[0]:
            return False                                        # measured kill/death rates of the bot's group: an archer in fist mode chased rabbits for 40 s (BotArchAdvR, 12:06, 2026-10-21)
        if b.facts.get("fists") or _tc.unarmed(b):
            return b.fist_prey(b.mkey(m))
        if getattr(b, "ranged", False) and b.ammo() <= 0:
            return False                                        # a bow with no arrows swings nothing (BaseRanged.OnSwing needs ammo): BotFairArcherVR took on a lizardman,
                                                                # a hart and a hind on its way to the shop with none, and died boxed in (2026-11-01)
        n_ = measured.net(b, b.mkey(m))
        if n_ is not None:
            return n_ > 0
        import spots as _sp
        if any(h in b.mkey(m) for h in _sp.HEAVY_UNMEASURED) or _sp.heavy_by_stats(b.mkey(m)):
            return False                                        # an unmeasured heavy kind is not worth the walk (the gazer that killed BotRangerBR, 2026-10-29)                                       # the measured expected value (the old worth floor ignored carving: 2026-10-29)
        share = _tc.kill_share(b, b.mkey(m)) / (_tc.KILL_PRIOR[0] / sum(_tc.KILL_PRIOR))
        w = b.worth(m)
        if w is not None:
            return w * share >= b.WORTH_FLOOR
        return b.unknown_worth(b.mkey(m)) * share > b.WORTH_FLOOR
    except Exception:
        return True


class Buddy(Step):
    """The shared tour's partner step (item 5): heal it when hurt (buddy.py's r_buddy_heal), walk back when it is far and nothing is in hand; the tour goes on
    alone when the partner is out of sight for BUDDY_LOST s."""

    def update(self):
        c, b, st, task = self.ctx, self.ctx.bot, self.ctx.st, self.ctx.task
        now = time.time()
        partner = c.partner()
        if partner is None:
            if st.get("partner_seen") and now - st["partner_seen"] > BUDDY_LOST and not st.get("partner_lost"):
                st["partner_lost"] = True
                b.ev("tour2_alone", partner=task.get("partner"), since=round(now - st["partner_seen"]))
                b.log(f"hunt tree: {task.get('partner')} out of sight for {int(now - st['partner_seen'])} s: the tour goes on alone")
            return Status.SUCCESS
        st["partner_seen"] = now
        st.pop("partner_lost", None)
        fn = getattr(b, "r_buddy_heal", None)
        if fn is not None and not st.get("target"):
            try:
                if fn():
                    c.step = "heal"
                    return Status.RUNNING
            except Exception as e:
                b.log(f"hunt tree: buddy heal: {type(e).__name__}: {e}")
        d = cheb(c.here(), (partner.x, partner.y))
        if not st.get("target") and d > BUDDY_STAY and not b.threats(6):
            c.step = "follow"
            b.activity = f"back to {partner.name}"
            if not c.walking() or cheb(tuple(st.get("goto", [0, 0])[:2]), (partner.x, partner.y)) > 6:
                c.issue(partner.x, partner.y)
            return Status.RUNNING
        return Status.SUCCESS


class Pick(Step):
    def roam_score(self, sp, here):
        """How good a roam target a tour spot is now: the share of its creatures expected back (spots.availability from the last kill any bot recorded there) less its
        distance over 150 tiles; a spot this bot just left is behind every other one (the plan's tour order only breaks ties)."""
        try:
            import spots as spots_mod
            import task_core
            mn, mx = task_core.spawn_delay_at(sp[0], sp[1])
            cell = spots_mod.cell_of(sp[0], sp[1])
            av = spots_mod.availability(self.ctx.bot, {"cell": cell, "mn": mn, "mx": mx})
        except Exception:
            av = 1.0
        d = cheb(here, (sp[0], sp[1]))
        return av - d / 150.0 - (1.0 if d <= IN_VIEW else 0.0)             # a spot already in view from here has just been looked at: last (703 look-arounds in 9 bot-hours, one every 48 s)

    def camp_for(self, p):
        """Seconds to stand at the roam point: a look-around, or the wait for a respawn that is due there (task_core.camp_seconds with the last kill near it)."""
        try:
            import task_core
            import spots as spots_mod
            kills = self.ctx.st.get("spot_kills") or {}
            last = max((t for k, t in kills.items() if cheb(tuple(int(v) for v in k.split(",")), (p[0], p[1])) <= 12), default=None)
            shared = spots_mod.last_kill_at(self.ctx.bot, spots_mod.cell_of(p[0], p[1]))
            last = max(x for x in (last, shared) if x is not None) if (last is not None or shared is not None) else None
            return float(task_core.camp_seconds(p[0], p[1], last))
        except Exception:
            return CAMP_S

    def update(self):
        c, b, st, task = self.ctx, self.ctx.bot, self.ctx.st, self.ctx.task
        now = time.time()
        here = c.here()
        if b.hp_pct() < (95 if task.get("cautious") else REST_BELOW) and not b.threats(10):
            c.step = "rest"
            b.activity = "resting"
            try:
                b.c.call("stop", timeout=3) if c.walking() else None
            except Exception:
                pass
            if not b.bandage_self():
                time.sleep(3.0)
            return Status.RUNNING
        try:
            import task_core as _tc
            if _tc.hurt_bare(b) and not b.mobs(1):
                b.log(f"hunt tree: {b.hp_pct():.0f}% health and nothing to heal with: home to rest")
                return c.fail("pick", "hurt")                   # learning 3: never start a fight hurt with nothing to heal with
        except Exception:
            pass
        try:
            b.fists_check()
        except Exception:
            pass
        if getattr(b, "ranged", False) and b.ammo() == 0 and not b.facts.get("fists"):
            c.step = "resupply"
            try:
                if b.r_resupply():
                    return Status.RUNNING                   # bought arrows (the old rule's code; the resupply task comes in phase 2)
            except Exception as e:
                b.log(f"hunt tree: resupply: {type(e).__name__}: {e}")
            time.sleep(2.0)
            return Status.RUNNING
        if b.hp_pct() < ENGAGE_HP and not b.mobs(2):
            c.step = "rest"
            b.activity = "resting before the next fight"
            if not b.bandage_self():
                time.sleep(3.0)
            return Status.RUNNING
        pend = [p for p in st.get("corpses", []) if now - p[4] < CORPSE_KEEP and p[0] not in b.facts["looted"]]
        if pend and not b.threats(7):
            st["target"] = None
            c.step = "loot"
            return Status.SUCCESS                           # a kill of ours is waiting (a restart, a hostile that came between): the loot step takes it
        t = st.get("target")
        if t and c.mobile(t["serial"]) is not None and now - t.get("t0", now) < PURSUE_S + NO_HURT_S:
            c.step = "pick"
            return Status.SUCCESS                           # a restarted brain: the target it had is still there
        st["target"] = None
        avoid = st.get("avoid_kinds") or []
        prey_all = b.prey(18)
        ps = [m for m in prey_all if not b.near_death_spot(m.x, m.y, 40) and not _boxed(b, m) and (m.distance <= 8 or b.safe_ground(m)) and (m.distance <= 1 or b.mkey(m) not in avoid)
              and ((m.distance <= 1 and fights_back(m)) or ((m.distance <= 2 and fights_back(m) and not _escapes(b, m))) or (task.get("relax") or 0) >= 3 or worth_it(b, m))]
        try:                                                # the pick funnel, once a minute (the Watcher, 2026-10-29: 878 creatures stand within 400 tiles and the bots
            if now - st.get("funnel_at", 0) >= 60:          # make 0.5 kills a spot visit: which test turns them away)
                st["funnel_at"] = now
                import task_core as _tcf
                seen = [m for m in b.c.mobiles(within=18) if not (m.name or "").startswith("Bot") and getattr(m, "notoriety", "") not in ("Innocent", "Invulnerable")]
                f_ = {"seen": len(seen), "prey": len(prey_all), "passed": len(ps), "worth_fail": sum(1 for m in prey_all if not worth_it(b, m)),
                      "death_spot": sum(1 for m in prey_all if b.near_death_spot(m.x, m.y, 40)), "boxed": sum(1 for m in prey_all if _boxed(b, m)),
                      "unsafe": sum(1 for m in prey_all if not (m.distance <= 8 or b.safe_ground(m))), "avoided": sum(1 for m in prey_all if b.mkey(m) in avoid),
                      "judged_out": sum(1 for m in ps if not _tcf.judge_target(b, m)), "pull_out": sum(1 for m in ps if _tcf.pull_crowd(b, m)),
                      "kinds_unprey": sorted({b.mkey(m) for m in seen if m not in prey_all})[:6], "why": _reject_reasons(b, seen, avoid)}
                b.ev("pick_funnel", **f_)
        except Exception:
            pass
        if ps and task.get("task") == "tour2" and task.get("role") == "follower":
            partner = c.partner()
            if partner is not None:
                ps = sorted(ps, key=lambda m: cheb((m.x, m.y), (partner.x, partner.y)))      # one pulls, one heals: the follower fights what reaches the leader
        if ps:
            import task_core as _tc
            judged = [m for m in ps if _tc.judge_target(b, m)]                 # learning 5: the danger model's say on this target and the pack around it, before the first blow
            for m in ps:
                if m not in judged:
                    b.ignored[m.serial] = now + 120
            ps = judged
        if ps:
            m = ps[0]
            others = [o for o in b.other_bots(26) if cheb((o[1], o[2]), (m.x, m.y)) <= CROWD_R]
            if len(others) >= CROWD_PACK:
                b.log(f"hunt tree: {len(others)} other bots on the pack at {m.x},{m.y} ({', '.join(o[0] for o in others[:3])}): crowded")
                return c.fail("pick", "crowded")
            st["target"] = {"serial": m.serial, "name": m.name, "t0": now, "xy0": list(here), "txy": [m.x, m.y], "hp0": m.hits, "since": now}
            st["seen_at"] = now
            st["seen_any"] = True
            b.target = m.serial
            c.step = "pick"
            b.activity = f"going for {m.name}"
            return Status.SUCCESS
        try:
            if any(b.is_prey(m) for m in b.mobs(18)):
                st["seen_at"] = now                         # prey in sight that is not worth the walk right now (ignored lately, a death spot, unsafe ground): the area is not empty
                st["seen_any"] = True
        except Exception:
            pass
        arrived = task.get("arrived") or now
        last_kill = b.facts.get("last_kill_at", 0) or 0
        seen = max(st.get("seen_at", 0) or 0, last_kill, arrived)
        if not st.get("seen_any") and last_kill < arrived and now - arrived >= EMPTY:
            b.log(f"hunt tree: nothing to hunt at {task['area']} in {int(now - arrived)} s since arriving: empty")
            return c.fail("pick", "empty")
        if now - max(last_kill, arrived) >= STALE and now - seen >= EMPTY:
            b.log(f"hunt tree: {task['area']} went quiet: no kill in {int(now - max(last_kill, arrived))} s, nothing in sight for {int(now - seen)} s: stale")
            return c.fail("pick", "stale")
        b.activity = f"working {task['area']}"
        p = st.get("roam")
        spots = task.get("spots") or [[here[0], here[1]]]
        at_spot = bool(p) and not c.walking() and cheb(here, (p[0], p[1])) <= CAMP_NEAR
        if at_spot and st.get("camp_since_p") != p[2]:
            st["camp_since_p"], st["camp_since"] = p[2], now           # the wait counts from ARRIVAL, not from the walk's start: a bot that arrived in 10 s stood 50 more (the 2026-10-21 read: camp 29% of the hour)
        cf = self.camp_for(p) if at_spot else 0.0
        if at_spot and cf > 0 and now - st.get("camp_since", now) <= cf:
            c.step = "camp"                                 # a respawn due here: a player waits for it, a step now and then (as r_camp did)
            b.activity = f"watching the spawn at {p[0]},{p[1]}"
            if now - st.get("camp_step", 0) > 30:
                st["camp_step"] = now
                c.issue(p[0] + random.randint(-2, 2), p[1] + random.randint(-2, 2))
            else:
                time.sleep(3.0)
            return Status.RUNNING
        c.step = "roam"
        if not p or at_spot or not c.walking() or now - p[2] > ROAM_S + 3 * CAMP_WALK:
            empties = st.setdefault("empty_n", {})
            visited = st.setdefault("visited", [])
            cur = st.get("roam_i")
            if p and cur is not None:
                if cur not in visited:
                    visited.append(cur)
                if (st.get("tour_kills") or {}).get(str(cur), 0) == 0 and now - (st.get("seen_at") or 0) > 20:
                    empties[str(cur)] = empties.get(str(cur), 0) + 1       # left with nothing: twice and the spot is passed for the rest of the tour
            order = [k for k in range(len(spots)) if empties.get(str(k), 0) < 2]
            if not order:
                b.log(f"hunt tree: every spot of {task['area']} found empty twice: empty")
                return c.fail("pick", "empty")
            pool = [k for k in order if k != cur] or order
            nxt = max(pool, key=lambda k: self.roam_score(spots[k], here))          # the spot most likely to hold prey now (the shared respawn clock), near first
            st["roam_i"] = nxt
            sp = spots[nxt]
            rx, ry = sp[0] + random.randint(-4, 4), sp[1] + random.randint(-4, 4)
            try:
                import task_core as _tc
                if _tc.in_box(b, rx, ry, pad=6):
                    rx, ry = _tc.box_exit(b, rx, ry)                 # the undead box is closed to a bot under 120 hit points: the roam point is moved out of it
            except Exception:
                pass
            p = st["roam"] = [rx, ry, now]
            c.issue(p[0], p[1])
        return Status.RUNNING


def _boxed(b, m):
    """True when the creature stands in the undead box and the box is closed to this bot."""
    try:
        import task_core as _tc
        return _tc.in_box(b, int(m.x), int(m.y), pad=3)
    except Exception:
        return False


class Pursue(Step):
    def update(self):
        c, b, st = self.ctx, self.ctx.bot, self.ctx.st
        t = st.get("target")
        if not t:
            return Status.SUCCESS
        c.step = "pursue"
        m = c.mobile(t["serial"])
        if m is None or getattr(m, "is_dead", False):
            st["target"] = None
            b.target = None
            return Status.SUCCESS                           # gone before it was reached: observe() books the fight as lost
        if _boxed(b, m):
            c.drop_target("it stands in the undead ground", ignore=FLEE_IGNORE)       # the box is closed to this bot: no chase into it
            return Status.SUCCESS
        if c.in_reach(m):
            b.begin_fight(m)                                # the fight is booked when the target is engaged (in reach), so an abandoned chase is no "lost fight"
            return Status.SUCCESS
        now = time.time()
        d_now = cheb(c.here(), (m.x, m.y))
        t.setdefault("d0", d_now)
        if now - t["t0"] >= FLEE_DROP_S and d_now >= t["d0"] - 1:
            c.drop_target(f"it is running away: {int(now - t['t0'])} s and no nearer ({d_now} tiles)", ignore=FLEE_IGNORE)       # fix B: prey that runs is let go, and left alone for five minutes
            return Status.SUCCESS
        if now - t["t0"] > PURSUE_S or cheb(c.here(), tuple(t["xy0"])) > PURSUE_TILES:
            c.drop_target(f"chased {int(now - t['t0'])} s and {cheb(c.here(), tuple(t['xy0']))} tiles")
            return Status.SUCCESS
        b.activity = f"pursuing {m.name}"
        moved = cheb((m.x, m.y), tuple(t.get("txy", (m.x, m.y))))
        lost_los = getattr(b, "ranged", False) and m.distance > 1 and not b.los(m.serial)
        if not c.walking() or moved > 2 or lost_los:
            t["txy"] = [m.x, m.y]
            c.issue(m.x, m.y)
        return Status.RUNNING


class Fight(Step):
    def update(self):
        c, b, st = self.ctx, self.ctx.bot, self.ctx.st
        t = st.get("target")
        if not t:
            return Status.SUCCESS
        c.step = "fight"
        now = time.time()
        m = c.mobile(t["serial"])
        if m is None or getattr(m, "is_dead", False):
            self.finish(t)
            return Status.SUCCESS
        d = cheb(c.here(), (m.x, m.y))
        if not t.get("opened"):
            t["opened"] = True
            hook = getattr(b, "fight_open", None)          # a brain's own opening move (the bard's provocation), once per target
            if hook is not None:
                try:
                    hook(m)
                except Exception:
                    pass
        try:
            import measured
            t.setdefault("fight_start", now)
            lim = measured.give_up_s(b, b.mkey(m))
            if lim and now - t["fight_start"] > lim and c.in_reach(m):         # the kind's measured ttk_p90 for this group: a fight that long is not a normal one
                try:
                    b.ev("give_up", prey=b.mkey(m), s=round(now - t["fight_start"]), p90=lim)
                except Exception:
                    pass
                c.drop_target(f"{int(now - t['fight_start'])} s against a {m.name} (measured p90 {lim:.0f} s)", ignore=RETREAT_IGNORE)
                return Status.SUCCESS
        except Exception:
            pass
        if now - t.get("since", now) > PURSUE_S + NO_HURT_S + 30:
            c.drop_target("the fight ran too long")
            return Status.SUCCESS
        mine = b.hp_pct()
        theirs = 100.0 * (m.hits or 0) / (m.max_hits or 0) if (m.max_hits or 0) else 100.0
        line = RETREAT_HP + (15 if self.ctx.task.get("cautious") else 0)          # no bandages: leave a losing fight earlier
        try:
            import task_core as _tc
            if getattr(b, "ranged", False) and int((b.c.state or {}).get("maxStam") or 99) < _tc.RANGED_LOW_STAM:
                line += _tc.RANGED_LEAVE                                            # learning 6: an archer with little stamina cannot run from a losing fight late
        except Exception:
            pass
        if mine < LOW_HP and d <= 3 and now - st.get("low_at", 0) > 2.0:
            # the Watcher, 2026-10-21: deaths at 2-4 hit points to a chicken, a hart and a zombie: below LOW_HP with the target close, no more shooting or swinging: heal first (the Heal
            # potion, else a bandage when it is not on top of us), else walk away from it; the reflexes' flee line (40) did not hold for a kiting archer
            st["low_at"] = now
            how = None
            try:
                if b.drink_heal("low hp"):                  # the shared rule (basics.py): one every 10 s, never while poisoned
                    how = "potion"
                if how is None and d >= 2 and b.skill_values.get("Healing", 0) >= 30 and b.bandages() > 0 and b.bandage_self():
                    how = "bandage"
            except Exception:
                how = None
            if how is None:
                how = "walk"
                c.drop_target(f"health {mine:.0f}% with {m.name} {d} tiles off: walking away", ignore=RETREAT_IGNORE)
                try:
                    b.end_fight("flee")
                except Exception:
                    pass
                b.step_away(m, 8)
                b.ev("low_hp", how=how, hp=round(mine), m=b.mkey(m), d=d, theirs=round(theirs))
                return Status.SUCCESS
            b.ev("low_hp", how=how, hp=round(mine), m=b.mkey(m), d=d, theirs=round(theirs))
            time.sleep(1.0)
            return Status.RUNNING
        if mine < line and theirs > mine + RETREAT_MARGIN and d <= 2:
            # losing: leave it now, with health to walk away on, instead of waiting for the flee line (the live A/B: 11 deaths, 36% lost fights)
            kind = b.mkey(m)
            n = st.setdefault("retreats", {})
            n[kind] = n.get(kind, 0) + 1
            if n[kind] >= AVOID_AFTER:
                st.setdefault("avoid_kinds", [])
                if kind not in st["avoid_kinds"]:
                    st["avoid_kinds"].append(kind)
            b.ev("retreat", m=kind, hp=round(mine), theirs=round(theirs), n=n[kind])
            try:
                import think
                think.say(b, f"Backing off from the {m.name.split(' ', 1)[-1] if ' ' in m.name else m.name}, health low", urgent=True)
            except Exception:
                pass
            c.drop_target(f"losing to {m.name} at {mine:.0f}% (it has {theirs:.0f}%)", ignore=RETREAT_IGNORE)
            try:
                b.end_fight("flee")
            except Exception:
                pass
            b.step_away(m, 8)
            return Status.SUCCESS
        if not c.in_reach(m):
            # it moved off (a wandering animal, a monster that turned on someone else): chase it, within the pursuit limits counted from where the chase began
            ch = t.get("chase")
            if not ch:
                ch = t["chase"] = [now, c.here()[0], c.here()[1]]
            if now - ch[0] > FLEE_DROP_S or cheb(c.here(), (ch[1], ch[2])) > PURSUE_TILES:
                c.drop_target(f"it got away: chased {int(now - ch[0])} s and {cheb(c.here(), (ch[1], ch[2]))} tiles", ignore=FLEE_IGNORE)       # fix B: ten seconds of chase, then it is left alone for five minutes
                return Status.SUCCESS
        else:
            t.pop("chase", None)
        if now - t.get("fight_tick", now) > FIGHT_GAP:
            t["since"] = now                                # the reflexes held the tick (a flee, a bandage): the clock starts again
        t["fight_tick"] = now
        if (m.hits or 0) < (t.get("hp0") or 0):
            t["hp0"], t["since"] = m.hits, now
        elif now - t.get("since", now) > no_hurt_s(b, b.mkey(m)):
            c.drop_target(f"not hurt in {int(no_hurt_s(b, b.mkey(m)))} s", ignore=FLEE_IGNORE)
            b.note("combat", f"A {m.name} could not be reached or hurt for 40 s; the bot gave up.", key=f"unreachable:{m.name}")
            return Status.SUCCESS
        b.activity = f"fighting {m.name}"
        if DEBUG:
            b.log(f"fight dbg: {m.name} d={d} here={c.here()} at={m.x},{m.y} hits={m.hits} war={b.c.war_mode} walking={c.walking()} nav={getattr(c.nav(), 'status', '?')}")
        b.begin_fight(m)
        if getattr(b, "ranged", False):
            try:                                                   # arrows into a target that takes no damage (out of line of sight, blocked): 3 arrows with no hit, or 6 shots without a kill: let it be
                import task_core as _tc
                t.setdefault("ammo0", b.ammo())
                t.setdefault("hits0", m.hits or 0)
                shot = int(t["ammo0"]) - int(b.ammo())
                if shot != t.get("shot_n"):
                    t["shot_n"], t["shot_at"] = shot, now                      # the last arrow left now: its damage needs a moment to show
                if (m.hits or 0) < t["hits0"]:
                    t["ammo0"], t["hits0"], t["shot_n"] = b.ammo(), m.hits or 0, 0           # damage dealt: the count of shots with no damage starts again
                limit, p_hit = _tc.miss_limit(b, b.mkey(m))
                if limit is not None and shot >= limit and now - t.get("shot_at", now) >= SHOT_SETTLE_S:
                    try:
                        b.ev("arrows_wasted", prey=b.mkey(m), n=shot, limit=limit, p=round(p_hit, 3))
                    except Exception:
                        pass
                    c.drop_target(f"{shot} shots and no damage (limit {limit} at a {p_hit:.0%} hit chance)", ignore=RETREAT_IGNORE)
                    return Status.SUCCESS
            except Exception:
                pass
            # an adjacent target is shot where it stands: BaseRanged has no minimum range, and every step resets the stationary delay before the next shot
            # (BaseRanged.GetStationaryDelay, UOR: 1000 - (Dex - 25) x 500 / 75 ms). Stepping away 4 tiles from a follower that keeps pace fired nothing: archers moved
            # a median 19 tiles in the fights they lost (the Watcher, 2026-10-29). The low-health retreat above still walks it off.
            if d > 1 and not b.los(m.serial) or d > weapon_reach(b):
                if not c.walking() or cheb((m.x, m.y), tuple(t.get("txy", (m.x, m.y)))) > 2:
                    t["txy"] = [m.x, m.y]
                    c.issue(m.x, m.y)
                return Status.RUNNING
        elif d > 1:
            if not c.walking() or cheb((m.x, m.y), tuple(t.get("txy", (m.x, m.y)))) > 1:
                t["txy"] = [m.x, m.y]
                c.issue(m.x, m.y)
            time.sleep(0.5)
            return Status.RUNNING
        if now - t.get("attacked_at", 0) >= ATTACK_EVERY:
            t["attacked_at"] = now
            if not b.c.war_mode:
                b.c.war(True)
            b.c.attack(m.serial)
        t["txy"] = [m.x, m.y]
        time.sleep(0.6)
        return Status.RUNNING

    def finish(self, t):
        """The target is gone: its corpse (one that appeared where it last stood) is this bot's to loot."""
        c, b, st = self.ctx, self.ctx.bot, self.ctx.st
        xy = tuple(t.get("txy") or (0, 0))
        try:
            corpses = [i for i in b.c.containers(within=16) if "corpse" in (i.name or "").lower() and (i.name or "").lower().startswith(("a ", "an "))
                       and i.serial not in b.facts["looted"] and cheb((i.x, i.y), xy) <= 2]
        except Exception:
            corpses = []
        pend = st.setdefault("corpses", [])
        mine = True
        if corpses and self.ctx.task.get("task") == "tour2" and self.ctx.partner() is not None:
            n = st["kills_n"] = int(st.get("kills_n", 0)) + 1
            mine = (n % 2 == 1) == (self.ctx.task.get("role") == "leader")          # the loot by turns: the odd kills to the leader, the even ones to the follower
            b.ev("loot_turn", mine=mine, n=n, partner=self.ctx.task.get("partner"))
        for i in corpses:
            if mine and all(p[0] != i.serial for p in pend):
                pend.append([i.serial, i.name, i.x, i.y, round(time.time(), 1)])
            elif not mine:
                b.facts["looted"].add(i.serial)                     # the partner's turn: not ours to open
        if corpses:
            spots = self.ctx.task.get("spots") or []
            near = min(range(len(spots)), key=lambda k: cheb((spots[k][0], spots[k][1]), xy), default=None)
            if near is not None and cheb((spots[near][0], spots[near][1]), xy) <= 30:
                st.setdefault("spot_kills", {})[f"{int(spots[near][0])},{int(spots[near][1])}"] = time.time()      # a kill at this spot: its respawn clock (camp_for)
                tk = st.setdefault("tour_kills", {})
                tk[str(near)] = tk.get(str(near), 0) + 1
            try:
                import spots as spots_mod
                b.mem.record("spotkill", cell=spots_mod.cell_of(xy[0], xy[1]))                        # every bot's clock for this spot
            except Exception:
                pass
        st["target"] = None
        b.target = None


class Loot(Step):
    def update(self):
        c, b, st = self.ctx, self.ctx.bot, self.ctx.st
        now = time.time()
        pend = [p for p in st.get("corpses", []) if now - p[4] < CORPSE_KEEP and p[0] not in b.facts["looted"]]
        for p_ in st.get("corpses", []):
            if now - p_[4] >= CORPSE_KEEP and p_[0] not in b.facts["looted"]:
                b.facts["looted"].add(p_[0])
                b.ev("loot_empty", prey=str(p_[1]), why="expired before it was reached")
        st["corpses"] = pend
        if not pend:
            return Status.SUCCESS
        if b.threats(7):
            return Status.SUCCESS                           # the corpse waits; the next cycle fights what came
        c.step = "loot"
        p = pend[0]
        corpse = next((i for i in b.c.containers(within=10) if i.serial == p[0]), None)
        if corpse is None:
            b.ev("loot_empty", prey=str(p[1]), why="the corpse is not in the container list within 10 tiles")
            pend.pop(0)
            return Status.RUNNING
        b.activity = "looting"
        if cheb(c.here(), (corpse.x, corpse.y)) > 1:
            if not c.walking():
                w = st.setdefault("loot_walk", [p[0], now, 0])
                if w[0] != p[0]:
                    w[:] = [p[0], now, 0]
                if now - w[1] > LOOT_WALK_S or w[2] >= ISSUE_RETRY:
                    b.facts["looted"].add(p[0])
                    pend.pop(0)
                    b.log(f"hunt tree: could not reach the corpse of {p[1]} at {corpse.x},{corpse.y}: left")
                    b.ev("loot_empty", prey=str(p[1]), why="could not reach it")
                    return Status.RUNNING
                w[2] += 1
                c.issue(corpse.x, corpse.y, exact=True)
            return Status.RUNNING
        b.facts["looted"].add(p[0])
        pend.pop(0)
        try:
            b.loot_corpse(corpse)
        except Exception as e:
            b.log(f"hunt tree: loot {p[1]}: {type(e).__name__}: {e}")
        return Status.RUNNING if pend else Status.SUCCESS


class Mark(Step):
    """A rune marked where the ground paid (runes.py's own r_rune_mark decides the spot and the way); nothing for a bot that cannot cast Mark."""

    def update(self):
        b, st = self.ctx.bot, self.ctx.st
        try:
            if not (b.rune_on() and b.rune_able()) or st.get("target") or st.get("marked_at", 0) > time.time() - 900:
                return Status.SUCCESS
            if b.r_rune_mark():
                st["marked_at"] = time.time()
                self.ctx.step = "mark"
        except Exception as e:
            b.log(f"hunt tree: mark: {type(e).__name__}: {e}")
        return Status.SUCCESS


class Loop(py_trees.composites.Composite):
    """Ticks its one child again and again: SUCCESS starts it over, FAILURE is passed up, RUNNING stays RUNNING."""

    def __init__(self, name, child):
        super().__init__(name, children=[child])

    def tick(self):
        child = self.children[0]
        for node in child.tick():
            yield node
        if child.status == Status.SUCCESS:
            child.stop(Status.INVALID)
            self.status = Status.RUNNING
        else:
            self.status = child.status
        yield self

    def stop(self, new_status=Status.INVALID):
        self.children[0].stop(new_status)
        self.status = new_status


class Play(Step):
    """A bard's music between fights (the plan: Peacemaking at the feet, Provocation on two hostiles): BardBot.r_music with its own cooldown; nothing for the others."""

    def update(self):
        b = self.ctx.bot
        fn = getattr(b, "r_music", None)
        if fn is None or self.ctx.st.get("target"):
            return Status.SUCCESS
        try:
            if fn():
                self.ctx.step = "play"
        except Exception as e:
            b.log(f"hunt tree: play: {type(e).__name__}: {e}")
        return Status.SUCCESS


def build(ctx):
    head = [Buddy("buddy", ctx)] if ctx.task.get("task") == "tour2" else []
    cycle = py_trees.composites.Sequence("cycle", memory=True, children=head + [Pick("pick", ctx), Pursue("pursue", ctx), Fight("fight", ctx), Loot("loot", ctx), Play("play", ctx), Mark("mark", ctx)])
    steps = py_trees.composites.Sequence("steps", memory=True, children=[Travel("travel", ctx), Loop("work", cycle)])
    return py_trees.composites.Sequence("hunt", memory=False, children=[Guard("guard", ctx), steps])


def render(tree=None):
    if tree is None:
        tree = build(Ctx(None, {"state": {}}))
    return py_trees.display.unicode_tree(tree, show_status=False)


def tick(bot, task):
    """One tick of the hunt task. Returns (step, why): why is "" while the task runs, else the tree's failure ("unreachable", "empty", "crowded")."""
    entry = bot.__dict__.get("_core_tree")
    if entry is None or entry[0].task is not task:
        ctx = Ctx(bot, task)
        entry = bot.__dict__["_core_tree"] = (ctx, build(ctx))
    ctx, root = entry
    ctx.why = ""
    fled = bot.facts.get("hunt_fled")
    if fled and float(fled.get("t", 0)) >= float(task.get("t0", 0)):
        # it ran from something it cannot fight (hunter.r_avoid: a caster, or one that out-damages it): the hunt there ends and the ground rests
        # (task_core.REST_S "danger"), as a player leaves; the roam walked BotMaceAdvR back to the graveyard edge three times in 21 s, into a spectre
        # and a bone mage, dead in 60 s from full health (2026-11-03 23:11)
        bot.facts.pop("hunt_fled", None)
        bot.log(f"hunt tree: ran from {fled.get('by')} at {task.get('area')}: the hunt there ends")
        return ctx.step, "danger"
    if time.time() < float(bot.facts.get("avoided_until", 0) or 0):
        return "wait", ""                                   # r_avoid's commitment (hunter.r_avoid): no roam back toward what it just stepped away from
    root.tick_once()
    if root.status == Status.FAILURE and ctx.why:
        return ctx.step, ctx.why
    if root.status == Status.FAILURE:
        return ctx.step, ""                                 # the guard: the task was replaced under the tree; the next tick builds a new one
    return ctx.step, ""
