"""The A1 house goal (Watcher 2026-10-17, plan HOUSE-GOAL-PLAN.md signed off by the Operator 2026-10-18; Helper 2; feature "house_goal"). Mixin for BotBase and CasterBot, written into the bot-farm folder by
patch_housegoal.py. NEVER switched on in the farm world without the owner's explicit OK (a lasting change to a persistent world); proved first on a disposable host.

State machine, one step per tick through the rule r_house, state in <bot>/house.json (resumable):
  none -> buy    the savings goal (goals.py: the house fund) is done and carried + banked gold covers a deed + RESERVE: stage "buy"
  buy  -> site   at the Architect (gazetteer role architect): bank first when the purse is short (visit_bank withdraw), buy the cheapest of "small brick house" / "field stone house" the list shows
  site -> lock   generated candidate sites (rings of points 60-200 tiles from the home town, outside every gazetteer town region, NoHousing region and the shard's unguarded areas, 12 tiles apart, nearest first,
                 no death cells, none the shared memory says was refused): walk there, double-click the deed, answer the target cursor with `targettile x y z`, judge by whether the deed is gone from the pack;
                 a refused site is recorded (res house_site) so no bot retries it; at most 12 tries an hour. ev house_placed {where, tries}
  lock -> furnish  stand at the site, drop up to 3 spare items (bedroll, kindling, candle), say "I wish to lock this down" and target each: ev lockdown {item}
  furnish -> done  the Furnisher (vendor spot from the shard's furnishers.json): read its list, buy the cheapest piece the purse affords above RESERVE_AFTER: ev furnisher_buy {item, price}; then home and done.
Nothing here is a coordinate of a particular house: the candidates come from the gazetteer and the bot's home; the Furnisher's spot comes from the shard's own data file.
"""
from __future__ import annotations

import json
import math
import os
import re
import time

FEATURE = "house_goal"
try:
    import goals as _goals
    DEED_COST = int(_goals.HOUSE_COST)         # the shard's small house price (16,000 since 2026-10-18; stock 43,800)
except Exception:                               # pragma: no cover
    DEED_COST = 16000
RESERVE = 1000              # carried + banked above the deed before the bot starts
RESERVE_AFTER = 200         # the purse a bot keeps when it buys the furnishing
DEED_WANTS = ("small brick house", "field stone house")
RINGS = (60, 80, 100, 120, 140, 160, 180, 200, 230, 260)
SPACING = 6
SEED_REACH = 400            # tiles from the home town centre: the surveyed sites farther away are not tried
TRIED_APART = 10            # a site this close to a refused one is skipped (the refusal is local)
TRIES_PER_HOUR = 12
STEP_GAP = 20.0
LOCK_WORDS = ("bedroll", "kindling", "candle", "empty bottle", "mortar")      # spare junk; a stack is dropped whole and locks down as one item
LOCK_MAX = 3
HERE = os.path.dirname(os.path.abspath(__file__))


def furnisher_spot():
    """The Furnisher's standing spot from the shard's generated data file, else None."""
    for rel in (("..", "..", "..", "data", "configuration", "furnishers.json"), ("..", "..", "..", "..", "ShardContent", "data", "configuration", "furnishers.json")):
        try:
            v = json.load(open(os.path.join(HERE, *rel), encoding="utf-8"))["vendor"]
            return int(v["x"]), int(v["y"])
        except (OSError, ValueError, KeyError, TypeError):
            continue
    return None


def open_ground(x, y, half=6):
    """True when the walk map says every tile of the square around (x, y) is walkable ground (a small house is 7 x 7 with its yard); True when the map is not available."""
    try:
        import walkroute
        g = walkroute.get()
        return all(g.walkable(x + dx, y + dy) for dx in range(-half, half + 1, 2) for dy in range(-half, half + 1, 2))
    except Exception:
        return True


def cheb(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


class HouseGoalMixin:
    # ---- state --------------------------------------------------------------------------------------------------------------------------------------

    def house_path(self):
        return os.path.join(self.dir, "house.json")

    def house_state(self):
        st = self.__dict__.get("_house")
        if st is None:
            st = {"phase": "none", "where": None, "tries": 0, "tried": [], "tries_at": [], "locked": 0, "fails": 0, "rest_until": 0}
            try:
                st.update(json.load(open(self.house_path(), encoding="utf-8")))
            except (OSError, ValueError, TypeError):
                pass
            self._house = st
        return st

    def house_save(self):
        try:
            with open(self.house_path() + ".tmp", "w", encoding="utf-8") as f:
                json.dump(self.house_state(), f)
            os.replace(self.house_path() + ".tmp", self.house_path())
        except (OSError, TypeError, ValueError):
            pass

    def house_emit(self, name, **kw):
        try:
            self.dlog("ev", ev=name, cell=None, rule=getattr(self, "current_rule", None), **kw)
        except Exception:
            pass

    # ---- the gate ---------------------------------------------------------------------------------------------------------------------------------

    def house_wealth(self):
        return (self.c.gold or 0) + self.facts.get("bank_balance", 0)

    def house_deed(self):
        """The deed in the pack: by the serial noted at the purchase (the client names every deed just "deed": no property lists in this era), else any item named "deed" or "deed to a ... house"."""
        want = self.house_state().get("deed_serial")
        if want:
            return next((i for i in self.c.backpack if i.serial == want), None)
        return next((i for i in self.c.backpack if "deed" in i.name.lower() and "house" in i.name.lower() and "guild" not in i.name.lower()), None)      # (never the plain "deed": every deed is named so)

    def house_ready(self):
        """A1 persona or not, the bot qualifies when the feature is on, it has no house yet and the money is there (the house fund of goals.py is done)."""
        if not self.feature(FEATURE):
            return False
        st = self.house_state()
        if st["phase"] != "none":
            return True                                              # under way
        g = self.facts.get("goal") or {}
        fund = g.get("kind") == "house" and g.get("meta", {}).get("fund_done")
        wealth = self.house_wealth()
        return (bool(fund) and wealth >= DEED_COST + RESERVE) or wealth >= DEED_COST + 2 * RESERVE      # the house fund of goals.py is done, or the money is plainly there

    def r_house(self):
        if not self.feature(FEATURE) or self.c.ghost or self.hp_pct() < 70:
            return False
        st = self.house_state()
        now = time.time()
        if st["phase"] == "done" or now < st.get("rest_until", 0) or now - self.__dict__.get("_house_step", 0) < STEP_GAP:
            return False
        try:
            if self.threats(10):
                return False
        except Exception:
            pass
        if not self.house_ready():
            return False
        self.__dict__["_house_step"] = now
        if st["phase"] == "none":
            st["phase"] = "buy"
            self.house_save()
        step = {"buy": self.house_buy, "site": self.house_site, "lock": self.house_lock, "furnish": self.house_furnish}.get(st["phase"])
        if step is None:
            return False
        self.activity = f"house: {st['phase']}"
        try:
            return bool(step(st))
        finally:
            self.house_save()

    def house_fail(self, st, why, rest=900):
        st["fails"] = st.get("fails", 0) + 1
        st["rest_until"] = time.time() + rest * min(st["fails"], 4)
        self.log(f"house: {st['phase']} failed: {why}")
        return True

    # ---- buy --------------------------------------------------------------------------------------------------------------------------------------

    def house_buy(self, st):
        """The Architect draws the price from the BANK ACCOUNT ("The total of your purchase is 43800 gold, which has been drawn from your bank account", verified on a disposable host): the deed price
        weighs hundreds of stones and cannot be carried, so nothing is withdrawn and shop_at (which budgets by carried gold) is not used. The deed arrives named just "deed"; its serial is noted."""
        if self.house_deed():
            st["phase"] = "site"
            return True
        if self.facts.get("bank_balance", 0) < DEED_COST:
            return self.house_fail(st, f"the bank holds {self.facts.get('bank_balance', 0)}, the deed costs {DEED_COST}")
        shops = self.find_places(("architect",), n=1) or self.find_places(("broker",), n=1)
        if not shops:
            return self.house_fail(st, "no architect in the gazetteer")
        self.goto_near(shops[0][0], shops[0][1], 3).wait(timeout=90)
        serial = None
        for v in [m for m in self.c.mobiles(within=9) if m.notoriety == "Innocent" and m.name and not m.name.startswith("Bot")]:
            lst = self.vendor_list(v, "buy")
            for want in DEED_WANTS:
                for line in lst[1:]:
                    m = re.search(r"(0x[0-9A-Fa-f]+)\s+(\d+)gp\s+x(\d+)\s+(.+)", line)
                    if m and want in m.group(4).lower() and int(m.group(2)) <= self.facts.get("bank_balance", 0):
                        serial = m.group(1)
                        break
                if serial:
                    break
            if serial:
                break
        if not serial:
            return self.house_fail(st, "no Architect list showed a small brick or field stone house deed")
        before = {i.serial for i in self.c.backpack}
        self.cmd(f"buy {serial} 1", timeout=10)
        time.sleep(3.0)
        self.c.open_backpack()
        time.sleep(1.0)
        new = [i for i in self.c.backpack if i.serial not in before and "deed" in i.name.lower()]
        if new:
            st["deed_serial"] = new[0].serial
            self.facts["bank_balance"] = max(0, self.facts.get("bank_balance", 0) - DEED_COST)
            self.log(f"house: bought the deed {new[0].serial}")
            st["phase"] = "site"
            return True
        return self.house_fail(st, "the purchase gave no deed")

    # ---- site -------------------------------------------------------------------------------------------------------------------------------------

    def house_seeds(self):
        """The surveyed placeable centres (house_sites.json: the server's own HousePlacement.Check, measured with the staff command [HousingSurvey), or []."""
        got = self.__dict__.get("_house_seeds")
        if got is None:
            try:
                got = [tuple(p) for p in json.load(open(os.path.join(HERE, "house_sites.json"), encoding="utf-8"))["sites"]]
            except (OSError, ValueError, KeyError, TypeError):
                got = []
            self._house_seeds = got
        return got

    def house_candidates(self):
        """Sites around the home town, nearest first: outside every town and NoHousing region and the shard's unguarded areas, on the home side of the map."""
        import gazetteer as gz
        home = self.home()
        cx, cy = (home["centre"][0], home["centre"][1]) if home else (self.c.x, self.c.y)
        side = gz.side(cx, cy)
        try:
            import townguard
            unguarded = townguard.unguarded_areas()
        except Exception:
            unguarded = []
        out = []
        seeds = self.house_seeds()
        for x, y in seeds:
            if cheb((x, y), (cx, cy)) > SEED_REACH or gz.side(x, y) != side or gz.in_town(x, y):
                continue
            if any(x1 - 8 <= x <= x2 + 8 and y1 - 8 <= y <= y2 + 8 for x1, y1, x2, y2 in unguarded):
                continue
            try:
                if self.near_death_spot(x, y, 40) or self.mem.dangerous_cell(__import__("memory").cell_of(x, y)):
                    continue
            except Exception:
                pass
            out.append((x, y))
        if out:
            return sorted(out, key=lambda p: cheb(p, (cx, cy)))                  # the surveyed sites, nearest first
        for r in RINGS:
            n = max(8, int(2 * math.pi * r / SPACING))
            for k in range(n):
                a = 2 * math.pi * k / n
                x, y = int(cx + r * math.cos(a)), int(cy + r * math.sin(a))
                if x < 8 or y < 8 or gz.side(x, y) != side or gz.in_town(x, y):
                    continue
                if any(rg["type"] in ("NoHousingRegion", "DungeonRegion") or rg["kind"] in ("town", "dungeon") for rg in gz.regions_at(x, y)):
                    continue
                if any(x1 - 8 <= x <= x2 + 8 and y1 - 8 <= y <= y2 + 8 for x1, y1, x2, y2 in unguarded):
                    continue
                try:
                    if self.near_death_spot(x, y, 40) or self.mem.dangerous_cell(__import__("memory").cell_of(x, y)):
                        continue
                except Exception:
                    pass
                if not open_ground(x, y):
                    continue                                                  # a house needs a solid surface under all of its foundation (the server refused sea shore and slopes)
                out.append((x, y))
        return sorted(out, key=lambda p: cheb(p, (cx, cy)))                      # nearest first

    def house_site(self, st):
        deed = self.house_deed()
        if not deed:
            st["phase"] = "buy"
            return True
        now = time.time()
        st["tries_at"] = [t for t in st.get("tries_at", []) if now - t < 3600]
        if len(st["tries_at"]) >= TRIES_PER_HOUR:
            return self.house_fail(st, "12 sites tried this hour", rest=600)
        tried = {tuple(t) for t in st.get("tried", [])}
        site = None
        for x, y in self.house_candidates():
            if (x, y) in tried or any(cheb((x, y), t) < TRIED_APART for t in tried):
                continue
            try:
                if not self.mem.usable("house_site", f"{x // 8},{y // 8}"):
                    continue                                          # another bot was refused here
            except Exception:
                pass
            site = (x, y)
            break
        if site is None:
            return self.house_fail(st, "no candidate site left", rest=3600)
        x, y = site
        st.setdefault("tried", []).append([x, y])
        st["tries_at"].append(now)
        st["tries"] = st.get("tries", 0) + 1
        self.log(f"house: trying the site {x},{y}")
        res = self.goto_near(x, y, 3).wait(timeout=90)
        if not str(res).startswith("arrived"):
            return True                                               # not reachable: the next site on the next step
        from uo import Event
        self.c.events.drain()
        self.c.use(deed.serial)
        self.c.wait_for(Event.TARGET_REQUEST, timeout=2)                 # (the house placement cursor does not announce itself in the log: the answer is sent either way)
        time.sleep(0.5)
        z = self.c.state.get("charPosZ", 0)
        self.c.call(f"targettile {x} {y} {z}", timeout=6)
        time.sleep(3.0)
        lines = self.read_journal()
        self.c.open_backpack()
        time.sleep(1.0)
        placed = self.house_deed() is None
        try:
            self.mem.record("res", kind="house_site", key=f"{x // 8},{y // 8}", ok=placed, reason=" ".join(lines)[-80:])
        except Exception:
            pass
        if placed:
            st["phase"], st["where"] = "lock", [x, y]
            self.house_emit("house_placed", where=[x, y], tries=st["tries"])
            self.log(f"house: placed at {x},{y} after {st['tries']} tries")
        else:
            try:
                self.mem.record("blocked", kind="house_site", key=f"{x // 8},{y // 8}", ttl=86400)      # no bot tries this plot again today
            except Exception:
                pass
            self.log(f"house: refused at {x},{y}: {' '.join(lines)[-100:]}")
        return True

    # ---- lock down, furnish ---------------------------------------------------------------------------------------------------------------------

    def house_lock(self, st):
        x, y = st["where"]
        self.goto_near(x, y + 4, 3).wait(timeout=60)                     # near the house first, then to its door (where the door is depends on the design)
        z_out = self.c.state.get("charPosZ", 0)
        door = None
        try:
            for l in self.c.call("allitems 12", timeout=8):                 # (a house's door and walls are multi parts: only allitems lists them)
                m = re.match(r"\s*(0x[0-9A-Fa-f]+)\s+(.*?door.*?)\s+\((-?\d+), (-?\d+), (-?\d+)\)\s+ground", l, re.I)
                if m and abs(int(m.group(3)) - x) <= 6 and abs(int(m.group(4)) - y) <= 6:
                    door = (int(m.group(3)), int(m.group(4)))
                    break
        except Exception:
            door = None
        if door:
            self.goto_near(door[0], door[1], 2).wait(timeout=40)
            try:
                self.c.call("opendoor", timeout=6)                           # the owner's door opens; the speech command only works INSIDE the house
            except Exception:
                pass
            time.sleep(1.5)
            self.c.gotoexact(door[0], door[1]).wait(timeout=20)
        res = None
        if door:
            for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0), (0, -2), (0, 2), (-2, 0), (2, 0)):        # a tile inside, beyond the door (the house floor is above the ground outside)
                res = self.c.gotoexact(door[0] + dx, door[1] + dy).wait(timeout=20)
                if self.c.state.get("charPosZ", 0) >= z_out + 6 and (self.c.x, self.c.y) != door:
                    break
        else:
            res = self.c.gotoexact(x, y).wait(timeout=30)
        if self.c.state.get("charPosZ", 0) < z_out + 6:                 # a house floor stands 7 above the ground outside (the porch step in front of it only 4)
            self.log(f"house: could not get inside (door {door}, {res}, z {self.c.state.get('charPosZ')}); the lockdown waits")
            st["lock_tries"] = st.get("lock_tries", 0) + 1
            if st["lock_tries"] >= 4:
                st["phase"] = "done" if st.get("furnish_serial") else "furnish"
                if st["phase"] == "done":
                    self.house_emit("house_done", where=st.get("where"), furnished=True)
            return True
        from uo import Event
        mine = st.get("furnish_serial")
        items = [i for i in self.c.backpack if i.serial == mine or (not mine and any(w in i.name.lower() for w in LOCK_WORDS))][: LOCK_MAX - st.get("locked", 0) if not mine else 1]      # the bought furnishing, else spare junk
        for it in items:
            name = it.name
            self.c.call(f"dropground {it.serial} {it.amount or 1}", timeout=8)
            time.sleep(1.0)
            ground = next((g for g in self.ground_items(3) if name.lower() in g.name.lower()), None)
            if ground is None:
                continue
            self.c.events.drain()
            self.c.say("I wish to lock this down")
            if self.c.wait_for(Event.TARGET_REQUEST, timeout=5) is None:
                continue
            self.c.target(ground.serial)
            time.sleep(1.5)
            st["locked"] = st.get("locked", 0) + 1
            self.house_emit("lockdown", item=name)
        if mine:
            st["phase"] = "done"
            self.house_emit("house_done", where=st.get("where"), furnished=True)
        else:
            st["phase"] = "furnish"
        return True

    def house_furnish(self, st):
        """The Furnisher also draws the price from the bank account, so nothing is withdrawn: walk to its spot (a far walk is the farm's own r_far machinery), read its list, buy the cheapest piece the bank covers
        above RESERVE_AFTER with `buy <serial> 1`. The list lines are the shop's standard "0x... NNNNgp xQQQ Name" (verified: 37 pieces, from 1,850 gold)."""
        spot = furnisher_spot()
        budget = self.facts.get("bank_balance", 0) + (self.c.gold or 0) - RESERVE_AFTER
        if spot is None or budget < 1000:
            st["phase"] = "done"
            self.house_emit("house_done", where=st.get("where"), furnished=False)
            return True
        res = self.far_front(spot, "shop", 90)
        if res:
            self.far_after(res, "shop")
            return True                                                   # the walk to the Furnisher is under way (or not worth it): this step again later
        self.goto_near(spot[0], spot[1], 3).wait(timeout=90)
        rows = []
        for v in [m for m in self.c.mobiles(within=9) if m.notoriety == "Innocent" and m.name and not m.name.startswith("Bot")]:
            lst = self.vendor_list(v, "buy")
            for line in lst[1:]:
                m = re.search(r"(0x[0-9A-Fa-f]+)\s+(\d+)gp\s+x(\d+)\s+(.+)", line)
                if m and int(m.group(2)) <= budget:
                    rows.append((int(m.group(2)), m.group(1), m.group(4).strip()))
            if rows:
                break
        if not rows:
            st["fur_tries"] = st.get("fur_tries", 0) + 1
            if st["fur_tries"] < 4:
                return True                                               # the list did not open or held nothing affordable: try again
            st["phase"] = "done"
            self.house_emit("house_done", where=st.get("where"), furnished=False)
            return True
        price, serial, name = min(rows)
        before = {i.serial for i in self.c.backpack}
        self.cmd(f"buy {serial} 1", timeout=10)
        time.sleep(3.0)
        self.c.open_backpack()
        time.sleep(1.0)
        new = [i for i in self.c.backpack if i.serial not in before]
        bought = bool(new)
        if bought:
            self.facts["bank_balance"] = max(0, self.facts.get("bank_balance", 0) - price)
            self.house_emit("furnisher_buy", item=name, price=price)
            st["furnish_serial"] = new[0].serial                              # home with it: drop it inside and lock it down (house_lock)
            st["phase"], st["lock_tries"] = "lock", 0
            return True
        st["phase"] = "done"
        self.house_emit("house_done", where=st.get("where"), furnished=False)
        return True

    def far_rules(self):
        rules = super().far_rules()
        if "r_house" not in rules and "r_bank" in rules:
            rules.insert(rules.index("r_bank"), "r_house")
        return rules
