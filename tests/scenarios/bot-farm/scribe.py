"""Scribes (owner 2026-10-18: "if no bots use inscription today ... make scrolls and trade them", then "we already have sorcerers who can scribe, so we
don't need new ones"); feature "scribe". Mixin for CasterBot (ScribeMixin): a caster with Inscription (the Sorcerer template starts at 42) scribes like a player.

The era's inscription (ModernUO T2A InscriptionMenu, DefInscription): double-click a scribe's pen, target a blank scroll, then "Which circle of spells?" and
"Which spell would you like to scribe?"; only spells the spellbook holds are offered. A scroll costs one blank scroll, the spell's reagents and its mana;
a failure loses some of the materials. Skill windows by circle (pre-AOS): 1st -25..25, 2nd -10.8..39.2, 3rd 3.5..53.5, 4th 17.8..67.8, 5th 32.1..82.1,
6th 46.4..96.4, 7th 60.7..110.7, 8th 75..125; success = (Inscription - min) / 50.
What a vendor pays (shard crafted-goods pricing for scrolls, owner 2026-10-18): the material cost (blank scroll 5, black pearl and blood moss 5, other
reagents 3) times 1.25, at least the stock price (2 x circle + 2). A Mage shop sells Recall (42) and Mark (62) since the same day (extraVendorStock).

A SESSION (rule r_scribe, every SESSION_GAP while no hostile is near and the bot is well): at the home Mage shop, the scribe
 * buys a pen when it has none, and the Recall and Mark scrolls for its own book when a shop sells them and it can spare the gold (dragged into the book:
   a scribe copies from its book, and every Recall it makes is one more trip by rune for some bot);
 * picks the spell to scribe: of the spells in its book, the best expected gold per attempt (success x pay - materials lost) plus a bonus while the skill
   can still rise (success under 95%); Recall first while its own stock is under KEEP["recall"] and it succeeds RECALL_FIRST of the time;
 * buys the blank scrolls and reagents for BATCH scrolls (what the gold allows above RESERVE), scribes until the batch, the materials or the mana run out;
 * sells what it made at the same shop, keeping KEEP of Recall and Mark for its runes.
Events (decisions.jsonl): scribe_session {spell, made, failed, sold, gold, minutes}, scribe_pick {spell, chance, value}, scribe_book {spell}.
"""
import math
import re
import time

SESSION_GAP = 1800
BATCH = 10
RESERVE = 120
KEEP = {"recall": 3, "mark": 2}
MIN_INSCRIPTION = 15.0
RECALL_FIRST = 0.4                           # Recall comes first from this success up (at 42 Inscription, 48%: a small loss per scroll, but every bot's runes need them)
SKILL_EVERY = 600
WINDOW = {1: -25.0, 2: -10.8, 3: 3.5, 4: 17.8, 5: 32.1, 6: 46.4, 7: 60.7, 8: 75.0}
SPAN = 50.0
MANA = {1: 4, 2: 6, 3: 9, 4: 11, 5: 14, 6: 20, 7: 40, 8: 50}
PRICE = {"BlackPearl": 5, "Bloodmoss": 5, "Garlic": 3, "Ginseng": 3, "MandrakeRoot": 3, "Nightshade": 3, "SpidersSilk": 3, "SulfurousAsh": 3}
BLANK = 5
LOSS = 0.5                                   # share of the materials a failure costs (a guess; the craft system loses "some")
GAIN_BONUS = 2.0
SHOP_LINE = re.compile(r"(0x[0-9A-Fa-f]+)\s+(\d+)gp\s+x(\d+)\s+(.+)")
REAGENT_NAMES = {"blackpearl": "BlackPearl", "bloodmoss": "Bloodmoss", "garlic": "Garlic", "ginseng": "Ginseng", "mandrakeroot": "MandrakeRoot",
                 "nightshade": "Nightshade", "spiderssilk": "SpidersSilk", "sulfurousash": "SulfurousAsh"}
CIRCLE_TEXT = {1: "first circle", 2: "second circle", 3: "third circle", 4: "fourth circle", 5: "fifth circle", 6: "sixth circle", 7: "seventh circle", 8: "eighth circle"}
OUTCOME = re.compile(r"you create|you fail|failed to create|not have enough mana|enough mana|worn out|don't have that spell|do not have that spell|"
                     r"you don't have the|not have the resources|cannot|must have", re.I)


def norm(s):
    return re.sub(r"[^a-z]", "", (s or "").lower())


def success(skill, circle):
    return max(0.0, min(1.0, (skill - WINDOW[circle]) / SPAN))


def cost_of(reagents):
    return BLANK + sum(PRICE.get(r, 3) for r in reagents)


def pay_of(circle, reagents):
    return max(2 * circle + 2, math.ceil(cost_of(reagents) * 1.25))


def value_of(skill, circle, reagents):
    """Expected gold per attempt, plus a bonus while the skill can rise."""
    p = success(skill, circle)
    c = cost_of(reagents)
    v = p * pay_of(circle, reagents) - c * (p + (1 - p) * LOSS)
    return v + (GAIN_BONUS if 0.05 < p < 0.95 else 0.0)


class ScribeMixin:
    # ---- what the scribe knows -------------------------------------------------------------------------------------------------------------------

    def scribe_on(self):
        return self.feature("scribe")

    def scribe_skill(self, force=False):
        """Inscription, read from the skills list every SKILL_EVERY (CasterBot keeps only Magery itself)."""
        st = self.facts.setdefault("scribe", {})
        if force or time.time() - st.get("skill_at", 0) > SKILL_EVERY:
            st["skill_at"] = time.time()
            try:
                for line in self.c.call("skills", timeout=8):
                    m = re.match(r"\[SKILL\]\s+Inscription\s+(\d+\.\d)", line)
                    if m:
                        st["skill"] = float(m.group(1))
            except Exception:
                pass
        return float(st.get("skill", 0.0))

    def scribe_pack(self):
        try:
            return list(self.c.backpack or [])
        except Exception:
            return []

    def scribe_pen(self):
        return next((i for i in self.scribe_pack() if "pen" in norm(i.name) and "open" not in norm(i.name)), None)

    def scribe_count(self, word):
        return sum((i.amount or 1) for i in self.scribe_pack() if norm(i.name) == word)

    def scribe_scrolls_of(self, spell):
        """Scrolls of a spell in the pack: the client names a Recall scroll "Recall", a Mark scroll "Mark Scroll"."""
        n = norm(spell)
        return [i for i in self.scribe_pack() if norm(i.name) in (n, n + "scroll")]

    def scribe_regs(self):
        have = {}
        for i in self.scribe_pack():
            k = REAGENT_NAMES.get(norm(i.name))
            if k:
                have[k] = have.get(k, 0) + (i.amount or 1)
        return have

    def scribe_choices(self, skill):
        """[(value, spell name, circle, reagents)] for the spells the book holds, best first."""
        out = []
        for s in self.k.spells.values():
            c = s["circle"]
            if c not in WINDOW or not self.spell_ok(s["name"]):
                continue
            out.append((round(value_of(skill, c, s["reagents"]), 2), s["name"], c, s["reagents"]))
        out.sort(reverse=True)
        return out

    def scribe_pick(self, skill):
        """The spell for this session: Recall while the scribe holds fewer than KEEP and succeeds RECALL_FIRST of the time, else the best value."""
        ch = self.scribe_choices(skill)
        if not ch:
            return None
        rec = next((c for c in ch if c[1].lower() == "recall"), None)
        if rec and success(skill, 4) >= RECALL_FIRST and len(self.scribe_scrolls_of("recall")) < KEEP["recall"]:
            return rec
        return ch[0] if ch[0][0] > 0 else None

    # ---- the shop ----------------------------------------------------------------------------------------------------------------------------------

    def scribe_vendors(self):
        return sorted([m for m in self.c.mobiles(within=10) if m.notoriety == "Innocent" and m.name and not m.name.startswith("Bot")], key=lambda m: m.distance)[:6]

    def scribe_buy(self, wants):
        """wants: [(word in the item name, quantity)]. Buys at the first vendor whose list has them; returns {word: bought}."""
        got = {}
        for v in self.scribe_vendors():
            lines = self.vendor_list(v, "buy")
            rows = [m for m in (SHOP_LINE.search(l) for l in lines) if m]
            if not rows:
                continue
            cart, spend = [], 0
            for word, qty in wants:
                row = next((r for r in rows if norm(r.group(4)) == word), None)
                if row is None or qty <= 0:
                    continue
                price, avail = int(row.group(2)), int(row.group(3))
                n = min(qty, avail, max(0, (self.c.gold - RESERVE - spend) // max(1, price)))
                if n > 0:
                    cart += [row.group(1), str(n)]
                    spend += n * price
                    got[word] = n
            if cart:
                self.cmd("buy " + " ".join(cart), timeout=10)
                time.sleep(2)
                return got
        return got

    def scribe_sell(self, spell):
        """Sell the scrolls of this session's spell (and any other made scroll), keeping KEEP of Recall and Mark."""
        keep = KEEP.get(spell.lower(), 0)
        for v in self.scribe_vendors():
            lines = self.vendor_list(v, "sell")
            rows = [m for m in (SHOP_LINE.search(l) for l in lines) if m]
            if not rows:
                continue
            mine = [r for r in rows if norm(r.group(4)) in (norm(spell), norm(spell) + "scroll")]
            mine = mine[keep:] if keep else mine
            if not mine:
                return 0
            gold0 = self.c.gold
            self.cmd("sell " + " ".join(f"{r.group(1)} {r.group(3)}" for r in mine), timeout=10)
            time.sleep(2)
            return max(0, self.c.gold - gold0)
        return 0

    def scribe_book(self, now):
        """Recall and Mark into the scribe's own book when a shop here sells them (owner: Mage shops sell Recall/Mark)."""
        for spell in ("recall", "mark"):
            if self.spell_ok(spell) or self.facts["scribe"].get("book_try:" + spell, 0) > now - 3600:
                continue
            self.facts["scribe"]["book_try:" + spell] = now
            if not self.scribe_scrolls_of(spell):
                self.scribe_buy([(spell + "scroll", 1), (spell, 1)])
            if self.scribe_scrolls_of(spell) and hasattr(self, "book_add") and self.book_add(spell):
                self.ev("scribe_book", spell=spell)

    # ---- scribing ----------------------------------------------------------------------------------------------------------------------------------

    def scribe_once(self, name, circle):
        """One scroll by the menu path; returns 'made', 'failed', or why it stopped."""
        pen = self.scribe_pen()
        blank = next((i for i in self.scribe_pack() if norm(i.name) == "blankscroll"), None)
        if pen is None:
            return "nopen"
        if blank is None:
            return "noscroll"
        from uo import Event
        self.c.events.drain()
        self.c.use(pen.serial)
        if self.c.wait_for(Event.TARGET_REQUEST, timeout=4) is None:
            return "notarget"
        self.c.target(blank.serial)
        menu = self.read_menu()
        if not menu:
            return "nomenu"
        idx = self.index_of(menu, CIRCLE_TEXT[circle])
        if not idx:
            self.close_menus([menu])
            return "nocircle"
        menu = self.scribe_pick_menu(menu, idx)
        if not menu:
            return "nomenu2"
        want = norm(re.sub(r"\bspell\b", "", name.lower()))
        idx = next((i for i, t in menu[2] if norm(t) == want or norm(t) == norm(name)), None)
        if not idx:
            self.close_menus([menu])
            return "nospell"
        try:
            self.c.call(f"menuresponse {menu[0]} {menu[1]} {idx}", timeout=8)
        except Exception as e:
            return "refused: " + str(e)[-60:]
        end, heard = time.time() + 10, []
        while time.time() < end:
            time.sleep(0.6)
            heard += self.read_journal() or []
            if any(OUTCOME.search(l) for l in heard):
                break
        text = " | ".join(heard).lower()
        if "you create" in text or "put the" in text:
            return "made"
        if "fail" in text:
            return "failed"
        if "mana" in text:
            return "nomana"
        return "silence: " + text[-80:]

    def scribe_pick_menu(self, menu, index):
        try:
            self.c.call(f"menuresponse {menu[0]} {menu[1]} {index}", timeout=8)
        except Exception:
            return None
        return self.read_menu()

    def r_scribe(self):
        if not self.scribe_on() or self.c.ghost or self.dangers(10) or self.hp_pct() < 60:
            return False
        now = time.time()
        st = self.facts.setdefault("scribe", {})
        if now - st.get("session_at", 0) < SESSION_GAP:
            return False
        skill = self.scribe_skill()
        if skill < MIN_INSCRIPTION or self.c.gold < RESERVE + 30:
            return False
        st["session_at"] = now
        xy = tuple(self.mage_shop_xy())
        far = self.far_front(xy, "shop", 90, True)
        if far:
            self.far_after(far, "shop")
            return True
        self.activity = "scribing scrolls"
        self.c.goto(*xy).wait(timeout=90)
        if self.scribe_pen() is None:
            self.scribe_buy([("penandink", 1), ("scribespen", 1)])
        self.scribe_book(now)
        if hasattr(self, "book_read"):
            self.book_read(force=True)
        pick = self.scribe_pick(skill)
        if pick is None or self.scribe_pen() is None:
            self.ev("scribe_session", spell=None, made=0, failed=0, sold=0, gold=self.c.gold, minutes=0, why="no pen" if pick else "nothing worth scribing")
            return True
        value, name, circle, regs = pick
        self.ev("scribe_pick", spell=name, chance=round(success(skill, circle), 2), value=value)
        per = cost_of(regs)
        n = max(0, min(BATCH, (self.c.gold - RESERVE) // max(1, per)))
        have = self.scribe_regs()
        wants = [("blankscroll", n - self.scribe_count("blankscroll"))]
        for r in regs:
            word = next(k for k, v in REAGENT_NAMES.items() if v == r)
            wants.append((word, n - have.get(r, 0)))
        self.scribe_buy([(w, q) for w, q in wants if q > 0])
        made = failed = 0
        for _ in range(n):
            if self.dangers(10) or self.c.ghost:
                break
            if (getattr(self.c, "mana", 0) or 0) < MANA[circle]:
                break                                            # the rest rule meditates; the next session carries on
            res = self.scribe_once(name, circle)
            if res == "made":
                made += 1
            elif res == "failed":
                failed += 1
            else:
                self.log(f"scribe: stopped ({res})")
                break
        sold = self.scribe_sell(name)
        self.ev("scribe_session", spell=name, made=made, failed=failed, sold=sold, gold=self.c.gold, minutes=round((time.time() - now) / 60, 1))
        self.log(f"scribe: {name} x{made} made, {failed} failed, sold for {sold}")
        return True
