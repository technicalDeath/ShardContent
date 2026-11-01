"""Skill plans (feature "skill_plan"; owner, 2026-11-01: "Do a pass at giving each bot type a full set of skills to fill out their 700 points that will
help them in their goals, and give them the behavior and logic to use them").

A real UO:R player chose seven skills that served the character's living and set the skill locks so the rest could fall: up on what was still rising, locked
on what had reached its target, down on everything else (the total is capped at 700, the shard's caps 700/100/225, so a skill gains past the cap only while
another one set down loses). The bots never touched their locks, so their 700 points drifted into whatever they happened to use: Camping and Cooking on
fighters, Wrestling on archers, Meditation everywhere.

    TEMPLATES     the profession's target skills and values (era templates, docs/Bot-Farm-Skill-Plans.md for the sources)
    tick(bot)     every PLAN_EVERY s (and at the first tick): read the skills (value, base, lock), set each lock to what the plan wants, record the plan's
                  state in bot.facts["skill_plan"] (behaviour code reads which skills are wanted with wants()/target())
Events: skill_locks {up, locked, down}, skill_plan {total, missing}.
"""
from __future__ import annotations

import re
import time

CAP = 700.0
PLAN_EVERY = 1800
SKILL_RE = re.compile(r"\[SKILL\]\s+(.+?)\s+(\d+\.\d)\s+\(base\s+(\d+\.\d)\)\s+(up|dn|locked)")

def _t(*skills):
    return {k: 100.0 for k in skills}


DEXXER = ("Tactics", "Anatomy", "Healing", "Parrying", "Resisting Spells", "Hiding")
# by the profession's name as the bots know it (BotBase.pname); docs/Bot-Farm-Skill-Plans.md gives the era source of each
TEMPLATES: dict[str, dict[str, float]] = {
    "AnimalTamer": _t("Animal Taming", "Animal Lore", "Veterinary", "Archery", "Tactics", "Anatomy", "Healing"),
    "Ranger": _t("Archery", "Tactics", "Anatomy", "Healing", "Animal Taming", "Tracking", "Hiding"),
    "Archer": _t("Archery", "Tactics", "Anatomy", "Healing", "Resisting Spells", "Bowcraft/Fletching", "Lumberjacking"),
    "Swordsman": _t("Swordsmanship", *DEXXER),
    "MaceFighter": _t("Mace Fighting", *DEXXER),
    "Fencer": _t("Fencing", *DEXXER),
    "Bard": _t("Musicianship", "Provocation", "Peacemaking", "Archery", "Tactics", "Anatomy", "Healing"),
    "PureMage": _t("Magery", "Evaluating Intelligence", "Meditation", "Resisting Spells", "Wrestling", "Tactics", "Anatomy"),
    "Sorcerer": _t("Magery", "Evaluating Intelligence", "Meditation", "Inscription", "Resisting Spells", "Wrestling", "Anatomy"),
    "Warlock": _t("Magery", "Evaluating Intelligence", "Meditation", "Resisting Spells", "Fencing", "Tactics", "Anatomy"),
    "Prospector": _t("Mining", "Blacksmithy", "Tinkering", "Hiding", "Healing", "Anatomy", "Wrestling"),
    "Blacksmith": _t("Blacksmithy", "Mining", "Tinkering", "Hiding", "Healing", "Anatomy", "Wrestling"),
    "Tinker": _t("Tinkering", "Mining", "Lumberjacking", "Carpentry", "Hiding", "Healing", "Anatomy"),
    "Carpenter": _t("Carpentry", "Lumberjacking", "Swordsmanship", "Tactics", "Anatomy", "Healing", "Hiding"),
    "Tailor": _t("Tailoring", "Swordsmanship", "Tactics", "Anatomy", "Healing", "Tracking", "Hiding"),
    "Fisherman": _t("Fishing", "Cooking", "Wrestling", "Tactics", "Anatomy", "Healing", "Hiding"),
}
assert all(abs(sum(t.values()) - CAP) < 0.01 and len(t) == 7 for t in TEMPLATES.values())


def plan_of(bot):
    """The bot's template: by profession (bot.pname), with a per-bot override in TEMPLATES under the bot's name."""
    return TEMPLATES.get(getattr(bot, "name", "")) or TEMPLATES.get(getattr(bot, "pname", "") or "")


def read(bot):
    """{skill: (value, base, lock)} from the client's skill list (Navrey 'skills'), lock 'up' | 'dn' | 'locked'."""
    out = {}
    for line in bot.c.call("skills", timeout=8):
        m = SKILL_RE.match(line.strip())
        if m:
            out[m.group(1).strip()] = (float(m.group(2)), float(m.group(3)), m.group(4))
    return out


def wanted_locks(table, plan):
    """{skill: lock} the plan wants: up below the target, locked at it, down for every other skill with points in it."""
    want = {}
    for name, (_v, base, lock) in table.items():
        if name in plan:
            want[name] = "up" if base < plan[name] else "locked"
        elif base > 0:
            want[name] = "dn"
    for name, target in plan.items():
        if name not in table:
            want[name] = "up"                             # not in the list yet (no points): up, so it can rise
    return want


def tick(bot, now=None):
    now = now or time.time()
    if not bot.feature("skill_plan") or bot.c.ghost:
        return False
    plan = plan_of(bot)
    if not plan:
        return False
    st = bot.facts.setdefault("skill_plan", {})
    if now - st.get("at", 0) < PLAN_EVERY:
        return False
    st["at"] = now
    table = read(bot)
    if not table:
        return False
    want = wanted_locks(table, plan)
    changed = {"up": [], "locked": [], "dn": []}
    for name, lock in want.items():
        have = table.get(name, (0, 0, None))[2]
        if have != lock:
            try:
                bot.c.call(f"skilllock {name} {'down' if lock == 'dn' else lock}", timeout=5)
                changed[lock].append(name)
            except Exception as e:
                bot.log(f"skill plan: {name} {lock} failed ({type(e).__name__}: {e})")
    total = round(sum(b for _v, b, _l in table.values()), 1)
    missing = {k: round(t - table.get(k, (0, 0, ""))[1], 1) for k, t in plan.items() if table.get(k, (0, 0, ""))[1] < t}
    st.update(total=total, missing=missing, plan=dict(plan))
    if any(changed.values()):
        bot.log(f"skill plan: locks up {changed['up']}, locked {changed['locked']}, down {changed['dn']} (base total {total})")
        bot.ev("skill_locks", up=changed["up"], locked=changed["locked"], down=changed["dn"])
    bot.ev("skill_plan", total=total, missing=missing)
    return True


def wants(bot, skill):
    """True when the bot's plan holds this skill and it is still below its target (behaviour code: worth practising)."""
    st = (getattr(bot, "facts", None) or {}).get("skill_plan") or {}
    return skill in (st.get("missing") or {})


def target(bot, skill):
    plan = plan_of(bot) or {}
    return plan.get(skill, 0.0)
