"""Social presence for the farm's bots (feature "talk"; patch_talk.py; the watcher's A7 company / G7 social presence, 2026-10-17).

What was there: chatter() (greet, reply, ghost, skill, wares, warn) and hear(), which the journal calls ONLY for speakers named Bot*: a human player, the owner at the keyboard, was never answered, while
the bots answered each other (514 "reply" lines of "Hail, X." ping-pong).

THE REPLY PATH (to people, conservative and stateful):
  * feed(bot, line) reads every journal line: "[LABEL] Name: Title" (a label that is longer than the name, "Ryan the minter", marks an NPC) and "[SAY] Name: text".
  * a speaker is a PERSON when it is not named Bot*, not an NPC by label or by the shop memory's vendor names, and a human body in view (is_human, not a monster, name without an article).
    Bots' speech is not answered (the ping-pong), except that a bot is never replied to by a bot at all.
  * it is answered when the text carries this bot's name (full, or without the Bot prefix) from up to 20 tiles, or is a plain greeting / farewell / thanks from up to 8 tiles. One reply per
    utterance, at least 8 s after the speaker's previous utterance was answered, at most 12 replies to people an hour, and a delay of 1.2-3.5 s (a person types).
  * the line comes from an intent bank in the words of the era ("Hail", "Well met", "thee"; no "lol" or "ok") and from the bot's real state: the profession and what it is doing in plain words,
    where it is as a player puts it. Never an internal name ("r_hunt"), a number or a coordinate.
CONTEXT LINES (a few an hour; BotBase.chatter keeps its per-kind cooldowns and its 3-minute gap, plus a cap of 6 lines an hour):
  * town_warn: a monster over 25 hit points inside the home town's core within 14 tiles: the nearest bot says so once per monster (a claim in the shared memory, 10 minutes).
  * sell_call: a crafter arriving at its buyer with stock says what it sells (crafter.py).
EVENTS: dlog "say" {kind, text, to_human, to}.
"""
from __future__ import annotations

import json
import os
import random
import re
import time

FEATURE = "talk"
REPLY_GAP = 8.0
SAME_ROOM = 8
NAMED_ROOM = 20
HUMAN_CAP = 12
CTX_CAP = 6
DELAY = (1.2, 3.5)
WARN_RANGE = 14
WARN_HITS = 25
WARN_CLAIM_TTL = 600
GREET_BUCKET = 120                  # seconds: one greeting from the whole farm per bucket
GLOBAL_KINDS = ("greet",)
LABEL = re.compile(r"^\[LABEL\]\s+(.+?):\s+(.+)$")
ADDRESSED_S = 180.0                 # seconds a speaker the bot has just spoken to by name counts as an NPC
ADDRESS = re.compile(r"^(\w+)\s+(buy|sell|bank|train|balance|withdraw|deposit)\b", re.I)
SHOP_VENDOR = re.compile(r"^\[SHOP\]\s+vendor\s+(0x[0-9A-Fa-f]+)")
SAY = re.compile(r"^\[SAY\]\s+([^:]+?):\s+(.+)$")

INTENTS = (
    ("bye", re.compile(r"\b(bye|farewell|goodbye|good night|see (you|ya|thee)|cya|gtg|later)\b", re.I)),
    ("thanks", re.compile(r"\b(thanks|thank (you|ye|thee)|ty|thx|much obliged)\b", re.I)),
    ("party", re.compile(r"\b(party|group|hunt with|hunt together|join (me|us)|come with|follow me)\b", re.I)),
    ("trade", re.compile(r"\b(buy|sell|selling|trade|price|how much|wares|for sale)\b", re.I)),
    ("help", re.compile(r"\b(help|res|rez|resurrect|heal me|bandage|need a)\b", re.I)),
    ("doing", re.compile(r"\b(what('?s| are| is| r)?\s+(you|ye|u|thee)\s+(doing|up to)|doing|up to|wat'?s up|whats up|sup)\b", re.I)),
    ("where", re.compile(r"\bwhere\b", re.I)),
    ("how", re.compile(r"\b(how (are|r|do) (you|ya|u|thee|ye)|how goes|how fare)\b", re.I)),
    ("greet", re.compile(r"\b(hail|hello|hallo|hi|hey|ho there|well met|greetings|good (day|morrow|morning|evening|even))\b", re.I)),
)

LINES = {
    "greet": ["Hail, {who}.", "Well met, {who}.", "Good day to thee, {who}.", "Greetings, {who}!"],
    "how": ["Well enough, {who}, and thee?", "Hale and hearty, I thank thee.", "I cannot complain, {who}."],
    "bye": ["Fare thee well, {who}.", "Safe travels, {who}.", "Until we meet again."],
    "thanks": ["Thou art welcome, {who}.", "Think nothing of it.", "Gladly done."],
    "help": ["I fear I can do little, {who}, but I wish thee luck.", "The healers keep the city, {who}; they will see thee right.", "Ask at the healer, {who}."],
    "party": ["I hunt alone for now, {who}.", "Perhaps later, {who}.", "Not just now, I thank thee."],
    "name": ["Aye, {who}?", "Yes, {who}?", "Thou hast my ear, {who}."],
    "no_trade": ["I have nothing to sell just now, {who}.", "Not today, {who}."],
    "doing": ["{doing}.", "{doing}, {who}.", "Just {doing}."],
    "where": ["{where_}, {who}.", "Right here, {who} - {where_}."],
    "warn": ["Beware, {m} in the city!", "Take care: {m} is loose in the city!", "{m} in the city! Mind thyself!"],
    "sell_call": ["Selling {item}, fair prices!", "{item} for sale, ask me.", "Fine {item} here!"],
}

RULE_WORDS = {
    "r_fight": "hunting", "r_hunt": "hunting", "r_explore": "looking for game", "r_camp": "keeping watch for game", "r_loot": "looting what I have won", "r_carve": "butchering",
    "r_craft": "crafting", "r_mine": "mining ore", "r_dig": "digging ore", "r_chop": "cutting wood", "r_fish": "fishing", "r_cook": "cooking",
    "r_bank": "seeing to my gold", "r_sell": "selling my wares", "r_sellgear": "selling my gear", "r_sellmeat": "selling meat", "r_resupply": "buying supplies", "r_restock": "buying supplies",
    "r_rest": "taking a moment's rest", "r_heal": "binding my wounds", "r_tame": "taming", "r_practice": "practising my spells", "r_book": "filling my spellbook", "r_trip": "travelling",
}


def on(bot):
    try:
        return bool(bot.feature(FEATURE))
    except Exception:
        return False


def _ctx_path(bot):
    d = getattr(bot, "dir", None)
    return os.path.join(d, "talk_ctx.json") if d else None


def _load_ctx(bot):
    """The times of this bot's context lines in the last hour (kept across a restart)."""
    p = _ctx_path(bot)
    try:
        now = time.time()
        return [t for t in json.load(open(p, encoding="utf-8")) if now - t < 3600] if p else []
    except (OSError, ValueError, TypeError):
        return []


def _save_ctx(bot):
    p = _ctx_path(bot)
    if not p:
        return
    try:
        with open(p + ".tmp", "w", encoding="utf-8") as f:
            json.dump(_st(bot)["ctx"], f)
        os.replace(p + ".tmp", p)
    except OSError:
        pass


def _st(bot):
    return bot.__dict__.setdefault("_talk", {"npc": set(), "people": {}, "pending": None, "replied": [], "ctx": _load_ctx(bot)})


# ---- who is a person ---------------------------------------------------------------------------------------------------------------------------------

def vendor_names(bot):
    try:
        return {v.get("name") for v in bot.mem.state["world"]["vendors"].values() if v.get("name")}
    except Exception:
        return set()


def note_label(bot, t):
    """A label that is longer than the name carries a title: an NPC."""
    m = LABEL.match(t)
    if not m:
        return
    name, label = m.group(1).strip(), m.group(2).strip()
    if label != name and label.lower().startswith(name.lower()):
        _st(bot)["npc"].add(name)


def serial_int(s):
    try:
        return int(str(s), 16)
    except (TypeError, ValueError):
        return -1


def is_person(bot, who):
    """A speaker we may answer: not a bot, not an NPC (by label, shop memory, a name the bot just addressed, a vendor's serial, a yellow notoriety), a human body in view."""
    if time.time() - _st(bot).get("addressed", {}).get(who, 0) < ADDRESSED_S:
        return False
    if who.startswith("Bot") or who in _st(bot)["npc"] or who in vendor_names(bot) or re.match(r"^(an?|the) ", who, re.I):
        return False
    try:
        for m in bot.c.mobiles(within=NAMED_ROOM + 4):
            if m.name == who:
                if getattr(m, "notoriety", "") == "Invulnerable" or serial_int(getattr(m, "serial", "")) in _st(bot).get("vendors", ()):
                    return False
                return bool(m.is_human) and not m.known_monster
    except Exception:
        return False
    return False


def distance_to(bot, who):
    try:
        for m in bot.c.mobiles(within=NAMED_ROOM + 4):
            if m.name == who:
                return m.distance
    except Exception:
        pass
    return 999


# ---- what to say ---------------------------------------------------------------------------------------------------------------------------------

def name_tokens(bot):
    n = bot.name.lower()
    return {n, n[3:] if n.startswith("bot") else n}


def addressed(bot, text):
    low = text.lower()
    return any(re.search(r"\b" + re.escape(tok) + r"\b", low) for tok in name_tokens(bot) if tok)


def doing_phrase(bot):
    if getattr(bot.c, "ghost", False):
        return "a ghost, seeking the healer"
    rule = getattr(bot, "current_rule", None) or getattr(bot, "last_rule", "") or ""
    act = (getattr(bot, "activity", "") or "").lower()
    word = RULE_WORDS.get(rule)
    out = word or "going about my business"
    if rule in ("r_craft",) and act.startswith("making "):
        out = "making " + act[7:]
    elif word == "hunting" and act.startswith(("fighting ", "approaching ")):
        out = "hunting " + act.split(" ", 1)[1]
    if re.search(r"\d|\br_|[,:]", out):
        out = "going about my business"                              # never a number, a coordinate or an internal name
    return out


def where_phrase(bot):
    try:
        w = bot.where()
    except Exception:
        return "Nearby"
    return "In the city" if w == "in town" else f"A little {w}"


def choose_intent(bot, text, dist):
    """The intent of an utterance and whether to answer it, or (None, False)."""
    named = addressed(bot, text)
    for kind, pat in INTENTS:
        if pat.search(text):
            if named and dist <= NAMED_ROOM:
                return kind, True
            if kind in ("greet", "bye", "thanks") and dist <= SAME_ROOM:
                return kind, True
            return None, False
    if named and dist <= NAMED_ROOM:
        return "name", True
    return None, False


def compose(bot, who, kind):
    if kind == "trade":
        stock = []
        try:
            stock = [i for i in bot.products() if i.name]
        except Exception:
            pass
        if stock:
            item = stock[0].name.lower()
            return "sell_call", random.choice(LINES["sell_call"]).format(item=item + ("" if item.endswith("s") else "s")).replace("{who}", who)
        kind = "no_trade"
    pool = LINES.get(kind) or LINES["name"]
    line = random.choice(pool).format(who=who, doing=doing_phrase(bot), where_=where_phrase(bot))
    return kind, line[:1].upper() + line[1:]


# ---- hearing and replying -------------------------------------------------------------------------------------------------------------------------

def feed(bot, t):
    try:
        import guildtalk
        guildtalk.feed(bot, t)                                  # guild chat: membership from the journal (feature guild_chat)
    except Exception:
        pass
    try:
        import marketvoice
        marketvoice.feed(bot, t)                                # the market's spoken side: a call that matches a want, a question about an offer (feature market_voice)
    except Exception:
        pass
    if not on(bot):
        return
    if t.startswith("[LABEL]"):
        note_label(bot, t)
        return
    sv = SHOP_VENDOR.match(t)
    if sv:
        _st(bot).setdefault("vendors", set()).add(serial_int(sv.group(1)))                 # a list a vendor sent: that serial is no person
        return
    m = SAY.match(t)
    if not m:
        return
    who, text = m.group(1).strip(), m.group(2).strip()
    if who == bot.name:
        a = ADDRESS.match(text)
        if a:
            _st(bot).setdefault("addressed", {})[a.group(1)] = time.time()                  # spoke to it by name: it is an NPC (a vendor, the banker)
        return
    if getattr(bot.c, "ghost", False):
        return
    hear(bot, who, text)


def hear(bot, who, text):
    st = _st(bot)
    if not is_person(bot, who):
        return
    now = time.time()
    p = st["people"].setdefault(who, {"answered": 0.0})
    dist = distance_to(bot, who)
    kind, ok = choose_intent(bot, text, dist)
    if not ok or st["pending"] or now - p["answered"] < REPLY_GAP:
        return
    st["replied"] = [t for t in st["replied"] if now - t < 3600]
    if len(st["replied"]) >= HUMAN_CAP:
        return
    kind, line = compose(bot, who, kind)
    st["pending"] = {"due": now + random.uniform(*DELAY), "kind": kind, "line": line, "who": who}
    p["answered"] = now


def tick(bot):
    """After every tick: send the pending reply when it is due; look for a monster in the city."""
    try:
        import guildtalk
        guildtalk.tick(bot)                                     # a situational line on the guild's chat (feature guild_chat)
    except Exception:
        pass
    try:
        import marketvoice
        marketvoice.tick(bot)                                   # the seller's call at the bank, a pending answer (feature market_voice)
    except Exception:
        pass
    if not on(bot) or getattr(bot.c, "ghost", False):
        return
    st = _st(bot)
    pend = st["pending"]
    now = time.time()
    if pend and now >= pend["due"]:
        st["pending"] = None
        bot.c.say(pend["line"])
        st["replied"].append(now)
        bot.dlog("say", kind=pend["kind"], text=pend["line"], to_human=True, to=pend["who"])
        bot.facts["said_any"] = now
        return
    if now - st.get("warn_at", 0) >= 5.0:
        st["warn_at"] = now
        warn(bot)


def dangerous(m):
    try:
        import danger
        c = danger.stats().get(re.sub(r"[^a-z]", "", (m.species or re.sub(r"^(an?|the) ", "", m.name.lower())).lower()))
        if c and c.get("hits"):
            return c["hits"][1] > WARN_HITS
    except Exception:
        pass
    return bool(m.known_monster) and not re.search(r"\b(rat|cat|bird|dog|snake|frog|mongbat|rabbit|chicken|sheep|pig|cow|goat)\b", m.name.lower())


def aggressive(m):
    """A kind that attacks a stranger on sight (or a red one): the test r_evade uses; animals and livestock fight back only, an unknown kind is not warned about."""
    try:
        import evade
        kind = re.sub(r"[^a-z]", "", (m.species or re.sub(r"^(an?|the) ", "", m.name.lower())).lower())
        return evade.classify(kind, m.notoriety, 999, None, False) is not None
    except Exception:
        return False


def warn(bot):
    """A monster over 25 hit points inside the home city: the nearest bot says so, once per monster."""
    if not hasattr(bot, "chatter"):
        return
    try:
        core = bot.home_core()
    except Exception:
        return
    if not (core[0] <= bot.c.x < core[2] and core[1] <= bot.c.y < core[3]):
        return
    near = [m for m in bot.c.mobiles(within=WARN_RANGE) if not m.name.startswith("Bot") and m.notoriety in ("Gray", "Criminal", "Enemy", "Murderer") and not getattr(m, "is_dead", False) and dangerous(m) and aggressive(m)]
    if not near:
        return
    m = min(near, key=lambda o: o.distance)
    st = _st(bot)
    key = str(m.serial)
    if st.get("warned", {}).get(key, 0) > time.time() - WARN_CLAIM_TTL:
        return
    if m.distance > 10:
        return                                                    # the nearest bot speaks: one that is far from it leaves it to the others
    try:
        if not bot.mem.usable("warn", key):
            st.setdefault("warned", {})[key] = time.time()
            return                                                # another bot claimed it
        bot.mem.record("claim", kind="warn", key=key, ttl=WARN_CLAIM_TTL)
    except Exception:
        pass
    st.setdefault("warned", {})[key] = time.time()
    try:
        import townguard
        townguard.call_guards(bot, m)                         # feature town_guards: the bot that warns also calls the guards, once per monster
    except Exception:
        pass
    name = m.name if m.name.lower().startswith(("a ", "an ", "the ")) else f"a {m.name}"
    bot.chatter("town_warn", cooldown=0, m=name)


def capped(bot, kind):
    """chatter(): at most CTX_CAP context lines an hour with the feature on."""
    if not on(bot) or kind in ("ghost",):
        return False
    st = _st(bot)
    now = time.time()
    st["ctx"] = [t for t in st["ctx"] if now - t < 3600]
    if len(st["ctx"]) >= CTX_CAP:
        return True
    if kind in GLOBAL_KINDS:                                      # one greeting from the whole farm per bucket (a restart gave every bot a turn at once)
        try:
            if not bot.mem.usable("say", str(int(now // GREET_BUCKET))):
                return True
        except Exception:
            pass
    return False


def spoke(bot, kind):
    if on(bot) and kind != "ghost":
        _st(bot)["ctx"].append(time.time())
        _save_ctx(bot)
        if kind in GLOBAL_KINDS:
            try:
                bot.mem.record("claim", kind="say", key=str(int(time.time() // GREET_BUCKET)), ttl=GREET_BUCKET)
            except Exception:
                pass


def phrases():
    """Phrase kinds talk adds to bot_common.PHRASES."""
    return {"town_warn": LINES["warn"], "sell_call": LINES["sell_call"]}
