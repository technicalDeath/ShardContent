"""The stair hold: a caster's way to hunt a dungeon floor whose way out is a stair (owner, 2026-11-08/09: casters effective on Despise's top and bottom
levels, with "positioning, heals, potions, buffs and debuffs, all the tools at their disposal"). Mixin for CasterBot; nothing in it knows Despise.

Creatures never take a teleporter (Teleporter.OnMoveOver: `if (!Creatures && !m.Player) return`), and a dungeon's stair lands a player on the tile
beside the stair back (Despise: the stair 5504,569-571 lands on 5574,628-630, whose stair back 5573,628-630 lands on 5503,569-571; the ettin floor's
pair is the same). So a caster holds the floor's landing tile (the hold):
 * it fights what comes from there (r_stair: the focus target, Greater Heal when nothing is about to arrive, Heal beside one);
 * it fights in bouts: when HOP_SECS more of the health loss it measures (at first HOP_PRIOR a second for each attacker beside it) would leave it under HOP_FLOOR, or out of mana, it
   steps on the stair (the hop: one tile);
 * on the far side, where nothing followed, it heals with spells, meditates to UP_HP / UP_MANA, casts Reactive Armor, and steps back up. What it left
   at the top is still there: a creature's AI stops when no player is within two sectors (Map.SectorActiveRange, BaseCreature.OnSectorDeactivate, no
   SeeksHome), so the camp is worn down bout by bout (it regains 1 a 2 s each, about 15 over a 30-second rest: a meditating caster with Meditation
   95 and Int 100 gains 1.9 mana a second, RegenRates before AOS);
 * with nothing in sight it walks out toward the spawn until one sees it (the lure: a creature sees 16 tiles, BaseCreature.DefaultRangePerception) and
   comes back to the hold before it arrives (a rider 0.1 s a tile, a Medium chaser such as a lizardman 0.2).
And it opens on a fresh target with Poison (hold_poison): before AOS Lesser poison is at least 4 a tick for 10 ticks, 3 s apart (PoisonKinds.cs), about
40 damage for 9 mana and a nightshade, and it ticks on while the caster heals below the stair; a lizardman (58-72 hits) regains 1 a 2 s
(RegenRates: 10 / (1 + 4) s a point), which a hop's wait otherwise hands back.
The danger rules (r_dungeon_out, r_flee, r_avoid) ran the casters away from the stair, not onto it: 25 caster deaths in about 23 Despise stays and no
lizardman killed (2026-11-09 08:22-14:00); BotSorcBR, put back up by its own exit walk at the landing, kited 17 tiles from the stair beside six lizardmen
and died (13:45-13:46). r_stair runs before them. Events: hold_set {spot, post, stair}, stair_hop {why, hp, adj, n, ok, crowd}, stair_up {hp, mana,
waited, ok}, lure {to, seen}.
"""
from __future__ import annotations

import time

HOLD_PULL = 44                # tiles from the stair to the spawn's centre at most: the lure's LURE_MAX, a creature's sight of 16 and a home of 12
HOLD_R = 1                    # tiles from the hold it fights within
HOLD_PACK = 2                 # monsters the hold fights at once (more beside it, and it hops): spots.spawn_ok rates this pack for a held spot
HOP_HP = 45                   # percent health under which it hops with nothing beside it
HOP_FLOOR = 30                # beside attackers it hops when HOP_SECS more of the bout's measured loss would leave it under this percent
HOP_SECS = 3.0                # s: a cast under way (Magic Arrow 0.75 + 0.9 of the client's wait) and the step through
HOP_LOOK = 4.0                # s of health readings the bout's loss is measured over
HOP_PRIOR = 1.2               # hp a second for each attacker beside it before there are readings: the rating's standing intake for a lizardman on a
                              # caster (5-7 scaled by its tactics and strength, halved on a player, about 4 a blow; a 2.6 s swing, 15000 / ((dex + 100) x 30);
                              # 65% landing), as the logs show it (BotWarlockAR, 93 to 15 in 16 s beside six, 2026-11-09 12:05)
HOP_TOP = 85                  # the line at most
RA_LOCK = 60.0                # s after Reactive Armor before it is cast again below (DefensiveSpell.Nullify's lockout once the pool is spent)
HOP_REACH = 30                # tiles from the stair within which the hold's rule acts (walks back to the hold, or to the stair and through): a lure's end
                              # and the walk round a corner past it (BotMageAR's lure stopped 20 out, 2026-11-09 17:01)
NOLOS_S = 15.0                # s a target out of sight from the hold is waited for, then left for NOLOS_SKIP s (it stands behind a wall)
NOLOS_SKIP = 60.0
UP_HP = 90                    # percent health to go back up
UP_MANA = 0.8                 # share of its mana to go back up
BELOW_MIN = 6.0               # s below at least (the world view settles; the stale pack is not a pack below)
CROWD_S = 4.0                 # a hop this soon after arriving at the hold is a crowded top
CROWD_WAIT = BELOW_MIN        # (a frozen camp does not clear: no longer waited for)
CROWD_MAX = 6                 # bouts in a row shorter than CROWD_S that rest the spot "danger" (a camp too big to wear down)
LURE_WAIT = 12.0              # s at the hold with nothing in sight before a lure walk
LURE_MAX = 16                 # tiles a lure walks out from the hold (the straight line, when no route is known)
LURE_PATH = 20                # tiles along the walk graph's route toward the spawn a lure walks
LURE_SLICE = 2.5              # s a lure slice runs before the rules look again
LURE_PULL = 10                # tiles within which an idle one at the lure's end is pulled with a Magic Arrow (a targeted spell's range before AOS)
POISON_MIN_HITS = 40          # a kind's average hit points at least for the Poison opener (less dies to one Lightning sooner than to the ticks)
POISON_SECS = 33.0            # s a Lesser poison runs: 3.5 s delay + 10 ticks x 3 s (PoisonKinds.cs, before AOS)


def cheb(a, b):
    return max(abs(int(a[0]) - int(b[0])), abs(int(a[1]) - int(b[1])))


_GEO = {}


def hold_geometry(side, centre):
    """The hold for a spot on `side` centred at `centre`: the nearest outward stair on its walkable component (spots.outward_stairs) within HOLD_PULL,
    with its stair back from the far side. {"stair": [src tiles on this floor], "back": [src tiles on the far side], "post": the far side's landing
    here beside the stair's middle tile, "below": the stair's landing over there}; None without such a pair."""
    key = (side, int(centre[0]), int(centre[1]))
    if key in _GEO:
        return _GEO[key]
    out = None
    try:
        import gazetteer
        import spots
        near = spots.outward_stairs(side, centre, HOLD_PULL)
        if near:
            t = near[0][1]
            trans = gazetteer.get().trans
            run = sorted([x for x in trans if x.get("src_side") == side and x.get("dst_side") == t.get("dst_side")
                          and cheb(x["src"], t["src"]) <= 2 and cheb(x["dst"], t["dst"]) <= 2], key=lambda x: (x["src"][0], x["src"][1]))
            back = [x for x in trans if x.get("src_side") == t.get("dst_side") and x.get("dst_side") == side
                    and cheb(x["src"], t["dst"]) <= 2 and cheb(x["dst"], t["src"]) <= 2]
            if run and back:
                mid = run[len(run) // 2]
                b = min(back, key=lambda x: (cheb(x["dst"], mid["src"]), abs(int(x["dst"][0]) - int(mid["src"][0])) + abs(int(x["dst"][1]) - int(mid["src"][1]))))
                post = (int(b["dst"][0]), int(b["dst"][1]))
                if cheb(post, centre) <= HOLD_PULL + 2:
                    posts = sorted({(int(x["dst"][0]), int(x["dst"][1])) for x in back}, key=lambda p: (cheb(p, post), p))
                    out = {"side": side, "stair": [(int(x["src"][0]), int(x["src"][1])) for x in run],
                           "back": [(int(x["src"][0]), int(x["src"][1])) for x in back],
                           "post": post, "posts": posts, "below": (int(mid["dst"][0]), int(mid["dst"][1]))}
    except Exception:
        out = None
    _GEO[key] = out
    return out


class StairHoldMixin:

    # ---- where ----------------------------------------------------------------------------------------------------------------------------------------

    def hold_for(self, spot):
        side = spot.get("side") or (self.facts.get("dungeon_hunt") or {}).get("side")
        if not side or side == "surface":
            return None
        return hold_geometry(side, (int(spot["x"]), int(spot["y"])))

    def cd_post(self, spot):
        """A spot with a hold: the hold is its post (castdungeon.cd_post's line to the stair otherwise)."""
        h = self.hold_for(spot)
        if h:
            return h["post"]
        return super().cd_post(spot)

    def cd_spawn_ok(self, s):
        """castdungeon's spot test, and in a dungeon only a spot with a hold: from anywhere else a caster stands where the pack can box it in, far from
        any stair (0 lizardmen killed and 25 deaths at Despise's unheld posts, 2026-11-09 08:22-14:00; BotSorcBR's pick sp5503,529 lay 41 tiles from
        its stair's landing and it died the old way at 14:53)."""
        if s.get("side") not in (None, "surface") and not self.hold_for(s):
            return False
        return super().cd_spawn_ok(s)

    def cd_hold_pack(self, s):
        """spots.spawn_ok's pack for a held spot: HOLD_PACK of its kinds (the hold hops off more), else None."""
        return HOLD_PACK if self.hold_for(s) else None

    def hold_now(self):
        """The running stay's hold (castdungeon's spot), or None."""
        if not self.facts.get("dungeon_hunt") or getattr(self.c, "ghost", False):
            return None
        st = self.cd_state()
        spot = st.get("spot")
        if not spot:
            return None
        if "hold" not in st:
            st["hold"] = self.hold_for(spot)
            if st["hold"]:
                self.ev("hold_set", spot=spot["id"], post=list(st["hold"]["post"]), stair=list(st["hold"]["stair"][0]))
        return st["hold"]

    def holding(self, h=None):
        h = h or self.hold_now()
        here = (self.c.x, self.c.y)
        return bool(h) and any(cheb(here, p) <= HOLD_R for p in (h.get("posts") or [h["post"]]))

    def hold_post(self, h):
        """The landing tile to hold: the one it stands on or beside, else a free one (a shared hold: one caster a tile), the middle first."""
        posts = h.get("posts") or [h["post"]]
        here = (int(self.c.x), int(self.c.y))
        if any(here == tuple(p) for p in posts):
            return here
        return tuple(self.free_tile(posts))

    def hold_attackers(self, within):
        """kite_attackers by the bot's own position (a mobile's distance can be a snapshot behind a hop)."""
        here = (int(self.c.x), int(self.c.y))
        return [m for m in self.kite_attackers(within + 2) if getattr(m, "x", None) is not None and cheb((m.x, m.y), here) <= within]

    # ---- the rule -------------------------------------------------------------------------------------------------------------------------------------

    def r_stair(self):
        h = self.hold_now()
        if not h:
            return False
        hs = self.__dict__.setdefault("_hold", {})
        now = time.time()
        here = (int(self.c.x), int(self.c.y))
        if cheb(here, h["below"]) <= 4:
            return self.hold_below(h, hs, now)
        if min(cheb(here, s) for s in h["stair"]) > HOP_REACH:
            return False
        skip = hs.setdefault("nolos_skip", {})
        seen = [m for m in self.hold_attackers(16) if float(skip.get(m.serial, 0) or 0) < now]
        att = [m for m in seen if cheb((m.x, m.y), here) <= 10]
        coming = [m for m in seen if getattr(m, "in_war_mode", False) and m not in att]
        hist = hs.setdefault("hp_hist", [])
        hist.append((now, float(self.c.hp or 0)))
        while hist and now - hist[0][0] > HOP_LOOK:
            hist.pop(0)
        if not att and not coming:
            return False
        self.cd_state()["seen"] = now                             # castdungeon's empty timer and the lure's
        adj = [m for m in att if cheb((m.x, m.y), here) <= 1]
        why = self.hop_due(att, adj)
        if why:
            return self.hold_hop(h, hs, why, att, adj, now)
        if not self.holding(h):
            self.activity = "back to the stair hold"
            p = self.hold_post(h)
            try:
                self.c.gotoexact(p[0], p[1]).wait(timeout=1.5)
            except Exception:
                pass
            return True
        if not att:
            self.activity = f"holding the stair: {coming[0].name} coming"
            time.sleep(0.4)
            return True
        return self.hold_fight(att, adj, hs, now)

    def hop_due(self, att, adj):
        """Why the hold hops now, or None."""
        if not att:
            return None
        hp = self.hp_pct()
        mhp = float(getattr(self.c, "max_hp", 0) or 100) or 100.0
        line = HOP_FLOOR + 100.0 * max(self.hold_intake(), HOP_PRIOR * len(adj)) * HOP_SECS / mhp
        if adj and hp < min(HOP_TOP, line):
            return f"health beside {len(adj)}"
        if not adj and hp < HOP_HP:
            return "health"
        if (self.c.mana or 0) < 4:
            return "mana"
        return None

    def hold_intake(self):
        """Hit points a second lost over the last HOP_LOOK s of readings at the top (r_stair keeps them), 0 with under a second of them."""
        hist = (self.__dict__.get("_hold") or {}).get("hp_hist") or []
        if len(hist) < 2 or hist[-1][0] - hist[0][0] < 1.0:
            return 0.0
        return max(0.0, (hist[0][1] - hist[-1][1]) / (hist[-1][0] - hist[0][0]))

    def hold_fight(self, att, adj, hs=None, now=None):
        """At the hold: heal when it fits, else a spell at the focus target (CasterBot.attack: the window, Reactive Armor, the Poison opener)."""
        try:
            from castfight import KITE_MARGIN, cast_delay
        except Exception:
            KITE_MARGIN, cast_delay = 0.25, (lambda c: 0.5 + 0.25 * (c or 1))
        hp = self.hp_pct()
        mana = self.c.mana or 0
        if hp < 70 and not adj and self.contact_s(att) >= cast_delay(4) + KITE_MARGIN and mana >= 11 and self.spell_ok("greater heal") and self.gh_regs():
            self.activity = "holding the stair: greater heal"
            self.cast("greater heal", "self")
            return True
        t = self.focus_order(att)[0]
        if int(getattr(t, "distance", 9) or 9) > 1 and not self.los(t.serial):
            if hs is not None:
                first = hs.setdefault("nolos", {}).setdefault(t.serial, now)
                if now - first > NOLOS_S:
                    hs["nolos"].pop(t.serial, None)
                    hs.setdefault("nolos_skip", {})[t.serial] = now + NOLOS_SKIP
            self.activity = f"holding the stair: {t.name} not in sight yet"
            time.sleep(0.5)
            return True
        if hs is not None:
            hs.setdefault("nolos", {}).pop(t.serial, None)
        if not self.c.war_mode:
            self.c.war(True)
        self.activity = f"holding the stair: {t.name}"
        self.last_rule = "r_stair"
        if not self.attack(t):
            time.sleep(0.5)
        return True

    def hold_strike(self, m):
        """mage_bot.r_fight's step_away from an adjacent target, at the hold: the hop when due, else a spell at it (first circle beside it: the
        castfight window). True."""
        if self.hold_kite(self.kite_attackers()):
            return True
        if not self.attack(m):
            time.sleep(0.5)
        return True

    def hold_kite(self, att):
        """castfight.kite_away at the hold: the hop when due (True when it went), else False (stand and cast: it is one step from safety); None when
        not holding (kite as before)."""
        h = self.hold_now()
        if not h or not self.holding(h):
            return None
        here = (int(self.c.x), int(self.c.y))
        att = [m for m in (att or []) if getattr(m, "x", None) is not None and cheb((m.x, m.y), here) <= 10]
        adj = [m for m in att if cheb((m.x, m.y), here) <= 1]
        why = self.hop_due(att, adj)
        if not why:
            return False
        return self.hold_hop(h, self.__dict__.setdefault("_hold", {}), why, att, adj, time.time())

    def free_tile(self, tiles):
        """The nearest of tiles no mobile stands on, else the nearest."""
        here = (int(self.c.x), int(self.c.y))
        try:
            taken = {(int(m.x), int(m.y)) for m in self.c.mobiles(within=6) if getattr(m, "x", None) is not None}
        except Exception:
            taken = set()
        order = sorted(tiles, key=lambda s: cheb(s, here))
        return next((s for s in order if tuple(s) not in taken), order[0])

    def hold_hop(self, h, hs, why, att, adj, now):
        here = (int(self.c.x), int(self.c.y))
        t = self.free_tile(h["stair"])
        self.activity = f"stepping through the stair ({why})"
        try:
            self.tele_allow(h["side"])
        except Exception:
            pass
        if hasattr(self, "sprint"):
            try:
                self.sprint()
            except Exception:
                pass
        try:
            if cheb(here, t) > 1:
                self.c.goto(t[0], t[1]).wait(timeout=2.5)
            if cheb((self.c.x, self.c.y), h["below"]) > 4:
                self.c.gotoexact(t[0], t[1]).wait(timeout=2.5)
        except Exception:
            pass
        ok = cheb((self.c.x, self.c.y), h["below"]) <= 4
        hs["hp_hist"] = []
        crowd = now - float(hs.get("up_at", 0) or 0) < CROWD_S
        hs["crowds"] = (int(hs.get("crowds", 0)) + 1) if crowd else 0
        if ok:
            hs["below_since"] = time.time()
            hs["crowd"] = crowd
        self.ev("stair_hop", why=why, hp=self.hp_pct(), adj=len(adj), n=len(att), ok=ok, crowd=crowd)
        if self.fight:
            self.end_fight("lost")
        if hs["crowds"] >= CROWD_MAX:
            spot = self.cd_state().get("spot")
            if spot:
                self.log(f"stair hold: {hs['crowds']} crowded tops in a row at {spot['id']}: that ground is given up for now")
                self.cd_rest(spot["id"], "danger")
                self.__dict__.pop("_cd", None)
            hs.clear()
        return True

    def hold_below(self, h, hs, now):
        """On the far side of the hold's stair: heal, meditate, wait, step back up."""
        hs.setdefault("below_since", now)
        waited = now - float(hs["below_since"])
        if waited < 2.0:
            self.activity = "below the stair"
            time.sleep(0.6)                                     # the world view settles before anything below counts
            return True
        if self.hold_attackers(10) or self.c.poisoned:
            return False                                        # something down here, or poison: the usual rules (r_cure is earlier)
        hp = self.hp_pct()
        mana = self.c.mana or 0
        mmax = self.c.state.get("maxMana") or 0
        if hp < UP_HP:
            if mana >= 11 and self.spell_ok("greater heal") and self.gh_regs():
                self.activity = "below the stair: greater heal"
                self.cast("greater heal", "self")
                return True
            if mana >= 4 and self.spell_ok("heal") and self.heal_regs():
                self.activity = "below the stair: heal"
                self.cast("heal", "self")
                return True
        if (mmax and mana < UP_MANA * mmax) or hp < UP_HP:
            if self.c.war_mode:
                self.c.war(False)
            self.activity = f"below the stair: meditating ({mana}/{mmax})"
            if now > float(self.facts.get("med_until", 0) or 0):
                self.cmd("useskill meditation")
                self.facts["med_until"] = now + 12
                time.sleep(1.0)
            else:
                time.sleep(2.0)
            return True
        if now - float(self.facts.get("ra_at", 0) or 0) >= RA_LOCK and mana >= 8 and self.spell_ok("reactive armor") \
                and all((getattr(self, "regs", {}) or {}).get(r, 0) > 0 for r in ("Garlic", "SpidersSilk", "SulfurousAsh")):
            # Reactive Armor before the bout: the camp's blows go into its pool first
            self.facts["ra_at"] = now
            self.ra_until = now + 240.0
            self.activity = "below the stair: reactive armor"
            self.ev("buff", spell="reactive armor", mana=int(mana), where="below")
            self.cast("reactive armor", None)
            return True
        wait_for = CROWD_WAIT if hs.get("crowd") else BELOW_MIN
        if waited < wait_for:
            self.activity = f"below the stair: letting the top clear ({int(wait_for - waited)} s)"
            time.sleep(min(2.0, wait_for - waited))
            return True
        here = (int(self.c.x), int(self.c.y))
        t = self.free_tile(h["back"])
        self.activity = "back up the stair"
        try:
            self.tele_allow(h["side"])
        except Exception:
            pass
        try:
            if cheb(here, t) > 1:
                self.c.goto(t[0], t[1]).wait(timeout=2.5)
            if cheb((self.c.x, self.c.y), h["post"]) > 3:
                self.c.gotoexact(t[0], t[1]).wait(timeout=2.5)
        except Exception:
            pass
        ok = min(cheb((self.c.x, self.c.y), p) for p in (h.get("posts") or [h["post"]])) <= 3
        self.ev("stair_up", hp=hp, mana=mana, waited=round(waited), ok=ok)
        if ok:
            hs["up_at"] = time.time()
            hs.pop("below_since", None)
            hs["crowd"] = False
        return True

    def hold_lure(self, st, spot, now):
        """castdungeon.r_cdungeon at the post, nothing in sight for LURE_WAIT: a slice of the walk out toward the spawn (LURE_MAX tiles), until one sees it
        (r_stair then walks it back to the hold). True when it walked."""
        h = st.get("hold")
        if not h:
            return False
        if st.get("lure_to") is None and (now - float(st.get("seen", now)) < LURE_WAIT or now - float(st.get("lure_end", 0) or 0) < LURE_WAIT):
            return False
        p, c = h["post"], (int(spot["x"]), int(spot["y"]))
        d = cheb(p, c) or 1
        to = tuple(st["lure_to"]) if st.get("lure_to") else (tuple(st["lure_route_to"]) if st.get("lure_route_to") else self.lure_route_point(p, c))
        if to is not None:
            st["lure_route_to"] = list(to)
        try:
            import spots
            comp = spots.component_near(p[0], p[1], h["side"])
            for k in ((LURE_MAX, LURE_MAX - 4, LURE_MAX - 8) if to is None else ()):
                f = min(1.0, k / float(d))
                q = (int(round(p[0] + (c[0] - p[0]) * f)), int(round(p[1] + (c[1] - p[1]) * f)))
                if comp is None or spots.component_near(q[0], q[1], h["side"]) == comp:
                    to = q
                    break
        except Exception:
            to = None
        if to is None:
            return False
        here = (int(self.c.x), int(self.c.y))
        seen = self.hold_attackers(16)
        if any(getattr(m, "in_war_mode", False) for m in seen):
            st["lure_end"] = now                                # one has noticed it: r_stair walks it back to the hold before it arrives
            st.pop("lure_to", None)
            self.ev("lure", to=list(to), seen=True)
            return False
        if cheb(here, to) <= 1:
            st["lure_end"] = now
            st.pop("lure_to", None)
            idle = [m for m in seen if cheb((m.x, m.y), here) <= LURE_PULL and self.los(m.serial)]
            if idle and (self.c.mana or 0) >= 4 and self.spell_ok("magic arrow"):
                # one in sight that has not noticed it (a creature at rest in its home): a Magic Arrow brings it (first circle, 4 mana)
                self.activity = f"pulling {idle[0].name} toward the stair"
                self.ev("lure", to=list(to), seen=True, pull=True)
                self.cast("magic arrow", idle[0].serial)
                return True
            self.ev("lure", to=list(to), seen=False)            # out and nothing came: back to the hold (r_cdungeon's walk), the next after LURE_WAIT
            return False
        self.activity = f"luring {spot['id']}'s spawn toward the stair"
        if st.get("lure_to") is None:
            st["lure_to"] = list(to)
            st["lure_t0"] = now
        elif now - float(st.get("lure_t0", now) or now) > LURE_MAX * 1.5:
            st["lure_end"] = now                                # the point is not reached in a slow walk's time: given up, back to the hold
            st.pop("lure_to", None)
            self.ev("lure", to=list(to), seen=False, stuck=True)
            return False
        try:
            self.c.goto(to[0], to[1]).wait(timeout=LURE_SLICE)
        except Exception:
            pass
        return True

    def lure_route_point(self, p, c):
        """The point LURE_PATH tiles along the walk graph's route from the hold p toward the spawn's centre c (walkroute.plan), within HOP_REACH of
        the hold; None without a route."""
        try:
            import walkroute
            r = walkroute.get().plan((int(p[0]), int(p[1])), (int(c[0]), int(c[1])), None, step=4)
            wps = [tuple(int(v) for v in q[:2]) for q in (r or {}).get("waypoints") or []]
        except Exception:
            return None
        walked, last = 0, tuple(p)
        for q in wps:
            walked += cheb(last, q)
            last = q
            if walked >= LURE_PATH or cheb(q, p) >= HOP_REACH - 4:
                return q
        return wps[-1] if wps else None

    # ---- the Poison opener ----------------------------------------------------------------------------------------------------------------------------

    def hold_poison(self, m):
        """On a dungeon stay: Poison first on a target not poisoned in the last POISON_SECS (by this caster), of a kind not immune to Lesser poison
        (loot_value.json, profit.poison_ok) with POISON_MIN_HITS or more, still over half health, when the cast ends before an attacker arrives
        (castfight.contact_s; a circle-3 spell is ruined by a blow). True when it cast."""
        if not self.facts.get("dungeon_hunt"):
            return False
        try:
            import profit
            from castfight import KITE_MARGIN, cast_delay
            e = self.profit_entry(profit.kind_of(m))
            if not e or not profit.poison_ok(e) or profit.avg(e.get("hits"), 0.0) < POISON_MIN_HITS:
                return False
            if (getattr(m, "max_hits", 0) or 0) > 0 and float(m.hp_pct) < 50:
                return False
            poisoned = self.facts.setdefault("profit_poisoned", {})
            now = time.time()
            for s in [s for s, t in poisoned.items() if now - t > POISON_SECS]:
                del poisoned[s]
            if m.serial in poisoned:
                return False
            if not self.spell_ok("poison") or not self.profit_have(profit.POISON) or (self.c.mana or 0) < profit.POISON["mana"] + 4:
                return False
            if profit.success(float(getattr(self, "skill", 0.0) or 0.0), profit.POISON["start"]) < profit.MIN_SUCCESS:
                return False
            if self.contact_s(self.kite_attackers()) < cast_delay(3) + KITE_MARGIN:
                return False
        except Exception:
            return False
        poisoned[m.serial] = now
        self.log(f"poison at {m.name} ({m.distance} tiles): 10 ticks of 4+ while the fight goes on")
        self.cast("poison", m.serial)
        return True
