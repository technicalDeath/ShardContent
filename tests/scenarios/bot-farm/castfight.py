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
HEAL_OUT = 65                 # percent health under which a caster with nothing beside it casts Greater Heal
HEAL_IN = 50                  # percent under which a caster with an attacker beside it casts Heal (first circle, never ruined) or drinks
GH_MANA = 11
HEAL_MANA = 4


def cast_delay(circle):
    """Seconds a cast of this (1-based) circle holds the caster still: MagerySpell.GetCastDelay before AOS."""
    return 0.5 + 0.25 * (max(1, int(circle or 1)) - 1)


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
            return [o for o in opts if cast_delay(o["spell"].get("circle")) + KITE_MARGIN <= window]

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

    def gh_regs(self):
        regs = getattr(self, "regs", {}) or {}
        return all(regs.get(r, 0) > 0 for r in ("Garlic", "Ginseng", "MandrakeRoot", "SpidersSilk"))

    # ---- the kit ------------------------------------------------------------------------------------------------------------------------------------

    def casts_left(self):
        """Casts of its best attack spell its reagents allow (mana aside), 0 when it casts none."""
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
                kites=int(f.get("kites", 0)), outcome=outcome)
