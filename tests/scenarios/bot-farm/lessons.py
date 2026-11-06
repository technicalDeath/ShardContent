"""Lessons from NPC trainers (feature "lessons"; owner, 2026-11-05: "adding NEW bot capabilities, I want them doing things they haven't done before").

A new UO:R player bought the first third of a skill from a town's NPCs instead of grinding it from zero. The engine's rules (BaseCreature):
  - an NPC teaches a skill whose base is 60 or more (OnSpeech HandleTraining, CheckTeachSkills), up to a third of its base and never past 42.0;
  - its context menu has a "Train <skill>" entry per skill (TeachEntry, cliloc 6000 + the skill's number); choosing it, the NPC quotes "I will teach thee
    all I know, if paid the amount in full. The price is: N" (1019077), N the tenths of a point to learn: one gold a tenth;
  - gold dropped on it after the quote buys that many tenths (OnGoldGiven -> Teach(..., dropped.Amount, true)), "Your skill level increases." (501540);
    gold dropped on an NPC with no quote standing is simply kept ("Thou art giving me gold?"), so a bot pays only right after the quote it heard.
LESSONS is each vendor type's guaranteed lesson per skill: a third of the lowest skill its definition rolls (SetSkill min / 3, at most 42), from the
engine's NPC files (Mobiles/Vendors/NPC, 2026-11-05) for the types the gazetteer places. A skill the bot's plan (skillplan.TEMPLATES) holds and that a
lesson raises by MARGIN or more is bought at the nearest trainer within LESSON_NEAR tiles, once per LESSON_GAP, a refusal (knows enough, the skill cap,
no entry, no quote) keeping that skill and trainer type off for FAIL_KEEP.
Events: lesson {skill, trainer, type, price, before, ok}, lesson_skip {skill, type, why}.
"""
from __future__ import annotations

import re
import time

# vendor type -> {skill as the client names it: the lesson it always gives (a third of its definition's lowest roll)}
LESSONS = {
    "Alchemist": {"Alchemy": 28.3, "Taste Identification": 21.7},
    "AnimalTrainer": {"Animal Lore": 21.3, "Animal Taming": 30.0, "Veterinary": 21.7},
    "Armorer": {"Arms Lore": 21.3, "Blacksmithy": 20.0},
    "Baker": {"Cooking": 25.0},
    "Bard": {"Discordance": 21.3, "Musicianship": 21.3, "Peacemaking": 21.7, "Provocation": 20.0},
    "BardGuildmaster": {"Archery": 26.7, "Discordance": 26.7, "Musicianship": 26.7, "Peacemaking": 26.7, "Provocation": 26.7, "Swordsmanship": 26.7},
    "Blacksmith": {"Blacksmithy": 21.7, "Fencing": 20.0, "Mace Fighting": 20.3, "Swordsmanship": 20.0, "Tactics": 20.0, "Parrying": 20.3},
    "BlacksmithGuildmaster": {"Arms Lore": 21.7, "Blacksmithy": 30.0},
    "Bowyer": {"Bowcraft/Fletching": 26.7, "Archery": 26.7},
    "Carpenter": {"Carpentry": 28.3, "Lumberjacking": 20.0},
    "Cobbler": {"Tailoring": 20.0},
    "Cook": {"Cooking": 30.0, "Taste Identification": 25.0},
    "Fisherman": {"Fishing": 25.0},
    "Furtrader": {"Animal Lore": 28.3},
    "Healer": {"Forensic Evaluation": 26.7, "Spirit Speak": 26.7, "Swordsmanship": 26.7},
    "HealerGuildmaster": {"Anatomy": 28.3, "Healing": 30.0, "Forensic Evaluation": 25.0, "Resisting Spells": 25.0, "Spirit Speak": 21.7},
    "Herbalist": {"Alchemy": 26.7, "Cooking": 26.7, "Taste Identification": 26.7},
    "Jeweler": {"Item Identification": 21.3},
    "Mage": {"Evaluating Intelligence": 21.7, "Inscription": 20.0, "Magery": 21.3, "Meditation": 20.0, "Resisting Spells": 21.7},
    "MageGuildmaster": {"Evaluating Intelligence": 28.3, "Inscription": 21.7, "Resisting Spells": 21.3, "Magery": 30.0, "Wrestling": 20.0, "Meditation": 28.3},
    "Mapmaker": {"Cartography": 30.0},
    "MerchantGuildmaster": {"Item Identification": 28.3, "Arms Lore": 28.3},
    "MinerGuildmaster": {"Item Identification": 20.0, "Mining": 30.0},
    "Scribe": {"Evaluating Intelligence": 20.0, "Inscription": 30.0},
    "Shipwright": {"Carpentry": 20.0},
    "Tailor": {"Tailoring": 21.3},
    "TailorGuildmaster": {"Tailoring": 30.0},
    "TinkerGuildmaster": {"Lockpicking": 21.7, "Tinkering": 30.0, "Remove Trap": 28.3},
    "WarriorGuildmaster": {"Arms Lore": 25.0, "Parrying": 28.3, "Resisting Spells": 20.0, "Tactics": 28.3, "Swordsmanship": 30.0, "Mace Fighting": 20.0,
                           "Fencing": 20.0},
    "Weaponsmith": {"Arms Lore": 21.3, "Blacksmithy": 21.7},
    "Weaver": {"Tailoring": 21.7},
}
MARGIN = 2.0               # points a lesson must add over what the bot has to be worth the walk
LESSON_NEAR = 100          # tiles to the trainer: a walk inside the town, short of far.FAR (120)
LESSON_GAP = 600           # s between lesson tries
FAIL_KEEP = 6 * 3600       # s a refused (skill, trainer type) stays off
WALK_KEEP = 1200           # s a trainer the walk did not reach stays off (a walk that stopped short, not a refusal)
PRICE_SLACK = 1.2          # the quote may exceed the guaranteed lesson (the NPC rolled more skill): carried gold covers this much over
PURSE_KEEP = 40            # gold kept back after paying
ENTRY_RE = re.compile(r"\[entry (\d+)\]\s+(.+)")
PRICE_RE = re.compile(r"price is:?\s*(\d+)", re.I)


def entry_matches(skill, text):
    """True when a context entry ("Train Blacksmithing", "Train Arms Lore": the client's cliloc 6000 + skill names, not the skills list's) is this skill's:
    every word of the skill's name starts (5 letters) a word of the entry's; for a name with a slash ("Bowcraft/Fletching") either half will do."""
    t = (text or "").strip().lower()
    if not t.startswith("train "):
        return False
    words = re.split(r"[\s/]+", t[6:])
    def hit(w):
        return any(x[:5] == w[:5] for x in words if x)
    parts = [w for w in re.split(r"[\s/]+", skill.lower()) if w]
    if "/" in skill:
        return any(hit(w) for w in parts)
    return all(hit(w) for w in parts)


def wanted(plan, have, near_types):
    """[(gain, skill, level, type)] best gain first: the plan's skills a trainer type in near_types teaches MARGIN or more above what the bot has."""
    out = []
    for skill in plan:
        cur = float(have.get(skill, 0.0) or 0.0)
        best = None
        for t in near_types:
            lvl = LESSONS.get(t, {}).get(skill)
            if lvl is not None and lvl - cur >= MARGIN and (best is None or lvl > best[0]):
                best = (lvl, t)
        if best:
            out.append((round(best[0] - cur, 1), skill, best[0], best[1]))
    return sorted(out, reverse=True)


class LessonMixin:
    def lesson_on(self):
        return self.feature("lessons")

    def lesson_have(self):
        """{skill: base} the lesson gate reads (CheckTeachSkills compares bases): refresh_skills' bases, else the values."""
        have = dict(getattr(self, "skill_values", {}) or {})
        have.update(self.__dict__.get("skill_bases") or {})
        return have

    def lesson_trainers(self):
        """{type: (x, y)} the nearest place of each trainer type within LESSON_NEAR tiles, on this side (gazetteer, spawner:Vendors)."""
        try:
            import gazetteer as gz
            g = gz.get()
            side = g.side(int(self.c.x), int(self.c.y))
            best = {}
            for p in g.places:
                t = p.get("type")
                if t not in LESSONS or not str(p.get("src", "")).startswith("spawner:Vendors") or p.get("side", "surface") != side:
                    continue
                d = max(abs(int(p["x"]) - self.c.x), abs(int(p["y"]) - self.c.y))
                if d <= LESSON_NEAR and (t not in best or d < best[t][0]):
                    best[t] = (d, (int(p["x"]), int(p["y"])))
            return {t: v[1] for t, v in best.items()}
        except Exception:
            return {}

    def lesson_choice(self):
        """(gain, skill, level, type, (x, y)) of the lesson to take now, or None."""
        try:
            import skillplan
            plan = skillplan.plan_of(self) or {}
        except Exception:
            plan = {}
        if not plan:
            return None
        trainers = self.lesson_trainers()
        refused = self.facts.get("lesson_refused") or {}
        now = time.time()
        types = [t for t in trainers]
        for gain, skill, level, ttype in wanted(plan, self.lesson_have(), types):
            if float(refused.get(f"{skill}|{ttype}", 0) or 0) > now:
                continue
            return gain, skill, level, ttype, trainers[ttype]
        return None

    def lesson_refuse(self, skill, ttype, why, keep=FAIL_KEEP):
        self.facts.setdefault("lesson_refused", {})[f"{skill}|{ttype}"] = time.time() + keep
        self.ev("lesson_skip", skill=skill, type=ttype, why=why)
        self.log(f"lesson: {skill} at a {ttype}: {why}")

    def r_lesson(self):
        """Feature lessons: buy the first third of a planned skill from a town NPC (the module doc)."""
        if not self.lesson_on() or self.c.ghost:
            return False
        now = time.time()
        if now < float(self.facts.get("lesson_next", 0) or 0):
            return False
        try:
            if self.hp_pct() < 70 or self.threats(12) or self.c.weight > self.c.max_weight * 0.9:
                return False
        except Exception:
            return False
        ch = self.lesson_choice()
        self.facts["lesson_next"] = now + LESSON_GAP
        if ch is None:
            return False
        gain, skill, level, ttype, xy = ch
        price_max = int(round(gain * 10 * PRICE_SLACK)) + 1
        if (self.c.gold or 0) < price_max + PURSE_KEEP:
            if float(self.facts.get("bank_balance", 0) or 0) >= price_max + 200 and hasattr(self, "visit_bank"):
                self.activity = f"taking gold out for a {skill} lesson"
                self.visit_bank("lesson", withdraw=price_max + PURSE_KEEP + 60)
                self.facts["lesson_next"] = now + 30                    # the lesson itself right after the bank
                return True
            return False
        self.activity = f"walking to a {ttype} for a {skill} lesson"
        self.__dict__["_walk_again_once"] = True                  # walk_again's second try and the walk grid's route for this walk (bot_common's goto wrapper)
        try:
            self.goto_near(xy[0], xy[1], 3).wait(timeout=120)
        finally:
            self.__dict__.pop("_walk_again_once", None)
        if max(abs(self.c.x - xy[0]), abs(self.c.y - xy[1])) > 8:
            self.lesson_refuse(skill, ttype, f"did not reach the trainer at {xy[0]},{xy[1]}", keep=WALK_KEEP)
            return True
        self.activity = f"asking for a {skill} lesson"
        people = [m for m in self.c.mobiles(within=10) if getattr(m, "notoriety", "") in ("Innocent", "Invulnerable") and m.name and not m.name.startswith("Bot")]
        for m in sorted(people, key=lambda m: getattr(m, "distance", 9) or 9)[:6]:
            try:
                lines = self.c.call(f"contextmenu {m.serial}", timeout=6)
            except Exception:
                continue
            idx = None
            for line in lines:
                e = ENTRY_RE.search(line)
                if e and entry_matches(skill, e.group(2)):
                    idx = int(e.group(1))
                    break
            if idx is None:
                continue
            if (getattr(m, "distance", 9) or 9) > 1:
                self.c.goto(m.x, m.y).wait(timeout=8)                     # gold is dropped on the NPC from beside it
            before = float(self.lesson_have().get(skill, 0.0) or 0.0)
            self.c.events.drain()
            self.c.call(f"contextpick {m.serial} {idx}", timeout=5)
            price, refusal = None, None
            end = time.time() + 5
            while time.time() < end and price is None and refusal is None:
                time.sleep(0.4)
                for ev in self.c.events.poll():
                    t = ev.text or ""
                    if not t.startswith(f"[SAY] {m.name}:") and "[SYSTEM]" not in t:
                        continue
                    p = PRICE_RE.search(t)
                    if p:
                        price = int(p.group(1))
                    elif re.search(r"cannot teach thee|knowest|marked to raise|skill cap", t, re.I):
                        refusal = t[:80]
            if refusal or price is None:
                self.lesson_refuse(skill, ttype, f"{m.name}: {refusal or 'no quote'}")
                return True
            if price <= 0 or price > (self.c.gold or 0) - PURSE_KEEP:
                self.lesson_refuse(skill, ttype, f"{m.name} asks {price} gold, {self.c.gold} carried")
                return True
            coin = max((i for i in self.c.backpack if (i.name or "").lower().startswith("gold coin")), key=lambda i: i.amount or 1, default=None)
            if coin is None:
                return True
            self.c.events.drain()
            self.c.call(f"drop {coin.serial} {m.serial} {price}", timeout=6)
            ok = False
            end = time.time() + 4
            while time.time() < end and not ok:
                time.sleep(0.4)
                ok = any("skill level increases" in (ev.text or "").lower() for ev in self.c.events.poll())
            self.ev("lesson", skill=skill, trainer=m.name, trainer_type=ttype, price=price, before=round(before, 1), ok=ok)
            self.log(f"lesson: {skill} from {m.name} ({ttype}) for {price} gold: {'taught' if ok else 'no answer'} (from {before:.1f})")
            if ok:
                self.facts["skills_at"] = 0                                 # the skills list read again at the next tick
                now_base = round(before + price / 10.0, 1)                  # one gold a tenth (BaseCreature.Teach): the base it was taught to
                for key in ("skill_bases", "_lesson_bases"):                # (the caster's lesson_have cache too) so the next choice does not repeat it
                    d = self.__dict__.get(key)
                    if isinstance(d, dict):
                        d[skill] = max(float(d.get(skill, 0) or 0), now_base)
                self.facts["lesson_next"] = time.time() + 60               # the next planned skill soon after
                self.note("training", f"An NPC's context menu offers 'Train <skill>'; it quotes a price (one gold a tenth of a point) and teaches when the gold is dropped on it: {skill} for {price} gold.", key="lesson")
            else:
                self.lesson_refuse(skill, ttype, f"{m.name} took no lesson payment")
            return True
        self.lesson_refuse(skill, ttype, "no NPC here offered the lesson")
        return True
