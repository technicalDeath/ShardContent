"""Pacing (G6; Watcher 2026-10-17, Helper 2; features "pacing" and "pacing_walk"): Britain looks inhabited when the people in it move like people. Mixin for BotBase and CasterBot, written into the bot-farm folder
by patch_pacing.py.

  pacing_walk  (feature "pacing_walk") a bot walks, never runs, inside a town region: the client's run mode is "never" while the bot stands in a town (gazetteer in_town: the city rectangles, not the farmland of the
               region) and goes back to "auto" outside. A flight is exempt: sprint() (r_flee, the danger rules) still runs the bot for its 8 seconds, and a ghost keeps the default. This slows town errands (bank,
               shops) by about a third: stage it on a cohort and read the per-hour economy before widening.
  pause        (feature "pacing") 2-6 seconds standing in front of a vendor or the banker before talking to them ("<name> buy" in vendor_list, "bank" in visit_bank), at most once per kind per 30 seconds,
               never with a threat near. ev pause {kind: vendor | bank, secs}.
  break        (feature "pacing") every 45-90 minutes of play, once the bot has just banked (facts banked_at within 90 s) and is calm (no threat, hp >= 80): stand where it is, at the bank, for 60-180 seconds
               (a tick sleeps 5 s at a time; a threat or a hurt ends it). ev pause {kind: "break", secs} when it ends. If no bank visit comes within 15 minutes of being due, the break is rescheduled.
Reaction delays are varied by the pause (2-6 s random) and by talk.py's reply delay (1.2-3.5 s); nothing else is delayed.
Logouts are the supervisor's: see PACING-LOGOUT-NOTE.md.
"""
import random
import time

try:
    import gazetteer as gz
except Exception:                                  # pragma: no cover - a tree without the gazetteer
    gz = None

PAUSE_MIN, PAUSE_MAX = 2.0, 6.0
PAUSE_GAP = 30.0
BREAK_EVERY = (45 * 60, 90 * 60)
BREAK_LEN = (60, 180)
BREAK_AFTER_BANK = 90
BREAK_WAIT = 900
SLICE = 5.0
SPRINT_S = 8.0


def _cell(bot):
    try:
        from memory import cell_of
        return cell_of(bot.c.x, bot.c.y)
    except Exception:
        return None


class PacingMixin:
    def pacing_on(self):
        return self.feature("pacing")

    def pacing_walk_on(self):
        return self.feature("pacing_walk")

    def pacing_emit(self, name, **kw):
        """BotBase.ev(kind, **kw) takes a `kind` of its own and these events carry one: write the same decisions line directly."""
        try:
            self.dlog("ev", ev=name, cell=_cell(self), rule=getattr(self, "current_rule", None) or getattr(self, "last_rule", None), **kw)
        except Exception:
            pass

    def pacing_threat(self, within=10):
        try:
            return bool(self.threats(within))
        except AttributeError:
            return bool(self.mobs(within))
        except Exception:
            return False

    # ---- after every tick ------------------------------------------------------------------------------------------------------------------------

    def pacing_tick(self):
        if self.pacing_walk_on() and not self.c.ghost:
            self.pacing_walk_mode()

    def pacing_walk_mode(self):
        """Run mode "never" in a town, back to "auto" outside; a flight (sprint) is left alone."""
        b = self.__dict__.setdefault("_pacing", {})
        try:
            town = bool(gz.in_town(self.c.x, self.c.y)) if gz else False
        except Exception:
            town = False
        now = time.time()
        sprinting = now - self.facts.get("sprint_at", 0) <= SPRINT_S or self.facts.get("runmode") == "always"
        if town and not sprinting:
            if self.facts.get("runmode") != "never":
                self.set_runmode("never")
                b["walking"] = True
        elif not town and b.get("walking"):
            if self.facts.get("runmode") == "never":
                self.set_runmode("auto")
            b["walking"] = False

    # ---- the pause before talking ----------------------------------------------------------------------------------------------------------------

    def pacing_pause(self, kind):
        """Stand 2-6 seconds before speaking to a vendor or the banker (once per kind per 30 s, not with a threat near, not as a ghost)."""
        if not self.pacing_on() or self.c.ghost:
            return 0.0
        now = time.time()
        last = self.facts.setdefault("pause_at", {})
        if now - last.get(kind, 0) < PAUSE_GAP or self.pacing_threat(8):
            return 0.0
        last[kind] = now
        secs = round(random.uniform(PAUSE_MIN, PAUSE_MAX), 1)
        time.sleep(secs)
        self.pacing_emit("pause", kind=kind, secs=secs)
        return secs

    # ---- the break at the bank ---------------------------------------------------------------------------------------------------------------------

    def r_break(self):
        """Every 45-90 minutes, right after a bank visit: stand there for 1-3 minutes."""
        if not self.pacing_on() or self.c.ghost:
            return False
        b = self.__dict__.setdefault("_pacing", {})
        now = time.time()
        if b.get("break_until"):
            if now >= b["break_until"] or self.pacing_threat(10) or self.hp_pct() < 80:
                secs = round(now - b["break_at"])
                b.pop("break_until", None)
                b["next_break"] = now + random.uniform(*BREAK_EVERY)
                self.pacing_emit("pause", kind="break", secs=secs)
                return False
            self.activity = "taking a break at the bank"
            time.sleep(min(SLICE, max(0.5, b["break_until"] - now)))
            return True
        due = b.setdefault("next_break", now + random.uniform(*BREAK_EVERY))
        if now < due:
            return False
        if now - self.facts.get("banked_at", 0) > BREAK_AFTER_BANK:
            if now - due > BREAK_WAIT:
                b["next_break"] = now + random.uniform(*BREAK_EVERY)         # no bank visit came: try again later
            return False
        if self.pacing_threat(10) or self.hp_pct() < 80:
            return False
        b["break_at"] = now
        b["break_until"] = now + random.uniform(*BREAK_LEN)
        self.activity = "taking a break at the bank"
        return True

    def far_rules(self):
        rules = super().far_rules()
        if "r_break" not in rules and "r_bank" in rules:
            rules.insert(rules.index("r_bank") + 1, "r_break")
        return rules
