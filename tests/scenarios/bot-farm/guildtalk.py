"""Guild chat for the farm's bots (A6/A7, Watcher 2026-10-17, Helper 2; feature "guild_chat"): once a bot is in a guild, a few situational lines an hour on the shard's guild chat (`\\` or `[g`, GuildChatService,
the client command `guild <text>`). Module functions called from talk.py's feed() and tick() (patch_guildtalk.py), so every brain that has talk has it.

Founding a guild is a different matter: the old guild system needs a Guild Deed (12,450 gp from the Provisioner) AND a house the founder owns, then the stone adds members. No bot has a house yet, so a guild exists
only if staff made one ([TestOnlyGuild on a host that loads the probe). This module works with any guild that exists; it never founds one.

  MEMBERSHIP  nothing is asked of the server. Guild chat reaches every member, the sender included, as "[GUILD] Name: text" in the client log; "[SYSTEM] You are not in a guild." answers a line from a bot without one.
              A "[GUILD] ..." line (anyone's) marks the bot a member (ev guild_join {guild} once, guild = the abbreviation or name when the line carried it, else ""). The refusal marks it not a member for 30 minutes;
              a bot of unknown standing probes with its first situational line, at most once per 30 minutes.
  LINES       kind "selling": a crafter with stock that has just banked ("Selling ingots at the bank."); kind "warn": an attack-on-sight monster of more than 25 hit points within 14 tiles ("A troll north of
              Britain, careful."); kind "hunt": a fighter in town ("Who wants to hunt?"). Era plain: no digits, no rule names, no internal words.
  RATE        at most 4 lines an hour per bot, 8 minutes apart, and one line per 90-second bucket for the whole farm (a claim of kind "gsay" in the shared memory), none as a ghost or with a threat near
              (except "warn", which is the point).
Events (decisions.jsonl): guild_join {guild}, guild_chat {kind, text}.
"""
from __future__ import annotations

import re
import time

FEATURE = "guild_chat"
CAP_PER_HOUR = 4
GAP = 480.0
BUCKET = 90
NOT_MEMBER_FOR = 1800.0
LOOK_EVERY = 60.0
WARN_RANGE = 14
GUILD_LINE = re.compile(r"^\[GUILD\]\s+([^:]+?):\s*(.*)$")
TAG = re.compile(r"\[([A-Za-z]{2,4})\]")
NOT_IN = "you are not in a guild"


def on(bot):
    try:
        return bool(bot.feature(FEATURE))
    except Exception:
        return False


def _st(bot):
    return bot.__dict__.setdefault("_guildtalk", {"member": None, "not_until": 0.0, "said": [], "joined": False, "look": 0.0})


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


def feed(bot, t):
    """Every journal line (talk.feed hands them on): the guild's own chat and the refusal tell membership."""
    if not on(bot):
        return
    st = _st(bot)
    low = t.lower()
    if low.startswith("[system]") and NOT_IN in low:
        st["member"] = False
        st["not_until"] = time.time() + NOT_MEMBER_FOR
        return
    m = GUILD_LINE.match(t)
    if m:
        st["member"] = True
        if not st["joined"]:
            st["joined"] = True
            tag = TAG.search(m.group(1))
            _emit(bot, "guild_join", guild=tag.group(1) if tag else "")


def hourly(st, now):
    st["said"] = [x for x in st["said"] if now - x < 3600]
    return st["said"]


def choose(bot):
    """(kind, text) for the situation, or None."""
    try:
        import talk
    except Exception:
        talk = None
    # a monster in sight: the warning is the point of the channel
    if talk is not None:
        try:
            near = [m for m in bot.c.mobiles(within=WARN_RANGE) if not m.name.startswith("Bot") and m.notoriety in ("Gray", "Criminal", "Enemy", "Murderer")
                    and not getattr(m, "is_dead", False) and talk.dangerous(m) and talk.aggressive(m)]
        except Exception:
            near = []
        if near:
            m = min(near, key=lambda o: o.distance)
            name = m.name if m.name.lower().startswith(("a ", "an ", "the ")) else f"a {m.name}"
            where = ""
            try:
                where = bot.where()
            except Exception:
                pass
            return "warn", (name[:1].upper() + name[1:]) + (f" {where}" if where else "") + ", careful."
    now = time.time()
    try:
        stock = [p for p in bot.products()]
    except Exception:
        stock = []
    if stock and now - bot.facts.get("banked_at", 0) < 180:
        item = getattr(stock[0], "name", str(stock[0])).lower()
        item = re.sub(r"[^a-z' -]", "", item).strip()
        if item:
            return "selling", f"Selling {item} at the bank."
    try:
        fighter = hasattr(bot, "main_skill") and bot.in_britain()
    except Exception:
        fighter = False
    if fighter and not stock:
        return "hunt", "Who wants to hunt?"
    return None


def tick(bot):
    """After every tick: at most one line a minute is considered."""
    if not on(bot) or getattr(bot.c, "ghost", False):
        return
    st = _st(bot)
    now = time.time()
    if now - st["look"] < LOOK_EVERY:
        return
    st["look"] = now
    if st["member"] is False and now < st["not_until"]:
        return
    said = hourly(st, now)
    if len(said) >= CAP_PER_HOUR or (said and now - said[-1] < GAP):
        return
    pick = choose(bot)
    if not pick:
        return
    kind, text = pick
    try:
        if kind != "warn" and bot.threats(10):
            return
    except Exception:
        pass
    key = str(int(now // BUCKET))
    try:
        if not bot.mem.usable("gsay", key):
            return
        bot.mem.record("claim", kind="gsay", key=key, ttl=BUCKET)
    except Exception:
        pass
    try:
        bot.c.call(f"guild {text}", timeout=5)
    except Exception:
        return
    st["said"].append(now)
    _emit(bot, "guild_chat", kind=kind, text=text)
