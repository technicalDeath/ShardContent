"""The ambition planner, v2 (R4; feature "planner"; needs "ambitions"): a bot picks its activity by how fast each one has moved its main ambition.

THE RATE: the persona's main ambition (A7 company uses the secondary) sets the measure: A3 mastery -> the working skill per hour; every other one ->
net worth per hour (carried + banked gold + the pack at known prices: gathered material counts), the fund a home, a livelihood or a possession is bought from. Every WINDOW seconds the bot credits the change
to the activity that was CHOSEN in that window (not the rule that happened to tick: selling and banking are part of crafting), and keeps an
exponential average per activity in facts["act_rates"]. Each window also goes to the shared memory (memory/activity_rates.json, keyed by
profession, measure and activity), so a bot that has never gathered knows what gathering paid other bots of its trade.

THE CHOICE: at each window's end the bot compares its activities (its own estimate after MIN_OWN windows, else the profession's after MIN_SHARED,
else unknown). It switches when another feasible one is clearly better (SWITCH_RATIO and a margin), tries an unknown one now and then when the
current one pays nothing (every EXPLORE_EVERY at most), and the stall sense (stall.py) asks it for the next best when progress stops altogether.
A choice other than the default is a timed window (CHOICE_SECS) that the profession's own rules read; it then falls back to the default.

LEVERS per class (CHOICES): crafters: craft (default) / gather (facts stall_gather_until: r_chop, r_dig, r_smelt run before the shop) / earn
(facts stall_earn_until: r_earn hunts vermin for coins). Other classes are measured only for now (one activity, "work"), so the watcher sees rates.

ROLLOUT: "planner" measures (all bots); "planner_switch" also lets it choose and switch (the watcher's canary, half the crafters first).
Events: ev "plan_rate" {activity, metric, rate, own, n} per window; ev "plan" {ambition, metric, from, to, why, rates} on a switch.
"""
from __future__ import annotations

import json
import os
import time

import farmdb

WINDOW = 600.0
VERSION = 2              # rates measured before products were valued at cost (v1 scored crafting as a loss) are dropped
ALPHA = 0.35
MIN_OWN, MIN_SHARED = 2, 3
SWITCH_RATIO = 1.5
MARGIN = {"worth": 60.0, "skill": 0.4}
EXPLORE_EVERY = 7200.0
CHOICE_SECS = 1500.0
HERE = os.path.dirname(os.path.abspath(__file__))
SHARED = os.path.join(HERE, "..", "..", "..", "..", "work", "botfarm", "memory", "activity_rates.json")
NAMES = {"A1": "home", "A2": "livelihood", "A3": "mastery", "A4": "adventure", "A5": "possessions", "A6": "renown", "A7": "company"}


class PlannerMixin:
    CHOICES = {"work": None}             # activity -> the facts key of its window (None: the default, no window)
    DEFAULT_CHOICE = "work"
    CHOICE_RULES = {}                     # activity -> the rules it runs (the stall sense does not back them off)

    def planner_on(self):
        f = getattr(self, "features", ())
        return "planner" in f and "ambitions" in f

    def planner_acts(self):
        """Measuring is "planner"; choosing and switching also needs "planner_switch" (the watcher's canary)."""
        return self.planner_on() and "planner_switch" in getattr(self, "features", ())

    def plan_metric(self):
        p = self.persona()
        a = p["second"] if p["main"] == "A7" else p["main"]
        return a, ("skill" if a == "A3" else "worth")

    def plan_value(self, metric):
        if metric == "skill":
            return float(self.working_skill())
        return float((self.c.gold or 0) + (self.facts.get("bank_balance", 0) or 0)) + self.plan_stock_value()

    def plan_stock_value(self):
        """The pack at known prices (the watcher: gathering makes boards and ingots, not coin): what a shop pays for it, else half what a shop asks
        (raw material), else nothing (a newbied starter piece nobody buys). Gold is counted apart."""
        try:
            vendors = self.mem.state["world"]["vendors"]
        except Exception:
            return 0.0
        buys, asks = {}, {}
        for v in vendors.values():
            for item, price in v.get("buys", {}).items():
                buys[item] = max(buys.get(item, 0), price)
            for item, (price, qty) in v.get("stock", {}).items():
                if price > 0:
                    asks[item] = min(asks.get(item, price), price)
        total = 0.0
        try:
            pack = list(self.c.backpack)
        except Exception:
            return 0.0
        for it in pack:
            n = (it.name or "").lower()
            if not n or n.startswith("gold coin"):
                continue
            each = buys.get(n, 0) or 0.5 * asks.get(n, 0) or self.plan_unpriced(n, buys, asks)
            total += each * (it.amount or 1)
        return total

    def plan_unpriced(self, name, buys, asks):
        """An item no shop has priced: worth nothing here; a crafter values its own products at cost (CrafterBot)."""
        return 0.0

    def plan_current(self):
        now = time.time()
        for name, key in self.CHOICES.items():
            if key and now < self.facts.get(key, 0):
                return name
        return self.DEFAULT_CHOICE

    def plan_feasible(self, name):
        return True

    # ---- estimates -------------------------------------------------------------------------------------------------------------------------------

    def plan_shared_key(self, metric, name):
        return f"v{VERSION}|{getattr(self, 'pname', '?')}|{metric}|{name}"

    def plan_shared(self):
        """The profession-wide rates, from the farm's database (farmdb: atomic, no lost updates); the JSON file is the fallback and an export."""
        try:
            return farmdb.rate_table("activity", import_json=SHARED)
        except Exception:
            try:
                return json.load(open(SHARED, encoding="utf-8"))
            except (OSError, ValueError):
                return {}

    def plan_share(self, metric, name, rate):
        k = self.plan_shared_key(metric, name)
        try:
            farmdb.rate_update("activity", k, rate, ALPHA)                 # atomic: the old read-change-rewrite of the JSON file lost concurrent updates
            farmdb.export_json("activity", SHARED)
        except Exception as e:
            self.log(f"planner: shared rate write failed ({type(e).__name__}: {e})")

    def plan_estimate(self, metric, name, shared=None):
        """(rate, source) or (None, "unknown")."""
        own = self.facts.get("act_rates", {}).get(f"{metric}|{name}")
        if own and own[1] >= MIN_OWN:
            return own[0], "own"
        sh = (shared if shared is not None else self.plan_shared()).get(self.plan_shared_key(metric, name))
        if sh and sh[1] >= MIN_SHARED:
            return sh[0], "trade"
        return None, "unknown"

    # ---- the tick --------------------------------------------------------------------------------------------------------------------------------

    def plan_tick(self, acted):
        if not self.planner_on() or getattr(self.c, "ghost", False):
            self.__dict__.pop("_plan", None)
            return
        now = time.time()
        if self.facts.get("plan_v") != VERSION:
            self.facts["act_rates"] = {}                    # an older model's rates (see VERSION)
            self.facts["plan_v"] = VERSION
        a, metric = self.plan_metric()
        st = self.__dict__.get("_plan")
        cur = self.plan_current()
        if not st or st["metric"] != metric or st["choice"] != cur:
            self.__dict__["_plan"] = {"t0": now, "v0": self.plan_value(metric), "metric": metric, "choice": cur, "last": now}
            return
        gap = now - st["last"]
        st["last"] = now
        if gap > 180:
            st["t0"], st["v0"] = now, self.plan_value(metric)       # the brain was not ticking: start the window again
            return
        if now - st["t0"] < WINDOW:
            return
        v = self.plan_value(metric)
        rate = (v - st["v0"]) / ((now - st["t0"]) / 3600.0)
        st["t0"], st["v0"] = now, v
        rates = self.facts.setdefault("act_rates", {})
        k = f"{metric}|{cur}"
        old = rates.get(k)
        rates[k] = [round(rate if not old else old[0] + ALPHA * (rate - old[0]), 2), (old[1] if old else 0) + 1]
        self.plan_share(metric, cur, rate)
        self.ev("plan_rate", activity=cur, metric=metric, rate=round(rate, 2), own=rates[k][0], n=rates[k][1])
        if len(self.CHOICES) > 1 and self.planner_acts():
            self.plan_decide(a, metric, cur, why_stall=False)

    def plan_decide(self, a, metric, cur, why_stall):
        """Pick the activity for the next while; True when it switched. why_stall: the stall sense asks (anything but the current one)."""
        now = time.time()
        shared = self.plan_shared()
        est = {n: self.plan_estimate(metric, n, shared) for n in self.CHOICES if self.plan_feasible(n)}
        if not est:
            return False
        cur_rate = est.get(cur, (None, ""))[0]
        known = {n: r for n, (r, _) in est.items() if r is not None}
        unknown = [n for n, (r, _) in est.items() if r is None and n != cur]
        to, why = None, ""
        others = {n: r for n, r in known.items() if n != cur}
        if why_stall:
            if unknown and now - self.facts.get("plan_explored_at", 0) > EXPLORE_EVERY / 4:
                to, why = unknown[0], "stalled: try what it has not measured"
            elif others:
                to = max(others, key=others.get)
                why = f"stalled: the next best ({others[to]:.1f}/h)"
        elif cur_rate is None:
            return False                                  # the current one is not measured yet: keep at it
        elif others:
            best = max(others, key=others.get)
            if others[best] > max(cur_rate * SWITCH_RATIO, cur_rate + MARGIN[metric]):
                to, why = best, f"{best} pays {others[best]:.1f}/h against {cur_rate:.1f}"
        if to is None and not why_stall and unknown and cur_rate <= 0 and now - self.facts.get("plan_explored_at", 0) > EXPLORE_EVERY:
            to, why = unknown[0], "the current one pays nothing: try what it has not measured"
        if to is None:
            return False
        if to in unknown:
            self.facts["plan_explored_at"] = now
        for n, key in self.CHOICES.items():
            if key:
                self.facts[key] = now + CHOICE_SECS if n == to else 0
        self.__dict__.pop("_plan", None)
        rates = {n: (round(r, 1) if r is not None else None) for n, (r, _) in est.items()}
        self.ev("plan", ambition=f"{a} {NAMES.get(a, a)}", metric=metric, **{"from": cur, "to": to}, why=why, rates=rates)
        self.log(f"plan: {cur} -> {to} for {NAMES.get(a, a)} ({why}; rates {rates})")
        return True

    def plan_for_stall(self):
        """stall.py: the planner's way out, or None when it has nothing else to offer."""
        if not self.planner_acts() or len(self.CHOICES) < 2:
            return None
        a, metric = self.plan_metric()
        cur = self.plan_current()
        if self.plan_decide(a, metric, cur, why_stall=True):
            to = self.plan_current()
            return f"planner: {cur} -> {to}", tuple(self.CHOICE_RULES.get(to, ()))
        return None
