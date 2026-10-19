"""Measured hunting grounds (R4 hunters' lever, 2026-10-17; feature "ground_rates"): where hunting has actually paid bots of this strength.

The ground choice (HunterBot.best_ground, CasterBot.caster_ground) scored a cell by the kinds sighted there and its recent kills. A player also
knows which grounds paid him: this module measures it. Every WINDOW seconds a hunting bot (on a hunting rule most of the window, not a ghost)
credits what it gained to the 40x40 cell it spent the most ticks in: working-skill gains (passive skills left out), kills and gold (carried +
banked). The farm shares it in memory/ground_rates.json, keyed by profession group (fighter, archer, caster, tamer), skill band (10 points) and
cell, as an exponential average of value per hour (gains x 1.0 + kills x 0.3 + gold x 0.02) with a count.

The ground choice adds BONUS x the measured value to a cell's score once MIN_N windows are known in the bot's band (or the band below): a ground
that keeps paying is chosen more, and one measured at nothing (MIN_N windows, value under DEAD) loses DEAD_PENALTY, so it is passed over like a
camped one. Events: ev ground_rate {ground, band, value, n, avg} per window.
"""
from __future__ import annotations

import json
import os
import time
from collections import Counter

import farmdb

WINDOW = 300.0
ALPHA = 0.3
MIN_N = 2
BONUS = 0.5
DEAD = 0.3
DEAD_PENALTY = 3.0
HUNT_RULES = ("r_hunt", "r_fight", "r_loot", "r_camp", "r_explore", "r_carve", "r_heal", "r_rest", "r_buddy", "r_buddy_heal", "r_music", "r_tame", "r_pet")
PASSIVE = ("Meditation", "Resisting Spells", "Focus", "Hiding", "Detecting Hidden", "Anatomy", "Evaluating Intelligence", "Spirit Speak", "Healing")
HERE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(HERE, "..", "..", "..", "..", "work", "botfarm", "memory", "ground_rates.json")
_cache = {"t": 0.0, "d": {}}
TABLE = "ground"


def _cell(x, y):
    return f"{int(x) // 40 * 40},{int(y) // 40 * 40}"


def load(force=False):
    """The shared table, from the farm's database (farmdb: atomic, no lost updates); the JSON file is the fallback and a read-only export."""
    now = time.time()
    if force or now - _cache["t"] > 30:
        try:
            _cache["d"] = farmdb.rate_table(TABLE, import_json=PATH)
        except Exception:
            try:
                _cache["d"] = json.load(open(PATH, encoding="utf-8"))
            except (OSError, ValueError):
                _cache["d"] = {}
        _cache["t"] = now
    return _cache["d"]


class GroundRateMixin:
    def gr_on(self):
        return "ground_rates" in getattr(self, "features", ())

    def gr_group(self):
        p = (getattr(self, "pname", "") or "").replace(" ", "")
        if p in ("PureMage", "Warlock", "Sorcerer"):
            return "caster"
        if p in ("Archer", "Ranger") or getattr(self, "ranged", False):
            return "archer"
        if p == "AnimalTamer":
            return "tamer"
        return "fighter"

    def gr_band(self):
        try:
            s = float(self.working_skill())
        except Exception:
            s = 0.0
        return int(s // 10 * 10)

    def gr_measure(self):
        gains = sum(v for k, v in getattr(self, "stats", {}).get("gains", {}).items() if k not in PASSIVE)
        return gains, getattr(self, "kills", 0), (self.c.gold or 0) + (self.facts.get("bank_balance", 0) or 0)

    def gr_tick(self, acted):
        if not self.gr_on() or getattr(self.c, "ghost", False):
            self.__dict__.pop("_gr", None)
            return
        now = time.time()
        st = self.__dict__.get("_gr")
        if st is None or now - st.get("last", now) > 120:
            g, k, w = self.gr_measure()
            self.__dict__["_gr"] = {"t0": now, "last": now, "g": g, "k": k, "w": w, "cells": Counter(), "hunt": 0, "all": 0}
            return
        st["last"] = now
        st["all"] += 1
        if acted in HUNT_RULES:
            st["hunt"] += 1
            st["cells"][_cell(self.c.x, self.c.y)] += 1
        if now - st["t0"] < WINDOW:
            return
        g, k, w = self.gr_measure()
        hours = (now - st["t0"]) / 3600.0
        if st["cells"] and st["hunt"] >= 0.6 * max(1, st["all"]):
            cell = st["cells"].most_common(1)[0][0]
            value = (max(0, g - st["g"]) * 1.0 + max(0, k - st["k"]) * 0.3 + max(0, w - st["w"]) * 0.02) / hours
            self.gr_record(cell, value)
        self.__dict__["_gr"] = {"t0": now, "last": now, "g": g, "k": k, "w": w, "cells": Counter(), "hunt": 0, "all": 0}

    def gr_key(self, band, cell):
        return f"{self.gr_group()}|{band}|{cell}"

    def gr_record(self, cell, value):
        d = load(force=True)
        band = self.gr_band()
        key = self.gr_key(band, cell)
        try:
            d[key] = farmdb.rate_update(TABLE, key, value, ALPHA)            # atomic: two bots writing at once both count (the JSON file lost one)
            farmdb.export_json(TABLE, PATH)
        except Exception as e:
            old = d.get(key)
            d[key] = [round(value if not old else old[0] + ALPHA * (value - old[0]), 2), (old[1] if old else 0) + 1, int(time.time())]
            self.log(f"ground rates: database write failed ({type(e).__name__}: {e}); kept in memory only")
        _cache["d"] = d
        self.ev("ground_rate", ground=cell, band=band, value=round(value, 2), n=d[key][1], avg=d[key][0])      # ev() adds its own cell (where the bot stands)

    def gr_bonus(self, cell):
        """Added to a ground's score: BONUS x the measured value, or -DEAD_PENALTY for a ground measured at nothing; 0 when unknown."""
        if not self.gr_on():
            return 0.0
        d = load()
        band = self.gr_band()
        for b in (band, band - 10):
            r = d.get(self.gr_key(b, cell))
            if r and r[1] >= MIN_N:
                return -DEAD_PENALTY if r[0] < DEAD else BONUS * r[0]
        return 0.0
