"""Fields for fighters: one hunting area, then the next (plan step 3, 2026-10-19; feature "fields"; the owner: "in general I think bots need to explore wider areas
more", "If a bot finds an area empty it should immediately move on", and "Yes: build plan step 3 (whole areas for fighters ...)").

Fighters spent 71% of their time in r_explore (13:00-15:00): a memory cell picked from past sightings, stood on and watched for the next spawn, or a random
patrol point. A player who knows the land goes to an area where the monsters he wants live, works it, and moves on when it is empty or stops paying. The casters
do this since P20 (profit.py); this is the same for HunterBot.

A FIELD is a Britain hunting area (britain_areas.json: its spawners and what each spawns), in the bot's patrol tiers (Places.patrol_tiers: its strength). Each
spawner is worth the mean of worth_kind over its kinds (hunter.py: what the profession has measured a kind to pay this bot a minute; 0 for pets, outgrown
vermin, kinds that killed bots like it, and dangerous kinds not yet measured). A spawner holding a kind that killed bots like this one (deadly_kinds), or in a
cell the danger map or the memory calls dangerous, puts the whole area out. The area's score is its spawners' mean, over (1 + other bots there)^2 (none at
all from CROWD), over the walk (halved at WALK tiles); the next area is drawn from the best CHOICES in proportion to their scores.
The bot walks to the area's nearest spawner, then works the whole area: a point within AROUND tiles of one of its spawners, another every 40 s; r_hunt and
r_fight (above r_explore in the rules) take what turns up. It moves on when the area is empty (no prey in sight EMPTY s after arriving), when it stops paying
(no kill in STALE s), after MAX s, or when it is not reached in TRAVEL s; a left area rests REST s. Events field_chosen / field_left, and log lines.
"""
from __future__ import annotations

import json
import os
import random
import time

HERE = os.path.dirname(os.path.abspath(__file__))
EMPTY = 75
STALE = 360
MAX = 1200
TRAVEL = 900
REST = 1800
NEAR = 15
WALK = 300.0
CROWD = 3
CHOICES = 3
AROUND = 20
RECHECK = 60.0
_AREAS = {"d": None}


def areas():
    if _AREAS["d"] is None:
        try:
            _AREAS["d"] = json.load(open(os.path.join(HERE, "britain_areas.json"), encoding="utf-8")).get("areas", [])
        except (OSError, ValueError):
            _AREAS["d"] = []
    return _AREAS["d"]


class FieldsMixin:
    def fields_on(self):
        return self.feature("fields")

    FIGHTER_TIER2 = 70.0                                  # weapon skill from which tier-2 fields are worked (patch_step3_fixes)

    def field_tiers(self):
        """Tier 1, and tier 2 from FIGHTER_TIER2 weapon skill: tier 2 comes in packs, and fighters at 55-62 died there 3.4 times as often (patch_step3_fixes)."""
        try:
            skill = float(self.skill_values.get(self.main_skill(), 0) or 0)
        except Exception:
            skill = 0.0
        return (1, 2) if skill >= self.FIGHTER_TIER2 else (1,)

    def field_spawner(self, sp, deadly):
        """(value, vetoed) for one spawner [x, y, range, kinds]."""
        from memory import cell_of
        x, y, rng, kinds = sp[0], sp[1], sp[2], sp[3]
        if any(k in deadly for k in kinds):
            return 0.0, True
        cell = cell_of(x, y)
        area = getattr(self.mem, "area", None)
        if area is not None and area.risky(cell) or self.mem.dangerous_cell(cell):
            return 0.0, True
        vals = [self.worth_kind(k, deadly) for k in kinds]
        return (sum(vals) / len(vals) if vals else 0.0), False

    def field_areas(self, here):
        """{name: {"score", "tier", "spots": [(x, y, value)], "load", "dist"}} for the areas worth working."""
        from memory import cell_of
        tiers = self.field_tiers()
        try:
            self.mem.refresh()
            deadly = self.mem.deadly_kinds()
        except Exception:
            deadly = set()
        # each spawner's value weighted by the share of its creatures back since any bot's last kill there (spots.availability: the memory's last kill and
        # the spawner's respawn window). Without it the tamer chose fields the fighters had just cleared, left each "empty" after EMPTY seconds and walked
        # 300-500 tiles to the next: BotTamerAR, 0 kills in an hour with a brown bear of strength 414 (2026-11-01 21:12-22:12)
        try:
            import spots as _sp
            idx = {(int(s["x"]), int(s["y"])): s for s in _sp.spawner_spots()}
        except Exception:
            _sp, idx = None, {}
        out = {}
        for a in areas():
            if a.get("tier") not in tiers:
                continue
            spots, veto, load, dist = [], False, 0, 99999
            for sp in a.get("spawners", []):
                v, bad = self.field_spawner(sp, deadly)
                if bad:
                    veto = True
                    break
                s = idx.get((int(sp[0]), int(sp[1])))
                if s is not None and _sp is not None:
                    try:
                        v *= _sp.availability(self, dict(s, cell=cell_of(sp[0], sp[1])))
                    except Exception:
                        pass
                spots.append((sp[0], sp[1], round(v, 2)))
                load = max(load, self.ground_load(cell_of(sp[0], sp[1])))
                dist = min(dist, max(abs(here[0] - sp[0]), abs(here[1] - sp[1])))
            if veto or not spots or load >= CROWD:
                continue
            mean = sum(s[2] for s in spots) / len(spots)
            if mean <= 0:
                continue
            out[a["name"]] = {"tier": a["tier"], "spots": [s for s in spots if s[2] > 0] or spots, "load": load, "dist": dist,
                              "score": mean / (1.0 + load) ** 2 / (1.0 + dist / WALK)}
        return out

    def field_prey(self):
        try:
            return bool(self.prey(16))
        except Exception:
            return False

    def field_pick(self):
        """(x, y) to walk to, or None (the old r_explore)."""
        now = time.time()
        here = (self.c.x, self.c.y)
        f = self.facts.get("field")
        if f:
            if not f.get("arrived") and any(max(abs(here[0] - s[0]), abs(here[1] - s[1])) <= NEAR for s in f["spots"]):
                f["arrived"] = now
            why = None
            if f.get("arrived"):
                empty = now - max(f["arrived"], f.get("prey_at", 0), self.facts.get("last_kill_at", 0))      # a fight in between is not an empty field
                idle = now - max(f["arrived"], self.facts.get("last_kill_at", 0))
                if empty >= EMPTY:
                    why = f"empty: no prey seen in {int(empty)} s"
                elif idle >= STALE:
                    why = f"no kill in {int(idle)} s"
                elif now - f["arrived"] >= MAX:
                    why = f"worked for {int(now - f['arrived'])} s: time to see another field"
            elif now - f["t"] >= TRAVEL:
                why = f"not reached in {int(now - f['t'])} s"
            if why is None and now - f.get("checked", 0) >= RECHECK:
                f["checked"] = now
                if f["name"] not in self.field_areas(here):
                    why = "unsafe or crowded now"
            if why is None:
                import places
                return places.scatter(getattr(self, "name", ""), *f["spots"][f.get("i", 0)][:2], r=6)
            rest = REST
            if why.startswith("empty"):
                # an empty field is back once its spawners respawn (their longest delay, spots.spawner_spots "mx" from the spawner's maxDelay), not after a
                # flat 30 minutes: with three fields open to its brown bear, BotTamerAR rested each after 77 s and ran out ("others: none"), 0 kills an hour
                # (2026-11-01 22:24-22:50)
                try:
                    import spots as _sp
                    idx = {(int(s["x"]), int(s["y"])): s for s in _sp.spawner_spots()}
                    mx = max(float(idx[(int(s[0]), int(s[1]))]["mx"]) for s in f["spots"] if (int(s[0]), int(s[1])) in idx)
                    rest = min(REST, max(120.0, mx))
                except Exception:
                    rest = REST
            self.facts.setdefault("fields_rested", {})[f["name"]] = now - (REST - rest)     # (rested while now - t < REST: for `rest` seconds)
            self.facts["field"] = None
            self.log(f"fields: leaving {f['name']}: {why}")
            self.ev("field_left", field=f["name"], why=why, mins=round((now - f["t"]) / 60, 1))
        rested = {k: t for k, t in (self.facts.get("fields_rested") or {}).items() if now - t < REST}
        self.facts["fields_rested"] = rested
        cand = {n: a for n, a in self.field_areas(here).items() if n not in rested}
        if not cand:
            return None
        ranked = sorted(cand.items(), key=lambda kv: -kv[1]["score"])[:CHOICES]
        pick, acc = random.random() * sum(a["score"] for n, a in ranked), 0.0
        name, a = ranked[-1]
        for n, aa in ranked:
            acc += aa["score"]
            if pick <= acc:
                name, a = n, aa
                break
        spots = [list(s) for s in a["spots"]]
        i = min(range(len(spots)), key=lambda j: max(abs(here[0] - spots[j][0]), abs(here[1] - spots[j][1])))
        self.facts["field"] = {"name": name, "spots": spots, "i": i, "t": now, "arrived": None}
        self.facts["ground"] = None                        # the field replaces the watched ground
        self.log(f"fields: working {name} next (score {a['score']:.2f}, {len(spots)} spawners, {a['dist']} tiles, {a['load']} bots there; "
                 f"others: {', '.join(n for n, x in ranked if n != name) or 'none'})")
        self.ev("field_chosen", field=name, score=round(a["score"], 2), tier=a["tier"], dist=a["dist"], load=a["load"], spawners=len(spots),
                others=[n for n, x in ranked if n != name])
        import places
        return places.scatter(getattr(self, "name", ""), *spots[i][:2], r=6)               # the first walk: near the spawner, not on the same tile as every bot (patch_scatter)

    def field_explore(self):
        """HunterBot.r_explore with the feature: walk to the field, then work all of it. False: the old r_explore."""
        if not self.fields_on():
            return False
        xy = self.field_pick()
        if not xy:
            return False
        f = self.facts["field"]
        x, y = xy
        if f.get("arrived"):
            if self.field_prey():
                f["prey_at"] = time.time()
            p = f.get("p")
            if not p or time.time() - f.get("p_t", 0) > 40 or max(abs(self.c.x - p[0]), abs(self.c.y - p[1])) < 2:
                f["i"] = random.randrange(len(f["spots"]))
                sx, sy = f["spots"][f["i"]][:2]
                p = f["p"] = [sx + random.randint(-AROUND, AROUND), sy + random.randint(-AROUND, AROUND)]
                f["p_t"] = time.time()
            x, y = p
            self.activity = f"working the field {f['name']}"
        else:
            self.activity = f"walking to the field {f['name']}"
        res = self.c.goto(x, y).wait(timeout=4)
        if not f.get("arrived") and res and str(res).startswith("nopath") and max(abs(self.c.x - x), abs(self.c.y - y)) > 40:
            f["t"] -= TRAVEL
        return True
