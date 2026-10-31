"""Casters who make money (owner 2026-10-19: "We need to deal with casters being so poor" ... "carving corpses to get leather and meat can make good money";
the A/B he chose: profit-aware hunting + selling what it yields). Feature "caster_profit". Mixin for CasterBot (ProfitMixin, before HuntMixin in its bases).

What the casters did (2026-10-18 23:50 - 2026-10-19 07:15, 61 bot-hours): 74% of the time walking (r_explore), 7% fighting; 2,190 gold of reagents for 894 gold
looted; giant rats and slimes their main prey, killed with spells: a 32-hit-point giant rat needs 2-3 Lightnings (12-18 gold) for 13 gold, and its six hides and
a rib (38 gold more) were left on the corpse - casters carved only farm animals and took only the meat.

The model (loot_value.json, make_loot_value.py: the server's own loot packs, hides, meat, hit points and poison immunity):
  VALUE of a kill  = its average gold + what carving pays (hides cut into leather, 5 each at the Tanner; ribs 8, lamb 4, a bird 3 at the Butcher)
                     + EXTRA_VALUE for potions / scrolls / gems / magic in its packs
  COST of a kill   = the reagent gold to do it the cheapest way this caster can:
                       fists      a creature of FIST_HITS or fewer hit points that hits for FIST_DAMAGE or less (rats, mongbats, rabbits): free
                       Poison     first on anything not immune to Lesser poison (3 gold of nightshade, 9 mana; pre-AOS Lesser: at least 4 a tick, 10 ticks:
                                  40 damage over 30 s; Magery + Poisoning under 130 casts Lesser)
                       a spell    for what is left: of Magic Arrow, Fireball, Lightning and Energy Bolt in the book with reagents, the least gold per expected
                                  damage at this Magery (pre-ML book bands: success = (Magery - circle start) / 40; damage pre-AOS from the spell code)
  NET = VALUE - COST. A spawner is worth the sum of its creatures' NET / 25 (the hunt_spot scale); a kind with NET <= 0 is no prey (unless it is next to the
  caster: then it is fought, the cheapest way). Prey are taken best NET first.
  THE FIGHT: fists, Poison and then follow on foot (fists while adjacent: free damage) as long as the poison can finish it, else the cheapest spell.
  CARVING: every corpse of a kind with hides or meat (not only farm animals): meat and hides taken while the weight allows, hides cut with the pack's scissors at
  once (5 stones each as hides, 1 as leather). SELLING: leather at the Tanner (r_sell_leather), meat at the Butcher (r_sellmeat, as before), hides that could not be
  cut at the Furtrader. STAYING: a ground that paid in the last STAY_KILL s is kept past the 240 s patrol turn, up to STAY_MAX.
LEARNING (owner: "build the logic into the brains so that the bots can reason and make some of these decisions themselves"): the engine table is only the prior.
  Every kill records what it cost (the reagents of the casts made at it) and, SETTLE s later, what it brought (gold picked up, leather cut, meat taken), into the
  shared farm store (farmdb table "kill_value": "<kind>|v" and "<kind>|c", exponential averages over all casters). From LEARN_MIN kills of a kind on, the
  measured value and cost replace the prior's, so a kind that pays more or less than the table thinks moves up or down every caster's list by itself.
Events: profit_kill {m, value, cost, net, method}, carve {..., hides}, leather_sold {n, gold}.
"""
import json
import os
import random
import re
import time
import items  # noqa: E402  (the shared item table)

HERE = os.path.dirname(os.path.abspath(__file__))
FIST_HITS = 8
FIST_DAMAGE = 3
EXTRA_VALUE = {"potions": 10, "scrolls": 12, "gems": 15, "magic": 8}
POISON = {"name": "poison", "circle": 3, "start": 20.0, "cost": 3, "damage": 40.0, "mana": 9, "reagents": ("Nightshade",)}
SPELLS = [  # pre-AOS damage from the spell code (Utility.Random(min, count) -> min .. min + count - 1), reagent gold at Britain's Mage
    {"name": "magic arrow", "start": 0.0, "damage": 5.5, "cost": 3, "mana": 4, "reagents": ("SulfurousAsh",)},
    {"name": "fireball", "start": 20.0, "damage": 13.0, "cost": 5, "mana": 9, "reagents": ("BlackPearl",)},
    {"name": "lightning", "start": 30.0, "damage": 16.0, "cost": 6, "mana": 11, "reagents": ("MandrakeRoot", "SulfurousAsh")},
    {"name": "energy bolt", "start": 50.0, "damage": 32.5, "cost": 8, "mana": 20, "reagents": ("BlackPearl", "Nightshade")},
]
MIN_SUCCESS = 0.6
POISON_TICKS = 10
POISON_TICK_DAMAGE = 4.0
POISON_SECS = 33.0
STAY_KILL = 360
STAY_MAX = 1200
LEATHER_SELL_AT = 25
SCALE = 25.0
SETTLE = 45
KV = "kill_value2"                       # the farm store's table of learned kill values; "kill_value" holds the zeros learned while no take landed (patch_pasture_harvest)
LEARN_MIN = 5
LEARN_ALPHA = 0.2
FIELD_STALE = 360                        # a field with no paying kill this long after arriving: the next one (patch_safe_fields)
FIELD_EMPTY = 75                         # no prey in sight this long after arriving: the field is empty, left at once
FIELD_MAX = 1200                         # a field worked this long is left even while it pays: a player sees other fields
FIELD_TRAVEL = 900                       # a field not reached in this long: given up
FIELD_REST = 600                         # a field left rests this long: the longest respawn (maxDelay 00:10:00) of the spawners in the tier-1 areas within 200 tiles
                                         # (greater-britain-spawn-areas.json: South-west Farmlands, Castle Woods, Britain Graveyard). It was 1800, and with only
                                         # those three near, 8 casters walked to fields 200-480 tiles out (2-4 gold a minute against 15-24, 2026-10-29)
FIELD_NEAR = 15                          # arrived: this close to one of its spawners
FIELD_WALK = 300.0                       # the score halves at this many tiles away
FIELD_FAR = 200                          # a field this many tiles away or more only when no nearer one is open: the casters' 68 field visits 18:00-23:20 2026-10-29
                                         # earned 15-24 gold a minute under 200 tiles (visit and walk counted) and 2-4 gold a minute at 200-480
FIELD_CROWD = 2                          # this many other casters on a field: it is left out
FIELD_CHOICES = 3                        # the next field: one of the best three, in proportion to their scores
FIELD_AROUND = 20                        # working a field: a point this close to one of its spawners
FIELD_BROKE_VETO = ("wolf", "bear", "cougar", "panther")
CASTER_TIER2 = 60.0                     # Magery a caster needs for tier-2 fields: two at 47-48 died there to packs (patch_field_recheck)
RECHECK = 60.0                          # the field being worked is checked again this often       # with DANGER_KINDS: what kills a mage with no spell to cast
_TABLE = None
_FIELDS = {"d": None}
_LEARNED = {"t": 0.0, "d": {}}


CASTER_RATE = 887.0 / 3600.0            # gold a caster earns a second all in (ledger caster3, 8 casters 22:34-22:55 2026-10-29: +887 gold a bot-hour with goods carried):
                                         # a fight paying less a second of its own time (its median length and the walk to it) is worth less than going on
FEATHER_GOLD = items.FEATHER_PRICE      # gold a feather fetched at the Bowyer (sale_task feathers, gold over items, 2026-10-29)


def _feathers():
    """{kind: feathers a carve gives} from the engine's creature files (`Feathers => N`, e.g. Eagle 36): loot_value.json's carve left them out, so an eagle read as
    3 gold of meat and the archers turned eagles away (the Watcher, 2026-10-29). {} when the engine sources are not there."""
    out = {}
    root = os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", "ModernUO", "Projects", "UOContent", "Mobiles"))
    for dirpath, _dirs, files in os.walk(root):
        for f in files:
            if not f.endswith(".cs"):
                continue
            try:
                src = open(os.path.join(dirpath, f), encoding="utf-8", errors="ignore").read()
            except OSError:
                continue
            m = re.search(r"Feathers\s*=>\s*(\d+)", src)
            c = re.search(r"public partial class (\w+)", src)
            if m and c and int(m.group(1)) > 0:
                out[norm(c.group(1))] = int(m.group(1))
    return out


def table():
    global _TABLE
    if _TABLE is None:
        try:
            _TABLE = json.load(open(os.path.join(HERE, "loot_value.json"), encoding="utf-8"))["kinds"]
        except (OSError, ValueError, KeyError):
            _TABLE = {}
        try:
            for k, n in _feathers().items():
                e = _TABLE.get(k)
                if e is not None and not e.get("feathers"):
                    e["feathers"] = n
                    e["carve"] = float(e.get("carve") or 0) + n * FEATHER_GOLD
        except Exception:
            pass
    return _TABLE


def learned():
    """{"<kind>|v" or "<kind>|c": [avg, n, t]} from the farm store, refreshed every minute; {} when the store is not there."""
    if time.time() - _LEARNED["t"] > 60:
        try:
            import farmdb
            _LEARNED["d"] = farmdb.rate_table(KV)
        except Exception:
            _LEARNED["d"] = _LEARNED.get("d") or {}
        _LEARNED["t"] = time.time()
    return _LEARNED["d"]


FIELD_RATES = {"t": 0.0, "d": {}}
FIELD_RATE_VISITS = 5                    # a field's measured rate counts from this many visits
FIELD_RATE_TTL = 1800.0


def field_rates():
    """{field: gold a minute} from the casters' own visits in the last day (field_chosen to field_left, the profit_kill values between, the walk there
    included), for fields with FIELD_RATE_VISITS or more. 2026-10-30: the Graveyard 29 and South-west Farmlands 27 gold a minute, Castle Woods 10, Bay Woods 8,
    North-east Pasture 7, from 151 visits; the field score knew only spawner values and distance."""
    now = time.time()
    if now - FIELD_RATES["t"] < FIELD_RATE_TTL:
        return FIELD_RATES["d"]
    FIELD_RATES["t"] = now
    agg = {}
    try:
        from bot_common import FARM
        import glob
        for p in [q for pat in ("BotMage*", "BotSorc*", "BotWarlock*") for q in glob.glob(os.path.join(FARM, pat, "decisions.jsonl"))]:      # the casters only
            cur = None
            with open(p, encoding="utf-8") as fh:
                fh.seek(0, 2)
                fh.seek(max(0, fh.tell() - 6_000_000))
                fh.readline()
                for line in fh:
                    if '"field_' not in line and '"profit_kill"' not in line:
                        continue
                    try:
                        j = json.loads(line)
                    except ValueError:
                        continue
                    if now - j.get("t", 0) > 86400:
                        continue
                    e = j.get("ev")
                    if e == "field_chosen":
                        cur = [j.get("field"), j["t"], 0.0]
                    elif e == "profit_kill" and cur:
                        cur[2] += float(j.get("value") or 0)
                    elif e == "field_left" and cur and cur[0] == j.get("field"):
                        a = agg.setdefault(cur[0], [0, 0.0, 0.0])
                        a[0] += 1
                        a[1] += (j["t"] - cur[1]) / 60.0
                        a[2] += cur[2]
                        cur = None
    except Exception:
        pass
    FIELD_RATES["d"] = {k: a[2] / a[1] for k, a in agg.items() if a[0] >= FIELD_RATE_VISITS and a[1] > 0}
    return FIELD_RATES["d"]


def fields(tiers):
    """[(area, tier, x, y, range, kinds)] for every spawner of the Britain hunting areas of these tiers (britain_areas.json; [] without it)."""
    if _FIELDS["d"] is None:
        try:
            _FIELDS["d"] = json.load(open(os.path.join(HERE, "britain_areas.json"), encoding="utf-8")).get("areas", [])
        except (OSError, ValueError):
            _FIELDS["d"] = []
    return [(a["name"], a["tier"], s[0], s[1], s[2], tuple(s[3])) for a in _FIELDS["d"] if a.get("tier") in tiers for s in a.get("spawners", [])]


def norm(s):
    return re.sub(r"[^a-z]", "", (s or "").lower())


def kind_of(m):
    """The table's key for a mobile, as BotBase.mkey: its body species when the client knows it, else its name without the article."""
    return re.sub(r"[^a-z]", "", (getattr(m, "species", None) or re.sub(r"^(an?|the) ", "", (m.name or "").lower())).lower())


def avg(v, default=0.0):
    return (v[0] + v[1]) / 2.0 if v else default


def success(magery, start):
    return max(0.0, min(1.0, (magery - start) / 40.0))


def poison_ok(entry):
    """Lesser poison lands: the kind is not immune to it (an immunity of Lesser or stronger)."""
    return not (entry or {}).get("poison_immune")


def value(entry):
    e = entry or {}
    return float(e.get("gold", 0) or 0) + float(e.get("carve", 0) or 0) + sum(EXTRA_VALUE.get(x, 0) for x in e.get("extras", ()))


from items import is_leather  # noqa: E402,F401  (one test for every brain: items.py)


def fistable(entry):
    e = entry or {}
    return avg(e.get("hits"), 99) <= FIST_HITS and (e.get("damage") or [0, 0])[1] <= FIST_DAMAGE


def best_spell(magery, have=lambda s: True):
    """The spell with the least reagent gold per expected point of damage at this Magery, of the ones `have` allows (book, reagents): dict or None."""
    best = None
    for s in SPELLS:
        p = success(magery, s["start"])
        if p < MIN_SUCCESS or not have(s):
            continue
        g = s["cost"] / (p * s["damage"])
        if best is None or g < best[0]:
            best = (g, s, p)
    return best


def kill_cost(entry, magery, have=lambda s: True):
    """(reagent gold, method) for the cheapest kill of this kind."""
    e = entry or {}
    hits = avg(e.get("hits"), 30.0)
    if fistable(e):
        return 0.0, "fists"
    sp = best_spell(magery, have)
    gpd = sp[0] if sp else 1.0
    pp = success(magery, POISON["start"])
    if poison_ok(e) and pp >= MIN_SUCCESS and have(POISON):
        rest = max(0.0, hits - POISON_TICKS * POISON_TICK_DAMAGE)
        return POISON["cost"] / pp + rest * gpd, "poison" if rest <= 0 else "poison+" + (sp[1]["name"] if sp else "spell")
    return hits * gpd, sp[1]["name"] if sp else "none"


def net(entry, magery, have=lambda s: True):
    cost, method = kill_cost(entry, magery, have)
    return value(entry) - cost, cost, method


class ProfitMixin:
    # ---- the model, for this caster -----------------------------------------------------------------------------------------------------------------------

    def profit_on(self):
        return self.feature("caster_profit")

    def profit_have(self, s):
        """The spell is in the book and its reagents are in the pack (an unread book counts as holding it)."""
        ok = getattr(self, "spell_ok", lambda n: True)(s["name"])
        regs = getattr(self, "regs", None) or {}
        return ok and all(regs.get(r, 0) > 0 for r in s["reagents"]) if regs else ok

    def profit_entry(self, key):
        return table().get(norm(key))

    def ground_closed(self, x, y):
        """Ground the caster keeps off, by the fighters' measured rules: within a losing spawner's home range + 14 (hunter.in_losing_range: its kinds' measured
        nets for the caster group sum below zero, or it holds an unmeasured heavy kind), or the undead box north of Britain for a caster under 120 hit points
        (task_core.in_box). BotMageAdvBR died to an orc beside a wraith at 1465,1377, the box's edge, 3 minutes after the mages' start (2026-10-29)."""
        try:
            import hunter
            import task_core
            return bool(hunter.in_losing_range(self, x, y) or task_core.in_box(self, x, y, pad=task_core.PULL_CLEAR))
        except Exception:
            return False

    def profit_fight_value(self, key):
        """Gold a fight with this kind pays the caster: the casters' measured value (measured.net: kill_pct x the loot less the solo death cost) less the reagents
        a fight spends (profit_net's spell cost), else profit_net's value per kill for a kind with no measured record (2026-10-29: hinds and harts, killed in 6% of
        caster fights, scored their fields with the 26 gold a kill)."""
        r = self.profit_net(key)
        try:
            import measured
            if measured.entry(self, key) is not None:
                mv = measured.net(self, key)
                if mv is not None:
                    return mv - (r[1] if r else 0.0)
        except Exception:
            pass
        return r[0] if r else None

    def profit_net(self, key):
        """(net, cost, method) for a kill of this kind: the engine prior, with the measured value and cost in its place from LEARN_MIN kills on."""
        k = norm(key)
        e = self.profit_entry(k)
        if not e:
            return None
        n, cost, method = net(e, float(getattr(self, "skill", 0.0) or 0.0), self.profit_have)
        lv, lc = learned().get(k + "|v"), learned().get(k + "|c")
        if lv and lv[1] >= LEARN_MIN:
            c = lc[0] if lc and lc[1] >= LEARN_MIN else cost
            return lv[0] - c, c, method + " (learned)"
        return n, cost, method

    # ---- learning: what a kill really cost and brought ----------------------------------------------------------------------------------------------------

    def profit_spent(self, gold):
        f = getattr(self, "fight", None)
        if f is not None:
            f["spent"] = f.get("spent", 0.0) + gold

    def profit_snapshot(self):
        meat = sum((i.amount or 1) * items.sale_price(i.name) for i in self.c.backpack if items.is_meat(i.name))
        hides = sum((i.amount or 1) for i in self.c.backpack if items.is_hide(i.name))
        return {"gold": self.c.gold, "leather": self.profit_leather(), "hides": hides, "meat": meat}

    def profit_killed(self, f):
        """CasterBot.end_fight on a kill: what it cost now; what it brought is measured SETTLE s later (profit_settle)."""
        if not self.profit_on() or not f:
            return
        self.facts.setdefault("profit_pending", []).append({"m": f.get("key"), "cost": round(f.get("spent", 0.0), 2), "t": time.time(),
                                                            "before": self.profit_snapshot(), "sold": self.facts.get("leather_sold_at", 0) + self.facts.get("meat_sold_at", 0)})

    def profit_settle(self):
        """Record the kills whose SETTLE s have passed: value = gold picked up + leather (hides counted as leather) + meat, unless a sale moved the counts."""
        pend = self.facts.get("profit_pending") or []
        if not pend:
            return
        now, keep = time.time(), []
        for p in pend:
            if now - p["t"] < SETTLE:
                keep.append(p)
                continue
            if self.facts.get("leather_sold_at", 0) + self.facts.get("meat_sold_at", 0) != p["sold"] or self.c.ghost or not p.get("m"):
                continue                                      # a sale (or a death) in between: the counts say nothing about the kill
            b, a = p["before"], self.profit_snapshot()
            value = max(0, a["gold"] - b["gold"]) + 5 * max(0, a["leather"] - b["leather"] + a["hides"] - b["hides"]) + max(0, a["meat"] - b["meat"])
            try:
                import farmdb
                farmdb.rate_update(KV, p["m"] + "|v", value, LEARN_ALPHA)
                farmdb.rate_update(KV, p["m"] + "|c", p["cost"], LEARN_ALPHA)
                _LEARNED["t"] = 0.0
            except Exception as e:
                self.log(f"profit: could not record the kill ({type(e).__name__}: {e})")
            if value > 0:
                self.facts["profit_paid_at"] = now                # the field still pays (profit_field, patch_safe_fields)
            r = self.profit_net(p["m"]) or (0, 0, "")
            self.ev("profit_kill", m=p["m"], value=value, cost=p["cost"], net=round(value - p["cost"], 1), method=r[2], learned="learned" in r[2])
        self.facts["profit_pending"] = keep[-20:]

    # ---- grounds: hunt_spot scores spawners by net gold -------------------------------------------------------------------------------------------------

    def hunt_kind_value(self, kind):
        if not self.profit_on():
            return super().hunt_kind_value(kind)
        base_v, base_c = super().hunt_kind_value(kind)
        if base_c > 0:
            return 0.0, base_c                                # it cannot win that fight (the Knowledge model): still ruled out
        r = self.profit_net(kind["cls"])
        if r is None:
            return base_v, base_c
        n, cost, method = r
        if base_v == 0.0 and not self.profit_fightable(kind["cls"]):
            return 0.0, 0.0
        return (n / SCALE if n > 0 else 0.0), 0.0

    def hunt_gold_value(self, kind):
        if not self.profit_on():
            return super().hunt_gold_value(kind)
        return 0.0                                            # the gold is in hunt_kind_value's NET already

    def profit_fightable(self, cls):
        """A farm animal or deer (no prey to the old hunt values) that this caster wins against: the Knowledge model, else small and harmless."""
        e = self.profit_entry(cls) or {}
        try:
            m = self.k.monsters.get(cls)
            if m:
                from hunt import _Fake
                a = self.k.assess(_Fake(m.get("name") or cls), max(self.c.max_hp, 1), max(int(self.c.mana or 0), 50), getattr(self, "skill", 0.0),
                                  {r: 99 for r in ("SulfurousAsh", "SpidersSilk", "Nightshade", "MandrakeRoot", "Ginseng", "Garlic", "Bloodmoss", "BlackPearl")})
                if a.get("known"):
                    return bool(a.get("fight"))
        except Exception:
            pass
        return (e.get("damage") or [0, 99])[1] <= 10

    # ---- prey: best NET first; a kind that does not pay is left alone unless it is on the caster ---------------------------------------------------------

    def profit_prey(self, ps):
        if not self.profit_on():
            return ps
        scored = []
        for m in ps:
            key = kind_of(m)
            r = self.profit_net(key)
            n = r[0] if r else 0.0
            try:
                import measured
                e = measured.entry(self, key)
                mv = measured.net(self, key)
            except Exception:
                e, mv = None, None
            if e is not None and mv is not None:
                # the casters' own measured fights (prey_measured.json "caster", 2026-10-29): a fight pays kill_pct x the loot less the solo death cost and the
                # reagents it spends (profit_net's spell cost for a kill, spent by a lost fight too); per second of its median fight. profit_net alone was per KILL
                # and hinds and harts, killed in 6% of 13,000 caster fights each, ranked with cows (86%)
                cost = r[1] if r else 0.0
                ev = mv - cost
                # its time: the median fight and the walk there at the bot's own measured pace (task_core.walk_rate, tiles a minute). A rat paid 1.0 gold a fight
                # (4.7% killed in 7,817 caster fights) and 36 of 74 let-go fights in caster3 were rats walked to across a field
                try:
                    import task_core
                    walk = 60.0 * (m.distance or 0) / task_core.walk_rate(self)
                except Exception:
                    walk = 0.0
                ev *= self.profit_reach_share(key)
                per_s = ev / (max(1.0, float(e.get("ttk_p50") or 10.0)) + walk)
                if (m.distance or 0) > 2 and per_s < CASTER_RATE:
                    continue
                scored.append((-per_s, m.distance or 0, m))
                continue
            if n <= 0 and (m.distance or 0) > 2:
                continue                                      # it does not pay: not hunted (it is fought only when it comes to the caster)
            scored.append((-n, m.distance or 0, m))
        scored.sort(key=lambda t: (t[0], t[1]))
        return [m for _, _, m in scored]

    # ---- the fight -------------------------------------------------------------------------------------------------------------------------------------

    def profit_attack(self, m):
        """One action against m the cheapest way; True when it acted, None to leave it to the old attack."""
        if not self.profit_on():
            return None
        key = kind_of(m)
        e = self.profit_entry(key)
        if not e:
            return None
        if fistable(e):
            return self.profit_melee(m, "fists")
        poisoned = self.facts.setdefault("profit_poisoned", {})
        for s in [s for s, t in poisoned.items() if time.time() - t > POISON_SECS + 10]:
            del poisoned[s]
        magery = float(getattr(self, "skill", 0.0) or 0.0)
        pct = getattr(m, "hits", None)
        mhp = avg(e.get("hits"), 30.0)
        if poison_ok(e) and m.serial not in poisoned and success(magery, POISON["start"]) >= MIN_SUCCESS and self.profit_have(POISON) \
                and (self.c.mana or 0) >= POISON["mana"]:
            poisoned[m.serial] = time.time()
            self.log(f"profit: Poison at {m.name} (worth {value(e):.0f}): {POISON_TICKS} ticks of {POISON_TICK_DAMAGE:.0f}+ for 3 gold")
            self.profit_spent(POISON["cost"])
            self.profit_reached(m)
            return bool(self.cast("poison", m.serial)) or True
        if m.serial in poisoned:
            left = POISON_TICKS - (time.time() - poisoned[m.serial] - 3.5) / 3.0
            est = (pct / 100.0 * mhp) if isinstance(pct, (int, float)) and pct <= 100 else mhp - (POISON_TICKS - left) * POISON_TICK_DAMAGE
            if left > 0 and est <= left * POISON_TICK_DAMAGE + 2:
                return self.profit_melee(m, "poison")         # the poison finishes it: follow, and hit it for free while beside it
        sp = best_spell(magery, self.profit_have)
        if sp is None or (self.c.mana or 0) < sp[1]["mana"]:
            return self.profit_melee(m, "no spell")
        self.profit_spent(sp[1]["cost"])
        self.profit_reached(m)
        return bool(self.cast(sp[1]["name"], m.serial)) or True

    REACH_WINDOW = 3600.0

    def profit_reach_share(self, key):
        """Of this kind's last hour of fights by this caster, the share that were not let go unreached: kills / (kills + fights never reached). Penned chickens
        in South-west Farmlands were 121 let-go fights with no blow or spell landing in 3.5 hours (2026-10-29/30), each ~17 s with the walk."""
        now = time.time()
        out = []
        for k in ("kind_kills", "kind_unreached"):
            d = self.facts.setdefault(k, {})
            ts = [t for t in d.get(key, []) if now - t < self.REACH_WINDOW]
            d[key] = ts
            out.append(len(ts))
        kills, unreached = out
        return 1.0 if not unreached else kills / float(kills + unreached)

    def profit_reached(self, m):
        """The fight with m got to blows or a spell (in reach, in sight): a fight let go without it was one the caster never reached (caster.r_fight)."""
        f = getattr(self, "fight", None)
        if f and f.get("serial") == m.serial:
            f["reached"] = True

    def profit_melee(self, m, why):
        if not self.c.war_mode:
            self.c.war(True)
        if (m.distance or 0) > 1:
            self.c.goto(m.x, m.y).wait(timeout=3)
            return True
        self.profit_reached(m)
        self.c.attack(m.serial)
        time.sleep(1.2)
        return True

    # ---- carving and leather -----------------------------------------------------------------------------------------------------------------------------

    def profit_carve_kind(self, corpse_name):
        """The table key of a corpse ('a great hart corpse' -> 'greathart') when carving it pays, else None."""
        kind = items.corpse_kind(corpse_name)
        e = table().get(kind)
        return kind if e and (e.get("carve") or 0) > 0 else None

    def profit_take(self, contents):
        """From a carved corpse: the meat, and the hides while the weight allows (5 stones each). Returns (meat value, hides taken)."""
        meat_value, hides = 0, 0
        room = self.c.max_weight * 0.8 - self.c.weight
        for it in contents:
            n = it.amount or 1
            low = (it.name or "").lower()
            if items.is_meat(low):                             # "cut of raw ribs", "raw bird"
                if self.profit_get(it.serial, n):
                    meat_value += n * items.sale_price(low)
                    room -= n * items.unit_weight(low)
            elif items.is_hide(low) and room >= items.unit_weight(low):
                take = min(n, int(room // items.unit_weight(low)))
                if take > 0 and self.profit_get(it.serial, take):
                    hides += take
                    room -= take * items.unit_weight(low)
        return meat_value, hides

    def profit_get(self, serial, n):
        """Take from a corpse, waiting out the server's action delay: a pick-up 0.1 s after opening or carving is refused ("You must wait to perform another
        action."). True when the server did not refuse it (patch_pasture_harvest)."""
        journal = getattr(self, "read_journal", None) or (lambda: [])
        for attempt in range(4):
            time.sleep(1.1 if attempt == 0 else 1.3)
            self.c.events.drain()
            self.c.get_item(serial, n if n > 1 else None)
            time.sleep(0.6)
            if not any("must wait" in (line or "").lower() for line in journal()):
                return True
        self.log(f"profit: the server kept refusing a pick-up of {serial} (action delay)")
        return False

    def profit_cut(self):
        """Cut every pile of hides in the pack with the scissors (a hide becomes a leather, 5 stones to 1). True when it cut something."""
        scissors = next((i for i in self.c.backpack if "scissor" in (i.name or "").lower()), None)
        piles = [i for i in self.c.backpack if "hide" in (i.name or "").lower() and "spined" not in (i.name or "").lower()]
        if not scissors or not piles:
            return False
        from uo import Event
        for p in piles:
            got = False
            for attempt in range(2):                          # the action delay after the last pick-up refuses the scissors too (patch_pasture_harvest)
                time.sleep(1.1)
                self.c.events.drain()
                self.c.use(scissors.serial)
                if self.c.wait_for(Event.TARGET_REQUEST, timeout=4) is not None:
                    got = True
                    break
            if not got:
                return False
            self.c.target(p.serial)
            time.sleep(1.2)
        return True

    def profit_leather(self):
        # "cut up leather" is the item's name (norm: "cutupleather"), so the old test ("leather", "cutleather", "leathers") counted none: no caster ever sold
        # leather and kill values learned no leather (2026-10-29). errands.py's test, as the fighters sell it
        return sum((i.amount or 1) for i in self.c.backpack if is_leather(i.name))

    def r_sell_leather(self):
        """Leather to the Tanner when there is enough of it or the pack is heavy; raw hides that could not be cut to the Furtrader."""
        if not self.profit_on() or self.c.ghost or self.dangers(10):
            return False
        n = self.profit_leather()
        hides = sum((i.amount or 1) for i in self.c.backpack if "hide" in (i.name or "").lower())
        if not n and not hides:
            return False
        if (not self.sell_due()) if hasattr(self, "sell_due") else (n < LEATHER_SELL_AT and hides < 6 and self.c.weight < self.c.max_weight * 0.7):
            return False                                          # the derived sell batch (CasterBot.sell_due), one trip for the meat and the leather
        if time.time() - self.facts.get("leather_sold_at", 0) < 300:
            return False
        self.facts["leather_sold_at"] = time.time()
        xy = tuple(self.where1(("tanner", "furtrader", "leatherworker")))
        far = self.far_front(xy, "sell", 100, n + hides)
        if far:
            self.far_after(far, "sell")
            return True
        self.activity = f"selling {n} leather"
        self.c.goto(*xy).wait(timeout=100)
        gold0 = self.c.gold
        sold = 0
        for v in sorted([m for m in self.c.mobiles(within=8) if m.notoriety == "Innocent" and m.name and not m.name.startswith("Bot")], key=lambda m: m.distance)[:6]:
            rows = [mm for mm in (re.search(r"(0x[0-9A-Fa-f]+)\s+(\d+)gp\s+x(\d+)\s+(.+)", l) for l in self.vendor_list(v, "sell")) if mm]
            mine = [r for r in rows if int(r.group(2)) > 0 and (is_leather(r.group(4)) or norm(r.group(4)) in ("hides", "pileofhides"))]
            self.log(f"profit: sell list from {v.name}: {len(rows)} rows, {len(mine)} leather or hides")
            if mine:
                self.cmd("sell " + " ".join(f"{r.group(1)} {r.group(3)}" for r in mine), timeout=10)
                time.sleep(2.5)
                sold += sum(int(r.group(3)) for r in mine)
        got = max(0, self.c.gold - gold0)
        self.ev("leather_sold", n=sold, gold=got)
        self.log(f"profit: sold {sold} leather/hides for {got} gold")
        return True

    # ---- staying on a ground that pays -------------------------------------------------------------------------------------------------------------------

    # ---- fields: one safe field, then the next (patch_safe_fields) -------------------------------------------------------------------------------------

    def profit_field_tiers(self):
        t = tuple(getattr(self, "patrol_tiers", lambda: (1,))() or (1,))
        if float(getattr(self, "skill", 0.0) or 0.0) < CASTER_TIER2:
            return (1,)                                        # tier 2 comes in packs (patch_field_recheck)
        return (1, 2) if 2 in t else (1,)

    def profit_field_unsafe(self, f):
        """Why the field being worked is no longer one to work (out of its tiers, or a spawner it must not meet), else None; checked every RECHECK s."""
        now = time.time()
        if now - f.get("checked", 0) < RECHECK:
            return None
        f["checked"] = now
        armed = self.can_cast() if getattr(self, "can_cast", None) else True
        mine = [fl for fl in fields((1, 2, 3, 4)) if fl[0] == f["name"]]
        if mine and mine[0][1] not in self.profit_field_tiers():
            return f"unsafe now: {f['name']} is tier {mine[0][1]}"
        bad = next((fl for fl in mine if self.profit_spawner_veto(fl, armed)), None)
        if bad:
            return f"unsafe now: the spawner at {bad[2]},{bad[3]} ({', '.join(bad[5][:4])})"
        return None

    def profit_spawner_value(self, f, armed):
        """Mean net gold a kill at this spawner pays this caster (its kinds spawn alike), or None when the spawner is left out (see the patch note)."""
        name, tier, x, y, rng, kinds = f
        danger = tuple(getattr(self, "DANGER_KINDS", ())) + FIELD_BROKE_VETO
        meat_kinds = tuple(getattr(self, "MEAT_KINDS", ()))
        vals = []
        for k in kinds:
            if not armed and any(d in k for d in danger):
                return None
            e = self.profit_entry(k)
            if not e:
                vals.append(0.0)
                continue
            cls = e.get("class") or k
            base_v, base_c = super().hunt_kind_value({"cls": cls})   # HuntMixin's, whichever arm of the A/B this caster is in
            if base_c > 0:
                return None                                       # the Knowledge model: a fight it cannot win
            if not armed and not (fistable(e) or any(m in k for m in meat_kinds)):
                vals.append(0.0)
                continue
            fv = self.profit_fight_value(k)
            vals.append(fv if fv is not None and fv > 0 and (base_v > 0 or self.profit_fightable(cls)) else 0.0)
        v = sum(vals) / len(vals) if vals else 0.0
        if v <= 0:
            return None
        cell = self.profit_cell(x, y)
        mem = getattr(self, "mem", None)
        if cell and mem is not None:
            area = getattr(mem, "area", None)
            if area is not None and area.risky(cell):
                return None
            if getattr(mem, "dangerous_cell", None) and mem.dangerous_cell(cell):
                return None
        return v

    def profit_spawner_veto(self, f, armed):
        """True when the spawner holds what this caster must not meet: with no attack spell, the dangerous kinds; a kind it cannot win against; a risky
        cell. Its whole area is then no field (patch_field_veto)."""
        name, tier, x, y, rng, kinds = f
        danger = tuple(getattr(self, "DANGER_KINDS", ())) + FIELD_BROKE_VETO
        for k in kinds:
            if not armed and any(d in k for d in danger):
                return True
            e = self.profit_entry(k)
            if e and super().hunt_kind_value({"cls": e.get("class") or k})[1] > 0:
                return True
        cell = self.profit_cell(x, y)
        mem = getattr(self, "mem", None)
        if cell and mem is not None:
            area = getattr(mem, "area", None)
            if area is not None and area.risky(cell):
                return True
            if getattr(mem, "dangerous_cell", None) and mem.dangerous_cell(cell):
                return True
        return False

    @staticmethod
    def profit_cell(x, y):
        try:
            from memory import cell_of
            return cell_of(x, y)
        except Exception:
            return None

    def profit_areas(self, armed, here):
        """{area: {"score", "tier", "spots": [(x, y, value)], "load", "dist"}} for every area with a spawner worth working (see the patch note)."""
        out, vetoed = {}, set()
        for fl in fields(self.profit_field_tiers()):
            if fl[0] in vetoed:
                continue
            if self.ground_closed(fl[2], fl[3]):
                continue                                          # a losing spawner's reach or the undead box (the fighters' measured rules, 2026-10-29)
            if self.profit_spawner_veto(fl, armed):
                vetoed.add(fl[0])                                 # one spawner it must not meet: not this area at all (patch_field_veto)
                out.pop(fl[0], None)
                continue
            v = self.profit_spawner_value(fl, armed)
            if v is None:
                continue
            a = out.setdefault(fl[0], {"tier": fl[1], "spots": [], "load": 0, "dist": 99999})
            a["spots"].append((fl[2], fl[3], round(v, 1)))
            cell = self.profit_cell(fl[2], fl[3])
            if cell and getattr(self, "caster_load", None):
                a["load"] = max(a["load"], self.caster_load(cell))
            a["dist"] = min(a["dist"], max(abs(here[0] - fl[2]), abs(here[1] - fl[3])))
        for name in list(out):
            a = out[name]
            if a["load"] >= FIELD_CROWD:
                del out[name]                                     # two casters there already: a player looks for another field
                continue
            a["score"] = sum(s[2] for s in a["spots"]) / len(a["spots"]) / (1.0 + a["load"]) ** 2 / (1.0 + a["dist"] / FIELD_WALK)
        rates = field_rates()
        known = [rates[n] for n in out if n in rates]
        if known:
            mean = sum(known) / len(known)
            for n, a in out.items():
                if n in rates and mean > 0:
                    a["score"] *= rates[n] / mean                 # the field's own measured gold a minute, against the mean of the fields in reach
                    a["rate"] = round(rates[n], 1)
        return out

    def profit_field(self):
        """(x, y) to walk to: a spawner of the area being worked, else of the next area; None when no area scores (the old r_explore)."""
        now = time.time()
        here = (self.c.x, self.c.y)
        f = self.facts.get("profit_field")
        if f:
            if not f.get("arrived") and any(max(abs(here[0] - s[0]), abs(here[1] - s[1])) <= FIELD_NEAR for s in f["spots"]):
                f["arrived"] = now
            why = None
            if f.get("arrived"):
                paid = self.facts.get("profit_paid_at", 0) if self.profit_on() else self.facts.get("last_kill_at", 0)   # the control measures no kill value
                idle = now - max(f["arrived"], paid)
                empty = now - max(f["arrived"], f.get("prey_at", 0))
                if empty >= FIELD_EMPTY:
                    why = f"empty: no prey seen in {int(empty)} s"     # the owner: an empty field is left at once, not circled
                elif idle >= FIELD_STALE:
                    why = f"no paying kill in {int(idle)} s"
                elif now - f["arrived"] >= FIELD_MAX:
                    why = f"worked for {int(now - f['arrived'])} s: time to see another field"
            elif now - f["t"] >= FIELD_TRAVEL:
                why = f"not reached in {int(now - f['t'])} s"
            if why is None:
                why = self.profit_field_unsafe(f)                # a field chosen under older rules, or before the caster lost its reagents
            if why is None:
                import places
                return places.scatter(getattr(self, "name", ""), *f["spots"][f.get("i", 0)][:2], r=6)
            self.facts.setdefault("fields_worked", {})[f["name"]] = now
            self.facts["profit_field"] = None
            self.log(f"profit: leaving the field {f['name']}: {why}")
            self.ev("field_left", field=f["name"], why=why, mins=round((now - f["t"]) / 60, 1))
        armed = self.can_cast() if getattr(self, "can_cast", None) else True
        worked = {k: t for k, t in (self.facts.get("fields_worked") or {}).items() if now - t < FIELD_REST}
        self.facts["fields_worked"] = worked
        areas = {n: a for n, a in self.profit_areas(armed, here).items() if n not in worked}
        if not areas:
            return None
        near = {n: a for n, a in areas.items() if a["dist"] < FIELD_FAR}
        if near:
            areas = near
        ranked = sorted(areas.items(), key=lambda kv: -kv[1]["score"])[:FIELD_CHOICES]
        tot = sum(a["score"] for n, a in ranked)
        pick, acc = random.random() * tot, 0.0
        name, a = ranked[-1]
        for n, aa in ranked:                                      # the best few, in proportion to their scores: not every caster to the same field
            acc += aa["score"]
            if pick <= acc:
                name, a = n, aa
                break
        spots = [list(s) for s in a["spots"]]
        i = min(range(len(spots)), key=lambda j: max(abs(here[0] - spots[j][0]), abs(here[1] - spots[j][1])))
        self.facts["profit_field"] = {"name": name, "spots": spots, "i": i, "t": now, "arrived": None, "score": round(a["score"], 2)}
        self.log(f"profit: working the field {name} next (score {a['score']:.1f}, {len(spots)} spawners, {a['dist']} tiles, {a['load']} casters there, "
                 f"{'armed' if armed else 'no attack spell'}; others: {', '.join(n for n, x in ranked if n != name) or 'none'})")
        self.ev("field_chosen", field=name, score=round(a["score"], 2), armed=armed, tier=a["tier"], dist=a["dist"], load=a["load"],
                spawners=len(spots), others=[n for n, x in ranked if n != name])
        import places
        return places.scatter(getattr(self, "name", ""), *spots[i][:2], r=6)               # the first walk: near the spawner, not on the same tile as every bot (patch_scatter)

    def profit_field_prey(self):
        """Something to hunt in sight: prey by the caster's own test, or a farm animal or deer (a caster with no spell has no prey by that test)."""
        try:
            if self.prey(16):
                return True
        except Exception:
            pass
        meat = tuple(getattr(self, "MEAT_KINDS", ()))
        try:
            return any(m.notoriety == "Gray" and not getattr(m, "is_dead", False) and any(k in (m.name or "").lower() for k in meat)
                       for m in self.c.mobiles(within=16))
        except Exception:
            return False

    def profit_explore(self):
        """CasterBot.r_explore, every caster: walk to the field, then work all of it (a spawner of the area and a point near it, a new one every 40 s).
        False: the old r_explore."""
        xy = self.profit_field()
        if not xy:
            return False
        f = self.facts["profit_field"]
        x, y = xy
        if f.get("arrived"):
            if self.profit_field_prey():
                f["prey_at"] = time.time()                       # something to hunt in sight: the field is not empty
            p = f.get("p")
            if not p or time.time() - f.get("p_t", 0) > 40 or max(abs(self.c.x - p[0]), abs(self.c.y - p[1])) < 2:
                f["i"] = random.randrange(len(f["spots"]))           # the whole field, spawner to spawner, as a player walks it
                sx, sy = f["spots"][f["i"]][:2]
                p = f["p"] = [sx + random.randint(-FIELD_AROUND, FIELD_AROUND), sy + random.randint(-FIELD_AROUND, FIELD_AROUND)]
                f["p_t"] = time.time()
            x, y = p
            self.activity = f"working the field {f['name']}"
        else:
            self.activity = f"walking to the field {f['name']}"
        res = self.c.goto(x, y).wait(timeout=4)
        if not f.get("arrived") and res and str(res).startswith("nopath") and max(abs(self.c.x - x), abs(self.c.y - y)) > 40:
            f["t"] -= FIELD_TRAVEL                                  # no way there from here: given up at the next tick
        return True

    def profit_hold_spot(self):
        """Keep the current patrol spot past the 240 s turn while it pays: a kill in the last STAY_KILL s, for at most STAY_MAX."""
        if not self.profit_on() or getattr(self, "cur_spot", None) is None:
            return False
        now = time.time()
        held = self.facts.get("profit_hold")
        if not held or tuple(held[0]) != tuple(self.cur_spot):
            held = self.facts["profit_hold"] = [list(self.cur_spot), now]
        if now - self.facts.get("last_kill_at", 0) < STAY_KILL and now - held[1] < STAY_MAX:
            self.spot_since = now - 120                       # the 240 s turn starts over
            return True
        return False
