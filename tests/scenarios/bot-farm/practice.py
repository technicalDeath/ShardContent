"""Practice from the book (Operator's board item 15:00; the Helper). Pure functions for CasterBot.r_practice and SpellbookMixin.book_wants, written into the bot-farm folder by
patch_practice_book.py.

The finding: the practice cohort was paused at 12:47. Its fixed PRACTICE list (Bless, Arch Cure, Arch Protection, Greater Heal, Magic Reflection, Reveal) is mostly circle 4+, which
no shop sells, so a filled starter book had nothing to practise and the casters stood still with full mana.

What a caster practises now (feature "practice"): any spell of SAFE below that the BOOK HOLDS (spellbook.spell_ok), that is challenging at its Magery (success 0.2-0.98, so a cast can
still teach), with the reagents carried and the mana to spare; the one with the best expected skill gain per mana. SAFE is the spells that do nothing harmful cast on oneself or
at nothing: no damage, no summons, no field or wall, no debuff, nothing that needs a rune or an item, nothing that changes the character (incognito, invisibility, polymorph) and
no Create Food (its food would weigh the pack down).
The expected gain of one cast comes from the server's own skill check (Skills.CheckSkill, UO:R rules): with chance p (the success chance, here (skill - min) / (max - min)) the gain
chance is (b + (1 - p) * (0.5 on success, 0.2 on failure)) / 2 * the skill's gain factor, b being how far the skill is from its cap; so
    gain(p) = p * (b + (1 - p) * 0.5) + (1 - p) * (b + (1 - p) * 0.2),  b = 1 - skill / 100
(the constant factors drop out of the comparison). A failed cast costs the mana and the reagents too, so the score is gain(p) / (mana + half the reagent gold).
A streak: once a practice cast was made, the next ones follow every tick while the mana after the cast stays above 40% of the maximum (a fresh streak starts at 60%), instead of one
cast every 20 seconds. The rule's other conditions are as before: no danger within 10, nothing to hunt within 9, not a ghost.
For the book: wants(bot) is empty while the book holds a spell that qualifies; else the best SAFE spell of circles 1 to 3 (the circles a stock Mage shop sells) that is challenging, so
r_book buys the next challenging low-circle spell first.
"""
SAFE = {                                   # spell -> target of the cast: "self" or None (no target cursor)
    "heal": "self", "night sight": "self", "agility": "self", "cunning": "self", "strength": "self", "cure": "self", "bless": "self",
    "protection": None, "reactive armor": None, "greater heal": "self", "arch cure": "self", "arch protection": "self", "magic reflection": None, "reveal": "self",
}
LOW, HIGH = 0.2, 0.98
BUY_CIRCLES = 3
STREAK_S = 15
START_FLOOR, STREAK_FLOOR = 0.6, 0.4


def gain_chance(p, skill):
    b = max(0.0, 1.0 - skill / 100.0)
    return p * (b + (1.0 - p) * 0.5) + (1.0 - p) * (b + (1.0 - p) * 0.2)


def options(bot, mana=None, reserve=0.0, held_only=True, ready=True):
    """The practice spells, best expected gain per mana first: dicts {name, key, target, p, score, circle}. ready=False leaves out the reagent and mana checks (for the shop list)."""
    k = bot.k
    out = []
    for key, target in SAFE.items():
        if held_only and not bot.spell_ok(key):
            continue
        s = k.spell(key)
        if not s or not k.challenging(s, bot.skill):
            continue
        p = k.success(s, bot.skill)
        if not (LOW <= p <= HIGH):
            continue
        if ready and (not k.reagent_ok(s, bot.regs) or s["mana"] > (bot.c.mana if mana is None else mana) - reserve):
            continue
        score = gain_chance(p, bot.skill) / (s["mana"] + 0.5 * k.gold_per_cast(s))
        out.append({"name": s["name"], "key": key, "target": target, "p": p, "score": score, "circle": s["circle"]})
    out.sort(key=lambda o: (-o["score"], o["circle"]))
    return out


def wants(bot):
    """Spell names r_book should buy for practice, best first: nothing while the book holds a qualifying spell."""
    if options(bot, held_only=True, ready=False):
        return []
    return [o["key"] for o in options(bot, held_only=False, ready=False) if o["circle"] <= BUY_CIRCLES]


PRACTICE_PURSE = 150


class PracticeMixin:
    def practice_affordable(self):
        """Practice burns reagents and earns nothing: only with gold carried + banked >= PRACTICE_PURSE (patch_caster_budget.py)."""
        return (self.c.gold or 0) + (self.facts.get("bank_balance", 0) or 0) >= PRACTICE_PURSE

    def practice_streak(self):
        return __import__("time").time() - self.facts.get("practice_at", 0) < STREAK_S

    def practice_floor(self, top):
        return (STREAK_FLOOR if self.practice_streak() else START_FLOOR) * top

    def practice_gap(self):
        return 0 if self.practice_streak() else 20
