"""The progress check (plan step 2, 2026-10-19; feature "progress_check"; the owner: "the bots need built-in logic to break them out of broken loops, like a
break-even wood/furniture loop. they should have enough smarts to know that what they're doing isn't advancing their goals").

WHAT THE OTHER LAYERS MISS. The stall sense (stall.py) counts any movement as progress: a new item in the pack, a kill, a new high of gold. A bot that is busy
but not getting anywhere passes it every few minutes: BotCarpBR bought boards for about 180 and sold furniture for 150-170 for two hours; BotMageAdvBR's
resupply ran 1,012 times; five casters circled one pasture. The planner (planner.py) rates activities by net worth with the pack valued on paper (products at
material cost x 1.25), so a loop that sells at a loss can still rate well. This layer asks the owner's question instead, once every SAMPLE seconds:

  IS WHAT I AM DOING MOVING MY OWN AMBITION? Over the last HORIZON seconds, against the persona's main ambition (ambition.py; plan_metric):
    * mastery (A3): the working skill per hour (SKILL_TARGET);
    * every other one: REALIZED net worth per hour, gold carried + banked (WORTH_TARGET). The pack does not count: a promise is not progress until it sells.
      Money spent on what the ambition is for (gear upgrades, a house, a spellbook, a tool: INVEST rules) is added back, so buying the goal is no loss.
    * either metric clearly up (STRONG) is progress whatever the ambition; two deaths in the horizon is losing whatever else happened.
  Verdict: advancing / stalled / losing.

NAMED LOOPS, caught sooner (LOOP_WINDOW): a buy-sell loop (LOOP_MIN buys and LOOP_MIN sales whose sum is at most LOOP_MARGIN of what was spent, while skill
barely moved), and circling (an hour inside CIRCLE_BOX tiles without the ambition moving).

WHAT IT DOES (a rethink): stalled, losing or a named loop ->
  * the planner's next-best activity, if the class has more than one (a crafter: gather its own material, or earn; a buy-sell loop goes to gather);
  * the rule that took most of the window (not a safety, fight or fallback rule, nor the new activity's own) is backed off for BAN seconds through the stall
    sense's own switch (stall_off), so the next rule in line gets its turn; a buy-sell loop backs off the rule that did the buying;
  * circling, or a roaming rule in the lead: another area (stall_leave);
  * the third rethink in a row also goes back to town and writes one line to the watcher's queue (once every 2 h).
Every rethink is an ev "rethink" {why, verdict, mins, worth_h, skill_h, deaths, ambition, rules, action}, a log line and a choice record; the next verdict comes
AFTER_RETHINK seconds later on fresh samples, so the new activity is judged on its own.
"""
from __future__ import annotations

import json
import os
import time
from collections import Counter, deque

SAMPLE = 600.0
HORIZON = 3600.0
AFTER_RETHINK = 1800.0
WORTH_TARGET = 60.0                     # realized gold per hour that counts as moving a money ambition (the planner's worth margin)
SKILL_TARGET = 0.5                      # working-skill points per hour that count as moving mastery
STRONG = {"worth": 150.0, "skill": 1.0}
LOSS = -100.0                           # realized gold per hour below which the activity is losing
DEATHS = 2
LOOP_WINDOW = 1800.0
LOOP_MIN = 3
LOOP_MARGIN = 0.10
CIRCLE_BOX = 40
BAN = 3600.0
INVEST = ("r_upgrade", "r_gear", "r_house", "r_book", "r_retool", "r_spellbook", "r_instrument")
BUYERS = ("r_restock", "r_resupply", "r_fletch", "r_chop", "r_pet", "r_tame", "r_market")
REPORT_EVERY = 7200.0
MIN_SAMPLES = 6                         # real samples (10 min apart) before any verdict (v2)
KILLS_TARGET = 5.0                      # kills per hour: a bot that kills this often is not stalled (v2, the Operator's sanity rule)
GATHER = ("r_fish", "r_mine", "r_dig", "r_chop", "r_lumber", "r_tame", "r_cut", "r_smelt")     # a gatherer's livelihood: never backed off (v2)
NOT_WORTH = ("deposit", "withdraw")     # moving gold between pack and bank is no change of worth
PASSIVE = ("Meditation", "Resisting Spells", "Focus", "Hiding", "Detecting Hidden", "Anatomy", "Evaluating Intelligence", "Spirit Speak", "Healing")


# v2 (2026-10-19 14:40, after the first verdicts): worth from the gold ledger (not the lagging bank fact) plus the pack at shop prices, skill from the gain
# tally (working_skill() did not move), MIN_SAMPLES before a verdict, kills or skill gains are never "stalled", a gatherer's own rule is never backed off.


class ProgressMixin:
    def progress_on(self):
        return self.feature("progress_check")

    # ---- inputs ------------------------------------------------------------------------------------------------------------------------------------

    def progress_flow(self, kind, delta, rule):
        """BotBase.after_tick: every change of carried gold, with the event kind it was booked as and the rule credited."""
        if not self.progress_on():
            return
        fl = self.__dict__.setdefault("_pg_flows", deque(maxlen=400))
        fl.append((time.time(), kind, delta, rule))
        if kind not in NOT_WORTH:
            self.__dict__["_pg_ledger"] = self.__dict__.get("_pg_ledger", 0.0) + delta

    def progress_worth(self):
        """Worth for the check (v2): the running sum of every change of carried gold except banking (the bank balance fact lags a deposit, which read
        as a loss), plus the pack at what a shop pays for it now (planner.plan_stock_value: gathered fish, logs, ore and hides count as they are made)."""
        try:
            stock = float(self.plan_stock_value())
        except Exception:
            stock = 0.0
        return self.__dict__.get("_pg_ledger", 0.0) + stock

    def progress_skill(self):
        """Skill points gained in working skills (v2): the gain tally, one per +0.1 (working_skill() was a stale reading: 0.0/h for bots gaining 6 points an hour)."""
        g = getattr(self, "stats", {}).get("gains", {}) or {}
        return 0.1 * sum(v for k, v in g.items() if k not in PASSIVE)

    def progress_deaths(self, since):
        return sum(1 for d in self.facts.get("death_log", []) if d[0] >= since)

    def progress_invested(self, since):
        return -sum(d for t, k, d, r in self.__dict__.get("_pg_flows", ()) if t >= since and d < 0 and r in INVEST)

    # ---- the tick ----------------------------------------------------------------------------------------------------------------------------------

    def progress_tick(self, acted):
        if not self.progress_on() or getattr(self.c, "ghost", False):
            return None
        if getattr(self, "core_active", None) and self.core_active():
            return None                                                     # the decision core's monitor owns progress (task_core.py)
        now = time.time()
        st = self.__dict__.setdefault("_pg", {"samples": deque(maxlen=12), "pos": deque(maxlen=62), "rules": Counter(), "sampled": 0.0, "posed": 0.0, "n": 0})
        st["rules"][str(acted)] += 1
        if now - st["posed"] >= 60:
            if st["pos"] and now - st["posed"] > 300:
                st["pos"].clear()                          # the brain was not ticking
            st["posed"] = now
            st["pos"].append((now, self.c.x, self.c.y))
        if now - st["sampled"] < SAMPLE:
            return None
        if st["samples"] and now - st["sampled"] > 3 * SAMPLE:
            st["samples"].clear()                          # a gap (paused, hung, restarted): judge from fresh samples
        st["sampled"] = now
        st["samples"].append((now, self.progress_worth(), self.progress_skill(), float(getattr(self, "kills", 0) or 0)))
        if now < st.get("quiet_until", 0):
            return None
        loop = self.progress_loop(now, st)
        if loop:
            return self.progress_rethink(st, now, *loop)
        v = self.progress_verdict(now, st)
        if v and v[0] != "advancing":
            return self.progress_rethink(st, now, v[0], v[0], v[1])
        if v:
            st["n"] = 0
        return None

    def progress_window(self, st, now, secs):
        """(oldest sample at least secs - SAMPLE old, latest), or None while the samples do not reach that far back."""
        s = list(st["samples"])
        if len(s) < 2:
            return None
        old = [x for x in s if now - x[0] >= secs - SAMPLE / 2]
        if not old:
            return None
        return old[-1], s[-1]

    def progress_numbers(self, a, b):
        hours = max((b[0] - a[0]) / 3600.0, 1e-6)
        worth_h = (b[1] - a[1] + self.progress_invested(a[0])) / hours
        skill_h = (b[2] - a[2]) / hours
        kills_h = (b[3] - a[3]) / hours if len(a) > 3 and len(b) > 3 else 0.0
        return {"mins": round((b[0] - a[0]) / 60), "worth_h": round(worth_h, 1), "skill_h": round(skill_h, 2), "kills_h": round(kills_h, 1),
                "deaths": self.progress_deaths(a[0])}

    def progress_ambition(self):
        try:
            return self.plan_metric()
        except Exception:
            return "A2", "worth"

    def progress_verdict(self, now, st):
        w = self.progress_window(st, now, HORIZON)
        if not w or len(st["samples"]) < MIN_SAMPLES:
            return None
        num = self.progress_numbers(*w)
        a, metric = self.progress_ambition()
        num["ambition"] = a
        moving = num["skill_h"] >= SKILL_TARGET if metric == "skill" else num["worth_h"] >= WORTH_TARGET
        strong = num["skill_h"] >= STRONG["skill"] or num["worth_h"] >= STRONG["worth"]
        if num["deaths"] >= DEATHS:
            return "losing", num
        if num["worth_h"] <= LOSS and num["skill_h"] < SKILL_TARGET:
            return "losing", num
        if moving or strong or num["skill_h"] >= SKILL_TARGET or num["kills_h"] >= KILLS_TARGET:
            return "advancing", num                        # learning or killing is never "stalled" (v2)
        return "stalled", num

    def progress_loop(self, now, st):
        """(why, verdict, numbers) for a named loop, else None."""
        a, metric = self.progress_ambition()
        w = self.progress_window(st, now, LOOP_WINDOW)
        if w:
            num = self.progress_numbers(*w)
            num["ambition"] = a
            flows = [f for f in self.__dict__.get("_pg_flows", ()) if f[0] >= w[0][0]]
            buys = [f for f in flows if f[1] == "buy" and f[2] < 0 and f[3] not in INVEST]
            sales = [f for f in flows if f[1] in ("sale", "trade") and f[2] > 0]
            spent, got = -sum(f[2] for f in buys), sum(f[2] for f in sales)
            if len(buys) >= LOOP_MIN and len(sales) >= LOOP_MIN and got - spent <= LOOP_MARGIN * spent and num["skill_h"] < SKILL_TARGET:
                buyer = Counter(f[3] for f in buys).most_common(1)[0][0]
                num.update(spent=round(spent), got=round(got), buyer=buyer)
                return f"buy-sell loop: {len(buys)} buys for {spent:.0f} gold, {len(sales)} sales for {got:.0f}, by {buyer}", "loop", num
        pos = list(st["pos"])
        if len(pos) >= 2 and pos[-1][0] - pos[0][0] >= HORIZON - 120:
            xs, ys = [p[1] for p in pos], [p[2] for p in pos]
            if max(xs) - min(xs) <= CIRCLE_BOX and max(ys) - min(ys) <= CIRCLE_BOX:
                v = self.progress_verdict(now, st)
                if v and v[0] != "advancing":
                    box = f"{min(xs)},{min(ys)}-{max(xs)},{max(ys)}"
                    v[1]["box"] = box
                    return f"circling: an hour inside {box} without the ambition moving", "circling", v[1]
        return None

    # ---- the rethink -------------------------------------------------------------------------------------------------------------------------------

    def progress_rethink(self, st, now, why, verdict, num):
        st["n"] += 1
        total = sum(st["rules"].values()) or 1
        top = [(r, round(100 * c / total)) for r, c in st["rules"].most_common(4)]
        actions, keep = [], ()
        try:
            from stall import FALLBACK, NEVER, ROAM
        except Exception:
            FALLBACK, NEVER, ROAM = ("r_wander", "r_idle", "r_rest", "None"), ("r_dead",), ()
        choices = getattr(self, "CHOICES", {}) or {}
        if len(choices) > 1:
            try:
                import planner
                a, metric = self.progress_ambition()
                cur = self.plan_current()
                if verdict == "loop" and "gather" in choices and cur != "gather":
                    for n, key in choices.items():
                        if key:
                            self.facts[key] = now + planner.CHOICE_SECS if n == "gather" else 0
                    self.__dict__.pop("_plan", None)
                    actions.append(f"planner: {cur} -> gather (make its own material)")
                elif self.plan_decide(a, metric, cur, why_stall=True):
                    actions.append(f"planner: {cur} -> {self.plan_current()}")
                keep = tuple(getattr(self, "CHOICE_RULES", {}).get(self.plan_current(), ()))
            except Exception as e:
                self.log(f"progress: planner: {type(e).__name__}: {e}")
        lead = next((r for r, _ in top if r not in FALLBACK), None)
        if verdict == "circling" or lead in ROAM or lead in GATHER:            # a gatherer goes to another spot, it does not stop gathering (v2)
            try:
                actions.append(self.stall_leave("no prey"))
                keep = tuple(keep) + tuple(ROAM)
                for r in ROAM:
                    self.facts.get("stall_off", {}).pop(r, None)
            except Exception as e:
                self.log(f"progress: leave: {type(e).__name__}: {e}")
        cause = num.get("buyer") if verdict == "loop" else None
        if cause is None and verdict != "circling" and lead not in ROAM and lead not in GATHER:
            cause = next((r for r, _ in top if r not in FALLBACK and r not in NEVER and r not in keep and r not in GATHER), None)
        if cause:
            self.facts.setdefault("stall_off", {})[cause] = now + BAN
            actions.append(f"backed off {cause} for {int(BAN / 60)} min")
        if st["n"] >= 3:
            try:
                x, y = self.home_centre()
                self.facts.pop("far", None)
                self.c.goto(x, y).wait(timeout=60)
                actions.append(f"back to town ({x},{y})")
            except Exception as e:
                actions.append(f"no change of scene ({type(e).__name__})")
            self.progress_report(why, num, top, actions, now)
        action = "; ".join(actions) or "none: nothing else to try"
        self.log(f"progress: {verdict} - {why if verdict in ('loop', 'circling') else self.progress_say(num)} (rules {', '.join(f'{r} {p}%' for r, p in top)}); doing: {action}")
        try:
            self.ev("rethink", why=why[:200], verdict=verdict, rules=top, action=action[:240], **{k: v for k, v in num.items() if k in (
                "mins", "worth_h", "skill_h", "kills_h", "deaths", "ambition", "spent", "got", "buyer", "box")})
            self.dlog("choice", what="rethink", why=f"{verdict}: {why[:160]}; {action[:160]}")
        except Exception:
            pass
        st["samples"].clear()
        st["pos"].clear()
        st["rules"] = Counter()
        st["quiet_until"] = now + AFTER_RETHINK
        return verdict

    @staticmethod
    def progress_say(num):
        return (f"{num['mins']} min: {num['worth_h']:+.0f} gold/h, {num['skill_h']:+.2f} skill/h, {num['deaths']} deaths, ambition {num.get('ambition')}")

    def progress_report(self, why, num, top, actions, now):
        if now - self.facts.get("progress_reported", 0) < REPORT_EVERY:
            return
        self.facts["progress_reported"] = now
        here = os.path.dirname(os.path.abspath(__file__))
        queue = os.path.join(here, "..", "..", "..", "..", "work", "botfarm-watch", "queue.jsonl")
        line = {"t": time.strftime("%Y-%m-%dT%H:%M"), "sev": "medium", "kind": "progress", "area": "brains", "bot": self.name, "why": why[:240],
                "numbers": {k: v for k, v in num.items() if k in ("mins", "worth_h", "skill_h", "deaths", "ambition")}, "rules": top,
                "action": "; ".join(actions)[:240], "status": "open", "owner": "BotFarm Watcher", "from": "brain"}
        try:
            with open(queue, "ab") as f:
                f.write((json.dumps(line, ensure_ascii=False) + "\n").encode("utf-8"))
        except OSError:
            pass
