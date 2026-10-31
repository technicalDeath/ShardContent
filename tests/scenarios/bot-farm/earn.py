"""How a broke gatherer or crafter earns its way back (the crafter and the broke miner had these five as word-for-word copies, 2026-10-30): what a kill
of a kind pays, which grey is prey for a bot that must earn, what in the pack a shop buys, and the ground that has paid. A brain says what its tool and its
material are (earn_tool, earn_material)."""
from __future__ import annotations

import time

from memory import cell_of


class EarnMixin:
    def earn_tool(self):
        return self.tool()

    def earn_material(self, low):
        return low == self.cfg["mat"] or low in self.cfg.get("mat_alt", ())

    def coin_value(self, kind):
        """Gold a kill of this kind pays, from every bot's loot over the fights seen; 0.0 for a kind fought 6+ times that never paid, None when not measured."""
        w = self.mem.state["world"]
        kl = w["kloot"]
        fights = sum(g["n"] for g in w["fights"].get(kind, {}).values()) if kind in w["fights"] else 0
        hit = kl.get(kind) or kl.get(kind + "s")
        if hit and hit["n"] >= 2:
            return hit["gold"] / max(fights, hit["n"])
        if any(k != kind and (k.startswith(kind) or kind.startswith(k)) for k in kl):
            return None
        return 0.0 if fights >= 6 and not hit else None

    def prey(self, within=9):
        ps = super().prey(within)
        if not self._coin_only:
            return ps
        keep = []
        for m in ps:
            v = self.coin_value(self.mkey(m))
            if m.distance <= 1 or v is None or v >= 1.0:
                keep.append(m)
            else:
                skipped = self.facts.setdefault("coin_skipped", set())
                if self.mkey(m) not in skipped:
                    skipped.add(self.mkey(m))
                    self.dlog("choice", what=f"skip {self.mkey(m)} for coins", why=f"{v:.1f} gold a kill in the shared memory")
        return keep

    def scraps(self):
        """[(name, price, xy, amount)] of pack items some known shop buys at a price; its material only when the tool is gone and the funds are short."""
        out = []
        toolless = not self.earn_tool()
        for it in self.c.backpack:
            low = it.name.lower()
            is_mat = self.earn_material(low)
            if any(w in low for w in self.SCRAP_PROTECT) or (is_mat and not (toolless and self.funds() < (self.tool_price() or self.TOOL_PRICE_GUESS))):
                continue
            offers = [(p, xy) for p, xy, item in self.mem.vendor_buying(low) if p > 0 and item in (low, low + "s")]
            if offers:
                p, xy = offers[0]
                out.append((low, p, tuple(int(v) for v in xy.split(",")), it.amount or 1))
        return out

    def earn_candidates(self):
        home = self.home_centre()
        core = self.home_core() if getattr(self, "home_core", None) else (home[0] - 60, home[1] - 60, home[0] + 60, home[1] + 60)
        cells = self.mem.state["world"]["cells"]
        cand = {}
        for x, y in self.earn_spots():
            cand[(x, y)] = cells[cell_of(x, y)]["gold"] if cell_of(x, y) in cells else 0.0
        for cell, c in cells.items():
            if c["gold"] < self.EARN_MIN_GOLD:
                continue
            cx, cy = (int(v) for v in cell.split(","))
            x, y = cx + 20, cy + 20
            if max(abs(x - home[0]), abs(y - home[1])) > self.EARN_REACH or (core[0] <= x <= core[2] and core[1] <= y <= core[3]):
                continue
            if self.mem.dangerous_cell(cell) or self.mem.camp_cell(cell):
                continue
            cand[(x, y)] = max(cand.get((x, y), 0.0), c["gold"])
        empty = self.facts.get("earn_empty", {})
        now = time.time()
        out = []
        for (x, y), g in cand.items():
            if self.near_death_spot(x, y, 40) or empty.get((x, y), 0) > now or self.mem.dangerous_cell(cell_of(x, y)):
                continue
            out.append((x, y, g - max(abs(x - self.c.x), abs(y - self.c.y)) / 30.0))
        return out

    def earn_ground(self):
        cand = self.earn_candidates()
        if not cand:
            self.facts.pop("earn_empty", None)
            spots = [s for s in self.earn_spots() if not self.near_death_spot(*s, 40) and not self.mem.dangerous_cell(cell_of(*s))] or [self.home_centre()]
            return spots[int(time.time() // 240) % len(spots)]
        best = max(cand, key=lambda c: c[2])
        if best[2] > 0:
            return best[0], best[1]
        pool = sorted(cand, key=lambda c: (c[0], c[1]))
        return pool[int(time.time() // 240) % len(pool)][:2]
