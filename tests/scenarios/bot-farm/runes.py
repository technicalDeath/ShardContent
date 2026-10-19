"""Runes, Mark and Recall (owner 2026-10-18: "Give the bots the skill to use runes, scrolls for Mark and recall when they have enough skill to do so"); feature "runes".
Mixin for BotBase and CasterBot (RuneMixin). Every bot has it; Magery decides who can use it.

Enough skill, from the engine (MagerySpell.GetCastSkills, pre-ML table: a book cast needs table[circle + 2], a scroll table[circle], max = min + 40):
  Recall (4th)  book 30-70, scroll 10-50        Mark (6th)  book 50-90, scroll 30-70        chance = (Magery - min) / 40
A way is usable when its chance is at least MIN_CHANCE: the BOOK (a spellbook that holds the spell, a black pearl, blood moss and mandrake root, the mana) or a
SCROLL in the pack (the mana; a fizzle eats the scroll, so the same bar). The book is used whenever it reaches the bar (scrolls are scarce, reagents cheap). Stock Mage shops sell scrolls of circles 1-3 only, so Recall and
Mark scrolls come from loot; spellbook.py puts a looted scroll into the book only when the book casts it well enough (rune_keep_scroll), else it stays a scroll.

What a bot that can do both now does (rules r_rune_mark, r_rune_buy; the hop inside far.py's routed walk):
 * BUYS blank runes (RUNES_WANT kept, two at a time) at the nearest shop the shared memory has seen selling them, else the home Mage shop, when it has no blank and
   gold to spare (BUY_FLOOR stays in the pack). Not more than once in BUY_EVERY.
 * MARKS a blank rune where it pays to come back: HOME (its home town's first refuge, walked to when in town and the home rune is missing) and a far GROUND (out in the
   wilds more than HOME_FAR tiles from home, where it stayed STAY_SECS within STAY_RADIUS tiles and killed STAY_KILLS or more, with no rune of its own within
   SPREAD tiles). With RUNES_WANT marked, the ground rune used least and longest ago is marked again (never the home rune).
 * RECALLS on a far walk (far.py far_run, any role but the ghost's walk to a healer): when one of its runes lands within HOP_NEAR tiles of the destination and that
   saves HOP_SAVE tiles or more, it casts Recall on the rune first and walks only the rest. Once per trip; a refusal or fizzle walks as before.
RUNES ARE KNOWN BY SERIAL: the client names pack items from the graphic table, and the shard's Backpack Ward shares the blank rune's graphic and hue (0x1F14, 0), so a
"recall rune" in the pack proves nothing. A blank is a serial that appeared in the pack with a purchase (facts["rune_blanks"]); a marked rune is one this bot marked
(facts["runes"]). Runes from loot are left alone.
Refusals are the server's own words (fizzle, blocked, encumbered, criminal, heat of battle, reagents, mana): each backs off FAIL_BACKOFF; the walk or the hunt goes on.
Events (decisions.jsonl): rune_buy {n, price, from}, rune_mark {label, x, y, way, chance}, rune_recall {label, to, saved, way, chance}, rune_fail {spell, why, way}.
"""
import re
import time
import zlib

SKILL = {"recall": {"book": 30.0, "scroll": 10.0, "mana": 11}, "mark": {"book": 50.0, "scroll": 30.0, "mana": 20}}
SPAN = 40.0
MIN_CHANCE = 0.6
REAGENTS = ("blackpearl", "bloodmoss", "mandrakeroot")
RUNES_WANT = 3
BUY_N = 2
BUY_FLOOR = 60
BUY_EVERY = 1800
PRICE_GUESS = 15                      # stock SBMage: a recall rune 15 gold
HOME_FAR = 150
STAY_SECS = 600
STAY_RADIUS = 40
STAY_KILLS = 3
SPREAD = 80
HOP_NEAR = 90                         # under far.py FAR - 20 (100): a landing this near is the caller's own short walk
HOP_SAVE = 120
FAIL_BACKOFF = 300
HOME_SPREAD = 3                       # the home rune is marked this many tiles or fewer off the refuge, a spot of each bot's own: a landing on a tile
                                      # someone stands on is refused ("That location is blocked", live 2026-10-18), and bots gather at the refuge
BLOCKED_REMARK = 3                    # a rune refused as blocked this many times running is marked again (somewhere free)
CAST_WAIT = {"recall": 3.5, "mark": 4.5}
FAIL_WORDS = ("fizzles", "location is blocked", "encumbered", "criminal", "heat of battle", "more reagents", "insufficient mana", "do not have that spell",
              "not allowed", "cannot recall", "can not recall", "concentration is disturbed", "you are frozen", "already casting", "too busy", "can't do that",
              "decide against", "cannot mark", "can not mark", "that is not a recall rune", "rune is not marked", "can't see", "too far away")
SHOP_LINE = re.compile(r"(0x[0-9A-Fa-f]+)\s+(\d+)gp\s+x(\d+)\s+(.+)")


def norm(s):
    return re.sub(r"[^a-z]", "", (s or "").lower())


def chance(skill, spell, way):
    lo = SKILL[spell][way]
    return max(0.0, min(1.0, (skill - lo) / SPAN))


def cheb(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


class RuneMixin:
    # ---- what the bot carries and can do ---------------------------------------------------------------------------------------------------------------

    def rune_on(self):
        return self.feature("runes")

    def rune_magery(self):
        if hasattr(self, "book_state"):
            return float(getattr(self, "skill", 0.0) or 0.0)          # CasterBot (mage_bot): self.skill is Magery's value
        sv = getattr(self, "skill_values", None) or {}
        return float(sv.get("Magery", 0.0) or 0.0)

    def rune_pack(self):
        try:
            return list(self.c.backpack or [])
        except Exception:
            return []

    def rune_items(self):
        """What the client calls a recall rune (graphic 0x1F14-0x1F17): runes, and also the Backpack Ward; only serials tell them apart (see the module doc)."""
        return [i for i in self.rune_pack() if "rune" in norm(i.name) and "runebook" not in norm(i.name)]

    def rune_book_present(self):
        return hasattr(self, "book_state") or any("spellbook" in norm(i.name) for i in self.rune_pack())       # CasterBot knows its book (spellbook.py)

    def rune_scroll(self, spell):
        keys = {spell + "scroll", "scrollof" + spell, spell}
        for i in self.rune_pack():
            n = norm(i.name)
            if ("scroll" in n or n == spell) and (n in keys or n.startswith(spell) and "scroll" in n):
                return i
        return None

    def rune_regs_ok(self):
        regs = getattr(self, "regs", None)
        if isinstance(regs, dict) and regs:
            return all(regs.get(k, 0) > 0 for k in ("BlackPearl", "Bloodmoss", "MandrakeRoot"))
        have = {norm(i.name) for i in self.rune_pack() if (getattr(i, "amount", 1) or 1) > 0}
        return all(any(r in h for h in have) for r in REAGENTS)

    def rune_way(self, spell, now_only=True):
        """The way to cast the spell: ("book", chance, None) when the book reaches MIN_CHANCE, else ("scroll", chance, item); None when neither does.
        now_only=False asks about skill and means (book held / scroll carried) without the reagents and mana of this moment."""
        sk = self.rune_magery()
        ways = []
        sc = self.rune_scroll(spell)
        if sc is not None:
            ways.append(("scroll", chance(sk, spell, "scroll"), sc))
        if self.rune_book_present() and self.spell_ok(spell) and (not now_only or self.rune_regs_ok()):
            ways.append(("book", chance(sk, spell, "book"), None))
        ways = [w for w in ways if w[1] >= MIN_CHANCE]
        if now_only and (getattr(self.c, "mana", 0) or 0) < SKILL[spell]["mana"]:
            return None
        books = [w for w in ways if w[0] == "book"]
        return books[0] if books else (ways[0] if ways else None)          # the book whenever it is good enough: scrolls are scarce (loot), reagents are not

    def rune_able(self):
        """Skill and means for both spells: worth buying and marking runes."""
        return self.rune_way("recall", now_only=False) is not None and self.rune_way("mark", now_only=False) is not None

    def rune_keep_scroll(self, spell):
        """spellbook.py asks before dragging a scroll into the book: keep a Recall or Mark scroll in the pack while the book would cast it under MIN_CHANCE."""
        spell = spell.lower()
        if spell not in SKILL:
            return False
        sk = self.rune_magery()
        return chance(sk, spell, "book") < MIN_CHANCE <= chance(sk, spell, "scroll")

    def rune_known(self):
        """facts["runes"]: {serial: {x, y, label, t, used, last}} for the runes this bot marked, kept to the ones still in the pack."""
        runes = self.facts.setdefault("runes", {})
        pack = self.rune_pack()
        if pack:                                               # an unread pack (empty list) is no reason to forget
            serials = {i.serial for i in pack}
            for s in [s for s in runes if s not in serials]:
                del runes[s]
        return runes

    def rune_blanks(self):
        """The blank runes this bot bought and has not marked: [serial], kept to the ones still in the pack."""
        known = self.rune_known()
        pack = self.rune_pack()
        blanks = [s for s in self.facts.setdefault("rune_blanks", []) if s not in known]
        if pack:
            serials = {i.serial for i in pack}
            blanks = [s for s in blanks if s in serials]
        self.facts["rune_blanks"] = blanks
        return blanks

    def rune_count(self):
        return len(self.rune_known()) + len(self.rune_blanks())

    # ---- casting ---------------------------------------------------------------------------------------------------------------------------------------------

    def rune_cast(self, spell, way, rune_serial):
        """Cast Mark or Recall on a rune by the chosen way; returns (ok, why). ok means no refusal was heard (Recall also checks that the bot moved)."""
        from uo import Event
        kind, ch, item = way
        here = (self.c.x, self.c.y)
        self.c.events.drain()
        self.last_spell = (spell, time.time())
        if kind == "scroll":
            self.c.use(item.serial)
        else:
            self.cmd(f"cast {spell}")
        if self.c.wait_for(Event.TARGET_REQUEST, timeout=4.0) is None:
            lines = self.read_journal()
            return False, self.rune_fail_why(lines) or "no target cursor"
        self.c.target(rune_serial)
        end = time.time() + CAST_WAIT[spell]
        heard = []
        while time.time() < end:
            time.sleep(0.5)
            heard += self.read_journal() or []
            why = self.rune_fail_why(heard)
            if why:
                return False, why
            if spell == "recall" and cheb(here, (self.c.x, self.c.y)) > 20:
                return True, "moved"
        if spell == "recall":
            return (cheb(here, (self.c.x, self.c.y)) > 20), ("moved" if cheb(here, (self.c.x, self.c.y)) > 20 else "did not move")
        return True, "no refusal"

    @staticmethod
    def rune_fail_why(lines):
        for l in lines or ():
            low = str(l).lower()
            for w in FAIL_WORDS:
                if w in low:
                    return w
        return None

    def rune_failed(self, spell, why, way):
        self.facts["rune_off_until"] = time.time() + FAIL_BACKOFF
        self.ev("rune_fail", spell=spell, why=why, way=way[0])
        self.log(f"runes: {spell} by {way[0]} failed ({why})")

    def rune_quiet(self):
        return not self.c.ghost and not self.threats(10) and self.hp_pct() >= 60 and time.time() >= self.facts.get("rune_off_until", 0)

    # ---- recall on a far walk (far.py far_run) ------------------------------------------------------------------------------------------------------------

    def rune_hop(self, dest, role):
        """Recall to the rune nearest the destination when it saves enough walking; True when the bot moved (the walk then goes on from the landing)."""
        if not self.rune_on() or role == "healer" or not self.rune_quiet():
            return False
        here = (self.c.x, self.c.y)
        best = None
        for s, r in self.rune_known().items():
            land = (r["x"], r["y"])
            saved = cheb(here, dest) - cheb(land, dest)
            if cheb(land, dest) <= HOP_NEAR and saved >= HOP_SAVE and (best is None or cheb(land, dest) < cheb((best[1]["x"], best[1]["y"]), dest)):
                best = (s, r, saved)
        if best is None:
            return False
        way = self.rune_way("recall")
        if way is None:
            return False
        s, r, saved = best
        self.activity = f"recalling to {r['label']}"
        ok, why = self.rune_cast("recall", way, s)
        if not ok:
            self.rune_failed("recall", why, way)
            if why == "location is blocked":
                r["blocked"] = r.get("blocked", 0) + 1
                if r["blocked"] >= BLOCKED_REMARK:
                    del self.rune_known()[s]
                    self.facts.setdefault("rune_blanks", []).append(s)          # marked again where the bot next stands for it
                    self.log(f"runes: the {r['label']} rune landed on a blocked tile {r['blocked']} times: it is marked again")
            return False
        r.pop("blocked", None)
        r["used"] = r.get("used", 0) + 1
        r["last"] = time.time()
        self.ev("rune_recall", label=r["label"], to=[r["x"], r["y"]], saved=saved, way=way[0], chance=round(way[1], 2))
        self.log(f"runes: recalled to {r['label']} ({r['x']},{r['y']}), {saved} tiles not walked")
        return True

    # ---- marking -------------------------------------------------------------------------------------------------------------------------------------------

    def rune_stay_tick(self):
        """Where the bot has been staying out in the wilds, and the kills it made there: facts["rune_stay"] {x, y, t0, k0}."""
        here = (self.c.x, self.c.y)
        st = self.facts.get("rune_stay")
        kills = getattr(self, "kills", 0)
        if not st or cheb(here, (st["x"], st["y"])) > STAY_RADIUS or kills < st["k0"]:
            st = self.facts["rune_stay"] = {"x": here[0], "y": here[1], "t0": time.time(), "k0": kills}
        return st

    def rune_spot(self):
        """(label, (x, y)) of the place worth a rune now, or None: home when the home rune is missing and the bot is in its home town, else the far ground it stays at."""
        here = (self.c.x, self.c.y)
        if self.c.x >= 5120:
            return None                                          # below ground: dungeons and the sewers are not marked
        known = self.rune_known()
        if not any(r["label"] == "home" for r in known.values()):
            if self.in_britain():
                return "home", self.rune_home_xy()
            return None
        st = self.rune_stay_tick()
        if self.region_name() != "wilds" or cheb(here, self.home_centre()) <= HOME_FAR:
            return None
        if time.time() - st["t0"] < STAY_SECS or getattr(self, "kills", 0) - st["k0"] < STAY_KILLS:
            return None
        if any(cheb(here, (r["x"], r["y"])) <= SPREAD for r in known.values()):
            return None
        return "ground", here

    def rune_home_xy(self):
        """The home rune's spot: the first refuge moved by a fixed offset of this bot's own (from its name), up to HOME_SPREAD tiles."""
        x, y = self.town_xy()
        h = zlib.crc32(str(getattr(self, "name", "bot")).encode())
        span = 2 * HOME_SPREAD + 1
        return (int(x) + h % span - HOME_SPREAD, int(y) + (h // span) % span - HOME_SPREAD)

    def rune_target(self):
        """The rune to mark: a blank, else (all RUNES_WANT marked) the ground rune used least and longest ago."""
        blanks = self.rune_blanks()
        if blanks:
            return blanks[0]
        known = self.rune_known()
        if len(known) < RUNES_WANT:
            return None
        grounds = [(r.get("used", 0), r.get("last", r["t"]), s) for s, r in known.items() if r["label"] != "home"]
        return min(grounds)[2] if grounds else None

    def r_rune_mark(self):
        if not self.rune_on() or not self.rune_quiet() or not self.rune_able():
            return False
        spot = self.rune_spot()
        if spot is None:
            return False
        target = self.rune_target()
        if target is None:
            return False
        label, xy = spot
        if cheb((self.c.x, self.c.y), xy) > 1:
            if label != "home":
                return False
            self.activity = "walking to mark a home rune"
            self.c.goto(*xy).wait(timeout=60)
            if cheb((self.c.x, self.c.y), xy) > HOME_SPREAD + 1 or not self.rune_quiet():
                self.facts["rune_off_until"] = time.time() + FAIL_BACKOFF
                return True
        way = self.rune_way("mark")
        if way is None:
            return False                                         # skill and book, but no reagents or mana this moment: the stock and rest rules see to those
        self.activity = f"marking a rune ({label})"
        ok, why = self.rune_cast("mark", way, target)
        if not ok:
            self.rune_failed("mark", why, way)
            return True
        now = time.time()
        self.rune_known()[target] = {"x": self.c.x, "y": self.c.y, "label": label if label == "home" else f"ground {self.c.x},{self.c.y}", "t": now, "used": 0, "last": now}
        self.facts.pop("rune_stay", None)
        self.ev("rune_mark", label=label, x=self.c.x, y=self.c.y, way=way[0], chance=round(way[1], 2))
        self.log(f"runes: marked a rune for {label} at {self.c.x},{self.c.y} ({way[0]}, chance {way[1]:.0%})")
        return True

    # ---- buying blank runes --------------------------------------------------------------------------------------------------------------------------------

    def rune_shop_xy(self):
        try:
            sellers = self.mem.vendor_selling("rune")
        except Exception:
            sellers = []
        sellers = [s for s in sellers if "runebook" not in norm(s[2])]
        if sellers:
            return tuple(min(sellers, key=lambda s: cheb((self.c.x, self.c.y), tuple(s[1])))[1])
        return tuple(self.mage_shop_xy())

    def r_rune_buy(self):
        if not self.rune_on() or not self.rune_quiet() or not self.rune_able():
            return False
        now = time.time()
        if self.rune_blanks() or self.rune_count() >= RUNES_WANT or now - self.facts.get("rune_buy_at", 0) < BUY_EVERY:
            return False
        if self.c.gold < BUY_FLOOR + BUY_N * PRICE_GUESS:
            return False
        self.facts["rune_buy_at"] = now
        xy = self.rune_shop_xy()
        far = self.far_front(xy, "shop", 90, True)
        if far:
            self.far_after(far, "shop")
            return True
        self.activity = "buying recall runes"
        self.c.goto(*xy).wait(timeout=90)
        people = sorted([m for m in self.c.mobiles(within=10) if m.notoriety == "Innocent" and m.name and not m.name.startswith("Bot")], key=lambda m: m.distance)
        for v in people[:8]:
            for line in self.vendor_list(v, "buy"):              # BotBase.vendor_list: walks up, and only this vendor's own answer counts
                m = SHOP_LINE.search(line)
                if not m or "rune" not in norm(m.group(4)) or "runebook" in norm(m.group(4)):
                    continue
                price, avail = int(m.group(2)), int(m.group(3))
                n = min(BUY_N, avail, max(0, (self.c.gold - BUY_FLOOR) // max(1, price)))
                if n <= 0:
                    return True
                before = {i.serial for i in self.rune_items()}
                self.cmd(f"buy {m.group(1)} {n}", timeout=10)
                time.sleep(2)
                new = [i.serial for i in self.rune_items() if i.serial not in before]
                self.facts.setdefault("rune_blanks", []).extend(new)
                got = len(new)
                self.ev("rune_buy", n=got, price=price, **{"from": v.name})
                self.log(f"runes: bought {got} blank runes at {price} from {v.name}")
                return True
        self.ev("rune_buy", n=0, price=None, **{"from": "none sells them here"})
        return True
