"""How a caster fights melee monsters (owner, 2026-11-08: "get casters to the point where they can hunt in the top and bottom levels of despise effectively.
they'll need to use positioning, heals, potions, consider buffs (spells) and debuffs, all the tools at their disposal"). Mixin for CasterBot; generic for
any ground: nothing in it knows Despise.

The engine's rules before AOS (ModernUO, the shard's UOR era):
 * a cast holds the caster still for 0.5 + 0.25 x (circle - 1) s (MagerySpell.GetCastDelay; Spell.BlocksMovement while casting); the 0.75 s recovery after it
   (Spell.NextSpellDelay) does not, so the caster may run between casts;
 * a blow taken while casting ruins the spell (Spell.OnCasterHurt), except a first-circle spell (Spell.cs: never disturbed by damage before AOS);
 * targeted spells reach 10 tiles (ITargetingSpell.TargetRange, T2A) and need line of sight;
 * a melee monster chases at its npc-speeds step (an ettin 0.6 s a tile, a lizardman or troll 0.45, casterpass.move_s); a player runs a tile in 0.2 s on
   foot, 0.1 mounted;
 * Reactive Armor absorbs (Magery + Meditation + Inscription) / 3 points of melee damage, at most 75, and holds until spent (ReactiveArmor.cs, UOR);
 * Heal is first circle (never disturbed); Greater Heal (fourth) heals more but a blow ruins it.

So the caster KITES: it casts only when no attacker can reach it before the cast ends (each attacker's tiles to contact x its step against the cast
delay), picks the strongest spell whose cast fits the time it has, and otherwise runs away from the pack for a moment; it puts Reactive Armor up when a
fight starts; it heals with Greater Heal out of reach and with Heal or a potion beside an attacker. Events: kite_step {n, near, from, to}, kite_fight
{kind, secs, dmg, stand_lost, kites} at each fight's end (the measure of rating.json's kite_leak), buff {spell}.
"""
from __future__ import annotations

import math
import time

KITE_MARGIN = 0.25            # s of slack between a cast's end and the first attacker's arrival (one step of a runner)
KITE_DIST = 6                 # tiles a kite step runs away from the pack
KITE_SEE = 10                 # tiles within which an attacker counts (the spell range: nothing beyond it is being fought)
RA_GAP = 240.0                # s between Reactive Armor casts (it holds until spent; recast after a fight has likely used it)
CASTS_TTL = 5.0               # s a casts_now reading holds (rating.bot_numbers asks it for every rating)
HEAL_OUT = 65                 # percent health under which a caster with nothing beside it casts Greater Heal
HEAL_IN = 50                  # percent under which a caster with an attacker beside it casts Heal (first circle, never ruined) or drinks
GH_MANA = 11
HEAL_MANA = 4


def cast_delay(circle):
    """Seconds a cast of this (1-based) circle holds the caster still: MagerySpell.GetCastDelay before AOS."""
    return 0.5 + 0.25 * (max(1, int(circle or 1)) - 1)


def on_teleporter(p):
    """p is a teleporter's tile or beside one (gazetteer transitions): Teleport lands on no teleporter (BotSorcBR's seven aims at Despise's stair tile
    5503,571 all failed, 2026-11-09 07:34), and the stair is walked onto instead."""
    try:
        import gazetteer
        return any(max(abs(int(t["src"][0]) - int(p[0])), abs(int(t["src"][1]) - int(p[1]))) <= 1 for t in gazetteer.get().trans)
    except Exception:
        return False


class CasterFightMixin:

    # ---- who is coming, and how soon ------------------------------------------------------------------------------------------------------------

    def kite_on(self):
        """The rating's kite model (rating.kite_factor) applies to this caster: feature caster_kite_rated (kept off until rating.json's kite_leak is
        measured from the kite_fight events)."""
        try:
            return bool(self.feature("caster_kite_rated"))
        except Exception:
            return False

    def kite_attackers(self, within=KITE_SEE):
        """Monsters that will close on it: attack-on-sight kinds and anything in war mode, within `within` tiles."""
        try:
            import task_core
            from bot_common import BotBase
            return [m for m in self.mobs(within) if not getattr(m, "is_dead", False)
                    and (getattr(m, "in_war_mode", False) or task_core.aggressive(BotBase.mkey(m)))]
        except Exception:
            return []

    def step_s(self, m):
        """Seconds a tile this monster chases at (casterpass.move_s), None for one that never moves."""
        try:
            import casterpass
            import danger
            from bot_common import BotBase
            k = BotBase.mkey(m)
            return casterpass.move_s(k, danger.stats().get(k) or {})
        except Exception:
            return 0.45

    def contact_s(self, attackers=None):
        """Seconds until the first attacker stands beside it (reach 1), if the caster stood still: min over attackers of (tiles - 1) x its step."""
        best = math.inf
        for m in (self.kite_attackers() if attackers is None else attackers):
            s = self.step_s(m)
            if s is None:
                continue
            d = max(0, int(getattr(m, "distance", 9) or 9) - 1)
            best = min(best, d * s)
        return best

    # ---- the spell that fits ----------------------------------------------------------------------------------------------------------------------

    def castfight_prep(self):
        """Filter the attack options by the time the caster has: an option whose cast would end with an attacker beside it is dropped (once)."""
        k = getattr(self, "k", None)
        if k is None or self.__dict__.get("_kite_orig") is not None:
            return
        self.__dict__["_kite_orig"] = k.attack_options
        bot = self

        def attack_options(skill, mana, regs, min_success=0.5):
            opts = bot.__dict__["_kite_orig"](skill, mana, regs, min_success)
            window = bot.__dict__.get("_kite_window")
            if window is None:
                return opts
            # a first-circle spell is cast even beside an attacker: no blow disturbs it before AOS (Spell.OnCasterHurt passes firstCircle false, Spell.Disturb
            # returns for a first-circle MagerySpell). With all spells dropped, BotSorcBR stood boxed beside one lizardman casting nothing but Teleport
            # ("no spell the mage can cast now", Despise, 2026-11-09 07:34)
            return [o for o in opts if o["spell"].get("circle") == 1 or cast_delay(o["spell"].get("circle")) + KITE_MARGIN <= window]

        k.attack_options = attack_options

    def kite_before_cast(self, target):
        """Called before an attack spell: sets the cast window from the attackers' time to contact, and runs instead when no spell fits. True when it ran."""
        self.castfight_prep()
        att = self.kite_attackers()
        window = self.contact_s(att)
        self.__dict__["_kite_window"] = window if window != math.inf else None
        if window == math.inf or window >= cast_delay(1) + KITE_MARGIN:
            return False                                       # a first-circle cast fits at least: attack
        return self.kite_away(att)

    def kite_away(self, att):
        """Run KITE_DIST tiles away from the attackers' centre, the walkable direction nearest straight away (spots.component on a dungeon's walk grid);
        a mounted or running caster gains on anything slower. True when it moved."""
        if not att:
            return False
        here = (int(self.c.x), int(self.c.y))
        cx = sum(int(m.x) for m in att) / len(att)
        cy = sum(int(m.y) for m in att) / len(att)
        ax, ay = here[0] - cx, here[1] - cy
        n = math.hypot(ax, ay) or 1.0
        base = math.atan2(ay / n, ax / n)
        try:
            import spots
            side = None
            try:
                import gazetteer
                side = gazetteer.side(here[0], here[1])
            except Exception:
                pass
            comp = spots.component_near(here[0], here[1], side) if side and side != "surface" else None
        except Exception:
            spots, comp = None, None
        tried = []
        out_step = self.kite_outward(att, here, side, comp, spots)
        if out_step is not None:
            # toward the way out when the pack does not stand on that line: away from it led BotWarlockAR, BotSorcBR, BotMageBR and BotMageAR into Despise's
            # dead-end west corner, boxed in by 4-10 lizardmen, four deaths (2026-11-09 02:41-04:05)
            try:
                self.c.goto(out_step[0], out_step[1]).wait(timeout=2.0)
            except Exception:
                pass
            if (int(self.c.x), int(self.c.y)) != here:
                f = self.fight or {}
                f["kites"] = f.get("kites", 0) + 1
                return True
        for k in (0, 1, -1, 2, -2, 3, -3):
            ang = base + k * math.pi / 4
            p = (int(round(here[0] + KITE_DIST * math.cos(ang))), int(round(here[1] + KITE_DIST * math.sin(ang))))
            if comp is not None and spots is not None and spots.component_near(p[0], p[1], side) != comp:
                continue
            if any(max(abs(p[0] - int(m.x)), abs(p[1] - int(m.y))) <= 2 for m in att):
                continue                                        # not into another of the pack
            tried.append(p)
            if hasattr(self, "sprint"):
                try:
                    self.sprint()
                except Exception:
                    pass
            try:
                self.c.goto(p[0], p[1]).wait(timeout=2.0)
            except Exception:
                pass
            moved = (int(self.c.x), int(self.c.y)) != here
            if moved:
                f = self.fight or {}
                f["kites"] = f.get("kites", 0) + 1
                now = time.time()
                if now - self.__dict__.get("_kite_logged", 0) > 10:
                    self.__dict__["_kite_logged"] = now
                    self.ev("kite_step", n=len(att), near=min(int(getattr(m, "distance", 9) or 9) for m in att), **{"from": list(here), "to": [int(self.c.x), int(self.c.y)]})
                return True
        return self.kite_teleport(att, tried)

    TELE_REACH = (10, 8, 6)    # tiles along the way out a Teleport aims at, farthest first (a targeted spell's range is 10 before AOS)

    def teleport_points(self, att):
        """Points to teleport to toward the way out: along the line to the stair a retreat would take (first_trip.trip_stair_near: not through the pack,
        toward the exit), TELE_REACH tiles off, on this floor's walk grid. The points straight away from the pack lay in the wall of a dead-end corner:
        BotMageBR's six Teleports at Despise's west end all failed ("not out", 2026-11-09 02:40-02:41)."""
        out = []
        try:
            import gazetteer
            import spots
            here = (int(self.c.x), int(self.c.y))
            side = gazetteer.side(here[0], here[1])
            if side == "surface":
                return out
            st = self.trip_stair_near(side, att) if hasattr(self, "trip_stair_near") else None
            if st is None:
                far = spots.outward_stairs(side, here, 10 ** 4)       # only the direction matters here: the way out at any distance
                st = far[0][1] if far else None
            if st is None:
                return out
            sx, sy = int(st["src"][0]), int(st["src"][1])
            d = max(abs(sx - here[0]), abs(sy - here[1])) or 1
            comp = spots.component_near(here[0], here[1], side)
            for r in self.TELE_REACH:
                f = min(1.0, r / d)
                p = (int(round(here[0] + (sx - here[0]) * f)), int(round(here[1] + (sy - here[1]) * f)))
                if comp is None or spots.component_near(p[0], p[1], side) == comp:
                    if not any(max(abs(p[0] - int(m.x)), abs(p[1] - int(m.y))) <= 1 for m in att):
                        out.append(p)
        except Exception:
            return out
        return out

    def kite_outward(self, att, here, side, comp, spots):
        """In a dungeon: the point KITE_DIST tiles along the line to the nearest stair out (spots.outward_stairs, any distance), when no attacker stands
        within 2 tiles of that stretch and it is on this floor's walk grid; else None."""
        if not side or side == "surface" or spots is None:
            return None
        try:
            from first_trip import seg_dist
            far = spots.outward_stairs(side, here, 10 ** 4)
            if not far:
                return None
            sx, sy = int(far[0][1]["src"][0]), int(far[0][1]["src"][1])
            d = max(abs(sx - here[0]), abs(sy - here[1])) or 1
            f = min(1.0, KITE_DIST / d)
            p = (int(round(here[0] + (sx - here[0]) * f)), int(round(here[1] + (sy - here[1]) * f)))
            if comp is not None and spots.component_near(p[0], p[1], side) != comp:
                return None
            if any(seg_dist(here, p, (int(m.x), int(m.y))) <= 2 for m in att):
                return None
            return p
        except Exception:
            return None

    def floor_tile(self, x, y):
        """(x, y, z, graphic) of the tile to stand on at x, y: the walkable static (flag Surface) nearest the caster's height, else the land itself;
        None when nothing there is loaded or walkable. A dungeon's floor is statics over void land: BotSorcBR's fifteen Teleports aimed at the land
        ("targettile 5394 558 61", graphic 0) and none moved it, and every caster Teleport of the night failed so (2026-11-09 02:40-04:02). Read with
        Navrey's "tiles x y"."""
        try:
            lines = self.c.call(f"tiles {int(x)} {int(y)}", timeout=4) or []
        except Exception:
            return None
        z0 = int(getattr(self.c, "z", 0) or 0)
        best = None
        land = None
        import re as _re
        for ln in lines:
            m = _re.search(r"(land|static)\s+0x([0-9A-Fa-f]+)\s+z=\s*(-?\d+)", ln)
            if not m:
                continue
            kind, g, z = m.group(1), int(m.group(2), 16), int(m.group(3))
            if kind == "static" and "Surface" in ln and "Impassable" not in ln:
                if best is None or abs(z - z0) < abs(best[2] - z0):
                    best = (int(x), int(y), z, g)
            elif kind == "land" and "Impassable" not in ln and int(x) < 5120:
                land = (int(x), int(y), z, 0)                      # land is ground on the surface only: under a dungeon it is the void
        return best or land

    def kite_teleport(self, att, points):
        """No run moved it (bodies on every side, a wall behind): Teleport (third circle, Bloodmoss and Mandrake Root) to the first open point a kite step
        tried, aimed with a ground cursor (Navrey targettile). A blow during its 1 s cast ruins it (Spell.OnCasterHurt): it is the last way out before a fight
        back. True when it moved."""
        if not self.spell_ok("teleport") or (self.c.mana or 0) < 9:
            return False
        if sum(1 for m in att if int(getattr(m, "distance", 9) or 9) <= 2) < 2:
            return False                                       # one beside it: Magic Arrow (first circle, never ruined) beats a 1 s Teleport a blow can ruin
        points = [p for p in self.teleport_points(att) + list(points or []) if not on_teleporter(p)]
        if not points:
            return False
        regs = getattr(self, "regs", {}) or {}
        if regs.get("Bloodmoss", 0) <= 0 or regs.get("MandrakeRoot", 0) <= 0:
            return False
        here = (int(self.c.x), int(self.c.y))
        aim = None
        for p in points[:4]:
            aim = self.floor_tile(p[0], p[1])
            if aim is not None:
                break
        if aim is None:
            return False
        x, y, z, graphic = aim
        try:
            from uo import Event
            self.c.events.drain()
            self.cmd("cast teleport")
            if self.c.wait_for(Event.TARGET_REQUEST, timeout=3.0) is None:
                return False
            self.cmd(f"targettile {x} {y} {z} {graphic}")
        except Exception as e:
            self.log(f"kite: teleport: {type(e).__name__}: {e}")
            return False
        time.sleep(0.6)
        moved = max(abs(int(self.c.x) - here[0]), abs(int(self.c.y) - here[1])) >= 3
        self.ev("kite_teleport", n=len(att), to=[x, y], ok=moved)
        self.log(f"kite: boxed in by {len(att)}: teleport to {x},{y}: {'out' if moved else 'not out'}")
        return moved

    # ---- leaving what it does not fight ------------------------------------------------------------------------------------------------------------

    def caster_avoid(self, dangers):
        """A danger within notice that it rates no fight: run from all of them (kite_away: a mounted caster outruns every Slow and Medium chaser, and
        the run takes it out of a spellcaster's range). True when it moved; False leaves mage_bot's r_avoid (fight back when cornered)."""
        att = self.kite_attackers(KITE_SEE) or list(dangers)
        if not att:
            return False
        if self.kite_away(att):
            self.activity = f"leaving {getattr(att[0], 'name', '?')}"
            return True
        return False

    # ---- buffs ------------------------------------------------------------------------------------------------------------------------------------

    def buff_before_fight(self, target):
        """Reactive Armor at a fight's start, once in RA_GAP: it absorbs a third of (Magery + Meditation) of melee damage and is never ruined (first circle).
        True when it cast."""
        now = time.time()
        if now - float(self.facts.get("ra_at", 0) or 0) < RA_GAP or not self.spell_ok("reactive armor"):
            return False
        regs = getattr(self, "regs", {}) or {}
        if not all(regs.get(r, 0) > 0 for r in ("Garlic", "SpidersSilk", "SulfurousAsh")) or (self.c.mana or 0) < 4 + HEAL_MANA:
            return False
        self.facts["ra_at"] = now
        self.ra_until = now + RA_GAP                            # (mage_bot.attack's own Reactive Armor check reads it)
        self.ev("buff", spell="reactive armor", mana=int(self.c.mana or 0))
        self.cast("reactive armor", None)
        return True

    # ---- heals ------------------------------------------------------------------------------------------------------------------------------------

    def caster_heal(self):
        """Out of reach and under HEAL_OUT: Greater Heal (more, but a blow ruins it). Beside an attacker and under HEAL_IN: Heal (first circle, never
        ruined), else a Heal potion. True when it healed (or tried)."""
        hp = self.hp_pct()
        if hp >= HEAL_OUT or self.c.poisoned:
            return False
        self.regs_fresh()
        att = self.kite_attackers(4)
        beside = any(int(getattr(m, "distance", 9) or 9) <= 1 for m in att)
        soon = self.contact_s(att) < cast_delay(4) + KITE_MARGIN
        if not beside and not soon and (self.c.mana or 0) >= GH_MANA and self.spell_ok("greater heal") and self.gh_regs():
            self.log(f"greater heal at {self.c.hp}")
            self.cast("greater heal", "self")
            return True
        if hp >= HEAL_IN:
            return False
        if (self.c.mana or 0) >= HEAL_MANA and self.spell_ok("heal") and self.heal_regs():
            self.log(f"heal (never ruined) at {self.c.hp}{' beside ' + att[0].name if beside else ''}")
            self.cast("heal", "self")
            return True
        return bool(self.drink_heal("caster: no heal spell"))

    def casts_now(self):
        """casts_left, read at most every CASTS_TTL s (rating.bot_numbers asks it for every rating): 0 with no reagents for any attack spell."""
        hit = self.__dict__.get("_casts_now")
        now = time.time()
        if hit and now - hit[0] < CASTS_TTL:
            return hit[1]
        self.regs_fresh()
        n = self.casts_left()
        self.__dict__["_casts_now"] = (now, n)
        return n

    def regs_fresh(self):
        """The reagent count read again after a death (mage_bot.refresh_state reads it once a minute): BotSorcBR, resurrected with its reagents on its
        corpse, cast Greater Heal twelve times from the old count, healed nothing, and a dire wolf killed it (2026-11-09 04:10)."""
        if self.__dict__.get("_regs_deaths") != getattr(self, "deaths", 0):
            self.__dict__["_regs_deaths"] = getattr(self, "deaths", 0)
            self.__dict__.pop("_casts_now", None)
            try:
                self.refresh_state(force=True)
            except Exception:
                pass

    def gh_regs(self):
        regs = getattr(self, "regs", {}) or {}
        return all(regs.get(r, 0) > 0 for r in ("Garlic", "Ginseng", "MandrakeRoot", "SpidersSilk"))

    # ---- the kit ------------------------------------------------------------------------------------------------------------------------------------

    def casts_left(self):
        """Casts of its best attack spell its reagents allow (mana aside), 0 when it casts none."""
        self.__dict__["_kite_window"] = None                       # every spell, not those that fit a fight's moment
        try:
            self.refresh_state()
            pick = self.k.best_attack(self.skill, 999, self.regs)
            if pick is None:
                return 0
            regs = getattr(self, "regs", {}) or {}
            return min((regs.get(r, 0) for r in pick["spell"].get("reagents") or []), default=0)
        except Exception:
            return 0

    def caster_heals(self):
        """Heal potions carried."""
        try:
            import items
            return sum((i.amount or 1) for i in self.c.backpack if items.potion_kind(i.name) == "heal")
        except Exception:
            return 0

    # ---- the measure ------------------------------------------------------------------------------------------------------------------------------

    def kite_fight_note(self, f, outcome):
        """At a fight's end, for a fight it kited at least once: the damage it took against what the rating says it would have taken standing (the
        stand-still loss). Their ratio over many fights is rating.json's kite_leak."""
        if not f or not f.get("kites"):
            return
        try:
            import rating
            me = rating.bot_numbers(self)
            me["kite"] = False                                  # the stand-still fight
            me["hp"] = max(float(f.get("hp0", 0) or 0), 1.0)
            r = rating.rate(self, f.get("key") or "", me)
            stand = r and r.get("lost")
        except Exception:
            stand = None
        dmg = max(0, int(f.get("hp0", 0) or 0) - int(f.get("hpmin", f.get("hp0", 0)) or 0))
        self.ev("kite_fight", m=f.get("key"), secs=round(time.time() - f.get("t0", time.time()), 1), dmg=dmg, stand_lost=stand,
                kites=int(f.get("kites", 0)), outcome=outcome, n=int(f.get("near_max", 0) or 0))
