"""The basic game mechanics every brain shares (the owner, 2026-10-30: "I want all bots of all brain types to have shared and standard intelligence and
behavior for basic game mechanics").

BotBase (the fighters, bards, crafters, broke miners, fishers, miners and tamers) and CasterBot (the mages, built on new-mage-playtest/mage_bot.py) both
inherit BasicsMixin. A brain overrides a hook (cure_spell, heal_spell, fight_back), never the rule itself. Before this each brain had its own copy and the
copies drifted: the fighters drank a Heal potion every 12 s while poisoned (refused by the engine), cured beside a slime that poisons again on half its hits,
and fled to a town refuge hundreds of tiles off; the casters stopped every far walk for a hind (BotBase.threats counted every animal).

What lives here, each with its source:
- potions: which item is which (items.POTION_NAMES), drinking with a free hand (BasePotion.HasFreeHand), the Heal potion's 10 s delay and its refusal while
  poisoned (BaseHealPotion.Delay, "You can not heal yourself in your current state."), the Cure rule beside a poisoner (BaseCreature.HitPoisonChance 0.5;
  pre-AOS Lesser poison at most 4 a tick for 10 ticks, PoisonKinds.cs), the Refresh potion when out of breath near a threat (RefreshPotion +25% of maximum)
- threats: a mobile that can hurt (an attack-on-sight kind, task_core.aggressive from the engine's AI, or anything in war mode)
- fleeing: 18 tiles straight away (a running player 0.2 s a tile, movement.delay.runFoot; a giant rat 0.45, a slime 0.6, npc-speeds.json; a creature notices
  within 16 tiles, BaseCreature.DefaultRangePerception), then the two right angles; "trapped" when none is open, and the bot fights back
- the selling decision: the goods' worth at the shops (items.py) against errands.sell_value, a heavy pack, or a bot nearly broke
- small shared helpers: the status file, line of sight, finding a gump, a fight's target dying, the memory's kind key
"""
from __future__ import annotations

import json
import os
import re
import time

import items

HARMLESS = ("rat", "cat", "dog", "bird", "chicken", "rabbit", "sheep", "cow", "pig", "goat", "hind", "deer", "crow", "magpie", "sparrow", "swallow",
            "nightingale", "plover", "thrush", "tern", "warbler", "squirrel", "toad", "frog", "lizard", "gull", "raven", "finch", "towhee", "starling")


LESSON_BEFORE = ("r_craft", "r_colour", "r_mine", "r_dig", "r_fish", "r_tame", "r_pet_hunt", "r_hunt", "r_explore", "r_camp", "r_idle", "r_wander")


class BasicsMixin:

    def house_worth(self):
        """Gold a bot's house holdings are worth: a small house deed bought (in the pack or the bank) or a house placed from it counts at the shard's
        small house price (goals.HOUSE_COST, housePricing.smallHouses: the Architect's price, the deed's house value and the Real Estate Broker's
        buy-back, HouseDeed.ValueAdjust). Owner, 2026-11-01: "Have net worth include house and house deeds"."""
        try:
            st = self.house_state() if hasattr(self, "house_state") else None
        except Exception:
            st = None
        if not st:
            return 0
        import goals as _goals
        placed = st.get("phase") in ("lock", "furnish", "done") and st.get("where")
        return int(_goals.HOUSE_COST) if placed or st.get("deed_serial") else 0

    def r_heal(self):
        """Bandage oneself after a fight (the shared fallback; fighters, tamers and casters have their own): under 65% of hit points with nothing within 3
        tiles, while the skill plan holds Healing or Healing is already 20+. The gatherers and crafters had no heal at all: a miner at a third of its hit
        points stood fleeing rabbits for minutes (2026-10-31). docs/Bot-Farm-Skill-Plans.md."""
        import skillplan
        if self.c.ghost or self.mobs(3) or not self.c.find("bandage"):
            return False
        if self.hp_pct() >= 65:
            # practice: a scratch of PRACTICE_MISS or more with nothing in view, while the plan holds Healing below its target (every bandage on a hurt
            # patient checks Healing, Bandage.cs; a patient full at the end checks nothing). Gatherers and crafters stood at Healing 30-45 (2026-11-07)
            missing = (self.c.max_hp or 0) - (self.c.hp or 0)
            if missing < self.PRACTICE_MISS or not skillplan.wants(self, "Healing") or self.threats(10):
                return False
            return self.bandage_self()
        if (getattr(self, "skill_values", None) or {}).get("Healing", 0) < 20 and not skillplan.wants(self, "Healing"):
            return False
        return self.bandage_self()

    PRACTICE_MISS = 3         # hit points a practice bandage needs missing (hunter.PRACTICE_MISS: regen closes a smaller scratch before the bandage ends)

    def r_train(self):
        """Practise the plan's skills that rise only with use, when idle and safe (owner, 2026-11-07: "bots should action against their full 700 skill
        bank and not focus on a singular profession/skill"): Hiding (hide_practice: 60 s apart, nothing hostile within 16, never in a shop), with no
        prey in view. The fighters' plans hold Hiding at 100 and every one stood at 0 (16 of the 27 bots with Hiding unfinished gained under 0.5 in a
        day); the gatherers, practising it idle, gained 1-6 a day."""
        if getattr(self, "prey", None) and self.prey(12):
            return False
        return self.hide_practice()

    HIDE_GAP = 10.0           # Hiding.cs: the next try 10 s after one (1 s after "You can't seem to hide right now")
    HIDE_STILL = 30.0         # s to stand hidden while the threat is in view (moving reveals: no Stealth in any plan)
    HIDE_PRACTICE = 60.0      # s between practice tries while idle and safe

    def hide_on(self):
        import skillplan
        return self.feature("skill_plan") and (skillplan.wants(self, "Hiding") or (getattr(self, "skill_values", None) or {}).get("Hiding", 0) >= 20)

    def try_hide(self):
        """Use Hiding and read the answer: True when hidden (501240 "You have hidden yourself well")."""
        self.facts["hide_at"] = time.time()
        self.read_journal()
        self.c.call("useskill hiding", timeout=6)
        end = time.time() + 2.5
        while time.time() < end:
            time.sleep(0.5)
            for l in self.read_journal():
                if re.search(r"hidden yourself", l, re.I):
                    return True
                if re.search(r"can't seem to hide|cannot hide", l, re.I):
                    return False
        return False

    def r_hide(self):
        """Hide from a threat coming close instead of running from it (docs/Bot-Farm-Skill-Plans.md): a miner of the era hid at the forge and in the hills.
        Hiding.cs: it works only before the monster has made this character its target, and its chance is the skill (0-100), so the threat is met at 4-10
        tiles; once hidden the bot stands still (a step reveals it) while the threat is in view, at most HIDE_STILL s. A failed try falls through to r_evade."""
        if self.c.ghost or not self.hide_on() or time.time() - self.facts.get("hide_at", 0) < self.HIDE_GAP:
            return False
        near = self.threats(10)
        if not near or any(getattr(m, "distance", 9) <= 3 for m in near):
            return False
        if not self.try_hide():
            return False
        self.activity = f"hidden from {near[0].name}"
        self.ev("hid", threat=near[0].name, dist=near[0].distance)
        until = time.time() + self.HIDE_STILL
        while time.time() < until and self.threats(14) and not self.c.ghost:
            time.sleep(1.0)
        return True

    SHOP_CLEAR = 2            # tiles beyond a vendor's wander radius (its spawner's, Vendors.json via the gazetteer) that still count as its shop

    def in_shop(self):
        """True within a vendor's wander radius + SHOP_CLEAR tiles of its spawner (the gazetteer's places): the inside of a shop, where the walkways
        are a tile or two wide."""
        try:
            import gazetteer as gz
            x, y = int(self.c.x), int(self.c.y)
            for p in gz.get().places:
                if not str(p.get("src", "")).startswith("spawner:Vendors"):
                    continue
                if max(abs(int(p["x"]) - x), abs(int(p["y"]) - y)) <= int(p.get("radius") or 0) + self.SHOP_CLEAR:
                    return True
        except Exception:
            pass
        return False

    def hide_practice(self):
        """Hiding practised while idle and safe (the skill only rises with use; nothing is near to make it fail for want of cover), never in a shop:
        hidden, the character is an invisible body in a walkway a tile or two wide that the others' planners cannot see (in_shop). BotCarpAR could not
        leave the carpenter's for 10 minutes past "something invisible" (2026-11-05)."""
        if (self.c.ghost or not self.hide_on() or self.threats(16) or time.time() - self.facts.get("hide_practice_at", 0) < self.HIDE_PRACTICE
                or time.time() - self.facts.get("hide_at", 0) < self.HIDE_GAP or self.in_shop()):
            return False
        self.facts["hide_practice_at"] = time.time()
        ok = self.try_hide()
        self.ev("hide_practice", ok=ok)
        return True

    def net_worth(self):
        """Carried gold, the bank balance and the house holdings (house_worth)."""
        return (self.c.gold or 0) + self.facts.get("bank_balance", 0) + self.house_worth()

    HARMLESS = HARMLESS

    HEAL_POTION_DELAY = 10.0             # BaseHealPotion.Delay: one Heal potion every 10 s
    CURE_RECHECK = 6.0                   # a drink takes about 1.5 s with its waits; the poison state is read again after this
    POISON_ALL = 40                      # all a Lesser poison can still do (4 a tick, 10 ticks): above it a bot fights the poisoner first, cures after
    REFRESH_BELOW = 0.25                 # a Refresh gives +25% of the maximum (RefreshPotion): drunk below a quarter, it never overfills
    REFRESH_EVERY = 20.0
    FLEE_TILES = 18
    SELL_HEAVY = 0.85                    # the pack share at which a sell trip is due whatever it holds (BotBase.bank_overload_pass share)
    SELL_BROKE = 60                      # gold under which a bot sells what it has (reagents and repairs cost about this much)

    def __init_subclass__(cls, **kw):
        """Every brain gets the standard rules: r_refresh right after r_cure."""
        super().__init_subclass__(**kw)
        rules = cls.__dict__.get("RULES")
        if isinstance(rules, list) and "r_cure" in rules and "r_refresh" not in rules:
            rules.insert(rules.index("r_cure") + 1, "r_refresh")
        if isinstance(rules, list) and "r_lesson" not in rules and hasattr(cls, "r_lesson"):         # (CasterBot borrows BotBase piecemeal: not it)
            # lessons from NPC trainers (lessons.py, feature lessons): after banking, selling and restocking, before the brain's work
            work = next((r for r in rules if r in LESSON_BEFORE), None)
            rules.insert(rules.index(work) if work else len(rules), "r_lesson")

    # ---- names ------------------------------------------------------------------------------------------------------------------------------------------

    @staticmethod
    def mkey(m):
        """The memory's name for a kind of monster: its body species when the client knows it ("orc" for a personally named orc), else its name without the article."""
        return re.sub(r"[^a-z]", "", (m.species or re.sub(r"^(an?|the) ", "", m.name.lower())).lower())

    # ---- threats -----------------------------------------------------------------------------------------------------------------------------------------

    def can_hurt(self, m):
        """A kind that attacks on sight (not AI_Animal: task_core.aggressive, from the engine's constructors), or anything already in war mode."""
        if getattr(m, "in_war_mode", False):
            return True
        try:
            import task_core
            return task_core.aggressive(self.mkey(m))
        except Exception:
            return True

    def threats(self, within):
        """Mobiles near that can hurt a working character: a hind or a town cat is none, an orc or a wolf fighting back is."""
        out = []
        for m in self.mobs(within):
            n = (m.name or "").lower()
            if not getattr(m, "in_war_mode", False) and n.startswith(("a ", "an ")) and any(re.search(r"\b" + re.escape(w) + r"\b", n) for w in self.HARMLESS) \
                    and not any(w in n for w in ("giant", "dire", "plague", "rat man", "ratman")):
                continue
            if getattr(m, "in_war_mode", False) and (getattr(m, "distance", 0) or 0) > self.ANIMAL_REACH and self._animal(m):
                continue                                          # an animal fights only what attacked it (AI_Animal, FightMode.Aggressor): one in war mode
                                                                  # away from the bot is fighting someone else (a cow at a newbie's sword, 2026-11-01)
            if self.can_hurt(m):
                out.append(m)
        return out

    ANIMAL_REACH = 2          # an animal fighting this bot stands next to it

    def _animal(self, m):
        try:
            import task_core
            return not task_core.aggressive(self.mkey(m)) and bool(task_core._CS.get(self.mkey(m)))
        except Exception:
            return False

    STILL_THREAT_S = 30        # a hostile in view this long that never came within STILL_NEAR and is no closer is not coming (its AI looks for targets about
    STILL_NEAR = 4             # every second): BotMinerBR stood 28 minutes by a giant rat that never came, BotTinkBR skipped crafting 20 (2026-10-31)

    def threat_coming(self, m):
        """Does this hostile stop work or a walk: new in view, within STILL_NEAR, or nearer than when first seen; not one that has kept its distance STILL_THREAT_S."""
        seen = self.__dict__.setdefault("_threat_seen", {})
        now = time.time()
        d = getattr(m, "distance", 0) or 0
        key = getattr(m, "serial", None) or id(m)
        first = seen.get(key)
        if not first or now - first[0] > 300:
            seen[key] = (now, d)
            return True
        return d <= self.STILL_NEAR or d < first[1] or now - first[0] < self.STILL_THREAT_S

    def threats_coming(self, within):
        return [m for m in self.threats(within) if self.threat_coming(m)]

    def adjacent_attacker(self):
        """Something that can hurt standing next to the bot: its next blow ruins a spell (Spell.OnCasterHurt) and a bandage's care, and undoes a cure."""
        try:
            return any(m.distance <= 1 for m in self.threats(2))
        except Exception:
            return False

    # ---- potions -----------------------------------------------------------------------------------------------------------------------------------------

    def potion(self, kind):
        return next((i for i in self.c.backpack if items.potion_kind(i.name) == kind), None)

    def potion_count(self, kind):
        return sum((i.amount or 1) for i in self.c.backpack if items.potion_kind(i.name) == kind)

    def drink(self, item):
        """Drink a potion the way the era makes a player do it: the engine refuses a potion without a free hand (BasePotion.HasFreeHand, "You must have a free
        hand to drink a potion."): a bow, or a weapon and a shield, fill both hands. The two-handed-layer piece goes to the pack, the potion is drunk, the piece
        goes back in hand. True when the potion left the pack (the Watcher, 2026-10-29: archers had logged 20 refused Cure potions each before a snake killed them)."""
        name = item.name
        before = sum((i.amount or 1) for i in self.c.backpack if i.name == name)
        one = next((w for w in self.c.equipped if (w.layer or "").replace(" ", "").lower() == "onehanded"), None)
        two = next((w for w in self.c.equipped if (w.layer or "").replace(" ", "").lower() == "twohanded"), None)
        moved = two if two is not None and (one is not None or "shield" not in (two.name or "").lower()) else None
        if moved is not None:
            self.c.unequip(moved.serial)
            time.sleep(0.7)
        self.c.use(item.serial)
        time.sleep(0.7)
        if moved is not None:
            try:
                self.c.call(f"equip {moved.serial}", timeout=6)
            except Exception:
                pass
            time.sleep(0.4)
        after = sum((i.amount or 1) for i in self.c.backpack if i.name == name)
        ok = after < before
        if moved is not None:
            self.ev("drink_hand_freed", item=name, freed=moved.name, ok=ok)
        return ok

    def drink_heal(self, why=""):
        """The Heal potion: never while poisoned (it is refused), at most one every 10 s. True when drunk."""
        if self.c.poisoned:
            return False
        now = time.time()
        if now - max(self.facts.get("heal_pot_at", 0), self.facts.get("drank", 0)) < self.HEAL_POTION_DELAY:
            return False
        pot = self.potion("heal")
        if pot is None:
            return False
        self.facts["heal_pot_at"] = self.facts["drank"] = now
        ok = self.drink(pot)
        self.ev("consumable_used", item="yellow potion", hp=self.hp_pct(), ok=ok, why=why)
        return ok

    def drink_cure(self, why=""):
        pot = self.potion("cure")
        if pot is None:
            return False
        ok = self.drink(pot)
        seen = getattr(self, "poison_seen", lambda: None)()
        self.ev("consumable_used", item="orange potion", hp=self.hp_pct(), ok=ok, why=why, **({"poison": seen} if seen else {}))
        return ok

    def drink_refresh(self, why=""):
        """The Refresh potion below a quarter of the maximum stamina, at most one every 20 s. True when drunk."""
        try:
            mx = int(self.c.state.get("maxStam") or 0)
        except Exception:
            mx = 0
        if mx <= 0 or self.c.stamina >= self.REFRESH_BELOW * mx or time.time() - self.facts.get("refresh_pot_at", 0) < self.REFRESH_EVERY:
            return False
        pot = self.potion("refresh")
        if pot is None:
            return False
        self.facts["refresh_pot_at"] = time.time()
        ok = self.drink(pot)
        self.ev("consumable_used", item="red potion", stam=self.c.stamina, ok=ok, why=why)
        return ok

    def cure_due(self):
        """Poisoned and worth curing now: not while what stands next to it still has more to give than the poison can take (it poisons again on half its hits)."""
        if self.c.ghost or not self.c.poisoned or time.time() - self.facts.get("cured_at", 0) < self.CURE_RECHECK:
            return False
        return not (self.adjacent_attacker() and self.c.hp > self.POISON_ALL)

    # hooks a brain fills in: a caster's spells
    def cure_spell(self):
        return False

    def heal_spell(self):
        return False

    def r_cure(self):
        """Poisoned: cure before anything else (a Heal potion or spell does nothing while poisoned). Beside an attacker the potion (a hit ruins a spell), else
        the Cure spell, else the potion, else a bandage from Healing 60 (the era's bandage cures only from there)."""
        if not self.cure_due():
            return False
        self.facts["cured_at"] = time.time()
        self.activity = "curing poison"
        adjacent = self.adjacent_attacker()
        if adjacent and self.drink_cure("adjacent attacker"):
            return True
        if not adjacent and self.cure_spell():
            return True
        if self.drink_cure("no spell"):
            return True
        if (getattr(self, "skill_values", {}) or {}).get("Healing", 0) >= 60 and self.c.find("bandage") and getattr(self, "bandage_self", None):
            return self.bandage_self()
        if getattr(self, "note", None):
            self.note("poison", f"A poisoned {getattr(self, 'pname', 'bot')} with no Cure potion and too little Healing can only run to a healer or wait it out.", key="cure:none")
        return False

    def r_refresh(self):
        """Out of breath with something that can hurt it near, or in a fight: the Refresh potion (a tired bot swings slower, 15000 / ((Stam + 100) x speed),
        and cannot run from a losing fight)."""
        if self.c.ghost:
            return False
        if not (getattr(self, "fight", None) or self.threats(10)):
            return False
        return self.drink_refresh("out of breath")

    # ---- fleeing -----------------------------------------------------------------------------------------------------------------------------------------

    @staticmethod
    def kind_casts(kind):
        """A kind that hurts at range, spells or breath (creature_stats via danger.stats), as first_trip.trip_caster."""
        try:
            import danger
            c = danger.stats().get(kind) or {}
            return bool(c.get("casts") or c.get("breath"))
        except Exception:
            return False

    def walk_threats(self):
        """detour.Threat for each monster in notice range this bot does not fight (dangers: not its prey, not a passive animal), casters marked."""
        import detour
        try:
            near = list(self.dangers(detour.NOTICE)) if hasattr(self, "dangers") else list(self.threats(detour.NOTICE))
        except Exception:
            near = []
        out = []
        for m in near:
            if getattr(m, "x", None) is None or getattr(m, "y", None) is None:
                continue
            try:
                kind = self.mkey(m)
            except Exception:
                kind = ""
            out.append(detour.Threat(int(m.x), int(m.y), self.kind_casts(kind), getattr(m, "name", "") or "", detour.poisons(kind)))
        self.note_casters(out)                                 # every bot's routes bend round what this one sees (live_caster_penalty)
        return out

    def caster_lair_home(self):
        """forbidden(point) for detour.py: inside the home range of a caster lair this bot loses to (spots.deadly_spawners), cached a minute."""
        got = self.__dict__.get("_lair_homes")
        if got is None or time.time() - got[0] > 60:
            try:
                import spots
                homes = [(o["x"], o["y"], max(int(o.get("home") or 10), 1)) for o, k in spots.deadly_spawners(self) if self.kind_casts(k)]
            except Exception:
                homes = []
            got = self.__dict__["_lair_homes"] = (time.time(), homes)
        homes = got[1]
        return lambda p: any(abs(p[0] - x) <= r and abs(p[1] - y) <= r for x, y, r in homes)

    def walk_detour(self, target):
        """The next point of any walk (a far walk's leg, a hunt journey's waypoint) when monsters this bot does not fight are in notice range: the best
        short leg round them (detour.plan_leg), or, with a caster inside its reach, a committed escape until out of every caster's notice (owner,
        2026-11-03: "make sure all bots utilize the new detour logic"). None when the way on is clear. The leg is walked by the caller."""
        try:
            import detour
            import walkroute
            wr = walkroute.get()
        except Exception:
            return None
        threats = self.walk_threats()
        esc = self.__dict__.setdefault("_walk_escape", {"on": False})
        if not threats:
            esc["on"] = False
            return None
        here = (int(self.c.x), int(self.c.y))
        casters = [th for th in threats if th.caster]
        if casters and detour.clearance_at(here, casters) < 0:
            esc.update(on=True, pack=False)
        elif len(threats) >= detour.PACK and detour.clearance_at(here, threats) < 0:
            esc.update(on=True, pack=True)                     # a pack in view and one of it in reach: out of every reach first (detour.PACK)
        elif esc["on"] and esc.get("pack") and all(detour.cheb(here, (th.x, th.y)) >= detour.NOTICE + 2 for th in threats):
            esc.update(on=False, pack=False)                   # past every one's notice: back to the walk (at its reach, the walk led back in)
        elif esc["on"] and not esc.get("pack") and all(detour.cheb(here, (th.x, th.y)) >= detour.NOTICE + 2 for th in casters):
            esc["on"] = False
        forbid = self.detour_forbid(here, self.caster_lair_home())
        if esc["on"]:
            try:
                import casterpass
                fixed = {(int(m.x), int(m.y)) for m in (self.dangers(detour.NOTICE) if hasattr(self, "dangers") else [])
                         if getattr(m, "x", None) is not None and self.mkey(m) in casterpass.IMMOBILE}
            except Exception:
                fixed = set()
            leg = detour.escape_leg(here, threats, wr.leg_clear, forbidden=forbid, fixed=fixed)
        else:
            leg = detour.plan_leg(here, (int(target[0]), int(target[1])), threats, wr.leg_clear, forbidden=forbid)
        if leg is not None:
            self.detour_note(here, leg)
        if leg is not None and time.time() - self.__dict__.get("_walk_detour_logged", 0) > 10:
            self.__dict__["_walk_detour_logged"] = time.time()
            self.log(f"walk: {leg.kind} to {leg.to[0]},{leg.to[1]} (clearance {leg.clearance}, gain {leg.progress}) round "
                     + ", ".join(f"{th.name} at {detour.cheb(here, (th.x, th.y))}" for th in threats)[:90])
            self.ev("walk_detour", leg=leg.kind, at=list(here), to=list(leg.to), clearance=leg.clearance, gain=leg.progress)
        return leg

    SHED_GOODS = ("cut up leather", "hides", "pile of hide", "raw ", "ribs", "feather", "fish steak", "bacon", "ham")    # loot that may go on the ground
    SHED_NEVER = ("tunic", "sleeves", "gloves", "leggings", "gorget", "cap", "skirt", "bustier", "armor", "armour", "shield", "helm", "boots")  # worn gear
    OVERLOAD_MARGIN = 5             # stones under the carry limit an overloaded bot sheds down to

    def pack_upkeep(self):
        """Every tick, cheaply (both checks rate-limited):
        - a pack the client has not opened since login is opened: until then the client lists only part of it, and the bot banks and sells only what it
          sees. BotBardBR, after the farm server's restart, saw 4 of 48 items, carried 150 cut leather and 38 ribs it never knew of, and stood 2 h
          over its limit at the Britain bank (370 of 359, every step "carrying too much weight") (2026-11-03 16:47-19:13);
        - over the carry limit, which stops every step: loot goods (SHED_GOODS: leather, hides, meat, feathers) go on the ground, the cheapest a shop
          pays for first, until OVERLOAD_MARGIN under it, as a player drops meat to move again. Gear, kit, gold and tools are never shed here."""
        if self.c.ghost:
            return
        now = time.time()
        st = self.c.state or {}
        if not st.get("backpackOpened") and now - self.__dict__.get("_pack_open_at", 0) > 60:
            self.__dict__["_pack_open_at"] = now
            bp = st.get("backpackID")
            if bp:
                try:
                    self.c.use(bp)
                    self.log("opened the backpack: the client had not listed it since login")
                except Exception:
                    pass
            return
        try:
            weight, limit = int(self.c.weight or 0), int(self.c.max_weight or 0)
        except Exception:
            return
        if not limit or weight <= limit or now - self.__dict__.get("_overload_at", 0) < 20:
            return
        self.__dict__["_overload_at"] = now
        goods = [i for i in self.c.backpack if any(w in (i.name or "").lower() for w in self.SHED_GOODS)
                 and not any(w in (i.name or "").lower() for w in self.SHED_NEVER)]

        def price(i):
            try:
                return max([p for p, xy, item in self.mem.vendor_buying((i.name or "").lower()) if p > 0] or [0])
            except Exception:
                return 0
        def unit(i):
            return 0.1 if "feather" in (i.name or "").lower() else 1.0     # a feather 0.1 stone, leather, hides and meat 1 (their DefaultWeight)
        goods.sort(key=lambda i: (price(i), -unit(i)))
        before, shed = weight, []
        for it in goods:
            over = int(self.c.weight or 0) - (limit - self.OVERLOAD_MARGIN)
            if over <= 0:
                break
            n = min(int(it.amount or 1), int(-(-over // unit(it))))         # only what takes it under: BotBardBR put down all 150 leather for 16 over
            if self.drop_to_ground(it, amount=n):
                shed.append(f"{it.name} x{n}")
        if shed:
            self.log(f"overloaded ({before}/{limit}, every step refused): put down {', '.join(shed)[:120]} -> {self.c.weight}/{limit}")
            self.ev("shed", how="overload", items=shed[:8], before=before, after=int(self.c.weight or 0), limit=limit)

    CASTER_SEEN_TTL = 1200          # s a caster sighting steers every bot's routes: the giant camps' and most spawners' maxDelay is 00:20:00 (cove-spawn-areas.json),
                                    # so a caster seen there is back within that even if someone killed it
    CASTER_SEEN_GRID = 8            # tiles a sighting is rounded to: one record per spot, not per step

    def note_casters(self, threats):
        """A caster in notice range goes into the shared memory (kind caster_seen, a 'blocked' record that lasts CASTER_SEEN_TTL), at most once per spot
        and bot every 5 minutes: every bot's route planning then bends round it (live_caster_penalty). The bots found the Trinsic road's reaper at
        1570,2152 one by one, five aborted trips by four bots, each a fresh discovery (2026-11-02/03)."""
        mem = getattr(self, "mem", None)
        if mem is None:
            return
        now = time.time()
        seen = self.__dict__.setdefault("_casters_noted", {})
        g = self.CASTER_SEEN_GRID
        for th in threats:
            if not getattr(th, "caster", False):
                continue
            key = f"{th.x // g * g + g // 2},{th.y // g * g + g // 2}"
            if now - seen.get(key, 0) < 300:
                continue
            seen[key] = now
            try:
                mem.record("blocked", kind="caster_seen", key=key, ttl=self.CASTER_SEEN_TTL, m=th.name)
            except Exception:
                pass

    def casters_seen(self):
        """[(x, y)] of the caster sightings still in force (any bot's, note_casters)."""
        mem = getattr(self, "mem", None)
        if mem is None:
            return []
        try:
            mem.refresh()
            rows = mem.state["world"]["res"].get("caster_seen", {})
        except Exception:
            return []
        now = time.time()
        out = []
        for key, r in rows.items():
            if r.get("blocked_until", 0) > now:
                try:
                    x, y = (int(v) for v in key.split(","))
                    out.append((x, y))
                except ValueError:
                    pass
        return out

    def live_caster_penalty(self, wr):
        """A route cost round every live caster sighting: its spell reach and a step (detour.CASTER_CLEAR), at a caster lair's weight (8, far.py)."""
        try:
            import detour
            pts = self.casters_seen()
            return wr.penalty_circles([(x, y, detour.CASTER_CLEAR, 8.0) for x, y in pts]) if pts else {}
        except Exception:
            return {}

    def detour_note(self, here, leg):
        """Remember the leg just chosen, for detour_forbid's look at how the walk went."""
        self.__dict__["_detour_last"] = (tuple(here), tuple(leg.to), time.time())

    def detour_forbid(self, here, base):
        """forbidden(point) for detour.py: base (a caster lair's home range) or within 2 tiles of a leg end the walk fell short of lately. The walk map
        knows the ground, not the walls of a town or a monster in the way: BotWarAdvR's escape legs by Trinsic ended "11 tiles short" over and over
        with a reaper at 4-14 tiles and an orc beside it (2026-11-03 17:02-17:03); a leg end it got no nearer to is barred 30 s and another is run."""
        import detour
        now = time.time()
        blocked = self.__dict__.setdefault("_detour_blocked", {})
        last = self.__dict__.get("_detour_last")
        if last and now - last[2] < 15:
            frm, to, _ = last
            if detour.cheb(here, to) > 3 and detour.cheb(here, frm) < 4:
                blocked[to] = now + 30
        for k in [k for k, until in blocked.items() if until < now]:
            del blocked[k]
        pts = list(blocked)
        return lambda p: base(p) or any(detour.cheb(p, q) <= 2 for q in pts)

    def flee_from(self, m, first=None):
        """Run from m: to `first` when given (a refuge close by), else FLEE_TILES straight away, else at right angles. Returns the walk's result, or "trapped"
        when no way is open (a fenced pocket: two casters died at 1180-1195,1778 still "fleeing")."""
        if getattr(self, "sprint", None):
            self.sprint()
        tries = []
        if first is not None:
            tries.append((int(first[0]), int(first[1])))
        elif m is not None:
            try:
                # no refuge given (a caster's flight): first the detour's way out, away from every danger in view, never into a caster lair
                import detour
                import walkroute
                here = (int(self.c.x), int(self.c.y))
                ths = self.walk_threats()
                if all((th.x, th.y) != (int(m.x), int(m.y)) for th in ths):
                    ths.append(detour.Threat(int(m.x), int(m.y), self.kind_casts(self.mkey(m)), getattr(m, "name", "") or "", detour.poisons(self.mkey(m))))
                leg = detour.escape_leg(here, ths, walkroute.get().leg_clear, forbidden=self.detour_forbid(here, self.caster_lair_home()))
                if leg is not None:
                    self.detour_note(here, leg)
                    tries.append(leg.to)
            except Exception:
                pass
        if m is not None:
            dx, dy = self.c.x - m.x, self.c.y - m.y
            sx, sy = (1 if dx >= 0 else -1), (1 if dy >= 0 else -1)
            tries += [(self.c.x + ux * self.FLEE_TILES, self.c.y + uy * self.FLEE_TILES) for ux, uy in ((sx, sy), (sx, -sy), (-sx, sy))]
        for x, y in tries:
            res = str(self.c.goto(x, y).wait(timeout=8))
            if not res.startswith(("nopath", "blocked")):
                self.ev("flee", away_from=self.mkey(m) if m is not None else None, res=res[:20], hp=self.c.hp)
                return res
        self.ev("flee", away_from=self.mkey(m) if m is not None else None, res="trapped", hp=self.c.hp)
        return "trapped"

    # armour by the worn piece's name (the client names it from its graphic): Items/Armor ArmorBase, pre-AOS
    ARMOR_WORDS = (("plate", 40), ("chainmail", 28), ("ringmail", 22), ("close helm", 30), ("norse helm", 30), ("helmet", 30), ("bascinet", 18), ("bone", 30),
                   ("studded", 16), ("leather", 13))

    def worn_profile(self):
        """{layer: armour rating} of the armour worn on the body parts a hit can land on (danger.HIT_SHARE), for the risk of an armoured gatherer."""
        out = {}
        for it in getattr(self.c, "equipped", None) or []:
            n = (getattr(it, "name", "") or "").lower()
            ar = next((v for w, v in self.ARMOR_WORDS if w in n), 0)
            if ar and getattr(it, "layer", None) in ("Necklace", "Gloves", "Arms", "Helmet", "Pants", "Torso"):
                out[it.layer] = max(out.get(it.layer, 0), ar)
        return out

    def fight_back(self, m):
        """No way out: fight it (a caster casts: CasterBot overrides), and stay in the fight FLEE_STUCK_S (fight_until: r_flee and r_avoid keep swinging,
        fight_committed) rather than try another flight next tick. A trapped flight only swung once between flights: BotFenceAdvR, cornered by a
        lizardman pack in Despise, logged 26 "flee_trapped" in 35 s, out of war mode at its death (2026-11-07 13:58:54-13:59:29)."""
        m = self.fight_pick(m)
        self.ev("flee_trapped", at=self.mkey(m), hp=self.c.hp)
        self.facts["fight_until"] = max(float(self.facts.get("fight_until", 0) or 0), time.time() + float(getattr(self, "FLEE_STUCK_S", 20)))
        if not self.c.war_mode:
            self.c.war(True)
        self.c.attack(m.serial)
        time.sleep(1.2)
        return True

    PICK_SWITCH = 0.6           # another attacker is worth the switch only with this share or less of the current one's hit points left

    def fight_pick(self, m):
        """Of the attackers beside it (in war mode within 2 tiles), the one with the fewest hit points left, by its health bar times its kind's hit points
        (rating.creature): each one killed is one fewer hitting it, so the quickest kill comes first, as a player cornered by a pack does. The current
        target stays unless another has PICK_SWITCH of its hit points or fewer. BotMaceAdvR, boxed in by five ettins and three earth elementals on
        Despise's lower floor, swung at whichever was listed first, 101 "fighting back" lines to its death (2026-11-08 13:31-13:40)."""
        try:
            import rating
            beside = [o for o in self.mobs(2) if getattr(o, "in_war_mode", False) and not getattr(o, "is_dead", False)]
            if len(beside) < 2:
                return m

            def left(o):
                mx = getattr(o, "max_hits", 0) or 0
                pct = (getattr(o, "hits", 0) or 0) / mx if mx > 1 else 1.0
                e = rating.creature(self.mkey(o)) or {}
                hits = e.get("hits") or [50]
                return pct * (sum(hits) / len(hits))

            best = min(beside, key=left)
            cur = next((o for o in beside if getattr(o, "serial", None) == getattr(m, "serial", None)), None)
            if cur is None or left(best) <= self.PICK_SWITCH * left(cur):
                return best
        except Exception:
            pass
        return m

    # ---- selling -----------------------------------------------------------------------------------------------------------------------------------------

    def sell_due(self):
        """A trip to sell pays: the goods carried at the shops' prices (items.py) reach errands.sell_value (r x sqrt(2T / p), T the trip home), or the pack is
        heavy, or the bot is nearly broke."""
        try:
            import errands
            v = items.goods_value(self.c.backpack)
            return v >= errands.sell_value(self) or self.c.weight >= self.c.max_weight * self.SELL_HEAVY or self.c.gold < self.SELL_BROKE
        except Exception:
            return self.c.weight >= self.c.max_weight * self.SELL_HEAVY

    @property
    def BUTCHER(self):
        return self.where1(("butcher",))

    def sale_due(self, key):
        """Twenty minutes since the last sale of this kind, or, for a bot that never sold, twenty minutes played in all (the totals' uptime plus this brain):
        counting from the brain's start reset the timer at every restart and no fighter ever reached it."""
        last = self.facts.get(key)
        if last:
            return time.time() - last > 1200
        return (getattr(self, "base", {}) or {}).get("uptime", 0) + time.time() - getattr(self, "started", time.time()) > 1200

    SELL_MAX = 99                        # entries a sale may hold: the server drops a sale of 100 or more without a word (IncomingVendorPackets, VendorSellReply:
                                         # count >= 100). BotTinkAR offered 110 tongs, shovels and hatchets in one sale, sold none, and wrote off tongs as unsellable

    def sell_cart(self, cart, vendor=None):
        """Sell [serial, amount, serial, amount, ...] in sales of at most SELL_MAX entries. The server closes the vendor's list after each sale, so the list is
        opened again (vendor_list) before the next one."""
        n = self.SELL_MAX * 2
        first = True
        while cart:
            part, cart = cart[:n], cart[n:]
            if not first and vendor is not None:
                self.vendor_list(vendor, "sell")
            self.cmd("sell " + " ".join(part), timeout=10)
            time.sleep(3)
            first = False

    def r_sellmeat(self):
        """Carved meat to the Butcher when a sell trip pays (sell_due), or twenty minutes out with meat in the pack. Meat no Butcher would buy is left on the
        ground only after the sale was tried at the shop: the fighters' copy dropped it whenever the sale returned nothing, a far walk just begun included."""
        meat = [i for i in self.c.backpack if items.is_meat(i.name)]
        if not meat or self.threats(10) or time.time() - self.facts.get("meat_sold_at", 0) < 300:
            return False
        if not (self.sell_due() or self.sale_due("meat_sold_at")):
            return False
        n = sum((i.amount or 1) for i in meat)
        self.facts["meat_sold_at"] = time.time()
        self.activity = "selling meat to the Butcher"
        earned = self.sell_items(self.BUTCHER, ("raw ",))
        pending = getattr(self, "far_pending", lambda: False)()
        if pending:
            return True                                    # a far walk to the Butcher is under way (r_far carries it)
        self.log(f"sold {n} pieces of meat for {earned} gold")
        if getattr(self, "dlog", None):
            self.dlog("choice", what="sell meat", why=f"{n} pieces for {earned} gold")
        if earned <= 0 and self.c.find("raw ") is not None and max(abs(self.c.x - self.BUTCHER[0]), abs(self.c.y - self.BUTCHER[1])) <= 4:
            for it in [i for i in self.c.backpack if items.is_meat(i.name)]:
                self.drop_to_ground(it)
        return True

    GOODS_SALE_RULES = ("r_sellmeat", "r_sell_leather")      # the rules that sell goods (meat at the Butcher, leather and hides at the Tanner)
    GOODS_OUT_SHARE = 0.8                # goods come out of the box up to this share of the weight limit (BotBase.CLEAR_SHARE); a sell trip is due at 0.85

    HUE_TAIL = re.compile(r"\s*\(hue 0x([0-9A-Fa-f]+)[^)]*\)\s*$")

    def box_contents(self, box, timeout=6):
        """c.container with each stack's hue. The client's reply carries it (CommandEngine DescribeItem: "iron ingot x361 (hue 0x0972 ...)"), but
        Navrey's Python parser keeps only serial, name and amount, so every banked coloured ingot read as plain iron: BotTinkBR took 118, 104 and 120
        "iron ingots" out in 5 minutes, all coloured, banked them again when overloaded, and stood "under 5 iron ingot" with 402 in the pack
        (2026-11-02 05:40-05:45). Falls back to c.container on any error."""
        try:
            from uo.client import serial_of
            from uo.entities import Item
            lines = self.c.call(f"container {serial_of(box)}", timeout=timeout)
        except Exception:
            return self.c.container(box, timeout=timeout)
        out = []
        for line in lines:
            text = line.strip()
            is_box = text.startswith("[container]")
            for tag in ("[container]", "[item]"):
                if text.startswith(tag):
                    text = text[len(tag):].strip()
            if not text.startswith("0x"):
                continue
            parts = text.split(None, 1)
            name, amount, hue = (parts[1] if len(parts) > 1 else ""), 1, 0
            m = self.HUE_TAIL.search(name)
            if m:
                hue, name = int(m.group(1), 16), name[:m.start()]
            head, sep, tail = name.rpartition(" x")
            if sep and tail.strip().isdigit():
                name, amount = head, int(tail.strip())
            out.append(Item({"serial": parts[0], "name": name.strip(), "amount": amount, "hue": hue, "isContainer": is_box}))
        return out

    def bank_goods_out(self, box):
        """At a bank visit, goods earlier visits banked (leather, hides, meat, feathers: the casters' KEEP lacked them until 2026-10-29) come back out for the
        shops, each stack cut to the room left at its weight a piece (taking whole stacks put a caster at 348 of 250 stones, unable to walk)."""
        if not any(r in (getattr(self, "RULES", None) or ()) for r in self.GOODS_SALE_RULES):
            return self.bank_material_out(box) + self.bank_products_out(box)      # no rule of this trade sells goods: out of the box they only weigh. BotSmithAR
                                                                                  # took 32 piles of hides (160 stones) out at every visit, never sold them and
                                                                                  # banked again as "heavy" (2026-11-01)
        if self.facts.get("goods_unbanked") and time.time() - self.facts["goods_unbanked"] < 6 * 3600:
            return self.bank_material_out(box) + self.bank_products_out(box)      # (the goods came out lately; a crafter's material and products still may)
        try:
            goods = [i for i in self.c.container(box, timeout=6) if items.is_goods(i.name)]
        except Exception:
            return 0
        room = self.c.max_weight * self.GOODS_OUT_SHARE - self.c.weight      # counted down here: the client's weight lags a take
        taken, left = 0, 0
        for it in sorted(goods, key=lambda i: -(i.amount or 1)):
            u = items.unit_weight(it.name)
            n = min(int(it.amount or 1), int(room // u))
            if n <= 0:
                left += 1
                continue
            self.c.get_item(it.serial, n if (it.amount or 1) > 1 else None)
            time.sleep(1.2)
            taken += 1
            room -= n * u
            if n < int(it.amount or 1):
                left += 1
        if not left:
            self.facts["goods_unbanked"] = time.time()
        if goods:
            self.log(f"bank: took out {taken} of {len(goods)} stacks of goods to sell ({left} left in the box)")
            self.ev("goods_unbanked", taken=taken, stacks=len(goods), left=left)
        return taken + self.bank_material_out(box) + self.bank_products_out(box)

    def bank_material_out(self, box):
        """A crafter's own material in the box comes out before any is bought (CrafterBot); 0 for the other trades."""
        return 0

    PRODUCTS_OUT_SHARE = 0.5             # a crafter's banked products come out only while the pack is under half its limit: room is kept for material
    # out of gold, a player takes all the stock he can carry to the shop: BotTailAdvR had 84 sellable hats in its box and 40 gold, took 12 a visit and stood
    # idle between (8 of 11 minutes, 2026-10-31). Then the goods' share of the weight limit, and up to POOR_PRODUCTS pieces
    POOR_GOLD = 100
    POOR_PRODUCTS = 60
    POOR_OUT_SHARE = 0.6                 # under the crafters' heavy line (CRAFT_WEIGHT), so the stock taken out can be carried to the shop and crafting goes on

    VENDOR_MAX_SELL = 500      # items one sale takes (BaseVendor.MaxSell): no more of a stack comes out of the bank at once

    def bank_products_out(self, box):
        """A crafter's products banked on heavy visits come back out to sell when a shop is known to pay for them. BotCarpAdvR's box held 60 quarter
        staffs (15 gold at the Carpenter) and 22 wooden boxes (25): about 1,450 gold that nothing took out, as the goods step knew only leather, meat,
        hides and feathers (2026-10-30). At most CLEAR_N stacks a visit, the weight read again after each take."""
        # a heavy or overloaded visit only puts in: taking stock back out there looped (BotSmithAdvR at 296/362 banked as heavy and took 14 pieces out again,
        # every few minutes, 2026-11-01)
        # (at most POOR_GOLD: a bank visit leaves exactly the 100-gold purse, so "under 100" never held after one and only CLEAR_N came out: BotSmithBR
        # took 12 of 89 banked products a visit at 100 gold and walked 280 tiles to dig between, 2026-11-08 09:32-10:00)
        poor = self.c.gold <= self.POOR_GOLD and self.__dict__.get("_bank_why") not in ("heavy", "overloaded")
        share = self.POOR_OUT_SHARE if poor else self.PRODUCTS_OUT_SHARE
        limit = self.POOR_PRODUCTS if poor else getattr(self, "CLEAR_N", 12)
        if not hasattr(self, "is_product") or self.c.weight >= self.c.max_weight * share:
            return 0
        try:
            stock = [i for i in self.c.container(box, timeout=6) if self.is_product(i.name)]
        except Exception:
            return 0
        def per_stone(i):
            n = i.name.lower()
            return max([p for p, xy, item in self.mem.vendor_buying(n) if item == n] or [0]) / max(items.unit_weight(n), 0.1)
        # best price a stone first, and part of a stack that does not fit whole (BotTinkBR's 2,932 lockpicks never came out: get_item took stacks whole)
        priced = sorted([i for i in stock if per_stone(i) > 0], key=per_stone, reverse=True)
        taken = 0
        for it in priced[:limit]:
            if self.c.weight >= self.c.max_weight * share:
                break
            amt = int(it.amount or 1)
            n = amt
            if amt > 1:
                room = self.c.max_weight * share - self.c.weight
                n = min(amt, self.VENDOR_MAX_SELL, int(room // max(items.unit_weight(it.name), 0.1)))
                if n <= 0:
                    continue
            self.c.get_item(it.serial, n if n < amt else None)
            time.sleep(1.2)
            taken += 1
        if taken:
            self.log(f"bank: took out {taken} of {len(priced)} banked products a shop pays for, to sell (weight {self.c.weight}/{self.c.max_weight})")
            self.ev("products_unbanked", taken=taken, priced=len(priced))
        return taken

    # ---- small shared helpers ----------------------------------------------------------------------------------------------------------------------------

    DROP_TILES = ((0, 0), (1, 0), (0, 1), (-1, 0), (0, -1), (1, 1), (-1, 1), (1, -1), (-1, -1))

    def drop_to_ground(self, it, amount=None, box=None):
        """Put a stack (or `amount` of it) on the ground, and know it went: the engine refuses a ground drop when the tile's 20 height slots above its surface
        are full (Item.DropToWorld, m_OpenSlots), and the refusal is silent - the item comes back. Every bot shed on the same bank floor tile, so BotCarpAdvR
        "threw out" 60 board games four times in an hour and still weighed 370 of 390 (2026-10-30). The own tile first, then the eight around it (InRange 2).
        `box` is the container the item sits in when it is not the backpack. Returns True once the amount there went down."""
        amt = int(amount or it.amount or 1)

        def held():
            try:
                pool = self.c.container(box, timeout=5) if box else self.c.backpack
            except Exception:
                return None
            return sum(int(i.amount or 1) for i in pool if i.serial == it.serial)
        before = held()
        for dx, dy in self.DROP_TILES:
            try:
                self.c.call(f"dropground {it.serial} {amt} {self.c.x + dx} {self.c.y + dy}", timeout=8)
            except Exception:
                continue
            time.sleep(0.8)
            now = held()
            if before is None or now is None or now < before:
                return True
        return False

    def cursor_after(self, act, timeout=4.0):
        """Run act() (a useskill, a use, a speech order) and wait for the server's target cursor without losing it. Client.wait_for drains the log before it
        listens, and after a synchronous call() the cursor has often landed already: BotTamerAR's "Tame which animal?" came 3 ms after useskill's [CMD-END],
        was never answered, and every try for hours ended in the 30 s skill delay (AnimalTaming.OnUse) with nothing tamed (2026-10-30). True when it came."""
        from uo import Event
        self.c.events.drain()
        act()
        end = time.time() + timeout
        while time.time() < end:
            for e in self.c.events.poll():
                if e.kind == Event.TARGET_REQUEST:
                    return True
            time.sleep(0.05)
        return False

    def write_status_file(self, s):
        """status.json, written whole: to a temp file, then swapped in (the supervisor read a half-written file as "no status" and killed two healthy brains,
        2026-10-30). A swap refused while a reader holds the file is retried, then the file is written in place as before."""
        path = os.path.join(self.dir, "status.json")
        tmp = path + ".tmp"
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(s, f)
            for _ in range(5):
                try:
                    os.replace(tmp, path)
                    return
                except PermissionError:
                    time.sleep(0.05)
        except Exception:
            pass
        with open(path, "w", encoding="utf-8") as f:
            json.dump(s, f)

    def los(self, serial):
        """Is there a clear line of sight to this mobile? (the `los` command; a spell or arrow at something behind a wall is lost without a word)"""
        now = time.time()
        if now - getattr(self, "_los_at", 0) > 0.8:
            self._los = {}
            for line in self.c.call("los 12", timeout=6):
                mm = re.match(r"\s+(YES|no)\s+(0x[0-9A-Fa-f]+)", line)
                if mm:
                    self._los[mm.group(2).upper()] = mm.group(1) == "YES"
            self._los_at = now
        return self._los.get(serial.upper(), True)

    def find_gump(self, word):
        serial = None
        found = None
        for line in self.c.call("gumps", timeout=8):
            mm = re.match(r"\[GUMP\] local \S+ server (0x[0-9A-Fa-f]+)", line)
            if mm:
                serial = mm.group(1)
            elif word in line and serial and not found:
                found = serial
        return found

    def target_died(self, f):
        """The fight's own target died, not just any corpse in view: a new corpse where the target last stood, or the target gone when last seen badly hurt."""
        x, y = f.get("xy", (None, None))
        for c in self.c.containers(within=16):
            if "corpse" in c.name.lower() and c.serial not in f.get("corpses0", set()) and x is not None and abs(c.x - x) <= 2 and abs(c.y - y) <= 2:
                return True
        return f.get("pct", 100) <= 25


# ---- module helpers several brains' modules shared as copies ----------------------------------------------------------------------------------------------

def cell_at(x, y):
    """memory.cell_of, else the 40-tile cell by hand (the memory module not loaded)."""
    try:
        from memory import cell_of
        return cell_of(x, y)
    except Exception:
        return f"{int(x) // 40 * 40},{int(y) // 40 * 40}"


def bot_cell(bot):
    try:
        from memory import cell_of
        return cell_of(bot.c.x, bot.c.y)
    except Exception:
        return None


_WR = None


def walkroute_mod():
    """walkroute with its grid loaded, or None where it or its grid cannot be loaded (callers keep their plain walks)."""
    global _WR
    if _WR is None:
        try:
            import walkroute
            walkroute.get()
            _WR = walkroute
        except Exception:
            _WR = False
    return _WR or None


def emit(bot, name, **kw):
    """A structured event through the bot's decision log, with its cell and rule (guildtalk.py, marketvoice.py)."""
    try:
        bot.dlog("ev", ev=name, cell=bot_cell(bot), rule=getattr(bot, "current_rule", None) or getattr(bot, "last_rule", None), **kw)
    except Exception:
        pass

