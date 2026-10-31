"""Thinking aloud (feature "think_aloud"; the owner, 2026-10-20: "we should have the bots speak what they are 'thinking' and planning and the decisions they make
so i can watch it in real time in client"). The decision core says its decisions as ordinary overhead speech, short and in plain words: the next task, why a
task ended, a switch, a rung, a journey's leg, a retreat, an errand that could not be done.

Rules: at most one line every GAP seconds a bot; the same line not again within REPEAT seconds (a waiting loop does not chant); never while the hunt tree is in
a fight's own steps (pursue, fight, loot) unless the line is urgent (a retreat); at most MAX_LEN characters; and no word the server or a vendor takes as a
command (speech keywords: bank, buy, sell, guards, vendor, train, stable, claim ...), which are rephrased, so a bot never opens its bank box or a shop list by
talking to itself.
"""
from __future__ import annotations

import re
import time

GAP = 8.0
REPEAT = 60.0
MAX_LEN = 70
QUIET_STEPS = ("pursue", "fight", "loot")
# speech keywords (the client sends a keyword id when one is in the text; vendors, bankers, guards and stablemasters act on them): said in other words
KEYWORDS = ((r"\bbank(ing|ed)?\b", "vault"), (r"\bbalance\b", "savings"), (r"\bwithdraw(ing)?\b", "take out"), (r"\bbuy(ing)?\b", "get"), (r"\bsell(ing)?\b", "trade"),
            (r"\bsold\b", "traded"), (r"\bbought\b", "got"), (r"\bguards?\b", "watch"), (r"\bvendor\b", "shop"), (r"\btrain(ing)?\b", "practise"),
            (r"\bstable\b", "stalls"), (r"\bclaim\b", "fetch"), (r"\bpurchase\b", "get"), (r"\bhire\b", "take on"), (r"\bdeposit\b", "store"))


def on(bot):
    try:
        return bool(bot.feature("think_aloud"))
    except Exception:
        return False


def clean(text):
    t = " ".join(str(text).split())
    for pat, rep in KEYWORDS:
        t = re.sub(pat, rep, t, flags=re.I)
    t = t.lstrip("[.!/")                                   # never a command prefix
    if len(t) > MAX_LEN:
        t = t[:MAX_LEN - 3].rstrip(" ,;:") + "..."
    return t


def say(bot, text, urgent=False):
    """Say one decision line overhead (rate-limited, de-duplicated). True when said."""
    if not on(bot):
        return False
    st = bot.__dict__.setdefault("_think", {"last": 0.0, "said": {}})
    now = time.time()
    try:
        task = bot.facts.get("task") or {}
        tree = bot.__dict__.get("_core_tree")
        step = tree[0].step if tree else None
    except Exception:
        task, step = {}, None
    if step in QUIET_STEPS and task.get("task") in ("hunt", "tour2") and not urgent:
        return False
    if now - st["last"] < GAP and not urgent:
        return False
    line = clean(text)
    if not line:
        return False
    if now - st["said"].get(line, 0) < REPEAT:
        return False
    st["last"] = now
    st["said"][line] = now
    if len(st["said"]) > 50:
        for k in sorted(st["said"], key=st["said"].get)[:25]:
            del st["said"][k]
    try:
        bot.c.say(line)
    except Exception:
        return False
    try:
        bot.ev("think", line=line)
    except Exception:
        pass
    return True


# ---- the core's decisions in words ----------------------------------------------------------------------------------------------------------------------

def place(task):
    a = str(task.get("area") or "")
    if a.startswith("tour "):
        try:
            import gazetteer as gz
            sp = (task.get("spots") or [[0, 0]])[0]
            side = task.get("side") or "surface"
            if side != "surface":
                return side
            r = gz.nearest_town(int(sp[0]), int(sp[1]))
            if r and r[1] <= 40:
                return f"the edge of {r[0]['name']}"
            return "the fields" if (task.get("tier") or 1) <= 1 else "the wilds"
        except Exception:
            return "new ground"
    return a


def kinds_word(task):
    try:
        ks = [k for k in (task.get("kinds") or [])][:2]
    except Exception:
        ks = []
    return " and ".join(ks)


def task_start(bot, task, cand):
    kind = task.get("task")
    walk = int(round(float(task.get("walk_min") or 0)))
    if kind in ("hunt", "tour2"):
        who = f" with {task.get('partner')}" if task.get("partner") else ""
        ks = ", ".join((cand.get("kinds") or [])[:2])
        walk_s = f", {walk} min walk" if walk >= 2 else ""
        say(bot, f"Next: hunt {ks + ' in ' if ks else ''}{place(task)}{who}{walk_s}")
    elif kind == "resupply":
        try:
            b = bot.bandages()
        except Exception:
            b = "few"
        say(bot, f"Next: restock at the healer, I have {b} bandages")
    elif kind == "gather":
        say(bot, "No coin: off to chop logs and sell them")
    elif kind == "ammo":
        say(bot, "No arrows: off to the bowyer")
    elif kind == "arm":
        say(bot, "I have no proper weapon: buying one")
    elif kind == "fletch":
        say(bot, "Out of arrows: making some from my feathers and wood")
    elif kind == "sell":
        say(bot, "Next: trading my loot in town, the pack is full")
    elif kind == "bank":
        say(bot, "Next: putting my gold in the vault")
    elif kind == "rest":
        say(bot, "Too hurt, resting first")
    elif kind == "upgrade":
        say(bot, f"Next: getting {task.get('area') or 'better gear'}"[:MAX_LEN])
    elif kind == "train":
        say(bot, "Next: practising on the dummy")
    elif kind == "wait":
        say(bot, "No hunting ground open, waiting a while")


WHY = {"empty": "nothing here", "stale": "the ground went quiet", "crowded": "too many others here", "unreachable": "I can't get there",
       "yield": "it isn't paying", "deaths": "too dangerous", "switch": "something better", "done": "done", "unmet": "couldn't do it"}


def task_end(bot, task, why, act):
    kind = task.get("task")
    if kind in ("hunt", "tour2"):
        k = int(act.get("kills", 0) or 0)
        say(bot, f"Leaving {place(task)}: {WHY.get(why, why)}, {k} kill{'s' if k != 1 else ''}")
    elif why == "unmet":
        say(bot, {"resupply": "Couldn't restock, hunting carefully with what I have", "sell": "No one took my loot",
                  "bank": "Couldn't reach the vault"}.get(kind, f"Couldn't {kind}, moving on"))


def switch(bot, to, why):
    say(bot, f"Change of plan: {to}, {why}"[:MAX_LEN])
