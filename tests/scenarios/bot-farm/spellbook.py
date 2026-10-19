"""Know and fill the spellbook (Operator's board item; the Helper). Mixin for CasterBot, written into the bot-farm folder by patch_spellbook.py.

Why: the practice casters made 233 casts in 25 minutes and every one was answered "You do not have that spell!" (Arch Cure, Bless, Reactive Armor); mana stayed
full and Magery did not move. The starter book holds only some spells, and nothing told the bot which.

What a caster now does, for any book in any town:
 * KNOWS the book. Opening a spellbook (double-click) makes the server send its content; the client turns that into one child item per held spell of the book,
   Amount = spell id + 1. `use <book>` then `container <book>` lists them (book_read). The bot keeps the held set; a read that lists no spell is not believed
   (the book may not have opened): it only counts when it lists at least one spell. Fallback that always works: the server's "You do not have that spell!" after a
   cast marks that spell missing for good. Both are kept in <bot>/spellbook.json, so a restart knows them.
 * CASTS only what the book holds. cast() refuses a spell the book is known not to hold (silently the second time; ev spell_missing the first), the attack options
   of the Knowledge object are filtered to held spells (so can_cast, best_attack, training pick among those), r_practice skips them, r_heal and r_cure do not try them.
 * FILLS the book like a player (feature "spellbook"): rule r_book, between resupply and the hunt. With the book read, gold to spare (the reserve for reagents stays),
   no danger near, it picks the spell it wants (the practice spell for its skill band first, then the attack spells the skill can use, then Heal, then Cure) that
   the book lacks and a Mage shop sells (the stock-ModernUO shop sells the scrolls of circles 1 to 3 only), walks to the nearest shop that has it, buys the scroll,
   and drags it onto the spellbook; the book is read again to confirm. A shop that does not stock a spell is remembered for six hours; a spell is tried at most
   once every 15 minutes; an add that fails twice stands the spell down for an hour.
Events (decisions.jsonl): spell_missing {spell, why (book|message)}, scroll_bought {spell, price, shop}, book_add {spell, count}, book_read {count, spells}.
"""
import json
import os
import re
import time

HERE = os.path.dirname(os.path.abspath(__file__))
RESERVE = 150                  # gold kept back for reagents
BUY_CIRCLES = 3                # what a stock Mage shop sells
READ_EVERY = 6 * 3600
TRY_EVERY = 900
NO_STOCK_FOR = 6 * 3600
ROW = re.compile(r"(0x[0-9A-Fa-f]+)\s+(\d+)gp\s+x(\d+)\s+(.+)")
_IDS = None


def spell_table():
    global _IDS
    if _IDS is None:
        try:
            _IDS = json.load(open(os.path.join(HERE, "spellids.json"), encoding="utf-8"))["spells"]
        except (OSError, ValueError, KeyError):
            _IDS = {}
    return _IDS


def norm(s):
    return re.sub(r"[^a-z]", "", s.lower())


def scroll_keys(spell):
    """The shop names a spell's scroll can have: 'Clumsy Scroll', and without the word spell ('Unlock Scroll')."""
    return {norm(spell) + "scroll", norm(re.sub(r"\bspell\b", "", spell.lower())) + "scroll", norm(spell)}      # the client calls some scrolls by the spell alone ("Recall")


class SpellbookMixin:
    _book = None
    _book_orig = None
    _book_marked = None
    _book_adding = None
    _book_reported = None

    # ---- state: <bot dir>/spellbook.json ---------------------------------------------------------------------------------------------------------

    def book_state(self):
        if self._book is None:
            self._book = {"missing": [], "have": None, "read_at": 0, "no_stock": {}, "tries": {}, "stood_down": {}}
            try:
                self._book.update(json.load(open(os.path.join(self.dir, "spellbook.json"), encoding="utf-8")))
            except (OSError, ValueError):
                pass
        return self._book

    def book_save(self):
        try:
            p = os.path.join(self.dir, "spellbook.json")
            with open(p + ".tmp", "w", encoding="utf-8") as f:
                json.dump(self._book, f)
            os.replace(p + ".tmp", p)
        except (OSError, TypeError, ValueError):
            pass

    def spell_id(self, name):
        s = spell_table().get(name.lower())
        return s["id"] if s else None

    def spell_ok(self, name):
        """False when the book is known not to hold the spell: marked missing, or a successful read of the book that lacks it."""
        n = name.lower()
        b = self.book_state()
        if n in b["missing"]:
            return False
        sid = self.spell_id(n)
        if b["have"] is not None and sid is not None:
            return sid in b["have"]
        return True

    def book_mark_missing(self, name, why):
        n = name.lower()
        b = self.book_state()
        if n not in b["missing"]:
            b["missing"].append(n)
            self.book_save()
        self.book_report(n, why)

    def book_mark_have(self, name):
        n = name.lower()
        b = self.book_state()
        sid = self.spell_id(n)
        if n in b["missing"]:
            b["missing"].remove(n)
        if sid is not None:
            have = set(b["have"] or [])
            have.add(sid)
            b["have"] = sorted(have)
        self.book_save()

    def book_report(self, n, why):
        """ev spell_missing, once per spell and brain."""
        if self._book_reported is None:
            self._book_reported = set()
        if n not in self._book_reported:
            self._book_reported.add(n)
            self.ev("spell_missing", spell=n, why=why)
            self.log(f"spellbook: no {n} in the book ({why})")

    # ---- knowledge of the spells the book holds ------------------------------------------------------------------------------------------------

    def book_prep(self):
        """Filter the Knowledge object's attack options to the spells the book holds (once)."""
        k = getattr(self, "k", None)
        if k is None or self._book_orig is not None:
            return
        self._book_orig = k.attack_options
        bot = self

        def attack_options(skill, mana, regs, min_success=0.5):
            return [o for o in bot._book_orig(skill, mana, regs, min_success) if bot.spell_ok(o["spell"]["name"])]

        k.attack_options = attack_options

    def book_item(self):
        for it in list(self.c.equipped) + list(self.c.backpack):
            low = (it.name or "").lower()
            if low == "spellbook" or low.endswith(" spellbook"):
                return it
        return None

    def book_read(self, force=False):
        """Open the spellbook and read which spells it holds: the set of spell ids, or None when the read did not list any (not believed)."""
        b = self.book_state()
        if not force and b["have"] is not None and time.time() - b["read_at"] < READ_EVERY:
            return set(b["have"])
        item = self.book_item()
        if item is None:
            return None
        ids, raw = set(), []
        for attempt in range(2):
            try:
                self.c.use(item.serial)                          # the server sends the content when the book is opened
                time.sleep(1.5 + attempt)
                raw = self.c.call(f"container {item.serial}", timeout=5)
            except Exception as e:
                self.log(f"spellbook: reading the book failed: {type(e).__name__}: {e}")
                return None
            ids = set()
            for line in raw:                                     # "  [item]  0x7FFFFFFD <name> x4": the child's Amount is the spell id + 1 (no suffix for 1)
                t = re.sub(r"^\[(?:item|container)\]\s*", "", line.strip())
                if t.startswith("0x"):
                    m = re.search(r" x(\d+)", t)
                    amount = int(m.group(1)) if m else 1
                    if 1 <= amount <= 64:
                        ids.add(amount - 1)
            if ids:
                break
        b["read_at"] = time.time()
        if not ids:
            self.log("spellbook: the book listed no spells (not opened, or empty): not believed; the client said: " + " | ".join(str(l).strip()[:70] for l in raw[:5]))
            return None
        b["have"] = sorted(ids)
        table = spell_table()
        names = {v["id"]: v["name"] for v in table.values()}
        b["missing"] = [m for m in b["missing"] if self.spell_id(m) not in ids]
        self.book_save()
        self.ev("book_read", count=len(ids), spells=[names.get(i, i) for i in sorted(ids)][:24])
        return ids

    # ---- casting only what the book holds ----------------------------------------------------------------------------------------------------------

    def cast(self, spell, target):
        self.book_prep()
        if not self.spell_ok(spell):
            self.book_report(spell.lower(), "book")
            return False
        self._book_marked = None
        res = super().cast(spell, target)
        if self._book_marked and self._book_marked == spell.lower():
            return False                                          # the server said the book does not hold it
        return res

    def book_journal(self, t):
        """Learn from the server's own words: a cast the book does not hold, a scroll the book already has."""
        low = t.lower()
        if "do not have that spell" in low:
            spell, at = getattr(self, "last_spell", (None, 0))
            if spell and time.time() - at < 15:
                self._book_marked = spell.lower()
                self.book_mark_missing(spell, "message")
        elif "already present in that spellbook" in low and self._book_adding:
            self.book_mark_have(self._book_adding)

    def book_has_attack(self):
        """Does the book hold at least one attack spell this skill can use? (r_resupply: no point buying reagents for spells it cannot cast.)"""
        k = getattr(self, "k", None)
        if k is None:
            return True
        orig = self._book_orig or k.attack_options
        full = {r: 99 for s in k.spells.values() for r in s["reagents"]}
        return bool(orig(self.skill, 999, full, 0.5)) and any(self.spell_ok(o["spell"]["name"]) for o in orig(self.skill, 999, full, 0.5))

    # ---- what to buy -----------------------------------------------------------------------------------------------------------------------------

    def book_wants(self):
        """Spells to add, most wanted first: the practice spell for the skill band, the attack spells it can use, Heal, Cure; only ones the book lacks and a
        stock Mage shop (or a shop the memory has seen selling the scroll) sells."""
        k = self.k
        table = spell_table()
        out = []

        def add(name):
            n = name.lower()
            if n in table and n not in out and not self.spell_ok(n):
                out.append(n)

        if self.feature("practice"):
            import practice                                    # nothing while the book holds a spell to practise; else the best challenging circle 1-3 spell
            for name in practice.wants(self):
                add(name)
        orig = self._book_orig or k.attack_options
        full = {r: 99 for s in k.spells.values() for r in s["reagents"]}
        for o in orig(self.skill, 999, full, 0.5)[:3]:
            add(o["spell"]["name"])
        add("heal")
        add("cure")
        b = self.book_state()
        now = time.time()
        return [n for n in out if now - b["tries"].get(n, 0) > TRY_EVERY and b["stood_down"].get(n, 0) < now and self.book_shops(n)]

    def book_shops(self, n):
        """Where the scroll can be had, nearest first: shops the memory has seen selling it, else the home Mage shop for the circles it stocks."""
        b = self.book_state()
        now = time.time()
        shops = []
        try:
            for price, xy, item, qty in self.mem.vendor_selling(f"{n} scroll"):
                if price > 0 and qty != 0:
                    x, y = (int(v) for v in xy.split(","))
                    shops.append((x, y))
        except Exception:
            pass
        circle = spell_table().get(n, {}).get("circle", 99)
        if not shops and circle <= BUY_CIRCLES:
            try:
                shops = [tuple(self.mage_shop_xy())]
            except Exception:
                shops = []
        shops.sort(key=lambda p: abs(p[0] - self.c.x) + abs(p[1] - self.c.y))
        return [p for p in shops if b["no_stock"].get(f"{p[0]},{p[1]}", {}).get(n, 0) < now - NO_STOCK_FOR]

    def book_price_guess(self, n):
        return 12 + 10 * (spell_table().get(n, {}).get("circle", 1) - 1)

    def book_scroll(self, n):
        keys = scroll_keys(n)
        return next((i for i in self.c.backpack if norm(i.name or "") in keys), None)

    def book_buy(self, n):
        """Walk to a shop that has the scroll and buy one. Returns "bought", "nostock", "poor" or "noshop"."""
        b = self.book_state()
        keys = scroll_keys(n)
        for xy in self.book_shops(n)[:2]:
            key = f"{xy[0]},{xy[1]}"
            res = self.c.goto(*xy).wait(timeout=90)
            self.log(f"spellbook: to the shop at {xy} for the {n} scroll: {res}")
            rows, vendor_name = [], ""
            for v in [m for m in self.c.mobiles(within=7) if m.notoriety == "Innocent" and m.name and not m.name.startswith("Bot")]:
                lines = self.vendor_list(v, "buy")
                if len(lines) < 2:
                    continue
                rows = [m.groups() for m in (ROW.search(l) for l in lines) if m]
                vendor_name = v.name
                if any(norm(r[3]) in keys for r in rows):
                    break
            if not rows:
                continue
            try:
                self.mem.record("vendor", xy=key, name=vendor_name, stock=[[r[3].strip(), int(r[1]), int(r[2])] for r in rows])
            except Exception:
                pass
            hit = next((r for r in rows if norm(r[3]) in keys), None)
            if hit is None:
                b["no_stock"].setdefault(key, {})[n] = time.time()
                self.book_save()
                self.log(f"spellbook: the shop at {xy} does not stock the {n} scroll")
                continue
            serial, price, avail = hit[0], int(hit[1]), int(hit[2])
            if avail <= 0:
                b["no_stock"].setdefault(key, {})[n] = time.time()
                self.book_save()
                continue
            if self.c.gold - price < RESERVE:
                return "poor"
            self.cmd(f"buy {serial} 1", timeout=10)
            time.sleep(3)
            if self.book_scroll(n):
                self.ev("scroll_bought", spell=n, price=price, shop=key)
                return "bought"
            self.log(f"spellbook: bought the {n} scroll but it is not in the pack")
        return "nostock" if self.book_shops(n) == [] else "noshop"

    def book_add(self, n):
        """Drag the scroll onto the spellbook, read the book again to confirm; True when the spell is in."""
        scroll, book = self.book_scroll(n), self.book_item()
        if not scroll or not book:
            return False
        self._book_adding = n
        try:
            self.c.drop(scroll.serial, book.serial)
            time.sleep(1.5)
            self.read_journal()
        finally:
            self._book_adding = None
        ids = self.book_read(force=True)
        if ids is not None and self.spell_id(n) in ids:
            self.book_mark_have(n)
            self.ev("book_add", spell=n, count=len(ids))
            self.log(f"spellbook: {n} is in the book ({len(ids)} spells)")
            return True
        return False

    # ---- the rule ---------------------------------------------------------------------------------------------------------------------------------

    def r_book(self):
        if not self.feature("spellbook") or self.c.ghost or self.dangers(10) or self.prey(9) or self.hp_pct() < 60:
            return False
        self.book_prep()
        b = self.book_state()
        now = time.time()
        if b["have"] is None or now - b["read_at"] > READ_EVERY:
            if now - self.facts.get("book_try_read", 0) < 600:
                return False
            self.facts["book_try_read"] = now
            self.book_read(force=True)
            return True
        # a scroll already in the pack goes into the book first
        for n in list(spell_table()):
            if not self.spell_ok(n) and self.book_scroll(n) and now - b["tries"].get("add:" + n, 0) > 60 and not (getattr(self, "rune_keep_scroll", None) and self.rune_keep_scroll(n)):
                b["tries"]["add:" + n] = now
                if self.book_add(n):
                    return True
                fails = b["tries"].get("fail:" + n, 0) + 1
                b["tries"]["fail:" + n] = fails
                if fails >= 2:
                    b["stood_down"][n] = now + 3600
                self.book_save()
                return True
        if now - self.facts.get("book_shopped", 0) < 120:
            return False
        for n in self.book_wants():
            if self.c.gold - self.book_price_guess(n) < RESERVE:
                import goals
                if not goals.fund(self, self.book_price_guess(n) + RESERVE + 10):       # saving for the book: the gold is in the bank
                    continue
            self.facts["book_shopped"] = now
            b["tries"][n] = now
            self.activity = f"buying the {n} scroll"
            how = self.book_buy(n)
            self.book_save()
            if how == "bought":
                return True
            if how in ("poor", "noshop"):
                return True
        return False
