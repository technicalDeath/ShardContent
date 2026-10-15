"""Shared memory for the farm's bots: what any bot learns about the world becomes data every bot can use in its decisions, and it outlives a run.

Two scopes, each an append-only JSON-lines file in work/botfarm/memory/:
  world.jsonl         facts about the world that hold for everyone: where monsters are seen and killed, where bots died, what each shop sells and buys,
                      which mining, chopping and fishing spots work, which targets cannot be reached;
  prof-<name>.jsonl   what only that profession's bots can use: how a fight against each monster went for a bot of that profession (time to kill, damage taken,
                      deaths), how often each craft succeeds, how a skill gained from each action.

A bot appends events and reads the files incrementally (only what is new since its last read), so there is no lock and no coordinator; bots of the same
profession share the second file, every bot shares the first. The folded state is plain dicts; the query helpers at the bottom are what the brains call.

Event kinds (every event also has t, bot, prof):
  sight   {m, cell}                      a hostile of kind m was seen in a map cell (40x40 tiles)
  fight   {m, grp, outcome, ttk, dmg, hp, cell}   outcome kill | death | flee | lost; ttk seconds, dmg = hit points lost, hp = the bot's maximum
  death   {cell, killers}                a bot died here
  loot    {cell, gold}                   gold taken from a corpse
  vendor  {xy, name, stock, buys}        stock = [[item, price, qty]], buys = [[item, price]]
  craft   {craft, item, ok, gain}        one craft attempt
  res     {kind, key, ok, reason}        a gathering target (ore, tree, water) worked or did not
  claim   {kind, key, ttl}               a bot is working this target for ttl seconds: others look elsewhere
  blocked {kind, key, ttl}               a target that cannot be reached or used for ttl seconds
  gain    {skill, action, value}         a skill rose after this action
"""
from __future__ import annotations

import json
import os
import time
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
MEMDIR = os.path.join(ROOT, "work", "botfarm", "memory")
CELL = 40
HALF_LIFE = 1800.0          # seconds: a cell's kills and gold count half as much after half an hour (spawns are used up and come back)
DEATH_HALF_LIFE = 14400.0   # a place that killed bots stays suspect for hours: camps do not move (the graveyard camp, quiet for an hour, looked safe again and killed four more)
FIGHT_HALF_LIFE = 7200.0    # bots get stronger, so old fight records weigh less than new ones
FIGHT_KEYS = ("n", "kill", "death", "flee", "lost", "ttk", "dmg", "dmgpct")

# professions whose fights look alike; a melee bot's record against a troll tells an archer little
GROUPS = {"Archer": "ranged", "Ranger": "ranged", "Bard": "ranged", "MaceFighter": "melee", "Fencer": "melee", "Swordsman": "melee",
          "PureMage": "caster", "Warlock": "caster", "Sorcerer": "caster"}


def cell_of(x, y):
    return f"{int(x) // CELL * CELL},{int(y) // CELL * CELL}"


def cell_center(cell):
    x, y = (int(v) for v in cell.split(","))
    return x + CELL // 2, y + CELL // 2


def group_of(prof):
    return GROUPS.get(prof, "other")


def _decay(d: dict, keys, t: float, half: float):
    """Bring the numbers in d (stamped d["t"]) forward to time t, halving them every `half` seconds."""
    dt = t - d.get("t", t)
    if dt > 0:
        f = 0.5 ** (dt / half)
        for k in keys:
            d[k] = d[k] * f
    d["t"] = max(t, d.get("t", 0))


def _empty():
    return {
        "fights": defaultdict(lambda: defaultdict(lambda: {"n": 0.0, "kill": 0.0, "death": 0.0, "flee": 0.0, "lost": 0.0, "ttk": 0.0, "dmg": 0.0, "dmgpct": 0.0, "t": 0.0})),
        "cells": defaultdict(lambda: {"kills": 0.0, "deaths": 0.0, "gold": 0.0, "sights": defaultdict(int), "fights": 0.0, "t": 0.0, "pres": []}),
        "vendors": {},
        "crafts": defaultdict(lambda: defaultdict(lambda: {"n": 0, "ok": 0, "gain": 0, "exc": 0})),
        "res": defaultdict(lambda: defaultdict(lambda: {"ok": 0, "fail": 0, "reason": "", "blocked_until": 0.0, "claim_until": 0.0, "claim_by": ""})),
        "gains": defaultdict(lambda: defaultdict(int)),
        "dps": {"hits": 0.0, "ttk": 0.0, "n": 0},
        "events": 0,
    }


class SharedMemory:
    def __init__(self, prof: str, bot: str, root: str = MEMDIR):
        self.prof = prof
        self.bot = bot
        self.grp = group_of(prof)
        os.makedirs(root, exist_ok=True)
        self.paths = {"world": os.path.join(root, "world.jsonl"), "prof": os.path.join(root, f"prof-{prof}.jsonl")}
        self.state = {"world": _empty(), "prof": _empty()}
        self.offset = {"world": 0, "prof": 0}
        self.last_read = 0.0
        self.sight_seen = {}
        self.refresh(force=True)

    # ---- writing ----------------------------------------------------------------------------------------------

    def record(self, k: str, /, scope: str = "world", **data):
        ev = {"t": round(time.time(), 1), "bot": self.bot, "prof": self.prof, "k": k, **data}
        line = (json.dumps(ev, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
        fd = os.open(self.paths[scope], os.O_APPEND | os.O_WRONLY | os.O_CREAT)
        try:
            os.write(fd, line)               # one write call: appends from several processes do not interleave inside a line
        finally:
            os.close(fd)

    def sight(self, m: str, x: int, y: int):
        """A hostile kind seen at a place; at most one event per kind and cell every five minutes per bot."""
        cell = cell_of(x, y)
        key = (m, cell)
        if time.time() - self.sight_seen.get(key, 0) > 300:
            self.sight_seen[key] = time.time()
            self.record("sight", m=m, cell=cell)

    # ---- reading ----------------------------------------------------------------------------------------------

    def refresh(self, force: bool = False, every: float = 20.0):
        if not force and time.time() - self.last_read < every:
            return
        self.last_read = time.time()
        for scope in ("world", "prof"):
            path = self.paths[scope]
            try:
                size = os.path.getsize(path)
            except OSError:
                continue
            if size <= self.offset[scope]:
                continue
            with open(path, "rb") as f:
                f.seek(self.offset[scope])
                chunk = f.read()
            end = chunk.rfind(b"\n")
            if end < 0:
                continue
            self.offset[scope] += end + 1
            for line in chunk[: end + 1].splitlines():
                try:
                    self._fold(scope, json.loads(line))
                except (ValueError, KeyError):
                    pass

    @staticmethod
    def _decay_cell(c: dict, t: float):
        dt = t - c.get("t", t)
        if dt > 0:
            c["kills"] *= 0.5 ** (dt / HALF_LIFE)
            c["fights"] *= 0.5 ** (dt / HALF_LIFE)
            c["gold"] *= 0.5 ** (dt / HALF_LIFE)
            c["deaths"] *= 0.5 ** (dt / DEATH_HALF_LIFE)
        c["t"] = max(t, c.get("t", 0))

    def _fold(self, scope: str, ev: dict):
        st = self.state[scope]
        st["events"] += 1
        k = ev["k"]
        if k == "fight":
            grp = ev.get("grp") or group_of(ev.get("prof"))
            f = st["fights"][ev["m"]][grp]
            _decay(f, FIGHT_KEYS, ev["t"], FIGHT_HALF_LIFE)
            f["n"] += 1
            f[ev["outcome"]] = f.get(ev["outcome"], 0) + 1
            f["ttk"] += float(ev.get("ttk", 0))
            f["dmg"] += float(ev.get("dmg", 0))
            f["dmgpct"] += float(ev.get("dmg", 0)) / max(1.0, float(ev.get("hp", 1)))
            if ev["outcome"] == "kill" and ev.get("mhits") and float(ev.get("ttk", 0)) > 1:
                st["dps"]["hits"] += float(ev["mhits"])
                st["dps"]["ttk"] += float(ev["ttk"])
                st["dps"]["n"] += 1
            c = st["cells"][ev["cell"]] if ev.get("cell") else None
            if c is not None:
                self._decay_cell(c, ev["t"])
                c["fights"] += 1
                if ev["outcome"] == "kill":
                    c["kills"] += 1
        elif k == "sight":
            st["cells"][ev["cell"]]["sights"][ev["m"]] += 1
        elif k == "death":
            c = st["cells"][ev["cell"]]
            self._decay_cell(c, ev["t"])
            c["deaths"] += 1
        elif k == "loot":
            c = st["cells"][ev["cell"]]
            self._decay_cell(c, ev["t"])
            c["gold"] += int(ev.get("gold", 0))
        elif k == "presence":
            c = st["cells"][ev["cell"]]
            c["pres"] = (c["pres"] + [(ev["t"], ev["bot"])])[-16:]
        elif k == "vendor":
            v = st["vendors"].setdefault(ev["xy"], {"name": "", "stock": {}, "buys": {}, "t": 0})
            v["name"] = ev.get("name") or v["name"]
            v["t"] = ev["t"]
            for item, price, qty in ev.get("stock", []):
                if price == 0 and qty == 0:              # "sold out" from a bot that found the shelf empty: every matching item at this shop
                    for k2 in v["stock"]:
                        if item.lower() in k2:
                            v["stock"][k2][1] = 0
                else:
                    v["stock"][item.lower()] = [price, qty]
            for item, price in ev.get("buys", []):
                v["buys"][item.lower()] = price
        elif k == "craft":
            c = st["crafts"][ev["craft"]][ev["item"]]
            c["n"] += 1
            c["ok"] += 1 if ev.get("ok") else 0
            c["gain"] += 1 if ev.get("gain") else 0
            c["exc"] = c.get("exc", 0) + (1 if ev.get("exc") else 0)
        elif k == "res":
            r = st["res"][ev["kind"]][ev["key"]]
            if ev.get("ok"):
                r["ok"] += 1
            else:
                r["fail"] += 1
                r["reason"] = ev.get("reason", "")
        elif k in ("claim", "blocked"):
            r = st["res"][ev["kind"]][ev["key"]]
            until = ev["t"] + float(ev.get("ttl", 600))
            if k == "claim":
                r["claim_until"], r["claim_by"] = until, ev["bot"]
            else:
                r["blocked_until"] = max(r["blocked_until"], until)
        elif k == "gain":
            st["gains"][ev["skill"]][ev.get("action", "?")] += 1

    # ---- what the brains ask -----------------------------------------------------------------------------------

    def fight_stats(self, m: str, min_n: int = 3):
        """How fights against monster kind m went for bots like this one: (stats, source) or (None, None). Own profession first, then the same kind of fighter anywhere."""
        self.refresh()
        for scope in ("prof", "world"):
            f = self.state[scope]["fights"].get(m, {}).get(self.grp)
            if f:
                _decay(f, FIGHT_KEYS, time.time(), FIGHT_HALF_LIFE)
            if f and f["n"] >= min_n:
                return self._summ(f), scope
        return None, None

    @staticmethod
    def _summ(f):
        n = max(1e-9, f["n"])
        return {"n": f["n"], "kill": f["kill"], "death": f["death"], "flee": f["flee"], "death_rate": f["death"] / n, "flee_rate": f["flee"] / n,
                "avg_ttk": f["ttk"] / n, "avg_dmg": f["dmg"] / n, "avg_dmgpct": f["dmgpct"] / n}

    def measured_dps(self, min_n: int = 6):
        """Hit points of damage per second this profession's bots have actually dealt, from their kills (None until there are min_n kills to average)."""
        self.refresh()
        d = self.state["prof"]["dps"]
        return d["hits"] / d["ttk"] if d["n"] >= min_n and d["ttk"] > 0 else None

    def deadly_kinds(self, min_deaths: int = 2):
        """Monster kinds that have killed bots like this one at least min_deaths times (world-wide, all fighters of this group)."""
        self.refresh()
        out = {}
        for m, groups in self.state["world"]["fights"].items():
            f = groups.get(self.grp)
            if f:
                _decay(f, FIGHT_KEYS, time.time(), FIGHT_HALF_LIFE)
            if f and f["death"] >= min_deaths - 0.01 and f["death"] >= 0.2 * f["n"]:
                out[m] = round(f["death"], 1)
        return out

    def cell_score(self, cell: str) -> float:
        """How good a map cell is for hunting: kills and gold per fight, with deaths counted heavily; unknown cells score neutral so they get tried."""
        self.refresh()
        c = self.state["world"]["cells"].get(cell)
        if c:
            self._decay_cell(c, time.time())
        crowd = self.crowd(cell) * 0.6
        if not c or c["fights"] + c["deaths"] < 1.5:
            return 0.5 - crowd
        gold = min(c["gold"] / 40.0, 2.0 * c["kills"])
        return (c["kills"] + gold) / (1.0 + c["fights"]) - 2.5 * c["deaths"] / (1.0 + c["fights"]) - crowd

    def crowd(self, cell: str, window: float = 300.0) -> int:
        """How many other bots were in this cell in the last few minutes (hunters share spawns, so a crowded cell yields less to each)."""
        c = self.state["world"]["cells"].get(cell)
        if not c:
            return 0
        now = time.time()
        return len({b for t, b in c["pres"] if now - t < window and b != self.bot})

    def hunting_cells(self, near=(1470, 1620), radius=260, n=8):
        """The best-known cells for hunting within radius of near, best first: [(score, cell)]."""
        self.refresh()
        out = []
        for cell, c in self.state["world"]["cells"].items():
            cx, cy = cell_center(cell)
            if abs(cx - near[0]) > radius or abs(cy - near[1]) > radius:
                continue
            if c["kills"] < 0.2 and not c["sights"]:
                continue
            out.append((self.cell_score(cell), cell))
        out.sort(reverse=True)
        return out[:n]

    def dangerous_cell(self, cell: str) -> bool:
        """A cell where bots die more than they kill, judged on the cell and on its eight neighbours together: a killing ground spreads its deaths
        over several cells, each of which alone looked safe."""
        now = time.time()
        x, y = (int(v) for v in cell.split(","))
        deaths = kills = 0.0
        own = None
        for dx in (-CELL, 0, CELL):
            for dy in (-CELL, 0, CELL):
                c = self.state["world"]["cells"].get(f"{x + dx},{y + dy}")
                if not c:
                    continue
                self._decay_cell(c, now)
                deaths += c["deaths"]
                kills += c["kills"]
                if dx == 0 and dy == 0:
                    own = c
        if own and own["deaths"] >= 1.8 and own["deaths"] > own["kills"] * 0.5:
            return True
        return deaths >= 2.0 and deaths > kills * 0.5

    def vendor_selling(self, word: str):
        """Shops that sell something whose name contains word: [(price, xy, item, qty)], cheapest first."""
        self.refresh()
        out = []
        for xy, v in self.state["world"]["vendors"].items():
            for item, (price, qty) in v["stock"].items():
                if word in item and qty > 0:
                    out.append((price, xy, item, qty))
        out.sort()
        return out

    def vendor_buying(self, word: str):
        """Shops that buy something whose name contains word: [(price, xy, item)], best price first."""
        self.refresh()
        out = []
        for xy, v in self.state["world"]["vendors"].items():
            for item, price in v["buys"].items():
                if word in item:
                    out.append((price, xy, item))
        out.sort(reverse=True)
        return out

    def craft_stats(self, craft: str, item: str):
        self.refresh()
        c = self.state["prof"]["crafts"].get(craft, {}).get(item) or self.state["world"]["crafts"].get(craft, {}).get(item)
        return dict(c) if c and c["n"] else None

    def usable(self, kind: str, key: str) -> bool:
        """False if the target is blocked or another bot is working it right now."""
        self.refresh()
        r = self.state["world"]["res"].get(kind, {}).get(key)
        if not r:
            return True
        now = time.time()
        if r["blocked_until"] > now:
            return False
        return not (r["claim_until"] > now and r["claim_by"] != self.bot)

    def res_stats(self, kind: str, key: str):
        self.refresh()
        r = self.state["world"]["res"].get(kind, {}).get(key)
        return dict(r) if r else None

    # ---- a readable summary (the report calls this) --------------------------------------------------------------

    def summary(self) -> str:
        self.refresh(force=True)
        lines = []
        w = self.state["world"]
        lines.append(f"events folded: world {w['events']}, {self.prof} {self.state['prof']['events']}")
        fights = []
        for m, groups in w["fights"].items():
            for grp, f in groups.items():
                if f["n"] >= 2:
                    s = self._summ(f)
                    fights.append((s["death_rate"], m, grp, s))
        fights.sort(reverse=True)
        lines.append("Fights by monster and fighter kind (n, kills, deaths, flees, avg seconds, avg % of hit points lost):")
        for dr, m, grp, s in fights[:25]:
            lines.append(f"  {m:18} {grp:7} n={s['n']:5.1f} kill={s['kill']:5.1f} death={s['death']:4.1f} flee={s['flee']:4.1f} ttk={s['avg_ttk']:5.1f}s lost={s['avg_dmgpct'] * 100:4.0f}%")
        for c in w["cells"].values():
            self._decay_cell(c, time.time())
        cells = sorted(((c["kills"] + c["deaths"], cell, c) for cell, c in w["cells"].items() if c["kills"] >= 0.1 or c["deaths"] >= 0.1 or c["sights"]), reverse=True)
        lines.append("Cells (kills and deaths fade with time; kinds seen are all-time):")
        for _, cell, c in cells[:15]:
            top = ", ".join(f"{k}x{v}" for k, v in sorted(c["sights"].items(), key=lambda kv: -kv[1])[:4])
            lines.append(f"  {cell:10} kills={c['kills']:4.1f} deaths={c['deaths']:4.1f} gold={c['gold']:6.0f} bots now={self.crowd(cell)} seen: {top}")
        return "\n".join(lines)


FRONTIER_CENTER = (1470, 1620)      # Britain


def choose_spot(mem: "SharedMemory", fixed, is_bad, here=None, recent=()):
    """Pick the next hunting spot: the fixed ring plus the best-known cells in the shared memory; spots for which is_bad(x, y) is true and cells that have killed
    bots are dropped, the rest are ranked by what the memory knows with some chance mixed in so new ground still gets tried. A spot within 20 tiles of
    `here` or of a spot in `recent` (just reached) is left out: arriving somewhere with nothing to fight must move the bot on, not choose the same place
    again (ten bots once stood in one cell for twenty minutes doing exactly that)."""
    import random

    def near(a, b, r=20):
        return a is not None and b is not None and abs(a[0] - b[0]) <= r and abs(a[1] - b[1]) <= r

    import math

    cands = [tuple(sp) for sp in fixed]
    for score, cell in mem.hunting_cells(radius=300, n=10):
        if score > 0.25:
            cands.append(cell_center(cell))
    # The frontier: a few untried points 140 to 320 tiles out from Britain. Forty bots empty the town's own spawn within minutes, and a player whose
    # usual ground is bare goes further afield. Unknown cells score neutral (0.5), so a frontier point beats a hunted-out spot; a point the walk
    # cannot reach (sea, mountain) is marked unusable for everyone by the explore rule.
    for _ in range(6):
        ang, r = random.random() * 2 * math.pi, random.uniform(140, 320)
        cands.append((int(FRONTIER_CENTER[0] + r * math.cos(ang)), int(FRONTIER_CENTER[1] + r * math.sin(ang))))
    cands = [p for p in cands if not near(p, here) and not any(near(p, r) for r in recent) and mem.usable("spot", cell_of(*p))]
    scored = [(mem.cell_score(cell_of(x, y)) + random.random() * 0.6, (x, y)) for x, y in cands if not is_bad(x, y) and not mem.dangerous_cell(cell_of(x, y))]
    if not scored:
        return random.choice(list(fixed))
    scored.sort(reverse=True)
    return scored[0][1]
