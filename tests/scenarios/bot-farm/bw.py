"""Between Worlds as a plan, not a status (the owner, 2026-10-17: "Resurrected bots should be between worlds and should be able to safely retrieve
their gear and flee, or continue hunting"; feature "bw_plan", with "materializing").

Before: BotSwordBR and BotMaceCR were resurrected, rearmed from the pack, explored for the whole 600 s window without touching their corpses (500
tiles away, and far_worth_corpse wants 300+ gold for over 120 tiles), and 10-20 minutes later walked back into the spawn that had killed them.

AT RESURRECTION (the server's Between Worlds line) the bot decides what the window is for:
  corpse  the corpse is reachable inside the window (its distance at BW_SPEED tiles a minute, plus a minute to spare) and before it rots: the corpse
          run goes at once, whatever the gold, the distance rule or the shared danger map says (monsters cannot see a bot Between Worlds); one
          double-click takes everything back (blue_self_loot), then the bot walks LEAVE tiles toward home before the server's 60 s after the opening.
  near    the corpse is too far, or there is none worth it: the window is not held for anything; the bot plays on near the healer (an attack ends
          the window, which the server allows).
  none    no corpse known.
Either way the death area (the 3x3 cells round the death) counts as crowded for this bot for AVOID_H hours, so its ground choice passes it over:
its own danger, besides the shared map.

Events: bw_plan {choice, corpse_dist, eta_min, window_left}; bw_result {choice, got_items, secs, died}.
"""
from __future__ import annotations

import time

BW_SPEED = 75.0          # tiles a minute on a routed walk: the 526-538 tile healer walks took 6.7 min once the flip-flop was fixed (the watcher)
SPARE = 60.0
WINDOW = 600.0
AVOID_H = 3.0
LEAVE = 30
RELEASE_AFTER = 20.0     # seconds for r_gear to put the pack's gear on before a "near" bot plays on


def _cell(x, y):
    try:
        from memory import cell_of
        return cell_of(x, y)
    except Exception:
        return f"{int(x) // 40 * 40},{int(y) // 40 * 40}"


class BetweenWorldsMixin:
    def bw_on(self):
        f = getattr(self, "features", ())
        return "bw_plan" in f and "materializing" in f

    def bw_start(self, now):
        if not self.bw_on():
            return
        info = self.facts.get("corpse")
        here = (self.c.x, self.c.y)
        choice, d, eta = "none", None, None
        if info and info.get("xy"):
            x, y = info["xy"]
            d = max(abs(here[0] - x), abs(here[1] - y))
            speed = min(120.0, max(30.0, float(self.facts.get("walk_rate") or BW_SPEED)))      # its own measured speed (far.py), else the default
            eta = d / speed * 60.0
            try:
                deadline = self.corpse_deadline(info)
            except Exception:
                deadline = info.get("t", now) + 420
            choice = "corpse" if eta + SPARE <= WINDOW and now + eta < deadline else "near"
            until = now + AVOID_H * 3600
            crowded = self.facts.setdefault("crowded", {})
            for dx in (-40, 0, 40):
                for dy in (-40, 0, 40):
                    crowded[_cell(x + dx, y + dy)] = max(crowded.get(_cell(x + dx, y + dy), 0), until)
        self.facts["bw"] = {"choice": choice, "t": now, "dist": d, "eta": round(eta) if eta is not None else None}
        self.ev("bw_plan", choice=choice, corpse_dist=d, eta_min=round(eta / 60, 1) if eta is not None else None, window_left=round(WINDOW))
        self.log(f"Between Worlds: {choice}" + (f" (corpse {d} tiles, about {eta / 60:.1f} min)" if d is not None else "") +
                 f"; the death area is avoided for {AVOID_H:.0f} h")

    def bw_released(self):
        """recovery_skip: the rules that would end the window run again (a "near" plan after the gear is on, or a corpse run that is done)."""
        b = self.facts.get("bw")
        if not b or not self.bw_on():
            return False
        if b["choice"] == "corpse":
            return bool(b.get("looted"))
        return time.time() - b["t"] > RELEASE_AFTER

    def bw_corpse_go(self):
        """r_corpse: go now, past the gold, distance and danger tests."""
        b = self.facts.get("bw")
        return bool(b) and b["choice"] == "corpse" and not b.get("looted") and self.bw_on() and self.materializing()

    def bw_looted(self, how):
        b = self.facts.get("bw")
        if not b or b.get("looted"):
            return
        b["looted"] = time.time()
        b["how"] = how or "item by item"
        try:
            hx, hy = self.home_centre()
            x, y = self.c.x, self.c.y
            dx, dy = hx - x, hy - y
            n = max(1, max(abs(dx), abs(dy)))
            k = min(1.0, LEAVE / n)
            self.activity = "Between Worlds: leaving the corpse area"
            self.c.goto(int(x + dx * k), int(y + dy * k)).wait(timeout=30)       # out before the 60 s after the opening run out
        except Exception as e:
            self.log(f"Between Worlds: leaving the corpse area failed ({type(e).__name__})")

    def bw_end(self, now, died=False):
        b = self.facts.pop("bw", None)
        if not b:
            return
        self.ev("bw_result", choice=b["choice"], got_items=b.get("how"), secs=round(now - b["t"]), died=died)
        self.log(f"Between Worlds over: {b['choice']}, " + (f"took back {b['how']}" if b.get("how") else "no corpse taken") + (", died" if died else ""))

    def bw_tick(self, now):
        info = self.facts.get("corpse")
        if info and not info.get("serial") and getattr(self.c, "ghost", False):
            try:                                            # the ghost stands on its corpse: keep the serial (bones are the same Corpse, unlisted)
                x, y = info["xy"]
                me = (getattr(self, "name", "") or "").lower()
                for i in self.c.containers(within=3):
                    n_ = (i.name or "").lower()
                    if "corpse" in n_ and (me in n_ or not n_.startswith(("a ", "an "))) and max(abs(i.x - x), abs(i.y - y)) <= 3:
                        info["serial"] = i.serial
                        break
            except Exception:
                pass
        b = self.facts.get("bw")
        if not b:
            return
        if self.c.ghost:
            self.bw_end(now, died=True)
        elif b["choice"] == "corpse" and not b.get("looted") and not self.facts.get("corpse") and now - b["t"] > 5:
            b["looted"], b["how"] = now, b.get("how") or "item by item or none"      # the corpse run ended without the one-click line
        elif now - b["t"] > WINDOW + 60 and not self.facts.get("mat_until"):
            self.bw_end(now)
