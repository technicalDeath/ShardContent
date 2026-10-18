"""Stall sense (G11, 2026-10-17; feature "stall_sense"): a bot notices when its work has stopped paying and does something else, as a player would.

Tonight's four cases (tailors with the wrong cloth, carpenters with nothing to learn, smiths who could not reach their bank money, ghosts walking back
and forth) were one pattern: a rule quietly stops working and nothing in the bot notices. This layer watches progress, not rules:

  progress = a gain in a working skill (not Meditation, Resisting Spells and the other passive ones: fighters meditating in town gain fast and are not
             working), a new high of net worth (carried + banked), a kill, or more of some item than the pack has held since the last progress
             (consumables left out; a high-water mark, so dropping and picking up the same thing is not progress).

After STALL seconds with none of it (ghosts and paused bots excluded; the clock stops while the brain is not ticking) the bot logs why: the rules
that acted and the commonest recent log line. Then it changes course, escalating while the stall lasts:

  1st stall  the profession's own switch (stall_switch: a crafter re-learns its menu, gathers its own material, or hunts vermin for coins); a bot
             looking for prey (ROAM rules on top) or hurt by something (a DANGER line) leaves the area for another ground (stall_leave); otherwise
             the rule that took most ticks is backed off for BACKOFF seconds so the next rule in line gets a turn (fallback rules such as r_wander
             are never "the cause": something above them declined).
  2nd        the same, plus a change of scene: back to the home town's centre (a wedged pocket, a dead spot).
  3rd+       also one line in the watcher's queue (work/botfarm-watch/queue.jsonl) per hour: the bot cannot help itself.

Every stall is an ev "stall" {n, mins, rules, why, action} in decisions.jsonl; progress after a stall is an ev "unstalled" {mins, by}.
"""
from __future__ import annotations

import json
import os
import re
import time
from collections import Counter

STALL = 900.0
SAMPLE = 60.0
BACKOFF = 1200.0
PASSIVE = ("Meditation", "Resisting Spells", "Focus", "Hiding", "Detecting Hidden", "Anatomy", "Evaluating Intelligence", "Spirit Speak", "Healing")
CONSUMABLE = ("gold coin", "bandage", "potion", "arrow", "bolt", "black pearl", "blood moss", "garlic", "ginseng", "mandrake", "nightshade", "sulfurous ash",
              "spider's silk", "kindling", "reagent", "scroll")
FALLBACK = ("r_wander", "r_idle", "r_rest", "None")
NEVER = ("r_dead", "r_corpse", "r_flee", "r_cure", "r_heal", "r_fight", "r_avoid", "r_evade", "r_gear", "r_far", "r_sewer_out", "r_buddy_heal", "r_party_heal")
ROAM = ("r_explore", "r_hunt", "r_camp", "r_tame", "r_rest", "r_avoid", "r_music", "r_buddy")     # looking for prey: the answer is another place, not a back-off
DANGER = re.compile(r"\b(hurt|danger|deadly|flee|fleeing|fled|running toward town|not in view)\b", re.I)
LEAVE_MIN = 30
BUSY = ("r_trip", "r_far", "r_dead", "r_corpse", "r_break")      # a long walk with a purpose (a trip, a far service walk, a corpse run): logged, not changed
MASK = re.compile(r"-?\d+(?:\.\d+)?")


class StallMixin:
    # ---- the progress measure ------------------------------------------------------------------------------------------------------------------------

    def stall_measure(self):
        gains = sum(v for k, v in getattr(self, "stats", {}).get("gains", {}).items() if k not in PASSIVE)
        worth = (self.c.gold or 0) + (self.facts.get("bank_balance", 0) or 0)
        pack = Counter()
        try:
            for it in self.c.backpack:
                n = (it.name or "").lower()
                if n and not any(w in n for w in CONSUMABLE):
                    pack[n] += it.amount or 1
        except Exception:
            pass
        return gains, worth, getattr(self, "kills", 0), pack

    def stall_tick(self, acted):
        if not self.feature("stall_sense"):
            return
        st = self.__dict__.setdefault("_stall", {})
        now = time.time()
        if not st.get("purged"):
            st["purged"] = True
            for r in ROAM:
                self.facts.get("stall_off", {}).pop(r, None)        # an older brain's back-off of a roaming rule (it left casters with no rule)
        st.setdefault("rules", Counter())[str(acted)] += 1
        if now - st.get("sampled", 0) < SAMPLE:
            return
        gap = now - st.get("sampled", now)
        st["sampled"] = now
        gains, worth, kills, pack = self.stall_measure()
        if "since" not in st or self.c.ghost:
            self.stall_reset(st, now, gains, worth, kills, pack)          # first sample, or a ghost: recovery has its own rules
            return
        if gap > 3 * SAMPLE:
            st["since"] += gap - SAMPLE                                     # the brain was not ticking (paused, hung): not the bot's stall
            st["last_act"] = st.get("last_act", st["since"]) + gap - SAMPLE
        by = []
        if gains > st["gains"]:
            by.append("skill")
        if worth > st["worth"]:
            by.append("gold")
        if kills > st["kills"]:
            by.append("kill")
        more = [n for n, a in pack.items() if a > st["pack"].get(n, 0)]
        if more:
            by.append("items:" + ",".join(sorted(more)[:3]))
        if by:
            if st.get("n"):
                self.log(f"stall over after {int((now - st['since']) / 60)} min: {' '.join(by)}")
                self.ev("unstalled", mins=round((now - st["since"]) / 60), by=by)
            self.stall_reset(st, now, gains, worth, kills, pack)
            return
        for n, a in pack.items():
            st["pack"][n] = max(st["pack"].get(n, 0), a)
        if now - st.get("last_act", st["since"]) >= STALL:
            st["last_act"] = now
            st["n"] = st.get("n", 0) + 1
            self.stall_act(st, now)

    def stall_reset(self, st, now, gains, worth, kills, pack):
        st.update(since=now, last_act=now, gains=gains, worth=worth, kills=kills, pack=dict(pack), n=0, rules=Counter())

    # ---- what the bot does about it ------------------------------------------------------------------------------------------------------------------

    def stall_why(self):
        """The commonest recent line of the bot's own log (numbers masked), and the last 'skip -' reason."""
        try:
            with open(self.log_path, "rb") as f:
                f.seek(max(0, os.path.getsize(self.log_path) - 40000))
                lines = f.read().decode("utf-8", "replace").splitlines()[-300:]
        except OSError:
            return ""
        body = [l[11:] if l.startswith("[") else l for l in lines]
        body = [l for l in body if l and not l.startswith(("rule ->", "tick ", "stall", "facts taken", "features now"))]
        skip = next((l for l in reversed(body) if " skip - " in l), "")
        common = Counter(MASK.sub("#", l)[:100] for l in body).most_common(1)
        out = common[0][0] if common else ""
        return (out + (f" | last skip: {skip[:100]}" if skip and skip[:60] not in out else "")).strip()

    def stall_leave(self, why):
        """Another place (the watcher: backing off r_explore helped 0 of 6 stalled hunters). No prey: this area counts as crowded for LEAVE_MIN
        minutes, so the ground choice (best_ground, the sewer spots, the casters' camps, tamer spots) passes it over. Danger: a "hurt" record in the
        shared memory, which the area danger map weighs like part of a death for every bot. Either way the held ground and patrol spot are dropped."""
        held = self.facts.get("ground")
        x, y = (held["x"], held["y"]) if held else (self.c.x, self.c.y)
        try:
            from memory import cell_of
        except Exception:
            def cell_of(a, b):
                return f"{int(a) // 40 * 40},{int(b) // 40 * 40}"
        cells = {cell_of(x, y), cell_of(self.c.x, self.c.y)}
        if why == "danger":
            try:                                           # danger is shared knowledge, not a crowd: the area danger map reads it (patch_hurt_mark.py)
                self.mem.record("hurt", at=[int(self.c.x), int(self.c.y)], cell=cell_of(self.c.x, self.c.y), skill=round(self.working_skill())
                                if hasattr(self, "working_skill") else None)
            except Exception:
                pass
        else:
            until = time.time() + LEAVE_MIN * 60
            for cell in cells:
                self.facts.setdefault("crowded", {})[cell] = until
        self.facts["ground"] = None
        self.facts.pop("anchor", None)
        if hasattr(self, "cur_spot"):
            self.cur_spot = None
        self.facts["pushed_at"] = 0                        # not "a near one first": a different area
        return f"leave the area at {x},{y} for {LEAVE_MIN} min ({why}): another ground"

    def stall_skip(self, name):
        """True while the stall sense has backed this rule off."""
        return time.time() < self.facts.get("stall_off", {}).get(name, 0)

    def stall_act(self, st, now):
        mins = round((now - st["since"]) / 60)
        total = sum(st["rules"].values()) or 1
        top = [(r, round(100 * c / total)) for r, c in st["rules"].most_common(4)]
        why = self.stall_why()
        n = st["n"]
        actions = []
        keep = ()
        try:
            own = self.stall_switch(n) if hasattr(self, "stall_switch") else None     # (what it does, the rules it relies on)
        except Exception as e:
            own = None
            self.log(f"stall_switch: {type(e).__name__}: {e}")
        if own:
            actions.append(own[0])
            keep = own[1]
        if top and top[0][0] in BUSY:
            self.log(f"stall {n}: no progress for {mins} min, but on {top[0][0]} (a walk with its own limits): left alone")
            self.ev("stall", n=n, mins=mins, rules=top, why=why[:240], action="none: " + top[0][0])
            return
        lead = next((r for r, _ in top if r not in FALLBACK), None)      # past "None" and r_wander: a backed-off r_explore leaves ticks with no rule
        roaming = lead in ROAM
        if not own and (roaming or DANGER.search(why or "")):
            actions.append(self.stall_leave("danger" if DANGER.search(why or "") else "no prey"))
            keep = ROAM                                   # the explore and hunt rules take it to the next ground
            for r in ROAM:
                self.facts.get("stall_off", {}).pop(r, None)      # and an older back-off of them ends
        cause = None if keep is ROAM else next((r for r, _ in top if r not in FALLBACK and r not in NEVER and r not in keep), None)    # leaving is the whole answer
        if cause:
            self.facts.setdefault("stall_off", {})[cause] = now + BACKOFF
            actions.append(f"backed off {cause} for {int(BACKOFF / 60)} min")
        if n >= 2 or not actions:
            try:
                x, y = self.home_centre()
                self.facts.pop("far", None)
                self.activity = "stalled: back to town to think again"
                self.c.goto(x, y).wait(timeout=60)
                actions.append(f"back to town ({x},{y})")
            except Exception as e:
                actions.append(f"no change of scene ({type(e).__name__})")
        action = "; ".join(actions)
        self.log(f"stall {n}: no progress for {mins} min (rules {', '.join(f'{r} {p}%' for r, p in top)}; commonest line: {why[:200]}); doing: {action}")
        self.ev("stall", n=n, mins=mins, rules=top, why=why[:240], action=action)
        if n >= 3 and now - self.facts.get("stall_reported", 0) > 3600:
            self.facts["stall_reported"] = now
            here = os.path.dirname(os.path.abspath(__file__))
            queue = os.path.join(here, "..", "..", "..", "..", "work", "botfarm-watch", "queue.jsonl")
            line = {"t": time.strftime("%Y-%m-%dT%H:%M"), "sev": "medium", "kind": "stall", "area": "brains", "bot": self.name, "mins": mins, "rules": top,
                    "why": why[:240], "action": action, "status": "open", "owner": "BotFarm Watcher", "from": "brain"}
            try:
                with open(queue, "ab") as f:
                    f.write((json.dumps(line, ensure_ascii=False) + "\n").encode("utf-8"))
            except OSError:
                pass
