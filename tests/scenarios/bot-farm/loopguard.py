"""Loop guard (mixin for BotBase): see work/botfarm/patches/patch_sewer_exit.py. A rule that spins (the same log line or event over and over) is backed off and reported."""
from __future__ import annotations

import json
import os
import re
import time
from collections import deque

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
QUEUE_PATH = os.path.join(ROOT, "work", "botfarm-watch", "queue.jsonl")
MASK = re.compile(r"-?\d+(?:\.\d+)?")
SKIP_PREFIXES = ("rule ->", "tick ", "start:", "facts taken", "features now", "loop guard")
SKIP_EVENTS = ("loop_guard", "trip_pos", "caster_pos", "area_avoid")      # area_avoid: a planning record, logged in bursts
PROTECTED = ("r_dead", "r_flee", "r_cure", "r_heal", "r_fight", "r_avoid")      # never backed off, only reported
WINDOW, LIMIT = 60.0, 20
BACKOFF, BACKOFF_MAX = 60.0, 900.0
REPORT_EVERY = 1800.0
# the server's refusals (patch_sysguard): the same one more than SYS_LIMIT times in SYS_WINDOW seconds is a loop
REFUSAL = re.compile(r"\b(cannot|can't|can not|must wait|too far|not accessible|no room|is not|are not|unable|out of range|too heavy|too many)\b", re.I)
SYS_WINDOW, SYS_LIMIT = 600.0, 40
SKILL_WAIT = "must wait a few moments to use another skill"
SKILL_GAP_MAX = 20.0


class LoopGuard:
    def guard_seen(self, typ, text):
        """Count one more occurrence of a log line (typ "log") or an event kind (typ "ev") in the last minute; trip the guard past LIMIT."""
        text = str(text)
        if typ == "log" and text.startswith(SKIP_PREFIXES) or typ == "ev" and text in SKIP_EVENTS:
            return
        now = time.time()
        hits = self.__dict__.setdefault("_guard_hits", {})
        key = (typ, MASK.sub("#", text)[:120])
        q = hits.setdefault(key, deque())
        q.append(now)
        while q and now - q[0] > WINDOW:
            q.popleft()
        if len(q) > LIMIT:
            n = len(q)
            q.clear()
            self.guard_trip(typ, text, n)

    def guard_off(self, rule):
        """True while the rule is backed off."""
        off = self.facts.get("rule_off", {}).get(rule)
        return bool(off) and time.time() < off[0]

    def guard_trip(self, typ, text, count):
        rule = getattr(self, "current_rule", None) or getattr(self, "last_rule", None) or "-"
        now = time.time()
        off = self.facts.setdefault("rule_off", {})
        delay = 0.0
        if rule not in PROTECTED and rule != "-":
            prev = off.get(rule)
            if prev and now < prev[0]:
                delay = prev[1]                       # still backed off (the same burst): no doubling, no extension (four trips in one second gave 480 s)
            else:
                delay = min(prev[1] * 2, BACKOFF_MAX) if prev and now - prev[2] < 600 else BACKOFF
                off[rule] = [now + delay, delay, now]
        sample = text[:160]
        self.log(f"loop guard: {rule} repeated {typ} '{sample}' {count} times in {int(WINDOW)} s; " + (f"backed off {int(delay)} s" if delay else "only reported (protected rule)"))
        try:
            self.dlog("loop_guard", rule=rule, what=typ, sample=sample, count=count, backoff=int(delay))
        except Exception:
            pass
        reported = self.facts.setdefault("guard_reported", {})
        if now - reported.get(rule, 0) > REPORT_EVERY:
            reported[rule] = now
            line = {"t": time.strftime("%Y-%m-%dT%H:%M"), "sev": "medium", "kind": "loop_guard", "area": "brains", "bot": self.name, "rule": rule, "sample": sample,
                    "count": count, "backoff_s": int(delay), "status": "open", "owner": "BotFarm Watcher", "from": "brain"}
            try:
                with open(QUEUE_PATH, "ab") as f:
                    f.write((json.dumps(line, ensure_ascii=False) + "\n").encode("utf-8"))
            except OSError:
                pass

    # ---- the server's refusals, from the client's own log (patch_sysguard.py) ------------------------------------------------------------------------

    def guard_client(self):
        """Read the new lines of this bot's client log; count the server's refusals (a loop the brain cannot see) and learn the skill delay."""
        path = os.path.join(ROOT, "work", "navrey-sessions", self.name, "cuolog")
        try:
            size = os.path.getsize(path)
        except OSError:
            return
        pos = self.__dict__.get("_cuolog_pos")
        if pos is None or size < pos:
            self.__dict__["_cuolog_pos"] = size                  # start at the end: what happened before this brain is not its loop
            return
        if size == pos:
            return
        with open(path, "rb") as f:
            f.seek(pos)
            data = f.read(min(size - pos, 1_000_000))
            self.__dict__["_cuolog_pos"] = f.tell()
        now = time.time()
        for raw in data.decode("utf-8", "replace").splitlines():
            if "[NEAR] on damage:" in raw:
                try:
                    import deathsrc
                    deathsrc.near_feed(self, raw)                # who stood by when the bot was hit (patch_near_killer.py)
                except Exception:
                    pass
                continue
            i = raw.find("[SYSTEM] ")
            if i < 0:
                continue
            text = raw[i + 9:].strip()
            hook = getattr(self, "recovery_line", None)
            if hook:
                try:
                    hook(text)                            # death recovery and stamina lines (recovery.py)
                except Exception:
                    pass
            if SKILL_WAIT in text:
                gap = min(SKILL_GAP_MAX, self.facts.get("skill_gap", 0.0) + 2.0)
                self.facts["skill_gap"] = gap
                self.facts["skill_ready_at"] = now + gap
                self.__dict__["_skill_clean"] = 0
            if not REFUSAL.search(text):
                continue
            key = MASK.sub("#", text)[:120]
            q = self.__dict__.setdefault("_sys_hits", {}).setdefault(key, deque())
            q.append(now)
            while q and now - q[0] > SYS_WINDOW:
                q.popleft()
            if len(q) > SYS_LIMIT:
                n = len(q)
                q.clear()
                self.guard_trip("sys", text, n)

    def skill_gate(self, cmd):
        """Before a "useskill": wait out the learned gap (at most 12 s); after twenty clean uses the gap shrinks by a second."""
        wait = self.facts.get("skill_ready_at", 0) - time.time()
        if wait > 0:
            time.sleep(min(wait, 12.0))
        clean = self.__dict__.get("_skill_clean", 0) + 1
        self.__dict__["_skill_clean"] = clean
        if clean >= 20 and self.facts.get("skill_gap", 0) > 0:
            self.facts["skill_gap"] = max(0.0, self.facts["skill_gap"] - 1.0)
            self.__dict__["_skill_clean"] = 0
        self.facts["skill_ready_at"] = time.time() + self.facts.get("skill_gap", 0.0)

    def guard_spin(self, acted, elapsed):
        """A rule that acted in under 0.2 s ten ticks running is a spin: sleep a second."""
        if acted and elapsed < 0.2:
            self.__dict__["_spin"] = self.__dict__.get("_spin", 0) + 1
            if self.__dict__["_spin"] >= 10:
                self.__dict__["_spin"] = 0
                time.sleep(1.0)
                return True
        else:
            self.__dict__["_spin"] = 0
        return False
