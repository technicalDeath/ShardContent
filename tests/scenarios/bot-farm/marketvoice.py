"""The spoken side of the bots' market at the bank (A7 company; Watcher 2026-10-17, Helper 2; feature "market_voice", which also needs the feature "trade"). Module functions called from talk.py's feed() and
tick() (patch_marketvoice.py). It only READS the market (market.py's offers and wants via mkt_view()); it writes nothing to it, books no deal and changes nothing in how deals are found or settled.

  SELLER   a bot with a fresh offer of its own in the market, standing within 12 tiles of its meeting spot (in front of the bank), says "Selling iron ingots." once per 20 minutes per item.
  BUYER    a bot with a fresh want of its own for that item, hearing the line from another bot, answers 1.5-3.5 s later: "How much for the iron ingots, SmithAR?" (the seller's name without Bot).
  PRICE    the seller, hearing that question with its name and an item it offers, answers 1.5-3.5 s later from the offer: "55 gold each, TinkBR." (the buyer's name without Bot).
  RATE     at most 3 lines an hour per bot; the seller's call also takes a farm-wide 60-second bucket (a "vsay" claim in the shared memory); the question and the price are one exchange and are not bucketed.
Lines are added to the bot's own_lines, as chatter() does, so the journal rules do not take them for the game talking. The deal itself still happens as before (mkt_match, the secure trade at the bank).
Events (decisions.jsonl): market_talk {kind: offer | ask | price, item}, and the usual say {kind, text, to_human: false}.
"""
from __future__ import annotations

import random
import re
import time

FEATURE = "market_voice"
FRESH = 900.0
NEAR = 12
CALL_GAP = 1200.0
CAP_PER_HOUR = 3
BUCKET = 60
DELAY = (1.5, 3.5)
EVERY = 30.0
SAY = re.compile(r"^\[SAY\]\s+(Bot\w+):\s+(.+)$")
SELLING = re.compile(r"^selling\s+(.+?)s?\.?$", re.I)
ASK = re.compile(r"^how much for the\s+(.+?)s?,\s*(\w+)\?$", re.I)


def on(bot):
    try:
        return bool(bot.feature(FEATURE) and bot.feature("trade"))
    except Exception:
        return False


def _st(bot):
    return bot.__dict__.setdefault("_mvoice", {"said": [], "called": {}, "pending": None, "asked": {}, "look": 0.0})


def short(name):
    return name[3:] if name.startswith("Bot") else name


def tables(bot):
    try:
        offers, wants, _ = bot.mkt_view()
        return offers, wants
    except Exception:
        return {}, {}


def mine(table, bot):
    now = time.time()
    return [o for o in table.values() if o.get("bot") == bot.name and now - o.get("t", 0) < FRESH and o.get("qty", 1) > 0]


def near_meet(bot):
    try:
        mx, my = bot.MEET[0], bot.MEET[1]
    except Exception:
        return False
    return max(abs(bot.c.x - mx), abs(bot.c.y - my)) <= NEAR


def plural(item):
    return item if item.endswith("s") else item + "s"


def _emit(bot, name, **kw):
    try:
        from memory import cell_of
        cell = cell_of(bot.c.x, bot.c.y)
    except Exception:
        cell = None
    try:
        bot.dlog("ev", ev=name, cell=cell, rule=getattr(bot, "current_rule", None) or getattr(bot, "last_rule", None), **kw)
    except Exception:
        pass


def _hourly(st, now):
    st["said"] = [x for x in st["said"] if now - x < 3600]
    return st["said"]


def _say(bot, st, kind, item, line):
    bot.c.say(line)
    now = time.time()
    st["said"].append(now)
    try:
        bot.facts.setdefault("own_lines", set()).add(line.lower())
        bot.facts["said_any"] = now
        bot.dlog("say", kind="market_" + kind, text=line, to_human=False)
    except Exception:
        pass
    _emit(bot, "market_talk", kind=kind, item=item)


def feed(bot, t):
    """The other bots' lines: a seller's call that matches a want of mine, a question put to me about an offer of mine."""
    if not on(bot):
        return
    m = SAY.match(t)
    if not m or m.group(1) == bot.name:
        return
    who, text = m.group(1), m.group(2).strip()
    st = _st(bot)
    now = time.time()
    if st["pending"] or len(_hourly(st, now)) >= CAP_PER_HOUR:
        return
    s = SELLING.match(text)
    if s:
        item = s.group(1).lower()
        offers, wants = tables(bot)
        want = next((w for w in mine(wants, bot) if w["item"] in item or item in w["item"]), None)
        if want and now - st["asked"].get((who, want["item"]), 0) > CALL_GAP:
            st["asked"][(who, want["item"])] = now
            st["pending"] = {"due": now + random.uniform(*DELAY), "kind": "ask", "item": want["item"], "line": f"How much for the {plural(want['item'])}, {short(who)}?"}
        return
    a = ASK.match(text)
    if a and a.group(2).lower() == short(bot.name).lower():
        item = a.group(1).lower()
        offers, _ = tables(bot)
        offer = next((o for o in mine(offers, bot) if o["item"] in item or item in o["item"]), None)
        if offer and offer.get("price"):
            st["pending"] = {"due": now + random.uniform(*DELAY), "kind": "price", "item": offer["item"], "line": f"{int(offer.get('price') or 0)} gold each, {short(who)}."}


def tick(bot):
    """After every tick: a pending answer when it is due; the seller's call at the bank."""
    if not on(bot) or getattr(bot.c, "ghost", False):
        return
    st = _st(bot)
    now = time.time()
    p = st["pending"]
    if p and now >= p["due"]:
        st["pending"] = None
        _say(bot, st, p["kind"], p["item"], p["line"])
        return
    if now - st["look"] < EVERY:
        return
    st["look"] = now
    if len(_hourly(st, now)) >= CAP_PER_HOUR or not near_meet(bot):
        return
    offers, _ = tables(bot)
    for o in mine(offers, bot):
        if now - st["called"].get(o["item"], 0) < CALL_GAP:
            continue
        key = str(int(now // BUCKET))
        try:
            if not bot.mem.usable("vsay", key):
                return
            bot.mem.record("claim", kind="vsay", key=key, ttl=BUCKET)
        except Exception:
            pass
        st["called"][o["item"]] = now
        _say(bot, st, "offer", o["item"], f"Selling {plural(o['item'])}.")
        return
