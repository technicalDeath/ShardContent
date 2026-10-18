"""Long walks as routed legs in the goto wrapper (Operator's finding, 14:30; the Helper). Mixin for BotBase, written into the bot-farm folder by patch_goto_routed.py.

The finding: explore gotos of 200+ tiles answered "arrived plans=1 nodes=60000": the client planner gives up around 150-200 tiles and stops at the closest tile (Helper 2's goto_far
turns that into "nopath: closest"), so a hunter or tamer whose patrol spot is 200-380 tiles out never got there and blocked the spot for six hours.

With feature "goto_routed" the wrapper (bot_common._wrap_goto) sends any goto of more than FAR = 120 tiles through goto_routed(): walkroute.plan (the penalty far.py uses: death cells
and strong spawner circles) gives waypoints at most 40 tiles apart; wait() walks the legs (each a plain wrapped goto of under 120 tiles, so tele_wait, the step-out retry and
far_arrival apply to every leg), and the last stretch (within FAR - 20 tiles) is the caller's own plain walk. The answer is the one a plain goto gives: "arrived", "timeout" (the caller's
timeout ran out; the next call resumes from the nearest waypoint, the route is cached), "nopath: closest X,Y" (three legs in a row failed, or no land route: sea between), and, for a
caller that waits 30 seconds or more (the rules cannot run meanwhile) and is not a safety rule, "interrupted: threat: <name>" / "interrupted: hurt" before a leg.
Without the feature, without walkroute or its grid, for a spot off the grid or in a dungeon: None, and the old plain goto.
explore_limit(): the 240 second patrol-spot expiry of hunter / tamer r_explore, longer for a spot that took a routed walk (0.8 s a step, so a 300 tile spot is not dropped half way).
ev goto_route {dest, dist, steps, legs} when a route is planned, once per route; {no_route} when there is none.
"""
import time

import far
from far import FAR, LEG_TIMEOUT, REACHED, STRAY, cheb

TAIL = FAR - 20             # within this many tiles of the target the caller's plain walk takes over
CACHE_S = 900
STEP_S = 0.8
LONG_WAIT = 30


class _Walk:
    def __init__(self, wait):
        self.wait = wait


class GotoRouteMixin:
    _groute = None

    def goto_routed(self, x, y, near=2):
        """A walk object for a goto of more than FAR tiles, or None when the plain goto should be used."""
        if not self.feature("goto_routed"):
            return None
        here = (self.c.x, self.c.y)
        if cheb(here, (x, y)) <= FAR:
            return None
        wr = far._wr()
        if wr is None:
            return None
        g = wr.get()
        if g.snap(x, y, 30) is None or g.snap(here[0], here[1], 30) is None:
            return None
        if self.facts.get("far") and cheb(self.facts["far"]["dest"], (x, y)) <= 12:
            return None                                                       # r_far's own trip: its legs are short and it decides itself
        route = self._groute
        if not route or cheb(route["dest"], (x, y)) > 12 or time.time() - route["t"] > (600 if route.get("dead") else CACHE_S):
            route = self._groute = self._goto_plan(wr, here, (x, y))
        if route.get("dead"):
            return _Walk(lambda timeout=300.0, poll=0.1: "nopath: no land route")
        bot = self

        def wait(timeout=300.0, poll=0.1):
            return bot._goto_legs(route, (x, y), near, timeout)

        return _Walk(wait)

    def _goto_plan(self, wr, here, dest):
        d = cheb(here, dest)
        try:
            r = wr.get().plan(here, dest, self.far_penalty())
        except Exception as e:
            self.log(f"routed goto: planning failed ({type(e).__name__}: {e})")
            r = None
        if r is None:
            self.ev("goto_route", dest=list(dest), dist=d, no_route=True)
            return {"dest": dest, "t": time.time(), "dead": True, "wps": [], "steps": 0, "fails": 0}
        route = {"dest": dest, "t": time.time(), "wps": [list(p) for p in r["waypoints"]], "steps": r["steps"], "fails": 0, "replan_at": 0}
        self.ev("goto_route", dest=list(dest), dist=d, steps=r["steps"], legs=len(route["wps"]))
        return route

    def _goto_legs(self, route, dest, near, timeout):
        end = time.time() + timeout
        safe = getattr(self, "current_rule", "") in far.SAFE_BLOCK
        wps = route["wps"]
        while True:
            here = (self.c.x, self.c.y)
            left = end - time.time()
            if cheb(here, dest) <= TAIL:
                return str(self.c.goto(dest[0], dest[1], None, near=near).wait(timeout=max(left, 1)))      # (the route stays cached: explore_limit still reads its length)
            if left <= 1:
                return "timeout"
            if timeout >= LONG_WAIT and not safe:
                why = self._goto_stop(here)
                if why:
                    return f"interrupted: {why}"
            near_i = min(range(len(wps)), key=lambda k: cheb(here, wps[k]))
            if cheb(here, wps[near_i]) > STRAY and time.time() - route.get("replan_at", 0) > 120:
                route["replan_at"] = time.time()
                try:
                    r = far._wr().get().plan(here, dest, self.far_penalty())
                except Exception:
                    r = None
                if r is None:
                    self._groute = None
                    return f"nopath: closest {here[0]},{here[1]}"
                route["wps"] = wps = [list(p) for p in r["waypoints"]]
                near_i = 0
            i = near_i
            while i < len(wps) - 1 and cheb(here, wps[i]) <= REACHED:
                i += 1
            res = str(self.c.goto(wps[i][0], wps[i][1], None, near=REACHED).wait(timeout=min(LEG_TIMEOUT, left)))
            if res == "teleported":
                self._groute = None
                return "interrupted: teleport"
            if res.startswith(("nopath", "blocked")):
                route["fails"] += 1
                if route["fails"] >= 3:
                    self._groute = None
                    return f"nopath: closest {self.c.x},{self.c.y}"
            else:
                route["fails"] = 0

    def _goto_stop(self, here):
        if self.c.ghost:
            return "ghost"
        near = (getattr(self, "threats", None) or self.dangers)(9)
        if near:
            return "threat: " + str(getattr(near[0], "name", "?"))
        if self.hp_pct() < 60:
            return "hurt"
        return None

    def explore_limit(self):
        """Seconds a patrol spot is kept: 240, plus the time a routed walk to it takes."""
        route = self._groute
        spot = getattr(self, "cur_spot", None)
        if route and spot and not route.get("dead") and cheb(route["dest"], spot) <= 12:
            return 240 + int(route["steps"] * STEP_S)
        return 240
