"""The area danger map (feature "danger_map"; patch_danger_map.py): which 40x40 cells of the map a bot of this skill should not choose to be in, known BEFORE anyone dies there.

Two sources, no coordinates written here:
  SPAWNERS  hardspots.json (make_hardspots.py: every spawner of a strong or soft-danger kind, its position and roaming reach). A point inside a circle meets that spawner's kinds; the
            risk is the worst kind's death chance for a bot of THIS combat skill from danger.prior (creature_stats.json, the exchange estimate), with the pack size taken from how many
            circles overlap there (one other circle = one companion, two or more = two). The sea monsters' circles (SeaLife.json) are left out: they do not walk the land.
  DEATHS    every "death" event of both memory folders (veteran and newbie: what any player hears) of the last day, weighed by a 3 hour half-life and SPREAD over the killer's roaming reach
            (the radius of the spawner circle that holds the death and names the killer; 30 tiles when none does). A death counts fully for bots up to 15 skill points above the victim's
            (events without a skill: bots under 70), a third for stronger ones. A cell is dangerous when the weights reaching it add up to DEATH_THRESHOLD (0.75: one fresh death for 75 min,
            two for about 3 hours, a band that keeps killing stays marked).
A cell is risky when a spawner's risk is over the prey bar (danger.MODES["prey"], 12% death) or the death weights are over the threshold. The sample points of a cell are its centre and the four
quarter points, the worst counts. memory.SharedMemory.dangerous_cell asks the map (when the bot is in the feature's cohort), so every place that chooses where to be (hunting grounds, patrol spots,
camps, tamer search spots, crafters' earning ground, fishing shores, ore and caster grounds, first-trip waypoints, route penalties) avoids a risky cell without being touched one by one.
A choice that turns a cell down is logged once per cell per 30 minutes as ev "area_avoid" {cell, why}.
"""
from __future__ import annotations

import json
import os
import time

import danger

HERE = os.path.dirname(os.path.abspath(__file__))
CELL = 40
HALF_LIFE = 3 * 3600.0
DEATH_SPREAD = 30
DEATH_THRESHOLD = 0.75
HURT_WEIGHT = 0.4            # a "hurt" record (stall.py: hurt by something unseen) counts as this much of a death
DEATH_WINDOW = 24 * 3600.0
SKILL_MARGIN = 15
UNDER = 70
AVOID_EVERY = 1800.0
READ_EVERY = 20.0
SAMPLES = ((0, 0), (-14, -14), (14, -14), (-14, 14), (14, 14))
COMBAT = ("Swordsmanship", "Mace Fighting", "Fencing", "Archery", "Wrestling", "Magery")
SKIP_FILES = ("SeaLife.json",)
GRID = 64
GATHER_CEILING = 0.5                                       # a gatherer may use a cell up to this risk (about one weighted death); the least risky cell is taken

_CIRCLES = None
_INDEX = None


def combat_skill(values):
    """The best of the fighting skills in a {skill name: value} dict (a bot's weakest hours are what a spawner finds out)."""
    return max([float((values or {}).get(k, 0) or 0) for k in COMBAT] or [0.0])


def circles():
    """[{x, y, r, kinds, factor}] of the land spawners in hardspots.json, with a coarse grid index."""
    global _CIRCLES, _INDEX
    if _CIRCLES is None:
        try:
            doc = json.load(open(os.path.join(HERE, "hardspots.json"), encoding="utf-8"))
            _CIRCLES = [c for c in doc.get("circles", []) if c.get("file") not in SKIP_FILES]
        except (OSError, ValueError):
            _CIRCLES = []
        _INDEX = {}
        for i, c in enumerate(_CIRCLES):
            for gx in range((c["x"] - c["r"]) // GRID, (c["x"] + c["r"]) // GRID + 1):
                for gy in range((c["y"] - c["r"]) // GRID, (c["y"] + c["r"]) // GRID + 1):
                    _INDEX.setdefault((gx, gy), []).append(i)
    return _CIRCLES


def covering(x, y):
    """The spawner circles that hold the point."""
    cs = circles()
    return [cs[i] for i in _INDEX.get((int(x) // GRID, int(y) // GRID), ()) if (x - cs[i]["x"]) ** 2 + (y - cs[i]["y"]) ** 2 <= cs[i]["r"] ** 2]


def spawn_risk(x, y, skill):
    """(death chance of the worst spawner kind at the point for this skill, that kind's name or "")."""
    cover = covering(x, y)
    if not cover:
        return 0.0, ""
    near = min(2, len(cover) - 1)
    best = (0.0, "")
    for c in cover:
        for k in c.get("kinds", ()):
            die = danger.prior(k.lower(), skill, near)["die"]
            if die > best[0]:
                best = (die, k)
    return best


def roam(x, y, killers):
    """How far a killer of this death roams: the radius of the spawner circle that holds the point and names a killer, else DEATH_SPREAD."""
    ks = {k.lower() for k in killers or ()}
    r = [c["r"] for c in covering(x, y) if ks & {n.lower() for n in c.get("kinds", ())}]
    return max(r) if r else DEATH_SPREAD


def killer_weight(killers, skill):
    """How much a death says to a bot of this skill: the worst killer's death chance for it (danger.prior) against the prey bar, between 0.2 and 1; 1 when no
    killer was named."""
    if not killers:
        return 1.0
    bar = danger.MODES["prey"][0]
    worst = max(danger.prior(k, skill, 0)["die"] for k in killers)
    return max(0.2, min(1.0, worst / bar))


class AreaDanger:
    def __init__(self, mem, skill_fn=None, enabled=None, on_avoid=None):
        self.mem, self.skill_fn, self._enabled, self.on_avoid = mem, skill_fn, enabled, on_avoid
        self.deaths, self.offsets, self.read_at = [], {}, 0.0
        self.cache, self.avoided = {}, {}

    def enabled(self):
        try:
            return bool(self._enabled()) if self._enabled else True
        except Exception:
            return False

    def skill(self):
        try:
            return float(self.skill_fn())
        except Exception:
            return 40.0

    # ---- the deaths of both memory folders --------------------------------------------------------------------------------------------------------

    def files(self):
        out = []
        for m in (self.mem, getattr(self.mem, "news", None)):
            try:
                out.append(m.paths["world"])
            except Exception:
                pass
        return out

    def refresh(self, force=False):
        now = time.time()
        if not force and now - self.read_at < READ_EVERY:
            return
        self.read_at = now
        for path in self.files():
            try:
                size = os.path.getsize(path)
            except OSError:
                continue
            off = self.offsets.get(path, 0)
            if size < off:
                off = 0
                self.deaths = [d for d in self.deaths if d["file"] != path]
            if size == off:
                continue
            try:
                with open(path, "rb") as f:
                    f.seek(off)
                    data = f.read()
            except OSError:
                continue
            end = data.rfind(b"\n") + 1                           # only whole lines; a line being written is read next time
            self.offsets[path] = off + end
            for line in data[:end].splitlines():
                if b'"death"' not in line and b'"hurt"' not in line:
                    continue
                try:
                    ev = json.loads(line)
                except ValueError:
                    continue
                if ev.get("k") not in ("death", "hurt") or now - ev.get("t", 0) > DEATH_WINDOW:
                    continue
                at = ev.get("at")
                if at and len(at) == 2:
                    x, y = int(at[0]), int(at[1])
                else:
                    cx, cy = (int(v) for v in ev["cell"].split(","))
                    x, y = cx + CELL // 2, cy + CELL // 2
                killers = ev.get("killers") or []
                self.deaths.append({"t": ev["t"], "x": x, "y": y, "skill": ev.get("skill"), "spread": roam(x, y, killers), "file": path,
                                    "w": HURT_WEIGHT if ev.get("k") == "hurt" else 1.0,
                                    "killers": sorted({str(k).lower() for k in killers if k})})
        self.deaths = [d for d in self.deaths if now - d["t"] <= DEATH_WINDOW]
        self.cache.clear()

    def death_weight(self, x, y, skill):
        """The decayed, spread, skill-weighed deaths that reach the point."""
        now, w = time.time(), 0.0
        for d in self.deaths:
            if max(abs(x - d["x"]), abs(y - d["y"])) > d["spread"]:
                continue
            ds = d["skill"]
            f = (1.0 if skill <= ds + SKILL_MARGIN else 0.3) if ds is not None else (1.0 if skill < UNDER else 0.3)
            f *= killer_weight(d.get("killers"), skill)
            w += f * d.get("w", 1.0) * 0.5 ** ((now - d["t"]) / HALF_LIFE)
        return w

    # ---- the question --------------------------------------------------------------------------------------------------------------------------

    def why(self, cell, skill=None):
        """"" when the cell is fine for this skill, else the reason (spawner kind and death chance, or the death weight)."""
        self.refresh()
        skill = self.skill() if skill is None else skill
        key = (cell, int(skill // 5))
        hit = self.cache.get(key)
        if hit is not None:
            return hit
        cx, cy = (int(v) for v in cell.split(","))
        why = ""
        bar = danger.MODES["prey"][0]
        for dx, dy in SAMPLES:
            x, y = cx + CELL // 2 + dx, cy + CELL // 2 + dy
            die, kind = spawn_risk(x, y, skill)
            if die > bar:
                why = f"spawner of {kind}: {die:.0%} death chance at skill {skill:.0f}"
                break
            dw = self.death_weight(x, y, skill)
            if dw >= DEATH_THRESHOLD:
                why = f"{dw:.1f} recent deaths reach it"
                break
        self.cache[key] = why
        return why

    ceiling = GATHER_CEILING

    def risk(self, cell, skill=None):
        """0..1 how deadly the cell is for this skill, whatever the prey bar: the worst sample point's spawner death chance, or the deaths' pull 1 - 0.5 ** weight."""
        self.refresh()
        skill = self.skill() if skill is None else skill
        cache = self.__dict__.setdefault("rcache", {})
        key = (cell, int(skill // 5), self.read_at)
        hit = cache.get(key)
        if hit is not None:
            return hit
        if len(cache) > 4000:
            cache.clear()
        cx, cy = (int(v) for v in cell.split(","))
        worst = 0.0
        for dx, dy in SAMPLES:
            x, y = cx + CELL // 2 + dx, cy + CELL // 2 + dy
            worst = max(worst, spawn_risk(x, y, skill)[0], 1.0 - 0.5 ** self.death_weight(x, y, skill))
        cache[key] = worst
        return worst

    def rank(self, cell):
        """risk() for a bot that has the feature, else 0.0 (the map is off)."""
        return self.risk(cell) if self.enabled() else 0.0

    def risky(self, cell):
        """True when the cell is one to stay out of (and the feature is on for this bot); the first refusal of a cell in 30 minutes is reported."""
        if not self.enabled():
            return False
        why = self.why(cell)
        if why and self.on_avoid:
            now = time.time()
            if now - self.avoided.get(cell, 0) > AVOID_EVERY:
                self.avoided[cell] = now
                try:
                    self.on_avoid(cell, why)
                except Exception:
                    pass
        return bool(why)
